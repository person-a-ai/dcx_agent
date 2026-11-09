"""Check documentation facts against repository sources (Python 3.12 stdlib)."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

DOCS = ["README.md", "CLAUDE.md", "backend/BACKEND.md", "frontend/PIPELINE.md", "frontend/README.md", "ops/macmini/README.md"]
ROOT = Path(__file__).resolve().parents[3]
CHECKS = ("exists", "paths", "api", "stages", "banned", "env")
PREFIXES = ("backend/", "frontend/", "ops/", "docs/", "scripts/", "nginx/", ".github/", "app/")
FILES = {"README.md", "CLAUDE.md", ".env.example", "harness.config.json"}
OPTIONAL_ENV = {"FIXTURE_CORPUS_PATH", "ENABLE_FIXTURE_CHANNEL", "LOW_VOLUME_THRESHOLD", "GATE_LOW_COUNT", "GATE_LOW_UNIQUE", "NAVER_SEARCH_BASE_URL"}


def paths(doc, content, fail):
    tokens = [(match.group(1), False) for match in re.finditer(r"`([^`\n]+)`", content)]
    tokens += [(match.group(1), True) for match in re.finditer(r"\]\(([^)\n]+)\)", content)]
    seen = set()
    for token, link in tokens:
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", token) or token.startswith(("~/", "$HOME", "shared/")) or re.search(r"\s", token):
            continue
        candidate = re.sub(r":\d+$", "", token.split("#", 1)[0])
        relative = candidate
        if link:
            relative = re.sub(r"^(?:\./|\.\./)+", "", relative)
        if not (relative.startswith(PREFIXES) or relative in FILES):
            continue
        parts = candidate.split("/")
        for index, part in enumerate(parts):
            if any(char in part for char in "<{*"):
                candidate = "/".join(parts[:index]) or "."
                break
        if candidate in seen:
            continue
        seen.add(candidate)
        bases = (ROOT, (ROOT / doc).parent, ROOT / "backend")
        if not any((base / candidate).exists() for base in bases):
            if candidate.startswith("ops/") and (ROOT / "ops/macmini" / candidate.removeprefix("ops/")).exists():
                continue
            fail("paths", doc, f"missing {token}")


def api(content, fail):
    documented = set(re.findall(r"\|\s*(GET|POST|PUT|PATCH|DELETE)\s*\|\s*`(/[^`\n]*)`\s*\|", content))
    command = "from app.main import app; import json; print(json.dumps([[m.upper(), p] for p, ops in app.openapi()['paths'].items() for m in ops]))"
    with tempfile.TemporaryDirectory(prefix="docs-check-") as data_dir:
        env = {key: os.environ[key] for key in ("HOME", "PATH") if key in os.environ}
        env.update(STORAGE="local", LOCAL_DATA_DIR=data_dir)
        try:
            result = subprocess.run([str(ROOT / "backend/.venv/bin/python"), "-c", command], cwd=ROOT / "backend", env=env, capture_output=True, text=True, check=True)
            actual = {tuple(operation) for operation in json.loads(result.stdout)}
        except (OSError, subprocess.CalledProcessError, ValueError, TypeError) as error:
            fail("api", "backend/BACKEND.md", f"OpenAPI subprocess failed: {str(error).replace(chr(10), ' ')}")
            return
    for method, path in sorted(actual - documented):
        fail("api", "backend/BACKEND.md", f"missing {method} {path}")
    for method, path in sorted(documented - actual):
        fail("api", "backend/BACKEND.md", f"not in code {method} {path}")


def stages(docs, fail):
    source = (ROOT / "frontend/src/components/StepBar.tsx").read_text()
    expected = set(re.findall(r'path:\s*"(/pipeline/[^"\n]+)"', source)) | {"/pipeline/compare"}
    for doc in ("README.md", "frontend/PIPELINE.md"):
        if doc not in docs:
            continue
        found = set(re.findall(r"/pipeline/[a-z-]+", docs[doc]))
        for path in sorted(expected - found):
            fail("stages", doc, f"missing {path}")
        for path in sorted(found - expected):
            fail("stages", doc, f"extra {path}")


def banned(doc, content, fail):
    for number, line in enumerate(content.splitlines(), 1):
        if re.search(r"Pinecone|pinecone_svc|persona1", line) or (re.search(r"EC2|systemd|Nginx|nginx/", line) and "예전" not in line):
            fail("banned", f"{doc}:{number}", line.strip())


def env(content, fail):
    names = set()
    in_table = False
    for line in content.splitlines():
        if not line.lstrip().startswith("|"):
            in_table = False
            continue
        first = line.strip().split("|")[1].strip()
        if first == "변수":
            in_table = True
            continue
        if in_table:
            for token in re.findall(r"`([^`]+)`", first):
                names.update(name.strip() for name in token.split("/") if name.strip())
    config = (ROOT / "backend/app/config.py").read_text()
    settings = re.search(r"^class Settings\([^\n]*\):\n((?:[ \t].*\n|\n)*)", config, re.MULTILINE)
    if settings is None:
        fail("env", "README.md", "Settings class not found")
        return
    allowed = {name.upper() for name in re.findall(r"^    ([a-zA-Z_]\w*):\s*[^\n=]+=[^\n]*", settings.group(1), re.MULTILINE)} | {"JEVMODEL_API_KEY"}
    for name in sorted(names - allowed):
        fail("env", "README.md", f"unknown variable {name}")
    example = set(re.findall(r"^([A-Za-z_]\w*)=", (ROOT / ".env.example").read_text(), re.MULTILINE))
    for name in sorted(example - names - OPTIONAL_ENV):
        fail("env", "README.md", f"missing {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="+", choices=CHECKS)
    selected = set(parser.parse_args().only or CHECKS)
    failures = 0

    def fail(check, doc, detail):
        nonlocal failures
        failures += 1
        print(f"FAIL {check} {doc}: {detail}")

    docs = {}
    for doc in DOCS:
        if not (ROOT / doc).is_file():
            fail("exists", doc, "missing")
        else:
            docs[doc] = (ROOT / doc).read_text()
    for doc, content in docs.items():
        if "paths" in selected:
            paths(doc, content, fail)
    if "api" in selected and "backend/BACKEND.md" in docs:
        api(docs["backend/BACKEND.md"], fail)
    if "stages" in selected:
        stages(docs, fail)
    if "banned" in selected:
        for doc, content in docs.items():
            banned(doc, content, fail)
    if "env" in selected and "README.md" in docs:
        env(docs["README.md"], fail)
    print(f"FAILED {failures}" if failures else "OK")
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
