# Mobi-Clim CMS API Reference

## Authentication

Routes accept either:

- an authenticated Better Auth admin session cookie; or
- `Authorization: Bearer <MOBI_CLIM_CMS_API_TOKEN>`.

For bearer auth, the deployed app must also set `MOBI_CLIM_CMS_API_USER_ID` to an
existing admin user id. That user is used for page revisions and audit logs.

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
- `500`: bearer auth configured without a valid admin actor.
