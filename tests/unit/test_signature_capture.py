"""Exercise the capture checker with synthetic PNGs, not runtime evidence."""
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from check_signature_capture import PNG, decode_png, inspect, paeth
from round_layout import ROOT, SOURCE, DIAMETERS, parse, project_layout


def chunk(kind,data):
    return struct.pack(">I",len(data))+kind+data+struct.pack(">I",zlib.crc32(kind+data))


def png(size, points, channels=3, filt=0, alpha=255):
    raw = bytearray()
    previous = bytearray(size*channels)
    for y in range(size):
        row = bytearray()
        for x in range(size):
            row.extend((1,0,0) if (x,y) in points else (0,0,0))
            if channels == 4:
                row.append(alpha)
        raw.append(filt)
        for i,value in enumerate(row):
            a = row[i-channels] if i>=channels else 0
            b = previous[i]
            c = previous[i-channels] if i>=channels else 0
            delta = (0,a,b,(a+b)//2,paeth(a,b,c))[filt]
            raw.append((value-delta)&255)
        previous = row
    return PNG+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,2 if channels==3 else 6,0,0,0))+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b"")


class CaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = parse((ROOT/SOURCE).read_bytes())

    def points(self,size,mode="ambient",hour=24):
        boxes=project_layout(self.layout,size)["regions"]
        names=set(boxes) if mode=="active" else {"time","date","ampm"}
        if hour==24:
            names.remove("ampm")
        return {(boxes[n][0]+boxes[n][2]//2,boxes[n][1]+boxes[n][3]//2) for n in names}

    def check(self,points,size=432,mode="ambient",hour=24,**kw):
        return inspect(png(size,points,**kw),size,mode,hour,self.layout)

    def test_all_diameters(self):
        for size in DIAMETERS:
            with self.subTest(size=size):
                r=self.check(self.points(size),size)
                self.assertEqual(r["result"],"PASS")
                self.assertEqual(r["nonblackPixels"],2)
                self.assertEqual(r["circlePixels"],sum((2*x+1-size)**2+(2*y+1-size)**2<=size**2 for y in range(size) for x in range(size)))

    def test_active_all_regions(self):
        r=self.check(self.points(432,"active",12),mode="active",hour=12)
        self.assertEqual(r["result"],"PASS")
        self.assertEqual(len(r["regionPixels"]),9)

    def test_filters_and_rgba(self):
        points=self.points(432)
        for filt in range(5):
            with self.subTest(filt=filt):
                self.assertEqual(self.check(points,channels=4,filt=filt)["nonblackPixels"],2)

    def test_12_hour_requires_marker(self):
        self.assertEqual(self.check(self.points(432),hour=12)["result"],"FAIL")
        self.assertEqual(self.check(self.points(432,hour=12),hour=12)["result"],"PASS")

    def test_24_hour_rejects_marker(self):
        self.assertGreater(self.check(self.points(432,hour=12))["outsideRegionPixels"],0)

    def test_blank(self):
        self.assertEqual(self.check(set())["result"],"FAIL")

    def test_outside_circle(self):
        self.assertEqual(self.check(self.points(432)|{(0,0)})["outsideCirclePixels"],1)

    def test_outside_regions(self):
        self.assertEqual(self.check(self.points(432)|{(216,70)})["outsideRegionPixels"],1)

    def test_ambient_budget_boundary(self):
        size=432
        boxes=project_layout(self.layout,size)["regions"]
        points=self.points(size)
        circle=sum((2*x+1-size)**2+(2*y+1-size)**2<=size**2 for y in range(size) for x in range(size))
        limit=circle//10
        for name in ("time","date"):
            x,y,w,h=boxes[name]
            for yy in range(y,y+h):
                for xx in range(x,x+w):
                    if len(points)<limit+1:
                        points.add((xx,yy))
        self.assertEqual(len(points),limit+1)
        self.assertIn("ambient nonblack pixel budget exceeded",self.check(points)["failures"])
        points.remove(next(p for p in points if p not in self.points(size)))
        self.assertEqual(self.check(points)["result"],"PASS")

    def test_transparency(self):
        with self.assertRaises(ValueError):
            self.check(self.points(432),channels=4,alpha=0)

    def test_wrong_dimensions(self):
        with self.assertRaises(ValueError):
            list(decode_png(png(432,set()),438))

    def test_crc_and_trailing_bytes(self):
        data=bytearray(png(432,set()))
        data[29]^=1
        for bad in (bytes(data),png(432,set())+b"x",png(432,set())[:-1],b""):
            with self.subTest(length=len(bad)),self.assertRaises(ValueError):
                list(decode_png(bad,432))

    def test_bounded_decompression(self):
        head=chunk(b"IHDR",struct.pack(">IIBBBBB",432,432,8,2,0,0,0))
        for raw in (b"",b"\0"*(432*(432*3+1)+1)):
            with self.assertRaises(ValueError):
                list(decode_png(PNG+head+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b""),432))

    def test_cli_failure_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"blank.png"
            path.write_bytes(png(432,set()))
            cmd=[sys.executable,str(ROOT/"tools/check_signature_capture.py"),str(path),"--diameter","432","--mode","ambient","--hour-format","24"]
            result=subprocess.run(cmd,capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,1)
            self.assertIn('"result": "FAIL"',result.stdout)
            path.write_bytes(png(432,self.points(432)))
            result=subprocess.run(cmd,capture_output=True,text=True,check=False)
            self.assertEqual(result.returncode,0)
            self.assertIn('"result": "PASS"',result.stdout)
