# Configuration file for the Sphinx documentation builder.
# Full options: https://www.sphinx-doc.org/en/master/usage/configuration.html

# ── Project info ──────────────────────────────────────────────────────────────
import os
import sys

project = "scoop_newsroom"
author = "Janke"
copyright = "2025, Janke"
release = "00.00.01"

# ── Path & Django setup ──────────────────────────────────────────────────────
# This file lives at: <project_root>/docs/source/conf.py
THIS_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(
    THIS_DIR, "..", ".."))  # -> <project_root>

# Ensure Python can import your project package(s)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Configure Django ONLY if available (helps when building on CI without Django)
DJANGO_SETTINGS = os.environ.get("DJANGO_SETTINGS_MODULE")
if not DJANGO_SETTINGS:
    # ⚠️ Change this to your actual settings module if different:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "capostone.settings")

try:
    import django  # noqa: WPS433 (import at top of file is fine here)
    django.setup()
except Exception as e:
    # Soft-fail so Sphinx can still build reference pages that don't require imports.
    # For hard failures (e.g., API docs), fix settings or mock imports (see autodoc_mock_imports).
    print(f"[conf.py] Django setup skipped or failed: {e}")

# ── General configuration ────────────────────────────────────────────────────
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",   # Google/NumPy style docstrings (via napoleon)
    "myst_parser",           # Markdown support
]

# Generate autosummary stubs automatically
autosummary_generate = True

# Autodoc defaults (tweak as you like)
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "private-members": False,
    "show-inheritance": True,
    "inherited-members": True,
}
autoclass_content = "class"       # or "both" if you want __init__ docstrings merged
# keep signatures clean; put types in the description
autodoc_typehints = "description"

# If certain imports break the build, mock them here (examples below):
# autodoc_mock_imports = ["celery", "numpy", "pandas"]

# Napoleon (Google/NumPy docstring parsing) – keep both on for flexibility
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_private_with_doc = False

# MyST (Markdown) options
myst_enable_extensions = [
    "deflist",
    "fieldlist",
    "colon_fence",
    "tasklist",
    "linkify",
]

templates_path = ["_templates"]

# Exclude noisy or generated paths from the source tree if needed
exclude_patterns = [
    "_build",
    "Thumbs.db",
    ".DS_Store",
    # You can exclude test/migration *source* files if you keep reST stubs separate:
    # "../../newsroom/tests.py",
    # "../../newsroom/migrations/**",
]

# ── HTML output ──────────────────────────────────────────────────────────────
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Optional: nice RTD theme tweaks
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "sticky_navigation": True,
    "titles_only": False,
}

# Keep Python as the primary domain
primary_domain = "py"

# Stop Sphinx from importing heavy/third-party modules that have wonky docstrings
autodoc_mock_imports = ["rest_framework", "newsroom.tests"]
autodoc_mock_imports = ["rest_framework"]
