from langchain.prompts import PromptTemplate


QUERY_PROCESSOR_INSTRUCTION = """
You are a travel query analyst. Your job is to extract all constraints from a user's travel request and rewrite it in a structured format.

User Query: {query}

Step 1 — Extract ALL constraints into a JSON object. Include:
- budget_usd (number or null)
- days (number or null)  
- cities (list of strings)
- origin_city (string or null)
- num_people (number, default 1)
- transportation_allowed (list — infer what's possible if not stated)
- transportation_disallowed (list — explicit rejections like "no self-driving")
- accommodation_type (e.g. "private room", "hotel", "entire home", or null)
- pet_friendly (true/false/null)
- cuisine_preferences (list of strings or empty list)
- special_requirements (list of any other constraints mentioned)

Step 2 — Rewrite the query as structured instructions.

Output EXACTLY in this format, nothing else:

USER REQUEST
-------------
{query}

EXTRACTED CONSTRAINTS (Structured)
----------------------------------
<json object here>

INSTRUCTIONS
------------
Create a detailed travel itinerary that STRICTLY follows ALL constraints above.
Every single decision — transport, accommodation, meals, attractions — must comply with the structured constraints.
dont generate empty fields in the JSON. If a constraint is not mentioned, set it to null or an empty list as appropriate.
make sure to view query aswell if there's something missed by the structured constraints. For example, if the query mentions "I want to visit the Louvre", but the structured constraints only list "attractions: [Eiffel Tower]", then you should also include the Louvre in your plan.
If any conflict arises between the original request and the structured constraints, the structured constraints take priority.
for example if theres "cuisine_preferences": [] if there's no constraints about cuisine preferences. Just dont mention about it either in the structured constraints or the instructions.
All information in the plan must come from the provided reference data only.
"""

query_processor_agent_prompt = PromptTemplate(
    input_variables=["query"],
    template=QUERY_PROCESSOR_INSTRUCTION,
)

CONTEXT_SELECTOR_INSTRUCTION = """You are a travel reference filtering agent.

You will be given a travel query and a block of reference information.
Your ONLY job is to remove lines that would make the plan exceed the budget or violate hard constraints.
Return ONLY the filtered reference text. No explanations, no headers, no commentary.

TRAVEL QUERY:
{query}

REFERENCE INFORMATION:
{reference_information}

---

STEP 1 — Extract constraints from the query (if not stated, use defaults):
- total_budget_usd: (number, or null if not mentioned)
- num_people: (number, default 1)
- num_days: (number)
- num_nights: num_days - 1
- num_destination_cities: (count cities to visit, not origin)
- transport_disallowed: list of exact words like ["self-driving", "taxi"] if mentioned
- accommodation_type_required: e.g. "entire room", "private room", "shared room", or null
- special_requirements: e.g. ["pets allowed", "parties allowed"], or []

STEP 2 — Compute thresholds (only if total_budget_usd is not null):

total_budget = total_budget_usd
transport_reserve = total_budget × 0.25
accommodation_reserve = total_budget × 0.35
meal_reserve = total_budget × 0.30
misc_reserve = total_budget × 0.10

max_hotel_per_night_total = accommodation_reserve / num_nights
max_hotel_per_night_per_person = max_hotel_per_night_total / num_people

meals_per_person_total = meal_reserve / num_people
num_meal_slots = (num_days - 1) × 3 + 2   (first and last day have fewer meals)
max_meal_cost_per_person = meals_per_person_total / num_meal_slots × 2.0

STEP 3 — Filter line by line using EXACTLY these rules:

RULE A — Restaurant lines (lines containing "Average Cost:"):
  - Parse the number after "Average Cost: $"
  - If that number > max_meal_cost_per_person × num_people → DISCARD
  - Otherwise → KEEP

RULE B — Accommodation lines (lines containing "price:"):
  - Parse the number after "price: $" 
  - If that number > max_hotel_per_night_total × 1.2 → DISCARD
  - Otherwise → KEEP

RULE C — Transportation lines:
  - NEVER discard flight lines (lines containing "Flight Number:")
  - If transport_disallowed is not empty AND the line contains any disallowed word → DISCARD
  - Otherwise → KEEP

RULE D — Attraction lines:
  - NEVER discard attraction lines

RULE E — Accommodation type filter (only if accommodation_type_required is not null):
  - If line contains "room type:" and the type does not match accommodation_type_required → DISCARD

RULE F — Special requirements (only if special_requirements is not empty):
  - "pets allowed": if line contains "pets: no" or "pets allowed: no" → DISCARD
  - "parties allowed": if line contains "parties: no" or "parties allowed: no" → DISCARD

STEP 4 — Safety checks (apply AFTER filtering):
  - If total_budget_usd is null → return the original reference information unchanged
  - Per destination city: if fewer than 3 restaurant lines remain → restore the cheapest
    discarded restaurants for that city until 3 remain
  - Per destination city: if 0 accommodation lines remain → restore the single cheapest
    discarded accommodation for that city
  - Never restore a line that was discarded for a non-budget reason (wrong type, disallowed transport)

STEP 5 — Output:
Return the kept lines exactly as they appear in the input, in their original order.
Do not add any text, headers, labels, or blank lines that were not in the original.
"""

context_selector_agent_prompt = PromptTemplate(
    input_variables=["query", "reference_information"],
    template=CONTEXT_SELECTOR_INSTRUCTION,
)


ZEROSHOT_REACT_INSTRUCTION = """Collect information for a query plan using interleaving 'Thought', 'Action', and 'Observation' steps. Ensure you gather valid information related to transportation, dining, attractions, and accommodation. All information should be written in Notebook, which will then be input into the Planner tool. Note that the nested use of tools is prohibited. 'Thought' can reason about the current situation, and 'Action' can have 8 different types:
(1) FlightSearch[Departure City, Destination City, Date]:
Description: A flight information retrieval tool.
Parameters:
Departure City: The city you'll be flying out from.
Destination City: The city you aim to reach.
Date: The date of your travel in YYYY-MM-DD format.
Example: FlightSearch[New York, London, 2022-10-01] would fetch flights from New York to London on October 1, 2022.

(2) GoogleDistanceMatrix[Origin, Destination, Mode]:
Description: Estimate the distance, time and cost between two cities.
Parameters:
Origin: The departure city of your journey.
Destination: The destination city of your journey.
Mode: The method of transportation. Choices include 'self-driving' and 'taxi'.
Example: GoogleDistanceMatrix[Paris, Lyon, self-driving] would provide driving distance, time and cost between Paris and Lyon.

(3) AccommodationSearch[City]:
Description: Discover accommodations in your desired city.
Parameter: City - The name of the city where you're seeking accommodation.
Example: AccommodationSearch[Rome] would present a list of hotel rooms in Rome.

(4) RestaurantSearch[City]:
Description: Explore dining options in a city of your choice.
Parameter: City – The name of the city where you're seeking restaurants.
Example: RestaurantSearch[Tokyo] would show a curated list of restaurants in Tokyo.

(5) AttractionSearch[City]:
Description: Find attractions in a city of your choice.
Parameter: City – The name of the city where you're seeking attractions.
Example: AttractionSearch[London] would return attractions in London.

(6) CitySearch[State]
Description: Find cities in a state of your choice.
Parameter: State – The name of the state where you're seeking cities.
Example: CitySearch[California] would return cities in California.

(7) NotebookWrite[Short Description]
Description: Writes a new data entry into the Notebook tool with a short description. This tool should be used immediately after FlightSearch, AccommodationSearch, AttractionSearch, RestaurantSearch or GoogleDistanceMatrix. Only the data stored in Notebook can be seen by Planner. So you should write all the information you need into Notebook.
Parameters: Short Description - A brief description or label for the stored data. You don't need to write all the information in the description. The data you've searched for will be automatically stored in the Notebook.
Example: NotebookWrite[Flights from Rome to Paris in 2022-02-01] would store the informatrion of flights from Rome to Paris in 2022-02-01 in the Notebook.

(8) Planner[Query]
Description: A smart planning tool that crafts detailed plans based on user input and the information stroed in Notebook.
Parameters: 
Query: The query from user.
Example: Planner[Give me a 3-day trip plan from Seattle to New York] would return a detailed 3-day trip plan.
You should use as many as possible steps to collect engough information to input to the Planner tool. 

Each action only calls one function once. Do not add any description in the action.

Query: {query}{scratchpad}"""

zeroshot_react_agent_prompt = PromptTemplate(
    input_variables=["query", "scratchpad"],
    template=ZEROSHOT_REACT_INSTRUCTION,
)

OVERGEN_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}

Please generate three different Travel Plans at one time for user to choose from. The format can be:
Travel Plan #1:
Travel Plan #2:
Travel Plan #3:

Three Different Candidate Travel Plans:
"""

overgen_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query"],
    template=OVERGEN_PLANNER_INSTRUCTION,
)

SELECT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}

There are three candidate travel plans from a travel plan designer: 
{select}

You can generate the final travel plan based on these three candidate travel plans. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).
Final Travel Plan:
"""

select_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "select"],
    template=SELECT_PLANNER_INSTRUCTION,
)

ALL_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}

This is your answer:
Travel Plan: {old_answer}.

Furthermore, you also invite {n} experts. They also give answers based on their own professional knowledge:
Here are second person descriptions of these experts with their answers:
{select}

Now you can refine your answer with these answers to better meet the query. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example.
Refined Travel Plan: 
"""

all_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "old_answer", "select", "n"],
    template=ALL_PLANNER_INSTRUCTION,
)

PK_PLANNER_INSTRUCTION = """
Given information: {text}
Query: {query}

We invite {n} experts. They give the travel plan based on their own professional knowledge:
Here are second person descriptions of these experts with their answers:
{select}

Now you can should help us select the best travel plan which can meet the query. 
You need to give reasons first and then give the answer with the format: \"Final Answer: Expert #XX\"
"""

pk_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "n", "select"],
    template=PK_PLANNER_INSTRUCTION,
)

# PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).



# STRICT OUTPUT RULES — MUST FOLLOW EXACTLY:
# 1. Every restaurant, hotel, attraction, and flight MUST come EXACTLY from the "Given information"
# 2. Copy names EXACTLY as they appear — no extra text, no prices, no descriptions after the name
# 3. Use EXACTLY this format for each field — no markdown, no bullet points, no bold text:
#    - Transportation: Flight Number: FXXXXXXX, from A to B, Departure Time: HH:MM, Arrival Time: HH:MM
#    - Breakfast/Lunch/Dinner: Restaurant Name, City
#    - Attraction: Place Name, City;Place Name, City
#    - Accommodation: Exact Name from data, City
# 4. Use exactly "-" (single dash) for missing information — nothing else
# 5. Do NOT add prices, ratings, descriptions, or any extra text after names
# 6. Do NOT use markdown formatting — no **, no #, no ```, no bullet points
# 7. Do NOT add "Same as Day X" — repeat the actual name
# 8. Do NOT add budget summaries, notes, or any text after the last day

# COMPLETENESS RULES (CRITICAL):
# 9. You MUST generate ALL days — count the days in the query and fill every single one
# 10. Every day MUST have Breakfast, Lunch, Dinner, Attraction filled with real data or "-"
# 11. On travel days (Day 1 and last day), still include Breakfast and at least one meal
# 12. NEVER skip a day — if query says 7 days, output exactly Day 1 through Day 7

# BUDGET RULES — CRITICAL:
# Before selecting any place, you MUST calculate the total cost mentally:
# - Step 1: Extract the budget from the query (e.g. $900 for 1 person, 3 days)
# - Step 2: Note the per-person costs from Given information:
#   * Transportation: use the cost listed
#   * Accommodation: cost per night × number of nights
#   * Restaurants: average cost per meal × number of people × number of meal slots
#   * Attractions: entry fee × number of people
# - Step 3: Add them up. If total exceeds budget, choose CHEAPER options.
# - Step 4: Prefer restaurants with lower average cost. Prefer cheaper accommodation.
# - Step 5: The final total MUST be under the stated budget. If you cannot fit everything, use "-" for expensive meals rather than exceed budget.

# ACCOMMODATION RULES:
# - Book accommodation for every night EXCEPT the final return day
# - For a 3-day trip: book nights 1 and 2, Day 3 accommodation = "-"
# - For a 5-day trip: book nights 1-4, Day 5 accommodation = "-"
# - NEVER leave intermediate night accommodation as "-"

# MEAL RULES:
# - Every Breakfast, Lunch, Dinner must be a restaurant name from Given information OR exactly "-"
# - Never write "breakfast at home", "grab something", or any free-form suggestion
# - Day 1 Breakfast can be "-" if no restaurant data exists for that morning


# ***** Example *****
# Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
# Travel Plan:
# Day 1:
# Current City: from Ithaca to Charlotte
# Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
# Breakfast: Nagaland's Kitchen, Charlotte
# Attraction: The Charlotte Museum of History, Charlotte
# Lunch: Cafe Maple Street, Charlotte
# Dinner: Bombay Vada Pav, Charlotte
# Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

# Day 2:
# Current City: Charlotte
# Transportation: -
# Breakfast: Olive Tree Cafe, Charlotte
# Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
# Lunch: Birbal Ji Dhaba, Charlotte
# Dinner: Pind Balluchi, Charlotte
# Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

# Day 3:
# Current City: from Charlotte to Ithaca
# Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
# Breakfast: Subway, Charlotte
# Attraction: Books Monument, Charlotte.
# Lunch: Olive Tree Cafe, Charlotte
# Dinner: Kylin Skybar, Charlotte
# Accommodation: -

# ***** Example Ends *****

# Given information: {text}
# Query: {query}
# Travel Plan:
# """
PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}
Travel Plan:
"""


COT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and hotel names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). 

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}
Travel Plan: Let's think step by step. First, """

REACT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and hotel names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). Solve this task by alternating between Thought, Action, and Observation steps. The 'Thought' phase involves reasoning about the current situation. The 'Action' phase can be of two types:
(1) CostEnquiry[Sub Plan]: This function calculates the cost of a detailed sub plan, which you need to input the people number and plan in JSON format. The sub plan should encompass a complete one-day plan. An example will be provided for reference.
(2) Finish[Final Plan]: Use this function to indicate the completion of the task. You must submit a final, complete plan as an argument.
***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
You can call CostEnquiry like CostEnquiry[{{"people_number": 7,"day": 1,"current_city": "from Ithaca to Charlotte","transportation": "Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46","breakfast": "Nagaland's Kitchen, Charlotte","attraction": "The Charlotte Museum of History, Charlotte","lunch": "Cafe Maple Street, Charlotte","dinner": "Bombay Vada Pav, Charlotte","accommodation": "Affordable Spacious Refurbished Room in Bushwick!, Charlotte"}}]
You can call Finish like Finish[Day: 1
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -]
***** Example Ends *****

You must use Finish to indict you have finished the task. And each action only calls one function once.
Given information: {text}
Query: {query}{scratchpad} """

REFLECTION_HEADER = 'You have attempted to give a sub plan before and failed. The following reflection(s) give a suggestion to avoid failing to answer the query in the same way you did previously. Use them to improve your strategy of correctly planning.\n'

REFLECT_INSTRUCTION = """You are an advanced reasoning agent that can improve based on self refection. You will be given a previous reasoning trial in which you were given access to an automatic cost calculation environment, a travel query to give plan and relevant information. Only the selection whose name and city match the given information will be calculated correctly. You were unsuccessful in creating a plan because you used up your set number of reasoning steps. In a few sentences, Diagnose a possible reason for failure and devise a new, concise, high level plan that aims to mitigate the same failure. Use complete sentences.  

Given information: {text}

Previous trial:
Query: {query}{scratchpad}

Reflection:"""

REACT_REFLECT_PLANNER_INSTRUCTION = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and hotel names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with common sense. Attraction visits and meals are expected to be diverse. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B). Solve this task by alternating between Thought, Action, and Observation steps. The 'Thought' phase involves reasoning about the current situation. The 'Action' phase can be of two types:
(1) CostEnquiry[Sub Plan]: This function calculates the cost of a detailed sub plan, which you need to input the people number and plan in JSON format. The sub plan should encompass a complete one-day plan. An example will be provided for reference.
(2) Finish[Final Plan]: Use this function to indicate the completion of the task. You must submit a final, complete plan as an argument.
***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
You can call CostEnquiry like CostEnquiry[{{"people_number": 7,"day": 1,"current_city": "from Ithaca to Charlotte","transportation": "Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46","breakfast": "Nagaland's Kitchen, Charlotte","attraction": "The Charlotte Museum of History, Charlotte","lunch": "Cafe Maple Street, Charlotte","dinner": "Bombay Vada Pav, Charlotte","accommodation": "Affordable Spacious Refurbished Room in Bushwick!, Charlotte"}}]
You can call Finish like Finish[Day: 1
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -]
***** Example Ends *****

{reflections}

You must use Finish to indict you have finished the task. And each action only calls one function once.
Given information: {text}
Query: {query}{scratchpad} """

planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query"],
    template=PLANNER_INSTRUCTION,
)

cot_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query"],
    template=COT_PLANNER_INSTRUCTION,
)

react_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "scratchpad"],
    template=REACT_PLANNER_INSTRUCTION,
)

reflect_prompt = PromptTemplate(
    input_variables=["text", "query", "scratchpad"],
    template=REFLECT_INSTRUCTION,
)

react_reflect_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "reflections", "scratchpad"],
    template=REACT_REFLECT_PLANNER_INSTRUCTION,
)

PLANNER_INSTRUCTION_META = """
You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****
⚠️ IMPORTANT: The expert you describe must work ONLY with the data provided. Do NOT create an expert that draws on real-world knowledge of specific places, restaurants, or hotels. The expert must select from the Given information only

Given information: {text}
Query: {query}

This is your answer:
Travel Plan: {answer}.

Now, you can create and collaborate with multiple experts to improve your plan to better meet the query. Therefore, please describe in as much detail as possible the different skills and focuses you need from multiple experts individually. 
We will provide each expert with the same information and query. However, please note that each profession has its own specialization, so you can assign each expert to just one sub-task to ensure a more refined response. 
We will relay their responses to you in turn, allowing you to reorganize them into a better answer.
Please note that the description should be narrated in the second person, for example: You are a XXX.

You MUST use ONLY the names of restaurants, hotels, attractions, and flights that appear VERBATIM in the "Given information" below.
Do NOT use your own knowledge. Do NOT invent or suggest any place not listed in the Given information.
If a field cannot be filled from the Given information, use exactly "-".
Any name not found in the Given information will cause this plan to FAIL evaluation.

These are the descriptions of the experts you have created before for this task:
{description}

Therefore, please remember you should not repeatedly create the same experts as described above.
Now, you can give the description for a new expert (Please note that only be one, do not give multiple at one time):
"""

meta_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "answer", "description"],
    template=PLANNER_INSTRUCTION_META,
)

PLANNER_INSTRUCTION_META2 = """
You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Given information: {text}
Query: {query}

This is your answer:
Travel Plan: {answer}.

Now, you can create and collaborate with multiple experts to improve your plan to better meet the query. Therefore, please describe in as much detail as possible the different skills and focuses you need from multiple experts individually. 
We will provide each expert with the same information and query. However, please note that each profession has its own specialization, so you can assign each expert to just one sub-task to ensure a more refined response. 
We will relay their responses to you in turn, allowing you to reorganize them into a better answer.
Please note that the description should be narrated in the second person, for example: You are a XXX.

These are the descriptions of the experts you have created before for this task:
{description}

Your response must be a single integer between 2 and 7, representing the number of specialized agents required to handle the travel-planning task. Determine this number by analyzing the user’s query, available database/reference information, constraints,
and the sub-domains involved (e.g., itinerary planning, budgeting, local logistics, compliance, recommendations, risk, optimization). 
Choose the minimal number of experts necessary to collaboratively solve the task. Output only the number—no explanations or text.
"""


meta_planner_agent_prompt2 = PromptTemplate(
    input_variables=["text", "query", "answer", "description"],
    template=PLANNER_INSTRUCTION_META2,
)

PLANNER_INSTRUCTION_MULTI = """
You are a proficient planner...

STRICT OUTPUT RULES — MUST FOLLOW EXACTLY:
1. Every restaurant, hotel, attraction, and flight MUST come EXACTLY from the "Given information"
2. Copy names EXACTLY as they appear — no extra text, no prices, no descriptions after the name
3. Use EXACTLY this format for each field — no markdown, no bullet points, no bold text:
   - Transportation: Flight Number: FXXXXXXX, from A to B, Departure Time: HH:MM, Arrival Time: HH:MM
   - Breakfast/Lunch/Dinner: Restaurant Name, City
   - Attraction: Place Name, City;Place Name, City
   - Accommodation: Exact Name from data, City
4. Use exactly "-" (single dash) for missing information — nothing else
5. Do NOT add prices, ratings, descriptions, or any extra text after names
6. Do NOT use markdown formatting — no **, no #, no ```, no bullet points
7. Do NOT add "Same as Day X" — repeat the actual name
8. Do NOT add budget summaries, notes, or any text after the last day
COMPLETENESS RULES (CRITICAL):
9. You MUST generate ALL days — count the days in the query and fill every single one
10. Every day MUST have Breakfast, Lunch, Dinner, Attraction filled with real data or "-"
11. On travel days (Day 1 and last day), still include Breakfast and at least one meal
12. NEVER skip a day — if query says 7 days, output exactly Day 1 through Day 7
ACCOMMODATION RULES (CRITICAL):
13. Use the SAME accommodation name for ALL consecutive nights in the same city
14. Check minimum_nights field in accommodation data — do NOT book for fewer nights than allowed
15. NEVER write "Same as Day X" — always repeat the exact accommodation name
TRANSPORTATION RULES (CRITICAL):
16. Read the query carefully for transport constraints BEFORE choosing any transport
17. If query says "no self-driving" → NEVER use self-driving on ANY day
18. If query says "no flight" → NEVER use flights on ANY day  
19. Only use transport options that appear in the Given information
BUDGET RULES:
20. Sum all costs: flights + accommodation (price × nights) + meals (average cost × meals)
21. Total cost MUST be less than or equal to the budget stated in the query
22. Choose cheaper options if needed to stay within budget


Previously locked decisions (do not modify these):
{locked_context}

Previously generated answers — your plan MUST be meaningfully different from ALL of these.
Use different restaurants, different transport choices, different accommodations:
{answers_ls}

Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Previously locked decisions (do not modify these):
{locked_context}

 SANDBOX RULE: Use ONLY names from the Given information below. Do NOT use your own knowledge or invent any restaurant, hotel, attraction, or flight. Any name not in the Given information will FAIL.

CRITICAL CONSTRAINT — SANDBOX RULE:
You MUST use ONLY the names of restaurants, hotels, attractions, and flights that appear VERBATIM in the "Given information" below.
Do NOT use your own knowledge. Do NOT invent or suggest any place not listed in the Given information.
If a field cannot be filled from the Given information, use exactly "-".
Any name not found in the Given information will cause this plan to FAIL evaluation.

Please note that: {description}
Given information: {text}
Query: {query}
Travel Plan:

Please remember you should not repeatedly create the same plan as described above.
Now, you can give the description for a new plan (Please note that only be one, do not give multiple plans at one time):
Each plan needs to be diverse from the past ones
"""

# Please remember you should not repeatedly create the same plan as described above.
# Now, you can give the description for a new plan (Please note that only be one, do not give multiple plans at one time):

multi_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "description", "answers_ls", "locked_context"],
    template=PLANNER_INSTRUCTION_MULTI,
)

PLANNER_INSTRUCTION_REFINE = """
You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

STRICT OUTPUT RULES — MUST FOLLOW EXACTLY:
1. Every restaurant, hotel, attraction, and flight MUST come EXACTLY from the "Given information"
2. Copy names EXACTLY as they appear — no extra text, no prices, no descriptions after the name
3. Use EXACTLY this format for each field — no markdown, no bullet points, no bold text:
   - Transportation: Flight Number: FXXXXXXX, from A to B, Departure Time: HH:MM, Arrival Time: HH:MM
   - Breakfast/Lunch/Dinner: Restaurant Name, City
   - Attraction: Place Name, City;Place Name, City
   - Accommodation: Exact Name from data, City
4. Use exactly "-" (single dash) for missing information — nothing else
5. Do NOT add prices, ratings, descriptions, or any extra text after names
6. Do NOT use markdown formatting — no **, no #, no ```, no bullet points
7. Do NOT add "Same as Day X" — repeat the actual name
8. Do NOT add budget summaries, notes, or any text after the last day
9. Keep the same day-by-day format as shown above — do not restructure
10. When refining, preserve all correctly formatted fields — only fix what needs fixing

BUDGET ENFORCEMENT: The refined plan MUST stay within the original budget.
If the expert suggestion exceeds the budget, REJECT it and keep the cheaper original option.
Never upgrade to a more expensive restaurant or hotel if it pushes the total over budget.

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****

Now contribute only your domain-specific improvements:
SANDBOX RULE: Use ONLY names from the Given information below. Do NOT use your own knowledge or invent any restaurant, hotel, attraction, or flight. Any name not in the Given information will FAIL.
⚠️ CRITICAL CONSTRAINT — SANDBOX RULE:
You MUST use ONLY the names of restaurants, hotels, attractions, and flights that appear VERBATIM in the "Given information" below.
Do NOT use your own knowledge. Do NOT invent or suggest any place not listed in the Given information.
If a field cannot be filled from the Given information, use exactly "-".
Any name not found in the Given information will cause this plan to FAIL evaluation.

Given information: {text}
Query: {query}

This is your answer:
Travel Plan: {old_answer}.

Furthermore, you also invite an expert whose description is: \"{description}\"
This expert also give an answer based on his own professional knowledge: {new_answer}.

Now you can refine your answer with this his answer to better meet the query. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example.
Refined Travel Plan: 
"""

# ─────────────────────────────────────────────
# PROMPT 1: Generate the Evaluator's Description
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# PROMPT 1: Evaluator Description Generator
# ─────────────────────────────────────────────
# KEY CHANGE: Instead of creating a narrow domain specialist, we now create
# a constraint compliance auditor that extracts ALL hard constraints from the
# query and uses them as the ranking checklist. The expert_description from
# the upstream pipeline is used only to weight emphasis, not to narrow scope.
 
EVALUATER_DESCRIPTION_INSTRUCTION = """
You are a travel plan evaluation designer. Your job is to define a constraint compliance auditor
that will rank multiple travel plans for a given query.
 
Given information: {text}
Query: {query}
Initial Travel Plan: {answer}
Expert Emphasis (use this to weight criteria, not to narrow scope): {expert_description}
 
TASK:
Extract ALL hard constraints from the query above and define a strict ranking rubric.
Hard constraints include: budget, number of people, transport restrictions, accommodation type,
room rules (e.g. parties allowed), cuisine preferences, city route requirements, and trip duration.
 
Your output must define:
 
1. Constraint Checklist — list every hard constraint found in the query as a binary pass/fail check.
   Format each as: "[constraint name]: [what must be true to pass]"
   Example:
   - Budget: total cost across all days must not exceed $11,000 for 4 people
   - Transport: no self-driving or rental car used at any point
   - Accommodation: must be entire home type, must allow parties
   - Room nights: 6 nights accommodation for 7-day trip
 
2. Ranking Rule — rank answers by number of constraints passed (descending).
   If two answers pass the same number of constraints, apply this tiebreaker:
   prefer the answer that passes the constraints from the expert emphasis domain first,
   then prefer the answer with more complete information (fewer '-' fields).
 
3. Disqualification Rule — if an answer violates a budget or transport constraint,
   it must be ranked last regardless of other scores.
 
Output ONLY the evaluator description in the format above. No extra commentary.
"""
 
evaluater_description_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "answer", "expert_description"],
    template=EVALUATER_DESCRIPTION_INSTRUCTION,
)


EVALUATER_INSTRUCTION = """
You are a strict travel plan constraint compliance ranker.
Your ONLY job is to rank a list of travel plans by how many hard constraints they satisfy.
 
CONSTRAINT COMPLIANCE RUBRIC (from evaluator profile):
{description}
 
Given information: {text}
Query: {query}
 
ANSWERS TO RANK:
{answers_ls}
 
RANKING PROCEDURE — follow exactly:
 
Step 1 — For each Answer, go through EVERY constraint in the rubric above.
         Mark each constraint as PASS or FAIL for that answer.
 
Step 2 — Count total PASSes for each answer.
 
Step 3 — Apply disqualification rule: any answer that fails a budget or
         transport constraint is automatically ranked last.
 
Step 4 — Rank answers by total PASSes (highest = rank 1).
         For ties: apply the tiebreaker rule from the rubric.
 
Step 5 — Output ONLY a Python dictionary.
         Keys = rank (integer, 1 = best)
         Values = the Answer NUMBER only (integer, e.g. 1, 2, 3)
         NO markdown, NO explanation, NO full answer text.
 
CORRECT OUTPUT FORMAT:
{{1: 3, 2: 1, 3: 2}}
Meaning: Answer 3 is best (most constraints passed), Answer 1 is second, Answer 2 is worst.
 
WRONG OUTPUT (do not do this):
{{1: "Answer 1 is best because..."}}
{{1: "Day 1: Current City..."}}
{{"best": 1, "second": 2}}
 
Ranked Output (Python dict only):
"""
 
evaluater_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "description", "answers_ls"],
    template=EVALUATER_INSTRUCTION,
)




refine_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "old_answer", "description", "new_answer"],
    template=PLANNER_INSTRUCTION_REFINE,
)

PLANNER_INSTRUCTION_MERGE = """You are a proficient planner. Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -

***** Example Ends *****
All elements in your plan MUST be derived from the provided data.
No new flights, restaurants, or attractions beyond what experts provided.


Given information: {text}
Query: {query}

==============================
📘 BASE PLAN (from initial planner)
==============================
{old_answer}

==============================
🧠 EXPERT DESCRIPTIONS
==============================
{expert_descriptions}

==============================
📝 EXPERT PLANS
==============================
{expert_plans}

==============================
💬 EXPERT SUB-ANSWERS
==============================
{expert_sub_answers}

==============================
📚 REFERENCE INFORMATION
==============================
{text}

==============================
❓ QUERY
==============================
{query}

==============================
Now produce a single **merged travel plan** that:
- keeps only information supported by the experts or reference data  
- respects commonsense  
- follows the required day-by-day strategy format  
- keeps dates and budget constraints intact  


Now you can refine your answer with this his answer to better meet the query. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example.
"""



merge_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "old_answer", "expert_descriptions", "expert_plans", "expert_sub_answers"],
    template=PLANNER_INSTRUCTION_MERGE,
)

PLANNER_INSTRUCTION_FEEDBACK = """
You are a travel plan critic. Your job is to identify specific, actionable issues in the travel plan below.

{expert_description_block}

CHECK THESE SPECIFIC ISSUES IN ORDER OF PRIORITY:
1. COMPLETENESS: Are all days present? Does each day have all fields filled?
2. MINIMUM NIGHTS: Is the same accommodation used for all nights in each city?
3. TRANSPORTATION: Does the plan violate any transport constraints from the query (no self-driving, no flight)?
4. BUDGET: Does the total cost exceed the budget?
5. SANDBOX: Are all names taken exactly from the Given information?


Given information: {text}
Query: {query}
Travel Plan: {answer}

Provide clear, specific, actionable suggestions. For each issue:
- State WHAT is wrong
- State WHY it is wrong
- State WHAT should be done instead

Suggestion:
"""

feedback_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "answer", "expert_description"],
    template=PLANNER_INSTRUCTION_FEEDBACK,
)

PLANNER_INSTRUCTION_SELF_REFINE = """
You are a proficient travel planner. Your task is to refine the travel plan below based on the critique provided.

{expert_description_block}

STRICT OUTPUT RULES — MUST FOLLOW EXACTLY:
1. Every restaurant, hotel, attraction, and flight MUST come EXACTLY from the "Given information"
2. Copy names EXACTLY as they appear — no extra text, no prices, no descriptions after the name
3. Use EXACTLY this format for each field — no markdown, no bullet points, no bold text:
   - Transportation: Flight Number: FXXXXXXX, from A to B, Departure Time: HH:MM, Arrival Time: HH:MM
   - Breakfast/Lunch/Dinner: Restaurant Name, City
   - Attraction: Place Name, City;Place Name, City
   - Accommodation: Exact Name from data, City
4. Use exactly "-" (single dash) for missing information — nothing else
5. Do NOT add prices, ratings, descriptions, or any extra text after names
6. Do NOT use markdown formatting — no **, no #, no ```, no bullet points
7. Do NOT add "Same as Day X" — repeat the actual name
8. Do NOT add budget summaries, notes, or any text after the last day
9. Keep the same day-by-day format as shown above — do not restructure
10. When refining, preserve all correctly formatted fields — only fix what needs fixing


Based on the provided information and query, please give me a detailed plan, including specifics such as flight numbers (e.g., F0123456), restaurant names, and accommodation names. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example. Additionally, all details should align with commonsense. The symbol '-' indicates that information is unnecessary. For example, in the provided sample, you do not need to plan after returning to the departure city. When you travel to two cities in one day, you should note it in the 'Current City' section as in the example (i.e., from A to B).

***** Example *****
Query: Could you create a travel plan for 7 people from Ithaca to Charlotte spanning 3 days, from March 8th to March 14th, 2022, with a budget of $30,200?
Travel Plan:
Day 1:
Current City: from Ithaca to Charlotte
Transportation: Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46
Breakfast: Nagaland's Kitchen, Charlotte
Attraction: The Charlotte Museum of History, Charlotte
Lunch: Cafe Maple Street, Charlotte
Dinner: Bombay Vada Pav, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 2:
Current City: Charlotte
Transportation: -
Breakfast: Olive Tree Cafe, Charlotte
Attraction: The Mint Museum, Charlotte;Romare Bearden Park, Charlotte.
Lunch: Birbal Ji Dhaba, Charlotte
Dinner: Pind Balluchi, Charlotte
Accommodation: Affordable Spacious Refurbished Room in Bushwick!, Charlotte

Day 3:
Current City: from Charlotte to Ithaca
Transportation: Flight Number: F3786167, from Charlotte to Ithaca, Departure Time: 21:42, Arrival Time: 23:26
Breakfast: Subway, Charlotte
Attraction: Books Monument, Charlotte.
Lunch: Olive Tree Cafe, Charlotte
Dinner: Kylin Skybar, Charlotte
Accommodation: -
***** Example Ends *****

Given information: {text}
Query: {query}

This is your answer:
Travel Plan: {answer}.

However, this answer is not very well. There is the suggestion from an assistant:
Suggestion: {feedback}

Now you can refine your answer with this his suggestion to better meet the query. Note that all the information in your plan should be derived from the provided data. You must adhere to the format given in the example.
Refined Travel Plan: 
"""

self_refine_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "answer", "feedback","expert_description"],
    template=PLANNER_INSTRUCTION_SELF_REFINE,
)

PLANNER_INSTRUCTION_CHECK = """
Given information: {text}
Query: {query}

We employ mulitple experts to answer this query. The following is a second-person introduction to the experts we have hired:
{description_ls}

Now, we will hire a new expert to help better respond to user query. Here is a second person description of the new expert:
{description}

Since hiring new experts takes extra time and money, please evaluate the new expert based on the following two criteria to decide whether they should be retained or not:
1. Based on the new expert's description, determine if they can effectively assist in answering users' questions.
2. The new experts are unique and do not overlap with previously hired experts.
The new expert must meet both of the above two criteria. If any of the criteria are not met, they should be discarded.
Give the reason first and then give the choice. If retaining, please reply with: 'Retain'. If discarding, please reply with: 'Discard'."
"""

check_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "description_ls", "description"],
    template=PLANNER_INSTRUCTION_CHECK,
)

PLANNER_INSTRUCTION_PROMPTREFINE = """
Given information: {text}
Query: {query}
This is the travel plan from a travel-plan AI designer, which description is "You are a proficient planner": 
{answer}.

Please do not refine the plan but refine the description of the travel-plan AI designer to help him better answer the user's query.
Please note that the description should be narrated in the second person, for example: You are a XXX.
Description:
"""

promptrefine_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "answer"],
    template=PLANNER_INSTRUCTION_PROMPTREFINE,
)

PLANNER_INSTRUCTION_SUGGEST = """
{description}

Given information: {text}
Query: {query}
This is the travel plan from a travel plan designer: {answer}.

Please do not refine the plan but give some insightful suggestions for the travel plan designer to help him better meet the user's query.
Suggestion:
"""

suggest_planner_agent_prompt = PromptTemplate(
    input_variables=["text", "query", "answer", "description"],
    template=PLANNER_INSTRUCTION_SUGGEST,
)
