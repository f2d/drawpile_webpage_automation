
if ('HTMLDetailsElement' in window);
else {
var	script = document.createElement('script');
	script.src = '../check-details.js';
	document.head.appendChild(script);
}

var	regSpace = /\s+/g
,	regTrim = /^\s+|\s+$/g
,	regTimeBreak = /^\d+(<|>|,|$)/
,	openClass = 'open'
,	splitSec = 60
,	TOS = ['object','string']
	;

//* Utility functions *--------------------------------------------------------

function gc(n,p) {try {return TOS.slice.call((p || document).getElementsByClassName(n) || []);} catch(e) {return [];}}
function gn(n,p) {try {return TOS.slice.call((p || document).getElementsByTagName(n) || []);} catch(e) {return [];}}
function id(i) {return document.getElementById(i);}
function orz(n) {return parseInt(n||0)||0;}
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
		var weekDayName = date.toLocaleString(window.navigator.language, { weekday : 'long' });

		if (
			weekDayName.indexOf(' ') < 0
		&&	weekDayName.indexOf(':') < 0
		) {
			return weekDayName;
		}
	}

//* https://stackoverflow.com/a/17964373

	var weekDayIndex = new Date(date).getDay();

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
	if (TOS.indexOf(typeof t) > -1) {
		t = orz(t) * 1000;
	}

	var d = (
		t
		? new Date(t > 0 ? t : t + new Date)
		: new Date
	);

	var t = (
		('FullYear,Month,Date'+(only_ymd ? '' : ',Hours,Minutes,Seconds'))
		.split(',')
		.map(
			function(v,i) {
				v = d['get'+v]();
				if (i == 1) ++v;

				return leftPad(v);
			}
		)
	);

	var YMD = t.slice(0,3).join('-');
	var HIS = (only_ymd ? '' : t.slice(3).join(for_filename ? '-' : ':'));

	if (plain) {
		return (HIS ? YMD+(for_filename ? '_' : ' ')+HIS : YMD);
	}

	var tz = getFormattedTimezoneOffset(t);

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

function toggleClass(e,c,keep) {
var	k = 'className'
,	old = e[k]
,	a = (old ? old.split(regSpace) : [])
,	i = a.indexOf(c)
	;
	if (i < 0) {
		if (!(keep < 0)) a.push(c);
	} else {
		if (!(keep > 0)) a.splice(i, 1);
	}
	if (a.length) e[k] = a.join(' ');
	else if (old) e[k] = '', e.removeAttribute(k);
}

//* Specific functions *-------------------------------------------------------

function toggle(e) {
	toggleClass(e, openClass);
}

//* Runtime *------------------------------------------------------------------

window.addEventListener('load', function() {
	gn('time').map(function(e) {
	var	t = e.getAttribute('data-t');
		if (t && t > 0) e.outerHTML = getFormattedTime(t);
	});
}, false);
