(function () {
  function initAccordion() {
    document.querySelectorAll(".fg-antrag-item__toggle").forEach(function (button) {
      button.addEventListener("click", function () {
        var expanded = button.getAttribute("aria-expanded") === "true";
        var content = button.parentElement.querySelector(".fg-antrag-item__content");
        button.setAttribute("aria-expanded", expanded ? "false" : "true");
        if (content) {
          content.hidden = expanded;
        }
      });
    });
  }

  function initFilter() {
    var filters = document.querySelectorAll(".fg-antraege-filter");
    var items = document.querySelectorAll(".fg-antrag-item");
    filters.forEach(function (filter) {
      filter.addEventListener("click", function () {
        var selected = filter.getAttribute("data-filter");
        filters.forEach(function (btn) {
          btn.classList.remove("is-active");
        });
        filter.classList.add("is-active");

        items.forEach(function (item) {
          var status = item.getAttribute("data-status");
          item.style.display = selected === "alle" || selected === status ? "" : "none";
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initAccordion();
    initFilter();
  });
})();
