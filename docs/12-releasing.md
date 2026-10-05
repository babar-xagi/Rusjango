# 📦 Release procedure

**Rusjango 0.1.4 · Alpha**

Releases use GitHub Actions and the repository's configured `PYPI_API_TOKEN` secret in the `pypi` environment. Local PyPI credentials are not required. Publication and release creation require an explicit maintainer request.

## 🧰 Prepare

1. Choose an unused patch/minor version; check both Git tags and PyPI.
2. Align Cargo workspace, Python package, and Python fallback versions. Cargo regenerates the relevant lockfile entries.
3. Update the changelog, guides, phase tracker, validation record, and `docs/releases/<version>.md`.
4. Run the full suite with both CLIs and live PostgreSQL, Rust formatting/tests/clippy, Python formatting/lint, and distribution checks.

```bash
python scripts/check_release.py v0.1.4
uv build --package rusjango
.venv/bin/python scripts/verify_wheel.py dist/rusjango-0.1.4-cp311-abi3-linux_x86_64.whl
```

Select the exact wheel when dist contains older builds. The example wheel name applies to the local Linux build; the workflow creates portable platform wheels.

## 🚀 Publish

Push the reviewed commit to main and require its hosted CI to pass. Create an annotated `v<version>` tag at that verified commit and push it. The tag starts the release workflow:

```text
tag -> version check + full CI -> platform wheels/source archive
    -> metadata validation -> PyPI upload -> GitHub release with artifacts
```

The release builds Linux x86_64/aarch64, Windows x86_64, and macOS x86_64/aarch64 wheels plus the source distribution. Stable ABI wheels target Python 3.11+. GitHub release creation uses the workflow's scoped GITHUB_TOKEN and attaches the distribution files after PyPI succeeds.

## ✅ Verify

Inspect all workflow jobs, confirm the new version and expected files through PyPI's JSON endpoint, and install the package from PyPI into a fresh environment. Import the native module, compare versions, and exercise scaffolding, migration, and CRUD. Confirm the GitHub release points to the intended tag and includes the release notes and assets.

If a job fails, inspect its logs and fix the cause before retrying. Do not replace uploaded PyPI files, reuse a published version, or move a public release tag. Record hosted results and links in the validation guide after they are available.

---

[📚 Documentation home](README.md)
