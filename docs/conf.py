# Configuration for Sphinx documentation generation

project = "Phantom"
copyright = "2026, Phantom Contributors"
author = "VoidNxSEC"
release = "0.0.1"
version = "0.0.1"

# -- General configuration ---
extensions = [
    "sphinx.ext.autodoc",           # Auto-document from docstrings
    "sphinx.ext.autosummary",       # Create summary tables
    "sphinx.ext.intersphinx",       # Link to other projects
    "sphinx.ext.napoleon",          # Support Google & NumPy docstrings
    "sphinx_rtd_theme",             # ReadTheDocs theme
    "sphinxcontrib.openapi",        # OpenAPI/Swagger support
    "sphinx.ext.viewcode",          # Add links to source code
    "sphinx.ext.todo",              # TODO/FIXME support
]

# Autodoc configuration
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    "show-inheritance": True,
}

autosummary_generate = True

# Napoleon (Google docstring) configuration
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

# OpenAPI/Swagger
openapi_url = "http://localhost:8000/openapi.json"

# Templates
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_favicon = "_static/favicon.ico"

html_theme_options = {
    "collapse_navigation": False,
    "sticky_navigation": True,
    "navigation_depth": 4,
    "includehidden": True,
    "titles_only": False,
    "logo_only": False,
    "display_version": True,
}

# -- Options for LaTeX output
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
}

# -- Python API documentation order
master_doc = "index"
language = "en"
pygments_style = "sphinx"
todo_include_todos = True

# Add any paths
import os
import sys
sys.path.insert(0, os.path.abspath("../src"))
