/**
 * outputParser.ts
 * ---------------
 * Step 3 of the pipeline.
 * Converts raw EvoAgent plan text → strict JSON the UI expects.
 *
 * Uses OpenAI (gpt-4o-mini) as a structured extraction LLM.
 */

import OpenAI from "openai";
import { TripInput } from "./inputParser";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export interface ItineraryDay {
  day: number;
  current_city: string;
  transportation: string;
  breakfast: string;
  attraction: string;
  lunch: string;
  dinner: string;
  accommodation: string;
}

export interface TravelOutput {
  org: string;
  dest: string;
  days: number;
  people_number: number;
  budget: number;
  itinerary: ItineraryDay[];
}

/**
 * Takes the raw plan text from EvoAgent and extracts it
 * into the strict JSON schema the frontend UI expects.
 */
export async function parseOutput(
  rawPlan: string,
  input: TripInput
): Promise<TravelOutput> {
  const response = await openai.chat.completions.create({
    model: "gpt-4o-mini",
    max_tokens: 2048,
    messages: [
      {
        role: "system",
        content: `You are a structured data extractor for travel plans.
Given a raw travel plan and trip metadata, extract and return ONLY a valid JSON object.
Follow this exact schema — no extra keys, no markdown fences, no explanation:

{
  "org": "<origin city>",
  "dest": "<destination city>",
  "days": <number>,
  "people_number": <number>,
  "budget": <number>,
  "itinerary": [
    {
      "day": <number>,
      "current_city": "<city name>",
      "transportation": "<how they arrived, or '-' for day 1>",
      "breakfast": "<breakfast detail>",
      "attraction": "<main attraction>",
      "lunch": "<lunch detail>",
      "dinner": "<dinner detail>",
      "accommodation": "<hotel or accommodation name>"
    }
  ]
}

Rules:
- itinerary must have exactly <days> entries, one per day.
- Use the provided metadata for org / dest / days / people_number / budget.
- Output ONLY the raw JSON object. No text before or after it.`,
      },
      {
        role: "user",
        content: `Trip metadata:
${JSON.stringify({
  org:           input.org,
  dest:          input.dest,
  days:          input.days,
  people_number: input.people_number,
  budget:        input.budget,
})}

Raw travel plan:
${rawPlan}`,
      },
    ],
  });

  const raw = (response.choices[0]?.message?.content ?? "")
    .trim()
    .replace(/^```json\s*/i, "")
    .replace(/^```\s*/i, "")
    .replace(/```\s*$/i, "");

  let parsed: TravelOutput;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new Error(
      `[outputParser] JSON parse failed.\nRaw response:\n${raw.slice(0, 400)}`
    );
  }

  // Safety fill — in case LLM drifted from metadata
  parsed.org           = parsed.org           || input.org;
  parsed.dest          = parsed.dest          || input.dest;
  parsed.days          = parsed.days          || input.days;
  parsed.people_number = parsed.people_number || input.people_number;
  parsed.budget        = parsed.budget        || input.budget;

  console.log(
    `[outputParser] ✓ Parsed ${parsed.itinerary?.length ?? 0} days`
  );
  return parsed;
}