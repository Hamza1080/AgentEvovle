import fs from "fs";
import path from "path";

/**
 * STEP 1: read input.json
 */
function readInput() {
  const filePath = path.join(process.cwd(), "data", "input.json");
  const raw = fs.readFileSync(filePath, "utf-8");
  const data = JSON.parse(raw);

  // your file is an array → take first object
  return data[0];
}

/**
 * STEP 2: dummy multi-agent pipeline (we will replace later)
 */
function runAgents(input: any) {
  // Agent 1: planner
  const plannerOutput = {
    ...input,
    agent_plan: `Plan created from ${input.org} → ${input.dest}`,
  };

  // Agent 2: scheduler
  const schedulerOutput = {
    ...plannerOutput,
    agent_schedule: `${input.days} day schedule generated`,
  };

  // Agent 3: budget checker
  const finalOutput = {
    ...schedulerOutput,
    budget_status: input.budget > 1500 ? "OK" : "LOW",
  };

  return finalOutput;
}

/**
 * STEP 3: write output.json
 */
function writeOutput(output: any) {
  const filePath = path.join(process.cwd(), "data", "output.json");
  fs.writeFileSync(filePath, JSON.stringify(output, null, 2));
}

/**
 * STEP 4: main runner
 */
export function runModelPipeline() {
  const input = readInput();

  console.log("🤖 INPUT LOADED:", input);

  const output = runAgents(input);

  console.log("🤖 OUTPUT GENERATED:", output);

  writeOutput(output);

  console.log("💾 output.json SAVED");
}