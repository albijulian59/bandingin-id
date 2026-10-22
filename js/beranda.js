/* Halaman utama: filter kategori, pencarian, urutan, daftar produk. */
(function () {
  var S = window.Situs;
  var produk = window.PRODUK || [];
  var kategoriAktif = "Semua", kataCari = "", urutan = "default";

  var elFilter = document.getElementById("filter");
  var elGrid = document.getElementById("grid");
  var elCari = document.getElementById("cari");
  var elInfo = document.getElementById("info-hasil");
  var elUrut = document.getElementById("urut");

  function buatFilter() {
    var daftar = [{ nama: "Semua", ikon: "✨" }].concat(window.KATEGORI || []);
    elFilter.innerHTML = daftar.map(function (k) {
      var n = k.nama === "Semua" ? produk.length :
        produk.filter(function (p) { return p.kategori === k.nama; }).length;
      return '<button type="button" class="chip' + (k.nama === kategoriAktif ? " active" : "") +
        '" data-kat="' + S.esc(k.nama) + '" aria-pressed="' + (k.nama === kategoriAktif) + '">' +
        k.ikon + " " + S.esc(k.nama) + ' <span class="count">' + n + "</span></button>";
    }).join("");
  }

  function kartu(p) {
    var link = "review.html?id=" + encodeURIComponent(p.id);
    return '<article class="card">' +
      '<a class="card-img" href="' + link + '">' + S.gambar(p, false, true) + S.badgeContoh(p) +
        (p.diskon >= 5 ? '<span class="badge-diskon">-' + p.diskon + "%</span>" : "") + "</a>" +
      '<div class="card-body">' +
        '<span class="cat">' + S.esc(p.jenisNama || p.kategori) + "</span>" +
        '<h3><a href="' + link + '" title="' + S.esc(p.nama) + '">' + S.esc(p.nama) + "</a></h3>" +
        '<div class="meta">' + S.bintang(p.rating) +
          (p.terjual != null ? '<span class="sold">' + S.esc(S.terjualTeks(p)) + " terjual/bln</span>" : "") + "</div>" +
        '<p class="price">' + S.hargaHtml(p) + "</p>" +
        '<div class="lbls">' + S.label(p) + "</div>" +
        '<a class="more" href="' + link + '">Baca review & perbandingan →</a>' +
        '<div class="btns">' + S.tombolToko(p) + "</div>" +
      "</div></article>";
  }

  function urutkan(list) {
    var a = list.slice();
    if (urutan === "murah") a.sort(function (x, y) { return x.harga - y.harga; });
    else if (urutan === "rating") a.sort(function (x, y) { return y.rating - x.rating || (y.terjual || 0) - (x.terjual || 0) || x.harga - y.harga; });
    else if (urutan === "laris") a.sort(function (x, y) { return (y.terjual || 0) - (x.terjual || 0) || y.rating - x.rating || x.harga - y.harga; });
    return a;
  }

  function tampilkan() {
    var q = kataCari.trim().toLowerCase();
    var hasil = produk.filter(function (p) {
      var cocokKat = kategoriAktif === "Semua" || p.kategori === kategoriAktif;
      var teks = (p.nama + " " + (p.jenisNama || "") + " " + p.kategori + " " + (p.ringkasan || "")).toLowerCase();
      return cocokKat && (!q || teks.indexOf(q) !== -1);
    });
    hasil = urutkan(hasil);
    elInfo.textContent = hasil.length + " produk ditemukan" +
      (kategoriAktif !== "Semua" ? " di " + kategoriAktif : "") + (q ? ' untuk "' + kataCari.trim() + '"' : "");
    elGrid.innerHTML = hasil.length ? hasil.map(kartu).join("") :
      '<div class="empty">😕 Produk tidak ditemukan. Coba kata lain atau pilih kategori "Semua".</div>';
  }

  elFilter.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-kat]");
    if (!b) return;
    kategoriAktif = b.getAttribute("data-kat");
    buatFilter(); tampilkan();
  });
  elCari.addEventListener("input", function () { kataCari = elCari.value; tampilkan(); });
  elUrut.addEventListener("change", function () { urutan = elUrut.value; tampilkan(); });
  document.getElementById("form-cari").addEventListener("submit", function (e) {
    e.preventDefault();
    document.getElementById("produk").scrollIntoView({ behavior: "smooth" });
  });

  var params = new URLSearchParams(location.search);
  if (params.get("kategori")) kategoriAktif = params.get("kategori");
  if (params.get("cari")) { kataCari = params.get("cari"); elCari.value = kataCari; }

  buatFilter();
  tampilkan();
})();
