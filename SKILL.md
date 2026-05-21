---
name: mobi-clim-cms
description: Manage the Mobi-Clim CMS and CMS-authenticated admin API. Use when Codex needs to list, get, create, batch upsert, update, publish, schedule, unpublish, upload media, generate article imagery with imagegen using the bundled Mobi-Clim brand kit, or document CMS content programmatically through the Mobi-Clim routes GET/POST /api/admin/cms/pages, GET/PATCH /api/admin/cms/pages/:pageId, POST/PATCH /api/admin/cms/pages/batch, GET/POST /api/admin/cms/orders, GET/PATCH/DELETE /api/admin/cms/orders/:orderId, GET/POST /api/admin/cms/users, GET/PATCH/DELETE /api/admin/cms/users/:userId, GET /api/admin/cms/email-logs, GET/DELETE /api/admin/cms/email-logs/:logId, POST /api/cron/mobi-clim/cms-publishing, and POST /api/cms/media.
---

# Mobi-Clim CMS

Use Mobi-Clim CMS to operate CMS pages, media, orders, users, and email logs through the programmatic API instead of the admin UI.

## Workflow

1. Identify the target app URL and environment.
   - Prefer explicit user-provided URL.
   - Otherwise use `MOBI_CLIM_CMS_API_BASE_URL`, `NEXT_PUBLIC_APP_URL`, `APP_URL`, or `BETTER_AUTH_URL`.
   - Do not target production unless the user explicitly asks.
2. Authenticate.
   - Use an admin session only when already available in the request context.
   - For external/API work, use bearer auth with a generated CMS API key or `MOBI_CLIM_CMS_API_TOKEN`.
   - When using the legacy env token, ensure the app has `MOBI_CLIM_CMS_API_USER_ID` set to an existing admin user id.
3. Build a JSON payload with the CMS fields.
4. Send the request.
   - List/search pages: `GET /api/admin/cms/pages`
   - Get one page: `GET /api/admin/cms/pages/:pageId`
   - Create: `POST /api/admin/cms/pages`
   - Update/publish/unpublish: `PATCH /api/admin/cms/pages/:pageId`
   - Batch upsert by slug, up to 50 pages: `POST /api/admin/cms/pages/batch`
   - Batch publish or schedule, up to 50 pages: `PATCH /api/admin/cms/pages/batch`
   - List/search orders: `GET /api/admin/cms/orders`
   - Get one order: `GET /api/admin/cms/orders/:orderId`
   - Create an order: `POST /api/admin/cms/orders`
   - Update order status or note: `PATCH /api/admin/cms/orders/:orderId`
   - Cancel an order: `DELETE /api/admin/cms/orders/:orderId`
   - List/search users: `GET /api/admin/cms/users`
   - Get one user: `GET /api/admin/cms/users/:userId`
   - Create a user: `POST /api/admin/cms/users`
   - Update a user: `PATCH /api/admin/cms/users/:userId`
   - Delete a user without attached orders: `DELETE /api/admin/cms/users/:userId`
   - List/search email logs: `GET /api/admin/cms/email-logs`
   - Get or delete an audited email log: `GET/DELETE /api/admin/cms/email-logs/:logId`
   - Upload media: `POST /api/cms/media`
   - Publish due scheduled pages: `POST /api/cron/mobi-clim/cms-publishing`
5. Verify the response includes `page.id`, `page.slug`, `page.status`, `editPath`, `previewPath`, and, for published pages, `publicPath`.
   - For list responses, verify `pages[]` and `nextCursor`.
   - For batch responses, verify `results[]`, `summary`, and any `missing` selectors.
   - For media uploads, verify `id`, `url`, `mimeType`, `sizeBytes`, `width`, and `height`.
   - For order responses, verify `order.id`, `order.orderNumber`, `status`, `paymentStatus`, monetary totals, addresses, items, payments, invoices, and shipments.
   - For user responses, verify `user.id`, `email`, `role`, account flags, profile fields, and counts.
   - For email log responses, verify `emailLogs[]` or `emailLog`, `status`, `source`, `event`, `recipient`, `subject`, `entityType`, and `entityId`.

## Page Payload Fields

Required for create:

- `title`

Optional for create/update:

- `slug`
- `status`: `DRAFT` or `PUBLISHED`
- `type`: `LEGAL`, `MARKETING`, `FAQ`, `LANDING`, or `SYSTEM`
- `contentMarkdown`
- `contentJson`
- `excerpt`
- `seoTitle`
- `seoDescription`
- `canonicalUrl`
- `robots`
- `ogTitle`
- `ogDescription`
- `ogImageId`
- `scheduledAt`: ISO datetime for scheduled publication. Only use with draft/scheduled pages, not immediate `PUBLISHED` payloads.

Use `contentMarkdown` by default. It supports the same Markdown and custom CMS blocks as the admin editor. Use `contentJson` only when the caller already has a compatible CMS/Tiptap document.

## Admin Resources

The CMS bearer key now also authorizes operational admin resources under `/api/admin/cms`. Treat these endpoints as admin-only and audit-sensitive.

Order routes:

- `GET /api/admin/cms/orders`: filters `status`, `paymentStatus`, `search`, `take`, `cursor`.
- `GET /api/admin/cms/orders/:orderId`: returns the order with addresses, items, payments, VosFactures invoices, shipments, labels, and recent tracking events.
- `POST /api/admin/cms/orders`: creates a `PENDING_PAYMENT` order through the same server-side checkout logic as the public reservation flow. This keeps rental duration, pricing, deposit, delivery fee, stock checks, snapshots, notifications, and audit logs server-authoritative.
- `PATCH /api/admin/cms/orders/:orderId`: accepts `status`, `internalNote`, `reason`, and optional `override`. Status changes go through the audited order workflow and synchronize availability blocks.
- `DELETE /api/admin/cms/orders/:orderId`: cancels the order through the audited cancellation workflow. It does not physically delete historical order data. Query params: `reason`, `overrideDelivered=true`.

Do not use the CMS API to mutate payment records directly. Payment state remains driven by Credit Agricole callbacks, payment retry flows, or existing admin workflow helpers.

Order create payload:

```json
{
  "items": [{ "productId": "product_id", "quantity": 1 }],
  "startsAt": "2026-06-15",
  "endsAt": "2026-06-17",
  "customer": {
    "firstName": "Ada",
    "lastName": "Lovelace",
    "email": "ada@example.com",
    "phone": "0600000000",
    "line1": "10 rue de Paris",
    "postalCode": "75001",
    "city": "Paris",
    "country": "FR"
  },
  "acceptedTerms": true
}
```

Order patch payload:

```json
{
  "status": "CONFIRMED",
  "reason": "Validation opérateur",
  "internalNote": "Client appelé le matin."
}
```

User routes:

- `GET /api/admin/cms/users`: filters `role`, `search`, `take`, `cursor`.
- `GET /api/admin/cms/users/:userId`: returns account flags, profile fields, metadata, and counts.
- `POST /api/admin/cms/users`: creates a user. Optional `password` creates a credential account with a hashed password.
- `PATCH /api/admin/cms/users/:userId`: updates identity, role, verification/ban flags, profile fields, and metadata.
- `DELETE /api/admin/cms/users/:userId`: physically deletes only users with no attached orders. For customers with orders, use a ban/update flow instead of deletion to preserve order history.

User create payload:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "role": "user",
  "emailVerified": false,
  "phone": "0600000000"
}
```

Email log routes:

- `GET /api/admin/cms/email-logs`: filters `status` (`all`, `sent`, `skipped`, `error`), `source` (`all`, `order`, `manual`, `contact`), `search`, `take`, `cursor`.
- `GET /api/admin/cms/email-logs/:logId`: returns one audited or derived email log.
- `DELETE /api/admin/cms/email-logs/:logId`: deletes an audited email log and writes a deletion audit record. Derived contact logs such as `contactSubmissionId:client` or `contactSubmissionId:admin` cannot be deleted because they are computed from contact submission columns.

Email logs are not stored in a single dedicated table. Order and manual email logs come from `AuditLog` records whose action starts with `email.`. Contact email logs are derived from contact submission email timestamp/error columns.

## CMS Article Image Generation

When creating an image for a Mobi-Clim CMS article, Open Graph image, blog thumbnail, social preview, or in-article visual, use the `imagegen` skill and the bundled brand-kit boards as image-brand references before generating.

Brand-kit reference files:

- `brand-kit/mobi-clim-brand-kit-overview.png`: overall identity, palette, typography, logo usage, icons, and brand applications.
- `brand-kit/mobi-clim-brand-kit-ui-product.png`: website, reservation, checkout, CMS, admin, and mobile UI direction.
- `brand-kit/mobi-clim-brand-kit-content-campaign.png`: CMS covers, social formats, seasonal campaign images, delivery, packaging, and photo rules.

Reference selection:

- Use `mobi-clim-brand-kit-content-campaign.png` by default for article hero images, Open Graph images, CMS covers, and social crops.
- Add `mobi-clim-brand-kit-overview.png` when the image must strongly express the core brand system.
- Use `mobi-clim-brand-kit-ui-product.png` when the image includes product UI, booking screens, payment, admin, or CMS interface mockups.

Before calling `imagegen`, inspect the selected brand-kit image(s) with `view_image` so they are visible in the conversation context and can be used as style/reference images.

Default image direction:

- Brand: French mobile air-conditioner rental, easy summer comfort, no installation, delivery and pickup, secure online booking.
- Visual world: warm daylight interiors, clean apartments/offices, mobile air conditioner near a window, subtle airflow lines, practical local service.
- Palette: dark surface `#101413`, deep surface `#10192d`, champagne `#e9c58a`, bronze `#d4af72`, teal `#2a8277`, coral action `#e95e4f`, off-white `#f7f5f2`, muted grey `#647082`.
- Typography/UI feel: Geist-like modern sans, shadcn/ui-style controls, modest radius, crisp spacing, restrained shadows.
- Text: avoid text inside generated article images unless the user explicitly asks for it. If text is needed, keep it short, French, and quote it verbatim in the prompt.
- Avoid: generic stock HVAC imagery, beach/pool scenes, medical or emergency imagery, purple/blue SaaS gradients, fake bank logos, cluttered ad collages, excessive snowflakes, illegible tiny copy, and watermarks.

Prompt scaffold:

```text
Use case: ads-marketing
Asset type: Mobi-Clim CMS article image / Open Graph image
Input images: selected Mobi-Clim brand-kit board(s) as brand references
Primary request: <article topic and intended placement>
Scene/backdrop: warm daylight French interior with mobile air conditioner, clean and realistic
Subject: <specific article subject, e.g. canicule, location Airbnb, appartement, bureau>
Style/medium: premium editorial product-lifestyle image aligned with the Mobi-Clim brand kit
Composition/framing: CMS cover / OG-ready landscape, clear focal point, safe crop margins
Color palette: #101413, #10192d, #e9c58a, #d4af72, #2a8277, #e95e4f, #f7f5f2, #647082
Constraints: brand-aligned, practical, local, trustworthy, no watermark, no fake logos
Avoid: clutter, unrelated appliances, beach/pool imagery, medical tone, illegible text
```

For CMS-bound generated images, copy the final selected image out of the default imagegen folder into a stable local path before upload, then upload it with `scripts/mobi_clim_cms.py upload`. Use a descriptive French `alt` and optional `caption`. Use the returned media `id` as `ogImageId` when the image is the page Open Graph image, and use the returned `url` in Markdown when embedding it in the article body.

## Page Listing

List pages:

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py list \
  --status DRAFT \
  --type MARKETING \
  --search canicule \
  --take 50
```

Supported filters:

- `status`: `DRAFT` or `PUBLISHED`
- `type`: `LEGAL`, `MARKETING`, `FAQ`, `LANDING`, or `SYSTEM`
- `search`
- `slug`
- `take`, clamped server-side
- `cursor`
- `--include-content` to return Markdown, JSON, and rendered HTML

Get one page:

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py get <pageId> --include-content
```

## Media Uploads

Upload CMS images before creating pages when an Open Graph image or Markdown image is needed:

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py upload ./hero.jpg \
  --alt "Climatiseur mobile dans un salon" \
  --caption "Location Mobi-Clim"
```

The app converts uploaded CMS media to AVIF by default and stores the media as a `MediaAsset`.
Use the returned `id` as `ogImageId` in page payloads. Use the returned `url` in Markdown image syntax.

If the original file format must be preserved, pass:

```bash
--format source
```

Upload response fields:

- `id`
- `url`
- `alt`
- `caption`
- `fileName`
- `mimeType`
- `sizeBytes`
- `width`
- `height`
- `storageKey`

## Common Operations

Create a draft:

```json
{
  "title": "Guide location climatiseur mobile",
  "slug": "guides/location-climatiseur-mobile",
  "status": "DRAFT",
  "type": "MARKETING",
  "contentMarkdown": "## Intro\n\nTexte de la page.",
  "excerpt": "Resume affiche dans le hero.",
  "seoTitle": "Location climatiseur mobile : guide complet",
  "seoDescription": "Comprendre comment louer un climatiseur mobile avec Mobi-Clim.",
  "robots": "index,follow"
}
```

Publish an existing page:

```json
{
  "status": "PUBLISHED"
}
```

Unpublish an existing page:

```json
{
  "status": "DRAFT"
}
```

Schedule a draft:

```json
{
  "status": "DRAFT",
  "scheduledAt": "2026-06-01T08:00:00.000Z"
}
```

## Batch Workflows

Upsert up to 50 pages by slug:

```json
{
  "pages": [
    {
      "title": "Guide canicule",
      "slug": "guides/canicule",
      "status": "DRAFT",
      "type": "MARKETING",
      "contentMarkdown": "## Intro\n\nTexte de la page."
    }
  ]
}
```

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py batch-upsert batch-pages.json
```

Publish pages immediately:

```json
{
  "slugs": ["guides/canicule", "guides/location-clim-airbnb"],
  "status": "PUBLISHED"
}
```

Schedule pages:

```json
{
  "ids": ["page_id_1", "page_id_2"],
  "scheduledAt": "2026-06-01T08:00:00.000Z"
}
```

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py batch-update batch-publication.json
```

Batch limits and behavior:

- `POST /api/admin/cms/pages/batch` accepts `pages` with 1 to 50 items.
- Each batch upsert item must include `slug`.
- Existing slugs are updated; missing slugs are created.
- `PATCH /api/admin/cms/pages/batch` accepts either `ids` or `slugs`, but not both.
- Scheduling sets pages back to `DRAFT` and stores `scheduledAt`.
- Immediate publication uses `status: "PUBLISHED"` and must not include a non-null `scheduledAt`.
- Batch update responses include `missing` selectors for ids/slugs not found.

## Scheduled Publishing

Pages with `scheduledAt` are published by the app cron endpoint:

```bash
curl -X POST "$MOBI_CLIM_CMS_API_BASE_URL/api/cron/mobi-clim/cms-publishing" \
  -H "x-mobi-clim-cron-secret: $MOBI_CLIM_CRON_SECRET"
```

This endpoint uses `MOBI_CLIM_CMS_API_USER_ID` as the admin actor for revisions and audit logs. It is not bearer-token authenticated.

## CLI Helper

Use `scripts/mobi_clim_cms.py` for repeatable calls:

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py create payload.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py list --status DRAFT --take 50
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py get <pageId> --include-content
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py update <pageId> payload.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py batch-upsert batch-pages.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py batch-update batch-publication.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py upload image.jpg --alt "Image alt"
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py list-orders --status PAID --take 50
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py get-order <orderId>
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py create-order order.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py update-order <orderId> order-patch.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py cancel-order <orderId> --reason "Annulation client"
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py list-users --role admin
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py get-user <userId>
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py create-user user.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py update-user <userId> user-patch.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py delete-user <userId>
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py list-email-logs --source order --status error
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py get-email-log <logId>
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py delete-email-log <logId>
```

The script reads:

- `--base-url` or `MOBI_CLIM_CMS_API_BASE_URL`
- `--token` or `MOBI_CLIM_CMS_API_TOKEN`

Use `-` as the payload path to read JSON from stdin.

## References

Read `references/mobi-clim-cms-api.md` when exact routes, response shapes, error handling, or Markdown block syntax are needed.
