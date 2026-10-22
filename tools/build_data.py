#!/usr/bin/env python3
"""
Generator data produk untuk website "Bandingin.id".

Membaca file .psv hasil pengumpulan data Shopee lalu membuat data/produk.js.

Pemakaian (dari folder web-review-affiliate):
    python3 tools/build_data.py
Opsi:
    --sumber  FOLDER   folder berisi file .psv (default: /workspace/shopee-data,
                       atau folder sumber-data/ di dalam website kalau ada)
    --tanggal "22 Oktober 2026"   tanggal pengambilan data (tampil di website)

Format tiap baris .psv (dipisah ' | '):
    keyword | judul | harga | harga asli (atau -) | rating | terjual/bln | kota | URL produk | URL gambar

File link affiliate (opsional) affiliate-links.psv di folder sumber:
    nomor | URL produk asli | link affiliate
"""
import argparse, json, math, os, re, sys
from datetime import date

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KATEGORI = [
    ("gadget-hp.psv", "Gadget & HP", "📱"),
    ("fashion-skincare.psv", "Fashion & Skincare", "👗"),
    ("rumah-tangga.psv", "Rumah Tangga", "🏠"),
    ("mainan-hobi.psv", "Mainan & Hobi", "🧸"),
]

# Nama kelompok (jenis produk) yang tampil di website
NAMA_JENIS = {
    "tws earbuds": "TWS Earbuds", "power bank": "Power Bank", "charger hp": "Charger HP",
    "smartwatch": "Smartwatch & Smartband", "speaker bluetooth": "Speaker Bluetooth",
    "sunscreen": "Sunscreen", "facial wash": "Sabun Cuci Muka (Facial Wash)",
    "moisturizer": "Pelembap Wajah (Moisturizer)", "kaos pria": "Kaos Pria",
    "tas wanita": "Tas Wanita", "air fryer": "Air Fryer", "rice cooker": "Rice Cooker",
    "blender": "Blender & Chopper", "rak serbaguna": "Rak Serbaguna",
    "vacuum cleaner": "Vacuum Cleaner", "lego": "LEGO", "rubik": "Kubus Puzzle & Magnetik",
    "mainan edukasi anak": "Mainan Edukasi Anak", "action figure": "Action Figure",
    "puzzle": "Puzzle",
}

# Fitur yang dicari di judul produk (hanya yang tertulis di judul)
POLA_FITUR = [
    r"\d[\d.,]*\s?mAh", r"\b\d+(?:[.,]\d+)?\s?(?:L|Liter)\b", r"\b\d+\s?(?:W|Watt|w)\b",
    r"\b(?:BT|Bluetooth)\s?\d\.\d\b", r"\bIPX\d\b", r"\bGaransi(?: Resmi)?(?: \d+ Tahun)?",
    r"\bSPF\s?\d+(?:\s?PA\+*)?", r"\bPA\+{2,}", r"\b\d+\s?(?:ml|ML|gr)\b", r"\b\d+Pa\b",
    r"\b\d+\s?(?:Pieces|PCS|pcs|Pcs)\b", r"\b\d+ in 1\b", r"\bAMOLED\b", r"\bGPS\b", r"\bNFC\b",
    r"\bECG\b", r"\bFast Charging\b", r"\bQuick Charging\b", r"\bType[ -]C\b", r"\bAnti Lengket\b",
    r"\bCordless\b", r"\bTanpa Kabel\b", r"\bLow (?:Watt|Power)\b", r"\bStainless(?: 304)?\b",
    r"\bMagnetic\b", r"\bKayu\b", r"\bLow pH\b", r"\bNiacinamide\b", r"\bCeramide\b",
    r"\bPanthenol\b", r"\bCotton Combed(?: \d+s)?\b", r"\bPremium Cotton(?: \d+s)?\b",
    r"\bOversize\b", r"\bS-\d?X+L\b", r"\bRGB\b", r"\b\d\s?(?:MIC|Microphon)\b", r"\bWaterproof\b",
    r"\bLayar Sentuh(?: Digital)?\b", r"\b\d+ Mode\b", r"\bDengan Roda\b|\bBeroda\b",
    r"\bAnti Karat\b", r"\b\d+/?\d* Susun\b", r"\b\d+ Tier\b", r"\bDua Kecepatan\b",
    r"\bBluetooth Call\b", r"\bWireless Charging\b", r"\bPortable\b", r"\bLampu\b",
]

# Tanda judul mencakup beberapa varian (pilihan ukuran/tipe/kapasitas)
POLA_VARIAN = (r"\bAll Series\b|\([^)]*,[^)]*\)|\d[\d.,]*\s?mAh\s?/\s?\d|\bSPF\s?\d+\s?/\s?SPF"
               r"|\b\d+/\d+ Susun\b|\d+% & \d+%|\d+ Tier & \d+ Tier|\b\d+w \d+w\b")

def rupiah(n):
    return "Rp" + f"{int(n):,}".replace(",", ".")

def angka(teks):
    teks = teks.strip()
    if teks in ("", "-"):
        return None
    return int(re.sub(r"[^\d]", "", teks))

def terjual(teks):
    """Teks terjual Shopee -> (angka, ada_plus, teks_asli). Contoh:
    '1RB+ Terjual/Bln' -> 1000, '919 Terjual/Bln' -> 919, '10RB+' -> 10000, '2,5RB+' -> 2500."""
    t = re.sub(r"terjual\s*/?\s*(bln|bulan)?", "", teks, flags=re.I).strip()
    m = re.match(r"([\d.,]+)\s*(RB|JT)?\s*(\+)?", t, re.I)
    if not m:
        return 0, False, t
    satuan = (m.group(2) or "").upper()
    angka_t = m.group(1)
    if satuan:
        n = float(angka_t.replace(",", "."))          # '2,5RB' -> 2.5 ribu
    else:
        n = float(re.sub(r"[.,]", "", angka_t))       # '1.234' -> 1234
    kali = {"RB": 1000, "JT": 1000000}.get(satuan, 1)
    return int(round(n * kali)), bool(m.group(3)), t

def rentang_terjual(n):
    """Angka terjual -> label rentang (sama dengan Situs.rentangTerjual di js/common.js).
    < 1000 -> '919'; 1000-9999 -> '1rb+' ... '9rb+' (dibulatkan ke bawah); >= 10000 -> '10rb+'."""
    n = int(n or 0)
    if n < 1000:
        return str(n)
    return f"{min(n // 1000, 10)}rb+"

def nilai_rentang(n):
    """Nilai angka dari rentang yang tampil: 2500 -> 2000, 15000 -> 10000, 919 -> 919."""
    n = int(n or 0)
    return n if n < 1000 else min(n // 1000, 10) * 1000

def teks_terjual(p):
    return rentang_terjual(p["terjual"])

def slug(s, maks=6):
    kata = re.sub(r"[^a-z0-9]+", " ", s.lower()).split()
    return "-".join(kata[:maks])

def nama_pendek(judul, maks=6):
    kata = judul.split()
    return " ".join(kata[:maks]) + ("…" if len(kata) > maks else "")

def fitur_judul(judul):
    hasil, lihat = [], set()
    for pola in POLA_FITUR:
        for m in re.finditer(pola, judul, re.I):
            f = m.group(0).strip()
            k = f.lower().replace(" ", "")
            if k not in lihat:
                lihat.add(k); hasil.append(f)
    return hasil[:6]

def normal_url(u):
    return u.strip().split("?")[0].rstrip("/")

def baca_affiliate(path):
    peta = {}
    if not os.path.exists(path):
        return peta
    with open(path, encoding="utf-8") as f:
        for no, baris in enumerate(f, 1):
            baris = baris.strip()
            if not baris or baris.startswith("#"):
                continue
            bag = [x.strip() for x in baris.split("|")]
            if len(bag) < 3:
                print(f"  ! affiliate-links.psv baris {no} dilewati (kolom kurang dari 3)")
                continue
            asli, aff = bag[1], bag[2]
            if not aff.startswith("http"):
                print(f"  ! affiliate-links.psv baris {no} dilewati (link affiliate tidak diawali http)")
                continue
            peta[normal_url(asli)] = aff
    return peta

def baca_produk(sumber):
    produk = []
    for file, kategori, _ in KATEGORI:
        path = os.path.join(sumber, file)
        if not os.path.exists(path):
            print(f"  ! File tidak ditemukan: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            for no, baris in enumerate(f, 1):
                if not baris.strip():
                    continue
                bag = [x.strip() for x in baris.rstrip("\n").split(" | ")]
                if len(bag) != 9:
                    print(f"  ! {file} baris {no} dilewati: ada {len(bag)} kolom, seharusnya 9")
                    continue
                kw, judul, harga, asli, rating, laku, kota, url, img = bag
                n, plus, ttk = terjual(laku)
                h, ha = angka(harga), angka(asli)
                if ha is not None and ha <= h:
                    ha = None
                m = re.search(r"/product/(\d+)/(\d+)", url)
                produk.append({
                    "id": slug(judul) + "-" + (m.group(2) if m else str(len(produk))),
                    "kategori": kategori,
                    "jenis": slug(kw, 5),
                    "jenisNama": NAMA_JENIS.get(kw.lower(), kw.title()),
                    "nama": judul,
                    "gambar": img,
                    "harga": h,
                    "hargaAsli": ha,
                    "diskon": round((ha - h) / ha * 100) if ha else 0,
                    "rating": float(rating),
                    "terjual": n,
                    "terjualPlus": plus,
                    "kota": "" if kota in ("-", "") else kota,
                    "urlProduk": url,
                    "_toko": m.group(1) if m else "",
                })
    return produk

def beri_label(grup):
    """Label verdict per kelompok. Seri = semua yang seri dapat label, kecuali semua 4 seri."""
    for p in grup:
        p["label"] = []
    catatan = []
    def juara(kunci, nama, terbalik=False, maks_seri=None):
        nilai = [kunci(p) for p in grup]
        terbaik = min(nilai) if terbalik else max(nilai)
        pemenang = [p for p in grup if kunci(p) == terbaik]
        if len(pemenang) == len(grup):
            return False
        if maks_seri and len(pemenang) > maks_seri:
            return len(pemenang)
        for p in pemenang:
            p["label"].append(nama)
        return True
    juara(lambda p: p["harga"], "Paling murah", terbalik=True)
    r = juara(lambda p: p["rating"], "Rating tertinggi", maks_seri=2)
    rmax = max(p["rating"] for p in grup)
    if r is False:
        catatan.append(f"Semua produk di kelompok ini punya rating sama ({rmax}), jadi tidak ada label 'Rating tertinggi'.")
    elif r is not True:
        catatan.append(f"{r} dari {len(grup)} produk sama-sama punya rating {rmax}, jadi tidak ada label 'Rating tertinggi'.")
    # Dibandingkan per rentang yang tampil di website (mis. 2.000 dan 2.500 sama-sama '2rb+')
    t = juara(lambda p: nilai_rentang(p["terjual"]), "Paling laris", maks_seri=2)
    top = max(grup, key=lambda p: p["terjual"])
    if t is False:
        catatan.append(f"Semua produk sama-sama {teks_terjual(grup[0])} terjual/bulan "
                       "(Shopee hanya menampilkan angka bulat seperti '1rb+'), jadi tidak ada label 'Paling laris'.")
    elif t is not True:
        catatan.append(f"{t} dari {len(grup)} produk sama-sama {teks_terjual(top)} terjual/bulan, "
                       "jadi tidak ada label 'Paling laris'.")
    elif any(p["terjualPlus"] for p in grup):
        catatan.append("Angka seperti '1rb+' berarti 1.000 atau lebih (Shopee tidak menampilkan angka pastinya).")
    # Paling seimbang: gabungan rating, penjualan, dan harga (dalam kelompok)
    def skala(v, a, b):
        return 0.5 if a == b else (v - a) / (b - a)
    rs = [p["rating"] for p in grup]; ss = [math.log10(p["terjual"] + 1) for p in grup]
    hs = [math.log10(p["harga"]) for p in grup]
    for p in grup:
        p["_skor"] = (0.4 * skala(p["rating"], min(rs), max(rs))
                      + 0.3 * skala(math.log10(p["terjual"] + 1), min(ss), max(ss))
                      + 0.3 * (1 - skala(math.log10(p["harga"]), min(hs), max(hs))))
    max(grup, key=lambda p: (p["_skor"], p["rating"], -p["harga"]))["label"].append("Paling seimbang")
    return catatan

def tulis_review(p, grup, tanggal):
    lain = [x for x in grup if x is not p]
    termurah = min(grup, key=lambda x: x["harga"])
    rating_max = max(x["rating"] for x in grup)
    rating_min = min(x["rating"] for x in grup)
    jual_min = min(x["terjual"] for x in grup)
    jual_max = max(x["terjual"] for x in grup)
    jenis = p["jenisNama"]
    jt = teks_terjual(p)

    plus = ["Dijual oleh toko resmi di Shopee (Shopee Mall)."]
    if p["rating"] >= 4.8:
        plus.append(f"Rating tinggi: {p['rating']} dari 5 menurut pembeli di Shopee.")
    elif p["rating"] >= 4.5:
        plus.append(f"Rating cukup baik: {p['rating']} dari 5 menurut pembeli di Shopee.")
    if p["terjual"] >= 1000:
        plus.append(f"Laris: {jt} terjual per bulan.")
    elif p["terjual"] >= 500:
        plus.append(f"Cukup laris: sekitar {jt} terjual per bulan.")
    if p["diskon"] >= 10:
        plus.append(f"Sedang diskon {p['diskon']}% dari harga coret {rupiah(p['hargaAsli'])}.")
    if "Paling murah" in p["label"]:
        plus.append(f"Harga paling murah di antara {len(grup)} pilihan {jenis} yang dibandingkan di Bandingin.id.")
    fit = fitur_judul(p["nama"])
    if fit:
        plus.append("Fitur yang tertulis di judul produk: " + ", ".join(fit) + ".")

    minus = []
    if p["diskon"] >= 50:
        minus.append(f"Diskonnya sangat besar ({p['diskon']}%). Harga coret belum tentu harga normal "
                     "di pasaran, jadi lihat harga akhirnya saja.")
    if p["rating"] < rating_max and p["rating"] == rating_min:
        minus.append(f"Ratingnya ({p['rating']}) paling rendah di kelompok ini (tertinggi {rating_max}).")
    if p["harga"] > termurah["harga"] * 1.1:
        minus.append(f"Ada pilihan lebih murah di kelompok yang sama: {nama_pendek(termurah['nama'])} "
                     f"({rupiah(termurah['harga'])}).")
    if p["terjual"] < 1000 and p["terjual"] == jual_min and jual_min < jual_max:
        minus.append(f"Penjualannya ({jt} per bulan) paling sedikit di kelompok ini.")
    kembar = [x for x in lain if x["_toko"] == p["_toko"] and x["harga"] == p["harga"]]
    if kembar:
        minus.append(f"Toko yang sama juga menjual {nama_pendek(kembar[0]['nama'])} dengan harga sama persis. "
                     "Cek bedanya (model/varian) supaya tidak salah pilih.")
    if not p["kota"]:
        minus.append("Lokasi pengiriman tidak tercantum di data. Cek di halaman produk.")
    if re.search(POLA_VARIAN, p["nama"], re.I):
        minus.append("Judulnya mencakup beberapa varian/ukuran. Harga yang tampil bisa jadi untuk varian "
                     "tertentu saja, jadi cek lagi varian yang kamu pilih.")
    if len(minus) < 1:
        minus.append(f"Harga yang tercantum adalah harga per {tanggal} dan bisa berubah saat promo selesai.")
    minus.append("Produk ini tidak diuji langsung oleh Bandingin.id. Baca deskripsi, pilihan varian, "
                 "dan ulasan pembeli di Shopee sebelum membeli.")

    kal = []
    L = p["label"]
    if L:
        teks = {"Paling murah": "paling murah", "Rating tertinggi": "rating tertinggi",
                "Paling laris": "paling laris", "Paling seimbang": "paling seimbang (harga, rating, dan penjualan)"}
        kal.append(f"Dari {len(grup)} pilihan {jenis} yang dibandingkan di Bandingin.id, produk ini "
                   + " sekaligus ".join(teks[x] for x in L) + ".")
    else:
        kal.append(f"Produk ini tidak unggul di satu hal tertentu dibanding {len(lain)} pilihan {jenis} lainnya, "
                   "tapi tetap bisa jadi pilihan kalau kamu suka merek atau modelnya.")
    kal.append(f"Harganya {rupiah(p['harga'])}" + (f" (diskon {p['diskon']}%)" if p["diskon"] >= 5 else "")
               + f" dengan rating {p['rating']} dan {jt} terjual per bulan.")
    kal.append("Cek harga terbaru dan pilih varian yang sesuai kebutuhanmu di Shopee.")

    if L:
        ring = L[0] + f" di kelompok {jenis}. Rating {p['rating']}, {jt} terjual/bln."
    else:
        ring = f"Rating {p['rating']} dari 5, {jt} terjual per bulan."
    if p["diskon"] >= 10:
        ring += f" Diskon {p['diskon']}%."
    return ring, plus, minus, " ".join(kal)

def main():
    ap = argparse.ArgumentParser()
    bawaan = os.path.join(SITE, "sumber-data")
    if not os.path.isdir(bawaan):
        bawaan = "/workspace/shopee-data"
    ap.add_argument("--sumber", default=bawaan)
    ap.add_argument("--tanggal", default="22 Oktober 2026")
    a = ap.parse_args()

    print(f"Membaca data dari: {a.sumber}")
    produk = baca_produk(a.sumber)
    aff = baca_affiliate(os.path.join(a.sumber, "affiliate-links.psv"))
    print(f"  {len(produk)} produk dibaca, {len(aff)} link affiliate ditemukan")

    urutan, grup = [], {}
    for p in produk:
        if p["jenis"] not in grup:
            grup[p["jenis"]] = []; urutan.append(p["jenis"])
        grup[p["jenis"]].append(p)

    daftar_grup, pakai_aff = [], 0
    for j in urutan:
        g = grup[j]
        catatan = beri_label(g)
        for p in g:
            p["ringkasan"], p["kelebihan"], p["kekurangan"], p["kesimpulan"] = tulis_review(p, g, a.tanggal)
        daftar_grup.append({"id": j, "nama": g[0]["jenisNama"], "kategori": g[0]["kategori"],
                            "produk": [p["id"] for p in g], "catatan": catatan})

    keluar = []
    for p in produk:
        link = aff.get(normal_url(p["urlProduk"]))
        if link:
            pakai_aff += 1
        keluar.append({
            "id": p["id"], "contoh": False, "nama": p["nama"], "kategori": p["kategori"],
            "jenis": p["jenis"], "jenisNama": p["jenisNama"], "gambar": p["gambar"],
            "harga": p["harga"], "hargaAsli": p["hargaAsli"], "diskon": p["diskon"],
            "rating": p["rating"], "terjual": p["terjual"], "terjualPlus": p["terjualPlus"],
            "terjualLabel": rentang_terjual(p["terjual"]),
            "kota": p["kota"], "label": p["label"], "ringkasan": p["ringkasan"],
            "kelebihan": p["kelebihan"], "kekurangan": p["kekurangan"], "kesimpulan": p["kesimpulan"],
            "urlProduk": p["urlProduk"], "linkShopee": link or p["urlProduk"], "linkAffiliate": bool(link),
            "tokopedia": "",
        })

    ids = [p["id"] for p in keluar]
    if len(ids) != len(set(ids)):
        sys.exit("ERROR: ada id produk yang sama. Cek data.")
    tidak_dipakai = set(aff) - {normal_url(p["urlProduk"]) for p in produk}

    kat = [{"nama": n, "ikon": i} for _, n, i in KATEGORI]
    isi = (
        "/* =====================================================================\n"
        "   FILE INI DIBUAT OTOMATIS oleh tools/build_data.py — JANGAN DIEDIT MANUAL.\n"
        "   Perubahan manual akan hilang saat generator dijalankan lagi.\n"
        "   Untuk mengubah data: edit file .psv / affiliate-links.psv, lalu jalankan:\n"
        "       python3 tools/build_data.py\n"
        f"   Dibuat: {date.today().isoformat()} · {len(keluar)} produk · {pakai_aff} link affiliate\n"
        "   ===================================================================== */\n\n"
        f"window.TANGGAL_DATA = {json.dumps(a.tanggal)};\n\n"
        f"window.KATEGORI = {json.dumps(kat, ensure_ascii=False, indent=2)};\n\n"
        f"window.GRUP = {json.dumps(daftar_grup, ensure_ascii=False, indent=2)};\n\n"
        f"window.PRODUK = {json.dumps(keluar, ensure_ascii=False, indent=2)};\n"
    )
    out = os.path.join(SITE, "data", "produk.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(isi)
    print(f"Selesai: {out}")
    print(f"  {len(keluar)} produk, {len(daftar_grup)} kelompok perbandingan")
    print(f"  {pakai_aff} produk memakai link affiliate, {len(keluar) - pakai_aff} masih memakai link biasa")
    if tidak_dipakai:
        print(f"  ! {len(tidak_dipakai)} link di affiliate-links.psv tidak cocok dengan produk mana pun:")
        for u in sorted(tidak_dipakai):
            print("    -", u)

if __name__ == "__main__":
    main()
