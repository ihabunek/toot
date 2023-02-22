from datetime import datetime

# -- Project information -----------------------------------------------------

project = 'toot'
year = datetime.now().year
copyright = '{}, Ivan Habunek'.format(year)
author = 'Ivan Habunek'

# -- General configuration ---------------------------------------------------

extensions = []
templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']
pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_theme_options = {
    "description": "Mastodon CLI client",
    "github_user": "ihabunek",
    "github_repo": "toot",
    "fixed_sidebar": True,
    "travis_button": True,
    "logo": 'trumpet.png',
}
html_static_path = ['_static']
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
    ]
}
