from pathlib import Path
import re
import subprocess


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"API_KEY\s*[:=]\s*['\"]?sk-", re.IGNORECASE),
]


def test_no_secret_or_local_init_file_tracked():
    tracked = subprocess.run(
        ["git", "ls-files"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()

    assert ".env" not in tracked
    assert "config/quickstart.yaml" not in tracked

    for relative in tracked:
        path = Path(relative)
        if path.suffix.lower() not in {".py", ".yaml", ".yml", ".md", ".toml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            assert not pattern.search(text), relative
