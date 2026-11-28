"""Build and verify four real material candidate APKs in a committed snapshot."""
import argparse
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

from generate_bootstrap import ROOT, FACE, safe_path
from check_flavor_isolation import FILES,DIRECTORIES,run
from committed_build_inputs import clean_commit,copy_committed_inputs
from profile_contract import enabled_profiles,debug_apk
from signature_material import generate,inspect_material_apk,digest,RESOURCE
from check_material_baseline import require_canonical_material


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    out=args.output.resolve()
    if out.exists() or out.is_relative_to(ROOT):
        raise ValueError("Use a new output directory outside repository")
    source=clean_commit(ROOT)
    original=(ROOT/FACE).read_bytes()
    expected=generate(ROOT)
    require_canonical_material(*expected)
    with tempfile.TemporaryDirectory(prefix="aura-material-") as folder:
        root=Path(folder)
        count=copy_committed_inputs(ROOT,root,source,FILES+("apps/watchface/build.gradle.kts",),DIRECTORIES)
        face,png,report=generate(root)
        if (face,png,report)!=expected or (root/FACE).read_bytes()!=original:
            raise ValueError("Committed material reproduction mismatch")
        print("MATERIAL_INPUTS_RESULT "+json.dumps({"sourceCommit":source,"count":count,**report},sort_keys=True))
        app=root/"apps/watchface"
        profiles=enabled_profiles(root)
        if [p["name"] for p in profiles]!=["wff2","wff3","wff4","wff5"]:
            raise ValueError("Expected all four WFF profiles")
        if any((app/"src"/p["name"]/"res/raw/watchface.xml").exists() for p in profiles):
            raise ValueError("Unexpected flavor override")
        (root/".aura-tools").mkdir()
        for name in ("wff-validator.jar","memory-footprint.jar"):
            path=".aura-tools/"+name
            shutil.copy2(safe_path(ROOT,path),root/path)
        (root/FACE).write_bytes(face)
        asset=app/"src/main/res/drawable-nodpi"/(RESOURCE+".png")
        with asset.open("xb") as stream:
            stream.write(png)
        # Preserve the exact compressed PNG bytes in this isolated debug build.
        gradle=app/"build.gradle.kts"
        text=gradle.read_text(encoding="utf-8")
        if text.count("debug {")!=1:
            raise ValueError("Unexpected debug build configuration")
        gradle.write_text(text.replace("debug {","debug {\n            isCrunchPngs = false"),encoding="utf-8")
        run(root,"verify_wff.py")
        run(root,"build_profiles.py","assemble")
        run(root,"check_apk.py")
        run(root,"verify_memory.py")
        run(root,"build_profiles.py","signatures")
        files={}
        for p in profiles:
            apk=debug_apk(p,app)
            with zipfile.ZipFile(apk) as z:
                inspect_material_apk(z,face,png)
            files[p["name"]+".apk"]=apk.read_bytes()
        if clean_commit(ROOT)!=source or (ROOT/FACE).read_bytes()!=original or generate(ROOT)!=expected:
            raise ValueError("Source changed during build")
        manifest={"sourceCommit":source,"report":report,"debugOnly":True,
                  "apkSha256":{k:digest(v) for k,v in files.items()}}
        files.update({"watchface.xml":face,RESOURCE+".png":png,
                      "manifest.json":(json.dumps(manifest,sort_keys=True,indent=2)+"\n").encode()})
        out.mkdir()
        try:
            for name,data in files.items():
                with (out/name).open("xb") as stream:
                    stream.write(data)
                if (out/name).read_bytes()!=data:
                    raise ValueError("Artifact read-back mismatch")
        except Exception:
            shutil.rmtree(out)
            raise
        print("MATERIAL_APK_RESULT "+json.dumps(manifest,sort_keys=True))
    print("PASS: four isolated material debug APKs; product source unchanged")


if __name__=="__main__":
    main()
