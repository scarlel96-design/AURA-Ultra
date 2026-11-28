"""Guard the approved static material candidate against encoder drift."""
import hashlib
import sys
import zlib

XML_SHA = "fe355897238beecc2e19ad9602fe0f82d0e3a75447644a118bbf63a4320c71de"
PNG_SHA = "0ca25941c01f013440698b81252025b7cb6e349e440a61325f7ba3d754da5d8c"
RGBA_SHA = "b58dc905375d628d218ec766d44185f43ae68de7144e29c351775bd81b3b7fdb"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def classify(xml, png, report):
    actual = {"xml": digest(xml), "png": digest(png), "rgba": report.get("panelRgbaSha256")}
    if actual["xml"] != XML_SHA:
        status = "XML_CHANGED"
    elif actual["rgba"] != RGBA_SHA:
        status = "PIXELS_CHANGED"
    elif actual["png"] != PNG_SHA:
        status = "PNG_ENCODING_CHANGED"
    else:
        status = "CANONICAL"
    return {"status": status, "actual": actual, "python": sys.version.split()[0],
            "zlibBuild": zlib.ZLIB_VERSION, "zlibRuntime": zlib.ZLIB_RUNTIME_VERSION}


def require_canonical_material(xml, png, report):
    result = classify(xml, png, report)
    if result["status"] != "CANONICAL":
        raise ValueError(f"Static material baseline mismatch: {result}; "
                         "use the reviewed CI toolchain or review the changed baseline")
    return result


if __name__ == "__main__":
    import json
    from signature_material import generate
    result = classify(*generate())
    print("MATERIAL_BASELINE " + json.dumps(result, sort_keys=True))
    sys.exit(0 if result["status"] == "CANONICAL" else 1)
