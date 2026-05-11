#!/usr/bin/env python3
"""Small CLI for the Mobi-Clim CMS page API."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or update Mobi-Clim CMS pages through the API.",
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.base_url:
        parser.error("Missing --base-url or MOBI_CLIM_CMS_API_BASE_URL")
    if not args.token:
        parser.error("Missing --token or MOBI_CLIM_CMS_API_TOKEN")

    payload = load_payload(args.payload)
    base_url = args.base_url.rstrip("/")

    if args.command == "create":
        method = "POST"
        url = f"{base_url}/api/admin/cms/pages"
    else:
        method = "PATCH"
        url = f"{base_url}/api/admin/cms/pages/{args.page_id}"

    status, response = request_json(method, url, payload, args.token)
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
