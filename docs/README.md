## Locally building Sphinx docs

In the root directory of this repository, install Sphinx requirements via

```bash
pip install -e .[docs]
```

Then run the Sphinx build commands:
```bash
cd docs/
make html
```

You can open the Sphinx index page at `docs/build/html/index.html` in your web browser.

## Serving new documentation to `readthedocs.io`

Documentation is automatically built when changes are pushed to the `dev` branch. You can see the most recent builds on the [RTD Build Page](https://readthedocs.org/projects/minerl/builds/).

There is also an option to build Pull Request test changes automatically (along with a status indicator for each commit), but we haven't figured out how to properly configure that yet.

If you are a RTD admin, you can modify ReadTheDocs settings at the [RTD MineRL Project Page](https://readthedocs.org/projects/minerl/).
