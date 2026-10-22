/* Halaman perbandingan: semua kelompok produk. */
(function () {
  var S = window.Situs;
  var grup = window.GRUP || [];
  var kat = window.KATEGORI || [];
  var el = document.getElementById("isi-banding");
  var nav = document.getElementById("nav-banding");

  nav.innerHTML = kat.map(function (k) {
    var gs = grup.filter(function (g) { return g.kategori === k.nama; });
    if (!gs.length) return "";
    return '<div class="nav-kat"><b>' + k.ikon + " " + S.esc(k.nama) + "</b>" +
      gs.map(function (g) { return '<a href="#' + S.esc(g.id) + '">' + S.esc(g.nama) + "</a>"; }).join("") + "</div>";
  }).join("");

  el.innerHTML = kat.map(function (k) {
    var gs = grup.filter(function (g) { return g.kategori === k.nama; });
    if (!gs.length) return "";
    return '<h2 class="judul-kat">' + k.ikon + " " + S.esc(k.nama) + "</h2>" +
      gs.map(function (g) {
        return '<section class="box banding" id="' + S.esc(g.id) + '"><h3>' + S.esc(g.nama) + "</h3>" + S.tabelGrup(g) + "</section>";
      }).join("");
  }).join("");

  if (location.hash) {
    var t = document.getElementById(location.hash.slice(1));
    if (t) t.scrollIntoView();
  }
})();
