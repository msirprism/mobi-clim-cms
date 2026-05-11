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

## Supported Fields

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
- `404`: single-page get/update target page not found.
- `409`: duplicate slug.
- `500`: bearer auth configured without a valid admin actor, or media storage unavailable.
