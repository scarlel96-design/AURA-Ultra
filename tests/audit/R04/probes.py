"""Read-only bounded snapshot audit and synthetic trust-boundary probes."""
import json, re, shutil, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/"tools"))
import check_foundation as foundation
import check_apk
import committed_build_inputs as committed
import profile_contract as profile

def git(root,*args):
    return subprocess.check_output(["git","--no-replace-objects",*args],cwd=root,timeout=60)
def attempt(fn):
    try:
        fn()
        return {"accepted":True}
    except Exception as e:
        return {"accepted":False,"error":type(e).__name__,"detail":str(e)[:160]}
def scan(ref):
    patterns={
        "private-key-header":rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----",
        "github-token":rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})",
        "aws-access-id":rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
        "google-api-key":rb"\bAIza[A-Za-z0-9_-]{35}\b",
        "openai-key-shape":rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}\b",
    }
    forbidden={".jks",".keystore",".p12",".pfx",".pem",".key",".apk",".aab"}
    entries=[]; hits=[]; skipped=[]
    for item in git(ROOT,"ls-tree","-r","-z",ref).split(b"\0"):
        if not item: continue
        header,path=item.split(b"\t",1)
        mode,kind,oid=header.decode().split()
        path=path.decode()
        if kind!="blob":
            skipped.append([path,kind]); continue
        size=int(git(ROOT,"cat-file","-s",oid))
        entries.append([path,mode,oid,size])
        if Path(path).suffix.lower() in forbidden or (Path(path).name.startswith(".env") and Path(path).name!=".env.example"):
            hits.append({"path":path,"kind":"sensitive-file-name"})
        if size>2*1024*1024:
            skipped.append([path,"size-limit"]); continue
        data=git(ROOT,"cat-file","blob",oid)
        for key,regex in patterns.items():
            for match in re.finditer(regex,data):
                hits.append({"path":path,"kind":key,"line":data[:match.start()].count(b"\n")+1})
    return {"ref":ref,"blobCount":len(entries),"bytes":sum(x[3] for x in entries),"hits":hits,"skipped":skipped,
            "nonregular":[x[:2] for x in entries if x[1] not in ("100644","100755")]}
def main():
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    scans=[scan(ref) for ref in sys.argv[2:]]
    for s in scans:
        print("AUDIT_SCAN "+json.dumps(s,ensure_ascii=False))
    results=[]
    def record(id,value):
        results.append({"id":id,"observed":value})
        print("AUDIT_R04 "+json.dumps(results[-1],ensure_ascii=False))
    with tempfile.TemporaryDirectory(prefix="aura-r04-") as td:
        tmp=Path(td);fake=tmp/"root"
        shutil.copytree(ROOT/"apps/watchface",fake/"apps/watchface",ignore=shutil.ignore_patterns("build"))
        shutil.copytree(ROOT/"design-system",fake/"design-system")
        app=fake/"apps/watchface";res=app/"src/main/res";path=app/"src/main/AndroidManifest.xml"
        original=path.read_text()
        def run_foundation():
            with patch.multiple(foundation,ROOT=fake,APP=app,RES=res,
                  load_profiles=lambda:profile.load_profiles(ROOT),
                  face_source=lambda p:profile.face_source(p,app),
                  check_source_sets=lambda p:profile.check_source_sets(p,app)):
                with redirect_stdout(StringIO()): foundation.check()
        assert attempt(run_foundation)["accepted"]
        record("CTRL01","normal source foundation accepted")
        mutations=[("R04-01a",original.replace("</application>",'<receiver android:name=".Example" android:exported="false"/></application>')),
                   ("R04-01b",original.replace("</application>",'<provider android:name=".Example" android:authorities="audit.test" android:exported="false"/></application>')),
                   ("R04-01c",original.replace("</application>",'<activity-alias android:name=".Alias" android:targetActivity=".Example" android:exported="false"/></application>')),
                   ("R04-01d",original.replace("<application ",'<uses-permission-sdk-23 android:name="android.permission.INTERNET"/><application '))]
        for ident,modified in mutations:
            path.write_text(modified)
            src=attempt(run_foundation)
            merged=modified.replace("<manifest ","<manifest package=\"io.github.scarlel96.aura.watchface.wff4\" ").replace("<application ",'<uses-sdk android:minSdkVersion="36"/><application ').replace(chr(36)+"{wffVersion}","4")
            record(ident,{"source":src,"compiledErrors":check_apk.inspect_manifest(merged,{"name":"wff4","minSdk":36,"version":4})})
        repo=tmp/"input";repo.mkdir()
        git(repo,"init","-q");git(repo,"config","user.name","Audit");git(repo,"config","user.email","audit@example.invalid")
        (repo/"tools").mkdir();(repo/"tools/probe.txt").write_text("synthetic audit\n")
        git(repo,"add",".");git(repo,"commit","-qm","synthetic baseline")
        sha=committed.clean_commit(repo)
        dst=tmp/"dest";dst.mkdir();outside=tmp/"sibling";outside.mkdir()
        (dst/"tools").symlink_to(outside,target_is_directory=True)
        record("R04-02",{"result":attempt(lambda:committed.copy_committed_inputs(repo,dst,sha,(),("tools",))),
                         "outsideWritten":(outside/"probe.txt").is_file(),"scope":"existing caller-controlled destination"})
        clean=tmp/"clean";clean.mkdir()
        assert committed.copy_committed_inputs(repo,clean,sha,(),("tools",))==1
        assert (clean/"tools/probe.txt").read_text()=="synthetic audit\n"
        record("CTRL02","normal clean destination byte-identical")
        p=tmp/"profile";(p/"compatibility").mkdir(parents=True)
        orig=(ROOT/"compatibility/profiles.json").read_text()
        target=p/"compatibility/profiles.json";target.write_text(orig)
        assert len(profile.load_profiles(p))==4
        duplicate=re.sub(r'"schemaVersion"\s*:\s*1', '"schemaVersion": 999, "schemaVersion": 1',orig,count=1)
        assert duplicate!=orig
        target.write_text(duplicate)
        record("R04-03",attempt(lambda:profile.load_profiles(p)))
        git(repo,"update-index","--assume-unchanged","tools/probe.txt")
        (repo/"tools/probe.txt").write_text("different synthetic bytes\n")
        record("R04-04",{"cleanCommitAccepted":attempt(lambda:committed.clean_commit(repo)),
                         "actualBytesDiffer":(repo/"tools/probe.txt").read_bytes()!=git(repo,"show",sha+":tools/probe.txt"),
                         "scope":"local assume-unchanged state; committed blob copy still exact"})
        assert check_apk.inspect_entries(["AndroidManifest.xml","resources.arsc","classes.dex"])
        assert check_apk.inspect_entries(["AndroidManifest.xml","resources.arsc","../escape"])
        record("CTRL03","executable payload and traversal entries rejected")
    (out/"results.json").write_text(json.dumps({"scans":scans,"probes":results},ensure_ascii=False,indent=2)+"\n")
if __name__=="__main__": main()
