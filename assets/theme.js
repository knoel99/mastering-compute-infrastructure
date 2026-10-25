(function () {
  var KEY = "mci-theme";
  var TOC_KEY = "mci-sommaire";
  var root = document.documentElement;

  function read(name) {
    try {
      return localStorage.getItem(name);
    } catch (err) {
      return null;
    }
  }

  function store(name, value) {
    try {
      if (value === null) localStorage.removeItem(name);
      else localStorage.setItem(name, value);
    } catch (err) {}
  }

  function systemDark() {
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
  }

  function chosen() {
    var saved = read(KEY);
    if (saved === "dark" || saved === "light") return saved;
    return systemDark() ? "dark" : "light";
  }

  function applyTheme(theme, persist) {
    root.setAttribute("data-theme", theme);
    if (persist) store(KEY, theme);
    var button = document.getElementById("theme-toggle");
    if (!button) return;
    var dark = theme === "dark";
    button.setAttribute("aria-pressed", dark ? "true" : "false");
    button.setAttribute("aria-label", dark ? "Passer au thème clair" : "Passer au thème sombre");
  }

  function headingText(node) {
    var copy = node.cloneNode(true);
    copy.querySelectorAll(".katex-mathml").forEach(function (el) { el.remove(); });
    return copy.textContent.replace(/\s+/g, " ").trim();
  }

  function buildToc(main, nav) {
    var heads = Array.prototype.filter.call(main.querySelectorAll("h2, h3"), function (node) {
      return !node.closest("#title-block-header");
    });
    nav.textContent = "";
    if (!heads.length) return [];
    var bar = document.createElement("div");
    bar.className = "sidetoc-head";
    var title = document.createElement("p");
    title.className = "sidetoc-title";
    title.textContent = "Sommaire";
    var close = document.createElement("button");
    close.type = "button";
    close.className = "sidetoc-close";
    close.textContent = "Fermer";
    bar.appendChild(title);
    bar.appendChild(close);
    nav.appendChild(bar);
    var list = document.createElement("ol");
    list.className = "sidetoc-list";
    var items = [];
    var current = null;
    heads.forEach(function (node, index) {
      if (!node.id) node.id = "partie-" + index;
      var link = document.createElement("a");
      link.href = "#" + node.id;
      link.textContent = headingText(node);
      var item = document.createElement("li");
      item.className = node.tagName === "H2" ? "lvl2" : "lvl3";
      item.appendChild(link);
      if (node.tagName === "H2" || !current) {
        list.appendChild(item);
        if (node.tagName === "H2") current = item;
      } else {
        if (!current.sublist) {
          current.sublist = document.createElement("ol");
          current.sublist.className = "sidetoc-sub";
          current.appendChild(current.sublist);
        }
        current.sublist.appendChild(item);
      }
      items.push({ node: node, link: link, parent: node.tagName === "H2" ? item : current });
    });
    nav.appendChild(list);
    var top = document.createElement("a");
    top.className = "sidetoc-top";
    top.href = "#main";
    top.textContent = "Haut de page";
    nav.appendChild(top);
    return items;
  }

  function setupToc() {
    var main = document.getElementById("main");
    var nav = document.getElementById("sidetoc");
    var toggle = document.getElementById("toc-toggle");
    if (!main || !nav) return;
    var items = buildToc(main, nav);
    if (!items.length) {
      root.classList.add("no-sidetoc");
      if (toggle) toggle.hidden = true;
      return;
    }
    root.classList.add("has-sidetoc");
    var wide = window.matchMedia("(min-width: 70rem)");
    var backdrop = document.createElement("div");
    backdrop.className = "toc-backdrop";
    document.body.appendChild(backdrop);
    if (read(TOC_KEY) === "1") root.classList.add("toc-hidden");

    function isOpen() {
      return wide.matches ? !root.classList.contains("toc-hidden") : root.classList.contains("toc-open");
    }

    function sync() {
      if (toggle) toggle.setAttribute("aria-expanded", isOpen() ? "true" : "false");
    }

    function shut() {
      root.classList.remove("toc-open");
      sync();
    }

    sync();
    if (toggle) {
      toggle.addEventListener("click", function () {
        if (wide.matches) {
          var hidden = root.classList.toggle("toc-hidden");
          store(TOC_KEY, hidden ? "1" : null);
        } else {
          root.classList.toggle("toc-open");
        }
        sync();
      });
    }
    backdrop.addEventListener("click", shut);
    var closer = nav.querySelector(".sidetoc-close");
    if (closer) closer.addEventListener("click", shut);
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") shut();
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a") && !wide.matches) shut();
    });
    if (wide.addEventListener) wide.addEventListener("change", shut);

    var active = null;
    var frame = false;
    function mark() {
      frame = false;
      var line = window.innerHeight * 0.3;
      var found = null;
      items.forEach(function (item) {
        if (item.node.getBoundingClientRect().top <= line) found = item;
      });
      if (found === active) return;
      if (active) {
        active.link.classList.remove("active");
        active.link.removeAttribute("aria-current");
        if (active.parent) active.parent.classList.remove("open");
      }
      active = found;
      if (!found) return;
      found.link.classList.add("active");
      found.link.setAttribute("aria-current", "location");
      if (found.parent) found.parent.classList.add("open");
      var label = document.getElementById("tb-title");
      if (label) label.textContent = headingText(found.node);
    }
    window.addEventListener("scroll", function () {
      if (!frame) {
        frame = true;
        window.requestAnimationFrame(mark);
      }
    }, { passive: true });
    mark();
  }

  function mount() {
    applyTheme(chosen(), false);
    var theme = document.getElementById("theme-toggle");
    if (theme) {
      theme.addEventListener("click", function () {
        applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark", true);
      });
    }
    setupToc();
    document.querySelectorAll("main table").forEach(function (table) {
      if (table.closest(".tbl-wrap")) return;
      var wrap = document.createElement("div");
      wrap.className = "tbl-wrap";
      table.parentNode.insertBefore(wrap, table);
      wrap.appendChild(table);
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount);
  else mount();

  if (window.matchMedia) {
    var query = window.matchMedia("(prefers-color-scheme: dark)");
    var onChange = function () {
      var saved = read(KEY);
      if (saved !== "dark" && saved !== "light") applyTheme(chosen(), false);
    };
    if (query.addEventListener) query.addEventListener("change", onChange);
  }
})();
