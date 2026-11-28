"""Audit exact prior Gradle inventories without approving trust or rebuilding."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import datetime
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from audit_published_checksums import artifact_path, repositories, RestrictedRedirect, allowed_url

SOURCE = "3609f3890c69267653badcef03961d75934de35a"
INPUTS = {
    "android": ("a01944838ba91c4a77837e5217c8aa462a7ae5f3e8c7234592bfb156905a40ad", 563, 177),
    "domain": ("35b52677a2b3b2516f50e7ecab7060f2bec8e9a0c557d5131ee2477097e5bde3", 113, 19),
}
OSV = "https://api.osv.dev/v1/querybatch"
NS = {"v": "https://schema.gradle.org/dependency-verification"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_inventory(path, build):
    expected, count, graph_count = INPUTS[build]
    if digest(path.read_bytes()) != expected:
        raise ValueError("Archive digest mismatch")
    with zipfile.ZipFile(path) as z:
        if z.testzip() or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError("Invalid archive")
        summary = json.loads(z.read("summary.json"))
        if (summary["sourceCommit"] != SOURCE or summary["build"] != build
                or summary["trust"] != "UNREVIEWED" or any(summary["commands"].values())):
            raise ValueError("Inventory scope mismatch")
        raw = z.read("verification-metadata.UNREVIEWED.xml")
        if digest(raw) != summary["metadata"]["sha256"]:
            raise ValueError("Metadata digest mismatch")
        root = ET.fromstring(raw)
        xml_rows = {}
        for c in root.findall("./v:components/v:component", NS):
            coord = ":".join(c.attrib[k] for k in ("group", "name", "version"))
            for a in c.findall("v:artifact", NS):
                key = (coord, a.attrib["name"])
                if key in xml_rows:
                    raise ValueError("Duplicate XML artifact")
                xml_rows[key] = [x.attrib["value"] for x in a.findall("v:sha256", NS)]
        rows = json.loads(z.read("artifacts.json"))
        actual = {}
        for r in rows:
            artifact_path(r)
            key = (r["coordinate"], r["artifact"])
            if key in actual:
                raise ValueError("Duplicate inventory artifact")
            actual[key] = r["sha256"]
        if len(actual) != count or actual != xml_rows:
            raise ValueError("XML/inventory mismatch")
        graphs = json.loads(z.read("graph.json"))
        if (len(graphs) != graph_count or any(g["error"] or g["unresolved"] for g in graphs)
                or len({(g["project"], g["scope"], g["configuration"]) for g in graphs}) != graph_count):
            raise ValueError("Incomplete graph")
        graph_modules = {m for g in graphs for m in g["modules"]}
        if not graph_modules <= {r["coordinate"] for r in rows}:
            raise ValueError("Graph module absent from inventory")
        return rows, graph_modules


def merge(inputs):
    components = {}
    for build, (rows, graph) in inputs.items():
        for r in rows:
            c = components.setdefault(r["coordinate"], {"artifacts": {}, "builds": set(), "graphBuilds": set()})
            name, sha = r["artifact"], r["sha256"][0]
            if name in c["artifacts"] and c["artifacts"][name] != sha:
                raise ValueError("Conflicting artifact digests")
            c["artifacts"][name] = sha
            c["builds"].add(build)
            if r["coordinate"] in graph:
                c["graphBuilds"].add(build)
    return components


def osv_query(coords, request):
    # An empty or truncated response is not a clean scan.
    queries = [{"package": {"ecosystem": "Maven", "name": ":".join(c.split(":")[:2])},
                "version": c.split(":")[2]} for c in coords]
    results = request(queries).get("results")
    if not isinstance(results, list) or len(results) != len(coords):
        raise ValueError("OSV response cardinality mismatch")
    rows = {}
    for c, q, result in zip(coords, queries, results):
        ids = set()
        seen_tokens = set()
        for _ in range(20):
            if not isinstance(result, dict) or set(result) - {"vulns", "next_page_token"}:
                raise ValueError("Unexpected OSV result")
            vulns = result.get("vulns", [])
            if not isinstance(vulns, list):
                raise ValueError("Malformed OSV vulnerabilities")
            for v in vulns:
                if not isinstance(v.get("id"), str) or not v["id"]:
                    raise ValueError("Missing advisory ID")
                ids.add(v["id"])
            token = result.get("next_page_token")
            if not token:
                rows[c] = {"status": "MATCH" if ids else "NO_KNOWN_MATCH", "ids": sorted(ids)}
                break
            if not isinstance(token, str) or token in seen_tokens:
                raise ValueError("Invalid OSV pagination")
            seen_tokens.add(token)
            page = request([dict(q, page_token=token)]).get("results")
            if not isinstance(page, list) or len(page) != 1:
                raise ValueError("Invalid OSV page")
            result = page[0]
        else:
            raise ValueError("OSV pagination limit")
    return rows


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("OSV redirect refused")


def request_osv(queries):
    req = urllib.request.Request(OSV, data=json.dumps({"queries": queries}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.build_opener(NoRedirect()).open(req, timeout=45) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("OSV response too large")
        return json.loads(raw)


def parse_pom(raw):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("DTD or entity refused")
    root = ET.fromstring(raw)
    if root.tag not in ("project", "{http://maven.apache.org/POM/4.0.0}project"):
        raise ValueError("Not a Maven POM")
    ns = {"p": "http://maven.apache.org/POM/4.0.0"} if root.tag.startswith("{") else {}
    prefix = "p:" if ns else ""
    licenses = []
    for el in root.findall(f"{prefix}licenses/{prefix}license", ns):
        entry = {k: (el.findtext(prefix + k, "", ns) or "").strip() for k in ("name", "url", "distribution")}
        if entry["name"] and not any("$" in v for v in entry.values()):
            licenses.append(entry)
    return licenses


def read_pom(url):
    if not allowed_url(url):
        raise ValueError("Unapproved POM source")
    with urllib.request.build_opener(RestrictedRedirect()).open(url, timeout=8) as response:
        if not allowed_url(response.geturl()):
            raise ValueError("Unapproved POM redirect")
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError("POM too large")
        return raw, response.geturl()


def license_evidence(coord, component, reader=read_pom):
    _, name, version = coord.split(":")
    filename = name + "-" + version + ".pom"
    expected = component["artifacts"].get(filename)
    if not expected:
        return {"status": "NO_PINNED_POM", "declarations": []}
    path = artifact_path({"coordinate": coord, "artifact": filename, "sha256": [expected],
                          "trust": "UNREVIEWED"}).removesuffix(".sha256")
    attempts = []
    for base in repositories(coord):
        try:
            raw, url = reader(base + path)
            actual = digest(raw)
            if actual != expected:
                return {"status": "HASH_MISMATCH", "source": url, "expected": expected,
                        "actual": actual, "declarations": []}
            declarations = parse_pom(raw)
            return {"status": "DECLARED" if declarations else "NO_DIRECT_DECLARATION",
                    "source": url, "sha256": actual, "declarations": declarations,
                    "attempts": attempts}
        except (OSError, ValueError, ET.ParseError) as exc:
            attempts.append({"url": base + path, "error": type(exc).__name__,
                             "http": getattr(exc, "code", None)})
    return {"status": "UNAVAILABLE", "declarations": [], "attempts": attempts}


def sbom(components):
    result = []
    for coord, c in sorted(components.items()):
        group, name, version = coord.split(":")
        purl = "pkg:maven/" + "/".join(urllib.parse.quote(x, safe="") for x in (group, name)) + "@" + urllib.parse.quote(version, safe="")
        properties = [{"name": "aura:inventoryTrust", "value": "UNREVIEWED"},
                      {"name": "aura:builds", "value": ",".join(sorted(c["builds"]))},
                      {"name": "aura:resolvedGraphBuilds", "value": ",".join(sorted(c["graphBuilds"])) or "none"}]
        properties.extend({"name": "aura:artifact-sha256:" + filename, "value": sha}
                          for filename, sha in sorted(c["artifacts"].items()))
        result.append({"type": "library", "bom-ref": purl, "group": group, "name": name,
                       "version": version, "purl": purl, "properties": properties})
    # Graph inventory contains module sets, not dependency edges. Do not invent edges.
    return {"bomFormat": "CycloneDX", "specVersion": "1.6", "version": 1,
            "metadata": {"component": {"type": "application", "name": "AURA Ultra audit inventory",
                                       "version": SOURCE, "bom-ref": "aura-audit"},
                         "properties": [{"name": "aura:scope", "value": "provisional Android and Domain Gradle inventory; not release SBOM; dependency edges and other build tools incomplete"}]},
            "components": result}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--android", type=Path, required=True)
    parser.add_argument("--domain", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    components = merge({b: load_inventory(getattr(args, b), b) for b in INPUTS})
    if len(components) != 373 or sum(len(c["artifacts"]) for c in components.values()) != 664:
        raise ValueError("Unexpected combined inventory")
    write_json(args.output / "provisional.cdx.json", sbom(components))
    coords = sorted(components)
    vulnerabilities = {}
    for start in range(0, len(coords), 50):
        batch = coords[start:start+50]
        try:
            vulnerabilities.update(osv_query(batch, request_osv))
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            vulnerabilities.update({c: {"status": "UNKNOWN", "error": type(exc).__name__} for c in batch})
    write_json(args.output / "osv-results.json", vulnerabilities)
    with ThreadPoolExecutor(max_workers=4) as executor:
        licenses = dict(zip(coords, executor.map(lambda c: license_evidence(c, components[c]), coords)))
    write_json(args.output / "license-results.json", licenses)
    counts = {"sourceCommit": SOURCE, "trust": "UNREVIEWED",
              "scannedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "components": len(coords), "artifacts": 664,
              "resolvedGraphComponents": sum(bool(c["graphBuilds"]) for c in components.values()),
              "osv": dict(Counter(r["status"] for r in vulnerabilities.values())),
              "licenses": dict(Counter(r["status"] for r in licenses.values())),
              "advisoryIds": sorted({i for r in vulnerabilities.values() for i in r.get("ids", [])})}
    write_json(args.output / "summary.json", counts)
    print("F03_R09", json.dumps(counts, sort_keys=True), flush=True)
    # A database match, incomplete scan or license review is a blocker, not an approval.
    if counts["osv"].get("UNKNOWN") or counts["osv"].get("MATCH") or any(
            r["status"] != "DECLARED" for r in licenses.values()):
        raise SystemExit("Incomplete or adverse dependency evidence; review required")


if __name__ == "__main__":
    main()
