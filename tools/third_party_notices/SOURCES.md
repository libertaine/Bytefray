# Third-party license texts for the Windows distribution

`tools/collect_third_party_notices.py` copies these files into the frozen
distribution's `licenses/` folder, together with license files it reads from
the build environment itself (the Python runtime, PySide6, pygame-ce, PyYAML,
PyInstaller and Bytefray Spectator). They are kept here, rather than
downloaded during a build, so a build needs no network access and always ships
the same texts.

Each file is the unmodified upstream text. Hashes are SHA-256 of the file with
LF line endings (the repository stores these files with LF).

| File | Upstream source | SHA-256 |
| --- | --- | --- |
| `gnu/lgpl-3.0.txt` | https://www.gnu.org/licenses/lgpl-3.0.txt | `e3a994d82e644b03a792a930f574002658412f62407f5fee083f2555c5f23118` |
| `gnu/gpl-3.0.txt` | https://www.gnu.org/licenses/gpl-3.0.txt | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |
| `godot-4.7.2-stable/LICENSE.txt` | https://raw.githubusercontent.com/godotengine/godot/4.7.2-stable/LICENSE.txt | `b0435e3b3e4e55238f05f4b306f30524a1b2e20147810d436eaa554fa6855c80` |
| `godot-4.7.2-stable/COPYRIGHT.txt` | https://raw.githubusercontent.com/godotengine/godot/4.7.2-stable/COPYRIGHT.txt | `cb1980c88089573bcacd7221d777c689bb8bbd778799f24c27fca0fe5f774d6d` |
| `pygame-ce-2.5.8/LICENSE.*.txt` (20 files) | https://github.com/pygame-community/pygame-ce/tree/2.5.8/docs/licenses | see below |

pygame-ce 2.5.8 `docs/licenses/`:

| File | SHA-256 |
| --- | --- |
| `LICENSE.FLAC.txt` | `eafd0d3fac93964d4274a2f99be928d41c167a925a9ddb8621ab9aee065f8fee` |
| `LICENSE.fluidsynth.txt` | `9b872a8a070b8ad329c4bd380fb1bf0000f564c75023ec8e1e6803f15364b9e9` |
| `LICENSE.freetype.txt` | `08c135755dd589039470f1fdbb400daaabaaa50d0b366d19cebff4d22986baa1` |
| `LICENSE.jpeg.txt` | `9958e43a298e61bd287d89d382dafbb2d8346dcb3b7d166b8d70e21ab6d18cf8` |
| `LICENSE.modplug.txt` | `708581155da4f72895bb8a5ac80609d75774c29d0c5e05e41417bc21b6ed294c` |
| `LICENSE.mpg123.txt` | `4caef0a17e05b6f9ac36f899941a7d2f41ad911836452718f3accdd7d8305d8e` |
| `LICENSE.numpy.txt` | `faaa516b85dbf609b0296918d61924e3145c9d2b8d91ea5be93e7ba073a78aa1` |
| `LICENSE.ogg-vorbis.txt` | `414bfd5d8ee64395a9231d6386188461500052c10915bee08b18bfa9489dd0b3` |
| `LICENSE.opus.txt` | `8338ce8d922bb4416ce3dd1e5680173332435e3f0755007ac7801ccd674fe682` |
| `LICENSE.opusfile.txt` | `0267ae795ab744c4e0f9c45e249440fdf2e75dac8c804f36066b28649bf74aaf` |
| `LICENSE.png.txt` | `bf5e22b9dce8464064ae17a48ea1133c3369ac9e1d80ef9e320e5219aa14ea9b` |
| `LICENSE.portmidi.txt` | `eb5d0724b2ae76a94ae804c44b3d6cfaaca822b7d42907aefa9256cb93db6fe0` |
| `LICENSE.sdl2.txt` | `7a771248ca372e2dff4887c921543699847ae44c56d7558692f5860237f1f914` |
| `LICENSE.sdl2_image.txt` | `13d8725c1eec72984ac99449d2bc0f674ad956d67ae5819e787620e6c7b509e2` |
| `LICENSE.sdl2_mixer.txt` | `c70bbdde99ecb6d521d7806256b49dcc1a014bf5e28fca06ac031e1eeaea87f2` |
| `LICENSE.sdl_gfx.txt` | `63744690fa28ecf2a9dedacafb08d1209031e7eff1820430d952264f678a1bcf` |
| `LICENSE.sse2neon-h.txt` | `ada11c843d252c0b70837629ac7a54a525ecb7d8c0932ebccf863c55dbd32cb1` |
| `LICENSE.tiff.txt` | `92b72ba97e6c2749c2a94bc0ef646b47080217f1e772a482b33cf5a5f98a6506` |
| `LICENSE.webp.txt` | `5aec868f669e384a22372a4e8a1a6cd7d44c64cd451f960ca69cc170d1e13acf` |
| `LICENSE.zlib.txt` | `464352f7afcece608041241e20b28e8006ae170446898e9713fb076323d1487d` |

## `sdl-windows-prebuilts/` — the libraries inside the pygame-ce 2.5.8 Windows wheel

pygame-ce 2.5.8's `buildconfig/download_win_prebuilt.py` builds its Windows
wheel from the upstream SDL release packages below (it pins their SHA-1s, which
these downloads matched). Every DLL of theirs that the frozen Bytefray trees
contain is byte-identical to the package's x64 copy, so the license files those
packages ship are the ones for the shipped binaries. Only the texts for shipped
libraries were kept (not `libavif`, `dav1d` or `libgme`).

| Package (SHA-1) | Files |
| --- | --- |
| `SDL2-devel-2.32.10-VC.zip` (`27f5179346a0b0db80c4dd1769c7c9d62b9a91f3`) | `SDL2-2.32.10/LICENSE.txt` |
| `SDL2_image-devel-2.8.12-VCpgce.zip` (`77058bbf460c7701d60b27e82bec17b529d55014`) | `SDL2_image-2.8.12/LICENSE.txt`, and from `lib/x64/optional/`: `LICENSE.libjpegturbo.md`, `LICENSE.tiff.txt`, `LICENSE.webp.txt` |
| `SDL2_mixer-devel-2.8.2-VC.zip` (`7e01cc961326ec44a61009c61a409310489aee6b`) | `SDL2_mixer-2.8.2/LICENSE.txt`, and from `lib/x64/optional/`: `LICENSE.ogg-vorbis.txt`, `LICENSE.opus.txt`, `LICENSE.opusfile.txt`, `LICENSE.wavpack.txt` (WavPack 5.6.0), `LICENSE.xmp.txt` (libxmp, MIT) |
| `SDL2_ttf-devel-2.24.0-VC.zip` (`2d18b9a4fc2ec0eee80de2a946b088d4e6efd0ee`) | `SDL2_ttf-2.24.0/LICENSE.txt` |

`SDL2_ttf.dll` links FreeType and HarfBuzz statically (it imports only
`KERNEL32.dll` and `SDL2.dll`). Their texts come from the commits SDL_ttf
`release-2.24.0` vendors as submodules:
`vendored/harfbuzz-COPYING.txt` from libsdl-org/harfbuzz
`e18e66409d0136cc8f8b05aac791f84314520676` (`COPYING`), and
`vendored/freetype-LICENSE.txt` and `vendored/freetype-FTL.txt` from
libsdl-org/freetype `12c5e620858bd503731091e9371d06c0a3e7c967` (`LICENSE.TXT`,
`docs/FTL.TXT`).

## `qt-6.11.2/QT_THIRD_PARTY_NOTICES.txt`

The text of https://doc.qt.io/qt-6.11/licenses-used-in-qt.html ("The following
sections list third-party components in Qt 6.11.2") and of the 53 component
pages it links for the Qt modules the frozen applications ship (Qt Core, Qt GUI,
Qt Image Formats, Qt Network, Qt SVG) plus Mesa llvmpipe (`opengl32sw.dll`),
converted from HTML to text without other changes. Qt Quick, QML, OpenGL, PDF
and Virtual Keyboard are not shipped (`tools/omit_unused_qt.py`).

| File | SHA-256 (LF) |
| --- | --- |
| `qt-6.11.2/QT_THIRD_PARTY_NOTICES.txt` | `3bb59575a35c8a4fb6f26b1a17f955bb35936e4b6114a0880a7128c53ca9a463` |
| `sdl-windows-prebuilts/SDL2-2.32.10/LICENSE.txt` | `97f35b302b361680ec1e891e95d2d52097bb95abff361434916d99dc1305f127` |
| `sdl-windows-prebuilts/SDL2_image-2.8.12/LICENSE.libjpegturbo.md` | `ba6bceebcba0fdd35488477c2cca8c4632ce82c74dbfbc87d886ce6fc4433579` |
| `sdl-windows-prebuilts/SDL2_image-2.8.12/LICENSE.tiff.txt` | `fbd6fed7938541d2c809c0826225fc85e551fdbfa8732b10f0c87e0847acafd7` |
| `sdl-windows-prebuilts/SDL2_image-2.8.12/LICENSE.txt` | `7826eca0a0f7e591f38dd844e207a200aac81a59b20d8a30c3af8c6282af13e6` |
| `sdl-windows-prebuilts/SDL2_image-2.8.12/LICENSE.webp.txt` | `5aec868f669e384a22372a4e8a1a6cd7d44c64cd451f960ca69cc170d1e13acf` |
| `sdl-windows-prebuilts/SDL2_mixer-2.8.2/LICENSE.ogg-vorbis.txt` | `ec1815db59fcd302846df949d7424876cb2e2dc5ed1606c5fb0b36787b1cf43a` |
| `sdl-windows-prebuilts/SDL2_mixer-2.8.2/LICENSE.opus.txt` | `8338ce8d922bb4416ce3dd1e5680173332435e3f0755007ac7801ccd674fe682` |
| `sdl-windows-prebuilts/SDL2_mixer-2.8.2/LICENSE.opusfile.txt` | `0267ae795ab744c4e0f9c45e249440fdf2e75dac8c804f36066b28649bf74aaf` |
| `sdl-windows-prebuilts/SDL2_mixer-2.8.2/LICENSE.txt` | `7826eca0a0f7e591f38dd844e207a200aac81a59b20d8a30c3af8c6282af13e6` |
| `sdl-windows-prebuilts/SDL2_mixer-2.8.2/LICENSE.wavpack.txt` | `275d65ec11a78d552d078b9c26d950e3075892bca895a415ceaaec33bcfabff9` |
| `sdl-windows-prebuilts/SDL2_mixer-2.8.2/LICENSE.xmp.txt` | `f34309e37033bd4da61f5448d18b7a1280336b00eb18d5e4165c1c509a9c318c` |
| `sdl-windows-prebuilts/SDL2_ttf-2.24.0/LICENSE.txt` | `7826eca0a0f7e591f38dd844e207a200aac81a59b20d8a30c3af8c6282af13e6` |
| `sdl-windows-prebuilts/SDL2_ttf-2.24.0/vendored/freetype-FTL.txt` | `08c135755dd589039470f1fdbb400daaabaaa50d0b366d19cebff4d22986baa1` |
| `sdl-windows-prebuilts/SDL2_ttf-2.24.0/vendored/freetype-LICENSE.txt` | `2e3bbb7d7c5c396368dd0853a790ec29ce5b8647163dde42a0493fb0d6556b2b` |
| `sdl-windows-prebuilts/SDL2_ttf-2.24.0/vendored/harfbuzz-COPYING.txt` | `ba8f810f2455c2f08e2d56bb49b72f37fcf68f1f4fade38977cfd7372050ad64` |

Update these files, and these tables, whenever the build's Godot, pygame-ce or
Qt version changes.
