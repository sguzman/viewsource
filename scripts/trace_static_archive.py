#!/usr/bin/env python3
"""Offline, private ZIP-to-AST bridge. Raw source never enters the repository.

Requires Node.js and the Acorn parser installed for the repository.
Reads only safe ZIP script members into an ephemeral system temp directory;
it does not execute a downloaded script, access the web or emit filenames.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zipfile

MAX_TOTAL = 512 * 1024 * 1024
MAX_SCRIPTS = 2000
ROOT = Path(__file__).resolve().parents[1]


def inspect_zip(input_file: Path, *, chat_trace: bool = False) -> dict:
    if not input_file.is_file() or input_file.resolve().is_relative_to(ROOT):
        raise ValueError("Input ZIP must exist outside the public repository")
    if input_file.stat().st_size > 1024 * 1024 * 1024:
        raise ValueError("ZIP exceeds size limit")
    with zipfile.ZipFile(input_file) as archive:
        infos = [i for i in archive.infolist() if not i.is_dir()
                 and i.filename.lower().endswith((".js", ".mjs", ".cjs"))]
        if len(infos) > MAX_SCRIPTS:
            raise ValueError("Too many JavaScript files")
        total = 0
        with tempfile.TemporaryDirectory(prefix="viewsource-ast-private-") as folder:
            for i, info in enumerate(sorted(infos, key=lambda item: item.filename), 1):
                # Captured member names never enter the output or file system.
                name = Path(info.filename)
                if (".." in name.parts or info.filename.startswith(("/", "\\")) or
                        "\\" in info.filename or stat.S_ISLNK(info.external_attr >> 16)):
                    raise ValueError("Invalid archive member")
                total += info.file_size
                if total > MAX_TOTAL:
                    raise ValueError("Uncompressed source exceeds safety limit")
                if info.file_size > 8 * 1024 * 1024:
                    continue
                if info.file_size / max(info.compress_size, 1) > 1000:
                    raise ValueError("Unsafe compression ratio")
                (Path(folder) / f"bundle-{i:04d}.js").write_bytes(archive.read(info))
            result = subprocess.run(
                ["node", str(ROOT / ("scripts/trace_chat_impl.cjs" if chat_trace else "scripts/static_ast_probe.cjs")), folder],
                capture_output=True, text=True, timeout=180, check=False,
            )
            if result.returncode:
                raise ValueError("Private static AST probe failed")
            return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize AST operations from an offline private ZIP")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--chat-trace", action="store_true",
                        help="Emit ordinal-only chat-pattern AST observations")
    args = parser.parse_args()
    try:
        report = inspect_zip(args.input, chat_trace=args.chat_trace)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired,
            zipfile.BadZipFile, UnicodeError):
        parser.exit(2, "Static AST analysis rejected (input or parser unavailable)\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
