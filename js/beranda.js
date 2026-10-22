/* Halaman utama: filter kategori (+ sub-filter jenis produk), pencarian, urutan, daftar produk. */
(function () {
  var S = window.Situs;
  var produk = window.PRODUK || [];
  var kategoriAktif = "Semua", jenisAktif = "", kataCari = "", urutan = "default";

  var elFilter = document.getElementById("filter");
  var elSub = document.getElementById("subfilter");
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

  // Sub-filter jenis produk (mis. Sabun Mandi / Sampo / Facial Wash) saat satu kategori dipilih
  function buatSubfilter() {
    var gs = (window.GRUP || []).filter(function (g) { return g.kategori === kategoriAktif; });
    if (kategoriAktif === "Semua" || gs.length < 2) { elSub.hidden = true; elSub.innerHTML = ""; jenisAktif = ""; return; }
    if (jenisAktif && !gs.some(function (g) { return g.id === jenisAktif; })) jenisAktif = "";
    var daftar = [{ id: "", pendek: "Semua " + kategoriAktif, n: produk.filter(function (p) { return p.kategori === kategoriAktif; }).length }]
      .concat(gs.map(function (g) { return { id: g.id, pendek: g.pendek || g.nama, n: g.produk.length }; }));
    elSub.innerHTML = daftar.map(function (d) {
      var on = d.id === jenisAktif;
      return '<button type="button" class="subchip' + (on ? " active" : "") + '" data-jenis="' + S.esc(d.id) +
        '" aria-pressed="' + on + '">' + S.esc(d.pendek) + ' <span class="count">' + d.n + "</span></button>";
    }).join("");
    elSub.hidden = false;
  }

  function urutkan(list) {
    var a = list.slice();
    if (urutan === "murah") a.sort(function (x, y) { return x.harga - y.harga; });
    else if (urutan === "rating") a.sort(function (x, y) { return y.rating - x.rating || (y.terjual || 0) - (x.terjual || 0) || x.harga - y.harga; });
    else if (urutan === "laris") a.sort(S.urutTerlaris);
    return a;
  }

  function tampilkan() {
    var q = kataCari.trim().toLowerCase();
    var hasil = produk.filter(function (p) {
      var cocokKat = (kategoriAktif === "Semua" || p.kategori === kategoriAktif) && (!jenisAktif || p.jenis === jenisAktif);
      var teks = (p.nama + " " + (p.jenisNama || "") + " " + p.kategori + " " + (p.ringkasan || "")).toLowerCase();
      return cocokKat && (!q || teks.indexOf(q) !== -1);
    });
    hasil = urutkan(hasil);
    elInfo.textContent = hasil.length + " produk ditemukan" +
      (kategoriAktif !== "Semua" ? " di " + kategoriAktif : "") +
      (jenisAktif ? " (" + ((S.grupDari(jenisAktif) || {}).nama || "") + ")" : "") + (q ? ' untuk "' + kataCari.trim() + '"' : "");
    elGrid.innerHTML = hasil.length ? hasil.map(S.kartu).join("") :
      '<div class="empty">😕 Produk tidak ditemukan. Coba kata lain atau pilih kategori "Semua".</div>';
  }

  elFilter.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-kat]");
    if (!b) return;
    kategoriAktif = b.getAttribute("data-kat");
    jenisAktif = "";
    buatFilter(); buatSubfilter(); tampilkan();
  });
  elSub.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-jenis]");
    if (!b) return;
    jenisAktif = b.getAttribute("data-jenis");
    buatSubfilter(); tampilkan();
  });
  elCari.addEventListener("input", function () { kataCari = elCari.value; tampilkan(); });
  elUrut.addEventListener("change", function () { urutan = elUrut.value; tampilkan(); });
  document.getElementById("form-cari").addEventListener("submit", function (e) {
    e.preventDefault();
    document.getElementById("produk").scrollIntoView({ behavior: "smooth" });
  });

  var params = new URLSearchParams(location.search);
  if (params.get("kategori")) kategoriAktif = params.get("kategori");
  if (params.get("jenis")) jenisAktif = params.get("jenis");
  if (params.get("cari")) { kataCari = params.get("cari"); elCari.value = kataCari; }

  buatFilter();
  buatSubfilter();
  tampilkan();
})();
