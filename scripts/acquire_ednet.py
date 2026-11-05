#!/usr/bin/env python3
"""Acquire only the official EdNet KT1 and question-content archives.

The original archives are stored unchanged under <data-root>/raw/ednet.
Interrupted HTTP transfers resume where the server supports Range requests.
The script verifies ZIP CRCs, records SHA-256 and response metadata, and does
not extract or preprocess files.
"""

from __future__ import annotations

import argparse
import hashlib
import html.parser
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


SOURCES = {
    "ednet-kt1.zip": "https://bit.ly/ednet_kt1",
    "ednet-content.zip": "https://bit.ly/ednet-content",
}
OFFICIAL_REPOSITORY = "https://github.com/riiid/ednet"
USER_AGENT = "MCP-RI-EdNet-Research/1.0 (dataset acquisition; Python urllib)"


class _FormParser(html.parser.HTMLParser):
    """Capture the first form action and its hidden/input values."""

    def __init__(self) -> None:
        super().__init__()
        self.action: str | None = None
        self.values: dict[str, str] = {}
        self.method = "get"
        self.in_first_form = False
        self.seen_form = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "form" and not self.seen_form:
            self.seen_form = True
            self.in_first_form = True
            self.action = attrs_dict.get("action")
            self.method = (attrs_dict.get("method") or "get").lower()
        elif tag == "input" and self.in_first_form:
            name, value = attrs_dict.get("name"), attrs_dict.get("value")
            if name:
                self.values[name] = value or ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "form" and self.in_first_form:
            self.in_first_form = False


def _opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def _request(opener: urllib.request.OpenerDirector, url: str, headers: dict[str, str] | None = None):
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(headers)
    return opener.open(urllib.request.Request(url, headers=request_headers), timeout=90)


def _resolve_download(opener: urllib.request.OpenerDirector, source_url: str) -> tuple[str, str, dict[str, str]]:
    """Resolve the official short link and Google Drive confirmation form."""
    with _request(opener, source_url) as response:
        final_url = response.geturl()
        content_type = response.headers.get("Content-Type", "")
        if "zip" in content_type.lower() or "octet-stream" in content_type.lower():
            return final_url, "get", {}
        body = response.read(2_000_000)

    match = re.search(r"/file/d/([A-Za-z0-9_-]+)", final_url)
    if not match:
        raise RuntimeError(f"Official link did not resolve to a recognizable download: {final_url}")
    file_id = match.group(1)
    download_url = "https://drive.google.com/uc?export=download&id=" + urllib.parse.quote(file_id)

    # Google Drive may return a confirmation form for large files. Submit its
    # actual form action and hidden fields instead of assuming a token value.
    with _request(opener, download_url) as response:
        content_type = response.headers.get("Content-Type", "")
        resolved = response.geturl()
        if "zip" in content_type.lower() or "octet-stream" in content_type.lower():
            return resolved, "get", {}
        html_bytes = response.read(2_000_000)
    parser = _FormParser()
    parser.feed(html_bytes.decode("utf-8", errors="replace"))
    if parser.action and parser.values:
        return urllib.parse.urljoin(download_url, parser.action), parser.method, parser.values

    # Some Drive versions put the confirmation token in a warning cookie.
    # The opener's cookie jar is retained and the token can be passed as query.
    token = None
    for handler in opener.handlers:
        cookiejar = getattr(handler, "cookiejar", None)
        if cookiejar:
            for cookie in cookiejar:
                if cookie.name.startswith("download_warning"):
                    token = cookie.value
                    break
    if token:
        parsed = urllib.parse.urlsplit(download_url)
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        query.append(("confirm", token))
        return urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query))), "get", {}

    snippet = html_bytes[:240].decode("utf-8", errors="replace").replace("\n", " ")
    raise RuntimeError(f"Provider returned an unsupported confirmation page: {snippet}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download_one(name: str, source_url: str, raw_dir: Path) -> dict[str, Any]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / name
    partial = raw_dir / (name + ".part")
    metadata_path = raw_dir / (name + ".metadata.json")

    if destination.exists():
        if not zipfile.is_zipfile(destination):
            raise RuntimeError(f"Existing file is not a ZIP archive: {destination}; preserve it and choose another data root")
        bad_member = _test_zip(destination)
        if bad_member:
            raise RuntimeError(f"Existing ZIP failed CRC verification at member {bad_member!r}")
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        metadata["sha256"] = _sha256(destination)
        metadata["integrity_check"] = "zip CRC passed; SHA-256 recorded"
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
        print(f"Verified existing archive: {destination}")
        return metadata

    opener = _opener()
    download_url, method, confirmation = _resolve_download(opener, source_url)
    existing = partial.stat().st_size if partial.exists() else 0
    request_headers: dict[str, str] = {}
    if existing:
        request_headers["Range"] = f"bytes={existing}-"
    if confirmation and method == "get":
        query = urllib.parse.urlencode(confirmation)
        separator = "&" if "?" in download_url else "?"
        download_url = download_url + separator + query
    elif confirmation:
        existing = 0
        partial.unlink(missing_ok=True)

    try:
        if method == "post":
            request = urllib.request.Request(
                download_url,
                data=urllib.parse.urlencode(confirmation).encode(),
                headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
            )
            response = opener.open(request, timeout=90)
        else:
            response = _request(opener, download_url, request_headers)
        status = getattr(response, "status", response.getcode())
        if existing and status != 206:
            # The server ignored Range; restart to avoid a corrupt concatenation.
            response.close()
            existing = 0
            partial.unlink(missing_ok=True)
            response = _request(opener, download_url)
            status = getattr(response, "status", response.getcode())
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type.lower():
            body = response.read(2_000_000)
            response.close()
            parser = _FormParser()
            parser.feed(body.decode("utf-8", errors="replace"))
            if parser.action and parser.values:
                form_url = urllib.parse.urljoin(download_url, parser.action)
                if parser.method == "post":
                    encoded = urllib.parse.urlencode(parser.values).encode()
                    req = urllib.request.Request(
                        form_url,
                        data=encoded,
                        headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"},
                    )
                    response = opener.open(req, timeout=90)
                else:
                    query = urllib.parse.urlencode(parser.values)
                    separator = "&" if "?" in form_url else "?"
                    response = _request(opener, form_url + separator + query)
                existing = 0
                partial.unlink(missing_ok=True)
                content_type = response.headers.get("Content-Type", "")
            if "text/html" in content_type.lower():
                raise RuntimeError("Provider returned HTML instead of the requested archive")

        mode = "ab" if existing else "wb"
        downloaded_now = 0
        with response, partial.open(mode) as output:
            while True:
                block = response.read(8 * 1024 * 1024)
                if not block:
                    break
                output.write(block)
                downloaded_now += len(block)
                if downloaded_now and downloaded_now % (128 * 1024 * 1024) < len(block):
                    print(f"{name}: {existing + downloaded_now:,} bytes received", flush=True)
            output.flush()
            os.fsync(output.fileno())
            headers = dict(response.headers.items())
            resolved_url = response.geturl()
            status = getattr(response, "status", response.getcode())
    except (urllib.error.URLError, TimeoutError, OSError):
        # Keep .part so a subsequent invocation can try a byte-range resume.
        raise

    if not zipfile.is_zipfile(partial):
        raise RuntimeError(f"Downloaded response is not a valid ZIP archive; partial retained at {partial}")
    bad_member = _test_zip(partial)
    if bad_member:
        raise RuntimeError(f"ZIP CRC verification failed for member {bad_member!r}; partial retained")
    partial.replace(destination)

    metadata: dict[str, Any] = {
        "filename": name,
        "source_url": source_url,
        "official_repository": OFFICIAL_REPOSITORY,
        "resolved_url": resolved_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "http_status": status,
        "content_type": headers.get("Content-Type"),
        "content_length_header": headers.get("Content-Length"),
        "etag": headers.get("ETag"),
        "last_modified": headers.get("Last-Modified"),
        "size_bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
        "integrity_check": "ZIP structure and every member CRC passed; SHA-256 recorded",
        "license": "CC BY-NC 4.0; research/non-commercial use; attribution required",
        "download_script_version": "1.0.0",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n")
    print(f"Downloaded and verified {destination} ({metadata['size_bytes']:,} bytes)")
    return metadata


def _test_zip(path: Path) -> str | None:
    with zipfile.ZipFile(path) as archive:
        return archive.testzip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(os.environ.get("MCP_RI_DATA_DIR", Path(__file__).resolve().parents[1] / "data")),
        help="dataset root (default: MCP_RI_DATA_DIR or repository data/)",
    )
    args = parser.parse_args(argv)
    raw_dir = args.data_root.expanduser() / "raw" / "ednet"

    try:
        for filename, url in SOURCES.items():
            _download_one(filename, url, raw_dir)
    except Exception as exc:
        print(f"Acquisition failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
