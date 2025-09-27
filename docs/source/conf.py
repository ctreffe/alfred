# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

sys.path.insert(0, os.path.abspath("../../src/alfred3"))


# -- Project information -----------------------------------------------------

project = "alfred3"
copyright = "2020, Christian Treffenstädt, Paul Wiemann, Johannes Brachem"
author = "Christian Treffenstädt, Paul Wiemann, Johannes Brachem"

# The full version, including alpha/beta/rc tags
# Parse version from _version.py in package directory
# See https://packaging.python.org/guides/single-sourcing-package-version/#single-sourcing-the-version
versiondict = {}
with open("../../src/alfred3/_version.py") as f:
    exec(f.read(), versiondict)
release = versiondict["__version__"]


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.doctest",
    "recommonmark",
    "sphinx.ext.autosummary",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.linkcode",
    "sphinx_remove_toctrees",  # speeds up build with many stub pages
]

autosummary_generate = True

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = "pydata_sphinx_theme"
# html_theme = 'sphinx_rtd_theme'
html_theme = "sphinx_book_theme"

html_theme_options = {
    "repository_url": "https://github.com/ctreffe/alfred/",
    "use_repository_button": True,
}

html_title = "alfred3"
html_logo = "../../src/alfred3/static/img/alfred_logo_color.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_css_files = ["custom.css"]

master_doc = "index"
pygments_style = "sphinx"

# Monkey patch for issue #2044 (None by default for instance attributes? #2044)
# Should be resolved in next release of sphinx
from sphinx.ext.autodoc import ClassLevelDocumenter, InstanceAttributeDocumenter  # noqa


def iad_add_directive_header(self, sig):
    ClassLevelDocumenter.add_directive_header(self, sig)


InstanceAttributeDocumenter.add_directive_header = iad_add_directive_header

autodoc_default_options = {"member-order": "bysource", "inherited-members": False}


def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    if not info["module"]:
        return None
    filename = info["module"].replace(".", "/")

    return f"https://github.com/ctreffe/alfred/blob/master/src/{filename}.py"


# Remove auto-generated API docs from sidebars. They take too long to build.
remove_from_toctrees = [
    "generated/alfred3.page.*.*.rst",
    "generated/alfred3.section.*.*.rst",
    "generated/alfred3.randomizer.*.*.rst",
    "generated/alfred3.experiment.*.*.rst",
    "generated/alfred3.cli.*.*.rst",
    "generated/alfred3.util.*.*.rst",
    "generated/alfred3.admin.*.*.rst",
    "generated/alfred3.element.*.*.*.rst",
]
