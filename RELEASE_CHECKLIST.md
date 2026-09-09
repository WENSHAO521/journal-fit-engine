# Release checklist

VERSION is canonical. PATCH covers docs/validation/compatibility fixes; MINOR adds fit-model capabilities or new integration; MAJOR changes incompatible schema or behavior. Never move or overwrite a published tag or its release assets.

1. Select VERSION and add/update the matching `## [VERSION]` heading in CHANGELOG.md. The release page, not a working-tree version heading, establishes publication status.
2. Run `python scripts/validate_skill.py`, `python -m unittest discover -s tests -v`, and `git diff --check`. Build with `python scripts/package_runtime.py`; optionally assert the version with `--version`.
3. Verify the ZIP and sidecars with `python scripts/package_runtime.py --verify <zip>`. Inspect its allowlisted members (one top-level folder), extracted-runtime validation, manifest, and checksum. Review content as well as absence of `.env`, `.env.*`, `*.pem`, `*.key`, `credentials*`, `token*`, `secrets*`, developer files, and linked paths. Do not claim filename filtering proves secret absence.
4. Review and commit source changes only. Never commit `dist/`. Push the intended branch, confirm a clean tree, and verify the successful CI run belongs to that exact commit.
5. Check remote tags and GitHub Releases for the version. If either already exists, stop and report the collision. Never force-push tags or replace existing release assets.
6. Create an annotated `vVERSION` tag on the CI-verified commit and push only that new tag. Confirm its remote target. Do not tag a dirty checkout or a different commit.
7. Create **Journal Fit Engine vVERSION** with concise release notes from the matching CHANGELOG entry. Use `gh release create` with `--verify-tag`, `--title`, and `--notes-file`. Attach the locally verified versioned ZIP, its SHA-256 sidecar, and the release manifest. Publish only after validation, tests, packaging, extracted-package checks, and checksum generation succeed.
8. Confirm the published release page, tag/commit, title, and asset names/sizes. Download the published ZIP and checksum into a temporary directory and compare the bytes/hash against the verified local artifact. Do not overwrite a prior release.

This project intentionally uses a manual release step after CI instead of a tag-triggered publisher. Ordinary branch pushes and PRs validate but never release. If permissions are unavailable, report **prepared but not published**, identify the verified commit/artifacts, and perform these remaining steps manually. No release API or network access is needed for a local build.

## Reproducibility

Build from the exact tagged source with Python 3.11+ and the standard library. UTF-8 LF-decoded text, sorted names, fixed timestamps/permissions, and ZIP_STORED entries make output independent of checkout newlines, file mtimes, and zlib versions. The generated external manifest records all file hashes; hosts do not consume it.

## Known limitations at this maturity stage

Before claiming this release satisfies the full acceptance criteria for a stable `1.0.0`, confirm the still-open items in [CHANGELOG.md](CHANGELOG.md)'s roadmap: Corpus Builder integration, live indexing/APC/scope verification against real journal sources, automated reference-neighborhood candidate discovery, and empirical submission-ladder evaluation. This checklist governs publishing whatever the current VERSION actually is -- it does not by itself justify advancing to `1.0.0`.
