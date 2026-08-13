"""
Unit tests for DryRun Security Documentation build system.
Run with: python3 -m pytest tests/test_build.py -v
"""
import re
import importlib.util
from pathlib import Path

# Load build.py as a module
BUILD_PATH = Path(__file__).parent.parent / "build.py"
spec = importlib.util.spec_from_file_location("build", BUILD_PATH)
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
CSS_PATH = DOCS_DIR / "style.css"
INDEX_PATH = DOCS_DIR / "index.html"


def _doc_html_files():
    """All generated documentation pages in the GitHub Pages source directory."""
    redirect_names = {f"{old}.html" for old, _ in getattr(build, "REDIRECTS", [])}
    return [p for p in DOCS_DIR.glob("*.html") if p.name not in redirect_names]


def _is_redirect_html(path):
    """Return True if `path` is a generated renamed-slug or legacy URL stub."""
    redirect_names = {f"{old}.html" for old, _ in getattr(build, "REDIRECTS", [])}
    return path.parent != DOCS_DIR or (
        path.name in redirect_names and path.parent == DOCS_DIR
    )


def _page_path(slug):
    """Path to a generated page in docs/. documentation -> index.html."""
    if slug == "documentation":
        return DOCS_DIR / "index.html"
    return DOCS_DIR / f"{slug}.html"


class TestDataIntegrity:
    """Verify all page data is complete and consistent."""

    def test_pages_not_empty(self):
        assert len(build.PAGES) >= 18, f"Should have at least 18 pages, got {len(build.PAGES)}"

    def test_sections_not_empty(self):
        assert len(build.SECTIONS) >= 4, f"Should have at least 4 sections, got {len(build.SECTIONS)}"

    def test_all_pages_have_required_fields(self):
        required = {"title", "description", "section", "content"}
        for slug, page in build.PAGES.items():
            missing = required - set(page.keys())
            assert not missing, f"Page '{slug}' missing fields: {missing}"

    def test_all_pages_have_nonempty_content(self):
        for slug, page in build.PAGES.items():
            assert len(page["content"].strip()) > 100, (
                f"Page '{slug}' has suspiciously short content ({len(page['content'])} chars)"
            )

    def test_all_section_slugs_exist_in_pages(self):
        for section in build.SECTIONS:
            for slug in section["pages"]:
                assert slug in build.PAGES, (
                    f"Section '{section['name']}' references slug '{slug}' not in PAGES"
                )

    def test_all_pages_belong_to_a_section(self):
        all_section_slugs = set()
        for section in build.SECTIONS:
            all_section_slugs.update(section["pages"])
        for slug in build.PAGES:
            assert slug in all_section_slugs, (
                f"Page '{slug}' is in PAGES but not in any SECTION"
            )

    def test_no_duplicate_slugs_in_sections(self):
        all_slugs = []
        for section in build.SECTIONS:
            for slug in section["pages"]:
                assert slug not in all_slugs, (
                    f"Duplicate slug '{slug}' found in section '{section['name']}'"
                )
                all_slugs.append(slug)

    def test_page_slugs_are_url_safe(self):
        for slug in build.PAGES:
            assert re.match(r'^[a-z0-9\-]+$', slug), (
                f"Slug '{slug}' is not URL-safe (use lowercase letters, numbers, hyphens)"
            )


class TestEscaping:
    """Verify HTML escaping is properly applied."""

    def test_esc_function_exists(self):
        assert hasattr(build, 'esc'), "build.py must define esc() function"

    def test_esc_escapes_html_chars(self):
        assert build.esc('<script>') == '&lt;script&gt;'
        assert build.esc('"hello"') == '&quot;hello&quot;'
        assert build.esc("it's") == "it&#x27;s"
        assert build.esc('a & b') == 'a &amp; b'

    def test_esc_handles_non_strings(self):
        assert build.esc(42) == '42'
        assert build.esc(None) == 'None'


class TestGeneratedFiles:
    """Verify generated HTML files have correct structure."""

    def test_index_exists(self):
        assert INDEX_PATH.exists()

    def test_all_doc_pages_exist(self):
        for slug in build.PAGES:
            page = _page_path(slug)
            assert page.exists(), f"Missing doc page: {page}"

    def test_sitemap_exists(self):
        assert (DOCS_DIR / "sitemap.xml").exists()

    def test_robots_txt_exists(self):
        assert (DOCS_DIR / "robots.txt").exists()

    def test_nojekyll_is_preserved_and_no_cname_is_created(self):
        assert (DOCS_DIR / ".nojekyll").exists()
        assert not (DOCS_DIR / "CNAME").exists()

    def test_doc_pages_have_doctype(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert content.strip().startswith("<!DOCTYPE html"), (
                f"{html_file.name} missing DOCTYPE"
            )

    def test_doc_pages_have_favicon(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert 'favicon.ico' in content, (
                f"{html_file.name} missing favicon reference"
            )

    def test_doc_pages_have_header(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert 'site-header' in content, (
                f"{html_file.name} missing header"
            )

    def test_doc_pages_have_footer(self):
        pass  # Footer has been intentionally removed from the docs site

    def test_doc_pages_have_sidebar(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert 'sidebar' in content, (
                f"{html_file.name} missing sidebar"
            )

    def test_doc_pages_have_toc(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert 'toc-sidebar' in content, (
                f"{html_file.name} missing TOC sidebar"
            )

    def test_index_has_sidebar_nav(self):
        content = INDEX_PATH.read_text()
        assert 'sidebar-nav' in content, "index.html missing sidebar navigation"

    def test_index_has_search_input(self):
        content = INDEX_PATH.read_text()
        assert 'search' in content.lower(), "index.html missing search"

    def test_index_has_search_index(self):
        content = INDEX_PATH.read_text()
        assert '__SEARCH_INDEX__' in content, "index.html missing search index"

    def test_search_index_contains_all_pages(self):
        import json
        content = INDEX_PATH.read_text()
        start = content.index('__SEARCH_INDEX__=') + len('__SEARCH_INDEX__=')
        end = content.index(';</script>', start)
        index = json.loads(content[start:end])
        # Page-level entries (no anchor) must cover every page
        page_entries = [e for e in index if 'a' not in e]
        assert len(page_entries) == len(build.PAGES), (
            f"Search index has {len(page_entries)} page-level entries but PAGES has {len(build.PAGES)}"
        )
        slugs = {entry['s'] for entry in page_entries}
        for slug in build.PAGES:
            assert slug in slugs, f"Page '{slug}' missing from search index"

    def test_search_index_has_section_entries_with_anchors(self):
        import json
        content = INDEX_PATH.read_text()
        start = content.index('__SEARCH_INDEX__=') + len('__SEARCH_INDEX__=')
        end = content.index(';</script>', start)
        index = json.loads(content[start:end])
        section_entries = [e for e in index if 'a' in e]
        assert len(section_entries) > 0, (
            "Search index should contain section-level entries with anchor IDs"
        )
        for entry in section_entries:
            assert entry['a'], f"Section entry for '{entry['s']}' has empty anchor"
            assert entry['s'] in build.PAGES, (
                f"Section entry anchor '{entry['a']}' references unknown slug '{entry['s']}'"
            )

    def test_search_index_entries_have_body_text(self):
        import json
        content = INDEX_PATH.read_text()
        start = content.index('__SEARCH_INDEX__=') + len('__SEARCH_INDEX__=')
        end = content.index(';</script>', start)
        index = json.loads(content[start:end])
        for entry in index:
            assert len(entry['b']) > 50, (
                f"Page '{entry['s']}' has insufficient body text in search index"
            )


class TestRelativePaths:
    """Verify no hardcoded domains in internal links."""

    def test_no_hardcoded_github_pages_url_in_html(self):
        for html_file in DOCS_DIR.glob("**/*.html"):
            content = html_file.read_text()
            assert 'wickett.github.io' not in content, (
                f"{html_file} contains hardcoded GitHub Pages URL"
            )

    def test_doc_pages_use_relative_css(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert './style.css' in content, (
                f"{html_file.name} should reference ./style.css"
            )

    def test_doc_pages_have_inline_logo_svg(self):
        for html_file in _doc_html_files():
            content = html_file.read_text()
            assert 'class="logo logo-light-mode" viewBox="0 0 450 119"' in content, (
                f"{html_file.name} should contain inline logo SVG"
            )

    def test_root_page_uses_relative_css(self):
        content = INDEX_PATH.read_text()
        assert 'style.css' in content, "index.html should reference style.css"

    def test_external_links_have_target_blank(self):
        for html_file in DOCS_DIR.glob("**/*.html"):
            if _is_redirect_html(html_file):
                continue
            content = html_file.read_text()
            for match in re.finditer(r'<a\s+([^>]*href="https?://[^"]*"[^>]*)>', content):
                attrs = match.group(1)
                if 'dryrun.security' in attrs or 'g2.com' in attrs or 'linkedin.com' in attrs:
                    assert 'target="_blank"' in attrs, (
                        f"{html_file.name}: external link missing target=_blank: {attrs[:80]}"
                    )


class TestAccessibility:
    """Enforce accessibility standards."""

    @staticmethod
    def _parse_css():
        return CSS_PATH.read_text()

    def test_base_font_size_at_least_16px(self):
        css = self._parse_css()
        match = re.search(r'html\s*\{[^}]*font-size:\s*(\d+)px', css)
        assert match, "Could not find html base font-size"
        base_px = int(match.group(1))
        assert base_px >= 16, f"Base font-size is {base_px}px, must be >= 16px"

    def test_muted_text_contrast(self):
        css = self._parse_css()
        match = re.search(r'--text-muted:\s*(#[0-9a-fA-F]{6})', css)
        assert match, "Could not find --text-muted CSS variable"
        hex_color = match.group(1).lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        avg = (r + g + b) / 3
        assert avg >= 140, (
            f"--text-muted color {match.group(1)} is too dark for accessibility. "
            f"Average channel brightness is {avg:.0f}, need >= 140."
        )

    def test_focus_visible_styles_exist(self):
        css = self._parse_css()
        assert 'focus-visible' in css, (
            "CSS must include :focus-visible styles for keyboard accessibility"
        )

    def test_all_images_have_alt_text(self):
        for html_file in DOCS_DIR.glob("**/*.html"):
            content = html_file.read_text()
            for match in re.finditer(r'<img\s+([^>]*)>', content):
                attrs = match.group(1)
                assert 'alt=' in attrs, (
                    f"{html_file.name}: <img> missing alt attribute: {attrs[:60]}"
                )

    def test_html_has_lang_attribute(self):
        content = INDEX_PATH.read_text()
        assert '<html lang=' in content.lower(), (
            "index.html missing lang attribute on <html> element"
        )

    def test_no_font_size_below_minimum(self):
        """No font-size in desktop CSS should be below 0.72rem (11.5px at 16px base).
        Mobile breakpoint is exempt."""
        css = self._parse_css()
        mobile_start = css.find('@media')
        desktop_css = css[:mobile_start] if mobile_start != -1 else css
        min_rem = 0.72
        violations = []
        for match in re.finditer(r'font-size:\s*([\d.]+)rem', desktop_css):
            val = float(match.group(1))
            if val < min_rem:
                start = max(0, match.start() - 80)
                context = desktop_css[start:match.start()].strip().split('\n')[-1]
                violations.append(f"{val}rem (near: ...{context})")
        assert not violations, (
            f"Font sizes below {min_rem}rem found in desktop CSS:\n" +
            "\n".join(f"  - {v}" for v in violations)
        )


class TestResponsiveCSS:
    """Regression guards for responsive layout issues."""

    @staticmethod
    def _parse_css():
        return CSS_PATH.read_text()

    def test_sidebar_search_styles_exist(self):
        """CSS must define sidebar search styles."""
        css = self._parse_css()
        assert '.sidebar-search' in css, (
            "CSS must include .sidebar-search styles"
        )
        assert '.sidebar-search input' in css, (
            "CSS must include .sidebar-search input styles"
        )

    def test_mobile_breakpoint_exists(self):
        """CSS must define mobile responsive rules."""
        css = self._parse_css()
        assert '@media (max-width: 600px)' in css, (
            "Missing mobile breakpoint at 600px"
        )
        assert '@media (max-width: 900px)' in css, (
            "Missing tablet breakpoint at 900px"
        )

    def test_sidebar_toggle_hidden_by_default(self):
        """Hamburger menu must be hidden at desktop widths."""
        css = self._parse_css()
        toggle_idx = css.index('.sidebar-toggle')
        toggle_block = css[toggle_idx:css.index('}', toggle_idx) + 1]
        assert 'display: none' in toggle_block or 'display:none' in toggle_block, (
            "Sidebar toggle (hamburger) must be display:none by default"
        )

    def test_header_nav_visible_by_default(self):
        pass  # Header nav links have been intentionally removed from the docs site


class TestSidebarNavigation:
    """Verify sidebar navigation is consistent across pages."""

    def test_every_page_has_active_link_in_sidebar(self):
        nav_hidden = set()
        for section in build.SECTIONS:
            nav_hidden.update(section.get('nav_hidden', []))
        for slug in build.PAGES:
            if slug in nav_hidden:
                continue  # hidden pages don't have an active sidebar link
            page_file = _page_path(slug)
            content = page_file.read_text()
            assert 'class="active"' in content, (
                f"{slug}.html has no active sidebar link"
            )

    def test_prev_next_links_form_chain(self):
        """First page should have no prev, last page should have no next."""
        all_slugs = []
        for section in build.SECTIONS:
            all_slugs.extend(section["pages"])

        first_page = _page_path(all_slugs[0])
        first_content = first_page.read_text()
        assert 'class="prev-next-link prev-link"' not in first_content, (
            f"First page '{all_slugs[0]}' should not have a previous link"
        )

        last_page = _page_path(all_slugs[-1])
        last_content = last_page.read_text()
        assert 'class="prev-next-link next-link"' not in last_content, (
            f"Last page '{all_slugs[-1]}' should not have a next link"
        )


class TestUIQualityCSS:
    """CSS guards for UI quality - prevent regressions in typography, contrast, spacing."""

    def test_body_text_uses_readable_color_token(self):
        """Body text (--text-body) should be distinct from --text-muted."""
        css = CSS_PATH.read_text()
        assert '--text-body:' in css, "CSS must define --text-body token for readable body text"
        assert '--text-muted:' in css, "CSS must define --text-muted token"
        # Extract hex values
        import re
        body_match = re.search(r'--text-body:\s*(#[0-9a-fA-F]+)', css)
        muted_match = re.search(r'--text-muted:\s*(#[0-9a-fA-F]+)', css)
        assert body_match and muted_match
        assert body_match.group(1) != muted_match.group(1), (
            "--text-body and --text-muted must be different colors"
        )

    def test_page_heading_size_is_authoritative(self):
        """Page heading should be at least 2rem."""
        css = CSS_PATH.read_text()
        import re
        match = re.search(r'\.page-heading\s*\{[^}]*font-size:\s*([\d.]+)rem', css)
        assert match, ".page-heading must have a font-size in rem"
        size = float(match.group(1))
        assert size >= 2.0, f".page-heading font-size should be >= 2rem, got {size}rem"

    def test_h2_size_hierarchy(self):
        """h2 should be at least 1.4rem."""
        css = CSS_PATH.read_text()
        import re
        match = re.search(r'\.doc-content h2\s*\{[^}]*font-size:\s*([\d.]+)rem', css)
        assert match, ".doc-content h2 must have a font-size in rem"
        size = float(match.group(1))
        assert size >= 1.4, f"h2 font-size should be >= 1.4rem, got {size}rem"

    def test_content_area_has_generous_padding(self):
        """Content area should have at least 40px horizontal padding."""
        css = CSS_PATH.read_text()
        import re
        match = re.search(r'\.content-area\s*\{[^}]*padding:\s*([^;]+)', css)
        assert match, ".content-area must have padding defined"
        # padding shorthand: top right bottom left or top horizontal bottom
        padding_val = match.group(1).strip()
        parts = padding_val.replace('px', '').split()
        if len(parts) >= 2:
            horizontal = float(parts[1])
        else:
            horizontal = float(parts[0])
        assert horizontal >= 40, f"Content horizontal padding should be >= 40px, got {horizontal}px"

    def test_copy_button_is_styled(self):
        """Copy button should have proper CSS styling."""
        css = CSS_PATH.read_text()
        assert '.copy-btn' in css, "CSS must style .copy-btn"
        assert 'position: absolute' in css or 'position:absolute' in css, (
            "Copy button should be absolutely positioned"
        )

    def test_sidebar_link_padding_is_adequate(self):
        """Sidebar links should have at least 6px vertical padding for tap targets."""
        css = CSS_PATH.read_text()
        import re
        match = re.search(r'\.sidebar-links a\s*\{[^}]*padding:\s*([^;]+)', css)
        assert match, ".sidebar-links a must have padding"
        padding_val = match.group(1).strip()
        parts = padding_val.replace('px', '').split()
        top_padding = float(parts[0])
        assert top_padding >= 6, f"Sidebar link vertical padding should be >= 6px, got {top_padding}px"

    def test_table_has_border_styling(self):
        """Tables should have border for visual definition."""
        css = CSS_PATH.read_text()
        import re
        match = re.search(r'\.doc-content table\s*\{[^}]*border:', css)
        assert match, ".doc-content table should have border styling"

    def test_no_em_dashes_in_css(self):
        """CSS should not contain em dashes."""
        css = CSS_PATH.read_text()
        assert '\u2014' not in css, "CSS should not contain em dashes"

    def test_keyboard_shortcut_hint_exists(self):
        """Index page should have keyboard shortcut hint on search."""
        index = INDEX_PATH.read_text()
        assert 'sidebar-search-kbd' in index, "Index should have keyboard shortcut hint on search"


class TestHeadingAnchors:
    """Verify h2/h3 headings on every generated page have linkable anchor IDs."""

    HEADING_RE = re.compile(
        r'<(h[23])\b([^>]*)>(.*?)</\1>',
        re.IGNORECASE | re.DOTALL,
    )
    ID_RE = re.compile(r'\bid\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    ANCHOR_LINK_RE = re.compile(
        r'<a\b[^>]*class=["\'][^"\']*\banchor-link\b[^"\']*["\'][^>]*href=["\']#([^"\']+)["\']',
        re.IGNORECASE,
    )

    def _doc_content_headings(self, html_text):
        """Yield h2/h3 matches found inside the main .doc-content container."""
        m = re.search(
            r'<div class="doc-content">(.*?)</div>\s*<(?:nav|/main|footer)',
            html_text,
            re.DOTALL,
        )
        scope = m.group(1) if m else html_text
        for match in self.HEADING_RE.finditer(scope):
            yield match

    def test_headings_have_anchor_ids(self):
        """Every h2/h3 in the doc content must have an id attribute."""
        for path in _doc_html_files():
            html_text = path.read_text()
            headings = list(self._doc_content_headings(html_text))
            if not headings:
                continue
            for match in headings:
                tag = match.group(1)
                attrs = match.group(2)
                id_match = self.ID_RE.search(attrs)
                assert id_match, (
                    f"{path.name}: <{tag}> missing id attribute: {match.group(0)[:120]}"
                )
                slug = id_match.group(1)
                assert re.fullmatch(r'[a-z0-9-]+', slug), (
                    f"{path.name}: heading id {slug!r} is not a valid slug"
                )

    def test_anchor_links_are_linkable(self):
        """Every heading must contain an anchor link pointing to its own id."""
        for path in _doc_html_files():
            html_text = path.read_text()
            headings = list(self._doc_content_headings(html_text))
            if not headings:
                continue
            for match in headings:
                tag = match.group(1)
                attrs = match.group(2)
                inner = match.group(3)
                id_match = self.ID_RE.search(attrs)
                assert id_match, f"{path.name}: <{tag}> missing id"
                heading_id = id_match.group(1)
                link_match = self.ANCHOR_LINK_RE.search(inner)
                assert link_match, (
                    f"{path.name}: <{tag} id={heading_id!r}> missing anchor-link "
                    f"child: {match.group(0)[:160]}"
                )
                assert link_match.group(1) == heading_id, (
                    f"{path.name}: anchor-link href #{link_match.group(1)} "
                    f"does not match heading id #{heading_id}"
                )

    def test_duplicate_heading_text_gets_unique_ids(self):
        """Duplicate heading text on the same page should produce unique slugs."""
        sample = (
            "<h2>Setup</h2>"
            "<p>first</p>"
            "<h3>Setup</h3>"
            "<p>second</p>"
            "<h2>Setup</h2>"
        )
        out = build.add_heading_anchors(sample)
        ids = self.ID_RE.findall(out)
        assert ids == ["setup", "setup-2", "setup-3"], (
            f"Expected unique sequential ids, got {ids!r}"
        )

    def test_anchor_link_css_present(self):
        """style.css should style .anchor-link with a hover-reveal pattern."""
        css = CSS_PATH.read_text()
        assert ".anchor-link" in css, "style.css missing .anchor-link rule"
        assert re.search(r'h2:hover\s+\.anchor-link', css), (
            "style.css should reveal .anchor-link on h2 hover"
        )
        assert re.search(r'h3:hover\s+\.anchor-link', css), (
            "style.css should reveal .anchor-link on h3 hover"
        )


class TestSearchIndex:
    """Verify generate_search_index() output matches the flat URL structure.

    Entries must use /{slug} URLs (or / for the documentation landing page),
    never the legacy /docs/{slug}.html pattern.
    """

    @staticmethod
    def _load_index():
        import json
        return json.loads(build.generate_search_index())

    def test_search_index_has_all_pages(self):
        index = self._load_index()
        page_entries = [e for e in index if 'a' not in e]
        page_slugs = {e['s'] for e in page_entries}
        for slug in build.ORDERED_PAGES:
            assert slug in page_slugs, (
                f"Search index missing page-level entry for slug '{slug}'"
            )

    def test_search_index_documentation_url(self):
        index = self._load_index()
        doc_entries = [e for e in index if e['s'] == 'documentation']
        assert doc_entries, "No search index entries for 'documentation' slug"
        for entry in doc_entries:
            assert entry['url'] == '/', (
                f"'documentation' entry url should be '/', got {entry['url']!r}"
            )

    def test_search_index_slug_urls(self):
        index = self._load_index()
        for entry in index:
            slug = entry['s']
            if slug == 'documentation':
                continue
            expected = f'/{slug}'
            assert entry['url'] == expected, (
                f"Entry for slug '{slug}' has url {entry['url']!r}, expected {expected!r}"
            )

    def test_search_index_no_old_url_patterns(self):
        index = self._load_index()
        for entry in index:
            url = entry['url']
            assert '/docs/' not in url, (
                f"Entry for slug '{entry['s']}' uses legacy /docs/ prefix: {url!r}"
            )
            assert not url.endswith('.html'), (
                f"Entry for slug '{entry['s']}' still uses .html extension: {url!r}"
            )

    def test_search_index_required_fields(self):
        index = self._load_index()
        required = {'s', 't', 'n', 'd', 'b', 'url'}
        for entry in index:
            missing = required - set(entry.keys())
            assert not missing, (
                f"Entry for slug '{entry.get('s')}' missing fields: {missing}"
            )

    def test_search_index_titles_not_empty(self):
        index = self._load_index()
        for entry in index:
            assert entry['t'] and entry['t'].strip(), (
                f"Entry for slug '{entry['s']}' has empty title"
            )

    def test_search_index_content_not_empty(self):
        index = self._load_index()
        for entry in index:
            assert entry['b'] and entry['b'].strip(), (
                f"Entry for slug '{entry['s']}' has empty body/content ('b')"
            )


class TestRedirectDefinitions:
    """Verify known renamed slug mappings remain documented in the generator."""

    def test_redirects_defined(self):
        assert hasattr(build, "REDIRECTS"), "build.py must expose a REDIRECTS list"
        assert isinstance(build.REDIRECTS, list)
        assert len(build.REDIRECTS) >= 1

    def test_coverage_matrix_redirect_present(self):
        assert ("coverage-matrix-vulnerability-categories",
                "vulnerability-coverage-matrix") in build.REDIRECTS

class TestGitHubPagesOutput:
    """Verify docs/ contains the real site served by GitHub Pages."""

    def test_flat_page_files_are_real_documentation(self):
        for slug in build.ORDERED_PAGES:
            path = _page_path(slug)
            content = path.read_text()
            assert "This page has moved." not in content, (
                f"{path.relative_to(ROOT)} is a redirect stub instead of documentation"
            )
            assert "site-header" in content, (
                f"{path.relative_to(ROOT)} is missing rendered documentation content"
            )

    def test_deployment_assets_are_copied(self):
        assert (DOCS_DIR / "style.css").exists()
        assert (DOCS_DIR / "app.js").exists()
        assert (DOCS_DIR / "assets" / "favicon.ico").exists()
