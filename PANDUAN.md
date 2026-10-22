# Panduan Website "Bandingin.id"

Bandingin.id membandingkan produk **perawatan diri, skincare & fashion** dari toko resmi Shopee (Shopee Mall).
Produk skincare punya analisa kandungan tulisan tangan; produk lain diulas otomatis dari data. Produk dibagi ke 3 kategori menurut pemakainya:

| Kategori      | Jenis produk (masing-masing 5 pilihan)                                   | Jumlah |
|---------------|---------------------------------------------------------------------------|--------|
| 👩 Perempuan  | Sabun Mandi, Sampo, Facial Wash, Baju, Tas, Pelembab Wajah, Serum Wajah, Sunscreen (Wanita) | 40 |
| 👨 Pria       | Sabun Mandi, Sampo, Facial Wash, Kaos, Pelembab Wajah, Serum Wajah, Sunscreen (Pria)        | 35 |
| 👶 Balita     | Sabun Bayi, Sampo Bayi                                                     | 10 |

Total 85 produk. Data diambil **22 Oktober 2026**. Jumlah produk yang tampil di website selalu
dihitung otomatis dari data.

> Versi lama (80 produk gadget, rumah tangga, dll.) disimpan di git dengan tag `versi-80-produk`.

Semua isi website (daftar produk, review, tabel perbandingan) **dibuat otomatis** dari
file data. Jadi kamu **tidak perlu mengedit HTML** sama sekali.

---

## 1. Isi folder (sekilas)

| File / Folder           | Isinya                                                       | Perlu diedit?        |
|-------------------------|--------------------------------------------------------------|----------------------|
| `tools/build_data.py`   | **Generator**: membaca file data lalu membuat `data/produk.js` | Tidak (cukup dijalankan) |
| `data/produk.js`        | Hasil generator. Dipakai oleh website.                       | ❌ **Jangan diedit manual** |
| `index.html`            | Halaman utama (slide show, Top 10, filter kategori + jenis, cari, urutkan) | Tidak  |
| `review.html`           | Halaman review (satu untuk semua produk)                     | Tidak                |
| `perbandingan.html`     | Tabel perbandingan per jenis produk                          | Tidak                |
| `css/`, `js/`           | Tampilan dan program kecil website                           | Tidak                |

File data ada di folder **`/workspace/shopee-data-v2/`**:

| File                       | Isinya                                         |
|----------------------------|------------------------------------------------|
| `perempuan.psv`            | 25 produk Perempuan                            |
| `pria.psv`                 | 20 produk Pria                                 |
| `balita.psv`               | 10 produk Balita                               |
| `affiliate-links.psv`      | **Link affiliate Shopee kamu** (lihat bagian 3) |

Kalau salah satu file belum ada, generator hanya memberi peringatan dan tetap jalan
(berguna untuk mencoba tampilan). Untuk deploy, pakai `--final` (lihat bagian 2).

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
     85 produk, 17 kelompok perbandingan
       Perempuan: 40 produk (...)
       Pria: 35 produk (...)
       Balita: 10 produk (...)
     85 produk memakai link affiliate, 0 masih memakai link biasa
     30 produk memakai analisa tulisan tangan (tools/analisa.json), 12 produk bermerek Korea
   ```
5. **Sebelum deploy** jalankan pemeriksaan akhir. Perintah ini gagal (dengan pesan
   `BELUM SIAP DEPLOY`) kalau ada file kategori yang belum ada, produk tanpa link affiliate, kelompok
   yang tidak berisi 5 produk, atau produk skincare yang belum punya analisa:
   ```
   python3 tools/build_data.py --final
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
- Produk yang belum punya link affiliate **tetap tampil** (tombolnya memakai link produk biasa),
  tapi website **tidak boleh di-deploy** sebelum semua produk punya link affiliate (`--final`).
- Generator akan memberi tahu kalau ada link affiliate yang tidak cocok dengan produk mana pun.
- Nama menu di Shopee Affiliate bisa berubah. Intinya: cari menu untuk **membuat link affiliate dari link produk**.

---

## 4. Menambah atau mengganti produk

Buka salah satu file `.psv` dengan Notepad / TextEdit / VS Code. Satu baris = satu produk,
10 kolom dipisah ` | `:

```
jenis | judul produk | harga | harga coret (atau -) | rating | total terjual | terjual per bulan | kota | link produk | link gambar
```

Contoh:
```
shampoo wanita | Sunsilk Shampoo Silky Smooth 450ml | Rp55.800 | Rp61.900 | 5.0 | 10RB+ Terjual | 1RB+ Terjual/Bln | Kab. Bogor | https://shopee.co.id/product/... | https://down-id.img.susercontent.com/file/...
```

Penjelasan kolom:

| Kolom              | Cara mengisi                                                                 |
|--------------------|------------------------------------------------------------------------------|
| jenis              | Salah satu dari: `sabun mandi wanita`, `shampoo wanita`, `facial wash wanita`, `baju wanita`, `tas wanita`, `sabun mandi pria`, `shampoo pria`, `facial wash pria`, `kaos pria`, `sabun bayi`, `shampoo bayi`. Produk dengan jenis sama dibandingkan dalam satu tabel. Nama kelompok & kategorinya diatur di `JENIS` dalam `tools/build_data.py`. |
| judul produk       | Salin dari Shopee. Fitur di review **hanya diambil dari judul ini**.          |
| harga              | Harga sekarang, misalnya `Rp319.130`.                                        |
| harga coret        | Harga sebelum diskon. Kalau tidak ada, tulis `-`.                            |
| rating             | Misalnya `4.9`.                                                              |
| total terjual      | Dari halaman produk, misalnya `10RB+ Terjual` atau `518 Terjual`.            |
| terjual per bulan  | Dari kartu hasil pencarian, misalnya `1RB+ Terjual/Bln` atau `870 Terjual/Bln`. |
| kota               | Kota pengirim, misalnya `Jakarta Utara`. Kalau tidak tahu, tulis `-`.         |
| link produk        | Link produk biasa dari Shopee (bukan link affiliate).                        |
| link gambar        | Link foto produk (klik kanan foto di Shopee → *Salin alamat gambar*).         |

Di website, angka terjual ditampilkan sebagai rentang: di bawah 1.000 tampil angkanya (`870`),
1.000–9.999 dibulatkan ke bawah per ribuan (`1rb+` … `9rb+`), dan 10.000 ke atas tampil `10rb+`.
Fungsinya ada di `tools/build_data.py` (`rentang_terjual`) dan `js/common.js` (`Situs.rentangTerjual`);
angka aslinya tetap disimpan (`terjual`, `terjualTotal`) untuk pengurutan.

Sebaiknya setiap jenis berisi **5 produk** supaya tabel perbandingan rapi.
Setelah mengedit, **jalankan generator** lalu buka/refresh website.

Kalau ada baris yang salah (jumlah kolom bukan 10), generator akan memberi tahu nomor barisnya
dan baris itu dilewati.

---

## 5. Bagaimana review dibuat?

Generator menulis review **hanya dari data yang ada**: judul produk, harga, diskon, rating,
total terjual, penjualan per bulan, kota pengirim, dan status toko resmi. Generator **tidak
mengarang spesifikasi**, **tidak mengaku sudah mencoba produk**, dan **tidak membuat klaim
kesehatan/medis** (khasiat atau keamanan produk tidak dinilai).

- **Kelebihan**: misalnya rating tinggi, banyak terjual, sedang diskon, paling murah di
  kelompoknya, paling hemat per 100 ml/g (kalau ukuran jelas di judul), dan hal yang tertulis di
  judul produk (ditandai "menurut penjual").
- **Kekurangan**: misalnya diskon sangat besar dari harga coret, rating paling rendah di
  kelompoknya, ada pilihan lebih murah, atau judul mencakup beberapa varian.
- **Label perbandingan**: 💰 Paling murah · ⭐ Rating tertinggi · 🔥 Paling laris (total terjual,
  lalu per bulan) · ⚖️ Paling seimbang. Kalau semua (atau lebih dari 2) produk nilainya sama,
  label tidak diberikan dan ada catatan kecil di bawah tabel.

**Tips** (kotak 💡 di halaman review) berisi saran praktis sesuai jenis produk (cara pakai serum/
sunscreen, cek tabel ukuran baju, dll.). Untuk **Balita** selalu ada tips: perhatikan usia yang
dianjurkan di kemasan dan coba dulu di sedikit area kulit.

Tidak ada catatan "belum dicoba" di tiap review/kartu. Hanya ada **satu catatan kecil di footer**:
"Ulasan disusun dari analisa kandungan dan informasi produk. Bandingin.id mendapat komisi dari link affiliate."

### 5a. Analisa skincare (tulisan tangan): `tools/analisa.json`

Untuk 30 produk skincare (pelembab, serum, sunscreen), review otomatis **diganti** dengan analisa
yang ditulis manual. Kuncinya adalah **item ID** Shopee (angka terakhir di URL produk,
`https://shopee.co.id/product/<toko>/<ITEM ID>`). Isi tiap produk:

```
"16581227588": {
  "ringkasan": "satu kalimat",
  "analisa": "80–150 kata: kandungan utama, jenis kulit yang cocok, tekstur & hasil akhir, harga per ml",
  "kelebihan": ["...", "..."], "kekurangan": ["...", "..."],
  "kesimpulan": "untuk siapa produk ini", "cocokKulit": ["berminyak", "kering", "normal", "sensitif", "berjerawat"]
}
```

Aturan menulis: gaya netral ("Bandingin.id menilai…", tanpa "kami"/"saya"), jangan mengaku sudah
mencoba, jangan klaim medis atau hasil pasti (pakai "umumnya", "dikenal untuk", "cocok untuk"),
dan kalau fakta tidak bisa dipastikan dari sumber resmi, lebih baik tidak ditulis.
Kalau produk skincare diganti, tulis analisa untuk item ID barunya (`--final` gagal kalau belum ada).

### 5b. "Pilihan Bandingin.id": `tools/pilihan.json`

Kotak hijau di atas tiap kelompok skincare (halaman perbandingan, bagian perbandingan di halaman
review, dan di beranda saat sub-filter Pelembab/Serum/Sunscreen dipilih). Kunci = id kelompok
(mis. `sunscreen-pria`), isi = daftar `{"label", "item" (item ID), "alasan"}`, biasanya 3:
kulit berminyak/berjerawat, kulit kering/sensitif, dan paling hemat.

### 5c. Badge 🇰🇷 Merek Korea

Daftar merek ada di `merek-korea.txt` (folder data, satu merek per baris). Produk yang judulnya
mengandung salah satu merek itu (tidak peduli huruf besar/kecil) otomatis mendapat badge.

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
  menampilkan ikon kategori (👩 👨 👶) sebagai gantinya. Perbarui link gambar di file `.psv`.
- **Link affiliate tidak terpakai** → link produk asli di `affiliate-links.psv` tidak sama
  persis dengan yang ada di `.psv`. Lihat pesan dari generator.
- **Harga sudah berubah** → wajar. Ambil data baru, perbarui `.psv`, lalu jalankan generator
  dengan `--tanggal` yang baru.

## 11. Slide show, Top 10 Terlaris, dan filter (beranda)

- **Slide show** (`js/slideshow.js`): slide 1 = hero, lalu satu produk unggulan per kategori
  (Perempuan, Pria, Balita), dipilih otomatis oleh `Situs.produkUnggulan` di `js/common.js`
  (utamakan label "Paling seimbang", lalu rating, terjual/bln, diskon, harga termurah).
- **Top 10 Terlaris** (`js/top10.js`): tab Perempuan / Pria / Balita. Disusun oleh
  `tools/build_data.py` (`window.TOP10`) dari semua produk di kategori itu: total terjual →
  terjual/bln → rating → harga termurah.
- **Filter**: chip kategori (Semua / Perempuan / Pria / Balita). Saat satu kategori dipilih,
  muncul sub-filter jenis (mis. Sabun Mandi / Sampo / Facial Wash / Baju / Tas). Bisa juga lewat
  link, misalnya `index.html?kategori=Pria&jenis=kaos-pria`.
