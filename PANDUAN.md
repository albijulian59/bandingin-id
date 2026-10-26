# Panduan Bandingin.id

Bandingin.id membandingkan **skincare**: satu produk merek lokal dan satu produk merek Korea, jenis yang sama. Isinya pelembab, serum, dan sunscreen. Tidak ada pembagian perempuan / pria. Facial wash tidak ditampilkan karena di data tidak ada facial wash merek Korea.

Situs ini statis (HTML, CSS, gambar). Cocok untuk GitHub Pages, tanpa server.

## Isi folder

| File | Fungsi |
|------|--------|
| `index.html` | Beranda. Hasil generator, jangan diedit manual. |
| `banding/*.html` | Satu halaman per perbandingan. Hasil generator. |
| `css/style.css` | Tampilan. |
| `img/` | Foto produk. Hasil generator. |
| `tools/pasangan.json` | Teks perbandingan: kandungan, manfaat, jenis kulit, verdict. |
| `tools/build_site.py` | Generator. |
| `tools/analisa.json` | Catatan kandungan. Acuan fakta, tidak ditampilkan mentah. |
| `sumber/` | Data Shopee skincare, link affiliate, daftar merek Korea, pasangan yang sudah diposting. |
| `ulasan.html` | Halaman Kasih Pendapat. Hasil generator (daftar perbandingan di dropdown ikut terbarui). |
| `js/config.js` | **Satu tempat** untuk alamat pengiriman formulir: `FEEDBACK_ENDPOINT`. |
| `js/ulasan.js` | Perilaku formulir. |

`review.html` dan `perbandingan.html` hanya mengalihkan ke beranda, supaya tautan lama tidak buntu.

## Membangun ulang

Dari folder situs:

```
python3 tools/build_site.py
```

Gambar yang sudah ada tidak diunduh lagi. Untuk mengunduh ulang: `python3 tools/build_site.py --gambar`.

Generator gagal kalau ada link affiliate yang bukan `https://s.shopee.co.id/…`, produk Korea/lokal tertukar, pasangan di `posted.log` tidak berada di urutan teratas, atau teks memakai kata yang tidak boleh tampil (rating, terjual, pria, wanita, dan sejenisnya).

## Menambah perbandingan

1. Produk harus ada di `sumber/perempuan.psv` atau `sumber/pria.psv`, dan punya link pendek di `sumber/affiliate-links.psv`.
2. Merek Korea hanya yang tercantum di `sumber/merek-korea.txt`. Sisi lokal tidak boleh merek dari daftar itu.
3. Tambah objek di `tools/pasangan.json`. Pasangan yang sudah diposting (urutan di `sumber/posted.log`) harus tetap di awal.
4. Tulis kandungan hanya dari `tools/analisa.json` atau dari nama produk. Jangan mengarang bahan, jangan mengaku sudah mencoba, jangan membuat klaim medis.
5. Bahasa untuk semua orang. Jangan menulis pria, wanita, cowok, atau sejenisnya.
6. Jangan menampilkan rating atau jumlah terjual.
7. Jalankan generator, lalu buka `index.html` lewat server lokal.

Dropdown "perbandingan mana yang kamu baca" di halaman Kasih Pendapat terisi dari `pasangan.json`. Tidak perlu mengedit formulirnya. Kalau nanti ada pertanyaan baru, tambah kuncinya di `js/ulasan.js` (objek kiriman) dan di daftar `KOLOM` pada skrip Google di bawah.

Tombol beli selalu memakai link affiliate pendek. Harga dan diskon diambil dari file `.psv`.

## Yang sengaja tidak masuk

- Sabun, sampo, baju, tas, kaos, dan produk balita: bukan skincare.
- Facial wash: tidak ada produk merek Korea di data, dan tidak ada analisa kandungan.
- Garnier: bukan merek lokal dan bukan merek Korea.
- Beberapa produk skincare lain tidak dipasangkan supaya setiap produk hanya muncul sekali, dengan prioritas penjualan di data. Daftarnya dicetak generator saat dijalankan.

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

Repository GitHub `bandingin-id`, branch `main`, folder root. Alamatnya `https://albijulian59.github.io/bandingin-id/`.

Tautan panduan (`https://lynk.id/albijulian`) hanya ada sekali, di beranda. Catatan affiliate hanya di footer.
