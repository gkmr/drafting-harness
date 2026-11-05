#!/usr/bin/env python3
"""lint.py - the mechanical gate of the drafting harness.

Two modes.

Draft mode (default) lints one draft for one channel:
    python3 gates/lint.py draft.txt --channel slack
    python3 gates/lint.py draft.txt --channel email --profile my-voice-profile.md
    cat draft.txt | python3 gates/lint.py - --channel text

Contract mode checks a full harness output against its stakes tier (header,
tagged drafts, tradeoff matrix, one selected draft, decision tree, named
adversary, pre-mortem), then lints every draft inside it for the channel the
header names:
    python3 gates/lint.py output.md --contract

A draft file may start with a "channel: <name>" line. It is used when
--channel is not given and is not counted as part of the draft.

Exit status: 0 when there is no FAIL finding, 1 when there is one, 2 on a
usage error. WARN findings print but never fail the run.

Python 3.8+, standard library only, no network.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_BANNED = os.path.join(HERE, "banned.tsv")

# Length caps and format rules per channel. "chars", "lines" and "words" apply
# to the whole draft; "bubble_chars" applies to each paragraph (one chat bubble).
CHANNELS = {
    "slack": {"chars": 600, "lines": 8, "markdown": "slack", "tables": "fail"},
    "slack-thread": {"chars": 400, "markdown": "slack", "tables": "fail"},
    "slack-dm": {"chars": 300, "markdown": "slack", "tables": "fail"},
    "text": {"bubble_chars": 160, "markdown": "none", "tables": "fail", "lists": "warn"},
    "email": {"words": 120, "markdown": "warn", "tables": "warn"},
    "linkedin": {"markdown": "none", "tables": "fail", "lists": "fail", "hashtags": 3},
    "doc": {"markdown": "ok", "tables": "ok", "paragraph": "warn"},
}
ALIASES = {
    "sms": "text", "imessage": "text", "whatsapp": "text", "signal": "text",
    "linkedin-dm": "linkedin", "linkedin-post": "linkedin",
    "memo": "doc", "markdown": "doc",
}
MAX_PARAGRAPH_SENTENCES = 3

EM_DASH = re.compile("\u2014|&(?:mdash|#8212);")  # the character and its HTML entities
DOUBLE_HYPHEN = re.compile(r"(?<=\w) -- (?=\w)|(?<=[A-Za-z])--(?=[A-Za-z])")
EN_AS_DASH = re.compile(r"(?<=\w) \u2013 (?=\w)")

MD_BOLD = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
MD_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+\S")
MD_LINK = re.compile(r"\[[^\]\n]+\]\((?:https?://|/|#)[^)\s]*\)")
MD_CODE = re.compile(r"`[^`\n]+`")
LIST_LINE = re.compile(r"^\s*(?:[-*\u2022]|\d{1,2}[.)])\s+\S")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
HASHTAG = re.compile(r"(?<![\w#])#[A-Za-z][\w]*")

PLACEHOLDERS = [
    re.compile(r"\[(?!\s?\]|[xX]\]|\d+\])[^\]\n]{1,60}\](?!\()"),
    re.compile(r"\{\{[^}\n]{1,40}\}\}"),
    re.compile(r"<[a-z][a-z _-]{1,30}>"),
    re.compile(r"\b(?:TBD|TODO|TK|XX+)\b"),
    re.compile(r"_{3,}"),
]
NOT_JUST_BUT = re.compile(r"\bnot (?:just|only|merely) [^.!?\n]{1,60}?,? but\b", re.I)
APOLOGY_OPENER = re.compile(
    r"\b(sorry to (bother|bug|pester)|i know you'?re (busy|slammed)|apologies for (the )?(bother|intrusion))\b", re.I)
RECAP_CLOSER = re.compile(r"^\s*(in summary|to summarize|in conclusion|to recap|in short|all in all)\b", re.I)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])[\"')\]]?\s+(?=[A-Z0-9\"'(])")
WORD = re.compile(r"\b[\w'\u2019-]+\b")


@dataclass
class Finding:
    rule: str
    severity: str  # "fail" or "warn"
    line: int
    excerpt: str
    fix: str

    def show(self) -> str:
        return "%-4s  %-22s line %-3d %s\n      fix: %s" % (
            self.severity.upper(), self.rule, self.line, self.excerpt[:90], self.fix)


# ---------------------------------------------------------------- loading

def load_banned(path: str = DEFAULT_BANNED):
    rules = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 4:
                raise ValueError("bad banned.tsv line (need 4 tab-separated fields): %r" % line)
            sev, rule, pattern, fix = parts
            rules.append((sev.strip(), rule.strip(), re.compile(pattern, re.I), fix.strip()))
    return rules


def load_profile(path):
    """Read a voice profile. Returns keep words, extra banned phrases, cap overrides.

    Recognized sections (level-2 headings, case-insensitive):
      ## Keep words              - bullets: words the banned list must never flag for you
      ## Extra banned phrases    - bullets: phrases you never want to send
      ## Length caps             - bullets like "- slack: 500 chars" or "- email: 90 words"
    """
    profile = {"keep": [], "banned": [], "caps": {}}
    if not path:
        return profile
    section = None
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if line.startswith("## "):
                head = line[3:].strip().lower()
                section = ("keep" if head.startswith("keep words") else
                           "banned" if head.startswith("extra banned") else
                           "caps" if head.startswith("length caps") else None)
                continue
            if not section or not line.startswith(("- ", "* ")):
                continue
            item = line[2:].split(" #", 1)[0].strip().strip('"').strip()
            if not item:
                continue
            if section == "keep":
                profile["keep"].append(item.lower())
            elif section == "banned":
                profile["banned"].append(item)
            else:
                m = re.match(r"([\w-]+)\s*:\s*(\d+)\s*(chars?|words?|lines?|bubble chars?)\b", item, re.I)
                if m:
                    unit = m.group(3).lower()
                    key = ("bubble_chars" if unit.startswith("bubble") else
                           "chars" if unit.startswith("char") else
                           "words" if unit.startswith("word") else "lines")
                    profile["caps"].setdefault(resolve_channel(m.group(1)), {})[key] = int(m.group(2))
    return profile


def resolve_channel(name):
    name = (name or "").strip().lower()
    return ALIASES.get(name, name)


# ---------------------------------------------------------------- helpers

def strip_code(text: str) -> str:
    """Blank out fenced and inline code, keeping line numbers stable."""
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"```.*?```", blank, text, flags=re.S)
    return MD_CODE.sub(blank, text)


def paragraphs(text: str):
    """Yield (first_line_number, [lines]) for each blank-line separated block."""
    block, start = [], 0
    for i, line in enumerate(text.split("\n"), 1):
        if line.strip():
            if not block:
                start = i
            block.append(line)
        elif block:
            yield start, block
            block = []
    if block:
        yield start, block


def sentences(text: str):
    flat = re.sub(r"\s+", " ", text.strip())
    return [s for s in SENTENCE_SPLIT.split(flat) if WORD.search(s)]


def words(text: str) -> int:
    return len(WORD.findall(text))


def is_structure(line: str) -> bool:
    return bool(LIST_LINE.match(line) or TABLE_ROW.match(line) or MD_HEADING.match(line))


def prose_runs(blocks):
    """Yield (line_number, lines) for each run of consecutive prose lines inside each block.

    A list item, table row or heading ends a run, so a paragraph followed by a list is
    judged on its prose alone.
    """
    for start, lines in blocks:
        run, run_start = [], start
        for k, line in enumerate(lines):
            if is_structure(line):
                if run:
                    yield run_start, run
                run = []
                continue
            if not run:
                run_start = start + k
            run.append(line)
        if run:
            yield run_start, run


GREETING = re.compile(r"^\s*(hi|hey|hello|dear|morning|evening)\b[^.!?]{0,40}[,!]?\s*$", re.I)
SUBJECT = re.compile(r"^\s*subject:", re.I)


def is_frame_block(lines) -> bool:
    """Subject lines, greetings and sign-offs: the frame around a message, not its body."""
    if all(SUBJECT.match(l) or GREETING.match(l) for l in lines):
        return True
    return len(lines) <= 3 and all(len(WORD.findall(l)) <= 4 and not re.search(r"[.?]\s*$", l) for l in lines)


def has_table(lines) -> bool:
    if any(TABLE_SEP.match(l) for l in lines):
        return True
    run = 0
    for l in lines:
        run = run + 1 if TABLE_ROW.match(l) else 0
        if run >= 2:
            return True
    return False


def split_header(text: str):
    """Pull an optional leading 'channel: x' line. Returns (channel or None, body, line_offset)."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        m = re.match(r"^\s*channel:\s*([\w-]+)\s*$", line, re.I)
        if m:
            return m.group(1), "\n".join(lines[i + 1:]), i + 1
        break
    return None, text, 0


def meter(text: str, channel: str, caps: dict) -> str:
    body = text.strip()
    parts = []
    if "chars" in caps:
        parts.append("%d/%d chars" % (len(body), caps["chars"]))
    if "lines" in caps:
        parts.append("%d/%d lines" % (sum(1 for l in body.split("\n") if l.strip()), caps["lines"]))
    if "words" in caps:
        parts.append("%d/%d words" % (words(email_body(body)), caps["words"]))
    if "bubble_chars" in caps:
        longest = max([len(" ".join(b).strip()) for _, b in paragraphs(body)] or [0])
        parts.append("longest bubble %d/%d chars" % (longest, caps["bubble_chars"]))
    return "Length (%s): %s" % (channel, " \u00b7 ".join(parts) if parts else "no cap")


def email_body(text: str) -> str:
    return "\n".join(l for l in text.split("\n") if not re.match(r"^\s*subject:", l, re.I))


# ---------------------------------------------------------------- draft lint

def lint_draft(text: str, channel: str = "doc", profile=None, banned=None, offset: int = 0):
    """Lint one draft. Returns a list of Finding. offset shifts reported line numbers."""
    channel = resolve_channel(channel)
    if channel not in CHANNELS:
        raise ValueError("unknown channel %r (known: %s)" % (channel, ", ".join(sorted(CHANNELS))))
    profile = profile or {"keep": [], "banned": [], "caps": {}}
    banned = banned if banned is not None else load_banned()
    caps = dict(CHANNELS[channel])
    caps.update(profile["caps"].get(channel, {}))
    keep = profile["keep"]
    out = []
    raw_lines = text.split("\n")
    plain = strip_code(text)
    plain_lines = plain.split("\n")

    def add(rule, sev, lineno, excerpt, fix):
        out.append(Finding(rule, sev, lineno + offset, excerpt.strip(), fix))

    # 1. dashes
    for i, line in enumerate(plain_lines, 1):
        if EM_DASH.search(line) or DOUBLE_HYPHEN.search(line):
            add("em-dash", "fail", i, raw_lines[i - 1], "use ' - ', a comma, or two sentences")
        elif EN_AS_DASH.search(line):
            add("em-dash", "warn", i, raw_lines[i - 1], "an en dash used as a dash reads the same; use ' - '")

    # 2. banned phrases (shared list, then the profile's own list)
    rules = list(banned) + [("fail", "profile-banned", re.compile(re.escape(p), re.I), "your voice profile bans this")
                            for p in profile["banned"]]
    for i, line in enumerate(plain_lines, 1):
        for sev, rule, rx, fix in rules:
            for m in rx.finditer(line):
                hit = m.group(0).lower().strip(" ,")
                if any(hit == k or hit.startswith(k) for k in keep):
                    continue
                add(rule, sev, i, line, '"%s": %s' % (m.group(0).strip(" ,"), fix))
                break
        if NOT_JUST_BUT.search(line):
            add("not-just-x-but-y", "warn", i, line, "say the one thing that matters")

    # 3. placeholders that survived from the brief (code blocks are exempt)
    for i, line in enumerate(plain_lines, 1):
        for rx in PLACEHOLDERS:
            m = rx.search(line)
            if m:
                add("placeholder", "fail", i, raw_lines[i - 1], "fill %r or ask for it; never ship a blank" % m.group(0))
                break

    # 4. paragraph shape: soggy middle, opener, closer
    blocks = list(paragraphs(plain))
    para_sev = caps.get("paragraph", "fail")
    for start, run in prose_runs(blocks):
        n = len(sentences(" ".join(run)))
        if n > MAX_PARAGRAPH_SENTENCES:
            add("soggy-middle", para_sev, start, run[0],
                "%d sentences in one paragraph; keep it to %d, or give it structure (a list, or split by idea)"
                % (n, MAX_PARAGRAPH_SENTENCES))
    body_blocks = [b for b in blocks if not is_frame_block(b[1])]
    if body_blocks:
        first_start, first_lines = body_blocks[0]
        if APOLOGY_OPENER.search(" ".join(first_lines)):
            add("apology-opener", "warn", first_start, first_lines[0],
                "open with the point; apologize only for a real mistake")
        last_start, last_lines = body_blocks[-1]
        if len(body_blocks) > 1 and RECAP_CLOSER.match(last_lines[0]):
            add("recap-closer", "fail", last_start, last_lines[0], "end on the ask or one line worth remembering")

    # 5. channel format
    md = caps.get("markdown", "ok")
    lists_rule = caps.get("lists")
    for i, line in enumerate(raw_lines, 1):
        kinds = []
        if MD_BOLD.search(line):
            kinds.append("bold")
        if MD_HEADING.match(line):
            kinds.append("heading")
        if MD_LINK.search(line):
            kinds.append("link")
        if MD_CODE.search(line) and md != "slack":
            kinds.append("code")
        if kinds and md in ("none", "warn"):
            add("markdown-in-plain-text", "fail" if md == "none" else "warn", i, line,
                "%s does not render markdown (%s); write it as plain text" % (channel, ", ".join(kinds)))
        elif md == "slack" and ("bold" in kinds or "heading" in kinds or "link" in kinds):
            add("markdown-in-plain-text", "warn", i, line,
                "Slack mrkdwn uses *single* asterisks and <url|text> links; this will show raw")
        if lists_rule and LIST_LINE.match(line) and not TABLE_ROW.match(line):
            add("list-in-plain-text", lists_rule, i, line,
                "%s reads as flow; turn the list into one sentence or separate messages" % channel)
    tables = caps.get("tables", "ok")
    if tables != "ok":
        for start, lines in paragraphs(text):
            if has_table(lines):
                add("table-in-chat", tables, start, lines[0],
                    "tables break in %s; use 2 to 3 short lines or link a doc" % channel)
    if "hashtags" in caps:
        tags = HASHTAG.findall(plain)
        if len(tags) > caps["hashtags"]:
            first = next(n for n, l in enumerate(plain_lines, 1) if HASHTAG.search(l))
            add("hashtag-wall", "warn", first, " ".join(tags), "%d hashtags; keep %d or fewer" % (len(tags), caps["hashtags"]))

    # 6. length caps
    body = text.strip()
    if "chars" in caps and len(body) > caps["chars"]:
        add("length", "fail", 1, "%d/%d chars" % (len(body), caps["chars"]),
            "cut, or move depth into a linked doc")
    if "lines" in caps:
        n = sum(1 for l in body.split("\n") if l.strip())
        if n > caps["lines"]:
            add("length", "fail", 1, "%d/%d lines" % (n, caps["lines"]), "cut to the top ideas")
    if "words" in caps:
        n = words(email_body(body))
        if n > caps["words"]:
            add("length", "fail", 1, "%d/%d words" % (n, caps["words"]), "cut, or attach a doc and keep the ask")
    if "bubble_chars" in caps:
        for start, lines in paragraphs(text):
            n = len(" ".join(l.strip() for l in lines))
            if n > caps["bubble_chars"]:
                add("length", "fail", start, lines[0],
                    "bubble is %d/%d chars; split it into separate messages" % (n, caps["bubble_chars"]))
    out.sort(key=lambda f: (f.line, f.rule))
    return out


# ---------------------------------------------------------------- contract lint

HEADER = re.compile(r"^\[\s*(S[1-5])\b([^\]]*)\]\s*$")
DRAFT_TAG = re.compile(r"^Draft ([A-E])\s*\[\s*optimize:\s*([^|\]]+?)\s*\|\s*sacrifice:\s*([^\]]+?)\s*\]\s*$")
DRAFT_LINE = re.compile(r"^Draft ([A-E])\b")
CONTROL = re.compile(
    r"^(Draft [A-E]\b|\||Recommendation:|Rationale:|Named adversary:|Pre-mortem:|Decision tree:|"
    r"Response tree:|Read-aloud check:|Delivery notes:|Assumptions:|Counterargument:|Decision point:|"
    r"Edit passes:|Graft:)")
MERGE = re.compile(
    r"best of (all|both) worlds|combin(e|es|ed|ing) the (best|strengths)|\bmerged? (draft|version)\b|"
    r"\bhybrid (of|draft|version)\b|\bblend(ed|ing)? (of )?(the |both )?(drafts|versions)\b|frankenstein", re.I)
TONE = re.compile(
    r"^(more |less |slightly |a bit )?(warm|warmer|warmest|warmth|friendly|friendlier|formal|casual|polite|"
    r"soft|softer|firm|firmer|short|shorter|long|longer|concise|detailed|professional|nice|nicer|tone|upbeat)$", re.I)
GENERIC_ADVERSARY = re.compile(
    r"^(a |the )?(skeptic|critic|reader|recipient|audience|someone|anyone|stakeholder|person|user|people)s?$", re.I)
TIER_DRAFTS = {"S1": 1, "S2": 2, "S3": 3, "S4": 3, "S5": 3}
TIER_BRANCHES = {"S2": 2, "S3": 3, "S4": 3, "S5": 3}
TIER_SECTIONS = {"S4": ["Read-aloud check:"], "S5": ["Assumptions:", "Counterargument:", "Decision point:"]}


def labelled(lines, label):
    for i, l in enumerate(lines, 1):
        if l.startswith(label):
            return i, l[len(label):].strip()
    return None, None


def lint_contract(text: str, profile=None, banned=None):
    """Check a full harness output. Returns (findings, tier, channel)."""
    out = []
    lines = text.split("\n")

    def add(rule, lineno, excerpt, fix, sev="fail"):
        out.append(Finding(rule, sev, lineno, excerpt.strip(), fix))

    head_no, head = next(((i, l) for i, l in enumerate(lines, 1) if l.strip()), (1, ""))
    m = HEADER.match(head.strip())
    if not m:
        add("contract-header", head_no, head,
            "first line must be a header like [S2 \u00b7 channel: email \u00b7 reader: ... \u00b7 fork axis: ...]")
        return out, None, None
    tier = m.group(1)
    cm = re.search(r"channel:\s*([\w-]+)", m.group(2))
    if not cm:
        add("contract-header", head_no, head, "the header must name the channel, for example 'channel: slack'")
        return out, tier, None
    channel = resolve_channel(cm.group(1))
    if channel not in CHANNELS:
        add("contract-header", head_no, head, "unknown channel %r" % channel)
        return out, tier, channel

    # collect drafts: (letter, optimize, sacrifice, first_line, body_lines)
    drafts, untagged = [], []
    i = head_no
    while i < len(lines):
        line = lines[i]
        dm = DRAFT_LINE.match(line)
        if dm:
            tag = DRAFT_TAG.match(line.strip())
            if not tag:
                untagged.append((i + 1, line, dm.group(1)))
            body, j = [], i + 1
            while j < len(lines) and not CONTROL.match(lines[j]):
                body.append(lines[j])
                j += 1
            drafts.append((dm.group(1), tag.group(2) if tag else None, tag.group(3) if tag else None, i + 2, body))
            i = j
            continue
        i += 1
    if tier == "S1" and not drafts:
        body, j = [], head_no
        while j < len(lines) and not CONTROL.match(lines[j]):
            body.append(lines[j])
            j += 1
        drafts.append(("A", None, None, head_no + 1, body))

    table_lines = [(n, l) for n, l in enumerate(lines, 1) if TABLE_ROW.match(l)]
    want = TIER_DRAFTS[tier]
    if tier == "S1":
        if len(drafts) > 1:
            add("fork-on-s1", drafts[1][3] - 1, "Draft %s" % drafts[1][0],
                "S1 is single-path: one draft, no alternatives")
        if table_lines:
            add("fork-on-s1", table_lines[0][0], table_lines[0][1], "S1 carries no tradeoff matrix")
    else:
        if len(drafts) != want:
            add("draft-count", head_no, head, "%s needs exactly %d drafts, found %d" % (tier, want, len(drafts)))
        for lineno, line, letter in untagged:
            add("untagged-draft", lineno, line, "tag it: Draft %s [optimize: X | sacrifice: Y]" % letter)
        objectives = {}
        for letter, opt, sac, first, _ in drafts:
            if opt is None:
                continue
            if TONE.match(opt.strip()):
                add("fake-fork", first - 1, "Draft %s optimizes %r" % (letter, opt),
                    "a tone is not an objective; fork on what the draft is trying to win")
            if opt.strip().lower() == (sac or "").strip().lower():
                add("fake-fork", first - 1, "Draft %s optimizes and sacrifices %r" % (letter, opt),
                    "a draft cannot win and give up the same thing")
            key = opt.strip().lower()
            if key in objectives:
                add("same-objective", first - 1, "Drafts %s and %s both optimize %r" % (objectives[key], letter, opt),
                    "each draft must optimize a different objective")
            objectives.setdefault(key, letter)
        # matrix
        header_row = next(((n, l) for n, l in table_lines
                           if re.search(r"optimi[sz]es", l, re.I) and re.search(r"sacrifices", l, re.I)
                           and re.search(r"best when", l, re.I)), None)
        if not header_row:
            add("missing-matrix", head_no, head, "add | Draft | Optimizes | Sacrifices | Best when |")
        else:
            rows = [l for n, l in table_lines if n > header_row[0] and not TABLE_SEP.match(l)]
            if len(rows) != len(drafts):
                add("missing-matrix", header_row[0], header_row[1],
                    "matrix has %d rows for %d drafts" % (len(rows), len(drafts)))
        # selection
        rn, rec = labelled(lines, "Recommendation:")
        letters = {d[0] for d in drafts}
        if rec is None:
            add("no-selection", head_no, head, "add 'Recommendation: <one draft letter>. <one-line reason>'")
        else:
            first_clause = re.split(r"(?<=[.;:])\s", rec, maxsplit=1)[0]
            picked = set(re.findall(r"\b([A-E])\b", first_clause))
            if len(picked) != 1 or not picked <= letters:
                add("no-selection", rn, "Recommendation: " + rec,
                    "select exactly one draft by letter; selecting is the point of the fork")
        # decision tree
        tn = next((n for n, l in enumerate(lines, 1) if re.match(r"^(Decision|Response) tree:", l)), None)
        branches = 0
        if tn:
            for l in lines[tn:]:
                if re.match(r"^\s*[-*]\s+\S", l):
                    branches += 1
                elif l.strip() and not l.startswith(" "):
                    break
        need = TIER_BRANCHES[tier]
        if branches < need:
            add("thin-tree", tn or head_no, lines[tn - 1] if tn else head,
                "%s needs a decision tree with %d or more branches ('- If they reply X -> do Y'), found %d"
                % (tier, need, branches))
    # merge language anywhere
    for n, l in enumerate(lines, 1):
        if MERGE.search(l):
            add("merge", n, l, "select one draft; graft at most one strictly additive sentence")
    # adversary and pre-mortem from S3 up
    if tier in ("S3", "S4", "S5"):
        an, adv = labelled(lines, "Named adversary:")
        if adv is None:
            add("missing-adversary", head_no, head,
                "add 'Named adversary: <specific role with a job and a bad day> - catches: <failure mode>'")
        else:
            who, _, catches = adv.partition("catches:")
            who = who.strip().rstrip("-").strip()
            if GENERIC_ADVERSARY.match(who) or len(WORD.findall(who)) < 3 or not catches.strip():
                add("generic-adversary", an, "Named adversary: " + adv,
                    "name a specific role (who, in what state) and what they catch, e.g. "
                    "'the skeptical CFO reading on her phone - catches: a number with no source'")
        pn, pm = labelled(lines, "Pre-mortem:")
        if pm is None:
            add("missing-premortem", head_no, head,
                "add 'Pre-mortem: two weeks after sending, the worst plausible outcome is ...'")
        elif words(pm) > 45 or len(sentences(pm)) > 2:
            add("long-premortem", pn, "Pre-mortem: " + pm, "one line, one outcome", sev="warn")
        for label in TIER_SECTIONS.get(tier, []):
            if labelled(lines, label)[1] is None:
                add("missing-section", head_no, head, "%s needs a '%s' line" % (tier, label))
    # lint every draft body for the channel
    for letter, _, _, first, body in drafts:
        while body and not body[-1].strip():
            body = body[:-1]
        for f in lint_draft("\n".join(body), channel, profile, banned, offset=first - 1):
            f.excerpt = "Draft %s: %s" % (letter, f.excerpt)
            out.append(f)
    out.sort(key=lambda f: (f.line, f.rule))
    return out, tier, channel


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Mechanical gate for drafts (drafting-harness).")
    ap.add_argument("path", help="draft file, or - for stdin")
    ap.add_argument("--channel", help="one of: %s (aliases: %s)" % (
        ", ".join(sorted(CHANNELS)), ", ".join(sorted(ALIASES))))
    ap.add_argument("--profile", help="voice profile markdown (keep words, extra banned phrases, caps)")
    ap.add_argument("--banned", default=DEFAULT_BANNED, help="banned phrase list (tsv)")
    ap.add_argument("--contract", action="store_true", help="check a full harness output against its tier")
    ap.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = ap.parse_args(argv)

    try:
        if args.path == "-":
            text = sys.stdin.read()
        else:
            with open(args.path, encoding="utf-8") as fh:
                text = fh.read()
        profile = load_profile(args.profile)
        banned = load_banned(args.banned)
        if args.contract:
            findings, tier, channel = lint_contract(text, profile, banned)
            meter_line = "contract: %s, channel: %s" % (tier, channel)
        else:
            head_channel, body, offset = split_header(text)
            channel = resolve_channel(args.channel or head_channel or "doc")
            findings = lint_draft(body, channel, profile, banned, offset=offset)
            caps = dict(CHANNELS[channel])
            caps.update(profile["caps"].get(channel, {}))
            meter_line = meter(body, channel, caps)
    except (ValueError, OSError) as exc:
        print("lint.py: %s" % exc, file=sys.stderr)
        return 2
    fails = sum(1 for f in findings if f.severity == "fail")
    warns = len(findings) - fails
    if args.json:
        print(json.dumps({"file": args.path, "channel": channel, "meter": meter_line, "fails": fails,
                          "warns": warns, "findings": [asdict(f) for f in findings]}, indent=1))
    else:
        print("%s  (%s)" % (args.path, meter_line))
        for f in findings:
            print(f.show())
        print("%d fail, %d warn" % (fails, warns))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
