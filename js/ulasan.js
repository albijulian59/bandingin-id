/* Formulir pendapat. Kolom yang dikirim (supaya gampang ditambah):
   membantu, perbandingan, perbandingan_id, mudah, kurang, saran,
   berikutnya, kontak, halaman, waktu.
   Pertanyaan baru: tambah input di ulasan.html, lalu masukkan kuncinya
   di objek kiriman di bawah dan di daftar KOLOM pada skrip Google Sheet. */
(function () {
  var form = document.getElementById("form-pendapat");
  if (!form) return;

  var sukses = document.getElementById("sukses");
  var judul = document.getElementById("sukses-judul");
  var teks = document.getElementById("sukses-teks");
  var kotakSalin = document.getElementById("salinan");
  var area = document.getElementById("teks-salinan");
  var tombolSalin = document.getElementById("salin");
  var endpoint = String(window.FEEDBACK_ENDPOINT || "").trim();

  var bantuan = { ya: "Ya, sangat", lumayan: "Lumayan", tidak: "Tidak" };

  var baca = "";
  try {
    baca = new URLSearchParams(location.search).get("baca") || "";
  } catch (e) {
    baca = "";
  }
  if (baca && form.perbandingan) {
    var ada = false;
    for (var i = 0; i < form.perbandingan.options.length; i++) {
      if (form.perbandingan.options[i].value === baca) ada = true;
    }
    if (ada) form.perbandingan.value = baca;
  }

  function nilai(nama) {
    var el = form.elements[nama];
    if (!el) return "";
    if (el.value == null) return "";
    return String(el.value).trim();
  }

  function kiriman() {
    var id = nilai("perbandingan");
    var label = "";
    if (id && form.perbandingan.selectedIndex >= 0) {
      label = form.perbandingan.options[form.perbandingan.selectedIndex].text;
    }
    return {
      membantu: nilai("membantu"),
      perbandingan: label,
      perbandingan_id: id,
      mudah: nilai("mudah"),
      kurang: nilai("kurang"),
      saran: nilai("saran"),
      berikutnya: nilai("berikutnya"),
      kontak: nilai("kontak"),
      halaman: location.href,
      waktu: new Date().toISOString()
    };
  }

  function teksJawaban(data) {
    return [
      "Pendapat untuk PilihYuk",
      "Membantu memutuskan: " + (bantuan[data.membantu] || "-"),
      "Perbandingan: " + (data.perbandingan || "-"),
      "Mudah dipahami (1-5): " + (data.mudah || "-"),
      "Yang kurang atau membingungkan: " + (data.kurang || "-"),
      "Saran: " + (data.saran || "-"),
      "Mau dibandingin berikutnya: " + (data.berikutnya || "-"),
      "Nama/kontak: " + (data.kontak || "-")
    ].join("\n");
  }

  function tampil(mode, data) {
    form.hidden = true;
    sukses.hidden = false;
    if (mode === "terkirim") {
      judul.textContent = "Makasih, pendapatnya sudah terkirim.";
      teks.textContent = "Masukan seperti ini yang bikin perbandingannya makin kepakai.";
      kotakSalin.hidden = true;
    } else {
      judul.textContent = "Makasih sudah menulis.";
      teks.textContent = mode === "kosong"
        ? "Kotak masuknya belum disambungkan. Salin jawaban di bawah, lalu kirim ke Albi."
        : "Jawaban belum terkirim. Salin teks di bawah supaya tidak hilang.";
      kotakSalin.hidden = false;
      area.value = teksJawaban(data);
    }
    sukses.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function kirim(url, data) {
    var body = JSON.stringify(data);
    return fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: body
    }).then(function (res) {
      if (res.ok) return "ok";
      throw new Error("status");
    }).catch(function () {
      return fetch(url, {
        method: "POST",
        mode: "no-cors",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: body
      }).then(function () {
        return "opaque";
      }).catch(function () {
        return "gagal";
      });
    });
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (!form.reportValidity()) return;
    var data = kiriman();
    if (!endpoint) {
      tampil("kosong", data);
      return;
    }
    var tombol = form.querySelector("[type=submit]");
    tombol.disabled = true;
    kirim(endpoint, data).then(function (hasil) {
      tampil(hasil === "gagal" ? "gagal" : "terkirim", data);
      tombol.disabled = false;
    });
  });

  if (tombolSalin) {
    tombolSalin.addEventListener("click", function () {
      var isi = area.value;
      function selesai() { tombolSalin.textContent = "Tersalin"; }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(isi).then(selesai, function () {
          area.focus();
          area.select();
        });
      } else {
        area.focus();
        area.select();
        try { document.execCommand("copy"); selesai(); } catch (err) {}
      }
    });
  }
})();
