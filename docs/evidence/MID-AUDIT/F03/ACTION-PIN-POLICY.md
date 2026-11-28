# CI action pin maintenance
Scope: active workflows on main. F03 R01, AUD-R01-07 and AUD-R04-06.
Use a full reviewed commit SHA for every external Action. Keep the upstream version label in a comment. Use contents: read and persist-credentials: false for the current read-only jobs. Preserve the historical reproduction checkout commit.
The current pins match the actual successful F02 main CI download log (job 140819134905, 2026-11-28) and official upstream version references:
| Action | Reviewed version reference | Commit |
|---|---|---|
| actions/checkout | v4 | 11d5960a326750d5838078e36cf38b85af677262 |
| actions/setup-java | v4 | cf277c60eb25467037889841efdb72551f06f6c3 |
| actions/setup-python | v5 | a26af69be951a213d495a4c3e4e4022e16d87065 |
| actions/upload-artifact | v4 | ea165f8d65b6e75b540449e92b4886f43607fa02 |
| android-actions/setup-android | v4.0.3 | 138b5fb1cf087fdb4c5f3c621466fe304d0cf2e3 |
Official upstream commit URLs use https://github.com/<owner>/<repo>/commit/<sha>. Resolve the intended release/reference at the official repository. Review commit provenance, action metadata, bundled code, changes and advisories before updating. Update the workflow references and the matching reviewed pin map in tests/unit/test_f03_r01.py together. Run the policy tests and full affected CI, including historical reproduction when changed. Preserve raw CI SHA evidence. Do not accept an arbitrary 40-character hash as trusted.
setup-java v4 declares deprecation and no future updates in its pinned action.yml. The current round deliberately freezes the already-tested implementation instead of combining a major upgrade with pinning. Track migration and review advisories separately. A pin prevents silent tag movement, not malicious upstream code or vulnerabilities. This policy does not replace Gradle verification/locking, full CVE/license/SBOM review, or independent review.
