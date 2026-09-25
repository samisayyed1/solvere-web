#!/usr/bin/env python3
"""User-space .deb installer for the Linux toolchain path (ADR-001 §8.L). Stdlib only.

KiCad's official Linux build is the kicad-10.0-releases PPA. Installing it with apt needs
root and drifts with the live archive, so instead:

  lock     resolve the root packages' Depends closure against a dated Ubuntu snapshot plus
           the PPA, minus what the host already has, and write debs.lock.json
           (name, version, url, sha256) for every .deb.
  install  download exactly what the lock names, check each sha256, and unpack it with
           `dpkg-deb -x` into a prefix. Nothing touches /usr or the dpkg database.

Trust chain on `lock`: each InRelease is checked with gpgv against a pinned keyring (the
Ubuntu archive keyring for the snapshot; the PPA key, pinned by fingerprint, for the PPA),
each Packages index is checked against the sha256 in its InRelease, and each .deb sha256
comes from that index. On `install`, the committed lock is the trust root.

  debfetch.py lock    --config debs.config.json --out debs.lock.json
  debfetch.py install --lock debs.lock.json --prefix ~/.forge/opt/kicad --cache ~/.forge/downloads/debs
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


class FetchError(RuntimeError):
    pass


def http_get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=300) as r:  # noqa: S310 (pinned https URLs)
        return r.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def gpgv_verify(inrelease: bytes, keyring: Path) -> bytes:
    """Verify a clearsigned InRelease; return the signed text. Raises on a bad signature."""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td, "InRelease")
        f.write_bytes(inrelease)
        out = Path(td, "out")
        p = subprocess.run(["gpgv", "--keyring", str(keyring), "--output", str(out), str(f)],
                           capture_output=True, text=True)
        if p.returncode != 0:
            raise FetchError(f"gpgv rejected InRelease: {p.stderr.strip()[-400:]}")
        return out.read_bytes()


def fetch_ppa_keyring(fingerprint: str, dest: Path) -> Path:
    """Fetch the PPA key from keyserver.ubuntu.com and refuse it unless the fingerprint matches."""
    key = http_get(f"https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x{fingerprint}")
    with tempfile.TemporaryDirectory() as home:
        env = {**os.environ, "GNUPGHOME": home}
        subprocess.run(["gpg", "--batch", "--import"], input=key, env=env, check=True, capture_output=True)
        p = subprocess.run(["gpg", "--batch", "--with-colons", "--fingerprint"], env=env,
                           capture_output=True, text=True, check=True)
        fprs = [ln.split(":")[9] for ln in p.stdout.splitlines() if ln.startswith("fpr:")]
        if fingerprint.upper() not in fprs:
            raise FetchError(f"keyserver key fingerprints {fprs} do not include pinned {fingerprint}")
        exported = subprocess.run(["gpg", "--batch", "--export", fingerprint], env=env,
                                  capture_output=True, check=True).stdout
    dest.write_bytes(exported)
    return dest


def parse_packages(text: str) -> dict[str, dict[str, str]]:
    pkgs: dict[str, dict[str, str]] = {}
    for stanza in text.split("\n\n"):
        fields: dict[str, str] = {}
        last = None
        for line in stanza.splitlines():
            if line.startswith((" ", "\t")) and last:
                fields[last] += "\n" + line
            elif ":" in line:
                k, v = line.split(":", 1)
                fields[k] = v.strip()
                last = k
        if "Package" in fields:
            name = fields["Package"]
            # Keep the highest version seen (later suites in the config override earlier ones).
            pkgs[name] = fields
    return pkgs


def load_repo(repo: dict, keyring: Path) -> dict[str, dict[str, str]]:
    base = repo["base"].rstrip("/")
    signed = gpgv_verify(http_get(f"{base}/dists/{repo['suite']}/InRelease"), keyring).decode()
    hashes: dict[str, str] = {}
    in_sha = False
    for line in signed.splitlines():
        if line.startswith("SHA256:"):
            in_sha = True
            continue
        if in_sha:
            if not line.startswith(" "):
                in_sha = False
                continue
            h, _size, path = line.split()
            hashes[path] = h
    out: dict[str, dict[str, str]] = {}
    for comp in repo["components"]:
        rel = f"{comp}/binary-amd64/Packages.gz"
        data = http_get(f"{base}/dists/{repo['suite']}/{rel}")
        if hashes.get(rel) != sha256(data):
            raise FetchError(f"{base} {repo['suite']} {rel}: sha256 not in signed InRelease")
        for name, f in parse_packages(gzip.decompress(data).decode("utf-8", "replace")).items():
            f["_base"] = base
            out[name] = f
    return out


def host_installed() -> set[str]:
    status = Path("/var/lib/dpkg/status")
    if not status.exists():
        return set()
    names = set()
    for st in status.read_text(errors="replace").split("\n\n"):
        m = re.search(r"^Package: (\S+)", st, re.M)
        if m and re.search(r"^Status: install ok installed", st, re.M):
            names.add(m.group(1))
    return names


def dep_alternatives(field: str) -> list[list[str]]:
    groups = []
    for grp in field.split(","):
        alts = []
        for a in grp.split("|"):
            a = re.sub(r"\(.*?\)|\[.*?\]|<.*?>", "", a).strip()
            if a:
                alts.append(a.split(":")[0])
        if alts:
            groups.append(alts)
    return groups


def resolve(roots: list[str], index: dict[str, dict[str, str]], have: set[str],
            exclude: set[str]) -> list[dict[str, str]]:
    provides: dict[str, str] = {}
    for name, f in index.items():
        for grp in dep_alternatives(f.get("Provides", "")):
            provides.setdefault(grp[0], name)
    chosen: dict[str, dict[str, str]] = {}
    queue = list(roots)
    while queue:
        name = queue.pop()
        if name in chosen or name in exclude:
            continue
        if name in have and name not in roots:
            continue
        f = index.get(name) or index.get(provides.get(name, ""))
        if f is None:
            raise FetchError(f"unresolvable dependency: {name}")
        if f["Package"] in chosen:
            continue
        chosen[f["Package"]] = f
        for field in ("Pre-Depends", "Depends"):
            for alts in dep_alternatives(f.get(field, "")):
                if any(a in have or a in chosen for a in alts):
                    continue
                pick = next((a for a in alts if a in index or a in provides), None)
                if pick is None:
                    raise FetchError(f"{f['Package']}: none of {alts} resolvable")
                queue.append(pick)
    return [
        {"package": f["Package"], "version": f["Version"],
         "url": f"{f['_base']}/{f['Filename']}", "sha256": f["SHA256"], "size": int(f["Size"])}
        for f in sorted(chosen.values(), key=lambda x: x["Package"])
    ]


def cmd_lock(a: argparse.Namespace) -> int:
    cfg = json.loads(Path(a.config).read_text())
    index: dict[str, dict[str, str]] = {}
    with tempfile.TemporaryDirectory() as td:
        ppa_ring = fetch_ppa_keyring(cfg["ppa_fingerprint"], Path(td, "ppa.gpg"))
        for repo in cfg["repos"]:
            ring = ppa_ring if repo.get("keyring") == "ppa" else Path(cfg["ubuntu_keyring"])
            index.update(load_repo(repo, ring))
    have = host_installed()
    debs = resolve(cfg["roots"], index, have, set(cfg.get("exclude", [])))
    for pin in cfg.get("pins", []):
        got = next((d for d in debs if d["package"] == pin["package"]), None)
        if not got or got["version"] != pin["version"] or got["sha256"] != pin["sha256"]:
            raise FetchError(f"pin mismatch for {pin['package']}: got {got}")
    lock = {"schema": 1, "config": cfg, "host_had": sorted(have & {d for d in index}),
            "debs": debs, "total_bytes": sum(d["size"] for d in debs)}
    Path(a.out).write_text(json.dumps(lock, indent=1) + "\n")
    print(f"locked {len(debs)} debs, {lock['total_bytes'] / 1e6:.1f} MB -> {a.out}")
    return 0


def cmd_install(a: argparse.Namespace) -> int:
    lock = json.loads(Path(a.lock).read_text())
    cache = Path(a.cache).expanduser()
    prefix = Path(a.prefix).expanduser()
    cache.mkdir(parents=True, exist_ok=True)
    prefix.mkdir(parents=True, exist_ok=True)
    for d in lock["debs"]:
        f = cache / Path(d["url"]).name
        if not f.exists() or sha256(f.read_bytes()) != d["sha256"]:
            f.write_bytes(http_get(d["url"]))
        got = sha256(f.read_bytes())
        if got != d["sha256"]:
            raise FetchError(f"sha256 mismatch for {f.name}: got {got} expected {d['sha256']}")
        subprocess.run(["dpkg-deb", "-x", str(f), str(prefix)], check=True)
    print(f"installed {len(lock['debs'])} debs into {prefix}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    lk = sub.add_parser("lock")
    lk.add_argument("--config", required=True)
    lk.add_argument("--out", required=True)
    ins = sub.add_parser("install")
    ins.add_argument("--lock", required=True)
    ins.add_argument("--prefix", required=True)
    ins.add_argument("--cache", required=True)
    a = ap.parse_args(argv)
    try:
        return cmd_lock(a) if a.cmd == "lock" else cmd_install(a)
    except FetchError as e:
        print(f"debfetch: FAIL: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
