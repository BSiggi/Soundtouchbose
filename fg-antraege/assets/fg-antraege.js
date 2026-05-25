/**
 * FG Anträge – Frontend JavaScript
 * Handles accordion toggle and filter buttons for [fg_antraege_liste].
 */

(function () {
    'use strict';

    /**
     * Initialise accordion and filter functionality inside a liste wrapper.
     *
     * @param {HTMLElement} liste - The .fg-antraege-liste root element.
     */
    function initListe(liste) {
        var filterBtns = liste.querySelectorAll('.fg-antraege-filter-btn');
        var items      = liste.querySelectorAll('.fg-antraege-item');

        /* ---- Filter buttons ---- */
        filterBtns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                var filter = btn.getAttribute('data-filter');

                /* Update active state */
                filterBtns.forEach(function (b) {
                    b.classList.remove('active');
                });
                btn.classList.add('active');

                /* Show / hide items */
                items.forEach(function (item) {
                    if (filter === 'alle' || item.getAttribute('data-status') === filter) {
                        item.classList.remove('is-hidden');
                    } else {
                        item.classList.add('is-hidden');
                        /* Also close hidden items */
                        item.classList.remove('is-open');
                    }
                });
            });
        });

        /* ---- Accordion headers ---- */
        items.forEach(function (item) {
            var header = item.querySelector('.fg-antraege-item-header');
            if (!header) {
                return;
            }
            header.addEventListener('click', function () {
                item.classList.toggle('is-open');
            });
        });
    }

    /* ---- Boot ---- */
    function init() {
        var listen = document.querySelectorAll('.fg-antraege-liste');
        listen.forEach(function (liste) {
            initListe(liste);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
}());
