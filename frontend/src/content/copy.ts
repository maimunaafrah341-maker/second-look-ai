// Fixed interface text. Nothing here is generated at run time.

export interface ExampleMessage {
  id: string;
  label: string;
  message: string;
}

/** Sample messages written for this demo. They are not real messages from real people. */
export const EXAMPLE_MESSAGES: ExampleMessage[] = [
  {
    id: "kyc-en",
    label: "KYC and OTP request (English)",
    message: "URGENT: Your SBI account will be blocked today. Update your KYC at http://bit.ly/kyc-update and share the OTP you receive.",
  },
  {
    id: "otp-hi",
    label: "Account block and OTP request (Hindi)",
    message: "आपका खाता आज बंद हो जाएगा। तुरंत अपना ओटीपी बताएं।",
  },
  {
    id: "job-hi-latn",
    label: "Job offer asking for a fee (Romanized Hindi)",
    message: "Ghar baithe kamai karein! Captcha job ke liye registration fee Rs 499 jama karo aur roz 2000 kamao.",
  },
  {
    id: "genuine-otp",
    label: "Genuine bank OTP notice",
    message: "Your OTP for login is 482913. It is valid for 10 minutes. Never share your OTP with anyone.",
  },
];

export interface SafetyStep {
  title: string;
  detail: string;
}

/**
 * General safety steps shown with every result and in the Safety tips section. They are
 * the same for every message and are based on advice in the CERT-In "Avoid Phishing
 * Attacks" leaflet and the I4C website, which are cited in docs/guidance_sources.md.
 */
export const SAFETY_STEPS: SafetyStep[] = [
  {
    title: "Pause before you respond",
    detail: "Don't reply, click links, or share personal or financial information, including passwords, PINs or card details, until you have checked the message.",
  },
  {
    title: "Check with the organisation directly",
    detail: "Contact the organisation directly to confirm whether the message is genuine, rather than following a link in the message.",
  },
  {
    title: "If you already responded",
    detail: "Contact your bank or merchant directly, change any passwords or PINs you shared, and review your statements for charges you did not make.",
  },
  {
    title: "If you lost money",
    detail: "Report it immediately by calling the national cybercrime helpline, 1930.",
  },
];

export const SAFETY_STEPS_SOURCE = "Based on advice from CERT-In and the Indian Cybercrime Coordination Centre (I4C).";
