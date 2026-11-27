"""Verify frame evidence boundaries, exact data and reproducibility."""
import hashlib
import json
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"tools"))
from motion_storyboard import ROOT, DIAMETERS, SAMPLES, generate, opacity

NS = {"s": "http://www.w3.org/2000/svg"}


class MotionStoryboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.svgs = generate()
        cls.report = json.loads(cls.data)

    def test_full_sample_matrix(self):
        self.assertEqual(SAMPLES, (0,100,150,250,425,450,475,500,550,575,725,800,850,900,1000))
        self.assertEqual(self.report["frameCount"],60)
        self.assertEqual(set(self.report["screens"]),{str(d) for d in DIAMETERS})
        for rows in self.report["screens"].values():
            self.assertEqual([r["wakeTick"] for r in rows],list(SAMPLES))
            self.assertEqual([r["sleepTick"] for r in rows],[1000-t for t in SAMPLES])

    def test_exact_rational_endpoints_and_midpoint(self):
        rows = {r["wakeTick"]:r for r in self.report["screens"]["480"]}
        for name in ("weather","heart"):
            self.assertEqual(rows[250]["objects"][name]["alpha"],[0,1])
            self.assertEqual(rows[575]["objects"][name]["alpha"],[1,2])
            self.assertEqual(rows[900]["objects"][name]["alpha"],[1,1])
            self.assertLess(Fraction(*rows[575]["objects"][name]["logicalBox"][2]),
                            Fraction(*rows[900]["objects"][name]["logicalBox"][2]))

    def test_fixed_core(self):
        for rows in self.report["screens"].values():
            for name in ("time","date","ampm"):
                first = rows[0]["objects"][name]
                self.assertEqual(first["alpha"],[1,1])
                self.assertTrue(all(r["objects"][name]==first for r in rows))

    def test_schedule_only_and_runtime_labels(self):
        self.assertEqual(self.report["scheduleOnly"],["time","ring","highlight"])
        self.assertEqual(self.report["runtimeVerification"],"NOT RUN")
        self.assertEqual(self.report["screens"]["432"][-1]["schedule"]["ring"],[1,1])
        self.assertNotIn("ring",self.report["screens"]["432"][-1]["objects"])

    def test_svg_hashes_and_frame_counts(self):
        for d, data in self.svgs.items():
            self.assertEqual(hashlib.sha256(data).hexdigest(),self.report["svgSha256"][str(d)])
            root = ET.fromstring(data)
            self.assertEqual(len(root.findall("s:svg",NS)),15)
            self.assertIn("runtime NOT RUN",root.find("s:title",NS).text)

    def test_hidden_objects_omitted_from_svg(self):
        root = ET.fromstring(self.svgs[432])
        cells = root.findall("s:svg",NS)
        names = lambda cell: {r.attrib["data-region"] for r in cell.findall("s:rect",NS)}
        self.assertEqual(names(cells[0]),{"time","date","ampm"})
        self.assertEqual(len(names(cells[-1])),9)

    def test_opacity_rounding(self):
        self.assertEqual(opacity([0,1]),"0.000000")
        self.assertEqual(opacity([1,3]),"0.333333")
        self.assertEqual(opacity([1,1]),"1.000000")

    def test_reproduction_in_separate_process(self):
        command = [sys.executable,str(ROOT/"tools/motion_storyboard.py"),"--json"]
        p = subprocess.run(command,cwd=ROOT,capture_output=True,timeout=30,check=True)
        self.assertEqual(p.stdout,self.data)

    def test_unsupported_diameter_cli(self):
        p = subprocess.run([sys.executable,str(ROOT/"tools/motion_storyboard.py"),
                            "--svg","433"],cwd=ROOT,capture_output=True,timeout=30)
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(p.stdout,b"")
