#!/usr/bin/env python3
"""Small CLI for the Mobi-Clim CMS page and media API."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid


def default_base_url() -> str | None:
    for name in (
        "MOBI_CLIM_CMS_API_BASE_URL",
        "NEXT_PUBLIC_APP_URL",
        "APP_URL",
        "BETTER_AUTH_URL",
    ):
        value = os.environ.get(name)
        if value:
            return value.rstrip("/")
    return None


def load_payload(path: str) -> object:
    if path == "-":
        return json.load(sys.stdin)

    with open(path, "r", encoding="utf-8") as payload_file:
        return json.load(payload_file)


def request_json(
    method: str,
    url: str,
    payload: object,
    token: str,
) -> tuple[int, object]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read().decode("utf-8")
            return response.status, json.loads(response_body)
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        try:
            parsed_error: object = json.loads(error_body)
        except json.JSONDecodeError:
            parsed_error = {"error": error_body or error.reason}
        return error.code, parsed_error


def request_multipart(
    method: str,
    url: str,
    fields: dict[str, str],
    file_field: str,
    file_path: str,
    token: str,
) -> tuple[int, object]:
    boundary = f"----mobi-clim-cms-{uuid.uuid4().hex}"
    body_parts: list[bytes] = []

    for name, value in fields.items():
        body_parts.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(
                    "utf-8",
                ),
                value.encode("utf-8"),
                b"\r\n",
            ],
        )

    filename = os.path.basename(file_path)
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    with open(file_path, "rb") as media_file:
        file_bytes = media_file.read()

    body_parts.extend(
        [
            f"--{boundary}\r\n".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{filename}"\r\n'
            ).encode("utf-8"),
            f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"),
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("utf-8"),
        ],
    )

    body = b"".join(body_parts)
    request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            response_body = response.read().decode("utf-8")
            return response.status, json.loads(response_body)
    except urllib.error.HTTPError as error:
        error_body = error.read().decode("utf-8")
        try:
            parsed_error: object = json.loads(error_body)
        except json.JSONDecodeError:
            parsed_error = {"error": error_body or error.reason}
        return error.code, parsed_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create/update Mobi-Clim CMS pages and upload CMS media through the API.",
    )
    parser.add_argument(
        "--base-url",
        default=default_base_url(),
        help="App base URL. Defaults to MOBI_CLIM_CMS_API_BASE_URL, NEXT_PUBLIC_APP_URL, APP_URL, or BETTER_AUTH_URL.",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("MOBI_CLIM_CMS_API_TOKEN"),
        help="Bearer token. Defaults to MOBI_CLIM_CMS_API_TOKEN.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print compact JSON instead of pretty JSON.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="Create a CMS page.")
    create.add_argument("payload", help="JSON payload file, or - for stdin.")

    update = subparsers.add_parser("update", help="Update a CMS page.")
    update.add_argument("page_id", help="CMS page id.")
    update.add_argument("payload", help="JSON payload file, or - for stdin.")

    upload = subparsers.add_parser("upload", help="Upload a CMS media asset.")
    upload.add_argument("file", help="Image file path.")
    upload.add_argument("--alt", default="", help="Image alt text.")
    upload.add_argument("--caption", default="", help="Image caption.")
    upload.add_argument(
        "--format",
        default="avif",
        choices=("avif", "source", "original"),
        help="Stored media format. Defaults to avif.",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.base_url:
        parser.error("Missing --base-url or MOBI_CLIM_CMS_API_BASE_URL")
    if not args.token:
        parser.error("Missing --token or MOBI_CLIM_CMS_API_TOKEN")

    base_url = args.base_url.rstrip("/")

    if args.command == "create":
        payload = load_payload(args.payload)
        method = "POST"
        url = f"{base_url}/api/admin/cms/pages"
        status, response = request_json(method, url, payload, args.token)
    elif args.command == "update":
        payload = load_payload(args.payload)
        method = "PATCH"
        url = f"{base_url}/api/admin/cms/pages/{args.page_id}"
        status, response = request_json(method, url, payload, args.token)
    else:
        url = f"{base_url}/api/cms/media"
        status, response = request_multipart(
            "POST",
            url,
            {
                "alt": args.alt,
                "caption": args.caption,
                "format": args.format,
            },
            "file",
            args.file,
            args.token,
        )

    print(
        json.dumps(
            response,
            ensure_ascii=False,
            separators=(",", ":") if args.compact else None,
            indent=None if args.compact else 2,
        ),
    )

    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())
