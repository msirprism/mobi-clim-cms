# Mobi-Clim CMS API Reference

## Authentication

Routes accept either:

- an authenticated Better Auth admin session cookie; or
- `Authorization: Bearer <generated-cms-api-key>` or `Authorization: Bearer <MOBI_CLIM_CMS_API_TOKEN>`.

For the legacy env bearer token, the deployed app must also set
`MOBI_CLIM_CMS_API_USER_ID` to an existing admin user id. Generated CMS API keys use
the admin user that created the key for revisions and audit logs.

## Endpoints

### List Pages

`GET /api/admin/cms/pages`

Query parameters:

- `status`: optional. `DRAFT` or `PUBLISHED`.
- `type`: optional. `LEGAL`, `MARKETING`, `FAQ`, `LANDING`, or `SYSTEM`.
- `search`: optional text search across title, slug, and excerpt.
- `slug`: optional exact slug lookup. The server normalizes the slug.
- `take`: optional page size. The server clamps the value.
- `cursor`: optional page id cursor for pagination.
- `includeContent`: optional. Use `true` or `1` to include `contentMarkdown`, `contentJson`, and `contentHtml`.

Response shape:

```json
{
  "pages": [
    {
      "id": "page_id",
      "title": "Guide canicule",
      "slug": "guides/canicule",
      "type": "MARKETING",
      "status": "DRAFT",
      "excerpt": "Resume",
      "seoTitle": "Guide canicule",
      "seoDescription": "Conseils pour louer une climatisation mobile.",
      "canonicalUrl": null,
      "robots": "index,follow",
      "ogTitle": null,
      "ogDescription": null,
      "ogImageId": null,
      "publishedAt": null,
      "scheduledAt": "2026-06-01T08:00:00.000Z",
      "createdAt": "2026-05-11T10:00:00.000Z",
      "updatedAt": "2026-05-11T10:00:00.000Z",
      "publicPath": null,
      "previewPath": "/admin/cms/page_id/preview",
      "editPath": "/admin/cms/page_id"
    }
  ],
  "nextCursor": null
}
```

### Get Page

`GET /api/admin/cms/pages/:pageId`

Query parameters:

- `includeContent`: optional. Use `true` or `1` to include `contentMarkdown`, `contentJson`, and `contentHtml`.

Response shape:

```json
{
  "page": {
    "id": "page_id",
    "title": "Guide canicule",
    "slug": "guides/canicule",
    "status": "DRAFT",
    "scheduledAt": "2026-06-01T08:00:00.000Z",
    "previewPath": "/admin/cms/page_id/preview",
    "editPath": "/admin/cms/page_id",
    "publicPath": null
  }
}
```

### Create Page

`POST /api/admin/cms/pages`

Minimum payload:

```json
{
  "title": "Page title"
}
```

Response status: `201`

Create payloads may include `scheduledAt` for future publication. Do not send a non-null
`scheduledAt` with `status: "PUBLISHED"`.

### Update Page

`PATCH /api/admin/cms/pages/:pageId`

Payload may contain any supported field. Empty objects are rejected. Omitted fields are
preserved.

Examples:

```json
{ "status": "PUBLISHED" }
```

```json
{ "status": "DRAFT" }
```

Schedule a draft:

```json
{ "status": "DRAFT", "scheduledAt": "2026-06-01T08:00:00.000Z" }
```

Clear scheduled publication:

```json
{ "scheduledAt": null }
```

### Batch Upsert Pages

`POST /api/admin/cms/pages/batch`

Creates or updates up to 50 pages by slug. Each item must include `slug`. Existing
slugs are updated; missing slugs are created. Omitted optional fields are preserved on
existing pages. If content is omitted for an existing page, existing content is
preserved.

Payload shape:

```json
{
  "pages": [
    {
      "title": "Guide canicule",
      "slug": "guides/canicule",
      "status": "DRAFT",
      "type": "MARKETING",
      "contentMarkdown": "## Intro\n\nTexte de la page.",
      "seoTitle": "Guide canicule",
      "seoDescription": "Conseils pour louer une climatisation mobile.",
      "scheduledAt": "2026-06-01T08:00:00.000Z"
    }
  ]
}
```

Response shape:

```json
{
  "results": [
    {
      "action": "created",
      "page": {
        "id": "page_id",
        "slug": "guides/canicule",
        "status": "DRAFT",
        "scheduledAt": "2026-06-01T08:00:00.000Z",
        "previewPath": "/admin/cms/page_id/preview"
      }
    }
  ],
  "summary": {
    "total": 1,
    "created": 1,
    "updated": 0
  }
}
```

### Batch Publish Or Schedule

`PATCH /api/admin/cms/pages/batch`

Updates up to 50 existing pages selected by either `ids` or `slugs`, but not both.

Publish immediately:

```json
{
  "slugs": ["guides/canicule", "guides/location-clim-airbnb"],
  "status": "PUBLISHED"
}
```

Schedule publication:

```json
{
  "ids": ["page_id_1", "page_id_2"],
  "scheduledAt": "2026-06-01T08:00:00.000Z"
}
```

Response shape:

```json
{
  "results": [
    {
      "action": "scheduled",
      "page": {
        "id": "page_id_1",
        "slug": "guides/canicule",
        "status": "DRAFT",
        "scheduledAt": "2026-06-01T08:00:00.000Z"
      }
    }
  ],
  "missing": [],
  "summary": {
    "total": 1,
    "published": 0,
    "scheduled": 1,
    "missing": 0
  }
}
```

### Publish Due Scheduled Pages

`POST /api/cron/mobi-clim/cms-publishing`

Headers:

- `x-mobi-clim-cron-secret: <MOBI_CLIM_CRON_SECRET>`

This endpoint publishes due pages where `status` is `DRAFT` and `scheduledAt` is in the
past. It uses `MOBI_CLIM_CMS_API_USER_ID` as the actor for revisions and audit logs.
It does not use bearer authentication.

Response shape:

```json
{
  "ok": true,
  "published": 2,
  "pages": [
    {
      "id": "page_id",
      "slug": "guides/canicule",
      "publishedAt": "2026-06-01T08:00:00.000Z"
    }
  ]
}
```

### List Media

`GET /api/cms/media?search=salon&take=80`

Returns recent media assets. `take` is clamped between 1 and 120.

Response shape:

```json
{
  "assets": [
    {
      "id": "media_asset_id",
      "url": "/api/media/cms/example.avif",
      "storageKey": "cms/example.avif",
      "fileName": "example.avif",
      "mimeType": "image/avif",
      "sizeBytes": 42000,
      "width": 1600,
      "height": 900,
      "alt": "Salon climatise",
      "caption": "Location Mobi-Clim",
      "source": "r2",
      "uploadedById": "admin_user_id",
      "createdAt": "2026-05-11T10:00:00.000Z",
      "updatedAt": "2026-05-11T10:00:00.000Z"
    }
  ]
}
```

### Upload Media

`POST /api/cms/media`

Content type: `multipart/form-data`

Fields:

- `file`: required image file.
- `alt`: optional alt text.
- `caption`: optional caption.
- `format`: optional. `avif` by default. Use `source` or `original` to preserve the input format.

Supported input types: JPEG, PNG, WebP, GIF, AVIF.

CMS media uploads are converted to AVIF by default. The response `id` can be used as
`ogImageId` in page payloads, and the response `url` can be used in Markdown image
syntax.

Response shape:

```json
{
  "id": "media_asset_id",
  "url": "/api/media/cms/example.avif",
  "alt": "Salon climatise",
  "caption": "Location Mobi-Clim",
  "fileName": "example.avif",
  "mimeType": "image/avif",
  "sizeBytes": 42000,
  "width": 1600,
  "height": 900,
  "storageKey": "cms/example.avif"
}
```

### List Orders

`GET /api/admin/cms/orders`

Query parameters:

- `status`: optional `OrderStatus`, for example `PAID`, `CONFIRMED`, `SCHEDULED`, `CANCELLED`, or `PAYMENT_FAILED`.
- `paymentStatus`: optional `PaymentStatus`, for example `PENDING`, `PAID`, `FAILED`, `CANCELLED`, or `REFUNDED`.
- `search`: optional text search across order number, email, and phone.
- `take`: optional page size, clamped server-side to 1-100.
- `cursor`: optional order id cursor for pagination.

Response shape:

```json
{
  "orders": [
    {
      "id": "order_id",
      "orderNumber": "MC-123",
      "userId": "user_id",
      "email": "client@example.com",
      "phone": "0600000000",
      "status": "PAID",
      "paymentStatus": "PAID",
      "subtotalCents": 7800,
      "depositTotalCents": 22200,
      "deliveryFeeCents": 0,
      "totalCents": 30000,
      "currency": "EUR",
      "startsAt": "2026-06-15T00:00:00.000Z",
      "endsAt": "2026-06-16T00:00:00.000Z",
      "rentalDays": 2,
      "isPreorder": true,
      "internalNote": null,
      "deliveryAddress": {
        "firstName": "Ada",
        "lastName": "Lovelace",
        "postalCode": "75001",
        "city": "Paris"
      },
      "items": [
        {
          "id": "item_id",
          "productId": "product_id",
          "productNameSnapshot": "Climatiseur mobile",
          "unitDailyPriceCents": 3900,
          "quantity": 1,
          "rentalDays": 2,
          "lineRentalTotalCents": 7800,
          "lineDepositTotalCents": 22200
        }
      ],
      "payments": [],
      "vosfacturesInvoices": [],
      "shipments": [],
      "createdAt": "2026-05-20T10:00:00.000Z",
      "updatedAt": "2026-05-20T10:00:00.000Z"
    }
  ],
  "nextCursor": null
}
```

### Get Order

`GET /api/admin/cms/orders/:orderId`

Returns one order using the same shape as list items, including addresses, items,
payments, VosFactures invoices, shipments, labels, and recent tracking events.

### Create Order

`POST /api/admin/cms/orders`

Creates a `PENDING_PAYMENT` order through the server-side checkout/order service. The
server recalculates rental days, pricing, deposit, delivery fee, stock availability,
snapshots, notifications, invoices, and audit logs. Do not send computed totals from
the client.

Payload shape:

```json
{
  "items": [
    {
      "productId": "product_id",
      "quantity": 1
    }
  ],
  "startsAt": "2026-06-15",
  "endsAt": "2026-06-17",
  "customer": {
    "firstName": "Ada",
    "lastName": "Lovelace",
    "email": "ada@example.com",
    "phone": "0600000000",
    "companyName": "Ada Conseil",
    "line1": "10 rue de Paris",
    "line2": null,
    "postalCode": "75001",
    "city": "Paris",
    "country": "FR",
    "deliveryNotes": "Digicode 1234"
  },
  "billingAddress": null,
  "shipping": {
    "method": "home_standard"
  },
  "acceptedTerms": true
}
```

Legacy single-item shape is also accepted with `productId` and `quantity` instead of
`items`.

### Update Order

`PATCH /api/admin/cms/orders/:orderId`

Updates `status` and/or `internalNote`.

Payload fields:

- `status`: optional `OrderStatus`. The transition must be allowed unless `override` is true.
- `internalNote`: optional string or null.
- `reason`: optional reason stored in the audit log.
- `override`: optional boolean for exceptional status corrections.

Example:

```json
{
  "status": "CONFIRMED",
  "reason": "Validation opérateur",
  "internalNote": "Client appelé le matin."
}
```

Status updates go through `applyOrderStatusTransition`, create audit logs, synchronize
availability blocks, and trigger existing confirmation/scheduling side effects where
applicable.

### Cancel Order

`DELETE /api/admin/cms/orders/:orderId?reason=Annulation%20client`

Cancels an order through the audited cancellation workflow. This endpoint does not
physically delete historical order records.

Query parameters:

- `reason`: optional. Defaults to `Annulation via API CMS`.
- `overrideDelivered`: optional `true` or `1`. Allows cancellation after delivered/rental states.

### List Users

`GET /api/admin/cms/users`

Query parameters:

- `role`: optional role filter, for example `admin` or `user`.
- `search`: optional text search across name, email, and phone.
- `take`: optional page size, clamped server-side to 1-100.
- `cursor`: optional user id cursor for pagination.

Response shape:

```json
{
  "users": [
    {
      "id": "user_id",
      "name": "Ada Lovelace",
      "email": "ada@example.com",
      "emailVerified": false,
      "role": "user",
      "banned": false,
      "banReason": null,
      "phone": "0600000000",
      "company": "Ada Conseil",
      "metadata": null,
      "counts": {
        "orders": 1,
        "sessions": 0,
        "accounts": 1
      },
      "createdAt": "2026-05-20T10:00:00.000Z",
      "updatedAt": "2026-05-20T10:00:00.000Z"
    }
  ],
  "nextCursor": null
}
```

### Get User

`GET /api/admin/cms/users/:userId`

Returns one user using the same shape as list items.

### Create User

`POST /api/admin/cms/users`

Payload fields:

- `name`: required.
- `email`: required, unique, normalized to lowercase.
- `password`: optional. When present, creates a credential account with a hashed password.
- `role`: optional, `user` by default. Accepted values: `user`, `admin`.
- `emailVerified`: optional boolean.
- `phone`, `company`, `jobTitle`: optional strings or null.
- `metadata`: optional JSON.

Example:

```json
{
  "name": "Ada Lovelace",
  "email": "ada@example.com",
  "role": "user",
  "emailVerified": false,
  "phone": "0600000000"
}
```

### Update User

`PATCH /api/admin/cms/users/:userId`

Payload may contain any of:

- `name`, `email`, `role`, `emailVerified`, `banned`, `banReason`
- `phone`, `bio`, `company`, `jobTitle`, `department`, `location`
- `websiteUrl`, `linkedinUrl`, `githubUrl`, `xUrl`
- `metadata`

Empty objects are rejected. Email uniqueness is enforced. Updates are audited.

### Delete User

`DELETE /api/admin/cms/users/:userId`

Physically deletes a user only when the user has no attached orders. If orders exist,
the endpoint rejects deletion so historical order records remain valid. Use `PATCH` to
ban or update such users instead.

### List Email Logs

`GET /api/admin/cms/email-logs`

Query parameters:

- `status`: optional. `all`, `sent`, `skipped`, or `error`. Defaults to `all`.
- `source`: optional. `all`, `order`, `manual`, or `contact`. Defaults to `all`.
- `search`: optional text search across log fields.
- `take`: optional page size, clamped server-side to 1-100.
- `cursor`: optional audit log id cursor for pagination.

Response shape:

```json
{
  "emailLogs": [
    {
      "id": "audit_log_id",
      "source": "order",
      "event": "order_created_customer",
      "action": "email.order_created_customer.sent",
      "status": "sent",
      "recipient": "client@example.com",
      "subject": "Commande MC-123 créée",
      "reference": "MC-123",
      "detail": null,
      "entityType": "order",
      "entityId": "order_id",
      "actor": null,
      "after": {
        "to": "client@example.com",
        "subject": "Commande MC-123 créée",
        "result": { "status": "sent" }
      },
      "createdAt": "2026-05-20T10:00:00.000Z"
    }
  ],
  "nextCursor": null
}
```

Order and manual email logs come from `AuditLog` records whose action starts with
`email.`. Contact email logs are derived from contact submission email timestamp/error
columns and use ids like `contact_submission_id:client` or
`contact_submission_id:admin`.

### Get Email Log

`GET /api/admin/cms/email-logs/:logId`

Returns one email log. When the id contains `:`, URL-encode the id path segment.

### Delete Email Log

`DELETE /api/admin/cms/email-logs/:logId`

Deletes an audited email log and writes a deletion audit record. Derived contact logs
cannot be deleted because they are computed from contact submission columns.

## Page Supported Fields

- `title`: required on create, optional on update.
- `slug`: optional. If omitted on create, the server derives it from `title`.
- `status`: `DRAFT` or `PUBLISHED`.
- `type`: `LEGAL`, `MARKETING`, `FAQ`, `LANDING`, or `SYSTEM`.
- `contentMarkdown`: Markdown source. Preferred for programmatic creation.
- `contentJson`: compatible CMS/Tiptap document. Use only when already available.
- `excerpt`: page hero summary.
- `seoTitle`: search title.
- `seoDescription`: search description.
- `canonicalUrl`: canonical URL.
- `robots`: robots directive, for example `index,follow`.
- `ogTitle`: Open Graph title.
- `ogDescription`: Open Graph description.
- `ogImageId`: existing `MediaAsset.id` for the featured/OG image.
- `scheduledAt`: ISO datetime for future publication. Only valid for draft/scheduled pages.

## Server Behavior

- Slugs are normalized server-side and reserved roots are rejected.
- Duplicate slugs return conflict.
- HTML is rendered and sanitized before storage.
- Every save creates a page revision.
- Saves are audited against the authenticated/actor admin user.
- Publishing sets `publishedAt` when needed.
- Switching back to `DRAFT` clears `publishedAt`.
- Scheduling stores `scheduledAt` and keeps or moves the page to `DRAFT`.
- Publishing clears `scheduledAt`.
- Changing the slug of an already published page creates a 301 redirect from the old path.
- Public rendering only exposes pages with `status: "PUBLISHED"`.
- The response includes `editPath`, `previewPath`, and `publicPath` when published.
- Order create/update/cancel endpoints use the existing order workflow helpers so pricing, deposits, availability, notifications, and audit logs stay server-authoritative.
- User deletion is rejected when attached orders exist.
- Email logs are partly derived data: audited logs can be deleted, contact-derived logs cannot.

## Markdown Blocks

GitHub-flavored Markdown is supported.

Custom callout:

```markdown
:::info Bon a savoir
Texte en **Markdown**.
:::
```

Variants: `info`, `success`, `warning`, `tip`.

FAQ:

```markdown
:::faq Combien coute une location ?
Le prix depend de la duree.
:::
```

Gallery:

```markdown
:::gallery
![Salon](/uploads/salon.webp)
![Bureau](/uploads/bureau.webp "Bureau climatise")
:::
```

CTA button:

```markdown
[button:Reserver maintenant](/reservation)
```

## Error Statuses

- `400`: invalid JSON, invalid payload, reserved slug, or other validation issue.
- `401`: missing/invalid admin session or bearer token.
- `404`: single-resource target page, order, user, or email log not found.
- `409`: duplicate slug.
- `500`: bearer auth configured without a valid admin actor, or media storage unavailable.
