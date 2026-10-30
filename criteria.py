"""Instructions and criteria sent to Clef.

v1 is used with clef-flash on comments.json. v2 (used with clef on comments-v2.json) adds the
edge cases a course forum actually produces, plus what the v1 review showed: clef-flash
confidently passed polite-sounding personal attacks and prejudice against groups as acceptable.
"""

CONTEXT = (
    "`comment` is a post on the discussion forum of an online college course on applied / "
    "generative AI. `thread` is the forum thread it was posted in (context only). Students use "
    "the forum to ask doubts, share their work, discuss grading and chat. Decide whether a "
    "moderator should leave `comment` up (acceptable), remove it as abuse (toxic), or remove "
    "it as promotion/junk (spam). Judge the comment's purpose and target, not individual words."
)

CRITERIA = {
    "v1": {
        "instructions": CONTEXT,
        "criteria": {
            "acceptable": "A normal course-forum post: questions, answers, sharing work, feedback, "
                          "discussion, or friendly off-topic chat. Includes disagreement and "
                          "criticism of the course or tools that stays civil.",
            "toxic": "Insults, harassment, mockery, threats or demeaning remarks aimed at a person "
                     "or group (a classmate, the instructor, TAs, a community), including slurs and "
                     "hostile profanity.",
            "spam": "Unsolicited promotion or junk: ads, selling services, paid assignment help, "
                    "scams, phishing or suspicious links, contact numbers for business, referral or "
                    "crypto schemes, or repeated irrelevant posting.",
        },
    },
    "v2": {
        "instructions": CONTEXT + (
            " Read the whole comment before deciding. Strong language, frustration or sarcasm "
            "about a tool, an assignment or the course is not toxic by itself; it becomes toxic "
            "when it attacks or belittles people. Mentioning a product, website or one's own "
            "project is not spam by itself; it is spam when the main purpose is to promote, sell "
            "or lure readers away from the course. Toxic comments are often calm and free of swear "
            "words: a comment that claims a group of students (by gender, region, hostel, community "
            "or background) gets marks unfairly or cheats by nature, calls a TA or instructor "
            "clueless, or tells a named classmate they are not fit for the course is toxic even "
            "when it is phrased as an opinion about grading or about a project."
        ),
        "criteria": {
            "acceptable": (
                "The comment contributes to or fits a course forum, even if blunt. Includes: "
                "questions and answers; sharing one's own work or a relevant free resource/link; "
                "honest, even harsh, criticism of the course, grading, instructors' decisions or "
                "AI tools, without personal insults; venting frustration; mild swearing not aimed "
                "at anyone; jokes; reporting or quoting abuse or spam in order to flag it; "
                "discussing toxic content or scams as part of course work; disagreeing with a "
                "classmate politely."
            ),
            "toxic": (
                "The comment attacks, demeans or intimidates people. Includes: insults or name-"
                "calling of a classmate, instructor or TA; mocking someone's intelligence, "
                "background, English, gender, caste, religion, region or appearance; threats; "
                "sexual comments about a person; sustained or pile-on harassment; publicly shaming "
                "or exposing someone's personal information; passive-aggressive or sarcastic put-"
                "downs whose clear intent is to humiliate a specific person."
            ),
            "spam": (
                "The comment's main purpose is promotion, solicitation or junk rather than course "
                "discussion. Includes: ads; selling or offering paid services, including doing "
                "assignments or exams for others; contact numbers, WhatsApp/Telegram groups or "
                "links pushed for business; referral, affiliate, giveaway, crypto or job scams; "
                "phishing or 'free premium account' links; unrelated product plugs; gibberish or "
                "copy-pasted repeated messages. Disguised promotion counts even if it is polite or "
                "framed as a helpful tip."
            ),
        },
    },
}
