# Voice profile: Rae Calder (example)

Rae Calder is an invented person. She runs operations at Fernway Freight, an invented
mid-size logistics company. Copy this file to `voice-profile.md`, replace every section
with your own evidence, and keep it out of any public repo: a real profile describes real
people and real messages.

The method in `skills/drafting-harness/SKILL.md` is the same for every user. This file is
the only part that is personal. `gates/lint.py --profile` reads three sections from it
(Keep words, Extra banned phrases, Length caps); the skill reads the rest.

## Who I am, in one line

Head of operations who writes like a dispatcher: the number first, the ask second, no
warm-up.

## Keep words

Words I actually use. The shared banned list must never flag these for me.

- roadmap   # I mean the literal quarterly route plan document, not the cliche
- navigate  # dispatch software screens; "navigate to Loads" is a real instruction

## Extra banned phrases

Phrases I never want to send, on top of the shared list.

- per my last email
- just checking in
- quick question

## Length caps

Overrides for the default channel caps in `gates/lint.py`.

- slack: 500 chars
- email: 100 words

## Mechanics

- Proper capitalization and punctuation every time; casual tone lives in word choice,
  not in dropped capitals.
- Spaced hyphen " - " where a dash is needed. Never an em dash.
- No exclamation marks in work email. One is fine in a text to a friend.
- Contractions everywhere except legal and vendor disputes.

## Vocabulary that is mine (keep when it occurs, never inject)

- "rough cut" for a first draft
- "two cents" when asking for advice
- "ship it" to approve

## Registers (by relationship role, never by named person)

| Role | Register | Rules |
|---|---|---|
| My manager | BLUF operator | The number in sentence one; one ask; no background unless asked |
| Peers on other teams | Direct, credit then add | One clause of credit, then the add; never "great point, and" |
| My team | Coach | A question before the answer; one concrete next step |
| Vendors and carriers, disputes | Firm and courteous | Numbered asks, exact amounts, a date; no adjectives |
| Recruiters | Evaluative peer | What caught my eye, why I am credible in one line, next step |
| Close friends | Short and warm | One idea per message; no structure; no sign-off |
| Unknown recipient | Ask before drafting | Never invent a shared history |

## Sign-offs

- "Rae" to peers and my team
- "Rae Calder" to vendors, recruiters and anyone new
- None in chat

## Judgment checks that are mine

Ranked. The shared checklist in the skill runs first; these run after it.

1. Any draft to my manager without a number in the first two sentences.
2. A vendor dispute that explains backstory before the ask.
3. A message to my team that answers a question they could have answered themselves.
4. Anything over two short paragraphs in a text.

## Named adversaries I use most

Roles from `docs/method.md` that catch my usual failures:

- the CFO reading my budget ask on her phone between meetings - catches: a number with no source
- the carrier's account manager who has heard every excuse - catches: an ask with no date
