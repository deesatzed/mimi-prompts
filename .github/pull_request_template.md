## Summary

What changed and why?

## Safety and privacy

- [ ] I did not include a private prompt store, sensitive conversation, credential, or API key.
- [ ] The change does not add automatic global host configuration or full-conversation scraping.

## Verification

- [ ] `python3 -m unittest discover -s tests -v`
- [ ] `python3 scripts/tabletop_demo.py --assert --output docs/reports/tabletop-results.json`
- [ ] `python3 scripts/release_check.py`
- [ ] `python3 -m py_compile core.py cli.py seeds.py minipromptlib/*.py scripts/*.py tests/*.py`
- [ ] `git diff --check`
