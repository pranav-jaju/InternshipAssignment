# Notes

## How to run

Needs Python 3.8+ only (standard library, no `pip install`).

```bash
cp cloud-flare.sh cloud-flare.local.sh   # then put your account ID and Workers AI token in it
python3 classify.py                       # comments.json    -> results.html     (clef-flash, criteria v1)
python3 classify.py --v2                  # comments-v2.json -> results-v2.html  (clef, criteria v2)
python3 classify.py --v2 --html-only      # rebuild a page from saved results without calling the API
```

- `criteria.py` holds the `instructions` and `criteria` sent to Clef. v2 adds the edge cases
  (blunt criticism vs. personal attacks, sharing one's own work vs. promotion, quoting abuse to
  report it, disguised promotion).
- Each run also saves Clef's raw answers to `results.json` / `results-v2.json`.
- Requests run 4 at a time and retry with backoff on HTTP 429 / 5xx.
- The HTML pages show each comment with a colour-coded label, Clef's probabilities and
  confidence. You can filter by label, show only low-confidence answers (< 0.5), sort by
  confidence, and search. The "Disagree with Clef?" box under each comment lets a reviewer mark
  their own label and reason (saved in the browser) and export them as Markdown.

## Tools and models

- Cloudflare Workers AI: `clef-flash` for v1, `clef` for v2.
- Claude (Anthropic) wrote `classify.py`, `criteria.py` and the HTML review pages, tested the
  program against a mock API, helped me debug an SSL certificate problem on my Mac, and helped
  draft these notes and the summaries at the top of the MISTAKES files.
- `MISTAKES.md` and `MISTAKES-v2.md` are my own review: I read every comment and Clef's label
  myself and decided each correct label. Claude only pointed out places where my written reasons
  were unclear or inconsistent with each other (e.g. v1 #98 vs v2 #88).

## What I found

- **v1 (`clef-flash`):** its mistakes were mostly toxic comments passed as acceptable: personal
  attacks and prejudice written calmly, without swear words. It was confident on most of them,
  so only reviewing low-confidence answers would have missed them.
- **v2 (`clef`):** the toxic comments it missed had low confidence (0.23–0.28), so a
  confidence threshold would have caught them. It over-called spam on posts where students
  offer something useful but also benefit themselves (shared Pro accounts, referral links, a
  discount code). Those are judgement calls and I marked most of them borderline.
- **Did my v2 criteria help?** I also ran the v2 comments with the v1 criteria
  (`results-v2-oldcriteria.html`). Only two labels changed: #20 (a student quoting an abusive
  post to ask a moderator to remove it) went from toxic to acceptable, and #40 (a post asking
  students to enter their Moodle username and password on an outside site) went from spam to
  acceptable. So the wording matters much less than the model, and a criteria change can fix
  one case while breaking another; every change needs re-checking.

## For 10,000 students

- Auto-publish only high-confidence "acceptable" posts; send everything else, plus a random
  sample of high-confidence posts, to a TA, since Clef can be confidently wrong.
- Never auto-delete: hide flagged posts until a TA confirms.
- Keep a list of every mistake TAs find and re-run it after each criteria change, so a fix in
  one place doesn't quietly break another.

## What I felt about it

Getting the program working was quick with AI; most of my time went into reading the comments
and deciding the hard cases, which is the part that matters. The most interesting part was
seeing that a model can be wrong and confident at the same time, and that the hardest calls
were not insults but posts mixing something useful with self-interest.
