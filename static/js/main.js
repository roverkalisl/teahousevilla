document.addEventListener("DOMContentLoaded", function () {
  initSmoothScroll();
  initMobileNav();
  initHeroSlider();
  initGalleryFilter();
  initInquiryDates();
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
        cell.style.display = show ? "" : "none";
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
