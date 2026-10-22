/* Fungsi bersama untuk semua halaman. Tidak perlu diedit. */
(function () {
  var ikonKategori = {};
  (window.KATEGORI || []).forEach(function (k) { ikonKategori[k.nama] = k.ikon; });
  var produkById = {};
  (window.PRODUK || []).forEach(function (p) { produkById[p.id] = p; });

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function aman(url) { return /^https?:\/\//i.test(url || "") ? url : ""; }

  // Angka -> "Rp197.000". Teks (data lama) ditampilkan apa adanya.
  function rupiah(n) {
    if (typeof n !== "number") return n || "";
    return "Rp" + Math.round(n).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }
  // Teks terjual Shopee / angka -> angka. "1RB+ Terjual/Bln" -> 1000, "2,5RB+" -> 2500, "919" -> 919
  function angkaTerjual(v) {
    if (typeof v === "number") return v;
    var t = String(v == null ? "" : v).replace(/terjual\s*\/?\s*(bln|bulan)?/i, "").trim();
    var m = t.match(/^([\d.,]+)\s*(rb|jt)?/i);
    if (!m) return 0;
    var satuan = (m[2] || "").toLowerCase();
    var n = satuan ? parseFloat(m[1].replace(",", ".")) : parseFloat(m[1].replace(/[.,]/g, ""));
    return Math.round(n * (satuan === "rb" ? 1000 : satuan === "jt" ? 1000000 : 1)) || 0;
  }
  // Angka/teks terjual -> label rentang (sama dengan rentang_terjual di tools/build_data.py).
  // < 1000 -> "919"; 1000-9999 -> "1rb+" ... "9rb+" (dibulatkan ke bawah); >= 10000 -> "10rb+"
  function rentangTerjual(v) {
    var n = angkaTerjual(v);
    return n < 1000 ? String(n) : Math.min(Math.floor(n / 1000), 10) + "rb+";
  }
  // Label terjual untuk satu produk (dipakai di kartu, halaman review, dan tabel perbandingan)
  function terjualTeks(p) {
    if (p.terjual == null) return "";
    return p.terjualLabel || rentangTerjual(p.terjual);
  }
  // Total terjual (dari halaman produk, hanya untuk sebagian produk) -> "10rb+ terjual"
  function terjualTotalTeks(p) {
    if (p.terjualTotal == null) return "";
    return (p.terjualTotalLabel || rentangTerjual(p.terjualTotal)) + " terjual";
  }

  function bintang(r) {
    r = Math.max(0, Math.min(5, Number(r) || 0));
    var html = "";
    for (var i = 1; i <= 5; i++) {
      var cls = r >= i ? "s-full" : r >= i - 0.5 ? "s-half" : "s-empty";
      html += '<span class="star ' + cls + '">★</span>';
    }
    return '<span class="stars" aria-label="Rating ' + r + ' dari 5">' + html +
      '<span class="rating-num">' + r.toFixed(1) + "</span></span>";
  }

  function placeholder(p, besar) {
    return '<div class="ph' + (besar ? " ph-big" : "") + '" aria-hidden="true">' +
      (ikonKategori[p.kategori] || "🛍️") + "</div>";
  }
  // Kalau gambar gagal dimuat, ganti dengan ikon kategori
  function gagal(img) {
    var ikon = img.getAttribute("data-ikon") || "🛍️";
    var d = document.createElement("div");
    d.className = "ph" + (img.getAttribute("data-besar") ? " ph-big" : "");
    d.setAttribute("aria-hidden", "true");
    d.textContent = ikon;
    img.replaceWith(d);
  }
  // kecil = true memakai versi thumbnail Shopee (lebih ringan)
  function gambar(p, besar, kecil) {
    var src = aman(p.gambar) || (p.gambar && !/^[a-z]+:/i.test(p.gambar) ? p.gambar : "");
    if (!src) return placeholder(p, besar);
    if (kecil && /susercontent\.com\/file\/[^_?]+$/.test(src)) src += "_tn";
    return '<img src="' + esc(src) + '" alt="' + esc(p.nama) + '" loading="lazy" decoding="async" ' +
      'referrerpolicy="no-referrer" data-ikon="' + esc(ikonKategori[p.kategori] || "🛍️") + '"' +
      (besar ? ' data-besar="1"' : "") + ' onerror="Situs.gagal(this)">';
  }

  var REL = 'target="_blank" rel="nofollow sponsored noopener"';
  function linkShopee(p) { return aman(p.linkShopee) || aman(p.shopee); }
  // Tombol toko. Tokopedia hanya muncul kalau field "tokopedia" diisi.
  function tombolToko(p, kecil) {
    var out = "", s = linkShopee(p), t = aman(p.tokopedia);
    var c = kecil ? " btn-sm" : "";
    if (s) out += '<a class="btn btn-shopee' + c + '" href="' + esc(s) + '" ' + REL + '>Cek Harga di Shopee</a>';
    if (t) out += '<a class="btn btn-tokped' + c + '" href="' + esc(t) + '" ' + REL + '>Cek di Tokopedia</a>';
    return out;
  }
  function badgeContoh(p) {
    return p.contoh ? '<span class="badge-contoh" title="Produk contoh, bukan review asli">Contoh</span>' : "";
  }
  var WARNA_LABEL = { "Paling murah": "lbl-murah", "Rating tertinggi": "lbl-rating", "Paling laris": "lbl-laris", "Paling seimbang": "lbl-seimbang" };
  var IKON_LABEL = { "Paling murah": "💰", "Rating tertinggi": "⭐", "Paling laris": "🔥", "Paling seimbang": "⚖️" };
  function label(p) {
    return (p.label || []).map(function (l) {
      return '<span class="lbl ' + (WARNA_LABEL[l] || "") + '">' + (IKON_LABEL[l] || "") + " " + esc(l) + "</span>";
    }).join("");
  }
  function hargaHtml(p) {
    var h = '<span class="harga-now">' + esc(rupiah(p.harga)) + "</span>";
    if (p.hargaAsli) h += ' <s class="harga-asli">' + esc(rupiah(p.hargaAsli)) + "</s>";
    if (p.diskon) h += ' <span class="diskon">-' + p.diskon + "%</span>";
    return h;
  }

  // Tabel perbandingan untuk satu kelompok (jenis produk)
  function tabelGrup(g, idAktif) {
    var list = g.produk.map(function (id) { return produkById[id]; }).filter(Boolean);
    var rows = list.map(function (p) {
      var link = "review.html?id=" + encodeURIComponent(p.id);
      return '<tr' + (p.id === idAktif ? ' class="aktif"' : "") + ">" +
        '<td class="t-img"><a href="' + link + '">' + gambar(p, false, true) + "</a></td>" +
        '<td class="t-nama"><a href="' + link + '">' + esc(p.nama) + "</a>" +
          (p.id === idAktif ? ' <span class="sedang">(sedang dilihat)</span>' : "") +
          '<div class="lbls">' + label(p) + "</div></td>" +
        '<td class="t-harga" data-th="Harga"><b>' + esc(rupiah(p.harga)) + "</b>" +
          (p.hargaAsli ? '<br><s class="harga-asli">' + esc(rupiah(p.hargaAsli)) + "</s>" : "") + "</td>" +
        '<td data-th="Diskon">' + (p.diskon ? '<span class="diskon">-' + p.diskon + "%</span>" : "–") + "</td>" +
        '<td data-th="Rating">⭐ ' + Number(p.rating).toFixed(1) + "</td>" +
        '<td data-th="Terjual/bln">' + esc(terjualTeks(p)) + "</td>" +
        '<td class="t-btn">' + tombolToko(p, true) + "</td></tr>";
    }).join("");
    return '<p class="geser">👉 Geser tabel ke samping untuk melihat semua kolom</p><div class="tabel-wrap"><table class="tabel">' +
      "<thead><tr><th>Gambar</th><th>Nama produk</th><th>Harga</th><th>Diskon</th><th>Rating</th><th>Terjual/bln</th><th></th></tr></thead>" +
      "<tbody>" + rows + "</tbody></table></div>" +
      ((g.catatan || []).length ? '<ul class="catatan">' + g.catatan.map(function (c) { return "<li>" + esc(c) + "</li>"; }).join("") + "</ul>" : "");
  }

  // Kartu produk (dipakai di beranda; bisa dipakai ulang untuk bagian lain, mis. "Top 10 Terlaris")
  function kartu(p) {
    var link = "review.html?id=" + encodeURIComponent(p.id);
    return '<article class="card">' +
      '<a class="card-img" href="' + link + '">' + gambar(p, false, true) + badgeContoh(p) +
        (p.diskon >= 5 ? '<span class="badge-diskon">-' + p.diskon + "%</span>" : "") + "</a>" +
      '<div class="card-body">' +
        '<span class="cat">' + esc(p.jenisNama || p.kategori) + "</span>" +
        '<h3><a href="' + link + '" title="' + esc(p.nama) + '">' + esc(p.nama) + "</a></h3>" +
        '<div class="meta">' + bintang(p.rating) +
          (p.terjual != null ? '<span class="sold">' + esc(terjualTeks(p)) + " terjual/bln</span>" : "") + "</div>" +
        '<p class="price">' + hargaHtml(p) + "</p>" +
        '<div class="lbls">' + label(p) + "</div>" +
        '<a class="more" href="' + link + '">Baca review & perbandingan →</a>' +
        '<div class="btns">' + tombolToko(p) + "</div>" +
      "</div></article>";
  }

  // Urutan terlaris: angka terjual (numerik), lalu rating, lalu harga termurah
  function urutTerlaris(x, y) {
    return (y.terjual || 0) - (x.terjual || 0) || y.rating - x.rating || x.harga - y.harga;
  }

  // Judul pendek untuk tempat sempit: potong di pemisah (" - ", "|", ",", "(") lalu maks. 8 kata
  function judulPendek(nama, maks) {
    maks = maks || 8;
    var t = String(nama || "").split(/\s[-|\u2013/]\s|\s\|\s?|,|\(|\sl\s/)[0].trim();
    var kata = t.split(/\s+/);
    if (kata.length < 3) kata = String(nama || "").split(/\s+/);
    return kata.slice(0, maks).join(" ") + (kata.length > maks ? "…" : "");
  }

  // Produk unggulan per kategori (untuk slide show di beranda). Aturan (deterministik):
  //  1. hanya produk yang punya gambar dan link Shopee;
  //  2. utamakan yang berlabel "Paling seimbang" (skor gabungan harga, rating, penjualan di kelompoknya);
  //  3. lalu rating tertinggi, 4. terjual terbanyak, 5. diskon terbesar, 6. harga termurah, 7. id (A-Z).
  // Hasil ikut berubah otomatis saat data/produk.js dibuat ulang.
  function produkUnggulan(kategori) {
    var list = (window.PRODUK || []).filter(function (p) {
      return p.kategori === kategori && p.gambar && linkShopee(p);
    });
    var seimbang = function (p) { return (p.label || []).indexOf("Paling seimbang") !== -1 ? 1 : 0; };
    list.sort(function (x, y) {
      return seimbang(y) - seimbang(x) || y.rating - x.rating || (y.terjual || 0) - (x.terjual || 0) ||
        (y.diskon || 0) - (x.diskon || 0) || x.harga - y.harga || (x.id < y.id ? -1 : x.id > y.id ? 1 : 0);
    });
    return list[0] || null;
  }
  // Satu produk unggulan untuk tiap kategori di window.KATEGORI (urutan kategori tetap)
  function daftarUnggulan() {
    return (window.KATEGORI || []).map(function (k) {
      var p = produkUnggulan(k.nama);
      return p ? { kategori: k.nama, ikon: k.ikon, produk: p } : null;
    }).filter(Boolean);
  }

  function grupDari(jenis) {
    return (window.GRUP || []).filter(function (g) { return g.id === jenis; })[0];
  }

  window.Situs = {
    esc: esc, rupiah: rupiah, terjualTeks: terjualTeks, terjualTotalTeks: terjualTotalTeks, rentangTerjual: rentangTerjual, angkaTerjual: angkaTerjual, bintang: bintang, gambar: gambar, gagal: gagal,
    tombolToko: tombolToko, badgeContoh: badgeContoh, label: label, hargaHtml: hargaHtml,
    tabelGrup: tabelGrup, grupDari: grupDari, produkById: produkById,
    kartu: kartu, urutTerlaris: urutTerlaris, judulPendek: judulPendek, linkShopee: linkShopee,
    produkUnggulan: produkUnggulan, daftarUnggulan: daftarUnggulan, REL: REL
  };

  document.addEventListener("DOMContentLoaded", function () {
    var y = document.getElementById("tahun");
    if (y) y.textContent = new Date().getFullYear();
    document.querySelectorAll(".tanggal-data").forEach(function (el) {
      el.textContent = window.TANGGAL_DATA || "";
    });
    // Jumlah produk selalu dihitung dari data (tidak ditulis manual)
    document.querySelectorAll(".jumlah-produk").forEach(function (el) {
      el.textContent = (window.PRODUK || []).length;
    });
  });
})();
