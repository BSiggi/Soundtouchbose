(function () {
	'use strict';

	function initFilters() {
		var wrappers = document.querySelectorAll('.fg-antraege-list-wrapper');
		if (!wrappers.length) {
			return;
		}

		wrappers.forEach(function (wrapper) {
			var buttons = wrapper.querySelectorAll('.fg-antraege-filter__btn');
			var items = wrapper.querySelectorAll('.fg-antrag-item');

			buttons.forEach(function (button) {
				button.addEventListener('click', function () {
					var filter = button.getAttribute('data-filter');
					buttons.forEach(function (inner) {
						inner.classList.remove('is-active');
					});
					button.classList.add('is-active');
					items.forEach(function (item) {
						var status = item.getAttribute('data-status');
						item.style.display = filter === 'alle' || filter === status ? '' : 'none';
					});
				});
			});
		});
	}

	function initAccordion() {
		var toggles = document.querySelectorAll('.fg-antrag-item__toggle');
		if (!toggles.length) {
			return;
		}

		toggles.forEach(function (toggle) {
			toggle.addEventListener('click', function () {
				var parent = toggle.closest('.fg-antrag-item');
				if (parent) {
					parent.classList.toggle('is-open');
				}
			});
		});
	}

	document.addEventListener('DOMContentLoaded', function () {
		initFilters();
		initAccordion();
	});
})();
