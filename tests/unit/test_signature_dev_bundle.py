"""Test development bundle integrity with synthetic ZIP fixtures."""
import io
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/"tools"))
from signature_dev_bundle import PROFILES, build_bundle, verify_bundle, write_new

FACE = b"<WatchFace/>"
SHA = "a"*40


def apk(face=FACE):
    out = io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        z.writestr("res/raw/watchface.xml",face)
    return out.getvalue()


def edit(data, name, payload=None, duplicate=False):
    out = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(data)) as src, zipfile.ZipFile(out,"w") as dst:
        for n in src.namelist():
            if n != name or duplicate:
                dst.writestr(n,src.read(n))
        if payload is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                dst.writestr(name,payload)
    return out.getvalue()


class DevBundleTests(unittest.TestCase):
    def setUp(self):
        self.apks = {p:apk() for p in PROFILES}
        self.data,self.meta = build_bundle(self.apks,FACE,SHA)

    def test_exact_matrix_and_determinism(self):
        self.assertEqual(build_bundle(self.apks,FACE,SHA),(self.data,self.meta))
        self.assertEqual(verify_bundle(self.data,FACE,SHA),self.meta)
        self.assertEqual([r["minSdk"] for r in self.meta["profiles"]],[34,35,36,37])

    def test_missing_and_extra_profiles(self):
        for p in ("wff2","wff9"):
            a = dict(self.apks)
            if p in a:
                del a[p]
            else:
                a[p] = apk()
            with self.assertRaises(ValueError):
                build_bundle(a,FACE,SHA)

    def test_wrong_apk_face(self):
        self.apks["wff4"] = apk(b"<Other/>")
        with self.assertRaises(ValueError):
            build_bundle(self.apks,FACE,SHA)

    def test_wrong_source_commit(self):
        with self.assertRaises(ValueError):
            verify_bundle(self.data,FACE,"b"*40)
        with self.assertRaises(ValueError):
            build_bundle(self.apks,FACE,"invalid")

    def test_manifest_mutation(self):
        with self.assertRaises(ValueError):
            verify_bundle(edit(self.data,"manifest.json",b"{}"),FACE,SHA)

    def test_apk_mutation(self):
        with self.assertRaises(ValueError):
            verify_bundle(edit(self.data,"wff3.apk",apk(b"x")),FACE,SHA)

    def test_unexpected_entries(self):
        for data in (edit(self.data,"wff2.apk"), edit(self.data,"../x",b"x"),
                     edit(self.data,"wff2.apk",apk(),duplicate=True)):
            with self.assertRaises(ValueError):
                verify_bundle(data,FACE,SHA)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"bundle.zip"
            write_new(path,self.data)
            with self.assertRaises(FileExistsError):
                write_new(path,b"replacement")
            self.assertEqual(path.read_bytes(),self.data)
