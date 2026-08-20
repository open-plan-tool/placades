extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
]
source_suffix = ".rst"
master_doc = "index"
project = "oemof-eesyplan"
year = "2025-2026"
author = "Open Plan Community"
copyright = f"{year}, {author}"
version = release = "0.0.1"

pygments_style = "trac"
templates_path = ["."]
extlinks = {
    "issue": ("https://github.com/oemof/oemof-eesyplan/issues/%s", "#%s"),
    "pr": ("https://github.com/oemof/oemof-eesyplan/pull/%s", "PR #%s"),
}

html_theme = "furo"
html_theme_options = {
    "githuburl": "https://github.com/oemof/oemof-eesyplan/",
}

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_short_title = f"{project}-{version}"

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False

linkcheck_ignore = [
    "https://coveralls.io",
]
