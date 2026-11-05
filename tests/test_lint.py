"""Tests for gates/lint.py. Run from the repo root:

    python3 -m unittest discover -s tests -v

Standard library only, no network. Em dashes are built from escapes so this file
itself passes the repo's own dash rule.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "gates"))
import lint  # noqa: E402

EM = "\u2014"
EXAMPLES = os.path.join(ROOT, "examples")
PROFILE = os.path.join(ROOT, "templates", "voice-profile.example.md")


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def rules(findings, severity=None):
    return {f.rule for f in findings if severity is None or f.severity == severity}


def fails(text, channel="doc", profile=None):
    return rules(lint.lint_draft(text, channel, profile), "fail")


def warns(text, channel="doc", profile=None):
    return rules(lint.lint_draft(text, channel, profile), "warn")


class DashRules(unittest.TestCase):
    def test_em_dash_fails(self):
        self.assertIn("em-dash", fails("The pilot worked %s mostly." % EM))

    def test_double_hyphen_counts_as_em_dash(self):
        self.assertIn("em-dash", fails("The pilot worked -- mostly."))
        self.assertIn("em-dash", fails("The pilot worked--mostly."))

    def test_spaced_hyphen_is_fine(self):
        self.assertNotIn("em-dash", fails("Quick favor - can you review the doc?"))

    def test_cli_flags_and_code_are_not_dashes(self):
        self.assertNotIn("em-dash", fails("Run it with --contract to check the tier."))
        self.assertNotIn("em-dash", fails("Use `a -- b` in the shell."))

    def test_en_dash_used_as_dash_warns(self):
        self.assertIn("em-dash", warns("The pilot worked \u2013 mostly."))


class BannedPhrases(unittest.TestCase):
    def test_ai_tell_words_fail(self):
        for word in ["leverage", "delve", "robust", "seamless", "game-changer", "synergy"]:
            self.assertIn("banned-phrase", fails("We will %s this." % word), word)

    def test_inflections_are_caught(self):
        self.assertIn("banned-phrase", fails("We are leveraging the data."))

    def test_cliches_fail(self):
        self.assertIn("cliche", fails("Let's circle back next week."))
        self.assertIn("cliche", fails("That said, the numbers hold."))

    def test_plain_that_said_is_not_flagged(self):
        self.assertNotIn("cliche", fails("The email that said yes arrived."))

    def test_hedges_warn_not_fail(self):
        f = lint.lint_draft("I think the lane is ready.", "doc")
        self.assertIn("hedge", rules(f, "warn"))
        self.assertNotIn("hedge", rules(f, "fail"))

    def test_word_inside_another_word_is_not_flagged(self):
        self.assertEqual(fails("The journeyman electrician arrived."), set())

    def test_list_file_is_well_formed(self):
        loaded = lint.load_banned()
        self.assertGreater(len(loaded), 20)
        self.assertTrue(all(sev in ("fail", "warn") for sev, _, _, _ in loaded))


class VoiceProfile(unittest.TestCase):
    def setUp(self):
        self.profile = lint.load_profile(PROFILE)

    def test_profile_sections_parse(self):
        self.assertIn("roadmap", self.profile["keep"])
        self.assertIn("per my last email", self.profile["banned"])
        self.assertEqual(self.profile["caps"]["slack"]["chars"], 500)
        self.assertEqual(self.profile["caps"]["email"]["words"], 100)

    def test_keep_words_override_the_shared_list(self):
        text = "Navigate to Loads and open the Q3 roadmap."
        self.assertIn("cliche", warns(text))
        self.assertNotIn("cliche", warns(text, profile=self.profile))
        self.assertNotIn("banned-phrase", warns(text, profile=self.profile))

    def test_profile_bans_its_own_phrases(self):
        self.assertIn("profile-banned", fails("Per my last email, the rate is $1,140.", profile=self.profile))

    def test_profile_caps_tighten_the_channel(self):
        text = "x" * 550
        self.assertNotIn("length", fails(text, "slack"))
        self.assertIn("length", fails(text, "slack", self.profile))


class ShapeRules(unittest.TestCase):
    def test_soggy_middle(self):
        par = "One. Two is here. Three is here. Four is here."
        self.assertIn("soggy-middle", fails(par, "email"))

    def test_three_sentences_is_fine(self):
        self.assertNotIn("soggy-middle", fails("One. Two is here. Three is here.", "email"))

    def test_a_list_is_structure_not_soggy(self):
        text = "Three updates.\n- One is done.\n- Two is done.\n- Three is late.\n- Four is next."
        self.assertNotIn("soggy-middle", fails(text, "slack"))

    def test_soggy_middle_is_only_a_warning_in_docs(self):
        par = "One. Two is here. Three is here. Four is here."
        self.assertIn("soggy-middle", warns(par, "doc"))

    def test_recap_closer(self):
        text = "The rate held at $1,140.\n\nIn summary, the pilot works."
        self.assertIn("recap-closer", fails(text, "email"))

    def test_recap_closer_ignores_sign_off(self):
        text = "The rate held at $1,140. Can you approve by Thursday?\n\nBest,\nRae"
        self.assertNotIn("recap-closer", fails(text, "email"))

    def test_apology_opener_skips_subject_and_greeting(self):
        text = "Subject: Rates\n\nHi Sam,\n\nSorry to bother you, but the rate changed."
        self.assertIn("apology-opener", warns(text, "email"))

    def test_placeholders(self):
        for text in ["Hi [Name], thanks.", "Dear {{first_name}},", "Revenue grew XX%.", "Call me at ___."]:
            self.assertIn("placeholder", fails(text, "email"), text)

    def test_placeholders_inside_code_are_exempt(self):
        self.assertNotIn("placeholder", fails("Run:\n\n```\nlint.py <draft> [--profile x]\n```\n\nThen `cat <file>`.", "doc"))

    def test_links_and_checkboxes_are_not_placeholders(self):
        self.assertNotIn("placeholder", fails("See [the doc](https://example.com/doc).\n- [x] done", "doc"))


class ChannelRules(unittest.TestCase):
    def test_markdown_fails_in_text(self):
        self.assertIn("markdown-in-plain-text", fails("**Heads up:** running late", "whatsapp"))

    def test_markdown_only_warns_in_email(self):
        self.assertIn("markdown-in-plain-text", warns("**Heads up:** running late", "email"))

    def test_double_asterisk_warns_in_slack(self):
        self.assertIn("markdown-in-plain-text", warns("**Heads up:** running late", "slack"))

    def test_markdown_is_fine_in_docs(self):
        self.assertEqual(fails("# Plan\n\n**Bold** is fine here.", "doc"), set())

    def test_table_fails_in_slack_and_text(self):
        table = "| Lane | Rate |\n|---|---|\n| Memphis | 96% |"
        self.assertIn("table-in-chat", fails(table, "slack"))
        self.assertIn("table-in-chat", fails(table, "sms"))
        self.assertNotIn("table-in-chat", fails(table, "doc"))

    def test_bullets_fail_on_linkedin(self):
        self.assertIn("list-in-plain-text", fails("Three things:\n- one\n- two", "linkedin"))

    def test_bubble_cap(self):
        self.assertIn("length", fails("word " * 40, "text"))
        self.assertNotIn("length", fails("word " * 20 + "\n\n" + "word " * 20, "text"))

    def test_slack_char_and_line_caps(self):
        self.assertIn("length", fails("x" * 601, "slack"))
        self.assertIn("length", fails("\n".join(["line"] * 9), "slack"))

    def test_email_word_cap_ignores_subject(self):
        body = " ".join(["word"] * 120)
        self.assertNotIn("length", fails("Subject: a b c d e\n\n" + body, "email"))
        self.assertIn("length", fails(body + " extra", "email"))

    def test_hashtag_wall_warns(self):
        self.assertIn("hashtag-wall", warns("Done. #a #b #c #d", "linkedin"))

    def test_unknown_channel_raises(self):
        with self.assertRaises(ValueError):
            lint.lint_draft("hi", "fax")


class ContractRules(unittest.TestCase):
    S2 = (
        "[S2 \u00b7 channel: email \u00b7 reader: a recruiter \u00b7 fork axis: urgency vs relationship]\n\n"
        "Draft A [optimize: urgency | sacrifice: room to recover]\nCan we meet before Wednesday?\n\n"
        "Draft B [optimize: relationship | sacrifice: speed]\nAnything I can do to help the timing?\n\n"
        "| Draft | Optimizes | Sacrifices | Best when |\n|---|---|---|---|\n"
        "| A | urgency | room | the offer is dated |\n| B | relationship | speed | the offer is early |\n\n"
        "Recommendation: A. The other offer has a date.\n\n"
        "Decision tree:\n- If they book it -> confirm\n- If no reply in 2 days -> call\n"
    )

    def check(self, text):
        findings, tier, channel = lint.lint_contract(text)
        return rules(findings, "fail"), tier, channel

    def test_valid_s2_passes(self):
        got, tier, channel = self.check(self.S2)
        self.assertEqual(got, set())
        self.assertEqual((tier, channel), ("S2", "email"))

    def test_missing_header(self):
        self.assertIn("contract-header", self.check("Draft A [optimize: x | sacrifice: y]\nhi")[0])

    def test_header_needs_channel(self):
        self.assertIn("contract-header", self.check("[S2 \u00b7 reader: x]\n")[0])

    def test_tone_fork_is_fake(self):
        text = self.S2.replace("optimize: urgency", "optimize: warmer")
        self.assertIn("fake-fork", self.check(text)[0])

    def test_same_objective_twice(self):
        text = self.S2.replace("optimize: relationship", "optimize: urgency")
        self.assertIn("same-objective", self.check(text)[0])

    def test_merge_language_fails(self):
        text = self.S2.replace("Recommendation: A. The other offer has a date.",
                               "Recommendation: A, then combine the strengths of B.")
        self.assertIn("merge", self.check(text)[0])

    def test_selection_must_name_one_draft(self):
        text = self.S2.replace("Recommendation: A.", "Recommendation: A or B.")
        self.assertIn("no-selection", self.check(text)[0])

    def test_matrix_rows_must_match_drafts(self):
        text = self.S2.replace("| B | relationship | speed | the offer is early |\n", "")
        self.assertIn("missing-matrix", self.check(text)[0])

    def test_s1_with_alternatives_fails(self):
        text = "[S1 \u00b7 channel: text \u00b7 reader: a colleague]\nDraft A [optimize: x | sacrifice: y]\nYes.\n\nDraft B [optimize: y | sacrifice: x]\nYep."
        self.assertIn("fork-on-s1", self.check(text)[0])

    def test_s3_requires_named_adversary_and_premortem(self):
        got = self.check(self.S2.replace("[S2", "[S3"))[0]
        self.assertTrue({"draft-count", "missing-adversary", "missing-premortem", "thin-tree"} <= got)

    def test_s4_needs_read_aloud_and_s5_needs_assumptions(self):
        s3 = read(os.path.join(EXAMPLES, "outputs", "s3-pilot-extension.md"))
        self.assertIn("missing-section", self.check(s3.replace("[S3", "[S4", 1))[0])
        self.assertIn("missing-section", self.check(s3.replace("[S3", "[S5", 1))[0])

    def test_drafts_inside_the_contract_are_linted(self):
        text = self.S2.replace("Can we meet before Wednesday?", "Can we circle back before Wednesday?")
        self.assertIn("cliche", self.check(text)[0])


class ExampleCorpus(unittest.TestCase):
    """Every example in examples/ must get the verdict recorded in examples/expected.json."""

    def test_examples_match_expected(self):
        expected = json.loads(read(os.path.join(EXAMPLES, "expected.json")))
        profile = lint.load_profile(None)
        checked = 0
        for rel, want in expected.items():
            if rel.startswith("_"):
                continue
            text = read(os.path.join(EXAMPLES, rel))
            if want["mode"] == "contract":
                findings = lint.lint_contract(text, profile)[0]
            else:
                channel, body, offset = lint.split_header(text)
                findings = lint.lint_draft(body, channel or "doc", profile, offset=offset)
            got_fail, got_warn = rules(findings, "fail"), rules(findings, "warn")
            if "fails" in want:
                self.assertEqual(len([f for f in findings if f.severity == "fail"]), want["fails"],
                                 "%s: %s" % (rel, [f.show() for f in findings]))
            for r in want.get("must_fire", []):
                self.assertIn(r, got_fail, "%s should FAIL on %s" % (rel, r))
            for r in want.get("must_warn", []):
                self.assertIn(r, got_warn, "%s should WARN on %s" % (rel, r))
            checked += 1
        self.assertEqual(checked, 13)

    def test_every_example_file_is_listed(self):
        expected = json.loads(read(os.path.join(EXAMPLES, "expected.json")))
        on_disk = set()
        for sub in ("drafts/good", "drafts/bad", "outputs"):
            for name in os.listdir(os.path.join(EXAMPLES, sub)):
                on_disk.add("%s/%s" % (sub, name))
        self.assertEqual(on_disk, {k for k in expected if not k.startswith("_")})


class CommandLine(unittest.TestCase):
    def run_cli(self, *args, stdin=None):
        return subprocess.run([sys.executable, os.path.join(ROOT, "gates", "lint.py")] + list(args),
                              input=stdin, capture_output=True, text=True)

    def test_good_draft_exits_zero(self):
        r = self.run_cli(os.path.join(EXAMPLES, "drafts", "good", "01-slack-pilot-update.txt"))
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("0 fail", r.stdout)

    def test_bad_draft_exits_one(self):
        r = self.run_cli(os.path.join(EXAMPLES, "drafts", "bad", "03-whatsapp-markdown.txt"))
        self.assertEqual(r.returncode, 1)

    def test_stdin_and_json(self):
        r = self.run_cli("-", "--channel", "email", "--json", stdin="Let's touch base.")
        self.assertEqual(r.returncode, 1)
        data = json.loads(r.stdout)
        self.assertEqual(data["channel"], "email")
        self.assertIn("cliche", {f["rule"] for f in data["findings"]})

    def test_unknown_channel_is_usage_error(self):
        r = self.run_cli("-", "--channel", "fax", stdin="hi")
        self.assertEqual(r.returncode, 2)

    def test_contract_flag(self):
        r = self.run_cli(os.path.join(EXAMPLES, "outputs", "bad-s2-fake-fork-merge.md"), "--contract")
        self.assertEqual(r.returncode, 1)
        self.assertIn("fake-fork", r.stdout)

    def test_main_in_process(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as fh:
            fh.write("channel: text\n\nSee you at 7.")
            path = fh.name
        try:
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = lint.main([path])
            self.assertEqual(code, 0)
            self.assertIn("(Length (text)", buf.getvalue())
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
