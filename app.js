/**
 * DryRun Security Docs - app.js
 * Handles: theme toggle, mobile sidebar toggle, TOC active state on scroll,
 * smooth scroll, docs search (index page), keyboard shortcuts, and copy buttons.
 */

// ── Theme toggle ──────────────────────────────────────────────────────────
(function () {
  var STORAGE_KEY = 'drs-theme';
  var html = document.documentElement;

  function getPreferred() {
    var stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function applyTheme(theme) {
    if (theme === 'light') {
      html.setAttribute('data-theme', 'light');
    } else {
      html.removeAttribute('data-theme');
    }
  }

  // Apply immediately to avoid flash
  applyTheme(getPreferred());

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('themeToggle');
    if (!btn) return;

    btn.addEventListener('click', function () {
      var current = html.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      var next = current === 'light' ? 'dark' : 'light';
      applyTheme(next);
      localStorage.setItem(STORAGE_KEY, next);
    });

    // Respond to OS-level preference changes
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', function (e) {
      if (!localStorage.getItem(STORAGE_KEY)) {
        applyTheme(e.matches ? 'light' : 'dark');
      }
    });
  });
})();

(function () {
  'use strict';

  // -------------------------------------------------------------------------
  // Mobile sidebar toggle
  // -------------------------------------------------------------------------
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const sidebarOverlay = document.getElementById('sidebarOverlay');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      const isOpen = sidebar.classList.toggle('open');
      if (sidebarOverlay) {
        sidebarOverlay.style.display = isOpen ? 'block' : 'none';
      }
    });
  }

  if (sidebarOverlay) {
    sidebarOverlay.addEventListener('click', function () {
      if (sidebar) sidebar.classList.remove('open');
      sidebarOverlay.style.display = 'none';
    });
  }

  // Close sidebar on Escape key
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && sidebar && sidebar.classList.contains('open')) {
      sidebar.classList.remove('open');
      if (sidebarOverlay) sidebarOverlay.style.display = 'none';
    }
  });

  // -------------------------------------------------------------------------
  // TOC active state tracking on scroll
  // -------------------------------------------------------------------------
  const tocLinks = document.querySelectorAll('.toc-list a');
  const headings = document.querySelectorAll('.doc-content h2, .doc-content h3');

  if (tocLinks.length > 0 && headings.length > 0) {
    let activeLink = null;

    function setActiveLink(link) {
      if (activeLink === link) return;
      if (activeLink) activeLink.classList.remove('active');
      activeLink = link;
      if (activeLink) activeLink.classList.add('active');
    }

    function updateActiveToc() {
      const scrollY = window.scrollY + 100; // offset for header
      let current = null;

      for (let i = headings.length - 1; i >= 0; i--) {
        const heading = headings[i];
        if (heading.offsetTop <= scrollY) {
          current = heading;
          break;
        }
      }

      if (current) {
        const id = current.getAttribute('id');
        if (id) {
          const matchingLink = document.querySelector('.toc-list a[href="#' + CSS.escape(id) + '"]');
          if (matchingLink) {
            setActiveLink(matchingLink);
          }
        }
      } else if (tocLinks.length > 0) {
        setActiveLink(tocLinks[0]);
      }
    }

    // Throttled scroll handler
    let scrollTicking = false;
    window.addEventListener('scroll', function () {
      if (!scrollTicking) {
        requestAnimationFrame(function () {
          updateActiveToc();
          scrollTicking = false;
        });
        scrollTicking = true;
      }
    }, { passive: true });

    // Initial state
    updateActiveToc();
  }

  // -------------------------------------------------------------------------
  // Smooth scroll for anchor links
  // -------------------------------------------------------------------------
  document.addEventListener('click', function (e) {
    const target = e.target.closest('a[href^="#"]');
    if (!target) return;
    const href = target.getAttribute('href');
    if (!href || href === '#') return;

    const id = href.slice(1);
    const el = document.getElementById(id);
    if (!el) return;

    e.preventDefault();
    const headerHeight = document.querySelector('.site-header')
      ? document.querySelector('.site-header').offsetHeight
      : 56;
    const top = el.getBoundingClientRect().top + window.scrollY - headerHeight - 16;
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });

    // Update URL without triggering scroll
    history.pushState(null, '', href);
  });

  // -------------------------------------------------------------------------
  // Full-text docs search (sidebar, all pages) + keyboard shortcut
  // -------------------------------------------------------------------------
  const docsSearch = document.getElementById('docsSearch');
  if (docsSearch) {
    const resultsContainer = document.getElementById('searchResults');
    const searchIndex = window.__SEARCH_INDEX__ || [];
    const MAX_RESULTS = 12;
    const SNIPPET_RADIUS = 60;
    let activeIdx = -1;

    // All pages live at site root under a flat URL structure:
    //   documentation -> '/', all others -> '/{slug}'.
    // Each search index entry carries its URL in `u`.

    // Build a snippet around the first match of query in text
    function buildSnippet(text, query) {
      var lower = text.toLowerCase();
      var pos = lower.indexOf(query);
      if (pos === -1) return '';
      var start = Math.max(0, pos - SNIPPET_RADIUS);
      var end = Math.min(text.length, pos + query.length + SNIPPET_RADIUS);
      var snippet = '';
      if (start > 0) snippet += '\u2026';
      var raw = text.slice(start, end);
      var matchStart = pos - start;
      snippet += raw.slice(0, matchStart)
        + '<mark>' + raw.slice(matchStart, matchStart + query.length) + '</mark>'
        + raw.slice(matchStart + query.length);
      if (end < text.length) snippet += '\u2026';
      return snippet;
    }

    function runSearch(query) {
      if (!resultsContainer) return;
      activeIdx = -1;

      if (!query) {
        resultsContainer.innerHTML = '';
        resultsContainer.hidden = true;
        return;
      }

      var results = [];
      for (var i = 0; i < searchIndex.length; i++) {
        var entry = searchIndex[i];
        var titleLower = entry.t.toLowerCase();
        var descLower = entry.d.toLowerCase();
        var bodyLower = entry.b.toLowerCase();
        var titleMatch = titleLower.indexOf(query) !== -1;
        var descMatch = descLower.indexOf(query) !== -1;
        var bodyMatch = bodyLower.indexOf(query) !== -1;

        if (titleMatch || descMatch || bodyMatch) {
          var snippet = '';
          var score = 0;
          if (titleMatch) {
            score = 3;
            snippet = buildSnippet(entry.d || entry.b, query) || buildSnippet(entry.b, query);
          } else if (descMatch) {
            score = 2;
            snippet = buildSnippet(entry.d, query);
          } else {
            score = 1;
            snippet = buildSnippet(entry.b, query);
          }
          results.push({ entry: entry, score: score, snippet: snippet });
        }
      }

      results.sort(function (a, b) { return b.score - a.score; });
      results = results.slice(0, MAX_RESULTS);

      if (results.length === 0) {
        resultsContainer.innerHTML = '<div class="search-no-results">No results found</div>';
        resultsContainer.hidden = false;
        return;
      }

      var html = '';
      for (var j = 0; j < results.length; j++) {
        var r = results[j];
        var anchor = r.entry.a ? '#' + r.entry.a : '';
        html += '<a class="search-result-item" href="' + r.entry.u + anchor + '"'
          + ' data-idx="' + j + '">'
          + '<span class="search-result-title">' + escHtml(r.entry.t) + '</span>'
          + '<span class="search-result-section">' + escHtml(r.entry.n) + '</span>'
          + (r.snippet ? '<span class="search-result-snippet">' + r.snippet + '</span>' : '')
          + '</a>';
      }
      resultsContainer.innerHTML = html;
      resultsContainer.hidden = false;
    }

    function escHtml(str) {
      var div = document.createElement('div');
      div.appendChild(document.createTextNode(str));
      return div.innerHTML;
    }

    function setActive(idx) {
      var items = resultsContainer.querySelectorAll('.search-result-item');
      if (items.length === 0) return;
      items.forEach(function (el) { el.classList.remove('active'); });
      if (idx >= 0 && idx < items.length) {
        items[idx].classList.add('active');
        items[idx].scrollIntoView({ block: 'nearest' });
      }
      activeIdx = idx;
    }

    // Debounced input handler
    var searchTimer = null;
    docsSearch.addEventListener('input', function () {
      clearTimeout(searchTimer);
      var q = this.value.trim().toLowerCase();
      searchTimer = setTimeout(function () { runSearch(q); }, 150);
    });

    // Keyboard navigation within results
    docsSearch.addEventListener('keydown', function (e) {
      var items = resultsContainer ? resultsContainer.querySelectorAll('.search-result-item') : [];
      if (e.key === 'ArrowDown' && items.length > 0) {
        e.preventDefault();
        setActive(Math.min(activeIdx + 1, items.length - 1));
      } else if (e.key === 'ArrowUp' && items.length > 0) {
        e.preventDefault();
        setActive(Math.max(activeIdx - 1, 0));
      } else if (e.key === 'Enter' && activeIdx >= 0 && items[activeIdx]) {
        e.preventDefault();
        items[activeIdx].click();
      } else if (e.key === 'Escape') {
        this.value = '';
        runSearch('');
        this.blur();
      }
    });

    // Close results when clicking outside the sidebar search area
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.sidebar-search')) {
        if (resultsContainer) {
          resultsContainer.innerHTML = '';
          resultsContainer.hidden = true;
        }
      }
    });

    // Re-show results when focusing back into search with a query
    docsSearch.addEventListener('focus', function () {
      var q = this.value.trim().toLowerCase();
      if (q) runSearch(q);
    });

    // Cmd/Ctrl+K to focus search
    document.addEventListener('keydown', function (e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        docsSearch.focus();
        docsSearch.select();
      }
    });
  }

  // -------------------------------------------------------------------------
  // Sidebar active link scroll into view
  // -------------------------------------------------------------------------
  const activeNavLink = document.querySelector('.sidebar-links .active');
  if (activeNavLink) {
    activeNavLink.scrollIntoView({ block: 'nearest', behavior: 'auto' });
  }

  // -------------------------------------------------------------------------
  // Code block copy button
  // -------------------------------------------------------------------------
  document.querySelectorAll('.doc-content pre').forEach(function (pre) {
    const btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = 'Copy';
    btn.setAttribute('aria-label', 'Copy code to clipboard');
    pre.appendChild(btn);

    btn.addEventListener('click', function () {
      const code = pre.querySelector('code');
      const text = code ? code.textContent : pre.textContent;
      navigator.clipboard.writeText(text).then(function () {
        btn.textContent = 'Copied';
        btn.classList.add('copied');
        setTimeout(function () {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 2000);
      }).catch(function () {
        btn.textContent = 'Error';
        setTimeout(function () { btn.textContent = 'Copy'; }, 2000);
      });
    });
  });

})();
