
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
function leftPad(n) {n = orz(n); return n > 9 || n < 0?n:'0'+n;}
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

function getFormattedTimezoneOffset(t) {
	return (
		(t = (t && t.getTimezoneOffset ? t : new Date()).getTimezoneOffset())
		? (t < 0?(t = -t, '+'):'-')+leftPad(Math.floor(t/splitSec))+':'+leftPad(t%splitSec)
		: 'Z'
	);
}

function getFormattedTime(t, plain, only_ymd) {
	if (TOS.indexOf(typeof t) > -1) t = orz(t)*1000;
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
