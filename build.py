#!/usr/bin/env python3
"""Rebuild index.html from src/template.html by embedding the Rive runtimes.

Downloads @rive-app/webgl2 and @rive-app/canvas via `npm pack`, base64-encodes
their rive.js / rive.wasm payloads, and substitutes them into the
<!--RIVE_RUNTIME--> placeholder in src/template.html to produce index.html.

Usage:
    python build.py                          # latest published versions
    python build.py --webgl2 2.41.0 --canvas 2.41.0   # pin exact versions
"""
import argparse
import base64
import json
import shutil
import subprocess
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "src" / "template.html"
OUTPUT = ROOT / "index.html"
PLACEHOLDER = "<!--RIVE_RUNTIME-->\r\n"

PACKAGES = {
    "webgl2": "@rive-app/webgl2",
    "canvas": "@rive-app/canvas",
}


def npm_pack(name, version, dest):
    spec = f"{name}@{version}" if version else name
    result = subprocess.run(
        ["npm", "pack", spec, "--silent"],
        cwd=dest,
        capture_output=True,
        text=True,
        shell=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"npm pack {spec} failed:\n{result.stderr}")
    tarball_name = result.stdout.strip().splitlines()[-1]
    return dest / tarball_name


def extract_runtime(name, version, work_dir):
    tarball = npm_pack(name, version, work_dir)
    extract_dir = work_dir / f"pkg-{name.split('/')[-1]}"
    with tarfile.open(tarball) as tar:
        tar.extractall(work_dir)
    (work_dir / "package").rename(extract_dir)

    package_json = json.loads((extract_dir / "package.json").read_text(encoding="utf-8"))
    js_bytes = (extract_dir / "rive.js").read_bytes()
    wasm_bytes = (extract_dir / "rive.wasm").read_bytes()

    return {
        "v": package_json["version"],
        "js": base64.b64encode(js_bytes).decode("ascii"),
        "wasm": base64.b64encode(wasm_bytes).decode("ascii"),
        "tarball": tarball,
        "extract_dir": extract_dir,
    }


def build_script_block(webgl2, canvas):
    lines = [
        "<script>\r\n",
        "window.__RT = {\r\n",
        f'  webgl2: {{v:"{webgl2["v"]}", js:"{webgl2["js"]}", wasm:"{webgl2["wasm"]}"}},\r\n',
        f'  canvas: {{v:"{canvas["v"]}", js:"{canvas["js"]}", wasm:"{canvas["wasm"]}"}}\r\n',
        "};\r\n",
        "</script>\r\n",
    ]
    return "".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--webgl2", help="Exact @rive-app/webgl2 version to pin (default: latest)")
    parser.add_argument("--canvas", help="Exact @rive-app/canvas version to pin (default: latest)")
    args = parser.parse_args()

    work_dir = ROOT / ".build-tmp"
    work_dir.mkdir(exist_ok=True)

    try:
        webgl2 = extract_runtime(PACKAGES["webgl2"], args.webgl2, work_dir)
        canvas = extract_runtime(PACKAGES["canvas"], args.canvas, work_dir)

        template = TEMPLATE.read_bytes().decode("utf-8")
        if PLACEHOLDER not in template:
            raise RuntimeError(f"placeholder {PLACEHOLDER!r} not found in {TEMPLATE}")

        script_block = build_script_block(webgl2, canvas)
        output = template.replace(PLACEHOLDER, script_block)

        OUTPUT.write_bytes(output.encode("utf-8"))

        print(f"webgl2: {webgl2['v']}")
        print(f"canvas: {canvas['v']}")
        print(f"output: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
