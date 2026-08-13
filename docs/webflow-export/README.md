# Webflow Export - DryRun Security Documentation

This directory contains DryRun Security documentation content formatted for
import into Webflow.

## Files

- **pages.csv** - All documentation pages in CSV format for Webflow CMS import
- **pages/*.html** - Individual HTML content files for use as Webflow Code Embeds
- **README.md** - This file

## Using the CSV for CMS Import

1. In Webflow, go to **CMS** > **Import/Export** (or use the API).
2. Upload `pages.csv`.
3. Map the columns to your CMS Collection fields:
   - `Name` -> Page title (plain text field)
   - `Slug` -> URL slug (slug field)
   - `Content` -> Page body (Rich Text or plain HTML field for Code Embed)
   - `Meta Description` -> SEO description (plain text field)
   - `Category` -> Section grouping (option/reference field)
4. Content is clean HTML suitable for Webflow Rich Text fields. If your Rich
   Text field strips custom classes, use a Code Embed element instead.

## Using Individual HTML Files as Code Embeds

Each file in `pages/` contains only the page body content wrapped in a single
`<div class="drs-doc-content">` element. To use in Webflow:

1. Add a **Code Embed** element to your page template.
2. Paste the contents of the corresponding `.html` file.
3. The HTML uses semantic tags (`h2`, `h3`, `h4`, `p`, `ul`, `ol`, `li`,
   `table`, `thead`, `tbody`, `tr`, `th`, `td`, `pre`, `code`, `strong`, `em`,
   `a`) that Webflow styles natively.
4. Custom layout classes use the `drs-` prefix to avoid conflicts with
   Webflow's own class namespace.

## CSS Classes

All custom CSS classes use the `drs-` prefix. Add these styles to your
Webflow project's custom CSS (Site Settings > Custom Code > Head):

| Class | Purpose |
|-------|---------|
| `drs-cols-3` | Cols 3 container/element |
| `drs-landing-card` | Landing Card container/element |
| `drs-landing-card-desc` | Landing Card Desc container/element |
| `drs-landing-card-title` | Landing Card Title container/element |
| `drs-landing-grid` | Landing Grid container/element |
| `drs-landing-section` | Landing Section container/element |
| `drs-landing-section-header` | Landing Section Header container/element |
| `drs-persona` | Persona container/element |

Copy the relevant styles from the original `style.css` file, renaming each
class to its `drs-` prefixed version. Semantic HTML elements (`h2`, `p`,
`table`, etc.) inherit Webflow's typography styles by default.

## Images and Assets

Images referenced in the content use relative paths. Before importing:

1. Upload all images from the `assets/` directory to Webflow's Asset Manager.
2. Update image `src` attributes in the HTML to point to Webflow-hosted URLs,
   or use Webflow's built-in image elements and reference CMS image fields.
3. SVG logos are inlined in the original site's header/footer and are **not**
   included in these content files. Use Webflow's native header/footer
   components instead.

## Notes

- Content HTML has been cleaned: no inline styles, no `<script>` tags, and
  no site wrapper elements (header, footer, sidebar, navigation).
- Internal links between pages use relative paths (e.g., `deepscan.html`).
  Update these to match your Webflow URL structure if slugs differ.
- Tables use standard HTML table markup (`<table>`, `<thead>`, `<tbody>`,
  `<tr>`, `<th>`, `<td>`) compatible with Webflow's table styling.
