# Changelog

## 1.0.0 (2026-11-05)

First public release.

- `skills/drafting-harness/SKILL.md`: FRAME, FORK, FIGHT, FINISH with stakes tiers S1 to S5,
  asymmetric tier defaults, channel rules, correction protocol and edit mode. Generic: the
  personal layer moved to a separate voice profile.
- `gates/lint.py`: draft mode (em dashes, banned phrases, placeholders, soggy middle, recap
  closers, markdown and tables by channel, length caps) and contract mode (tier shape, fake
  forks, single selection, merge language, decision tree, named adversary, pre-mortem).
- `gates/banned.tsv`: banned phrases as data, each with its fix.
- `templates/`: output contract per tier and an example voice profile for an invented persona.
- `docs/method.md`: reasoning, axis library, adversary library.
- 13 examples with recorded verdicts and 57 unit tests.
