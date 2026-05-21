#!/usr/bin/env python3
"""Small CLI for the Mobi-Clim CMS and admin resource API."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.parse
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
    payload: object | None,
    token: str,
) -> tuple[int, object]:
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
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


def append_query(url: str, params: dict[str, str | None]) -> str:
    query = {name: value for name, value in params.items() if value not in (None, "")}
    if not query:
        return url

    return f"{url}?{urllib.parse.urlencode(query)}"


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
        description="Operate Mobi-Clim CMS pages, media, orders, users, and email logs through the API.",
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

    list_pages = subparsers.add_parser("list", help="List CMS pages.")
    list_pages.add_argument("--status", choices=("DRAFT", "PUBLISHED"))
    list_pages.add_argument(
        "--type",
        choices=("LEGAL", "MARKETING", "FAQ", "LANDING", "SYSTEM"),
    )
    list_pages.add_argument("--search", help="Search title, slug, or excerpt.")
    list_pages.add_argument("--slug", help="Filter by exact slug.")
    list_pages.add_argument("--take", type=int, help="Page size.")
    list_pages.add_argument("--cursor", help="Pagination cursor.")
    list_pages.add_argument(
        "--include-content",
        action="store_true",
        help="Include Markdown, JSON, and rendered HTML.",
    )

    get = subparsers.add_parser("get", help="Get a CMS page.")
    get.add_argument("page_id", help="CMS page id.")
    get.add_argument(
        "--include-content",
        action="store_true",
        help="Include Markdown, JSON, and rendered HTML.",
    )

    update = subparsers.add_parser("update", help="Update a CMS page.")
    update.add_argument("page_id", help="CMS page id.")
    update.add_argument("payload", help="JSON payload file, or - for stdin.")

    batch_upsert = subparsers.add_parser(
        "batch-upsert",
        help="Create or update up to 50 CMS pages by slug.",
    )
    batch_upsert.add_argument("payload", help="JSON payload file, or - for stdin.")

    batch_update = subparsers.add_parser(
        "batch-update",
        help="Publish or schedule up to 50 CMS pages by ids or slugs.",
    )
    batch_update.add_argument("payload", help="JSON payload file, or - for stdin.")

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

    list_orders = subparsers.add_parser("list-orders", help="List Mobi-Clim orders.")
    list_orders.add_argument("--status", help="Filter by OrderStatus.")
    list_orders.add_argument("--payment-status", help="Filter by PaymentStatus.")
    list_orders.add_argument("--search", help="Search order number, email, or phone.")
    list_orders.add_argument("--take", type=int, help="Page size.")
    list_orders.add_argument("--cursor", help="Pagination cursor.")

    get_order = subparsers.add_parser("get-order", help="Get a Mobi-Clim order.")
    get_order.add_argument("order_id", help="Order id.")

    create_order = subparsers.add_parser(
        "create-order",
        help="Create a pending-payment order through the server-side checkout logic.",
    )
    create_order.add_argument("payload", help="JSON payload file, or - for stdin.")

    update_order = subparsers.add_parser(
        "update-order",
        help="Update an order status and/or internal note.",
    )
    update_order.add_argument("order_id", help="Order id.")
    update_order.add_argument("payload", help="JSON payload file, or - for stdin.")

    cancel_order = subparsers.add_parser(
        "cancel-order",
        help="Cancel an order through the audited order workflow.",
    )
    cancel_order.add_argument("order_id", help="Order id.")
    cancel_order.add_argument("--reason", help="Cancellation reason.")
    cancel_order.add_argument(
        "--override-delivered",
        action="store_true",
        help="Allow cancellation after delivery states.",
    )

    list_users = subparsers.add_parser("list-users", help="List users.")
    list_users.add_argument("--role", help="Filter by role, for example user or admin.")
    list_users.add_argument("--search", help="Search name, email, or phone.")
    list_users.add_argument("--take", type=int, help="Page size.")
    list_users.add_argument("--cursor", help="Pagination cursor.")

    get_user = subparsers.add_parser("get-user", help="Get a user.")
    get_user.add_argument("user_id", help="User id.")

    create_user = subparsers.add_parser("create-user", help="Create a user.")
    create_user.add_argument("payload", help="JSON payload file, or - for stdin.")

    update_user = subparsers.add_parser("update-user", help="Update a user.")
    update_user.add_argument("user_id", help="User id.")
    update_user.add_argument("payload", help="JSON payload file, or - for stdin.")

    delete_user = subparsers.add_parser(
        "delete-user",
        help="Delete a user when no orders are attached.",
    )
    delete_user.add_argument("user_id", help="User id.")

    list_email_logs = subparsers.add_parser(
        "list-email-logs",
        help="List audited and derived email logs.",
    )
    list_email_logs.add_argument(
        "--status",
        choices=("all", "sent", "skipped", "error"),
        help="Filter by email send result.",
    )
    list_email_logs.add_argument(
        "--source",
        choices=("all", "order", "manual", "contact"),
        help="Filter by source.",
    )
    list_email_logs.add_argument("--search", help="Search log fields.")
    list_email_logs.add_argument("--take", type=int, help="Page size.")
    list_email_logs.add_argument("--cursor", help="Pagination cursor.")

    get_email_log = subparsers.add_parser("get-email-log", help="Get an email log.")
    get_email_log.add_argument("log_id", help="Email log id.")

    delete_email_log = subparsers.add_parser(
        "delete-email-log",
        help="Delete an audited email log. Derived contact logs cannot be deleted.",
    )
    delete_email_log.add_argument("log_id", help="Email log id.")

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
    elif args.command == "list":
        url = append_query(
            f"{base_url}/api/admin/cms/pages",
            {
                "status": args.status,
                "type": args.type,
                "search": args.search,
                "slug": args.slug,
                "take": str(args.take) if args.take else None,
                "cursor": args.cursor,
                "includeContent": "true" if args.include_content else None,
            },
        )
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "get":
        url = append_query(
            f"{base_url}/api/admin/cms/pages/{args.page_id}",
            {
                "includeContent": "true" if args.include_content else None,
            },
        )
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "update":
        payload = load_payload(args.payload)
        method = "PATCH"
        url = f"{base_url}/api/admin/cms/pages/{args.page_id}"
        status, response = request_json(method, url, payload, args.token)
    elif args.command == "batch-upsert":
        payload = load_payload(args.payload)
        method = "POST"
        url = f"{base_url}/api/admin/cms/pages/batch"
        status, response = request_json(method, url, payload, args.token)
    elif args.command == "batch-update":
        payload = load_payload(args.payload)
        method = "PATCH"
        url = f"{base_url}/api/admin/cms/pages/batch"
        status, response = request_json(method, url, payload, args.token)
    elif args.command == "upload":
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
    elif args.command == "list-orders":
        url = append_query(
            f"{base_url}/api/admin/cms/orders",
            {
                "status": args.status,
                "paymentStatus": args.payment_status,
                "search": args.search,
                "take": str(args.take) if args.take else None,
                "cursor": args.cursor,
            },
        )
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "get-order":
        url = f"{base_url}/api/admin/cms/orders/{args.order_id}"
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "create-order":
        payload = load_payload(args.payload)
        url = f"{base_url}/api/admin/cms/orders"
        status, response = request_json("POST", url, payload, args.token)
    elif args.command == "update-order":
        payload = load_payload(args.payload)
        url = f"{base_url}/api/admin/cms/orders/{args.order_id}"
        status, response = request_json("PATCH", url, payload, args.token)
    elif args.command == "cancel-order":
        url = append_query(
            f"{base_url}/api/admin/cms/orders/{args.order_id}",
            {
                "reason": args.reason,
                "overrideDelivered": "true" if args.override_delivered else None,
            },
        )
        status, response = request_json("DELETE", url, None, args.token)
    elif args.command == "list-users":
        url = append_query(
            f"{base_url}/api/admin/cms/users",
            {
                "role": args.role,
                "search": args.search,
                "take": str(args.take) if args.take else None,
                "cursor": args.cursor,
            },
        )
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "get-user":
        url = f"{base_url}/api/admin/cms/users/{args.user_id}"
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "create-user":
        payload = load_payload(args.payload)
        url = f"{base_url}/api/admin/cms/users"
        status, response = request_json("POST", url, payload, args.token)
    elif args.command == "update-user":
        payload = load_payload(args.payload)
        url = f"{base_url}/api/admin/cms/users/{args.user_id}"
        status, response = request_json("PATCH", url, payload, args.token)
    elif args.command == "delete-user":
        url = f"{base_url}/api/admin/cms/users/{args.user_id}"
        status, response = request_json("DELETE", url, None, args.token)
    elif args.command == "list-email-logs":
        url = append_query(
            f"{base_url}/api/admin/cms/email-logs",
            {
                "status": args.status,
                "source": args.source,
                "search": args.search,
                "take": str(args.take) if args.take else None,
                "cursor": args.cursor,
            },
        )
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "get-email-log":
        url = f"{base_url}/api/admin/cms/email-logs/{urllib.parse.quote(args.log_id, safe='')}"
        status, response = request_json("GET", url, None, args.token)
    elif args.command == "delete-email-log":
        url = f"{base_url}/api/admin/cms/email-logs/{urllib.parse.quote(args.log_id, safe='')}"
        status, response = request_json("DELETE", url, None, args.token)
    else:
        parser.error(f"Unsupported command: {args.command}")

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
