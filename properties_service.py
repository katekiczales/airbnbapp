import json, requests
from pathlib import Path
from config_private import OPENROUTER_API_KEY

PROPERTIES_DATA_PATH = Path(__file__).parent / "data" / "properties.json"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"

if not OPENROUTER_API_KEY:
    raise RuntimeError(
        "Please set OPENROUTER_API_KEY in config_private.py"
    )

HEADERS = {"Authorization": f"Bearer {OPENROUTER_API_KEY}",
           "Content-Type": "application/json"}

SYSTEM_PROMPT = """\
You are a data generator for an Airbnb-style app. 
Return ONLY valid JSON (no other text). 
Return a JSON array of 25 property objects. Each object must have:
- property_id (string, unique)
- location (city/town, string)
- type (e.g., house, condo, cabin; a string)
- nightly_price (integer)
- features (array of strings, e.g., ["wifi","pool"])
- tags (array of strings, e.g., ["city","lake","nightlife","pet-friendly"])
- capacity (number of people the property can accommodate, integer)
- lat (the latitude of the location)
- lon (the longitude of the location)
Other constraints:
- Include at least 3 properties with location exactly "Tofino".
- Vary prices, types, features, tags, and capacities to simulate possible real properties.
"""

"""
This module handles all properties data, including generation, storage, and retrieval.
"""

def llm_generate_properties(model: str = MODEL, temperature: float = 0.7) -> list[dict]:
    """
      Generates properties using the LLM OpenRouter's API

      :param model: the model to be used
      :param temperature: the temperature to be used
      :return: the generated properties
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
        ],
        "temperature": temperature,
    }

    response = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code} with details: {response.text}")
    data = response.json()
    content = (data.get("choices") or [{}])[0].get("message", {}).get("content")
    if not content:
        raise RuntimeError(f"Empty response with raw: {data}")
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        s, e = content.find("["), content.rfind("]")
        if s != -1 and e != -1 and e > s:
            try:
                return json.loads(content[s:e+1])
            except json.JSONDecodeError:
                raise RuntimeError(f"Non-JSON content with raw: {content}")
        raise RuntimeError(f"Non-JSON content with raw: {content}")

def save_properties(props: list[dict], path: Path = PROPERTIES_DATA_PATH) -> None:
    """
      Save the properties to the properties.json file

      :param props: the properties to be saved
      :param path: the path to save the files to
      :return: None
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(props, indent=2), encoding="utf-8")

def load_properties_from_disk() -> list[dict]:
    """
    Return a list of properties from disk, or [] if missing/empty/invalid.
    """
    try:
        if not PROPERTIES_DATA_PATH.exists() or PROPERTIES_DATA_PATH.stat().st_size == 0:
            return []
        with PROPERTIES_DATA_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []

def ensure_properties() -> list[dict]:
    """
    Return properties, generating and saving them & if missing

    :return: a list of properties
    """
    props = load_properties_from_disk()
    if not props:
        props = llm_generate_properties()
        save_properties(props)
    return props

if __name__ == "__main__":
    print("Generating properties using OpenRouter")
    properties = llm_generate_properties()
    print(properties)
    save_properties(properties)
    print(f"Wrote {len(properties)} properties to {PROPERTIES_DATA_PATH}")