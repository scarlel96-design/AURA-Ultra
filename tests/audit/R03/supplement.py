"""Additional bounded, synthetic audit observations. Never invoke ADB."""
import hashlib
import json
import os
import struct
import sys
import tempfile
import tracemalloc
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
sys.path.insert(0,str(ROOT/"tests/compatibility/ag-01"))
import wear_emulator_runtime as runtime
import test_ag01_suite as fixture

def observe():
    records=[]
    for count in (1000,50000,250000):
        raw=bytearray(fixture._build_valid_mp4_bytes(sample_count=1))
        offset=raw.index(b"stsz")+12
        struct.pack_into(">I",raw,offset,count)
        tracemalloc.start()
        try:
            runtime.parse_and_validate_mp4_structure(bytes(raw))
            status="ACCEPTED"
        except RuntimeError as exc:
            status=str(exc)
        finally:
            _,peak=tracemalloc.get_traced_memory()
            tracemalloc.stop()
        row={"case":"R03-09","count":count,"fileBytes":len(raw),"peakBytes":peak,"status":status}
        records.append(row)
        print("SUPPLEMENT "+json.dumps(row))
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"synthetic.apk"
        fixture._build_synthetic_resource_only_apk(p)
        calls=[]
        def runner(args,timeout=30,binary=False):
            calls.append(list(args))
            answers={
                ("shell","getprop","ro.boot.qemu.avd_name"):"aura_wear36_round",
                ("shell","getprop","sys.boot_completed"):"1",
                ("shell","getprop","ro.build.characteristics"):"watch",
                ("shell","getprop","ro.build.version.sdk"):"36",
                ("install","-r",str(p)):"Success",
                ("shell","pm","list","packages","io.github.scarlel96.aura.watchface.wff4"):"",
            }
            if tuple(args) not in answers:
                raise AssertionError("Unexpected mock command: "+str(args))
            return SimpleNamespace(returncode=0,stdout=answers[tuple(args)],stderr="")
        try:
            runtime.execute_runtime_verification("UNUSED_MOCK","emulator-5554",p,
                "io.github.scarlel96.aura.watchface.wff4",4,Path(d)/"evidence",
                runner=runner,manifest_printer=lambda p: fixture._valid_manifest_xml(),
                recorder_factory=lambda: (_ for _ in ()).throw(AssertionError("recorder called")),
                sleep_fn=lambda t:None)
            err="unexpected success"
        except Exception as exc:
            err=type(exc).__name__+": "+str(exc)
        row={"case":"R03-10","mockCommands":calls,"error":err,"actualDeviceCommands":0}
        records.append(row)
        print("SUPPLEMENT "+json.dumps(row))
    Path(sys.argv[1]).write_text(json.dumps(records,indent=2)+"\n",encoding="utf-8")

if __name__=="__main__": observe()
