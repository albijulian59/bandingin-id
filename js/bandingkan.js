/* Halaman Bandingin Sendiri (bandingkan.html).
   Data produk ada di <script id="data-bandingkan">, dibuat tools/build_site.py.
   Bagian kedua: formulir request produk, dikirim ke FEEDBACK_ENDPOINT (js/config.js). */
(function () {
  var sumber = document.getElementById("data-bandingkan");
  if (!sumber) return;
  var DATA = JSON.parse(sumber.textContent);
  var MAKS = 3;
  var semua = DATA.produk;
  var byId = {};
  semua.forEach(function (p) { byId[p.id] = p; });

  var chips = Array.prototype.slice.call(document.querySelectorAll("[data-jenis]"));
  var cari = document.getElementById("cari-produk");
  var grid = document.getElementById("grid-pilih");
  var info = document.getElementById("info-pilih");
  var kosong = document.getElementById("kosong-pilih");
  var hasil = document.getElementById("hasil-banding");
  var bandingGrid = document.getElementById("banding-grid");
  var ringkas = document.getElementById("ringkas-harga");
  var pairAda = document.getElementById("pair-ada");
  var baki = document.getElementById("baki");
  var bakiTeks = document.getElementById("baki-teks");
  var bakiLihat = document.getElementById("baki-lihat");
  var tplBeli = document.getElementById("tpl-beli");

  var jenis = "";
  var pilih = [];

  function rp(n) {
    return "Rp" + String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  }

  function buat(tag, kelas, teks) {
    var el = document.createElement(tag);
    if (kelas) el.className = kelas;
    if (teks != null) el.textContent = teks;
    return el;
  }

  function badgeAsal(asal) {
    return buat("span", "asal asal-" + asal, asal === "korea" ? "Korea" : "Lokal");
  }

  function foto(p, lazy) {
    var img = document.createElement("img");
    img.src = "img/" + p.id + ".jpg";
    img.alt = p.nama;
    img.width = 720;
    img.height = 720;
    img.decoding = "async";
    if (lazy) img.loading = "lazy";
    return img;
  }

  function teksCari(p) {
    return [p.nama, p.merek, p.asal, p.tekstur, p.bahan.join(" "), p.kulit.join(" ")].join(" ").toLowerCase();
  }

  /* ---------- daftar produk ---------- */

  function renderDaftar() {
    grid.innerHTML = "";
    if (!jenis) {
      kosong.hidden = true;
      return;
    }
    var q = (cari.value || "").toLowerCase().trim();
    var n = 0;
    semua.forEach(function (p) {
      if (p.jenis !== jenis) return;
      if (q && teksCari(p).indexOf(q) === -1) return;
      n++;
      var li = buat("li");
      var b = buat("button", "kartu-pilih");
      b.type = "button";
      b.setAttribute("data-id", p.id);
      var dipilih = pilih.indexOf(p.id) !== -1;
      b.setAttribute("aria-pressed", dipilih ? "true" : "false");
      var bingkai = buat("span", "kp-foto");
      bingkai.appendChild(foto(p, true));
      b.appendChild(bingkai);
      var teks = buat("span", "kp-teks");
      teks.appendChild(badgeAsal(p.asal));
      teks.appendChild(buat("span", "kp-nama", p.nama));
      teks.appendChild(buat("span", "kp-harga", (p.hargaMaks ? "mulai " : "") + rp(p.harga)));
      b.appendChild(teks);
      b.appendChild(buat("span", "kp-cek", dipilih ? "Dipilih" : "Pilih"));
      b.addEventListener("click", function () { toggle(p.id); });
      li.appendChild(b);
      grid.appendChild(li);
    });
    kosong.hidden = n !== 0;
  }

  function segarkanTombol() {
    Array.prototype.forEach.call(grid.querySelectorAll(".kartu-pilih"), function (b) {
      var dipilih = pilih.indexOf(b.getAttribute("data-id")) !== -1;
      b.setAttribute("aria-pressed", dipilih ? "true" : "false");
      b.querySelector(".kp-cek").textContent = dipilih ? "Dipilih" : "Pilih";
    });
  }

  function setInfo(pesan) {
    info.textContent = pesan;
  }

  function infoBawaan() {
    if (!jenis) return "Pilih jenis produknya dulu, ya.";
    if (pilih.length === 0) return "Ketuk dua produk yang mau dibandingin.";
    if (pilih.length === 1) return "Satu lagi. Pilih produk kedua.";
    if (pilih.length === 2) return "Sip. Hasilnya ada di bawah. Mau tambah satu lagi juga bisa.";
    return "Sudah tiga, ini batasnya. Ketuk produk yang dipilih buat menghapus.";
  }

  function toggle(id) {
    var i = pilih.indexOf(id);
    if (i !== -1) {
      pilih.splice(i, 1);
    } else if (pilih.length >= MAKS) {
      setInfo("Maksimal tiga produk. Hapus satu dulu kalau mau ganti.");
      return;
    } else {
      pilih.push(id);
    }
    perbarui(true);
  }

  function setJenis(nilai, simpanPilihan) {
    if (!DATA.jenis[nilai]) nilai = "";
    if (nilai !== jenis && !simpanPilihan) pilih = [];
    jenis = nilai;
    chips.forEach(function (c) {
      var aktif = c.getAttribute("data-jenis") === jenis;
      c.classList.toggle("aktif", aktif);
      c.setAttribute("aria-pressed", aktif ? "true" : "false");
    });
    cari.disabled = !jenis;
    renderDaftar();
    perbarui(false);
  }

  /* ---------- hasil ---------- */

  function sel(isi, kelas) {
    var d = buat("div", "bg-sel" + (kelas ? " " + kelas : ""));
    if (isi) d.appendChild(isi);
    return d;
  }

  function barisLabel(teks) {
    bandingGrid.appendChild(buat("div", "bg-label", teks));
  }

  function tombolBeli(p) {
    var a = tplBeli.content.firstElementChild.cloneNode(true);
    a.href = p.link;
    a.setAttribute("aria-label", "Beli " + p.nama + " di Shopee");
    return a;
  }

  function renderHasil() {
    var dipilih = pilih.map(function (id) { return byId[id]; });
    if (dipilih.length < 2) {
      hasil.hidden = true;
      bandingGrid.innerHTML = "";
      return;
    }
    hasil.hidden = false;
    bandingGrid.innerHTML = "";
    bandingGrid.style.setProperty("--n", dipilih.length);
    bandingGrid.setAttribute("data-n", dipilih.length);

    var hargaMin = Math.min.apply(null, dipilih.map(function (p) { return p.harga; }));
    var hargaMax = Math.max.apply(null, dipilih.map(function (p) { return p.harga; }));
    var termurah = dipilih.filter(function (p) { return p.harga === hargaMin; });
    var semuaKulit = {};
    dipilih.forEach(function (p) {
      p.kulit.forEach(function (k) { semuaKulit[k] = (semuaKulit[k] || 0) + 1; });
    });

    // ringkasan harga
    if (hargaMin === hargaMax) {
      ringkas.textContent = "Harganya sama persis: " + rp(hargaMin) + ".";
    } else if (dipilih.length === 2) {
      var mahal = dipilih.filter(function (p) { return p.harga === hargaMax; })[0];
      ringkas.textContent = termurah[0].nama + " lebih murah " + rp(hargaMax - hargaMin) + " dari " + mahal.nama + ".";
    } else {
      var palingMahal = dipilih.filter(function (p) { return p.harga === hargaMax; })[0];
      var namaMurah = termurah.map(function (p) { return p.nama; }).join(" dan ");
      ringkas.textContent = namaMurah + (termurah.length > 1 ? " sama-sama paling murah" : " paling murah") +
        ". Selisihnya " + rp(hargaMax - hargaMin) + " dari yang paling mahal, " + palingMahal.nama + ".";
    }

    if (dipilih.some(function (p) { return p.hargaMaks; })) {
      ringkas.textContent += " Untuk harga rentang, yang dihitung harga terendahnya.";
    }

    // pasangan yang sudah dibahas lengkap
    pairAda.innerHTML = "";
    var hitung = {};
    var namaPair = {};
    dipilih.forEach(function (p) {
      p.pairs.forEach(function (pr) {
        hitung[pr[0]] = (hitung[pr[0]] || 0) + 1;
        namaPair[pr[0]] = pr[1];
      });
    });
    var lengkap = Object.keys(hitung).filter(function (k) { return hitung[k] >= 2; });
    if (lengkap.length) {
      pairAda.appendChild(buat("p", "", dipilih.length === 2
        ? "Dua produk ini sudah dibahas lengkap, sampai saran buat tiap jenis kulit."
        : "Ada pilihanmu yang sudah dibahas lengkap, sampai saran buat tiap jenis kulit."));
      lengkap.forEach(function (id) {
        var a = buat("a", "btn btn-lengkap", "Baca: " + namaPair[id]);
        a.href = "banding/" + id + ".html";
        pairAda.appendChild(a);
      });
      pairAda.hidden = false;
    } else {
      pairAda.hidden = true;
    }

    // kepala kolom
    dipilih.forEach(function (p) {
      var kepala = buat("div", "bg-kepala");
      var bingkai = buat("div", "bg-foto photo-" + p.asal);
      bingkai.appendChild(foto(p, false));
      kepala.appendChild(bingkai);
      kepala.appendChild(badgeAsal(p.asal));
      kepala.appendChild(buat("h3", "bg-nama", p.nama));
      var hapus = buat("button", "tautan-tombol bg-hapus", "Hapus");
      hapus.type = "button";
      hapus.setAttribute("aria-label", "Hapus " + p.nama + " dari perbandingan");
      hapus.addEventListener("click", function () { toggle(p.id); });
      kepala.appendChild(hapus);
      bandingGrid.appendChild(sel(kepala, "bg-sel-kepala"));
    });

    barisLabel("Harga");
    dipilih.forEach(function (p) {
      var h = buat("p", "harga");
      h.appendChild(buat("span", "now", rp(p.harga) + (p.hargaMaks ? "–" + rp(p.hargaMaks) : "")));
      if (p.asli) {
        h.appendChild(document.createTextNode(" "));
        h.appendChild(buat("s", "", rp(p.asli)));
        var off = Math.round((p.asli - p.harga) * 100 / p.asli);
        if (off >= 1) {
          h.appendChild(document.createTextNode(" "));
          h.appendChild(buat("span", "off", "−" + off + "%"));
        }
      }
      var wadah = buat("div");
      wadah.appendChild(h);
      if (p.hargaMaks) wadah.appendChild(buat("p", "bg-redup", "Harga ikut pilihan ukuran atau varian di listing."));
      if (hargaMin !== hargaMax && p.harga === hargaMin) {
        wadah.appendChild(buat("span", "lencana-murah", termurah.length > 1 ? "Sama-sama termurah" : (dipilih.length === 2 ? "Lebih murah" : "Paling murah")));
      }
      bandingGrid.appendChild(sel(wadah, p.harga === hargaMin && hargaMin !== hargaMax ? "bg-murah" : ""));
    });

    barisLabel("Asal");
    dipilih.forEach(function (p) {
      bandingGrid.appendChild(sel(buat("p", "", (p.asal === "korea" ? "Korea" : "Lokal") + " · " + p.merek)));
    });

    barisLabel("Isi dan tekstur");
    dipilih.forEach(function (p) {
      var w = buat("div");
      w.appendChild(buat("p", "", p.isi));
      w.appendChild(buat("p", "bg-redup", p.tekstur));
      if (p.varian) w.appendChild(buat("p", "bg-redup", p.varian));
      bandingGrid.appendChild(sel(w));
    });

    barisLabel("Cocok untuk kulit");
    dipilih.forEach(function (p) {
      var ul = buat("ul", "kulit");
      p.kulit.forEach(function (k) {
        var li = buat("li", semuaKulit[k] === dipilih.length ? "kulit-sama" : "", k);
        ul.appendChild(li);
      });
      bandingGrid.appendChild(sel(ul));
    });

    barisLabel("Kandungan utama");
    dipilih.forEach(function (p) {
      var ul = buat("ul", "bg-bahan");
      p.bahan.forEach(function (b) { ul.appendChild(buat("li", "", b)); });
      bandingGrid.appendChild(sel(ul));
    });

    barisLabel("Ulasan lengkap");
    dipilih.forEach(function (p) {
      var ul = buat("ul", "bg-ulasan");
      p.pairs.forEach(function (pr) {
        var li = buat("li");
        var a = buat("a", "", pr[1]);
        a.href = "banding/" + pr[0] + ".html";
        li.appendChild(a);
        ul.appendChild(li);
      });
      bandingGrid.appendChild(sel(ul, "bg-kecil"));
    });

    barisLabel("Beli");
    dipilih.forEach(function (p) {
      bandingGrid.appendChild(sel(tombolBeli(p)));
    });
  }

  /* ---------- baki bawah (mobile) dan URL ---------- */

  function renderBaki() {
    if (!pilih.length) {
      baki.hidden = true;
      return;
    }
    baki.hidden = false;
    bakiTeks.textContent = pilih.length + " dari maks. 3 dipilih";
    bakiLihat.disabled = pilih.length < 2;
    bakiLihat.textContent = pilih.length < 2 ? "Pilih 1 lagi" : "Lihat hasil";
  }

  function simpanUrl() {
    if (!window.history || !history.replaceState) return;
    var q = [];
    if (jenis) q.push("jenis=" + encodeURIComponent(jenis));
    if (pilih.length) q.push("pilih=" + pilih.map(encodeURIComponent).join(","));
    history.replaceState(null, "", location.pathname + (q.length ? "?" + q.join("&") : "") + location.hash);
  }

  function perbarui(dariKlik) {
    segarkanTombol();
    setInfo(infoBawaan());
    var sebelumnya = !hasil.hidden;
    renderHasil();
    renderBaki();
    simpanUrl();
    if (dariKlik && !sebelumnya && !hasil.hidden && window.innerWidth >= 800) {
      hasil.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  chips.forEach(function (c) {
    c.addEventListener("click", function () { setJenis(c.getAttribute("data-jenis"), false); });
  });
  cari.addEventListener("input", renderDaftar);
  document.getElementById("form-cari-produk").addEventListener("submit", function (e) {
    e.preventDefault();
    renderDaftar();
  });
  bakiLihat.addEventListener("click", function () {
    hasil.scrollIntoView({ behavior: "smooth", block: "start" });
    hasil.focus({ preventScroll: true });
  });

  // buka dari URL, misalnya ?jenis=serum&pilih=123,456
  (function () {
    var params = {};
    location.search.replace(/^\?/, "").split("&").forEach(function (kv) {
      if (!kv) return;
      var i = kv.indexOf("=");
      var k = decodeURIComponent(i === -1 ? kv : kv.slice(0, i));
      params[k] = i === -1 ? "" : decodeURIComponent(kv.slice(i + 1));
    });
    var awal = (params.pilih || "").split(",").filter(function (id, i, arr) {
      return byId[id] && arr.indexOf(id) === i;
    }).slice(0, MAKS);
    var j = params.jenis;
    if (awal.length) j = byId[awal[0]].jenis;
    pilih = awal.filter(function (id) { return byId[id].jenis === j; });
    setJenis(j || "", true);
  })();

  /* ---------- formulir request ---------- */

  var form = document.getElementById("form-request");
  var bagian = document.getElementById("request");
  if (!form || !bagian || bagian.hidden) return;
  var pesan = document.getElementById("pesan-request");
  var sukses = document.getElementById("sukses-request");
  var endpoint = String(window.FEEDBACK_ENDPOINT || "").trim();

  function nilai(nama) {
    var el = form.elements[nama];
    return el && el.value != null ? String(el.value).trim() : "";
  }

  function tampilPesan(teks) {
    pesan.textContent = teks;
    pesan.hidden = !teks;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    tampilPesan("");
    var p1 = nilai("produk_1");
    if (!p1) {
      tampilPesan("Isi nama produk 1 dulu, ya.");
      form.elements.produk_1.focus();
      return;
    }
    if (nilai("situs")) {  // jebakan bot: pura-pura berhasil
      form.hidden = true;
      sukses.hidden = false;
      return;
    }
    if (!endpoint) {
      tampilPesan("Form request lagi disiapkan. Coba lagi nanti, ya.");
      return;
    }
    var data = {
      produk_1: p1,
      produk_2: nilai("produk_2"),
      jenis_kulit: nilai("jenis_kulit"),
      catatan: nilai("catatan")
    };
    var ringkasan = "Produk 1: " + data.produk_1 +
      " | Produk 2: " + (data.produk_2 || "-") +
      " | Jenis kulit: " + (data.jenis_kulit || "-") +
      " | Catatan: " + (data.catatan || "-");
    // Kolom yang dikenal skrip Google Sheet Kasih Pendapat (KOLOM di PANDUAN.md).
    // Request ditandai perbandingan_id "request-produk"; isinya di kolom "berikutnya".
    var kiriman = {
      waktu: new Date().toISOString(),
      membantu: "",
      perbandingan: "Request produk",
      perbandingan_id: "request-produk",
      mudah: "",
      kurang: "",
      saran: data.catatan,
      berikutnya: ringkasan,
      kontak: "",
      halaman: location.origin + location.pathname,
      jenis: "request-produk",
      produk_1: data.produk_1,
      produk_2: data.produk_2,
      jenis_kulit: data.jenis_kulit,
      catatan: data.catatan
    };
    var tombol = form.querySelector("[type=submit]");
    tombol.disabled = true;
    tombol.textContent = "Mengirim…";
    fetch(endpoint, {
      method: "POST",
      mode: "no-cors",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(kiriman)
    }).then(function () {
      form.hidden = true;
      sukses.hidden = false;
      form.reset();
    }).catch(function () {
      tampilPesan("Request belum terkirim. Cek koneksi, lalu coba lagi.");
    }).then(function () {
      tombol.disabled = false;
      tombol.textContent = "Kirim request";
    });
  });

  document.getElementById("request-lagi").addEventListener("click", function () {
    sukses.hidden = true;
    form.hidden = false;
    form.elements.produk_1.focus();
  });
})();
