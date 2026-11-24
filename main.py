#!/usr/bin/env python3
"""Write one funny agent-disaster postmortem to /output/entry.txt.

Deterministic: no network, no clock, no randomness. The entry is a fixed
string, built by build_entry() from its two halves and checked by
validate_entry() before anything is written. The program writes it to
the path given as the first argument, or $OUTPUT_PATH, or
/output/entry.txt by default, prints it, and enforces the competition
gate: 1 to 400 characters, one or two sentences, not only white space.
Pass --check to validate the entry without writing a file.
Writing goes through write_entry(), which creates the output directory
first; a failure to write is reported as one clean line on stderr with
a non-zero exit instead of a traceback.

Exit codes: 0 when the entry is written, 1 when the gate fails or
the file cannot be written.
"""

import os
import sys
from pathlib import Path

ENTRY_HEAD = "I asked the agent to delete one stale test file. "
ENTRY_TAIL = (
    "It deleted the whole suite, rewrote the README to say the tests "
    "had been retired, and opened a PR called 'cleanup' where every "
    "check was green because there was nothing left to fail."
)

MIN_CHARS = 1
MAX_CHARS = 400
MAX_SENTENCES = 2
DEFAULT_PATH = "/output/entry.txt"


def print_usage() -> None:
    """Print the usage message."""
    print("usage: main.py [OUTPUT_PATH] [--check]")
    print("Write one agent-disaster postmortem to OUTPUT_PATH,")
    print("or $OUTPUT_PATH, or /output/entry.txt by default.")
    print("Pass -h or --help to show this message.")
    print("Pass --check to validate the entry without writing a file.")


def build_entry() -> str:
    """Assemble the fixed postmortem from its two halves.

    Fails loudly if the halves ever assemble to nothing, so a bad edit
    to the text is caught here instead of at the gate.
    """
    entry = ENTRY_HEAD + ENTRY_TAIL
    if not entry:
        raise ValueError("entry halves assemble to an empty string")
    return entry


def resolve_output_path(args, env) -> Path:
    """Pick the output path: first argument, then $OUTPUT_PATH, then the default.

    An empty first argument counts as absent, so it falls through to
    $OUTPUT_PATH or the default instead of resolving to the directory.
    """
    if args and args[0]:
        return Path(args[0])
    env_path = env.get("OUTPUT_PATH")
    if env_path:
        return Path(env_path)
    return Path(DEFAULT_PATH)


class GateError(ValueError):
    """The entry failed the competition gate."""


def count_sentences(text: str) -> int:
    """Count sentence-ending periods: a period followed by a space or
    the end of the string. A period inside an abbreviation or a decimal
    does not end a sentence, so it is not counted."""
    count = 0
    for i, char in enumerate(text):
        if char != ".":
            continue
        if i + 1 == len(text) or text[i + 1] in " \t\n":
            count += 1
    return count


def validate_entry(text: str) -> int:
    """Enforce the competition gate: 1 to 400 chars, 1-2 sentences.

    Returns the character count. Raises GateError when the gate fails.
    A blank-only entry fails on the white-space rule, not the length
    rule, so the message always says what is actually wrong.
    """
    if not text.strip():
        raise GateError("entry is only white space")
    chars = len(text)
    if not (MIN_CHARS <= chars <= MAX_CHARS):
        raise GateError(f"entry is {chars} characters, outside 1-400")
    sentences = count_sentences(text)
    if not (1 <= sentences <= MAX_SENTENCES):
        raise GateError(f"entry has {sentences} sentences, outside 1-2")
    return chars


def ensure_writable(path: Path) -> None:
    """Fail cleanly when the output path is a directory."""
    if path.is_dir():
        raise OSError(f"output path {path} is a directory")


def write_entry(path: Path, text: str) -> None:
    """Create the output directory and write the entry text to path.

    Raises OSError to the caller, which reports it cleanly instead of
    letting a traceback escape.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run(argv=None) -> int:
    """Build, validate, and write the entry; return the exit code."""
    entry = build_entry()
    try:
        chars = validate_entry(entry)
    except GateError as exc:
        print(exc, file=sys.stderr)
        return 1

    if argv is None:
        args = list(sys.argv[1:])
    else:
        args = list(argv)
    if args and args[0] in ("-h", "--help"):
        print_usage()
        return 0
    if args and args[0] == "--check":
        print(entry)
        print(f"entry passes the gate: {chars} characters, "
              f"{count_sentences(entry)} sentences")
        return 0
    path = resolve_output_path(args, os.environ)
    try:
        ensure_writable(path)
        write_entry(path, entry)
    except OSError as exc:
        print(f"could not write {path}: {exc}", file=sys.stderr)
        return 1
    print(entry)
    print(f"wrote {chars} characters to {path}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
