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
  function terjualTeks(p) {
    if (p.terjual == null) return "";
    return rupiah(p.terjual).slice(2) + (p.terjualPlus ? "+" : "");
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

  function grupDari(jenis) {
    return (window.GRUP || []).filter(function (g) { return g.id === jenis; })[0];
  }

  window.Situs = {
    esc: esc, rupiah: rupiah, terjualTeks: terjualTeks, bintang: bintang, gambar: gambar, gagal: gagal,
    tombolToko: tombolToko, badgeContoh: badgeContoh, label: label, hargaHtml: hargaHtml,
    tabelGrup: tabelGrup, grupDari: grupDari, produkById: produkById
  };

  document.addEventListener("DOMContentLoaded", function () {
    var y = document.getElementById("tahun");
    if (y) y.textContent = new Date().getFullYear();
    document.querySelectorAll(".tanggal-data").forEach(function (el) {
      el.textContent = window.TANGGAL_DATA || "";
    });
  });
})();
