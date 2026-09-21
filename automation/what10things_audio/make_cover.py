#!/usr/bin/env python3
"""Generate deterministic 1400x1400 What10Things Audio cover art using stdlib."""
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
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "G": ["01111","10000","10000","10111","10001","10001","01110"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "W": ["10001","10001","10001","10101","10101","10101","01010"],
    " ": ["00000"] * 7,
}


def chunk(kind: bytes, data: bytes) -> bytes:
    crc = binascii.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def setpx(buf: bytearray, x: int, y: int, colour: tuple[int, int, int]):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i+3] = bytes(colour)


def rect(buf: bytearray, x1: int, y1: int, x2: int, y2: int, colour: tuple[int,int,int]):
    x1=max(0,x1); y1=max(0,y1); x2=min(W,x2); y2=min(H,y2)
    pixel=bytes(colour)
    for y in range(y1,y2):
        start=(y*W+x1)*3
        buf[start:start+(x2-x1)*3]=pixel*(x2-x1)


def text_width(text: str, scale: int) -> int:
    return sum(6 * scale for _ in text) - scale


def draw_text(buf: bytearray, text: str, y: int, scale: int, colour: tuple[int,int,int]):
    x=(W-text_width(text,scale))//2
    for ch in text:
        glyph=FONT[ch]
        for gy,row in enumerate(glyph):
            for gx,bit in enumerate(row):
                if bit=="1":
                    rect(buf,x+gx*scale,y+gy*scale,x+(gx+1)*scale,y+(gy+1)*scale,colour)
        x += 6*scale


def build(output: Path):
    buf=bytearray(W*H*3)
    for y in range(H):
        t=y/(H-1)
        c=(int(6+8*t),int(18+28*t),int(35+45*t))
        start=y*W*3
        buf[start:start+W*3]=bytes(c)*W

    rng=random.Random(1010)
    for _ in range(260):
        x=rng.randrange(40,W-40); y=rng.randrange(60,560)
        b=rng.randrange(120,220)
        setpx(buf,x,y,(b,b,min(255,b+20)))

    # Golden ten-bar motif and quiet audio waveform.
    for i in range(10):
        x=235+i*95
        height=120+int(65*math.sin((i+1)*0.9)**2)
        rect(buf,x,335-height//2,x+48,335+height//2,(219,184,92))
    for i in range(80):
        x=150+i*14
        amp=int(35+55*math.sin(i*0.31)**2)
        rect(buf,x,1040-amp,x+5,1040+amp,(116,154,181))

    draw_text(buf,"WHAT10THINGS",610,14,(245,247,250))
    draw_text(buf,"AUDIO",785,22,(219,184,92))

    raw=bytearray()
    stride=W*3
    for y in range(H):
        raw.append(0)
        start=y*stride
        raw.extend(buf[start:start+stride])

    png=b"\x89PNG\r\n\x1a\n"
    png+=chunk(b"IHDR",struct.pack(">IIBBBBB",W,H,8,2,0,0,0))
    png+=chunk(b"IDAT",zlib.compress(bytes(raw),9))
    png+=chunk(b"IEND",b"")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(png)
    print(f"What10Things Audio cover written to {output} ({len(png)} bytes)")


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    build(args.output)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
