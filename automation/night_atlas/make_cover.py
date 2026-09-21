#!/usr/bin/env python3
"""Generate a deterministic 1400x1400 Night Atlas PNG using only stdlib."""
from __future__ import annotations

import argparse
import binascii
import math
import random
import struct
import zlib
from pathlib import Path

W = H = 1400
FONT = {
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "G": ["01111","10000","10000","10111","10001","10001","01110"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    " ": ["00000"] * 7,
}


def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def setpx(buf: bytearray, x: int, y: int, colour: tuple[int, int, int]):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i+3] = bytes(colour)


def circle(buf: bytearray, cx: int, cy: int, radius: int, colour: tuple[int, int, int]):
    r2 = radius * radius
    for y in range(max(0, cy-radius), min(H, cy+radius+1)):
        dy2 = (y-cy) * (y-cy)
        span = int(math.sqrt(max(0, r2-dy2)))
        start = max(0, cx-span)
        end = min(W-1, cx+span)
        row = (y * W + start) * 3
        pixel = bytes(colour)
        for _ in range(start, end+1):
            buf[row:row+3] = pixel
            row += 3


def text_width(text: str, scale: int) -> int:
    return sum((5 * scale) + scale for _ in text) - scale


def draw_text(buf: bytearray, text: str, y: int, scale: int, colour: tuple[int,int,int]):
    x = (W - text_width(text, scale)) // 2
    for ch in text:
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    for yy in range(scale):
                        for xx in range(scale):
                            setpx(buf, x + gx*scale + xx, y + gy*scale + yy, colour)
        x += 6 * scale


def build(output: Path):
    buf = bytearray(W * H * 3)

    # Deep blue night gradient.
    for y in range(H):
        t = y / (H - 1)
        c = (
            int(4 + 5*t),
            int(15 + 30*t),
            int(35 + 42*t),
        )
        start = y * W * 3
        buf[start:start + W*3] = bytes(c) * W

    rng = random.Random(1042)
    for _ in range(390):
        x = rng.randrange(40, W-40)
        y = rng.randrange(35, 720)
        b = rng.randrange(170, 256)
        setpx(buf, x, y, (b, b, min(255, b+12)))
        if rng.random() < 0.12:
            setpx(buf, x+1, y, (b, b, b))
            setpx(buf, x-1, y, (b, b, b))
            setpx(buf, x, y+1, (b, b, b))
            setpx(buf, x, y-1, (b, b, b))

    # Crescent moon.
    circle(buf, 700, 330, 125, (224, 242, 250))
    circle(buf, 748, 302, 118, (5, 24, 49))

    # Mountain layers.
    for x in range(W):
        ridge1 = int(905 - 170*math.exp(-((x-700)/260)**2) - 85*math.exp(-((x-320)/160)**2) - 65*math.exp(-((x-1110)/190)**2))
        ridge2 = int(1030 - 125*math.exp(-((x-820)/330)**2) - 60*math.exp(-((x-180)/220)**2))
        for y in range(max(0, ridge1), H):
            setpx(buf, x, y, (7, 27, 42))
        for y in range(max(0, ridge2), H):
            setpx(buf, x, y, (4, 18, 29))

    # Lake glow.
    for y in range(1040, H):
        t = (y-1040)/(H-1040)
        for x in range(W):
            glow = max(0.0, 1 - abs(x-700)/700)
            c = (4, int(21 + 18*glow*(1-t)), int(34 + 34*glow*(1-t)))
            setpx(buf, x, y, c)

    draw_text(buf, "NIGHT ATLAS", 575, 17, (238, 246, 249))

    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        start = y * stride
        raw.extend(buf[start:start+stride])

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(png)
    print(f"Night Atlas cover written to {output} ({len(png)} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
