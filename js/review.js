/* Halaman review: membaca ?id=... lalu menampilkan produknya. */
(function () {
  var S = window.Situs;
  var id = new URLSearchParams(location.search).get("id");
  var p = S.produkById[id];
  var el = document.getElementById("review");

  if (!p) {
    document.title = "Produk tidak ditemukan";
    el.innerHTML = '<div class="empty">😕 Review tidak ditemukan. <a href="index.html">Kembali ke beranda</a></div>';
    return;
  }

  var namaSitus = (document.title.split("—")[1] || "").trim();
  document.title = "Review " + p.nama + (namaSitus ? " — " + namaSitus : "");
  var meta = document.querySelector('meta[name="description"]');
  if (meta) meta.setAttribute("content", p.ringkasan || "");

  function daftar(arr, cls) {
    return '<ul class="' + cls + '">' + (arr || []).map(function (x) { return "<li>" + S.esc(x) + "</li>"; }).join("") + "</ul>";
  }
  var g = p.jenis ? S.grupDari(p.jenis) : null;
  var tgl = window.TANGGAL_DATA || "";

  var fakta = '<ul class="fakta">' +
    "<li><span>Harga</span><b>" + S.esc(S.rupiah(p.harga)) + "</b></li>" +
    (p.hargaAsli ? "<li><span>Harga coret</span><b><s>" + S.esc(S.rupiah(p.hargaAsli)) + "</s> (-" + p.diskon + "%)</b></li>" : "") +
    "<li><span>Rating</span><b>" + Number(p.rating).toFixed(1) + " / 5</b></li>" +
    (p.terjual != null ? "<li><span>Terjual</span><b>" + S.esc(S.terjualTeks(p)) + " / bulan</b></li>" : "") +
    (p.terjualTotal != null ? "<li><span>Total terjual</span><b>" + S.esc(S.terjualTotalTeks(p)) + "</b></li>" : "") +
    (p.hargaPer100 ? "<li><span>Harga per 100 " + S.esc(p.satuanIsi) + "</span><b>± " + S.esc(S.rupiah(p.hargaPer100)) + "</b></li>" : "") +
    (p.kota ? "<li><span>Dikirim dari</span><b>" + S.esc(p.kota) + "</b></li>" : "") +
    (p.contoh ? "" : "<li><span>Toko</span><b>Toko resmi (Shopee Mall)</b></li>") +
    "</ul>";

  el.innerHTML =
    '<nav class="crumbs"><a href="index.html">Beranda</a> › <a href="index.html?kategori=' +
      encodeURIComponent(p.kategori) + '#produk">' + S.esc(p.kategori) + "</a>" +
      (g ? ' › <a href="perbandingan.html#' + S.esc(g.id) + '">' + S.esc(g.nama) + "</a>" : "") + "</nav>" +
    (p.contoh ? '<div class="note-contoh">⚠️ Ini adalah <b>produk contoh</b> untuk tampilan website. Isi review, harga, dan link belum asli.</div>' :
      '<div class="note-sumber">ℹ️ Ulasan ini disusun dari data yang tampil di toko resmi Shopee (judul produk, harga, rating, dan penjualan per ' +
      S.esc(tgl) + '), bukan dari uji langsung, dan tidak menilai keamanan atau khasiat produk. Harga bisa berubah.' +
      (p.kategori === "Balita" ? ' Untuk produk bayi dan balita, perhatikan usia yang dianjurkan di kemasan dan lakukan uji pada sedikit area kulit dulu.' : "") +
      "</div>") +
    '<div class="review-top">' +
      '<div class="review-img">' + S.gambar(p, true) + S.badgeContoh(p) + "</div>" +
      '<div class="review-info">' +
        '<span class="cat">' + S.esc(p.jenisNama || p.kategori) + "</span>" +
        "<h1>" + S.esc(p.nama) + "</h1>" +
        S.bintang(p.rating) +
        '<div class="lbls">' + S.label(p) + "</div>" +
        '<p class="price big">' + S.hargaHtml(p) + "</p>" +
        fakta +
        '<div class="btns">' + S.tombolToko(p) + "</div>" +
      "</div>" +
    "</div>" +
    '<div class="proscons">' +
      '<section class="box pros"><h2>👍 Kelebihan</h2>' + daftar(p.kelebihan, "list-pros") + "</section>" +
      '<section class="box cons"><h2>👎 Kekurangan</h2>' + daftar(p.kekurangan, "list-cons") + "</section>" +
    "</div>" +
    '<section class="box kesimpulan"><h2>📝 Kesimpulan</h2><p>' + S.esc(p.kesimpulan) + "</p>" +
      '<div class="btns">' + S.tombolToko(p) + "</div></section>" +
    (g ? '<section class="box banding" id="perbandingan"><h2>📊 Perbandingan ' + S.esc(g.nama) + "</h2>" +
      '<p class="muted small">' + g.produk.length + " pilihan " + S.esc(g.nama) + " dari toko resmi di Shopee, data per " + S.esc(tgl) + ".</p>" +
      S.tabelGrup(g, p.id) +
      '<p class="small"><a href="perbandingan.html">Lihat semua perbandingan →</a></p></section>' : "");
})();
