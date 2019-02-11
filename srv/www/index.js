var	LS = window.localStorage || localStorage

,	classPageLoading          = 'loading'
,	classSectionOpen          = 'open'
,	classLinksChain           = 'links-chain'
,	classMediaRowsEnabled     = 'media-rows-separated'
,	classMediaRowsContainer   = 'media-rows-table'
,	classMediaRow             = 'media-row'
,	classMediaRowInlineHeader = 'media-row-header-inside'
,	classMediaRowInlineValue  = 'media-row-value-inside'
,	classMediaRowInfoTable    = 'media-row-info'
,	classMediaRowImages       = 'media-row-images'
,	classMediaRowImageBreaks  = 'media-row-img-newlines'
,	classMediaRowImageLink    = 'media-row-img'
,	classSimpleRowsContainer  = 'simple-rows-table'
,	classSimpleRow            = 'simple-row'

,	regDrawpilePartStart = '^(?:.*\\/)?'
,	regDrawpilePartDate  = '(\\d{4}(?:\\D\\d\\d){5}\\S*) - '
,	regDrawpilePartID    = '([0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})'
,	regDrawpilePartEnd   = '(?:[#?].*)?$'

,	regDrawpileUserName = /^(.+?)\s(\d+)$/
,	regDrawpileRecording = new RegExp(
		regDrawpilePartStart
	+	'(?:' + regDrawpilePartDate
	+	'(?:' + regDrawpilePartDate + ')?)?'
	+	'(?:(r\\d+|\\d+[g+]+) - )?'
	+	'(?:(\\d+)s - )?'
	+	'(?:(\\d+)u - )?'
	+	'(?:(\\S.*?) - )?'
	+	regDrawpilePartID
	+	'(\\.dprec)(\\.archived)?'
	+	regDrawpilePartEnd
	, 'i')

,	regDrawpileImage = new RegExp(
		regDrawpilePartStart
	+	regDrawpilePartID
	+	'-(\\d+)_(full|thumb)_(\\d+)x(\\d+)(\\.\\w+)'
	+	regDrawpilePartEnd
	, 'i')

,	attrSort = 'data-sort-'
,	argSort = {
		'sort_by': 'name'
	,	'sort_order': 'ascending'
	}

,	regNum = /\d+/
,	regSlash = /[\\\/]+/g
,	regSpace = /\s+/g
,	regTrim = /^\s+|\s+$/g
,	regTrimDots = getTrimReg('.\\s')
,	regTrimSlash = /^[\\\/]+|[\\\/]+$/g
,	regTimeBreak = /^\d+(<|>|,|$)/

,	splitSec = 60
,	maxThumbWidth = 200
,	maxThumbHeight = 200

,	dprecMetaByID = {}

,	TOS = ['object', 'string']

,	la, lang = document.documentElement.lang || 'en'
	;

//* UI translation *-----------------------------------------------------------

//if (LS && !(LS.lang && LS.lang == lang)) LS.lang = lang;	//* <- use user-selectable cookie instead

if (lang == 'ru') la = {
	'toggle': {
		'media_rows': 'Переключить вид медиафайлов'
	,	'img_newlines': 'Переключить ряды картинок'
	}
,	'drawpile': {
		'start': 'Начало'
	,	'end': 'Конец'
	,	'restrict': 'Ограничение'
	,	'dl': 'Скачать'
	,	'size': 'Вес'
	,	'strokes': 'Черт'
	,	'index_of_total': ' из '
	,	'users': 'Участников'
	,	'users_omitted': '(ещё $1)'
	}
}; else la = {
	'toggle': {
		'media_rows': 'Toggle media file view'
	,	'img_newlines': 'Toggle image rows'
	}
,	'drawpile': {
		'start': 'Start'
	,	'end': 'End'
	,	'restrict': 'Restrict'
	,	'dl': 'Download'
	,	'size': 'Size'
	,	'strokes': 'Strokes'
	,	'index_of_total': ' of '
	,	'users': 'Users'
	,	'users_omitted': '($1 more)'
	}
};

//* Utility functions *--------------------------------------------------------

function showProps(o,r,z /*incl.zero*/) {var i,t=''; for(i in o)if(z||o[i])t+='\n'+i+'='+o[i]; if(r)return t; alert(t); return o;}
function compareCaseless(a, b) {return a.toLowerCase() > b.toLowerCase() ? 1 : -1;}
function gc(n,p) {try {return TOS.slice.call((p || document).getElementsByClassName(n) || []);} catch(e) {return [];}}
function gt(n,p) {try {return TOS.slice.call((p || document).getElementsByTagName(n) || []);} catch(e) {return [];}}
function gn(n,p) {try {return TOS.slice.call((p || document).getElementsByName(n) || []);} catch(e) {return [];}}
function id(i) {return document.getElementById(i);}
function orz(n) {return parseInt(n||0)||0;}
function hasValue(v) {return !!v;}
function leftPad(n) {n = orz(n); return n > 9 || n < 0?n:'0'+n;}
function getTrimReg(c) {return new RegExp('^['+c+']+|['+c+']+$', 'gi');}
function getClassReg(c) {return new RegExp('(^|\\s)('+c+')($|\\s)', 'i');}
function toggleClass(e,c,keep) {
var	j = orz(keep)
,	k = 'className'
,	old = e[k] || e.getAttribute(k) || ''
,	a = old.split(regSpace)
,	i = a.indexOf(c)
	;
	if (i < 0) {
		if (j >= 0) a.push(c);
	} else {
		if (j <= 0) a.splice(i, 1);
	}
	if (a.length) {
		j = a.filter(hasValue).join(' ');
		if (old != j) e[k] = j;
	} else if (old) e[k] = '', e.removeAttribute(k);
}

function cre(e,p,b) {
	e = document.createElement(e);
	if (b) p.insertBefore(e, b); else
	if (p) p.appendChild(e);
	return e;
}

function del(e) {
	if (!e) return;
	if (e.substr) e = gt(e);
	if (e.map) e.map(del); else
	if (p = e.parentNode) p.removeChild(e);
	return p;
}
function eventStop(e,i,d) {
	if ((e && e.eventPhase !== null) ? e : (e = window.event)) {
		if (d && e.preventDefault) e.preventDefault();
		if (i && e.stopImmediatePropagation) e.stopImmediatePropagation();
		if (e.stopPropagation) e.stopPropagation();
		if (e.cancelBubble !== null) e.cancelBubble = true;
	}
	return e;
}

function getParentByTagName(e,t) {
var	p = e
,	t = t.toLowerCase()
	;
	while (e && !(e.tagName && e.tagName.toLowerCase() == t) && (p = e.parentNode)) e = p;
	return e;
}

function getParentBeforeTagName(e,t) {
var	p = e
,	t = t.toLowerCase()
	;
	while (e && (e = e.parentNode) && !(e.tagName && e.tagName.toLowerCase() == t)) p = e;
	return p;
}

function getParentBeforeClass(e,c) {
var	p = e
,	r = (c.test ? c : getClassReg(c))
	;
	while (e && (e = e.parentNode) && !(e.className && r.test(e.className))) p = e;
	return p;
}

function decodeHTMLSpecialChars(t) {
	return String(t)
	.replace(/&nbsp;/gi, ' ')
	.replace(/&lt;/gi, '<')
	.replace(/&gt;/gi, '>')
	.replace(/&quot;/gi, '"')
	.replace(/&#0*39;/g, "'")
	.replace(/&amp;/gi, '&');
}

function encodeHTMLSpecialChars(t) {
	return String(t)
	.replace(/&/g, '&amp;')
	.replace(/"/g, '&quot;')
	.replace(/'/g, '&#39;')
	.replace(/</g, '&lt;')
	.replace(/>/g, '&gt;');
}

function encodeTagAttr(t) {
	return String(t).replace(/"/g, '&quot;');
}

function getTagAttrIfNotEmpty(name, values, delim) {
	if (name && values) {
	var	a = (values.filter ? values : [values]).filter(function(v) {return !!v;});
		if (a.length) return ' ' + name + '="' + encodeTagAttr(a.join(delim || ' ')) + '"';
	}
	return '';
}

function getFormattedTimezoneOffset(t) {
	return (
		(t = (t && t.getTimezoneOffset ? t : new Date()).getTimezoneOffset())
		? (t < 0?(t = -t, '+'):'-')+leftPad(Math.floor(t/splitSec))+':'+leftPad(t%splitSec)
		: 'Z'
	);
}

function getFormattedTime(t, plain, only_ymd) {
	if (TOS.indexOf(typeof t) > -1) {
	var	text = '' + t;
		if (typeof t === 'string' && Date.parse) {
			t = Date.parse(t.replace(/(T\d+)-(\d+)-(\d+\D*)/, '$1:$2:$3'));
		} else {
			t = n * 1000;
		}
		if (!t && text) return text;
	}
var	d = (t ? new Date(t+(t > 0 ? 0 : new Date())) : new Date());
	t = ('FullYear,Month,Date'+(only_ymd?'':',Hours,Minutes,Seconds')).split(',').map(function(v,i) {
		v = d['get'+v]();
		if (i == 1) ++v;
		return leftPad(v);
	});
var	YMD = t.slice(0,3).join('-')
,	HIS = t.slice(3).join(':')
	;
	return (
		plain
		? YMD+' '+HIS
		: '<time datetime="'+YMD+'T'+HIS
		+	getFormattedTimezoneOffset(t)
		+	'" data-t="'+Math.floor(d/1000)
		+	'">'+YMD+' <small>'+HIS+'</small></time>'
	);
}

function getFileSizeText(size) {
	return (size ?
		size.short + ' ('
	+	size.bytes + ')'
	: '');
}

function getTextOrURImatch(text, pattern) {
var	t = '' + text;
	return (
		t.match(pattern)
	||	decodeURIComponent(t).match(pattern)
	);
}

//* Page-specific functions *--------------------------------------------------

function toggle(e) {
	toggleClass(e, classSectionOpen);
}

function toggleMediaRows(e) {
	toggleClass(getParentBeforeClass(e.target || e, 'inside').parentNode, classMediaRowsEnabled);
}

function toggleImageNewlines(e) {
	toggleClass(getParentBeforeClass(e.target || e, 'inside').parentNode, classMediaRowImageBreaks);
}

function getSortFromURL(url) {
var	a = url.split(/"/g)
,	i = a.length
,	a = a[i > 1 ? 1 : 0].split(/[?&#]/g)
,	i = a.length
,	j,k,arg
,	result = {}
	;

	while (i--) if (arg = a[i]) {
		j = arg.split(/=/g);
		k = j.shift();
		if (
			!result[k]
		&&	(k in argSort)
		) {
			result[k] = j.join('=');
		}
	}

	for (k in argSort) if (!result[k]) {
		result[k] = argSort[k];
	}

	return result;
}

function sortByColumn(e) {
var	ev = eventStop(0,1,1)
,	arg = getSortFromURL(e.href || e)
,	table = getParentByTagName(e, 'table')
,	tbody,tr,td
,	row_a = gt('tr', table)
,	row_i = row_a.length
,	rows = []
,	i,j,k
,	compareOrder = ['type', 'value', 'text']
	;

	while (row_i--) if (tr = row_a[row_i]) {
		i = tr.getAttribute(attrSort + 'type');
		if (j = tr.getAttribute(attrSort + arg.sort_by)) {
			rows.push({
				'row_e': tr
			,	'text': tr.textContent
			,	'type': i
			,	'value': (arg.sort_by === 'name' ? j : orz(j))
			});

			if (!tbody) tbody = tr.parentNode;
		}
	}

	rows.sort(function(a, b) {
		for (i in compareOrder) {
		var	i,k = compareOrder[i];
			if (a[k] !== b[k]) return (a[k] < b[k]) ? -1 : 1;
		}

		return 1;
	});

	if (arg.sort_order !== 'ascending') rows.reverse();

	for (i = 0, j = rows.length; i < j; i++) if (tr = rows[i].row_e) {
		tbody.appendChild(tr);
	}
}

function updateDrawpileTable(e) {
	if (
		e
	&&	(e.target ? (e = e.target) : e).src
	&&	(i = e.src.match(regDrawpilePartID))
	) {
	var	a,p
	,	i = i[1]
	,	d = dprecMetaByID[i]
		;

		if (
			(e = id(i))
		&&	(a = gc('user', e))
		&&	(p = a[0])
		&&	(p = p.parentNode)
		) {
			del(a);

			for (i in d) {
				e = cre('tr', p);
				e.className = 'user';
				e.innerHTML = (
					'<td colspan="2">' + i + '</td>'
				+	'<td colspan="2">' + d[i] + '</td>'
				);
			}
		}
	}
}

//* Runtime *------------------------------------------------------------------

window.addEventListener('load', function() {

	gt('time').map(function(e) {
	var	t = e.getAttribute('data-t');
		if (t && orz(t) > 0) e.outerHTML = getFormattedTime(t);
	});

	gc('inside').map(function(eContainer) {

		function addPathLink(text, link) {
		var	p = pathLinkContainer || topButtonContainer || eContainer
		,	a = cre('a', p)
			;

			a.textContent = text || link;
			a.href = link || text;
		}

		function addTopButton(text, func) {
		var	p = topButtonContainer || pathLinkContainer || eContainer
		,	b = cre('button', p)
			;

			b.textContent = text;
			b.onclick = func;
		}

//* Simple dir/file list sort:

	var	p = id('path')
	,	p = (p ? p.parentNode : eContainer.firstElementChild)
	,	topButtonContainer = p
	,	pathLinkContainer = p
	,	countByType = {}
	,	dirsInside = []
	,	dirsAround = []
		;

		gt('tr', eContainer).map(function(tr) {
		var	a,e,f,g,h,i,j,k,v;

			if (i = (a = gt('td', tr)).length) {
				j = {};

				while (i--) if (e = a[i]) {
					k = v = '';
					if (f = gt('a', e)[0]) {
						k = 'name';
						v = f.getAttribute('href');
					} else
					if (f = gt('time', e)[0]) {
						k = 'mtime';
						v = orz(f.getAttribute('data-t'));
					} else
					if (f = e.title) {
						k = 'size';
						v = orz(f);
					}
					if (k) j[k] = v;
				}

				if (j) {
					j.type = g = ('size' in j ? 'file' : 'dir');
					if (LS && g == 'dir') dirsInside.push(j.name);
					for (i in j) tr.setAttribute(attrSort + i, j[i]);

					if (g in countByType) {
						countByType[g] += 1;
					} else {
						countByType[g] = 1;
					}
				}
			} else
			if (i = (a = gt('a', tr)).length) {
				while (i--) if (
					(e = a[i])
				&&	(h = e.href)
				) {
					v = getSortFromURL(h);
					h = '';

					for (k in v) {
						h += (h ? '&' : '#') + k + '=' + v[k];
					}

					e.href = 'javascript:sortByColumn("' + h + '")';
					e.setAttribute('onclick', 'sortByColumn(this)');
				}
			}
		});

		if (
			!countByType.file
		&&	(a = gt('th', eContainer)).length > 0
		) {
			a[0].setAttribute('colspan', 2);
			del(a[1]);
		}

		if (e = id('path')) {
		var	a = (
				e.textContent
				.replace(regTrim, '')
				.replace(regTrimSlash, '')
				.split(regSlash)
			)
		,	k = a.length
		,	p = e.parentNode
		,	pathLinkContainer = p
			;
			del(e);
			p.innerHTML = p.innerHTML.replace(/[\s:.,]*$/, ': ');

			if (k > 1) {
			var	currentPath = ''
			,	i = 0
			,	j = '/'
				;

				e = pathLinkContainer = cre('span', p);
				e.className = classLinksChain;

				a.unshift('');

				for (k++; i < k; i++) {
				var	currentName = a[i] + j;
					currentPath += currentName;
					addPathLink(currentName, currentPath);
					// cre('span', pathLinkContainer).textContent = '»';
				}

				pathLinkContainer = p;
			}

			if (LS) {

	//* Remember dir list to display prev/next inside them:

			var	currentName = a.slice(-1)[0] + '/'
			,	currentPath = ('/' + a.join('/') + '/').replace(regSlash, '/')
			,	parentPath = ('/' + a.slice(0, -1).join('/') + '/').replace(regSlash, '/')
				;

				if (dirsInside.length > 0) {
					dirsInside.sort(compareCaseless);

				var	v = JSON.stringify(dirsInside)
				,	k = currentPath
				,	o = LS[k] || ''
					;

					if (o !== v) LS[k] = v;
				}

	//* Restore dirs around to display prev/next links:

				if (
					(currentPath !== parentPath)
				&&	(v = LS[parentPath])
				&&	(v = dirsAround = JSON.parse(v))
				&&	(v.length > 0)
				&&	(i = v.indexOf(currentName)) > -1
				) {
				var	a = [];

					if (i > 0) {
						k = v[i - 1], a.push([k + ' ←', '../' + k]);
					}
					if (i < v.length - 1) {
						k = v[i + 1], a.push(['→ ' + k, '../' + k]);
					}

					k = a.length;
					if (k > 0) {
						p = pathLinkContainer;
						e = pathLinkContainer = cre('span', p);
						e.className = classLinksChain;

						for (i = 0; i < k; i++) {
							addPathLink(a[i][0], a[i][1]);
						}

						pathLinkContainer = p;
					}
				}

				/*console.log([
					'Up:     ' + parentPath
				,	'Here:   ' + currentPath
				,	'This:   ' + currentName
				,	'In:     ' + dirsInside.join('\n')
				,	'Around: ' + dirsAround.join('\n')
				].join('\n\n'));*/
			}
		}

//* Drawpile sessions:
//* 1. Get all session IDs: *----/----

	var	fileRecIDs = []
	,	simpleFileTable
	,	simpleFileCount = 0
		;

		gt('a', eContainer).map(function(e) {
		var	url = e.href
		,	recID
		,	match
			;
			if (
				url
			&&	(match = getTextOrURImatch(url, regDrawpileRecording))
			&&	(recID = match[7])
			&&	fileRecIDs.indexOf(recID) < 0
			) {
				fileRecIDs.push(recID);
				if (!simpleFileTable) simpleFileTable = getParentByTagName(e, 'table');
			}
		});

//* 2. Get all files by session IDs: *----/----

		if (fileRecIDs.length > 0) {
			toggleClass(eContainer, classMediaRowsEnabled, 1);

			// addTopButton(la.toggle.media_rows, toggleMediaRows);
			// addTopButton(la.toggle.img_newlines, toggleImageNewlines);

		var	filesByRecID = {};

			gt('a', eContainer).map(function(e) {
			var	url = e.href
			,	i,j,k
			,	recID
			,	match
			,	specialFileExts = ['js']
				;
				if (url) {
					for (i in fileRecIDs) if (
						(recID = fileRecIDs[i])
					&&	url.indexOf(recID) >= 0
					) {
					var	tr = getParentByTagName(e, 'tr')
					,	td = gt('td', tr)
					,	f = e.textContent
					,	s = td[1].textContent
					,	b = td[1].title
					,	t = gt('time', td[2])[0]
					,	t = (t ? t.getAttribute('data-t') : 0)
					,	file = {
							'name': f
						,	'time': t
						,	'size': {
								'short': s
							,	'bytes': b
							,	'num': orz(b)
							}
						}
					,	o = filesByRecID[recID] || (filesByRecID[recID] = {})
					,	ext
						;

						if (match = getTextOrURImatch(f, regDrawpileImage)) {
							file.index  = k = orz(match[2]);
							file.width  = orz(match[4]);
							file.height = orz(match[5]);
							j = o.img || (o.img = []);
							j = j[k]  || (j[k]  = {});
							j[match[3]] = file;
						} else {
							if (match = getTextOrURImatch(f, regDrawpileRecording)) {
								file.time = {
									'start': match[1] || ''
								,	'end': match[2] || ''
								};
								file.restrict = match[3] || '';
								file.num = {
									'strokes': orz(match[4])
								,	'users': orz(match[5])
								};
								file.userNames = (match[6] || '').split(', ') || [];
							}
							if (specialFileExts.indexOf(ext = f.split(/\./g).pop()) < 0) {
								ext = 'dl';
							} else
							if (ext == 'js') {
							var	js = cre('script', document.head);
								js.addEventListener('load', updateDrawpileTable, false);
								js.src = file.name;
							}
							(o[ext] || (o[ext] = [])).push(file);
						}

						toggleClass(tr, classSimpleRow, 1);

						return;
					}
				}
			});

			toggleClass(simpleFileTable, classSimpleRowsContainer, 1);

			if (simpleFileTable) {
				simpleFileCount = gt('tr', simpleFileTable).filter(function(e) {
				var	c = e.className;
					return (
						(!c || c.indexOf(classSimpleRow) < 0)
					&&	gt('td', e).length > 0
					);
				}).length;

				if (simpleFileCount === 0) {
					toggleClass(simpleFileTable, classSimpleRow, 1);
				}
			}

//* 3. Make separate table with rows by session IDs: *----/----

		var	table = cre('table', eContainer)
		,	tableRows = []
		,	recID
		,	a,b,c,d,e,f,g,h,i,j,k,m,n,v
			;

			table.className = classMediaRowsContainer;

//* 3.1. Get downloads, images and metadata:

			for (recID in filesByRecID) {
			var	o = filesByRecID[recID]
			,	start = ''
			,	end = ''
			,	restrict = []
			,	strokes = 0
			,	users = 0
			,	size = {}
			,	userNames = []
			,	downloadSortOrder = ['text', 'size', 'html']
			,	downloads = (
					(o.dl || [])
					.filter(hasValue)
					.map(
						function(file) {
							if (j = file.userNames) {
								for (k in j) if (
									(n = j[k])
								&&	userNames.indexOf(n) < 0
								) userNames.push(n);
							}
							if (j = file.restrict) {
								if (!restrict || restrict.indexOf(j) < 0) restrict.push(j);
							}
							if (j = file.time) {
								if ((k = j.start) && (!start || start < k)) start = k;
								if ((k = j.end  ) && (!end   || end   > k)) end = k;
							}
							if (j = file.num) {
								if ((k = j.strokes) && strokes < k) strokes = k;
								if ((k = j.users  ) && users   < k) users = k;
							}
							if (j = file.size) {
								if ((k = j.num) && (!size || !size.num || size.num < k)) size = j;
							}

						var	i,j,k
						,	n = file.name
						,	label = n.substr(n.indexOf(recID) + recID.length).replace(regTrimDots, '')
						,	downloadLink = (
								'<a href="'
							+		n
							+	'" target="_blank" rel="nofollow">'
							+		label
							+	'</a> (' + j.short + ')'
							)
						,	downloadSize = getTagAttrIfNotEmpty('title', getFileSizeText(j))
							;

							return {
								'text': label
							,	'size': (j ? k : 0)
							,	'html': (
									downloadSize ?
										'<span'
									+		downloadSize
									+	'>'
									+		downloadLink
									+	'</span>'
									: downloadLink
								)
							};
						}
					).sort(
						function(a, b) {
							for (var i in downloadSortOrder) {
							var	k = downloadSortOrder[i]
							,	c = a[k]
							,	d = b[k]
								;
								if (c !== d) return c > d ? 1 : -1;
							}
							return -1;
						}
					)
				)
			,	tableRowName = (
					[
						start || ''
					,	end || ''
					,	recID
					]
					.filter(hasValue)
					.join('\n')
				)
			,	prevHeight = 0
			,	images = (
					(o.img || [])
					.filter(hasValue)
					.map(
						function(file, i, a) {
					var	full = file.full || file.thumb
					,	thumb = file.thumb || file.full
					,	meta = (
							'#'
						+	full.index + la.drawpile.index_of_total
						+	a.length + ' - '
						+	full.width + 'x'
						+	full.height + ', '
						+	getFileSizeText(full.size)
						)
					,	width = thumb.width
					,	height = thumb.height
						;

						if (
							width > maxThumbWidth
						||	height > maxThumbHeight
						) {
							k = Math.max(
								width / maxThumbWidth
							,	height / maxThumbHeight
							);
							width = Math.min(maxThumbWidth, Math.round(width / k) || 1);
							height = Math.min(maxThumbHeight, Math.round(height / k) || 1);
						}

					var	newLine = (prevHeight && prevHeight != height ? '<br>' : '');
						prevHeight = height;

						return (
							newLine
						+	'<a href="' + full.name
						+	'" class="' + classMediaRowImageLink
						+	'" title="' + meta
						+	'" target="_blank">'
						+		'<img src="' + thumb.name
						+		'" width="' + width
						+		'" height="' + height
						+		'" alt="' + meta
						+		'">'
						+	'</a>'
						);
					}
					)
				)

//* 3.2. Get row metadata fields:

			,	userNames = userNames.sort(compareCaseless)
			,	rowID = {
					'head': 1
				,	'sort': {'id': recID}
				,	'tabs': [
						'<a href="#'
					+		recID
					+	'">'
					+		recID
					+	'</a>'
					]
				}
			,	rowTimeStart = (start ? {
					'sort': {'start': start}
				,	'tabs': [
						la.drawpile.start + ':'
					,	{'tip': start, 'html': getFormattedTime(start)}
					]
				} : null)
			,	rowTimeEnd = (end ? {
					'sort': {'end': end}
				,	'tabs': [
						la.drawpile.end + ':'
					,	{'tip': end, 'html': getFormattedTime(end)}
					]
				} : null)
			,	rowRestrict = (
					restrict.length > 0
				&&	(
						k = 0
					,	v = restrict.map(
							function(v) {
							var	match = v.match(regNum)
							,	num = orz(match ? match[0] : 0)
								;
								if (k < num) k = num;
								return v;
							}
						).join(' ')
					,	v = (
							k == v
							? k
							: k + '+ (' + v + ')'
						)
					)
				? {
					'sort': {'restrict': v}
				,	'tabs': [
						la.drawpile.restrict + ':'
					,	v
					]
				} : null)
			,	rowDownloads = (
					downloads.length > 0
				&&	(
						k = downloads.map(function(a) { return a.text; }).join('\n')
					,	v = downloads.map(function(a) { return a.html; }).join(', ')
					)
				? {
					'sort': {'dl': k}
				,	'tabs': [
						la.drawpile.dl + ':'
					,	v
					]
				} : null)
			,	rowUserCount = (users || strokes ? {
					'sort': {
						'users': users
					,	'strokes': strokes
					}
				,	'tabs': [
						la.drawpile.users + ':'
					,	users
					,	la.drawpile.strokes + ':'
					,	strokes
					]
				} : null)
			,	usersLeft = users
			,	strokesLeft = strokes
			,	rowUserList = userNames.map(
					function(line) {
					var	match = line.match(regDrawpileUserName)
					,	name = (match ? match[1] : name)
					,	stat = (match ? orz(match[2]) : 0)
						;
						usersLeft--;
						strokesLeft -= stat;

						return {
							'class': 'user'
						,	'tabs': [name, stat]
						};
					}
				)

//* 3.3. Get row metadata table rows:

			,	dataRows = [
				,	rowID
				,	rowTimeStart
				,	rowTimeEnd
				,	rowRestrict
				,	rowDownloads
				,	rowUserCount
				].concat(rowUserList)
				.concat(
					usersLeft || strokesLeft
					? [
						{
							'class': 'user'
						,	'tabs': [
								la.drawpile.users_omitted.replace('$1', usersLeft)
							,	strokesLeft
							]
						}
					]
					: []
				)
				.filter(hasValue)
			,	rowMaxTabCount = dataRows.reduce(
					function(prev, row) {
					var	k = (row.tabs ? row.tabs.length : 0) + (row.lines ? 1 : 0);
						return (k && k > prev ? k : prev);
					}
				,	0
				)
			,	dataRows = dataRows.map(
					function(row) {
					var	className = getTagAttrIfNotEmpty('class', row['class'])
					,	tip = getTagAttrIfNotEmpty('title', row.tip)
					,	lines = row.lines
					,	tabs = row.tabs.filter(hasValue)
					,	i, o = row.sort
					,	sort = ''
						;

						if (o) for (i in o) {
							sort += getTagAttrIfNotEmpty(attrSort + i, o[i]);
						}

						if (tabs && (i = tabs.length) > 0) {
						var	tagName = (row.head ? 'th' : 'td')
						,	j = rowMaxTabCount
						,	k = (j > i ? Math.ceil(j / i) : 1)
							;
							tabs = tabs.map(
								function(tab) {
								var	tip = getTagAttrIfNotEmpty('title', tab.tip)
								,	n = Math.min(j, k)
								,	combine = (n > 1 ? ' colspan="' + n + '"' : '')
									;
									j -= k;
									return (
										'<' + tagName + combine + tip + '>'
									+		(tab.html || tab)
									+	'</' + tagName + '>'
									);
								}
							);
						}

						return tabs ? (
							'<tr' + className + tip + sort + '>'
						+		tabs.join('')
						+	'</tr>'
						) : '';
					}
				).filter(hasValue)
				;

//* 3.4. Get media table row with all relevant files:

				tableRows.push({
					'sort': tableRowName
				,	'id': recID
				,	'html': (
						'<table class="' + classMediaRowInfoTable + '">'
					+		dataRows.join('')
					+	'</table>'
					+	'<span class="' + classMediaRowImages + '">'
					+		images.join('')
					+	'</span>'
					)
				});
			}

//* 3.4. Add rows to media table:

		var	compareOrder = ['sort', 'id', 'html'];

			tableRows.sort(function(a, b) {
				for (i in compareOrder) {
				var	i,k = compareOrder[i];
					if (a[k] !== b[k]) return (a[k] < b[k]) ? -1 : 1;
				}

				return 1;
			});

			tableRows.map(
				function(row) {
				var	e = cre('tr', table);
					e = cre('td', e);
					e.id = row.id;
					e.className = classMediaRow;
					e.innerHTML = row.html;
				}
			);
		}
	});

//* END Drawpile sessions

	toggleClass(document.documentElement, classPageLoading, -1);

}, false);

toggleClass(document.documentElement, classPageLoading, 1);
