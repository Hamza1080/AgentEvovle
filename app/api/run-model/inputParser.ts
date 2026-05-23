/**
 * inputParser.ts
 * --------------
 * Deterministic + fault-tolerant input parser.
 * Converts structured + free-text input into EvoAgent query.
 */

export interface TripInput {
  org?: string;
  dest?: string;
  days?: number;
  people_number?: number;
  budget?: number;
  notes?: string;
}

function clean(str: any): string | null {
  if (!str || typeof str !== "string") return null;
  const trimmed = str.trim();
  return trimmed.length > 0 ? trimmed : null;
}

/**
 * Deterministic input → query conversion
 */
export function parseInput(input: TripInput): string {
  if (!input || typeof input !== "object") {
    throw new Error("[inputParser] Invalid input object");
  }

  const org = clean(input.org) ?? "unspecified origin";
  const dest = clean(input.dest) ?? "unspecified destination";

  const days = Number(input.days);
  const people = Number(input.people_number);
  const budget = Number(input.budget);

  // ⚠️ DO NOT crash — fallback instead
  const safeDays = Number.isFinite(days) && days > 0 ? days : 3;
  const safePeople = Number.isFinite(people) && people > 0 ? people : 1;
  const safeBudget = Number.isFinite(budget) && budget > 0 ? budget : null;

  // -----------------------------
  // 🔹 Deterministic base prompt
  // -----------------------------
  let query = `You are a travel planning agent.

Create a ${safeDays}-day travel plan from ${org} to ${dest} for ${safePeople} traveler(s).`;

  if (safeBudget) {
    query += ` The total budget is $${safeBudget}.`;
  } else {
    query += ` The budget is flexible or unspecified.`;
  }

  query += `
You MUST generate:
- Daily itinerary
- Transportation plan
- Meals (breakfast, lunch, dinner)
- Attractions
- Accommodation
Keep output structured and realistic.
`;

  // -----------------------------
  // 🔹 Free-text handling (deterministic)
  // -----------------------------
  const notes = clean(input.notes);

  if (notes) {
    // deterministic truncation + normalization
    const normalizedNotes = notes
      .toLowerCase()
      .replace(/\s+/g, " ")
      .slice(0, 250);

    query += `
User preferences (must respect if possible):
${normalizedNotes}
`;
  }

  console.log("[inputParser] ✓ deterministic query generated");
  console.log(query);

  return query;
}