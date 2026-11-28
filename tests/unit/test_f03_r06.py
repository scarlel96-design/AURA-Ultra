"""Verify lock evidence and graph comparisons with deterministic fixtures."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import audit_gradle_lock_pilot as pilot


def row(configuration="classpath", modules=None, project=":", scope="buildscript", **kw):
    return dict(project=project, scope=scope, configuration=configuration,
                modules=["a:b:1"] if modules is None else modules,
                unresolved=[], error=None) | kw


class LockEvidenceTests(unittest.TestCase):
    def test_exact_graph(self):
        self.assertEqual(pilot.compare_graphs([row()], [row()], "domain"), [])

    def test_only_known_empty_android_configuration(self):
        extra = row("androidApis", [], ":apps:watchface", "project")
        self.assertEqual(pilot.compare_graphs([row()], [row(), extra], "android"),
                         [(":apps:watchface", "project", "androidApis")])
        for changed in (dict(extra, modules=["x:y:1"]), dict(extra, configuration="unexpected")):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                pilot.compare_graphs([row()], [row(), changed], "android")

    def test_graph_mutation_rejected(self):
        for changed in ([], [row(modules=["a:b:2"])], [row(), row()],
                        [row(error="failed")], [row(unresolved=["x:y:1"])]):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                pilot.compare_graphs([row()], changed, "domain")

    def test_lock_content_matches_exact_graph(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            lock = root / "buildscript-gradle.lockfile"
            lock.write_text("# generated\n" "a:b:1=classpath\nempty=\n", encoding="utf-8")
            self.assertEqual(pilot.lock_index(root, [lock]), pilot.graph_index([row()]))
            lock.write_text("a:b:2=classpath\nempty=\n", encoding="utf-8")
            self.assertNotEqual(pilot.lock_index(root, [lock]), pilot.graph_index([row()]))

    def test_empty_lock_config_and_bad_entries(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            lock = root / "gradle.lockfile"
            lock.write_text("empty=compileClasspath\n", encoding="utf-8")
            self.assertEqual(pilot.lock_index(root, [lock]),
                             pilot.graph_index([row("compileClasspath", [], ":", "project")]))
            for bad in ("a:b:1=compileClasspath\nempty=compileClasspath\n",
                        "empty=compileClasspath\na:b:1=compileClasspath\n",
                        "a:b:1=compileClasspath,compileClasspath\n",
                        "a:b:1=\n", "a:b:1=compileClasspath\na:b:1=testClasspath\n"):
                lock.write_text(bad, encoding="utf-8")
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    pilot.lock_index(root, [lock])


if __name__ == "__main__":
    unittest.main()
