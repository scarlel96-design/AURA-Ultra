"""Inspect opaque 8-bit RGB/RGBA PNG captures of the basic Signature face."""
import argparse
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path

from round_layout import ROOT, SOURCE, DIAMETERS, parse, project_layout

PNG = b"\x89PNG\r\n\x1a\n"
MAX_FILE = 4 * 1024 * 1024
AOD_PERCENT = 10


def paeth(a, b, c):
    p = a + b - c
    da, db, dc = abs(p-a), abs(p-b), abs(p-c)
    return a if da <= db and da <= dc else b if db <= dc else c


def decode_png(data, diameter):
    """Decode a bounded PNG subset. Reject unsupported capture encodings."""
    if type(diameter) is not int or diameter not in DIAMETERS:
        raise ValueError("Unsupported diameter")
    if len(data) > MAX_FILE or not data.startswith(PNG):
        raise ValueError("Invalid PNG signature or size")
    pos, channels, idat, ended, closed = 8, None, bytearray(), False, False
    while pos < len(data):
        if pos + 12 > len(data):
            raise ValueError("Truncated PNG chunk")
        size = struct.unpack_from(">I", data, pos)[0]
        kind = data[pos+4:pos+8]
        end = pos+12+size
        if end > len(data):
            raise ValueError("Truncated PNG payload")
        payload = data[pos+8:end-4]
        if zlib.crc32(kind+payload) != struct.unpack_from(">I", data, end-4)[0]:
            raise ValueError("PNG CRC mismatch")
        if channels is None:
            if kind != b"IHDR" or size != 13:
                raise ValueError("Missing PNG header")
            w,h,depth,color,compression,filtering,interlace = struct.unpack(">IIBBBBB", payload)
            if (w,h) != (diameter,diameter):
                raise ValueError("Capture dimensions mismatch")
            if depth != 8 or color not in (2,6) or (compression,filtering,interlace) != (0,0,0):
                raise ValueError("Unsupported PNG format")
            channels = 3 if color == 2 else 4
        elif kind == b"IDAT":
            if closed:
                raise ValueError("Non-consecutive IDAT")
            idat.extend(payload)
        elif kind == b"IEND":
            if size or not idat or end != len(data):
                raise ValueError("Invalid PNG end")
            ended = True
            break
        else:
            # Reject animation, transparency and unknown critical chunks.
            if kind in (b"IHDR",b"tRNS",b"acTL",b"fcTL",b"fdAT") or not kind[0] & 32:
                raise ValueError("Unsupported PNG chunk")
            if idat:
                closed = True
        pos = end
    if not ended:
        raise ValueError("Missing PNG end")
    stride = diameter * channels
    expected = (stride+1)*diameter
    inflater = zlib.decompressobj()
    try:
        raw = inflater.decompress(idat, expected+1)
    except zlib.error as exc:
        raise ValueError("Invalid compressed PNG") from exc
    if len(raw) != expected or not inflater.eof or inflater.unused_data or inflater.unconsumed_tail:
        raise ValueError("PNG decompressed size or stream mismatch")
    previous = bytearray(stride)
    for y in range(diameter):
        start = y*(stride+1)
        filt = raw[start]
        row = bytearray(raw[start+1:start+1+stride])
        if filt > 4:
            raise ValueError("Invalid PNG filter")
        for i in range(stride):
            a = row[i-channels] if i >= channels else 0
            b = previous[i]
            c = previous[i-channels] if i >= channels else 0
            if filt:
                delta = (a, b, (a+b)//2, paeth(a,b,c))[filt-1]
                row[i] = (row[i]+delta)&255
        if channels == 4 and any(a != 255 for a in row[3::4]):
            raise ValueError("Capture must be opaque")
        yield row, channels
        previous = row


def inspect(data, diameter, mode, hour_format, layout):
    if mode not in ("active","ambient") or type(hour_format) is not int or hour_format not in (12,24):
        raise ValueError("Invalid capture mode or hour format")
    boxes = project_layout(layout, diameter)["regions"]
    required = set(boxes) if mode == "active" else {"date","time","ampm"}
    if hour_format == 24:
        required.remove("ampm")
    counts = {name: 0 for name in sorted(required)}
    circle = lit = outside_circle = outside_regions = 0
    for y,(row,channels) in enumerate(decode_png(data,diameter)):
        spans = [(name,x,x+w) for name,(x,top,w,h) in boxes.items()
                 if name in required and top <= y < top+h]
        for x in range(diameter):
            inside = (2*x+1-diameter)**2+(2*y+1-diameter)**2 <= diameter**2
            circle += inside
            i = x*channels
            if not any(row[i:i+3]):
                continue
            if not inside:
                outside_circle += 1
                continue
            lit += 1
            region = next((name for name,left,right in spans if left <= x < right),None)
            if region is None:
                outside_regions += 1
            else:
                counts[region] += 1
    missing = [name for name,n in counts.items() if not n]
    failures = []
    if outside_circle:
        failures.append("nonblack pixels outside round display")
    if outside_regions:
        failures.append("nonblack pixels outside expected text regions")
    if missing:
        failures.append("missing region pixels: " + ", ".join(missing))
    if mode == "ambient" and lit*100 > AOD_PERCENT*circle:
        failures.append("ambient nonblack pixel budget exceeded")
    return {"schemaVersion": 1, "scope": "basic candidate capture pixel check; not runtime provenance, OCR or power",
            "sha256": hashlib.sha256(data).hexdigest(), "diameter":diameter, "mode":mode,
            "hourFormat":hour_format, "circlePixels":circle, "nonblackPixels":lit,
            "nonblackPercent":round(lit*100/circle,6), "outsideCirclePixels":outside_circle,
            "outsideRegionPixels":outside_regions, "regionPixels":counts,
            "ambientLimitPercent":AOD_PERCENT if mode=="ambient" else None,
            "failures":failures, "result":"FAIL" if failures else "PASS"}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("capture", type=Path)
    p.add_argument("--diameter", type=int, choices=DIAMETERS, required=True)
    p.add_argument("--mode", choices=("active","ambient"), required=True)
    p.add_argument("--hour-format", type=int, choices=(12,24), required=True)
    args = p.parse_args()
    try:
        with args.capture.open("rb") as stream:
            data = stream.read(MAX_FILE+1)
        report = inspect(data,args.diameter,args.mode,args.hour_format,parse((ROOT/SOURCE).read_bytes()))
        print(json.dumps(report,sort_keys=True))
        return int(report["result"] != "PASS")
    except (OSError,ValueError) as exc:
        print(json.dumps({"result":"FAIL","error":str(exc)},sort_keys=True),file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
