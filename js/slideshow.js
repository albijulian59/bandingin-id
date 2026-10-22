/* Slide show di beranda. Slide 1 = hero (sudah ada di index.html), slide berikutnya = produk unggulan
   per kategori (Situs.daftarUnggulan di js/common.js). Tanpa library. */
(function () {
  var S = window.Situs;
  var root = document.getElementById("slideshow");
  var track = document.getElementById("hs-track");
  if (!root || !track || !S) return;
  var elDots = document.getElementById("hs-dots");
  var elKontrol = document.getElementById("hs-kontrol");
  var btnPrev = document.getElementById("hs-prev");
  var btnNext = document.getElementById("hs-next");
  var JEDA_MS = 5000;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function slideProduk(u) {
    var p = u.produk, link = "review.html?id=" + encodeURIComponent(p.id), s = S.linkShopee(p);
    var img = S.gambar(p, true, false).replace('loading="lazy"', 'loading="eager"');
    return '<div class="hs-slide hs-produk" role="group" aria-roledescription="slide">' +
      '<a class="hs-img" href="' + link + '" tabindex="-1" aria-hidden="true">' + img + "</a>" +
      '<div class="hs-info">' +
        '<p class="hs-kicker">' + u.ikon + " Pilihan teratas " + S.esc(u.kategori) + "</p>" +
        '<span class="hs-cat">' + S.esc(p.jenisNama || p.kategori) + "</span>" +
        '<h2 class="hs-judul"><a href="' + link + '" title="' + S.esc(p.nama) + '">' + S.esc(S.judulPendek(p.nama)) + "</a></h2>" +
        '<p class="hs-harga"><b>' + S.esc(S.rupiah(p.harga)) + "</b>" +
          (p.hargaAsli ? " <s>" + S.esc(S.rupiah(p.hargaAsli)) + "</s>" : "") +
          (p.diskon ? ' <span class="hs-diskon">-' + p.diskon + "%</span>" : "") + "</p>" +
        '<p class="hs-meta">' + S.bintang(p.rating) +
          (p.terjual != null ? '<span class="hs-sold">' + S.esc(S.terjualTeks(p)) + " terjual/bln</span>" : "") + "</p>" +
        '<div class="hs-btns"><a class="hs-btn hs-btn-review" href="' + link + '">Baca review</a>' +
          (s ? '<a class="hs-btn hs-btn-shopee" href="' + S.esc(s) + '" ' + S.REL + ">Cek Harga di Shopee</a>" : "") +
        "</div>" +
      "</div></div>";
  }

  track.insertAdjacentHTML("beforeend", S.daftarUnggulan().map(slideProduk).join(""));
  var slides = [].slice.call(track.querySelectorAll(".hs-slide"));
  var n = slides.length;
  if (n < 2) return;

  var aktif = 0, timer = null, dijeda = reduce, hover = false, fokus = false;
  elKontrol.hidden = false;
  root.classList.add("hs-siap");
  elDots.innerHTML = slides.map(function (sl, i) {
    var nama = i === 0 ? "Beranda" : sl.querySelector(".hs-kicker").textContent.replace(/^\S+\s/, "");
    sl.setAttribute("aria-label", (i + 1) + " dari " + n + ": " + nama);
    return '<button type="button" class="hs-dot" aria-label="Slide ' + (i + 1) + ": " + S.esc(nama) + '"></button>';
  }).join("");
  var dots = [].slice.call(elDots.querySelectorAll(".hs-dot"));

  function tampil(i, dariUser) {
    aktif = (i + n) % n;
    track.style.transform = "translateX(" + (-100 * aktif) + "%)";
    slides.forEach(function (sl, j) {
      var on = j === aktif;
      sl.setAttribute("aria-hidden", on ? "false" : "true");
      if (on) sl.removeAttribute("inert"); else sl.setAttribute("inert", "");
    });
    dots.forEach(function (d, j) {
      if (j === aktif) d.setAttribute("aria-current", "true"); else d.removeAttribute("aria-current");
    });
    if (dariUser) mulai();
  }
  function jalan() { return !dijeda && !hover && !fokus && !document.hidden; }
  function mulai() {
    clearInterval(timer); timer = null;
    if (jalan()) timer = setInterval(function () { tampil(aktif + 1); }, JEDA_MS);
    // Saat berputar otomatis, pembaca layar tidak diberi tahu tiap pergantian slide
    track.setAttribute("aria-live", timer ? "off" : "polite");
    root.classList.toggle("hs-jalan", !!timer);
  }

  btnPrev.addEventListener("click", function () { tampil(aktif - 1, true); });
  btnNext.addEventListener("click", function () { tampil(aktif + 1, true); });
  dots.forEach(function (d, i) { d.addEventListener("click", function () { tampil(i, true); }); });
  root.addEventListener("keydown", function (e) {
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (e.key === "ArrowLeft") { e.preventDefault(); tampil(aktif - 1, true); }
    else if (e.key === "ArrowRight") { e.preventDefault(); tampil(aktif + 1, true); }
  });
  root.addEventListener("mouseenter", function () { hover = true; mulai(); });
  root.addEventListener("mouseleave", function () { hover = false; mulai(); });
  root.addEventListener("focusin", function () { fokus = true; mulai(); });
  root.addEventListener("focusout", function (e) {
    if (!root.contains(e.relatedTarget)) { fokus = false; mulai(); }
  });
  document.addEventListener("visibilitychange", mulai);

  // Geser (swipe) di layar sentuh
  var x0 = null, y0 = 0;
  track.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; hover = true; mulai(); }, { passive: true });
  track.addEventListener("touchend", function (e) {
    if (x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
    x0 = null; hover = false;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) tampil(aktif + (dx < 0 ? 1 : -1), true);
    else mulai();
  }, { passive: true });

  tampil(0);
  mulai();
  window.SlideShow = { ke: function (i) { tampil(i, true); }, aktif: function () { return aktif; }, jumlah: n };
})();
