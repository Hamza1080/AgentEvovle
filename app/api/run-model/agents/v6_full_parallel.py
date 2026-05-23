"""
v6_full_parallel.py
--------------------
Changes from original:
- Rich terminal logging at every stage (timestamps, token counts, progress)
- Forced single-query mode: always runs only query index 0
- Log prefix [Q1] shown on every line for easy grepping
"""

import os, sys, json, time, argparse, traceback, threading
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.callbacks import get_openai_callback
from dotenv import load_dotenv

import openai
from openai import OpenAI
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import sys
import io
from dotenv import load_dotenv
from openai import OpenAI

# # Fix terminal encoding (Windows safe)
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load .env
load_dotenv()

# Debug: check key
key = os.getenv("OPENAI_API_KEY")

print("KEY LOADED:", bool(key))

if key:
    print("KEY PREVIEW:", key[:8] + "..." + key[-4:])
else:
    print("KEY MISSING")
    
# IMPORTANT: client auto-reads env var
client = OpenAI()

print("Sending request...")

try:
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": "Say: OpenAI is working"}
        ]
    )

    print("RESPONSE:")
    print(resp.choices[0].message.content)

except Exception as e:
    print("FAILED:")
    print(e)

CURRENT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../../"))
PLANNER_DIR  = os.path.abspath(os.path.join(CURRENT_DIR, "../"))

for p in [PROJECT_ROOT, PLANNER_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

os.chdir(PROJECT_ROOT)

from apis import *
from prompts import *
from ablation_utils import (filter_reference_by_budget, compute_diversity,
                             pick_best_solution, save_result)

VARIANT             = "v6_full_parallel"
MAX_EXPERTS         = 2
NUM_CANDIDATES      = 2
CRITIC_ROUNDS       = 2
FINAL_CRITIC_ROUNDS = 2
_stats_lock   = threading.Lock()
_shared_stats = {"total_tokens": 0, "total_cost": 0.0, "requests": 0}


# ── Logging helpers ───────────────────────────────────────────────────────────

def _ts():
    """Return current timestamp string for log lines."""
    return datetime.now().strftime("%H:%M:%S")

def _log(msg, tag="v6"):
    """Print a timestamped log line to stdout immediately."""
    print(f"[{_ts()}][{tag}] {msg}", flush=True)

def _log_sep(label="", tag="v6"):
    """Print a section separator."""
    line = "─" * 55
    if label:
        pad = max(0, 55 - len(label) - 2)
        line = f"── {label} " + "─" * pad
    print(f"[{_ts()}][{tag}] {line}", flush=True)

def _elapsed(start):
    """Return human-readable elapsed time string."""
    secs = time.time() - start
    return f"{int(secs // 60)}m {int(secs % 60)}s"


# ── Stats helpers ─────────────────────────────────────────────────────────────

def _accumulate(cb):
    with _stats_lock:
        _shared_stats["total_tokens"] += cb.total_tokens
        _shared_stats["total_cost"]   += cb.total_cost
        _shared_stats["requests"]     += cb.successful_requests


def _reset_stats():
    with _stats_lock:
        _shared_stats["total_tokens"] = 0
        _shared_stats["total_cost"]   = 0.0
        _shared_stats["requests"]     = 0


def _truncate(ref, max_chars=10000):
    if not ref:
        return ""
    truncated = ref[:max_chars] + "\n...[truncated]" if len(ref) > max_chars else ref
    if len(ref) > max_chars:
        _log(f"Reference truncated: {len(ref)} → {max_chars} chars")
    return truncated


# ── Critic-author loop ────────────────────────────────────────────────────────

def _critic_author(ref_info, query, solution, expert_desc, model_name,
                   rounds=1, sol_idx=None, expert_idx=None):
    tag = f"pipeline-{sol_idx}" if sol_idx is not None else "v6"
    current = solution
    for r in range(rounds):
        try:
            _log(f"  critic-author round {r+1}/{rounds}"
                 + (f" [expert {expert_idx}]" if expert_idx is not None else ""), tag)
            fp      = Feedback_Planner(model_name=model_name,
                                       agent_prompt=feedback_planner_agent_prompt)
            fb      = fp.run(ref_info, query, current, expert_description=expert_desc)
            _log(f"  feedback received ({len(fb)} chars)", tag)

            srp     = Self_Refine_Planner(model_name=model_name,
                                          agent_prompt=self_refine_planner_agent_prompt)
            current = srp.run(ref_info, query, current, fb, expert_description=expert_desc)
            _log(f"  refined solution ({len(current)} chars)", tag)
        except Exception as e:
            _log(f"  WARNING critic-author round {r+1} failed: {e}", tag)
    return current


# ── Single solution pipeline ──────────────────────────────────────────────────

def run_pipeline(sol_idx, initial_sol, ref_info, query, base_plan,
                 expert_descriptions, evaluater_descriptions,
                 ind, model_name):
    """Single solution pipeline — runs in its own thread."""
    tag = f"pipeline-{sol_idx}"
    _log_sep(f"Pipeline {sol_idx} START", tag)
    _log(f"Seed solution length: {len(initial_sol)} chars", tag)

    current = initial_sol

    # Expert 0 critic-author
    _log("Stage: Expert-0 critic-author", tag)
    current = _critic_author(ref_info, query, current,
                              expert_descriptions.get(0, ""), model_name,
                              CRITIC_ROUNDS, sol_idx=sol_idx, expert_idx=0)
    _log(f"After expert-0: {len(current)} chars", tag)

    # Expert 1+: generate candidates → rank → critic-author → integrate
    for i in range(1, ind):
        _log(f"Stage: Expert-{i} candidate generation ({NUM_CANDIDATES} candidates)", tag)
        cand_ls = []
        for c in range(NUM_CANDIDATES):
            try:
                _log(f"  Generating candidate {c+1}/{NUM_CANDIDATES}", tag)
                mp        = Multi_Planner(model_name=model_name,
                                          agent_prompt=multi_planner_agent_prompt)
                candidate = mp.run(ref_info, query, expert_descriptions[i],
                                   '\n-'.join(cand_ls), locked_context=current)
                cand_ls.append(candidate)
                _log(f"  Candidate {c+1} ready ({len(candidate)} chars)", tag)
            except Exception as e:
                _log(f"  WARNING candidate {c+1} failed: {e}", tag)
                if cand_ls:
                    break
                raise

        _log(f"Stage: Expert-{i} ranking {len(cand_ls)} candidates", tag)
        try:
            ev     = Evaluater(model_name=model_name, agent_prompt=evaluater_agent_prompt)
            ranked = ev.run(ref_info, query, evaluater_descriptions[i], cand_ls)
            best   = ranked.get(1, cand_ls[0])
            if not isinstance(best, str) or len(best.strip()) < 100:
                best = cand_ls[0]
            _log(f"  Best candidate selected ({len(best)} chars)", tag)
        except Exception as e:
            _log(f"  WARNING ranking failed: {e} — using candidate 0", tag)
            best = cand_ls[0]

        _log(f"Stage: Expert-{i} critic-author on best candidate", tag)
        refined = _critic_author(ref_info, query, best,
                                  expert_descriptions[i], model_name,
                                  CRITIC_ROUNDS, sol_idx=sol_idx, expert_idx=i)

        _log(f"Stage: Expert-{i} integration into current plan", tag)
        try:
            rp      = Refine_Planner(model_name=model_name,
                                     agent_prompt=refine_planner_agent_prompt)
            current = rp.run(ref_info, query, current, expert_descriptions[i], refined)
            _log(f"  Integrated plan ({len(current)} chars)", tag)
        except Exception as e:
            _log(f"  WARNING integration failed: {e} — using refined directly", tag)
            current = refined

    # Final polish
    _log("Stage: Final polish — refine against base plan", tag)
    try:
        rp      = Refine_Planner(model_name=model_name,
                                 agent_prompt=refine_planner_agent_prompt)
        current = rp.run(ref_info, query, base_plan, "Final integration expert", current)
        _log(f"  Post-integration plan ({len(current)} chars)", tag)
    except Exception as e:
        _log(f"  WARNING final refine failed: {e}", tag)

    _log(f"Stage: Final critic-author ({FINAL_CRITIC_ROUNDS} rounds)", tag)
    for r in range(FINAL_CRITIC_ROUNDS):
        current = _critic_author(ref_info, query, current, "", model_name, 1,
                                 sol_idx=sol_idx)

    _log(f"Pipeline {sol_idx} DONE — final plan {len(current)} chars", tag)
    return sol_idx, current


# ── Main run ──────────────────────────────────────────────────────────────────

def run(input_file, output_dir, model_name="gpt-4o-mini", ind=2):
    os.makedirs(output_dir, exist_ok=True)

    _log_sep("v6_full_parallel START")
    _log(f"input_file : {input_file}")
    _log(f"output_dir : {output_dir}")
    _log(f"model      : {model_name}")
    _log(f"ind        : {ind}")

    with open(input_file, "r", encoding="utf-8") as f:
        query_data_list = json.load(f)

    # ── FORCED SINGLE-QUERY MODE ──────────────────────────────────────────────
    # Always process only the first query regardless of how many are in the file
    if isinstance(query_data_list, list):
        query_data_list = [query_data_list[0]]
        _log("SINGLE-QUERY MODE: running query index 0 only")
    else:
        query_data_list = [query_data_list]
        _log("SINGLE-QUERY MODE: input was a plain object, wrapping as single query")

    summary     = []
    batch_start = time.time()

    with get_openai_callback() as cb:
        for idx, query_data in enumerate(tqdm(query_data_list,
                                               desc=f"[{VARIANT}]", unit="query")):

            tag = f"Q{idx+1}"
            _log_sep(f"Query {idx+1}", tag)

            query                 = query_data.get("query", "")
            reference_information = query_data.get("reference_information", "")
            query_dir             = os.path.join(output_dir, f"query_{idx+1}")
            os.makedirs(query_dir, exist_ok=True)

            _log(f"Query text  : {query[:120]}{'...' if len(query)>120 else ''}", tag)
            _log(f"Reference   : {len(reference_information)} chars", tag)
            _log(f"Output dir  : {query_dir}", tag)

            if os.path.exists(os.path.join(query_dir, "result.json")):
                _log("result.json already exists — SKIPPING", tag)
                continue

            _reset_stats()
            tokens_before   = cb.total_tokens
            requests_before = cb.successful_requests
            start           = time.time()

            try:
                # ── Query Processor ──────────────────────────────────────────
                _log_sep("Query Processor", tag)
                qp               = Query_Processor(model_name=model_name)
                structured_query = qp.run(query)
                _log(f"Structured query ({len(structured_query)} chars):", tag)
                _log(f"  {structured_query[:200]}", tag)

                # ── Budget Filter ────────────────────────────────────────────
                _log_sep("Budget Filter", tag)
                filtered_ref = filter_reference_by_budget(reference_information, query)
                _log(f"Reference: {len(reference_information)} → {len(filtered_ref)} chars after budget filter", tag)
                ref_info     = _truncate(filtered_ref)

                # ── Base Planner ─────────────────────────────────────────────
                _log_sep("Base Planner", tag)
                base_plan = None
                base_planner = Planner(model_name=model_name,
                                       agent_prompt=planner_agent_prompt)
                for attempt, max_chars in enumerate([len(filtered_ref), 8000, 6000, 4000]):
                    _log(f"  Attempt {attempt+1}: using {max_chars} chars of reference", tag)
                    result = base_planner.run(filtered_ref[:max_chars], structured_query)
                    if result and "Max Token Length Exceeded" not in result:
                        base_plan = result
                        _log(f"  Base plan ready ({len(base_plan)} chars) on attempt {attempt+1}", tag)
                        break
                    _log(f"  Attempt {attempt+1} failed or exceeded token limit", tag)
                if not base_plan:
                    raise RuntimeError("base_planner failed on all truncation levels")

                # ── Meta Planner 2 (adaptive expert count) ───────────────────
                _log_sep("Meta Planner 2 (expert count)", tag)
                ind_actual = ind
                try:
                    mp2        = Meta_Planner2(model_name=model_name,
                                               agent_prompt=meta_planner_agent_prompt2)
                    no_experts = mp2.run(ref_info, structured_query, base_plan, "")
                    ind_actual = min(ind, int(no_experts))
                    _log(f"Adaptive expert count: {ind_actual} (requested {ind})", tag)
                except Exception as e:
                    _log(f"Meta Planner 2 failed: {e} — using ind={ind_actual}", tag)

                # ── Expert descriptions ──────────────────────────────────────
                _log_sep(f"Building {ind_actual} Expert Descriptions", tag)
                description_ls         = []
                expert_descriptions    = {}
                evaluater_descriptions = {}

                for i in range(ind_actual):
                    _log(f"  Expert {i}: generating description", tag)
                    flag = 0
                    while True:
                        try:
                            mp          = Meta_Planner(model_name=model_name,
                                                       agent_prompt=meta_planner_agent_prompt)
                            description = mp.run(ref_info, structured_query,
                                                 base_plan, '\n-'.join(description_ls))
                            cp          = Check_Planner(model_name=model_name,
                                                        agent_prompt=check_planner_agent_prompt)
                            check       = cp.run(ref_info, structured_query,
                                                 description_ls, description)
                            if 'discard' not in check.lower() or flag > 2:
                                description_ls.append(description)
                                _log(f"  Expert {i}: description accepted (attempt {flag+1})", tag)
                                break
                            _log(f"  Expert {i}: description discarded, retrying (attempt {flag+1})", tag)
                            flag += 1
                        except Exception as e:
                            _log(f"  Expert {i}: API error — {e}, retrying", tag)
                            catch_openai_api_error()
                            continue

                    expert_descriptions[i] = description
                    _log(f"  Expert {i}: description = {description[:100]}...", tag)

                    try:
                        ev_desc = Evaluater_Description(
                            model_name=model_name,
                            agent_prompt=evaluater_description_agent_prompt)
                        evaluater_descriptions[i] = ev_desc.run(
                            ref_info, structured_query, base_plan,
                            expert_description=description)
                        _log(f"  Expert {i}: evaluator description ready", tag)
                    except Exception as e:
                        _log(f"  Expert {i}: evaluator description failed: {e} — using expert desc", tag)
                        evaluater_descriptions[i] = description

                # ── Expert 0 seed candidates ─────────────────────────────────
                _log_sep(f"Expert-0 Seed Candidates ({NUM_CANDIDATES})", tag)
                answers_ls = []
                for attempt in range(NUM_CANDIDATES):
                    try:
                        _log(f"  Generating seed candidate {attempt+1}/{NUM_CANDIDATES}", tag)
                        mp        = Multi_Planner(model_name=model_name,
                                                  agent_prompt=multi_planner_agent_prompt)
                        candidate = mp.run(ref_info, structured_query,
                                           expert_descriptions[0], '\n-'.join(answers_ls))
                        answers_ls.append(candidate)
                        _log(f"  Seed candidate {attempt+1} ready ({len(candidate)} chars)", tag)
                    except Exception as e:
                        _log(f"  Seed candidate {attempt+1} failed: {e}", tag)
                        if answers_ls:
                            break
                        raise

                _log(f"Ranking {len(answers_ls)} seed candidates", tag)
                try:
                    ev     = Evaluater(model_name=model_name,
                                       agent_prompt=evaluater_agent_prompt)
                    ranked = ev.run(ref_info, structured_query,
                                   evaluater_descriptions[0], answers_ls)
                    top_3 = [
                        ranked.get(1, answers_ls[0]),
                        ranked.get(2, answers_ls[1] if len(answers_ls) > 1 else answers_ls[0]),
                        ranked.get(3, answers_ls[2] if len(answers_ls) > 2 else answers_ls[0]),
                    ]
                    top_3 = [t if isinstance(t, str) and len(t.strip()) > 100
                              else answers_ls[min(i, len(answers_ls)-1)]
                              for i, t in enumerate(top_3)]
                    _log(f"Top-3 seeds: {[len(t) for t in top_3]} chars", tag)
                except Exception as e:
                    _log(f"Ranking failed: {e} — using raw candidates as top-3", tag)
                    top_3 = (answers_ls + [answers_ls[0]] * 3)[:3]

                # ── Parallel pipelines ────────────────────────────────────────
                _log_sep("Launching 3 Parallel Pipelines", tag)
                final_solutions = [None, None, None]

                def tracked_pipeline(sol_idx, initial_sol):
                    with get_openai_callback() as pipeline_cb:
                        try:
                            return run_pipeline(
                                sol_idx, initial_sol, ref_info, structured_query,
                                base_plan, expert_descriptions, evaluater_descriptions,
                                ind_actual, model_name
                            )
                        finally:
                            _accumulate(pipeline_cb)
                            _log(f"Pipeline {sol_idx} token usage: {pipeline_cb.total_tokens}", tag)

                with ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {
                        executor.submit(tracked_pipeline, sol_idx, sol): sol_idx
                        for sol_idx, sol in enumerate(top_3)
                    }
                    _log(f"All 3 pipelines submitted, waiting for results...", tag)
                    for future in as_completed(futures):
                        pipeline_id = futures[future]
                        try:
                            sol_idx, result = future.result()
                            final_solutions[sol_idx] = result
                            _log(f"Pipeline {sol_idx} collected ({len(result)} chars) "
                                 f"[{sum(1 for s in final_solutions if s)} / 3 done]", tag)
                        except Exception as e:
                            tqdm.write(f"    Pipeline {pipeline_id} failed: {e}")
                            _log(f"Pipeline {pipeline_id} FAILED: {e}", tag)

                # Fallback for any failed pipeline
                failed = [i for i, s in enumerate(final_solutions) if not s]
                if failed:
                    _log(f"Pipelines {failed} failed — falling back to base_plan", tag)
                final_solutions = [s if s else base_plan for s in final_solutions]

                # ── Stats & save ─────────────────────────────────────────────
                elapsed       = round(time.time() - start, 2)
                seq_tokens    = cb.total_tokens        - tokens_before
                seq_requests  = cb.successful_requests - requests_before
                true_tokens   = seq_tokens  + _shared_stats["total_tokens"]
                true_requests = seq_requests + _shared_stats["requests"]

                _log_sep("Results", tag)
                _log(f"Time          : {_elapsed(start)}", tag)
                _log(f"True tokens   : {true_tokens} "
                     f"(sequential {seq_tokens} + parallel {_shared_stats['total_tokens']})", tag)
                _log(f"True requests : {true_requests}", tag)
                _log(f"Solution lens : {[len(s) for s in final_solutions]} chars", tag)

                diversity = compute_diversity(final_solutions)
                _log(f"Diversity     : {diversity['mean_diversity']:.4f}", tag)

                save_result(
                    query_dir        = query_dir,
                    query            = query,
                    variant          = VARIANT,
                    base_plan        = base_plan,
                    structured_query = structured_query,
                    solutions        = final_solutions,
                    stats            = {
                        "time_seconds":      elapsed,
                        "true_tokens":       true_tokens,
                        "true_requests":     true_requests,
                        "sequential_tokens": seq_tokens,
                        "parallel_tokens":   _shared_stats["total_tokens"],
                    },
                    diversity = diversity,
                )
                _log(f"result.json written to {query_dir}", tag)

                with open(os.path.join(query_dir, "output.txt"), "w", encoding="utf-8") as f:
                    f.write(f"VARIANT: {VARIANT}\n")
                    f.write(f"QUERY:\n{query}\n\n")
                    f.write(f"STRUCTURED QUERY:\n{structured_query}\n\n")
                    f.write(f"BASE PLAN:\n{base_plan}\n\n")
                    f.write("=" * 60 + "\n")
                    for si, sol in enumerate(final_solutions):
                        f.write(f"SOLUTION {si+1}:\n{sol}\n\n{'='*60}\n")
                    f.write(f"DIVERSITY: {diversity['mean_diversity']}\n")
                    f.write(f"TIME:      {int(elapsed//60)}m {int(elapsed%60)}s\n")
                    f.write(f"TOKENS:    {true_tokens}\n")
                _log("output.txt written", tag)

                summary.append({
                    "query_idx": idx+1, "status": "success",
                    "time": elapsed, "tokens": true_tokens,
                    "diversity": diversity["mean_diversity"],
                })
                tqdm.write(f"  [Q{idx+1}] ✓ | {int(elapsed//60)}m{int(elapsed%60)}s "
                           f"| tokens={true_tokens} | diversity={diversity['mean_diversity']}")

            except Exception as e:
                elapsed = round(time.time() - start, 2)
                _log(f"FATAL ERROR: {e}", tag)
                traceback.print_exc()
                with open(os.path.join(query_dir, "FAILED.txt"), "w") as f:
                    f.write(f"ERROR: {e}\n{traceback.format_exc()}")
                summary.append({"query_idx": idx+1, "status": "failed", "error": str(e)})
                tqdm.write(f"  [Q{idx+1}] ✗ {e}")

    _write_summary(output_dir, VARIANT, query_data_list, summary, cb, batch_start)


# ── Summary writer ─────────────────────────────────────────────────────────────

def _write_summary(output_dir, variant, query_data_list, summary, cb, batch_start):
    total_time  = round(time.time() - batch_start, 2)
    diversities = [s["diversity"] for s in summary if "diversity" in s]

    _log_sep("BATCH SUMMARY")
    _log(f"Total time    : {int(total_time//60)}m {int(total_time%60)}s")
    _log(f"Queries done  : {sum(1 for s in summary if s['status']=='success')} / {len(query_data_list)}")
    _log(f"Failed        : {sum(1 for s in summary if s['status']=='failed')}")
    _log(f"Total tokens  : {cb.total_tokens}")
    _log(f"Total cost    : ${cb.total_cost:.4f}")
    _log(f"Mean diversity: {round(sum(diversities)/len(diversities),4) if diversities else 'N/A'}")

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump({
            "variant":              variant,
            "total_queries":        len(query_data_list),
            "completed":            sum(1 for s in summary if s["status"] == "success"),
            "failed":               sum(1 for s in summary if s["status"] == "failed"),
            "mean_diversity":       round(sum(diversities)/len(diversities), 4) if diversities else 0,
            "total_time_seconds":   total_time,
            "total_tokens":         cb.total_tokens,
            "total_requests":       cb.successful_requests,
            "total_cost":           cb.total_cost,
            "per_query":            summary,
        }, f, indent=4)

    print(f"\n[{variant}] DONE | time={int(total_time//60)}m{int(total_time%60)}s "
          f"| tokens={cb.total_tokens} | cost=${cb.total_cost:.4f}")


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_dir", default=f"./ablation/{VARIANT}")
    parser.add_argument("--model_name", default="gpt-4o-mini")
    parser.add_argument("--ind",        type=int, default=2)
    args = parser.parse_args()
    run(args.input_file, args.output_dir, args.model_name, args.ind)