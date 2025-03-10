﻿var	LS = window.localStorage || localStorage
,	canToggleView = true //(location.protocol === 'file:')

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
,	classMediaRowStatsDL      = 'sub-list-row download'
,	classMediaRowStatsUser    = 'sub-list-row user'
,	classSimpleRowsContainer  = 'simple-rows-table'
,	classSimpleRow            = 'simple-row'

,	regDrawpilePartStart = '^(?:.*\\/)?'
,	regDrawpilePartEnd = '(?:[#?].*)?$'
,	regDrawpilePartID = (
		'('
	+	[	'[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}'
		,	'[0-9a-z]{26}'
		].join('|')
	+	')'
	)
,	regDrawpilePartIndex = (
		'('
	+	[	'[\\s_]r\\d+'
		,	'[\\s_]?[\\[\\{\\(]\\d+[\\]\\)\\}]'
		].join('|')
	+	')?'
	)

,	regDrawpileRecordingFileName = new RegExp(
		regDrawpilePartStart
	+	'((?:\\S.*? - )*?)'	//* <- [1] = any meta parts in any order
	+	regDrawpilePartID	//* <- [2] = session ID
	+	regDrawpilePartIndex	//* <- [3] = session part index
	+	'(\\.(?:dprec|dptxt))'	//* <- [4] = file ext
	+	'(\\.archived)?'	//* <- [5] = file ext optional suffix
	+	regDrawpilePartEnd
	, 'i')

,	regDrawpileRecordingUserName = /^(.+?)\s(\d+)$/
,	regDrawpileRecordingMetaPart = new RegExp(
		'^(?:'
	+	[	'part (\\d+)(?: of (\\d+))?'	//* <- [1,2] = part index/total count
		,	'(\\d{4}(?:\\D\\d\\d){5}\\S*)'	//* <- [3] = date/time
		,	'(r\\d+|r?\\d+[g+]+)'		//* <- [4] = restriction rating
		,	'(\\d+)s'			//* <- [5] = strokes count
		,	'(\\d+)u'			//* <- [6] = users count
		].join('|')
	+	')$'
	, 'i')

,	regDrawpileImageFileName = new RegExp(
		regDrawpilePartStart
	+	regDrawpilePartID	//* <- [1] = session ID
	+	regDrawpilePartIndex	//* <- [2] = session part index
	+	'[_-](\\d+)'		//* <- [3] = image index
	+	'[_-](full|thumb)'	//* <- [4] = view/preview
	+	'[_-](\\d+)'		//* <- [5] = image width
	+	'x(\\d+)'		//* <- [6] = image height
	+	'(\\.\\w+)'		//* <- [7] = file ext
	+	regDrawpilePartEnd
	, 'i')

,	regDrawpileMetaFileName = new RegExp(
		regDrawpilePartStart
	+	regDrawpilePartID	//* <- [1] = session ID
	+	'(\\.\\w+)'		//* <- [2] = file ext
	+	regDrawpilePartEnd
	, 'i')

,	attrSort = 'data-sortable-'
,	argSortNumeric = ['size', 'time', 'mtime']
,	argSort = {
		'sort_by': 'name'
	,	'sort_order': 'ascending'
	}

,	regNum = /\d+/g
,	regNonNum = /\D+/g
,	regSlash = /[\\\/]+/g
,	regSpace = /\s+/g
,	regTrim = /^\s+|\s+$/g
,	regTrimSlash = /^[\\\/]+|[\\\/]+$/g
,	regTimeBreak = /^\d+(<|>|,|$)/
,	regSplitTime = /[^\d-]+/g
,	regSplitName = /\s+-\s+/g
,	regLastZeroes = /0+$/g

,	maxThumbWidth = 200
,	maxThumbHeight = 200

,	dprecIDinURL = (location.hash || '').replace(/#/g, '')
,	dprecMetaByID = {}

,	TOS = ['object', 'string']
,	TYMD = ['FullYear', 'Month', 'Date']
,	TYMDHMS = ['FullYear', 'Month', 'Date', 'Hours', 'Minutes', 'Seconds']

,	la, lang = document.documentElement.lang || 'en'
	;

//* UI translation *-----------------------------------------------------------

//if (LS && !(LS.lang && LS.lang == lang)) LS.lang = lang;	//* <- use user-selectable cookie instead

if (lang == 'ru') {
	la = {
		'bytes': 'байт'
	,	'go_to': 'Перейти к'
	,	'toggle': {
			'media_rows': 'Переключить вид медиафайлов'
		,	'img_newlines': 'Переключить ряды картинок одной высоты'
		,	'id_filter': 'Переключить вид'
		}
	,	'drawpile': {
			'start': 'Начало'
		,	'end': 'Конец'
		,	'restrict': 'Ограничение'
		,	'dl': 'Скачать'
		,	'dl_num_prefix': '№ '
		,	'dl_file_count': 'Записей'
		,	'dl_total_size': 'Общий вес'
		,	'size': 'Вес'
		,	'strokes': 'Черт'
		,	'session_part': 'части сессии'
		,	'screenshot': 'снимок'
		,	'screenshots_skipped': 'снимков пропущено'
		,	'index_of_total': ' из '
		,	'total': 'всего'
		,	'users': 'Участников'
		,	'users_omitted': '(ещё $1)'
		}
	};
} else {
	la = {
		'bytes': 'bytes'
	,	'go_to': 'Go to'
	,	'toggle': {
			'media_rows': 'Toggle media file view'
		,	'img_newlines': 'Toggle image rows of same height'
		,	'id_filter': 'Toggle view'
		}
	,	'drawpile': {
			'start': 'Start'
		,	'end': 'End'
		,	'restrict': 'Restrict'
		,	'dl': 'Download'
		,	'dl_num_prefix': '# '
		,	'dl_file_count': 'Rec.files'
		,	'dl_total_size': 'Total size'
		,	'size': 'Size'
		,	'strokes': 'Strokes'
		,	'session_part': 'session part'
		,	'screenshot': 'screenshot'
		,	'screenshots_skipped': 'screenshots skipped'
		,	'index_of_total': ' of '
		,	'total': 'total'
		,	'users': 'Users'
		,	'users_omitted': '($1 more)'
		}
	};
}

//* Utility functions, mostly copypasted from old projects as is *-------------

//* Create type-checking functions, e.g. "isString()" or "isImageElement()":
//* Source: https://stackoverflow.com/a/17772086
[
	'Array',	//* <- matches anything with 'Array' at the end, e.g. 'Uint8Array'
	'String',
].map(
	function (typeName) {
	var	functionName = 'is' + typeName;

		if (typeof window[functionName] !== 'function') {
			window[functionName] = function (value) {
				return (toString.call(value).slice(-1 - typeName.length, -1) === typeName);
			};
		}
	}
);

//* Variable level array flatten with recursion using reduce and concat:
//* source: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array/flat
function getFlatDeepArray(values, maxLevel) {
	if (typeof maxLevel === 'undefined') {
		maxLevel = +Infinity;
	}

	return (
		maxLevel > 0
		? values.reduce(
			function(values, value) {
				return values.concat(
					isArray(value)
					? getFlatDeepArray(value, maxLevel - 1)
					: value
				)
			}
		,	[]
		)
		: values.slice()
	);
};

function compareCaseless(a, b) {return a.toLowerCase() > b.toLowerCase() ? 1 : -1;}
function gc(n,p) {try {return Array.prototype.slice.call((p || document).getElementsByClassName(n) || []);} catch(e) {return [];}}
function gt(n,p) {try {return Array.prototype.slice.call((p || document).getElementsByTagName(n) || []);} catch(e) {return [];}}
function gn(n,p) {try {return Array.prototype.slice.call((p || document).getElementsByName(n) || []);} catch(e) {return [];}}
function id(i) {return document.getElementById(i);}
function orz(n) {return parseInt(n||0)||0;}
function hasValue(v) {return !!v;}
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

function delAllChildNodes(parent) {
	while (del(parent.lastChild));

	return parent;
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
	var	a = (values.filter ? values : [values]).filter(function(v) { return !!v; });
		if (a.length) return ' ' + name + '="' + encodeTagAttr(a.join(delim || ' ')) + '"';
	}
	return '';
}

function leftPad(n, len, pad) {
	n = String(orz(n));
	len = orz(len) || 2;
	pad = String(pad || 0);

	while (n.length < len) n = pad+n;

	return n;
}

//* Accepts a Date object or date string that is recognized by the Date.parse() method
function getWeekDayName(date) {

//* https://stackoverflow.com/a/27347503

	if (date.toLocaleString) {
	var	weekDayName = date.toLocaleString(window.navigator.language, { weekday : 'long' });

		if (
			weekDayName.indexOf(' ') < 0
		&&	weekDayName.indexOf(':') < 0
		) {
			return weekDayName;
		}
	}

//* https://stackoverflow.com/a/17964373

var	weekDayIndex = new Date(date).getDay();

	return (
		isNaN(weekDayIndex)
		? null :
		// ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
		['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
		[weekDayIndex]
	);
}

function getFormattedTimezoneOffset(t) {
	return (
		(t = (t && t.getTimezoneOffset ? t : new Date).getTimezoneOffset())
		? (t < 0 ? (t = -t, '+') : '-')+leftPad(Math.floor(t/60))+':'+leftPad(t%60)
		: 'Z'
	);
}

function getFormattedTime(t, plain, only_ymd, for_filename) {

	function getFormattedTimePart(v,i) {
		v = d['get'+v]();
		if (i == 1) ++v;

		return leftPad(v);
	}

	if (TOS.indexOf(typeof t) > -1) {
	var	text = String(t);

		if (isString(t) && Date.parse) {
			t = Date.parse(t.replace(/(T\d+)-(\d+)-(\d+\D*)/, '$1:$2:$3'));
		} else {
			t = orz(t) * 1000;
		}

		if (!t && text) return text;
	}

var	d = (
		t
		? new Date(t > 0 ? t : t + new Date)
		: new Date
	);

var	t = (only_ymd ? TYMD : TYMDHMS).map(getFormattedTimePart);
var	YMD = t.slice(0,3).join('-');
var	HIS = (only_ymd ? '' : t.slice(3).join(for_filename ? '-' : ':'));

	if (plain) {
		return (HIS ? YMD+(for_filename ? '_' : ' ')+HIS : YMD);
	}

var	tz = getFormattedTimezoneOffset(t);

	return (
		'<time datetime="'
	+		(HIS ? YMD+'T'+HIS : YMD)
	+		tz
	+	'" title="'
	+		getWeekDayName(d)+', '
	+		YMD+(HIS ? ' '+HIS : '')+', '
	+		tz
	+	'" data-t="'
	+		Math.floor(d / 1000)
	+	'">'
	+		YMD
	+		(HIS ? ' <small>'+HIS+'</small>' : '')
	+	'</time>'
	);
}

function getFileExt(path) {
	return (
		path
		.split(/\//g).pop()
		.split(/\./g).pop()
	)
}

function getFileSizeText(size) {
	return (size ?
		size.short + ' ('
	+	getFormattedNum(size.bytes) + ' ' + la.bytes + ')'
	: '');
}

function getFormattedNum(num) {
var	text = String(num)
,	funcName = 'toLocaleString'
,	result
	;

	return (
		(num = orz(num))[funcName]
	&&	(result = num[funcName]())
	&&	(text != result)
		? result
		: text.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1 ')
	);
}

function getTextOrURImatch(text, pattern) {
var	text = String(text);
	return (
		text.match(pattern)
	||	decodeURIComponent(text).match(pattern)
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

function toggleIDFilter(keep) {
	toggleClass(document.body, 'id-filter', keep);
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
var	evt = eventStop(0,1,1)
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
			,	'value': (
					argSortNumeric.indexOf(arg.sort_by) >= 0
					? orz(j)
					: j
				)
			});

			if (!tbody) {
				tbody = tr.parentNode;
			}
		}
	}

	rows.sort(
		function(a, b) {
			for (i in compareOrder) {
			var	i,k = compareOrder[i];

				if (a[k] !== b[k]) {
					return (a[k] < b[k]) ? -1 : 1;
				}
			}

			return 1;
		}
	);

	if (arg.sort_order !== 'ascending') rows.reverse();

	for (i = 0, j = rows.length; i < j; i++) if (tr = rows[i].row_e) {
		tbody.appendChild(tr);
	}
}

function updateDrawpileTable(evt) {

	function addStatsRow(userName, statsContent) {
		statsRow = cre('tr', statsContainer);
		statsRow.className = classMediaRowStatsUser;
		statsRow.innerHTML = (
			'<td colspan="2">' + userName + '</td>'
		+	'<td colspan="2">' + statsContent + '</td>'
		);
	}

var	js = (evt && evt.target ? evt.target : evt)
,	match
	;

	if (
		js
	&&	js.src
	&&	(match = js.src.match(regDrawpileMetaFileName))
	) {
	var	recID = match[1]
	,	stats = dprecMetaByID[recID]
	,	sessionContainer = id(recID)
	,	statsContainer
	,	statsSummary
	,	statsRows
		;

		if (
			stats
		&&	sessionContainer
		&&	(statsRows = gc('user', sessionContainer))
		&&	(statsSummary = statsRows[0].previousSibling)
		&&	(statsContainer = statsRows[0].parentNode)
		) {
			del(statsRows);

			if (isArray(stats)) {
			var	userNames = []
			,	statsCombined = {}
			,	statsSum = 0
				;

				stats.map(
					function(stats) {
						for (var userName in stats) {
						var	userStatValue = stats[userName];

							if (userNames.indexOf(userName) < 0) {
								userNames.push(userName);
								statsCombined[userName] = userStatValue;
							} else {
								statsCombined[userName] += userStatValue;
							}

							statsSum += userStatValue;
						}
					}
				);

			var	statsSumFields = gt('td', statsSummary);
				statsSumFields[1].textContent = userNames.length;
				statsSumFields[3].textContent = statsSum;

				userNames.sort();
				userNames.map(
					function(userName) {
						addStatsRow(userName, statsCombined[userName]);
					}
				);
			} else
			for (var userName in stats) {
				addStatsRow(userName, stats[userName]);
			}
		}
	}
}

//* Runtime *------------------------------------------------------------------

function init() {

	cre('style', document.head).textContent = '.inside .anchor::after { content: "(' + la.toggle.id_filter + ')"; }';

	gt('time').map(function(timeElement) {
	var	timeStamp = timeElement.getAttribute('data-t');
		if (timeStamp && orz(timeStamp) > 0) {
			timeElement.outerHTML = getFormattedTime(timeStamp);
		}
	});

	gc('inside').map(function(pageCenterContainer) {

		function addPathLink(text, url) {
		var	parent = pathLinkContainer || topButtonContainer || pageCenterContainer
		,	a = cre('a', parent)
			;

			a.textContent = text || url;
			a.href = url || text;
		}

		function addTopButton(text, func) {
		var	parent = topButtonContainer || pathLinkContainer || pageCenterContainer
		,	button = cre('button', parent)
			;

			button.textContent = text;
			button.onclick = func;
		}

//* Simple dir/file list sort:

	var	currentPathElement = id('path')
	,	currentPathContainer = (
			currentPathElement
			? currentPathElement.parentNode
			: pageCenterContainer.firstElementChild
		)
	,	topButtonContainer = currentPathContainer
	,	pathLinkContainer = currentPathContainer
	,	countByType = {}
	,	dirsInside = []
	,	dirsAround = []
		;

		gt('tr', pageCenterContainer).map(function(tr) {
		var	a,e,f,g,h,i,j,k,v;

			if (i = (a = gt('td', tr)).length) {
			var	sortableValues = {};

				while (i--) if (e = a[i]) {
				var	sortType = ''
				,	sortValue = ''
				,	sortRef = ''
					;

					if (sortRef = gt('a', e)[0]) {
						sortType = 'name';
						sortValue = sortRef.getAttribute('href');
					} else
					if (sortRef = gt('time', e)[0]) {
						sortType = 'mtime';
						sortValue = orz(sortRef.getAttribute('data-t'));
					} else
					if (sortRef = e.title) {
						sortType = 'size';
						sortValue = orz(sortRef);
					} else
					if (sortRef = e.textContent) {
						sortType = 'ext';
						sortValue = String(sortRef);
					}

					if (sortType) {
						sortableValues[sortType] = sortValue;
					}
				}

				if (sortableValues) {
				var	sortGroup = sortableValues.type = ('size' in sortableValues ? 'file' : 'dir');

					if (LS && sortGroup == 'dir') {
						dirsInside.push(sortableValues.name);
					}

					for (var sortType in sortableValues) {
						tr.setAttribute(attrSort + sortType, sortableValues[sortType]);
					}

					if (sortGroup in countByType) {
						countByType[sortGroup] += 1;
					} else {
						countByType[sortGroup] = 1;
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
		&&	(a = gt('th', pageCenterContainer)).length > 0
		) {
		var	k = a.length - 1
		,	headerTime = a.pop()
		,	headerName = a.shift()
		,	parent = headerName.parentNode
			;

			delAllChildNodes(parent);

			parent.appendChild(headerName);
			parent.appendChild(headerTime);

			if (k > 1) {
				headerName.setAttribute('colspan', k);
			}
		}

		if (e = id('path')) {
		var	a = (
				e.textContent
				.replace(regTrim, '')
				.replace(regTrimSlash, '')
				.split(regSlash)
			)
		,	currentPath = ''
		,	i = 0
		,	j = '/'
		,	k = a.length + 1
		,	p = e.parentNode
		,	pathLinkContainer = p
			;

			del(e);
			p.innerHTML = p.innerHTML.replace(/[\s:.,]*$/, ': ');

			e = pathLinkContainer = cre('span', p);
			e.className = classLinksChain;

			a.unshift('');

			for (; i < k; i++) {
			var	currentName = a[i] + j;
				currentPath += currentName;
				addPathLink(currentName, currentPath);
				// cre('span', pathLinkContainer).textContent = '»';
			}

			pathLinkContainer = p;

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
						cre('span', p).textContent = la.go_to + ': ';

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
	,	fileRecIDsToUpdateTable = []
	,	simpleFileTable
	,	simpleFileCount = 0
		;

		gt('a', pageCenterContainer).map(function(e) {
		var	url = e.href
		,	recID
		,	match
			;

			if (
				url
			&&	(match = getTextOrURImatch(url, regDrawpileRecordingFileName))
			&&	(recID = match[2])
			&&	fileRecIDs.indexOf(recID) < 0
			) {
				fileRecIDs.push(recID);
				if (recID === dprecIDinURL) toggleIDFilter(1);
				if (!simpleFileTable) simpleFileTable = getParentByTagName(e, 'table');
			}
		});

//* 2. Get all files by session IDs: *----/----

		if (fileRecIDs.length > 0) {
			toggleClass(pageCenterContainer, classMediaRowsEnabled, 1);

			if (canToggleView) {
				topButtonContainer = cre('div', currentPathContainer);
				addTopButton(la.toggle.media_rows, toggleMediaRows);
				addTopButton(la.toggle.img_newlines, toggleImageNewlines);
			}

		var	filesByRecID = {};

			gt('a', pageCenterContainer).map(function(e) {
			var	url = e.href
			,	recID
			,	match
				;

				if (url) {
					for (var recIndex in fileRecIDs) if (
						(recID = fileRecIDs[recIndex])
					&&	url.indexOf(recID) >= 0
					) {
					var	tr = getParentByTagName(e, 'tr')
					,	td = gt('td', tr)[0]
					,	fileName = e.textContent
					,	timeElement = gt('time', tr)[0]
					,	fileModTime = (timeElement ? timeElement.getAttribute('data-t') : '')
					,	sizeShort = ''
					,	sizeBytes = ''
						;

						while (td) {
							if (td.title) {
								sizeShort = td.textContent;
								sizeBytes = td.title;

								break;
							}

							td = td.nextElementSibling;
						}

					var	file = {
							'name': fileName
						,	'mtime': fileModTime
						,	'size': {
								'short': sizeShort
							,	'bytes': sizeBytes
							,	'num': orz(sizeBytes)
							}
						}
					,	filesByType = filesByRecID[recID] || (filesByRecID[recID] = {})
						;

						if (match = getTextOrURImatch(fileName, regDrawpileImageFileName)) {
						var	partIndex = (match[2] ? orz(match[2].replace(regNonNum, '')) : 0)
						,	imageIndex = orz(match[3])
						,	imagesByPartIndex = filesByType.img || (filesByType.img = [])
						,	imagesByImageIndex = imagesByPartIndex[partIndex] || (imagesByPartIndex[partIndex] = [])
						,	imagesBySize = imagesByImageIndex[imageIndex] || (imagesByImageIndex[imageIndex] = {})
						,	fullOrThumb = match[4]
							;

							imagesBySize[fullOrThumb] = file;

							file.partIndex = partIndex;
							file.index = imageIndex;
							file.width = orz(match[5]);
							file.height = orz(match[6]);
						} else {
							if (match = getTextOrURImatch(fileName, regDrawpileRecordingFileName)) {
							var	metaParts = (match[1] || '').split(regSplitName)
							,	timeStamps = []
								;

								for (var m_i in metaParts) {
								var	v = metaParts[m_i];

									if (match = v.match(regDrawpileRecordingMetaPart)) {
										if (v = match[1]) {
											(file.num || (file.num = {})).index = orz(v);

											if (v = match[2]) {
												file.num.parts = orz(v);
											}
										} else
										if (v = match[3]) {
											v = getFormattedTime(v, -1);

											if (timeStamps.indexOf(v) < 0) {
												timeStamps.push(v);
											}
										} else
										if (v = match[4]) {
										var	a = (file.restrict || (file.restrict = []));

											if (a.indexOf(v) < 0) {
												a.push(v);
											}
										} else
										if (v = match[5]) {
											(file.num || (file.num = {})).strokes = orz(v);
										} else
										if (v = match[6]) {
											(file.num || (file.num = {})).users = orz(v);
										}
									} else {
										file.users = (file.users || []).concat(
											v.split(', ')
										);
									}
								}

								if (timeStamps) {
								var	timeStart = 0
								,	timeEnd = 0
									;

									for (var t_i in timeStamps) {
									var	t = timeStamps[t_i];

										if (!timeStart || timeStart > t) timeStart = t;
										if (!timeEnd   || timeEnd   < t) timeEnd   = t;
									}

									file.timeInterval = {};

									if (timeStart) {
										file.timeInterval.start = timeStart;
									}

									if (timeEnd && timeEnd !== timeStart) {
										file.timeInterval.end = timeEnd;
									}
								}
							}

						var	ext = getFileExt(fileName);

							if (ext === 'js') {
							var	match = fileName.match(regDrawpileMetaFileName);

								if (match) {
								var	recID = match[1];

									if (fileRecIDsToUpdateTable.indexOf(recID) < 0) {
										fileRecIDsToUpdateTable.push(recID);
									}

								var	js = cre('script', document.head);
									js.addEventListener('load', updateDrawpileTable, false);
									js.src = file.name;
								}
							} else {
								ext = 'dl';
							}

							(filesByType[ext] || (filesByType[ext] = [])).push(file);
						}

						toggleClass(tr, classSimpleRow, 1);

						return;
					}
				}
			});

			toggleClass(simpleFileTable, classSimpleRowsContainer, 1);

			if (simpleFileTable) {
				simpleFileCount = gt('tr', simpleFileTable).filter(
					function(e) {
					var	c = e.className;
						return (
							(!c || c.indexOf(classSimpleRow) < 0)
						&&	gt('td', e).length > 0
						);
					}
				).length;

				if (simpleFileCount === 0) {
					toggleClass(simpleFileTable, classSimpleRow, 1);
				}
			}

//* 3. Make separate table with rows by session IDs: *----/----

		var	table = cre('table', pageCenterContainer)
		,	tableRows = []
		,	recID
		,	a,b,c,d,e,f,g,h,i,j,k,m,n,v
			;

			table.className = classMediaRowsContainer;

//* 3.1. Get downloads, images and metadata:

			for (recID in filesByRecID) {
			var	filesByType = filesByRecID[recID]
			,	fileIndexFromOne = true
			,	start = ''
			,	end = ''
			,	strokes = 0
			,	users = 0
			,	metaLists = {
					'restrict': []
				,	'users': []
				}
			,	downloadSortOrder = ['index', 'time', 'ext', 'size']
			,	downloads = (
					(filesByType.dl || [])
					.filter(hasValue)
					.map(
						function(file) {
						var	i,j,k,n;

							for (k in metaLists) {
								if (j = file[k]) {
									for (i in j) if (
										(n = j[i])
									&&	metaLists[k].indexOf(n) < 0
									) {
										metaLists[k].push(n);
									}
								}
							}

							if (j = file.timeInterval) {
								if ((k = j.start) && (fileTime = k) && (!start || start > k)) start = k;
								if ((k = j.end  ) && (fileTime = k) && (!end   || end   < k)) end = k;
							}

							if (j = file.num) {
								if (k = j.index) fileIndex = k;
								if ((k = j.strokes) && strokes < k) strokes = k;
								if ((k = j.users  ) && users   < k) users = k;
							}

						var	fileName = file.name
						,	fileExt = getFileExt(fileName)
						,	fileTime = fileTime || file.mtime
						,	fileIndex = fileIndex || orz(
								fileName
								.substr(fileName.lastIndexOf(recID) + recID.length)
								.replace(fileExt, '')
								.replace(regNonNum, '')
							)
						,	downloadLink = (
								'<a href="'
							+		fileName
							+	'" title="'
							+		fileName
							+	'" target="_blank" rel="nofollow">'
							+		fileExt
							+	'</a>'
							);

							if (fileIndex === 1) {
								fileIndexFromOne = false;
							}

							return {
								'ext': fileExt
							,	'time': fileTime
							,	'index': fileIndex
							,	'size': (file.size ? file.size.num : 0)
							,	'info': (file.size ? file.size.short : '')
							,	'hint': getFileSizeText(file.size)
							,	'link': downloadLink
							};
						}
					).sort(
						function(a, b) {
							for (var i in downloadSortOrder) {
							var	k = downloadSortOrder[i]
							,	c = a[k]
							,	d = b[k]
								;

								if (c !== d) {
									return c > d ? 1 : -1;
								}
							}

							return 0;
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
			,	imageFiles = getFlatDeepArray(
					filesByType.img || []
				).filter(
					function(file) {
						return !!(file && (file.full || file.thumb));
					}
				)
			,	imageCount = imageFiles.length
			,	imagesHTMLParts = imageFiles.map(
					function(file, imageIndex) {
					var	full = file.full || file.thumb
					,	thumb = file.thumb || file.full
					,	imageTotalIndex = imageIndex + 1
						;

						if (
							imageTotalIndex > 5
						&&	imageTotalIndex < imageCount
						&&	(
								imageTotalIndex < 10
							||	String(imageTotalIndex).replace(regLastZeroes, '').length > 1
							)
						) {
							return;
						}

					var	meta = (
							la.drawpile.screenshot + ' '
						+	full.index
						) + (
							!full.partIndex
							? '' :
							la.drawpile.index_of_total
						+	la.drawpile.session_part + ' '
						+	la.drawpile.dl_num_prefix
						+	full.partIndex
						+	la.drawpile.index_of_total
						+	downloads.length + ', '
						+	la.drawpile.total + ' '
						+	imageTotalIndex
						) + (
							la.drawpile.index_of_total
						+	imageCount + ' - '
						+	full.width + 'x'
						+	full.height + ', '
						+	getFileSizeText(full.size)
						)
					,	skipPlaceHolder = (
							imageIndex > 0
						||	imageCount <= 2
							? '' : (
								'<a href="#'
							+		recID
							+	'" class="media-row-img-skip" onclick="toggleIDFilter()">'
							+		(imageCount - 2)
							+		la.drawpile.index_of_total
							+		imageCount
							+		'<br>'
							+		la.drawpile.screenshots_skipped.replace(/\s+/g, '<br>')
							+	'</a>'
							)
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
						+	skipPlaceHolder
						);
					}
				).filter(hasValue)

//* 3.2. Get row metadata fields:

			,	userNames = metaLists.users.sort(compareCaseless)
			,	rowID = {
					'head': 1
				,	'sortable': {'id': recID}
				,	'tabs': [
						'<a href="#'
					+		recID
					+	'" class="anchor" onclick="toggleIDFilter()">'
					+		recID
					+	'</a>'
					]
				}
			,	rowTimeStart = (start ? {
					'sortable': {'start': start}
				,	'tabs': [
						la.drawpile.start + ':'
					,	{'tip': start, 'html': getFormattedTime(start)}
					]
				} : null)
			,	rowTimeEnd = (end ? {
					'sortable': {'end': end}
				,	'tabs': [
						la.drawpile.end + ':'
					,	{'tip': end, 'html': getFormattedTime(end)}
					]
				} : null)
			,	rowRestrict = (
					metaLists.restrict.length > 0
				&&	(
						k = 0
					,	v = metaLists.restrict.map(
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
					'sortable': {'restrict': v}
				,	'tabs': [
						la.drawpile.restrict + ':'
					,	v
					]
				} : null)
			,	downloadsTotalSize = downloads.reduce(
					function(sum, file) {
						return sum + file.size;
					}
				,	0
				)
			,	rowDownloadCount = (
					downloadsTotalSize > 0
				||	downloads.length > 0
				? {
					'sortable': {
						'files': downloads.length,
						'bytes': downloadsTotalSize,
					}
				,	'tabs': [
						la.drawpile.dl_file_count + ':'
					,	downloads.length
					,	la.drawpile.dl_total_size + ':'
					,	getFormattedNum(downloadsTotalSize) + ' ' + la.bytes
					]
				} : null)
			,	rowDownloadList = downloads.map(
					function(file) {
						return {
							'class': classMediaRowStatsDL
						,	'tabs': [
								file.link
							,	la.drawpile.dl_num_prefix + (
									fileIndexFromOne
									? (file.index || 1)
									: file.index
								)
							,	{
									'tip': file.hint
								,	'html': file.info
								}
							// ,	file.time.split(regSplitTime)[0]
							,	getFormattedTime(file.time)
							]
						};
					}
				)
			,	rowUserCount = (
					users > 0
				||	strokes > 0
				? {
					'sortable': {
						'users': users,
						'strokes': strokes,
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
			,	rowUserList = (
					fileRecIDsToUpdateTable.indexOf(recID) >= 0
					? '' :
					userNames.map(
						function(line) {
						var	match = line.match(regDrawpileRecordingUserName)
						,	name = (match ? match[1] : name)
						,	stat = (match ? orz(match[2]) : 0)
							;

							usersLeft--;
							strokesLeft -= stat;

							return {
								'class': classMediaRowStatsUser
							,	'tabs': [name, stat]
							};
						}
					)
				)

//* 3.3. Get row metadata table rows:

			,	dataRows = [
				,	rowID
				,	rowTimeStart
				,	rowTimeEnd
				,	rowRestrict
				,	rowDownloadCount
				]
				.concat(rowDownloadList)
				.concat([
					rowUserCount
				])
				.concat(rowUserList)
				.concat(
					usersLeft || strokesLeft
					? [
						{
							'class': classMediaRowStatsUser
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
			,	fileSortableValues = {}
			,	dataRows = dataRows.map(
					function(row) {
					var	className = getTagAttrIfNotEmpty('class', row['class'])
					,	tip = getTagAttrIfNotEmpty('title', row.tip)
					,	lines = row.lines
					,	tabs = row.tabs.filter(hasValue)
					,	rowSortableValues = row.sortable
						;

						if (rowSortableValues) for (key in rowSortableValues) {
							fileSortableValues[key] = rowSortableValues[key];
						}

						if (tabs && (i = tabs.length) > 0) {
						var	tagName = (row.head ? 'th' : 'td')
						,	i
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
							'<tr' + className + tip + '>'
						+		tabs.join('')
						+	'</tr>'
						) : '';
					}
				).filter(hasValue)
				;

//* 3.4. Get media table row with all relevant files:

				tableRows.push({
					'id': recID
				,	'sort_key': tableRowName
				,	'sortable': fileSortableValues
				,	'html': (
						'<table class="' + classMediaRowInfoTable + '">'
					+		dataRows.join('')
					+	'</table>'
					+	'<span class="' + classMediaRowImages + '">'
					+		imagesHTMLParts.join('')
					+	'</span>'
					)
				});
			}

//* 3.4. Add rows to media table:

		var	compareOrder = ['sort_key', 'id', 'html'];

			tableRows.sort(
				function(a, b) {
					for (i in compareOrder) {
					var	i,k = compareOrder[i];
						if (a[k] !== b[k]) return (a[k] < b[k]) ? -1 : 1;
					}

					return 1;
				}
			);

			tableRows.map(
				function(row) {
				var	tr = cre('tr', table)
				,	td = cre('td', tr)
				,	fileSortableValues = row.sortable
					;

					for (var key in fileSortableValues) {
						tr.setAttribute(attrSort + key, fileSortableValues[key]);
					}

					tr.id = row.id;
					tr.className = classMediaRow;
					td.innerHTML = row.html;
				}
			);
		}
	});

//* END Drawpile sessions

	toggleClass(document.documentElement, classPageLoading, -1);
}

toggleClass(document.documentElement, classPageLoading, 1);

window.addEventListener('load', init, false);
