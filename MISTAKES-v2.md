# Clef's mistakes: `comments-v2.json` (model `clef`, criteria v2)

## Summary

- I flagged 7 comments where I disagree with Clef.
- Clef's toxic misses (#42, #91) and its false toxic (#7) all had low confidence (0.23–0.28), so a "send low-confidence answers to a TA" rule would have caught them. That is the opposite of v1, where clef-flash was confident on the toxic comments it missed.
- Its spam over-calls (#23, #31, #65) were confident (0.62–0.80).

## Comment 7

- **Clef:** toxic (toxic 0.64, confidence 0.28)
- **Correct:** acceptable
- **Why:** Since the person hasn't called out someone else or attacked someone, it is not toxic. His concern might be genuine - his only fault is his reaction on himself is a bit too harsh. Anyways this is acceptable as its an issue and someone in the thread below helped answer his problem.

## Comment 23

- **Clef:** spam (spam 0.86, confidence 0.62)
- **Correct:** acceptable
- **Why:** This isn't a promotional message. If at all, it is making lives easier for students by getting them claude pro through common pooling and grouping.

## Comment 31 (borderline)

- **Clef:** spam (spam 0.88, confidence 0.68)
- **Correct:** acceptable
- **Why:** This is acceptable to some extent - borderline call because while he's shared something that could solve a common issue, he's also added his own monetary benefit to the agenda.

## Comment 42

- **Clef:** acceptable (acceptable 0.58, confidence 0.24)
- **Correct:** toxic
- **Why:** Toxic because it's a sarcastic attack directed at a person. The criticism isn't shaped positively and the sarcastic tone makes the message very rude.

## Comment 65 (borderline)

- **Clef:** spam (spam 0.93, confidence 0.80)
- **Correct:** acceptable
- **Why:** this is acceptable to some extent because there's a genuine usecase for the people involved in this. Relevant to coursework and will help students with access to more and better resources/models.

## Comment 88 (borderline)

- **Clef:** acceptable (acceptable 0.84, confidence 0.57)
- **Correct:** toxic
- **Why:** Borderline toxic because it attacks course content/slides. Complimenting the quality of the discussion thread is great, but pairing that with unnecessary and unstructured criticism for the course takes it too far. could have raised concern in a better way

## Comment 91 (borderline)

- **Clef:** acceptable (acceptable 0.55, confidence 0.23)
- **Correct:** toxic
- **Why:** Borderline toxic because message seems creepy with regards to the tone and the wink emoji. It also reveals where and when she can be found and encourages others to confront her.
