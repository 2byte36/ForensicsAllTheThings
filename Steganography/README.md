# Steganography and media

[Home](../README.md) · [Quick reference](../QUICKSTART.md) · [Reference library](../REFERENCES.md)

Use structure and signal clues to choose the channel, bitplane, or encoding worth testing.

## Summary

- [Tools and setup](#tools-and-setup)
- [Script and command recipe](#script-and-command-recipe)
- [Images](#images)
- [Video frame sampling](#video-frame-sampling)
- [Audio and spectrograms](#audio-and-spectrograms)
- [Framing and error correction](#framing-and-error-correction)
- [Choose the right stego tool](#choose-the-right-stego-tool)
- [Text and metadata channels](#text-and-metadata-channels)
- [References](#references)

## Tools and setup

Linux package commands below target Debian/Ubuntu-family systems, including a Linux shell in WSL. Use [SETUP.md](../SETUP.md) for the shared Python environment, PATH notes, Windows tools, and other platforms. Install only the tools needed for your artifact.

| Tool | Purpose | Install / upstream setup | Verify |
| --- | --- | --- | --- |
| Python 3 | Repository helpers | `sudo apt install python3 python3-venv`. [Source](https://www.python.org/downloads/) | `python3 --version` |
| Pillow | Image bitplanes | In the Python venv: `python -m pip install Pillow`. [Source](https://pillow.readthedocs.io/en/stable/installation/basic-installation.html) | `python -m PIL` |
| FFmpeg / SoX / pngcheck | Media and PNG analysis | `sudo apt install ffmpeg sox pngcheck`. [Source](https://ffmpeg.org/download.html) | `ffmpeg -version`; `sox --version`; `pngcheck -h` |
| zsteg | PNG/BMP steganography | Install Ruby, then `gem install --user-install zsteg`; add the gem executable directory to PATH. [Source](https://github.com/zed-0xff/zsteg#installation) | `zsteg --help` |
| steghide | Supported carrier extraction | `sudo apt install steghide`. [Source](https://steghide.sourceforge.net/download.php) | `steghide --version` |
| ExifTool | Metadata | `sudo apt install libimage-exiftool-perl`. [Source](https://exiftool.org/install.html) | `exiftool -ver` |

## Script and command recipe

Helper: [lsb_extract.py](../scripts/helpers/lsb_extract.py). See [the script catalog](../SCRIPTS.md) for runtime requirements and failure behavior.

Run from the repository root. Set `CASE` to an existing case directory outside this repository; filenames are examples to replace with your evidence paths.

```bash
CASE=/absolute/path/to/case
mkdir -p "$CASE/work" "$CASE/carved" "$CASE/extracts"
python3 scripts/helpers/lsb_extract.py "$CASE/image.png" "$CASE/carved/blue-lsb.bin" --channel B --bit 0 --order msb
```

Extracts row-major bits from a native RGB/RGBA image with explicit byte packing. Requires Pillow. Rejects absent channels, palette/grayscale modes, and pixel counts not divisible by eight. Does not strip padding or locate a payload automatically.

## Images

```bash
exiftool image.png
pngcheck -v image.png
binwalk image.png
zsteg image.png
```

`zsteg` targets supported PNG/BMP data; it is not a universal stego detector. Inspect alpha, palette, individual channels, bitplanes, appended bytes, and dimensions. Many reported strings will be false positives.

Display the blue channel's lowest bit with Pillow:

```bash
python3 - <<'PYCODE'
from PIL import Image
im = Image.open('image.png').convert('RGB')
blue = im.getchannel('B')
blue.point(lambda value: (value & 1) * 255).save('work/blue-bit0.png')
PYCODE
```

**a bit plan** used blue bit 0. **Evaporated** needed structural repair before meaningful stego analysis. See [file triage](../File-Triage/README.md) for signatures and PNG CRCs.

## Video frame sampling

```bash
ffprobe -v error -show_streams -show_format clip.avi
mkdir -p work/frames
ffmpeg -i clip.avi -vf 'select=gte(n\,52)*not(mod(n-52\,10))' \
  -fps_mode vfr work/frames/%06d.png
```

This example uses zero-based frame indices and selects 52, 62, 72, …; verify the challenge's indexing convention. Lossy re-encoding can destroy pixel LSBs. Preserve the original and extract losslessly where possible.

**Moai** encoded two characters in selected frames' blue-channel LSBs. OpenCV arrays are normally BGR; Pillow RGB arrays use a different channel order. Record bit order, pixel traversal, channel, frame sequence, and byte packing.

## Audio and spectrograms

```bash
ffprobe -v error -show_streams -show_format audio.wav
sox audio.wav -n spectrogram -o work/spectrogram.png
# Audition or inspect the difference between stereo channels:
ffmpeg -i audio.wav -af 'pan=mono|c0=c0-c1' work/difference.wav
```

Inspect sample rate, bit depth, integer versus floating-point samples, and channel count before extracting LSBs. Filtering or resampling can destroy low bits. Keep the original PCM bytes for bit-level analysis. Subtract channels in a wide numeric type for exact analysis to avoid overflow/clipping.

Useful branches: visible spectrogram text, Morse/OOK, FSK/ASK, SSTV, channel differences, sample bitplanes, and metadata clues. Let the spectrum and file structure guide the choice.

## Framing and error correction

For a digital signal, recover symbol rate, carrier/threshold, preamble, bit order, interleaver, error-correction code, length, and checksum before interpreting payload text. Validate CRCs and authentication tags rather than accepting the first readable output.

**key item get** combined a Morse hint, a right-channel LSB recovery block, and a real signal in the left-minus-right channel. Other decoded carriers were decoys. Its seed, frequencies, and frame layout are specific to that challenge.

**From Outer Space** used SSTV. **Secret Signal** treated video as encoded storage; a media extension on the extracted result did not guarantee it was a video file.

## Choose the right stego tool

| Carrier | First candidates | Limitation |
| --- | --- | --- |
| PNG / BMP | zsteg, channels, alpha, palette, bitplanes | Byte traversal and bit order vary |
| JPEG | Metadata, appended data, steghide when indicated | Lossy pixels are unsuitable for naive PNG-style LSB assumptions |
| WAV / AU | PCM bits, channels, steghide when indicated | Sample encoding and channel interleaving matter |
| Animated GIF | Individual frames, delays, palette, frame differences | Composited frames differ from raw update rectangles |
| QR / barcode | Orientation, contrast, quiet zone, multiple symbols | Text order must come from layout or sequence clues |

```bash
steghide info image.jpg
# Prompts for the passphrase; use a known case value or test empty only if justified.
steghide extract -sf image.jpg -xf extracts/hidden.bin
```

No steghide result does not rule out other embedding methods. Conversely, arbitrary strings from a bitplane search need framing or a valid embedded file before being accepted.

## Text and metadata channels

Inspect comments, EXIF/XMP, filenames, whitespace, and Unicode code points when the visible image or text is uninformative. For suspicious text:

```bash
python3 - <<'PYCODE'
from pathlib import Path
import unicodedata
for index, char in enumerate(Path('message.txt').read_text(encoding='utf-8')):
    if not char.isascii() or char in '\t\r':
        print(index, f'U+{ord(char):04X}', unicodedata.name(char, 'UNNAMED'))
PYCODE
```

These indices are characters, not byte offsets. Zero-width characters, homoglyphs, or line-ending differences can encode data, but multilingual text also contains them legitimately. Preserve normalization and original bytes before testing an encoding hypothesis.

## References

- [Steghide documentation](https://steghide.sourceforge.net/documentation.php)
- [Python Unicode database](https://docs.python.org/3/library/unicodedata.html)
- [NCLP — image, SSTV, and video techniques](https://2byte36.github.io/blog/nclp-ctf-s1)
- [GCW quals — Moai](https://2byte36.github.io/blog/gcw-2026-quals)
- [JOINTS — key item get](https://2byte36.github.io/blog/joints-2026-quals)
- [zsteg](https://github.com/zed-0xff/zsteg)
