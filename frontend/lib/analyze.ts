/**
 * DEMO ke liye aarzi (placeholder) analysis — keyword based, koi AI nahi.
 *
 * Asli kaam backend/app/services/openai_service.py mein hai (OpenAI se).
 * Jab FastAPI backend Railway par deploy ho jayega, ye file hata kar
 * seedha us API ko call karna hai.
 */

const CONCERN_WORDS = [
  "concern", "concerned", "worried", "worry", "issue", "problem", "risk",
  "delay", "delayed", "budget", "expensive", "cost", "complaint", "unhappy",
  "blocker", "tight", "behind schedule",
];

const ACTION_WORDS = [
  "will send", "will share", "will follow", "will prepare", "will update",
  "need to", "needs to", "we'll", "i'll", "follow up", "action item",
  "by next", "deadline", "schedule a", "send over", "get back",
];

const STOP_WORDS = new Set([
  "the", "and", "for", "that", "with", "this", "have", "from", "they", "them",
  "what", "when", "were", "been", "will", "would", "could", "should", "about",
  "there", "their", "which", "your", "yours", "just", "like", "also", "into",
  "more", "very", "want", "wants", "know", "think", "said", "says", "okay",
  "yeah", "right", "sure", "going", "make", "made", "over", "then", "than",
  "some", "these", "those", "because", "meeting", "client", "team",
]);

function sentences(text: string): string[] {
  return text
    .replace(/\s+/g, " ")
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 15);
}

function hasAny(sentence: string, words: string[]): boolean {
  const low = sentence.toLowerCase();
  return words.some((w) => low.includes(w));
}

export type LocalAnalysis = {
  summary: string;
  topics: string[];
  concerns: string[];
  followups: string[];
};

export function analyzeTranscript(transcript: string): LocalAnalysis {
  const sents = sentences(transcript);

  const summary =
    sents.slice(0, 3).join(" ").slice(0, 600) ||
    transcript.trim().slice(0, 300) ||
    "Transcript is too short to summarize.";

  const freq = new Map<string, number>();
  for (const word of transcript.toLowerCase().match(/[a-z][a-z'-]{3,}/g) ?? []) {
    if (STOP_WORDS.has(word)) continue;
    freq.set(word, (freq.get(word) ?? 0) + 1);
  }

  const topics = [...freq.entries()]
    .filter(([, n]) => n >= 2)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([w]) => w[0].toUpperCase() + w.slice(1));

  const concerns = sents
    .filter((s) => hasAny(s, CONCERN_WORDS))
    .slice(0, 5)
    .map((s) => s.slice(0, 220));

  const followups = sents
    .filter((s) => hasAny(s, ACTION_WORDS))
    .slice(0, 6)
    .map((s) => s.slice(0, 220));

  return { summary, topics, concerns, followups };
}
