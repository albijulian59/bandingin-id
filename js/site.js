function gambarGagal(img) {
  var d = document.createElement("div");
  d.className = "ph";
  d.setAttribute("role", "img");
  d.setAttribute("aria-label", img.alt || "Gambar produk");
  d.textContent = (img.alt || "?").trim().charAt(0) || "?";
  img.replaceWith(d);
}

(function () {
  var daftar = document.getElementById("daftar");
  if (!daftar) return;

  var kartu = Array.prototype.slice.call(daftar.querySelectorAll(".card"));
  var kosong = document.getElementById("kosong");
  var info = document.getElementById("info-hasil");
  var jenisOk = { semua: 1, pelembab: 1, serum: 1, sunscreen: 1, "facial-wash": 1 };
  var untukOk = { semua: 1, perempuan: 1, pria: 1 };
  var params = new URLSearchParams(location.search);
  var state = {
    jenis: jenisOk[params.get("jenis")] ? params.get("jenis") : "semua",
    untuk: untukOk[params.get("untuk")] ? params.get("untuk") : "semua"
  };

  function terapkan(dariKlik) {
    var n = 0;
    kartu.forEach(function (el) {
      var lolosJenis = state.jenis === "semua" || el.getAttribute("data-jenis") === state.jenis;
      var lolosUntuk = state.untuk === "semua" || el.getAttribute("data-untuk") === state.untuk;
      var tampil = lolosJenis && lolosUntuk;
      el.hidden = !tampil;
      if (tampil) n += 1;
    });
    document.querySelectorAll("[data-filter]").forEach(function (tombol) {
      var grup = tombol.getAttribute("data-filter");
      var nyala = tombol.getAttribute("data-value") === state[grup];
      tombol.setAttribute("aria-pressed", nyala ? "true" : "false");
    });
    if (info) {
      info.textContent = n === 0 ? "0 perbandingan" : n + " perbandingan";
    }
    if (kosong) {
      kosong.hidden = n !== 0;
      if (n === 0) {
        kosong.textContent = state.jenis === "facial-wash"
          ? "Facial wash belum bisa dijejerin. Di data toko resmi yang punya link affiliate, semuanya merek lokal. Belum ada facial wash Korea buat pasangan head-to-head."
          : "Belum ada perbandingan di filter ini.";
      }
    }
    var q = new URLSearchParams();
    if (state.jenis !== "semua") q.set("jenis", state.jenis);
    if (state.untuk !== "semua") q.set("untuk", state.untuk);
    var berikutnya = location.pathname + (q.toString() ? "?" + q.toString() : "");
    if (dariKlik) history.pushState(state, "", berikutnya);
    else history.replaceState(state, "", berikutnya);
  }

  document.querySelectorAll("[data-filter]").forEach(function (tombol) {
    tombol.addEventListener("click", function () {
      state[tombol.getAttribute("data-filter")] = tombol.getAttribute("data-value");
      terapkan(true);
    });
  });

  window.addEventListener("popstate", function () {
    var ulang = new URLSearchParams(location.search);
    state.jenis = jenisOk[ulang.get("jenis")] ? ulang.get("jenis") : "semua";
    state.untuk = untukOk[ulang.get("untuk")] ? ulang.get("untuk") : "semua";
    terapkan(false);
  });

  terapkan(false);
})();
