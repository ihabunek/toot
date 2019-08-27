Interesting urwid implementations:
* https://github.com/CanonicalLtd/subiquity/blob/master/subiquitycore/core.py#L280
* https://github.com/TomasTomecek/sen/blob/master/sen/tui/ui.py
* https://github.com/rndusr/stig/tree/master/stig/tui

TODO/Ideas:
* pack left column in timeline view
* allow scrolling of toot contents if they don't fit the screen, perhaps using
  pageup/pagedown
* consider adding semi-automated error reporting when viewing an exception,
  something along the lines of "press T to submit a ticket", which would link
  to a pre-filled issue submit page.
* show new toots, some ideas:
    * R to reload/refresh timeline
    * streaming new toots? not sold on the idea
    * go up on first toot to fetch any newer ones, and prepend them?
* Switch timeline to top/bottom layout for narrow views.
* Think about how to show media
    * download media and use local image viewer?
    * convert to ascii art?
* use signals to avoid tightly coupling components

Questions:
* is it possible to make a span a urwid.Text selectable? e.g. for urls and hashtags
