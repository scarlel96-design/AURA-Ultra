"""Test material output, profile allocation and independent PNG read-back."""
import copy
import hashlib
import json
import struct
import subprocess
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"tools"))
from material_foundation import ROOT,SOURCE,KINDS,DIAMETERS,parse,generate,pixels,png


def decode(data):
    if data[:8]!=b"\x89PNG\r\n\x1a\n":
        raise ValueError("signature")
    offset=8
    chunks=[]
    while offset<len(data):
        size,kind=struct.unpack(">I4s",data[offset:offset+8])
        body=data[offset+8:offset+8+size]
        crc=struct.unpack(">I",data[offset+8+size:offset+12+size])[0]
        if zlib.crc32(kind+body)!=crc:
            raise ValueError("CRC")
        chunks.append((kind,body))
        offset+=12+size
    if [k for k,_ in chunks]!=[b"IHDR",b"IDAT",b"IEND"] or chunks[-1][1]:
        raise ValueError("chunks")
    w,h,*flags=struct.unpack(">IIBBBBB",chunks[0][1])
    if flags!=[8,6,0,0,0]:
        raise ValueError("format")
    raw=zlib.decompress(chunks[1][1])
    stride=w*4+1
    if len(raw)!=stride*h or any(raw[i]!=0 for i in range(0,len(raw),stride)):
        raise ValueError("scanline")
    return w,h,b"".join(raw[i+1:i+stride] for i in range(0,len(raw),stride))


class MaterialFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=parse((ROOT/SOURCE).read_bytes())
        cls.report,cls.outputs=generate()

    def test_matrix_and_profile_budgets(self):
        self.assertEqual(self.report["assetCount"],12)
        self.assertEqual(set(self.outputs),{(d,k) for d in DIAMETERS for k in KINDS})
        for d in DIAMETERS:
            screen=self.report["screens"][str(d)]
            a=screen["assets"]
            p=screen["rgbaBytesByProfile"]
            self.assertEqual(p["ULTRA"],sum(v["rgbaBytes"] for v in a.values()))
            self.assertEqual(p["BALANCED"],p["ULTRA"])
            self.assertEqual(p["ECO"],p["ULTRA"]-a["highlight"]["rgbaBytes"])
            self.assertEqual(p["AOD"],0)
            self.assertLessEqual(p["ULTRA"],100000)

    def test_decode_and_hash_all_assets(self):
        for (d,k),data in self.outputs.items():
            w,h,rgba=decode(data)
            entry=self.report["screens"][str(d)]["assets"][k]
            self.assertEqual((w,h),(entry["width"],entry["height"]))
            self.assertEqual(hashlib.sha256(data).hexdigest(),entry["sha256"])
            self.assertEqual(hashlib.sha256(rgba).hexdigest(),entry["rgbaSha256"])
            self.assertEqual(len(rgba),entry["rgbaBytes"])
            self.assertTrue(any(rgba[3::4]))

    def test_rounded_coverage_and_transparent_rgb(self):
        for data in self.outputs.values():
            w,h,rgba=decode(data)
            for i in (0,w-1,(h-1)*w,h*w-1):
                self.assertEqual(rgba[4*i:4*i+4],bytes(4))
            for i in range(0,len(rgba),4):
                if rgba[i+3]==0:
                    self.assertEqual(rgba[i:i+3],bytes(3))
            self.assertTrue(any(0<a<255 for a in rgba[3::4]))

    def test_metal_has_nonflat_grain_and_bevel(self):
        w,h,rgba=decode(self.outputs[(480,"titanium")])
        def p(x,y):
            return rgba[4*(y*w+x)]
        self.assertGreater(len({p(w//2,y) for y in range(3,h-3)}),8)
        self.assertGreater(p(w//2,0),p(w//2,h-1))

    def test_glass_reflection_and_dark_center(self):
        w,h,rgba=decode(self.outputs[(480,"glass")])
        def p(x,y):
            return rgba[4*(y*w+x):4*(y*w+x)+3]
        self.assertGreater(sum(p(10,10)),sum(p(w-11,h-11)))
        self.assertLessEqual(max(p(w//2,h//2)),60)
        self.assertGreater(sum(p(w//2,0)),sum(p(w//2,h//2)))

    def test_highlight_alpha_bounded(self):
        w,h,rgba=decode(self.outputs[(498,"highlight")])
        self.assertLessEqual(max(rgba[3::4]),self.config["assets"]["highlight"]["peakAlpha"])
        self.assertGreater(rgba[4*((h//2)*w+w//2)+3],rgba[4*((h//2)*w+2)+3])

    def test_seed_changes_metal_not_glass(self):
        for k in ("titanium","glass"):
            a=self.config["assets"][k]
            x=pixels(k,a,432,296)
            y=pixels(k,a,432,297)
            self.assertEqual(x==y,k=="glass")

    def test_repeat_and_separate_process(self):
        self.assertEqual((self.report,self.outputs),generate())
        p=subprocess.run([sys.executable,str(ROOT/"tools/material_foundation.py"),"--manifest"],
                         cwd=ROOT,capture_output=True,timeout=60,check=True)
        self.assertEqual(json.loads(p.stdout),self.report)

    def test_invalid_contract(self):
        for edit in (lambda v:v.update(seed=True),
                     lambda v:v["lighting"].update(angleDegrees=30),
                     lambda v:v["profiles"].update(AOD=["glass"]),
                     lambda v:v["assets"]["glass"].update(base=[255,0,0]),
                     lambda v:v["assets"]["titanium"].update(radius=100),
                     lambda v:v["assets"]["highlight"].update(peakAlpha=255),
                     lambda v:v["assets"]["glass"].update(size=[450,450])):
            v=copy.deepcopy(self.config)
            edit(v)
            with self.assertRaises(ValueError):
                parse(json.dumps(v))
        with self.assertRaises(ValueError):
            parse(b'{"schemaVersion":1,"schemaVersion":1}')

    def test_invalid_png_and_diameter(self):
        with self.assertRaises(ValueError):
            png(2,2,b"")
        with self.assertRaises(ValueError):
            pixels("glass",self.config["assets"]["glass"],433,296)
        data=bytearray(self.outputs[(432,"glass")])
        data[-1]^=1
        with self.assertRaisesRegex(ValueError,"CRC"):
            decode(data)

    def test_cli_asset_selection(self):
        command=[sys.executable,str(ROOT/"tools/material_foundation.py"),"--png"]
        good=subprocess.run(command+["432","glass"],cwd=ROOT,capture_output=True,timeout=60,check=True)
        self.assertEqual(good.stdout,self.outputs[(432,"glass")])
        bad=subprocess.run(command+["433","glass"],cwd=ROOT,capture_output=True,timeout=60)
        self.assertNotEqual(bad.returncode,0)
        self.assertEqual(bad.stdout,b"")

    def test_runtime_scope_explicit(self):
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        self.assertIn("not WFF resources",self.report["scope"])
        print("MATERIAL_RESULT "+json.dumps(self.report,sort_keys=True))
