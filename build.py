"""
DryRun Security Documentation Site Generator
Generates all HTML pages for the docs site.
Usage: python3 build.py

Site structure: 4 sections, 18 pages
"""
import csv
import datetime
import html
import io
import json
import re
import shutil
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(value: str) -> str:
    """Escape a string for safe HTML interpolation."""
    return html.escape(str(value), quote=True)


def slugify_heading(text: str) -> str:
    """Convert a heading string to an anchor slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text.strip())
    return text


def extract_toc(html_content: str):
    """Extract h2 and h3 headings from HTML content for TOC generation."""
    pattern = re.compile(r'<(h[23])[^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
    items = []
    for match in pattern.finditer(html_content):
        level = match.group(1).lower()
        anchor = match.group(2)
        inner = match.group(3)
        # Remove the injected anchor link before extracting the visible label.
        inner = re.sub(
            r'<a\b[^>]*class=["\'][^"\']*\banchor-link\b[^"\']*["\'][^>]*>.*?</a>',
            '',
            inner,
            flags=re.IGNORECASE | re.DOTALL,
        )
        label = re.sub(r'<[^>]+>', '', inner).strip()
        label = html.unescape(label)  # decode entities like &amp; before re-encoding
        items.append({'level': level, 'anchor': anchor, 'label': label})
    return items


def add_heading_anchors(html_content: str) -> str:
    """Inject id attributes and visible anchor links into every h2/h3 tag.

    For each heading, generate a slug from its (HTML-stripped) text, set
    id="<slug>" on the tag (preserving any existing attributes that are not
    id), and append an anchor link inside the heading pointing at the same
    slug. Duplicate slugs on the same page are disambiguated with -2, -3, etc.
    """
    seen: dict = {}

    def replacer(m):
        tag = m.group(1)
        attrs = m.group(2) or ''
        inner = m.group(3)
        label = re.sub(r'<[^>]+>', '', inner).strip()
        base_slug = slugify_heading(label)
        if not base_slug:
            return m.group(0)
        count = seen.get(base_slug, 0) + 1
        seen[base_slug] = count
        slug = base_slug if count == 1 else f'{base_slug}-{count}'

        existing_id = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if existing_id:
            slug = existing_id.group(1)
            new_attrs = attrs
        else:
            new_attrs = f'{attrs} id="{slug}"'

        anchor = (
            f' <a class="anchor-link" href="#{slug}" '
            f'aria-label="Link to this section">#</a>'
        )
        return f'<{tag}{new_attrs}>{inner}{anchor}</{tag}>'

    pattern = re.compile(r'<(h[23])([^>]*)>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
    return pattern.sub(replacer, html_content)


def inject_heading_ids(html_content: str) -> str:
    """Inject id attributes into h2/h3 tags without adding visible anchor links.

    Used for non-page contexts (search index, Webflow export) where we want
    stable anchors but not the visible `#` link character.
    """
    seen: dict = {}

    def replacer(m):
        tag = m.group(1)
        attrs = m.group(2) or ''
        inner = m.group(3)
        existing_id = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if existing_id:
            return m.group(0)
        label = re.sub(r'<[^>]+>', '', inner).strip()
        base_slug = slugify_heading(label)
        if not base_slug:
            return m.group(0)
        count = seen.get(base_slug, 0) + 1
        seen[base_slug] = count
        slug = base_slug if count == 1 else f'{base_slug}-{count}'
        return f'<{tag}{attrs} id="{slug}">{inner}</{tag}>'

    pattern = re.compile(r'<(h[23])([^>]*)>(.*?)</\1>', re.IGNORECASE | re.DOTALL)
    return pattern.sub(replacer, html_content)


# ---------------------------------------------------------------------------
# Site structure
# ---------------------------------------------------------------------------


# Former page slugs retained as (old_slug, new_slug) mappings. The QA build
# does not publish flat redirect stubs because its GitHub Pages source is docs/
# and each served HTML file must contain documentation content.
REDIRECTS = [
    ('coverage-matrix-vulnerability-categories', 'vulnerability-coverage-matrix'),
    ('ai-coding-integration', 'dryrun-skill'),
]


SECTIONS = [
    {
        'name': 'Getting Started',
        'slug': 'getting-started',
        'pages': ['documentation', 'quick-start'],
    },
    {
        'name': 'Scanning',
        'slug': 'scanning',
        'pages': ['deepscan', 'pr-scanning', 'secrets-scanning', 'iac-scanning', 'sca', 'auto-fix', 'language-support', 'vulnerability-coverage-matrix'],
    },
    {
        'name': 'Platform',
        'slug': 'platform',
        'pages': ['code-security-intelligence', 'pr-scanning-configuration', 'custom-code-policies', 'repository-context', 'risk-register', 'finding-tuning', 'pr-blocking', 'compliance-grc', 'permissions', 'mcp', 'dryrun-api', 'dashboard'],
        'nav_hidden': ['compliance-grc', 'dashboard'],
    },
    {
        'name': 'Integrations',
        'slug': 'integrations',
        'pages': ['slack-integration', 'webhook-integration', 'jira-integration', 'api-access-keys', 'dryrun-skill'],
    },
]



# ---------------------------------------------------------------------------
# Page content definitions
# ---------------------------------------------------------------------------

PAGES = {}


# -- Getting Started --

PAGES['documentation'] = {
    'title': 'Documentation',
    'description': 'DryRun Security is an AI-native application security platform that reviews every pull request and repository scan for vulnerabilities in real time. It builds an intelligence layer on top of all scan data, surfacing trends, patterns, and risks across your entire codebase and development organization. These docs cover setup, scanning, code security intelligence, platform administration, and integrations.',
    'section': 'Getting Started',
    'content': '''
<div class="landing-section">
  <div class="landing-grid cols-3">
    <a class="landing-card persona" href="./risk-register">
      <span class="landing-card-title">AppSec Engineers</span>
      <span class="landing-card-desc">Surface top-level risk across your organization, review findings in depth, and run targeted security reviews on any repository.</span>
    </a>
    <a class="landing-card persona" href="./quick-start">
      <span class="landing-card-title">Developers</span>
      <span class="landing-card-desc">Connect your repositories, understand PR findings as they appear, and triage false positives without leaving your workflow.</span>
    </a>
    <a class="landing-card persona" href="./pr-scanning-configuration">
      <span class="landing-card-title">Admins</span>
      <span class="landing-card-desc">Configure repository scanning rules, manage notification channels, customize finding interpretation, and integrate via the API and MCP.</span>
    </a>
  </div>
</div>

<div class="landing-section">
  <div class="landing-section-header">
    <h2 id="scanning-products">Products</h2>
  </div>
  <div class="landing-grid cols-3">
    <a class="landing-card" href="./pr-scanning">
      <span class="landing-card-title">PR Scanning</span>
      <span class="landing-card-desc">Every PR is reviewed by DryRun Security&#x27;s AI engine, which posts contextual findings directly in your code review.</span>
    </a>
    <a class="landing-card" href="./deepscan">
      <span class="landing-card-title">Repository Scanning with DeepScan</span>
      <span class="landing-card-desc">Scan an entire codebase on demand to uncover vulnerabilities that predate PR-level analysis.</span>
    </a>
    <a class="landing-card" href="./secrets-scanning">
      <span class="landing-card-title">Secrets Scanning</span>
      <span class="landing-card-desc">Catch API keys, tokens, and hardcoded passwords in diffs before they are merged into protected branches.</span>
    </a>
    <a class="landing-card" href="./iac-scanning">
      <span class="landing-card-title">IaC Scanning</span>
      <span class="landing-card-desc">Scan Terraform configurations for security misconfigurations and insecure defaults in pull requests.</span>
    </a>
    <a class="landing-card" href="./sca">
      <span class="landing-card-title">SCA</span>
      <span class="landing-card-desc">Identify known CVEs and license issues in your open-source dependencies with DeepScan.</span>
    </a>
    <a class="landing-card" href="./auto-fix">
      <span class="landing-card-title">Auto Fix</span>
      <span class="landing-card-desc">Accept AI-generated fixes for common vulnerability patterns and verify the remediation in a single step.</span>
    </a>
  </div>
</div>

<div class="landing-section">
  <div class="landing-section-header">
    <h2 id="code-security-intelligence">Code Security Intelligence</h2>
  </div>
  <div class="landing-grid cols-3">
    <a class="landing-card" href="./code-security-intelligence" style="grid-column: 1 / -1">
      <span class="landing-card-title">Code Security Intelligence</span>
      <span class="landing-card-desc">An intelligence layer built on top of all finding data and trends, surfacing feature ships, vulnerability trends, architecture risks, developer patterns, shadow AI usage, incident investigation, and more.</span>
    </a>
  </div>
</div>

<div class="landing-section">
  <div class="landing-section-header">
    <h2 id="platform-integrations">Platform & Integrations</h2>
  </div>
  <div class="landing-grid cols-3">
    <a class="landing-card" href="./pr-blocking">
      <span class="landing-card-title">PR Blocking</span>
      <span class="landing-card-desc">Prevent PRs from merging when findings exceed the severity or policy thresholds you define.</span>
    </a>
    <a class="landing-card" href="./custom-code-policies">
      <span class="landing-card-title">Custom Code Policies</span>
      <span class="landing-card-desc">Write organization-specific security rules in plain language and enforce them on every scan.</span>
    </a>
    <a class="landing-card" href="./compliance-grc">
      <span class="landing-card-title">Compliance & GRC</span>
      <span class="landing-card-desc">Generate compliance reports, maintain audit trails, and demonstrate regulatory readiness from a single dashboard.</span>
    </a>
    <a class="landing-card" href="./slack-integration">
      <span class="landing-card-title">Slack Integration</span>
      <span class="landing-card-desc">Route finding alerts and scan summaries to the Slack channels your team already monitors.</span>
    </a>
    <a class="landing-card" href="./webhook-integration">
      <span class="landing-card-title">Webhook Integration</span>
      <span class="landing-card-desc">Stream scan events and finding data to any HTTP endpoint for custom automation and reporting pipelines.</span>
    </a>
    <a class="landing-card" href="./mcp">
      <span class="landing-card-title">MCP</span>
      <span class="landing-card-desc">Expose DryRun Security data to AI coding assistants and agents through the Model Context Protocol.</span>
    </a>
  </div>
</div>

''',
}

PAGES['quick-start'] = {
    'title': 'Quick Start',
    'description': 'Install DryRun Security on GitHub or GitLab and start scanning pull requests in minutes.',
    'section': 'Getting Started',
    'content': '''
<h2 id="getting-started">Getting Started</h2>

<p>DryRun Security is an AI-native application security platform that reviews every pull request for vulnerabilities in real time. This guide helps you install DryRun Security on GitHub or GitLab, run your first scan, and configure the platform to match your workflow.</p>

<h3 id="deployment-rollout-best-practices">Deployment Rollout Best Practices</h3>

<p>Follow these steps to get the most out of DryRun Security:</p>

<table>
  <thead>
    <tr>
      <th>Step</th>
      <th>Action</th>
      <th>Description</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td><strong><a href="#github-installation">Install DryRun Security</a></strong></td>
      <td>Connect your repositories on GitHub or GitLab so every pull request is automatically reviewed.</td>
    </tr>
    <tr>
      <td>2</td>
      <td><strong><a href="./deepscan">DeepScan</a></strong></td>
      <td>Run a full-repository scan to establish your baseline security posture.</td>
    </tr>
    <tr>
      <td>3</td>
      <td><strong><a href="./risk-register">Review findings in the Risk Register</a></strong></td>
      <td>Examine and prioritize vulnerabilities surfaced across your repositories.</td>
    </tr>
    <tr>
      <td>4</td>
      <td><strong><a href="./finding-tuning">Triage false positives as needed</a></strong></td>
      <td>Suppress findings that are not applicable so future scans stay focused on real risks.</td>
    </tr>
    <tr>
      <td>5</td>
      <td><strong><a href="./repository-context">Configure context</a></strong></td>
      <td>Provide repository-level context so DryRun Security&#x27;s analysis is tailored to your codebase.</td>
    </tr>
    <tr>
      <td>6</td>
      <td><strong><a href="./custom-code-policies">Create Custom Code Policies</a></strong></td>
      <td>Define organization-specific security rules written in plain English.</td>
    </tr>
    <tr>
      <td>7</td>
      <td><strong><a href="./slack-integration">Configure integrations and notifications</a></strong></td>
      <td>Route alerts to Slack, webhooks, or other channels your team already uses.</td>
    </tr>
    <tr>
      <td>8</td>
      <td><strong><a href="./pr-blocking">Enforcement</a></strong></td>
      <td>Configure blocking rules to prevent PRs from merging when findings exceed your defined severity or policy thresholds.</td>
    </tr>
    <tr>
      <td>9</td>
      <td><strong><a href="./code-security-intelligence">Unlock the power of Code Security Intelligence</a></strong></td>
      <td>Query the intelligence index to track features, trends, and risks across your organization.</td>
    </tr>
  </tbody>
</table>

<h3 id="supported-platforms">Supported Platforms</h3>

<table>
  <thead>
    <tr>
      <th>Platform</th>
      <th>Supported Versions</th>
      <th>Setup Guide</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GitHub</td>
      <td>GitHub.com (Cloud)</td>
      <td><a href="#github-installation">GitHub Installation</a></td>
    </tr>
    <tr>
      <td>GitHub</td>
      <td>GitHub Enterprise Server (On-Premises)</td>
      <td><a href="#ghes-installation">GitHub Enterprise Server Installation</a></td>
    </tr>
    <tr>
      <td>GitLab</td>
      <td>GitLab.com (Cloud)</td>
      <td><a href="#gitlab-installation">GitLab Installation</a></td>
    </tr>
  </tbody>
</table>

<h3 id="installation-requirements">Installation Requirements</h3>

<p>Before installing DryRun Security, confirm the account performing the installation has the required permissions for your platform:</p>

<table>
  <thead>
    <tr>
      <th>Platform</th>
      <th>Who Can Install</th>
      <th>Access Granted</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GitHub</td>
      <td>Organization admin, or Enterprise admin if an enterprise account is in use</td>
      <td>GitHub App with read access to code and metadata, and read/write access to checks, issues, and pull requests</td>
    </tr>
    <tr>
      <td>GitLab</td>
      <td>System Administrator or Group Owner</td>
      <td>API access via a scoped Group Access Token</td>
    </tr>
  </tbody>
</table>

<h2 id="github-installation">GitHub Installation</h2>

<h3 id="authorize-and-install">Authorize and Install the DryRun Security GitHub Application</h3>

<p><strong>Note:</strong> You must be signed in as an organization admin (or an enterprise admin, if your organization is part of a GitHub Enterprise account) to install the GitHub App.</p>

<ol>
  <li>
    <p>Navigate to <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a> and click the <strong>Log in with GitHub</strong> button.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/01-login.png" alt="DryRun Security Login page" loading="lazy"></figure>
  </li>
  <li>
    <p>Log in to the GitHub account where DryRun Security will be installed.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/02-github-login.png" alt="GitHub Login for DryRun Security" loading="lazy"></figure>
  </li>
  <li>
    <p>Authorize the DryRun Security GitHub Application by clicking the <strong>Authorize DryRunSecurity</strong> button.</p>
    <p><strong>Note:</strong> This is a standard authorization screen for all applications in GitHub.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/06-github-authorize.png" alt="Authorize DryRun Security on GitHub" loading="lazy"></figure>
  </li>
  <li>
    <p>You'll be redirected to the DryRun Security portal. Click the <strong>Install</strong> button.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/04-install.png" alt="DryRun Security Install button" loading="lazy"></figure>
  </li>
  <li>
    <p>Click the <strong>Install</strong> button on the DryRunSecurity GitHub Application page.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/03-github-install.png" alt="DryRun Security GitHub Application install" loading="lazy"></figure>
  </li>
  <li>
    <p>Choose the GitHub repositories DryRun Security will run by selecting <strong>All Repositories</strong> or <strong>Only selected repositories</strong>.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/05-github-installation.png" alt="Select repositories for DryRun Security" loading="lazy"></figure>
  </li>
  <li>
    <p>After step one your installation may be paused for up to 2 business days as we activate your account.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/07-awaiting-activation.png" alt="DryRun Security awaiting account activation" loading="lazy"></figure>
  </li>
  <li>
    <p>Once your account has been activated, you'll see the <strong>Installation Complete</strong> message the next time you visit <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a>.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/08-installation-complete.png" alt="DryRun Security installation complete" loading="lazy"></figure>
  </li>
</ol>

<p><strong>Congratulations!</strong> Installation is complete. At this point DryRun Security will run checks on your repository as code is committed to Pull Requests.</p>

<h2 id="ghes-installation">GitHub Enterprise Server Installation</h2>

<p>DryRun Security supports on-premises GitHub Enterprise Server (GHES) installations. Setup requires a brief coordination with the DryRun Security team before installation can proceed.</p>

<h3>Step 1 - Initial Setup</h3>

<p>To get started, email <a href="mailto:hi@dryrun.security">hi@dryrun.security</a> with your <strong>Enterprise Profile URL</strong> (e.g., <code>https://github.yourcompany.com/enterprises/your-enterprise</code>).</p>

<p>DryRun Security will verify that your GitHub Enterprise Server is reachable at the provided URL before installation can proceed. Once confirmed, DryRun Security will follow up with next steps.</p>

<p><strong>Note:</strong> If your instance is not yet publicly accessible to DryRun Security over HTTPS, reach out and we can discuss connectivity options for your environment before moving forward.</p>

<h3>Step 2 - Create the GitHub App</h3>

<p>DryRun Security will send you a link to begin installation. When you open it, you will see a Webhook Secret and a <strong>Create GitHub App</strong> button.</p>

<ol>
  <li>Copy the Webhook Secret shown on the page - you will need to paste it into the GitHub App during creation</li>
  <li>Click <strong>Create GitHub App</strong> - this opens the GitHub App creation page in your GHES instance with DryRun Security's configuration pre-filled</li>
  <li>Paste the Webhook Secret into the Webhook Secret field in the GitHub App creation form</li>
  <li>
    <p>Click <strong>Create GitHub App</strong> on GitHub to complete the creation</p>
    <p><strong>Note:</strong> Depending on your GHES version, you may see a radio button at the bottom of the creation page to install this app for <strong>Any organization and any user</strong>. If present, select this option to ensure the app is available across your enterprise and not limited to the user creating it.</p>
  </li>
  <li>Return to the DryRun Security setup page and click <strong>I've created my App - Continue to Step 2</strong></li>
</ol>

<h3>Step 3 - Enter App Credentials</h3>

<p>Step 2 of the DryRun Security setup asks for credentials from the GitHub App you just created. In your GHES GitHub App settings page:</p>

<ol>
  <li>Copy the <strong>App ID</strong> and <strong>Client ID</strong> shown at the top of the page</li>
  <li>Click <strong>Generate a new client secret</strong> and copy the value</li>
  <li>Scroll to the bottom of the settings page and click <strong>Generate a private key</strong> - this downloads a <code>.pem</code> file</li>
</ol>

<p>Return to the DryRun Security setup page and fill in the App ID, Client ID, and Client Secret fields, then upload the <code>.pem</code> file. Click <strong>Submit</strong>. Once complete, you can install DryRun Security on your repositories.</p>

<h3>Step 4 - Install on Repositories</h3>

<ol>
  <li>
    <p>Navigate to <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a> and select your corporate organization from the org picker. The org picker may default to your personal GitHub account - make sure the correct enterprise organization is selected before proceeding.</p>
  </li>
  <li>
    <p>Click the <strong>Install</strong> button.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/04-install.png" alt="DryRun Security Install button" loading="lazy"></figure>
  </li>
  <li>
    <p>Click the <strong>Install</strong> button on the DryRunSecurity GitHub Application page.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/03-github-install.png" alt="DryRun Security GitHub Application install" loading="lazy"></figure>
  </li>
  <li>
    <p>Choose the GitHub repositories DryRun Security will run by selecting <strong>All Repositories</strong> or <strong>Only selected repositories</strong>.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/05-github-installation.png" alt="Select repositories for DryRun Security" loading="lazy"></figure>
  </li>
  <li>
    <p>After installation your account may be paused for up to 2 business days as we activate your account.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/07-awaiting-activation.png" alt="DryRun Security awaiting account activation" loading="lazy"></figure>
  </li>
  <li>
    <p>Once your account has been activated, you'll see the <strong>Installation Complete</strong> message the next time you visit <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a>.</p>
    <figure class="docs-screenshot"><img src="{asset_prefix}assets/images/install/08-installation-complete.png" alt="DryRun Security installation complete" loading="lazy"></figure>
  </li>
</ol>

<p><strong>Congratulations!</strong> Installation is complete. DryRun Security will run checks on your repositories as code is committed to Pull Requests.</p>

<h2 id="gitlab-installation">GitLab Installation</h2>

<p>DryRun Security for GitLab.com enables fast, contextual code reviews that help your team spot unknown risks before they start.</p>

<p>This guide will walk you through connecting your GitLab environment to DryRun Security by:</p>

<ul>
  <li>Creating a GitLab Group Access Token with the correct scopes.</li>
  <li>Installing DryRun Security via the DryRun Security Dashboard.</li>
</ul>

<p>Once installed and activated, you&#x27;ll get immediate visibility into security risks across your GitLab projects, without slowing development down.</p>

<h3 id="create-a-group-access-token">Create a Group Access Token</h3>

<p>This section describes creating a Group Access Token that will be used during the installation of DryRun Security. Creating a Group Access Token requires <strong>System Administrator</strong> or <strong>Group Owner</strong> permissions.</p>

<h4 id="generating-the-group-access-token">Generating the Group Access Token</h4>

<ol>
  <li>Log in to <a href="https://gitlab.com" target="_blank" rel="noopener noreferrer">gitlab.com</a>.</li>
  <li>Navigate to the Group where DryRun Security will be installed.</li>
  <li>Go to <strong>Settings &gt; Access Tokens</strong>.</li>
  <li>Click <strong>Add new token</strong>.</li>
  <li>Add a token name, set the role to at least <strong>Maintainer</strong>, and select the <code>api</code> scope.</li>
  <li>Click <strong>Create group access token</strong>.</li>
  <li>Copy the token and save it for later use.</li>
</ol>

<p>Done! The Group Access Token can be used to install DryRun Security.</p>

<h3 id="install-via-dashboard">Install DryRun Security via the Dashboard</h3>

<ol>
  <li>Navigate to <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a> and click the <strong>Log in with GitLab</strong> button.</li>
  <li>Authorize the DryRun Security OAuth Application.</li>
</ol>

<p><strong>Important:</strong> Choose the User or Group where DryRun Security will run from the User/Group Selector. This is usually a Group.</p>

<ol start="3">
  <li>Click the <strong>Add Token</strong> button or navigate to <strong>Settings &gt; GitLab</strong>.</li>
  <li>Enter the Group Access Token created earlier and click <strong>Save Token</strong>.</li>
  <li>Verify the User/Group for the Installation and click <strong>Confirm</strong> to confirm API access.</li>
  <li>Install on Projects by clicking <strong>+</strong> next to the Project and then click <strong>Save Projects</strong>.</li>
</ol>

<h4 id="activation">Activation</h4>

<p>Your installation may be paused for up to 2 business days as we activate your account. We&#x27;ll notify you as soon as your account has been activated.</p>

<p>Once your account has been activated, you&#x27;ll see the <strong>Installation Complete</strong> message the next time you log in to the portal at <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a>.</p>

<p><strong>Congratulations!</strong> Installation is complete.</p>

<p><strong>Note:</strong> At this point the DryRun Security application will run and analyze changes as code is committed to the Project(s).</p>


<h2 id="references">References</h2>

<ul>
  <li><a href="./pr-scanning">PR Code Reviews</a> - understand how DryRun Security analyzes your pull requests.</li>
  <li><a href="./pr-scanning-configuration">Configurations</a> - customize which agents and policies run on each repository.</li>
  <li><a href="./custom-code-policies">Custom Code Policies</a> - create custom security rules in plain English.</li>
</ul>
''',
}


# -- Scanning --

PAGES['deepscan'] = {
    'title': 'Repository Scanning with DeepScan',
    'description': 'DeepScan analyzes your entire codebase, not just recent pull requests, to find vulnerabilities that accumulate over time.',
    'section': 'Scanning',
    'content': '''
<h2 id="what-is-deepscan">What Is DeepScan?</h2>

<p>DryRun Security's standard PR Code Review analyzes changes as they arrive in each pull request. This is highly effective for catching new vulnerabilities before they merge, but it doesn't address risk that was already present in the codebase before DryRun Security was installed - or vulnerabilities that were introduced gradually across many small commits.</p>

<p><strong>DeepScan</strong> solves this by triggering a full-repository analysis. Rather than examining a diff, DeepScan ingests and analyzes the complete codebase, tracing data flows across files, identifying vulnerable patterns in legacy code, and surfacing risks that would never appear in a PR-only workflow.</p>

<h2 id="when-to-use-deepscan">When to Use DeepScan</h2>

<p>DeepScan is most valuable in several scenarios:</p>

<ul>
  <li><strong>Initial onboarding</strong> - Run a DeepScan when first connecting a repository to DryRun Security to establish your baseline security posture.</li>
  <li><strong>After a security incident</strong> - Use DeepScan to sweep a repository for related vulnerabilities after a finding is reported.</li>
  <li><strong>Compliance and audit preparation</strong> - Generate a comprehensive findings report for auditors or regulators who need evidence of security review.</li>
  <li><strong>Periodic security reviews</strong> - Schedule DeepScans on a regular cadence to catch drift and regression that PR-level analysis might miss across long periods.</li>
  <li><strong>Major refactors or dependency upgrades</strong> - When significant portions of the codebase change outside of a single PR, DeepScan ensures the full scope of changes is reviewed.</li>
</ul>

<h2 id="triggering-a-deepscan">Triggering a DeepScan</h2>

<ol>
  <li>Log in to the <strong>DryRun Security Dashboard</strong>.</li>
  <li>Navigate to the <strong>DeepScan</strong> page.</li>
  <li>Click <strong>&ldquo;New Scan&rdquo;</strong>.</li>
  <li>Select the repository and branch if desired.</li>
  <li>Monitor scan progress on the <strong>DeepScan</strong> page.</li>
</ol>

<h2 id="deepscan-workflow">DeepScan Workflow</h2>

<ol>
  <li><strong>Understand the codebase</strong> - Profile the app&rsquo;s language, frameworks, components, and data stores.</li>
  <li><strong>Gather security-relevant info</strong> - Map routes, auth files, configs, and authorization patterns.</li>
  <li><strong>Plan the review</strong> - Generate a targeted attack plan for each security domain.</li>
  <li><strong>Run the reviews</strong> - Analyze each domain (auth, injection, crypto, config, SCA, etc.) and log findings.</li>
  <li><strong>Clean up the report</strong> - Calibrate severities, remove hallucinations, deduplicate, and add exec summary and recommendations.</li>
  <li><strong>Publish and triage</strong> - Findings land in the dashboard where users can categorize and annotate each one.</li>
</ol>

<h2 id="deepscan-findings">DeepScan Findings</h2>

<p>There are two ways to review findings from a completed DeepScan:</p>

<h3 id="option-1-risk-register">Option 1 - Risk Register</h3>

<p>Filter the <a href="./risk-register">Risk Register</a> by DeepScan to see all findings surfaced by DeepScan across repositories. This gives a unified view alongside PR scan findings for triage and prioritization.</p>

<h3 id="option-2-deepscan-page">Option 2 - DeepScan Page</h3>

<p>From the DeepScan page, click on a previously scanned repository to see findings from the latest scan. A severity summary at the top shows counts across Critical, High, Medium, and Low. Previous scans can be reviewed by date, and findings can be filtered by risk level, SCA, or dismissed status.</p>
<p>Clicking on an individual finding opens a pop-out module with the finding detail, the DeepScan summary, and any artifact files. The Scan Details view provides the full scan report and includes a report download option.</p>

<h2 id="vulnerability-categories">Vulnerability Categories</h2>

<p>DeepScan detects a broad set of vulnerability categories across your codebase. For the complete list of all finding types surfaced by DeepScan, PR scanning, and SCA, see the <a href="./vulnerability-coverage-matrix">Vulnerability Coverage Matrix</a>.</p>

<h2 id="supported-languages">Supported Languages</h2>

<p>DeepScan supports a wide range of languages and frameworks. For the full list including PR scanning and SCA ecosystem coverage, see <a href="./language-support">Language and Framework Support</a>.</p>

<h2 id="behavioral-analysis">Git Behavioral Analysis</h2>

<p class="lead">DryRun Security constructs a <strong>Git Behavioral Graph</strong> before its AI agent reads a single line of code - analyzing commit history across five behavioral axes to steer the scanner toward the code that matters most.</p>

<div class="callout callout-info">
<p>The techniques described here are grounded in Adam Tornhill's <em>Your Code as a Crime Scene</em> (2nd ed., Pragmatic Programmers, 2024). DryRun Security engineered these forensic principles into a pipeline that steers an AI agent with deterministic precision. <a href="https://www.dryrun.security/blog/steering-agentic-security-scanners-with-git-behavioral-graphs" target="_blank" rel="noopener noreferrer">Read the full blog post</a> for additional context.</p>
</div>

<h3 id="why-git-history-matters">Why Git History Matters for Security</h3>

<p>Traditional static analysis lacks a fundamental dimension of context: the human element. Vulnerabilities are rarely just syntactical errors - they are the byproduct of diffuse ownership, shifting requirements, and knowledge decay. The Git Behavioral Graph provides a deterministic, high-signal heuristic to prioritize the agent's attention before it reads any code.</p>

<h3 id="five-behavioral-axes">The Five Behavioral Axes</h3>

<ul>
  <li><strong>Code churn</strong> - Files with high revision counts and many distinct contributors historically correlate with vulnerability density. The pipeline quantifies this as a normalized churn score.</li>
  <li><strong>Contributor coupling</strong> - When many authors touch the same file, implicit knowledge can be lost. The ratio of unique contributors to total revisions produces a diffuse-ownership signal.</li>
  <li><strong>Temporal coupling</strong> - Files that change together frequently suggest hidden dependencies. If a change to <code>auth_middleware.py</code> always accompanies changes to <code>session_handler.py</code>, a change to one without the other is suspicious.</li>
  <li><strong>Recency weighting</strong> - Recent changes carry more risk than ancient stable code. The pipeline applies exponential decay weighting so churn from last week outweighs churn from last year.</li>
  <li><strong>Complexity hotspot scoring</strong> - Combining churn and contributor metrics with code complexity produces composite hotspot scores that identify the files most likely to harbor latent vulnerabilities.</li>
</ul>
''',
}

PAGES['pr-scanning'] = {
    'title': 'PR Scanning',
    'description': 'Understand how DryRun Security automatically analyzes your pull requests for security vulnerabilities.',
    'section': 'Scanning',
    'content': '''
<h2 id="how-it-works">How It Works</h2>

<p>DryRun Security analyzes code changes every time a pull request is opened or updated. Its security agents inspect the diff, evaluate the surrounding context, and report findings directly on the PR - before the code is merged. Each finding is evaluated for impact and exploitability and tagged with a severity: Critical, High, Medium, or Low. Scanning runs automatically with no manual steps required: open a PR and DryRun Security handles the rest.</p>

<p>Results appear as a summary comment on the pull request, inline comments on specific lines, and a pass/fail check status that integrates with your branch protection rules. This keeps security feedback inside the developer workflow where it can be acted on immediately.</p>

<h2 id="supported-platforms">Supported Platforms</h2>

<p>DryRun Security integrates natively with GitHub, GitLab, and GitHub Enterprise Server (GHES), covering both cloud-hosted and self-managed source code platforms:</p>

<table>
  <thead>
    <tr>
      <th>Platform</th>
      <th>Trigger</th>
      <th>Check Status</th>
      <th>Inline Comments</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>GitHub</td>
      <td>Pull request opened or synchronized</td>
      <td>GitHub Checks API</td>
      <td>PR review comments on affected lines</td>
    </tr>
    <tr>
      <td>GitLab</td>
      <td>Merge request opened or updated</td>
      <td>GitLab pipeline status</td>
      <td>Merge request discussion comments</td>
    </tr>
    <tr>
      <td>GitHub Enterprise Server (GHES)</td>
      <td>Pull request opened or synchronized</td>
      <td>GitHub Checks API</td>
      <td>PR review comments on affected lines</td>
    </tr>
  </tbody>
</table>

<h2 id="what-gets-analyzed">What Gets Analyzed</h2>

<p>When a pull request is opened, DryRun Security retrieves the diff along with relevant surrounding code context - imported modules, authentication middleware, framework conventions, and any configured security policies. Analysis is scoped to the changed regions and the code paths that flow through them.</p>

<p>DryRun Security also reads the repository's <code>agents.md</code> file, if present. This allows teams to provide context and instructions that guide the security analysis - such as project-specific conventions, known safe patterns, or areas of particular concern.</p>

<p>The following security agents run on every PR scan:</p>

<ul>
  <li><strong>Cross-Site Scripting Analyzer</strong></li>
  <li><strong>General Security Analyzer</strong></li>
  <li><strong>IDOR Analyzer</strong></li>
  <li><strong>Mass Assignment</strong></li>
  <li><strong>Secrets Analyzer</strong></li>
  <li><strong>Server-Side Request Forgery Analyzer</strong></li>
  <li><strong>SQL Injection Analyzer</strong></li>
  <li>Any <a href="./custom-code-policies">custom code policies</a> created by your team</li>
</ul>

<p>All findings are filtered to the changed regions of the pull request. Pre-existing issues in unchanged code are excluded from the results so developers can focus on what they introduced.</p>

<h2 id="check-status-and-feedback">Check Status & Feedback</h2>

<p>DryRun Security reports results through two channels: a <strong>summary comment</strong> on the pull request with an overview of all findings, and individual <strong>check statuses</strong> that integrate with your branch protection rules.</p>

<p>Each check corresponds to a specific security agent or policy. The check status reflects the outcome of that agent's analysis:</p>

<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Meaning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Success</strong></td>
      <td>No findings at or above the configured severity threshold. The PR is clear to merge.</td>
    </tr>
    <tr>
      <td><strong>Failure</strong></td>
      <td>One or more findings meet or exceed the blocking threshold. The PR cannot be merged until issues are resolved.</td>
    </tr>
  </tbody>
</table>

<p>When findings are detected, inline comments are posted directly on the affected lines of code with a description of the vulnerability and remediation guidance. For details on enforcing merge gates with check statuses, see <a href="./pr-blocking">PR Blocking</a>.</p>

<p>If you are seeing noisy or irrelevant findings, you can <a href="./finding-tuning">tune your findings</a> to reduce noise and focus on the issues that matter most to your team.</p>

<h2 id="configuration">Configuration</h2>

<p>PR scanning behavior is controlled through configurations in the DryRun Security dashboard. Each configuration can be applied to one or more repositories, and a <code>default</code> configuration covers any repository not assigned to a specific one.</p>

<table>
  <thead>
    <tr>
      <th>Setting</th>
      <th>Default</th>
      <th>What It Controls</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Security Agents</td>
      <td>All enabled</td>
      <td>Which code security analyzers (XSS, SQLi, IDOR, Secrets, etc.) run on PRs</td>
    </tr>
    <tr>
      <td>Custom Code Policies</td>
      <td>None attached</td>
      <td>Organization-specific rules written in plain English, enforced on every PR</td>
    </tr>
    <tr>
      <td>PR Blocking</td>
      <td>Disabled</td>
      <td>Whether findings at a given severity fail the check status and prevent merge</td>
    </tr>
    <tr>
      <td>Blocking Threshold</td>
      <td>High</td>
      <td>Minimum severity level (Critical, High, Medium, Low) that triggers a failed check</td>
    </tr>
    <tr>
      <td>PR Issue Comments</td>
      <td>Enabled</td>
      <td>Whether DryRun Security posts a summary comment and inline findings on the PR</td>
    </tr>
    <tr>
      <td>Notifications</td>
      <td>Disabled</td>
      <td>Alerts sent via Slack or webhook when findings are detected</td>
    </tr>
  </tbody>
</table>

<p>Configurations follow an inheritance model: the <code>default</code> configuration applies to all repositories, and repository-specific configurations override it. This lets you set organization-wide baselines while customizing behavior for individual repositories or teams.</p>

<p>See <a href="./pr-scanning-configuration">PR Scanning Configuration</a> for a full walkthrough of creating and managing configurations.</p>

<h2 id="pr-scanning-vs-deepscan">How PR Scanning Differs From DeepScan</h2>

<p>DryRun Security offers two scanning modes. PR Scanning analyzes changes as they arrive in pull requests. <a href="./deepscan">DeepScan</a> performs a full-repository analysis to find vulnerabilities in existing code. The two modes are complementary:</p>

<table>
  <thead>
    <tr>
      <th>Aspect</th>
      <th>PR Scan</th>
      <th>DeepScan</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Scope</td>
      <td>Changed files and surrounding context in the PR</td>
      <td>Entire repository codebase</td>
    </tr>
    <tr>
      <td>Trigger</td>
      <td>Automatic on PR open or update</td>
      <td>Manual or scheduled from the dashboard</td>
    </tr>
    <tr>
      <td>Speed</td>
      <td>Seconds to minutes, depending on diff size</td>
      <td>Minutes to hours, depending on repo size</td>
    </tr>
    <tr>
      <td>Differential Analysis</td>
      <td>Yes - only new findings from the PR are reported</td>
      <td>No - all findings in the codebase are reported</td>
    </tr>
    <tr>
      <td>Results Location</td>
      <td>PR comments, inline annotations, check statuses, and the DryRun Security dashboard</td>
      <td>DryRun Security dashboard and Risk Register</td>
    </tr>
    <tr>
      <td>Best For</td>
      <td>Catching new vulnerabilities before merge</td>
      <td>Baseline assessment, audits, and legacy code review</td>
    </tr>
  </tbody>
</table>

<h2 id="supported-languages">Supported Languages</h2>

<p>PR scanning supports the same languages and frameworks as DeepScan. For the full list, see <a href="./language-support">Language and Framework Support</a>.</p>

<h2 id="vulnerability-categories">Vulnerability Categories</h2>

<p>PR scanning can detect a broad set of vulnerability categories. For the complete system-wide reference, see the <a href="./vulnerability-coverage-matrix">Vulnerability Coverage Matrix</a>.</p>

''',
}

PAGES['secrets-scanning'] = {
    'title': 'Secrets Scanning',
    'description': 'How DryRun Security detects hardcoded credentials, API keys, tokens, and other secrets in your codebase.',
    'section': 'Scanning',
    'content': '''
<h2 id="the-secrets-analyzer">The Secrets Analyzer</h2>

<p>Hardcoded credentials are among the most common and most exploitable security vulnerabilities in modern software. API keys, database passwords, authentication tokens, and private keys committed to source code are routinely discovered by attackers scanning public repositories - and by insiders with unintended access to private ones.</p>

<p>DryRun Security's <strong>Secrets Analyzer</strong> is a specialized agent that runs on every pull request, examining code changes for signs of embedded credentials. Unlike tools that rely solely on pattern matching, the Secrets Analyzer goes a critical step further: it attempts to <strong>validate detected secrets</strong> to determine whether they are real and currently active. This verification step is a key differentiator - rather than flooding teams with alerts for every string that resembles a credential, DryRun Security confirms which secrets pose a genuine risk by testing them against the services they are meant to authenticate with.</p>

<p>The analyzer also operates contextually, evaluating whether a candidate secret is genuine based on its surrounding context, variable naming, usage patterns, and code structure. Combined with active validation, this approach dramatically reduces false positives while ensuring that truly dangerous credentials are caught before they reach production.</p>

<h2 id="what-secrets-detection-covers">What Secrets Detection Covers</h2>

<p>The Secrets Analyzer detects a wide range of credential types, including:</p>

<ul>
  <li>API keys and access tokens for cloud providers (AWS, GCP, Azure) and third-party services</li>
  <li>Database connection strings with embedded credentials</li>
  <li>Private keys (RSA, EC, SSH)</li>
  <li>Authentication tokens and session secrets</li>
  <li>OAuth client secrets</li>
  <li>Webhook secrets and signing keys</li>
  <li>Generic high-entropy strings that exhibit the statistical properties of cryptographic secrets</li>
</ul>

''',
}

PAGES['iac-scanning'] = {
    'title': 'IaC Scanning',
    'description': 'DryRun Security scans Terraform configurations for security misconfigurations and insecure defaults in pull requests.',
    'section': 'Scanning',
    'content': '''
<h2 id="overview">Overview</h2>

<p>DryRun Security provides Infrastructure as Code scanning focused on Terraform configurations. When a pull request modifies <code>.tf</code> files, DryRun Security analyzes the changes for security misconfigurations and flags findings as part of its <a href="pr-scanning.html">PR scanning</a> workflow.</p>

<h2 id="what-it-detects">What It Detects</h2>

<p>IaC scanning identifies common Terraform security issues including:</p>

<ul>
  <li><strong>Overly permissive IAM policies</strong> - Roles granting broader access than required, violating least privilege</li>
  <li><strong>Exposed resources</strong> - Security groups, firewall rules, or storage buckets with unintended public access</li>
  <li><strong>Insecure defaults</strong> - Unencrypted data stores, disabled logging, or missing audit trails</li>
  <li><strong>Subdomain takeover risks</strong> - Dangling DNS records or CDN configurations that could be claimed by an attacker</li>
</ul>

<p>Beyond the built-in IaC checks, teams can use <a href="./custom-code-policies">Custom Code Policies</a> to monitor additional infrastructure concerns. Custom policies let you enforce specific configuration requirements, flag unapproved resource types, or define any other infrastructure rules that matter to your organization. This extends IaC coverage to match your team's specific infrastructure security requirements.</p>

<h2 id="how-findings-appear">How Findings Appear</h2>

<p>IaC findings are reported the same way as other DryRun Security results: as comments on pull requests and as entries in the <a href="risk-register.html">Risk Register</a> dashboard. Each finding includes the affected resource, a description of the risk, and guidance on remediation.</p>
''',
}

PAGES['sca'] = {
    'title': 'SCA',
    'description': 'Dependency scanning and supply chain risk detection - find vulnerable third-party packages before they reach production.',
    'section': 'Scanning',
    'content': '''
<h2 id="what-is-sca">What Is SCA</h2>

<p>Software Composition Analysis (SCA) identifies the third-party libraries and open-source packages your application depends on and checks whether any carry known security vulnerabilities. The majority of code in any production service comes from the open-source ecosystem, making dependency risk one of the most important areas to monitor.</p>

<p>DryRun Security checks each dependency against known vulnerability databases, matching specific CVEs to affected version ranges across all major package ecosystems.</p>

<h2 id="how-scanning-works">How Scanning Works</h2>

<p>DryRun Security runs SCA through two paths:</p>

<p><strong>DeepScan</strong> - When a DeepScan is triggered from the dashboard, SCA runs as part of that scan, analyzing dependency manifests and lock files across the entire codebase at that point in time. This is the on-demand path for getting a current snapshot of supply chain risk whenever you need it.</p>

<p><strong>Automatic background scanning</strong> - DryRun Security also scans active repositories automatically in the background to keep SCA findings current without requiring a manual trigger. Scan frequency is based on PR activity, so the most active repositories are kept up to date most often. See Scan Schedule below.</p>

<h2 id="scan-schedule">Scan Schedule</h2>

<p>Automatic SCA scans are scheduled based on repository PR activity over the last 30 days:</p>

<table>
  <thead><tr><th>Activity</th><th>Frequency</th></tr></thead>
  <tbody>
    <tr><td>High activity</td><td>Daily</td></tr>
    <tr><td>Moderate activity</td><td>Weekly to bi-weekly</td></tr>
    <tr><td>Low activity</td><td>Monthly</td></tr>
    <tr><td>Inactive (fewer than 3 PRs in 30 days)</td><td>No automatic scan</td></tr>
  </tbody>
</table>

<p>Repositories that fall below the activity threshold do not receive automatic scans. Run a DeepScan manually from the dashboard to get current SCA findings for an inactive repository.</p>

<h2 id="whats-checked">What&rsquo;s Checked</h2>

<p>DryRun Security scans package manifests and lock files across all major ecosystems:</p>

<ul>
  <li><strong>JavaScript / Node.js</strong> - <code>package-lock.json</code>, <code>yarn.lock</code></li>
  <li><strong>Python</strong> - <code>requirements.txt</code>, <code>Pipfile</code>, <code>pyproject.toml</code>, <code>poetry.lock</code>, <code>uv.lock</code></li>
  <li><strong>Ruby</strong> - <code>Gemfile</code>, <code>Gemfile.lock</code></li>
  <li><strong>Java / Kotlin</strong> - <code>pom.xml</code>, <code>gradle.lockfile</code>, <code>buildscript-gradle.lockfile</code>, <code>gradle/verification-metadata.xml</code></li>
  <li><strong>Go</strong> - <code>go.mod</code></li>
  <li><strong>Rust</strong> - <code>Cargo.lock</code></li>
  <li><strong>.NET</strong> - <code>*.csproj</code>, <code>deps.json</code>, <code>packages.config</code>, <code>packages.lock.json</code></li>
  <li><strong>PHP</strong> - <code>composer.lock</code></li>
</ul>

<p><strong>Note:</strong> For Gradle projects, SCA requires a committed dependency lock file. Standard Gradle build files (<code>build.gradle</code>, <code>settings.gradle</code>) are not used for dependency resolution. <code>gradle.lockfile</code> and <code>buildscript-gradle.lockfile</code> are supported at any directory level; <code>gradle/verification-metadata.xml</code> is only read from the repository root.</p>

<h2 id="viewing-findings">Viewing Findings</h2>

<p>SCA findings are available in three places in the DryRun Security dashboard:</p>

<ul>
  <li><strong>Risk Register</strong> - Filter by SCA agent type to see all dependency findings across repositories, alongside PR scan and DeepScan results.</li>
  <li><strong>Repository pages</strong> - SCA findings for a specific repository are visible from that repository&rsquo;s detail page in the dashboard.</li>
  <li><strong>DeepScan page</strong> - SCA findings from a DeepScan run are included in the results and can be filtered separately.</li>
</ul>

<h2 id="sbom">SBOM</h2>

<p>SCA findings feed into SBOM (Software Bill of Materials) generation. DryRun Security generates a complete inventory of your software dependencies from both DeepScan and automatic background scans, which can be downloaded for compliance and audit purposes via the <a href="./dryrun-api">DryRun Security API</a>.</p>
''',
}

PAGES['auto-fix'] = {
    'title': 'Auto Fix',
    'description': 'Automated remediation guidance and fix verification for security findings.',
    'section': 'Scanning',
    'content': '''
<h2 id="why-implement-auto-fix">Why Implement Auto Fix</h2>

<p>Automating security fixes delivers measurable value across your development organization:</p>

<ul>
  <li><strong>Speed of deployment</strong> - Fixing vulnerabilities faster means shipping faster</li>
  <li><strong>Reduced time-to-remediation</strong> - Vulnerabilities are resolved quickly rather than sitting in backlogs</li>
  <li><strong>Developer productivity</strong> - Developers spend less time on manual security fixes and more time building features</li>
  <li><strong>Consistent remediation</strong> - AI-powered fixes follow security best practices every time</li>
  <li><strong>Shift-left at scale</strong> - Security fixes happen as part of the development workflow, not as a separate process</li>
</ul>

<h2 id="how-dryrun-enables-auto-fix">How DryRun Enables Auto Fix with AI Coding</h2>

<p>DryRun Security enables auto fix by integrating with AI coding tools. Supported tools include:</p>

<ul>
  <li><strong>Claude Code</strong></li>
  <li><strong>Codex</strong></li>
  <li><strong>Cursor</strong></li>
  <li><strong>GitHub Copilot</strong></li>
  <li><strong>Windsurf</strong></li>
  <li><strong>VS Code</strong></li>
</ul>

<p>Auto fix is enabled by:</p>

<ol>
  <li>Creating an API key from the DryRun Security dashboard (see <a href="./api-access-keys">API Access Keys</a>)</li>
  <li>Connecting your AI coding tool to the DryRun Security <a href="./mcp">MCP (Model Context Protocol) server</a></li>
  <li>Installing the DryRun Security remediation skill: see the <a href="./dryrun-skill">DryRun Skill</a> page for instructions</li>
</ol>

<p>Once connected, the AI coding tool can read DryRun Security findings and automatically generate fixes in the context of your codebase.</p>
''',
}


PAGES['language-support'] = {
    'title': 'Language and Framework Support',
    'description': 'Languages, frameworks, and package ecosystems supported across all DryRun Security scanning capabilities.',
    'section': 'Scanning',
    'content': '''
<p>DryRun Security supports a broad range of languages, frameworks, and package ecosystems across its scanning capabilities. Coverage varies by scanning mode: PR scanning and DeepScan analyze source code, while SCA analyzes dependency manifests and lock files.</p>

<h2 id="pr-scanning-and-deepscan">PR Scanning and DeepScan</h2>

<p>Both <a href="./pr-scanning">PR scanning</a> and <a href="./deepscan">DeepScan</a> support the same set of programming languages and frameworks. The scanner automatically detects the language and framework in use during analysis and tailors its review accordingly.</p>

<table>
  <thead>
    <tr>
      <th>Language</th>
      <th>Frameworks and Runtimes</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>JavaScript / TypeScript</td><td>Node.js, React, Angular, Vue</td></tr>
    <tr><td>Python</td><td>Django, Flask, FastAPI</td></tr>
    <tr><td>Java</td><td>Spring, Jakarta EE</td></tr>
    <tr><td>Go</td><td></td></tr>
    <tr><td>Ruby</td><td>Rails, Sinatra</td></tr>
    <tr><td>PHP</td><td>Laravel, Symfony</td></tr>
    <tr><td>C#</td><td>.NET</td></tr>
    <tr><td>Kotlin</td><td></td></tr>
    <tr><td>Swift</td><td></td></tr>
    <tr><td>Rust</td><td></td></tr>
  </tbody>
</table>

<h2 id="sca-ecosystems">SCA: Dependency Ecosystems</h2>

<p><a href="./sca">Software Composition Analysis (SCA)</a> runs as part of DeepScan and scans package manifests and lock files across all major package ecosystems. Each dependency is checked against known vulnerability databases, matching specific CVEs to affected version ranges.</p>

<table>
  <thead>
    <tr>
      <th>Ecosystem</th>
      <th>Manifest and Lock Files</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>JavaScript / Node.js</td><td><code>package-lock.json</code>, <code>yarn.lock</code></td></tr>
    <tr><td>Python</td><td><code>requirements.txt</code>, <code>Pipfile</code>, <code>pyproject.toml</code>, <code>poetry.lock</code>, <code>uv.lock</code></td></tr>
    <tr><td>Ruby</td><td><code>Gemfile</code>, <code>Gemfile.lock</code></td></tr>
    <tr><td>Java / Kotlin</td><td><code>pom.xml</code>, <code>gradle.lockfile</code>, <code>buildscript-gradle.lockfile</code>, <code>gradle/verification-metadata.xml</code></td></tr>
    <tr><td>Go</td><td><code>go.mod</code></td></tr>
    <tr><td>Rust</td><td><code>Cargo.lock</code></td></tr>
    <tr><td>.NET</td><td><code>*.csproj</code>, <code>deps.json</code>, <code>packages.config</code>, <code>packages.lock.json</code></td></tr>
    <tr><td>PHP</td><td><code>composer.lock</code></td></tr>
  </tbody>
</table>

<h2 id="language-detection">Automatic Language Detection</h2>

<p>DryRun Security automatically detects languages and frameworks in use during scanning. No manual configuration is required: the scanner profiles the repository structure, file extensions, and framework conventions to tailor its security analysis to your specific stack.</p>

<p>For SCA, the scanner identifies all manifest and lock files present in the repository and checks each dependency against the appropriate vulnerability database for that ecosystem.</p>
''',
}

PAGES['vulnerability-coverage-matrix'] = {
    'title': 'Vulnerability Coverage Matrix',
    'description': 'All finding types detectable by DryRun Security across PR scanning, DeepScan, and SCA, with CWE mappings.',
    'section': 'Scanning',
    'content': '''
<p>DryRun Security detects vulnerabilities across three scanning modes: <a href="./pr-scanning">PR scanning</a>, <a href="./deepscan">DeepScan</a>, and <a href="./sca">SCA</a>. The categories below represent the full set of finding types surfaced across all scanning sources. CWE mappings are provided as reference anchors for each category.</p>

<h2 id="all-finding-types">All Finding Types</h2>

<table>
  <thead>
    <tr>
      <th>Category</th>
      <th>Description</th>
      <th>Example CWEs</th>
    </tr>
  </thead>
  <tbody>
    <tr><td>API Query Injection</td><td>Improper handling of user-controlled input in API queries that allows attackers to manipulate backend queries or filters.</td><td>CWE-943, CWE-74</td></tr>
    <tr><td>Authentication Bypass</td><td>Flaws that allow users to bypass authentication mechanisms and gain access without valid credentials.</td><td>CWE-287, CWE-306</td></tr>
    <tr><td>Missing Authorization Checks</td><td>Endpoints or functions that fail to enforce authorization, allowing users to access resources they should not.</td><td>CWE-862</td></tr>
    <tr><td>Business Logic Flaw</td><td>Errors in application logic that can be abused to gain unintended outcomes, even when traditional security controls are in place.</td><td>CWE-840</td></tr>
    <tr><td>Cache Poisoning</td><td>Manipulation of cache entries to serve malicious or incorrect content to other users.</td><td>CWE-444, CWE-113</td></tr>
    <tr><td>Configuration Injection</td><td>Injection of untrusted input into configuration files, environment variables, or runtime settings.</td><td>CWE-15, CWE-20</td></tr>
    <tr><td>Cryptographic Weakness</td><td>Use of weak, broken, or outdated cryptographic algorithms, keys, or practices.</td><td>CWE-327, CWE-326</td></tr>
    <tr><td>Cross-Site Request Forgery (CSRF)</td><td>Actions performed on behalf of an authenticated user without their consent due to missing or weak CSRF protections.</td><td>CWE-352</td></tr>
    <tr><td>CSV Injection</td><td>Injection of spreadsheet formulas into CSV exports that execute when opened in spreadsheet software.</td><td>CWE-1236</td></tr>
    <tr><td>Email Header Injection</td><td>Manipulation of email headers through unsanitized input, potentially enabling spam or phishing attacks.</td><td>CWE-93</td></tr>
    <tr><td>Excessive Privileges</td><td>Users, services, or tokens granted more permissions than required for their intended function.</td><td>CWE-250, CWE-269</td></tr>
    <tr><td>Hardcoded Credentials</td><td>Credentials such as passwords, API keys, or tokens embedded directly in source code.</td><td>CWE-798, CWE-259</td></tr>
    <tr><td>HTTP Header Injection</td><td>Injection of malicious content into HTTP headers due to improper input validation.</td><td>CWE-113, CWE-93</td></tr>
    <tr><td>Insecure Direct Object Reference (IDOR)</td><td>Direct access to internal objects using user-controlled identifiers without proper authorization checks.</td><td>CWE-639, CWE-284</td></tr>
    <tr><td>Information Disclosure</td><td>Exposure of sensitive data such as secrets, internal paths, stack traces, or system details.</td><td>CWE-200, CWE-209</td></tr>
    <tr><td>Insecure Client Storage</td><td>Sensitive data stored insecurely on the client side, such as in local storage or cookies.</td><td>CWE-922, CWE-312</td></tr>
    <tr><td>Insecure Defaults</td><td>Unsafe default configurations that weaken security if not explicitly changed.</td><td>CWE-276, CWE-1188</td></tr>
    <tr><td>Insecure Deserialization</td><td>Deserializing untrusted data in a way that allows code execution or data manipulation.</td><td>CWE-502</td></tr>
    <tr><td>Insecure File Upload</td><td>File upload functionality that allows malicious files or unrestricted file types.</td><td>CWE-434</td></tr>
    <tr><td>Insecure Transport</td><td>Use of unencrypted or improperly secured network communication channels.</td><td>CWE-319, CWE-295</td></tr>
    <tr><td>Intent Redirection</td><td>Unvalidated or unsafe redirection logic that can be abused to send users to unintended destinations specifically in mobile applications.</td><td>CWE-601</td></tr>
    <tr><td>Language Version Risk</td><td>Use of outdated or unsupported programming language versions with known security issues.</td><td>CWE-1104</td></tr>
    <tr><td>LLM Tool Misuse</td><td>Unsafe or unintended use of large language model tools, including insecure prompt handling or tool invocation.</td><td>CWE-20, CWE-74, CWE-1426</td></tr>
    <tr><td>Log Injection</td><td>Injection of untrusted input into logs that can mislead monitoring systems or hide malicious activity.</td><td>CWE-117</td></tr>
    <tr><td>Mass Assignment</td><td>Automatic binding of user input to object properties without restricting sensitive fields.</td><td>CWE-915</td></tr>
    <tr><td>Memory Safety Issue</td><td>Unsafe memory operations that can lead to crashes, data corruption, or code execution.</td><td>CWE-119, CWE-787, CWE-416</td></tr>
    <tr><td>Network Exposure</td><td>Unintended exposure of internal services, ports, or network resources.</td><td>CWE-668</td></tr>
    <tr><td>Open CORS Policy</td><td>Overly permissive Cross-Origin Resource Sharing policies that allow unintended access.</td><td>CWE-942</td></tr>
    <tr><td>Open Redirect</td><td>Redirects that accept untrusted input, enabling phishing or malicious redirection attacks.</td><td>CWE-601</td></tr>
    <tr><td>Path Traversal</td><td>Manipulation of file paths to access files or directories outside the intended scope.</td><td>CWE-22</td></tr>
    <tr><td>Privilege Escalation</td><td>Flaws that allow users or processes to gain higher privileges than intended.</td><td>CWE-269, CWE-284</td></tr>
    <tr><td>Prompt Injection</td><td>Manipulation of LLM prompts that alters behavior, bypasses safeguards, or leaks sensitive data.</td><td>CWE-77, CWE-74, CWE-913, CWE-1427</td></tr>
    <tr><td>Prototype Pollution</td><td>Modification of object prototypes that can impact application logic or security.</td><td>CWE-1321</td></tr>
    <tr><td>Remote Code Execution (RCE)</td><td>Flaws that allow attackers to execute arbitrary code on the host system.</td><td>CWE-94, CWE-78</td></tr>
    <tr><td>Resource Exhaustion</td><td>Operations that can be abused to consume excessive CPU, memory, or other resources.</td><td>CWE-400</td></tr>
    <tr><td>SQL Injection (SQLi)</td><td>Injection of malicious SQL queries through unsanitized input.</td><td>CWE-89</td></tr>
    <tr><td>Server-Side Request Forgery (SSRF)</td><td>Ability to make server-side requests to internal or unintended external resources.</td><td>CWE-918</td></tr>
    <tr><td>Subdomain Takeover</td><td>Dangling or misconfigured subdomains that can be claimed by attackers, as defined by Infrastructure as Code (IaC).</td><td>CWE-668, CWE-284</td></tr>
    <tr><td>Supply Chain Risk</td><td>Risks introduced through third-party libraries, dependencies, or external services.</td><td>CWE-1104, CWE-829</td></tr>
    <tr><td>Terminal Escape Injection</td><td>Injection of terminal control characters that can manipulate terminal output or behavior.</td><td>CWE-150, CWE-74</td></tr>
    <tr><td>Time-of-Check Time-of-Use (TOCTOU)</td><td>Race conditions where system state changes between validation and use.</td><td>CWE-367</td></tr>
    <tr><td>Timing Side Channel</td><td>Information leakage through measurable differences in execution time.</td><td>CWE-208</td></tr>
    <tr><td>UI Spoofing</td><td>User interface elements designed to deceive users into taking unintended actions.</td><td>CWE-451</td></tr>
    <tr><td>User Enumeration</td><td>Ability to determine valid users based on application responses.</td><td>CWE-203, CWE-204</td></tr>
    <tr><td>Vulnerable Dependency</td><td>Use of third-party dependencies with known security vulnerabilities.</td><td>CWE-937, CWE-1104</td></tr>
    <tr><td>XML Injection</td><td>Injection of malicious XML content that alters processing or behavior.</td><td>CWE-91</td></tr>
    <tr><td>Cross-Site Scripting (XSS)</td><td>Injection of malicious scripts that execute in a user&rsquo;s browser.</td><td>CWE-79</td></tr>
    <tr><td>XML External Entity (XXE)</td><td>XML parsing vulnerabilities that allow access to internal files or services.</td><td>CWE-611</td></tr>
  </tbody>
</table>
''',
}



# -- Code Security Intelligence (consolidated) --

PAGES['code-security-intelligence'] = {
    'title': 'Code Security Intelligence',
    'description': 'DryRun Security builds an intelligence layer on top of vulnerability findings and scan data, enabling actionable security workflows across your codebase and development organization.',
    'section': 'Platform',
    'content': '''
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/code-security-intelligence/01-csi-architecture.jpg" alt="Code Security Intelligence architecture diagram showing sources, the DryRun intelligence layer, access methods, and intelligence workflows" loading="lazy"></figure>

<h2 id="overview">Overview</h2>

<p>DryRun Security takes vulnerability scanning to the next level by building an intelligence layer on top of all the finding data and trends from <a href="./pr-scanning">PR scanning</a> and <a href="./deepscan">DeepScan</a>. This intelligence layer is actionable and enables AppSec teams to do meaningful security work beyond just reviewing individual findings, surfacing trends, patterns, risks, and insights across the entire codebase and development organization.</p>

<p>Every pull request DryRun Security reviews and every DeepScan contributes to a structured, queryable intelligence index. This index powers a range of security workflows that would otherwise require manual data collection, spreadsheet tracking, and cross-referencing multiple tools.</p>

<h2 id="intelligence-workflows">Intelligence Workflows</h2>

<p>The intelligence layer enables a range of security workflows. Each workflow draws on the findings and scan data DryRun Security continuously collects across your repositories.</p>

<div class="table-wrap">
<table>
  <thead>
    <tr>
      <th>Workflow</th>
      <th>What It Shows</th>
      <th>Example Use Case</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Feature Ships</td>
      <td>Security posture of features shipped in a sprint or release, with risk annotations and PR links</td>
      <td>Summarize the security status of features shipped this sprint for a release review</td>
    </tr>
    <tr>
      <td>Resolved Risk</td>
      <td>Pull requests from the last 30 days that were merged after an identified risk was resolved, with links to the PR and the resolution</td>
      <td>Confirm that all findings identified in last sprint&rsquo;s merged PRs were addressed before a release</td>
    </tr>
    <tr>
      <td>Vulnerability Trends</td>
      <td>Trending vulnerability patterns and coverage data across repos over time, including OWASP Top 10 mapping</td>
      <td>Compare critical finding counts quarter over quarter to measure security program effectiveness</td>
    </tr>
    <tr>
      <td>Architecture Risks</td>
      <td>Structural risk patterns in the codebase, including trust boundary changes, auth drift, and data flow modifications</td>
      <td>Identify new unauthenticated endpoints or service-to-service communication paths added this month</td>
    </tr>
    <tr>
      <td>Developer Trends</td>
      <td>Which teams or repos have recurring finding patterns, remediation velocity, and code change activity</td>
      <td>Determine which teams would benefit most from targeted security training based on finding patterns</td>
    </tr>
    <tr>
      <td>Shadow AI</td>
      <td>AI and LLM usage detected across the codebase: tool fingerprints, code pattern analysis, and volume anomalies</td>
      <td>Audit all AI-generated code contributions in security-critical paths for governance reporting</td>
    </tr>
    <tr>
      <td>Incident Response</td>
      <td>Queryable record of code changes, findings, and triage decisions for rapid incident investigation</td>
      <td>Trace which PR introduced a vulnerable dependency and assess blast radius during an active incident</td>
    </tr>
    <tr>
      <td>Application Summary</td>
      <td>Security profile of a specific service or application: open findings, scan coverage, and risk trends</td>
      <td>Generate an application security profile for a new team member onboarding onto a service</td>
    </tr>
    <tr>
      <td>Security Reviews</td>
      <td>Contextual security analysis results, business logic detection, and multi-model verification insights</td>
      <td>Investigate which findings required cross-file analysis to detect and would be missed by pattern matchers</td>
    </tr>
    <tr>
      <td>New Feature/Repo Review</td>
      <td>Precedent-based risk assessment for new features or repositories using historical findings</td>
      <td>Before building a new payment integration, review security findings from similar past implementations</td>
    </tr>
    <tr>
      <td>PR Variant Analysis</td>
      <td>Deep investigation of individual PR findings using the Insights AI assistant</td>
      <td>Click &ldquo;Investigate&rdquo; on a finding to explore its security implications interactively</td>
    </tr>
  </tbody>
</table>
</div>

<h2 id="how-to-access-insights">How to Access Insights</h2>

<p>Users interact with these intelligence capabilities through the <strong>Insights</strong> page in the DryRun Security dashboard in two ways:</p>

<h3 id="ai-assistant">AI Assistant</h3>

<p>The Insights page has an AI assistant chat interface. Users can interact with it to generate security reports, feature ship summaries, risk assessments, and more, all grounded in real DryRun Security findings data. Simply describe what you want (e.g., &ldquo;Create a security summary for the features shipped this week&rdquo;) and the assistant generates it from your actual scan data.</p>

<p>Example prompts:</p>

<ul>
  <li>&ldquo;What features shipped this sprint and what are their security implications?&rdquo;</li>
  <li>&ldquo;Show me the top vulnerability trends across my repos for the past quarter&rdquo;</li>
  <li>&ldquo;Which repos need the most attention right now?&rdquo;</li>
  <li>&ldquo;Generate an incident response summary for this vulnerability&rdquo;</li>
  <li>&ldquo;What AI coding tools are being used across our organization?&rdquo;</li>
  <li>&ldquo;Summarize the security posture of repo X&rdquo;</li>
  <li>&ldquo;Which PRs in the last 30 days were merged after a risk was resolved?&rdquo;</li>
</ul>

<p>Because DryRun Security continuously scans every pull request and repository, these responses are grounded in real findings from your codebase, not generic checklists. They pull from live data, so the answers reflect your current state.</p>

<h3 id="saved-queries">Saved Queries</h3>

<p>Users can create and save custom queries in the Insights page for questions they return to regularly. For example:</p>

<ul>
  <li>A report on new critical findings across all repositories</li>
  <li>A developer trend summary highlighting teams with the most new findings</li>
  <li>A risk overview comparing finding rates period over period</li>
  <li>A sprint-aligned feature ship summary for release reviews</li>
</ul>

<p>Saved queries stay available in the Insights page and can be run any time by selecting them from the query list.</p>

<h2 id="mcp-integration">MCP Integration</h2>

<p>AppSec engineers and AI coding tools can also access the intelligence layer programmatically via DryRun Security&#x27;s MCP integration. This enables AI coding assistants and agents to query findings, trends, and risk data directly from the development environment. See <a href="./mcp">MCP Integration</a> for setup instructions.</p>
''',
}

# -- Platform --

PAGES['pr-scanning-configuration'] = {
    'title': 'PR Scanning Configuration',
    'description': 'Customize DryRun Security behavior per repository - enable agents, attach policies, configure blocking, and set up notifications.',
    'section': 'Platform',
    'content': '''
<p>Configurations let you customize how DryRun Security behaves for each repository or group of repositories. You can control which agents run, which policies are enforced, whether findings block PRs, and how notifications are delivered.</p>

<h2 id="creating-a-configuration">Creating a Configuration</h2>

<ol>
  <li>Log in to the DryRun Security portal at <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a>.</li>
  <li>Navigate to <strong>Settings &gt; Configurations</strong> in the sidebar.
    <br><strong>Note:</strong> The <code>default</code> configuration is editable and applies to all repositories not included in another configuration.</li>
  <li>Click <strong>Add new Configuration +</strong>.</li>
  <li>Enter a <strong>Configuration Name</strong> at the top of the page.</li>
</ol>

<h2 id="configuration-walkthrough">Configuration Walkthrough</h2>

<p>The Configurations page shows all your existing repository configurations.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/01-configurations.png" alt="Repository configurations list in DryRun Security dashboard" loading="lazy"></figure>

<p>Click <strong>Add New Configuration</strong> to create a configuration for your repositories.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/02-add-new-config.png" alt="Add New Configuration dialog" loading="lazy"></figure>

<h3 id="select-repositories">Select Repositories</h3>
<p>Choose which repositories this configuration applies to.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/03-select-repos.png" alt="Selecting repositories for a configuration" loading="lazy"></figure>

<h3 id="pr-comments-and-notifications">PR Comments and Notifications</h3>
<p>Enable or disable PR issue comments for this configuration.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/04-issue-comment.png" alt="Issue comment toggle" loading="lazy"></figure>

<p>Enable notifications to get alerts when security findings are detected.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/05-notifications.png" alt="Notifications toggle" loading="lazy"></figure>
<p><strong>Draft PRs:</strong> Comments are not sent to draft PRs. Findings from draft PR scans still appear in the Risk Register dashboard, but no comment is posted to the SCM until the PR is marked ready for review.</p>

<h3 id="attach-policies">Attach Code Policies</h3>
<p>Add up to 7 Custom Code Policies to a configuration.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/06-add-policies.png" alt="Adding code policies to a configuration" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/07-configure-policies.png" alt="Configuring attached policies" loading="lazy"></figure>

<h3 id="configure-security-agents">Code Security Agents</h3>
<p>Configure which security agents are enabled and whether they block or run silently.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/08-configure-agents.png" alt="Configuring code security agents" loading="lazy"></figure>

<p>Save the configuration when complete.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/09-config-save.png" alt="Saving a repository configuration" loading="lazy"></figure>

<h2 id="code-security-agents">Code Security Agents</h2>

<p>The bottom section of the configuration page lists all available Security Analyzers. Each analyzer has its own row with three controls:</p>

<table>
  <thead>
    <tr><th>Analyzer</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Cross-Site Scripting Analyzer</strong></td><td>Detects XSS vulnerabilities across rendering contexts</td></tr>
    <tr><td><strong>General Security Analyzer</strong></td><td>Broad-spectrum analyzer covering auth gaps, crypto, debug artifacts, and more</td></tr>
    <tr><td><strong>IDOR Analyzer</strong></td><td>Surfaces broken object-level authorization</td></tr>
    <tr><td><strong>Mass Assignment</strong></td><td>Detects unsafe model binding patterns</td></tr>
    <tr><td><strong>Secrets Analyzer</strong></td><td>Catches committed credentials, API keys, and tokens</td></tr>
    <tr><td><strong>Server-Side Request Forgery Analyzer</strong></td><td>Identifies SSRF via user-controlled outbound requests</td></tr>
    <tr><td><strong>SQL Injection Analyzer</strong></td><td>Traces data flow to detect unsafe query composition</td></tr>
  </tbody>
</table>

<h2 id="setting-descriptions">Setting Descriptions</h2>

<p>The top section of a configuration provides these controls:</p>

<ul>
  <li><strong>Select Repositories</strong> - A dropdown selector to choose which repositories use this configuration. Repositories can only belong to one configuration at a time; repositories already assigned to another configuration will be greyed out.</li>
  <li><strong>Issue Comment Enabled</strong> - Toggle to enable or disable DryRun Security's PR/MR comment. When enabled, DryRun posts a summary comment on each pull request with findings. Comments are not sent to draft PRs; findings from draft PR scans are still visible in the Risk Register.</li>
  <li><strong>PR Blocking Enabled</strong> - Toggle to enable PR blocking globally for this configuration. When enabled, findings from configured agents and policies will create status checks on GitHub Cloud and GitHub Enterprise Server (GHES) that must pass before merging.</li>
  <li><strong>Notifications Enabled</strong> - Toggle to enable notification delivery. When enabled, choose which integrations receive alerts (see <a href="./slack-integration">Notifications</a> for setup details).</li>
  <li><strong>Severity-Based PR Blocking</strong> - Toggle to block PRs based on severity. When enabled, set a minimum severity threshold; any finding at or above that level will block the PR from being merged. See <a href="./pr-blocking">PR Blocking</a> for threshold options.</li>
  <li><strong>Show Comment for No Findings</strong> - Toggle to control whether DryRun posts a comment even when no security findings are detected. Toggle off for the familiar behavior where DryRun posts a comment only when scans produce findings. Toggle on to have DryRun post a comment on every PR scanned, useful for visibility and audit trails.</li>
  <li><strong>Deduplicate Notifications</strong> - Toggle to reduce duplicate notifications on PRs where the severity has not changed. When enabled, repeated notifications for the same severity are suppressed, reducing noise.</li>
</ul>

<h3 id="policy-enforcement">Policy Enforcement Agent</h3>

<p>Below the general settings, the <strong>Policy Enforcement Agent</strong> section lets you attach Custom Code Policies to this configuration:</p>

<ul>
  <li><strong>Add Policy</strong> - Attach an existing policy from your organization's <a href="./custom-code-policies">Policy Library</a></li>
  <li><strong>Create Policy</strong> - Write a new Custom Code Policy directly from this screen</li>
</ul>

<p>Each attached policy is shown as a row with its own controls:</p>

<ul>
  <li><strong>Blocking</strong> - Toggle to make this policy a required status check. When enabled, a policy violation prevents the PR from being merged.</li>
  <li><strong>Silent Mode</strong> - Toggle to run the policy without posting findings in the PR comment. Useful for testing new policies before enforcing them.</li>
  <li><strong>Risk Level</strong> - Dropdown to set the severity label returned when the policy has findings. Options are <strong>Critical</strong>, <strong>High</strong>, <strong>Medium</strong>, or <strong>Low</strong>.</li>
</ul>

<p>The Policy Enforcement Agent can run up to 7 code policies per repository.</p>
''',
}

PAGES['custom-code-policies'] = {
    'title': 'Custom Code Policies',
    'description': 'Create custom security rules in plain English using Custom Code Policies.',
    'section': 'Platform',
    'content': '''
<h2 id="custom-code-policies">Custom Code Policies</h2>

<p>DryRun Security's Custom Code Policies let you define and enforce security policies in your codebase using natural language instead of complex scripting or specialized rule languages. Rather than writing regex patterns or static analysis rules, you describe what you care about in plain English and the LLM reasons through the code to evaluate it.</p>

<p>The key advantage of Custom Code Policies is that they are <strong>agentic</strong>. The LLM does not simply pattern-match against your code. Instead, it reasons about the code in context. It can follow function calls, trace data flow, understand business logic, and make judgments that traditional static analysis tools cannot. This means your policies can go far beyond what is possible with grep-style rules or AST matchers.</p>

<p>Custom Code Policies can be laser-focused on a unique function or structure specific to your application. Because you control the context (through the Question, Background, and Guidance fields), you can guide the analysis to look exactly where it matters and reason about the patterns that are unique to your codebase.</p>

<p>When a pull request is opened, DryRun Security's Policy Enforcement Agent runs all configured Custom Code Policies for the repository. The Policy Enforcement Agent can run up to 7 code policies per repository. Results appear in the PR comment and in the GitHub Checks area, with the option to block merges when a policy has findings.</p>


<h2 id="use-cases">Use Cases</h2>

<h3 id="identifying-vulnerabilities">1. Identifying specific vulnerabilities unique to your codebase</h3>

<p>Custom Code Policies can find security issues that generic scanners miss, including vulnerabilities tied to your application's specific architecture, patterns, or business logic. Because the LLM reasons through your code agenetically, it can identify risks that only make sense in the context of how your application actually works.</p>

<p>For example, a Custom Code Policy could detect an authentication bypass that only exists because of how your specific auth model chains middleware, or flag an injection risk in a custom query builder that is unique to your application. These are the kinds of vulnerabilities that generic scanners overlook because they lack the context of your particular codebase.</p>

<h3 id="monitoring-non-vulnerability-changes">2. Monitoring for non-vulnerability changes</h3>

<p>Custom Code Policies are not limited to security vulnerabilities. They can detect any type of change you want to monitor, including compliance checks, procedural guardrails, and architectural standards.</p>

<p>For example, you can create policies that detect when a regulated data model is modified, flag the use of deprecated internal APIs, or monitor for changes to configuration files that require a review process. This makes Custom Code Policies a flexible tool for enforcing organizational standards beyond traditional security scanning.</p>


<h2 id="creating-a-policy">Creating a Policy</h2>

<h3 id="using-the-ai-assistant">Using the AI Assistant</h3>

<p>The AI assistant provides a chat interface where you simply explain the type of vulnerability or change you want to monitor for. The assistant will ask you clarifying questions to understand your intent and gather the context needed. When you're ready, tell it to create the policy and it will automatically fill out all the related fields for you. This is the recommended approach for most users.</p>

<h3 id="manual-creation">Manual Creation</h3>

<p>For users who prefer direct control over every field, policies can be created manually:</p>

<ol>
  <li>Log in to the DryRun Security portal at <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a>.</li>
  <li>Navigate to the <strong>Code Policies</strong> section. You'll see a list of previously saved Code Policies.</li>
  <li>Click <strong>Add New Code Policy</strong>. You'll see the Code Policy Builder, which can be used to evaluate and save a Custom Code Policy.</li>
  <li>Enter a <strong>Name</strong> for the policy.</li>
  <li>Choose a <strong>Repository</strong> and <strong>Pull Request</strong> to evaluate.</li>
  <li>Enter the Custom Code Policy details:
    <ul>
      <li><strong>Question</strong> (required): A natural language question that identifies whether a specific change relates to the policy. For example, "Does this change expose any sensitive data?"</li>
      <li><strong>Background</strong> (optional): Background information or examples that may be used to refine the evaluation. For example, "We are concerned about..."</li>
      <li><strong>Guidance</strong> (optional): Additional information on actions to take when the policy condition is met.</li>
    </ul>
  </li>
  <li>Click <strong>Run</strong> to see the results of the Code Policy evaluation.</li>
  <li>Once the policy is returning expected results, click <strong>Save</strong> to save it for use in a Repository configuration.</li>
</ol>

<p>To apply the Code Policy to one or more repositories, click <strong>Configure</strong> and follow the steps in <a href="./pr-scanning-configuration">Configure Repositories</a>.</p>


<h2 id="field-usage">Field Usage</h2>

<h3 id="question">Question</h3>

<p>The question field is the prompt given to the LLM that triggers it to begin investigating for the vulnerability. This field should contain a series of things you want the model to check for or validate against. Think of it as the investigation directive: it should be specific enough to focus the analysis but broad enough to cover the relevant variations of the issue you want to catch.</p>

<h3 id="background">Background</h3>

<p>The background field provides context that loads alongside the question, giving the LLM the background information it needs to properly assess the code it is reviewing for this vulnerability type. Use this field to provide factual details about your app&rsquo;s function, architecture, authentication handling, data flow, or other dynamics. Do not tell the LLM what you want it to do here. Just provide factual details about your application so the model has the context it needs to make accurate assessments.</p>

<h3 id="guidance">Guidance</h3>

<p>The guidance field contains the instructions that the LLM will deliver to your development team when a vulnerability is identified by the code policy. This text appears as a comment in your SCM (GitHub, GitLab, etc.) on the relevant PR, so it should be written as actionable remediation instructions, telling developers exactly what to fix and how.</p>
''',
}

PAGES['repository-context'] = {
    'title': 'Repository Context',
    'description': 'Repository context lets teams share application-specific knowledge with DryRun Security\'s agents - covering architecture decisions, accepted patterns, and security controls that exist outside the code itself.',
    'section': 'Platform',
    'content': '''
<p>DryRun Security automatically scans active repositories in the background to build and maintain repository context, keeping PR analysis working from up-to-date knowledge of your codebase without any configuration required.</p>

<p>You can also add your own context to give DryRun Security's agents a deeper understanding of application-specific details that exist outside the code itself, covering architecture decisions, accepted patterns, and security controls. DryRun Security supports two ways to do this: a context managed in the dashboard, or an <code>AGENTS.md</code> file committed directly to the repo.</p>

<p><strong>Note:</strong> Dashboard context and AGENTS.md do not apply to Code Policies. To add context to a Code Policy, use the Background field in the <a href="./custom-code-policies">Code Policy</a> configuration directly.</p>

<h2 id="context-in-the-dashboard">Context in the Dashboard</h2>

<p>The DryRun Security dashboard includes a <strong>Context</strong> section where you can create and manage context without committing anything to the repository. A context is a settings file that captures the security-relevant details of your application - similar to the Security Review Guidelines section of an <code>AGENTS.md</code> - and can be applied to one or many repositories at once through a configuration.</p>

<p>Once a context is saved, it can be applied to a <a href="./pr-scanning-configuration">configuration</a>.</p>

<p>To create a context:</p>
<ol>
  <li>Log in to the DryRun Security dashboard at <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">app.dryrun.security</a></li>
  <li>Select <strong>Context</strong> from the left-hand navigation</li>
  <li>Create a new context, give it a name, and add your repository context</li>
  <li>Once saved, apply it to a configuration under <strong>Settings &gt; Configurations</strong> - or follow the prompt to go there directly from the Context section</li>
</ol>

<h2 id="agents-md">AGENTS.md</h2>

<p><a href="https://agents.md/" target="_blank" rel="noopener noreferrer">AGENTS.md</a> is a format supported by the <a href="https://aaif.io/" target="_blank" rel="noopener noreferrer">Agentic AI Foundation</a>, a Linux Foundation Project. The file is intended to be "a predictable place to provide the context and instructions to help AI coding agents work on your project."</p>

<p>DryRun Security supports <code>AGENTS.md</code> for both core analyzer products: the Code Review Agent and the DeepScan Agent. DryRun Security's agents will look for and review this file to apply the additional context it provides during analysis.</p>

<p>Some teams prefer <code>AGENTS.md</code> over the dashboard context because it keeps context management in the repository itself. Developers can review and update it alongside the code, without needing to log in to the DryRun Security dashboard.</p>

<p><strong>Note:</strong> The Code Review Agent checks for AGENTS.md in the root. The DeepScan Agent can discover both root and nested AGENTS.md files.</p>

<p>To best leverage this, add a <strong>Security Review Guidelines</strong> section to your <code>AGENTS.md</code> with any context related to design assumptions, areas of particular security interest, or other relevant points for an agentic security reviewer.</p>

<h2 id="when-to-use-context">When to Use Context</h2>

<p>Repository context works best when DryRun Security needs more information about your application to assess findings accurately. If a class of finding keeps appearing because DryRun Security is not aware of a specific pattern, architectural decision, or security control in your codebase, adding context is the right fix. It teaches the system how your application works so that every future scan benefits from that understanding - rather than managing each instance of that finding one at a time.</p>

<p>Good candidates for a context update:</p>
<ul>
  <li>A vulnerability class that keeps surfacing because of a known, accepted pattern in your codebase (e.g., intentionally public routes, TLS handled upstream)</li>
  <li>Authorization or authentication behavior that does not follow standard patterns but is correct by design</li>
  <li>Security controls that exist outside the code and are not visible to a scanner (e.g., WAF rules, middleware, infrastructure-level protections)</li>
</ul>

<p>If DryRun Security already has the right context but a specific finding is incorrect or not relevant to your team, that is outside the scope of repository context. The <a href="./finding-tuning">finding tuning</a> page covers how to mark findings as false positives.</p>

<h2 id="what-to-include">What to Include</h2>

<p>Both methods support the same types of context. The following are useful starting points for a Security Review Guidelines section:</p>
<ul>
  <li>Structure of a monolith, and how authorization works between components</li>
  <li>Collections of routes or controllers that do not follow typical authorization patterns by design</li>
  <li>Specific security requirements coding assistants need to validate against during code generation</li>
  <li>Assumptions about security-impacting configurations not clear in code (e.g., TLS offloading, WAF rules)</li>
  <li>Specific security patterns that must be followed, with examples of allowed and disallowed code snippets</li>
</ul>

<h2 id="example">Example Security Review Guidelines Section</h2>

<pre><code>## Security Review Guidelines

### Device Trust for internal routes
All routes that are prefixed with /abc123 are to be recognized
as internal-only routes, and require the use of trusted devices
issued by the enterprise. Device trust is recognized by an Okta
device token, and these routes are verified within Okta for
proper authorization scopes from the IdP and authorization
server, which will not be checked by the application layer
specifically. Row or object-level authorization issues related to
this pattern only for these internal routes can be ignored as
accepted.

### Intentionally Public Routes
Some controllers have embedded routes with authentication and
authorization decorators disabled or skipped on purpose for
public facing content. The routes are intended to allow anonymous
access to these features ONLY IF the specific controller action
does not perform edits or require write access. Validate the read-
only nature of these endpoints and flag any actions that enable
write behavior when the authentication decorations are skipped.

### Ignore HTTPS related issues on cookies and configuration files
This application is always deployed to a kubernetes cluster as a
mesh service. TLS offloading is provided in front of the application.
Ignore any issues related to Cookies missing Secure flags, requiring
HTTPS in build configurations, or certificate requirements in
this application.</code></pre>

''',
}

PAGES['risk-register'] = {
    'title': 'Risk Register',
    'description': 'One view to see, search, and act on all security risk across your organization.',
    'section': 'Platform',
    'content': '''
<p>The Risk Register is the working space for AppSec engineers, designed to surface findings that need action taken. It aggregates findings from two sources: the <a href="./pr-scanning">PR Scanner</a>, which reviews every pull request for vulnerabilities in real time, and <a href="./deepscan">DeepScan</a>, which performs full-repository security analysis on demand. Findings range from critical vulnerabilities and secrets exposures to policy violations and dependency risks. Because these findings represent real or potential security issues in your codebase, the Risk Register provides a single place to review, triage, and act on them before they become incidents.</p>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/risk-register/01-risk-register.png" alt="DryRun Security Risk Register dashboard" loading="lazy"></figure>

<h2 id="common-workflows">Common Workflows</h2>

<h3 id="reviewing-merged-risk">Reviewing Merged Risk</h3>
<p>Filter by &ldquo;merged&rdquo; PR status. This shows findings DryRun Security identified as containing a vulnerability but that were merged anyway, meaning the vulnerability lives in the codebase. These represent accepted or overlooked risk and should be reviewed to determine if remediation is needed.</p>

<h3 id="triaging-open-prs">Triaging Open PRs</h3>
<p>Filter by &ldquo;open&rdquo; PR status. This surfaces findings on pull requests that are still open and have not been merged to main yet. Because the PR is still open, there is still time to fix the issue before it reaches production. These findings should be prioritized and actioned first.</p>
<p>Draft PRs are also surfaced here. DryRun Security scans draft PRs and surfaces findings in the Risk Register, but does not post comments to the SCM until the PR is marked ready for review.</p>

<h3 id="reviewing-dismissed-findings">Reviewing Dismissed Findings</h3>
<p>Filter to show dismissed findings. AppSec engineers can see who dismissed each finding and take appropriate follow-up action: override the dismissal if the finding represents real risk, reach out to the developer to help educate them, or stay informed about what is being marked as &ldquo;won&rsquo;t fix&rdquo;, &ldquo;nit pick&rdquo;, or &ldquo;false positive&rdquo;. This workflow supports both risk oversight and developer security education.</p>

<h2 id="search-and-filter">Search and Filter</h2>

<p>The Risk Register provides several ways to narrow your view:</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/risk-register/02-risk-filter.png" alt="Risk Register filtering and search options" loading="lazy"></figure>

<ul>
  <li><strong>Search</strong> - A full-text search box lets you search across finding titles, file paths, repository names, PR titles, PR numbers, and other fields</li>
  <li><strong>30D date filter</strong> - Quickly scope findings to the last 30 days, or adjust the date range to match your review period</li>
  <li><strong>Filter</strong> - Opens advanced filtering options to narrow by risk level, agent type (including Code Policy), status, and more</li>
  <li><strong>Triage</strong> - Select one or more findings and triage them in bulk with a reason and optional context</li>
</ul>

<h2 id="findings-table">Findings Table</h2>

<p>The main findings table shows all findings with the following columns:</p>

<table>
  <thead>
    <tr><th>Column</th><th>Description</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>Risk</strong></td><td>Severity label (Critical, High, Medium, Low) with color coding. Sortable.</td></tr>
    <tr><td><strong>Type</strong></td><td>The vulnerability or finding description (e.g., "Authorization Bypass in Next.js", "Token Validation Check", "client-side-trust")</td></tr>
    <tr><td><strong>File</strong></td><td>The file path where the finding was detected (e.g., <code>package-lock.json</code>, <code>app/api/generate-vi...</code>, <code>firestore.rules</code>)</td></tr>
    <tr><td><strong>Repo</strong></td><td>The repository name where the finding originated</td></tr>
    <tr><td><strong>Detected</strong></td><td>Timestamp showing when the finding was first detected (e.g., 03/18/26 16:51:18)</td></tr>
    <tr><td><strong>Agent</strong></td><td>Which agent produced the finding - SCA, Code Policy, DeepScan, or a specific Security Analyzer</td></tr>
    <tr><td><strong>Status</strong></td><td>The current state of the finding, shown as an icon indicating open, triaged, or resolved</td></tr>
  </tbody>
</table>

<p>Each row has a checkbox for bulk selection, and findings are paginated (e.g., "Showing 1-20 of 203 entries") with page navigation at the bottom.</p>

<p>Clicking a finding row expands the inline detail view. This shows the full finding description alongside a code snippet at the exact location of the finding. For findings where DryRun Security has gathered support evidence, that context appears in the detail view alongside the finding. For DeepScan findings, the inline view includes application details surfaced during the scan, such as relevant framework context, data flows, and authentication patterns that informed the finding.</p>
''',
}

PAGES['finding-tuning'] = {
    'title': 'Finding Tuning with Feedback',
    'description': 'Tune security findings and reduce false positives with feedback from developers and AppSec engineers.',
    'section': 'Platform',
    'content': '''
<p>Developers and AppSec engineers can dismiss findings directly from the PR thread or the Risk Register dashboard. Every dismissal is logged for audit. Dismissals marked as <strong>False Positive</strong> or <strong>Won&rsquo;t Fix / Nitpick</strong> also feed back into the model, improving scan accuracy over time.</p>

<h2 id="dismissal-statuses">Dismissal Statuses</h2>

<table>
  <thead>
    <tr>
      <th>Status</th>
      <th>Description</th>
      <th>Available From</th>
      <th>LLM Learning</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>False Positive</strong></td>
      <td>The finding is not real or does not apply to the codebase. DryRun Security fingerprints the pattern and suppresses it in future scans. Context provided improves detection accuracy across similar patterns over time.</td>
      <td>PR comment and Risk Register</td>
      <td>Yes</td>
    </tr>
    <tr>
      <td><strong>Won&rsquo;t Fix / Nitpick</strong></td>
      <td>The finding is valid but below the bar the team cares about, or the team has decided not to fix it. Feeds back into the model to reduce similar noise over time.</td>
      <td>PR comment and Risk Register</td>
      <td>Yes</td>
    </tr>
    <tr>
      <td><strong>Accepted Risk</strong></td>
      <td>The team knowingly accepts the risk and will not remediate it. Removed from the active view and SCM comment. Documented in the audit trail with the reason and who accepted it.</td>
      <td>Risk Register</td>
      <td>No</td>
    </tr>
    <tr>
      <td><strong>In Progress</strong></td>
      <td>A fix is planned but not yet applied. Removed from the active view and SCM comment. DryRun Security resolves it once the fix is applied.</td>
      <td>Risk Register</td>
      <td>No</td>
    </tr>
    <tr>
      <td><strong>Resolved</strong></td>
      <td>The finding has been addressed. Removed from the active view and SCM comment.</td>
      <td>Risk Register</td>
      <td>No</td>
    </tr>
  </tbody>
</table>

<p>False Positive and Won&rsquo;t Fix / Nitpick dismissals feed into the <a href="./code-security-intelligence">Code Security Knowledge Graph</a>, building a model of your codebase&rsquo;s specific patterns and risk profile. Scan accuracy improves continuously as your team triages findings.</p>

<h2 id="from-the-pr">From the PR</h2>

<p>Developers can dismiss findings directly from the pull request thread without leaving their workflow. Dismissals sync to the Risk Register for AppSec review.</p>

<p>To mark a finding as a false positive:</p>
<p><code>@dryrunsecurity FP [issue ID] details why</code></p>

<p>To mark a finding as a nitpick:</p>
<p><code>@dryrunsecurity NIT [issue ID] details why</code></p>

<p>When a developer submits a dismissal, DryRun Security removes the finding from the active list, regenerates the PR summary comment, logs the decision for the audit trail, and feeds the signal back into the system.</p>

<p>If a finding is incorrectly blocking a merge via <a href="./pr-blocking">branch protection rules</a>, developers can dismiss it directly in the PR thread. DryRun Security automatically removes the block without requiring AppSec intervention. The dismissal is logged so AppSec can review it afterward.</p>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/risk-register/05-scm-feedback.jpg" alt="SCM feedback workflow" loading="lazy"></figure>

<h2 id="from-the-risk-register">From the Risk Register</h2>

<p>AppSec engineers manage dismissals from the <a href="./risk-register">Risk Register</a>, which provides a centralized view across all repositories and scan types. Select one or more findings using the checkboxes, then click <strong>Dismiss</strong> to choose a status and optionally add context.</p>

<p>Dismissing a finding as False Positive or Won&rsquo;t Fix / Nitpick from the Risk Register also removes the associated failed SCM check on the pull request, clearing the block automatically. Accepted Risk, In Progress, and Resolved dismissals do not automatically clear the SCM check.</p>
<p>From the Risk Register, AppSec teams can also:</p>
<ul>
  <li>Override dismissals when a finding represents real risk that was incorrectly dismissed</li>
  <li>Monitor dismissal patterns across the organization to identify trends</li>
  <li>Use the audit trail to confirm all triage decisions are intentional and documented</li>
</ul>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/risk-register/03-finding-triage.png" alt="Finding triage in the Risk Register" loading="lazy"></figure>

<figure class="docs-screenshot docs-screenshot-sm"><img src="{asset_prefix}assets/images/risk-register/04-triage-pr.png" alt="Finding triage from the PR workflow" loading="lazy"></figure>

<h2 id="dismissed-findings">Dismissed Findings</h2>

<p>View dismissed findings in the Risk Register using the <strong>Dismissed</strong> filter. Each entry shows the dismissal status, reason, who dismissed it, and when. Use the <strong>Restore</strong> button to return a finding to the active queue if the dismissal needs to be revisited.</p>

<div class="callout callout-warning">
<p><strong>When a finding is valid but mitigating circumstances exist:</strong> Sometimes your team knows DryRun Security is right about a finding, but another layer of protection already addresses it. Rather than marking it as a false positive, the right resolution is to update your AGENTS.md with the context that explains why. This tells DryRun Security about the mitigating control so it does not raise the same class of issue again, without misrepresenting the finding as invalid. See <a href="./repository-context">Repository Context</a> for details.</p>
</div>

''',
}

PAGES['pr-blocking'] = {
    'title': 'PR Blocking',
    'description': 'Configure DryRun Security to block pull requests when critical vulnerabilities are detected.',
    'section': 'Platform',
    'content': '''
<h2 id="overview">Overview</h2>

<p>DryRun Security can be configured to block pull requests from being merged when security findings exceed your defined thresholds. PR Blocking integrates with your source code management platform's native branch protection features to enforce security gates in your development workflow.</p>

<h2 id="how-it-works">How It Works</h2>

<p>When PR Blocking is enabled, DryRun Security reports its scan results as a required status check on each pull request. If findings meet or exceed the configured severity threshold, the check is marked as failed, preventing the PR from being merged until the issues are resolved.</p>

<p>Blocking can be configured at two levels:</p>

<ul>
  <li><strong>PR Blocking Enabled</strong> (configuration level): When toggled on, any analyzer included in the configuration that produces a finding at or above the configured severity threshold triggers a failing blocking status for your SCM to enforce.</li>
  <li><strong>Blocking</strong> (individual analyzer level): When toggled on for a specific analyzer, that analyzer blocks the PR on any finding it produces, regardless of severity or criticality.</li>
</ul>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/18-pr-blocking-toggles.png" alt="Configuration showing the PR Blocking Enabled toggle and per-analyzer Blocking toggles" loading="lazy"></figure>

<h2 id="configuring-blocking">Configuring PR Blocking</h2>

<ol>
  <li>Open the configuration for the repository you want to protect.</li>
  <li>Go to <strong>Settings</strong> for the repository you want to configure.</li>
  <li>Under <strong>PR Blocking</strong>, enable the blocking toggle.</li>
  <li>Set the <strong>severity threshold</strong>. Findings at or above this level will block the PR. Options include:
    <ul>
      <li><strong>Critical</strong>: Only block on critical severity findings.</li>
      <li><strong>High</strong>: Block on high and critical findings.</li>
      <li><strong>Medium</strong>: Block on medium, high, and critical findings.</li>
      <li><strong>Low</strong>: Block on all findings.</li>
    </ul>
  </li>
  <li>Configure your SCM's branch protection or merge request rules to require the DryRun Security status check.</li>
</ol>

<h2 id="override-workflow">Override Workflow</h2>

<p>When a finding is dismissed as False Positive or Won&rsquo;t Fix / Nitpick, DryRun Security automatically clears the failing SCM check on the associated pull request. The block lifts as soon as the dismissal is processed, whether submitted from the PR thread or the Risk Register.</p>

<p>Dismissals marked as Accepted Risk, In Progress, or Resolved do not clear the SCM check. The pull request remains blocked until the finding is dismissed as False Positive or Won&rsquo;t Fix / Nitpick.</p>

<p>All dismissal decisions are logged in the <a href="./risk-register">Risk Register</a> for audit purposes.</p>

<h2 id="configure-blocking">Configure Blocking with GitHub Branch Protection</h2>

<p>These steps apply to both GitHub.com and GitHub Enterprise Server (GHES). The branch protection interface and workflow are identical on both, so GHES administrators can follow the same instructions.</p>

<p>The recommended approach is to configure a severity threshold at the configuration level. Any finding at or above that threshold will trigger the blocking flow across all agents.</p>

<p>For teams that prefer per-policy or per-analyzer blocking, that is still supported. After enabling <strong>Blocking</strong> on a specific policy or analyzer, follow these steps:</p>

<h3 id="set-up-branch-protection">Set Up a Classic Branch Protection Rule</h3>

<ol>
  <li>On GitHub, navigate to the main page of the repository.</li>
  <li>Under your repository name, click <strong>Settings</strong>.</li>
  <li>In the <strong>Code and automation</strong> section of the sidebar, click <strong>Branches</strong>.</li>
  <li>Choose <strong>Add classic branch protection rule</strong>.</li>
  <li>Under <strong>Branch name pattern</strong>, type the name of the branch to protect (e.g., <code>main</code>).</li>
  <li>Select <strong>Require status checks to pass before merging</strong>.</li>
  <li>
    <p>In the search field, search for the DryRun Security check you want to require. The following checks are available:</p>
    <table>
      <thead><tr><th>Check name</th><th>What it covers</th></tr></thead>
      <tbody>
        <tr><td>Cross-Site Scripting Analyzer</td><td>XSS vulnerabilities across rendering contexts</td></tr>
        <tr><td>General Security Analyzer</td><td>Auth gaps, crypto issues, debug artifacts, and more</td></tr>
        <tr><td>IDOR Analyzer</td><td>Broken object-level authorization</td></tr>
        <tr><td>Mass Assignment</td><td>Unsafe model binding patterns</td></tr>
        <tr><td>Secrets Analyzer</td><td>Committed credentials, API keys, and tokens</td></tr>
        <tr><td>Server-Side Request Forgery Analyzer</td><td>SSRF via user-controlled outbound requests</td></tr>
        <tr><td>SQL Injection Analyzer</td><td>Unsafe query composition</td></tr>
        <tr><td>Code Policies</td><td>All custom code policies configured for your team</td></tr>
      </tbody>
    </table>
  </li>
  <li>Click <strong>Create</strong>.</li>
</ol>

<p>When a Custom Code Policy has <strong>Blocking</strong> enabled, it appears as a single Check in GitHub under the name <strong>Code Policies</strong>. When a Code Security Agent has blocking enabled, it appears as a Check with the agent's name (e.g., <strong>Secrets Analyzer</strong>).</p>

<h2 id="github-branch-protection-rules">GitHub Branch Protection Rules</h2>

<p>Use GitHub Branch Protection Rules to enforce DryRun Security checks before merging.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/10-github-settings.png" alt="GitHub repository Settings page" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/11-github-branches.png" alt="GitHub Branches settings" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/12-branch-protection.png" alt="GitHub Branch Protection rule" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/13-branch-name.png" alt="Branch name pattern for protection" loading="lazy"></figure>

<p>Require DryRun Security status checks to pass before merging.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/14-require-checks.png" alt="Requiring status checks for DryRun Security" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/15-checks-policies.png" alt="DryRun Security policy checks in branch protection" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/16-checks-secrets.png" alt="DryRun Security secrets check in branch protection" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/configurations/17-checks-details.png" alt="DryRun Security check details in branch protection" loading="lazy"></figure>
''',
}

PAGES['compliance-grc'] = {
    'title': 'Compliance & GRC',
    'description': 'Compliance reporting, audit readiness, and SBOM generation.',
    'section': 'Platform',
    'content': '''
<h2 id="compliance-audit">Compliance and Audit Readiness</h2>

<h2 id="overview">Overview</h2>

<p>DryRun Security provides the evidence trail that compliance and audit workflows require. Every PR review, finding, remediation, and policy enforcement action is tracked and accessible through the platform's reporting capabilities.</p>

<h2 id="soc2-certification">SOC2 Type II Certification</h2>

<p>DryRun Security is SOC2 Type II certified. This means the platform itself has been independently audited for security, availability, and confidentiality controls. Your data is handled according to the same standards your organization is working to meet.</p>

<h2 id="audit-evidence">Audit Evidence Generation</h2>

<p>The platform automatically generates evidence that auditors and regulators commonly request:</p>

<ul>
  <li><strong>Findings history</strong> - complete record of every vulnerability found, when it was found, and when it was resolved</li>
  <li><strong>Remediation timelines</strong> - time-to-fix metrics for each finding, broken down by severity and category</li>
  <li><strong>Policy enforcement records</strong> - which <a href="./custom-code-policies">Custom Code Policies</a> were evaluated, what they found, and how findings were resolved</li>
  <li><strong>Scan coverage</strong> - which repositories were scanned, how frequently, and what percentage of PRs received security review</li>
  <li><strong>DeepScan reports</strong> - point-in-time full-repository security assessments for baseline evidence</li>
</ul>

<h2 id="dashboard-reporting">Dashboard and Reporting</h2>

<p>The <a href="./code-security-intelligence">Security Dashboard</a> provides real-time metrics that map to common compliance requirements:</p>

<ul>
  <li>Vulnerability trends over time (are things getting better or worse?)</li>
  <li>Open findings by severity and category</li>
  <li>Mean time to remediation</li>
  <li>Policy compliance rates across repositories</li>
  <li>Coverage gaps (repositories not yet connected)</li>
</ul>

<p>Use the <a href="./code-security-intelligence">intelligence index</a> to generate custom audit-ready reports by asking natural language questions like "show me a chart of risky alerts by repo for last quarter."</p>

<h2 id="risk-register">Risk Register as Audit Trail</h2>

<p>The <a href="./risk-register">Risk Register</a> serves as the central audit trail for all findings. Every finding includes:</p>

<ul>
  <li>The specific code change that introduced the vulnerability</li>
  <li>Which analyzer detected it and why</li>
  <li>The remediation status and any associated PR that fixed it</li>
  <li>Triage records with notes explaining why a finding was marked as acceptable risk</li>
</ul>

<p>This level of traceability satisfies auditors who need to understand not just what vulnerabilities exist, but how the organization identified and responded to them.</p>

<h2 id="sbom-and-ai-bom">SBOM and AI-BOM</h2>

<p>DryRun Security generates <a href="./compliance-grc">Software Bills of Materials (SBOM)</a> that document the third-party components in your codebase. SBOMs are increasingly required by regulation (Executive Order 14028, EU Cyber Resilience Act) and by enterprise customers who need supply chain transparency.</p>

<h2 id="deepscan-compliance">DeepScan for Compliance Assessments</h2>

<p>Run a <a href="./deepscan">DeepScan</a> to generate a point-in-time security assessment of an entire repository. This is useful for:</p>

<ul>
  <li>Initial onboarding - establishing a security baseline when connecting a repository</li>
  <li>Pre-audit preparation - generating comprehensive findings reports ahead of an audit</li>
  <li>Regulatory submissions - providing evidence of security review for compliance certifications</li>
  <li>Periodic assessments - quarterly or annual full-repository reviews beyond continuous PR scanning</li>
</ul>


<h2 id="sbom-generation">SBOM Generation</h2>

<h2 id="what-is-sbom">What Is an SBOM?</h2>

<p>A Software Bill of Materials (SBOM) is a formal inventory of all the components in a software product - every library, package, framework, and dependency, along with version information and provenance data. SBOMs have become an important tool for supply chain security, enabling organizations to quickly determine whether they're affected when a new vulnerability is disclosed in a widely-used library.</p>

<p>Regulatory frameworks and government procurement requirements increasingly mandate SBOM production. Executive Order 14028 in the United States requires SBOM from software vendors selling to the federal government. Similar requirements are emerging in the EU and other jurisdictions. Even organizations not subject to regulatory mandates benefit from the visibility SBOMs provide into their software supply chain.</p>

<h2 id="sbom-with-dryrun">SBOM with DryRun Security</h2>

<p>DryRun Security generates SBOMs as a natural output of its dependency scanning capability. Because DryRun Security already analyzes your dependency manifests and lock files on every scan, the data needed for SBOM production is continuously maintained and up to date.</p>

<p>SBOMs can be exported in industry-standard formats, enabling integration with vulnerability management platforms, procurement systems, and compliance tools that consume SBOM data.</p>

<h2 id="ai-bom">AI-BOM: Bill of Materials for AI Components</h2>

<p>As AI-generated code and AI-powered libraries become prevalent in modern software, a new challenge emerges: understanding what AI components are present in your software and what their provenance is. DryRun Security generates <strong>AI-BOMs</strong> - bills of materials specifically tracking AI-originated components and AI library dependencies.</p>

<p>An AI-BOM captures:</p>
<ul>
  <li>AI and ML libraries present in the codebase and their versions</li>
  <li>Model dependencies and third-party AI service integrations</li>
  <li>Sections of code identified as AI-generated (via DryRun's AI coding visibility capability)</li>
</ul>

<h2 id="compliance-readiness">Compliance and Audit Readiness</h2>

<p>SBOM and AI-BOM data produced by DryRun Security can be provided directly to auditors, customers, or regulators as evidence of supply chain visibility and control. Combined with DryRun Security's continuous vulnerability scanning and risk trending, this provides the documented, traceable security program that compliance frameworks require.</p>
''',
}

PAGES['permissions'] = {
    'title': 'Permissions',
    'description': 'Understand the two-role permission model in DryRun Security and how SCM platform roles map to Admin and Developer access.',
    'section': 'Platform',
    'content': '''
<h2 id="overview">Overview</h2>

<p>DryRun Security uses your SCM platform (GitHub or GitLab) for authentication. Because DryRun already knows your SCM role at login, it maps that role directly to a DryRun permission level with no additional setup required.</p>

<p>GitHub Enterprise Server (GHES) follows the same permission model as GitHub Cloud. Anywhere this page refers to GitHub, it applies equally to GHES.</p>

<p>DryRun uses a two-role model: <strong>Admin</strong> and <strong>Developer</strong>. To give a user more access, you can either elevate their permissions in the SCM, or request an <a href="#admin-override">Admin Override</a> (see the Admin Override section below).</p>

<h2 id="permissions-matrix">Permissions Matrix</h2>

<p><em>Note: Developers can only view findings, repositories, and pull requests for repositories they have membership access to in GitHub or GitLab. All other access listed below applies to the full platform.</em></p>

<table>
  <thead>
    <tr><th>Feature</th><th>Admin</th><th>Developer</th><th>Details</th></tr>
  </thead>
  <tbody>
    <tr><td>Install</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Install DryRun Security on GitHub or GitLab organizations and repositories.</td></tr>
    <tr><td>Risk Register</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>Central view of security findings across repositories, organized by severity and status. Developers see findings only for repos they have membership access to.</td></tr>
    <tr><td>Repositories</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>View repositories connected to DryRun Security and their scan status. Developers see only repos they have membership access to.</td></tr>
    <tr><td>Pull Requests</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>View pull requests and their associated security findings. Developers see only PRs for repos they have membership access to.</td></tr>
    <tr><td>Dismiss Findings</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>Dismiss a finding from the DryRun dashboard or directly from the SCM PR comment.</td></tr>
    <tr><td>DeepScan: View</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>View DeepScan runs, reports, and findings for repositories.</td></tr>
    <tr><td>DeepScan: Trigger</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Initiate a new DeepScan run on a repository on demand.</td></tr>
    <tr><td>Code Policies: View</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>View existing custom code policies configured for the account.</td></tr>
    <tr><td>Code Policies: Configure</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Create, edit, and manage custom code policies used during scanning.</td></tr>
    <tr><td>Insights & AI Assistant</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>AI-powered security insights and a chat assistant for querying findings and trends.</td></tr>
    <tr><td>Daily Digest</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Automated daily summary of new findings, trends, and security posture changes.</td></tr>
    <tr><td>Configurations: View</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>View PR scanner behavior, blocking rules, and policy enforcement settings.</td></tr>
    <tr><td>Configurations: Edit</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Edit PR scanner behavior, blocking rules, and policy enforcement settings.</td></tr>
    <tr><td>Integrations: View</td><td><span class="check">&#x2713;</span></td><td><span class="check">&#x2713;</span></td><td>View connected integrations including Slack, webhooks, and AI coding integrations (MCP/IDE).</td></tr>
    <tr><td>Integrations: Configure</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Set up and manage Slack, webhook, and AI coding integrations (MCP/IDE).</td></tr>
    <tr><td>Access Keys</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Generate and manage API access keys for programmatic access to DryRun Security.</td></tr>
    <tr><td>Install / Uninstall Repos</td><td><span class="check">&#x2713;</span></td><td class="no-access"><span class="cross">&#x2717;</span></td><td>Add or remove repositories from DryRun Security scanning.</td></tr>
  </tbody>
</table>

<h2 id="scm-role-mapping">SCM Role Mapping</h2>

<p>DryRun Security automatically maps SCM roles to DryRun roles at login. No manual configuration is required.</p>

<table>
  <thead>
    <tr><th>SCM Platform</th><th>SCM Role</th><th>DryRun Role</th></tr>
  </thead>
  <tbody>
    <tr><td>GitHub</td><td>Admin</td><td>Admin</td></tr>
    <tr><td>GitHub</td><td>Member</td><td>Developer</td></tr>
    <tr><td>GitLab</td><td>Owner</td><td>Admin</td></tr>
    <tr><td>GitLab</td><td>Maintainer</td><td>Admin</td></tr>
    <tr><td>GitLab</td><td>Developer</td><td>Developer</td></tr>
  </tbody>
</table>

<h2 id="admin-override">Admin Override</h2>

<p>An account administrator can request that a developer be promoted to Admin within the platform. This setting is not self-serve and is managed by our team. The override applies only within DryRun Security and does not change the user's role in GitHub or GitLab. To request an override, contact us at <a href="mailto:hi@dryrun.security">hi@dryrun.security</a>.</p>
''',
}

PAGES['mcp'] = {
    'title': 'MCP',
    'description': 'Connect AI assistants to DryRun Security insights using the Model Context Protocol for natural language queries about your security data.',
    'section': 'Platform',
    'content': '''
<p>The DryRun Security Insights MCP (Model Context Protocol) server gives AI assistants direct access to your organization's security data. Once connected, your AI coding tool can query findings, trends, pull request context, and Code Security Intelligence results in natural language, without leaving your development environment.</p>

<h2 id="what-you-can-do">What You Can Do</h2>

<p>With the Insights MCP connected, your AI assistant can:</p>
<ul>
  <li>Generate summaries of recent security activity across your repositories</li>
  <li>Query findings for a specific pull request or file</li>
  <li>Ask natural language questions about your security posture (for example: "Have any new payment integrations been introduced in the last week?")</li>
  <li>Access Code Security Intelligence trends and agent stats</li>
  <li>Surface pull requests from the last 30 days that were merged after an identified risk was resolved</li>
  <li>Track security posture changes over time</li>
</ul>

<p>For the full list of Code Security Intelligence capabilities, see <a href="./code-security-intelligence">Code Security Intelligence</a>.</p>

<h2 id="supported-clients">Supported Clients</h2>

<p>The following AI coding tools support the DryRun Security Insights MCP:</p>

<table>
  <thead>
    <tr><th>Tool</th><th>Connection method</th></tr>
  </thead>
  <tbody>
    <tr><td>Cursor</td><td>HTTP MCP config</td></tr>
    <tr><td>Codex</td><td>HTTP MCP config</td></tr>
    <tr><td>Claude Code</td><td>CLI (<code>claude mcp add</code>)</td></tr>
    <tr><td>Claude Desktop</td><td>Settings &gt; Connectors</td></tr>
    <tr><td>Windsurf</td><td>HTTP MCP config</td></tr>
    <tr><td>VS Code</td><td>HTTP MCP config</td></tr>
  </tbody>
</table>

<p>For step-by-step setup instructions for each tool, go to <strong>Settings &gt; Integrations</strong> in the DryRun Security dashboard, or see <a href="./dryrun-skill">DryRun Skill</a>.</p>

<h2 id="authentication">Authentication</h2>

<p>The MCP server uses API key authentication. Pass your API key as a Bearer token in the <code>Authorization</code> header.</p>

<p>Before connecting, generate an API key from <strong>Settings &gt; Access Keys</strong> in the DryRun Security dashboard. See <a href="./api-access-keys">API Access Keys</a> for instructions.</p>

<p>The MCP server URL is:</p>

<pre><code>https://insights-mcp.dryrun.security/api/insights/mcp</code></pre>

<h2 id="configuration">Configuration</h2>

<h3 id="claude-code">Claude Code (CLI)</h3>

<pre><code>claude mcp add --transport http dryrun-security https://insights-mcp.dryrun.security/api/insights/mcp --header "Authorization: Bearer &lt;your-api-key&gt;"</code></pre>

<h3 id="http-json-config">HTTP JSON Config (Cursor, Windsurf, VS Code, Codex)</h3>

<pre><code>{
  "mcpServers": {
    "dryrun-security": {
      "type": "http",
      "url": "https://insights-mcp.dryrun.security/api/insights/mcp",
      "headers": {
        "Authorization": "Bearer &lt;your-api-key&gt;"
      }
    }
  }
}</code></pre>

<h3 id="claude-desktop">Claude Desktop</h3>

<ol>
  <li>Navigate to <a href="https://claude.ai" target="_blank" rel="noopener noreferrer">https://claude.ai</a></li>
  <li>Select <strong>Settings</strong></li>
  <li>Select <strong>Connectors</strong></li>
  <li>Click <strong>Add custom connector</strong></li>
  <li>Enter the URL: <code>https://insights-mcp.dryrun.security/api/insights/mcp</code></li>
  <li>Select <strong>Add</strong></li>
</ol>

<p>Replace <code>&lt;your-api-key&gt;</code> with the key from <strong>Settings &gt; Access Keys</strong>. See <a href="./api-access-keys">API Access Keys</a>.</p>

<h2 id="remediation-skill">DryRun Remediation Skill</h2>

<p>In addition to the MCP connection, you can install the DryRun Security remediation skill into your AI coding tool. The skill enables the tool to automatically detect findings and generate fixes. See <a href="./dryrun-skill">DryRun Skill</a> for installation instructions.</p>

<h2 id="verifying-the-connection">Verifying the Connection</h2>

<p>Once configured, confirm the DryRun Security Insights tool is available in your AI assistant's toolset. Try asking: "What is my insights summary for the past week?"</p>

<p>If you encounter any issues, reach out at <a href="mailto:hi@dryrun.security">hi@dryrun.security</a>.</p>
''',
}

PAGES['dryrun-api'] = {
    'title': 'DryRun API',
    'description': 'Programmatic access to DryRun Security findings, scans, configurations, and insights via the Simple API.',
    'section': 'Platform',
    'content': '''
<h2 id="dryrun-simple-api">DryRun Simple API</h2>

<p>The DryRun Simple API provides programmatic access to your organization's security data: findings, scans, deepscans, configurations, repositories, and insights.</p>

<ul>
  <li><strong>Swagger UI:</strong> <a href="https://simple-api.dryrun.security/api-docs/index.html" target="_blank" rel="noopener noreferrer">https://simple-api.dryrun.security/api-docs/index.html</a></li>
  <li><strong>OpenAPI (v3.0) spec:</strong> <a href="https://simple-api.dryrun.security/api-docs/v1/swagger.yaml" target="_blank" rel="noopener noreferrer">https://simple-api.dryrun.security/api-docs/v1/swagger.yaml</a></li>
  <li><strong>Base URL:</strong> <code>https://simple-api.dryrun.security/v1</code></li>
</ul>

<h2 id="authentication">Authentication</h2>

<p>For information on creating and managing API keys, see the <a href="./api-access-keys">API Access Keys</a> page. All API requests require a valid API key sent in the <code>Authorization</code> header using the <code>Bearer</code> scheme.</p>

<h2 id="quick-start">Quick Start</h2>

<p>Most endpoints are scoped to an account. You will need:</p>
<ul>
  <li><code>account_id</code> - provided by the DryRun Security platform (e.g., <code>12345678-1234-1234-1234-1234567890ab</code>)</li>
  <li><code>repository_id</code> - a UUID for a repository</li>
</ul>

<p>Typical workflow:</p>
<ol>
  <li>List your accessible accounts.</li>
  <li>Pick an account, then list repositories in that account.</li>
  <li>Use repository IDs to fetch scans and findings.</li>
</ol>

<h3 id="step-1-list-accounts">Step 1: List accounts</h3>

<pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts"</code></pre>

<p>Example response:</p>

<pre><code>{
  "data": [
    {
      "account_id": "22222222-2222-2222-2222-222222222222",
      "org_name": "SampleOrg",
      ...
    }
  ]
}</code></pre>

<h3 id="step-2-get-repositories">Step 2: Get repositories</h3>

<pre><code>curl -X 'GET' \\
  -H 'Authorization: Bearer $DRYRUN_API_KEY' \\
  'https://simple-api.dryrun.security/v1/accounts/22222222-2222-2222-2222-222222222222/repositories'</code></pre>

<p>Example response:</p>

<pre><code>{
  "data": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "name": "some-demo-repo-name",
      ...
    }
  ]
}</code></pre>

<h3 id="step-3-get-findings">Step 3: Get findings for a repository</h3>

<pre><code>curl -X 'GET' \\
  -H 'Authorization: Bearer $DRYRUN_API_KEY' \\
  'https://simple-api.dryrun.security/v1/accounts/22222222-2222-2222-2222-222222222222/repositories/11111111-1111-1111-1111-111111111111/findings'</code></pre>

<p>Example response:</p>

<pre><code>{
  "data": [
    {
      "id": "00000000-0000-0000-0000-000000000000",
      "dashboard_url": "https://app.dryrun.security/risk-register/44444444-4444-4444-4444-444444444444",
      "severity": "error",
      "type": "Missing Authorization and IDOR in User Deletion",
      "description": "The new DELETE /users/{id} endpoint is registered without any authentication or authorization middleware...",
      "filename": "backend/main.go",
      "line_start": 516,
      "line_end": 553,
      "created_at": "2026-03-03T00:00:00Z"
    },
    ...
  ]
}</code></pre>

<h2 id="endpoint-reference">Endpoint Reference</h2>

<!-- Accounts -->
<h3 id="accounts">Accounts</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts</code>
    <span class="api-endpoint-desc">List all accounts accessible by the API key.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all accounts that the authenticated API key has access to, including organization information.</p>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - accounts listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts"</code></pre>
  </div>
</details>

<!-- Repositories -->
<h3 id="repositories">Repositories</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories</code>
    <span class="api-endpoint-desc">List all repositories for an account.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all repositories associated with the specified account.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - repositories listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories"</code></pre>
  </div>
</details>

<!-- Scans -->
<h3 id="scans">Scans</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/scans</code>
    <span class="api-endpoint-desc">List PR scans for a repository.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>List PR scans for a repository. Supports filtering by PR number, date range, severity, result, and the user who initiated the scan.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
        <tr><td>pr_number</td><td>query</td><td>no</td><td>integer</td><td>Filter by pull request number</td></tr>
        <tr><td>date_from</td><td>query</td><td>no</td><td>string (ISO 8601)</td><td>Return scans on or after this date</td></tr>
        <tr><td>date_to</td><td>query</td><td>no</td><td>string (ISO 8601)</td><td>Return scans on or before this date</td></tr>
        <tr><td>severity</td><td>query</td><td>no</td><td>string</td><td>Filter by highest severity finding: <code>critical</code>, <code>high</code>, <code>medium</code>, <code>low</code>, <code>none</code></td></tr>
        <tr><td>result</td><td>query</td><td>no</td><td>string</td><td>Filter by scan result: <code>pass</code> or <code>fail</code></td></tr>
        <tr><td>initiated_by</td><td>query</td><td>no</td><td>string</td><td>Filter by the username or email of the user who triggered the scan</td></tr>
      </tbody>
    </table>
    <h4>Response Fields</h4>
    <table>
      <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>scan_id</td><td>string</td><td>Unique identifier for the scan</td></tr>
        <tr><td>dashboard_url</td><td>string</td><td>Link to the scan results in the DryRun Security dashboard</td></tr>
        <tr><td>pr_number</td><td>integer</td><td>Pull request number</td></tr>
        <tr><td>pr_title</td><td>string</td><td>Title of the pull request</td></tr>
        <tr><td>pr_status</td><td>string</td><td>Current status of the pull request: <code>open</code>, <code>closed</code>, or <code>merged</code></td></tr>
        <tr><td>scan_date</td><td>string (ISO 8601)</td><td>Date and time the scan was completed</td></tr>
        <tr><td>initiated_by</td><td>string</td><td>Username or email of the user who triggered the scan</td></tr>
        <tr><td>status</td><td>string</td><td>Scan status: <code>pass</code> or <code>fail</code></td></tr>
        <tr><td>summary</td><td>string</td><td>Short plain-text summary of scan results</td></tr>
        <tr><td>vulnerability_summary</td><td>object</td><td>Counts of findings by severity: <code>critical</code>, <code>high</code>, <code>medium</code>, <code>low</code></td></tr>
        <tr><td>risk_threshold</td><td>string</td><td>The highest-severity finding that caused the scan to fail, if applicable</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - scans listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/scans?pr_number=42"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/scans/{id}</code>
    <span class="api-endpoint-desc">Get detailed PR scan results including findings.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Get detailed results for a specific PR scan, including all findings.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
        <tr><td>id</td><td>path</td><td>yes</td><td>string</td><td>Scan ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - scan found</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/scans/{id}"</code></pre>
  </div>
</details>

<!-- Findings -->
<h3 id="findings">Findings</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/findings</code>
    <span class="api-endpoint-desc">List all PR findings for a repository.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>List all PR findings for a repository. Each finding includes a <code>dashboard_url</code> linking to the finding in the DryRun Security dashboard.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - findings listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/findings"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/all_findings</code>
    <span class="api-endpoint-desc">List all findings across PR scans, DeepScans, SCA, and code policies for an account.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>List all findings across PR scans, DeepScans, SCA, and code policies for an account. By default, returns only findings from the latest scan. Results are sorted by newest first.</p>
    <p>Each finding includes a <code>state</code> field indicating its current status: <code>open</code> (present in the latest scan and not triaged), <code>dismissed</code> (triaged with a category such as false positive or accepted risk), or <code>resolved</code> (no longer present in the latest scan). For triaged findings, the response also includes a <code>triage</code> object with the <code>category</code> (<code>false_positive</code>, <code>wont_fix</code>, <code>accepted_risk</code>, <code>in_progress</code>) and <code>category_name</code>.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>days</td><td>query</td><td>yes</td><td>integer</td><td>Filter to findings from the last N days (1-365)</td></tr>
        <tr><td>finding_type</td><td>query</td><td>no</td><td>string</td><td>Filter by finding type. One of: deepscan, pullrequest, sca, code_policy, all. Defaults to 'all'</td></tr>
        <tr><td>severity</td><td>query</td><td>no</td><td>string</td><td>Filter by severity (comma-separated: critical, high, medium, low)</td></tr>
        <tr><td>repository_id</td><td>query</td><td>no</td><td>string</td><td>Filter by repository ID</td></tr>
        <tr><td>branch</td><td>query</td><td>no</td><td>string</td><td>Filter SCA and DeepScan findings by branch name. When omitted, returns findings from the default branch. Does not affect PR or code policy findings.</td></tr>
        <tr><td>all_results</td><td>query</td><td>no</td><td>boolean</td><td>When true, returns all findings including historical scans. Defaults to false (latest scan only).</td></tr>
        <tr><td>page</td><td>query</td><td>no</td><td>integer</td><td>Page number (default: 1)</td></tr>
        <tr><td>per_page</td><td>query</td><td>no</td><td>integer</td><td>Results per page (default: 50, max: 100)</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - findings listed</li>
    </ul>
    <h4>Example response</h4>
    <pre><code>{
  "data": [
    {
      "id": "00000000-0000-0000-0000-000000000000",
      "finding_type": "pullrequest",
      "dashboard_url": "https://app.dryrun.security/risk-register/44444444-4444-4444-4444-444444444444",
      "severity": "high",
      "type": "Missing Authorization and IDOR in User Deletion",
      "description": "The DELETE /users/{id} endpoint is registered without authentication or authorization middleware...",
      "filename": "backend/main.go",
      "line_start": 516,
      "line_end": 553,
      "repository_name": "some-demo-repo-name",
      "state": "open",
      "triage": null,
      "created_at": "2026-03-03T00:00:00Z"
    }
  ]
}</code></pre>
    <h4>Response Fields</h4>
<table>
  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td>id</td><td>string</td><td>Finding ID, used with the triage endpoints</td></tr>
    <tr><td>finding_type</td><td>string</td><td>Source of the finding: <code>deepscan</code>, <code>pullrequest</code>, <code>sca</code>, <code>code_policy</code></td></tr>
    <tr><td>dashboard_url</td><td>string</td><td>Link to the finding in the DryRun Security dashboard</td></tr>
    <tr><td>severity</td><td>string</td><td>Finding severity: <code>critical</code>, <code>high</code>, <code>medium</code>, <code>low</code></td></tr>
    <tr><td>type</td><td>string</td><td>Finding type or title</td></tr>
    <tr><td>label</td><td>string</td><td>Classifier label (e.g. <code>auth_bypass</code>, <code>sqli</code>, <code>idor</code>)</td></tr>
    <tr><td>description</td><td>string</td><td>Finding description</td></tr>
    <tr><td>filename</td><td>string</td><td>File path where the finding was detected</td></tr>
    <tr><td>line_start</td><td>integer</td><td>Starting line number</td></tr>
    <tr><td>line_end</td><td>integer</td><td>Ending line number</td></tr>
    <tr><td>repository_name</td><td>string</td><td>Repository name</td></tr>
    <tr><td>pr_number</td><td>integer</td><td>Pull request number (for <code>pullrequest</code> findings only)</td></tr>
    <tr><td>created_at</td><td>string (ISO 8601)</td><td>When the finding was detected</td></tr>
    <tr><td>state</td><td>string</td><td>Derived finding state: <code>open</code> (from latest scan, not triaged), <code>dismissed</code> (triaged), <code>resolved</code> (not in latest scan)</td></tr>
    <tr><td>triage</td><td>object</td><td>Triage details if triaged, otherwise <code>null</code>. Includes <code>category</code> (<code>false_positive</code>, <code>wont_fix</code>, <code>accepted_risk</code>, <code>in_progress</code>) and <code>category_name</code>.</td></tr>
  </tbody>
</table>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/all_findings?days=30"</code></pre>
  </div>
</details>

<!-- Finding Triage -->
<h3 id="finding-triage">Finding Triage</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-post">POST</span>
    <code>/v1/accounts/{account_id}/findings/{finding_id}/triage</code>
    <span class="api-endpoint-desc">Set a triage category for a finding.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Set a triage category for a finding to track its resolution status.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>finding_id</td><td>path</td><td>yes</td><td>string</td><td>Finding ID</td></tr>
      </tbody>
    </table>
    <h4>Request Body</h4>
    <pre><code>{
  "triage_category": "false_positive"
}</code></pre>
    <p>Valid values for <code>triage_category</code>: <code>false_positive</code>, <code>wont_fix</code>, <code>accepted_risk</code>, <code>in_progress</code>.</p>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - triage category set</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X POST \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"triage_category": "false_positive"}' \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/findings/{finding_id}/triage"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/findings/{finding_id}/triage</code>
    <span class="api-endpoint-desc">Get the triage status for a finding.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve the current triage status for a specific finding.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>finding_id</td><td>path</td><td>yes</td><td>string</td><td>Finding ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - triage status returned</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/findings/{finding_id}/triage"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-delete">DELETE</span>
    <code>/v1/accounts/{account_id}/findings/{finding_id}/triage</code>
    <span class="api-endpoint-desc">Remove the triage category from a finding.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Remove the triage category from a finding, resetting its triage status.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>finding_id</td><td>path</td><td>yes</td><td>string</td><td>Finding ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - triage category removed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X DELETE \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/findings/{finding_id}/triage"</code></pre>
  </div>
</details>

<!-- Deepscans -->
<h3 id="deepscans">Deepscans</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/deepscans</code>
    <span class="api-endpoint-desc">List all deepscans for an account.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all deepscans associated with the specified account.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - deepscans listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/deepscans"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/deepscans</code>
    <span class="api-endpoint-desc">List deepscans for a repository.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all deepscans for a specific repository.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - deepscans listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/deepscans"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-post">POST</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/deepscans</code>
    <span class="api-endpoint-desc">Trigger a new DeepScan on a repository.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Trigger a full-repository DeepScan programmatically. Useful for integrating DeepScan into CI/CD pipelines, scheduled automation, or external workflows. All request body fields are optional. Omitting <code>branch</code> and <code>commit_sha</code> scans the repository&rsquo;s default branch at HEAD.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
      </tbody>
    </table>
    <h4>Request body</h4>
    <table>
      <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td><code>branch</code></td><td>string</td><td>no</td><td>Branch to scan. Defaults to the repository&rsquo;s default branch.</td></tr>
        <tr><td><code>commit_sha</code></td><td>string</td><td>no</td><td>Specific commit SHA to scan.</td></tr>
        <tr><td><code>full_scan</code></td><td>boolean</td><td>no</td><td>Whether to run a full scan. Defaults to <code>true</code>.</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>202</code> - scan triggered</li>
      <li><code>404</code> - repository not found</li>
      <li><code>422</code> - API key has no associated user</li>
      <li><code>429</code> - scan quota exceeded</li>
      <li><code>502</code> - internal invocation error</li>
    </ul>
    <p>Teams running DeepScan through automation should handle <code>429</code> quota exceeded errors gracefully, as accounts have a limit on concurrent scans.</p>
    <h4>Example response</h4>
    <pre><code>{
  "data": {
    "id": "11111111-1111-1111-1111-111111111111",
    "repository_id": "22222222-2222-2222-2222-222222222222",
    "status": "queued"
  }
}</code></pre>
    <h4>Example (curl)</h4>
    <pre><code>curl -X POST \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d &apos;{"branch": "main"}&apos; \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/deepscans"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/deepscans/{deepscan_id}/results</code>
    <span class="api-endpoint-desc">List findings for a specific deepscan.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all findings from a specific deepscan run.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
        <tr><td>deepscan_id</td><td>path</td><td>yes</td><td>string</td><td>DeepScan ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - deepscan results listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/deepscans/{deepscan_id}/results"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/deepscans/{deepscan_id}/sca_results</code>
    <span class="api-endpoint-desc">List SCA findings for a specific DeepScan run.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>List SCA findings for a specific DeepScan run.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
        <tr><td>deepscan_id</td><td>path</td><td>yes</td><td>string</td><td>DeepScan ID</td></tr>
        <tr><td>severity</td><td>query</td><td>no</td><td>string</td><td>Filter by severity (comma-separated). Valid values: critical, high, medium, low</td></tr>
      </tbody>
    </table>
    <h4>Response Fields</h4>
    <p><code>id</code>, <code>dashboard_url</code>, <code>title</code>, <code>description</code>, <code>severity</code>, <code>package_name</code>, <code>package_version</code>, <code>package_ecosystem</code>, <code>cve_id</code>, <code>cvss_score</code>, <code>fixed_version</code>, <code>remediation</code>, <code>locations</code>, <code>references</code>, <code>created_at</code></p>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - SCA results listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer &lt;your-api-key&gt;" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/deepscans/{deepscan_id}/sca_results"</code></pre>
  </div>
</details>

<!-- SBOM -->
<h3 id="sbom">SBOM</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/repositories/{repository_id}/deepscans/{deepscan_id}/sbom</code>
    <span class="api-endpoint-desc">Get the CycloneDX SBOM for a specific DeepScan run.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve SBOM metadata and a time-limited download URL for the CycloneDX SBOM generated during a DeepScan. The <code>download_url</code> is valid until <code>download_url_expires_at</code> and points directly to the SBOM file.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>repository_id</td><td>path</td><td>yes</td><td>string</td><td>Repository ID</td></tr>
        <tr><td>deepscan_id</td><td>path</td><td>yes</td><td>string</td><td>DeepScan ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - SBOM metadata and download URL</li>
      <li><code>404</code> - DeepScan not found</li>
    </ul>
    <h4>Response fields</h4>
    <table>
      <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td><code>deepscan_id</code></td><td>string (uuid)</td><td>ID of the DeepScan that produced this SBOM</td></tr>
        <tr><td><code>repository_id</code></td><td>string (uuid)</td><td>Repository ID</td></tr>
        <tr><td><code>branch</code></td><td>string</td><td>Branch scanned (nullable)</td></tr>
        <tr><td><code>commit_sha</code></td><td>string</td><td>Commit SHA at time of scan (nullable)</td></tr>
        <tr><td><code>format</code></td><td>string</td><td>SBOM format, e.g. <code>cyclonedx</code></td></tr>
        <tr><td><code>component_count</code></td><td>integer</td><td>Total number of components in the SBOM</td></tr>
        <tr><td><code>generated_at</code></td><td>string (date-time)</td><td>When the SBOM was generated (nullable)</td></tr>
        <tr><td><code>vulnerability_summary</code></td><td>object</td><td>Counts of vulnerable components by severity: <code>critical</code>, <code>high</code>, <code>medium</code>, <code>low</code>, <code>total</code></td></tr>
        <tr><td><code>download_url</code></td><td>string (uri)</td><td>Time-limited URL to download the SBOM file</td></tr>
        <tr><td><code>download_url_expires_at</code></td><td>string (date-time)</td><td>Expiry time for the download URL</td></tr>
      </tbody>
    </table>
    <h4>Example response</h4>
    <pre><code>{
  "data": {
    "deepscan_id": "11111111-1111-1111-1111-111111111111",
    "repository_id": "22222222-2222-2222-2222-222222222222",
    "branch": "main",
    "commit_sha": "abc123def456",
    "format": "cyclonedx",
    "component_count": 142,
    "generated_at": "2026-06-01T00:00:00Z",
    "vulnerability_summary": {
      "critical": 1,
      "high": 3,
      "medium": 7,
      "low": 4,
      "total": 15
    },
    "download_url": "https://...",
    "download_url_expires_at": "2026-06-01T01:00:00Z"
  }
}</code></pre>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/repositories/{repository_id}/deepscans/{deepscan_id}/sbom"</code></pre>
  </div>
</details>

<!-- Configurations -->
<h3 id="configurations">Configurations</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/configurations</code>
    <span class="api-endpoint-desc">List configurations for an account.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all configurations associated with the specified account.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - configurations listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-post">POST</span>
    <code>/v1/accounts/{account_id}/configurations</code>
    <span class="api-endpoint-desc">Create a new configuration.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Create a new configuration for the specified account.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Request Body</h4>
    <pre><code>{
  "configuration": {
    "name": "string",
    "configuration": {
      "comment": "disabled",
      "show_scan_confirmation": false,
      "risk_threshold": 0,
      "analyzers": {},
      "code_policies": [
        {
          "id": null,
          "enabled": null,
          "silent": null,
          "blocking": null
        }
      ],
      "notifications": {
        "enabled": false,
        "deduplicate": false,
        "integrationNames": [null]
      }
    }
  },
  "repositories": [
    "00000000-0000-0000-0000-000000000000"
  ]
}</code></pre>
    <h4>Responses</h4>
    <ul>
      <li><code>201</code> - configuration created</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X POST \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"configuration": {"name": "My Config", "configuration": {"comment": "disabled", "risk_threshold": 0, "analyzers": {}}}, "repositories": []}' \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-post">POST</span>
    <code>/v1/accounts/{account_id}/configurations/assign_repositories</code>
    <span class="api-endpoint-desc">Assign a configuration to multiple repositories.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Assign a configuration to one or more repositories by ID, name, or pattern.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Request Body</h4>
    <pre><code>{
  "configuration_id": "00000000-0000-0000-0000-000000000000",
  "repository_ids": [
    "00000000-0000-0000-0000-000000000000"
  ],
  "repository_names": [
    "string"
  ],
  "repository_pattern": "string"
}</code></pre>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - repositories assigned</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X POST \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"configuration_id": "CONFIG_ID", "repository_ids": ["REPO_ID"]}' \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations/assign_repositories"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-post">POST</span>
    <code>/v1/accounts/{account_id}/configurations/bulk_update</code>
    <span class="api-endpoint-desc">Bulk update multiple configurations.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Apply the same updates to multiple configurations at once.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Request Body</h4>
    <pre><code>{
  "configuration_ids": [
    "00000000-0000-0000-0000-000000000000"
  ],
  "updates": {
    "comment": "disabled",
    "show_scan_confirmation": false,
    "risk_threshold": 0,
    "analyzers": {},
    "code_policies": [
      {
        "id": "00000000-0000-0000-0000-000000000000",
        "enabled": false,
        "silent": false,
        "blocking": false
      }
    ],
    "notifications": {
      "enabled": false,
      "deduplicate": false,
      "integrationNames": ["string"]
    }
  }
}</code></pre>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - configurations updated</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X POST \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"configuration_ids": ["CONFIG_ID_1", "CONFIG_ID_2"], "updates": {"risk_threshold": 5}}' \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations/bulk_update"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/configurations/{id}</code>
    <span class="api-endpoint-desc">Get a single configuration.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve details for a specific configuration.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>id</td><td>path</td><td>yes</td><td>string</td><td>Configuration ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - configuration found</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations/{id}"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-put">PUT</span>
    <code>/v1/accounts/{account_id}/configurations/{id}</code>
    <span class="api-endpoint-desc">Update a configuration.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Update an existing configuration.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>id</td><td>path</td><td>yes</td><td>string</td><td>Configuration ID</td></tr>
      </tbody>
    </table>
    <h4>Request Body</h4>
    <pre><code>{
  "configuration": {
    "name": "string",
    "configuration": {
      "comment": "disabled",
      "show_scan_confirmation": false,
      "risk_threshold": 0,
      "analyzers": {},
      "code_policies": [
        {
          "id": null,
          "enabled": null,
          "silent": null,
          "blocking": null
        }
      ],
      "notifications": {
        "enabled": false,
        "deduplicate": false,
        "integrationNames": [null]
      }
    }
  }
}</code></pre>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - configuration updated</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X PUT \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"configuration": {"name": "Updated Config", "configuration": {"risk_threshold": 5}}}' \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations/{id}"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-patch">PATCH</span>
    <code>/v1/accounts/{account_id}/configurations/{id}</code>
    <span class="api-endpoint-desc">Partially update a configuration.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Apply a partial update to an existing configuration. Only the fields provided in the request body are updated.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>id</td><td>path</td><td>yes</td><td>string</td><td>Configuration ID</td></tr>
      </tbody>
    </table>
    <h4>Request Body</h4>
    <pre><code>{
  "configuration": {
    "name": "string",
    "configuration": {
      "comment": "disabled",
      "show_scan_confirmation": false,
      "risk_threshold": 0,
      "analyzers": {},
      "code_policies": [
        {
          "id": null,
          "enabled": null,
          "silent": null,
          "blocking": null
        }
      ],
      "notifications": {
        "enabled": false,
        "deduplicate": false,
        "integrationNames": [null]
      }
    }
  }
}</code></pre>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - configuration updated</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X PATCH \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"configuration": {"configuration": {"risk_threshold": 5}}}' \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations/{id}"</code></pre>
  </div>
</details>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-delete">DELETE</span>
    <code>/v1/accounts/{account_id}/configurations/{id}</code>
    <span class="api-endpoint-desc">Delete a configuration.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Permanently delete a configuration. This action cannot be undone.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>id</td><td>path</td><td>yes</td><td>string</td><td>Configuration ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - configuration deleted</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl -X DELETE \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/configurations/{id}"</code></pre>
  </div>
</details>

<!-- Analyzers -->
<h3 id="analyzers">Analyzers</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/analyzers</code>
    <span class="api-endpoint-desc">List available analyzers.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all enabled and visible analyzers. Use the <code>slug</code> field as the key in configuration analyzer settings.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - analyzers listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/analyzers"</code></pre>
  </div>
</details>

<!-- Custom Policies -->
<h3 id="custom-policies">Custom Policies</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/custom_policies</code>
    <span class="api-endpoint-desc">List all Custom Code Policies for an account.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve all Custom Code Policies associated with the specified account.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - custom policies listed</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/custom_policies"</code></pre>
  </div>
</details>

<!-- Insights -->
<h3 id="insights">Insights</h3>

<details class="api-endpoint">
  <summary class="api-endpoint-summary">
    <span class="method-get">GET</span>
    <code>/v1/accounts/{account_id}/insights</code>
    <span class="api-endpoint-desc">Retrieve the daily insights digest.</span>
  </summary>
  <div class="api-endpoint-body">
    <p>Retrieve the daily insights digest for an account. Supports an optional <code>date</code> query parameter in <code>YYYY-MM-DD</code> format.</p>
    <h4>Parameters</h4>
    <table>
      <thead><tr><th>Name</th><th>In</th><th>Required</th><th>Type</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td>account_id</td><td>path</td><td>yes</td><td>string</td><td>Account ID</td></tr>
        <tr><td>date</td><td>query</td><td>no</td><td>string</td><td>Date in YYYY-MM-DD format</td></tr>
      </tbody>
    </table>
    <h4>Responses</h4>
    <ul>
      <li><code>200</code> - insights returned</li>
    </ul>
    <h4>Example (curl)</h4>
    <pre><code>curl \\
  -H "Authorization: Bearer $DRYRUN_API_KEY" \\
  "https://simple-api.dryrun.security/v1/accounts/{account_id}/insights?date=2026-01-15"</code></pre>
  </div>
</details>

<h2 id="conventions">Conventions</h2>

<ul>
  <li><strong>IDs and scoping:</strong> <code>account_id</code> is required for most endpoints. <code>repository_id</code> is required for repository-scoped endpoints.</li>
  <li><strong>Response shape:</strong> Most list endpoints return a top-level <code>data</code> array.</li>
  <li><strong>Errors:</strong> If an item is not found, endpoints return <code>404</code> with <code>{"error": "not found"}</code>.</li>
</ul>

<h2 id="support">Support</h2>

<p>If you have questions about authentication, account access, or expected responses, contact DryRun Security support and include the endpoint URL you called, the HTTP status code, and the <code>request_id</code> header (if present).</p>
''',
}


# -- Integrations --

PAGES['slack-integration'] = {
    'title': 'Slack Integration',
    'description': 'Receive DryRun Security alerts and notifications in Slack.',
    'section': 'Integrations',
    'content': '''
<p>In this section we set up an integration webhook and use it to receive event notifications from DryRun Security. There is a dedicated Slack integration and a Generic webhook option. The configuration steps are identical for both.</p>

<p><strong>Prerequisite:</strong> You'll need to have already created a Webhook URL on the system you wish to integrate. Messages sent are JSON-formatted POST requests.</p>


<h2 id="notifications-setup-walkthrough">Notification Setup Walkthrough</h2>

<p>The Integrations page in the DryRun Security dashboard shows available notification channels.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/01-integrations.png" alt="Notification integrations page in DryRun Security" loading="lazy"></figure>

<h3 id="slack-integration">Slack Integration</h3>
<p>Connect DryRun Security to Slack for real-time security alerts.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/02-slack-setup.png" alt="Slack integration setup" loading="lazy"></figure>

<h3 id="generic-webhook">Generic Webhook</h3>
<p>Configure a generic webhook to send notifications to any HTTP endpoint.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/03-generic-webhook.png" alt="Generic webhook configuration" loading="lazy"></figure>

<h3 id="integration-scope">Integration Scope</h3>
<p>Global integrations notify on findings across all repositories in your organization.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/04-global-integration.png" alt="Global integration settings" loading="lazy"></figure>

<p>Targeted integrations notify only for specific repositories.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/05-targeted-integration.png" alt="Targeted integration settings" loading="lazy"></figure>

<h3 id="risk-triggers">Risk Level Triggers</h3>
<p>Configure which risk levels trigger notifications.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/06-risk-trigger.png" alt="Risk level trigger configuration" loading="lazy"></figure>

<p>Use the test button to validate your notification configuration.</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/07-test-notification.png" alt="Test notification button" loading="lazy"></figure>

<h3 id="webhook-format">Webhook Format</h3>
<p>Example JSON body sent by the generic webhook:</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/08-webhook-body.png" alt="Generic webhook JSON body example" loading="lazy"></figure>

<p>Example of a Slack notification message:</p>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/09-slack-message.png" alt="Slack notification message example" loading="lazy"></figure>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/10-notification-config.png" alt="Notification configuration overview" loading="lazy"></figure>
<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/notifications/11-notification-list.png" alt="List of configured notifications" loading="lazy"></figure>

<h2 id="configure-global-integration">Configure a Global Integration</h2>

<p>A global integration works across all repositories in your organization with no additional configuration required.</p>

<ol>
  <li>Log in to the DryRun Security portal at <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">https://app.dryrun.security</a>.</li>
  <li>Navigate to <strong>Settings</strong>, then click <strong>Integrations</strong>.</li>
  <li>Click <strong>Details</strong> on the integration card you want to configure.</li>
  <li>In the <strong>Webhook URL</strong> box, add the URL for the target webhook to receive notifications.</li>
  <li>Choose a <strong>Risk Level</strong>. Notifications will be triggered when a change has a risk at or above the chosen level.</li>
  <li>Leave <strong>Enabled</strong> selected.</li>
  <li>Leave <strong>Global</strong> checked.</li>
  <li>Click <strong>Save</strong>.</li>
</ol>

<p>Once saved, the <strong>Test</strong> button will be enabled. Click it to send a test message to the Webhook URL to validate the setup.</p>

<h2 id="configure-targeted-integration">Configure a Targeted Integration</h2>

<p>A targeted integration can be used to receive notifications about one or more specific repositories. It must be assigned to a Configuration.</p>

<ol>
  <li>Follow steps 1–5 above.</li>
  <li>Leave <strong>Enabled</strong> selected.</li>
  <li>Uncheck the <strong>Global</strong> option. A <strong>Name</strong> box will appear - this name is used to reference the integration in a Configuration.</li>
  <li>Click <strong>Save</strong>, then click <strong>Test</strong> to validate.</li>
</ol>

<p><strong>Note:</strong> You'll need to add your webhook to a Configuration before notifications will be sent.</p>

<h2 id="add-to-configuration">Add Notification to a Configuration</h2>

<ol>
  <li>Navigate to <strong>Settings &gt; Configurations</strong>.</li>
  <li>Select the Configuration you want to edit.</li>
  <li>Toggle on <strong>Notifications Enabled</strong>.</li>
  <li>Select the desired webhook name(s) from the <strong>Integrations</strong> dropdown.</li>
  <li>Click <strong>Save</strong>.</li>
</ol>

<p>Changes in the repository that match the integration's risk level will now trigger a notification.</p>

''',
}

PAGES['webhook-integration'] = {
    'title': 'Webhook Integration',
    'description': 'Receive a POST request to any HTTP endpoint when DryRun Security detects a finding on a pull request.',
    'section': 'Integrations',
    'content': '''
<h2 id="overview">Overview</h2>

<p>DryRun Security sends a webhook POST request to a configured endpoint when a finding is detected on a pull request. Use this to route finding data to custom dashboards, ticketing systems, SIEMs, or automation tools.</p>

<p>Webhook setup is a two-step process: first create the webhook in Integrations, then attach it to a configuration to activate it for specific repositories.</p>

<h2 id="step-1-create-a-webhook">Step 1: Create a Webhook</h2>

<ol>
  <li>In the left nav of the <a href="https://app.dryrun.security" target="_blank" rel="noopener noreferrer">DryRun Security dashboard</a>, click <strong>Integrations</strong>.</li>
  <li>Find the <strong>Generic Webhook</strong> entry and click <strong>Details</strong>.</li>
  <li>Click <strong>Add Webhook +</strong>.</li>
  <li>Enter a <strong>Name</strong> for the webhook.</li>
  <li>Enter the <strong>Webhook URL</strong> of your endpoint.</li>
  <li>Select a <strong>Risk Level</strong>. Findings at the selected severity and above will trigger the webhook.</li>
</ol>

<table>
  <thead>
    <tr><th>Risk Level</th><th>Findings included</th></tr>
  </thead>
  <tbody>
    <tr><td>All</td><td>All findings regardless of severity</td></tr>
    <tr><td>Medium</td><td>Medium, High, and Critical</td></tr>
    <tr><td>High</td><td>High and Critical</td></tr>
    <tr><td>Critical</td><td>Critical only</td></tr>
  </tbody>
</table>

<ol start="7">
  <li>Use the <strong>Enabled</strong> toggle to activate or pause the webhook at any time.</li>
  <li>Check <strong>Global</strong> to trigger this webhook for all repositories, regardless of configuration. Leave it unchecked to activate it only through specific configurations (see Step 2).</li>
  <li>Click <strong>Save</strong>.</li>
</ol>

<h2 id="step-2-activate-for-repositories">Step 2: Activate for Repositories</h2>

<p>A webhook only fires for repositories included in a configuration with notifications enabled. To attach your webhook to a configuration:</p>

<ol>
  <li>Navigate to <strong>Configurations</strong> in the dashboard.</li>
  <li>Click <strong>Edit</strong> on an existing configuration.</li>
  <li>Toggle <strong>Notifications Enabled</strong> on.</li>
  <li>In the <strong>Select Integrations</strong> dropdown, choose the webhook you created in Step 1.</li>
  <li>Click <strong>Save</strong> at the bottom of the page.</li>
</ol>

<p>The webhook will now fire for any PR finding in the repositories covered by that configuration.</p>

<p class="docs-note">If you have not created a webhook yet, click <strong>Add +</strong> on the Configurations page to go directly to the Generic Webhook setup page.</p>

<h2 id="payload-format">Payload Format</h2>

<p>DryRun Security sends an HTTP POST with a JSON body to your endpoint when a scan completes. The body includes PR context, scan metadata, and the full list of findings.</p>

<pre><code>{
    "dashboard_url": "https://app.dryrun.security/pull-requests/00000000-0000-0000-0000-000000000000",
    "github_url": "https://github.com/org/repo/pull/123",
    "risk_threshold": "high",
    "org": "your-org",
    "repo_name": "your-repo",
    "repo_full_name": "your-org/your-repo",
    "pr_number": 123,
    "pr_title": "Add payment endpoint",
    "pr_status": "open",
    "branch": "feature/payments",
    "commit_author": "developer",
    "issue_status": "open",
    "run_time": "2026-06-09T16:48:44.960558Z",
    "results": [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "finding_type": "pullrequest",
            "type": "Missing Authorization on Payment Endpoint",
            "filename": "src/payments/handler.py",
            "line_start": 42,
            "line_end": 58,
            "description": "The POST /payments endpoint does not verify the caller's identity...",
            "risk": "high"
        }
    ]
}</code></pre>

<h3 id="top-level-fields">Top-level fields</h3>

<table>
  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>dashboard_url</code></td><td>string</td><td>Link to the PR in the DryRun Security dashboard</td></tr>
    <tr><td><code>github_url</code></td><td>string</td><td>Link to the pull request in your SCM</td></tr>
    <tr><td><code>risk_threshold</code></td><td>string</td><td>Highest risk level among all findings in this scan: <code>critical</code>, <code>high</code>, <code>medium</code>, or <code>low</code>. Returns <code>passing</code> when no findings meet the configured Risk Level threshold.</td></tr>
    <tr><td><code>org</code></td><td>string</td><td>Organization name</td></tr>
    <tr><td><code>repo_name</code></td><td>string</td><td>Repository name</td></tr>
    <tr><td><code>repo_full_name</code></td><td>string</td><td>Full repository identifier in <code>org/repo</code> format</td></tr>
    <tr><td><code>pr_number</code></td><td>integer</td><td>Pull request number</td></tr>
    <tr><td><code>pr_title</code></td><td>string</td><td>Pull request title</td></tr>
    <tr><td><code>pr_status</code></td><td>string</td><td>Pull request status: <code>open</code> or <code>closed</code></td></tr>
    <tr><td><code>branch</code></td><td>string</td><td>Branch the pull request was opened from</td></tr>
    <tr><td><code>commit_author</code></td><td>string</td><td>Author of the triggering commit</td></tr>
    <tr><td><code>issue_status</code></td><td>string</td><td>Whether any open findings remain: <code>open</code> or <code>resolved</code></td></tr>
    <tr><td><code>run_time</code></td><td>string (date-time)</td><td>Timestamp of when the scan completed</td></tr>
    <tr><td><code>results</code></td><td>array</td><td>List of findings from this scan. Empty when no findings meet the configured Risk Level.</td></tr>
  </tbody>
</table>

<h3 id="result-fields">Result fields</h3>

<table>
  <thead><tr><th>Field</th><th>Type</th><th>Description</th></tr></thead>
  <tbody>
    <tr><td><code>id</code></td><td>string (uuid)</td><td>Unique finding ID</td></tr>
    <tr><td><code>finding_type</code></td><td>string</td><td>Source of the finding: <code>pullrequest</code>, <code>code_policy</code>, <code>deepscan</code>, or <code>sca</code></td></tr>
    <tr><td><code>type</code></td><td>string</td><td>Finding name</td></tr>
    <tr><td><code>filename</code></td><td>string</td><td>File where the finding was detected</td></tr>
    <tr><td><code>line_start</code></td><td>integer</td><td>Starting line of the affected code</td></tr>
    <tr><td><code>line_end</code></td><td>integer</td><td>Ending line of the affected code</td></tr>
    <tr><td><code>description</code></td><td>string</td><td>Full finding description</td></tr>
    <tr><td><code>risk</code></td><td>string</td><td>Risk level of this finding: <code>critical</code>, <code>high</code>, <code>medium</code>, or <code>low</code></td></tr>
  </tbody>
</table>

''',
}

PAGES['jira-integration'] = {
    'title': 'Jira Integration',
    'description': 'Connect DryRun Security to Jira using automation middleware for automated ticket creation and deduplication.',
    'section': 'Integrations',
    'content': '''
<h2 id="overview">Overview</h2>

<p>DryRun Security does not have a native Jira integration today, but admins can connect DryRun Security to Jira using an automation middleware tool, either <strong>Tines</strong> or <strong>Zapier</strong>. DryRun Security sends a webhook when a finding is detected on a PR scan. The middleware receives the webhook, unpacks the finding details, checks Jira for an existing ticket for that finding, and either creates a new ticket or updates the existing one.</p>

<p>When a PR is scanned and a finding is returned, DryRun Security sends a POST request with a JSON payload containing the event type, timestamp, repository, pull request number, and a finding object with <code>id</code>, <code>severity</code>, <code>category</code>, <code>title</code>, <code>file</code>, <code>line</code>, and <code>description</code>. See the <a href="./webhook-integration">Webhook Integration</a> page for the full payload structure and configuration details.</p>

<h2 id="prerequisites">Prerequisites</h2>

<ul>
  <li>DryRun Security webhook configured (see <a href="./webhook-integration">Webhook Integration</a>)</li>
  <li>A Jira project with API access (Jira API token and project key)</li>
  <li>A <a href="https://www.tines.com/" target="_blank" rel="noopener noreferrer">Tines</a> or <a href="https://zapier.com/" target="_blank" rel="noopener noreferrer">Zapier</a> account</li>
</ul>

<h2 id="jira-field-mapping">Jira Field Mapping</h2>

<p>Map DryRun Security finding fields to Jira ticket fields as follows:</p>

<table>
  <thead>
    <tr><th>Jira Field</th><th>Value from DryRun</th></tr>
  </thead>
  <tbody>
    <tr><td>Summary</td><td><code>[DryRun] {finding.title} in {finding.file}:{finding.line}</code></td></tr>
    <tr><td>Description</td><td>Full finding description, repository, PR number, severity, file path, finding ID</td></tr>
    <tr><td>Labels</td><td><code>dryrun-security</code>, <code>{finding.severity}</code>, <code>{finding.category}</code>, <code>{finding.id}</code> (used for deduplication)</td></tr>
    <tr><td>Priority</td><td>Critical &rarr; Highest, High &rarr; High, Medium &rarr; Medium, Low &rarr; Low</td></tr>
  </tbody>
</table>

<p><strong>Note:</strong> The <code>finding.id</code> label is used as the deduplication key to check whether a ticket already exists.</p>

<h2 id="tines-workflow">Tines Workflow</h2>

<p><a href="https://www.tines.com/" target="_blank" rel="noopener noreferrer">Tines</a> is a security automation platform. Use it to receive DryRun Security webhooks and automate Jira ticket creation with deduplication logic.</p>

<ol>
  <li>
    <strong>Create a Webhook action in Tines:</strong> Add a &ldquo;Webhook&rdquo; action as the trigger. Tines will generate a unique URL. Copy this URL and use it as the DryRun Security webhook destination in <strong>Settings &gt; Integrations</strong>.
  </li>
  <li>
    <strong>Add a Filter action:</strong> Filter on <code>event == &quot;new_finding&quot;</code> to ensure the workflow only runs for new findings (not scan completions or resolved findings).
  </li>
  <li>
    <strong>Search Jira for an existing ticket:</strong> Add an HTTP Request action to call the Jira REST API:
<pre><code>GET {JIRA_BASE_URL}/rest/api/3/search
  ?jql=project={PROJECT_KEY} AND labels=&quot;{finding.id}&quot; AND statusCategory != Done
Authorization: Basic {base64(email:api_token)}</code></pre>
    <p>This checks whether a ticket already exists for this specific finding by searching for its unique ID in labels.</p>
  </li>
  <li>
    <strong>Add a Branch (condition) action:</strong> Check the <code>issues</code> array in the Jira search response:
    <ul>
      <li>If <code>issues.length &gt; 0</code> &rarr; ticket exists &rarr; go to Step 5</li>
      <li>If <code>issues.length == 0</code> &rarr; no ticket &rarr; go to Step 6</li>
    </ul>
  </li>
  <li>
    <strong>Add a comment to the existing Jira ticket.</strong> HTTP Request action:
<pre><code>POST {JIRA_BASE_URL}/rest/api/3/issue/{issues[0].id}/comment
Body:
{
  &quot;body&quot;: &quot;DryRun Security flagged this finding again on PR #{pull_request} in {repository} at {timestamp}.&quot;
}</code></pre>
  </li>
  <li>
    <strong>Create a new Jira ticket.</strong> HTTP Request action:
<pre><code>POST {JIRA_BASE_URL}/rest/api/3/issue
Body:
{
  &quot;fields&quot;: {
    &quot;project&quot;: { &quot;key&quot;: &quot;{PROJECT_KEY}&quot; },
    &quot;summary&quot;: &quot;[DryRun] {finding.title} in {finding.file}:{finding.line}&quot;,
    &quot;description&quot;: {
      &quot;type&quot;: &quot;doc&quot;, &quot;version&quot;: 1,
      &quot;content&quot;: [
        { &quot;type&quot;: &quot;paragraph&quot;, &quot;content&quot;: [{ &quot;type&quot;: &quot;text&quot;, &quot;text&quot;: &quot;PR: #{pull_request} | Repository: {repository}&quot; }] },
        { &quot;type&quot;: &quot;paragraph&quot;, &quot;content&quot;: [{ &quot;type&quot;: &quot;text&quot;, &quot;text&quot;: &quot;Severity: {finding.severity} | Category: {finding.category}&quot; }] },
        { &quot;type&quot;: &quot;paragraph&quot;, &quot;content&quot;: [{ &quot;type&quot;: &quot;text&quot;, &quot;text&quot;: &quot;File: {finding.file}:{finding.line}&quot; }] },
        { &quot;type&quot;: &quot;paragraph&quot;, &quot;content&quot;: [{ &quot;type&quot;: &quot;text&quot;, &quot;text&quot;: &quot;Finding ID: {finding.id}&quot; }] },
        { &quot;type&quot;: &quot;paragraph&quot;, &quot;content&quot;: [{ &quot;type&quot;: &quot;text&quot;, &quot;text&quot;: &quot;{finding.description}&quot; }] }
      ]
    },
    &quot;issuetype&quot;: { &quot;name&quot;: &quot;Bug&quot; },
    &quot;labels&quot;: [&quot;dryrun-security&quot;, &quot;{finding.severity}&quot;, &quot;{finding.id}&quot;],
    &quot;priority&quot;: { &quot;name&quot;: &quot;{mapped priority}&quot; }
  }
}</code></pre>
  </li>
</ol>

<p><strong>Workflow diagram:</strong> Webhook &rarr; Filter (<code>new_finding</code>) &rarr; Search Jira &rarr; Branch &rarr; [Comment on existing ticket | Create new ticket]</p>

<h2 id="zapier-workflow">Zapier Workflow</h2>

<p><a href="https://zapier.com/" target="_blank" rel="noopener noreferrer">Zapier</a> is a no-code automation platform. Use it to build the same DryRun Security &rarr; Jira workflow without writing code.</p>

<ol>
  <li>
    <strong>Create a new Zap and choose &ldquo;Webhooks by Zapier&rdquo; as the trigger:</strong> Select &ldquo;Catch Hook&rdquo; as the trigger event. Zapier generates a webhook URL. Copy it and configure it as the DryRun Security webhook destination in <strong>Settings &gt; Integrations</strong>.
  </li>
  <li>
    <strong>Test the trigger:</strong> Use DryRun Security&rsquo;s <strong>Test</strong> button in the webhook configuration to send a sample payload. This lets Zapier detect the field structure from the finding payload.
  </li>
  <li>
    <strong>Add a Filter step:</strong> Insert a &ldquo;Filter&rdquo; action and set the condition: <code>event</code> (exactly) <code>new_finding</code>. This ensures the Zap only continues for new findings.
  </li>
  <li>
    <strong>Add a &ldquo;Find Issue&rdquo; Jira action:</strong> Choose the Jira Cloud app and select &ldquo;Find Issue.&rdquo; Configure the search using JQL:
<pre><code>project = {PROJECT_KEY} AND labels = &quot;{finding.id}&quot; AND statusCategory != Done</code></pre>
    <p>Map <code>finding.id</code> from the DryRun Security payload as the label value.</p>
  </li>
  <li>
    <strong>Add a &ldquo;Paths&rdquo; step (two branches)</strong>:
    <ul>
      <li>
        <strong>Path A: Ticket exists</strong> (Find Issue returned a result):
        <ul>
          <li>Add a Jira &ldquo;Add Comment to Issue&rdquo; action.</li>
          <li>Set the Issue ID from the Find Issue result.</li>
          <li>Comment body: <code>DryRun Security flagged this finding again on PR #{pull_request} in {repository}.</code></li>
        </ul>
      </li>
      <li>
        <strong>Path B: No ticket</strong> (Find Issue returned no result):
        <ul>
          <li>Add a Jira &ldquo;Create Issue&rdquo; action.</li>
          <li>Map fields from the DryRun Security payload:
            <ul>
              <li>Summary: <code>[DryRun] {finding.title} in {finding.file}:{finding.line}</code></li>
              <li>Description: <code>PR: #{pull_request} | Repository: {repository} | Severity: {finding.severity} | File: {finding.file}:{finding.line} | Finding ID: {finding.id} | {finding.description}</code></li>
              <li>Labels: <code>dryrun-security</code>, severity value, finding ID</li>
              <li>Priority: map from severity</li>
              <li>Issue Type: Bug</li>
            </ul>
          </li>
        </ul>
      </li>
    </ul>
  </li>
  <li>
    <strong>Turn on the Zap:</strong> Once all steps are configured and tested, enable the Zap.
  </li>
</ol>

''',
}

PAGES['api-access-keys'] = {
    'title': 'API Access Keys',
    'description': 'Create and manage API access keys for programmatic access to DryRun Security.',
    'section': 'Integrations',
    'content': '''
<h2 id="overview">Overview</h2>

<p>API access keys allow you to authenticate with the <a href="./dryrun-api">DryRun API</a> for programmatic access to DryRun Security. Use API keys to integrate DryRun Security into your CI/CD pipelines, custom tooling, or automation workflows.</p>

<h2 id="creating-keys">Creating an API Key</h2>

<p>Navigate to <strong>Settings &gt; Access Keys</strong> in the sidebar at <a href="https://app.dryrun.security/settings/access-keys" target="_blank" rel="noopener noreferrer">app.dryrun.security</a>. The Access Keys page provides two sections:</p>

<ul>
  <li><strong>API Keys</strong> - Create and manage API keys for your applications. Click <strong>+ Generate New API Key</strong> to create a new key.</li>
  <li><strong>Your API Keys</strong> - View and manage your existing API keys. You can revoke any key at any time.</li>
</ul>

<div class="callout callout-warning">
  <strong>Keep your API keys secure.</strong> Treat API keys like passwords. Never share them in public repositories, client-side code, or unsecured locations. If a key is compromised, revoke it immediately from the Access Keys page.
</div>

<p>The API key must be scoped to at least one account. One API key can be used to access more than one account. After creating the key, copy it to a safe place - it will not be shown again.</p>

<h2 id="using-keys">Using API Keys</h2>

<p>Send your API key in the <code>Authorization</code> header using the <code>Bearer</code> scheme:</p>

<pre><code>Authorization: Bearer dryrunsec_**********************</code></pre>

<h2 id="key-management">Key Management</h2>

<ul>
  <li><strong>Rotate keys regularly</strong> - Generate a new key and revoke the old one periodically.</li>
  <li><strong>Use descriptive names</strong> - Name keys after their use case for easy identification.</li>
  <li><strong>Revoke unused keys</strong> - Delete keys that are no longer in use from the API Keys settings page.</li>
  <li><strong>Never commit keys to source control</strong> - Use environment variables or secret management tools.</li>
</ul>

<h2 id="rate-limits">Rate Limits</h2>

<p>API keys are subject to rate limits to ensure platform stability. Current limits are displayed in the API Keys settings page. If you need higher limits, contact <a href="https://dryrun.security" target="_blank" rel="noopener noreferrer">DryRun Security support</a>.</p>
''',
}

PAGES['dryrun-skill'] = {
    'title': 'DryRun Skill',
    'description': 'The DryRun Security skill gives your AI coding tool the context it needs to author, review, and remediate code securely.',
    'section': 'Integrations',
    'content': '''
<h2 id="overview">Overview</h2>

<p>AI coding tools are fast, but they operate in a silo. Left to their defaults, they may skip pull requests, ignore organizational best practices, and even when a PR is opened, they will not check for security findings unless explicitly told to. The DryRun Security skill closes that gap, giving the AI the context it needs to follow proper PR workflow and treat security findings as a required step in the process.</p>

<p>Works with Claude Code, Codex, Cursor, Windsurf, and VS Code.</p>

<h2 id="what-the-skill-does">What the DryRun Security Skill Does</h2>

<p>The DryRun Security skill equips your AI coding tool with the context it needs to author, review, and remediate code securely. It guides the AI through three steps: opening changes as a pull request so DryRun Security can scan them, waiting for and surfacing any findings, and applying well-informed fixes when vulnerabilities are found.</p>

<blockquote>
<p><strong>Note:</strong> For most AI coding tools this workflow is packaged as a single skill. For Claude Code, it is split across two skills - one covering Author and Review, one covering Remediate. The workflow and experience are the same either way.</p>
</blockquote>

<h3 id="author">Author</h3>

<p>The skill instructs the AI coding tool to open a pull request rather than push changes directly to the main branch. This is what makes DryRun Security scanning possible. DryRun Security analyzes pull requests in real time. If code is pushed directly to main, there is no pull request to scan and no opportunity to catch vulnerabilities before they land.</p>

<h3 id="review">Review</h3>

<p>The skill gives the AI coding tool awareness that DryRun Security will scan the open pull request and post findings as a comment in GitHub or GitLab. After the PR is opened, the AI polls for that comment, waits for findings to be posted, and presents each one to the developer. After every commit to the branch, the AI re-polls for new findings and presents them, keeping the developer informed throughout the lifecycle of the PR.</p>

<h3 id="remediate">Remediate</h3>

<p>When the developer wants to fix a finding, the skill gives the AI coding tool additional context to work from: how DryRun Security identified the vulnerability, background on the vulnerability class, OWASP guidance, and relevant framework documentation. This context helps the AI produce a fix that is accurate, minimal, and appropriate for the codebase.</p>

<h2 id="example-prompts">Example Prompts</h2>

<p>To start the Author and Review workflow, describe your change and include a prompt to open a pull request. The skill takes over from there:</p>

<pre><code>[Describe the change you want]. When ready, open a pull request.</code></pre>

<p>To invoke Remediate, paste the DryRun Security finding directly. The skill extracts the vulnerability details and applies a contextual fix:</p>

<pre><code>Fix this DryRun Security finding: [paste the finding comment]</code></pre>

<h2 id="installation">Installation</h2>

<p>Install instructions for each tool are available in the DryRun Security dashboard under <strong>Settings &gt; Integrations</strong>.</p>
''',
}


PAGES['dashboard'] = {
    'title': 'Dashboard',
    'description': 'The Security Dashboard provides a real-time view of your organization\'s security posture across every repository and pull request DryRun Security monitors, with overview metrics and trend charts scoped to a configurable time window.',
    'section': 'Platform',
    'content': '''

<h2 id="overview">Overview</h2>

<p>The Security Dashboard provides a real-time view of your organization's security posture across every repository and pull request DryRun Security monitors. All metrics are scoped to a configurable time window - 24 hours, 7 days, 30 days, or 90 days - so security and engineering teams can evaluate both current state and longer-term trends.</p>

<h2 id="overview-metrics">Overview Metrics</h2>

<p>Six summary tiles appear across the top of the dashboard, giving an at-a-glance picture of activity and risk across the selected period.</p>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/dashboard/dashboard-chart.jpg" alt="DryRun Security Dashboard overview" loading="lazy"></figure>

<h3 id="prs-scanned">PRs Scanned</h3>

<p>The total number of pull requests DryRun Security analyzed in the selected window. This is your coverage signal - every PR that entered review was evaluated for security issues across the repositories connected to your account.</p>

<h3 id="total-findings">Total Findings</h3>

<p>The cumulative number of security findings identified across all scanned PRs during the period. This represents the full volume of security signals your team is working through, spanning all severity levels and vulnerability classes.</p>

<h3 id="merged-prs">Merged PRs</h3>

<p>The total number of PRs merged during the period. Read alongside PRs Scanned and Merged PRs w/ Risk, this provides a clear picture of code velocity relative to security outcomes.</p>

<h3 id="merged-prs-with-risk">Merged PRs w/ Risk</h3>

<p>PRs authored by a developer and merged while carrying at least one unresolved finding. This is a direct measure of residual risk entering your codebase. A low count relative to total merged PRs indicates your team is consistently resolving findings before code ships.</p>

<h3 id="improvement-rate">Improvement Rate</h3>

<p>The percentage of scanned PRs flagged as improved during the selected period. A PR is considered improved when a finding identified in one scan is no longer present in the next scan of that same PR - meaning the developer addressed it within the review cycle, before merge. A high improvement rate indicates findings are being caught and fixed at the point of introduction rather than carried forward.</p>

<h3 id="hardcoded-credentials">Hardcoded Credentials</h3>

<p>A dedicated count of credential-related findings - API keys, tokens, secrets, and similar sensitive values - across all scanned PRs. Hardcoded credentials represent one of the highest-impact risks in any codebase and are surfaced separately so they remain visible regardless of overall finding volume.</p>

<h2 id="charts">Charts</h2>

<h3 id="findings-over-time">Findings Over Time</h3>

<p>A stacked line chart tracking findings at each severity level - Critical, High, Medium, and Low - across the selected time window. Each line moves independently, so you can see whether risk is shifting between severity tiers over time, not just whether the total is going up or down.</p>

<h3 id="findings-by-repository">Findings by Repository</h3>

<p>A ranked view of which repositories are generating the most findings. This helps security and platform teams understand where risk is concentrated and prioritize remediation effort across the portfolio.</p>

<h3 id="severity-distribution">Severity Distribution</h3>

<p>A breakdown of active findings by severity - Critical, High, Medium, and Low - with a count and percentage for each tier. The center of the chart shows the total. Use this to assess whether your open risk is weighted toward high-severity issues that need immediate attention or spread across lower-severity findings.</p>

<h3 id="findings-by-class">Findings by Class</h3>

<p>A ranked breakdown by vulnerability type - such as Hardcoded Credentials, Cross-Site Scripting, SQL Injection, and others. Recurring patterns within a class often point to a shared dependency, an architectural pattern, or a training gap, making this view useful for identifying systemic issues beyond individual findings.</p>

<h3 id="developer-activity">Developer Activity</h3>

<p>A per-developer breakdown showing PRs opened and the subset of those PRs merged with at least one unresolved finding. This view helps AppSec and engineering leads understand how security habits are distributed across the team and where additional guidance may be needed.</p>

<figure class="docs-screenshot"><img src="{asset_prefix}assets/images/dashboard/dashboard-lower.jpg" alt="DryRun Security Dashboard charts - findings by repository, severity distribution, findings by class, and developer activity" loading="lazy"></figure>

''',
}


# ---------------------------------------------------------------------------

ORDERED_PAGES = []
for section in SECTIONS:
    for slug in section['pages']:
        ORDERED_PAGES.append(slug)


def get_section_for_slug(slug: str) -> str:
    for section in SECTIONS:
        if slug in section['pages']:
            return section['name']
    return ''


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------

def render_sidebar(current_slug: str, asset_prefix: str) -> str:
    parts = []
    parts.append('<nav class="sidebar" id="sidebar">')
    parts.append('<div class="sidebar-search">')
    parts.append('<div class="sidebar-search-wrap">')
    parts.append('<svg class="sidebar-search-icon" viewBox="0 0 20 20" fill="currentColor" width="14" height="14" aria-hidden="true"><path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd"/></svg>')
    parts.append('<input type="text" id="docsSearch" placeholder="Search docs..." autocomplete="off">')
    parts.append('<span class="sidebar-search-kbd"><kbd>&#8984;</kbd><kbd>K</kbd></span>')
    parts.append('</div>')
    parts.append('<div id="searchResults" class="search-results" hidden></div>')
    parts.append('</div>')
    parts.append('<div class="sidebar-nav">')
    for section in SECTIONS:
        hidden = section.get('nav_hidden', [])
        visible_pages = [s for s in section['pages'] if s not in hidden]
        if not visible_pages:
            continue
        parts.append('<div class="sidebar-section">')
        parts.append(f'<p class="sidebar-section-title">{esc(section["name"])}</p>')
        parts.append('<ul class="sidebar-links">')
        for slug in visible_pages:
            page = PAGES.get(slug, {})
            title = page.get('title', slug)
            active_class = ' class="active"' if slug == current_slug else ''
            if slug == 'documentation':
                href = f'{esc(asset_prefix)}'
            else:
                href = f'{esc(asset_prefix)}{esc(slug)}'
            parts.append(f'<li><a href="{href}"{active_class}>{esc(title)}</a></li>')
        parts.append('</ul>')
        parts.append('</div>')
    parts.append('</div>')
    parts.append('<div class="sidebar-footer">')
    parts.append('<button class="sidebar-theme-btn" id="themeToggle" aria-label="Toggle light/dark mode">')
    parts.append('<svg class="icon-sun" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>')
    parts.append('<svg class="icon-moon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>')
    parts.append('<span class="theme-label">Toggle dark mode</span>')
    parts.append('</button>')
    parts.append('</div>')
    parts.append('</nav>')
    return '\n'.join(parts)


def render_toc(toc_items: list) -> str:
    if not toc_items:
        return ''
    parts = []
    parts.append('<aside class="toc-sidebar">')
    parts.append('<p class="toc-title">On this page</p>')
    parts.append('<ul class="toc-list">')
    for item in toc_items:
        level_class = 'toc-h3' if item['level'] == 'h3' else 'toc-h2'
        parts.append(f'<li class="{esc(level_class)}"><a href="#{esc(item["anchor"])}">{esc(item["label"])}</a></li>')
    parts.append('</ul>')
    parts.append('</aside>')
    return '\n'.join(parts)


def render_prev_next(slug: str, asset_prefix: str) -> str:
    idx = ORDERED_PAGES.index(slug) if slug in ORDERED_PAGES else -1
    if idx == -1:
        return ''

    parts = ['<nav class="prev-next">']

    if idx > 0:
        prev_slug = ORDERED_PAGES[idx - 1]
        prev_page = PAGES.get(prev_slug, {})
        prev_title = prev_page.get('title', prev_slug)
        if prev_slug == 'documentation':
            prev_href = f'{esc(asset_prefix)}'
        else:
            prev_href = f'{esc(asset_prefix)}{esc(prev_slug)}'
        parts.append(
            f'<a href="{prev_href}" class="prev-next-link prev-link">'
            f'<span class="prev-next-label">← Previous</span>'
            f'<span class="prev-next-title">{esc(prev_title)}</span>'
            f'</a>'
        )
    else:
        parts.append('<span></span>')

    if idx < len(ORDERED_PAGES) - 1:
        next_slug = ORDERED_PAGES[idx + 1]
        next_page = PAGES.get(next_slug, {})
        next_title = next_page.get('title', next_slug)
        if next_slug == 'documentation':
            next_href = f'{esc(asset_prefix)}'
        else:
            next_href = f'{esc(asset_prefix)}{esc(next_slug)}'
        parts.append(
            f'<a href="{next_href}" class="prev-next-link next-link">'
            f'<span class="prev-next-label">Next →</span>'
            f'<span class="prev-next-title">{esc(next_title)}</span>'
            f'</a>'
        )

    parts.append('</nav>')
    return '\n'.join(parts)


HEADER_HTML = '''  <header class="site-header">
    <div class="header-inner">
      <div class="header-left">
        <a href="{asset_prefix}" class="logo-link">
          <img class="logo logo-dark-mode" src="{asset_prefix}assets/logo-dark.svg" alt="DryRun Security">
          <svg class="logo logo-light-mode" viewBox="0 0 450 119" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DryRun Security"><path d="M160.284 0C176.345 0 185.949 10.3885 185.949 25.6751V25.7541C185.949 40.9616 176.345 51.3501 160.284 51.3501H140.719V0H160.284ZM148.977 43.5488H160.284C171.077 43.5488 177.612 36.2808 177.612 25.7343V25.6553C177.612 15.1285 171.057 7.78151 160.284 7.78151H148.977V43.5488Z"/><path d="M237.714 51.3501H228.406L216.94 33.9898H204.286V51.3501H196.029V0H216.485C229.357 0 236.426 6.59652 236.426 17.222V17.301C236.426 25.0826 232.407 30.6521 224.822 32.8838L237.694 51.3501H237.714ZM204.306 7.50501V26.8008H216.505C223.871 26.8008 228.189 23.6013 228.189 17.301V17.222C228.189 10.8428 223.871 7.50501 216.505 7.50501H204.306Z"/><path d="M265.893 25.1615L281.735 0H290.884L270.052 32.5678V51.3304H261.715V32.5678L240.882 0H249.952L265.873 25.1615H265.893Z"/><path d="M340.431 51.3501H331.124L319.678 33.9898H307.024V51.3501H298.766V0H319.222C332.094 0 339.164 6.59652 339.164 17.222V17.301C339.164 25.0826 335.144 30.6521 327.559 32.8838L340.431 51.3501ZM307.024 7.50501V26.8008H319.222C326.589 26.8008 330.906 23.6013 330.906 17.301V17.222C330.906 10.8428 326.589 7.50501 319.222 7.50501H307.024Z"/><path d="M385.344 0H393.681V28.4203C393.681 45.2671 383.779 52.2389 371.284 52.2389H371.205C358.709 52.2389 348.808 45.2671 348.808 28.4203V0H357.145V28.4203C357.145 40.2901 363.996 44.2203 371.205 44.2203H371.284C378.492 44.2203 385.344 40.2901 385.344 28.4203V0Z"/><path d="M441.881 0H449.921V51.3501H442.336L413.622 13.8053V51.3501H405.582V0H413.167L441.881 37.5448V0Z"/><path d="M167.314 89.4481C165.215 86.0313 161.908 84.1748 156.878 84.1748H156.819C151.472 84.1748 148.383 86.1103 148.383 89.1321C148.383 91.2848 149.591 93.1018 154.185 94.1881L162.403 96.1236C169.572 97.7826 171.572 102.503 171.513 107.342C171.513 113.938 165.71 118.066 156.898 118.066H156.839C148.898 118.066 143.274 115.044 140.68 109.475L145.749 105.841C148.007 110.679 151.809 112.615 156.957 112.615H157.017C162.423 112.615 165.294 110.423 165.294 107.164C165.294 104.458 163.75 102.542 159.829 101.496L150.838 99.2441C144.501 97.7036 142.185 93.7931 142.185 89.3493C142.185 82.4763 147.987 78.6646 157.076 78.6646H157.136C163.651 78.6646 168.384 81.0346 171.037 84.9846L167.334 89.4481H167.314Z"/><path d="M210.009 79.3164V85.0439H190.702V95.5509H208.029V101.338H190.702V111.687H210.009V117.414H184.583V79.3362H210.009V79.3164Z"/><path d="M250.566 87.6311C247.912 85.4388 244.605 84.3921 241.021 84.3921H240.961C232.842 84.3921 227.614 90.2776 227.614 98.3159V98.3751C227.674 106.512 232.902 112.358 240.961 112.358H241.021C244.882 112.358 248.031 111.193 250.566 109.119L253.932 113.741C250.506 116.723 246.15 118.086 241.021 118.086H240.961C228.981 118.086 221.475 110.047 221.475 98.3949V98.3356C221.475 86.7226 228.981 78.6843 240.961 78.6843H241.021C245.813 78.6843 250.348 79.9483 253.932 83.0293L250.566 87.6508V87.6311Z"/><path d="M292.548 79.3164H298.726V100.39C298.726 112.891 291.379 118.046 282.112 118.046H282.052C272.784 118.046 265.438 112.872 265.438 100.39V79.3164H271.616V100.39C271.616 109.198 276.686 112.121 282.052 112.121H282.112C287.458 112.121 292.548 109.198 292.548 100.39V79.3164Z"/><path d="M344.114 117.394H337.223L328.727 104.517H319.341V117.394H313.222V79.3164H328.391C337.936 79.3164 343.183 84.2144 343.183 92.0749V92.1342C343.183 97.921 340.193 102.029 334.569 103.688L344.114 117.394ZM319.341 84.8662V99.1652H328.391C333.856 99.1652 337.045 96.7952 337.045 92.1144V92.0552C337.045 87.3152 333.837 84.8464 328.391 84.8464H319.341V84.8662Z"/><path d="M356.966 117.394V79.3164H363.085V117.394H356.966Z"/><path d="M406.018 79.3164V85.2019H393.879V117.394H387.7V85.2019H375.561V79.3164H406.018Z"/><path d="M431.445 97.9802L443.208 79.3164H450L434.554 103.471V117.394H428.375V103.471L412.929 79.3164H419.662L431.465 97.9802H431.445Z"/><path d="M114.163 10.5269H107.767C107.213 10.5269 106.777 10.9614 106.777 11.5144V17.1629L72.221 76.966L62.478 58.3417L73.7854 35.9452H78.3401C78.8945 35.9452 79.3302 35.5107 79.3302 34.9577V28.5784C79.3302 28.0254 78.8945 27.5909 78.3401 27.5909H71.9437C71.3893 27.5909 70.9536 28.0254 70.9536 28.5784V30.2966H50.2992V28.5784C50.2992 28.0254 49.8636 27.5909 49.3091 27.5909H42.9128C42.3583 27.5909 41.9226 28.0254 41.9226 28.5784V34.9577C41.9226 35.5107 42.3583 35.9452 42.9128 35.9452H47.4278L59.1511 58.3615L35.7243 104.794L8.3766 52.7327V47.0249C8.3766 46.4719 7.94094 46.0374 7.38646 46.0374H0.990142C0.435663 46.0374 0 46.4719 0 47.0249V53.4042C0 53.9572 0.435663 54.3917 0.990142 54.3917H5.92105L32.4371 104.893C31.9024 104.912 31.4865 105.347 31.4865 105.88V112.259C31.4865 112.812 31.9222 113.247 32.4767 113.247H38.873C39.4275 113.247 39.8631 112.812 39.8631 112.259V105.88C39.8631 105.88 39.8631 105.821 39.8631 105.781C39.8235 105.327 39.4473 104.972 38.972 104.912L60.8343 61.6005L68.8941 77.0055C68.4386 77.0845 68.0624 77.4795 68.0624 77.9535V84.3328C68.0624 84.8858 68.498 85.3203 69.0525 85.3203H75.4489C76.0033 85.3203 76.439 84.8858 76.439 84.3328V77.9535C76.439 77.4597 76.0627 77.0647 75.6073 77.0055L109.193 18.8811H114.163C114.718 18.8811 115.154 18.4466 115.154 17.8936V11.5144C115.154 10.9614 114.718 10.5269 114.163 10.5269ZM60.7947 55.1422L50.2794 35.0367C50.2794 35.0367 50.2794 34.9972 50.2794 34.9774V33.2592H70.9338V34.9774C70.9338 34.9774 70.9338 34.9774 70.9338 34.9972L60.7749 55.1422H60.7947Z"/><path d="M9.28748 40.8627C9.12906 40.8627 8.97063 40.843 8.81221 40.7837C8.39635 40.6455 7.52503 40.3492 7.58443 39.9345C7.64384 39.4605 7.76266 39.263 7.88148 38.9075C15.8422 15.6814 37.1897 1.61938 61.8244 1.61938C76.1815 1.61938 89.291 6.1224 99.9053 15.7407C100.103 15.925 100.348 16.2081 100.638 16.5899C100.876 16.8862 100.262 17.5182 100.004 17.8144C99.4499 18.4267 98.5191 18.4662 97.925 17.9132C87.8652 8.78865 75.4488 4.56214 61.8244 4.56214C38.4571 4.56214 19.684 17.9724 10.6737 39.8752C10.436 40.4677 9.88157 40.8627 9.28748 40.8627Z" fill="#38D92D"/><path d="M26.219 103.944C25.9022 103.865 25.5259 103.609 25.2487 103.391C13.4066 93.6745 6.03995 79.9679 4.53493 64.8197C4.49533 64.4839 4.3369 63.6939 4.61414 63.5359C4.9904 63.3186 5.36665 63.2594 5.84192 63.2199C6.63403 63.1014 7.36674 63.7334 7.46575 64.5432C8.91136 78.9212 15.9018 91.9167 27.13 101.14C27.7637 101.653 27.8231 102.443 27.3082 103.075C27.0112 103.431 26.5161 103.865 26.219 103.984V103.944Z" fill="#38D92D"/><path d="M61.8245 116.446C56.5966 116.446 51.4281 115.755 46.4575 114.372C46.1011 114.274 45.7446 114.214 45.3684 113.977C44.9921 113.74 45.309 112.99 45.4278 112.555C45.6456 111.765 46.4575 111.311 47.2497 111.528C51.9627 112.832 56.8738 113.484 61.8245 113.484C91.9447 113.484 116.441 89.0529 116.441 59.0131C116.441 49.1776 114.262 41.3171 109.233 32.9233C108.817 32.2321 108.916 31.0471 109.708 30.5533C110.104 30.2966 110.322 30.1386 110.678 30.0793C110.975 30.0398 111.431 30.7113 111.609 31.0076C116.896 39.8556 119.391 48.6641 119.391 59.0329C119.391 90.6922 93.5685 116.446 61.8245 116.446Z" fill="#38D92D"/><path d="M35.6254 93.0228L53.1113 58.0653L44.4574 41.3172H38.4968C37.6056 41.3172 36.8927 40.6062 36.8927 39.7175V23.7792C36.8927 22.8904 37.6056 22.1794 38.4968 22.1794H82.7165C83.6077 22.1794 84.3206 22.8904 84.3206 23.7792V39.7372C84.3206 40.626 83.6077 41.337 82.7165 41.337H76.7955L68.4783 57.9665L72.5181 65.7678L97.2914 22.9102C88.1425 13.9832 75.6469 8.4729 61.8443 8.4729C37.467 8.4729 17.1295 25.6357 12.258 48.4865L35.6452 93.0228H35.6254Z" fill="#38D92D"/><path d="M81.8649 76.9266V89.1518C81.8649 90.0406 81.152 90.7516 80.2609 90.7516H64.28C63.3889 90.7516 62.676 90.0406 62.676 89.1518V76.6105L60.8739 73.1148L44.1801 106.473C49.6655 108.507 55.6064 109.613 61.8046 109.613C89.8059 109.613 112.5 86.9793 112.5 59.0528C112.5 50.2245 110.223 41.9295 106.242 34.7207L81.8451 76.9463L81.8649 76.9266Z" fill="#38D92D"/></svg>
        </a>
      </div>
      <div class="header-right">
        <button class="sidebar-toggle" id="sidebarToggle" aria-label="Toggle navigation">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M3 5h14M3 10h14M3 15h14"/>
          </svg>
        </button>
      </div>
    </div>
  </header>'''

FOOTER_HTML = ''''''


def render_doc_page(slug: str, page: dict, asset_prefix: str = './',
                    search_index: str = '[]') -> str:
    title = page['title']
    description = page['description']
    section_name = page.get('section', get_section_for_slug(slug))
    raw_content = page['content'].strip()
    raw_content = raw_content.replace('{asset_prefix}', asset_prefix)
    content_with_ids = add_heading_anchors(raw_content)
    toc_items = extract_toc(content_with_ids)

    base_url = 'https://docs.dryrun.security'
    if slug == 'documentation':
        canonical_url = f'{base_url}/'
    else:
        canonical_url = f'{base_url}/{slug}'

    header = HEADER_HTML.replace('{asset_prefix}', asset_prefix)
    footer = FOOTER_HTML.replace('{asset_prefix}', asset_prefix)
    sidebar = render_sidebar(slug, asset_prefix)
    toc = render_toc(toc_items)
    prev_next = render_prev_next(slug, asset_prefix)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} - DryRun Security Docs</title>
  <meta name="description" content="{esc(description)}">
  <!-- OpenGraph -->
  <meta property="og:title" content="{esc(title)} - DryRun Security Docs">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{canonical_url}">
  <meta property="og:image" content="https://docs.dryrun.security/assets/og-default.png">
  <meta property="og:site_name" content="DryRun Security Docs">
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)} - DryRun Security Docs">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="https://docs.dryrun.security/assets/og-default.png">
  <!-- Canonical & robots -->
  <link rel="canonical" href="{canonical_url}">
  <meta name="robots" content="index, follow">
  <meta name="author" content="DryRun Security">
  <link rel="icon" href="{asset_prefix}assets/favicon.ico" type="image/png">
  <link rel="apple-touch-icon" href="{asset_prefix}assets/logo192.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{asset_prefix}style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "TechArticle",
    "name": "{esc(title)}",
    "description": "{esc(description)}",
    "url": "{canonical_url}",
    "publisher": {{
      "@type": "Organization",
      "name": "DryRun Security",
      "url": "https://dryrun.security"
    }}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{
        "@type": "ListItem",
        "position": 1,
        "name": "DryRun Security Docs",
        "item": "https://docs.dryrun.security/"
      }},
      {{
        "@type": "ListItem",
        "position": 2,
        "name": "{esc(title)}",
        "item": "{canonical_url}"
      }}
    ]
  }}
  </script>
</head>
<body>
{header}
  <div class="docs-layout">
{sidebar}
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="document.querySelector('.sidebar').classList.remove('open');document.getElementById('sidebarOverlay').style.display='none'"></div>
    <main class="content-area">
      <div class="content-inner">
        <div class="breadcrumb"><a href="{asset_prefix}">Docs</a><span class="breadcrumb-sep">/</span><span class="breadcrumb-section">{esc(section_name)}</span><span class="breadcrumb-sep">/</span><span class="breadcrumb-current">{esc(title)}</span></div>
        <div class="page-heading-row">
          <h1 class="page-heading">{esc(title)}</h1>
          <button class="btn-download-pdf" onclick="window.print()" title="Download as PDF"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 2v8M4.5 7.5 8 10l3.5-2.5"/><path d="M2.5 11v2a1 1 0 001 1h9a1 1 0 001-1v-2"/></svg><span>PDF</span></button>
        </div>
        <p class="page-description">{esc(description)}</p>
        <div class="doc-content">
{content_with_ids}
        </div>
{prev_next}
      </div>
    </main>
{toc}
  </div>
{footer}
  <script>window.__SEARCH_INDEX__={search_index};</script>
  <script src="{asset_prefix}app.js"></script>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Index page - renders the documentation intro in doc-page layout
# ---------------------------------------------------------------------------

def render_index_page() -> str:
    """Render index.html as a landing page with hero, persona cards, and feature grid."""
    asset_prefix = './'
    description = 'DryRun Security documentation - AI-native application security for your development workflow.'

    header = HEADER_HTML.replace('{asset_prefix}', asset_prefix)
    footer = FOOTER_HTML.replace('{asset_prefix}', asset_prefix)
    sidebar = render_sidebar('documentation', asset_prefix)
    search_index = generate_search_index()

    dp = './docs/'

    landing_content = f'''
        <div class="breadcrumb"><a href="{asset_prefix}index.html">Docs</a><span class="breadcrumb-sep">/</span><span class="breadcrumb-current">Documentation</span></div>
        <h1 class="page-heading">Documentation</h1>
        <p class="page-description">DryRun Security is an AI-native application security platform that reviews every pull request for vulnerabilities in real time. These docs cover setup, scanning configuration, code security intelligence, platform administration, and integrations.</p>
        <div class="doc-content">
        <div class="landing-hero"></div>

        <div class="landing-section">
          <div class="landing-section-header">
            <h2>Get Started</h2>
          </div>
          <div class="landing-grid cols-3">
            <a class="landing-card persona" href="{esc(dp)}quick-start.html">
              <span class="landing-card-title">I&#x27;m a Developer</span>
              <span class="landing-card-desc">Connect your repo, enable PR scanning, and get security findings inline with your pull requests.</span>
            </a>
            <a class="landing-card persona" href="{esc(dp)}deepscan.html">
              <span class="landing-card-title">I&#x27;m in AppSec</span>
              <span class="landing-card-desc">Discover vulnerabilities across repositories, review findings, configure policies, and track compliance.</span>
            </a>
            <a class="landing-card persona" href="{esc(dp)}pr-scanning-configuration.html">
              <span class="landing-card-title">I&#x27;m an Admin</span>
              <span class="landing-card-desc">Set up integrations, manage team permissions, configure scanning settings, and generate API tokens.</span>
            </a>
          </div>
        </div>

        <div class="landing-section">
          <div class="landing-section-header">
            <h2>Scanning Products</h2>
          </div>
          <div class="landing-grid cols-3">
            <a class="landing-card" href="{esc(dp)}pr-scanning.html">
              <span class="landing-card-title">PR Scanning</span>
              <span class="landing-card-desc">Automatic security review on every pull request with contextual analysis and inline comments.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}deepscan.html">
              <span class="landing-card-title">Repository Scanning (DeepScan)</span>
              <span class="landing-card-desc">Full repository analysis for comprehensive vulnerability detection beyond individual PRs.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}secrets-scanning.html">
              <span class="landing-card-title">Secrets Scanning</span>
              <span class="landing-card-desc">Detect leaked credentials, API keys, and tokens before they reach production.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}iac-scanning.html">
              <span class="landing-card-title">IaC Scanning</span>
              <span class="landing-card-desc">Scan Terraform configurations for security misconfigurations and insecure defaults.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}sca.html">
              <span class="landing-card-title">SCA</span>
              <span class="landing-card-desc">Software composition analysis for known vulnerabilities in open-source dependencies.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}auto-fix.html">
              <span class="landing-card-title">Auto Fix</span>
              <span class="landing-card-desc">Automated remediation suggestions with one-click fix verification.</span>
            </a>
          </div>
        </div>

        <div class="landing-section">
          <div class="landing-section-header">
            <h2>Code Security Intelligence</h2>
          </div>
          <div class="landing-grid cols-3">
            <a class="landing-card" href="{esc(dp)}code-security-intelligence.html" style="grid-column: 1 / -1">
              <span class="landing-card-title">Code Security Intelligence</span>
              <span class="landing-card-desc">An intelligence layer built on top of all finding data and trends, surfacing feature ships, vulnerability trends, architecture risks, developer patterns, shadow AI usage, incident investigation, and more.</span>
            </a>
          </div>
        </div>

        <div class="landing-section">
          <div class="landing-section-header">
            <h2>Platform & Integrations</h2>
          </div>
          <div class="landing-grid cols-3">
            <a class="landing-card" href="{esc(dp)}pr-blocking.html">
              <span class="landing-card-title">PR Blocking</span>
              <span class="landing-card-desc">Block pull requests based on security finding severity and policy rules.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}custom-code-policies.html">
              <span class="landing-card-title">Custom Code Policies</span>
              <span class="landing-card-desc">Create custom security rules in plain English to enforce your standards.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}compliance-grc.html">
              <span class="landing-card-title">Compliance & GRC</span>
              <span class="landing-card-desc">Compliance reporting, audit trails, and governance readiness.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}slack-integration.html">
              <span class="landing-card-title">Slack Integration</span>
              <span class="landing-card-desc">Receive real-time security alerts and findings in your Slack channels.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}webhook-integration.html">
              <span class="landing-card-title">Webhook Integration</span>
              <span class="landing-card-desc">Send DryRun Security events to any webhook endpoint for custom workflows.</span>
            </a>
            <a class="landing-card" href="{esc(dp)}mcp.html">
              <span class="landing-card-title">MCP</span>
              <span class="landing-card-desc">Model Context Protocol integration for AI-powered development tools.</span>
            </a>
          </div>
        </div>

        <div class="landing-section">
          <div class="landing-section-header">
            <h2>Resources</h2>
          </div>
          <div class="landing-resources">
            <a href="{esc(dp)}documentation.html">
              <span>Documentation Overview<span class="res-desc">Full table of contents and platform overview</span></span>
            </a>
            <a href="{esc(dp)}dryrun-api.html">
              <span>DryRun API<span class="res-desc">Programmatic access to DryRun Security</span></span>
            </a>
            <a href="{esc(dp)}api-access-keys.html">
              <span>API Access Keys<span class="res-desc">Manage API keys for integrations</span></span>
            </a>
            <a href="{esc(dp)}dryrun-skill.html">
              <span>DryRun Skill<span class="res-desc">Integrate with AI coding tools and agents</span></span>
            </a>
          </div>
        </div>
        </div>
'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DryRun Security Documentation</title>
  <meta name="description" content="{esc(description)}">
  <!-- OpenGraph -->
  <meta property="og:title" content="DryRun Security Documentation">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="https://docs.dryrun.security/">
  <meta property="og:image" content="https://docs.dryrun.security/assets/og-default.png">
  <meta property="og:site_name" content="DryRun Security Docs">
  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="DryRun Security Documentation">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="https://docs.dryrun.security/assets/og-default.png">
  <!-- Canonical & robots -->
  <link rel="canonical" href="https://docs.dryrun.security/">
  <meta name="robots" content="index, follow">
  <meta name="author" content="DryRun Security">
  <link rel="icon" href="{asset_prefix}assets/favicon.ico" type="image/png">
  <link rel="apple-touch-icon" href="{asset_prefix}assets/logo192.png">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{asset_prefix}style.css">
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "DryRun Security",
    "url": "https://dryrun.security",
    "sameAs": ["https://docs.dryrun.security"]
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": "DryRun Security Docs",
    "url": "https://docs.dryrun.security",
    "description": "Documentation for DryRun Security, an AI-native application security platform"
  }}
  </script>
</head>
<body>
{header}
  <div class="docs-layout">
{sidebar}
    <div class="sidebar-overlay" id="sidebarOverlay" onclick="document.querySelector('.sidebar').classList.remove('open');document.getElementById('sidebarOverlay').style.display='none'"></div>
    <main class="content-area">
      <div class="content-inner">
{landing_content}
      </div>
    </main>
  </div>
{footer}
  <script>window.__SEARCH_INDEX__={search_index};</script>
  <script src="{asset_prefix}app.js"></script>
</body>
</html>'''


# ---------------------------------------------------------------------------
# Sitemap and robots.txt
# ---------------------------------------------------------------------------

def render_sitemap(base_url: str = 'https://docs.dryrun.security') -> str:
    today = datetime.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    lines.append(f'  <url><loc>{base_url}/</loc><priority>1.0</priority><lastmod>{today}</lastmod></url>')
    for slug in ORDERED_PAGES:
        if slug == 'documentation':
            continue
        lines.append(f'  <url><loc>{base_url}/{slug}</loc><priority>0.8</priority><lastmod>{today}</lastmod></url>')
    lines.append('</urlset>')
    return '\n'.join(lines)


def render_llms_txt(base_url: str = 'https://docs.dryrun.security') -> str:
    """Generate llms.txt for AI crawler indexing per llmstxt.org spec."""
    lines = []
    lines.append('# DryRun Security Docs')
    lines.append('')
    lines.append('> AI-native application security platform documentation. Covers PR scanning, DeepScan, secrets detection, IaC scanning, SCA, custom code policies, risk register, finding tuning, and integrations.')
    lines.append('')
    lines.append('## Docs')
    for slug in ORDERED_PAGES:
        page = PAGES[slug]
        title = page['title']
        description = page.get('description', '')
        if slug == 'documentation':
            url = f'{base_url}/'
        else:
            url = f'{base_url}/{slug}'
        lines.append(f'- [{title}]({url}): {description}')
    return '\n'.join(lines) + '\n'


def render_llms_full_txt(base_url: str = 'https://docs.dryrun.security') -> str:
    """Generate llms-full.txt: concatenated clean markdown of all docs pages."""
    sections = []
    for slug in ORDERED_PAGES:
        page = PAGES[slug]
        title = page['title']
        description = page.get('description', '')
        content_html = page['content']
        clean = re.sub(r'<[^>]+>', '', content_html)
        clean = re.sub(r'\n{3,}', '\n\n', clean.strip())
        if slug == 'documentation':
            url = f'{base_url}/'
        else:
            url = f'{base_url}/{slug}'
        sections.append(f'# {title}\n\nURL: {url}\n\n{description}\n\n{clean}')
    return '\n\n---\n\n'.join(sections) + '\n'


def render_robots() -> str:
    return '''User-agent: *
Allow: /

Sitemap: https://docs.dryrun.security/sitemap.xml
'''


def render_redirect(target_path: str,
                    base_url: str = 'https://docs.dryrun.security') -> str:
    """Generate a minimal HTML redirect page that points to base_url + target_path.

    target_path should start with '/' (e.g. '/quick-start' or '/').
    """
    target = f'{base_url}{target_path}'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Page moved</title>
<meta http-equiv="refresh" content="0; url={esc(target)}">
<link rel="canonical" href="{esc(target)}">
<meta name="robots" content="noindex">
<script>window.location.replace({json.dumps(target)});</script>
</head>
<body>
<p>This page has moved. <a href="{esc(target)}">Click here if you are not redirected.</a></p>
</body>
</html>
'''


def _canonical_path_for_slug(slug: str) -> str:
    """Return the canonical site path for a page slug under the flat URL structure."""
    if slug == 'documentation':
        return '/'
    return f'/{slug}'


def copy_static_files(source_dir: Path, output_dir: Path) -> None:
    """Copy assets required by the GitHub Pages source directory."""
    for filename in ('style.css', 'app.js'):
        shutil.copy2(source_dir / filename, output_dir / filename)
        print(f'  Generated: {filename}')
    shutil.copytree(source_dir / 'assets', output_dir / 'assets', dirs_exist_ok=True)
    print('  Generated: assets/')


# ---------------------------------------------------------------------------
# Search index generation
# ---------------------------------------------------------------------------

_TAG_RE = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')


def _strip_html(raw_html: str) -> str:
    """Remove HTML tags and collapse whitespace to produce plain text."""
    text = _TAG_RE.sub(' ', raw_html)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(' ', text).strip()
    return text


_HEADING_SPLIT_RE = re.compile(
    r'(<h[23][^>]*id=["\']([^"\']+)["\'][^>]*>(.*?)</h[23]>)',
    re.IGNORECASE | re.DOTALL,
)


def _extract_sections(content_html: str):
    """Split HTML content into sections delimited by h2/h3 headings.

    Returns a list of (anchor, heading_text, section_body_html) tuples.
    """
    matches = list(_HEADING_SPLIT_RE.finditer(content_html))
    if not matches:
        return []
    sections = []
    for i, m in enumerate(matches):
        anchor = m.group(2)
        heading_text = html.unescape(re.sub(r'<[^>]+>', '', m.group(3)).strip())
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content_html)
        body_html = content_html[start:end]
        sections.append((anchor, heading_text, body_html))
    return sections


def generate_search_index() -> str:
    """Build a JSON search index of all pages with section-level entries.

    Each page gets a page-level entry (no anchor) plus one entry per h2/h3
    section that includes the anchor id for deep linking.
    """
    index = []
    for slug in ORDERED_PAGES:
        page = PAGES.get(slug)
        if page is None:
            continue
        content_html = page.get('content', '')
        content_with_ids = inject_heading_ids(content_html)
        plain_text = _strip_html(content_html)
        url = '/' if slug == 'documentation' else f'/{slug}'
        # Page-level entry (no anchor)
        index.append({
            's': slug,
            'u': url,
            't': page.get('title', slug),
            'n': page.get('section', ''),
            'd': page.get('description', ''),
            'b': plain_text,
            'url': url,
        })
        # Section-level entries with anchors
        for anchor, heading, body_html in _extract_sections(content_with_ids):
            section_text = _strip_html(body_html)
            if len(section_text.strip()) < 20:
                continue
            index.append({
                's': slug,
                'u': url,
                't': heading,
                'n': page.get('section', ''),
                'd': '',
                'b': section_text,
                'a': anchor,
                'url': url,
            })
    return json.dumps(index, separators=(',', ':'))


# ---------------------------------------------------------------------------
# Webflow export
# ---------------------------------------------------------------------------

_INLINE_STYLE_RE = re.compile(r'\s+style="[^"]*"', re.IGNORECASE)
_SCRIPT_TAG_RE = re.compile(
    r'<script[\s>].*?</script>', re.IGNORECASE | re.DOTALL
)
_CLASS_ATTR_RE = re.compile(r'class="([^"]*)"')
_ASSET_PREFIX_RE = re.compile(r'\{asset_prefix\}')

# CSS class names used in page content that need the drs- prefix
_DRS_CLASS_MAP = {
    'landing-hero': 'drs-landing-hero',
    'landing-section': 'drs-landing-section',
    'landing-section-header': 'drs-landing-section-header',
    'landing-grid': 'drs-landing-grid',
    'landing-card': 'drs-landing-card',
    'landing-card-title': 'drs-landing-card-title',
    'landing-card-desc': 'drs-landing-card-desc',
    'landing-resources': 'drs-landing-resources',
    'res-desc': 'drs-res-desc',
    'cols-2': 'drs-cols-2',
    'cols-3': 'drs-cols-3',
    'persona': 'drs-persona',
    'doc-content': 'drs-doc-content',
    'info-box': 'drs-info-box',
    'warning-box': 'drs-warning-box',
    'feature-grid': 'drs-feature-grid',
    'feature-item': 'drs-feature-item',
    'feature-icon': 'drs-feature-icon',
    'code-block': 'drs-code-block',
    'copy-btn': 'drs-copy-btn',
}


def _clean_content_for_webflow(raw_content: str) -> str:
    """Clean page content HTML for Webflow compatibility.

    - Removes inline styles
    - Removes <script> tags
    - Remaps CSS class names to drs- prefixed versions
    - Removes {asset_prefix} placeholders (replaces with relative paths)
    """
    content = raw_content.strip()

    # Remove {asset_prefix} references - use relative paths for Webflow
    content = _ASSET_PREFIX_RE.sub('', content)

    # Remove inline styles
    content = _INLINE_STYLE_RE.sub('', content)

    # Remove script tags
    content = _SCRIPT_TAG_RE.sub('', content)

    # Remap class names to drs- prefix
    def _remap_classes(m):
        original = m.group(1)
        classes = original.split()
        remapped = []
        for cls in classes:
            remapped.append(_DRS_CLASS_MAP.get(cls, cls))
        return f'class="{" ".join(remapped)}"'

    content = _CLASS_ATTR_RE.sub(_remap_classes, content)

    # Inject heading IDs for proper anchor linking
    content = inject_heading_ids(content)

    return content


def _extract_meta_description(content: str) -> str:
    """Extract a meta description from the first <p> tag in the content."""
    match = re.search(r'<p[^>]*>(.*?)</p>', content, re.DOTALL)
    if not match:
        return ''
    text = _strip_html(match.group(1)).strip()
    if len(text) > 160:
        text = text[:157] + '...'
    return text


def generate_webflow_csv(output_dir: Path) -> None:
    """Generate a CSV file for Webflow CMS import with all documentation pages."""
    webflow_dir = output_dir / 'webflow-export'
    webflow_dir.mkdir(parents=True, exist_ok=True)

    csv_path = webflow_dir / 'pages.csv'
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['Name', 'Slug', 'Content', 'Meta Description', 'Category'])

    for slug in ORDERED_PAGES:
        page = PAGES.get(slug)
        if page is None:
            continue
        title = page['title']
        description = page.get('description', '')
        section = page.get('section', get_section_for_slug(slug))
        raw_content = page['content']
        clean = _clean_content_for_webflow(raw_content)

        meta_desc = description if description else _extract_meta_description(clean)

        writer.writerow([title, slug, clean, meta_desc, section])

    csv_path.write_text(buf.getvalue(), encoding='utf-8')
    print('  Generated: webflow-export/pages.csv')


def generate_webflow_pages(output_dir: Path) -> None:
    """Generate individual clean HTML content files for Webflow code embeds."""
    pages_dir = output_dir / 'webflow-export' / 'pages'
    pages_dir.mkdir(parents=True, exist_ok=True)

    for slug in ORDERED_PAGES:
        page = PAGES.get(slug)
        if page is None:
            continue
        raw_content = page['content']
        clean = _clean_content_for_webflow(raw_content)

        page_html = f'<div class="drs-doc-content">\n{clean}\n</div>\n'
        out_path = pages_dir / f'{slug}.html'
        out_path.write_text(page_html, encoding='utf-8')

    print(f'  Generated: webflow-export/pages/ ({len(ORDERED_PAGES)} files)')


def generate_webflow_readme(output_dir: Path) -> None:
    """Generate a README explaining how to use the Webflow export files."""
    webflow_dir = output_dir / 'webflow-export'
    webflow_dir.mkdir(parents=True, exist_ok=True)

    # Collect all drs- classes actually used across content
    all_classes = set()
    for slug in ORDERED_PAGES:
        page = PAGES.get(slug)
        if page is None:
            continue
        clean = _clean_content_for_webflow(page['content'])
        for m in _CLASS_ATTR_RE.finditer(clean):
            for cls in m.group(1).split():
                if cls.startswith('drs-'):
                    all_classes.add(cls)

    class_table = '\n'.join(
        f'| `{cls}` | {cls.replace("drs-", "").replace("-", " ").title()} container/element |'
        for cls in sorted(all_classes)
    )

    readme = f'''# Webflow Export - DryRun Security Documentation

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
   Webflow\'s own class namespace.

## CSS Classes

All custom CSS classes use the `drs-` prefix. Add these styles to your
Webflow project\'s custom CSS (Site Settings > Custom Code > Head):

| Class | Purpose |
|-------|---------|
{class_table}

Copy the relevant styles from the original `style.css` file, renaming each
class to its `drs-` prefixed version. Semantic HTML elements (`h2`, `p`,
`table`, etc.) inherit Webflow\'s typography styles by default.

## Images and Assets

Images referenced in the content use relative paths. Before importing:

1. Upload all images from the `assets/` directory to Webflow\'s Asset Manager.
2. Update image `src` attributes in the HTML to point to Webflow-hosted URLs,
   or use Webflow\'s built-in image elements and reference CMS image fields.
3. SVG logos are inlined in the original site\'s header/footer and are **not**
   included in these content files. Use Webflow\'s native header/footer
   components instead.

## Notes

- Content HTML has been cleaned: no inline styles, no `<script>` tags, and
  no site wrapper elements (header, footer, sidebar, navigation).
- Internal links between pages use relative paths (e.g., `deepscan.html`).
  Update these to match your Webflow URL structure if slugs differ.
- Tables use standard HTML table markup (`<table>`, `<thead>`, `<tbody>`,
  `<tr>`, `<th>`, `<td>`) compatible with Webflow\'s table styling.
'''

    (webflow_dir / 'README.md').write_text(readme, encoding='utf-8')
    print('  Generated: webflow-export/README.md')


# ---------------------------------------------------------------------------
# Build entry point
# ---------------------------------------------------------------------------

def build(output_dir: str = None) -> None:
    source_dir = Path(__file__).parent
    if output_dir is None:
        output_dir = source_dir / 'docs'
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # GitHub Pages publishes docs/ for this repository, so keep every served
    # file, including CSS, JavaScript, and images, in that directory.
    copy_static_files(source_dir, output_dir)

    # Pre-generate the search index once for all pages
    search_index = generate_search_index()

    # Generate doc pages in docs/; documentation slug becomes docs/index.html.
    for slug in ORDERED_PAGES:
        page = PAGES.get(slug)
        if page is None:
            print(f'WARNING: No content defined for slug: {slug}')
            continue
        html_content = render_doc_page(slug, page, asset_prefix='./',
                                       search_index=search_index)
        if slug == 'documentation':
            out_path = output_dir / 'index.html'
            out_name = 'index.html'
        else:
            out_path = output_dir / f'{slug}.html'
            out_name = f'{slug}.html'
        out_path.write_text(html_content, encoding='utf-8')
        print(f'  Generated: {out_name}')

    # Remove flat redirect stubs so every published docs/*.html page is real
    # documentation content. Existing directory-index redirects remain intact.
    (output_dir / 'documentation.html').unlink(missing_ok=True)
    for old_slug, _ in REDIRECTS:
        (output_dir / f'{old_slug}.html').unlink(missing_ok=True)

    # Sitemap
    (output_dir / 'sitemap.xml').write_text(render_sitemap(), encoding='utf-8')
    print('  Generated: sitemap.xml')

    # Robots
    (output_dir / 'robots.txt').write_text(render_robots(), encoding='utf-8')
    print('  Generated: robots.txt')

    # llms.txt and llms-full.txt for AI crawler indexing
    (output_dir / 'llms.txt').write_text(render_llms_txt(), encoding='utf-8')
    print('  Generated: llms.txt')
    (output_dir / 'llms-full.txt').write_text(render_llms_full_txt(), encoding='utf-8')
    print('  Generated: llms-full.txt')

    # Webflow export
    generate_webflow_csv(output_dir)
    generate_webflow_pages(output_dir)
    generate_webflow_readme(output_dir)

    total = len(ORDERED_PAGES) + 5  # pages + index + sitemap + robots + llms.txt + llms-full.txt
    webflow_total = len(ORDERED_PAGES) + 2  # pages + CSV + README
    print(f'\nBuild complete: {total} site files + {webflow_total} webflow-export files generated in {output_dir}')


if __name__ == '__main__':
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else None
    build(out)
