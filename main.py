#!/usr/bin/env python3
"""Ignition Ribbon -- draws the ai-excited-01 entry image.

One image: a satin ribbon of plasma whips across a deep violet void, twists
edge-on, and ignites a blazing knot where it crosses itself, throwing embers
and a shock-ring outward. Everything is computed, nothing is loaded: the
program is pure Python 3.13 standard library (math, zlib, struct) and writes
/output/entry.png (1024x1024 truecolour PNG under 1 MiB).

    python3 main.py                              # writes /output/entry.png
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import math
import os
import random
import struct
import zlib

W = H = 1024
KX, KY = 0.585 * W, 0.415 * H          # ignition knot: off-centre, rule of thirds

# Control points of the ribbon (Catmull-Rom through them), in pixels.
SPINE = [
    (-140.0, 1010.0),
    (120.0, 720.0),
    (410.0, 560.0),
    (700.0, 690.0),
    (930.0, 470.0),
    (760.0, 210.0),
    (470.0, 250.0),
    (330.0, 470.0),
    (470.0, 690.0),
    (820.0, 800.0),
    (1080.0, 640.0),
]


def clamp01(v):
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def catmull(pts, t):
    """Position and tangent on a Catmull-Rom spline, t in [0, 1]."""
    n = len(pts) - 1
    f = t * n
    i = min(int(f), n - 1)
    u = f - i
    p0 = pts[max(i - 1, 0)]
    p1 = pts[i]
    p2 = pts[i + 1]
    p3 = pts[min(i + 2, n)]
    u2, u3 = u * u, u * u * u
    x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u +
               (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2 +
               (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3)
    y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u +
               (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2 +
               (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3)
    dx = 0.5 * ((-p0[0] + p2[0]) + 2 * (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u +
                3 * (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u2)
    dy = 0.5 * ((-p0[1] + p2[1]) + 2 * (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u +
                3 * (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u2)
    return x, y, dx, dy


def sky():
    """Deep violet void with nebula clouds and a soft vignette (linear light)."""
    img = [0.0] * (W * H * 3)
    rng = random.Random(11)
    n = 26
    grid = [[rng.random() for _ in range(n + 1)] for _ in range(n + 1)]

    def noise(px, py):
        gx = clamp01(px / W) * n
        gy = clamp01(py / H) * n
        ix = min(int(gx), n - 1)
        iy = min(int(gy), n - 1)
        fx, fy = gx - ix, gy - iy
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        a = grid[iy][ix] + (grid[iy][ix + 1] - grid[iy][ix]) * fx
        b = grid[iy + 1][ix] + (grid[iy + 1][ix + 1] - grid[iy + 1][ix]) * fx
        return a + (b - a) * fy

    lobes = [(0.30 * W, 0.78 * H, 0.52 * W, 0.30, (0.30, 0.06, 0.34)),
             (0.86 * W, 0.16 * H, 0.40 * W, 0.22, (0.05, 0.12, 0.36)),
             (0.50 * W, 0.50 * H, 0.62 * W, 0.32, (0.20, 0.04, 0.16))]
    px_ = 0
    for y in range(H):
        for x in range(W):
            dx = x - KX
            dy = y - KY
            r = math.sqrt(dx * dx + dy * dy) / W
            k = math.exp(-(r / 0.55) ** 2)
            cr = 0.012 + 0.032 * k
            cg = 0.006 + 0.010 * k
            cb = 0.040 + 0.062 * k
            for lx, ly, lr, amp, tint in lobes:
                d = math.hypot(x - lx, y - ly) / lr
                wgt = amp * math.exp(-d * d * 1.7)
                if wgt > 0.002:
                    cr += tint[0] * wgt
                    cg += tint[1] * wgt
                    cb += tint[2] * wgt
            g = noise(x * 0.9 + 40, y * 0.9 - 25) - 0.5
            g += 0.5 * (noise(x * 2.3 - 60, y * 2.3 + 90) - 0.5)
            cloud = g * 0.11 * math.exp(-(r / 0.55) ** 2)
            cr += cloud * 0.9
            cg += cloud * 0.35
            cb += cloud * 1.0
            vx = (x - 0.5 * W) / (0.5 * W)
            vy = (y - 0.5 * H) / (0.5 * H)
            vig = 1.0 - 0.42 * clamp01((vx * vx + vy * vy) * 0.62)
            img[px_] = max(cr * vig, 0.0)
            img[px_ + 1] = max(cg * vig, 0.0)
            img[px_ + 2] = max(cb * vig, 0.0)
            px_ += 3
    return img


def add(img, x, y, r, g, b):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        img[i] += r
        img[i + 1] += g
        img[i + 2] += b


def splat(img, x, y, r, g, b, rad=1.0):
    """Bilinear-weighted additive splat: the antialiasing for every stroke."""
    ix, iy = int(x), int(y)
    fx, fy = x - ix, y - iy
    for oy in (0, 1):
        wy = fy if oy else 1.0 - fy
        for ox in (0, 1):
            wx = fx if ox else 1.0 - fx
            w = wx * wy
            if w > 0.004:
                add(img, ix + ox, iy + oy, r * w * rad, g * w * rad, b * w * rad)


def ribbon(img):
    """The plasma ribbon: a tapered, twisting satin band with a hot core."""
    steps = 5200
    for s in range(steps + 1):
        t = s / steps
        x, y, dx, dy = catmull(SPINE, t)
        ln = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        env = math.sin(math.pi * clamp01(t)) ** 0.55
        twist = math.cos(t * math.pi * 5.2 - 0.6)
        width = (2.0 + 26.0 * env) * (0.34 + 0.66 * abs(twist))
        flare = 0.45 + 0.9 * (1.0 - abs(twist))
        heat = clamp01(0.30 + 0.85 * env * (0.45 + 0.55 * abs(twist)))
        hue = clamp01(t * 1.15 - 0.05)
        if hue < 0.5:
            k = hue / 0.5
            edge = (0.22 + 0.55 * k, 0.55 + 0.10 * k, 0.95 - 0.25 * k)
        else:
            k = (hue - 0.5) / 0.5
            edge = (0.77 + 0.20 * k, 0.65 - 0.30 * k, 0.70 - 0.60 * k)
        usteps = max(3, int(width * 2.2))
        for j in range(usteps + 1):
            u = (j / usteps) * 2.0 - 1.0
            au = abs(u)
            px = x + nx * u * width
            py = y + ny * u * width
            core = math.exp(-(au / 0.42) ** 2)
            rim = math.exp(-((au - 0.80) / 0.16) ** 2) * 0.55
            body = 0.16 * (1.0 - au)
            if body < 0:
                body = 0.0
            wgt = (core * flare + rim + body) * env
            if wgt < 0.012:
                continue
            hc = heat * wgt
            r = (edge[0] * 0.95 + 0.55 * core) * hc * 1.05
            g = (edge[1] * 0.95 + 0.42 * core) * hc * 1.00
            b = (edge[2] * 0.95 + 0.38 * core) * hc * 1.10
            splat(img, px, py, r, g, b, 1.0)


def knot(img):
    """Ignition: a white-hot point where the ribbon crosses itself."""
    rng = random.Random(3)
    rad = 46
    for oy in range(-rad, rad + 1):
        for ox in range(-rad, rad + 1):
            d = math.hypot(ox, oy) / rad
            if d > 1.0:
                continue
            f = (1.0 - d) ** 2.1
            hot = math.exp(-(d / 0.30) ** 2)
            add(img, int(KX) + ox, int(KY) + oy,
                3.4 * f + 2.6 * hot, 3.0 * f + 2.3 * hot, 2.4 * f + 1.9 * hot)
    # radial cracks: jagged filaments of light from the core
    for _ in range(26):
        a = rng.uniform(0, 2 * math.pi)
        ln = rng.uniform(38, 132)
        w = rng.uniform(0.7, 1.9)
        bend = rng.uniform(-0.22, 0.22)
        for s in range(int(ln)):
            aa = a + bend * (s / ln)
            x = KX + s * math.cos(aa)
            y = KY + s * math.sin(aa) * 0.96
            fall = (1.0 - s / ln) ** 1.7
            splat(img, x, y, 1.9 * fall, 1.55 * fall, 1.25 * fall, w)
    # shock ring, thin and slightly elliptical, still expanding
    for s in range(720):
        a = 2 * math.pi * s / 720
        rr = 168 + 7 * math.sin(a * 3.0 + 0.4)
        x = KX + rr * math.cos(a)
        y = KY + rr * 0.93 * math.sin(a)
        f = 0.30 + 0.22 * math.sin(a * 5.0)
        splat(img, x, y, 0.55 * f, 0.42 * f, 0.60 * f, 1.0)


def embers(img):
    """Sparks thrown off the ribbon: streaks with direction, so it is moving."""
    rng = random.Random(91)
    for _ in range(360):
        t = min(max(rng.gauss(0.62, 0.24), 0.0), 1.0)
        x, y, dx, dy = catmull(SPINE, t)
        ln = math.hypot(dx, dy) or 1.0
        dx, dy = dx / ln, dy / ln
        side = 1.0 if rng.random() < 0.5 else -1.0
        ang = math.atan2(dy, dx) + side * rng.uniform(1.35, 2.05)
        speed = rng.uniform(14, 120)
        ox = math.cos(ang) * rng.uniform(0, 26)
        oy = math.sin(ang) * rng.uniform(0, 26)
        steps = int(speed)
        life = rng.uniform(0.45, 1.0)
        hot = rng.random()
        for s in range(steps):
            f = (1.0 - s / steps) ** 1.6 * life
            px = x + ox + math.cos(ang) * s
            py = y + oy + math.sin(ang) * s * 0.97
            if hot > 0.72:
                splat(img, px, py, 1.9 * f, 1.35 * f, 0.55 * f, 1.0)
            else:
                splat(img, px, py, 1.45 * f, 0.75 * f, 1.35 * f, 1.0)
    # a few dozen heavier sparks with fat heads
    for _ in range(46):
        ang = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(90, 420)
        x = KX + rr * math.cos(ang)
        y = KY + rr * 0.95 * math.sin(ang)
        l = rng.uniform(8, 34)
        f = rng.uniform(0.5, 1.0)
        for s in range(int(l)):
            k = (1.0 - s / l) ** 1.4 * f
            splat(img, x + math.cos(ang) * s, y + math.sin(ang) * s, 2.6 * k, 1.7 * k, 1.1 * k, 1.6)


def silhouette(img):
    """A tiny figure on a dark ridge, arms raised to the light: the scale beat."""
    rng = random.Random(17)
    fx, fy = 0.20 * W, 0.885 * H          # feet on the ridge
    hgt = 46                              # ~4.5% of frame: small but readable
    # the ridge: a dark slope the figure stands on
    for y in range(int(fy) - 6, H):
        wob = 8 * math.sin((y - fy) * 0.05 + 1.2)
        for x in range(0, W):
            d = abs(x - fx) - (y - fy) * 2.6 - wob
            if d < 90:
                i = (y * W + x) * 3
                img[i] *= 0.10
                img[i + 1] *= 0.08
                img[i + 2] *= 0.16
    # figure: head, body, two raised arms, legs; pure dark against the glow
    hx, hy = fx, fy - hgt * 0.86
    hr = hgt * 0.115
    body_top = fy - hgt * 0.72
    def dark(x, y):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            img[i] *= 0.06
            img[i + 1] *= 0.05
            img[i + 2] *= 0.10
    for oy in range(-int(hr) - 1, int(hr) + 2):
        for ox in range(-int(hr) - 1, int(hr) + 2):
            if ox * ox + oy * oy <= hr * hr:
                dark(int(hx + ox), int(hy + oy))
    bw = hgt * 0.13
    for y in range(int(body_top), int(fy - hgt * 0.30)):
        for x in range(int(hx - bw), int(hx + bw) + 1):
            dark(x, y)
    # raised arms: from shoulders up and out
    for sgn in (-1, 1):
        for s in range(int(hgt * 0.42)):
            t = s / (hgt * 0.42)
            ax = hx + sgn * (hgt * 0.10 + t * hgt * 0.30)
            ay = body_top + hgt * 0.06 - t * hgt * 0.34
            for oy in range(-1, 2):
                for ox in range(-1, 2):
                    dark(int(ax + ox), int(ay + oy))
    # legs
    for sgn in (-1, 1):
        for s in range(int(hgt * 0.30)):
            lx = hx + sgn * hgt * 0.07
            ly = fy - hgt * 0.30 + s
            for oy in range(0, 2):
                for ox in range(-1, 2):
                    dark(int(lx + ox), int(ly + oy))


def stars(img):
    """Sparse stars in the dark corners, a handful with cross flares."""
    rng = random.Random(5)
    for _ in range(420):
        x = rng.randrange(W)
        y = rng.randrange(H)
        dx, dy = (x - 0.5 * W) / W, (y - 0.5 * H) / H
        if (dx * dx + dy * dy) < 0.045:
            continue
        b = rng.random() ** 2.6
        v = 0.10 + 0.85 * b
        add(img, x, y, v, v * 0.96, v * 1.05)
        if b > 0.72:
            for d in range(1, 7):
                g = (1.0 - d / 7.0) ** 2 * 0.55
                for xx, yy in ((x + d, y), (x - d, y), (x, y + d), (x, y - d)):
                    add(img, xx, yy, g, g * 0.9, g)


def blur1d(src, w, h, radius, passes=3):
    """Separable box blur on a float channel (runs tiny, so cost is nothing)."""
    a = list(src)
    for _ in range(passes):
        out = [0.0] * len(a)
        for y in range(h):
            row = y * w
            acc = 0.0
            for x in range(-radius, radius + 1):
                acc += a[row + min(max(x, 0), w - 1)]
            k = 1.0 / (2 * radius + 1)
            for x in range(w):
                out[row + x] = acc * k
                acc -= a[row + min(max(x - radius, 0), w - 1)]
                acc += a[row + min(max(x + radius + 1, 0), w - 1)]
        for x in range(w):
            acc = 0.0
            for y in range(-radius, radius + 1):
                acc += out[min(max(y, 0), h - 1) * w + x]
            k = 1.0 / (2 * radius + 1)
            for y in range(h):
                a[y * w + x] = acc * k
                acc -= out[min(max(y - radius, 0), h - 1) * w + x]
                acc += out[min(max(y + radius + 1, 0), h - 1) * w + x]
    return a


def glow(img):
    """Wide atmospheric bloom: downsample, blur at two scales, add back."""
    gw = gh = 256
    small = [0.0] * (gw * gh * 3)
    step = W // gw
    for y in range(gh):
        for x in range(gw):
            sr = sg = sb = 0.0
            for oy in range(step):
                row = ((y * step + oy) * W + x * step) * 3
                for ox in range(step):
                    i = row + ox * 3
                    sr += img[i]
                    sg += img[i + 1]
                    sb += img[i + 2]
            inv = 1.0 / (step * step)
            j = (y * gw + x) * 3
            small[j] = sr * inv
            small[j + 1] = sg * inv
            small[j + 2] = sb * inv
    near_c = [blur1d([small[i] for i in range(c, len(small), 3)], gw, gh, 2, 3)
              for c in range(3)]
    hw = hh = 64
    far_c = []
    for c in range(3):
        ch = near_c[c]
        down = [0.0] * (hw * hh)
        for y in range(hh):
            for x in range(hw):
                s = 0.0
                for oy in range(4):
                    for ox in range(4):
                        s += ch[(y * 4 + oy) * gw + x * 4 + ox]
                down[y * hw + x] = s * 0.0625
        far_c.append(blur1d(down, hw, hh, 3, 3))
    # composite: bilinear upsample so the wide bloom carries no blockiness
    for y in range(H):
        gy = (y + 0.5) * gh / H - 0.5
        iy = min(int(gy), gh - 2)
        wy = gy - iy
        fyi = (y + 0.5) * hh / H - 0.5
        jy = min(int(fyi), hh - 2)
        wyf = fyi - jy
        row_n0 = iy * gw
        row_n1 = (iy + 1) * gw
        row_f0 = jy * hw
        row_f1 = (jy + 1) * hw
        for x in range(W):
            gx = (x + 0.5) * gw / W - 0.5
            ix = min(int(gx), gw - 2)
            wx = gx - ix
            w00 = (1 - wx) * (1 - wy)
            w10 = wx * (1 - wy)
            w01 = (1 - wx) * wy
            w11 = wx * wy
            j00 = row_n0 + ix
            j10 = j00 + 1
            j01 = row_n1 + ix
            j11 = j01 + 1
            fx2 = (x + 0.5) * hw / W - 0.5
            jx = min(int(fx2), hw - 2)
            wxf = fx2 - jx
            f00 = (1 - wxf) * (1 - wyf)
            f10 = wxf * (1 - wyf)
            f01 = (1 - wxf) * wyf
            f11 = wxf * wyf
            g00 = row_f0 + jx
            g10 = g00 + 1
            g01 = row_f1 + jx
            g11 = g01 + 1
            i = (y * W + x) * 3
            for c in range(3):
                near = (near_c[c][j00] * w00 + near_c[c][j10] * w10 +
                        near_c[c][j01] * w01 + near_c[c][j11] * w11)
                far = (far_c[c][g00] * f00 + far_c[c][g10] * f10 +
                       far_c[c][g01] * f01 + far_c[c][g11] * f11)
                img[i + c] += near * (0.55, 0.45, 0.75)[c] + far * (0.55, 0.40, 0.65)[c]


def tonemap(img):
    """Filmic rolloff so highlights bloom to white instead of clipping flat."""
    rng = random.Random(77)
    out = bytearray(W * H * 3)
    for i in range(0, len(img), 3):
        for c in range(3):
            v = img[i + c]
            if v <= 0.0:
                q = 0.0
            else:
                q = 1.0 - math.exp(-v * 1.16)
                q = q ** (1.0 / 1.06)
            n = int(q * 255.0 + (rng.random() - 0.5) * 0.4 + 0.5)
            out[i + c] = 0 if n < 0 else (255 if n > 255 else n)
    return out


def write_png(path, rgb):
    """Truecolour PNG writer: adaptive row filters, one zlib stream, checksums."""
    def chunk(tag, data):
        return (struct.pack('>I', len(data)) + tag + data +
                struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF))

    stride = W * 3
    prev = bytearray(stride)
    raw = bytearray()
    for y in range(H):
        row = rgb[y * stride:(y + 1) * stride]
        # pick the filter with the smallest sum of absolute residuals
        best = None
        best_i = 1
        best_cost = None
        for ft in range(5):
            cand = bytearray(stride)
            if ft == 0:
                cand[:] = row
            elif ft == 2:
                for i in range(stride):
                    cand[i] = (row[i] - prev[i]) & 0xFF
            elif ft == 1:
                for i in range(stride):
                    cand[i] = (row[i] - (row[i - 3] if i >= 3 else 0)) & 0xFF
            elif ft == 3:
                for i in range(stride):
                    left = row[i - 3] if i >= 3 else 0
                    cand[i] = (row[i] - ((left + prev[i]) >> 1)) & 0xFF
            else:
                for i in range(stride):
                    a = row[i - 3] if i >= 3 else 0
                    b = prev[i]
                    c = prev[i - 3] if i >= 3 else 0
                    p = a + b - c
                    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                    pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                    cand[i] = (row[i] - pr) & 0xFF
            cost = sum(v if v < 128 else 256 - v for v in cand)
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best = cand
                best_i = ft
        raw.append(best_i)
        raw += best
        prev = row
    png = (b'\x89PNG\r\n\x1a\n' +
           chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(bytes(raw), 9)) +
           chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    img = sky()
    ribbon(img)
    knot(img)
    embers(img)
    stars(img)
    silhouette(img)
    glow(img)
    png = write_png(os.path.join(out_dir, 'entry.png'), tonemap(img))
    print('wrote entry.png (%dx%d, %d bytes)' % (W, H, png))


if __name__ == '__main__':
    main()
