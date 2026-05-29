// @ts-check
const { test, expect } = require('@playwright/test');

// ============================================================
// Landing Page  -  Structure
// ============================================================
test.describe('Landing Page  -  Structure', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
  });

  test('page loads with correct title', async ({ page }) => {
    await expect(page).toHaveTitle(/DryRun Security/);
  });

  test('header renders with logo, nav links, and CTA buttons', async ({ page, isMobile }) => {
    await expect(page.locator('.site-header')).toBeVisible();
    await expect(page.locator('.logo')).toBeVisible();
    if (!isMobile) {
      await expect(page.locator('.header-nav')).toBeVisible();
      const navLinks = page.locator('.header-nav a');
      expect(await navLinks.count()).toBeGreaterThanOrEqual(3);
    }
    await expect(page.locator('.btn-demo')).toBeVisible();
  });

  test('page heading and description are visible', async ({ page }) => {
    await expect(page.locator('.page-heading')).toBeVisible();
    await expect(page.locator('.page-description')).toBeVisible();
  });

  test('sidebar nav is present with sections', async ({ page, isMobile }) => {
    if (isMobile) return;
    await expect(page.locator('.sidebar')).toBeVisible();
    const sections = page.locator('.sidebar-section-title');
    expect(await sections.count()).toBeGreaterThanOrEqual(5);
  });

  test('sidebar search input is present', async ({ page, isMobile }) => {
    if (isMobile) return;
    await expect(page.locator('.sidebar-search input')).toBeVisible();
  });

  test('doc content area has substantial text', async ({ page }) => {
    const content = page.locator('.doc-content');
    await expect(content).toBeVisible();
    const text = await content.textContent();
    expect(text.length).toBeGreaterThan(200);
  });

  test('footer renders with logo and link sections', async ({ page }) => {
    const footer = page.locator('.site-footer');
    await footer.scrollIntoViewIfNeeded();
    await expect(footer).toBeVisible();
    await expect(footer.locator('.footer-logo-img')).toBeVisible();
  });
});

// ============================================================
// Landing Page  -  Responsive Layout
// ============================================================
test.describe('Landing Page  -  Responsive Layout', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
  });

  test('no horizontal overflow at any viewport', async ({ page }) => {
    const hasOverflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    expect(hasOverflow).toBe(false);
  });

  test('desktop: sidebar and content render side by side', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    const layout = await page.evaluate(() => {
      const sidebar = document.querySelector('.sidebar');
      const content = document.querySelector('.content-area');
      if (!sidebar || !content) return null;
      const sr = sidebar.getBoundingClientRect();
      const cr = content.getBoundingClientRect();
      return { sidebarRight: Math.round(sr.right), contentLeft: Math.round(cr.left) };
    });
    expect(layout).not.toBeNull();
    // Content should start to the right of or near the sidebar
    expect(layout.contentLeft).toBeGreaterThanOrEqual(layout.sidebarRight - 5);
  });

  test('desktop: nav links visible, hamburger hidden', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    await expect(page.locator('.header-nav')).toBeVisible();
    await expect(page.locator('.sidebar-toggle')).not.toBeVisible();
  });

  test('mobile: hamburger visible, nav links hidden', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await expect(page.locator('.sidebar-toggle')).toBeVisible();
    await expect(page.locator('.header-nav')).not.toBeVisible();
  });

  test('mobile: content takes full width', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    const layout = await page.evaluate(() => {
      const content = document.querySelector('.content-area');
      if (!content) return null;
      const rect = content.getBoundingClientRect();
      return { width: Math.round(rect.width), viewportWidth: window.innerWidth };
    });
    expect(layout).not.toBeNull();
    // Content area should be close to full viewport width on mobile
    expect(layout.width).toBeGreaterThanOrEqual(layout.viewportWidth - 40);
  });

  test('mobile: header is compact', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    const box = await page.locator('.site-header').boundingBox();
    expect(box).not.toBeNull();
    expect(box.height).toBeLessThanOrEqual(55);
  });
});

// ============================================================
// Documentation Pages  -  Structure
// ============================================================
test.describe('Documentation Pages  -  Structure', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
  });

  test('page heading and description are visible', async ({ page }) => {
    await expect(page.locator('.page-heading')).toBeVisible();
    await expect(page.locator('.page-description')).toBeVisible();
  });

  test('breadcrumb navigation is present', async ({ page }) => {
    await expect(page.locator('.breadcrumb')).toBeVisible();
    const links = page.locator('.breadcrumb a');
    expect(await links.count()).toBeGreaterThanOrEqual(1);
  });

  test('doc content area has substantial text', async ({ page }) => {
    const content = page.locator('.doc-content');
    await expect(content).toBeVisible();
    const text = await content.textContent();
    expect(text.length).toBeGreaterThan(200);
  });

  test('prev/next navigation exists at bottom', async ({ page }) => {
    const nav = page.locator('.prev-next');
    await nav.scrollIntoViewIfNeeded();
    await expect(nav).toBeVisible();
  });

  test('footer is present on doc pages', async ({ page }) => {
    const footer = page.locator('.site-footer');
    await footer.scrollIntoViewIfNeeded();
    await expect(footer).toBeVisible();
  });
});

// ============================================================
// Documentation Pages  -  Sidebar Navigation
// ============================================================
test.describe('Documentation Pages  -  Sidebar', () => {
  test('desktop: sidebar is visible with sections and links', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('.sidebar')).toBeVisible();
    const sections = page.locator('.sidebar-section-title');
    expect(await sections.count()).toBeGreaterThanOrEqual(5);
    const links = page.locator('.sidebar-links a');
    expect(await links.count()).toBeGreaterThanOrEqual(20);
  });

  test('desktop: active page is highlighted in sidebar', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    const active = page.locator('.sidebar-links a.active');
    await expect(active).toBeVisible();
    expect(await active.count()).toBe(1);
    const text = await active.textContent();
    expect(text).toContain('Quick Start');
  });

  test('desktop: TOC sidebar is visible on wide screens', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    await page.goto('/docs/pr-scanning.html');
    await page.waitForLoadState('domcontentloaded');
    const vw = await page.evaluate(() => window.innerWidth);
    if (vw > 1200) {
      await expect(page.locator('.toc-sidebar')).toBeVisible();
    }
  });

  test('sidebar link navigates to correct page', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    // Click on a different page link in the sidebar
    const prLink = page.locator('.sidebar-links a:text-is("PR Scanning")');
    await prLink.click();
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('.page-heading')).toContainText('PR Scanning');
  });
});

// ============================================================
// Mobile Navigation
// ============================================================
test.describe('Mobile Navigation', () => {
  test('hamburger opens sidebar overlay', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    await page.locator('.sidebar-toggle').click();
    await page.waitForTimeout(400);
    const sidebar = page.locator('.sidebar');
    const classList = await sidebar.getAttribute('class');
    expect(classList).toContain('open');
    // Sidebar should have links
    const links = sidebar.locator('.sidebar-links a');
    expect(await links.count()).toBeGreaterThanOrEqual(20);
  });

  test('mobile sidebar link navigates correctly', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    await page.locator('.sidebar-toggle').click();
    await page.waitForTimeout(400);
    const secretsLink = page.locator('.sidebar-links a', { hasText: 'Secrets Scanning' });
    await secretsLink.click();
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('.page-heading')).toContainText('Secrets Scanning');
  });

  test('no horizontal overflow on mobile doc pages', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await page.goto('/docs/pr-blocking.html');
    await page.waitForLoadState('domcontentloaded');
    const hasOverflow = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth
    );
    expect(hasOverflow).toBe(false);
  });
});

// ============================================================
// Search Functionality
// ============================================================
test.describe('Search', () => {
  test('search input filters results on landing page', async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
    const input = page.locator('#docsSearch');
    await input.fill('secrets');
    await page.waitForTimeout(400);
    const value = await input.inputValue();
    expect(value).toBe('secrets');
    // Full-text search should show result items
    const results = page.locator('#searchResults .search-result-item');
    expect(await results.count()).toBeGreaterThan(0);
  });

  test('search matches content inside page body', async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
    const input = page.locator('#docsSearch');
    // Search for a term that only appears inside page body content,
    // not in any page title
    await input.fill('false positive');
    await page.waitForTimeout(400);
    const results = page.locator('#searchResults .search-result-item');
    expect(await results.count()).toBeGreaterThan(0);
    // Each result should have a title and snippet
    const firstTitle = results.first().locator('.search-result-title');
    await expect(firstTitle).not.toBeEmpty();
    const firstSnippet = results.first().locator('.search-result-snippet');
    await expect(firstSnippet).not.toBeEmpty();
  });

  test('search shows no results message for nonsense query', async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
    const input = page.locator('#docsSearch');
    await input.fill('xyzzyspqr12345');
    await page.waitForTimeout(400);
    const noResults = page.locator('.search-no-results');
    await expect(noResults).toBeVisible();
  });
});

// ============================================================
// Cross-page Navigation Flow
// ============================================================
test.describe('Navigation Flow', () => {
  test('landing page sidebar link navigates to doc page', async ({ page, isMobile }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
    // On mobile, open sidebar first
    if (isMobile) {
      const toggle = page.locator('.sidebar-toggle');
      await toggle.click();
      await page.locator('.sidebar.open').waitFor({ state: 'visible' });
    }
    // Click first doc link in sidebar nav
    const firstLink = page.locator('.sidebar-nav .sidebar-links a').first();
    await firstLink.click();
    await page.waitForLoadState('domcontentloaded');
    // Should be on a doc page with header and content
    await expect(page.locator('.page-heading')).toBeVisible();
    await expect(page.locator('.site-header')).toBeVisible();
  });

  test('prev/next links form a navigable chain', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    // Start at first page
    await page.goto('/docs/documentation.html');
    await page.waitForLoadState('domcontentloaded');
    // Should have next but no prev
    const prevLinks = page.locator('.prev-next-link.prev-link');
    expect(await prevLinks.count()).toBe(0);
    const nextLink = page.locator('.prev-next-link.next-link');
    await expect(nextLink).toBeVisible();
    // Click next and verify we moved
    await nextLink.scrollIntoViewIfNeeded();
    await nextLink.click();
    await page.waitForLoadState('domcontentloaded');
    const heading = await page.locator('.page-heading').textContent();
    expect(heading).not.toContain('Documentation');
    // Now should have a prev link
    const newPrev = page.locator('.prev-next-link.prev-link');
    await expect(newPrev).toBeVisible();
  });

  test('Docs link in header returns to landing page', async ({ page }) => {
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    const docsLink = page.locator('.header-nav a', { hasText: 'Docs' });
    if (await docsLink.isVisible()) {
      await docsLink.click();
      await page.waitForLoadState('domcontentloaded');
      await expect(page.locator('.page-heading')).toContainText('Documentation');
    }
  });
});

// ============================================================
// Accessibility
// ============================================================
test.describe('Accessibility', () => {
  test('html has lang attribute', async ({ page }) => {
    await page.goto('/index.html');
    const lang = await page.locator('html').getAttribute('lang');
    expect(lang).toBe('en');
  });

  test('all images have alt text', async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
    const images = page.locator('img');
    const count = await images.count();
    for (let i = 0; i < count; i++) {
      const alt = await images.nth(i).getAttribute('alt');
      expect(alt).toBeTruthy();
    }
  });

  test('focus-visible styles are applied', async ({ page }) => {
    await page.goto('/index.html');
    // Tab to first focusable element and check outline
    await page.keyboard.press('Tab');
    const focused = page.locator(':focus-visible');
    expect(await focused.count()).toBeGreaterThanOrEqual(1);
  });

  test('color contrast: body text is readable', async ({ page }) => {
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    const bodyColor = await page.evaluate(() => {
      const el = document.querySelector('.doc-content');
      if (!el) return null;
      return getComputedStyle(el).color;
    });
    // Text should be dark on light background
    expect(bodyColor).not.toBeNull();
    // Parse rgb values - text should be dark (max channel < 150 for dark text)
    const match = bodyColor.match(/\d+/g);
    if (match) {
      const maxChannel = Math.max(...match.map(Number));
      expect(maxChannel).toBeLessThan(150);
    }
  });
});

// ============================================================
// Typography & Sizing Regression Guards
// ============================================================
test.describe('Typography Regression Guards', () => {
  test('page heading is not oversized', async ({ page }) => {
    await page.goto('/index.html');
    await page.waitForLoadState('domcontentloaded');
    const fontSize = await page.evaluate(() => {
      const el = document.querySelector('.page-heading');
      return parseFloat(getComputedStyle(el).fontSize);
    });
    // Should be between 22px and 40px
    expect(fontSize).toBeGreaterThanOrEqual(22);
    expect(fontSize).toBeLessThanOrEqual(40);
  });

  test('page heading font size is reasonable', async ({ page }) => {
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    const fontSize = await page.evaluate(() => {
      const el = document.querySelector('.page-heading');
      return parseFloat(getComputedStyle(el).fontSize);
    });
    expect(fontSize).toBeGreaterThanOrEqual(22);
    expect(fontSize).toBeLessThanOrEqual(40);
  });

  test('base body font size is at least 16px', async ({ page }) => {
    await page.goto('/index.html');
    const fontSize = await page.evaluate(() =>
      parseFloat(getComputedStyle(document.documentElement).fontSize)
    );
    expect(fontSize).toBeGreaterThanOrEqual(16);
  });
});

// ============================================================
// Content Coverage  -  Spot Checks
// ============================================================
test.describe('Content Coverage', () => {
  test('coverage matrix page has a table', async ({ page }) => {
    await page.goto('/docs/vulnerability-trends.html');
    await page.waitForLoadState('domcontentloaded');
    const table = page.locator('.doc-content table').first();
    await expect(table).toBeVisible();
  });

  test('Custom Code Policy page has content about policies', async ({ page }) => {
    await page.goto('/docs/custom-code-policies.html');
    await page.waitForLoadState('domcontentloaded');
    const text = await page.locator('.doc-content').textContent();
    expect(text.toLowerCase()).toContain('polic');
  });

  test('API guide page has content', async ({ page }) => {
    await page.goto('/docs/dryrun-api.html');
    await page.waitForLoadState('domcontentloaded');
    const text = await page.locator('.doc-content').textContent();
    expect(text.length).toBeGreaterThan(100);
  });

  test('AI agent security page exists and loads', async ({ page }) => {
    await page.goto('/docs/dryrun-skill.html');
    await page.waitForLoadState('domcontentloaded');
    await expect(page.locator('.page-heading')).toBeVisible();
  });
});

// ============================================================
// UI Acceptance Tests (borrowed from capability matrix patterns)
// ============================================================
test.describe('UI Acceptance', () => {
  test('no horizontal overflow on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const hasOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth;
    });
    expect(hasOverflow).toBe(false);
  });

  test('no horizontal overflow on mobile doc pages', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await page.goto('/docs/pr-blocking.html');
    await page.waitForLoadState('domcontentloaded');
    const hasOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth;
    });
    expect(hasOverflow).toBe(false);
  });

  test('no horizontal overflow on table pages on mobile', async ({ page, isMobile }) => {
    test.skip(!isMobile, 'Mobile only');
    await page.goto('/docs/vulnerability-trends.html');
    await page.waitForLoadState('domcontentloaded');
    const hasOverflow = await page.evaluate(() => {
      return document.body.scrollWidth > window.innerWidth;
    });
    expect(hasOverflow).toBe(false);
  });

  test('header stays visible when scrolling on desktop', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    await page.goto('/docs/quick-start.html');
    await page.waitForLoadState('domcontentloaded');
    // Scroll down well past the header
    await page.evaluate(() => window.scrollBy(0, 800));
    await page.waitForTimeout(300);
    const headerVisible = await page.evaluate(() => {
      const header = document.querySelector('.site-header');
      if (!header) return false;
      const rect = header.getBoundingClientRect();
      return rect.top >= 0 && rect.bottom <= window.innerHeight;
    });
    expect(headerVisible).toBe(true);
  });

  test('sidebar stays visible when scrolling on desktop', async ({ page, isMobile }) => {
    test.skip(!!isMobile, 'Desktop only');
    // Use a long page so there's enough content to scroll
    await page.goto('/docs/vulnerability-trends.html');
    await page.waitForLoadState('domcontentloaded');
    await page.evaluate(() => window.scrollBy(0, 800));
    await page.waitForTimeout(300);
    // Sidebar should be sticky - verify it's still in the viewport
    const sidebarInViewport = await page.evaluate(() => {
      const sidebar = document.querySelector('.sidebar');
      if (!sidebar) return false;
      const rect = sidebar.getBoundingClientRect();
      // Sticky sidebar should have top near 56px (header height)
      return rect.top >= 0 && rect.top < 100 && rect.height > 200;
    });
    expect(sidebarInViewport).toBe(true);
  });

  test('code blocks do not overflow their container', async ({ page }) => {
    await page.goto('/docs/mcp.html');
    await page.waitForLoadState('domcontentloaded');
    const hasOverflow = await page.evaluate(() => {
      const codeBlocks = document.querySelectorAll('.doc-content pre');
      for (const pre of codeBlocks) {
        if (pre.scrollWidth > pre.clientWidth + 2) {
          // Allow overflow only if overflow-x is auto/scroll (scrollable)
          const style = getComputedStyle(pre);
          if (style.overflowX !== 'auto' && style.overflowX !== 'scroll') {
            return true;
          }
        }
      }
      return false;
    });
    expect(hasOverflow).toBe(false);
  });

  test('all landing page sidebar sections have links', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const sections = page.locator('.sidebar-nav .sidebar-section');
    const count = await sections.count();
    expect(count).toBeGreaterThanOrEqual(5);
    // Each section should have at least one link
    for (let i = 0; i < count; i++) {
      const links = sections.nth(i).locator('.sidebar-links a');
      const linkCount = await links.count();
      expect(linkCount).toBeGreaterThan(0);
    }
  });
});
