# The method, and why it works

FRAME → FORK → FIGHT → FINISH is a drafting loop for messages that have to work on one
reader. This page explains the reasoning behind each step, the adversary library, and
the two rules people push back on most: fork by objective, and select instead of merge.

## The problem with "give me three versions"

Ask a model for options and you usually get the same message three times at different
temperatures: warm, warmer, warmest. The reader would react the same way to all three.
You have spent attention choosing between drafts that do not differ in any way that
matters, and the real decision (what is this message trying to win?) was never made.

## FORK: opposed objective functions

A message is a small optimization problem. It can try to get a fast yes, protect the
relationship, be defensible if forwarded, keep options open, or set a deadline. Those
goals pull against each other. A short ask with a date gets speed and gives up room to
recover. A context-first note protects the relationship and gives up speed.

So each draft is built to maximize one objective and to admit what it gives up:

```
Draft A [optimize: urgency | sacrifice: room to recover]
Draft B [optimize: relationship | sacrifice: speed]
```

Three things follow from writing the tag down:

1. **The choice becomes explicit.** The matrix row "Best when" forces the writer to name
   the condition under which each draft is right. Picking a draft is now a judgment about
   the reader, not about wording.
2. **Fake forks become detectable.** If the optimize value is a tone ("warmer", "more
   formal", "shorter"), or two drafts optimize the same thing, the fork is fake.
   `gates/lint.py --contract` fails both.
3. **The validity test has something to test.** Would this reader plausibly react
   differently to A and B? With opposed objectives the answer is usually yes, by
   construction. With tone variants it is usually no.

Axis library (pick the one where this reader's reaction actually splits):

| Axis | A wins | B wins |
|---|---|---|
| directness vs relationship | a clear answer now | goodwill for the next ask |
| brevity vs defensibility | a fast read | survives being forwarded to a skeptic |
| ask-led vs context-led | the ask cannot be missed | the reader understands why first |
| reveal vs withhold | trust, no surprise later | control of the story |
| now vs later | momentum | better information |
| reader's interest vs writer's interest | the reader feels served | the writer's goal is stated plainly |
| escalation vs room to recover | the problem gets fixed | the relationship survives a miss |
| speed to a yes vs reversibility | a full commitment | a small, stoppable commitment |

## FIGHT: a named adversary and a one-line pre-mortem

"Pressure-test this draft" produces generic advice because "a skeptic" has no job, no
mood and no history. A specific role does. "The CFO reading this on her phone between
board prep meetings" generates concrete objections at once: where does the savings
number come from, when does the spend stop, why is this in my inbox today.

Pick the one reader most likely to reject the draft, and write what they catch. Then ask
five questions as that reader:

1. Which line do I reject?
2. What is the worst plausible misunderstanding?
3. What information is missing?
4. Which sentence sounds generated rather than lived?
5. What happens two weeks after this is sent?

The last question is the pre-mortem. It gets one line of its own because it changes the
recommendation more often than any other check: "Two weeks after sending this exact
draft, the worst plausible outcome is a 'not this quarter' because the savings looked
unsourced; Draft B minimizes it."

### Adversary library

Generalized to roles. Each entry is who they are, in what state, and what they catch.

| Adversary | Catches |
|---|---|
| The skeptical CFO, reading on her phone between meetings | a number with no source; an ask with no end date |
| The recruiter screening 200 profiles before lunch | a generic pitch; desperation; job-description parroting |
| The executive who hates consultant-speak | fog, frameworks, "alignment" with no decision |
| The engineer asking "where is the mechanism?" | claims with no how; hand-waving about AI |
| The counterparty's lawyer | ambiguity; warmth that reads as an opening; extra options offered |
| The worried parent at 7am | abstract probabilities used as reassurance; no plan with checkpoints |
| The close friend who can tell when you are performing | manufactured sentiment; corporate structure in a personal note |
| The mentor who catches over-consoling | sympathy where a reframe and a next step belong |
| The busy manager skimming on a phone | the ask buried below the fold; three asks with no owner |
| The colleague who spots AI tells | em dashes, symmetrical triplets, "that said", recap endings |
| The hiring manager two days after the onsite | a thank-you that adds nothing; a follow-up with no artifact |

Add your own in the voice profile. A good entry is specific enough that you can hear
their reply.

## FINISH: select, never merge

After the fork and the fight, there is a strong pull to combine the best parts. Resist it.
Each draft was built to win one objective. A merge averages the objectives, and the
average wins none of them: the urgency draft loses its date, the relationship draft
loses its warmth, and the result is longer than either.

The rule:

- **Select one draft** and say why in one line tied to a fact about the reader.
- **Graft at most one sentence** from another draft, and only when it is strictly
  additive (it adds information, not a second objective), keeps the register, and does
  not erase the tradeoff. Record it on a `Graft:` line so the reader of the output can
  see what moved.
- **If you want to merge, the fork was wrong.** Reaching for "best of both worlds" means
  the two drafts were not really opposed, or the real objective was a third one nobody
  drafted. Go back to FORK with a sharper axis.

The decision tree after the recommendation is the payoff of selecting: once you have
committed to one draft, you can plan the replies to it. Merged drafts have no clear
replies to plan for.

## Stakes: output scales with stakes, not effort

The most common failure in assisted writing is not a bad draft. It is a one-line
confirmation delivered with a matrix, three options and a rationale. The stakes tier sets
the size of the output, and S1 is one line.

Asymmetric defaults handle the unclear cases. Between S1 and S2, go down: padding a
routine message wastes the reader's time every time. Between S2 and S3, go up: a hard
message under-prepared costs more than an extra draft. Above that, ask.

## Gates: what a script can judge, and what it cannot

The harness splits checks by who can judge them:

- **Mechanical (script).** Em dashes, banned phrases, placeholders, paragraph length,
  markdown and tables in the wrong channel, length caps. These are countable, so a
  script counts them. A model asked "did you avoid em dashes?" will say yes; a regex
  will not be persuaded.
- **Contract (script).** The output shape per tier: tags, matrix, one selection, tree
  branches, a specific adversary, a one-line pre-mortem, no merge language. Also
  countable.
- **Judgment (model or human).** Register fit, whether the forks would split this
  reader, whether a sentence sounds lived. These stay a ranked checklist in the skill,
  because no regex knows the reader.

Keeping the scripted gates outside the model is the point. The model drafts; the gate
decides whether the draft ships.

## Method and voice are separate files

The method is the same for anyone. A voice profile is personal: the words you actually
use, the registers you use with each kind of relationship, your sign-offs, the adversaries
that catch your usual mistakes. Keeping them apart has two effects:

1. The method can be shared and tested without exposing anyone's messages or contacts.
2. The gates can respect the person. A banned list that flags "roadmap" is right for
   most writers and wrong for someone who means a literal route plan. The profile's
   "Keep words" list exempts it, and `gates/lint.py --profile` honors that.

Registers in the profile are defined by relationship role (my manager, vendors in a
dispute, close friends), not by named people. A role-based register generalizes to the
next person in that role; a per-person rule set does not, and it puts private
information in the one file you might be tempted to share.

## Where this came from

I built this as my own writing system and used it for outbound messages where the stakes
were real: recruiter replies, negotiation emails, hard 1:1s. The private layer (my
relationships, my vocabulary, my message samples) stays private. This repo is the method
and the gates, with an invented persona standing in for the personal layer.
