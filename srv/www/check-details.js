
if ('HTMLDetailsElement' in window);
else (function(){

	function addClassName(e, nameToAdd) {
		e.className = (
			e.className
			? e.className + ' ' + nameToAdd
			: nameToAdd
		);
	}

var	checkClassName = 'check-details';

	addClassName(document.documentElement, checkClassName);

	window.onload = function addClickOnSummary(evt) {
	var	a = document.getElementsByTagName('summary');
	var	i = a.length;

		while (i--) {
		var	e = a[i];

			if (e && typeof e === 'object') {
			var	parent = e.parentNode;

				if (parent && typeof parent === 'object') {
					if ('open' in parent) {
						break;
					} else {
					var	checkbox = document.createElement('input');
					var	forId = checkbox.id = checkClassName + '_' + i;
						checkbox.type = 'checkbox';

						parent.insertBefore(checkbox, e);

						e.outerHTML = e.outerHTML.replace(/^(<)(\w+)|(\w+)(>)$/g, '$1label$4');
						e = checkbox.nextSibling;
						e.setAttribute('for', forId);

						// addClassName(e, 'toggle');
					}
				}
			}
		}
	};
})();
