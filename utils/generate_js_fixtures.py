#!/usr/bin/env python3

import subprocess
from pathlib import Path

SPHINX_ROOT = Path(__file__).resolve().parents[1]
TEST_JS_FIXTURES = SPHINX_ROOT / "tests" / "js" / "fixtures"
TEST_JS_ROOTS = SPHINX_ROOT / "tests" / "js" / "roots"


def build(srcdir: Path) -> None:
    cmd = ("sphinx-build", "-E", "-q", "-b", "html", f"{srcdir}", f"{srcdir}/build")
    subprocess.run(cmd, check=True, capture_output=True)


def beautify(filename: Path) -> None:
    cmd = ("js-beautify", "-r", filename)
    subprocess.run(cmd, check=True, capture_output=True)


for directory in TEST_JS_ROOTS.iterdir():
    searchindex = directory / "build" / "searchindex.js"
    destination = TEST_JS_FIXTURES / directory.name / "searchindex.js"

    print(f"Building {directory} ... ", end="")
    build(directory)
    print("done")

    print(f"Beautifying {searchindex} ... ", end="")
    beautify(searchindex)
    print("done")

    print(f"Moving {searchindex} to {destination} ... ", end="")
    searchindex.replace(destination)
    print("done")
