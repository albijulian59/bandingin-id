# Panduan Website "Bandingin.id"

Bandingin.id membandingkan produk dari toko resmi berdasarkan data, bukan review pribadi.
Website ini berisi **80 produk asli dari toko resmi Shopee (Shopee Mall)**, dibagi ke
4 kategori dan 20 jenis produk (masing-masing 4 pilihan). Data diambil **22 Oktober 2026**.

Semua isi website (daftar produk, review, tabel perbandingan) **dibuat otomatis** dari
file data. Jadi kamu **tidak perlu mengedit HTML** sama sekali.

---

## 1. Isi folder (sekilas)

| File / Folder           | Isinya                                                       | Perlu diedit?        |
|-------------------------|--------------------------------------------------------------|----------------------|
| `tools/build_data.py`   | **Generator**: membaca file data lalu membuat `data/produk.js` | Tidak (cukup dijalankan) |
| `data/produk.js`        | Hasil generator. Dipakai oleh website.                       | ❌ **Jangan diedit manual** |
| `index.html`            | Halaman utama (cari, filter kategori, urutkan)               | Tidak                |
| `review.html`           | Halaman review (satu untuk semua produk)                     | Tidak                |
| `perbandingan.html`     | Tabel perbandingan 20 jenis produk                           | Tidak                |
| `css/`, `js/`           | Tampilan dan program kecil website                           | Tidak                |

File data ada di folder **`/workspace/shopee-data/`**:

| File                       | Isinya                                         |
|----------------------------|------------------------------------------------|
| `gadget-hp.psv`            | 20 produk Gadget & HP                          |
| `fashion-skincare.psv`     | 20 produk Fashion & Skincare                   |
| `rumah-tangga.psv`         | 20 produk Rumah Tangga                         |
| `mainan-hobi.psv`          | 20 produk Mainan & Hobi                        |
| `affiliate-links.psv`      | **Link affiliate Shopee kamu** (lihat bagian 3) |

---

## 2. Cara kerja singkat

```
file .psv  +  affiliate-links.psv   →   python3 tools/build_data.py   →   data/produk.js   →   website
```

Setiap kali kamu mengubah file `.psv`, **jalankan generator lagi** supaya website ikut berubah.

### Cara menjalankan generator

1. Buka **Terminal** (di Mac/Linux) atau **Command Prompt** (Windows).
2. Masuk ke folder website:
   ```
   cd /workspace/web-review-affiliate
   ```
3. Jalankan:
   ```
   python3 tools/build_data.py
   ```
4. Kalau berhasil, akan muncul tulisan seperti:
   ```
   Selesai: .../data/produk.js
     80 produk, 20 kelompok perbandingan
     80 produk memakai link affiliate, 0 masih memakai link biasa
   ```

Kalau file data kamu ada di folder lain, tambahkan `--sumber`:
```
python3 tools/build_data.py --sumber "C:\Users\NamaKamu\shopee-data"
```
Kalau mengambil data baru di tanggal lain, ganti tanggalnya juga:
```
python3 tools/build_data.py --tanggal "15 November 2026"
```

> Tips: kalau kamu membuat folder `sumber-data/` di dalam folder website dan menaruh semua
> file `.psv` di sana, generator otomatis memakai folder itu (tidak perlu `--sumber`).

---

## 3. Memasang link Shopee Affiliate kamu

File: `affiliate-links.psv` (di folder data). Satu baris = satu produk:

```
nomor | link produk asli | link affiliate kamu
```

Contoh:
```
1 | https://shopee.co.id/product/1112776376/42807278779 | https://s.shopee.co.id/AbCdEf123
```

**Langkah:**
1. Masuk ke **Shopee Affiliate** (affiliate.shopee.co.id).
2. Tempel link produk asli (kolom ke-2) ke menu pembuat link (misalnya **"Custom Link"** /
   **"Dapatkan Link"**), lalu salin link pendek yang diawali `https://s.shopee.co.id/...`.
3. Tulis di kolom ke-3, pisahkan dengan ` | ` (spasi, garis tegak, spasi).
4. Simpan file, lalu **jalankan generator** (bagian 2).

Aturan penting:
- Link produk asli harus **sama persis** dengan link di file `.psv` (generator mencocokkan dari situ).
- Produk yang belum punya link affiliate **tetap tampil**, tombolnya memakai link produk biasa.
- Generator akan memberi tahu kalau ada link affiliate yang tidak cocok dengan produk mana pun.
- Nama menu di Shopee Affiliate bisa berubah. Intinya: cari menu untuk **membuat link affiliate dari link produk**.

---

## 4. Menambah atau mengganti produk

Buka salah satu file `.psv` dengan Notepad / TextEdit / VS Code. Satu baris = satu produk,
9 kolom dipisah ` | `:

```
jenis | judul produk | harga | harga coret (atau -) | rating | terjual per bulan | kota | link produk | link gambar
```

Contoh:
```
air fryer | HAN RIVER Air Fryer HRAF04 3.5L Low Power 500 Watt | Rp319.130 | Rp899.000 | 4.9 | 1RB+ Terjual/Bln | Kab. Tangerang | https://shopee.co.id/product/177266177/12719204055 | https://down-id.img.susercontent.com/file/...
```

Penjelasan kolom:

| Kolom              | Cara mengisi                                                                 |
|--------------------|------------------------------------------------------------------------------|
| jenis              | Jenis produk, misalnya `air fryer`. Produk dengan jenis sama akan dibandingkan dalam satu tabel. |
| judul produk       | Salin dari Shopee. Fitur di review **hanya diambil dari judul ini**.          |
| harga              | Harga sekarang, misalnya `Rp319.130`.                                        |
| harga coret        | Harga sebelum diskon. Kalau tidak ada, tulis `-`.                            |
| rating             | Misalnya `4.9`.                                                              |
| terjual per bulan  | Seperti di Shopee, misalnya `1RB+ Terjual/Bln` atau `870 Terjual/Bln`.       |

Di website, angka terjual ditampilkan sebagai rentang: di bawah 1.000 tampil angkanya (`870`), 1.000–9.999 dibulatkan ke bawah per ribuan (`1rb+` … `9rb+`), dan 10.000 ke atas tampil `10rb+`. Fungsinya ada di `tools/build_data.py` (`rentang_terjual`) dan `js/common.js` (`Situs.rentangTerjual`); angka aslinya tetap disimpan di field `terjual` untuk urutan "Terlaris".
| kota               | Kota pengirim, misalnya `Jakarta Utara`. Kalau tidak tahu, tulis `-`.         |
| link produk        | Link produk biasa dari Shopee (bukan link affiliate).                        |
| link gambar        | Link foto produk (klik kanan foto di Shopee → *Salin alamat gambar*).         |

Sebaiknya setiap jenis berisi **4 produk** supaya tabel perbandingan rapi.
Setelah mengedit, **jalankan generator** lalu buka/refresh website.

Kalau ada baris yang salah (jumlah kolom bukan 9), generator akan memberi tahu nomor barisnya
dan baris itu dilewati.

---

## 5. Bagaimana review dibuat?

Generator menulis review **hanya dari data yang ada**: judul produk, harga, diskon, rating,
penjualan per bulan, kota pengirim, dan status toko resmi. Generator **tidak mengarang
spesifikasi** dan **tidak mengaku sudah mencoba produk**.

- **Kelebihan**: misalnya rating tinggi, laris, sedang diskon, paling murah di kelompoknya,
  dan fitur yang tertulis di judul.
- **Kekurangan**: misalnya diskon sangat besar dari harga coret, rating paling rendah di
  kelompoknya, ada pilihan lebih murah, atau judul mencakup beberapa varian.
- **Label perbandingan**: 💰 Paling murah · ⭐ Rating tertinggi · 🔥 Paling laris ·
  ⚖️ Paling seimbang. Kalau semua (atau 3 dari 4) produk nilainya sama, label tidak diberikan
  dan ada catatan kecil di bawah tabel.

Setiap halaman review otomatis menampilkan tulisan bahwa review disusun dari data toko resmi
Shopee per tanggal data, bukan dari uji langsung.

> Gaya bahasa website sengaja netral dan berbasis data ("Bandingin.id membandingkan…"),
> bukan pendapat pribadi. Saat menambah produk, jangan tulis seolah-olah produk sudah dicoba sendiri.

---

## 6. Tombol Tokopedia

Untuk sekarang hanya tombol **Cek Harga di Shopee** yang tampil. Website masih mendukung
tombol **Cek di Tokopedia** (muncul otomatis kalau data produk punya link Tokopedia), tapi
generator belum membaca link Tokopedia. Minta bantuan kalau nanti mau menambahkannya.

---

## 7. Mencoba website di komputer sendiri

Klik dua kali `index.html`. Website langsung terbuka di browser.

Cek beberapa hal setelah menjalankan generator:
- Jumlah produk di beranda benar.
- Klik tombol **Cek Harga di Shopee**, pastikan produk yang benar terbuka.
- Buka menu **Perbandingan**.

---

## 8. Online gratis di GitHub Pages (ringkas)

1. Buat akun di **github.com**.
2. Buat repository baru, misalnya `bandingin-id` (pilih **Public**).
3. Klik **Add file → Upload files**, upload **semua isi** folder `web-review-affiliate`
   (`index.html`, `review.html`, `perbandingan.html`, `css`, `js`, `data`, `tools`, dst.).
   Folder `screenshots` tidak wajib.
4. Buka **Settings → Pages** → Branch `main`, folder `/ (root)` → **Save**.
5. Tunggu 1–2 menit. Website online di `https://NAMA-AKUN.github.io/bandingin-id/`.

Setiap kali data berubah: jalankan generator di komputer, lalu upload ulang file
`data/produk.js` ke GitHub.

---

## 9. Mengganti nama website

Nama **Bandingin.id** ada di `index.html`, `review.html`, dan `perbandingan.html`
(logo di bagian atas, judul halaman `<title>`, dan teks di bagian bawah). Kalimat review
yang menyebut "Bandingin.id" ada di `tools/build_data.py`; setelah mengubahnya, jalankan generator lagi.

## 10. Masalah yang sering terjadi

- **Website kosong / produk tidak muncul** → `data/produk.js` rusak karena diedit manual.
  Jalankan generator lagi.
- **Gambar tidak muncul** → link gambar salah atau sudah dihapus Shopee. Website otomatis
  menampilkan ikon kategori sebagai gantinya. Perbarui link gambar di file `.psv`.
- **Link affiliate tidak terpakai** → link produk asli di `affiliate-links.psv` tidak sama
  persis dengan yang ada di `.psv`. Lihat pesan dari generator.
- **Harga sudah berubah** → wajar. Ambil data baru, perbarui `.psv`, lalu jalankan generator
  dengan `--tanggal` yang baru.

## Slide show & Top 10 Terlaris (beranda)

- **Slide show** (`js/slideshow.js`): slide 1 = hero, slide 2–5 = produk unggulan per kategori, dipilih otomatis oleh `Situs.produkUnggulan` di `js/common.js` (utamakan label "Paling seimbang", lalu rating, terjual/bln, diskon, harga termurah).
- **Top 10 Terlaris** (`js/top10.js`): sumbernya `top10-kandidat.psv` di folder data (11 kolom: kategori | keyword | judul | harga | harga coret | rating | total terjual | terjual/bln | kota | link produk | link gambar). Link produknya harus sama dengan salah satu dari 80 produk. `tools/build_data.py` menambahkan `terjualTotal` ke produk tersebut dan menyusun `window.TOP10` per kategori: total terjual → terjual/bln → rating → harga termurah.
