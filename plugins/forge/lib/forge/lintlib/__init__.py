"""Lint rule library for `forge lint` (CONTRACTS.md SS11-13).

One module per rule family: :mod:`frontmatter` (the shared stdlib YAML-subset
parser), :mod:`agents`, :mod:`skills`, :mod:`claudemd`, :mod:`wording` and
:mod:`manifest`. Every ``lint_*`` function returns a list of
``forge.checks.CheckResult`` so the ``lint`` command can report and
aggregate them the same way ``forge doctor`` does.
"""
