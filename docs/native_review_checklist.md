# Native-speaker review checklist: Telugu, Urdu and Bengali

**Status: deferred.** Telugu, Urdu and Bengali are not part of the current Second Look release. The app does not run the checks described here, and it tells users that text in these languages is not analysed. The checks are kept, switched off, for a future release, and this review is what that release needs first.

Second Look checks suspicious messages for warning signs. Its Telugu, Urdu and Bengali checks were written by someone who is not a native speaker of these languages, and nobody fluent has checked them yet.

This checklist is for a fluent reader of one of the three languages. You do not need to read code. Each language takes about 45 to 60 minutes.

## What to do

For your language, go through its four parts in order and mark every row:

- **OK**: natural, correctly spelled, and means what the English column says.
- **Fix**: write the corrected wording next to it.
- **Remove**: wrong, misleading, or something no one would write.

Then answer the questions at the end of the section, and add any common scam wording that is missing. Real messages you have received are the most useful examples; remove names, phone numbers and account details first.

Please judge the wording as it appears in real SMS and WhatsApp messages in India, including English words written in your script (OTP, KYC, link) and informal spelling.

## How the checks work, in brief

- **Warning signs** are found by looking for fixed words and short phrases (Part 1). There is no translation and no AI model for these languages.
- **Official guidance** is in English. A small word list (Part 2) connects words in your language to English topic words, only to pick which English guidance to show. Users never see this list.
- **Test messages** (Parts 3 and 4) were written to check the rules. They are invented, not real messages.

## Telugu

### Telugu Part 1: words and phrases the rules look for

| Meaning | Words and phrases | How it is used | OK / Fix / Remove |
| --- | --- | --- | --- |
| Final warning | చివరి హెచ్చరిక, తుది హెచ్చరిక | Flagged as urgency wherever it appears. | |
| Immediately / today itself / right now | వెంటనే, తక్షణమే, తక్షణం, ఈరోజే, ఇప్పుడే | Flagged as urgency only when an action follows in the same sentence: కాల్, క్లిక్, అప్‌డేట్, పేమెంట్, or any polite request ending in -ండి (చేయండి, పంపండి, చెప్పండి…). Not flagged in "వెంటనే వస్తాను". "రండి" (come) is deliberately not counted as an action. | |
| Something will be, or has been, blocked or cut off | ఖాతా, అకౌంట్, కార్డ్, కార్డు, సిమ్, కనెక్షన్, సేవ, నంబర్, కేవైసీ, కరెంట్, విద్యుత్ (also SIM, KYC, ATM, UPI, account, card in English letters), followed by బ్లాక్, నిలిపివేయ, రద్దు, సస్పెండ్, డీయాక్టివేట్, కట్, మూసివేయ + అవుతుంది, అవుతాయి, అయింది, అయ్యింది, చేయబడుతుంది, చేయబడింది, చేయబడతాయి, బడుతుంది, బడింది, చేస్తాము, చేస్తాం | Flagged as urgency. Example: "మీ ఖాతా బ్లాక్ అవుతుంది", "కనెక్షన్ నిలిపివేయబడుతుంది". | |
| The secret being asked for | ఓటీపీ, ఓటిపి, పిన్, పాస్‌వర్డ్, సీవీవీ, కార్డ్ వివరాలు, కార్డు వివరాలు, బ్యాంక్ వివరాలు (also OTP, PIN, password, CVV in English letters); endings -ని, -ను, -లను are accepted | "పిన్ కోడ్" (postal code) is deliberately not counted. | |
| Request to tell, send, give, share or enter it | చెప్పండి, చెప్పు, చెప్పేయండి; పంపండి, పంపించండి, పంపు, పంపించు; ఇవ్వండి, ఇవ్వు, ఇచ్చేయండి; షేర్ / నమోదు / ఎంటర్ + చేయండి, చెయ్యండి, చేయి, చెయ్యి | A secret followed by one of these in the same sentence is flagged as a credential request. | |
| Words that turn it into safety advice (not flagged) | ఎవరికీ, ఎవరితోనూ, వద్దు, కూడదు, ఎప్పుడూ; and the "don't" verb forms చెప్పకండి, పంపకండి, షేర్ చేయకండి, పంపవద్దు, చెప్పవద్దు | Example not flagged: "మీ OTP ఎవరికీ చెప్పకండి". | |
| Named fees | రిజిస్ట్రేషన్, ప్రాసెసింగ్, డెలివరీ, కస్టమ్స్, వెరిఫికేషన్, యాక్టివేషన్ + ఫీజు, రుసుము, ఛార్జీ, ఛార్జ్ | Flagged as a payment demand wherever it appears. | |
| Pay a fee / send money | ఫీజు, రుసుము, ఛార్జీ, ఛార్జ్, ఛార్జీలు + చెల్లించండి, చెల్లించు, కట్టండి, కట్టు, డిపాజిట్ / జమ / పే చేయండి; డబ్బు, డబ్బులు, రూపాయలు, మొత్తం, or an amount (₹500, రూ.500) + పంపండి, పంపించండి, చెల్లించండి, కట్టండి, డిపాజిట్ / జమ / ట్రాన్స్‌ఫర్ / పే చేయండి; on their own: చెల్లించండి, చెల్లింపు చేయండి, పేమెంట్ చేయండి, డిపాజిట్ చేయండి | Flagged as a payment demand. Past tense ("చెల్లించాను") and "చెల్లుతుంది" (is valid) are not flagged. | |

### Telugu Part 2: words that point to English guidance topics

Check that each word really means the English topic word, and is spelled the way people write it.

| English topic word | Words in Telugu | OK / Fix / Remove |
| --- | --- | --- |
| otp | ఓటీపీ, ఓటిపి, ఓటీపీని | |
| pin | పిన్ | |
| password | పాస్వర్డ్ | |
| cvv | సీవీవీ | |
| card | కార్డ్, కార్డు | |
| detail | వివరాలు | |
| link | లింక్ | |
| click | క్లిక్ | |
| account | ఖాతా, ఖాతాకు, ఖాతాను, అకౌంట్ | |
| blocked | బ్లాక్, నిలిపివేయబడుతుంది, నిలిపివేయబడింది, రద్దు | |
| urgent | వెంటనే, తక్షణమే, తక్షణం | |
| kyc | కేవైసీ | |
| prize | బహుమతి | |
| lottery | లాటరీ, లాటరీలో | |
| fee | ఫీజు, రుసుము | |
| registration | రిజిస్ట్రేషన్ | |
| deposit | డిపాజిట్ | |
| job | జాబ్, జాబ్తో, ఉద్యోగం | |
| earn | సంపాదించండి, సంపాదన | |
| task | టాస్క్, టాస్క్లు | |
| captcha | క్యాప్చా | |
| payment | చెల్లింపు, పేమెంట్ | |
| money | డబ్బు, డబ్బులు | |
| fraud | మోసం, మోసంలో | |
| cheated | మోసపోయాను, మోసపోయారు, మోసపోయాము | |
| complaint | ఫిర్యాదు | |
| helpline | హెల్ప్లైన్, హెల్ప్లైన్కు | |
| shared | చెప్పాను, చెప్పేశాను, షేర్ చేశాను, పంపాను | |
| gave | ఇచ్చాను, ఇచ్చేశాను | |
| clicked | క్లిక్ చేశాను | |
| entered | ఎంటర్ చేశాను, నమోదు చేశాను | |
| reward | రివార్డ్ | |
| withdraw | విత్డ్రా | |
| lost | పోగొట్టుకున్నాను | |

### Telugu Part 3: test messages (development set)

These were used while writing the rules.

For each message, check two things: is the wording natural, and is the "should be flagged as" column right?

| ID | Message | Kind | Should be flagged as | Guidance that should appear | OK / Fix / Remove |
| --- | --- | --- | --- | --- | --- |
| te-dev-01 | మీ బ్యాంక్ ఖాతా ఈరోజు బ్లాక్ అవుతుంది. వెంటనే మీ OTP చెప్పండి. | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| te-dev-02 | చివరి హెచ్చరిక: మీ KYC పెండింగ్‌లో ఉంది. ఈ లింక్ క్లిక్ చేయండి http://bit.ly/kyc-te | Scam message | Urgency or threat; Contains a link | Phishing advice (CERT-In) | |
| te-dev-03 | అభినందనలు! మీరు లాటరీలో బహుమతి గెలుచుకున్నారు. బహుమతి పొందడానికి వెంటనే మీ కార్డ్ వివరాలు పంపండి. | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| te-dev-04 | ఇంటి నుండి క్యాప్చా జాబ్ చేసి రోజుకు రూ.2000 సంపాదించండి. ముందుగా రిజిస్ట్రేషన్ ఫీజు రూ.499 చెల్లించండి. | Scam message | Asks for money or a fee | Fake CAPTCHA-job advice (I4C) | |
| te-dev-05 | మీ కరెంట్ కనెక్షన్ ఈ రాత్రి 9:30కి నిలిపివేయబడుతుంది. వెంటనే ఈ నంబర్‌కు కాల్ చేయండి 98xxxxxx10 | Scam message | Urgency or threat | None | |
| te-dev-06 | మీ పార్సెల్ కస్టమ్స్‌లో ఆగిపోయింది. విడుదల కోసం రూ.300 కస్టమ్స్ ఫీజు చెల్లించండి: http://bit.ly/parcel-te | Scam message | Contains a link; Asks for money or a fee | None | |
| te-dev-07 | నేను పొరపాటున OTP చెప్పాను, ఇప్పుడు ఏం చేయాలి? | Someone asking for help | Nothing | Phishing advice (CERT-In) | |
| te-dev-08 | ఆన్‌లైన్ మోసంలో డబ్బు పోగొట్టుకున్నాను, ఫిర్యాదు ఎక్కడ చేయాలి? | Someone asking for help | Nothing | Reporting helpline 1930 (I4C) | |
| te-dev-09 | బ్యాంక్ ఎప్పుడూ OTP అడగదు. మీ OTP ఎవరికీ చెప్పకండి. | Genuine safety advice | Nothing | None | |
| te-dev-10 | మీ OTP 482913. ఇది 10 నిమిషాలు చెల్లుతుంది. దీన్ని ఎవరితోనూ షేర్ చేయకండి. - SBI | Genuine safety advice | Nothing | None | |
| te-dev-11 | నేను ఇప్పుడు ఇంట్లో ఉన్నాను, సాయంత్రం కలుద్దాం. | Ordinary message | Nothing | None | |
| te-dev-12 | షాపు ఈరోజు మూసి ఉంటుంది, రేపు రండి. | Ordinary message | Nothing | None | |

### Telugu Part 4: test messages (check set)

These were written before the rules and kept aside to test them. Please review them just as carefully.

For each message, check two things: is the wording natural, and is the "should be flagged as" column right?

| ID | Message | Kind | Should be flagged as | Guidance that should appear | OK / Fix / Remove |
| --- | --- | --- | --- | --- | --- |
| te-chk-01 | ప్రియమైన కస్టమర్, మీ ATM కార్డ్ బ్లాక్ చేయబడింది. దాన్ని తిరిగి ప్రారంభించడానికి మీ ATM పిన్ పంపండి. | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| te-chk-02 | మీ SIM 24 గంటల్లో రద్దు అవుతుంది. ఆపడానికి తక్షణమే ఈ లింక్‌లో వివరాలు నమోదు చేయండి www.sim-update.in | Scam message | Urgency or threat; Contains a link | Phishing advice (CERT-In) | |
| te-chk-03 | పార్ట్ టైమ్ ఉద్యోగం: సింపుల్ టాస్క్‌లు చేసి రోజూ సంపాదించండి. డబ్బు విత్‌డ్రా చేయడానికి ముందు రూ.999 డిపాజిట్ చేయండి. | Scam message | Asks for money or a fee | Fake CAPTCHA-job advice (I4C) | |
| te-chk-04 | మీ ఖాతాకు రూ.5000 రివార్డ్ వచ్చింది. పొందడానికి మీ UPI పిన్ నమోదు చేయండి. | Scam message | Asks for an OTP, PIN, password or card details | None | |
| te-chk-05 | మీ కరెంట్ బిల్లు బకాయి ఉంది. ఈరోజే చెల్లించకపోతే కనెక్షన్ కట్ అవుతుంది. | Scam message | Urgency or threat; Asks for money or a fee | None | |
| te-chk-06 | నేను ఒక లింక్ క్లిక్ చేసి నా పాస్‌వర్డ్ ఎంటర్ చేశాను. ఇప్పుడు ఏం చేయాలి? | Someone asking for help | Nothing | Phishing advice (CERT-In) | |
| te-chk-07 | నా నాన్నగారు నకిలీ కస్టమర్ కేర్ కాల్ వల్ల మోసపోయారు. ఏ హెల్ప్‌లైన్‌కు ఫిర్యాదు చేయాలి? | Someone asking for help | Nothing | Reporting helpline 1930 (I4C) | |
| te-chk-08 | ఎవరైనా ఫోన్ చేసి OTP అడిగితే చెప్పవద్దు. బ్యాంక్ ఎప్పుడూ పిన్ అడగదు. | Genuine safety advice | Nothing | None | |
| te-chk-09 | అమ్మా, నేను బస్సులో ఉన్నాను. వెంటనే వస్తాను. | Ordinary message | Nothing | None | |
| te-chk-10 | నా కార్డ్ ఇంట్లో మర్చిపోయాను, రేపు కలుద్దాం. | Ordinary message | Nothing | None | |

### Telugu: questions for the reviewer

1. Is ఓటీపీ the spelling people actually use, or is ఓటిపి / OTP in English letters more common in real messages?
2. Is "any polite request ending in -ండి after వెంటనే" too broad? Give an everyday sentence it would wrongly flag.
3. Are కరెంట్ and విద్యుత్ both natural for an electricity cut-off threat? Which other subjects are common (గ్యాస్, లోన్, ఇన్సూరెన్స్…)?
4. Scam messages often say "if you don't pay…" (చెల్లించకపోతే). The rules do not catch this form. What are the common ways to write it?
5. Which very common scam phrases are missing altogether?

### Telugu: sign-off

- Reviewer name:
- Date:
- Where you learned and use the language (state or region):
- Parts reviewed (1, 2, 3, 4):
- Overall: **Ready to describe as reviewed** / **Needs the fixes above first** / **Not usable**

## Urdu

### Urdu Part 1: words and phrases the rules look for

| Meaning | Words and phrases | How it is used | OK / Fix / Remove |
| --- | --- | --- | --- |
| Final warning | آخری وارننگ، آخری انتباہ، آخری موقع، آخری نوٹس | Flagged as urgency wherever it appears. | |
| Immediately / right now / today itself | فوراً، فورا، فوری طور پر، ابھی، آج ہی | Flagged as urgency only when an action follows in the same sentence: کال، کلک، اپڈیٹ، اپ ڈیٹ، ادائیگی, or a request verb from the lists below (کریں، بھیجیں، بتائیں…). Not flagged in "فوراً آتا ہوں". | |
| Something will be, or has been, blocked or cut off | اکاؤنٹ، کھاتہ، کھاتا، کارڈ، سم، کنکشن، سروس، نمبر، بجلی (also SIM, KYC, ATM, UPI, account, card in English letters), followed by بند، بلاک، معطل، منقطع، کاٹ، کٹ + ہو جائے گا، ہو جائے گی، ہو جائیں گے، کر دیا جائے گا، کر دی جائے گی، دیا جائے گا، دی جائے گی، کر دیا گیا، کر دی گئی، ہو گیا، ہو گئی، جائے گا، جائے گی | Flagged as urgency. Example: "آپ کا اکاؤنٹ بند ہو جائے گا". "دکان آج بند ہے" is not flagged. | |
| The secret being asked for | او ٹی پی، پن، پاس ورڈ، سی وی وی، کارڈ کی تفصیلات، بینک کی تفصیلات (also OTP, PIN, password, CVV in English letters) | "پن کوڈ" is deliberately not counted, and "پن" must be a whole word ("پنجاب" is not counted). | |
| Request to tell, send, share, enter or give it | بتائیں، بتائیے، بتاؤ، بتا دیں، بتا دو، بتا دیجیے؛ بھیجیں، بھیجیے، بھیجو، بھیج دیں، بھیج دو؛ شیئر / درج / داخل + کریں، کرو، کیجیے، کیجئے، کر دیں، کر دو؛ دیں | A secret followed by one of these in the same sentence is flagged as a credential request. Bare "دو" is left out because it also means "two". | |
| Words that turn it into safety advice (not flagged) | نہ، مت، نہیں، کبھی (between the secret and the verb); نہیں or مت straight after the verb | Example not flagged: "اپنا او ٹی پی کسی کو نہ بتائیں". | |
| Named fees | رجسٹریشن، پروسیسنگ، پراسیسنگ، ڈلیوری، ڈیلیوری، کسٹمز، کسٹم، تصدیقی، ایکٹیویشن + فیس، چارجز، چارج | Flagged as a payment demand wherever it appears. | |
| Pay a fee / send money | فیس، چارجز، چارج + ادا کریں، ادا کرو، ادا کیجیے، ادا کر دیں، ادائیگی کریں، ادائیگی کرو، جمع کرائیں، جمع کروائیں، جمع کریں، جمع کرو، جمع کرا دیں، بھریں، بھرو، دیں؛ پیسے، پیسہ، رقم، روپے، روپیہ + بھیجیں، بھیجو، بھیج دیں، ادا کریں، جمع کرائیں، ٹرانسفر کریں؛ on their own: ادا کریں، ادائیگی کریں، پیمنٹ کریں | Flagged as a payment demand. "شکریہ ادا کریں" and past tense ("ادا کر دیا ہے") are not flagged. | |

### Urdu Part 2: words that point to English guidance topics

Check that each word really means the English topic word, and is spelled the way people write it.

| English topic word | Words in Urdu | OK / Fix / Remove |
| --- | --- | --- |
| otp | او ٹی پی, اوٹی پی | |
| pin | پن | |
| password | پاس ورڈ | |
| cvv | سی وی وی | |
| card | کارڈ | |
| detail | تفصیلات | |
| link | لنک | |
| click | کلک | |
| account | اکاؤنٹ, کھاتہ, کھاتے | |
| blocked | بلاک, بند, معطل | |
| urgent | فوراً, فورا, فوری | |
| kyc | کے وائی سی | |
| prize | انعام | |
| lottery | لاٹری | |
| fee | فیس | |
| registration | رجسٹریشن | |
| deposit | جمع | |
| job | نوکری, جاب | |
| earn | کمائیں, کمائی, کماؤ | |
| task | ٹاسک | |
| captcha | کیپچا | |
| payment | ادائیگی | |
| money | پیسے, رقم, روپے | |
| fraud | فراڈ, دھوکہ, دھوکا | |
| complaint | شکایت | |
| helpline | ہیلپ لائن | |
| shared | بتا دیا, شیئر کر دیا, بھیج دیا | |
| gave | دے دیا | |
| clicked | کلک کیا, کلک کر دیا | |
| entered | ڈال دیا, درج کر دیا | |

### Urdu Part 3: test messages (development set)

These were used while writing the rules.

For each message, check two things: is the wording natural, and is the "should be flagged as" column right?

| ID | Message | Kind | Should be flagged as | Guidance that should appear | OK / Fix / Remove |
| --- | --- | --- | --- | --- | --- |
| ur-dev-01 | آپ کا بینک اکاؤنٹ آج بند ہو جائے گا۔ فوراً اپنا او ٹی پی بتائیں۔ | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| ur-dev-02 | آخری وارننگ: آپ کا KYC نامکمل ہے۔ اس لنک پر کلک کریں http://bit.ly/kyc-ur | Scam message | Urgency or threat; Contains a link | Phishing advice (CERT-In) | |
| ur-dev-03 | مبارک ہو! آپ نے لاٹری میں انعام جیتا ہے۔ انعام حاصل کرنے کے لیے فوراً اپنے کارڈ کی تفصیلات بھیجیں۔ | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| ur-dev-04 | گھر بیٹھے کیپچا جاب کریں اور روزانہ 2000 روپے کمائیں۔ پہلے 499 روپے رجسٹریشن فیس جمع کرائیں۔ | Scam message | Asks for money or a fee | Fake CAPTCHA-job advice (I4C) | |
| ur-dev-05 | آپ کا بجلی کا کنکشن آج رات ساڑھے نو بجے کاٹ دیا جائے گا۔ فوراً اس نمبر پر کال کریں 98xxxxxx10 | Scam message | Urgency or threat | None | |
| ur-dev-06 | آپ کا پارسل کسٹمز میں روکا گیا ہے۔ چھڑانے کے لیے 300 روپے کسٹمز فیس ادا کریں: http://bit.ly/parcel-ur | Scam message | Contains a link; Asks for money or a fee | None | |
| ur-dev-07 | میں نے غلطی سے او ٹی پی بتا دیا، اب کیا کروں؟ | Someone asking for help | Nothing | Phishing advice (CERT-In) | |
| ur-dev-08 | آن لائن فراڈ میں میرے پیسے چلے گئے، شکایت کہاں کروں؟ | Someone asking for help | Nothing | Reporting helpline 1930 (I4C) | |
| ur-dev-09 | بینک کبھی او ٹی پی نہیں مانگتا۔ اپنا او ٹی پی کسی کو نہ بتائیں۔ | Genuine safety advice | Nothing | None | |
| ur-dev-10 | آپ کا OTP 482913 ہے۔ یہ 10 منٹ کے لیے درست ہے۔ اسے کسی کے ساتھ شیئر نہ کریں۔ - SBI | Genuine safety advice | Nothing | None | |
| ur-dev-11 | میں ابھی گھر پر ہوں، شام کو ملتے ہیں۔ | Ordinary message | Nothing | None | |
| ur-dev-12 | دکان آج بند ہے، کل آئیے گا۔ | Ordinary message | Nothing | None | |

### Urdu Part 4: test messages (check set)

These were written before the rules and kept aside to test them. Please review them just as carefully.

For each message, check two things: is the wording natural, and is the "should be flagged as" column right?

| ID | Message | Kind | Should be flagged as | Guidance that should appear | OK / Fix / Remove |
| --- | --- | --- | --- | --- | --- |
| ur-chk-01 | محترم صارف، آپ کا ATM کارڈ بلاک کر دیا گیا ہے۔ دوبارہ چالو کرنے کے لیے اپنا ATM پن بھیجیں۔ | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| ur-chk-02 | آپ کی SIM چوبیس گھنٹوں میں بند ہو جائے گی۔ روکنے کے لیے فوری طور پر اس لنک پر تفصیلات درج کریں www.sim-update.in | Scam message | Urgency or threat; Contains a link | Phishing advice (CERT-In) | |
| ur-chk-03 | پارٹ ٹائم نوکری: آسان ٹاسک کریں اور روزانہ کمائیں۔ رقم نکالنے سے پہلے 999 روپے جمع کرائیں۔ | Scam message | Asks for money or a fee | Fake CAPTCHA-job advice (I4C) | |
| ur-chk-04 | آپ کے اکاؤنٹ میں 5000 روپے کا انعام آیا ہے۔ حاصل کرنے کے لیے اپنا UPI پن درج کریں۔ | Scam message | Asks for an OTP, PIN, password or card details | None | |
| ur-chk-05 | آپ کا بجلی کا بل باقی ہے۔ آج ہی ادائیگی نہ کی تو کنکشن کٹ جائے گا۔ | Scam message | Urgency or threat; Asks for money or a fee | None | |
| ur-chk-06 | میں نے ایک لنک پر کلک کر کے اپنا پاس ورڈ ڈال دیا۔ اب کیا کروں؟ | Someone asking for help | Nothing | Phishing advice (CERT-In) | |
| ur-chk-07 | میرے والد کے ساتھ جعلی کسٹمر کیئر کال کے ذریعے دھوکہ ہوا۔ شکایت کے لیے کون سی ہیلپ لائن پر کال کریں؟ | Someone asking for help | Nothing | Reporting helpline 1930 (I4C) | |
| ur-chk-08 | اگر کوئی فون کر کے او ٹی پی مانگے تو مت بتائیں۔ بینک کبھی پن نہیں مانگتا۔ | Genuine safety advice | Nothing | None | |
| ur-chk-09 | امی، میں بس میں ہوں۔ فوراً آتا ہوں۔ | Ordinary message | Nothing | None | |
| ur-chk-10 | میرا کارڈ گھر پر رہ گیا، کل ملتے ہیں۔ | Ordinary message | Nothing | None | |

### Urdu: questions for the reviewer

1. People write OTP as او ٹی پی, اوٹی پی or in English letters. Which other spellings are common?
2. The rules accept Arabic-keyboard letters (ك ي ه) in place of ک ی ہ. Are there other common keyboard variants we should accept?
3. Is "دیں" on its own ("اپنا پن دیں") a natural way to ask for a PIN, or does it cause false alarms?
4. Scam messages often say "if you don't pay…" (ادائیگی نہ کی تو). The rules do not catch this form. What are the common ways to write it?
5. These rules are for Urdu as used in India. Is any wording here mainly Pakistani usage that Indian readers would not write?
6. Which very common scam phrases are missing altogether?

### Urdu: sign-off

- Reviewer name:
- Date:
- Where you learned and use the language (state or region):
- Parts reviewed (1, 2, 3, 4):
- Overall: **Ready to describe as reviewed** / **Needs the fixes above first** / **Not usable**

## Bengali

### Bengali Part 1: words and phrases the rules look for

| Meaning | Words and phrases | How it is used | OK / Fix / Remove |
| --- | --- | --- | --- |
| Final warning | শেষ সতর্কতা, শেষ সতর্কবার্তা, শেষ সুযোগ, শেষ নোটিশ, চূড়ান্ত সতর্কতা | Flagged as urgency wherever it appears. | |
| Right now / immediately / today itself / quickly | এখনই, অবিলম্বে, আজই, তাড়াতাড়ি, দ্রুত | Flagged as urgency only when an action follows in the same sentence: কল, ক্লিক, আপডেট, পেমেন্ট, পরিশোধ, or a request verb from the lists below (করুন, পাঠান, বলুন, দিন…). Not flagged in "এখনই আসছি". | |
| Something will be, or has been, blocked or cut off | অ্যাকাউন্ট, খাতা, কার্ড, সিম, সংযোগ, কানেকশন, পরিষেবা, সার্ভিস, নম্বর, বিদ্যুৎ (also SIM, KYC, ATM, UPI, account, card in English letters), followed by বন্ধ, ব্লক, স্থগিত, বিচ্ছিন্ন, সাসপেন্ড, নিষ্ক্রিয়, কেটে + হয়ে যাবে, হবে, করা হবে, করে দেওয়া হবে, দেওয়া হবে, করা হয়েছে, হয়েছে, হয়ে গেছে | Flagged as urgency. Example: "আপনার অ্যাকাউন্ট বন্ধ হয়ে যাবে". "দোকান আজ বন্ধ থাকবে" is not flagged. | |
| The secret being asked for | ওটিপি, ও টি পি, পিন, পাসওয়ার্ড, সিভিভি, কার্ডের / ব্যাংকের / অ্যাকাউন্টের + তথ্য, বিবরণ, নম্বর (also OTP, PIN, password, CVV in English letters); endings -টি, -টা are accepted | "পিন কোড" is deliberately not counted. | |
| Request to tell, send, give, share, enter or write it | বলুন, বলো, বলে দিন, বলে দাও; পাঠান, পাঠাও, পাঠিয়ে দিন, পাঠিয়ে দাও; দিন, দাও, দিয়ে দিন; শেয়ার / এন্টার + করুন, করো, করে দিন; লিখুন | A secret followed by one of these in the same sentence is flagged as a credential request. "দিন" must be a whole word ("প্রতিদিন" is not counted). | |
| Words that turn it into safety advice (not flagged) | না, কখনো, কখনও, কাউকে (between the secret and the verb); and the "don't" forms বলবেন না, পাঠাবেন না, শেয়ার করবেন না | Example not flagged: "আপনার ওটিপি কাউকে বলবেন না". "দিন না" (please give) is still treated as a request. | |
| Named fees | রেজিস্ট্রেশন, প্রসেসিং, প্রক্রিয়াকরণ, ডেলিভারি, কাস্টমস, কাস্টম, ভেরিফিকেশন, অ্যাক্টিভেশন + ফি, চার্জ | Flagged as a payment demand wherever it appears. | |
| Pay a fee / send money | ফি, ফিস, চার্জ + পরিশোধ / পেমেন্ট / পে + করুন, করো, করে দিন; জমা দিন, জমা দাও, জমা করুন; দিন, দাও; টাকা, অর্থ + পাঠান, পাঠাও, পাঠিয়ে দিন, জমা দিন, দিন, ট্রান্সফার করুন; on their own: পরিশোধ করুন, পেমেন্ট করুন | Flagged as a payment demand. Past tense ("পরিশোধ করেছি") is not flagged. | |

### Bengali Part 2: words that point to English guidance topics

Check that each word really means the English topic word, and is spelled the way people write it.

| English topic word | Words in Bengali | OK / Fix / Remove |
| --- | --- | --- |
| otp | ওটিপি | |
| pin | পিন | |
| password | পাসওয়ার্ড | |
| cvv | সিভিভি | |
| card | কার্ড, কার্ডের | |
| detail | তথ্য, বিবরণ | |
| link | লিংক, লিঙ্ক, লিংকে | |
| click | ক্লিক | |
| account | অ্যাকাউন্ট, অ্যাকাউন্টে, অ্যাকাউন্টের | |
| blocked | বন্ধ, ব্লক, স্থগিত | |
| urgent | এখনই, অবিলম্বে | |
| kyc | কেওয়াইসি | |
| prize | পুরস্কার, পুরস্কারের | |
| lottery | লটারি, লটারিতে, লটারির | |
| fee | ফি | |
| registration | রেজিস্ট্রেশন | |
| deposit | জমা | |
| job | জব, চাকরি | |
| earn | আয় | |
| task | টাস্ক | |
| captcha | ক্যাপচা | |
| payment | পরিশোধ, পেমেন্ট | |
| money | টাকা | |
| fraud | প্রতারণা, প্রতারণায় | |
| cheated | প্রতারিত | |
| complaint | অভিযোগ | |
| helpline | হেল্পলাইন, হেল্পলাইনে | |
| shared | বলে দিয়েছি, শেয়ার করেছি, পাঠিয়েছি | |
| gave | দিয়ে দিয়েছি, দিয়েছি | |
| clicked | ক্লিক করেছি | |
| lost | হারিয়েছি | |

### Bengali Part 3: test messages (development set)

These were used while writing the rules.

For each message, check two things: is the wording natural, and is the "should be flagged as" column right?

| ID | Message | Kind | Should be flagged as | Guidance that should appear | OK / Fix / Remove |
| --- | --- | --- | --- | --- | --- |
| bn-dev-01 | আপনার ব্যাংক অ্যাকাউন্ট আজ বন্ধ হয়ে যাবে। এখনই আপনার ওটিপি বলুন। | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| bn-dev-02 | শেষ সতর্কতা: আপনার KYC অসম্পূর্ণ। এই লিংকে ক্লিক করুন http://bit.ly/kyc-bn | Scam message | Urgency or threat; Contains a link | Phishing advice (CERT-In) | |
| bn-dev-03 | অভিনন্দন! আপনি লটারিতে পুরস্কার জিতেছেন। পুরস্কার পেতে এখনই আপনার কার্ডের তথ্য পাঠান। | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| bn-dev-04 | ঘরে বসে ক্যাপচা জব করুন এবং প্রতিদিন ২০০০ টাকা আয় করুন। আগে ৪৯৯ টাকা রেজিস্ট্রেশন ফি জমা দিন। | Scam message | Asks for money or a fee | Fake CAPTCHA-job advice (I4C) | |
| bn-dev-05 | আপনার বিদ্যুৎ সংযোগ আজ রাত সাড়ে নয়টায় বিচ্ছিন্ন করা হবে। এখনই এই নম্বরে কল করুন 98xxxxxx10 | Scam message | Urgency or threat | None | |
| bn-dev-06 | আপনার পার্সেল কাস্টমসে আটকে আছে। ছাড়াতে ৩০০ টাকা কাস্টমস ফি পরিশোধ করুন: http://bit.ly/parcel-bn | Scam message | Contains a link; Asks for money or a fee | None | |
| bn-dev-07 | আমি ভুল করে ওটিপি বলে দিয়েছি, এখন কী করব? | Someone asking for help | Nothing | Phishing advice (CERT-In) | |
| bn-dev-08 | অনলাইন প্রতারণায় টাকা হারিয়েছি, কোথায় অভিযোগ করব? | Someone asking for help | Nothing | Reporting helpline 1930 (I4C) | |
| bn-dev-09 | ব্যাংক কখনো ওটিপি চায় না। আপনার ওটিপি কাউকে বলবেন না। | Genuine safety advice | Nothing | None | |
| bn-dev-10 | আপনার OTP 482913। এটি ১০ মিনিটের জন্য বৈধ। এটি কারো সাথে শেয়ার করবেন না। - SBI | Genuine safety advice | Nothing | None | |
| bn-dev-11 | আমি এখন বাড়িতে আছি, সন্ধ্যায় দেখা হবে। | Ordinary message | Nothing | None | |
| bn-dev-12 | দোকান আজ বন্ধ থাকবে, কাল আসুন। | Ordinary message | Nothing | None | |

### Bengali Part 4: test messages (check set)

These were written before the rules and kept aside to test them. Please review them just as carefully.

For each message, check two things: is the wording natural, and is the "should be flagged as" column right?

| ID | Message | Kind | Should be flagged as | Guidance that should appear | OK / Fix / Remove |
| --- | --- | --- | --- | --- | --- |
| bn-chk-01 | প্রিয় গ্রাহক, আপনার ATM কার্ড ব্লক করা হয়েছে। আবার চালু করতে আপনার ATM পিন পাঠান। | Scam message | Urgency or threat; Asks for an OTP, PIN, password or card details | Phishing advice (CERT-In) | |
| bn-chk-02 | আপনার SIM ২৪ ঘণ্টার মধ্যে বন্ধ হয়ে যাবে। আটকাতে অবিলম্বে এই লিংকে তথ্য দিন www.sim-update.in | Scam message | Urgency or threat; Contains a link | Phishing advice (CERT-In) | |
| bn-chk-03 | পার্ট টাইম চাকরি: সহজ টাস্ক করে প্রতিদিন আয় করুন। টাকা তোলার আগে ৯৯৯ টাকা জমা দিন। | Scam message | Asks for money or a fee | Fake CAPTCHA-job advice (I4C) | |
| bn-chk-04 | আপনার অ্যাকাউন্টে ৫০০০ টাকার পুরস্কার এসেছে। পেতে আপনার UPI পিন দিন। | Scam message | Asks for an OTP, PIN, password or card details | None | |
| bn-chk-05 | আপনার বিদ্যুৎ বিল বকেয়া আছে। আজই পরিশোধ না করলে সংযোগ কেটে দেওয়া হবে। | Scam message | Urgency or threat; Asks for money or a fee | None | |
| bn-chk-06 | আমি একটা লিংকে ক্লিক করে আমার পাসওয়ার্ড দিয়ে দিয়েছি। এখন কী করব? | Someone asking for help | Nothing | Phishing advice (CERT-In) | |
| bn-chk-07 | আমার বাবা একটি ভুয়া কাস্টমার কেয়ার কলে প্রতারিত হয়েছেন। অভিযোগ করতে কোন হেল্পলাইনে ফোন করব? | Someone asking for help | Nothing | Reporting helpline 1930 (I4C) | |
| bn-chk-08 | কেউ ফোন করে ওটিপি চাইলে বলবেন না। ব্যাংক কখনো পিন চায় না। | Genuine safety advice | Nothing | None | |
| bn-chk-09 | মা, আমি বাসে আছি। এখনই আসছি। | Ordinary message | Nothing | None | |
| bn-chk-10 | আমার কার্ড বাড়িতে রয়ে গেছে, কাল দেখা হবে। | Ordinary message | Nothing | None | |

### Bengali: questions for the reviewer

1. Both লিংক and লিঙ্ক are accepted. Are ওটিপি and পিন the spellings people actually use?
2. "টাকা … দিন" is flagged as a payment demand. Give an everyday sentence this would wrongly flag.
3. Is "দিন না" really a polite request here, as the rules assume, or would readers take it as "don't give"?
4. Scam messages often say "if you don't pay…" (পরিশোধ না করলে). The rules do not catch this form. What are the common ways to write it?
5. These rules are for Bengali as used in India. Is any wording here mainly Bangladeshi usage, or the reverse?
6. Which very common scam phrases are missing altogether?

### Bengali: sign-off

- Reviewer name:
- Date:
- Where you learned and use the language (state or region):
- Parts reviewed (1, 2, 3, 4):
- Overall: **Ready to describe as reviewed** / **Needs the fixes above first** / **Not usable**

## After a review

The project applies the fixes and reruns the tests. A reviewed language can then be considered for a future release; it is not switched on by the review alone. One reviewed language does not change what is said about the other two. A review confirms the wording; it does not measure how many real scams the checks catch.

The files behind this checklist are `backend/app/warning_signs.py` (Part 1), `backend/app/data/term_map_deferred.json` (Part 2) and `backend/evaluation/multilingual_eval.json` (Parts 3 and 4).
