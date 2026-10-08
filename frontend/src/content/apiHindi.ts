// Hindi for the fixed English text the API sends: explanations, notices and the summaries
// Second Look wrote for each official source. Each entry is keyed by the exact English
// text. If the API ever sends text that is not listed here, the English is shown as it
// is, so a change on the server can never show a Hindi line that no longer matches.
//
// Written by the project, not by the publishers, and not reviewed by a language
// specialist. Source titles, publisher names, section names, dates and links are never
// translated.

import type { ResultsLanguage } from "../lib/resultsLanguage";

const STILL_CHECKED = "लिंक, रुपये की रकम और OTP या KYC जैसे अंग्रेज़ी शब्द फिर भी जाँचे जाते हैं।";
const ESTIMATE = "यह स्वचालित अनुमान है और गलत हो सकता है।";

export const API_TEXT_HINDI: Record<string, string> = {
  // Why each warning sign matters
  "The message uses urgency, a threat, or a deadline. Pressure to act quickly is a common tactic to stop people from checking whether a request is genuine.":
    "संदेश में जल्दबाज़ी, धमकी या समय-सीमा का इस्तेमाल किया गया है। जल्दी कदम उठाने का दबाव एक आम तरीका है, ताकि लोग यह न जाँच पाएँ कि माँग असली है या नहीं।",
  "The message asks for an OTP, PIN, password, or banking details. These are meant to be kept secret; sharing them can give someone else access to your account.":
    "संदेश में OTP, PIN, पासवर्ड या बैंक की जानकारी माँगी गई है। ये गोपनीय रखने के लिए होते हैं; इन्हें बताने से कोई दूसरा आपके खाते तक पहुँच सकता है।",
  "The message contains a link. Do not open it unless you have confirmed the sender through an official channel.":
    "संदेश में एक लिंक है। जब तक आप किसी आधिकारिक माध्यम से भेजने वाले की पुष्टि न कर लें, इसे न खोलें।",
  "The message asks for a payment, transfer, or fee. Being asked to pay before receiving a prize, refund, parcel, or service is a common advance-fee pattern.":
    "संदेश में भुगतान, पैसे भेजने या शुल्क की माँग की गई है। इनाम, रिफ़ंड, पार्सल या सेवा मिलने से पहले पैसे माँगना अग्रिम-शुल्क वाली ठगी का एक आम तरीका है।",

  // What stands out about a link
  "uses a link-shortening service, which hides the real destination": "पता छोटा करने वाली सेवा का इस्तेमाल करता है, जिससे असली पता छिप जाता है",
  "uses a numeric IP address instead of a domain name": "डोमेन नाम की जगह अंकों वाला IP पता इस्तेमाल करता है",
  "uses an encoded (punycode) domain, which can imitate another site's name":
    "एन्कोड किया हुआ (punycode) डोमेन इस्तेमाल करता है, जो किसी दूसरी साइट के नाम की नकल कर सकता है",
  "has an '@' before the real address, which can disguise the destination": "असली पते से पहले '@' रखता है, जिससे असली पता छिप सकता है",
  "uses unencrypted http": "बिना एन्क्रिप्शन वाला http इस्तेमाल करता है",

  // Notices
  "These are rule-based indicators only. They cannot determine whether a message is fraudulent: a message with no indicators may still be a scam, and a message with indicators may be legitimate. Verify through an official channel before acting.":
    "ये केवल नियमों पर आधारित संकेत हैं। ये तय नहीं कर सकते कि कोई संदेश धोखाधड़ी है या नहीं: बिना किसी संकेत वाला संदेश भी ठगी हो सकता है, और संकेत वाला संदेश असली भी हो सकता है। कुछ भी करने से पहले आधिकारिक माध्यम से पुष्टि करें।",
  "These entries were retrieved by keyword similarity from a small, English-only collection of official guidance. They are not a judgement about this message, and the publishers have not reviewed or endorsed this service. Read the linked source.":
    "ये प्रविष्टियाँ आधिकारिक मार्गदर्शन के एक छोटे, केवल अंग्रेज़ी वाले संग्रह से, शब्दों की समानता के आधार पर चुनी गई हैं। ये इस संदेश के बारे में कोई फ़ैसला नहीं हैं, और प्रकाशकों ने इस सेवा की समीक्षा या समर्थन नहीं किया है। लिंक किया गया स्रोत पढ़ें।",
  "No matching official guidance was found. The collection is small and English-only, so this does not mean the message is safe.":
    "कोई मिलता-जुलता आधिकारिक मार्गदर्शन नहीं मिला। यह संग्रह छोटा है और केवल अंग्रेज़ी में है, इसलिए इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
  "Summary written by Second Look. It is not a quotation from the source.": "यह सारांश Second Look ने लिखा है। यह स्रोत का उद्धरण नहीं है।",
  "These steps come from the linked official sources and are the same for everyone who picks the same answer. They are not advice about your particular case, and Second Look does not contact anyone or file a report for you.":
    "ये कदम लिंक किए गए आधिकारिक स्रोतों से लिए गए हैं और एक ही जवाब चुनने वाले हर व्यक्ति के लिए एक जैसे हैं। ये आपके खास मामले के लिए सलाह नहीं हैं, और Second Look आपकी ओर से किसी से संपर्क नहीं करता और न ही कोई शिकायत दर्ज करता है।",
  "Call 1930": "1930 पर कॉल करें",

  // Auxiliary classifier
  "This auxiliary signal compares the message with English SMS spam from a 2011 UK and Singapore dataset. It was not trained on Indian scams and cannot tell whether this message is fraudulent. Genuine bank, OTP and delivery messages are often rated spam-like, and many scams are not. A 'not spam-like' label does not mean the message is safe. This signal does not change the warning signs or the official guidance.":
    "यह सहायक संकेत संदेश की तुलना 2011 के ब्रिटेन और सिंगापुर के एक डेटासेट के अंग्रेज़ी SMS स्पैम से करता है। इसे भारतीय ठगी के संदेशों पर प्रशिक्षित नहीं किया गया है और यह नहीं बता सकता कि यह संदेश धोखाधड़ी है या नहीं। बैंक, OTP और डिलीवरी के असली संदेश अक्सर स्पैम जैसे आँके जाते हैं, और कई ठगी के संदेश नहीं आँके जाते। 'स्पैम जैसा नहीं' लेबल का मतलब यह नहीं है कि संदेश सुरक्षित है। यह संकेत चेतावनी संकेतों या आधिकारिक मार्गदर्शन को नहीं बदलता।",
  "The auxiliary classifier was not run because this message does not appear to be mainly in English, and the model was trained only on English SMS. This does not mean the message is safe.":
    "सहायक क्लासिफ़ायर नहीं चलाया गया, क्योंकि यह संदेश मुख्य रूप से अंग्रेज़ी में नहीं लगता, और मॉडल को केवल अंग्रेज़ी SMS पर प्रशिक्षित किया गया है। इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
  "The auxiliary classifier is not available. The warning signs and official guidance are unaffected. This does not mean the message is safe.":
    "सहायक क्लासिफ़ायर उपलब्ध नहीं है। चेतावनी संकेतों और आधिकारिक मार्गदर्शन पर इसका कोई असर नहीं पड़ता। इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
  "UCI SMS Spam Collection: English SMS from the UK and Singapore, around 2011":
    "UCI SMS Spam Collection: ब्रिटेन और सिंगापुर के अंग्रेज़ी SMS, लगभग 2011 के",

  // Language estimate
  "Estimated language: English. All of Second Look's checks are designed for English. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: अंग्रेज़ी। Second Look की सभी जाँचें अंग्रेज़ी के लिए बनाई गई हैं। ${ESTIMATE}`,
  "Estimated language: Hindi (Devanagari). A limited list of common Hindi scam phrases is checked, and some Hindi words are used to find the official guidance, which is in English. Other wording may be missed. Links, rupee amounts and English words such as OTP or KYC are still checked. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: हिन्दी (देवनागरी)। ठगी में इस्तेमाल होने वाले आम हिन्दी वाक्यांशों की एक सीमित सूची जाँची जाती है, और आधिकारिक मार्गदर्शन खोजने के लिए कुछ हिन्दी शब्दों का इस्तेमाल होता है; यह मार्गदर्शन अंग्रेज़ी में है। दूसरे शब्दों वाले संदेश छूट सकते हैं। ${STILL_CHECKED} ${ESTIMATE}`,
  "Estimated language: Hindi written in English letters. A limited list of common romanised Hindi scam phrases and spellings is checked, and some romanised Hindi words are used to find the official guidance, which is in English. Other wording or spellings may be missed. Links, rupee amounts and English words such as OTP or KYC are still checked. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: अंग्रेज़ी अक्षरों में लिखी हिन्दी। ठगी में इस्तेमाल होने वाले आम रोमन-हिन्दी वाक्यांशों और वर्तनियों की एक सीमित सूची जाँची जाती है, और आधिकारिक मार्गदर्शन खोजने के लिए कुछ रोमन-हिन्दी शब्दों का इस्तेमाल होता है; यह मार्गदर्शन अंग्रेज़ी में है। दूसरे शब्द या वर्तनियाँ छूट सकती हैं। ${STILL_CHECKED} ${ESTIMATE}`,
  "Estimated language: a mix of languages or scripts. English parts are checked fully; other parts may be checked only partly or not at all. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: कई भाषाओं या लिपियों का मेल। अंग्रेज़ी हिस्सों की पूरी जाँच होती है; बाकी हिस्सों की जाँच आंशिक हो सकती है या बिल्कुल नहीं भी हो सकती। ${ESTIMATE}`,
  "Estimated language: Telugu. Telugu text is not analysed yet. Links, rupee amounts and English words such as OTP or KYC are still checked. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: तेलुगु। तेलुगु पाठ का विश्लेषण अभी नहीं किया जाता। ${STILL_CHECKED} ${ESTIMATE}`,
  "Estimated language: Urdu. Urdu text is not analysed. Links, rupee amounts and English words such as OTP or KYC are still checked. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: उर्दू। उर्दू पाठ का विश्लेषण नहीं किया जाता। ${STILL_CHECKED} ${ESTIMATE}`,
  "Estimated language: Bengali. Bengali text is not analysed. Links, rupee amounts and English words such as OTP or KYC are still checked. This is an automatic estimate and may be wrong.": `अनुमानित भाषा: बांग्ला। बांग्ला पाठ का विश्लेषण नहीं किया जाता। ${STILL_CHECKED} ${ESTIMATE}`,
  "The language could not be estimated, for example because the message has few or no letters or uses a script Second Look does not recognise. Links, rupee amounts and English words such as OTP or KYC are still checked.": `भाषा का अनुमान नहीं लगाया जा सका, उदाहरण के लिए इसलिए कि संदेश में अक्षर बहुत कम हैं या नहीं हैं, या ऐसी लिपि है जिसे Second Look नहीं पहचानता। ${STILL_CHECKED}`,

  // Official guidance: topics and the summaries Second Look wrote for each source
  "Fake CAPTCHA-filling jobs: how it works": "नकली CAPTCHA भरने की नौकरियाँ: यह कैसे होता है",
  "Fraudsters advertise well-paid CAPTCHA-filling work on social media, job portals and messaging apps. Applicants are asked to pay a registration, training or software fee, then given large tasks on a fake platform. Payouts are later refused, and further payments are demanded as taxes, charges or upgrades.":
    "ठग सोशल मीडिया, नौकरी के पोर्टल और मैसेजिंग ऐप पर CAPTCHA भरने के अच्छे वेतन वाले काम का विज्ञापन देते हैं। आवेदकों से पंजीकरण, प्रशिक्षण या सॉफ़्टवेयर का शुल्क माँगा जाता है, फिर उन्हें एक नकली प्लेटफ़ॉर्म पर बड़े-बड़े काम दिए जाते हैं। बाद में भुगतान से इनकार कर दिया जाता है, और टैक्स, शुल्क या अपग्रेड के नाम पर और पैसे माँगे जाते हैं।",
  "Fake CAPTCHA-filling jobs: warning signs and precautions": "नकली CAPTCHA भरने की नौकरियाँ: चेतावनी संकेत और सावधानियाँ",
  "The advisory lists four warning signs: upfront payment, unrealistic earnings, delayed or denied withdrawals, and heavy emphasis on referrals. It advises researching the platform, not sharing sensitive personal or financial information, and reporting fraud immediately by calling 1930 or through the national cybercrime reporting portal.":
    "एडवाइज़री में चार चेतावनी संकेत बताए गए हैं: पहले से भुगतान की माँग, अवास्तविक कमाई का वादा, पैसे निकालने में देरी या इनकार, और दूसरों को जोड़ने (रेफ़रल) पर बहुत ज़ोर। यह प्लेटफ़ॉर्म के बारे में जाँच-पड़ताल करने, संवेदनशील निजी या वित्तीय जानकारी साझा न करने, और धोखाधड़ी की शिकायत तुरंत 1930 पर कॉल करके या राष्ट्रीय साइबर अपराध रिपोर्टिंग पोर्टल के ज़रिए करने की सलाह देती है।",
  "Matrimonial-platform investment fraud: how it works": "वैवाहिक प्लेटफ़ॉर्म पर निवेश की धोखाधड़ी: यह कैसे होती है",
  "Fraudsters create fake profiles on matrimonial and dating platforms, often with stolen photographs and invented professions. They build emotional trust over calls and chats. They then create urgent or emotional situations to obtain money, or push investment and cryptocurrency schemes that promise high returns.":
    "ठग वैवाहिक और डेटिंग प्लेटफ़ॉर्म पर नकली प्रोफ़ाइल बनाते हैं, अक्सर चोरी की तस्वीरों और मनगढ़ंत पेशों के साथ। वे कॉल और चैट के ज़रिए भावनात्मक भरोसा बनाते हैं। फिर वे पैसे पाने के लिए जल्दबाज़ी वाली या भावनात्मक स्थितियाँ बनाते हैं, या ऊँचे मुनाफ़े का वादा करने वाली निवेश और क्रिप्टोकरेंसी योजनाओं के लिए दबाव डालते हैं।",
  "Matrimonial-platform investment fraud: precautions": "वैवाहिक प्लेटफ़ॉर्म पर निवेश की धोखाधड़ी: सावधानियाँ",
  "The advisory recommends verifying the person's identity, including a reverse image search of their photographs. It advises not sharing private details, photographs or financial information with someone you have not met in person. It also advises not transferring money or investing on the word of an unverified online contact, especially where returns look unrealistic.":
    "एडवाइज़री व्यक्ति की पहचान की पुष्टि करने की सलाह देती है, जिसमें उनकी तस्वीरों की रिवर्स इमेज सर्च भी शामिल है। यह सलाह देती है कि जिस व्यक्ति से आप आमने-सामने नहीं मिले हैं, उसके साथ निजी जानकारी, तस्वीरें या वित्तीय जानकारी साझा न करें। यह भी सलाह देती है कि किसी ऐसे ऑनलाइन संपर्क के कहने पर पैसे न भेजें या निवेश न करें जिसकी पुष्टि नहीं हुई है, खासकर जब मुनाफ़ा अवास्तविक लगे।",
  "Phishing: how to recognise it": "फ़िशिंग: इसे कैसे पहचानें",
  "The leaflet advises treating any email request for financial or personal information with suspicion, especially an urgent one. It describes common signs: threats that an account will be closed, web addresses that closely imitate a known organisation, and spelling or grammar mistakes.":
    "पत्रक सलाह देता है कि वित्तीय या निजी जानकारी माँगने वाले किसी भी ईमेल को शक की नज़र से देखें, खासकर जब उसमें जल्दबाज़ी हो। इसमें आम संकेत बताए गए हैं: खाता बंद करने की धमकी, किसी जानी-मानी संस्था से बहुत मिलते-जुलते वेब पते, और वर्तनी या व्याकरण की गलतियाँ।",
  "Phishing: what not to do": "फ़िशिंग: क्या न करें",
  "The leaflet advises against replying to messages that ask for personal or financial information, and against clicking links in unexpected messages. It advises never responding to phone calls that ask for bank details. It says an SMS asking you to confirm account information, or to reveal personal information to receive a prize, is most likely phishing.":
    "पत्रक सलाह देता है कि निजी या वित्तीय जानकारी माँगने वाले संदेशों का जवाब न दें, और अनपेक्षित संदेशों में दिए लिंक न खोलें। यह सलाह देता है कि बैंक की जानकारी माँगने वाले फ़ोन कॉल का कभी जवाब न दें। इसके अनुसार, खाते की जानकारी की पुष्टि करने को कहने वाला, या इनाम पाने के लिए निजी जानकारी बताने को कहने वाला SMS संभवतः फ़िशिंग है।",
  "Phishing: if you have already responded": "फ़िशिंग: अगर आप जवाब दे चुके हैं",
  "The leaflet advises changing the passwords or PINs of accounts that may be affected. It advises contacting the bank or merchant directly, without using the link in the suspicious message, and reviewing bank and card statements for transactions you did not make.":
    "पत्रक सलाह देता है कि जिन खातों पर असर पड़ सकता है, उनके पासवर्ड या PIN बदल दें। यह सलाह देता है कि संदिग्ध संदेश में दिए लिंक का इस्तेमाल किए बिना, बैंक या व्यापारी से सीधे संपर्क करें, और बैंक व कार्ड के विवरण में ऐसे लेन-देन देखें जो आपने नहीं किए।",
  "Reporting cybercrime": "साइबर अपराध की शिकायत",
  "The I4C website tells people to report cybercrime by calling the helpline 1930.":
    "I4C की वेबसाइट लोगों को हेल्पलाइन 1930 पर कॉल करके साइबर अपराध की शिकायत करने को कहती है।",
};

/** The Hindi for a fixed API text, or the text unchanged when Hindi is not chosen or not available. */
export function localizeApiText(text: string, language: ResultsLanguage): string {
  return language === "hi" ? (API_TEXT_HINDI[text] ?? text) : text;
}

/** True when a Hindi version of this API text is being shown instead of the English. */
export function isLocalized(text: string, language: ResultsLanguage): boolean {
  return language === "hi" && text in API_TEXT_HINDI;
}

const LINK_DETAIL = " This link ";

/**
 * The explanation of a warning sign. For a link, the API adds what stands out about it
 * ("This link uses unencrypted http; ..."), built from a fixed list. If any part is not
 * known, the whole explanation stays in English.
 */
export function localizeExplanation(explanation: string, language: ResultsLanguage): string {
  if (language !== "hi") return explanation;
  if (explanation in API_TEXT_HINDI) return API_TEXT_HINDI[explanation];

  const split = explanation.indexOf(LINK_DETAIL);
  if (split > 0 && explanation.endsWith(".")) {
    const base = API_TEXT_HINDI[explanation.slice(0, split)];
    const traits = explanation
      .slice(split + LINK_DETAIL.length, -1)
      .split("; ")
      .map((trait) => API_TEXT_HINDI[trait]);
    if (base && traits.every(Boolean)) return `${base} यह लिंक ${traits.join("; ")}।`;
  }
  return explanation;
}
