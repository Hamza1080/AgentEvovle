# # """
# # run_evo_bridge.py
# # -----------------
# # Thin bridge between Next.js and EvoAgent.

# # Called by evoAgent.ts (Node spawns this as a subprocess).

# # Flow:
# #   1. Read  data/evo_input.json   (written by evoAgent.ts)
# #   2. Run   EvoAgent pipeline
# #   3. Write data/evo_output.txt   (read back by evoAgent.ts)

# # Place this file in your `agents/` folder, at the same level
# # as v6_full_parallel.py (or wherever your pipeline lives).
# # """

# # import os, sys, json, traceback

# # # ── Path setup ────────────────────────────────────────────
# # # Adjust these if your directory structure differs.
# # CURRENT_DIR  = os.path.dirname(os.path.abspath(__file__))
# # PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))

# # for p in [PROJECT_ROOT, CURRENT_DIR]:
# #     if p not in sys.path:
# #         sys.path.insert(0, p)

# # # ── Paths ─────────────────────────────────────────────────
# # DATA_DIR    = os.path.join(PROJECT_ROOT, "data")
# # EVO_IN      = os.path.join(DATA_DIR, "evo_input.json")
# # EVO_OUT     = os.path.join(DATA_DIR, "evo_output.txt")

# # os.makedirs(DATA_DIR, exist_ok=True)

# # # ─────────────────────────────────────────────────────────
# # def main():
# #     # 1. Read input written by evoAgent.ts
# #     print("[bridge] Reading evo_input.json ...", flush=True)
# #     with open(EVO_IN, "r", encoding="utf-8") as f:
# #         query_data_list = json.load(f)

# #     query_data = query_data_list[0]
# #     query      = query_data.get("query", "")
# #     print(f"[bridge] Query: {query[:80]}...", flush=True)

# #     # ── 2. Import and run your EvoAgent ──────────────────
# #     # OPTION A — call v6_full_parallel.run() directly
# #     # (uncomment when dependencies are ready)
# #     #
# #     # from v6_full_parallel import run
# #     # run(
# #     #     input_file  = EVO_IN,
# #     #     output_dir  = DATA_DIR,
# #     #     model_name  = "gpt-4o-mini",
# #     #     ind         = 2,
# #     # )
# #     # # v6 writes result.json under DATA_DIR/query_1/
# #     # result_path = os.path.join(DATA_DIR, "query_1", "result.json")
# #     # with open(result_path, "r") as f:
# #     #     result = json.load(f)
# #     # raw_plan = result.get("solutions", [""])[0]

# #     # ── OPTION B — stub (active for now) ─────────────────
# #     # Direct OpenAI call so the bridge is live before
# #     # EvoAgent dependencies are sorted.
# #     raw_plan = run_stub(query, query_data)

# #     # 3. Write output for evoAgent.ts to read back
# #     with open(EVO_OUT, "w", encoding="utf-8") as f:
# #         f.write(raw_plan)

# #     print(f"[bridge] ✓ Wrote evo_output.txt ({len(raw_plan)} chars)", flush=True)


# # def run_stub(query: str, meta: dict) -> str:
# #     """
# #     Temporary stub — calls OpenAI directly as a single planner.
# #     Replace with real EvoAgent call (Option A above) once ready.
# #     """
# #     from openai import OpenAI

# #     client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# #     print("[bridge] Running stub planner via OpenAI ...", flush=True)
# #     response = client.chat.completions.create(
# #         model      = "gpt-4o-mini",
# #         max_tokens = 2048,
# #         messages   = [
# #             {
# #                 "role": "system",
# #                 "content": (
# #                     "You are an expert travel planner. "
# #                     "Given a travel query, produce a detailed day-by-day travel plan. "
# #                     "For each day include: city, transportation, breakfast, lunch, dinner, "
# #                     "main attraction, and accommodation. Use real place names. "
# #                     f"Trip is for {meta.get('people_number', 2)} people "
# #                     f"with a total budget of ${meta.get('budget', 2000)} USD."
# #                 ),
# #             },
# #             {"role": "user", "content": query},
# #         ],
# #     )
# #     return response.choices[0].message.content.strip()


# # if __name__ == "__main__":
# #     try:
# #         main()
# #     except Exception as e:
# #         print(f"[bridge] ERROR: {e}", flush=True)
# #         traceback.print_exc()
# #         sys.exit(1)


# import json
# import os

# print("[INFO] Python bridge started")

# # -----------------------------
# # Resolve absolute project root
# # -----------------------------
# BASE_DIR = os.path.abspath(
#     os.path.join(os.path.dirname(__file__), "../../../..")
# )

# INPUT_PATH = os.path.join(BASE_DIR, "data", "evo_input.json")
# OUTPUT_PATH = os.path.join(BASE_DIR, "data", "evo_output.json")

# print("[INFO] INPUT_PATH:", INPUT_PATH)
# print("[INFO] OUTPUT_PATH:", OUTPUT_PATH)

# # -----------------------------
# # Load input safely
# # -----------------------------
# with open(INPUT_PATH, "r", encoding="utf-8") as f:
#     data = json.load(f)

# print("[INFO] INPUT RECEIVED:")
# print(data)

# # -----------------------------
# # Handle both object / array (safety)
# # -----------------------------
# if isinstance(data, list):
#     data = data[0]

# # -----------------------------
# # Extract fields safely
# # -----------------------------
# org = data.get("org", "Unknown Origin")
# dest = data.get("dest", "Unknown Destination")
# days = data.get("days", 3)
# people_number = data.get("people_number", 1)
# budget = data.get("budget", 1000)

# # -----------------------------
# # Fake Evo output (for now)
# # -----------------------------
# # Fake Evo output (for now)

# itinerary = []

# for i in range(1, days + 1):
#     itinerary.append({
#         "day": i,
#         "current_city": org if i == 1 else dest,
#         "transportation": "Flight / Train / Bus",
#         "breakfast": "Hotel breakfast",
#         "lunch": "Local restaurant lunch",
#         "dinner": "City dinner spot",
#         "attraction": f"Top attraction Day {i}",
#         "accommodation": "Hotel / Airbnb stay"
#     })

# output = {
#     "org": org,
#     "dest": dest,
#     "days": days,
#     "people_number": people_number,
#     "budget": budget,
#     "itinerary": itinerary
# }
# # -----------------------------
# # Write output safely
# # -----------------------------
# os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
# import os
# import json

# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

# OUTPUT_PATH = os.path.join(BASE_DIR, "data", "evo_output.json")
# os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
#     json.dump(output, f, indent=2, ensure_ascii=False)

# print("[SUCCESS] evo_output.json written")



"""
run_evo_bridge.py
-----------------
Bridge between Next.js and EvoAgent v6.

Flow:
  1. Read  data/evo_input.json        (written by evoAgent.ts)
  2. Run   v6_full_parallel.run()     (writes data/query_1/result.json)
  3. Parse best solution text → structured itinerary JSON
  4. Write data/evo_output.json       (read back by route.ts)
"""

import os, sys, json, re, traceback

# ── Path setup ────────────────────────────────────────────────────────────────
# run_evo_bridge.py lives in the same folder as v6_full_parallel.py
CURRENT_DIR  = os.path.dirname(os.path.abspath(__file__))

# Project root = 4 levels up from bridge file
# Adjust this if your folder depth differs
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../../.."))

for p in [PROJECT_ROOT, CURRENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Paths ─────────────────────────────────────────────────────────────────────
DATA_DIR   = os.path.join(PROJECT_ROOT, "data")
EVO_IN     = os.path.join(DATA_DIR, "evo_input.json")
EVO_OUT    = os.path.join(DATA_DIR, "evo_output.json")
RESULT_DIR = os.path.join(DATA_DIR, "query_1")          # v6 always writes here

os.makedirs(DATA_DIR, exist_ok=True)

print("[bridge] INPUT_PATH :", EVO_IN,  flush=True)
print("[bridge] OUTPUT_PATH:", EVO_OUT, flush=True)
import json

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# client automatically reads OPENAI_API_KEY from env
client = OpenAI()


def llm_parse_to_itinerary(plan_text, org, dest, days):

    prompt = f"""
You are a strict JSON converter for travel plans.

Convert the following travel plan into structured JSON.

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation
- If missing field, use "-"

SCHEMA:
{{
  "itinerary": [
    {{
      "day": 1,
      "current_city": "",
      "transportation": "",
      "breakfast": "",
      "lunch": "",
      "dinner": "",
      "attraction": "",
      "accommodation": ""
    }}
  ]
}}

Origin: {org}
Destination: {dest}
Days: {days}

TRAVEL PLAN:
{plan_text}
"""

    try:
        print("[parser] Sending request to OpenAI...", flush=True)

        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You convert text into strict JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = resp.choices[0].message.content.strip()

        # cleanup accidental markdown
        content = content.replace("```json", "").replace("```", "")

        return json.loads(content)

    except Exception as e:
        print("[parser ERROR]", e, flush=True)
        return {"itinerary": []}
    
# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    # 1. Read input written by evoAgent.ts
    print("[bridge] Reading evo_input.json ...", flush=True)
    with open(EVO_IN, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # evo_input.json can be a list or a plain object
    meta = raw[0] if isinstance(raw, list) else raw

    org           = meta.get("org",           "Unknown Origin")
    dest          = meta.get("dest",          "Unknown Destination")
    days          = int(meta.get("days",      3))
    people_number = int(meta.get("people_number", 1))
    budget        = int(meta.get("budget",    1000))

    print(f"[bridge] Trip: {org} {dest}, {days} days, "
          f"{people_number} pax, ${budget}", flush=True)

    # 2. Run v6_full_parallel pipeline
    print("[bridge] Importing v6_full_parallel ...", flush=True)
    from v6_full_parallel import run as run_v6

    run_v6(
        input_file = EVO_IN,
        output_dir = DATA_DIR,
        model_name = "gpt-4o",
        ind        = 2,
    )
    print("[bridge] v6 pipeline complete.", flush=True)

    # 3. Read best solution from result.json
    result_path = os.path.join(RESULT_DIR, "result.json")
    print(f"[bridge] Reading result from: {result_path}", flush=True)

    with open(result_path, "r", encoding="utf-8") as f:
        result = json.load(f)

    # result.json has a "solutions" list — pick solution 0 (best ranked)

    solutions = result.get("solutions", {})

    if not solutions:
        raise RuntimeError("v6 returned no solutions in result.json")

    # ALWAYS pick solution_1
    best_plan_text = (
        solutions.get("solution_1")
        or solutions.get("solution_2")
        or solutions.get("solution_3")
    )

    if not best_plan_text:
        raise RuntimeError("No valid solution found in v6 output")

    print(f"[bridge] Selected solution length: {len(best_plan_text)} chars", flush=True)
    
    
# parse with LLM
    try:
        parsed = llm_parse_to_itinerary(best_plan_text, org, dest, days)
        itinerary = parsed.get("itinerary", [])
    except Exception as e:
        print("[bridge] LLM parse failed:", e, flush=True)
        itinerary = []

    output = {
        "org": org,
        "dest": dest,
        "days": days,
        "people_number": people_number,
        "budget": budget,
        "itinerary": itinerary,
    }

    # 5. Write evo_output.json for route.ts to read
    with open(EVO_OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"[bridge] evo_output.json written ({len(itinerary)} days)", flush=True)


def extract_field(text: str, keywords: list) -> str:
    """
    Look for lines like 'Transportation: ...' or '- Breakfast: ...'
    Returns the value, or '-' if not found.
    """
    for kw in keywords:
        # Match "keyword: value" anywhere in the block, case-insensitive
        pattern = rf'(?i){kw}\s*[:\-–]\s*(.+)'
        match   = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            # Trim trailing punctuation / extra lines
            value = value.split('\n')[0].strip(' .,;')
            if value:
                return value
    return "-"


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[bridge] ERROR: {e}", flush=True)
        traceback.print_exc()
        sys.exit(1)