/* Bagian "Top 10 Terlaris" di beranda: tab per kategori + daftar peringkat #1-#10.
   Data: window.TOP10 (dibuat tools/build_data.py dari top10-kandidat.psv). */
(function () {
  var S = window.Situs;
  var data = (window.TOP10 || []).filter(function (t) { return t.produk && t.produk.length; });
  var sec = document.getElementById("top10");
  var elTabs = document.getElementById("top10-tabs");
  var elPanel = document.getElementById("top10-panel");
  if (!sec || !S) return;
  if (!data.length) { sec.hidden = true; return; }

  function baris(p, i) {
    var link = "review.html?id=" + encodeURIComponent(p.id), s = S.linkShopee(p);
    var sold = p.terjualTotal != null ? S.terjualTotalTeks(p) : S.terjualTeks(p) + " terjual/bln";
    return '<li class="t10-row">' +
      '<span class="t10-rank' + (i < 3 ? " t10-rank-" + (i + 1) : "") + '" aria-label="Peringkat ' + (i + 1) + '">' + (i + 1) + "</span>" +
      '<span class="t10-img">' + S.gambar(p, false, true) + "</span>" +
      '<div class="t10-info">' +
        '<a class="t10-nama" href="' + link + '" title="' + S.esc(p.nama) + '">' + S.esc(S.judulPendek(p.nama, 7)) + "</a>" +
        '<div class="t10-meta"><b class="t10-harga">' + S.esc(S.rupiah(p.harga)) + "</b>" +
          '<span class="t10-rating">⭐ ' + Number(p.rating).toFixed(1) + "</span>" +
          '<span class="t10-sold">' + S.esc(sold) + "</span></div>" +
      "</div>" +
      (s ? '<a class="t10-btn" href="' + S.esc(s) + '" ' + S.REL + ' aria-label="Cek ' + S.esc(S.judulPendek(p.nama, 5)) + ' di Shopee">Cek di Shopee</a>' : "") +
      "</li>";
  }

  elTabs.innerHTML = data.map(function (t, i) {
    return '<button type="button" role="tab" class="t10-tab" id="t10-tab-' + i + '" aria-controls="t10-list-' + i + '"' +
      ' aria-selected="' + (i === 0) + '" tabindex="' + (i === 0 ? 0 : -1) + '">' + t.ikon + " " + S.esc(t.kategori) + "</button>";
  }).join("");
  elPanel.innerHTML = data.map(function (t, i) {
    var list = t.produk.map(function (id) { return S.produkById[id]; }).filter(Boolean);
    return '<ol class="t10-list" role="tabpanel" id="t10-list-' + i + '" aria-labelledby="t10-tab-' + i + '"' +
      (i === 0 ? "" : " hidden") + ">" + list.map(baris).join("") + "</ol>";
  }).join("");

  var tabs = [].slice.call(elTabs.querySelectorAll(".t10-tab"));
  var lists = [].slice.call(elPanel.querySelectorAll(".t10-list"));
  function pilih(i, fokus) {
    tabs.forEach(function (b, j) {
      b.setAttribute("aria-selected", j === i ? "true" : "false");
      b.tabIndex = j === i ? 0 : -1;
      lists[j].hidden = j !== i;
    });
    if (fokus) tabs[i].focus();
    tabs[i].scrollIntoView({ block: "nearest", inline: "nearest" });
  }
  tabs.forEach(function (b, i) { b.addEventListener("click", function () { pilih(i); }); });
  elTabs.addEventListener("keydown", function (e) {
    var i = tabs.indexOf(document.activeElement);
    if (i < 0) return;
    var k = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
    if (k === undefined) return;
    e.preventDefault();
    pilih((k + tabs.length) % tabs.length, true);
  });
  window.Top10 = { pilih: pilih };
})();
