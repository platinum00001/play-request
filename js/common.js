/* Shared page behaviour: menu, contact, social, data URLs, footer year. */
(function () {
  const PR = (window.PR = window.PR || {});
  const ICONS = {
    instagram: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.2c3.2 0 3.6 0 4.8.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 3.9 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zm0 4.8a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4zM17.2 5.6a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z"/></svg>',
    facebook: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M24 12a12 12 0 1 0-13.9 11.9v-8.4H7.1V12h3V9.4c0-3 1.8-4.7 4.5-4.7 1.3 0 2.7.2 2.7.2v3h-1.5c-1.5 0-2 .9-2 1.9V12h3.4l-.5 3.5h-2.9v8.4A12 12 0 0 0 24 12z"/></svg>',
    x: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18.9 1.2h3.7l-8 9.2 9.4 12.4h-7.4l-5.8-7.6-6.6 7.6H.5l8.6-9.8L0 1.2h7.6l5.2 6.9 6.1-6.9zm-1.3 19.5h2L6.5 3.2H4.3l13.3 17.5z"/></svg>'
  };
  const NAMES = { instagram: "Instagram", facebook: "Facebook", x: "X" };
  PR.cfg = function () { return window.PR_CONFIG || {}; };
  PR.esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; });
  };
  PR.email = function () { return (PR.cfg().CONTACT_EMAIL || "").trim(); };
  PR.pageURL = function (page) { return new URL(page, location.href).href.split("#")[0].split("?")[0]; };
  PR.dataUrl = function (file) {
    const root = document.body && document.body.getAttribute("data-root");
    return new URL((root || "./") + "data/" + file, location.href).href;
  };
  PR.socialHTML = function () {
    const s = (PR.cfg().SOCIAL) || {};
    return Object.keys(NAMES).map(function (k) {
      return s[k]
        ? '<a href="' + PR.esc(s[k]) + '" target="_blank" rel="noopener">' + ICONS[k] + NAMES[k] + "</a>"
        : '<span title="Account coming soon">' + ICONS[k] + NAMES[k] + " · soon</span>";
    }).join("");
  };
  document.addEventListener("DOMContentLoaded", function () {
    const btn = document.querySelector(".burger"), menu = document.getElementById("site-nav");
    if (btn && menu) btn.addEventListener("click", function () {
      const open = menu.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.classList.toggle("nav-open", open);
    });
    const email = PR.email();
    document.querySelectorAll("[data-email]").forEach(function (a) {
      if (!email) { a.hidden = true; return; }
      if (a.tagName === "A") a.href = "mailto:" + email + (a.dataset.subject ? "?subject=" + encodeURIComponent(a.dataset.subject) : "");
      if (!a.hasAttribute("data-keep-text")) a.textContent = email;
    });
    document.querySelectorAll("[data-social]").forEach(function (el) { el.innerHTML = PR.socialHTML(); });
    document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
    try {
      const signedIn = Object.keys(localStorage).some(function (k) { return /^sb-.*-auth-token$/.test(k); });
      if (signedIn) document.querySelectorAll("[data-account-link]").forEach(function (a) { a.textContent = "My account"; });
    } catch (e) {}
  });
})();
