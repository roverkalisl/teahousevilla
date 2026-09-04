document.addEventListener("DOMContentLoaded", function () {
  initSmoothScroll();
  initMobileNav();
  initHeroSlider();
  initGalleryFilter();
  initInquiryDates();
  initScrolledNav();
  initReveals();
  initLightbox();
});

function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(function (link) {
    link.addEventListener("click", function (e) {
      var target = document.querySelector(link.getAttribute("href"));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth" });
      }
    });
  });
}

function initMobileNav() {
  var toggle = document.getElementById("navToggle");
  var menu = document.getElementById("mobileNav");
  if (!toggle || !menu) return;
  toggle.addEventListener("click", function () {
    var isOpen = !menu.classList.contains("hidden");
    menu.classList.toggle("hidden");
    menu.classList.toggle("flex");
    toggle.setAttribute("aria-expanded", String(!isOpen));
  });
  menu.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      menu.classList.add("hidden");
      menu.classList.remove("flex");
      toggle.setAttribute("aria-expanded", "false");
    });
  });
}

function initScrolledNav() {
  var nav = document.getElementById("siteNav");
  if (!nav) return;
  var update = function () { nav.classList.toggle("is-scrolled", window.scrollY > 24); };
  update();
  window.addEventListener("scroll", update, { passive: true });
}

function initReveals() {
  var items = document.querySelectorAll(".reveal");
  if (!items.length || !("IntersectionObserver" in window)) {
    items.forEach(function (item) { item.classList.add("is-visible"); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) { entry.target.classList.add("is-visible"); observer.unobserve(entry.target); }
    });
  }, { threshold: 0.12 });
  items.forEach(function (item) { observer.observe(item); });
}

function initLightbox() {
  var cells = document.querySelectorAll("[data-lightbox-src]");
  if (!cells.length) return;
  var box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.innerHTML = '<button class="lightbox-close" type="button" aria-label="Close image">&times;</button><img alt="">';
  document.body.appendChild(box);
  var image = box.querySelector("img");
  var close = function () { box.classList.remove("is-open"); document.body.style.overflow = ""; };
  cells.forEach(function (cell) {
    cell.addEventListener("click", function () {
      image.src = cell.getAttribute("data-lightbox-src");
      image.alt = cell.getAttribute("data-lightbox-alt") || "";
      box.classList.add("is-open");
      document.body.style.overflow = "hidden";
    });
  });
  box.querySelector(".lightbox-close").addEventListener("click", close);
  box.addEventListener("click", function (event) { if (event.target === box) close(); });
  document.addEventListener("keydown", function (event) { if (event.key === "Escape") close(); });
}

function initHeroSlider() {
  var slides = document.querySelectorAll(".hero-slide");
  if (slides.length <= 1) return;
  var index = 0;
  setInterval(function () {
    slides[index].classList.remove("is-active");
    index = (index + 1) % slides.length;
    slides[index].classList.add("is-active");
  }, 5000);
}

function initGalleryFilter() {
  var buttons = document.querySelectorAll("#galleryFilters button");
  var cells = document.querySelectorAll(".gallery-cell");
  if (!buttons.length) return;
  buttons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      buttons.forEach(function (b) { b.classList.remove("bg-forest", "text-white"); });
      btn.classList.add("bg-forest", "text-white");
      var filter = btn.getAttribute("data-filter");
      cells.forEach(function (cell) {
        var show = filter === "all" || cell.getAttribute("data-category") === filter;
        cell.classList.toggle("is-hidden", !show);
      });
    });
  });
}

function initInquiryDates() {
  var checkIn = document.getElementById("id_check_in");
  var checkOut = document.getElementById("id_check_out");
  if (!checkIn || !checkOut) return;
  var today = new Date().toISOString().split("T")[0];
  checkIn.setAttribute("min", today);
  checkOut.setAttribute("min", checkIn.value || today);
  checkIn.addEventListener("change", function () {
    checkOut.setAttribute("min", checkIn.value);
  });
}
