# Bytefray 5.0.0 — Publication Record

This is a historical record of the GitHub publication of Bytefray 5.0.0. It
documents what was published, from what artifacts, and how the publication
was independently verified. It performs no qualification of its own — see
[`V5_FINAL_ARTIFACT_REBUILD_AND_CROSS_PLATFORM_REQUALIFICATION.md`](V5_FINAL_ARTIFACT_REBUILD_AND_CROSS_PLATFORM_REQUALIFICATION.md)
for that.

## 1. Release identity

| Item | Value |
|---|---|
| Release | Bytefray 5.0.0 |
| Publication date/time | 2026-09-16T01:40:20Z (`publishedAt`; created 2026-09-16T00:22:10Z) |
| GitHub Release URL | https://github.com/libertaine/Bytefray/releases/tag/v5.0.0 |

## 2. Provenance

| Item | Value |
|---|---|
| Artifact source SHA (`FINAL_SOURCE_SHA`) | `6827ae58d969ddbe483f3601749bb78014aa2c5f` |
| `v5.0.0` tag target (dereferenced, local and remote) | `6827ae58d969ddbe483f3601749bb78014aa2c5f` |

The `v5.0.0` tag is an annotated tag; its own tag-object SHA
(`592614070d2d6ddd0bee87649e080e343680e0e0`) differs from the commit it
points to, which is expected for an annotated tag. The dereferenced commit
(`git rev-parse "v5.0.0^{commit}"` locally, and `refs/tags/v5.0.0^{}` on
`origin` via `git ls-remote`) matches `FINAL_SOURCE_SHA` exactly on both
local and remote. The tag was not moved, recreated, or force-updated as part
of this publication.

## 3. Qualification

Qualification reference:
[`V5_FINAL_ARTIFACT_REBUILD_AND_CROSS_PLATFORM_REQUALIFICATION.md`](V5_FINAL_ARTIFACT_REBUILD_AND_CROSS_PLATFORM_REQUALIFICATION.md),
§24 ("Final publication gate — closeout"):

    FINAL 5.0.0 PUBLICATION QUALIFICATION PASSED —
    READY FOR RELEASE PUBLICATION

Read in full before publication, including its §22 addendum (which
independently refuted an initially-claimed WSL2 Linux GUI smoke pass before
accepting it, per this repository's qualification-tier-honesty standard) and
§23 (native Ubuntu GNOME/Wayland closeout on separate hardware, explicitly
distinguishing session-witnessed evidence from the user's first-hand,
non-session-witnessed report).

## 4. Public release assets

All four assets below were built under `dist/phase4b-final-6827ae5/` from
`FINAL_SOURCE_SHA` and are unchanged from the Phase 4B qualification report's
§4 artifact inventory. No artifact was rebuilt, substituted, or copied in
from any other `dist/` directory for this publication.

| Filename | Bytes | SHA-256 |
|---|---|---|
| `bytefray-5.0.0-py3-none-any.whl` | 1,068,017 | `94c4ec81b5428617d605db0468d360eeb0bf89b65671bc6c15302761310acb3a` |
| `bytefray-5.0.0.tar.gz` | 975,998 | `084902725c7237da13d97b17552db32625aaeec0cb35b52b04fac8bc0ff22d11` |
| `Bytefray-Setup-5.0.0.exe` | 101,243,431 | `13988e4330bd85105ada9fac9a42761bda4675ff72145367867bd4dc33220219` |
| `SHA256SUMS` | 277 | `66b007069b661f7c6e916468d48f852a7f9b214162d0d1db63abea7a782530c3` |

Asset-set determination (Section D of the publication task): the current
README documents exactly two Windows/Python distribution channels — the
standalone Windows installer and the wheel/sdist via `pip install` — with no
mention of a portable Windows ZIP or standalone loose executables as a
supported download. The most recent actual precedent in this version line
(`v5.0.0-rc1`) also shipped installer + checksums only. The four assets
above (wheel, sdist, installer, checksums) are exactly what the README
promises and what the Phase 4B report qualified; the four raw PyInstaller
`.exe` files inside `dist/phase4b-final-6827ae5/windows/*/` were
deliberately not published standalone, since each requires its adjacent
`_internal/` payload to run and publishing the bare `.exe` alone would be
non-functional. The `v4.0.0` release's `bytefray-4.0.0-windows.zip`
convention was considered and not followed, since it is not part of the
current README's documented install path and was not part of what Phase 4B
qualified as a unit.

## 5. SHA256SUMS

`SHA256SUMS` was generated from the exact three binary/package assets above
(basename only, one per line, lowercase hex, deterministic order: wheel,
sdist, installer), uploaded as a release asset, and independently verified
twice: once locally against the `dist/phase4b-final-6827ae5/` files before
upload, and again after downloading it back from GitHub (§6).

## 6. Post-upload verification

All four release assets were downloaded from GitHub into a clean temporary
directory (`…/scratchpad/release-verify/`, outside the `dist/` tree) after
publication and re-hashed with `Get-FileHash`. Every downloaded file matched
the corresponding local `dist/phase4b-final-6827ae5/` file exactly in both
byte count and SHA-256, and the downloaded `SHA256SUMS` content was
byte-identical to the uploaded manifest. No mismatch occurred.

## 7. Distribution channels

| Channel | Status |
|---|---|
| GitHub Release | **PUBLISHED** — https://github.com/libertaine/Bytefray/releases/tag/v5.0.0 |
| PyPI | **NOT PUBLISHED / NOT PART OF THIS RELEASE TASK** |

## 8. Repository state

| Ref | SHA at publication |
|---|---|
| `main` | `2d46bd36baf9850d2e25b32e617e08605be2caec` |
| `v5-research` | `dfad2e44c3fed5bc93fe520d90bced44ecc3c4a3` |

Both were confirmed unchanged from the values recorded in the publication
task's pre-flight check; the release itself was created against the existing
`v5.0.0` tag and did not require any code change, so neither ref moved as
part of publishing.

## 9. Final verdict

    BYTEFRAY 5.0.0 RELEASED SUCCESSFULLY
