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


def inspect_zip(input_file: Path, *, chat_trace: bool = False,
                transport_trace: bool = False,
                selector_trace: bool = False,
                transcript_trace: bool = False,
                viewport_trace: bool = False,
                module_trace: bool = False,
                styles_trace: bool = False,
                feature_trace: bool = False) -> dict:
    if sum((chat_trace, transport_trace, selector_trace, transcript_trace,
            viewport_trace, module_trace, styles_trace, feature_trace)) > 1:
        raise ValueError("Choose at most one specialized AST analysis")
    if not input_file.is_file() or input_file.resolve().is_relative_to(ROOT):
        raise ValueError("Input ZIP must exist outside the public repository")
    if input_file.stat().st_size > 1024 * 1024 * 1024:
        raise ValueError("ZIP exceeds size limit")
    with zipfile.ZipFile(input_file) as archive:
        extensions = (".js", ".mjs", ".cjs", ".css") if styles_trace else (".js", ".mjs", ".cjs")
        infos = [i for i in archive.infolist() if not i.is_dir()
                 and i.filename.lower().endswith(extensions)]
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
                ext = ".css" if styles_trace and info.filename.lower().endswith(".css") else ".js"
                stem = "style" if ext == ".css" else "bundle"
                (Path(folder) / f"{stem}-{i:04d}{ext}").write_bytes(archive.read(info))
            script = ("scripts/trace_feature_impl.cjs" if feature_trace else
                      "scripts/trace_style_hooks.cjs" if styles_trace else
                      "scripts/trace_module_graph.cjs" if module_trace else
                      "scripts/trace_viewport_impl.cjs" if viewport_trace else
                      "scripts/trace_transcript_impl.cjs" if transcript_trace else
                      "scripts/trace_selector_impl.cjs" if selector_trace else
                      "scripts/trace_stream_impl.cjs" if transport_trace else
                      "scripts/trace_chat_impl.cjs" if chat_trace else
                      "scripts/static_ast_probe.cjs")
            result = subprocess.run(
                ["node", str(ROOT / script), folder],
                capture_output=True, text=True, timeout=180, check=False,
            )
            if result.returncode:
                raise ValueError("Private static AST probe failed")
            return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize AST operations from an offline private ZIP")
    parser.add_argument("--input", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--chat-trace", action="store_true",
                      help="Emit ordinal-only chat-pattern AST observations")
    mode.add_argument("--transport-trace", action="store_true",
                      help="Emit allowlisted transport callback and handler AST observations")
    mode.add_argument("--selector-trace", action="store_true",
                      help="Emit candidate selected ancestry and feature reference AST patterns")
    mode.add_argument("--transcript-trace", action="store_true",
                      help="Emit candidate turn derivation and message component patterns")
    mode.add_argument("--viewport-trace", action="store_true",
                      help="Emit candidate virtual list, scroll anchor and viewport patterns")
    mode.add_argument("--module-trace", action="store_true",
                      help="Emit anonymous bundle module ordinals and static import candidates")
    mode.add_argument("--styles-trace", action="store_true",
                      help="Count CSS syntax and script/style vocabulary without source output")
    mode.add_argument("--feature-trace", action="store_true",
                      help="Emit source-ordinal-only feature implementation leads")
    args = parser.parse_args()
    try:
        report = inspect_zip(args.input, chat_trace=args.chat_trace,
                             transport_trace=args.transport_trace,
                             selector_trace=args.selector_trace,
                             transcript_trace=args.transcript_trace,
                             viewport_trace=args.viewport_trace,
                             module_trace=args.module_trace,
                             styles_trace=args.styles_trace,
                             feature_trace=args.feature_trace)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired,
            zipfile.BadZipFile, UnicodeError):
        parser.exit(2, "Static AST analysis rejected (input or parser unavailable)\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
