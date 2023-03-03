from datetime import datetime

# -- Project information -----------------------------------------------------

project = 'toot'
year = datetime.now().year
copyright = '{}, Ivan Habunek'.format(year)
author = 'Ivan Habunek'

# -- General configuration ---------------------------------------------------

extensions = []
source_suffix = '.rst'
master_doc = 'index'
exclude_patterns = ['_build']
pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_theme_options = {
    "description": "Mastodon CLI client",
    "fixed_sidebar": True,
}
