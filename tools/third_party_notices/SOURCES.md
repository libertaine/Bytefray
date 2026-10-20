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

Update these files, and this table, whenever the build's Godot, pygame-ce or
Qt licensing changes.
