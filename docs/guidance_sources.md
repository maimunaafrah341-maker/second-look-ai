# Official guidance: sources, provenance, and limitations

`POST /analyze` returns a `guidance` section alongside the rule-based `findings`. It lists short summaries of official Indian cyber-safety guidance whose wording is similar to the submitted message, each with a link to the original document.

This file records where that guidance comes from, how it was checked, what the site policies say, and what the feature cannot do.

## What the guidance section is, and is not

- **It is retrieved evidence.** Each entry points to a real document published by a government body.
- **It is not a verdict.** A match means the guidance uses similar words. It says nothing about whether the message is fraudulent.
- **It is not an endorsement.** The publishers have not reviewed or approved this project.
- **Summaries are ours.** Each summary is written by Second Look in its own words. Nothing is quoted, and no graphics are reproduced. Read the linked source for the official wording.
- **English guidance, limited Hindi matching.** The corpus and its summaries are English. Hindi (Devanagari) and romanised-Hindi messages can reach the same English passages through a small term map (see "Hindi and romanised-Hindi matching" below). Telugu, Urdu, and Bengali words are not matched. Hindi matching has not been evaluated on real messages.

## Sources in the corpus

All were retrieved on 2026-10-04. The corpus file is `backend/app/data/guidance.json`.

| Source | Publisher | Published | Passages |
| --- | --- | --- | --- |
| [Advisory on 'Digital Arrest' based cybercrime in India](https://i4c.mha.gov.in/theme/resources/advisories/ADVISORYTAU-ADV-003DigitalArrest06.03.2025.pdf) | Indian Cyber Crime Coordination Centre (I4C), Ministry of Home Affairs | 6 March 2025 | 2, held back for review and not served |
| [Advisory on 'Rise in Fake Captcha Filling Jobs' based cybercrime](https://i4c.mha.gov.in/theme/resources/advisories/ADVISORY%20TAU-ADV-004_Captcha%20Filling%20Fraud_08.04.2025.pdf) | I4C | 8 April 2025 | 2 |
| [Misuse of Matrimonial Platforms for Investment/Crypto Frauds](https://i4c.mha.gov.in/theme/resources/advisories/ADVISORY-Matriminy%20Scam.pdf) | I4C | 31 October 2025 | 2 |
| [Avoid Phishing Attacks](https://www.csk.gov.in/documents/Phishing.pdf) | Indian Computer Emergency Response Team (CERT-In), Ministry of Electronics and Information Technology | Undated | 3 |
| [Indian Cybercrime Coordination Centre home page](https://i4c.mha.gov.in/) | I4C | Not applicable | 1 |

## How each source was verified

- **I4C advisories.** Each PDF was downloaded from i4c.mha.gov.in and its text layer was read. Titles and dates come from the [I4C advisories index](https://i4c.mha.gov.in/advisories.aspx). The advisory number and date were also found inside the captcha-jobs and matrimonial documents.
- **CERT-In phishing leaflet.** The PDF was downloaded from the Cyber Swachhta Kendra site. Both of its pages carry the CERT-In logo, and it is listed under this title on CERT-In's [security best practices page](https://www.csk.gov.in/security-best-practices.html). It carries no date.
- **I4C home page.** The helpline text was read in the page source.
- **Restriction markings.** No "restricted" marking was found in the text of any included document, or in the page backgrounds of the phishing leaflet. A marking that exists only inside an image in an I4C advisory would not have been detected.

### Known verification gaps

- **Digital-arrest advisory is held back.** Some characters in its text layer did not decode, so its two passages are marked `needs_review` and are not served. To release them, read each summary beside the original document, then change `verification_status` to `verified` in the corpus file. Two details are already left out because they were garbled: the courier company names, and the helpline number printed in that document.
- **Section names, not page numbers.** Locators are section headings. Page numbers were not recorded.
- **Manual review still worthwhile.** The summaries were checked against extracted text, not against the documents as displayed. A person should read each summary beside the original.

## Site policies and licensing

No source is published under an open licence. The corpus therefore stores only metadata, original summaries, and links.

| Site | What its policy says | How this project responds |
| --- | --- | --- |
| i4c.mha.gov.in | [Website policies](https://i4c.mha.gov.in/websitepolicies.aspx): linking needs no prior permission; reproducing material needs permission by email | Linked. Nothing reproduced. |
| www.csk.gov.in | No copyright or linking policy was found; only an "as is" disclaimer | Linked. Nothing reproduced. This is an open question, not a confirmed permission. |

This is a good-faith reading of the policies, not legal advice.

## Sources considered and excluded

| Source | Reason |
| --- | --- |
| National Cyber Crime Reporting Portal (Ministry of Home Affairs) | Its policy requires prior permission to link to the site. It is named in words in one summary, with no URL. |
| Sanchar Saathi / Chakshu (Department of Telecommunications) | Its policy requires prior permission to reproduce content and to link. |
| Reserve Bank of India, BE(A)WARE booklet | Its disclaimer requires permission to link to internal pages, and the booklet's contents could not be verified. |
| I4C advisory on fake electricity-bill SMS (May 2022) | The document carries a "restricted" marking. |
| I4C advisory on fake customer-care numbers (March 2022) | The document carries a "restricted" marking. |
| CERT-In "Digital Payment for Customers" brochure | Image-only PDF; contents could not be read. |
| I4C advisory on fake job rackets (June 2024) | Image-only PDF; contents could not be read. |
| NPCI UPI safety material | Official pages could not be read; seen only through third-party sites. |
| CERT-In advisory on banking phishing | Found only in news coverage; the official advisory was not located. |

## How retrieval works

- **Method.** TF-IDF with cosine similarity, written in plain Python in `backend/app/guidance.py`. It adds no dependencies and makes no network requests.
- **What is indexed.** Each passage's topic, summary, and match terms. Match terms are chosen by this project to help matching. They are not statements from the source and are never shown as such.
- **Match groups.** Each passage has two groups of match terms, for example "what is being asked for" (link, OTP, PIN, card details) and "the pressure or lure used" (urgent, blocked, KYC, prize). A message must contain a term from every group. A link and a password on their own are not enough.
- **Safety advice is ignored.** Text from "never", "do not", "don't", "beware", "be careful", or "avoid" to the end of that sentence is left out before matching. A bank's "Never share your OTP" line is advice, not a request. Other sentences in the same message are still matched.
- **When a passage matches.** All three must hold: a term from every match group, at least two distinct shared terms, and similarity of at least 0.15. A web address in the message counts as the word "link".
- **What is returned.** At most three passages, each with its source title, publisher, URL, publication date, retrieval date, section, and the terms that matched. The similarity value is not returned, so it cannot be mistaken for a fraud probability.
- **When nothing matches.** The response has an empty list and a notice saying the collection is small and that no match does not mean the message is safe.
- **Validation.** The corpus is checked when the service starts: unique identifiers, valid dates, `https` links on an allowlist of two hosts, no links inside summaries, and every passage tied to a known source. An invalid corpus stops the service from starting. Passages marked `needs_review` are never served.
- **Independence.** Retrieval does not use the warning-sign rules, the classifier, or any language-model provider.

Memory on the development machine (Windows, Python 3.11): the running API used a 47 MB working set at startup and 49 MB after 200 requests. Loading scikit-learn's vectorizer instead would have raised it to about 126 MB, which is why retrieval is written in plain Python.

## Retrieval check on a hand-written set

`backend/evaluation/retrieval_eval.json` holds 70 messages written by this project. Run the check with:

```powershell
python backend/evaluation/evaluate_retrieval.py
```

**Read these numbers narrowly.** The set is small, written by the same person who wrote the matching rules, and not drawn from real messages. The numbers describe behaviour on these examples. They are not an estimate of how retrieval performs in general.

The set has two parts:

- **Development (40 messages).** Used while adjusting the matching rules, so a clean score here is expected and proves little.
- **Check (30 messages).** Written after the rules were frozen, and run once. Nothing was adjusted afterwards.

Each part contains malicious messages, benign security-awareness messages, unrelated messages, and ambiguous ones. Ambiguous messages are listed in the output but left out of the counts.

How a message is counted:

- **Correct match:** guidance was expected, and the first result is from an expected source.
- **Missed:** guidance was expected, and the first result is absent or from another source.
- **False match:** the first result is from a source that was not expected, including any result where nothing was expected.
- **Correct silence:** nothing was expected and nothing was returned.

| Part | Scored | Correct matches | False matches | Missed | Correct silences | Precision | Recall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Development | 35 | 12 | 1 | 0 | 22 | 0.923 | 1.000 |
| Check | 27 | 7 | 3 | 4 | 13 | 0.700 | 0.636 |

Effect of each rule on the check part:

| Rules applied | Correct matches | False matches | Missed |
| --- | --- | --- | --- |
| Similarity and two shared terms only | 9 | 12 | 2 |
| Plus match groups | 7 | 5 | 4 |
| Plus safety-advice filter (current) | 7 | 3 | 4 |

The match groups remove most false matches and cost two correct matches.

What went wrong on the check part:

- **False matches (3).** An awareness tip that describes a phishing message without using a warning word; a message about winning a marathon prize with a link; and a to-do note containing "task" and "charge".
- **Missed (4).** A job scam that says "joining amount" instead of "fee"; a matrimonial scam that says "Bitcoin" instead of "crypto"; a KYC message whose link has no `http` or `www`; and a fraud victim who asks "whom should I inform" instead of "report".

Every miss is a wording gap. That is the expected weakness of keyword matching.

A test (`backend/tests/test_retrieval_eval.py`) fails if any of these counts changes, so a change to the corpus or rules has to be looked at and recorded.

## Hindi and romanised-Hindi matching

`backend/app/data/term_map.json` lists Hindi (Devanagari) and romanised-Hindi words and short phrases, each pointing to a term the English corpus already uses, for example ओटीपी → `otp`, खाता or khata → `account`, शुल्क or shulk → `fee`, "bata diya" → `shared`.

- **Not a translation.** The map only adds existing corpus terms to the query. The user's message is never changed, and no translated text is produced or shown.
- **Same safeguards.** Mapped terms go through the same match groups, two-term minimum, and similarity threshold as English words. One mapped word on its own matches nothing.
- **Checked when loaded.** Every concept must already be a retrieval term in the corpus, and a romanised entry may not be an English corpus word, so English messages are unaffected. An invalid map stops the service from starting, like an invalid corpus.
- **Hindi safety advice is ignored.** Hindi puts the negation after the object ("OTP किसी को न बताएं", "OTP share mat karo"), so any sentence containing न, ना, नहीं, मत, nahi, nahin, or nhi, or "na", "naa", or "mat" next to other romanised-Hindi words, is left out of matching. A missed match is preferred to a phishing warning on a bank's own advice.
- **English unchanged.** Run over all 5,574 UCI English messages and the 70 retrieval-set messages, the term map changed the result for one message only: the Hindi item `dev-19`.

### Effect on the development set

`dev-19` ("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।") was labelled "expect nothing" when retrieval was English-only. It now retrieves the phishing guidance, which is the intended behaviour, but against its original label it counts as a false match. The label and the evaluation file are left unchanged, so the development counts above moved from 0 to 1 false match. The frozen check part is unchanged.

## Rules and retrieval can disagree

The rule-based `findings` and the retrieved `guidance` are produced independently. Any combination can occur:

| Findings | Guidance | Example |
| --- | --- | --- |
| Present | None | An electricity-disconnection threat: urgency is detected, and no verified guidance exists. |
| None | Present | A matrimonial investment pitch: no rule covers it, and guidance is found. |
| None | None | A digital-arrest message today: no rule covers it, and its guidance is held back. |

The third row is a scam pattern that returns nothing at all. For that reason:

- **The response never states that a message is safe.** It has no verdict, score, or probability field, and tests check this.
- **Both notices are always present.** One says a message with no indicators may still be a scam. The other says that no matching guidance does not mean the message is safe.
- **Any interface built on this API must show both notices.** It must not use a green tick, the word "safe", or an "all clear" for empty results.

## Limitations

- **Tiny corpus.** Ten passages from five sources, of which eight passages are served.
- **Coverage gaps.** There is no verified guidance yet on OTP or KYC-update messages specifically, UPI or QR-code scams, electricity-bill or parcel-delivery SMS, remote-access apps, loan apps, or lottery scams beyond one line in the phishing leaflet. Messages of those kinds usually return no guidance.
- **Keyword matching only.** It matches words, not meaning. A scam described in unusual wording will be missed.
- **Hindi matching is narrow.** Only words in the term map are matched, a Hindi sentence containing a negation word is ignored, and nothing has been measured on real Hindi messages.
- **False matches and misses happen.** See the check results above.
- **The advice filter can be exploited.** A scam sentence that contains "never" or "do not" is ignored for matching. The result is no guidance, with the notice that this does not mean the message is safe.
- **No real-world evaluation.** The only measurement is the small hand-written set above.
- **Sources go out of date.** Links and advice can change. The retrieval date is shown with every result, and nothing checks the links automatically.
- **Languages.** See "What the guidance section is, and is not" above.

## Adding or changing a source

1. Confirm the site's policy allows linking, and that the document has no restriction marking.
2. Read the document itself, not a news report about it.
3. Write the summary in your own words. Leave out anything you could not read clearly.
4. Add the source and passage to `backend/app/data/guidance.json` with the retrieval date, section, match groups, licence note, and verification note. Use `needs_review` until a person has checked the summary against the original.
5. If the host is new, add it to `ALLOWED_HOSTS` in `backend/app/guidance.py`.
6. Run `python -m pytest` and `python backend/evaluation/evaluate_retrieval.py` from the repository root. If the evaluation counts change, update the recorded counts in the test and in this file.
