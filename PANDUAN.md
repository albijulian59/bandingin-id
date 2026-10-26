# Panduan Bandingin.id

Situs ini membandingkan **skincare lokal vs Korea** yang setipe: pelembab, serum, sunscreen, dan (kalau datanya ada) facial wash. Satu halaman = satu produk lokal dijejer dengan satu produk Korea.

Bukan katalog semua produk. Produk di luar skincare tidak masuk. Facial wash dihitung skincare, tapi baru bisa dibandingin kalau ada pasangan Korea-nya.

Isi halaman (judul, kandungan, manfaat, putusan) ada di `tools/konten.json`. Harga, foto, dan tombol beli diambil dari data Shopee saat situs dibangun, bukan diketik di HTML.

## Membangun situs

```bash
python3 tools/build_site.py --sumber /path/ke/shopee-data-v2
```

Folder sumber butuh `perempuan.psv`, `pria.psv`, `affiliate-links.psv`, dan `merek-korea.txt`. Analisa kandungan dibaca dari `tools/analisa.json`.

Skrip menolak build kalau:

- ada tombol yang bukan link pendek `https://s.shopee.co.id/...`
- ada produk skincare ber-affiliate yang tidak masuk perbandingan dan tidak tercatat alasannya
- produk "lokal" ternyata merek di `merek-korea.txt`, atau sebaliknya
- teks situs memuat rating atau angka terjual

`index.html` dan `banding/*.html` hasil generate. Edit `tools/konten.json`, lalu jalankan skrip lagi.

## Isi perbandingan

Delapan perbandingan pertama mengikuti urutan thread di X. Empat berikutnya mengisi jenis yang masih punya pasangan Korea yang belum terpakai. Satu produk hanya dipakai sekali.

Tombol **Beli di Shopee** selalu link affiliate pendek. Rating dan jumlah terjual tidak ditampilkan.

Catatan komisi affiliate hanya di footer. E-book (`https://lynk.id/albijulian`) hanya di beranda.

## Menambah pasangan

1. Pastikan dua produk setipe (sama-sama pelembab, atau serum, atau sunscreen, atau facial wash), satu lokal dan satu Korea, dan keduanya punya baris di `affiliate-links.psv`.
2. Tambah objek di `tools/konten.json`. Fakta kandungan hanya dari `tools/analisa.json`. Kalau belum ada analisa, jangan mengarang daftar bahan.
3. Kalau produk yang tadinya dilewati sekarang dipakai, hapus item ID-nya dari `ALASAN_DILEWATI` di `tools/build_site.py`.
4. Jalankan skrip di atas.

## Online

GitHub Pages, branch `main`, folder root. Alamatnya `https://albijulian59.github.io/bandingin-id/`. File `.nojekyll` harus tetap ada.
