#!/usr/bin/env python3
"""Generate test PNGs (valid, exotic, and deliberately broken) for PNG.bt."""
import struct, zlib, os

OUT = os.path.join(os.path.dirname(__file__), "testfiles")
os.makedirs(OUT, exist_ok=True)

def chunk(ctype: bytes, data: bytes = b"", bad_crc=False) -> bytes:
    return (struct.pack(">I", len(data)) + ctype + data +
            struct.pack(">I", zlib.crc32(ctype + data) ^ (0xDEADBEEF if bad_crc else 0)))

SIG = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])

def ihdr(w, h, depth=8, ct=2):
    return chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, depth, ct, 0, 0, 0))

def idat_rgb(w, h):
    raw = b"".join(b"\x00" + bytes([ (x*7)%256, (y*11)%256, (x^y)%256 ])
                   for y in range(h) for x in range(w))
    return chunk(b"IDAT", zlib.compress(raw))

def idat_pal(w, h):
    raw = b"".join(b"\x00" + bytes([(x + y) % 4]) for y in range(h) for x in range(w))
    return chunk(b"IDAT", zlib.compress(raw))

PLTE = chunk(b"PLTE", bytes([255,0,0, 0,255,0, 0,0,255, 255,255,0]))

# 1. minimal valid RGB png
with open(f"{OUT}/1_normal.png", "wb") as f:
    f.write(SIG + ihdr(8, 8) + idat_rgb(8, 8) + chunk(b"IEND"))

# 2. kitchen-sink palette png: gAMA cHRM sRGB sBIT tEXt zTXt iTXt tIME pHYs
#    PLTE tRNS bKGD hIST sPLT iCCP eXIf oFFs sCAL caNv IDAT IEND
iccp_profile = zlib.compress(b"fake icc profile data for testing " * 4)
with open(f"{OUT}/2_full.png", "wb") as f:
    f.write(SIG
        + ihdr(8, 8, ct=3)
        + chunk(b"gAMA", struct.pack(">I", 45455))
        + chunk(b"cHRM", struct.pack(">8I", 31270, 32900, 64000, 33000, 30000, 60000, 15000, 6000))
        + chunk(b"sRGB", b"\x00")
        + chunk(b"sBIT", b"\x02\x02\x02")
        + chunk(b"pHYs", struct.pack(">IIB", 2835, 2835, 1))
        + chunk(b"tIME", struct.pack(">HBBBBB", 2026, 10, 19, 12, 34, 56))
        + chunk(b"tEXt", b"Title\x00CTF template test image")
        + chunk(b"tEXt", b"Comment\x00Trailing junk after this chunk is a secret")
        + chunk(b"zTXt", b"Secret\x00\x00" + zlib.compress(b"hidden in compressed text 123"))
        + chunk(b"iTXt", b"Key\x00\x00\x00en\x00Key\x00international text here")
        + chunk(b"iTXt", b"ZKey\x00\x01\x00en\x00K\x00" + zlib.compress(b"compressed international"))
        + PLTE
        + chunk(b"tRNS", b"\x00\x40\x80")
        + chunk(b"bKGD", b"\x01")
        + chunk(b"hIST", struct.pack(">4H", 100, 200, 300, 400))
        + chunk(b"sPLT", b"main\x00\x08" + bytes([9,9,9,255]) + struct.pack(">H", 1)
                                 + bytes([1,2,3,128]) + struct.pack(">H", 2))
        + chunk(b"iCCP", b"icc\x00\x00" + iccp_profile)
        + chunk(b"eXIf", b"MM\x00\x2a\x00\x00\x00\x08\x00\x00")
        + chunk(b"oFFs", struct.pack(">iiB", 10, 20, 0))
        + chunk(b"sCAL", b"\x00" + b"1.5\x00" + b"2.5")
        + chunk(b"caNv", struct.pack(">4i", 1, 2, 3, 4))
        + chunk(b"cICP", bytes([9, 16, 0, 1]))
        + chunk(b"mDCv", struct.pack(">8HII", 13250, 34500, 7500, 3000, 34000, 16000, 15635, 16450, 10000000, 1))
        + chunk(b"cLLi", struct.pack(">II", 10000000, 4000))
        + idat_pal(8, 8)
        + chunk(b"IEND"))

# 3. valid png + flag text + zip appended after IEND
flag = b"\nflag{you_found_me_after_IEND}\n"
zipdata = b"PK\x03\x04" + b"\x14\x00\x00\x00\x00\x00" + b"secret.txt" + b"ZIP-with-hidden-file-payload"
with open(f"{OUT}/3_trailing.png", "wb") as f:
    f.write(SIG + ihdr(8, 8) + idat_rgb(8, 8) + chunk(b"IEND") + flag + zipdata)

# 4. junk before the signature (signature at offset 32)
junk = b"this file is definitely not a GIF89a... or is it?" .ljust(32, b".")
with open(f"{OUT}/4_prepended.png", "wb") as f:
    f.write(junk + SIG + ihdr(8, 8) + idat_rgb(8, 8) + chunk(b"IEND"))

# 5. APNG-style: acTL + fcTL + fdAT
fctl = struct.pack(">IIIIIHHBB", 0, 8, 8, 0, 0, 5, 10, 0, 0)
with open(f"{OUT}/5_apng.png", "wb") as f:
    f.write(SIG + ihdr(8, 8)
        + chunk(b"acTL", struct.pack(">II", 2, 0))
        + chunk(b"fcTL", fctl)
        + idat_rgb(8, 8)
        + chunk(b"fcTL", struct.pack(">IIIIIHHBB", 1, 8, 8, 0, 0, 5, 0, 1, 1))
        + chunk(b"fdAT", struct.pack(">I", 2) + zlib.compress(b"\x00" + b"\x11" * 24))
        + chunk(b"IEND"))

# 6. corrupted CRC on tEXt + unknown critical chunk
unk = chunk(b"crXt", b"private data with flag{custom_chunk_secret}")
with open(f"{OUT}/6_badcrc.png", "wb") as f:
    f.write(SIG + ihdr(8, 8)
        + chunk(b"tEXt", b"Note\x00this chunk has a broken CRC", bad_crc=True)
        + idat_rgb(8, 8)
        + unk
        + chunk(b"IEND"))

# 7. truncated in the middle of IDAT
good = SIG + ihdr(8, 8) + idat_rgb(64, 64)
with open(f"{OUT}/7_truncated.png", "wb") as f:
    f.write(good[: len(good) - 40])

# 8. junk of 5 bytes at the end (incomplete chunk header) + text after IEND via chunk
with open(f"{OUT}/8_tailjunk.png", "wb") as f:
    f.write(SIG + ihdr(8, 8) + idat_rgb(8, 8) + chunk(b"IEND")
            + b"flag" + b"\x00\x00\x00\x08abc" + b"hidden-raw-tail-text!!")

# 9. plain flag text appended directly after IEND (misc5 style)
with open(f"{OUT}/9_flagtext.png", "wb") as f:
    f.write(SIG + ihdr(8, 8) + idat_rgb(8, 8) + chunk(b"IEND")
            + b"flag{2a476b4011805f1a8e4b906c8f84083e}")

# 10. a complete second PNG embedded after IEND (misc8 style)
second = SIG + ihdr(4, 4) + idat_rgb(4, 4) + chunk(b"IEND")
with open(f"{OUT}/10_embedded.png", "wb") as f:
    f.write(SIG + ihdr(8, 8) + idat_rgb(8, 8) + chunk(b"IEND") + second)

# 11. iTXt with empty language tag + empty translated keyword, tEXt with
#     empty keyword (zero-size array edge cases, misc9 style)
with open(f"{OUT}/11_emptylang.png", "wb") as f:
    f.write(SIG + ihdr(8, 8)
        + chunk(b"iTXt", b"Key\x00\x00\x00\x00\x00text here")          # lang="" translated=""
        + chunk(b"iTXt", b"K2\x00\x01\x00\x00\x00" + zlib.compress(b"zz"))  # compressed, lang="" translated=""
        + chunk(b"tEXt", b"\x00value with empty keyword")
        + chunk(b"zTXt", b"\x00\x00" + zlib.compress(b"empty keyword ztxt"))
        + idat_rgb(8, 8)
        + chunk(b"IEND"))

print("written to", OUT)
for name in sorted(os.listdir(OUT)):
    print(" ", name, os.path.getsize(os.path.join(OUT, name)), "bytes")
