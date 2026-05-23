/**
 * route.ts  —  /api/run-model
 * ----------------------------
 * Orchestrator only. No business logic here.
 * Calls each pipeline step in order and returns the result.
 *
 * Pipeline:
 *   input.json
 *       ↓  inputParser.ts   →  natural language query
 *       ↓  evoAgent.ts      →  raw plan text
 *       ↓  outputParser.ts  →  strict JSON
 *       ↓  output1.json  +  API response
 */

import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

import { parseInput }  from "./inputParser";
import { runEvoAgent } from "./evoAgent";
// import { parseOutput } from "./Outputparser";

const DATA_DIR   = path.join(process.cwd(), "data");
const INPUT_PATH = path.join(DATA_DIR, "input.json");
const OUT_PATH   = path.join(DATA_DIR, "output1.json");

export async function POST() {
  try {
    // ── 1. Read form input ─────────────────────────────────
    if (!fs.existsSync(INPUT_PATH)) {
      return NextResponse.json(
        { success: false, done: false, error: "input.json not found. Call /api/plan first." },
        { status: 400 }
      );
    }

    const input = JSON.parse(fs.readFileSync(INPUT_PATH, "utf-8"));
    console.log("\n[run-model] ▶ Pipeline started for:", input.org, "→", input.dest);

    // ── 2. Input Parser: JSON → query string ───────────────
    const query = await parseInput(input);
    console.log("\n[inputParser OUTPUT]");
    console.log(query); 

    // ── 3. EvoAgent: query → raw plan text ────────────────
    const rawPlan = await runEvoAgent(query, input);

        // route.ts — replace step 4 & 6

    // ── 4. Read evo_output.json written by the Python bridge ──
    const EVO_OUT_PATH = path.join(DATA_DIR, "evo_output.json");

    if (!fs.existsSync(EVO_OUT_PATH)) {
      return NextResponse.json(
        { success: false, error: "evo_output.json not found. Did the Python bridge run?" },
        { status: 500 }
      );
    }

    const structured = JSON.parse(fs.readFileSync(EVO_OUT_PATH, "utf-8"));

    // ── 5. Write output1.json (optional archive) ──────────────
    fs.mkdirSync(DATA_DIR, { recursive: true });
    fs.writeFileSync(OUT_PATH, JSON.stringify(structured, null, 2));

    console.log("[run-model] ✓ Pipeline complete\n");

    // ── 6. Return to frontend ─────────────────────────────────
    return NextResponse.json({
      success: true,
      done: true,
      normalized: structured,   // ← page.tsx checks this first
    });

  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    console.error("[run-model] ✗ Error:", message);
    return NextResponse.json(
      { success: false, done: false, error: message },
      { status: 500 }
    );
  }
}