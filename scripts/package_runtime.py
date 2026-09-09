#!/usr/bin/env python3
"""Build and verify an allowlisted runtime ZIP for journal-fit-engine.

Bundles exactly the files a host needs to run the skill (SKILL.md, README,
LICENSE, agent metadata, references/, disciplines/) -- none of the dev-only
tooling (CHANGELOG, VERSION, evals, scripts, tests, CI). Deterministic:
sorted members, fixed timestamps/permissions, stored (uncompressed) entries,
so the archive is independent of checkout newlines, mtimes, and zlib
version. No network access, standard library only.
"""

import argparse
import hashlib
import json
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_skill import RUNTIME_FILES, VERSION_RE  # noqa: E402

NAME = "journal-fit-engine"
ZIP_TIME = (1980, 1, 1, 0, 0, 0)
VALIDATOR = Path(__file__).resolve().parent / "validate_skill.py"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def release_version(root: Path) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    if not VERSION_RE.match(version):
        raise ValueError(f"VERSION must contain a plain MAJOR.MINOR.PATCH version, got: {version!r}")
    return version


def run_source_validation(root: Path) -> None:
    proc = subprocess.run([sys.executable, str(VALIDATOR)], cwd=root,
                           capture_output=True, text=True, encoding="utf-8")
    if proc.returncode != 0:
        raise ValueError("source validation failed:\n" + proc.stdout + proc.stderr)


def safe_file(root: Path, relative: str) -> Path:
    """Reject symlinks/junctions and paths outside the requested root."""
    root = root.resolve()
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"outside repository: {relative}")
    for part in (path, *path.parents):
        if part == root:
            break
        is_junction = getattr(part, "is_junction", None)
        if part.is_symlink() or (is_junction and is_junction()):
            raise ValueError(f"linked path is not allowed: {relative}")
    if not path.is_file():
        raise ValueError(f"missing required runtime file: {relative}")
    return path


def collect_runtime(root: Path) -> dict[str, bytes]:
    files = {}
    for relative in RUNTIME_FILES:
        text = safe_file(root, relative).read_text(encoding="utf-8")
        files[f"{NAME}/{relative}"] = text.encode("utf-8")
    return files


def frontmatter_name(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return None


def validate_runtime_folder(folder: Path) -> list[str]:
    """Lightweight checks against an extracted runtime-only tree (no
    CHANGELOG/evals/scripts/tests present, so the full source validator
    does not apply)."""
    problems = []
    expected = {f"{NAME}/{relative}" for relative in RUNTIME_FILES}
    actual = {str(p.relative_to(folder.parent)).replace("\\", "/")
              for p in folder.rglob("*") if p.is_file()}
    if actual != expected:
        problems.append(f"runtime folder contents differ from allowlist: "
                         f"extra={sorted(actual - expected)} missing={sorted(expected - actual)}")
    skill_md = folder / "SKILL.md"
    if not skill_md.is_file():
        problems.append("extracted runtime is missing SKILL.md")
    else:
        name = frontmatter_name(skill_md.read_text(encoding="utf-8"))
        if name != NAME:
            problems.append(f"SKILL.md frontmatter name mismatch: {name!r}")
    return problems


def verify_archive(archive: Path, expected: dict[str, bytes] | None = None) -> dict[str, str]:
    expected_names = {f"{NAME}/{relative}" for relative in RUNTIME_FILES}
    with zipfile.ZipFile(archive) as zipped:
        infos = zipped.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)) or set(names) != expected_names:
            raise ValueError(
                f"ZIP must contain exactly the {len(expected_names)} allowlisted runtime files "
                "under one folder")
        for info in infos:
            if stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("ZIP symlink is forbidden")
            if info.file_size > 5_000_000:
                raise ValueError("unexpectedly large runtime text file")
        payload = {info.filename: zipped.read(info) for info in infos}
    if expected is not None and payload != expected:
        raise ValueError("ZIP payload differs from the validated source snapshot")
    with tempfile.TemporaryDirectory(prefix="journal-fit-runtime-check-") as temporary:
        folder = Path(temporary) / NAME
        for name, data in payload.items():
            target = Path(temporary) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        problems = validate_runtime_folder(folder)
        if problems:
            raise ValueError("runtime validation failed: " + "; ".join(problems))
    return {name.removeprefix(NAME + "/"): sha256(data) for name, data in sorted(payload.items())}


def manifest(version: str, archive_name: str, digest: str, hashes: dict[str, str]) -> dict:
    return {
        "name": NAME, "version": version, "release_type": "runtime",
        "required_entrypoint": "SKILL.md", "includes": sorted(RUNTIME_FILES),
        "artifact": archive_name, "sha256": digest, "file_sha256": hashes,
    }


def verify_artifacts(archive_path: Path, root: Path) -> str:
    archive_path = Path(archive_path)
    version = release_version(root)
    if archive_path.name != f"{NAME}-v{version}.zip":
        raise ValueError("artifact filename does not match VERSION")
    hashes = verify_archive(archive_path)
    digest = sha256(archive_path.read_bytes())
    checksum = archive_path.with_suffix(".zip.sha256").read_text(encoding="utf-8")
    if checksum != f"{digest}  {archive_path.name}\n":
        raise ValueError("checksum sidecar mismatch")
    record = json.loads((archive_path.parent / "release-manifest.json").read_text(encoding="utf-8"))
    if record != manifest(version, archive_path.name, digest, hashes):
        raise ValueError("release manifest mismatch")
    return digest


def build(root: Path, out_dir: Path, version: str | None = None) -> Path:
    root = Path(root).resolve()
    run_source_validation(root)
    actual_version = release_version(root)
    if version is not None and version != actual_version:
        raise ValueError("--version disagrees with VERSION")
    version = actual_version
    files = collect_runtime(root)
    archive_name = f"{NAME}-v{version}.zip"
    with tempfile.TemporaryDirectory(prefix="journal-fit-build-") as temporary:
        candidate = Path(temporary) / archive_name
        with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_STORED) as zipped:
            for name, data in sorted(files.items()):
                info = zipfile.ZipInfo(name, date_time=ZIP_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_STORED
                zipped.writestr(info, data)
        hashes = verify_archive(candidate, expected=files)
        data = candidate.read_bytes()
    digest = sha256(data)
    output = Path(out_dir)
    output.mkdir(parents=True, exist_ok=True)
    archive = output / archive_name
    archive.write_bytes(data)
    archive.with_suffix(".zip.sha256").write_bytes(f"{digest}  {archive_name}\n".encode("utf-8"))
    record = manifest(version, archive_name, digest, hashes)
    (output / "release-manifest.json").write_bytes(
        (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    verify_artifacts(archive, root)
    return archive


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--out-dir", type=Path, default=Path("dist"))
    parser.add_argument("--version", help="optional assertion; must match VERSION")
    parser.add_argument("--verify", type=Path, help="verify an existing ZIP and its two sidecars")
    args = parser.parse_args()
    try:
        if args.verify:
            if args.version and args.version != release_version(args.root):
                raise ValueError("--version disagrees with VERSION")
            print("PASS: extracted runtime, manifest, and SHA-256: " + verify_artifacts(args.verify, args.root))
        else:
            archive = build(args.root, args.out_dir, args.version)
            print(archive)
            print(archive.with_suffix(".zip.sha256"))
            print(archive.parent / "release-manifest.json")
            print(f"PASS: source and extracted runtime validated; {len(RUNTIME_FILES)} allowlisted files")
        return 0
    except (OSError, ValueError, UnicodeError, zipfile.BadZipFile) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
