"""Read-only mid-audit probes. No ADB/device commands. Synthetic files only."""
import copy
import dataclasses
import hashlib
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zlib
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests/compatibility/ag-01"))
import wear_emulator_runtime as ag
import test_ag01_suite as fixtures
import verify_wff
import motion_events as ev
import motion_coordinator as co
import fluid_digits as digits
import signature_material as material

RESULTS = []
def emit(name, actual, expected, kind):
    rec = dict(id=name, actual=actual, expected=expected, kind=kind)
    RESULTS.append(rec)
    print("AUDIT_R03 " + json.dumps(rec, sort_keys=True), flush=True)

def outcome(fn):
    try:
        value = fn()
        return {"accepted": True, "status": value.get("status") if isinstance(value, dict) else None}
    except Exception as exc:
        return {"accepted": False, "error": type(exc).__name__, "detail": str(exc)[:220]}

def png(width=4, height=4, color=6, depth=8, before=(), raw=None):
    if raw is None:
        raw = (b"\x00" + b"\x00\x00\x00\xff" * width) * height
    return (ag.PNG_SIGNATURE + fixtures._png_chunk(b"IHDR", struct.pack(">IIBBBBB",width,height,depth,color,0,0,0))
            + b"".join(fixtures._png_chunk(k,v) for k,v in before)
            + fixtures._png_chunk(b"IDAT",zlib.compress(raw))
            + fixtures._png_chunk(b"IEND",b""))

def main():
    # Positive controls: known valid inputs; invalid CRC; actual generated assets.
    valid = png()
    assert ag.validate_png_bytes(valid)["width"] == 4
    bad = bytearray(valid); bad[-1] ^= 1
    assert not outcome(lambda: ag.validate_png_bytes(bad))["accepted"]
    emit("CTRL01", "valid PNG accepted; invalid CRC rejected", "same", "control")
    face,panel,report=material.generate()
    assert hashlib.sha256(face).hexdigest()=="fe355897238beecc2e19ad9602fe0f82d0e3a75447644a118bbf63a4320c71de"
    assert hashlib.sha256(panel).hexdigest()=="0ca25941c01f013440698b81252025b7cb6e349e440a61325f7ba3d754da5d8c"
    ring=ET.fromstring(face).find("./Scene/Group/PartDraw")
    assert len(ring.findall("Line"))==60
    assert len({tuple(sorted(x.attrib.items())) for x in ring.findall("Line")})==60
    emit("CTRL02", {"xml":report["xmlSha256"],"png":report["panelSha256"],"ticks":60,
                    "minContrast":min(report["panelContrast"].values())}, "prior artifact hashes and distinct ticks", "control")

    c=digits.ClockSample(datetime(2026,1,1,10,8),0,"audit",True)
    d=digits.ClockSample(datetime(2026,1,1,10,9),0,"audit",True)
    s=co.advance(None,co.Request(ev.Sample(0,weather="CLEAR"),c)).state
    s=co.advance(s,co.Request(ev.Sample(10,weather="RAIN"),c)).state
    assert s.events.active and s.events.active.kind=="M09"
    protected=co.advance(s,co.Request(ev.Sample(11,ambient=True,reduced=True,weather="RAIN"),c))
    assert protected.state.events.active is None and protected.state.progress==0
    emit("CTRL03", "current AOD/reduced request cancels active effect", "same", "control")
    for tick in (9,10):
        p=co.advance(s,co.Request(ev.Sample(tick,ambient=True,reduced=True,weather="RAIN"),c))
        emit("R03-01", {"tick":tick,"reason":p.reason,"ambient":p.state.request.sample.ambient,
             "reduced":p.state.request.sample.reduced,"active":p.state.events.active.kind if p.state.events.active else None},
             "protective flags cannot be lost by consumer sequencing", "integration-risk")
    trans=digits.plan(c,d)
    forged=dataclasses.replace(trans,duration_ms=5000,changed=(),reason="forged")
    value=digits.digit_frame(forged,100)
    emit("R03-02",outcome(lambda: digits.verify_frame(forged,100,value)),
         "reject inconsistent transition metadata if validator receives arbitrary transition","validation-gap")
    for ident,blob in (
        ("R03-03a",png(before=((b"tRNS",b"\x00"),))),
        ("R03-03b",png(before=((b"abca",b""),))),
        ("R03-03c",png(width=1,height=1,color=3,depth=8,before=((b"PLTE",b"\x00\x00\x00"),),raw=b"\x00\x01")),
        ("R03-03d",png(width=1,height=1,color=3,depth=8,before=((b"PLTE",b"\x00\x00\x00"),(b"tRNS",b"\xff"),(b"tRNS",b"\x80")),raw=b"\x00\x00"))
    ):
        emit(ident,outcome(lambda: ag.validate_png_bytes(blob)),"reject malformed PNG","validation-gap")
    pkg="io.github.scarlel96.aura.watchface.wff4"
    normal=f"mCurrentUserId=0\nUser 0:\n  mWallpaperComponent=ComponentInfo{{{pkg}/Face}}\n"
    assert ag.verify_active_watchface_selected(normal,pkg)["selected"]
    leak=f"mCurrentUserId=0\nUser 0:\n\nLock wallpaper:\n  mWallpaperComponent=ComponentInfo{{{pkg}/Face}}\n"
    emit("R03-04",ag.verify_active_watchface_selected(leak,pkg),
         "unconfirmed separate wallpaper section is not proof of active watch face","validation-gap")
    with tempfile.TemporaryDirectory(prefix="aura-audit-r03-") as td:
        tmp=Path(td)
        apk=tmp/"synthetic.apk"
        fixtures._build_synthetic_resource_only_apk(apk)
        normal_manifest=fixtures._valid_manifest_xml()
        assert ag.verify_local_apk_before_install(apk,pkg,4,manifest_printer=lambda p: normal_manifest)["package_id"]==pkg
        malformed=normal_manifest.replace('android:hasCode="false"','android:hasCode="true"').replace("</application>",'<!-- android:hasCode="false" -->\n<service android:name=".Example"/>\n</application>')
        duplicate=normal_manifest.replace("</application>",'<property android:name="com.google.wear.watchface.format.version" android:value="5"/>\n</application>')
        for ident,manifest in (("R03-05a",malformed),("R03-05b",duplicate)):
            emit(ident,outcome(lambda: ag.verify_local_apk_before_install(apk,pkg,4,manifest_printer=lambda p: manifest)),
                 "reject conflicting or executable manifest","validation-gap")
        # Race only in an isolated temporary directory, no real user evidence.
        staged,final=tmp/"staged.mp4",tmp/"final.mp4"
        staged.write_bytes(b"new evidence")
        real_move=shutil.move
        def competing_move(src,dst):
            Path(dst).write_bytes(b"existing evidence")
            return real_move(src,dst)
        with patch.object(ag.os,"link",side_effect=OSError("synthetic unsupported hardlink")),patch.object(ag.shutil,"move",side_effect=competing_move):
            x=outcome(lambda: ag._promote_staged_evidence_file(staged,final))
        emit("R03-06",{"result":x,"final":final.read_bytes().decode()},"preserve competing existing evidence","race-risk")
        # Run actual decoder on a valid synthetic video, then mismatch container bytes.
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            vid=tmp/"valid.mp4"
            proc=subprocess.run(["ffmpeg","-v","error","-f","lavfi","-i","color=c=blue:s=64x64:r=12:d=1",
                "-c:v","libx264","-threads","1","-pix_fmt","yuv420p","-y",str(vid)],capture_output=True,timeout=30)
            if proc.returncode:
                emit("R03-07",proc.stderr.decode(errors="replace")[:300],"synthetic real decoder probe","NOT RUN")
            else:
                result=ag.verify_mp4_video_artifact(vid)
                assert result["status"]=="VERIFIED" and result["decoded_frame_count"]==12
                emit("CTRL04",{"frames":result["decoded_frame_count"],"codec":result["codec_name"]},"real ffprobe 12/12","control")
                fake=fixtures._build_valid_mp4_bytes(sample_count=12)
                mismatched=ag.verify_mp4_video_artifact(vid,data=fake)
                emit("R03-07",{"status":mismatched["status"],"containerSha":mismatched["container"]["sha256"],
                     "decodedFileSha":hashlib.sha256(vid.read_bytes()).hexdigest(),"frames":mismatched["decoded_frame_count"]},
                     "verify the same bytes that are decoded","validation-gap")
        else:
            emit("R03-07","ffmpeg or ffprobe missing","real decoder probe","NOT RUN")
        # Actual main() path with injected process failure; no real jar/network.
        cache=tmp/"fakecache";cache.mkdir();jar=cache/"wff-validator.jar";jar.write_bytes(b"audit-only")
        real_face=tmp/"valid.xml";real_face.write_text("<WatchFace/>")
        def fake_run(jar,face,version):
            if face.name=="invalid.xml":
                return SimpleNamespace(returncode=1,stdout="JVM invocation crashed\n")
            return SimpleNamespace(returncode=0,stdout=f"INFO: PASSED : {face} is valid against watch face format version #{version}\n")
        output=io.StringIO()
        with patch.multiple(verify_wff,CACHE=cache,SHA256=hashlib.sha256(jar.read_bytes()).hexdigest(),
                            load_profiles=lambda:[{"name":"wff4","enabled":True,"version":4}],
                            check_source_sets=lambda p:None,face_source=lambda p:real_face,run_validator=fake_run):
            with redirect_stdout(output):
                x=outcome(verify_wff.main)
        emit("R03-08",{"result":x,"printedPass": "real validator rejected invalid XML" in output.getvalue()},
             "tool crash is not successful negative schema test","validation-gap")
    Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("AUDIT_R03_SUMMARY "+json.dumps({"observations":len(RESULTS),"controls":sum(x["kind"]=="control" for x in RESULTS),
           "runtime":"NOT RUN","deviceCommands":0}),flush=True)

if __name__=="__main__":
    main()
