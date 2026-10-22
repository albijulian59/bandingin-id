#!/usr/bin/env python3
"""
Generator data produk untuk website "Bandingin.id" (perawatan diri & fashion: Perempuan, Pria, Balita).

Membaca file .psv hasil pengumpulan data Shopee lalu membuat data/produk.js.

Pemakaian (dari folder website):
    python3 tools/build_data.py            # boleh ada file yang belum lengkap (hanya peringatan)
    python3 tools/build_data.py --final    # untuk deploy: gagal kalau ada file hilang atau link affiliate kurang
Opsi:
    --sumber  FOLDER   folder berisi file .psv (default: /workspace/shopee-data-v2,
                       atau folder sumber-data/ di dalam website kalau ada)
    --tanggal "22 Oktober 2026"   tanggal pengambilan data (tampil di website)

File di folder sumber: perempuan.psv, pria.psv, balita.psv (+ affiliate-links.psv).
Format tiap baris produk (10 kolom, dipisah ' | '):
    keyword | judul | harga | harga asli (atau -) | rating | total terjual | terjual/bln | kota | URL produk | URL gambar
    contoh total terjual: '10RB+ Terjual', terjual/bln: '1RB+ Terjual/Bln'

File link affiliate affiliate-links.psv:
    nomor | URL produk asli | link affiliate
"""
import argparse, json, math, os, re, sys
from datetime import date

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMBER_BAWAAN = "/workspace/shopee-data-v2"

# (file, nama kategori, ikon)
KATEGORI = [
    ("perempuan.psv", "Perempuan", "👩"),
    ("pria.psv", "Pria", "👨"),
    ("balita.psv", "Balita", "👶"),
]

# keyword (kolom 1) -> (nama kelompok, nama pendek untuk sub-filter, kategori, tipe)
# tipe dipakai untuk memilih teks review yang sesuai: sabun, sampo, facial, pelembab, serum, sunscreen, baju, tas
# URUTAN di sini = urutan kelompok di website (per kategori), apa pun urutan baris di file .psv.
JENIS = {
    "sabun mandi wanita": ("Sabun Mandi Wanita", "Sabun Mandi", "Perempuan", "sabun"),
    "shampoo wanita": ("Sampo Wanita", "Sampo", "Perempuan", "sampo"),
    "facial wash wanita": ("Facial Wash Wanita", "Facial Wash", "Perempuan", "facial"),
    "pelembab wajah wanita": ("Pelembab Wajah Wanita", "Pelembab", "Perempuan", "pelembab"),
    "serum wajah wanita": ("Serum Wajah Wanita", "Serum", "Perempuan", "serum"),
    "sunscreen wanita": ("Sunscreen Wanita", "Sunscreen", "Perempuan", "sunscreen"),
    "baju wanita": ("Baju Wanita", "Baju", "Perempuan", "baju"),
    "tas wanita": ("Tas Wanita", "Tas", "Perempuan", "tas"),
    "sabun mandi pria": ("Sabun Mandi Pria", "Sabun Mandi", "Pria", "sabun"),
    "shampoo pria": ("Sampo Pria", "Sampo", "Pria", "sampo"),
    "facial wash pria": ("Facial Wash Pria", "Facial Wash", "Pria", "facial"),
    "pelembab wajah pria": ("Pelembab Wajah Pria", "Pelembab", "Pria", "pelembab"),
    "serum wajah pria": ("Serum Wajah Pria", "Serum", "Pria", "serum"),
    "sunscreen pria": ("Sunscreen Pria", "Sunscreen", "Pria", "sunscreen"),
    "kaos pria": ("Kaos Pria", "Kaos", "Pria", "baju"),
    "sabun bayi": ("Sabun Bayi", "Sabun Bayi", "Balita", "sabun"),
    "shampoo bayi": ("Sampo Bayi", "Sampo Bayi", "Balita", "sampo"),
}

# Hal yang tertulis di judul produk (dikutip apa adanya, tidak dinilai kebenarannya)
POLA_FITUR = [
    r"\b\d+(?:[.,]\d+)?\s?(?:ml|mL|ML|gr|gram|g|G|L)\b", r"\b\d+\s?[xX]\s?\d+\s?(?:ml|mL|gr|g)?\b", r"\bIsi \d+\b",
    r"\bPouch\b", r"\bRefill\b", r"\bBotol\b", r"\bBatang\b|\bBar Soap\b", r"\bCair\b",
    r"\bLow pH\b", r"\bpH[ -]?Balanced?\b", r"\bHypoallergenic\b", r"\bTear[- ]Free\b|\bTidak Pedih\b",
    r"\bNiacinamide\b", r"\bCeramide\b", r"\bPanthenol\b", r"\bCollagen\b", r"\bVitamin [A-Z]\b",
    r"\bSalicylic(?: Acid)?\b", r"\bCharcoal\b", r"\bMenthol\b|\bCool(?:ing)?\b", r"\bAloe Vera\b",
    r"\bOat(?:meal)?\b", r"\bChamomile\b", r"\bMinyak Telon\b|\bTelon\b", r"\bZaitun\b|\bOlive\b",
    r"\bAnti Ketombe\b|\bAnti[- ]Dandruff\b", r"\bAnti (?:Rambut )?Rontok\b|\bAnti[- ]Hair ?fall\b",
    r"\bWangi Tahan Lama\b", r"\bHijab\b",
    r"\bSPF\s?\d+\+?(?:\s?PA\s?\+{1,4})?", r"\bPA\s?\+{1,4}", r"\bBroad Spectrum\b", r"\bTone[- ]?Up\b", r"\bMatte\b",
    r"\bHyaluronic(?: Acid)?\b", r"\bRetinol\b", r"\bCentella\b|\bCica\b", r"\bAlpha Arbutin\b|\bArbutin\b",
    r"\bNon[- ]?Comedogenic\b", r"\bOil[- ]?Free\b", r"\bGel\b", r"\bMencerahkan\b|\bBrightening\b",
    r"\bKatun(?: Rayon)?\b|\bCotton(?: Combed)?(?: \d+s)?\b|\bRayon\b|\bLinen(?: Rami)?\b",
    r"\bLengan (?:Panjang|Pendek)\b|\b(?:Long|Short) Sleeve\b", r"\bOversize\b", r"\bSlim Fit\b|\bRegular Fit\b",
    r"\bCrew ?Neck\b|\bO-?Neck\b|\bV-?Neck\b|\bOneck\b", r"\b(?:S|M|L)\s?-\s?\d?X{1,3}L\b|\bAll ?Size\b",
    r"\bSelempang\b|\bSling ?Bag\b", r"\bTote ?Bag\b|\bTotebag\b", r"\bShoulder(?: Bag)?\b", r"\bSatchel\b",
    r"\bTas Tangan\b", r"\bKapasitas Besar\b", r"\bTali Panjang\b", r"\bAnti Air\b|\bWaterproof\b",
]

# Judul mencakup beberapa varian (harga bisa beda per varian)
POLA_VARIAN = (r"\bAll Series\b|\bSemua Varian\b|\bAll Variant|\bSeries\b|\([^)]*,[^)]*\)|\bVarian\b"
               r"|\b\d+\s?(?:ml|gr|g)\s?/\s?\d+|\bPilih\b")

# Catatan umum per tipe produk (tanpa klaim medis)
# Jumlah produk yang diharapkan per kelompok (dicek dengan --final)
JUMLAH_PER_JENIS = 5

CATATAN_TIPE = {
    "sabun": "Kecocokan sabun berbeda untuk tiap orang. Kalau kulit mudah iritasi, coba di sedikit area kulit dulu.",
    "sampo": "Kecocokan sampo berbeda untuk tiap jenis rambut dan kulit kepala. Coba dulu dan lihat hasilnya setelah beberapa kali pemakaian.",
    "facial": "Kecocokan facial wash berbeda untuk tiap jenis kulit. Cek jenis kulit yang disebut di deskripsi dan coba di sedikit area dulu.",
    "pelembab": ("Reaksi kulit terhadap pelembab berbeda untuk tiap orang. Lakukan uji pada sedikit area kulit dulu. "
                 "Klaim seperti 'mencerahkan' atau 'melembapkan' adalah klaim penjual; Bandingin.id tidak menilai hasilnya."),
    "serum": ("Reaksi kulit terhadap serum berbeda untuk tiap orang, apalagi untuk kulit sensitif. Lakukan uji pada sedikit "
              "area kulit dulu dan ikuti petunjuk pemakaian. Klaim seperti 'mencerahkan' adalah klaim penjual; Bandingin.id tidak menilai hasilnya."),
    "sunscreen": ("Nilai SPF/PA hanya disebut sesuai yang tertulis di judul atau kemasan; Bandingin.id tidak menguji tingkat "
                  "perlindungannya. Ikuti petunjuk pemakaian di kemasan, termasuk anjuran pemakaian ulang."),
    "baju": "Ukuran dan potongan baju bisa berbeda antar merek. Cek tabel ukuran dan foto dari pembeli di halaman produk.",
    "tas": "Cek ukuran (dimensi) tas, bahan, dan foto asli dari pembeli di halaman produk supaya sesuai harapan.",
}
CATATAN_BALITA = ("Untuk produk bayi dan balita, perhatikan usia yang dianjurkan di kemasan dan lakukan uji pada "
                  "sedikit area kulit dulu. Bandingin.id tidak menilai keamanan produk; ikuti petunjuk pemakaian di kemasan.")

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


def fitur_judul(judul):
    hasil, lihat = [], set()
    for pola in POLA_FITUR:
        for m in re.finditer(pola, judul, re.I):
            f = m.group(0).strip()
            k = f.lower().replace(" ", "")
            if k not in lihat and not any(k in x for x in lihat):
                lihat.add(k); hasil.append(f)
    return hasil[:6]

def ukuran_total(judul, tipe):
    """Isi total dari judul untuk sabun/sampo/facial wash: '3x100gr' -> (300, 'g'), '400ml' -> (400, 'ml').
    None kalau tidak jelas (tidak ada ukuran, beberapa ukuran berbeda, atau judul berisi banyak varian)."""
    if tipe not in ("sabun", "sampo", "facial", "pelembab", "serum", "sunscreen") or re.search(POLA_VARIAN, judul, re.I):
        return None
    t = judul.replace(",", ".")
    m = re.search(r"\b(\d+)\s?[xX]\s?(\d+(?:\.\d+)?)\s?(ml|gr|gram|g)\b", t, re.I)
    if m:
        jumlah, isi, sat = int(m.group(1)), float(m.group(2)), m.group(3).lower()
    else:
        semua = re.findall(r"\b(\d+(?:\.\d+)?)\s?(ml|gr|gram|g|l|liter)\b", t, re.I)
        if len({(a, b.lower()) for a, b in semua}) != 1:
            return None
        isi, sat = float(semua[0][0]), semua[0][1].lower()
        if sat in ("l", "liter"):
            isi, sat = isi * 1000, "ml"
        k = re.search(r"\b(?:Isi|isi)\s?(\d+)\b|\b[xX]\s?(\d+)\b|\b(\d+)\s?[xX]\b(?!\s?\d)", t)
        jumlah = int(next(g for g in k.groups() if g)) if k else 1
    sat = "ml" if sat == "ml" else "g"
    total = isi * jumlah
    return (total, sat) if 5 <= total <= 5000 else None

def baca_produk(sumber):
    produk, hilang = [], []
    for file, kategori, _ in KATEGORI:
        path = os.path.join(sumber, file)
        if not os.path.exists(path):
            print(f"  ! File belum ada (dilewati): {path}")
            hilang.append(file)
            continue
        with open(path, encoding="utf-8") as f:
            for no, baris in enumerate(f, 1):
                if not baris.strip() or baris.lstrip().startswith("#"):
                    continue
                bag = [x.strip() for x in baris.rstrip("\n").split(" | ")]
                if len(bag) != 10:
                    print(f"  ! {file} baris {no} dilewati: ada {len(bag)} kolom, seharusnya 10")
                    continue
                kw, judul, harga, asli, rating, total, laku, kota, url, img = bag
                info = JENIS.get(kw.lower())
                if not info:
                    print(f"  ! {file} baris {no}: keyword '{kw}' belum dikenal, dipakai apa adanya")
                    info = (kw.title(), kw.title(), kategori, "")
                elif info[2] != kategori:
                    print(f"  ! {file} baris {no}: keyword '{kw}' biasanya untuk kategori {info[2]}, bukan {kategori}")
                n, plus, _ = terjual(laku)
                tot, _, _ = terjual(total)
                h, ha = angka(harga), angka(asli)
                if h is None:
                    print(f"  ! {file} baris {no} dilewati: harga kosong"); continue
                if ha is not None and ha <= h:
                    ha = None
                m = re.search(r"/product/(\d+)/(\d+)", url)
                produk.append({
                    "id": slug(judul) + "-" + (m.group(2) if m else str(len(produk))),
                    "kategori": kategori,
                    "jenis": slug(kw, 5),
                    "jenisNama": info[0],
                    "jenisPendek": info[1],
                    "tipe": info[3],
                    "nama": judul,
                    "gambar": img,
                    "harga": h,
                    "hargaAsli": ha,
                    "diskon": round((ha - h) / ha * 100) if ha else 0,
                    "rating": float(rating),
                    "terjual": n,
                    "terjualPlus": plus,
                    "terjualTotal": tot,
                    "kota": "" if kota in ("-", "") else kota,
                    "urlProduk": url,
                    "_toko": m.group(1) if m else "",
                    "_isi": ukuran_total(judul, info[3]),
                })
    return produk, hilang

def kunci_laris(p):
    """Laris = total terjual (rentang yang tampil), lalu terjual/bln (rentang yang tampil)."""
    return (nilai_rentang(p["terjualTotal"]), nilai_rentang(p["terjual"]))

def per_isi(p):
    """Harga per 100 ml / 100 g (kalau isi produk jelas dari judul)."""
    if not p["_isi"]:
        return None
    total, sat = p["_isi"]
    return p["harga"] / total * 100, sat

def beri_label(grup):
    """Label verdict per kelompok. Seri = semua yang seri dapat label (maks. 2), kecuali semuanya seri."""
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
    t = juara(kunci_laris, "Paling laris", maks_seri=2)
    top = max(grup, key=kunci_laris)
    jt = f"{rentang_terjual(top['terjualTotal'])} terjual (total) dan {rentang_terjual(top['terjual'])}/bulan"
    if t is False:
        catatan.append(f"Semua produk sama-sama {jt}, jadi tidak ada label 'Paling laris'.")
    elif t is not True:
        catatan.append(f"{t} dari {len(grup)} produk sama-sama {jt}, jadi tidak ada label 'Paling laris'.")
    catatan.append("Angka seperti '10rb+' berarti 10.000 atau lebih. Shopee tidak menampilkan angka pastinya.")
    # Paling seimbang: gabungan rating, penjualan (total + bulanan), dan harga (dalam kelompok)
    def skala(v, a, b):
        return 0.5 if a == b else (v - a) / (b - a)
    laku = lambda p: math.log10(p["terjualTotal"] + 1) + math.log10(p["terjual"] + 1)
    rs = [p["rating"] for p in grup]; ss = [laku(p) for p in grup]; hs = [math.log10(p["harga"]) for p in grup]
    for p in grup:
        p["_skor"] = (0.4 * skala(p["rating"], min(rs), max(rs)) + 0.3 * skala(laku(p), min(ss), max(ss))
                      + 0.3 * (1 - skala(math.log10(p["harga"]), min(hs), max(hs))))
    max(grup, key=lambda p: (p["_skor"], p["rating"], -p["harga"]))["label"].append("Paling seimbang")
    return catatan

def tulis_review(p, grup, tanggal):
    lain = [x for x in grup if x is not p]
    termurah = min(grup, key=lambda x: x["harga"])
    rating_max = max(x["rating"] for x in grup)
    rating_min = min(x["rating"] for x in grup)
    laris_min = min(kunci_laris(x) for x in grup)
    laris_max = max(kunci_laris(x) for x in grup)
    jenis = p["jenisNama"]
    jt = rentang_terjual(p["terjual"])
    jtot = rentang_terjual(p["terjualTotal"])

    plus = ["Dijual oleh toko resmi di Shopee (Shopee Mall)."]
    if p["rating"] >= 4.8:
        plus.append(f"Rating tinggi: {p['rating']} dari 5 menurut pembeli di Shopee.")
    elif p["rating"] >= 4.5:
        plus.append(f"Rating cukup baik: {p['rating']} dari 5 menurut pembeli di Shopee.")
    if p["terjualTotal"] >= 1000:
        plus.append(f"Banyak dibeli: {jtot} terjual (total) dan {jt} terjual per bulan.")
    elif p["terjual"] >= 500:
        plus.append(f"Cukup laris: sekitar {jt} terjual per bulan.")
    if p["diskon"] >= 10:
        plus.append(f"Sedang diskon {p['diskon']}% dari harga coret {rupiah(p['hargaAsli'])}.")
    if "Paling murah" in p["label"]:
        plus.append(f"Harga paling murah di antara {len(grup)} pilihan {jenis} yang dibandingkan di Bandingin.id.")
    hi = per_isi(p)
    banding_isi = [per_isi(x) for x in grup if per_isi(x) and per_isi(x)[1] == (hi[1] if hi else None)]
    if hi and len(banding_isi) >= 2 and hi[0] <= min(b[0] for b in banding_isi):
        plus.append(f"Paling hemat per isi di kelompok ini: sekitar {rupiah(hi[0])} per 100 {hi[1]} "
                    "(dihitung dari ukuran yang tertulis di judul).")
    fit = fitur_judul(p["nama"])
    if fit:
        plus.append("Yang tertulis di judul produk: " + ", ".join(fit) + " (menurut penjual).")

    minus = []
    if p["diskon"] >= 50:
        minus.append(f"Diskonnya sangat besar ({p['diskon']}%). Harga coret belum tentu harga normal "
                     "di pasaran, jadi lihat harga akhirnya saja.")
    if p["rating"] < rating_max and p["rating"] == rating_min:
        minus.append(f"Ratingnya ({p['rating']}) paling rendah di kelompok ini (tertinggi {rating_max}).")
    if p["harga"] > termurah["harga"] * 1.1:
        minus.append(f"Ada pilihan lebih murah di kelompok yang sama: {nama_pendek(termurah['nama'])} "
                     f"({rupiah(termurah['harga'])}).")
    if kunci_laris(p) == laris_min and laris_min < laris_max:
        minus.append(f"Penjualannya ({jtot} total, {jt}/bulan) paling sedikit di kelompok ini.")
    kembar = [x for x in lain if x["_toko"] == p["_toko"] and x["harga"] == p["harga"]]
    if kembar:
        minus.append(f"Toko yang sama juga menjual {nama_pendek(kembar[0]['nama'])} dengan harga sama persis. "
                     "Cek bedanya (model/varian) supaya tidak salah pilih.")
    if not p["kota"]:
        minus.append("Lokasi pengiriman tidak tercantum di data. Cek di halaman produk.")
    if re.search(POLA_VARIAN, p["nama"], re.I):
        minus.append("Judulnya mencakup beberapa varian/ukuran. Harga yang tampil bisa jadi untuk varian "
                     "tertentu saja, jadi cek lagi varian yang kamu pilih.")
    if p["tipe"] in CATATAN_TIPE:
        minus.append(CATATAN_TIPE[p["tipe"]])
    if p["kategori"] == "Balita":
        minus.append(CATATAN_BALITA)
    minus.append("Produk ini tidak diuji langsung oleh Bandingin.id. Ulasan ini disusun dari data yang tampil "
                 "di Shopee; baca deskripsi, komposisi/bahan, dan ulasan pembeli sebelum membeli.")

    kal = []
    L = p["label"]
    if L:
        teks = {"Paling murah": "paling murah", "Rating tertinggi": "rating tertinggi",
                "Paling laris": "paling laris", "Paling seimbang": "paling seimbang (harga, rating, dan penjualan)"}
        kal.append(f"Dari {len(grup)} pilihan {jenis} yang dibandingkan di Bandingin.id, produk ini "
                   + " sekaligus ".join(teks[x] for x in L) + ".")
    else:
        kal.append(f"Produk ini tidak unggul di satu hal tertentu dibanding {len(lain)} pilihan {jenis} lainnya, "
                   "tapi tetap bisa jadi pilihan kalau kamu cocok dengan merek atau modelnya.")
    kal.append(f"Harganya {rupiah(p['harga'])}" + (f" (diskon {p['diskon']}%)" if p["diskon"] >= 5 else "")
               + f" dengan rating {p['rating']}, {jtot} terjual (total), dan {jt} terjual per bulan.")
    if p["kategori"] == "Balita":
        kal.append("Perhatikan usia yang dianjurkan di kemasan sebelum memakai.")
    kal.append("Cek harga terbaru dan pilih varian yang sesuai kebutuhanmu di Shopee.")

    if L:
        ring = L[0] + f" di kelompok {jenis}. Rating {p['rating']}, {jtot} terjual."
    else:
        ring = f"Rating {p['rating']} dari 5, {jtot} terjual ({jt}/bln)."
    if p["diskon"] >= 10:
        ring += f" Diskon {p['diskon']}%."
    return ring, plus, minus, " ".join(kal)

def susun_top10(produk, maks=10):
    """Top 10 terlaris per kategori. Urutan: total terjual (Shopee maks. '10RB+'), lalu terjual/bln,
    lalu rating, lalu harga termurah, lalu id (supaya selalu sama)."""
    hasil = []
    for _, kat, ikon in KATEGORI:
        calon = sorted((p for p in produk if p["kategori"] == kat),
                       key=lambda p: (-p["terjualTotal"], -p["terjual"], -p["rating"], p["harga"], p["id"]))
        if calon:
            hasil.append({"kategori": kat, "ikon": ikon, "produk": [p["id"] for p in calon[:maks]]})
    return hasil

def main():
    ap = argparse.ArgumentParser()
    bawaan = os.path.join(SITE, "sumber-data")
    if not os.path.isdir(bawaan):
        bawaan = SUMBER_BAWAAN
    ap.add_argument("--sumber", default=bawaan)
    ap.add_argument("--tanggal", default="22 Oktober 2026")
    ap.add_argument("--final", action="store_true",
                    help="mode deploy: gagal kalau ada file kategori hilang atau produk tanpa link affiliate")
    a = ap.parse_args()

    print(f"Membaca data dari: {a.sumber}")
    produk, hilang = baca_produk(a.sumber)
    path_aff = os.path.join(a.sumber, "affiliate-links.psv")
    if not os.path.exists(path_aff):
        print(f"  ! File link affiliate belum ada: {path_aff} (sementara memakai link Shopee biasa)")
    aff = baca_affiliate(path_aff)
    print(f"  {len(produk)} produk dibaca, {len(aff)} link affiliate ditemukan")
    if not produk:
        sys.exit("ERROR: tidak ada produk yang terbaca. Cek folder sumber.")

    # Urutkan produk: kategori (urutan KATEGORI), lalu kelompok (urutan JENIS), lalu urutan baris di file
    posisi_kat = {n: i for i, (_, n, _) in enumerate(KATEGORI)}
    posisi_jenis = {slug(k, 5): i for i, k in enumerate(JENIS)}
    produk = [p for _, p in sorted(enumerate(produk), key=lambda x: (
        posisi_kat.get(x[1]["kategori"], 99), posisi_jenis.get(x[1]["jenis"], 999), x[0]))]

    urutan, grup = [], {}
    for p in produk:
        if p["jenis"] not in grup:
            grup[p["jenis"]] = []; urutan.append(p["jenis"])
        grup[p["jenis"]].append(p)

    daftar_grup, pakai_aff = [], 0
    for j in urutan:
        g = grup[j]
        if len(g) < 2:
            print(f"  ! Kelompok '{g[0]['jenisNama']}' hanya berisi {len(g)} produk")
        catatan = beri_label(g)
        for p in g:
            p["ringkasan"], p["kelebihan"], p["kekurangan"], p["kesimpulan"] = tulis_review(p, g, a.tanggal)
        daftar_grup.append({"id": j, "nama": g[0]["jenisNama"], "pendek": g[0]["jenisPendek"],
                            "kategori": g[0]["kategori"], "produk": [p["id"] for p in g], "catatan": catatan})

    keluar, tanpa_aff = [], []
    for p in produk:
        link = aff.get(normal_url(p["urlProduk"]))
        if link:
            pakai_aff += 1
        else:
            tanpa_aff.append(p)
        hi = per_isi(p)
        keluar.append({
            "id": p["id"], "contoh": False, "nama": p["nama"], "kategori": p["kategori"],
            "jenis": p["jenis"], "jenisNama": p["jenisNama"], "jenisPendek": p["jenisPendek"], "gambar": p["gambar"],
            "harga": p["harga"], "hargaAsli": p["hargaAsli"], "diskon": p["diskon"],
            "rating": p["rating"], "terjual": p["terjual"], "terjualPlus": p["terjualPlus"],
            "terjualLabel": rentang_terjual(p["terjual"]),
            "terjualTotal": p["terjualTotal"], "terjualTotalLabel": rentang_terjual(p["terjualTotal"]),
            "hargaPer100": round(hi[0]) if hi else None, "satuanIsi": hi[1] if hi else None,
            "kota": p["kota"], "label": p["label"], "ringkasan": p["ringkasan"],
            "kelebihan": p["kelebihan"], "kekurangan": p["kekurangan"], "kesimpulan": p["kesimpulan"],
            "urlProduk": p["urlProduk"], "linkShopee": link or p["urlProduk"], "linkAffiliate": bool(link),
            "tokopedia": "",
        })

    ids = [p["id"] for p in keluar]
    if len(ids) != len(set(ids)):
        sys.exit("ERROR: ada id produk yang sama. Cek data.")
    urls = [normal_url(p["urlProduk"]) for p in produk]
    if len(urls) != len(set(urls)):
        print("  ! Ada URL produk yang dipakai lebih dari sekali.")
    tidak_dipakai = set(aff) - set(urls)

    kat = [{"nama": n, "ikon": i} for _, n, i in KATEGORI if any(p["kategori"] == n for p in produk)]
    top10 = susun_top10(produk)
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
        f"window.PRODUK = {json.dumps(keluar, ensure_ascii=False, indent=2)};\n\n"
        "// Top 10 terlaris per kategori (id produk, urutan peringkat):\n"
        "// total terjual, lalu terjual/bln, lalu rating, lalu harga termurah\n"
        f"window.TOP10 = {json.dumps(top10, ensure_ascii=False, indent=2)};\n"
    )
    out = os.path.join(SITE, "data", "produk.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write(isi)
    print(f"Selesai: {out}")
    print(f"  {len(keluar)} produk, {len(daftar_grup)} kelompok perbandingan")
    for k in kat:
        gs = [g for g in daftar_grup if g["kategori"] == k["nama"]]
        print(f"    {k['nama']}: {sum(len(g['produk']) for g in gs)} produk (" +
              ", ".join(f"{g['nama']} {len(g['produk'])}" for g in gs) + ")")
    belum = [info[0] for kw, info in JENIS.items() if slug(kw, 5) not in grup]
    if belum:
        print(f"  ! Kelompok yang belum ada datanya ({len(belum)}): " + ", ".join(belum))
    print(f"  {pakai_aff} produk memakai link affiliate, {len(tanpa_aff)} masih memakai link biasa")
    if tanpa_aff and len(tanpa_aff) <= 10:
        for p in tanpa_aff:
            print("    - tanpa affiliate:", p["urlProduk"])
    if tidak_dipakai:
        print(f"  ! {len(tidak_dipakai)} link di affiliate-links.psv tidak cocok dengan produk mana pun:")
        for u in sorted(tidak_dipakai):
            print("    -", u)
    if a.final:
        masalah = []
        if hilang:
            masalah.append("file belum ada: " + ", ".join(hilang))
        kurang = []
        for kw, info in JENIS.items():
            n = len(grup.get(slug(kw, 5), []))
            if n != JUMLAH_PER_JENIS:
                kurang.append(f"{info[0]} {n}/{JUMLAH_PER_JENIS}")
        if kurang:
            masalah.append("jumlah produk per kelompok belum sesuai: " + ", ".join(kurang))
        if tanpa_aff:
            masalah.append(f"{len(tanpa_aff)} produk tanpa link affiliate")
        if masalah:
            sys.exit("BELUM SIAP DEPLOY: " + "; ".join(masalah))
        print("  SIAP DEPLOY: semua file ada dan semua produk memakai link affiliate.")

if __name__ == "__main__":
    main()
