# Output contract by stakes tier

The stakes tier decides the shape of the output. Effort does not. A one-line
confirmation that arrives with a matrix has failed the contract as surely as a
negotiation email that arrives as one unexamined draft.

`python3 gates/lint.py <output.md> --contract` checks every rule marked (checked)
below, then lints each draft for the channel named in the header.

## The header (every tier)

```
[S2 · channel: email · reader: the hiring manager, two days after the onsite · fork axis: urgency vs relationship]
```

- First non-empty line, in square brackets. (checked)
- Names the tier S1 to S5 and the channel. (checked) Channels: slack, slack-thread,
  slack-dm, text (sms, whatsapp, imessage), email, linkedin, doc.
- Names the reader in a specific state, and from S2 up the fork axis.

## S1 - routine (single path)

Confirmations, thanks, simple logistics. One send-ready draft.

```
[S1 · channel: text · reader: a colleague confirming a time]
Thursday at 3 works. See you then.
```

- Exactly one draft. (checked)
- No alternatives, no matrix, no tree. (checked)
- A one-line `Rationale:` only if the user asked for it.

## S2 - standard (two drafts)

A normal work message, an ordinary recruiter reply, a vendor request.

```
[S2 · channel: email · reader: ... · fork axis: X vs Y]

Draft A [optimize: X | sacrifice: Y]
<draft>

Draft B [optimize: Y | sacrifice: X]
<draft>

| Draft | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A | X | Y | <the condition that makes A right> |
| B | Y | X | <the condition that makes B right> |

Recommendation: A. <one-line reason tied to a fact about the reader>

Decision tree:
- If they reply <X> -> <next move>
- If they reply <Y> -> <next move>
- If no reply in <n> days -> <next move>
```

- Exactly two drafts, each tagged `[optimize: X | sacrifice: Y]`. (checked)
- The two optimize values differ, and neither is a tone ("warmer", "more formal",
  "shorter"). (checked)
- A matrix with the columns Optimizes, Sacrifices, Best when and one row per draft.
  (checked)
- `Recommendation:` names exactly one draft letter. (checked)
- A decision tree with two or more branches. (checked)
- No merge language: "best of both worlds", "combine the strengths", "hybrid". (checked)

## S3 - high stakes (three drafts, adversary, pre-mortem)

A difficult 1:1, important outreach, a negotiation, a relationship repair, an escalation.

```
[S3 · channel: email · reader: ... · fork axis: ...]
Named adversary: <specific role, in a specific state> - catches: <the failure they would spot>
Pre-mortem: two weeks after sending, the worst plausible outcome is <one outcome>; Draft <X> minimizes it.

Draft A [optimize: ... | sacrifice: ...]
<draft>

Draft B [optimize: ... | sacrifice: ...]
<draft>

Draft C [optimize: ... | sacrifice: ...]
<draft>

| Draft | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A | | | |
| B | | | |
| C | | | |

Recommendation: B. <one-line reason>
Graft: <optional, one strictly additive sentence from another draft, same register>

Decision tree:
- If ... -> ...
- If ... -> ...
- If no reply in ... -> ...
```

Everything in S2, plus:

- Exactly three drafts. (checked)
- `Named adversary:` a role of three or more words with a `catches:` clause. "A skeptic"
  or "the reader" fails. (checked)
- `Pre-mortem:` one line, at most 45 words. (checked; over the limit is a warning)
- A decision tree with three or more branches. (checked)

## S4 - spoken (interview answer, talk, forum)

S3, plus:

- `Read-aloud check:` one line on whether it lands spoken at a normal pace: breath
  length, numbers and proper nouns paced, no nested clauses. (checked)
- `Delivery notes:` optional, only when useful.

## S5 - strategic (board memo, negotiation position, investor update)

S3, plus an answer-first argument and a three-pass edit (logic, then concision, then
voice):

- `Assumptions:` the ones that would change the recommendation. (checked)
- `Counterargument:` the strongest one, stated fairly. (checked)
- `Decision point:` what the reader must decide, by when. (checked)
- `Edit passes:` optional, one line per pass.

## Unattended runs (no human in the loop)

A scheduled or batch run has nobody to answer questions. It does not fork.

```
assumption: <job / reader / stakes / channel inferred, one line>
<the single send-ready draft>
```

Lint it in draft mode (`gates/lint.py draft.txt --channel <name>`), not contract mode.

## Overrides the user can give

- "just one draft": drop to S1 shape at any tier; say so in the header.
- "give me options": the drafts must still differ by objective, not tone.
- "too AI" or "doesn't sound like me": rewrite at once, show only the new draft, then one
  line naming the pattern removed.
