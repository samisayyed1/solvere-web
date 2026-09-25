#!/usr/bin/env python3
"""Unpack a .conda package (a zip of zstd tarballs) without a zstd binary (ADR-001 §8.L).

    unconda.py <file.conda> <dest-dir>

Decompression uses the zstandard wheel pinned below, run through `uv run` so the host needs
only python3 and uv. The caller has already checked the .conda file's sha256.
"""
from __future__ import annotations

import io
import subprocess
import sys
import tarfile
import zipfile

ZSTANDARD = "zstandard==0.25.0"
DECOMPRESS = (
    "import sys, zstandard; "
    "sys.stdout.buffer.write(zstandard.ZstdDecompressor().stream_reader(sys.stdin.buffer).read())"
)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src, dest = argv
    z = zipfile.ZipFile(src)
    name = next((n for n in z.namelist() if n.startswith("pkg-") and n.endswith(".tar.zst")), None)
    if name is None:
        print(f"unconda: {src} has no pkg-*.tar.zst member", file=sys.stderr)
        return 1
    raw = subprocess.run(
        ["uv", "run", "--no-project", "--with", ZSTANDARD, "python", "-c", DECOMPRESS],
        input=z.read(name), capture_output=True, check=True,
    ).stdout
    tarfile.open(fileobj=io.BytesIO(raw)).extractall(dest, filter="data")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
