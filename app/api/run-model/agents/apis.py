import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))
from langchain.prompts import PromptTemplate
#from prompts import planner_agent_prompt, cot_planner_agent_prompt, react_planner_agent_prompt,reflect_prompt,react_reflect_planner_agent_prompt, REFLECTION_HEADER
from prompts import *
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.llms.base import BaseLLM
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)
import json
import tiktoken
import re
import openai
import time
from enum import Enum
from typing import List, Union, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
import argparse
import openai

import importlib.metadata
if not hasattr(importlib.metadata, "packages_distributions"):
    importlib.metadata.packages_distributions = lambda: {}

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']

import google.generativeai as genai
import os
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
# print(genai.GenerativeModel("gemini-2.5-flash").generate_content("Hello Gemini!").text)

def catch_openai_api_error():
    error = sys.exc_info()[0]
    if error == openai.error.APIConnectionError:
        print("APIConnectionError")
    elif error == openai.error.RateLimitError:
        print("RateLimitError")
        time.sleep(60)
    elif error == openai.error.APIError:
        print("APIError")
    elif error == openai.error.AuthenticationError:
        print("AuthenticationError")
    else:
        print("API error:", error)


class ReflexionStrategy(Enum):
    """
    REFLEXION: Apply reflexion to the next reasoning trace 
    """
    REFLEXION = 'reflexion'
class Refine_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = refine_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, old_answer, description, new_answer, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, old_answer, description, new_answer))
        # print(self._build_agent_prompt(text, query, old_answer, description, new_answer))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, old_answer, description, new_answer)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, old_answer, description, new_answer))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, old_answer, description, new_answer))]).content
                        return answer
                    except:
                        continue


    def _build_agent_prompt(self, text, query, old_answer, description, new_answer) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            old_answer=old_answer,
            description=description,
            new_answer=new_answer
            )

class Multi_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, description, answers_ls, locked_context="", log_file=None) -> str:
        if self.model_name in ['gemini', 'ollama']:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, description, answers_ls, locked_context)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, description, answers_ls, locked_context))) > 12000:
                return 'Max Token Length Exceeded.'
            while True:
                try:
                    return self.llm([HumanMessage(content=self._build_agent_prompt(text, query, description, answers_ls, locked_context))]).content
                except:
                    continue

    def _build_agent_prompt(self, text, query, description, answers_ls, locked_context="") -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            description=description,
            answers_ls=answers_ls,
            locked_context=locked_context
        )
    
class Evaluater_Description:
    def __init__(self,
                 agent_prompt: PromptTemplate = evaluater_description_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106') -> None:

        self.agent_prompt = agent_prompt
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8301/v1", model_name="gpt-3.5-turbo")
        elif model_name in ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8501/v1", model_name="gpt-3.5-turbo")
        elif model_name in ['mixtral']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8501/v1", model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="ollama", openai_api_base="http://localhost:11434/v1", model_name=os.environ.get("OLLAMA_MODEL", "llama3"))
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)

        print(f"Evaluater_Description {model_name} loaded.")

    def run(self, text, query, answer, expert_description="", log_file=None) -> str:
        if self.model_name in ['gemini', 'ollama']:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, expert_description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, expert_description))) > 12000:
                return 'Max Token Length Exceeded.'
            while True:
                try:
                    return self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, expert_description))]).content
                except:
                    continue

    def _build_agent_prompt(self, text, query, answer, expert_description="") -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            answer=answer,
            expert_description=expert_description
        )

class Evaluater:
    def __init__(self,
                 agent_prompt: PromptTemplate = evaluater_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106') -> None:

        self.agent_prompt = agent_prompt
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8301/v1", model_name="gpt-3.5-turbo")
        elif model_name in ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8501/v1", model_name="gpt-3.5-turbo")
        elif model_name in ['mixtral']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8501/v1", model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="ollama", openai_api_base="http://localhost:11434/v1", model_name=os.environ.get("OLLAMA_MODEL", "llama3"))
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)

        print(f"Evaluater {model_name} loaded.")

    def run(self, text, query, description, answers_ls, log_file=None) -> dict:

        prompt = self._build_agent_prompt(text, query, description, answers_ls)

        if self.model_name in ['gemini', 'ollama']:
            raw = str(self.llm.invoke(prompt).content)
        else:
            if len(self.enc.encode(prompt)) > 12000:
                return {i+1: ans for i, ans in enumerate(answers_ls)}
            while True:
                try:
                    raw = self.llm([HumanMessage(content=prompt)]).content
                    break
                except:
                    continue

        print(f"[EVALUATER RAW OUTPUT]:\n{repr(raw)}")

        # Strip markdown fences
        cleaned = raw.strip()
        cleaned = re.sub(r'^```(?:python|json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = cleaned.strip()

        def map_to_full_answers(rank_dict):
            """Convert {rank: answer_number} → {rank: full_answer_text}"""
            result = {}
            for rank, ans_num in rank_dict.items():
                try:
                    # ans_num is 1-based index
                    idx = int(ans_num) - 1
                    if 0 <= idx < len(answers_ls):
                        result[int(rank)] = answers_ls[idx]
                        print(f"[EVALUATER] Rank {rank} → Answer {ans_num} (idx {idx})")
                    else:
                        result[int(rank)] = answers_ls[0]
                        print(f"[EVALUATER] Rank {rank} → Answer {ans_num} OUT OF RANGE — fallback to 0")
                except Exception as e:
                    print(f"[EVALUATER] Failed to map rank {rank} ans_num {ans_num}: {e}")
                    result[int(rank)] = answers_ls[0]
            return result

        # Strategy 1: direct eval
        try:
            result = eval(cleaned)
            if isinstance(result, dict) and len(result) > 0:
                print(f"[EVALUATER] Parsed via eval — raw ranks: {result}")
                return map_to_full_answers(result)
        except Exception as e:
            print(f"[EVALUATER] eval failed: {e}")

        # Strategy 2: regex extract dict
        try:
            match = re.search(r'\{[^{}]+\}', cleaned, re.DOTALL)
            if match:
                result = eval(match.group())
                if isinstance(result, dict) and len(result) > 0:
                    print(f"[EVALUATER] Parsed via regex — raw ranks: {result}")
                    return map_to_full_answers(result)
        except Exception as e:
            print(f"[EVALUATER] regex parse failed: {e}")

        # Strategy 3: json parse
        try:
            result = json.loads(cleaned)
            if isinstance(result, dict) and len(result) > 0:
                result = {int(k): v for k, v in result.items()}
                print(f"[EVALUATER] Parsed via json — raw ranks: {result}")
                return map_to_full_answers(result)
        except Exception as e:
            print(f"[EVALUATER] json parse failed: {e}")

        # All failed
        print(f"[EVALUATER] ALL STRATEGIES FAILED — raw:\n{raw}")
        return {i+1: ans for i, ans in enumerate(answers_ls)}
    
    def _build_agent_prompt(self, text, query, description, answers_ls) -> str:
        formatted_answers = "\n\n".join([
            f"Answer {i+1}:\n{ans.replace('{', '{{').replace('}', '}}')}"
            for i, ans in enumerate(answers_ls)
        ])

        return self.agent_prompt.format(
            text=text,
            query=query,
            description=description,
            answers_ls=formatted_answers
        )
class Query_Processor:
    def __init__(self,
                 agent_prompt: PromptTemplate = query_processor_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106') -> None:

        self.agent_prompt = agent_prompt
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8301/v1", model_name="gpt-3.5-turbo")
        elif model_name in ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8501/v1", model_name="gpt-3.5-turbo")
        elif model_name in ['mixtral']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="EMPTY", openai_api_base="http://localhost:8501/v1", model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096, openai_api_key="ollama", openai_api_base="http://localhost:11434/v1", model_name=os.environ.get("OLLAMA_MODEL", "llama3"))
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-2.5-flash", google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)

        print(f"Query_Processor {model_name} loaded.")

    def run(self, query, log_file=None) -> str:
        if self.model_name in ['gemini', 'ollama']:
            return str(self.llm.invoke(self._build_agent_prompt(query)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(query))) > 12000:
                return query  # fallback to original query if too long
            while True:
                try:
                    return self.llm([HumanMessage(content=self._build_agent_prompt(query))]).content
                except:
                    continue

    def _build_agent_prompt(self, query) -> str:
        return self.agent_prompt.format(query=query)


class Context_Selector:
    """
    Constraint-Aware Context Selection Agent.
 
    Drop-in replacement for filter_reference_by_budget().
    Takes the same inputs (reference_information, query) and returns
    a filtered reference string — but uses the LLM to reason about
    budget thresholds, transport constraints, accommodation type,
    and special requirements instead of hardcoded regex rules.
    """
 
    def __init__(self,
                 agent_prompt: PromptTemplate = context_selector_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106') -> None:
 
        self.agent_prompt = agent_prompt
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
 
        if model_name in ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096,
                                  openai_api_key="EMPTY",
                                  openai_api_base="http://localhost:8301/v1",
                                  model_name="gpt-3.5-turbo")
        elif model_name in ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096,
                                  openai_api_key="EMPTY",
                                  openai_api_base="http://localhost:8501/v1",
                                  model_name="gpt-3.5-turbo")
        elif model_name in ['mixtral']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096,
                                  openai_api_key="EMPTY",
                                  openai_api_base="http://localhost:8501/v1",
                                  model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(temperature=0, max_tokens=4096,
                                  openai_api_key="ollama",
                                  openai_api_base="http://localhost:11434/v1",
                                  model_name=os.environ.get("OLLAMA_MODEL", "llama3"))
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,
                                              model="gemini-2.5-flash",
                                              google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0,
                                  max_tokens=4096,
                                  openai_api_key=OPENAI_API_KEY)
 
        print(f"Context_Selector {model_name} loaded.")
 
    def run(self, reference_information: str, query: str) -> str:
        """
        Same signature pattern as filter_reference_by_budget(reference_information, query).
        Returns filtered reference_information string.
        Falls back to original if model fails or output is suspiciously short.
        """
        prompt = self._build_agent_prompt(reference_information, query)
 
        # If no budget in query, skip entirely — matches original function behavior
        import re
        if not re.search(r'\$\s*[\d,]+', query):
            return reference_information
 
        if self.model_name in ['gemini', 'ollama']:
            try:
                result = str(self.llm.invoke(prompt).content).strip()
                return result if len(result) > 200 else reference_information
            except Exception:
                return reference_information
 
        # Token guard — truncate reference if prompt is too large
        if len(self.enc.encode(prompt)) > 12000:
            truncated = reference_information[:6000]
            prompt = self._build_agent_prompt(truncated, query)
            if len(self.enc.encode(prompt)) > 12000:
                return reference_information  # give up gracefully
 
        while True:
            try:
                result = self.llm([HumanMessage(content=prompt)]).content.strip()
                return result if len(result) > 200 else reference_information
            except Exception:
                continue
 
    def _build_agent_prompt(self, reference_information: str, query: str) -> str:
        return self.agent_prompt.format(
            query=query,
            reference_information=reference_information
        )    

class Meta_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt2,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, description, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, answer, description))
        # print(self._build_agent_prompt(text, query, answer, description))
        if self.model_name in ['gemini',"ollama","openai"]:         
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, description))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        #import pdb
                        #pdb.set_trace()
                        #print(self._build_agent_prompt(text, query, answer, description))
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, description))]).content
                        return answer
                    except:
                        continue

    def _build_agent_prompt(self, text, query, answer, description) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            answer=answer,
            description=description
            )



class Meta_Planner2:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt2,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, description, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, answer, description))
        # print(self._build_agent_prompt(text, query, answer, description))
        if self.model_name in ['gemini',"ollama","openai"]:
            
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, description))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        #import pdb
                        #pdb.set_trace()
                        #print(self._build_agent_prompt(text, query, answer, description))
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, description))]).content
                        return answer
                    except:
                        continue

    def _build_agent_prompt(self, text, query, answer, description) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            answer=answer,
            description=description
            )
    

class Feedback_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")

        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )       
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0, model=model_name, google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, expert_description="", log_file=None) -> str:
        if self.model_name in ['gemini', 'ollama']:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, expert_description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, expert_description))) > 12000:
                return 'Max Token Length Exceeded.'
            while True:
                try:
                    return self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, expert_description))]).content
                except:
                    continue
    def _build_feedback_prompt_block(self, expert_description=""):
        if expert_description.strip():
            return f"""You are acting as a DOMAIN SPECIALIST with the following expertise:
    \"{expert_description}\"

    Your critique must be strictly limited to your domain of expertise above.
    - Only flag issues that fall within your domain
    - Do NOT comment on budget, logistics, or anything outside your role
    - Be precise — point to specific days, meals, routes, or choices that violate your domain standards
    - Rank your issues from most critical to least critical within your domain
    - Do not rewrite the plan — only identify what needs fixing and why"""
        else:
            return """You are acting as a SENIOR TRAVEL PLAN REVIEWER doing a final holistic review.
    Review the ENTIRE plan across all dimensions:
    - You should not change the plan much as the plan has already been refined by domain experts. Your role is to identify any remaining issues that slipped through the cracks.
    - Budget: Does total cost fit within the stated budget? Are choices cost-efficient?
    - Logistics: Are routes logical? Are travel times realistic? Is the sequence of cities sensible?
    - Meals: Is there variety across cuisines? Are meals present for each day? Do restaurants match stated preferences?
    - Accommodation: Are all stays pet-friendly? Are they private rooms as requested? Is pricing reasonable?
    - Pet needs: Are travel durations manageable for pets? Are rest stops accounted for on long drives?
    - Overall coherence: Does the plan flow well day by day? Are there gaps or contradictions?    Flag the most impactful issues first. Be specific — reference exact days, restaurants, or routes."""


    def _build_agent_prompt(self, text, query, answer, expert_description="") -> str:
        return self.agent_prompt.format(
            text=text, query=query, answer=answer,
            expert_description_block=self._build_feedback_prompt_block(expert_description)
        )
    
class Self_Refine_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0, model=model_name, google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer,feedback, expert_description="", log_file=None) -> str:
        if self.model_name in ['gemini', 'ollama']:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer,feedback, expert_description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, feedback, expert_description))) > 12000:
                return 'Max Token Length Exceeded.'
            while True:
                try:
                    return self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, feedback, expert_description))]).content
                except:
                    continue

    def _build_self_refine_prompt_block(self,expert_description=""):
        if expert_description.strip():
            return f"""You are refining this plan as a DOMAIN SPECIALIST with the following expertise:
    \"{expert_description}\"

    Refinement rules:
    - ONLY apply changes that address issues within your domain of expertise
    - DO NOT modify transportation, budget, or any section outside your domain unless the critique explicitly mentions it
    - DO NOT remove or replace content that is unrelated to your domain — preserve everything else exactly as-is
    - For each change you make, it must directly correspond to a point raised in the critique
    - If a critique point is outside your domain, skip it — do not address it
    - Keep the same day-by-day format as the original plan"""
        else:
            return """You are doing a FINAL HOLISTIC REFINEMENT of this travel plan.

    Refinement rules:
    -You arent allowed to change much of the plan. You can only make changes that directly address the issues raised in the critique.
    - Address ALL issues raised in the critique across every dimension
    - Fix budget overruns by substituting cheaper alternatives from the provided data
    - Fix routing issues by reordering cities or changing transport modes
    - Fill any missing meals, accommodations, or attractions using the provided reference data
    - Ensure ALL accommodations are pet-friendly and private rooms as required
    - Ensure cuisine variety matches the traveler's stated preferences
    - Every piece of information in the refined plan must come from the provided reference data
    - Keep the same day-by-day format as the original — do not change the structure, only the content
    - Do not add commentary, notes, or suggestions — output only the refined travel plan"""
        
    def _build_agent_prompt(self, text, query, answer, feedback, expert_description="") -> str:
        return self.agent_prompt.format(
            text=text, query=query, answer=answer, feedback=feedback,
            expert_description_block= self._build_self_refine_prompt_block(expert_description)
        )
class Merge_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = merge_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
            
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, old_answer, expert_descriptions, expert_plans,expert_sub_answers, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, old_answer, expert_descriptions, expert_plans,expert_sub_answers))
        # print(self._build_agent_prompt(text, query, old_answer, description, new_answer))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, old_answer, expert_descriptions, expert_plans, expert_sub_answers)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, old_answer, expert_descriptions, expert_plans,expert_sub_answers))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, old_answer, expert_descriptions, expert_plans,expert_sub_answers))]).content
                        return answer
                    except:
                        continue


    # def _build_agent_prompt(self, text, query, old_answer, description, new_answer) -> str:
    #     return self.agent_prompt.format(
    #         text=text,
    #         query=query,
    #         old_answer=old_answer,
    #         description=description,
    #         new_answer=new_answer
    #         )    
    
    def _build_agent_prompt(self, text, query, old_answer,expert_descriptions,expert_plans,expert_sub_answers) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            old_answer=old_answer,
            expert_descriptions="\n".join(expert_descriptions),
            expert_plans="\n".join([str(p) for p in expert_plans]),
            expert_sub_answers="\n".join([str(s) for s in expert_sub_answers])
            )
        
class Check_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
            
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, description_ls, description, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, description_ls, description))
        # print(self._build_agent_prompt(text, query, description_ls, description))
        if self.model_name in ['gemini',"ollama","openai"]:
            
            return str(self.llm.invoke(self._build_agent_prompt(text, query, description_ls, description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, description_ls, description))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        #import pdb
                        #pdb.set_trace()
                        #print(self._build_agent_prompt(text, query, description_ls, description))
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, description_ls, description))]).content
                        #print(answer)
                        return answer
                    except:
                        continue

    def _build_agent_prompt(self, text, query, description_ls, description) -> str:
        temp = []
        for i in range(len(description_ls)):
            temp.append(f"{i+1} Expert: {description_ls[i]}")
        return self.agent_prompt.format(
            text=text,
            query=query,
            description_ls='\n'.join(temp),
            description=description
            )
class SPP_Feedback_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0, model=model_name, google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, persona, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, answer, persona))
        # print(self._build_agent_prompt(text, query, answer, persona))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, persona)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, persona))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, persona))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, answer, persona) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            persona=persona,
            answer=answer)
class SPP_Self_Refine_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
            
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, suggestion, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, answer, suggestion))
        # print(self._build_agent_prompt(text, query, answer, suggestion))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, suggestion)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, suggestion))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, suggestion))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, answer, suggestion) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            answer=answer,
            suggestion=suggestion)
class SPP_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, suggestion, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, suggestion))
        # print(self._build_agent_prompt(text, query, suggestion))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, suggestion)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, suggestion))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, suggestion))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, suggestion) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            suggestion=suggestion)
class PK_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, n, select, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, n, select))
        # print(self._build_agent_prompt(text, query, n, select))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, n, select)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, n, select))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, n, select))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, n, select) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            select=select,
            n = n
            )       
                     
class Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query))
        # print(self._build_agent_prompt(text, query))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query)
    
class All_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
            
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, old_answer, select, n, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, old_answer, select, n))
        # print(self._build_agent_prompt(text, query, old_answer, select, n))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, old_answer, select, n)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, old_answer, select, n))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, old_answer, select, n))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, old_answer, select, n) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            select=select,
            n = n,
            old_answer = old_answer
            )    


class Select_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, select, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, select))
        # print(self._build_agent_prompt(text, query, select))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, select)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, select))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, select))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, select) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            select=select
            )        
class Overgen_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query))
        # print(self._build_agent_prompt(text, query))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query
            )    


    
class Suggestion_Generator:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, persona, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, persona))
        # print(self._build_agent_prompt(text, query, persona))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, persona)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, persona))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, persona))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, persona) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            persona=persona)    

class PromptRefine_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        elif model_name in ['gpt-4-1106-preview']:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)
        elif model_name in ['gpt-3.5-turbo-1106']:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, answer))
        # print(self._build_agent_prompt(text, query, answer))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, text, query, answer) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            answer=answer)

class Suggest_Planner:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = meta_planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        elif model_name in ['gpt-4-1106-preview']:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)
        elif model_name in ['gpt-3.5-turbo-1106']:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, text, query, answer, description, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(text, query, answer, description))
        # print(self._build_agent_prompt(text, query, answer, description))
        if self.model_name in ['gemini',"ollama","openai"]:
            
            return str(self.llm.invoke(self._build_agent_prompt(text, query, answer, description)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(text, query, answer, description))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        #import pdb
                        #pdb.set_trace()
                        #print(self._build_agent_prompt(text, query, answer, description))
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(text, query, answer, description))]).content
                        return answer
                    except:
                        continue

    def _build_agent_prompt(self, text, query, answer, description) -> str:
        return self.agent_prompt.format(
            text=text,
            query=query,
            answer=answer,
            description=description
            )

class Persona_Generator:
    def __init__(self,
                 # args,
                 agent_prompt: PromptTemplate = planner_agent_prompt,
                 model_name: str = 'gpt-3.5-turbo-1106',
                 ) -> None:

        self.agent_prompt = agent_prompt
        self.scratchpad: str = ''
        self.model_name = model_name
        self.enc = tiktoken.encoding_for_model("gpt-3.5-turbo")

        if model_name in  ['mistral-7B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8301/v1", 
                     model_name="gpt-3.5-turbo")
        
        elif model_name in  ['ChatGLM3-6B-32K']:
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="gpt-3.5-turbo")
            
        elif model_name in ['mixtral']:
            self.max_token_length = 30000
            self.llm = ChatOpenAI(temperature=0,
                     max_tokens=4096,
                     openai_api_key="EMPTY", 
                     openai_api_base="http://localhost:8501/v1", 
                     model_name="YOUR/MODEL/PATH")
        
        elif model_name in ['ollama']:
            self.llm = ChatOpenAI(
                temperature=0,
                max_tokens=4096,
                openai_api_key="ollama",
                openai_api_base="http://localhost:11434/v1",
                model_name=os.environ.get("OLLAMA_MODEL", "llama3")
            )
                
            
        elif model_name in ['gemini']:
            self.llm = ChatGoogleGenerativeAI(temperature=0,model="gemini-2.5-flash",google_api_key=GOOGLE_API_KEY)
        else:
            self.llm = ChatOpenAI(model_name=model_name, temperature=0, max_tokens=4096, openai_api_key=OPENAI_API_KEY)


        print(f"PlannerAgent {model_name} loaded.")

    def run(self, query, log_file=None) -> str:
        if log_file:
            log_file.write('\n---------------Planner\n'+self._build_agent_prompt(query))
        # print(self._build_agent_prompt(query))
        if self.model_name in ['gemini',"ollama","openai"]:
            return str(self.llm.invoke(self._build_agent_prompt(query)).content)
        else:
            if len(self.enc.encode(self._build_agent_prompt(query))) > 12000:
                return 'Max Token Length Exceeded.'
            else:
                while True:
                    try:
                        answer = self.llm([HumanMessage(content=self._build_agent_prompt(query))]).content
                        return answer
                    except:
                        continue
                

    def _build_agent_prompt(self, query) -> str:
        return self.agent_prompt.format(
            query=query)


