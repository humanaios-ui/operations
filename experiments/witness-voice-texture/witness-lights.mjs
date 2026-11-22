// Z1 experiment only (Q-WITNESS-FORM-01, unratified): six-light projection and ask-and-receipt rule.
// Display logic only. A light is lit by a validated texture view and nothing else.
// Synthetic fixtures only. No network, storage, audio, or authority actions.
import { STATES } from "./texture-encoder.mjs";

// Fixed positions on the open ring, clockwise from the upper left. Position and shape,
// not color, identify a channel. Order is part of the contract.
export const LIGHT_ORDER = STATES;

export function projectLights(view) {
  if (!view || typeof view !== "object" || view.isSynthetic !== true ||
      view.authorityEffect !== "NONE" || view.canRatify !== false) {
    throw new TypeError("lights accept only a validated synthetic no-authority view");
  }
  if (!LIGHT_ORDER.includes(view.channel)) throw new TypeError("unknown Witness channel");
  return LIGHT_ORDER.map((channel, index) => ({
    channel, index, lit: channel === view.channel
  }));
}

// Synthetic records. The receipt is a fixture label, not a computed or cryptographic hash.
export const DEMO_RECORDS = Object.freeze([
  Object.freeze({
    id: "DEMO-REC-1",
    receipt: "DEMO-HASH-0001",
    text: "A synthetic decision was recorded as ACCEPT by a synthetic ratifier."
  }),
  Object.freeze({
    id: "DEMO-REC-2",
    receipt: "DEMO-HASH-0002",
    text: "A synthetic correction superseded a prior synthetic entry. The prior entry remains in the record."
  })
]);

// A fixed menu. Free text is not accepted: the demo does no inference.
export const DEMO_QUESTIONS = Object.freeze([
  Object.freeze({ id: "DEMO-Q-DECISION", label: "What was decided?", recordId: "DEMO-REC-1" }),
  Object.freeze({ id: "DEMO-Q-CORRECTION", label: "What was corrected?", recordId: "DEMO-REC-2" }),
  Object.freeze({ id: "DEMO-Q-FEELING", label: "How do you feel about it?", recordId: null })
]);

export const NO_RECORD = "No record.";

export function askWitness(questionId) {
  const base = { authorityEffect: "NONE", canRatify: false, isSynthetic: true };
  const question = DEMO_QUESTIONS.find((q) => q.id === questionId);
  const record = question && question.recordId
    ? DEMO_RECORDS.find((r) => r.id === question.recordId) : null;
  if (!record) {
    return { ...base, answered: false, text: NO_RECORD, recordId: null, receipt: null };
  }
  return { ...base, answered: true, text: record.text, recordId: record.id, receipt: record.receipt };
}
