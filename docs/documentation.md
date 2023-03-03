Documentation
=============

Documentation is generated using [mdBook](https://rust-lang.github.io/mdBook/).

Documentation is written in markdown and located in the `docs` directory.

Additional plugins:

- [mdbook-toc](https://github.com/badboy/mdbook-toc)

Install prerequisites
---------------------

You'll need a moderately recent version of Rust (1.60) at the time of writing.
Check out [mdbook installation docs](https://rust-lang.github.io/mdBook/guide/installation.html)
for details.

Install by building from source:

```
cargo install mdbook mdbook-toc
```

Generate
--------

HTML documentation is generated from sources by running:

```
mdbook build
```

To run a local server which will rebuild on change:

```
mdbook serve
```
