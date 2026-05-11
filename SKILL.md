---
name: mobi-clim-cms
description: Manage the Mobi-Clim CMS page and media control API. Use when Codex needs to list, get, create, batch upsert, update, publish, schedule, unpublish, upload media, or document CMS content programmatically through the Mobi-Clim routes GET/POST /api/admin/cms/pages, GET/PATCH /api/admin/cms/pages/:pageId, POST/PATCH /api/admin/cms/pages/batch, POST /api/cron/mobi-clim/cms-publishing, and POST /api/cms/media, including Markdown content, SEO fields, Open Graph fields, media assets, slugs, statuses, scheduledAt, and page types.
---

# Mobi-Clim CMS

Use Mobi-Clim CMS to operate Mobi-Clim CMS pages and media through the programmatic API instead of the admin UI.

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
   - Upload media: `POST /api/cms/media`
   - Publish due scheduled pages: `POST /api/cron/mobi-clim/cms-publishing`
5. Verify the response includes `page.id`, `page.slug`, `page.status`, `editPath`, `previewPath`, and, for published pages, `publicPath`.
   - For list responses, verify `pages[]` and `nextCursor`.
   - For batch responses, verify `results[]`, `summary`, and any `missing` selectors.
   - For media uploads, verify `id`, `url`, `mimeType`, `sizeBytes`, `width`, and `height`.

## Payload Fields

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
```

The script reads:

- `--base-url` or `MOBI_CLIM_CMS_API_BASE_URL`
- `--token` or `MOBI_CLIM_CMS_API_TOKEN`

Use `-` as the payload path to read JSON from stdin.

## References

Read `references/mobi-clim-cms-api.md` when exact routes, response shapes, error handling, or Markdown block syntax are needed.
