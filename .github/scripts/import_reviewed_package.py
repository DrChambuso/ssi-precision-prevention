#!/usr/bin/env python3
"""Import one sealed release asset; never execute code from its archive.

This bootstrap is intentionally limited to one repository, tag and archive digest.
The caller provides the sealed archive SHA256 as a manual workflow input.
The archive must contain ssi-precision-prevention/manifest.sha256 and exactly the
files recorded by that manifest. The manifest itself is authenticated by the
sealed archive SHA256. Git metadata and workflow files cannot be overwritten.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile


REPOSITORY = "DrChambuso/ssi-precision-prevention"
TAG = "v1.0.0-rc2"
ARCHIVE_PREFIX = "ssi-precision-prevention"
ARCHIVE_NAME = "Supplementary_Software_1_SSI_Code_v1.0.0-rc2.zip"
EXPECTED_SHA256 = os.environ.get("INPUT_ARCHIVE_SHA256", "")
API_ROOT = "https://api.github.com/repos/" + REPOSITORY
MAX_ARCHIVE_BYTES = 300 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_FILE_BYTES = 99 * 1024 * 1024
MAX_FILES = 5000


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


def api_request(path: str, token: str, accept: str = "application/vnd.github+json"):
    require(path.startswith("/") and not path.startswith("//"), "Invalid API path")
    request = urllib.request.Request(
        API_ROOT + path,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ssi-reviewed-package-import",
        },
    )
    return urllib.request.build_opener(NoRedirect()).open(request, timeout=60)


def read_json(path: str, token: str):
    with api_request(path, token) as response:
        return json.load(response)


def find_draft_asset(token: str) -> dict:
    matching = []
    for page in range(1, 11):
        releases = read_json(f"/releases?per_page=100&page={page}", token)
        require(isinstance(releases, list), "Unexpected releases response")
        matching.extend(r for r in releases if r.get("tag_name") == TAG)
        if len(releases) < 100:
            break
    require(len(matching) == 1, "Expected exactly one release for the sealed tag")
    release = matching[0]
    require(release.get("draft") is True, "Import source must remain a draft release")
    release_id = release.get("id")
    require(isinstance(release_id, int) and release_id > 0, "Invalid release ID")
    assets = read_json(f"/releases/{release_id}/assets?per_page=100", token)
    matches = [a for a in assets if a.get("name") == ARCHIVE_NAME]
    require(len(matches) == 1, "Expected exactly one archive with the sealed name")
    asset = matches[0]
    require(asset.get("state") == "uploaded", "Archive upload is incomplete")
    require(0 < asset.get("size", 0) <= MAX_ARCHIVE_BYTES, "Unexpected archive size")
    asset_id = asset.get("id")
    require(isinstance(asset_id, int) and asset_id > 0, "Invalid asset ID")
    require(asset.get("url") == API_ROOT + f"/releases/assets/{asset_id}", "Unexpected asset API URL")
    server_digest = asset.get("digest")
    if server_digest:
        require(server_digest == "sha256:" + EXPECTED_SHA256, "GitHub asset digest differs from sealed digest")
    return asset


def download_asset(asset: dict, token: str, target: Path) -> None:
    try:
        response = api_request(f"/releases/assets/{asset['id']}", token, "application/octet-stream")
    except urllib.error.HTTPError as error:
        if error.code != 302:
            raise
        location = error.headers.get("Location", "")
        parsed = urllib.parse.urlsplit(location)
        require(parsed.scheme == "https", "Asset redirect must use HTTPS")
        require(parsed.hostname in {"release-assets.githubusercontent.com", "objects.githubusercontent.com"}, "Unexpected asset redirect host")
        require(parsed.username is None and parsed.password is None and parsed.port in {None, 443}, "Unexpected asset redirect authority")
        # A signed GitHub asset URL needs no Authorization header. Do not forward
        # the API token to the object store, and do not follow further redirects.
        request = urllib.request.Request(location, headers={"User-Agent": "ssi-reviewed-package-import"})
        response = urllib.request.build_opener(NoRedirect()).open(request, timeout=60)
    with response, target.open("xb") as handle:
        total = 0
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            total += len(chunk)
            require(total <= MAX_ARCHIVE_BYTES, "Archive exceeds permitted size")
            handle.write(chunk)
    require(target.stat().st_size == asset["size"], "Archive download length differs from GitHub metadata")


def safe_relative(name: str) -> str:
    require(bool(name) and "\\" not in name and "\x00" not in name, "Invalid archive path")
    require(not any(ord(c) < 32 or ord(c) == 127 for c in name), "Control character in path")
    path = PurePosixPath(name)
    require(not path.is_absolute() and all(p not in {".", "..", ""} for p in path.parts), "Unsafe archive path")
    require(str(path) == name, "Archive path is not canonical")
    require(not any(p.casefold() == ".git" for p in path.parts), "Git metadata cannot be imported")
    require(path.parts[0].casefold() != ".github" or path.parts[0] == ".github", "Invalid workflow directory capitalization")
    return name


def verify_and_stage(archive: Path, staging: Path) -> list[str]:
    require(re.fullmatch(r"[0-9a-f]{64}", EXPECTED_SHA256) is not None, "Sealed SHA256 was not configured")
    require(digest(archive) == EXPECTED_SHA256, "Archive SHA256 does not match sealed value")
    with zipfile.ZipFile(archive) as zf:
        files = {}
        seen = set()
        total = 0
        for info in zf.infolist():
            require(not (info.flag_bits & 1), "Encrypted ZIP entries are not supported")
            mode = info.external_attr >> 16
            require(not stat.S_ISLNK(mode), "ZIP symlinks are forbidden")
            require(stat.S_IFMT(mode) in {0, stat.S_IFREG, stat.S_IFDIR}, "Special ZIP entry is forbidden")
            raw = info.filename.rstrip("/") if info.is_dir() else info.filename
            require(raw == ARCHIVE_PREFIX or raw.startswith(ARCHIVE_PREFIX + "/"), "Unexpected ZIP root")
            require(raw.casefold() not in seen, "Duplicate or case-colliding ZIP path")
            seen.add(raw.casefold())
            if raw == ARCHIVE_PREFIX:
                require(info.is_dir(), "ZIP root must be a directory")
                continue
            relative = safe_relative(raw[len(ARCHIVE_PREFIX) + 1:])
            if info.is_dir():
                continue
            require(info.file_size <= MAX_FILE_BYTES, "File exceeds GitHub import size limit")
            total += info.file_size
            require(total <= MAX_TOTAL_BYTES, "ZIP expands beyond permitted total size")
            files[relative] = info
        require(1 < len(files) <= MAX_FILES, "Unexpected archive file count")
        require("manifest.sha256" in files, "Archive is missing its checksum manifest")
        manifest_bytes = zf.read(files["manifest.sha256"])
        require(len(manifest_bytes) <= 2 * 1024 * 1024, "Manifest is unexpectedly large")
        manifest = {}
        for line in manifest_bytes.decode("utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            require(match is not None, "Malformed checksum manifest line")
            checksum, name = match.groups()
            safe_relative(name)
            require(name != "manifest.sha256" and name not in manifest, "Invalid duplicate/self checksum entry")
            manifest[name] = checksum
        require(set(manifest) == set(files) - {"manifest.sha256"}, "Manifest does not exactly cover archive files")
        for name, info in files.items():
            target = staging.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            with zf.open(info) as source, target.open("xb") as destination:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    h.update(chunk)
                    destination.write(chunk)
            if name != "manifest.sha256":
                require(h.hexdigest() == manifest[name], "Internal checksum mismatch: " + name)
            target.chmod(0o644)
    return sorted(files)


def git(*args: str, env: dict | None = None) -> str:
    return subprocess.check_output(["git", *args], text=True, env=env).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-archive", type=Path, help="Verify a local archive without network or Git changes")
    arguments = parser.parse_args()
    require(re.fullmatch(r"[0-9a-f]{64}", EXPECTED_SHA256) is not None, "Supply the sealed lowercase SHA256 as INPUT_ARCHIVE_SHA256")
    with tempfile.TemporaryDirectory(prefix="ssi-reviewed-import-") as temp:
        temporary = Path(temp)
        stage = temporary / "verified"
        stage.mkdir()
        if arguments.local_archive:
            names = verify_and_stage(arguments.local_archive, stage)
            print(json.dumps({"status": "verified", "files": len(names), "archive_sha256": EXPECTED_SHA256}, sort_keys=True))
            return
        require(os.environ.get("GITHUB_REPOSITORY") == REPOSITORY, "Workflow repository differs from the approved repository")
        require(os.environ.get("GITHUB_REF") == "refs/heads/main", "Import is restricted to main")
        require(os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch", "Only manual workflow dispatch is allowed")
        token = os.environ.get("GH_TOKEN", "")
        require(bool(token), "Missing repository-scoped workflow token")
        require(git("rev-parse", "--show-toplevel") == str(Path.cwd().resolve()), "Run from the repository root")
        require(not git("status", "--porcelain"), "Repository must be clean before import")
        asset = find_draft_asset(token)
        archive = temporary / "package.zip"
        download_asset(asset, token, archive)
        names = verify_and_stage(archive, stage)
        # Verification finishes before any file in the checkout is changed.
        root = Path.cwd().resolve()
        for name in names:
            target = root.joinpath(*PurePosixPath(name).parts)
            require(not any(parent.is_symlink() for parent in [target, *target.parents] if parent != root.parent), "Existing symlink in import destination")
            require(target.resolve().is_relative_to(root), "Destination escapes checkout")
            require(not target.exists() or target.is_file(), "Import destination is not a regular file")
            if PurePosixPath(name).parts[0] == ".github":
                require(target.is_file() and digest(target) == digest(stage / name), "Archive workflow/bootstrap bytes differ from the reviewed checkout: " + name)
        for name in names:
            if PurePosixPath(name).parts[0] == ".github":
                continue
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(stage / name, target)
            target.chmod(0o644)
        git("config", "user.name", "github-actions[bot]")
        git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        git("add", "--", *(name for name in names if PurePosixPath(name).parts[0] != ".github"))
        if not git("diff", "--cached", "--name-only"):
            print("Verified package already matches the repository; nothing to commit.")
            return
        git("commit", "-m", "Import verified study code package " + TAG)
        # Keep the short-lived token out of command arguments and .git/config.
        push_env = os.environ.copy()
        push_env["GIT_CONFIG_COUNT"] = "1"
        push_env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
        push_env["GIT_CONFIG_VALUE_0"] = "AUTHORIZATION: basic " + base64.b64encode(("x-access-token:" + token).encode()).decode()
        push_env["GIT_TERMINAL_PROMPT"] = "0"
        git("push", "https://github.com/" + REPOSITORY + ".git", "HEAD:refs/heads/main", env=push_env)
        print(json.dumps({"status": "imported", "files_verified": len(names), "commit": git("rev-parse", "HEAD"), "archive_sha256": EXPECTED_SHA256}, sort_keys=True))


if __name__ == "__main__":
    main()
