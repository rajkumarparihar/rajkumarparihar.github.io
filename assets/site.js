(function () {
  var toggle = document.querySelector("[data-nav-toggle]");
  var nav = document.querySelector("[data-nav]");
  if (toggle && nav) {
    function setOpen(open) {
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.textContent = open ? "Close" : "Menu";
    }
    toggle.addEventListener("click", function () {
      setOpen(!nav.classList.contains("is-open"));
    });
    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        setOpen(false);
      });
    });
  }

  var links = document.querySelectorAll("[data-spy]");
  var sections = [];
  links.forEach(function (link) {
    var id = link.getAttribute("href");
    if (!id || id.charAt(0) !== "#") return;
    var section = document.querySelector(id);
    if (section) sections.push({ link: link, section: section });
  });

  if (sections.length && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          sections.forEach(function (item) {
            item.link.classList.toggle("is-current", item.section === entry.target);
          });
        });
      },
      { rootMargin: "-40% 0px -50% 0px", threshold: 0 }
    );
    sections.forEach(function (item) {
      observer.observe(item.section);
    });
  }
})();
