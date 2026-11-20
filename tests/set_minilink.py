"""Set the minilink every notebook installs, in one place, or check that they all agree.

The pin is written in requirements.txt (the local run and CI) and in each notebook's Colab
install cell, always the same:

    python tests/set_minilink.py 0.4.0       a release, from PyPI: minilink[full]==0.4.0
    python tests/set_minilink.py dev         a branch of minilink, from GitHub
    python tests/set_minilink.py e106e6b4    a commit of minilink, from GitHub
    python tests/set_minilink.py --check     fail when a notebook's pin differs from requirements.txt

`main` pins a release, `dev` the branch `dev`, a twin branch the minilink branch of its own name
(README, "Branches and pins"). The notebooks are rewritten as JSON in the format git keeps them
in, so nothing but the pin changes.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = ROOT / "requirements.txt"
REPOSITORY = "git+https://github.com/alx87grd/minilink"

# A requirement for minilink, in either form: ==version, or @ git+...@ref
PIN = re.compile(
    r"minilink\[full\]"
    r"(?:==[^\s\"'\\]+| @ git\+https://github\.com/alx87grd/minilink@[^\s\"'\\]+)"
)

# A release as PyPI writes it: 0.4.0, 0.4.0b1, 0.4.0rc2, 0.4.1.post1
RELEASE = re.compile(r"^\d+\.\d+\.\d+((a|b|rc)\d+)?(\.post\d+)?$")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", nargs="?", help="a release (0.4.0), a branch or a commit")
    parser.add_argument("--check", action="store_true", help="only check that every pin agrees")
    args = parser.parse_args()

    if args.check:
        sys.exit(check())
    if not args.target:
        parser.error("give a release, a branch or a commit, or --check")

    spec = requirement_of(args.target)
    changed = [path for path in pinned_files() if set_pin(path, spec)]
    print(f"minilink pinned to {spec!r} in {len(changed)} file(s)")
    for path in changed:
        print(f"  {path.relative_to(ROOT)}")


def requirement_of(target) -> str:
    """The requirement for a release (PyPI) or a branch or commit (GitHub)."""
    if RELEASE.match(target):
        return f"minilink[full]=={target}"

    return f"minilink[full] @ {REPOSITORY}@{target}"


def pinned_files() -> list:
    """requirements.txt, then every notebook that installs minilink."""
    notebooks = sorted(p for p in ROOT.glob("*/*.ipynb") if PIN.search(p.read_text()))

    return [REQUIREMENTS, *notebooks]


def set_pin(path, spec) -> bool:
    """Write ``spec`` in place of the file's minilink pin; ``True`` when the file changed."""
    if path.suffix != ".ipynb":
        text = path.read_text()
        lines = text.splitlines(keepends=True)
        new = "".join(
            line if line.lstrip().startswith("#") else PIN.sub(spec, line)
            for line in lines
        )
        path.write_text(new)
        return new != text

    # A notebook: the pin in its code cells' source, the JSON written back as git keeps it
    text = path.read_text()
    notebook = json.loads(text)
    require_same_format(path, notebook, text)
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = [PIN.sub(spec, line) for line in cell["source"]]
    new = dump(notebook)
    path.write_text(new)

    return new != text


def check() -> int:
    """0 when requirements.txt and every notebook pin the same minilink, else 1 with the offenders."""
    expected = pins_of(REQUIREMENTS.read_text())
    if len(expected) != 1:
        print(f"requirements.txt must pin minilink once, found {expected}")
        return 1
    (spec,) = expected

    offenders = []
    for path in pinned_files()[1:]:
        found = pins_of(path.read_text())
        if found != {spec}:
            offenders.append((path, found))

    for path, found in offenders:
        print(f"{path.relative_to(ROOT)} pins {sorted(found)}, requirements.txt {spec!r}")
    if not offenders:
        print(f"every notebook pins {spec!r}")

    return 1 if offenders else 0


def pins_of(text) -> set:
    """The minilink pins a file's text holds, as written; a comment line holds none."""
    lines = [line for line in text.splitlines() if not line.lstrip().startswith("#")]

    return set(PIN.findall("\n".join(lines)))


def dump(notebook) -> str:
    """A notebook as git keeps it: one-space indent, characters unescaped, a final newline."""
    return json.dumps(notebook, indent=1, ensure_ascii=False) + "\n"


def require_same_format(path, notebook, text):
    """Refuse a notebook whose file is not in the format this script writes back."""
    if dump(notebook) != text:
        raise SystemExit(
            f"{path.relative_to(ROOT)} is not in the JSON format git keeps "
            "(one-space indent, a final newline); save it once with nbstripout, then rerun"
        )


if __name__ == "__main__":
    main()
