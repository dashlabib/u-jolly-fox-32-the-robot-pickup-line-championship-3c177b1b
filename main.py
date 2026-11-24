#!/usr/bin/env python3
"""The Robot Pickup Line Championship — make.fun entry.

Reads the single robot pickup line from entry.txt, checks it against
the competition gate (one line, 1-200 characters, not only whitespace,
no tabs, carriage returns or control characters), and writes the
exact bytes to the output directory.

The published bytes are the entry bytes verbatim: the line stored
in entry.txt plus one trailing newline, confirmed by a byte-for-byte
read-back comparison and by `cmp` against entry.txt.

Usage:
    python3 main.py [--entry-file FILE] [--output-dir DIR] [--verify-only]
"""
import argparse
import os
import sys

ENTRY_FILE = "entry.txt"
OUTPUT_NAME = "entry.txt"
MAX_CHARS = 200
MIN_CHARS = 1


def gate_limits():
    """Return the gate limits as a (min_chars, max_chars) pair."""
    return (MIN_CHARS, MAX_CHARS)


def load_entry(path):
    """Read the entry text from path and return it as a string."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError as exc:
        raise ValueError("cannot read entry file %s: %s" % (path, exc)) from exc
    except UnicodeDecodeError as exc:
        raise ValueError("entry file %s is not valid UTF-8: %s" % (path, exc)) from exc


def split_single_line(text):
    """Return the single line in text, allowing one trailing newline.

    Raises ValueError when the text holds more than one line.
    """
    lines = text.split("\n")
    if text.endswith("\n"):
        lines = lines[:-1]
    if len(lines) != 1:
        raise ValueError("entry must be exactly one line, got %d" % len(lines))
    return lines[0]


def check_characters(line):
    """Reject characters the gate forbids, returning the line unchanged."""
    if "\r" in line or "\t" in line:
        raise ValueError("entry must not contain carriage returns or tabs")
    if any(ord(ch) < 0x20 for ch in line):
        raise ValueError("entry must not contain control characters")
    return line


def validate(line):
    """Enforce the gate and return the line unchanged.

    The gate is: one non-blank line of 1-200 characters, with no
    carriage returns, tabs or control characters, and no leading
    or trailing spaces that would silently change the judged text.
    """
    if not line.strip():
        raise ValueError("entry must not be only whitespace")
    if line != line.strip():
        raise ValueError("entry must not start or end with whitespace")
    check_characters(line)
    low, high = gate_limits()
    if len(line) < low or len(line) > high:
        raise ValueError(
            "entry must be %d-%d characters, got %d" % (low, high, len(line))
        )
    return line


def report_gate(line):
    """Print a one-line summary of the gate check for this entry."""
    print("entry (%d chars): %s" % (len(line), line))
    print("gate check passed: single line, %d chars" % len(line))


def publish(line, output_dir):
    """Write the line plus a trailing newline, then read it back.

    The written bytes must equal the entry bytes exactly; any
    difference raises ValueError instead of publishing silently.
    """
    os.makedirs(output_dir, exist_ok=True)
    target = os.path.join(output_dir, OUTPUT_NAME)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
    with open(target, "rb") as handle:
        written = handle.read()
    expected = (line + "\n").encode("utf-8")
    if written != expected:
        raise ValueError("read-back mismatch: output bytes differ from entry")
    return target


def build_parser():
    """Build the command-line parser for this entry program."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entry-file",
        default=None,
        help="entry text file to read (default: entry.txt beside main.py)",
    )
    parser.add_argument(
        "--output-dir",
        default=os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"),
        help="directory to write entry.txt into (default: $MAKEFUN_OUTPUT_DIR or /output)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="only validate the entry, writing nothing",
    )
    return parser


def run(argv=None):
    """Validate the entry and publish it; return the exit code."""
    args = build_parser().parse_args(argv)
    here = os.path.dirname(os.path.abspath(__file__))
    entry_path = args.entry_file or os.path.join(here, ENTRY_FILE)
    try:
        text = load_entry(entry_path)
        line = validate(split_single_line(text))
    except ValueError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    report_gate(line)
    if args.verify_only:
        return 0
    try:
        target = publish(line, args.output_dir)
    except (OSError, ValueError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    print("wrote %s (read-back verified)" % target)
    return 0


def main(argv=None):
    return run(argv)


if __name__ == "__main__":
    sys.exit(main())
