#!/usr/bin/env python3
"""Buat img/logo.png, img/logo.webp, favicon.ico, img/favicon-32.png, img/apple-touch-icon.png
dari img/logo-asli.jpg. Warna terracotta -> #0c6b52 (--lokal), sage -> #1a4f86 (--korea).
Jalankan dari folder situs: python3 tools/proses_logo.py
"""
from PIL import Image
import numpy as np
src = Image.open('img/logo-asli.jpg').convert('RGB')
im = np.asarray(src).astype(float)
d = np.sqrt(((255 - im) ** 2).sum(2))
mask = d > 40
cols = np.where(mask.any(0))[0]
# kolom kosong pemisah ikon dan teks
gaps = [c for c in range(cols.min(), cols.max()) if not mask[:, c].any()]
print('gaps', gaps[:5], gaps[-5:] if gaps else None)
# solid colors
solid = im[d > 150]
print('solid samples', np.percentile(d[d>150],[5,50]))
T0, T1 = 14.0, 170.0
a = np.clip((d - T0) / (T1 - T0), 0, 1)
rgb = np.empty_like(im)
safe = np.maximum(a, 1e-6)[..., None]
rgb = (im - (1 - a[..., None]) * 255.0) / safe
rgb = np.clip(rgb, 0, 255)
rgb[a == 0] = 0
# Warna ulang ke palet situs (css/style.css), bentuk dan anti-aliasing tetap.
SRC_TERRA = np.array([209., 117., 83.])   # terracotta di logo asli
SRC_SAGE = np.array([139., 156., 121.])   # sage di logo asli
DST_TERRA = np.array([0x0c, 0x6b, 0x52], float)  # --lokal #0c6b52 (warna utama situs)
DST_SAGE = np.array([0x1a, 0x4f, 0x86], float)   # --korea #1a4f86 (warna aksen kedua situs)
dt = np.sqrt(((rgb - SRC_TERRA) ** 2).sum(2))
ds = np.sqrt(((rgb - SRC_SAGE) ** 2).sum(2))
w = (ds / np.maximum(dt + ds, 1e-6))[..., None]  # 1 = terracotta, 0 = sage
rgb = w * DST_TERRA + (1 - w) * DST_SAGE
rgb[a == 0] = 0
rgba = np.dstack([rgb, a * 255]).round().astype(np.uint8)
full = Image.fromarray(rgba, 'RGBA')
ys, xs = np.where(a > 0.02)
pad = 6
box = (xs.min() - pad, ys.min() - pad, xs.max() + 1 + pad, ys.max() + 1 + pad)
print('box', box)
logo = full.crop(box)
# logo header: tinggi 120 px (@2x untuk 40 px tampil? kita tampil ~36-40px)
H = 120
W = round(logo.width * H / logo.height)
# resize di ruang premultiplied supaya tepi tidak kotor
def resize_rgba(img, size):
    arr = np.asarray(img).astype(float)
    al = arr[..., 3:4] / 255
    pre = np.dstack([arr[..., :3] * al, arr[..., 3:4]])
    chans = [Image.fromarray(pre[..., i].astype(np.float32), 'F').resize(size, Image.Resampling.LANCZOS) for i in range(4)]
    out = np.dstack([np.asarray(c) for c in chans])
    out = np.clip(out, 0, 255)
    al2 = out[..., 3:4] / 255
    col = np.where(al2 > 0, out[..., :3] / np.maximum(al2, 1e-6), 0)
    return Image.fromarray(np.dstack([np.clip(col, 0, 255), out[..., 3:4]]).round().astype(np.uint8), 'RGBA')
out = resize_rgba(logo, (W, H))
out.save('img/logo.png', optimize=True)
out.save('img/logo.webp', lossless=True, method=6)
print('logo', out.size)
# ikon: kaca pembesar (kolom sebelum celah pertama yang lebar)
xs_mask = np.where((a > 0.02).any(0))[0]
# cari celah >= 15 kolom
prev = xs_mask[0]; split = None
for c in xs_mask[1:]:
    if c - prev > 15:
        split = (prev, c); break
    prev = c
print('split', split)
ix1 = split[0] + 1
sub = a[:, xs.min():ix1]
iy = np.where((sub > 0.02).any(1))[0]
ib = (xs.min(), iy.min(), ix1, iy.max() + 1)
icon = full.crop(ib)
s = max(icon.size)
m = round(s * 0.06)
sq = Image.new('RGBA', (s + 2 * m, s + 2 * m), (0, 0, 0, 0))
sq.paste(icon, (m + (s - icon.width) // 2, m + (s - icon.height) // 2))
print('icon', ib, sq.size)
fav32 = resize_rgba(sq, (32, 32)); fav32.save('img/favicon-32.png', optimize=True)
big = resize_rgba(sq, (256, 256))
ico_sizes = [resize_rgba(sq, (n, n)) for n in (16, 32, 48)]
ico_sizes[2].save('favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)], append_images=ico_sizes[:2])
# apple touch: latar terang, ikon dengan margin
at = Image.new('RGBA', (180, 180), (255, 252, 248, 255))
ic = resize_rgba(sq, (150, 150))
at.alpha_composite(ic, (15, 15))
at.convert('RGB').save('img/apple-touch-icon.png', optimize=True)
big.save('/tmp/icon-256.png')
# img/logo-asli.jpg adalah sumbernya (tidak ditimpa)
prev = Image.new('RGBA', (logo.width + 80, logo.height + 80), (255, 252, 248, 255))
prev.alpha_composite(logo, (40, 40))
prev2 = Image.new('RGBA', prev.size, (31, 26, 23, 255)); prev2.alpha_composite(logo, (40, 40))
both = Image.new('RGB', (prev.width, prev.height * 2)); both.paste(prev.convert('RGB'), (0, 0)); both.paste(prev2.convert('RGB'), (0, prev.height))
both.save('/tmp/logo-preview.png')
