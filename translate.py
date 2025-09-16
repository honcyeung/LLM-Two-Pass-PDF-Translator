# execute other python scripts
# import extract

import json
import os
import requests
from google import genai
from google.genai import types
from google.cloud import aiplatform
from tqdm import tqdm
from dotenv import load_dotenv
import time

EXTRACTED_DATA_PATH = "./extracted_content/data.json"
TRANSLATED_DATA_PATH = "./translated_content/translated_data.json"
GLOSSARY_PATH = "./glossary/glossary.json"
SOURCE_LANG = "Spanish" 
TARGET_LANG = "English" 

load_dotenv()
# LOCATION = os.environ["REGION"]
PROMPTLAYER_API_KEY = os.environ["PROMPTLAYER_API_KEY"]
PROMPT_TEMPLATE_IDENTIFIER = os.environ["PROMPT_TEMPLATE_IDENTIFIER"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_GENERATIVE_MODEL = "gemini-2.5-flash-lite" # JSON Schema only works with Gemini 2.5
TEMPERATURE = 0.2

client = genai.Client(api_key = GEMINI_API_KEY)

def get_prompt():
  
    url = f"https://api.promptlayer.com/prompt-templates/{PROMPT_TEMPLATE_IDENTIFIER}"
    headers = {
        "X-API-KEY": PROMPTLAYER_API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers = headers)
    response.raise_for_status()
    data = response.json()
    
    messages = data.get("prompt_template", {}).get("messages", {})

    system_prompts = []
    for m in messages:
        system_prompt = m.get("content", [])[0].get("text", "")
        if system_prompt:
            system_prompts.append(system_prompt)

    if not system_prompts:
        raise ValueError("System  prompts not found in the PromptLayer response.")

    return system_prompts

def call_llm_model(content, config):

    try:
        response = client.models.generate_content(
            model = GEMINI_GENERATIVE_MODEL,
            contents = content,
            config = config
        )

        return response
    except Exception as e:
        print(f"Error: {e}")

        return

def get_glossary_terms(data_blocks, system_prompts):

    response_schema = types.Schema(
        type = types.Type.OBJECT,
        properties = {
            'glossary_terms': types.Schema(
                type = types.Type.ARRAY,
                items = types.Schema(
                    type = types.Type.OBJECT,
                    properties = {
                        'source_term': types.Schema(type = types.Type.STRING),
                        'target_term': types.Schema(type = types.Type.STRING)
                    },
                    required = ['source_term', 'target_term']
                )
            )
        }
    )

    glossary_data = {}
    for block in tqdm(data_blocks, desc = "Phase 1: Discovering Terms"):
        if not glossary_data:
            glossary_for_prompt = "No approved terms yet."
        else:
            glossary_for_prompt = json.dumps(glossary_data, indent = 2)
    
        # first prompt from the prompt template on prompt layer
        system_prompt = system_prompts[0].format(
            source_lang = SOURCE_LANG,
            target_lang = TARGET_LANG,
            approved_terms_list = glossary_for_prompt
        )

        config = types.GenerateContentConfig(
            system_instruction = system_prompt,
            temperature = TEMPERATURE,
            response_mime_type = "application/json",
            response_schema = response_schema,
        )

        input_text = block.get('content', '')
        ans = call_llm_model(input_text, config)

        try:
            glossary_terms = ans.parsed.get("glossary_terms", [])
            for term in glossary_terms:
                if term["source_term"] != term["target_term"]:
                    glossary_data[term["source_term"]] = term["target_term"]
        except Exception as e:
            print(e)

        time.sleep(4) # rate per minute: 15 for gemini-2.5-flash-lite

    try:
        with open(GLOSSARY_PATH, "w", encoding = "utf-8") as f:
            json.dump(glossary_data, f, indent = 2, ensure_ascii = False)
    except Exception as e:
        print(f"Error: {e}")

def final_translation(data_blocks, system_prompts):

    try:
        with open(GLOSSARY_PATH, "r", encoding = "utf-8") as f:
            complete_glossary_data = f.read()
    except:
        print(f"Error: Glossary file not found at {GLOSSARY_PATH}. Cannot proceed with Phase 2.")
        return

    # second prompt from the prompt template on prompt layer
    system_prompt = system_prompts[1].format(
        source_lang = SOURCE_LANG,
        target_lang = TARGET_LANG,
        glossary = complete_glossary_data
    )

    config = types.GenerateContentConfig(
        system_instruction = system_prompt,
        temperature = TEMPERATURE, 
    )
    
    translated_blocks = []
    for block in tqdm(data_blocks, desc = "Phase 2: Translating Blocks"):
        input_text = f"""**Translate this text:**\n\n---\n\n{block.get('content', '')}\n\n---"""
        ans = call_llm_model(input_text, config)
        try:
            ordered_block = {
                "type": block.get("type"),
                "page": block.get("page"),
                "content": block.get("content"),
                "translated_content": ans.text,
                "bbox": block.get("bbox")
            }
            translated_blocks.append(ordered_block)
        except Exception as e:
            print(f"No block translated: {e}")

        time.sleep(4) # rate per minute: 15 for gemini-2.5-flash-lite

    try:
        with open(TRANSLATED_DATA_PATH, "w", encoding = "utf-8") as f:
            json.dump(translated_blocks, f, indent = 2, ensure_ascii = False)
    except Exception as e:
        print(f"Error saving final translated data: {e}")

try:
    with open(EXTRACTED_DATA_PATH, "r", encoding = "utf-8") as f:
        data_blocks = json.load(f)
except Exception as e:
    raise Exception(f"An error occurred: {e}")

sorted_data_blocks = sorted(data_blocks, key = lambda block: (block['page'], block['bbox'][1]))
system_prompts = get_prompt()
sorted_data_blocks = sorted_data_blocks[86:86+50] # skip title and table of content
get_glossary_terms(sorted_data_blocks, system_prompts)
final_translation(sorted_data_blocks, system_prompts)

