#!/usr/bin/env python3
"""Bangun situs statis PilihYuk: perbandingan skincare lokal vs Korea dan lokal vs lokal.

    python3 tools/build_site.py            # pakai gambar yang sudah ada
    python3 tools/build_site.py --gambar   # unduh ulang gambar produk
    python3 tools/build_site.py --draft    # pratinjau: link pendek boleh kosong
                                           # (tombol jadi "Link menyusul", nonaktif)

Sumber: sumber/*.psv, sumber/tambahan-*.psv, sumber/merek-korea.txt,
sumber/posted.log, tools/pasangan.json
Hasil: index.html, banding/*.html, bandingkan.html, ulasan.html, tentang.html, img/*.jpg
"""
import argparse, glob, json, os, re, sys, urllib.request
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
    ("facial-wash", "Facial Wash"),
]
JENIS_LABEL = dict(JENIS)
# Jenis perbandingan. Pasangan lama tanpa kunci "banding" dianggap lokal-korea.
BANDING_JENIS = [
    ("lokal-korea", "Lokal vs Korea"),
    ("lokal-lokal", "Lokal vs Lokal"),
]
BANDING_LABEL = dict(BANDING_JENIS)
DRAFT = False
MEREK = "PilihYuk"
# Alamat situs yang hidup (custom domain, file CNAME). Satu tempat untuk URL absolut:
# canonical, og:url, sitemap.xml, robots.txt. Tautan antar halaman tetap relatif.
BASE_URL = "https://pilihyuk.id/"
# Verifikasi Google Search Console (properti https://pilihyuk.id/).
GOOGLE_SITE_VERIFICATION = "ygg-CttU-Raot4lAzh9pI1CV8HeUt5f1_sjWReFvTng"
# Gambar untuk og:image, twitter:image, dan logo Organization (JSON-LD). URL absolut, 512x512.
GAMBAR_SOSIAL = BASE_URL + "img/favicon-512.png"
# Akun resmi PilihYuk untuk sameAs di JSON-LD beranda.
AKUN_RESMI = ["https://x.com/pilihyukid", "https://www.threads.com/@pret.zel59"]

# Teks kepercayaan: dipakai di footer, dekat tombol beli, dan di Tentang Kami.
CATATAN_AFFILIATE = (
    "Link di situs ini adalah link affiliate Shopee. Kamu tetap membeli di Shopee resmi "
    "dengan harga yang sama, dan PilihYuk mendapat komisi kecil."
)
CATATAN_AMAN = "Kamu akan diarahkan ke Shopee resmi. PilihYuk tidak meminta data pribadi atau pembayaran."
CATATAN_STATIS = "Situs statis tanpa login dan tanpa pembayaran."

# KONTAK (PLACEHOLDER): email atau akun media sosial resmi PilihYuk belum ditentukan.
# Isi daftar ini nanti dengan pasangan (label, URL), misalnya ("Email", "mailto:...").
# Jangan isi dengan alamat karangan. Selama kosong, Tentang Kami hanya mengarahkan ke
# formulir Kasih Pendapat. Kalau memakai mailto:, sesuaikan juga pemeriksaan di periksa().
KONTAK_LAIN = []

# Sumber kandungan yang tidak ditampilkan sebagai tautan walau ada di data (domain, tanpa www).
# Kosong: semua URL dari data tampil. Catatan: inkeedecoder.com adalah nama baru resmi
# INCIDecoder (incidecoder.com dialihkan ke sana, lihat https://inkeedecoder.com/new-name).
SUMBER_DILEWATI = ()
# Logo dan ikon (dibuat dari img/logo-asli.jpg, warna disesuaikan ke palet situs).
# File ini tidak ikut dihapus saat membersihkan foto produk lama di img/.
LOGO_W, LOGO_H = 429, 120  # ukuran asli img/logo.png; tampil 40 px (CSS)
ASET_MEREK = {
    "logo.png", "logo.webp", "logo-asli.jpg", "favicon-32.png", "apple-touch-icon.png",
    # favicon persegi untuk Google, manifest, dan og:image (tools/buat_favicon.py)
    "favicon-48.png", "favicon-96.png", "favicon-192.png", "favicon-512.png",
}

BANNED = re.compile(
    r"\b(pria|wanita|cowok|cewek|perempuan|laki-laki|for men|terjual|rating|"
    r"bintang|terlaris|paling laku|belum dicoba|menyembuhkan|mengobati)\b|"
    r"rb\+|★|☆",
    re.I,
)

ALASAN_LEWAT = {
    "facial": "Facial wash yang tidak punya pasangan sejenis di data.",
    "20774296730": "Garnier bukan merek lokal Indonesia dan tidak ada di daftar merek Korea, jadi tidak masuk sisi mana pun.",
    "41107048405": "Garnier bukan merek lokal Indonesia dan tidak ada di daftar merek Korea, jadi tidak masuk sisi mana pun.",
    "27221469602": "Garnier bukan merek lokal Indonesia dan tidak ada di daftar merek Korea, jadi tidak masuk sisi mana pun.",
    "28870869761": "Nivea bukan merek lokal Indonesia dan tidak ada di daftar merek Korea, jadi tidak masuk sisi mana pun.",
    "3059551066": (
        "Scarlett Glowtening Serum sudah jadi salah satu varian di listing SCARLETT Face Serum "
        "(19311657068), yang dibahas varian per varian. Supaya produk yang sama tidak muncul dua kali."
    ),
    "58055792468": (
        "Produk yang sama dengan Scarlett Ultra Light Daily Sunscreen 27220208261 (toko resmi), "
        "hanya beda toko. Yang dipakai listing toko resmi."
    ),
    "29458576491": (
        "SCARLETT Moisturizer Series: bahan tidak tercantum dan daftar varian di listing tidak bisa dipastikan "
        "(halaman Shopee minta login). Jumlah pelembap lokal juga ganjil, jadi ini yang dilewati."
    ),
    "28234426003": (
        "HANASUI Ceramide Probiotics (Semua jenis kulit;Sensitif) dulu dipasangkan dengan COSRX HA Cream, "
        "krim untuk kulit kering. Pasangan itu diganti Avoskin GCT Aqua Ceramide. Tidak ada pelembap lokal "
        "lain tanpa pasangan dengan jenis kulit utama yang sama, jadi Hanasui disembunyikan (data tetap ada)."
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


RENTANG = re.compile(r"^\s*(?:Rp)?\s*([\d.]+)\s*[-\u2013]\s*(?:Rp)?\s*([\d.]+)\s*$", re.I)


def parse_rentang(teks):
    """"Rp47.900-222.500" -> (47900, 222500). Harga tunggal -> (harga, None)."""
    m = RENTANG.match(teks or "")
    if not m:
        return parse_rp(teks), None
    lo, hi = parse_rp(m.group(1)), parse_rp(m.group(2))
    if not lo or not hi or hi <= lo:
        raise SystemExit(f"Rentang harga tidak sah: {teks}")
    return lo, hi


def produk_pair(produk, pair, iid):
    """Data produk untuk satu pasangan.

    Produk lama boleh dipakai lagi di pasangan baru. Kalau harga atau link pendek listing
    baru berbeda, isi pair["produk"][iid]["listing"] = {"harga", "asli", "aff"}.
    Data lama di sumber/ tetap utuh dan pasangan lama tetap memakai data lama.
    """
    p = produk[iid]
    ov = (pair["produk"].get(iid) or {}).get("listing")
    if not ov:
        return p
    harga, maks = parse_rentang(ov.get("harga"))
    asli = parse_rp(ov.get("asli")) if ov.get("asli") else harga
    return {**p, "harga": harga, "harga_maks": maks, "asli": asli, "aff": ov.get("aff") or None}


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


def jenis_banding(pair):
    return pair.get("banding", "lokal-korea")


def sisi_pair(pair):
    """Daftar (kunci, item id, asal) untuk dua sisi pasangan, urut kiri ke kanan."""
    if jenis_banding(pair) == "lokal-lokal":
        return [("a", pair["a"], "lokal"), ("b", pair["b"], "lokal")]
    return [("lokal", pair["lokal"], "lokal"), ("korea", pair["korea"], "korea")]


def id_pair(pair):
    return [iid for _, iid, _ in sisi_pair(pair)]


def label_sisi(pair, kunci):
    """Judul kolom tabel: Lokal/Korea, atau nama singkat untuk lokal vs lokal."""
    if jenis_banding(pair) != "lokal-lokal":
        return "Lokal" if kunci == "lokal" else "Korea"
    copy = pair["produk"][pair[kunci]]
    return copy.get("label") or copy["nama"]


def badge_banding(pair):
    b = jenis_banding(pair)
    return f'<span class="tipe tipe-{b}">{esc(BANDING_LABEL[b])}</span>'


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
    muat_tambahan(produk)
    return produk


def muat_tambahan(produk):
    """File tambahan-*.psv: produk baru dengan link pendek dan catatan bahan.

    Kolomnya tetap: type, brand, origin, name, price, original price,
    product URL, image URL, short link, key ingredients.
    Batch baru cukup ditambah sebagai file baru di sumber/.
    """
    wajib = [
        "type", "brand", "origin", "name", "price", "original price",
        "product url", "image url", "short link", "key ingredients",
    ]
    paths = sorted(glob.glob(os.path.join(SUMBER, "tambahan-*.psv")))
    for path in paths:
        with open(path, encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
        if not lines:
            continue
        header = [h.strip().lower() for h in lines[0].split(" | ")]
        if header != wajib:
            raise SystemExit(os.path.basename(path) + ": header tidak dikenali")
        for n, line in enumerate(lines[1:], 2):
            kolom = [x.strip() for x in line.split(" | ")]
            if len(kolom) != len(header):
                raise SystemExit(f"{os.path.basename(path)} baris {n} bukan {len(header)} kolom")
            row = dict(zip(header, kolom))
            iid = item_id(row["product url"])
            if iid in produk:
                raise SystemExit(f"{iid} bentrok dengan produk yang sudah ada")
            aff = row["short link"]
            if not aff and DRAFT:
                aff = None  # pratinjau: tombol "Link menyusul"
            elif not aff and iid in ALASAN_LEWAT:
                aff = None  # sengaja dilewati, tidak pernah tampil
            elif not aff.startswith("https://s.shopee.co.id/"):
                raise SystemExit(
                    f"Bukan link pendek di {os.path.basename(path)} ({iid}): {aff or '(kosong)'}"
                    + ("" if aff else ". Isi kolom short link, atau bangun pratinjau dengan --draft.")
                )
            if row["origin"] not in ("lokal", "korea"):
                raise SystemExit(f"origin tidak dikenal: {row['origin']}")
            harga, harga_maks = parse_rentang(row["price"])
            if not harga:
                raise SystemExit(f"harga kosong: {iid}")
            produk[iid] = {
                "id": iid,
                "keyword": row["type"],
                "judul": row["name"],
                "harga": harga,
                "harga_maks": harga_maks,
                "asli": parse_rentang(row["original price"])[0],
                "url": row["product url"],
                "gambar": row["image url"],
                "aff": aff,
                "asal": row["origin"],
                "merek": row["brand"],
                "bahan_mentah": row["key ingredients"],
            }


def muat_sumber_kandungan():
    """sumber/kandungan-batch*.json: {item id: {"sumber": [URL, ...], ...}}.

    Hanya URL http(s) dari data yang dipakai. Tidak ada URL tambahan.
    """
    data = {}
    for path in sorted(glob.glob(os.path.join(SUMBER, "kandungan-batch*.json"))):
        with open(path, encoding="utf-8") as f:
            for iid, isi in json.load(f).items():
                if iid in data:
                    raise SystemExit(f"Sumber kandungan {iid} tercatat dua kali ({os.path.basename(path)})")
                data[iid] = isi
    hasil = {}
    for iid, isi in data.items():
        urls = []
        for u in (isi.get("sumber") or []) if isinstance(isi, dict) else []:
            u = str(u).strip()
            if not re.match(r"^https?://[^\s\"<>]+$", u):
                continue
            if domain(u) in SUMBER_DILEWATI:
                continue
            if u not in urls:
                urls.append(u)
        if urls:
            hasil[iid] = urls
    return hasil


def domain(url):
    m = re.match(r"^https?://([^/:?#]+)", url)
    d = m.group(1).lower() if m else url
    return d[4:] if d.startswith("www.") else d


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
        butuh.extend(id_pair(pair))
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
    if p.get("harga_maks"):
        # listing dengan beberapa pilihan ukuran/varian: tampil sebagai rentang, tanpa coret
        return f'<span class="now">{esc(rp(p["harga"]))}–{esc(rp(p["harga_maks"]))}</span>'
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


def catatan_pemakai_html(produk_copy):
    """Catatan singkat dari pengalaman pemakai (data: produk[id].catatan_pemakai)."""
    teks = produk_copy.get("catatan_pemakai")
    if not teks:
        return ""
    return f'<p class="catatan-pemakai">{esc(teks)}</p>'


def varian_dipilih_html(produk_copy):
    """Listing berisi banyak varian, tapi yang dibandingkan hanya satu."""
    v = produk_copy.get("varianDipilih")
    if not v:
        return ""
    return f'<p class="varian-dipilih">Varian yang dibandingkan: <strong>{esc(v)}</strong>. Pilih varian ini saat checkout.</p>'


# Catatan pemakai harus netral: tanpa nama platform atau kata "review".
PLATFORM_CATATAN = re.compile(r"(?i)\b(review|reviewer|twitter|tiktok|shopee|instagram|female ?daily|pengguna x)\b|\bX\b")
# Judul listing yang menandakan seri multi-varian.
SERI_LISTING = re.compile(r"(?i)\b(all series|semua varian|all variant|series)\b")


def kulit_html(produk_copy):
    return "".join(f'<li>{esc(k)}</li>' for k in produk_copy["kulit"])


def foto(iid, nama, eager=False):
    lazy = "" if eager else ' loading="lazy"'
    return (
        f'<img src="{{base}}img/{esc(iid)}.jpg" alt="{esc(nama)}" width="720" height="720"'
        f'{lazy} decoding="async">'
    )


def url_absolut(path):
    path = (path or "").lstrip("/")
    if path in ("", "index.html"):
        path = ""
    return BASE_URL + path


def head(title, description, base, canonical_path, extra_head=""):
    # Aset dan tautan tetap relatif. canonical_path: path halaman dari root situs
    # ("" atau "index.html" = beranda), dipakai untuk canonical dan og:url.
    url = url_absolut(canonical_path)
    return f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="theme-color" content="#f3efe7">
  <meta property="og:site_name" content="{MEREK}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{esc(url)}">
  <meta property="og:image" content="{GAMBAR_SOSIAL}">
  <meta property="og:image:width" content="512">
  <meta property="og:image:height" content="512">
  <meta property="og:image:alt" content="Logo {MEREK}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{GAMBAR_SOSIAL}">
  <link rel="canonical" href="{esc(url)}">
  <meta name="google-site-verification" content="{GOOGLE_SITE_VERIFICATION}" />
  <link rel="stylesheet" href="{base}css/style.css">
  <link rel="icon" href="{base}favicon.ico" sizes="any">
  <link rel="icon" type="image/png" sizes="32x32" href="{base}img/favicon-32.png">
  <link rel="icon" type="image/png" sizes="48x48" href="{base}img/favicon-48.png">
  <link rel="icon" type="image/png" sizes="192x192" href="{base}img/favicon-192.png">
  <link rel="apple-touch-icon" href="{base}img/apple-touch-icon.png">
  <link rel="manifest" href="{base}site.webmanifest">{extra_head}
  <script data-goatcounter="https://pilihyuk.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>
</head>
"""


def header(base, aktif=None):
    tautan = []
    for kunci, label in JENIS:
        href = f"{base}index.html#{kunci}"
        kelas = " class=\"aktif\"" if aktif == kunci else ""
        aria = " aria-current=\"true\"" if aktif == kunci else ""
        tautan.append(f'<a href="{href}"{kelas}{aria}>{esc(label)}</a>')
    kelas_s = " class=\"aktif\"" if aktif == "bandingkan" else ""
    aria_s = " aria-current=\"page\"" if aktif == "bandingkan" else ""
    tautan.append(f'<a href="{base}bandingkan.html"{kelas_s}{aria_s}>Bandingin Sendiri</a>')
    kelas_p = " class=\"aktif\"" if aktif == "pendapat" else ""
    aria_p = " aria-current=\"page\"" if aktif == "pendapat" else ""
    tautan.append(f'<a href="{base}ulasan.html"{kelas_p}{aria_p}>Kasih Pendapat</a>')
    kelas_t = " class=\"aktif\"" if aktif == "tentang" else ""
    aria_t = " aria-current=\"page\"" if aktif == "tentang" else ""
    tautan.append(f'<a href="{base}tentang.html"{kelas_t}{aria_t}>Tentang Kami</a>')
    return f"""<a class="skip" href="{base}index.html#daftar">Langsung ke perbandingan</a>
<header class="site-header">
  <div class="wrap nav">
    <a class="logo" href="{base}index.html"><picture><source srcset="{base}img/logo.webp" type="image/webp"><img src="{base}img/logo.png" alt="PilihYuk" width="{LOGO_W}" height="{LOGO_H}"></picture></a>
    <nav class="nav-links" aria-label="Menu">
      {''.join(tautan)}
    </nav>
  </div>
</header>
"""


def footer(base, tanggal):
    return f"""<footer class="site-footer">
  <div class="wrap">
    <p class="footnote" id="disclosure">{esc(CATATAN_AFFILIATE)}</p>
    <p class="footnote">Ulasan disusun dari analisa kandungan dan informasi produk, bukan saran medis. {esc(CATATAN_STATIS)}</p>
    <p class="footer-nav"><a href="{base}bandingkan.html">Bandingin Sendiri</a> · <a href="{base}tentang.html">Tentang Kami</a> · <a href="{base}ulasan.html">Kasih Pendapat</a></p>
    <p class="copy">© 2026 {MEREK} · Dikelola secara independen oleh Albi · Harga mengikuti halaman produk Shopee per {esc(tanggal)} dan bisa berubah.</p>
  </div>
</footer>
"""


def beli(p, nama, kelas="btn"):
    if not p.get("aff"):
        # hanya terjadi di --draft: link pendek belum ada
        return (
            f'<button class="{kelas} btn-menyusul" type="button" disabled'
            f' aria-label="Link {esc(nama)} menyusul">Link menyusul</button>'
        )
    return (
        f'<a class="{kelas}" href="{esc(p["aff"])}" target="_blank" rel="sponsored noopener noreferrer"'
        f' aria-label="Beli {esc(nama)} di Shopee">Beli di Shopee</a>'
    )


def catatan_beli(base, kelas=""):
    """Catatan singkat di dekat tombol beli: affiliate + diarahkan ke Shopee resmi."""
    return (
        f'<div class="catatan-beli{(" " + kelas) if kelas else ""}" role="note">'
        f'<p>{esc(CATATAN_AMAN)}</p>'
        f'<p>{esc(CATATAN_AFFILIATE)} <a href="{base}tentang.html#affiliate">Selengkapnya</a></p>'
        f'</div>'
    )


def sumber_html(urls):
    if not urls:
        return ""
    item = "".join(
        f'<li><a href="{esc(u)}" target="_blank" rel="noopener noreferrer nofollow">{esc(domain(u))}</a></li>'
        for u in urls
    )
    return f"""<div class="sumber-kandungan">
        <h3>Sumber kandungan</h3>
        <ul>{item}</ul>
      </div>"""


def foto_tautan(p, copy, asal, eager, href, base, pos):
    foto_html = foto(p["id"], copy["nama"], eager).replace("{base}", base)
    return f'<a class="photo photo-{asal} pos-{pos}" href="{esc(href)}">{foto_html}</a>'


def meta_kartu(p, copy, asal, href, pos):
    badge = "Lokal" if asal == "lokal" else "Korea"
    return f"""<div class="sisi sisi-{asal} pos-{pos}">
      <p class="asal asal-{asal}">{badge}</p>
      <h3><a href="{esc(href)}">{esc(copy["nama"])}</a></h3>
      <p class="harga">{harga_html(p)}</p>
      {beli(p, copy["nama"])}
    </div>"""


def json_ld_beranda():
    """Data terstruktur beranda: nama situs dan logo untuk hasil pencarian Google."""
    graf = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": BASE_URL + "#website",
                "name": MEREK,
                "alternateName": "PilihYuk.id",
                "url": BASE_URL,
                "inLanguage": "id-ID",
                "publisher": {"@id": BASE_URL + "#organization"},
            },
            {
                "@type": "Organization",
                "@id": BASE_URL + "#organization",
                "name": MEREK,
                "url": BASE_URL,
                "logo": {
                    "@type": "ImageObject",
                    "url": GAMBAR_SOSIAL,
                    "width": 512,
                    "height": 512,
                },
                "sameAs": AKUN_RESMI,
            },
        ],
    }
    return '<script type="application/ld+json">' + json_aman(graf) + "</script>"


def tulis_manifest():
    manifest = {
        "name": MEREK,
        "short_name": MEREK,
        "start_url": "/",
        "display": "browser",
        "background_color": "#fffcf8",
        "theme_color": "#f3efe7",
        "icons": [
            {"src": f"/img/favicon-{n}.png", "sizes": f"{n}x{n}", "type": "image/png"}
            for n in (48, 96, 192, 512)
        ],
    }
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


def render_index(data, produk, pasangan):
    kartu = []
    for i, pair in enumerate(pasangan):
        (_, ia, asal_a), (_, ib, asal_b) = sisi_pair(pair)
        lok = produk_pair(produk, pair, ia)
        kor = produk_pair(produk, pair, ib)
        cl = pair["produk"][ia]
        ck = pair["produk"][ib]
        href = f"banding/{pair['id']}.html"
        b = jenis_banding(pair)
        cari = " ".join([
            pair["hook"], pair["ringkas"], cl["nama"], ck["nama"],
            JENIS_LABEL[pair["jenis"]], BANDING_LABEL[b],
            " ".join(x["nama"] for x in cl["bahan"]),
            " ".join(x["nama"] for x in ck["bahan"]),
            " ".join(v["nama"] for v in cl.get("varian", [])),
            " ".join(v["nama"] for v in ck.get("varian", [])),
        ]).lower()
        kartu.append(f"""<article class="duel" data-jenis="{esc(pair["jenis"])}" data-banding="{esc(b)}" data-cari="{esc(cari)}">
  <div class="kicker-baris"><p class="kicker">{esc(JENIS_LABEL[pair["jenis"]])}</p>{badge_banding(pair)}</div>
  <h2><a href="{href}">{esc(pair["hook"])}</a></h2>
  <p class="lawan">{esc(cl["nama"])} <span>vs</span> {esc(ck["nama"])}</p>
  <div class="duo">
    {foto_tautan(lok, cl, asal_a, i == 0, href, "", 1)}
    <div class="vs" aria-hidden="true">vs</div>
    {foto_tautan(kor, ck, asal_b, i == 0, href, "", 2)}
    {meta_kartu(lok, cl, asal_a, href, 1)}
    {meta_kartu(kor, ck, asal_b, href, 2)}
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

    chips_b = ['<button type="button" class="chip aktif" data-banding-filter="semua" aria-pressed="true">Semua</button>']
    for kunci, label in BANDING_JENIS:
        n = sum(1 for p in pasangan if jenis_banding(p) == kunci)
        chips_b.append(
            f'<button type="button" class="chip" data-banding-filter="{kunci}" aria-pressed="false">{esc(label)} <span class="count">{n}</span></button>'
        )

    desk = (
        "PilihYuk mengadu dua skincare sejenis, lokal vs Korea atau lokal vs lokal: facial wash, pelembab, "
        "serum, dan sunscreen. Lihat kandungan, harga, dan cocok untuk kulit yang mana."
    )
    html = head(
        "PilihYuk — Facial Wash, Pelembab, Serum, Sunscreen Lokal vs Korea",
        desk,
        "",
        "index.html",
        "\n  " + json_ld_beranda(),
    )
    html += f"""<body>
{header("")}
<main>
  <section class="hero">
    <div class="wrap">
      <p class="kicker kicker-terang">Lokal vs Korea · Lokal vs Lokal</p>
      <h1>Skincare mana yang mending?</h1>
      <p>Dua produk sejenis diadu berdampingan: lokal vs Korea, atau lokal vs lokal. Ada facial wash, pelembab, serum, dan sunscreen. Lihat kandungan, harga, dan cocok untuk kulit yang mana.</p>
      <form class="search" id="form-cari" role="search">
        <label class="sr" for="q">Cari perbandingan</label>
        <input id="q" type="search" placeholder="Cari merek atau bahan, misalnya niacinamide" autocomplete="off">
      </form>
      <aside class="ajak-banding">
        <p><strong>Mau adu produk pilihanmu sendiri?</strong> Pilih dua atau tiga produk, bedanya langsung kelihatan.</p>
        <a class="btn btn-banding" href="bandingkan.html">Bandingin sendiri</a>
      </aside>
    </div>
  </section>
  <div class="wrap" id="daftar">
    <div class="filter" role="group" aria-label="Filter jenis">{''.join(chips)}</div>
    <div class="filter filter-banding" role="group" aria-label="Filter perbandingan"><span class="filter-label">Perbandingan:</span>{''.join(chips_b)}</div>
    <p class="hasil" id="hasil" aria-live="polite">{len(pasangan)} perbandingan</p>
    {catatan_beli("", "catatan-beli-index")}
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
  var banding = "semua";
  var q = document.getElementById("q");
  var chips = Array.prototype.slice.call(document.querySelectorAll("[data-filter]"));
  var chipsB = Array.prototype.slice.call(document.querySelectorAll("[data-banding-filter]"));
  var kartu = Array.prototype.slice.call(document.querySelectorAll(".duel"));
  var hasil = document.getElementById("hasil");
  var kosong = document.getElementById("kosong");
  var sah = {{ pelembab: 1, serum: 1, sunscreen: 1, "facial-wash": 1, semua: 1 }};

  function terapkan() {{
    var s = (q.value || "").toLowerCase().trim();
    var n = 0;
    kartu.forEach(function (el) {{
      var okJ = jenis === "semua" || el.getAttribute("data-jenis") === jenis;
      var okB = banding === "semua" || el.getAttribute("data-banding") === banding;
      var okS = !s || el.getAttribute("data-cari").indexOf(s) !== -1;
      var tampil = okJ && okB && okS;
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
  chipsB.forEach(function (c) {{
    c.addEventListener("click", function () {{
      banding = c.getAttribute("data-banding-filter");
      chipsB.forEach(function (d) {{
        var aktif = d === c;
        d.classList.toggle("aktif", aktif);
        d.setAttribute("aria-pressed", aktif ? "true" : "false");
      }});
      terapkan();
    }});
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


def tabel_varian(pair, kunci, iid, copy):
    baris = []
    for v in copy["varian"]:
        baris.append(
            f'<tr><th scope="row">{esc(v["nama"])}</th><td>{esc(v["bahan"])}</td>'
            f'<td>{esc(", ".join(v["kulit"]))}</td><td>{esc(v.get("catatan", ""))}</td></tr>'
        )
    return f"""<div class="varian-sisi">
      <h3>{esc(copy["nama"])} <span class="varian-n">{len(copy["varian"])} varian</span></h3>
      <div class="tabel-wrap">
        <table class="cmp cmp-varian">
          <caption class="sr">Varian {esc(copy["nama"])}</caption>
          <thead><tr><th scope="col">Varian</th><th scope="col">Kandungan kunci</th><th scope="col">Cocok untuk</th><th scope="col">Catatan</th></tr></thead>
          <tbody>{''.join(baris)}</tbody>
        </table>
      </div>
    </div>"""


def bagian_varian(pair):
    sisi = [(k, iid, pair["produk"][iid]) for k, iid, _ in sisi_pair(pair) if pair["produk"][iid].get("varian")]
    if not sisi:
        return ""
    html = '\n  <section class="varian" id="varian">\n  <h2 class="bagian">Varian satu per satu</h2>\n'
    html += f'  <p class="varian-intro">{esc(pair.get("varianIntro", "Link ini berisi beberapa varian. Pilih varian saat checkout."))}</p>\n'
    html += "".join(tabel_varian(pair, k, iid, c) for k, iid, c in sisi)
    if pair.get("adu"):
        (ka, _, _), (kb, _, _) = sisi_pair(pair)
        baris = []
        for a in pair["adu"]:
            baris.append(
                f'<tr><th scope="row">{esc(a["kebutuhan"])}</th><td>{esc(a[ka])}</td><td>{esc(a[kb])}</td>'
                f'<td class="pilih">{esc(a["pilih"])}</td></tr>'
            )
        html += f"""<h3 class="adu-judul">Adu varian: kebutuhan yang sama, dua pilihan</h3>
    <div class="tabel-wrap">
      <table class="cmp cmp-adu">
        <caption class="sr">Adu varian {esc(label_sisi(pair, ka))} dan {esc(label_sisi(pair, kb))}</caption>
        <thead><tr><th scope="col">Kebutuhan</th><th scope="col">{esc(label_sisi(pair, ka))}</th><th scope="col">{esc(label_sisi(pair, kb))}</th><th scope="col">Pilih yang mana</th></tr></thead>
        <tbody>{''.join(baris)}</tbody>
      </table>
    </div>"""
    return html + "\n</section>"


def render_pair(data, produk, pair, sumber=None):
    sumber = sumber or {}
    (ka, ia, asal_a), (kb, ib, asal_b) = sisi_pair(pair)
    lok = produk_pair(produk, pair, ia)
    kor = produk_pair(produk, pair, ib)
    cl = pair["produk"][ia]
    ck = pair["produk"][ib]
    lokal_lokal = jenis_banding(pair) == "lokal-lokal"
    base = "../"
    judul = f"{pair['hook']} {cl['nama']} vs {ck['nama']}"
    desk = pair["ringkas"]
    x = ""
    if pair.get("x"):
        x = f'<p class="lihat-x"><a href="{esc(pair["x"])}" target="_blank" rel="noopener noreferrer">Lihat di X</a></p>'

    def blok_atas(p, copy, asal, pos):
        badge = "Lokal" if asal == "lokal" else "Korea"
        foto_html = foto(p["id"], copy["nama"], True).replace("{base}", base)
        return (
            f'<div class="photo photo-{asal} pos-{pos}">{foto_html}</div>',
            f"""<div class="sisi sisi-{asal} pos-{pos}">
      <p class="asal asal-{asal}">{badge}</p>
      <h2>{esc(copy["nama"])}</h2>{varian_dipilih_html(copy)}
      <p class="tekstur">{esc(copy["tekstur"])}</p>
      <ul class="kulit">{kulit_html(copy)}</ul>
      <p class="harga">{harga_html(p)}</p>
      {beli(p, copy["nama"])}
    </div>""",
        )

    def blok_detail(p, copy, asal, kunci):
        badge = "Lokal" if asal == "lokal" else "Korea"
        anchor = f"lokal-{kunci}" if lokal_lokal else asal
        return f"""<article class="detail sisi-{asal}" id="{anchor}">
      <p class="asal asal-{asal}">{badge}</p>
      <h2>{esc(copy["nama"])}</h2>{varian_dipilih_html(copy)}
      <p class="tekstur">{esc(copy["tekstur"])} · {esc(copy["isi"])}</p>
      <h3>Kandungan utama</h3>
      {list_bahan(copy)}
      <h3>Manfaat</h3>
      {list_manfaat(copy)}
      <h3>Cocok untuk kulit</h3>
      <ul class="kulit">{kulit_html(copy)}</ul>{catatan_pemakai_html(copy)}
      <p class="catatan">{esc(copy["catatan"])}</p>
      {sumber_html(sumber.get(p["id"]))}
      <p class="harga">{harga_html(p)}</p>
      {beli(p, copy["nama"])}
    </article>"""

    def sel_beli(p, copy):
        return beli(p, copy["nama"], "btn btn-sm")

    tabel = f"""<div class="tabel-wrap">
      <table class="cmp">
        <caption class="sr">Perbandingan {esc(cl["nama"])} dan {esc(ck["nama"])}</caption>
        <thead>
          <tr><th scope="col"> </th><th scope="col">{esc(label_sisi(pair, ka))}</th><th scope="col">{esc(label_sisi(pair, kb))}</th></tr>
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
    foto_l, meta_l = blok_atas(lok, cl, asal_a, 1)
    foto_k, meta_k = blok_atas(kor, ck, asal_b, 2)
    html = head(judul + " — " + MEREK, desk, base, f"banding/{pair['id']}.html")
    html += f"""<body>
{header(base, pair["jenis"])}
<main class="wrap artikel">
  <p class="crumbs"><a href="../index.html">Beranda</a> / <a href="../index.html#{esc(pair["jenis"])}">{esc(JENIS_LABEL[pair["jenis"]])}</a></p>
  <div class="kicker-baris"><p class="kicker">{esc(JENIS_LABEL[pair["jenis"]])}</p>{badge_banding(pair)}</div>
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
  {catatan_beli(base)}
  <h2 class="bagian">Perbandingan singkat</h2>
  {tabel}
  <h2 class="bagian">Kandungan dan manfaat</h2>
  <div class="detail-grid">
    {blok_detail(lok, cl, asal_a, ka)}
    {blok_detail(kor, ck, asal_b, kb)}
  </div>
  {catatan_beli(base)}{bagian_varian(pair)}
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
        <h3>Soal harga</h3>
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
        ia, ib = id_pair(pair)
        cl = pair["produk"][ia]["nama"]
        ck = pair["produk"][ib]["nama"]
        label = f'{JENIS_LABEL[pair["jenis"]]}: {cl} vs {ck}'
        opsi.append(f'<option value="{esc(pair["id"])}">{esc(label)}</option>')
    angka = []
    for n in range(1, 6):
        angka.append(f'<label><input type="radio" name="mudah" value="{n}"> {n}</label>')
    desk = "Kasih pendapat tentang PilihYuk: apakah perbandingannya membantu memilih produk, plus saran dan kritik."
    html = head("Kasih Pendapat — " + MEREK, desk, "", "ulasan.html")
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


def render_tentang(data, pasangan):
    n_lk = sum(1 for p in pasangan if jenis_banding(p) == "lokal-korea")
    n_ll = sum(1 for p in pasangan if jenis_banding(p) == "lokal-lokal")
    if KONTAK_LAIN:
        kontak_lain = "<p>Kontak lain: " + " · ".join(
            f'<a href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(l)}</a>' for l, u in KONTAK_LAIN
        ) + "</p>"
    else:
        kontak_lain = (
            "<!-- PLACEHOLDER KONTAK: email atau akun media sosial PilihYuk belum ditentukan.\n"
            "       Isi KONTAK_LAIN di tools/build_site.py, lalu bangun ulang. Jangan isi alamat karangan. -->"
        )
    desk = (
        "Tentang PilihYuk: siapa yang mengelola, kenapa situs ini dibuat, cara perbandingan disusun, "
        "dan penjelasan link affiliate Shopee."
    )
    html = head("Tentang Kami — " + MEREK, desk, "", "tentang.html")
    html += f"""<body>
{header("", "tentang")}
<main class="wrap artikel tentang">
  <p class="crumbs"><a href="index.html">Beranda</a> / Tentang Kami</p>
  <h1>Tentang PilihYuk</h1>

  <section id="pengelola">
    <h2 class="bagian">Siapa yang mengelola</h2>
    <p>PilihYuk dikelola secara independen oleh Albi. Perbandingan disusun dari data produk yang bisa dicek (harga Shopee, daftar kandungan dari situs resmi merek dan database kandungan). Isinya informasi umum, bukan saran medis. Kalau ragu, konsultasikan ke dokter kulit.</p>
    <p>Ini proyek pribadi, bukan toko dan bukan bagian dari merek mana pun.</p>
  </section>

  <section id="kenapa">
    <h2 class="bagian">Kenapa situs ini ada</h2>
    <p>Pilihan skincare banyak sekali dan sering bikin bingung. PilihYuk dibuat untuk membantu kamu memilih skincare lokal vs Korea, dan lokal vs lokal, secara jujur: produk dari jenis yang sama dibandingkan berdampingan supaya kamu bisa memutuskan sendiri.</p>
    <p>Saat ini ada {len(pasangan)} perbandingan: {n_lk} Lokal vs Korea dan {n_ll} Lokal vs Lokal.</p>
  </section>

  <section id="cara">
    <h2 class="bagian">Cara perbandingan dibuat</h2>
    <ul class="daftar-tentang">
      <li><strong>Harga</strong> diambil dari halaman produk Shopee per {esc(data["tanggal"])}. Harga dan diskon bisa berubah sewaktu-waktu, jadi cek lagi harga terakhir di Shopee.</li>
      <li><strong>Kandungan</strong> diambil dari informasi produk di Shopee, website resmi merek, dan database bahan seperti INKEEDecoder (dulu INCIDecoder) dan Skinsort. Kalau sumbernya tercatat, tautannya ada di bagian <em>Sumber kandungan</em> di halaman perbandingan.</li>
      <li>Kalau daftar bahan tidak tercantum, kami tulis apa adanya dan tidak mengarang.</li>
      <li><strong>Tidak ada klaim medis.</strong> Isi situs ini informasi umum, bukan pengganti saran dokter. Kalau kulitmu bermasalah atau sensitif, konsultasikan ke dokter kulit.</li>
    </ul>
  </section>

  <section id="affiliate">
    <h2 class="bagian">Soal link affiliate</h2>
    <p>{esc(CATATAN_AFFILIATE)}</p>
    <p>{esc(CATATAN_AMAN)} Tombol <em>Beli di Shopee</em> membuka halaman produk di Shopee. Semua pembelian dan pembayaran terjadi di Shopee, bukan di PilihYuk.</p>
    <p>Komisi tidak menentukan isi perbandingan. Produk yang lebih murah atau lebih cocok tetap ditulis apa adanya.</p>
  </section>

  <section id="aman">
    <h2 class="bagian">Tanpa login, tanpa pembayaran</h2>
    <p>{esc(CATATAN_STATIS)} Kamu tidak perlu membuat akun atau memasukkan data apa pun untuk membaca perbandingan.</p>
  </section>

  <section id="kontak">
    <h2 class="bagian">Kontak</h2>
    <p>Punya pertanyaan, koreksi, atau ide perbandingan berikutnya? Kirim lewat formulir <a href="ulasan.html">Kasih Pendapat</a>. Pesanmu langsung masuk ke catatan Albi. Kolom nama atau kontak di formulir boleh dikosongkan.</p>
    {kontak_lain}
  </section>
</main>
{footer("", data["tanggal"])}
</body>
</html>
"""
    return html


# Halaman Bandingin Sendiri (bandingkan.html): pengunjung memilih 2-3 produk sendiri.
# Datanya dibangun dari pasangan.json + sumber/*.psv setiap kali build, jadi produk baru
# di pasangan otomatis ikut. Hanya produk yang tampil di situs (ada di pasangan) yang bisa
# dipilih, karena hanya produk itu yang punya foto, jenis kulit, dan kandungan yang sudah dicek.
#
# REQUEST_AKTIF: bagian "Produk yang kamu mau belum ada?" di halaman yang sama. Kiriman masuk
# ke alamat FEEDBACK_ENDPOINT di js/config.js (Google Sheet yang sama dengan Kasih Pendapat).
# Isi False untuk menyembunyikan bagian itu tanpa menghapus kodenya.
REQUEST_AKTIF = True

# Nama merek seperti yang ditulis di situs. Dicocokkan dengan awal nama produk (tanpa beda
# huruf besar/kecil) atau dengan kolom brand di tambahan-*.psv. Merek baru yang belum ada di
# sini tetap tampil (pakai kolom brand), generator hanya memberi peringatan.
MEREK_TAMPIL = [
    "Anua", "Avoskin", "Azarine", "Barber", "Beauty of Joseon", "COSRX", "ELVICTO", "Emina",
    "Glad2Glow", "Gloow&be", "Hanasui", "ILLIYOON", "ISNTREE", "Kahf", "LANEIGE", "MS Glow",
    "Nature Republic", "NEXTPRIME", "OMG", "Round Lab", "Scarlett", "SCORA", "SKIN1004", "SKINTIFIC",
    "SOME BY MI", "Somethinc",
    "The Originote", "Torriden", "Wardah", "Whitelab",
]
JENIS_KULIT_REQUEST = ["Berminyak", "Kering", "Kombinasi", "Normal", "Sensitif", "Berjerawat", "Belum tahu"]


def merek_tampil(p, copy):
    nama = copy["nama"].lower()
    mentah = (p.get("merek") or "").strip().lower()
    for m in sorted(MEREK_TAMPIL, key=len, reverse=True):
        ml = m.lower()
        if nama.startswith(ml) or (mentah and mentah in (ml, ml.replace("the ", ""))):
            return m
    if p.get("merek"):
        print(f"PERINGATAN: merek {p['merek']!r} ({p['id']}) belum ada di MEREK_TAMPIL")
        return p["merek"]
    tebak = copy["nama"].split()[0]
    print(f"PERINGATAN: merek {p['id']} ditebak dari nama: {tebak!r}. Tambahkan ke MEREK_TAMPIL.")
    return tebak


def data_bandingkan(produk, pasangan):
    """Daftar produk untuk halaman Bandingin Sendiri. Semua isinya dari data, tidak ada teks baru.

    Satu entri per produk. Produk yang dipakai di beberapa pasangan memakai data pasangan
    terbaru (urutan terakhir di pasangan.json, termasuk harga/link dari "listing"), dan
    semua pasangannya dicatat di "pairs".
    """
    per_id = {}
    for pair in pasangan:
        sisi = sisi_pair(pair)
        nama_pair = " vs ".join(pair["produk"][iid]["nama"] for _, iid, _ in sisi)
        for _, iid, asal in sisi:
            p = produk_pair(produk, pair, iid)
            copy = pair["produk"][iid]
            catatan_varian = ""
            if copy.get("varianDipilih"):
                catatan_varian = f"Varian yang dibahas: {copy['varianDipilih']}"
            elif copy.get("varian"):
                catatan_varian = f"{len(copy['varian'])} varian dalam satu link: " + ", ".join(
                    v["nama"] for v in copy["varian"]
                )
            pairs = per_id[iid]["pairs"] if iid in per_id else []
            pairs.append([pair["id"], nama_pair])
            per_id[iid] = {
                "id": iid,
                "jenis": pair["jenis"],
                "nama": copy["nama"],
                "merek": merek_tampil(p, copy),
                "asal": asal,
                "harga": p["harga"],
                # listing dengan beberapa pilihan ukuran/varian: rentang harga, tanpa coret
                "hargaMaks": p.get("harga_maks") or None,
                "asli": p["asli"] if not p.get("harga_maks") and p["asli"] and p["asli"] > p["harga"] else None,
                "isi": copy["isi"],
                "tekstur": copy["tekstur"],
                "kulit": list(copy["kulit"]),
                "bahan": [b["nama"] for b in copy["bahan"]],
                "varian": catatan_varian,
                # tombol beli: link pendek affiliate; kalau belum ada, URL produk Shopee
                "link": p["aff"] or p["url"],
                "pairs": pairs,
            }
    hasil = list(per_id.values())
    hasil.sort(key=lambda x: (x["merek"].lower(), x["nama"].lower()))
    return hasil


def json_aman(obj):
    """JSON untuk <script type="application/json">: tanpa '</' supaya tag tidak tertutup."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_bandingkan(data, produk, pasangan):
    daftar = data_bandingkan(produk, pasangan)
    chips = []
    for kunci, label in JENIS:
        n = sum(1 for d in daftar if d["jenis"] == kunci)
        if not n:
            continue
        chips.append(
            f'<button type="button" class="chip" data-jenis="{kunci}" aria-pressed="false">'
            f'{esc(label)} <span class="count">{n}</span></button>'
        )
    payload = {
        "tanggal": data["tanggal"],
        "jenis": {k: l for k, l in JENIS},
        "produk": daftar,
    }
    opsi_kulit = '<option value="">Lewati saja</option>' + "".join(
        f'<option value="{esc(k)}">{esc(k)}</option>' for k in JENIS_KULIT_REQUEST
    )
    hidden_req = "" if REQUEST_AKTIF else " hidden"
    desk = (
        "Pilih dua atau tiga skincare sendiri, lalu lihat berdampingan: harga, asal, jenis kulit, "
        "dan kandungan utama. Facial wash, pelembab, serum, dan sunscreen."
    )
    html = head("Bandingin Sendiri — " + MEREK, desk, "", "bandingkan.html")
    html += f"""<body>
{header("", "bandingkan")}
<main class="wrap artikel bandingkan">
  <p class="crumbs"><a href="index.html">Beranda</a> / Bandingin Sendiri</p>
  <h1>Bandingin sendiri</h1>
  <p class="intro-form">Pilih jenis produknya dulu. Lalu pilih dua produk, atau tiga kalau masih galau. Hasilnya muncul berdampingan di bawah.</p>

  <section class="pilih-langkah" aria-labelledby="langkah-1">
    <h2 class="langkah" id="langkah-1"><span>1</span> Pilih jenis</h2>
    <div class="filter filter-pilih" role="group" aria-label="Jenis produk">{''.join(chips)}</div>
  </section>

  <section class="pilih-langkah" aria-labelledby="langkah-2">
    <h2 class="langkah" id="langkah-2"><span>2</span> Pilih 2 atau 3 produk</h2>
    <form class="search search-pilih" id="form-cari-produk" role="search">
      <label class="sr" for="cari-produk">Cari produk</label>
      <input id="cari-produk" type="search" placeholder="Cari merek atau bahan" autocomplete="off" disabled>
    </form>
    <p class="info-pilih" id="info-pilih" aria-live="polite">Pilih jenis produknya dulu, ya.</p>
    <ul class="grid-pilih" id="grid-pilih"></ul>
    <p class="kosong" id="kosong-pilih" hidden>Nggak ada yang cocok. Coba kata lain.</p>
  </section>

  <section class="hasil-banding" id="hasil-banding" hidden aria-labelledby="judul-hasil" tabindex="-1">
    <h2 class="bagian" id="judul-hasil">Hasil perbandingan</h2>
    <p class="ringkas-harga" id="ringkas-harga"></p>
    <div class="pair-ada" id="pair-ada" hidden></div>
    <div class="banding-grid" id="banding-grid"></div>
    <p class="catatan-harga">Harga dari halaman produk Shopee per {esc(data["tanggal"])} dan bisa berubah. Ukuran tiap produk bisa beda, jadi cek juga isinya.</p>
    {catatan_beli("")}
  </section>

  <template id="tpl-beli"><a class="btn btn-sm" target="_blank" rel="sponsored noopener noreferrer">Beli di Shopee</a></template>

  <section class="request" id="request" aria-labelledby="judul-request"{hidden_req}>
    <h2 class="bagian" id="judul-request">Produk yang kamu mau belum ada? Request di sini</h2>
    <p class="intro-form">Tulis nama produknya. Kalau mau diadu sama produk lain, tulis juga yang kedua. Albi baca semua request yang masuk.</p>
    <form class="form-kartu" id="form-request" action="#" method="post" novalidate>
      <div class="field">
        <label class="label" for="req-produk-1">Nama produk 1</label>
        <input id="req-produk-1" name="produk_1" type="text" maxlength="150" required placeholder="Merek dan nama produknya">
      </div>
      <div class="field">
        <label class="label" for="req-produk-2">Nama produk 2 <span class="opsional">opsional</span></label>
        <input id="req-produk-2" name="produk_2" type="text" maxlength="150" placeholder="Kalau mau dibandingin sama produk lain">
      </div>
      <div class="field">
        <label class="label" for="req-kulit">Jenis kulit kamu <span class="opsional">opsional</span></label>
        <select id="req-kulit" name="jenis_kulit">{opsi_kulit}</select>
      </div>
      <div class="field">
        <label class="label" for="req-catatan">Catatan <span class="opsional">opsional</span></label>
        <textarea id="req-catatan" name="catatan" maxlength="1000" placeholder="Misalnya budget kamu, atau masalah kulit yang lagi dicari solusinya"></textarea>
      </div>
      <div class="hp" aria-hidden="true">
        <label for="req-situs">Jangan diisi</label>
        <input id="req-situs" name="situs" type="text" tabindex="-1" autocomplete="off">
      </div>
      <p class="pesan-form" id="pesan-request" aria-live="polite" hidden></p>
      <button class="btn btn-kirim" type="submit">Kirim request</button>
    </form>
    <section class="sukses" id="sukses-request" hidden aria-live="polite">
      <h3>Request kamu sudah masuk. Makasih!</h3>
      <p>Mau request produk lain? <button type="button" class="tautan-tombol" id="request-lagi">Isi lagi</button></p>
    </section>
  </section>
</main>
<div class="baki" id="baki" hidden>
  <div class="wrap baki-isi">
    <p class="baki-teks" id="baki-teks"></p>
    <button type="button" class="btn baki-lihat" id="baki-lihat">Lihat hasil</button>
  </div>
</div>
{footer("", data["tanggal"])}
<script type="application/json" id="data-bandingkan">{json_aman(payload)}</script>
<script src="js/config.js"></script>
<script src="js/bandingkan.js"></script>
</body>
</html>
"""
    return html, daftar


def periksa_bandingkan(html, daftar, pasangan):
    """Data Bandingin Sendiri: satu entri per produk di pasangan, semua punya foto dan link."""
    m = re.search(r'<script type="application/json" id="data-bandingkan">(.*?)</script>', html, re.S)
    if not m:
        raise SystemExit("bandingkan.html: data produk tidak ada")
    isi = json.loads(m.group(1))["produk"]
    harus = {iid for pair in pasangan for iid in id_pair(pair)}
    ada = [d["id"] for d in isi]
    if len(ada) != len(set(ada)) or set(ada) != harus:
        raise SystemExit("bandingkan.html: daftar produk tidak sama dengan produk di pasangan")
    per_pair = {}
    for d in isi:
        for k in ("nama", "merek", "asal", "harga", "kulit", "bahan", "link", "pairs", "jenis"):
            if not d.get(k):
                raise SystemExit(f"bandingkan.html: {d['id']} kosong: {k}")
        if d["asal"] not in ("lokal", "korea"):
            raise SystemExit(f"bandingkan.html: asal salah {d['id']}")
        if not os.path.isfile(os.path.join(IMG, d["id"] + ".jpg")):
            raise SystemExit(f"bandingkan.html: foto {d['id']} tidak ada")
        if not (d["link"].startswith("https://s.shopee.co.id/") or d["link"].startswith("https://shopee.co.id/")):
            raise SystemExit(f"bandingkan.html: link beli aneh {d['id']}")
        for pid, _ in d["pairs"]:
            per_pair.setdefault(pid, []).append(d)
    for pair in pasangan:
        if len(per_pair.get(pair["id"], [])) != 2:
            raise SystemExit(f"bandingkan.html: pasangan {pair['id']} tidak lengkap")
        if not os.path.isfile(os.path.join(BANDING, pair["id"] + ".html")):
            raise SystemExit(f"bandingkan.html: banding/{pair['id']}.html tidak ada")
    if 'id="form-request"' not in html or "js/config.js" not in html:
        raise SystemExit("bandingkan.html: formulir request tidak lengkap")


def periksa(html_per_path, produk, pasangan, posted, merek, sumber=None):
    # posted.log tetap disimpan sebagai arsip. Posting affiliate di X/Threads sudah berhenti,
    # jadi pasangan yang pernah diposting boleh dirombak. Yang dicek: kalau pasangan itu masih
    # ada, link X-nya harus sama; dan link X hanya boleh menempel di pasangan yang memang diposting.
    xsah = {}
    for a, b, xurl in posted:
        xsah[frozenset((a, b))] = xurl
    for pair in pasangan:
        kunci = frozenset(id_pair(pair))
        if pair.get("x"):
            if kunci not in xsah:
                raise SystemExit(f"{pair['id']}: link X ada, tapi pasangan ini tidak ada di posted.log")
            if pair["x"] != xsah[kunci]:
                raise SystemExit(f"Link X tidak cocok untuk {pair['id']}")
        elif kunci in xsah:
            raise SystemExit(f"{pair['id']} ada di posted.log, link X-nya hilang")

    sumber_sah = {u for urls in (sumber or {}).values() for u in urls}
    terpakai = []
    for pair in pasangan:
        if pair["jenis"] not in JENIS_LABEL:
            raise SystemExit("Jenis tidak dikenal: " + pair["jenis"])
        b = jenis_banding(pair)
        if b not in BANDING_LABEL:
            raise SystemExit("Jenis perbandingan tidak dikenal: " + b)
        if b == "lokal-lokal" and ("lokal" in pair or "korea" in pair):
            raise SystemExit(f"{pair['id']}: lokal vs lokal memakai kunci a dan b")
        for kunci_sisi_ini, iid, sisi in sisi_pair(pair):
            if iid not in pair["produk"]:
                raise SystemExit(f"{pair['id']} tanpa teks {iid}")
            p = produk_pair(produk, pair, iid)
            if p["aff"] is None:
                if not DRAFT:
                    raise SystemExit("Link affiliate kosong " + iid)
            elif not p["aff"].startswith("https://s.shopee.co.id/"):
                raise SystemExit("Link affiliate salah " + iid)
            if p.get("merek"):
                terdaftar = any(p["merek"].lower() == m.lower() for m in merek)
                if p.get("asal") == "korea" and not terdaftar:
                    raise SystemExit(f"Merek Korea belum didaftarkan: {p['merek']}")
                if p.get("asal") == "lokal" and terdaftar:
                    raise SystemExit(f"Merek lokal ada di daftar Korea: {p['merek']}")
            if p.get("asal") and p["asal"] != sisi:
                raise SystemExit(f"{iid} asal {p['asal']} dipakai sebagai {sisi}")
            korea = judul_korea(p["judul"], merek)
            if sisi == "korea" and not korea:
                raise SystemExit(f"{iid} bukan merek Korea: {p['judul'][:80]}")
            if sisi == "lokal" and korea:
                raise SystemExit(f"{iid} terdeteksi merek Korea, dipakai sebagai lokal")
            copy = pair["produk"][iid]
            mentah = (p.get("bahan_mentah") or "").strip().lower()
            if mentah == "tidak tercantum":
                teks_copy = json.dumps(copy, ensure_ascii=False).lower()
                if "tidak tercantum" not in teks_copy and "tidak menuliskan" not in teks_copy:
                    raise SystemExit(f"{pair['id']} {iid}: bahan tidak tercantum, teks jangan mengarang daftar")
            for kunci in ("nama", "tekstur", "isi", "catatan", "bahan", "manfaat", "kulit"):
                if not copy.get(kunci):
                    raise SystemExit(f"{pair['id']} {iid} kosong: {kunci}")
            if len(copy["bahan"]) < 1 or len(copy["manfaat"]) < 2 or len(copy["kulit"]) < 1:
                raise SystemExit(f"{pair['id']} {iid} isi kurang")
            cp = copy.get("catatan_pemakai")
            if cp is not None:
                if not isinstance(cp, str) or not cp.strip():
                    raise SystemExit(f"{pair['id']} {iid}: catatan_pemakai kosong")
                if PLATFORM_CATATAN.search(cp):
                    raise SystemExit(f"{pair['id']} {iid}: catatan_pemakai menyebut platform/review: {cp}")
                if len(cp) > 220:
                    raise SystemExit(f"{pair['id']} {iid}: catatan_pemakai terlalu panjang")
            if copy.get("varianDipilih"):
                if copy.get("varian"):
                    raise SystemExit(f"{pair['id']} {iid}: varianDipilih tidak boleh digabung dengan varian")
                if copy["varianDipilih"].lower() not in copy["nama"].lower():
                    raise SystemExit(f"{pair['id']} {iid}: nama kartu harus menyebut varian {copy['varianDipilih']}")
                if "varian lain" not in copy["catatan"].lower():
                    raise SystemExit(f"{pair['id']} {iid}: tulis bahwa link berisi varian lain")
            if b != "lokal-lokal" and SERI_LISTING.search(p["judul"]) and not (copy.get("varian") or copy.get("varianDipilih")):
                raise SystemExit(f"{pair['id']} {iid}: listing seri di lokal vs Korea wajib memilih satu varian (varianDipilih)")
            for v in copy.get("varian", []):
                for k in ("nama", "bahan", "kulit"):
                    if not v.get(k):
                        raise SystemExit(f"{pair['id']} {iid} varian {v.get('nama')} kosong: {k}")
            if copy.get("varian"):
                if b == "lokal-lokal":
                    # setiap varian wajib diadu berdampingan, lengkap dengan pilihan
                    disebut = " ".join(a.get(kunci_sisi_ini, "") for a in pair.get("adu", []))
                    for v in copy["varian"]:
                        if v["nama"] not in disebut:
                            raise SystemExit(f"{pair['id']}: varian {v['nama']} belum diadu")
                elif "varian lain" not in copy["catatan"].lower():
                    raise SystemExit(f"{pair['id']} {iid}: tulis bahwa link berisi varian lain")
        for a in pair.get("adu", []):
            for k in ("kebutuhan", "pilih") + tuple(k for k, _, _ in sisi_pair(pair)):
                if not a.get(k):
                    raise SystemExit(f"{pair['id']}: adu varian kosong: {k}")
        kunci_sisi = [k for k, _, _ in sisi_pair(pair)]
        if pair["lebihMurah"] not in kunci_sisi:
            raise SystemExit("lebihMurah salah " + pair["id"])
        (k1, i1, _), (k2, i2, _) = sisi_pair(pair)
        harga = {k1: produk_pair(produk, pair, i1)["harga"], k2: produk_pair(produk, pair, i2)["harga"]}
        lain = k2 if pair["lebihMurah"] == k1 else k1
        if not harga[pair["lebihMurah"]] < harga[lain]:
            raise SystemExit(f"{pair['id']} {pair['lebihMurah']} tidak lebih murah")
        for kunci in ("berminyak", "kering", "budget"):
            if not pair["verdict"].get(kunci):
                raise SystemExit(f"verdict {kunci} kosong {pair['id']}")
        terpakai.append(frozenset(id_pair(pair)))
    # Produk boleh dipakai lagi di pasangan lain (lihat produk_pair), tapi pasangan yang
    # sama persis tidak boleh muncul dua kali.
    if len(terpakai) != len(set(terpakai)):
        raise SystemExit("Ada pasangan produk yang sama persis lebih dari sekali")

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
            if href.startswith(BASE_URL):
                bersih = href[len(BASE_URL):] or "index.html"
                if not os.path.isfile(os.path.join(ROOT, bersih)):
                    raise SystemExit(f"URL absolut putus di {path}: {href}")
                continue
            if href in sumber_sah:
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
            if src == "https://gc.zgo.at/count.js":  # penghitung pengunjung GoatCounter
                continue
            tujuan = os.path.normpath(os.path.join(ROOT, os.path.dirname(path), src))
            if not os.path.isfile(tujuan):
                raise SystemExit(f"Gambar putus di {path}: {src}")
        # tombol beli hanya link pendek. Halaman pendapat tidak menjual produk.
        if path not in ("index.html", "ulasan.html", "tentang.html") and "Beli di Shopee" not in html:
            if not (DRAFT and "Link menyusul" in html):
                raise SystemExit("Tidak ada tombol beli di " + path)
        if "Link menyusul" in html and not DRAFT:
            raise SystemExit("Tombol Link menyusul hanya boleh di --draft: " + path)

    index = html_per_path["index.html"]
    if index.count("https://lynk.id/albijulian") != 1:
        raise SystemExit("Tautan panduan harus tepat satu kali, di beranda")
    for path, html in html_per_path.items():
        if path != "index.html" and "lynk.id" in html:
            raise SystemExit("Panduan tidak boleh muncul di " + path)
        if path not in ("ulasan.html", "tentang.html", "banding/index.html") and "s.shopee.co.id" not in html:
            if not (DRAFT and "Link menyusul" in html):
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

    # kepercayaan: catatan affiliate di footer semua halaman, catatan dekat tombol beli,
    # dan Tentang Kami tertaut dari header dan footer
    for path, html in html_per_path.items():
        if CATATAN_AFFILIATE not in html:
            raise SystemExit("Catatan affiliate hilang di " + path)
        if "tentang.html" not in html:
            raise SystemExit("Tautan Tentang Kami hilang di " + path)
        if path.startswith("banding/") and CATATAN_AMAN not in html:
            raise SystemExit("Catatan Shopee resmi hilang di " + path)
        for m in re.finditer(r'<a [^>]*href="https://s\.shopee\.co\.id/[^"]*"[^>]*>', html):
            tag = m.group(0)
            if 'rel="sponsored noopener' not in tag or 'target="_blank"' not in tag:
                raise SystemExit(f"Tombol beli tanpa rel sponsored/noopener di {path}")
    for iid, urls in (sumber or {}).items():
        for pair in pasangan:
            if iid in id_pair(pair) and not all(u in html_per_path[f"banding/{pair['id']}.html"] for u in urls):
                raise SystemExit(f"Sumber kandungan {iid} tidak tampil di {pair['id']}")
    tentang = html_per_path["tentang.html"]
    if "ulasan.html" not in tentang or 'id="affiliate"' not in tentang:
        raise SystemExit("Tentang Kami belum lengkap")

    # setiap tombol beli di situs memakai link yang ada di data
    aff_sah = {p["aff"] for p in produk.values() if p["aff"]}
    aff_sah |= {produk_pair(produk, pair, iid)["aff"] for pair in pasangan for iid in id_pair(pair)} - {None}
    for path, html in html_per_path.items():
        for m in re.finditer(r'https://s\.shopee\.co\.id/[A-Za-z0-9]+', html):
            if m.group(0) not in aff_sah:
                raise SystemExit(f"Link Shopee tidak dikenal di {path}: {m.group(0)}")


def laporan(produk, pasangan):
    terpakai = {iid for p in pasangan for iid in id_pair(p)}
    print("\nPerbandingan:")
    for b, blabel in BANDING_JENIS:
        sub = [p for p in pasangan if jenis_banding(p) == b]
        print(f"  {blabel}: {len(sub)}")
        for jenis, label in JENIS:
            print(f"    {label}: {sum(1 for p in sub if p['jenis'] == jenis)}")
    kosong = sorted({iid for p in pasangan for iid in id_pair(p) if not produk_pair(produk, p, iid)["aff"]})
    if kosong:
        print("Belum punya link pendek (tombol 'Link menyusul'):")
        for iid in kosong:
            print(f"  - {iid} | {produk[iid]['url']}")
    print("Dilewati:")
    for iid, p in produk.items():
        if iid in terpakai:
            continue
        alasan = ALASAN_LEWAT.get(iid)
        if not alasan:
            alasan = ALASAN_LEWAT["facial"] if p["keyword"].startswith("facial") else "Tidak dipasangkan."
        print(f"  - {iid} | {p['judul'][:90]}")
        print(f"    {alasan}")


def tulis_sitemap(paths):
    """sitemap.xml dan robots.txt di root. paths: halaman publik (relatif ke root)."""
    import datetime
    hari = datetime.date.today().isoformat()
    urut = sorted(paths, key=lambda p: (p != "index.html", p.startswith("banding/"), p))
    baris = [
        f"  <url><loc>{esc(url_absolut(p))}</loc><lastmod>{hari}</lastmod></url>"
        for p in urut
    ]
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(baris) + "\n</urlset>\n"
    )
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(xml)
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}sitemap.xml\n")
    return len(baris)


def tulis_redirect():
    html = """<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url=index.html">
  <title>PilihYuk</title>
  <link rel="canonical" href="index.html">
  <script>location.replace("index.html");</script>
</head>
<body>
  <p><a href="index.html">Ke beranda PilihYuk</a></p>
</body>
</html>
"""
    for nama in ("review.html", "perbandingan.html"):
        with open(os.path.join(ROOT, nama), "w", encoding="utf-8") as f:
            f.write(html)
    os.makedirs(BANDING, exist_ok=True)
    with open(os.path.join(BANDING, "index.html"), "w", encoding="utf-8") as f:
        f.write(html.replace("index.html", "../index.html"))


def muat_redirect_banding(pasangan):
    """id lama -> id baru. Halaman lama jadi redirect ke perbandingan pengganti."""
    path = os.path.join(ROOT, "tools", "redirect_banding.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        peta = json.load(f)
    ada = {pair["id"] for pair in pasangan}
    for lama, baru in peta.items():
        if lama in ada:
            raise SystemExit(f"Redirect {lama}: id ini masih dipakai pasangan aktif")
        if baru not in ada:
            raise SystemExit(f"Redirect {lama} menuju {baru}, tapi {baru} tidak ada")
    return peta


def tulis_redirect_banding(peta):
    """Satu HTML per id lama: noindex, meta refresh, canonical, dan location.replace.
    Tidak masuk sitemap.xml."""
    for lama, baru in sorted(peta.items()):
        tujuan = f"{baru}.html"
        kanonik = url_absolut(f"banding/{baru}.html")
        html = f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex, follow">
  <meta http-equiv="refresh" content="0; url={esc(tujuan)}">
  <title>Perbandingan ini sudah dipindah | PilihYuk</title>
  <link rel="canonical" href="{esc(kanonik)}">
  <script>location.replace("{tujuan}" + location.search + location.hash);</script>
</head>
<body>
  <p>Perbandingan ini sudah diperbarui. <a href="{esc(tujuan)}">Buka perbandingan yang baru</a>.</p>
</body>
</html>
"""
        with open(os.path.join(BANDING, f"{lama}.html"), "w", encoding="utf-8") as f:
            f.write(html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gambar", action="store_true", help="unduh ulang gambar")
    ap.add_argument(
        "--draft", action="store_true",
        help="pratinjau: produk tanpa link pendek boleh tampil, tombolnya 'Link menyusul' (nonaktif)",
    )
    args = ap.parse_args()
    global DRAFT
    DRAFT = args.draft
    os.chdir(ROOT)
    with open(os.path.join(ROOT, "tools", "pasangan.json"), encoding="utf-8") as f:
        data = json.load(f)
    produk = muat_produk()
    merek = muat_merek()
    posted = muat_posted()
    sumber = muat_sumber_kandungan()
    pasangan = data["pasangan"]
    for pair in pasangan:
        for iid in id_pair(pair):
            if iid not in produk:
                raise SystemExit(f"{iid} tidak ada di data, atau tidak punya link affiliate")
    pastikan_gambar(produk, pasangan, args.gambar)
    os.makedirs(BANDING, exist_ok=True)
    # halaman lama tidak dihapus lagi: pasangan yang dirombak diganti halaman redirect
    # (lihat tools/redirect_banding.json), supaya link lama tetap jalan.
    redirect = muat_redirect_banding(pasangan)
    sah = {pair["id"] + ".html" for pair in pasangan} | {"index.html"} | {i + ".html" for i in redirect}
    for nama in os.listdir(BANDING):
        if nama not in sah and nama.endswith(".html"):
            print(f"PERINGATAN: banding/{nama} tidak dikenal (bukan pasangan dan bukan redirect). Dibiarkan.")

    berkas = {
        "index.html": render_index(data, produk, pasangan),
        "ulasan.html": render_ulasan(data, pasangan),
        "tentang.html": render_tentang(data, pasangan),
    }
    for pair in pasangan:
        berkas[f"banding/{pair['id']}.html"] = render_pair(data, produk, pair, sumber)
    berkas["bandingkan.html"], daftar_banding = render_bandingkan(data, produk, pasangan)
    for path, html in berkas.items():
        tujuan = os.path.join(ROOT, path)
        os.makedirs(os.path.dirname(tujuan), exist_ok=True)
        with open(tujuan, "w", encoding="utf-8") as f:
            f.write(html)
    tulis_manifest()
    tulis_redirect()
    tulis_redirect_banding(redirect)
    # redirect tidak ikut pemeriksaan kata (hampir kosong) tapi tautannya diperiksa lewat berkas
    periksa(berkas, produk, pasangan, posted, merek, sumber)
    periksa_bandingkan(berkas["bandingkan.html"], daftar_banding, pasangan)
    for path, html in berkas.items():
        if f'content="{GOOGLE_SITE_VERIFICATION}"' not in html:
            raise SystemExit("Meta verifikasi Google hilang di " + path)
        if 'src="https://gc.zgo.at/count.js"' not in html:
            raise SystemExit("Skrip GoatCounter hilang di " + path)
    for path, html in berkas.items():
        for wajib in ('img/favicon-48.png"', 'img/favicon-192.png"', 'site.webmanifest"', 'name="twitter:card"', 'property="og:image"'):
            if wajib not in html:
                raise SystemExit(f"{wajib} hilang di {path}")
    if '"@type":"Organization"' not in berkas["index.html"]:
        raise SystemExit("JSON-LD Organization hilang di index.html")
    n_sitemap = tulis_sitemap(berkas.keys())
    # CNAME (custom domain pilihyuk.id) tidak pernah ditulis atau dihapus generator.
    if not os.path.isfile(os.path.join(ROOT, "CNAME")):
        print("PERINGATAN: file CNAME tidak ada. Jangan hapus CNAME, domain pilihyuk.id memakainya.")
    # gambar yang tidak terpakai
    terpakai = {iid + ".jpg" for pair in pasangan for iid in id_pair(pair)}
    if os.path.isdir(IMG):
        for nama in os.listdir(IMG):
            if nama not in terpakai and nama not in ASET_MEREK:
                os.remove(os.path.join(IMG, nama))
    laporan(produk, pasangan)
    print("Bandingin Sendiri (produk yang bisa dipilih):")
    for kunci, label in JENIS:
        print(f"  {label}: {sum(1 for d in daftar_banding if d['jenis'] == kunci)}")
    print(f"  Total: {len(daftar_banding)}" + ("" if REQUEST_AKTIF else " (form request disembunyikan)"))
    print(f"sitemap.xml: {n_sitemap} URL")
    print(f"\nSelesai: {len(pasangan)} perbandingan" + (" (DRAFT: jangan dipublikasikan sebelum link lengkap)" if DRAFT else ""))


if __name__ == "__main__":
    main()
