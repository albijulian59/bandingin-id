#!/usr/bin/env python3
"""Bangun situs statis Bandingin.id: perbandingan skincare lokal vs Korea.

    python3 tools/build_site.py --sumber /path/ke/shopee-data-v2

Membaca tools/konten.json + analisa.json + file .psv, lalu menulis
index.html dan banding/*.html. Harga, gambar, dan link affiliate
diambil dari data, bukan diketik di HTML.

Tiap produk skincare yang punya link affiliate harus masuk perbandingan
atau disebut di ALASAN_DILEWATI. Kalau tidak, skrip ini gagal.
"""
import argparse
import html
import json
import os
import re
import sys

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMBER_BAWAAN = "/tmp/skincare-src/shopee-data-v2"

JENIS_LABEL = {
    "pelembab": "Pelembab",
    "serum": "Serum",
    "sunscreen": "Sunscreen",
    "facial-wash": "Facial Wash",
}
UNTUK_LABEL = {"perempuan": "Perempuan", "pria": "Pria"}
KULIT_LABEL = {
    "berminyak": "Berminyak",
    "kering": "Kering",
    "normal": "Normal",
    "sensitif": "Sensitif",
    "berjerawat": "Berjerawat",
}
KEYWORD_JENIS = {
    "facial wash wanita": ("facial-wash", "perempuan"),
    "facial wash pria": ("facial-wash", "pria"),
    "pelembab wajah wanita": ("pelembab", "perempuan"),
    "pelembab wajah pria": ("pelembab", "pria"),
    "serum wajah wanita": ("serum", "perempuan"),
    "serum wajah pria": ("serum", "pria"),
    "sunscreen wanita": ("sunscreen", "perempuan"),
    "sunscreen pria": ("sunscreen", "pria"),
}

# Produk skincare yang sengaja tidak masuk halaman. Alasannya dicek saat build.
ALASAN_DILEWATI = {
    "56310901303": "Facial wash perempuan. Tidak ada facial wash Korea di data (merek-korea.txt) yang punya link affiliate, jadi tidak bisa dijejerkan head-to-head.",
    "26720368293": "Facial wash perempuan, listing semua varian. Tidak ada pasangan Korea.",
    "41101567247": "Facial wash perempuan, listing semua varian. Tidak ada pasangan Korea.",
    "43358097567": "Facial wash perempuan. Tidak ada pasangan Korea.",
    "41107048405": "Facial wash perempuan, listing semua varian. Tidak ada pasangan Korea.",
    "5358717104": "Facial wash pria. Tidak ada facial wash Korea di data yang punya link affiliate.",
    "27221469602": "Facial wash pria, listing semua varian. Tidak ada pasangan Korea.",
    "57857445714": "Facial wash pria, listing semua varian. Tidak ada pasangan Korea.",
    "28870869761": "Facial wash pria. Tidak ada pasangan Korea.",
    "25989145906": "Facial wash pria. Tidak ada pasangan Korea.",
    "40401770290": "Pelembab perempuan (Wardah Collagen). Dua pelembab Korea di data (COSRX dan ILLIYOON) sudah dipakai di perbandingan yang pernah naik di X. Produk tidak diulang biar tiap halaman pasangan yang beda.",
    "42528194882": "Serum perempuan (OMG Active Expert) satu listing untuk lima varian dengan formula berbeda. Serum Korea yang tersisa, Torriden, formula tunggal buat hidrasi, dipasangkan dengan Wardah C-Glow yang juga satu formula.",
    "28218154859": "Sunscreen perempuan (Wardah UV Shield) seri banyak varian. Dua sunscreen Korea di data (Beauty of Joseon Aqua-Fresh dan Round Lab) sudah dipakai di perbandingan yang pernah naik di X.",
    "29319814911": "Pelembab pria (MS Glow Dual Cream), paket dua krim pagi-malam. Penjualan di data sama-sama mentok di batas tampilan dengan Kahf. Satu pelembab Korea yang tersisa (Nature Republic) dipasangkan dengan Kahf karena Kahf satu produk, bukan paket dua krim.",
    "25142085435": "Serum pria (Barber Daily). Total terjual di data lebih rendah dari MS Glow Maxi Bright. Serum Korea yang tersisa (COSRX Niacinamide 15) dipasangkan dengan yang penjualannya lebih tinggi. Angka terjual tidak ditampilkan di situs.",
    "20774296730": "Sunscreen pria (Garnier Men). Total terjual di data lebih rendah dari ELVICTO. Sunscreen Korea yang tersisa (SOME BY MI V10) dipasangkan dengan ELVICTO. Angka terjual tidak ditampilkan di situs.",
}

DILARANG = re.compile(
    r"terjual|rating|terlaris|\brb\+|bintang|⭐|top\s*10|/bln",
    re.I,
)


def e(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def angka_harga(teks):
    teks = (teks or "").strip()
    if teks in ("", "-"):
        return None
    return int(re.sub(r"[^\d]", "", teks))


def rupiah(n):
    return "Rp" + f"{int(n):,}".replace(",", ".")


def normal_url(u):
    return u.strip().split("?")[0].rstrip("/")


def item_id(u):
    return normal_url(u).split("/")[-1]


def baca_korea(path):
    merek = []
    with open(path, encoding="utf-8") as f:
        for baris in f:
            baris = baris.strip()
            if baris and not baris.startswith("#"):
                merek.append(baris)
    return merek


def korea_dari_judul(judul, merek):
    rendah = judul.lower()
    return any(m.lower() in rendah for m in merek)


def baca_affiliate(path):
    peta = {}
    with open(path, encoding="utf-8") as f:
        for no, baris in enumerate(f, 1):
            baris = baris.strip()
            if not baris or baris.startswith("#"):
                continue
            kolom = [x.strip() for x in baris.split("|")]
            if len(kolom) < 3 or not kolom[2].startswith("http"):
                print(f"  ! affiliate baris {no} dilewati", file=sys.stderr)
                continue
            peta[normal_url(kolom[1])] = kolom[2]
    return peta


def baca_psv(path, gender_file):
    produk = []
    with open(path, encoding="utf-8") as f:
        for no, baris in enumerate(f, 1):
            baris = baris.strip()
            if not baris:
                continue
            kolom = [x.strip() for x in baris.split(" | ")]
            if len(kolom) != 10:
                raise SystemExit(f"{path} baris {no}: {len(kolom)} kolom, harus 10")
            kw, judul, harga, asli, _rating, _sold, _bulan, _kota, url, gambar = kolom
            produk.append({
                "keyword": kw,
                "judul": judul,
                "harga": angka_harga(harga),
                "hargaAsli": angka_harga(asli),
                "url": normal_url(url),
                "gambar": gambar,
                "id": item_id(url),
                "file": gender_file,
            })
    return produk


def harga_html(p):
    asli = p["hargaAsli"]
    harga = p["harga"]
    potong = ""
    if asli and asli > harga:
        persen = round((asli - harga) * 100 / asli)
        if persen > 0:
            potong = f' <s>{e(rupiah(asli))}</s> <span class="diskon">-{persen}%</span>'
    return f'<span class="harga-now">{e(rupiah(harga))}</span>{potong}'


def gambar_html(p, alt, thumb=False, eager=False):
    src = p["gambar"]
    if thumb and re.search(r"susercontent\.com/file/[^_?]+$", src):
        src += "_tn"
    loading = "eager" if eager else "lazy"
    extra = ' fetchpriority="high"' if eager else ""
    return (
        f'<img src="{e(src)}" alt="{e(alt)}" loading="{loading}" decoding="async"'
        f'{extra} referrerpolicy="no-referrer" onerror="gambarGagal(this)">'
    )


def cek_konten(konten, katalog, analisa):
    salah = []
    ids = []
    for c in konten:
        for sisi in ("lokal", "korea"):
            iid = c[sisi]["item"]
            ids.append(iid)
            if iid not in katalog:
                salah.append(f"{c['id']}: item {iid} tidak ada di katalog / tanpa link affiliate")
                continue
            p = katalog[iid]
            if p["jenis"] != c["jenis"] or p["untuk"] != c["untuk"]:
                salah.append(f"{c['id']}: {iid} jenis/untuk tidak cocok ({p['jenis']}/{p['untuk']})")
            if sisi == "korea" and not p["korea"]:
                salah.append(f"{c['id']}: {iid} bukan merek Korea menurut merek-korea.txt")
            if sisi == "lokal" and p["korea"]:
                salah.append(f"{c['id']}: {iid} terdeteksi merek Korea, tapi dipasang sebagai lokal")
            if iid not in analisa:
                salah.append(f"{c['id']}: {iid} tidak punya analisa.json")
            if not c[sisi]["kandungan"] or not c[sisi]["manfaat"]:
                salah.append(f"{c['id']}: {sisi} kandungan/manfaat kosong")
        if not c["x"]:
            continue
        if not str(c["x"]).startswith("https://x.com/"):
            salah.append(f"{c['id']}: link X tidak valid")
    if len(ids) != len(set(ids)):
        salah.append("Ada produk yang dipakai di lebih dari satu perbandingan")
    return salah


def nav(prefix, aktif=None):
    jenis = [
        ("pelembab", "Pelembab"),
        ("serum", "Serum"),
        ("sunscreen", "Sunscreen"),
        ("facial-wash", "Facial Wash"),
    ]
    jenis_tautan = []
    for slug, label in jenis:
        cur = ' aria-current="page"' if aktif == slug else ""
        jenis_tautan.append(f'<a href="{prefix}index.html?jenis={slug}"{cur}>{label}</a>')
    untuk = (
        f'<a href="{prefix}index.html?untuk=perempuan">Perempuan</a>'
        f'<a href="{prefix}index.html?untuk=pria">Pria</a>'
    )
    return (
        '<div class="nav-row">' + "".join(jenis_tautan) + "</div>"
        + '<div class="nav-row">' + untuk + "</div>"
    )


FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
    "%3Crect width='100' height='100' rx='22' fill='%230c6b62'/%3E"
    "%3Ctext x='50' y='64' text-anchor='middle' font-size='42' font-family='Georgia' fill='white'%3Evs%3C/text%3E%3C/svg%3E"
)


def head(judul, deskripsi, prefix, path):
    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{e(judul)}</title>
  <meta name="description" content="{e(deskripsi)}">
  <link rel="canonical" href="https://albijulian59.github.io/bandingin-id/{path}">
  <link rel="icon" href="{FAVICON}">
  <link rel="stylesheet" href="{prefix}css/style.css">
</head>
"""


def header(prefix, aktif=None):
    return f"""<a class="skip" href="#isi">Langsung ke isi</a>
<header class="site-header">
  <div class="wrap bar">
    <a class="logo" href="{prefix}index.html"><span class="mark" aria-hidden="true">vs</span>Bandingin<span class="tld">.id</span></a>
    <nav class="nav" aria-label="Jenis dan pemakai">
        {nav(prefix, aktif)}
    </nav>
  </div>
</header>
"""


def footer(prefix):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p class="footnote">Harga dari data listing 22 Oktober 2026, cek lagi di Shopee sebelum bayar. Ulasan disusun dari analisa kandungan dan informasi produk. Bandingin.id mendapat komisi dari link affiliate.</p>
    <p class="copy">© 2026 Bandingin.id</p>
  </div>
</footer>
<script src="{prefix}js/site.js"></script>
"""


def kulit_html(analisa_item):
    chips = "".join(
        f'<li>{e(KULIT_LABEL.get(k, k))}</li>' for k in analisa_item.get("cocokKulit") or []
    )
    if not chips:
        return ""
    return f'<ul class="kulit">{chips}</ul>'


def produk_detail(sisi, p, analisa_item):
    bahan = "".join(
        f'<li><b>{e(b["bahan"])}</b><span>{e(b["fungsi"])}</span></li>'
        for b in sisi["kandungan"]
    )
    manfaat = "".join(f"<li>{e(m)}</li>" for m in sisi["manfaat"])
    ukuran = ""
    if sisi.get("ukuran"):
        uk = sisi["ukuran"]
        ekstra = " Cek varian di halaman produk." if (" dan " in uk or " atau " in uk) else ""
        ukuran = f'<p class="ukuran">Isi {e(uk)}.{ekstra}</p>'
    peran = "korea" if p["korea"] else "lokal"
    return f"""<section class="produk {peran}" id="{peran}">
      <p class="asal">{'Korea' if p['korea'] else 'Lokal'}</p>
      <h2>{e(sisi['nama'])}</h2>
      <p class="tekstur">{e(sisi['tekstur'])}</p>
      <p class="harga">{harga_html(p)}</p>
      {ukuran}
      <h3>Kandungan utama</h3>
      <ul class="bahan">{bahan}</ul>
      <h3>Manfaat</h3>
      <ul class="manfaat">{manfaat}</ul>
      <h3>Cocok buat kulit</h3>
      {kulit_html(analisa_item)}
      <p class="catatan">{e(sisi['catatan'])}</p>
      <a class="btn" href="{e(p['aff'])}" target="_blank" rel="nofollow sponsored noopener">Beli di Shopee</a>
    </section>"""


def sisi_ringkas(sisi, p, eager):
    peran = "korea" if p["korea"] else "lokal"
    return f"""<div class="sisi {peran}">
        <div class="foto">{gambar_html(p, sisi['nama'], thumb=False, eager=eager)}</div>
        <p class="asal">{'Korea' if p['korea'] else 'Lokal'}</p>
        <p class="nama">{e(sisi['nama'])}</p>
        <p class="tekstur">{e(sisi['tekstur'])}</p>
        <p class="harga">{harga_html(p)}</p>
        <a class="btn" href="{e(p['aff'])}" target="_blank" rel="nofollow sponsored noopener">Beli di Shopee</a>
      </div>"""


def halaman_banding(c, katalog, analisa, semua):
    lok = katalog[c["lokal"]["item"]]
    kor = katalog[c["korea"]["item"]]
    jenis = JENIS_LABEL[c["jenis"]]
    untuk = UNTUK_LABEL[c["untuk"]]
    x = ""
    if c.get("x"):
        x = f'<p class="ke-x"><a href="{e(c["x"])}" target="_blank" rel="noopener noreferrer">Lihat di X</a></p>'
    lain = [x for x in semua if x["id"] != c["id"]]
    lain.sort(key=lambda x: (x["jenis"] != c["jenis"], x["untuk"] != c["untuk"]))
    kartu = []
    for lain_c in lain[:3]:
        kartu.append(
            f'<a href="{e(lain_c["id"])}.html"><span>{e(JENIS_LABEL[lain_c["jenis"]])} · {e(UNTUK_LABEL[lain_c["untuk"]])}</span>{e(lain_c["judul"])}</a>'
        )
    deskripsi = c["ringkas"]
    path = f"banding/{c['id']}.html"
    return f"""{head(c['judul'] + ' | Bandingin.id', deskripsi, '../', path)}
<body>
{header('../', c['jenis'])}
<main id="isi" class="wrap cmp">
  <p class="crumbs"><a href="../index.html">Beranda</a> · <a href="../index.html?jenis={c['jenis']}">{jenis}</a> · <a href="../index.html?jenis={c['jenis']}&amp;untuk={c['untuk']}">{untuk}</a></p>
  <p class="kicker">{jenis} · {untuk}</p>
  <h1>{e(c['judul'])}</h1>
  <p class="pembuka">{e(c['pembuka'])}</p>
  {x}
  <div class="duel">
      {sisi_ringkas(c['lokal'], lok, True)}
      <p class="vs" aria-hidden="true">vs</p>
      {sisi_ringkas(c['korea'], kor, True)}
  </div>
  <div class="rinci">
    {produk_detail(c['lokal'], lok, analisa[c['lokal']['item']])}
    {produk_detail(c['korea'], kor, analisa[c['korea']['item']])}
  </div>
  <section class="putusan">
    <h2>Jadi, mending yang mana?</h2>
    <p class="tl">{e(c['verdict']['putusan'])}</p>
    <div class="tiga">
      <article>
        <h3>Kulit berminyak / berjerawat</h3>
        <p>{e(c['verdict']['berminyak'])}</p>
      </article>
      <article>
        <h3>Kulit kering / sensitif</h3>
        <p>{e(c['verdict']['kering'])}</p>
      </article>
      <article>
        <h3>Budget vs kandungan</h3>
        <p>{e(c['verdict']['budget'])}</p>
      </article>
    </div>
  </section>
  <section class="lain">
    <h2>Perbandingan lain</h2>
    <div class="lain-grid">{''.join(kartu)}</div>
  </section>
</main>
{footer('../')}
</body>
</html>
"""


def tombol_beli(p, nama, kecil=False, teks="Beli di Shopee"):
    kelas = "btn btn-kecil" if kecil else "btn"
    return (
        f'<a class="{kelas}" href="{e(p["aff"])}" target="_blank" rel="nofollow sponsored noopener"'
        f' aria-label="Beli {e(nama)} di Shopee">{e(teks)}</a>'
    )


def kartu_beranda(c, katalog):
    lok = katalog[c["lokal"]["item"]]
    kor = katalog[c["korea"]["item"]]
    jenis = JENIS_LABEL[c["jenis"]]
    untuk = UNTUK_LABEL[c["untuk"]]
    href = f"banding/{e(c['id'])}.html"
    return f"""<article class="card" data-jenis="{e(c['jenis'])}" data-untuk="{e(c['untuk'])}">
      <a class="card-foto" href="{href}">
        {gambar_html(lok, c['lokal']['nama'], thumb=True)}
        <span class="card-vs" aria-hidden="true">vs</span>
        {gambar_html(kor, c['korea']['nama'], thumb=True)}
      </a>
      <div class="card-isi">
        <p class="kicker">{jenis} · {untuk}</p>
        <h2><a href="{href}">{e(c['judul'])}</a></h2>
        <p class="nama-vs">{e(c['lokal']['nama'])} <span>vs</span> {e(c['korea']['nama'])}</p>
        <p class="ringkas">{e(c['ringkas'])}</p>
        <div class="card-beli">
          {tombol_beli(lok, c['lokal']['nama'], kecil=True, teks="Beli lokal")}
          {tombol_beli(kor, c['korea']['nama'], kecil=True, teks="Beli Korea")}
        </div>
        <a class="lebih" href="{href}">Lihat perbandingan</a>
      </div>
    </article>"""


def halaman_index(konten, katalog):
    kartu = "\n".join(kartu_beranda(c, katalog) for c in konten)
    n = len(konten)
    deskripsi = (
        "Perbandingan head-to-head skincare: pelembab, serum, dan sunscreen. "
        "Satu produk lokal dijejerin dengan satu produk Korea yang setipe."
    )
    return f"""{head('Bandingin.id — Skincare lokal vs Korea, mending yang mana?', deskripsi, '', 'index.html')}
<body>
{header('')}
<main id="isi">
  <section class="hero">
    <div class="wrap">
      <p class="kicker kicker-terang">Skincare · lokal vs Korea</p>
      <h1>Lokal vs Korea,<br>mending yang mana?</h1>
      <p>Pelembab, serum, dan sunscreen. Satu produk lokal dijejerin dengan satu produk Korea yang setipe: kandungan, harga, terus siapa mending pilih yang mana.</p>
    </div>
  </section>
  <section class="wrap daftar-wrap">
    <div class="filter" role="group" aria-label="Saring perbandingan">
      <div class="filter-baris">
        <button type="button" data-filter="jenis" data-value="semua" aria-pressed="true">Semua</button>
        <button type="button" data-filter="jenis" data-value="pelembab">Pelembab</button>
        <button type="button" data-filter="jenis" data-value="serum">Serum</button>
        <button type="button" data-filter="jenis" data-value="sunscreen">Sunscreen</button>
        <button type="button" data-filter="jenis" data-value="facial-wash">Facial Wash</button>
      </div>
      <div class="filter-baris">
        <button type="button" data-filter="untuk" data-value="semua" aria-pressed="true">Semua</button>
        <button type="button" data-filter="untuk" data-value="perempuan">Perempuan</button>
        <button type="button" data-filter="untuk" data-value="pria">Pria</button>
      </div>
    </div>
    <p class="info-hasil" id="info-hasil">{n} perbandingan</p>
    <div class="grid" id="daftar">
      {kartu}
    </div>
    <p class="kosong" id="kosong" hidden>Facial wash belum bisa dijejerin. Di data toko resmi yang punya link affiliate, semuanya merek lokal. Belum ada facial wash Korea buat pasangan head-to-head.</p>
    <aside class="ebook">
      <div>
        <p class="kicker">Dari Albi</p>
        <h2>Panduan skincare lengkap</h2>
        <p>Urutan pakai, dari cuci muka sampai sunscreen, dirangkum di e-book.</p>
      </div>
      <a href="https://lynk.id/albijulian" target="_blank" rel="noopener noreferrer">Buka di Lynk.id</a>
    </aside>
  </section>
</main>
{footer('')}
</body>
</html>
"""


def alihkan(nama):
    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=index.html">
  <link rel="canonical" href="https://albijulian59.github.io/bandingin-id/index.html">
  <title>Bandingin.id</title>
  <script>location.replace("index.html");</script>
</head>
<body>
  <p><a href="index.html">Ke beranda Bandingin.id</a></p>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sumber", default=SUMBER_BAWAAN)
    args = ap.parse_args()
    sumber = args.sumber
    merek = baca_korea(os.path.join(sumber, "merek-korea.txt"))
    aff = baca_affiliate(os.path.join(sumber, "affiliate-links.psv"))
    mentah = []
    mentah += baca_psv(os.path.join(sumber, "perempuan.psv"), "perempuan")
    mentah += baca_psv(os.path.join(sumber, "pria.psv"), "pria")

    katalog = {}
    bukan_skincare = {}
    tanpa_aff = []
    for p in mentah:
        if p["keyword"] not in KEYWORD_JENIS:
            bukan_skincare[p["keyword"]] = bukan_skincare.get(p["keyword"], 0) + 1
            continue
        jenis, untuk = KEYWORD_JENIS[p["keyword"]]
        link = aff.get(p["url"])
        if not link or not link.startswith("https://s.shopee.co.id/"):
            tanpa_aff.append(p["id"] + " " + p["judul"][:60])
            continue
        katalog[p["id"]] = {
            "id": p["id"],
            "judul": p["judul"],
            "harga": p["harga"],
            "hargaAsli": p["hargaAsli"],
            "gambar": p["gambar"],
            "url": p["url"],
            "aff": link,
            "jenis": jenis,
            "untuk": untuk,
            "korea": korea_dari_judul(p["judul"], merek),
        }

    if tanpa_aff:
        raise SystemExit("Produk skincare tanpa link pendek s.shopee.co.id:\n" + "\n".join(tanpa_aff))

    with open(os.path.join(SITE, "tools", "konten.json"), encoding="utf-8") as f:
        konten = json.load(f)
    with open(os.path.join(SITE, "tools", "analisa.json"), encoding="utf-8") as f:
        analisa = json.load(f)

    salah = cek_konten(konten, katalog, analisa)
    dipakai = {c[sisi]["item"] for c in konten for sisi in ("lokal", "korea")}
    for iid, p in katalog.items():
        if iid in dipakai:
            continue
        if iid not in ALASAN_DILEWATI:
            salah.append(f"Produk skincare {iid} ({p['jenis']}/{p['untuk']}) tidak dipakai dan tidak ada alasannya")
        elif p["korea"] and p["jenis"] == "facial-wash":
            salah.append(f"Ada facial wash Korea {iid} tapi tidak dibandingin")
    korea_facial = [p for p in katalog.values() if p["korea"] and p["jenis"] == "facial-wash"]
    if korea_facial:
        salah.append("Facial wash Korea ada di data. Tambahkan perbandingannya.")
    if salah:
        raise SystemExit("Konten tidak lolos pemeriksaan:\n- " + "\n- ".join(salah))

    for iid in ALASAN_DILEWATI:
        if iid not in katalog:
            raise SystemExit(f"Alasan dilewati untuk item yang tidak ada: {iid}")

    out_dir = os.path.join(SITE, "banding")
    os.makedirs(out_dir, exist_ok=True)
    for nama in os.listdir(out_dir):
        if nama.endswith(".html"):
            os.remove(os.path.join(out_dir, nama))

    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(halaman_index(konten, katalog))
    for c in konten:
        with open(os.path.join(out_dir, c["id"] + ".html"), "w", encoding="utf-8") as f:
            f.write(halaman_banding(c, katalog, analisa, konten))
    for nama in ("review.html", "perbandingan.html"):
        with open(os.path.join(SITE, nama), "w", encoding="utf-8") as f:
            f.write(alihkan(nama))

    # Katalog tanpa angka rating/terjual, buat build ulang yang tidak menampilkan metrik itu.
    simpan = {iid: {k: v for k, v in p.items()} for iid, p in katalog.items() if iid in dipakai}
    with open(os.path.join(SITE, "tools", "katalog.json"), "w", encoding="utf-8") as f:
        json.dump(simpan, f, ensure_ascii=False, indent=2)
        f.write("\n")

    html_gabungan = open(os.path.join(SITE, "index.html"), encoding="utf-8").read()
    for c in konten:
        html_gabungan += open(os.path.join(out_dir, c["id"] + ".html"), encoding="utf-8").read()
    temuan = DILARANG.findall(html_gabungan)
    if temuan:
        raise SystemExit("Teks terlarang muncul di HTML: " + ", ".join(sorted(set(temuan))))
    if "https://shopee.co.id/" in html_gabungan:
        raise SystemExit("Ada link Shopee panjang. Tombol beli harus s.shopee.co.id.")
    beli = re.findall(r'class="btn(?: btn-kecil)?" href="([^"]+)"', html_gabungan)
    if len(beli) != len(konten) * 6 or any(not u.startswith("https://s.shopee.co.id/") for u in beli):
        raise SystemExit(f"Tombol beli tidak beres: {len(beli)} tautan (harus {len(konten) * 6}, dua di kartu dan empat di halaman)")

    from collections import Counter
    hitung = Counter((c["jenis"], c["untuk"]) for c in konten)
    print(f"Selesai: {len(konten)} perbandingan, {len(beli)} tombol beli")
    for jenis in ("pelembab", "serum", "sunscreen", "facial-wash"):
        for untuk in ("perempuan", "pria"):
            print(f"  {JENIS_LABEL[jenis]:12} {UNTUK_LABEL[untuk]:10} {hitung.get((jenis, untuk), 0)}")
    print("Bukan skincare, tidak masuk situs:")
    for kw, n in sorted(bukan_skincare.items()):
        print(f"  {n} × {kw}")
    print(f"Skincare dilewati: {len(ALASAN_DILEWATI)}")
    for iid, alasan in ALASAN_DILEWATI.items():
        print(f"  {iid} {katalog[iid]['judul'][:70]}")
        print(f"    {alasan}")


if __name__ == "__main__":
    main()
