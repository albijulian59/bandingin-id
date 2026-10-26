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

Tombol beli selalu memakai link affiliate pendek. Harga dan diskon diambil dari file `.psv`.

## Yang sengaja tidak masuk

- Sabun, sampo, baju, tas, kaos, dan produk balita: bukan skincare.
- Facial wash: tidak ada produk merek Korea di data, dan tidak ada analisa kandungan.
- Garnier: bukan merek lokal dan bukan merek Korea.
- Beberapa produk skincare lain tidak dipasangkan supaya setiap produk hanya muncul sekali, dengan prioritas penjualan di data. Daftarnya dicetak generator saat dijalankan.

## Online

Repository GitHub `bandingin-id`, branch `main`, folder root. Alamatnya `https://albijulian59.github.io/bandingin-id/`.

Tautan panduan (`https://lynk.id/albijulian`) hanya ada sekali, di beranda. Catatan affiliate hanya di footer.
