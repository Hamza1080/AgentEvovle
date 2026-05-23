/**
 * evoAgent.ts
 * Step 2 - Python EvoAgent bridge (FIXED + STABLE)
 */

import { execFile } from "child_process";
import fs from "fs";
import path from "path";
import { TripInput } from "./inputParser";

const DATA_DIR = path.join(process.cwd(), "data");
const EVO_IN_PATH = path.join(DATA_DIR, "evo_input.json");
const EVO_OUT_PATH = path.join(DATA_DIR, "evo_output.json");

const PYTHON_SCRIPT = path.resolve(
  process.cwd(),
  "app",
  "api",
  "run-model",
  "agents",
  "run_evo_bridge.py"
);

// ✅ safe cross-platform python path
const PYTHON_BIN_RAW =
  process.env.PYTHON_PATH ||
  "C:/fyp/seprate/seprate/travelplanner_env/Scripts/python.exe";

const PYTHON_BIN = path.normalize(PYTHON_BIN_RAW);

/**
 * Main entry
 */
export async function runEvoAgent(
  query: string,
  input: TripInput
): Promise<string> {
  fs.mkdirSync(DATA_DIR, { recursive: true });

  console.log("[evoAgent] Python path:", PYTHON_BIN);

  // ❗ debug existence
  if (!fs.existsSync(PYTHON_BIN)) {
    throw new Error(`[evoAgent] Python not found at: ${PYTHON_BIN}`);
  }

  const evoInput = {
    query,
    org: input.org || "",
    dest: input.dest || "",
    days: input.days || 1,
    people_number: input.people_number || 1,
    budget: input.budget || 0,
  };

  fs.writeFileSync(EVO_IN_PATH, JSON.stringify([evoInput], null, 2));
  console.log("[evoAgent] ✓ Wrote evo_input.json");

  await runPython(PYTHON_SCRIPT);

  if (!fs.existsSync(EVO_OUT_PATH)) {
    throw new Error("[evoAgent] evo_output.json not found");
  }

  const rawPlan = JSON.parse(
    fs.readFileSync(EVO_OUT_PATH, "utf-8")
  );

  if (!rawPlan) {
    throw new Error("[evoAgent] evo_output.json is empty");
  }

  console.log("[evoAgent] ✓ EvoAgent output received");
  return Array.isArray(rawPlan) ? rawPlan[0] : rawPlan;
}

/**
 * Python execution (Windows-safe)
 */
import { spawn } from "child_process";

function runPython(scriptPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    console.log("[evoAgent] Running Python via:", PYTHON_BIN);

    const proc = spawn(PYTHON_BIN, [scriptPath], {
      cwd: path.dirname(PYTHON_SCRIPT), // ← run from agents/ folder so v6 imports work
      env: {
        ...process.env,
        PYTHONPATH: path.dirname(PYTHON_SCRIPT), // agents/ folder on PYTHONPATH
        PATH: `${path.dirname(PYTHON_BIN)}${path.delimiter}${process.env.PATH}`, // venv first
      },
      shell: true,
    });

    let stderr = "";

    proc.stdout.on("data", (data) => {
      process.stdout.write(`[python] ${data}`);
    });

    proc.stderr.on("data", (data) => {
      stderr += data.toString();
      process.stderr.write(`[python:err] ${data}`);
    });

    proc.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(stderr || `Python exited with code ${code}`));
      }
    });

    proc.on("error", (err) => {
      reject(new Error(`[evoAgent] spawn error: ${err.message}`));
    });
  });
}