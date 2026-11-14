"""Run the notebooks and fail on any cell error.

Pick what to run:

    python tests/run_notebooks.py --course gro860      the notebooks a course's list links
    python tests/run_notebooks.py --topic control      one topic folder
    python tests/run_notebooks.py --notebook cartpole_lqr
    python tests/run_notebooks.py                      every notebook

Long notebooks (``"long": true`` in tests/notebooks.json) are left out unless ``--long``
is given; ``"ci": false`` ones are left out when the ``CI`` environment variable is set.
Outputs are discarded: the files on disk are never changed.
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = json.loads((ROOT / "tests" / "notebooks.json").read_text())
TOPICS = (
    "python",
    "dynamics",
    "control",
    "optimal_control",
    "dynamic_programming",
    "reinforcement_learning",
    "machine_learning",
)
DEFAULT_TIMEOUT = 180


def course_notebooks(course):
    """The notebooks a course list links, in the list's order."""
    text = (ROOT / "courses" / f"{course}.md").read_text()
    links = re.findall(r"\]\(\.\./([^)]+\.ipynb)\)", text)
    return list(dict.fromkeys(links))


def all_notebooks():
    return [
        p.relative_to(ROOT).as_posix()
        for t in TOPICS
        for p in sorted((ROOT / t).glob("*.ipynb"))
    ]


def run_one(path, timeout):
    """Execute one notebook in a fresh kernel; return (status, seconds, message)."""
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError, CellTimeoutError

    start = time.perf_counter()
    try:
        nb = nbformat.read(ROOT / path, as_version=4)
        client = NotebookClient(
            nb,
            timeout=timeout,
            kernel_name="python3",
            resources={"metadata": {"path": str((ROOT / path).parent)}},
        )
        client.execute()
    except CellTimeoutError:
        return "fail", time.perf_counter() - start, f"a cell took more than {timeout} s"
    except CellExecutionError as exc:
        return "fail", time.perf_counter() - start, str(exc).strip()[-600:]
    except Exception as exc:
        return "fail", time.perf_counter() - start, f"{type(exc).__name__}: {exc}"
    return "pass", time.perf_counter() - start, ""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    pick = parser.add_mutually_exclusive_group()
    pick.add_argument("--course", help="a course list in courses/, e.g. gro860")
    pick.add_argument("--topic", choices=TOPICS)
    pick.add_argument("--notebook", help="a notebook's name, without .ipynb")
    parser.add_argument(
        "--long", action="store_true", help="also run the long notebooks"
    )
    parser.add_argument("--jobs", type=int, default=1, help="notebooks run at once")
    args = parser.parse_args(argv)

    # The selection
    if args.course:
        paths = course_notebooks(args.course)
    elif args.topic:
        paths = [p for p in all_notebooks() if p.startswith(args.topic + "/")]
    elif args.notebook:
        paths = [p for p in all_notebooks() if Path(p).stem == args.notebook]
        if not paths:
            parser.error(f"no notebook named {args.notebook}")
    else:
        paths = all_notebooks()

    # Drop the long ones and, on CI, the interactive ones (a single named notebook always runs)
    in_ci = bool(os.environ.get("CI"))
    selected, skipped = [], []
    for path in paths:
        entry = SETTINGS.get(path, {})
        if not args.notebook and in_ci and entry.get("ci") is False:
            skipped.append((path, "not run on CI"))
        elif not args.notebook and entry.get("long") and not args.long:
            skipped.append((path, "long (use --long)"))
        else:
            selected.append((path, entry.get("timeout", DEFAULT_TIMEOUT)))

    # The runs
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    with ProcessPoolExecutor(max_workers=max(args.jobs, 1)) as pool:
        futures = [
            (path, pool.submit(run_one, path, timeout)) for path, timeout in selected
        ]
        results = [(path, *future.result()) for path, future in futures]

    # The report
    for path, reason in skipped:
        print(f"skip  {path}  ({reason})")
    for path, status, seconds, message in results:
        print(f"{status}  {path}  {seconds:.0f} s")
        if message:
            print("      " + message.replace("\n", "\n      "))
    failed = [r for r in results if r[1] == "fail"]
    print(
        f"\n{len(results) - len(failed)} passed, {len(failed)} failed, {len(skipped)} skipped"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
