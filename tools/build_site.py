#!/usr/bin/env python3
"""Bangun situs statis Bandingin.id: perbandingan skincare lokal vs Korea.

    python3 tools/build_site.py            # pakai gambar yang sudah ada
    python3 tools/build_site.py --gambar   # unduh ulang gambar produk

Sumber: sumber/*.psv, sumber/merek-korea.txt, sumber/posted.log, tools/pasangan.json
Hasil: index.html, banding/*.html, img/*.jpg
"""
import argparse, json, os, re, sys, urllib.request
from html import escape
from io import BytesIO
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMBER = os.path.join(ROOT, "sumber")
IMG = os.path.join(ROOT, "img")
BANDING = os.path.join(ROOT, "banding")

JENIS = [
    ("pelembab", "Pelembab"),
    ("serum", "Serum"),
    ("sunscreen", "Sunscreen"),
]
JENIS_LABEL = dict(JENIS)

BANNED = re.compile(
    r"\b(pria|wanita|cowok|cewek|perempuan|laki-laki|for men|terjual|rating|"
    r"bintang|terlaris|paling laku|belum dicoba|menyembuhkan|mengobati)\b|"
    r"rb\+|★|☆",
    re.I,
)

ALASAN_LEWAT = {
    "facial": (
        "Tidak ada facial wash merek Korea di data, dan tidak ada analisa kandungan. "
        "Perbandingan lokal vs Korea tidak dibuat supaya tidak mengarang produk atau daftar bahan."
    ),
    "20774296730": "Garnier bukan merek lokal Indonesia dan tidak ada di daftar merek Korea, jadi tidak masuk sisi mana pun.",
    "24386158862": (
        "Pelembap Korea yang belum terpakai hanya Nature Republic, dan itu dipasangkan dengan Wardah Plump & Firm. "
        "Kahf ini gabungan pelembap dan sunscreen SPF 35, dan setiap produk hanya dipakai sekali."
    ),
    "29319814911": (
        "Slot pelembap Korea yang tersisa sudah dipakai Wardah vs Nature Republic. "
        "Analisa juga menyebut informasi bahan lengkapnya terbatas."
    ),
    "28471442468": (
        "Penjualan bulanan di data lebih rendah daripada Wardah C-Glow dan OMG serum, "
        "yang mengisi slot serum Korea tersisa. Konsentrasi bahannya juga tidak dipublikasikan."
    ),
    "25142085435": (
        "Penjualan bulanan di data lebih rendah daripada serum lokal yang dipasangkan "
        "(Wardah C-Glow dan OMG, sama-sama 1rb+ per bulan di data)."
    ),
    "5276988352": (
        "Sunscreen Korea yang tersisa (SOME BY MI V10) dipasangkan dengan Wardah UV Shield, "
        "yang penjualan bulanannya lebih tinggi di data."
    ),
}


def esc(s):
    return escape(str(s if s is not None else ""), quote=True)


def parse_rp(teks):
    if teks is None:
        return None
    t = teks.strip()
    if t in ("", "-"):
        return None
    digit = re.sub(r"[^\d]", "", t)
    return int(digit) if digit else None


def rp(n):
    return "Rp" + f"{int(n):,}".replace(",", ".")


def diskon(harga, asli):
    if not harga or not asli or asli <= harga:
        return None
    persen = int(round((asli - harga) * 100 / asli))
    return persen if persen >= 1 else None


def item_id(url):
    m = re.search(r"/(\d+)$", url.strip())
    if not m:
        raise SystemExit(f"URL tanpa item id: {url}")
    return m.group(1)


def muat_merek():
    path = os.path.join(SUMBER, "merek-korea.txt")
    merek = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                merek.append(line)
    return merek


def judul_korea(judul, merek):
    t = judul.lower()
    return any(m.lower() in t for m in merek)


def muat_produk():
    aff = {}
    with open(os.path.join(SUMBER, "affiliate-links.psv"), encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            bagian = [p.strip() for p in line.split(" | ")]
            if len(bagian) != 3:
                raise SystemExit(f"affiliate-links.psv baris {n} bukan 3 kolom")
            if not bagian[2].startswith("https://s.shopee.co.id/"):
                raise SystemExit(f"Bukan link pendek: {bagian[2]}")
            aff[item_id(bagian[1])] = bagian[2]

    produk = {}
    for nama_file in ("perempuan.psv", "pria.psv"):
        with open(os.path.join(SUMBER, nama_file), encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                p = [x.strip() for x in line.split(" | ")]
                if len(p) != 10:
                    raise SystemExit(f"{nama_file} baris {n} bukan 10 kolom")
                iid = item_id(p[8])
                if iid not in aff:
                    raise SystemExit(f"{iid} tidak punya link affiliate pendek")
                produk[iid] = {
                    "id": iid,
                    "keyword": p[0],
                    "judul": p[1],
                    "harga": parse_rp(p[2]),
                    "asli": parse_rp(p[3]),
                    "url": p[8],
                    "gambar": p[9],
                    "aff": aff[iid],
                }
    return produk


def muat_posted():
    pasangan = []
    with open(os.path.join(SUMBER, "posted.log"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            bagian = [p.strip() for p in line.split(" | ")]
            pasangan.append((item_id(bagian[1]), item_id(bagian[2]), bagian[3]))
    return pasangan


def pastikan_gambar(produk, pasangan, ulang):
    os.makedirs(IMG, exist_ok=True)
    butuh = []
    for pair in pasangan:
        butuh.append(pair["lokal"])
        butuh.append(pair["korea"])
    for iid in butuh:
        tujuan = os.path.join(IMG, iid + ".jpg")
        if os.path.exists(tujuan) and os.path.getsize(tujuan) > 1000 and not ulang:
            continue
        url = produk[iid]["gambar"]
        terakhir = None
        for _ in range(3):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=40) as resp:
                    data = resp.read()
                im = Image.open(BytesIO(data)).convert("RGB")
                im.thumbnail((720, 720), Image.Resampling.LANCZOS)
                im.save(tujuan, "JPEG", quality=82, optimize=True)
                terakhir = None
                break
            except Exception as e:
                terakhir = e
        if terakhir:
            raise SystemExit(f"Gagal mengunduh gambar {iid}: {terakhir}")
        print("gambar", iid, os.path.getsize(tujuan))


def harga_html(p):
    potong = diskon(p["harga"], p["asli"])
    html = f'<span class="now">{esc(rp(p["harga"]))}</span>'
    if potong:
        html += f' <s>{esc(rp(p["asli"]))}</s> <span class="off">−{potong}%</span>'
    return html


def list_bahan(produk_copy):
    item = []
    for b in produk_copy["bahan"]:
        item.append(
            "<li><strong>" + esc(b["nama"]) + "</strong> "
            "<span>" + esc(b["fungsi"]) + "</span></li>"
        )
    return "<ul class=\"bahan\">" + "".join(item) + "</ul>"


def list_manfaat(produk_copy):
    return "<ul class=\"manfaat\">" + "".join(f"<li>{esc(m)}</li>" for m in produk_copy["manfaat"]) + "</ul>"


def kulit_html(produk_copy):
    return "".join(f'<li>{esc(k)}</li>' for k in produk_copy["kulit"])


def foto(iid, nama, eager=False):
    lazy = "" if eager else ' loading="lazy"'
    return (
        f'<img src="{{base}}img/{esc(iid)}.jpg" alt="{esc(nama)}" width="720" height="720"'
        f'{lazy} decoding="async">'
    )


def head(title, description, base, canonical_path):
    # canonical_path unused; relative assets only, supaya GitHub Pages di subfolder tetap jalan.
    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#f3efe7">
  <link rel="stylesheet" href="{base}css/style.css">
  <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='%230c6b52'/><text x='32' y='40' text-anchor='middle' font-family='Georgia,serif' font-size='22' fill='white'>vs</text></svg>">
</head>
"""


def header(base, aktif=None):
    tautan = []
    for kunci, label in JENIS:
        href = f"{base}index.html#{kunci}"
        kelas = " class=\"aktif\"" if aktif == kunci else ""
        aria = " aria-current=\"true\"" if aktif == kunci else ""
        tautan.append(f'<a href="{href}"{kelas}{aria}>{esc(label)}</a>')
    kelas_p = " class=\"aktif\"" if aktif == "pendapat" else ""
    aria_p = " aria-current=\"page\"" if aktif == "pendapat" else ""
    tautan.append(f'<a href="{base}ulasan.html"{kelas_p}{aria_p}>Kasih Pendapat</a>')
    return f"""<a class="skip" href="{base}index.html#daftar">Langsung ke perbandingan</a>
<header class="site-header">
  <div class="wrap nav">
    <a class="logo" href="{base}index.html"><span class="mark" aria-hidden="true">vs</span>Bandingin<span class="tld">.id</span></a>
    <nav class="nav-links" aria-label="Menu">
      {''.join(tautan)}
    </nav>
  </div>
</header>
"""


def footer(base, tanggal):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p class="footnote" id="disclosure">Ulasan disusun dari analisa kandungan dan informasi produk. Bandingin.id mendapat komisi dari link affiliate.</p>
    <p class="footer-nav"><a href="{base}ulasan.html">Kasih Pendapat</a></p>
    <p class="copy">© 2026 Bandingin.id · Harga mengikuti listing Shopee per {esc(tanggal)} dan bisa berubah.</p>
  </div>
</footer>
"""


def beli(p, nama, kelas="btn"):
    return (
        f'<a class="{kelas}" href="{esc(p["aff"])}" target="_blank" rel="sponsored noopener noreferrer"'
        f' aria-label="Beli {esc(nama)} di Shopee">Beli di Shopee</a>'
    )


def foto_tautan(p, copy, asal, eager, href, base):
    foto_html = foto(p["id"], copy["nama"], eager).replace("{base}", base)
    return f'<a class="photo photo-{asal}" href="{esc(href)}">{foto_html}</a>'


def meta_kartu(p, copy, asal, href):
    badge = "Lokal" if asal == "lokal" else "Korea"
    return f"""<div class="sisi sisi-{asal}">
      <p class="asal asal-{asal}">{badge}</p>
      <h3><a href="{esc(href)}">{esc(copy["nama"])}</a></h3>
      <p class="harga">{harga_html(p)}</p>
      {beli(p, copy["nama"])}
    </div>"""


def render_index(data, produk, pasangan):
    kartu = []
    for i, pair in enumerate(pasangan):
        lok = produk[pair["lokal"]]
        kor = produk[pair["korea"]]
        cl = pair["produk"][pair["lokal"]]
        ck = pair["produk"][pair["korea"]]
        href = f"banding/{pair['id']}.html"
        cari = " ".join([
            pair["hook"], pair["ringkas"], cl["nama"], ck["nama"],
            JENIS_LABEL[pair["jenis"]],
            " ".join(b["nama"] for b in cl["bahan"]),
            " ".join(b["nama"] for b in ck["bahan"]),
        ]).lower()
        kartu.append(f"""<article class="duel" data-jenis="{esc(pair["jenis"])}" data-cari="{esc(cari)}">
  <p class="kicker">{esc(JENIS_LABEL[pair["jenis"]])}</p>
  <h2><a href="{href}">{esc(pair["hook"])}</a></h2>
  <p class="lawan">{esc(cl["nama"])} <span>vs</span> {esc(ck["nama"])}</p>
  <div class="duo">
    {foto_tautan(lok, cl, "lokal", i == 0, href, "")}
    <div class="vs" aria-hidden="true">vs</div>
    {foto_tautan(kor, ck, "korea", i == 0, href, "")}
    {meta_kartu(lok, cl, "lokal", href)}
    {meta_kartu(kor, ck, "korea", href)}
  </div>
  <p class="ringkas">{esc(pair["ringkas"])}</p>
  <a class="more" href="{href}">Lihat perbandingan</a>
</article>""")

    chips = ['<button type="button" class="chip aktif" data-filter="semua" aria-pressed="true">Semua</button>']
    for kunci, label in JENIS:
        n = sum(1 for p in pasangan if p["jenis"] == kunci)
        chips.append(
            f'<button type="button" class="chip" data-filter="{kunci}" aria-pressed="false">{esc(label)} <span class="count">{n}</span></button>'
        )

    desk = (
        "Bandingin pelembab, serum, dan sunscreen. Satu merek lokal dibanding satu merek Korea "
        "yang sejenis: kandungan, harga, dan cocok untuk kulit yang mana."
    )
    html = head(
        "Bandingin.id — Pelembab, Serum, dan Sunscreen Lokal vs Korea",
        desk,
        "",
        "index.html",
    )
    html += f"""<body>
{header("")}
<main>
  <section class="hero">
    <div class="wrap">
      <p class="kicker kicker-terang">Skincare lokal vs Korea</p>
      <h1>Lokal vs Korea, mending yang mana?</h1>
      <p>Pelembab, serum, dan sunscreen. Satu merek lokal, satu merek Korea, jenis yang sama. Lihat kandungan, harga, dan cocok untuk kulit yang mana.</p>
      <form class="search" id="form-cari" role="search">
        <label class="sr" for="q">Cari perbandingan</label>
        <input id="q" type="search" placeholder="Cari merek atau bahan, misalnya niacinamide" autocomplete="off">
      </form>
    </div>
  </section>
  <div class="wrap" id="daftar">
    <div class="filter" role="group" aria-label="Filter jenis">{''.join(chips)}</div>
    <p class="hasil" id="hasil" aria-live="polite">{len(pasangan)} perbandingan</p>
    <div class="list" id="list">
      {''.join(kartu)}
    </div>
    <p class="kosong" id="kosong" hidden>Tidak ada perbandingan yang cocok.</p>
    <aside class="panduan">
      <p>Mau urutan pakai yang lebih lengkap?</p>
      <a href="https://lynk.id/albijulian">Panduan skincare lengkap</a>
    </aside>
  </div>
</main>
{footer("", data["tanggal"])}
<script>
(function () {{
  var jenis = "semua";
  var q = document.getElementById("q");
  var chips = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
  var kartu = Array.prototype.slice.call(document.querySelectorAll(".duel"));
  var hasil = document.getElementById("hasil");
  var kosong = document.getElementById("kosong");
  var sah = {{ pelembab: 1, serum: 1, sunscreen: 1, semua: 1 }};

  function terapkan() {{
    var s = (q.value || "").toLowerCase().trim();
    var n = 0;
    kartu.forEach(function (el) {{
      var okJ = jenis === "semua" || el.getAttribute("data-jenis") === jenis;
      var okS = !s || el.getAttribute("data-cari").indexOf(s) !== -1;
      var tampil = okJ && okS;
      el.hidden = !tampil;
      if (tampil) n++;
    }});
    var kata = n === 1 ? "perbandingan" : "perbandingan";
    hasil.textContent = n + " " + kata;
    kosong.hidden = n !== 0;
  }}

  function setJenis(nilai, dariHash) {{
    if (!sah[nilai]) nilai = "semua";
    jenis = nilai;
    chips.forEach(function (c) {{
      var aktif = c.getAttribute("data-filter") === jenis;
      c.classList.toggle("aktif", aktif);
      c.setAttribute("aria-pressed", aktif ? "true" : "false");
    }});
    document.querySelectorAll(".nav-links a").forEach(function (a) {{
      var href = a.getAttribute("href") || "";
      var kunci = href.split("#")[1] || "";
      var aktif = kunci === jenis;
      a.classList.toggle("aktif", aktif);
      if (aktif) a.setAttribute("aria-current", "true");
      else a.removeAttribute("aria-current");
    }});
    if (!dariHash) {{
      var url = lokasiTanpaHash() + (jenis === "semua" ? "" : "#" + jenis);
      history.replaceState(null, "", url);
    }}
    terapkan();
  }}

  function lokasiTanpaHash() {{
    return location.pathname + location.search;
  }}

  chips.forEach(function (c) {{
    c.addEventListener("click", function () {{ setJenis(c.getAttribute("data-filter"), false); }});
  }});
  q.addEventListener("input", terapkan);
  document.getElementById("form-cari").addEventListener("submit", function (e) {{
    e.preventDefault();
    terapkan();
  }});
  document.querySelectorAll(".nav-links a").forEach(function (a) {{
    a.addEventListener("click", function (e) {{
      var kunci = (a.getAttribute("href") || "").split("#")[1];
      if (!kunci) return;
      e.preventDefault();
      setJenis(kunci, false);
      document.getElementById("daftar").scrollIntoView({{ behavior: "smooth", block: "start" }});
    }});
  }});

  var hash = (location.hash || "").replace("#", "");
  if (sah[hash]) setJenis(hash, true);
}})();
</script>
</body>
</html>
"""
    return html


def render_pair(data, produk, pair):
    lok = produk[pair["lokal"]]
    kor = produk[pair["korea"]]
    cl = pair["produk"][pair["lokal"]]
    ck = pair["produk"][pair["korea"]]
    base = "../"
    judul = f"{pair['hook']} {cl['nama']} vs {ck['nama']}"
    desk = pair["ringkas"]
    x = ""
    if pair.get("x"):
        x = f'<p class="lihat-x"><a href="{esc(pair["x"])}" target="_blank" rel="noopener noreferrer">Lihat di X</a></p>'

    def blok_atas(p, copy, asal):
        badge = "Lokal" if asal == "lokal" else "Korea"
        foto_html = foto(p["id"], copy["nama"], True).replace("{base}", base)
        return (
            f'<div class="photo photo-{asal}">{foto_html}</div>',
            f"""<div class="sisi sisi-{asal}">
      <p class="asal asal-{asal}">{badge}</p>
      <h2>{esc(copy["nama"])}</h2>
      <p class="tekstur">{esc(copy["tekstur"])}</p>
      <ul class="kulit">{kulit_html(copy)}</ul>
      <p class="harga">{harga_html(p)}</p>
      {beli(p, copy["nama"])}
    </div>""",
        )

    def blok_detail(p, copy, asal):
        badge = "Lokal" if asal == "lokal" else "Korea"
        return f"""<article class="detail sisi-{asal}" id="{asal}">
      <p class="asal asal-{asal}">{badge}</p>
      <h2>{esc(copy["nama"])}</h2>
      <p class="tekstur">{esc(copy["tekstur"])} · {esc(copy["isi"])}</p>
      <h3>Kandungan utama</h3>
      {list_bahan(copy)}
      <h3>Manfaat</h3>
      {list_manfaat(copy)}
      <h3>Cocok untuk kulit</h3>
      <ul class="kulit">{kulit_html(copy)}</ul>
      <p class="catatan">{esc(copy["catatan"])}</p>
      <p class="harga">{harga_html(p)}</p>
      {beli(p, copy["nama"])}
    </article>"""

    def sel_beli(p, copy):
        return beli(p, copy["nama"], "btn btn-sm")

    tabel = f"""<div class="tabel-wrap">
      <table class="cmp">
        <caption class="sr">Perbandingan {esc(cl["nama"])} dan {esc(ck["nama"])}</caption>
        <thead>
          <tr><th scope="col"> </th><th scope="col">Lokal</th><th scope="col">Korea</th></tr>
        </thead>
        <tbody>
          <tr><th scope="row">Tekstur</th><td>{esc(cl["tekstur"])}</td><td>{esc(ck["tekstur"])}</td></tr>
          <tr><th scope="row">Cocok untuk</th><td>{esc(", ".join(cl["kulit"]))}</td><td>{esc(", ".join(ck["kulit"]))}</td></tr>
          <tr><th scope="row">Isi</th><td>{esc(cl["isi"])}</td><td>{esc(ck["isi"])}</td></tr>
          <tr><th scope="row">Harga</th><td>{harga_html(lok)}</td><td>{harga_html(kor)}</td></tr>
          <tr><th scope="row">Beli</th><td>{sel_beli(lok, cl)}</td><td>{sel_beli(kor, ck)}</td></tr>
        </tbody>
      </table>
    </div>"""

    v = pair["verdict"]
    foto_l, meta_l = blok_atas(lok, cl, "lokal")
    foto_k, meta_k = blok_atas(kor, ck, "korea")
    html = head(judul + " — Bandingin.id", desk, base, "")
    html += f"""<body>
{header(base, pair["jenis"])}
<main class="wrap artikel">
  <p class="crumbs"><a href="../index.html">Beranda</a> / <a href="../index.html#{esc(pair["jenis"])}">{esc(JENIS_LABEL[pair["jenis"]])}</a></p>
  <p class="kicker">{esc(JENIS_LABEL[pair["jenis"]])}</p>
  <h1>{esc(pair["hook"])}</h1>
  <p class="lawan lawan-besar">{esc(cl["nama"])} <span>vs</span> {esc(ck["nama"])}</p>
  {x}
  <div class="duo duo-halaman">
    {foto_l}
    <div class="vs" aria-hidden="true">vs</div>
    {foto_k}
    {meta_l}
    {meta_k}
  </div>
  <h2 class="bagian">Perbandingan singkat</h2>
  {tabel}
  <h2 class="bagian">Kandungan dan manfaat</h2>
  <div class="detail-grid">
    {blok_detail(lok, cl, "lokal")}
    {blok_detail(kor, ck, "korea")}
  </div>
  <section class="verdict">
    <h2>Jadi, mending yang mana?</h2>
    <div class="v-grid">
      <article>
        <h3>Kulit berminyak atau berjerawat</h3>
        <p>{esc(v["berminyak"])}</p>
      </article>
      <article>
        <h3>Kulit kering atau sensitif</h3>
        <p>{esc(v["kering"])}</p>
      </article>
      <article>
        <h3>Budget atau kandungan</h3>
        <p>{esc(v["budget"])}</p>
      </article>
    </div>
  </section>
  <aside class="ajak-pendapat">
    <p>Membantu milih, atau masih ada yang membingungkan?</p>
    <a class="more" href="../ulasan.html?baca={esc(pair["id"])}">Kasih pendapat</a>
  </aside>
  <p class="kembali"><a href="../index.html#{esc(pair["jenis"])}">Semua {esc(JENIS_LABEL[pair["jenis"]].lower())}</a></p>
</main>
{footer(base, data["tanggal"])}
</body>
</html>
"""
    return html


def render_ulasan(data, pasangan):
    opsi = ['<option value="">Lewati saja</option>']
    for pair in pasangan:
        cl = pair["produk"][pair["lokal"]]["nama"]
        ck = pair["produk"][pair["korea"]]["nama"]
        label = f'{JENIS_LABEL[pair["jenis"]]}: {cl} vs {ck}'
        opsi.append(f'<option value="{esc(pair["id"])}">{esc(label)}</option>')
    angka = []
    for n in range(1, 6):
        angka.append(f'<label><input type="radio" name="mudah" value="{n}"> {n}</label>')
    desk = "Kasih pendapat tentang Bandingin.id: apakah perbandingannya membantu memilih produk, plus saran dan kritik."
    html = head("Kasih Pendapat — Bandingin.id", desk, "", "ulasan.html")
    html += f"""<body>
{header("", "pendapat")}
<main class="wrap artikel">
  <p class="crumbs"><a href="index.html">Beranda</a> / Kasih Pendapat</p>
  <h1>Kasih pendapat</h1>
  <p class="intro-form">Albi lagi kumpulin masukan. Yang wajib cuma pertanyaan pertama. Sisanya boleh dikosongkan.</p>
  <form class="form-kartu" id="form-pendapat" action="#" method="post" novalidate>
    <fieldset class="field">
      <legend>Apakah website ini membantu kamu memutuskan produk mana yang dibeli?</legend>
      <div class="pilihan">
        <label><input type="radio" name="membantu" value="ya" required> Ya, sangat</label>
        <label><input type="radio" name="membantu" value="lumayan" required> Lumayan</label>
        <label><input type="radio" name="membantu" value="tidak" required> Tidak</label>
      </div>
    </fieldset>
    <div class="field">
      <label class="label" for="perbandingan">Perbandingan mana yang kamu baca? <span class="opsional">opsional</span></label>
      <select id="perbandingan" name="perbandingan">
        {''.join(opsi)}
      </select>
    </div>
    <fieldset class="field">
      <legend>Seberapa mudah dipahami? <span class="hint">1 susah, 5 gampang. Boleh dikosongkan.</span></legend>
      <div class="pilihan pilihan-angka">
        {''.join(angka)}
      </div>
    </fieldset>
    <div class="field">
      <label class="label" for="kurang">Apa yang kurang atau membingungkan? <span class="opsional">opsional</span></label>
      <textarea id="kurang" name="kurang" maxlength="2000"></textarea>
    </div>
    <div class="field">
      <label class="label" for="saran">Saran untuk website ini? <span class="opsional">opsional</span></label>
      <textarea id="saran" name="saran" maxlength="2000"></textarea>
    </div>
    <div class="field">
      <label class="label" for="berikutnya">Produk atau jenis skincare apa yang ingin dibandingkan berikutnya? <span class="opsional">opsional</span></label>
      <textarea id="berikutnya" name="berikutnya" maxlength="2000"></textarea>
    </div>
    <div class="field">
      <label class="label" for="kontak">Nama atau kontak <span class="opsional">opsional</span></label>
      <input id="kontak" name="kontak" type="text" maxlength="200" autocomplete="name" placeholder="Nama, email, atau Instagram">
    </div>
    <button class="btn btn-kirim" type="submit">Kirim pendapat</button>
  </form>
  <section class="sukses" id="sukses" hidden aria-live="polite">
    <h2 id="sukses-judul"></h2>
    <p id="sukses-teks"></p>
    <div id="salinan" hidden>
      <label class="label" for="teks-salinan">Jawaban kamu</label>
      <textarea id="teks-salinan" readonly></textarea>
      <button class="btn btn-salin" id="salin" type="button">Salin jawaban</button>
    </div>
  </section>
  <noscript><p class="catatan">Untuk mengirim pendapat, nyalakan JavaScript.</p></noscript>
</main>
{footer("", data["tanggal"])}
<script src="js/config.js"></script>
<script src="js/ulasan.js"></script>
</body>
</html>
"""
    return html


def periksa(html_per_path, produk, pasangan, posted, merek):
    if len(posted) < 1:
        raise SystemExit("posted.log kosong")
    for i, (a, b, xurl) in enumerate(posted):
        pair = pasangan[i]
        if pair["lokal"] != a or pair["korea"] != b:
            raise SystemExit(f"Urutan posting tidak cocok di indeks {i}: {pair['id']}")
        if pair.get("x") != xurl:
            raise SystemExit(f"Link X tidak cocok untuk {pair['id']}")

    terpakai = []
    for pair in pasangan:
        if pair["jenis"] not in JENIS_LABEL:
            raise SystemExit("Jenis tidak dikenal: " + pair["jenis"])
        for sisi, iid in (("lokal", pair["lokal"]), ("korea", pair["korea"])):
            if iid not in pair["produk"]:
                raise SystemExit(f"{pair['id']} tanpa teks {iid}")
            p = produk[iid]
            if not p["aff"].startswith("https://s.shopee.co.id/"):
                raise SystemExit("Link affiliate salah " + iid)
            korea = judul_korea(p["judul"], merek)
            if sisi == "korea" and not korea:
                raise SystemExit(f"{iid} bukan merek Korea: {p['judul'][:80]}")
            if sisi == "lokal" and korea:
                raise SystemExit(f"{iid} terdeteksi merek Korea, dipakai sebagai lokal")
            copy = pair["produk"][iid]
            for kunci in ("nama", "tekstur", "isi", "catatan", "bahan", "manfaat", "kulit"):
                if not copy.get(kunci):
                    raise SystemExit(f"{pair['id']} {iid} kosong: {kunci}")
            if len(copy["bahan"]) < 1 or len(copy["manfaat"]) < 2 or len(copy["kulit"]) < 1:
                raise SystemExit(f"{pair['id']} {iid} isi kurang")
        if pair["lebihMurah"] not in ("lokal", "korea"):
            raise SystemExit("lebihMurah salah " + pair["id"])
        hl = produk[pair["lokal"]]["harga"]
        hk = produk[pair["korea"]]["harga"]
        if pair["lebihMurah"] == "lokal" and not (hl < hk):
            raise SystemExit(f"{pair['id']} lokal tidak lebih murah")
        if pair["lebihMurah"] == "korea" and not (hk < hl):
            raise SystemExit(f"{pair['id']} Korea tidak lebih murah")
        for kunci in ("berminyak", "kering", "budget"):
            if not pair["verdict"].get(kunci):
                raise SystemExit(f"verdict {kunci} kosong {pair['id']}")
        terpakai.extend([pair["lokal"], pair["korea"]])
    if len(terpakai) != len(set(terpakai)):
        raise SystemExit("Ada produk yang dipakai lebih dari sekali")

    for jenis, _ in JENIS:
        if not any(p["jenis"] == jenis for p in pasangan):
            raise SystemExit("Tidak ada perbandingan untuk " + jenis)

    for path, html in html_per_path.items():
        if BANNED.search(html):
            m = BANNED.search(html)
            cuplikan = html[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
            raise SystemExit(f"Kata terlarang di {path}: {m.group(0)!r} … {cuplikan}")
        if "★" in html or "☆" in html:
            raise SystemExit("Simbol rating muncul di " + path)
        for m in re.finditer(r'href="([^"]+)"', html):
            href = m.group(1)
            if href.startswith("https://s.shopee.co.id/"):
                continue
            if href.startswith("https://x.com/") or href.startswith("https://lynk.id/"):
                continue
            if href.startswith("#") or href.startswith("data:"):
                continue
            if href.startswith("mailto:"):
                raise SystemExit("mailto tidak dipakai")
            # sisanya harus file lokal (buang query dan hash)
            bersih = href.split("#", 1)[0].split("?", 1)[0]
            if not bersih:
                continue
            tujuan = os.path.normpath(os.path.join(ROOT, os.path.dirname(path), bersih))
            if not os.path.isfile(tujuan):
                raise SystemExit(f"Tautan putus di {path}: {href} -> {tujuan}")
        for m in re.finditer(r'src="([^"]+)"', html):
            src = m.group(1)
            if src.startswith("data:"):
                continue
            tujuan = os.path.normpath(os.path.join(ROOT, os.path.dirname(path), src))
            if not os.path.isfile(tujuan):
                raise SystemExit(f"Gambar putus di {path}: {src}")
        # tombol beli hanya link pendek. Halaman pendapat tidak menjual produk.
        if path not in ("index.html", "ulasan.html") and "Beli di Shopee" not in html:
            raise SystemExit("Tidak ada tombol beli di " + path)

    index = html_per_path["index.html"]
    if index.count("https://lynk.id/albijulian") != 1:
        raise SystemExit("Tautan panduan harus tepat satu kali, di beranda")
    for path, html in html_per_path.items():
        if path != "index.html" and "lynk.id" in html:
            raise SystemExit("Panduan tidak boleh muncul di " + path)
        if path not in ("ulasan.html", "banding/index.html") and "s.shopee.co.id" not in html:
            raise SystemExit("Tidak ada link Shopee di " + path)

    ulasan = html_per_path["ulasan.html"]
    if "js/config.js" not in ulasan or "js/ulasan.js" not in ulasan:
        raise SystemExit("ulasan.html tidak memuat skrip pendapat")
    if "FEEDBACK_ENDPOINT" not in open(os.path.join(ROOT, "js/config.js"), encoding="utf-8").read():
        raise SystemExit("js/config.js tidak punya FEEDBACK_ENDPOINT")
    for pair in pasangan:
        if f'value="{pair["id"]}"' not in ulasan:
            raise SystemExit("Dropdown pendapat tidak memuat " + pair["id"])
        if f'ulasan.html?baca={pair["id"]}' not in html_per_path[f"banding/{pair['id']}.html"]:
            raise SystemExit("Ajakan pendapat hilang di " + pair["id"])

    # setiap tombol beli di situs memakai link yang ada di data
    aff_sah = {p["aff"] for p in produk.values()}
    for path, html in html_per_path.items():
        for m in re.finditer(r'https://s\.shopee\.co\.id/[A-Za-z0-9]+', html):
            if m.group(0) not in aff_sah:
                raise SystemExit(f"Link Shopee tidak dikenal di {path}: {m.group(0)}")


def laporan(produk, pasangan):
    terpakai = {p["lokal"] for p in pasangan} | {p["korea"] for p in pasangan}
    print("\nPerbandingan:")
    hitung = {}
    for pair in pasangan:
        hitung[pair["jenis"]] = hitung.get(pair["jenis"], 0) + 1
    for jenis, label in JENIS:
        print(f"  {label}: {hitung.get(jenis, 0)}")
    print("Dilewati:")
    for iid, p in produk.items():
        if iid in terpakai:
            continue
        alasan = ALASAN_LEWAT.get(iid) or ALASAN_LEWAT.get(p["keyword"].split()[0], "Tidak dipasangkan.")
        if p["keyword"].startswith("facial"):
            alasan = ALASAN_LEWAT["facial"]
        print(f"  - {iid} | {p['judul'][:90]}")
        print(f"    {alasan}")


def tulis_redirect():
    html = """<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=index.html">
  <title>Bandingin.id</title>
  <link rel="canonical" href="index.html">
  <script>location.replace("index.html");</script>
</head>
<body>
  <p><a href="index.html">Ke beranda Bandingin.id</a></p>
</body>
</html>
"""
    for nama in ("review.html", "perbandingan.html"):
        with open(os.path.join(ROOT, nama), "w", encoding="utf-8") as f:
            f.write(html)
    os.makedirs(BANDING, exist_ok=True)
    with open(os.path.join(BANDING, "index.html"), "w", encoding="utf-8") as f:
        f.write(html.replace("index.html", "../index.html"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gambar", action="store_true", help="unduh ulang gambar")
    args = ap.parse_args()
    os.chdir(ROOT)
    with open(os.path.join(ROOT, "tools", "pasangan.json"), encoding="utf-8") as f:
        data = json.load(f)
    produk = muat_produk()
    merek = muat_merek()
    posted = muat_posted()
    pasangan = data["pasangan"]
    for pair in pasangan:
        for iid in (pair["lokal"], pair["korea"]):
            if iid not in produk:
                raise SystemExit(f"{iid} tidak ada di data, atau tidak punya link affiliate")
    pastikan_gambar(produk, pasangan, args.gambar)
    os.makedirs(BANDING, exist_ok=True)
    # bersihkan halaman lama yang tidak lagi ada
    sah = {pair["id"] + ".html" for pair in pasangan} | {"index.html"}
    for nama in os.listdir(BANDING):
        if nama not in sah and nama.endswith(".html"):
            os.remove(os.path.join(BANDING, nama))

    berkas = {
        "index.html": render_index(data, produk, pasangan),
        "ulasan.html": render_ulasan(data, pasangan),
    }
    for pair in pasangan:
        berkas[f"banding/{pair['id']}.html"] = render_pair(data, produk, pair)
    for path, html in berkas.items():
        tujuan = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(tujuan), exist_ok=True)
        with open(tujuan, "w", encoding="utf-8") as f:
            f.write(html)
    tulis_redirect()
    # redirect tidak ikut pemeriksaan kata (hampir kosong) tapi tautannya diperiksa lewat berkas
    periksa(berkas, produk, pasangan, posted, merek)
    # gambar yang tidak terpakai
    terpakai = {pair["lokal"] + ".jpg" for pair in pasangan} | {pair["korea"] + ".jpg" for pair in pasangan}
    if os.path.isdir(IMG):
        for nama in os.listdir(IMG):
            if nama not in terpakai:
                os.remove(os.path.join(IMG, nama))
    laporan(produk, pasangan)
    print(f"\nSelesai: {len(pasangan)} perbandingan")


if __name__ == "__main__":
    main()
