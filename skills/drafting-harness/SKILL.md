---
name: drafting-harness
description: "Drafting method for consequential writing: FRAME the job, reader, channel and stakes; FORK drafts by opposed objectives (never by tone); FIGHT each draft with a named adversary and a one-line pre-mortem; FINISH by selecting one draft (never merging). Output scales with stakes (S1 to S5) and every draft passes mechanical gates (gates/lint.py) before it ships. Use for any email, Slack, text, LinkedIn message, memo or spoken answer the user will send or say, and for 'give me options', 'make it less AI', 'draft a reply'."
---

# Drafting harness

A method for writing messages that have to work on a specific reader. It is the same for
every user. What is personal (words you use, registers by relationship, sign-offs) lives
in a separate voice profile the user fills in from `templates/voice-profile.example.md`.

Principle: mechanics aspire up, vocabulary stays real. Clean spelling and punctuation
every time; the user's own words are never scrubbed for being informal.

## 0. Load

1. If the user has a voice profile (`voice-profile.md` beside this skill, or a path they
   name), read it. Without one, write in a neutral, direct voice and do not invent a
   personal style.
2. The voice profile activates only when the draft goes out as the user (outbound) or the
   user asks for their voice. Never put personal tics into neutral explanations,
   research summaries, code or literal strings.
3. Precedence when instructions conflict: accuracy and safety; the user's explicit
   instruction in this message; a required legal or format standard; literal source
   text where exact wording matters; the reader's comprehension; the voice profile;
   cosmetic style.

## 1. FRAME

Set four variables before writing a word:

- **Job**: the one concrete thing the reader should do after reading.
- **Reader**: who, in what state ("the CFO, two days before board prep, who did not
  sponsor the pilot"). A role and a state, not just a name.
- **Channel**: slack, slack-thread, slack-dm, text (sms, WhatsApp, iMessage), email,
  linkedin, doc, or spoken.
- **Stakes**: S1 to S5, from the table below.

If the job, reader or goal is missing or still a bracketed placeholder ("[Recipient]"),
ask two or three sharp questions and stop. Do not invent a recipient, a company, a claim
or a shared history to fill the shape. A placeholder that reaches the draft is a defect.

In an unattended run (scheduled task, batch), do not ask: state a one-line assumption and
produce one draft.

### Stakes tiers

| Tier | Examples | Output |
|---|---|---|
| S1 routine | confirm a time, thanks, simple logistics | One draft. No alternatives, no rationale unless asked |
| S2 standard | normal work message, ordinary recruiter reply, vendor request | Two drafts, tradeoff matrix, recommendation, decision tree |
| S3 high | hard 1:1, important outreach, negotiation, repair, escalation | Three drafts, named adversary, pre-mortem, matrix, recommendation, decision tree |
| S4 spoken | interview answer, talk, forum | S3 plus a read-aloud check |
| S5 strategic | board memo, negotiation position, investor update | S3 plus answer-first argument, assumptions, counterargument, decision point, three-pass edit |

Asymmetric defaults when the tier is unclear:

- S1 or S2: go down to S1. Most messages are routine, and padding a routine message is
  the most common failure.
- S2 or S3: go up to S3. Under-preparing a consequential message costs more than an extra
  draft.
- S3, S4 or S5: ask.

Single-path exception: if there is one obvious right answer and no real tradeoff, write
one draft at any tier and say so in the header. Never manufacture divergence.

## 2. FORK (S2 and up)

Fork by opposed objective functions. Each draft maximizes one thing and names what it
gives up, as a tag:

```
Draft A [optimize: urgency | sacrifice: room to recover]
```

Good axes: directness vs relationship; brevity vs defensibility; ask-led vs context-led;
reveal vs withhold; now vs later; reader's interest vs writer's interest; escalation vs
room to recover; speed to a yes vs reversibility.

Bad axes: warm vs warmer; formal vs slightly formal; long vs a bit shorter. Tone is a
setting inside a draft, not an objective.

Validity test: would this reader plausibly react differently to the two drafts? If not,
the fork failed. Pick a sharper axis and regenerate.

## 3. FIGHT (S3 and up)

1. **Named adversary.** Pick the specific reader most likely to reject the draft, as a
   role with a job and a state, plus what they catch. "A skeptic" is not an adversary.
   Library in `docs/method.md`, for example:
   - the skeptical CFO reading on her phone between meetings - catches: a number with no source
   - the recruiter screening 200 profiles before lunch - catches: a generic pitch
   - the counterparty's lawyer - catches: ambiguity, and warmth that reads as an opening
2. **Five questions**, asked as that reader: which line do I reject; what is the worst
   plausible misunderstanding; what is missing; which sentence sounds generated rather
   than lived; what happens two weeks after this is sent?
3. **Pre-mortem, one line**: "Two weeks after sending this exact draft, the worst
   plausible outcome is ___; Draft X minimizes it."

Fix the drafts. Show the adversary and pre-mortem lines; keep the rest of the analysis
internal unless the user asks.

## 4. FINISH

Select one draft and name it: `Recommendation: B. <one-line reason tied to a fact about
the reader>`.

Never merge. A merged draft averages two objective functions and wins neither. You may
graft one sentence from another draft only when it is strictly additive, keeps the
register, and does not erase the tradeoff; record it on a `Graft:` line. If you want to
write "best of both worlds" or "combine the strengths", the fork axis was wrong: go back
to FORK.

## 5. Output contract

Follow `templates/output-contract.md` exactly for the tier: header line
`[S2 · channel: email · reader: ... · fork axis: ...]`, tagged drafts, the matrix with
columns Optimizes, Sacrifices, Best when, one recommendation, a decision tree
(`- If they reply X -> do Y`, two branches at S2, three from S3), and for S3 and up the
`Named adversary:` and `Pre-mortem:` lines. Each draft is written in the channel's native
format, ready to paste.

## 6. Gates (before anything ships)

**Gate 1, mechanical (scripted).** Run on each draft:

```
python3 gates/lint.py draft.txt --channel <channel> [--profile voice-profile.md]
```

It fails em dashes (and "--" used as one), banned AI-tell phrases (`gates/banned.tsv`,
minus the profile's keep words), surviving placeholders, paragraphs over three sentences
(the soggy middle), recap closers, markdown in plain-text channels, tables in Slack, text
and LinkedIn, and channel length caps. It warns on hedges, apology openers, hashtag walls
and "not just X but Y". Fix every FAIL. Read every WARN.

**Gate 2, contract (scripted).** Run on the full output:

```
python3 gates/lint.py output.md --contract
```

It checks the tier shape: draft count, tags, fake forks (tone objectives, repeated
objectives), the matrix, a single selection, merge language, decision-tree branches,
a specific adversary, a one-line pre-mortem, and the S4 and S5 sections.

If no shell is available, apply both gates by hand and say "gates run by hand" in one line.

**Gate 3, judgment (not scriptable).** Ranked; check in order:

1. The draft does the job from FRAME; the ask is unmistakable and has an owner.
2. The register fits the reader's relationship to the user (from the voice profile).
3. Barbell length: a one-to-three-sentence reaction, or real structure. Nothing in
   between that explains without arriving.
4. At most three ideas; every ask tied to a named owner.
5. The forks differ in outcome, not tone.
6. Hedges ("I think", "perhaps") are not weakening a claim the user can state.
7. No apology or humility opener that an actual mistake did not earn.
8. The last line is the ask or one line worth remembering, never a summary.
9. The user's real words, from the profile, survived the edit.
10. Nothing sounds manufactured: no symmetrical three-part slogans, no pseudo-profound
    closer, no warmth adjectives, no invented history or intimacy.

## 7. Channel rules

- **Text and chat apps**: one idea per bubble, several short bubbles rather than one
  block, no markdown, no tables, lists only when the user writes that way.
- **Slack**: the decision or status in line one, up to three bullets, a doc link for
  depth. No tables. Single asterisks for bold.
- **Email**: the ask in the subject when there is one; body under 120 words unless it is
  a document; paragraphs of three short sentences or fewer.
- **LinkedIn**: no markdown, no bullets, no hashtag walls, every claim verifiable.
- **Doc**: full structure is fine; a dated version line at the top; a five-line summary.
- **Spoken**: contractions, one idea per breath, numbers and proper nouns paced, and the
  test "would I say this out loud?" on every sentence.

## 8. Corrections

When the user says "too AI", "too long", "too polished" or "doesn't sound like me":
rewrite at once, show only the new draft, then one line naming the pattern removed
("Removed: a recap closer and two hedges"). Do not defend the previous draft.

## 9. Edit mode

When editing the user's own text: the minimum effective edit. Fix what fails the gates,
keep strong human sentences, protect every specific fact, name, number and literal string.
`slop check <text>` means detect only: name each pattern, quote the line, give the fix in
a few words. Never rewrite in slop-check mode and never claim to detect AI authorship.

## Files

- `templates/output-contract.md`: the output shape per tier.
- `templates/voice-profile.example.md`: the personal layer, with an invented persona.
- `docs/method.md`: why the method works, and the named-adversary library.
- `gates/lint.py`, `gates/banned.tsv`: the mechanical and contract gates.
