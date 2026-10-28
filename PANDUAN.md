# Panduan PilihYuk

PilihYuk membandingkan **skincare** dari jenis yang sama, dalam dua bentuk: **Lokal vs Korea** (satu merek lokal, satu merek Korea) dan **Lokal vs Lokal** (dua merek lokal). Isinya facial wash, pelembab, serum, dan sunscreen. Tidak ada pembagian perempuan / pria.

Situs ini statis (HTML, CSS, gambar). Cocok untuk GitHub Pages, tanpa server.

## Isi folder

| File | Fungsi |
|------|--------|
| `index.html` | Beranda. Hasil generator, jangan diedit manual. |
| `banding/*.html` | Satu halaman per perbandingan. Hasil generator. |
| `css/style.css` | Tampilan. |
| `img/` | Foto produk (hasil generator) plus logo dan ikon: `logo.png`, `logo.webp`, `favicon-32.png`, `apple-touch-icon.png`, dan `logo-asli.jpg` (desain asli). Logo dan ikon tidak ikut dihapus generator. |
| `favicon.ico` | Ikon tab browser (16/32/48 px). |
| `tools/proses_logo.py` | Membuat ulang logo dan ikon dari `img/logo-asli.jpg`, warnanya disesuaikan ke palet situs (#0c6b52 dan #1a4f86). |
| `tools/pasangan.json` | Teks perbandingan: kandungan, manfaat, jenis kulit, verdict. |
| `tools/build_site.py` | Generator. |
| `tools/analisa.json` | Catatan kandungan. Acuan fakta, tidak ditampilkan mentah. |
| `sumber/kandungan-batch2.json` | Catatan kandungan batch 27 Oktober 2026 (per produk, per varian kalau ada), lengkap dengan sumbernya. |
| `sumber/kandungan-batch3.json` | Catatan kandungan batch 28 Oktober 2026 dengan sumbernya. Generator membaca semua `kandungan-batch*.json`; satu produk hanya boleh tercatat di satu file. |
| `sumber/` | Data Shopee skincare, link affiliate, daftar merek Korea, pasangan yang sudah diposting. |
| `sumber/tambahan-*.psv` | Batch produk baru. Kolom: type, brand, origin, name, price, original price, product URL, image URL, short link, key ingredients. |
| `ulasan.html` | Halaman Kasih Pendapat. Hasil generator (daftar perbandingan di dropdown ikut terbarui). |
| `tentang.html` | Halaman Tentang Kami: pengelola, alasan situs dibuat, cara perbandingan dibuat, link affiliate, kontak. Hasil generator. |
| `js/config.js` | **Satu tempat** untuk alamat pengiriman formulir: `FEEDBACK_ENDPOINT`. |
| `js/ulasan.js` | Perilaku formulir. |

`review.html` dan `perbandingan.html` hanya mengalihkan ke beranda, supaya tautan lama tidak buntu.

## Membangun ulang

Dari folder situs:

```
python3 tools/build_site.py
```

Gambar yang sudah ada tidak diunduh lagi. Untuk mengunduh ulang: `python3 tools/build_site.py --gambar`.

### Pratinjau sebelum link pendek ada (`--draft`)

```
python3 tools/build_site.py --draft
```

Dengan `--draft`, produk di `tambahan-*.psv` yang kolom short link-nya masih kosong tetap ikut dibangun. Tombolnya jadi **Link menyusul** (abu-abu, tidak bisa diklik). Generator mencetak daftar id produk + URL Shopee yang masih butuh link pendek. Hasil draft **jangan dipublikasikan**.

Tanpa `--draft`, build tetap gagal kalau ada short link kosong atau bukan `https://s.shopee.co.id/…`. Setelah semua link diisi, jalankan build biasa lalu commit hasilnya.

Generator gagal kalau ada link affiliate yang bukan `https://s.shopee.co.id/…`, produk Korea/lokal tertukar, pasangan di `posted.log` tidak berada di urutan teratas, atau teks memakai kata yang tidak boleh tampil (rating, terjual, pria, wanita, dan sejenisnya).

## Menambah perbandingan

1. Produk harus ada di `sumber/perempuan.psv`, `sumber/pria.psv` (plus `affiliate-links.psv`), atau di `sumber/tambahan-*.psv` (link pendeknya sudah di kolom short link).
2. Merek Korea hanya yang tercantum di `sumber/merek-korea.txt`. Sisi lokal tidak boleh merek dari daftar itu. Anua dan ISNTREE masuk daftar itu lewat batch tambahan.
3. Tambah objek di `tools/pasangan.json`. Pasangan yang sudah diposting (urutan di `sumber/posted.log`) harus tetap di awal. Produk boleh dipakai lagi di pasangan lain, tapi pasangan yang sama persis tidak boleh dua kali. Kalau produk lama dipakai lagi dengan harga atau link pendek listing yang baru, jangan ubah baris lamanya: isi `"listing": {"harga", "asli", "aff"}` di teks produk pasangan baru. Pasangan lama tetap memakai data lama.
4. Tulis kandungan dari `tools/analisa.json`, dari kolom key ingredients di file tambahan, atau dari nama produk. Kalau kolomnya `tidak tercantum`, jangan karang daftar bahan: jelaskan dari jenis dan nama, dan tulis bahwa bahan tidak tercantum. Bentuk yang longgar (essence, stik, pelembap sekaligus sunscreen) disebut apa adanya. Jangan mengaku sudah mencoba, jangan membuat klaim medis.
5. Bahasa untuk semua orang. Jangan menulis pria, wanita, cowok, atau sejenisnya.
6. Jangan menampilkan rating atau jumlah terjual.
7. Jalankan generator, lalu buka `index.html` lewat server lokal (`python3 -m http.server`).

### Lokal vs Korea dan Lokal vs Lokal

Setiap objek di `pasangan.json` punya kunci `banding`:

- `"lokal-korea"` (bawaan kalau tidak ditulis): sisi produk memakai kunci `lokal` dan `korea`. `lebihMurah` berisi `lokal` atau `korea`. Pasangan di `posted.log` selalu jenis ini.
- `"lokal-lokal"`: sisi produk memakai kunci `a` dan `b`, keduanya merek lokal (bukan dari `merek-korea.txt`). Tiap sisi boleh punya `label` (misalnya nama merek) untuk judul kolom tabel. `lebihMurah` berisi `a` atau `b`.

Beranda punya dua baris filter: jenis produk (facial wash, pelembab, serum, sunscreen) dan jenis perbandingan. Keduanya bisa digabung, angka di chip terhitung otomatis. Tiap kartu dan halaman memberi badge jenis perbandingan.

### Listing "Series" / banyak varian

Listing yang berisi beberapa varian (All Series, 3 in 1, dan sejenisnya) masuk **Lokal vs Lokal**. Isi di sisi produknya:

- `varian`: daftar `{ "nama", "kandungan", "cocok": [...], "catatan" }`, satu per varian. Jangan karang bahan; kalau belum ketemu, tulis begitu.
- Di level pasangan: `varianIntro` (penjelasan singkat, misalnya bahwa varian diambil dari judul listing) dan `adu`: daftar `{ "kebutuhan", "a", "b", "pilih" }` untuk membandingkan varian berdampingan dengan verdict per kebutuhan.

Generator gagal kalau ada varian yang tidak muncul di kolom `adu` sisinya, atau kalau isi `adu` kosong. Halaman menampilkan bagian **Varian satu per satu** di bawah detail produk.

Dropdown "perbandingan mana yang kamu baca" di halaman Kasih Pendapat terisi dari `pasangan.json`. Tidak perlu mengedit formulirnya. Kalau nanti ada pertanyaan baru, tambah kuncinya di `js/ulasan.js` (objek kiriman) dan di daftar `KOLOM` pada skrip Google di bawah.

Tombol beli selalu memakai link affiliate pendek. Harga dan diskon diambil dari file `.psv` (atau dari `listing` di pasangan, lihat di atas).

Harga listing dengan beberapa pilihan (ukuran, paket, varian) boleh ditulis sebagai rentang di kolom price dan original price, misalnya `Rp47.900-222.500`. Halaman menampilkan `Rp47.900–Rp222.500` tanpa harga coret, dan pemeriksaan `lebihMurah` memakai harga terendah. Sebutkan di catatan produk bahwa harga ikut pilihan di listing. Harga setelah voucher toko ditulis sama di price dan original price, dan disebut di catatan.

Listing banyak varian di **Lokal vs Korea** memakai `varianDipilih` (contoh: SKINTIFIC UV Shield, yang dibandingkan Bright Fit).

## Yang sengaja tidak masuk

- Sabun, sampo, baju, tas, kaos, dan produk balita: bukan skincare.
- Facial wash dari data awal: tidak ada analisa kandungan dan tidak ada pasangan Korea di batch itu. Facial wash yang tampil berasal dari `tambahan-*.psv`.
- Garnier dan Nivea: bukan merek lokal dan bukan merek Korea.
- Batch 27 Oktober 2026: Scarlett Moisturizer Series (bahan tidak tercantum, varian tidak bisa dicek, dan jumlah pelembab ganjil), Scarlett Glowtening Serum (sudah jadi varian di listing Scarlett Face Serum), dan Scarlett Ultra Light Sunscreen dari toko lain (produk sama dengan listing toko resmi yang dipakai).
- Batch 28 Oktober 2026: Beauty of Joseon Aqua-Fresh, Round Lab Birch Juice Sunscreen, dan SKIN1004 Centella Soothing Cream dipakai lagi lewat `listing` (data lama tidak diubah).
- Beberapa produk skincare lain tidak dipasangkan, dengan prioritas penjualan di data. Daftarnya dicetak generator saat dijalankan.

## Kasih Pendapat

Halaman `ulasan.html` (tautan **Kasih Pendapat** di menu dan footer, plus ajakan di akhir tiap perbandingan). Formulir mengirim JSON ke alamat di `js/config.js`:

```javascript
var FEEDBACK_ENDPOINT = "";
```

Kalau string itu kosong, pengunjung tetap melihat ucapan terima kasih dan bisa menyalin jawabannya. Tidak ada pesan error.

Isi dengan URL web app Google (berakhiran `/exec`) atau URL Formspree (`https://formspree.io/f/xxxxxxxx`).

### Google Sheet

1. Buat spreadsheet baru. Sheet pertama boleh dibiarkan, atau beri nama `Pendapat`.
2. Menu **Extensions → Apps Script**. Hapus isi editor, tempel skrip di bawah, simpan.
3. **Deploy → New deployment → Select type: Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
4. Salin URL yang berakhiran `/exec` ke `FEEDBACK_ENDPOINT` di `js/config.js`, lalu unggah file itu ke GitHub.
5. Kalau skripnya diubah, buka **Deploy → Manage deployments → Edit → Version: New version → Deploy**. URL-nya tetap.

Kolom yang ditulis: waktu, membantu, perbandingan, perbandingan_id, mudah, kurang, saran, berikutnya, kontak, halaman. Pertanyaan baru tinggal ditambah ke array `KOLOM`.

```javascript
var KOLOM = [
  "waktu",
  "membantu",
  "perbandingan",
  "perbandingan_id",
  "mudah",
  "kurang",
  "saran",
  "berikutnya",
  "kontak",
  "halaman"
];

function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Pendapat") || ss.getSheets()[0];
  var data = {};
  try {
    data = JSON.parse(e.postData && e.postData.contents ? e.postData.contents : "{}");
  } catch (err) {
    data = e.parameter || {};
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(KOLOM);
  }
  var baris = KOLOM.map(function (kunci) {
    return data[kunci] == null ? "" : String(data[kunci]);
  });
  sheet.appendRow(baris);
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
```

## Online

Nama yang tampil ke pengunjung adalah PilihYuk. Repository GitHub tetap `bandingin-id`, branch `main`, folder root. Alamat yang hidup sekarang `https://pilihyuk.id/` (file `CNAME`, jangan dihapus). URL absolut (canonical, og:url, sitemap) diambil dari `BASE_URL` di `tools/build_site.py`. Generator juga menulis `sitemap.xml` dan `robots.txt`, dan meta verifikasi Google Search Console (`GOOGLE_SITE_VERIFICATION`) di setiap halaman.

Tautan panduan (`https://lynk.id/albijulian`) hanya ada sekali, di beranda.

## Kepercayaan pengunjung

Teksnya ada di bagian atas `tools/build_site.py` (`CATATAN_AFFILIATE`, `CATATAN_AMAN`, `CATATAN_STATIS`), jadi cukup diubah di satu tempat.

- Catatan affiliate Shopee tampil di footer semua halaman, di dekat tombol beli (beranda dan tiap perbandingan), dan di Tentang Kami (`tentang.html#affiliate`).
- Di dekat tombol beli ada catatan bahwa pengunjung diarahkan ke Shopee resmi dan PilihYuk tidak meminta data pribadi atau pembayaran.
- Tombol beli memakai `target="_blank"` dan `rel="sponsored noopener noreferrer"`. Generator gagal kalau ada link Shopee tanpa itu.
- **Sumber kandungan**: URL di kolom `sumber` pada `sumber/kandungan-batch2.json` tampil sebagai tautan di kartu produk. Hanya URL dari data. Domain yang dimasukkan ke `SUMBER_DILEWATI` di `tools/build_site.py` tidak ditampilkan; saat ini kosong. `inkeedecoder.com` adalah nama baru resmi INCIDecoder (`incidecoder.com` dialihkan ke sana), jadi tautannya asli.
- **Kontak**: belum ditentukan. Tentang Kami mengarahkan ke formulir Kasih Pendapat. Kalau email atau akun media sosial sudah dipilih, isi `KONTAK_LAIN` di `tools/build_site.py` lalu bangun ulang. Jangan isi alamat karangan.
