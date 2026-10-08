// Second Look's own wording for the results, in English and Hindi. Nothing here is
// generated at run time, and no translation service is used. The Hindi was written by the
// project and has not been reviewed by a language specialist.

import type { ResultsLanguage } from "../lib/resultsLanguage";
import type { SafetyStep } from "./copy";
import { SAFETY_STEPS, SAFETY_STEPS_SOURCE } from "./copy";

export interface ResultsText {
  summaryFound: (count: number) => string;
  summaryFoundBody: string;
  summaryNoneTitle: string;
  summaryNoneBody: string;
  summaryUnsupportedTitle: string;
  summaryUnsupportedBody: string;
  summaryPartialBody: string;
  summaryUnsupportedFoundNote: string;
  summaryUnidentifiedBody: string;
  summaryUnidentifiedFoundNote: string;
  yourMessage: string;
  messageLanguage: string;
  languageLabels: Record<string, string>;
  coverageLabels: Record<string, string>;
  findingsStep: string;
  findingsTitle: string;
  findingsLead: string;
  findingsNone: string;
  findingsNoneUnsupported: string;
  findingsNonePartial: string;
  findingsNoneUnidentified: string;
  fromYourMessage: string;
  whyItMatters: string;
  categoryLabels: Record<string, string>;
  categoryFallback: string;
  guidanceStep: string;
  guidanceTitle: string;
  guidanceLead: string;
  source: string;
  section: string;
  published: string;
  retrieved: string;
  viewSource: string;
  opensInNewTab: string;
  stepsStep: string;
  stepsTitle: string;
  stepsLead: string;
  safetySteps: SafetyStep[];
  safetyStepsSource: string;
  nextStep: string;
  nextTitle: string;
  nextLead: string;
  nextChoose: string;
  nextLoading: string;
  nextError: string;
  tryAgain: string;
  situationLabels: Record<string, string>;
  classifierTitle: string;
  experimental: string;
  classifierHeadlines: Record<string, string>;
  classifierNoSignal: string;
  classifierModel: (trainingData: string) => string;
  checkAnother: string;
}

const ENGLISH: ResultsText = {
  summaryFound: (count) => `We noticed ${count} warning ${count === 1 ? "sign" : "signs"}`,
  summaryFoundBody: "Review them below before you reply, click a link, share a code, or pay.",
  summaryNoneTitle: "We didn't find the warning signs we check for",
  summaryNoneBody:
    "That does not mean the message is safe. Scams can avoid these patterns, so verify through an official channel before you act.",
  summaryUnsupportedTitle: "This message hasn't been fully checked",
  summaryUnsupportedBody:
    "We can check links, rupee amounts, and some English terms, but we may miss warning signs in this language. This does not mean the message is safe.",
  summaryPartialBody:
    "We could check only some of the wording in this message, so we may miss warning signs. This does not mean the message is safe.",
  summaryUnsupportedFoundNote: "This language is not analysed, so other warning signs may have been missed.",
  summaryUnidentifiedBody:
    "We couldn't fully check this message. Some warning signs may be missed. This does not mean the message is safe.",
  summaryUnidentifiedFoundNote: "We couldn't fully check this message, so other warning signs may have been missed.",
  yourMessage: "Your message",
  messageLanguage: "Message language (estimate):",
  languageLabels: {
    en: "English",
    hi: "Hindi",
    "hi-Latn": "Romanized Hindi",
    te: "Telugu",
    ur: "Urdu",
    bn: "Bengali",
    mixed: "Mixed languages",
    unknown: "Not identified",
  },
  coverageLabels: {
    supported: "All checks apply",
    partial: "Partial checks",
    unsupported: "Language not supported",
  },
  findingsStep: "1 · What we noticed",
  findingsTitle: "Warning signs",
  findingsLead: "Specific phrases from your message, and why they deserve attention.",
  findingsNone: "None of the warning signs we check for appeared in this message.",
  findingsNoneUnsupported:
    "This language is not analysed. No link or English-language warning sign was found, but others may have been missed.",
  findingsNonePartial: "We didn't find these warning signs in the parts we could check.",
  findingsNoneUnidentified: "No link or English-language warning sign was found, but others may have been missed.",
  fromYourMessage: "From your message",
  whyItMatters: "Why it matters: ",
  categoryLabels: {
    urgency_pressure: "Urgency or threats",
    credential_request: "Asks for an OTP, PIN or password",
    link: "Contains a link",
    payment_demand: "Asks for money or a fee",
  },
  categoryFallback: "Warning sign",
  guidanceStep: "2 · Official guidance",
  guidanceTitle: "What official sources say",
  guidanceLead: "Matched from a small collection of Indian government cyber-safety guidance.",
  source: "Source",
  section: "Section",
  published: "Published",
  retrieved: "Retrieved",
  viewSource: "View official source",
  opensInNewTab: " (opens in a new tab)",
  stepsStep: "3 · What to do next",
  stepsTitle: "Safer next steps",
  stepsLead: "General steps for any suspicious message. They are the same for every check.",
  safetySteps: SAFETY_STEPS,
  safetyStepsSource: SAFETY_STEPS_SOURCE,
  nextStep: "4 · If something already happened",
  nextTitle: "What happened next?",
  nextLead: "Pick the closest answer to see what the official sources say to do. Your answer stays in your browser.",
  nextChoose: "Choose what happened",
  nextLoading: "Loading the options…",
  nextError: "We couldn't load these steps right now. The general steps above still apply.",
  tryAgain: "Try again",
  // In English the labels come from the API; these are not used.
  situationLabels: {},
  classifierTitle: "Auxiliary signal",
  experimental: "Experimental",
  classifierHeadlines: {
    spam_like: "Resembles older English SMS spam",
    not_spam_like: "Does not resemble older English SMS spam",
    not_applicable: "Not applied to this message",
    unavailable: "Not available right now",
  },
  classifierNoSignal: "No signal",
  classifierModel: (trainingData) => `Trained on: ${trainingData}. It does not decide whether a message is fraudulent.`,
  checkAnother: "Check another message",
};

const HINDI: ResultsText = {
  summaryFound: (count) => (count === 1 ? "हमें 1 चेतावनी संकेत मिला" : `हमें ${count} चेतावनी संकेत मिले`),
  summaryFoundBody: "जवाब देने, लिंक खोलने, कोड बताने या पैसे भेजने से पहले इन्हें नीचे देख लें।",
  summaryNoneTitle: "जिन चेतावनी संकेतों की हम जाँच करते हैं, वे नहीं मिले",
  summaryNoneBody:
    "इसका मतलब यह नहीं है कि संदेश सुरक्षित है। ठगी के संदेश इन संकेतों से बच सकते हैं, इसलिए कुछ भी करने से पहले आधिकारिक माध्यम से पुष्टि करें।",
  summaryUnsupportedTitle: "इस संदेश की पूरी तरह जाँच नहीं हो सकी",
  summaryUnsupportedBody:
    "हम लिंक, रुपये की रकम और कुछ अंग्रेज़ी शब्दों की जाँच कर सकते हैं, लेकिन इस भाषा में चेतावनी के संकेत छूट सकते हैं। इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
  summaryPartialBody:
    "हम इस संदेश के केवल कुछ शब्दों की जाँच कर सके, इसलिए चेतावनी के संकेत छूट सकते हैं। इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
  summaryUnsupportedFoundNote: "इस भाषा का विश्लेषण नहीं किया जाता, इसलिए दूसरे चेतावनी संकेत छूट सकते हैं।",
  summaryUnidentifiedBody:
    "हम इस संदेश की पूरी तरह जाँच नहीं कर सके। कुछ चेतावनी संकेत छूट सकते हैं। इसका मतलब यह नहीं है कि संदेश सुरक्षित है।",
  summaryUnidentifiedFoundNote: "हम इस संदेश की पूरी तरह जाँच नहीं कर सके, इसलिए दूसरे चेतावनी संकेत छूट सकते हैं।",
  yourMessage: "आपका संदेश",
  messageLanguage: "संदेश की भाषा (अनुमान):",
  languageLabels: {
    en: "अंग्रेज़ी",
    hi: "हिन्दी",
    "hi-Latn": "रोमन लिपि में हिन्दी",
    te: "तेलुगु",
    ur: "उर्दू",
    bn: "बांग्ला",
    mixed: "मिली-जुली भाषाएँ",
    unknown: "पहचान नहीं हुई",
  },
  coverageLabels: {
    supported: "सभी जाँचें लागू",
    partial: "आंशिक जाँच",
    unsupported: "भाषा समर्थित नहीं",
  },
  findingsStep: "1 · हमने क्या देखा",
  findingsTitle: "चेतावनी संकेत",
  findingsLead: "आपके संदेश के खास अंश, और उन पर ध्यान देना क्यों ज़रूरी है।",
  findingsNone: "जिन चेतावनी संकेतों की हम जाँच करते हैं, उनमें से कोई इस संदेश में नहीं मिला।",
  findingsNoneUnsupported:
    "इस भाषा का विश्लेषण नहीं किया जाता। कोई लिंक या अंग्रेज़ी में लिखा चेतावनी संकेत नहीं मिला, लेकिन दूसरे संकेत छूट सकते हैं।",
  findingsNonePartial: "जिन हिस्सों की हम जाँच कर सके, उनमें ये चेतावनी संकेत नहीं मिले।",
  findingsNoneUnidentified: "कोई लिंक या अंग्रेज़ी में लिखा चेतावनी संकेत नहीं मिला, लेकिन दूसरे संकेत छूट सकते हैं।",
  fromYourMessage: "आपके संदेश से",
  whyItMatters: "यह क्यों मायने रखता है: ",
  categoryLabels: {
    urgency_pressure: "जल्दबाज़ी या धमकी",
    credential_request: "OTP, PIN या पासवर्ड माँगा गया है",
    link: "संदेश में लिंक है",
    payment_demand: "पैसे या शुल्क माँगा गया है",
  },
  categoryFallback: "चेतावनी संकेत",
  guidanceStep: "2 · आधिकारिक मार्गदर्शन",
  guidanceTitle: "आधिकारिक स्रोत क्या कहते हैं",
  guidanceLead: "भारत सरकार के साइबर-सुरक्षा मार्गदर्शन के एक छोटे संग्रह से मिलान किया गया।",
  source: "स्रोत",
  section: "अनुभाग",
  published: "प्रकाशित",
  retrieved: "देखा गया",
  viewSource: "आधिकारिक स्रोत देखें",
  opensInNewTab: " (नए टैब में खुलेगा)",
  stepsStep: "3 · आगे क्या करें",
  stepsTitle: "सुरक्षित अगले कदम",
  stepsLead: "किसी भी संदिग्ध संदेश के लिए सामान्य कदम। ये हर जाँच में एक जैसे रहते हैं।",
  safetySteps: [
    {
      title: "जवाब देने से पहले रुकें",
      detail:
        "जब तक आप संदेश की जाँच न कर लें, तब तक जवाब न दें, लिंक न खोलें, और पासवर्ड, PIN या कार्ड की जानकारी जैसी कोई निजी या वित्तीय जानकारी साझा न करें।",
    },
    {
      title: "संस्था से सीधे पुष्टि करें",
      detail: "संदेश में दिए लिंक का इस्तेमाल करने के बजाय, संस्था से सीधे संपर्क करके पता करें कि संदेश असली है या नहीं।",
    },
    {
      title: "अगर आप जवाब दे चुके हैं",
      detail:
        "अपने बैंक या व्यापारी से सीधे संपर्क करें, जो पासवर्ड या PIN आपने बताए हैं उन्हें बदलें, और अपने खाते के विवरण में ऐसे लेन-देन देखें जो आपने नहीं किए।",
    },
    {
      title: "अगर आपके पैसे गए हैं",
      detail: "तुरंत राष्ट्रीय साइबर अपराध हेल्पलाइन 1930 पर कॉल करके इसकी शिकायत करें।",
    },
  ],
  safetyStepsSource: "CERT-In और भारतीय साइबर अपराध समन्वय केंद्र (I4C) की सलाह पर आधारित।",
  nextStep: "4 · अगर कुछ हो चुका है",
  nextTitle: "आगे क्या हुआ?",
  nextLead: "सबसे मिलता-जुलता जवाब चुनें और देखें कि आधिकारिक स्रोत क्या करने को कहते हैं। आपका जवाब आपके ब्राउज़र में ही रहता है।",
  nextChoose: "बताएँ कि क्या हुआ",
  nextLoading: "विकल्प लोड हो रहे हैं…",
  nextError: "अभी ये कदम लोड नहीं हो सके। ऊपर दिए गए सामान्य कदम फिर भी लागू होते हैं।",
  tryAgain: "फिर कोशिश करें",
  // Keyed by the situation ids the API sends.
  situationLabels: {
    not_responded: "मैंने न जवाब दिया, न लिंक खोला, न पैसे भेजे",
    clicked_link: "मैंने संदेश में दिया लिंक खोल लिया",
    shared_details: "मैंने OTP, PIN, पासवर्ड, या कार्ड या बैंक की जानकारी बता दी",
    lost_money: "मैंने पैसे भेज दिए, या मेरे खाते से पैसे निकल गए",
  },
  classifierTitle: "सहायक संकेत",
  experimental: "प्रायोगिक",
  classifierHeadlines: {
    spam_like: "पुराने अंग्रेज़ी SMS स्पैम से मिलता-जुलता है",
    not_spam_like: "पुराने अंग्रेज़ी SMS स्पैम से मिलता-जुलता नहीं है",
    not_applicable: "इस संदेश पर लागू नहीं किया गया",
    unavailable: "अभी उपलब्ध नहीं है",
  },
  classifierNoSignal: "कोई संकेत नहीं",
  classifierModel: (trainingData) => `प्रशिक्षण डेटा: ${trainingData}। यह तय नहीं करता कि संदेश धोखाधड़ी है या नहीं।`,
  checkAnother: "दूसरा संदेश जाँचें",
};

export const RESULTS_TEXT: Record<ResultsLanguage, ResultsText> = { en: ENGLISH, hi: HINDI };

/** Shown only with Hindi results. */
export const HINDI_PRESENTATION_NOTE =
  "यह हिन्दी पाठ Second Look ने तैयार किया है और अभी किसी भाषा-विशेषज्ञ ने इसकी समीक्षा नहीं की है। आपका संदेश, उसके अंश और आधिकारिक स्रोतों के नाम जैसे हैं वैसे ही दिखाए जाते हैं।";

/** Label on official-guidance text shown in Hindi. */
export const HINDI_EXPLANATION_LABEL = "हिन्दी व्याख्या · Second Look का अनुवाद, आधिकारिक पाठ नहीं";
export const ORIGINAL_ENGLISH_SUMMARY_LABEL = "मूल अंग्रेज़ी सारांश";
