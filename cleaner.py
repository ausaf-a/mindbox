import json
from pathlib import Path
import openai
import os
import re
from tqdm import tqdm

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load raw summaries
input_path = Path("data/daily_summaries.json")
with open(input_path, "r", encoding="utf-8") as f:
    raw_summaries = json.load(f)

# Function to call GPT on a smaller chunk
def clean_chunk(chunk):
    raw_json_str = json.dumps(chunk, indent=2)
    prompt = f"""
You are a helpful assistant. A user has shared a JSON object that maps dates to ChatGPT usage summaries.

Your task is to rewrite each summary to make it:
- Short (1–2 sentence max)
- Natural sounding, like a tooltip or journal summary
- Redacted to remove personal/sensitive info (e.g., health, private relationships, mental health). Replace such topics with neutral phrases like "personal matters", "life questions", or "day-to-day tasks".

Output a cleaned JSON object with the same structure: {{date_string: cleaned_summary}}.
Only return valid JSON—no explanation, no commentary.

Here is the data:
{raw_json_str}
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {"role": "system", "content": "You transform user summaries into natural, redacted tooltips."},
            {"role": "user", "content": prompt.strip()}
        ],
        temperature=0.5,
        max_tokens=4096
    )

    content = response.choices[0].message["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"```json\\n(.*?)```", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        else:
            raise ValueError("Could not parse JSON from GPT response")

# Split the data into smaller chunks
chunk_size = 20
keys = list(raw_summaries.keys())
chunks = [
    {k: raw_summaries[k] for k in keys[i:i + chunk_size]}
    for i in range(0, len(keys), chunk_size)
]

# Process each chunk and combine the results
cleaned_all = {}
for i, chunk in enumerate(tqdm(chunks, desc="Cleaning chunks")):
    cleaned_chunk = clean_chunk(chunk)
    cleaned_all.update(cleaned_chunk)

# Save final output
output_path = Path("data/daily_summaries_clean.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cleaned_all, f, indent=2)

print(f"Saved cleaned summaries to {output_path}")
