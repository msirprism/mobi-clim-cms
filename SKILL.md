---
name: mobi-clim-cms
description: Manage the Mobi-Clim CMS page control API. Use when Codex needs to create, update, publish, unpublish, or document CMS pages programmatically through the Mobi-Clim routes POST /api/admin/cms/pages and PATCH /api/admin/cms/pages/:pageId, including Markdown content, SEO fields, Open Graph fields, slugs, statuses, and page types.
---

# Mobi-Clim CMS

Use Mobi-Clim CMS to operate Mobi-Clim CMS pages through the programmatic API instead of the admin UI.

## Workflow

1. Identify the target app URL and environment.
   - Prefer explicit user-provided URL.
   - Otherwise use `MOBI_CLIM_CMS_API_BASE_URL`, `NEXT_PUBLIC_APP_URL`, `APP_URL`, or `BETTER_AUTH_URL`.
   - Do not target production unless the user explicitly asks.
2. Authenticate.
   - Use an admin session only when already available in the request context.
   - For external/API work, use bearer auth with `MOBI_CLIM_CMS_API_TOKEN`.
   - Ensure the app has `MOBI_CLIM_CMS_API_USER_ID` set to an existing admin user id.
3. Build a JSON payload with the CMS fields.
4. Send the request.
   - Create: `POST /api/admin/cms/pages`
   - Update/publish/unpublish: `PATCH /api/admin/cms/pages/:pageId`
5. Verify the response includes `page.id`, `page.slug`, `page.status`, `editPath`, `previewPath`, and, for published pages, `publicPath`.

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

Use `contentMarkdown` by default. It supports the same Markdown and custom CMS blocks as the admin editor. Use `contentJson` only when the caller already has a compatible CMS/Tiptap document.

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

## CLI Helper

Use `scripts/mobi_clim_cms.py` for repeatable calls:

```bash
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py create payload.json
python3 /Users/msirprism/.codex/skills/mobi-clim-cms/scripts/mobi_clim_cms.py update <pageId> payload.json
```

The script reads:

- `--base-url` or `MOBI_CLIM_CMS_API_BASE_URL`
- `--token` or `MOBI_CLIM_CMS_API_TOKEN`

Use `-` as the payload path to read JSON from stdin.

## References

Read `references/mobi-clim-cms-api.md` when exact routes, response shapes, error handling, or Markdown block syntax are needed.
