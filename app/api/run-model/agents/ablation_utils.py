"""
ablation_utils.py — shared utilities for all ablation variants.
Provides:
  - filter_reference_by_budget()   : deterministic Python budget filter
  - hybrid_filter()                : LLM constraint extraction + Python filter
  - compute_diversity()            : pairwise Jaccard diversity across solutions
  - pick_best_solution()           : completeness-based solution selector
  - save_result()                  : unified result.json writer
"""

import re, json, os
from difflib import SequenceMatcher


# ─────────────────────────────────────────────
# 1. DETERMINISTIC BUDGET FILTER
# ─────────────────────────────────────────────

def _parse_query_numbers(query):
    budget_match  = re.search(r'\$\s*([\d,]+)', query)
    people_match  = re.search(r'(\d+)\s*(?:person|people|travell?er)', query, re.IGNORECASE)
    days_match    = re.search(r'(\d+)\s*day', query, re.IGNORECASE)
    budget   = int(budget_match.group(1).replace(',', '')) if budget_match else None
    people   = int(people_match.group(1)) if people_match else 1
    days     = int(days_match.group(1))   if days_match   else 3
    return budget, people, days


def filter_reference_by_budget(reference_information, query):
    """
    Deterministic Python budget filter.
    Removes restaurants/hotels that would blow the budget.
    Always keeps flights and attractions.
    Restores cheapest option per city if minimums are not met.
    """
    budget, people, days = _parse_query_numbers(query)
    if not budget:
        return reference_information

    nights     = max(days - 1, 1)
    meal_slots = (days - 1) * 3 + 2          # first/last day have fewer meals
    max_meal   = (budget * 0.30 / people / meal_slots) * 2.0   # per person per meal
    max_hotel  = (budget * 0.35 / nights) * 1.2                # per night total

    lines = reference_information.splitlines()
    kept = []
    discarded_restaurants = {}   # city → [(cost, line)]
    discarded_hotels      = {}   # city → [(cost, line)]

    for line in lines:
        # ── Restaurant filter ──
        m = re.search(r'Average Cost:\s*\$?([\d.]+)', line)
        if m:
            cost = float(m.group(1))
            if cost > max_meal * people:
                city = _extract_city(line)
                discarded_restaurants.setdefault(city, []).append((cost, line))
                continue

        # ── Hotel filter (skip flight lines) ──
        if 'Flight Number' not in line:
            m = re.search(r'price:\s*\$?([\d.]+)', line, re.IGNORECASE)
            if m:
                cost = float(m.group(1))
                if cost > max_hotel:
                    city = _extract_city(line)
                    discarded_hotels.setdefault(city, []).append((cost, line))
                    continue

        kept.append(line)

    # ── Safety: ensure ≥ 3 restaurants per city ──
    city_rest_count = {}
    for line in kept:
        if 'Average Cost:' in line:
            city = _extract_city(line)
            city_rest_count[city] = city_rest_count.get(city, 0) + 1

    for city, discarded in discarded_restaurants.items():
        count = city_rest_count.get(city, 0)
        for cost, line in sorted(discarded, key=lambda x: x[0]):
            if count >= 3:
                break
            kept.append(line)
            count += 1

    # ── Safety: ensure ≥ 1 hotel per city ──
    city_hotel_count = {}
    for line in kept:
        if 'Flight Number' not in line and re.search(r'price:\s*\$', line, re.IGNORECASE):
            city = _extract_city(line)
            city_hotel_count[city] = city_hotel_count.get(city, 0) + 1

    for city, discarded in discarded_hotels.items():
        if city_hotel_count.get(city, 0) == 0 and discarded:
            kept.append(sorted(discarded, key=lambda x: x[0])[0][1])

    return '\n'.join(kept)


def _extract_city(line):
    m = re.search(r',\s*([A-Z][a-zA-Z ]+?)(?:\s*[,\n]|$)', line)
    return m.group(1).strip() if m else 'unknown'


# ─────────────────────────────────────────────
# 2. HYBRID FILTER (LLM extract + Python math)
# ─────────────────────────────────────────────

CONSTRAINT_EXTRACTION_PROMPT = """Extract travel constraints from this query as valid JSON only.
Output ONLY the JSON object, no other text, no markdown.

Query: {query}

Output format:
{{
  "budget_usd": <number or null>,
  "num_people": <number, default 1>,
  "num_days": <number>,
  "transport_disallowed": <list of strings, e.g. ["self-driving", "taxi"]>,
  "accommodation_type": <"entire home" | "private room" | "shared room" | null>,
  "pets_required": <true | false | null>,
  "parties_required": <true | false | null>
}}"""


def hybrid_filter(reference_information, query, model_name, llm_caller):
    """
    Hybrid filter:
      - LLM extracts semantic constraints (transport restrictions, room type, pets, etc.)
      - Python enforces budget thresholds deterministically
    Falls back to pure Python filter if LLM extraction fails.

    llm_caller: callable(prompt, model_name) → str
    """
    # Step 1: LLM extracts structured constraints
    constraints = None
    try:
        prompt = CONSTRAINT_EXTRACTION_PROMPT.format(query=query)
        response = llm_caller(prompt, model_name)
        # Strip markdown fences if present
        response = re.sub(r'```(?:json)?', '', response).strip().strip('`')
        constraints = json.loads(response)
    except Exception:
        pass  # fall through to regex fallback

    if not constraints:
        # Regex fallback
        budget, people, days = _parse_query_numbers(query)
        constraints = {
            "budget_usd": budget,
            "num_people": people,
            "num_days": days,
            "transport_disallowed": [],
            "accommodation_type": None,
            "pets_required": None,
            "parties_required": None,
        }

    budget  = constraints.get("budget_usd")
    people  = constraints.get("num_people", 1) or 1
    days    = constraints.get("num_days", 3)   or 3
    nights  = max(days - 1, 1)
    slots   = (days - 1) * 3 + 2
    transport_banned  = [t.lower() for t in constraints.get("transport_disallowed", [])]
    accom_type        = (constraints.get("accommodation_type") or "").lower()
    pets_required     = constraints.get("pets_required")
    parties_required  = constraints.get("parties_required")

    max_meal  = (budget * 0.30 / people / slots) * 2.0  if budget else None
    max_hotel = (budget * 0.35 / nights) * 1.2           if budget else None

    lines = reference_information.splitlines()
    kept = []
    discarded_restaurants = {}
    discarded_hotels      = {}

    for line in lines:
        line_lower = line.lower()

        # Never discard flights or attractions
        if 'Flight Number' in line:
            kept.append(line)
            continue

        # ── Transport disallowed ──
        if transport_banned and any(t in line_lower for t in transport_banned):
            continue

        # ── Accommodation type filter ──
        if accom_type and 'room type:' in line_lower:
            if accom_type not in line_lower:
                continue

        # ── Pet / party filter ──
        if pets_required and ('pets: no' in line_lower or 'pets allowed: no' in line_lower):
            continue
        if parties_required and 'parties: no' in line_lower:
            continue

        # ── Budget: restaurant ──
        if max_meal is not None:
            m = re.search(r'Average Cost:\s*\$?([\d.]+)', line)
            if m:
                cost = float(m.group(1))
                if cost > max_meal * people:
                    city = _extract_city(line)
                    discarded_restaurants.setdefault(city, []).append((cost, line))
                    continue

        # ── Budget: hotel ──
        if max_hotel is not None:
            m = re.search(r'price:\s*\$?([\d.]+)', line, re.IGNORECASE)
            if m:
                cost = float(m.group(1))
                if cost > max_hotel:
                    city = _extract_city(line)
                    discarded_hotels.setdefault(city, []).append((cost, line))
                    continue

        kept.append(line)

    # Safety minimums
    city_rest  = {}
    city_hotel = {}
    for line in kept:
        if 'Average Cost:' in line:
            c = _extract_city(line)
            city_rest[c] = city_rest.get(c, 0) + 1
        if re.search(r'price:\s*\$', line, re.IGNORECASE) and 'Flight' not in line:
            c = _extract_city(line)
            city_hotel[c] = city_hotel.get(c, 0) + 1

    for city, disc in discarded_restaurants.items():
        count = city_rest.get(city, 0)
        for cost, line in sorted(disc, key=lambda x: x[0]):
            if count >= 3: break
            kept.append(line); count += 1

    for city, disc in discarded_hotels.items():
        if city_hotel.get(city, 0) == 0 and disc:
            kept.append(sorted(disc, key=lambda x: x[0])[0][1])

    return '\n'.join(kept)


# ─────────────────────────────────────────────
# 3. DIVERSITY METRIC
# ─────────────────────────────────────────────

def _extract_plan_entities(plan_text):
    """
    Extract the set of named entities (restaurants, hotels, attractions)
    from a plan text for diversity comparison.
    """
    if not plan_text:
        return set()
    entities = set()
    for field in ['Breakfast', 'Lunch', 'Dinner', 'Accommodation', 'Attraction']:
        for match in re.finditer(rf'{field}:\s*([^\n]+)', plan_text, re.IGNORECASE):
            val = match.group(1).strip()
            if val and val != '-':
                # Split on semicolons for attractions
                for part in val.split(';'):
                    part = part.strip()
                    # Take just the name (before first comma)
                    name = part.split(',')[0].strip()
                    if name and name != '-':
                        entities.add(name.lower())
    return entities


def _jaccard(set_a, set_b):
    """Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def compute_diversity(solutions):
    """
    Compute diversity among a list of plan text strings.
    Returns dict with:
      - pairwise_jaccard_distances: list of (i,j, distance) tuples
      - mean_diversity: float 0-1 (higher = more diverse)
      - min_diversity: float (most similar pair)
      - entity_sets: extracted entity sets per solution
    """
    valid = [(i, s) for i, s in enumerate(solutions) if s and len(s.strip()) > 50]
    if len(valid) < 2:
        return {
            "mean_diversity": 0.0,
            "min_diversity": 0.0,
            "pairwise_jaccard_distances": [],
            "entity_sets": {},
            "note": "fewer than 2 valid solutions — diversity not computable"
        }

    entity_sets = {i: _extract_plan_entities(s) for i, s in valid}
    pairs = []
    for idx_a in range(len(valid)):
        for idx_b in range(idx_a + 1, len(valid)):
            i, _ = valid[idx_a]
            j, _ = valid[idx_b]
            sim = _jaccard(entity_sets[i], entity_sets[j])
            dist = round(1.0 - sim, 4)   # distance = 1 - similarity
            pairs.append((i, j, dist))

    mean_div = round(sum(d for _, _, d in pairs) / len(pairs), 4) if pairs else 0.0
    min_div  = round(min(d for _, _, d in pairs), 4) if pairs else 0.0

    return {
        "mean_diversity": mean_div,
        "min_diversity": min_div,
        "pairwise_jaccard_distances": [
            {"sol_i": i, "sol_j": j, "distance": d} for i, j, d in pairs
        ],
        "entity_sets": {str(i): sorted(list(s)) for i, s in entity_sets.items()},
    }


# ─────────────────────────────────────────────
# 4. BEST SOLUTION SELECTOR
# ─────────────────────────────────────────────

def _count_filled_fields(plan_text):
    """Count non-dash fields in a plan — higher = more complete."""
    if not plan_text:
        return -1
    count = 0
    for field in ['Current City', 'Transportation', 'Breakfast', 'Lunch',
                  'Dinner', 'Attraction', 'Accommodation']:
        for m in re.finditer(rf'{field}:\s*([^\n]+)', plan_text, re.IGNORECASE):
            val = m.group(1).strip()
            if val and val != '-':
                count += 1
    return count


def pick_best_solution(solutions):
    """
    Given a list of plan text strings, return the most complete one.
    Used by prepare_eval.py to select which solution to submit.
    """
    if not solutions:
        return ""
    scored = [(s, _count_filled_fields(s)) for s in solutions if s]
    if not scored:
        return ""
    return max(scored, key=lambda x: x[1])[0]


# ─────────────────────────────────────────────
# 5. UNIFIED RESULT SAVER
# ─────────────────────────────────────────────

def save_result(query_dir, query, variant, base_plan=None,
                structured_query=None, solutions=None,
                stats=None, diversity=None):
    """
    Write a standardised result.json that prepare_eval.py can read.
    solutions: list of plan strings (up to 3)
    """
    solutions = solutions or []
    sol_dict  = {f"solution_{i+1}": s for i, s in enumerate(solutions) if s}

    payload = {
        "query":    query,
        "variant":  variant,
    }
    if structured_query:
        payload["structured_query"] = structured_query
    if base_plan:
        payload["base_plan"] = base_plan
    payload["solutions"] = sol_dict
    if stats:
        payload["stats"] = stats
    if diversity:
        payload["diversity"] = diversity

    with open(os.path.join(query_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)