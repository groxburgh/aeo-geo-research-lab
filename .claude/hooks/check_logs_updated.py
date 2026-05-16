"""
Stop hook: exits with code 2 (forcing Claude to continue) when .py files were
modified in the working tree but session-log.md was not updated in the same session.
No external dependencies — stdlib only.
"""
import subprocess
import sys


def main() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.exit(0)

    changed = [line[3:].strip() for line in result.stdout.splitlines() if line.strip()]
    py_changed = any(f.endswith(".py") for f in changed)
    log_changed = any("session-log.md" in f for f in changed)

    if py_changed and not log_changed:
        print(
            "session-log.md has not been updated. "
            "Append a session entry to session-log.md (and decisions-log.md if a "
            "new library, pattern, or rejected alternative was involved) before finishing."
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
