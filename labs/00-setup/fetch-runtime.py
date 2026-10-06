#!/usr/bin/env python3
"""Download the prebuilt llama.cpp release binaries for this machine.

Replaces compiling llama-cpp-python with CMAKE_ARGS. The release archive is
10-35 MB (CUDA builds are larger), ships llama-server + llama-bench + llama-cli,
and is new enough to load Gemma 4 (architecture "gemma4", April 2026).

    .venv/bin/python labs/00-setup/fetch-runtime.py            # auto-pick from hardware.json
    .venv/bin/python labs/00-setup/fetch-runtime.py --list      # show all assets, pick nothing
    .venv/bin/python labs/00-setup/fetch-runtime.py --asset llama-b10488-bin-win-vulkan-x64.zip
"""
from __future__ import annotations

import argparse
import json
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "lib"))
import labkit  # noqa: E402

REPO = "ggml-org/llama.cpp"
BUILD = labkit.LLAMA_CPP_BUILD

# Accelerator keywords that appear in asset names. "plain" = none of these.
ALL_ACCEL = ("cuda", "vulkan", "rocm", "hip", "sycl", "openvino", "cann", "musa")
# Never auto-pick these: vendor toolchains needing a separate SDK, or non-laptop targets.
NEVER = ("sycl", "openvino", "cann", "musa", "musl", "opencl", "adreno", "android", "s390x")

# Fallback if the GitHub API is rate-limited (a whole classroom shares one NAT).
# Keyed by (os_token, arch_token, accel). Covers every platform docs/HARDWARE-GUIDE.md
# promises, so a rate-limited classroom is never told to go compile instead.
FALLBACK_ASSETS = {
    ("-macos-", "arm64", "plain"): f"llama-{BUILD}-bin-macos-arm64.tar.gz",
    ("-macos-", "x64", "plain"): f"llama-{BUILD}-bin-macos-x64.tar.gz",
    ("-ubuntu-", "x64", "plain"): f"llama-{BUILD}-bin-ubuntu-x64.tar.gz",
    ("-ubuntu-", "x64", "vulkan"): f"llama-{BUILD}-bin-ubuntu-vulkan-x64.tar.gz",
    ("-ubuntu-", "arm64", "plain"): f"llama-{BUILD}-bin-ubuntu-arm64.tar.gz",
    ("-ubuntu-", "arm64", "vulkan"): f"llama-{BUILD}-bin-ubuntu-vulkan-arm64.tar.gz",
    ("-win-", "x64", "plain"): f"llama-{BUILD}-bin-win-cpu-x64.zip",
    ("-win-", "x64", "vulkan"): f"llama-{BUILD}-bin-win-vulkan-x64.zip",
    ("-win-", "x64", "cuda"): f"llama-{BUILD}-bin-win-cuda-12.4-x64.zip",
    ("-win-", "x64", "rocm"): f"llama-{BUILD}-bin-win-rocm-7.14-x64.zip",
    ("-win-", "arm64", "plain"): f"llama-{BUILD}-bin-win-cpu-arm64.zip",
}


def platform_token() -> tuple[str, str]:
    """(os_token, arch_token) matched independently.

    Asset names interleave the accelerator between the two -- e.g.
    "ubuntu-vulkan-x64" -- so a single "ubuntu-x64" substring test would throw
    away every accelerated Linux build.
    """
    machine = platform.machine().lower()
    arm = machine in ("arm64", "aarch64")
    if sys.platform == "darwin":
        return "-macos-", "arm64" if arm else "x64"
    if sys.platform.startswith("linux"):
        return "-ubuntu-", "arm64" if arm else "x64"
    if sys.platform == "win32":
        return "-win-", "arm64" if arm else "x64"
    labkit.die(f"Unsupported platform: {sys.platform}")
    return "", ""


def driver_cuda_version() -> tuple[int, int] | None:
    """Max CUDA version this NVIDIA driver supports, from nvidia-smi."""
    if not shutil.which("nvidia-smi"):
        return None
    try:
        out = subprocess.run(
            ["nvidia-smi"], capture_output=True, text=True, timeout=10, check=False
        ).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"CUDA Version:\s*(\d+)\.(\d+)", out)
    return (int(m.group(1)), int(m.group(2))) if m else None


def accel_preference(hw: dict) -> list[str]:
    b = hw.get("gpu", {}).get("backends", {})
    if b.get("nvidia_cuda"):
        return ["cuda", "vulkan", "plain"]
    if b.get("amd_rocm"):
        return ["rocm", "hip", "vulkan", "plain"]
    if b.get("vulkan"):
        return ["vulkan", "plain"]
    # Apple Metal is compiled into the standard macOS build -- nothing to pick.
    return ["plain"]


def list_assets() -> list[str]:
    url = f"https://api.github.com/repos/{REPO}/releases/tags/{BUILD}"
    req = urllib.request.Request(url, headers={"User-Agent": "day20-lab"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return [a["name"] for a in json.loads(r.read())["assets"]]
    except (urllib.error.URLError, urllib.error.HTTPError, KeyError, ValueError) as exc:
        print(f"    (GitHub API unavailable: {exc} -- using the built-in name table)")
        return []


def pick_asset(assets: list[str], token: str, prefs: list[str]) -> str | None:
    os_tok, arch_tok = token

    def platform_ok(name: str) -> bool:
        low = name.lower()
        if os_tok not in low:
            return False
        # Arch lives at the end of the name; arm64 and x64 must not cross-match.
        other = "x64" if arch_tok == "arm64" else "arm64"
        return arch_tok in low and other not in low

    # Only the real binary bundles: skips cudart-*, llama-*-ui, llama-*-xcframework.
    prefix = f"llama-{BUILD}-bin-"
    pool = [
        a for a in assets
        if a.startswith(prefix) and platform_ok(a) and not any(n in a.lower() for n in NEVER)
    ]
    if not pool:
        return None

    for pref in prefs:
        if pref == "plain":
            plain = [a for a in pool if not any(k in a.lower() for k in ALL_ACCEL)]
            if plain:
                return sorted(plain, key=len)[0]
            continue
        matches = [a for a in pool if pref in a.lower()]
        if not matches:
            continue
        if pref == "cuda":
            # Pick the newest CUDA the installed driver can actually run.
            driver = driver_cuda_version()
            versioned = []
            for a in matches:
                m = re.search(r"cuda-(\d+)\.(\d+)", a.lower())
                if m:
                    versioned.append(((int(m.group(1)), int(m.group(2))), a))
            if versioned:
                versioned.sort()
                if driver:
                    usable = [a for v, a in versioned if v <= driver]
                    if usable:
                        return usable[-1]
                    # An asset newer than the driver will not load. Skip CUDA entirely
                    # and let the next preference (Vulkan, then CPU) win.
                    print(f"    (no CUDA build works with driver {driver[0]}.{driver[1]} -- "
                          f"falling back to the next backend)")
                    continue
                return versioned[0][1]
        return sorted(matches, key=len)[0]
    return None


def download(asset: str, dest: pathlib.Path) -> pathlib.Path:
    url = f"https://github.com/{REPO}/releases/download/{BUILD}/{asset}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out = dest.parent / asset
    print(f"==> Downloading {asset} using curl")
    print(f"    {url}")
    try:
        subprocess.run(["curl.exe", "-L", "-#", "-o", str(out), url], check=True)
    except subprocess.CalledProcessError as exc:
        labkit.die(
            f"Download failed: {exc}",
            f"Fetch it manually from https://github.com/{REPO}/releases/tag/{BUILD}",
            f"and unzip into {dest.parent}/",
        )
    return out


def extract(archive: pathlib.Path, into: pathlib.Path) -> None:
    print(f"==> Extracting into {into.relative_to(labkit.repo_root())}/")
    into.mkdir(parents=True, exist_ok=True)
    if archive.name.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive) as tf:
            try:
                tf.extractall(into, filter="data")  # Python 3.12+: blocks path traversal
            except TypeError:
                tf.extractall(into)
    elif archive.suffix == ".zip":
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(into)
        # zipfile drops the executable bit.
        for p in into.rglob("*"):
            if p.is_file() and (p.suffix in ("", ".exe", ".so", ".dylib") or "llama" in p.name):
                p.chmod(p.stat().st_mode | 0o755)
    else:
        labkit.die(f"Don't know how to extract {archive.name}")
    archive.unlink(missing_ok=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch prebuilt llama.cpp binaries.")
    ap.add_argument("--list", action="store_true", help="List release assets and exit")
    ap.add_argument("--asset", help="Download this exact asset name instead of auto-picking")
    ap.add_argument("--force", action="store_true", help="Re-download even if already present")
    args = ap.parse_args()

    assets = list_assets()
    if args.list:
        if not assets:
            return 1
        print(f"Assets for llama.cpp {BUILD}:")
        for a in sorted(assets):
            print(f"  {a}")
        return 0

    into = labkit.runtime_dir() / BUILD
    existing = labkit.runtime_bin("llama-server", required=False)
    # Only a binary inside the repo counts as "already fetched". runtime_bin() also
    # falls back to PATH, and a system-wide llama-server would both skip the pinned
    # build and blow up relative_to() with a ValueError.
    if existing:
        try:
            existing = existing.resolve().relative_to(labkit.repo_root())
        except ValueError:
            existing = None
    if existing and not args.force:
        print(f"==> llama-server already present: {existing}")
        print("    (re-fetch with --force)")
        return 0

    hw = labkit.load_hardware(required=False)
    token = platform_token()
    prefs = accel_preference(hw)
    print(f"==> Target: {token[0].strip('-')} {token[1]}, accelerator preference {prefs}")

    asset = args.asset
    if not asset and assets:
        asset = pick_asset(assets, token, prefs)
    if not asset:
        # GitHub API unavailable (rate limit) -- fall back to the name table, trying
        # each accelerator preference in order before settling for the CPU build.
        for pref in prefs + ["plain"]:
            asset = FALLBACK_ASSETS.get((token[0], token[1], pref))
            if asset:
                print(f"    (using the built-in name table: {pref})")
                break
    if not asset:
        labkit.die(
            f"No prebuilt asset matches {token[0].strip('-')} {token[1]}.",
            f"See https://github.com/{REPO}/releases/tag/{BUILD} and pass --asset NAME,",
            "or build from source (bonus): make build-llama,",
            "or run the lab in cloud/Day20-lab.ipynb.",
        )

    archive = download(asset, into / asset)
    extract(archive, into)

    if "win-cuda" in asset and "cuda" in asset:
        m = re.search(r"cuda-(\d+\.\d+)", asset)
        arch = "arm64" if "arm64" in asset else "x64"
        cudart = f"cudart-llama-bin-win-cuda-{m.group(1)}-{arch}.zip" if m else None
        if cudart and (not assets or cudart in assets):
            print("\n==> CUDA build: also fetching the CUDA runtime DLLs")
            print("    (needed unless you already have the CUDA Toolkit installed)")
            extract(download(cudart, into / cudart), into)

    server = labkit.runtime_bin("llama-server", required=False)
    bench = labkit.runtime_bin("llama-bench", required=False)
    if not server:
        labkit.die(f"Extracted {asset} but found no llama-server inside {into}/")

    print(f"\n==> llama-server : {server.relative_to(labkit.repo_root())}")
    if bench:
        print(f"==> llama-bench  : {bench.relative_to(labkit.repo_root())}")
    rc = subprocess.run([str(server), "--version"], capture_output=True, text=True, check=False)
    version = (rc.stdout + rc.stderr).strip().splitlines()
    for line in version[:3]:
        print(f"    {line}")

    (labkit.runtime_dir() / "active.json").write_text(
        json.dumps({"build": BUILD, "asset": asset,
                    "llama_server": str(server.relative_to(labkit.repo_root())),
                    "llama_bench": str(bench.relative_to(labkit.repo_root())) if bench else None},
                   indent=2)
    )
    print("\n==> Runtime ready. No compiler required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
