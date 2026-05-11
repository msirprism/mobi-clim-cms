# Mobi-Clim CMS API Reference

## Authentication

Routes accept either:

- an authenticated Better Auth admin session cookie; or
- `Authorization: Bearer <generated-cms-api-key>` or `Authorization: Bearer <MOBI_CLIM_CMS_API_TOKEN>`.

For the legacy env bearer token, the deployed app must also set
`MOBI_CLIM_CMS_API_USER_ID` to an existing admin user id. Generated CMS API keys use
the admin user that created the key for revisions and audit logs.

## Endpoints

### Create Page

`POST /api/admin/cms/pages`

Minimum payload:

```json
{
  "title": "Page title"
}
```

Response status: `201`

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

## Server Behavior

- Slugs are normalized server-side and reserved roots are rejected.
- Duplicate slugs return conflict.
- HTML is rendered and sanitized before storage.
- Every save creates a page revision.
- Saves are audited against the authenticated/actor admin user.
- Publishing sets `publishedAt` when needed.
- Switching back to `DRAFT` clears `publishedAt`.
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
- `404`: update target page not found.
- `409`: duplicate slug.
- `500`: bearer auth configured without a valid admin actor, or media storage unavailable.
