import pandas as pd
import json
from pathlib import Path

# Load and structure all messages
chat_dir = Path("data/chats")
rows = []

for chat_file in chat_dir.glob("*.json"):
    with open(chat_file, encoding="utf-8") as f:
        convo = json.load(f)
        for msg in convo.get("messages", []):
            rows.append({
                "conversation_id": convo.get("id"),
                "title": convo.get("title"),
                "filename": chat_file.name,
                "timestamp": msg.get("timestamp"),
                "role": msg.get("sender", {}).get("role"),
                "text": msg.get("text"),
            })

# Create DataFrame and filter messages
df = pd.DataFrame(rows)
df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df[~df["text"].astype(str).str.startswith("{")]  # Filter out system/json messages

# Group by date
df["date"] = df["timestamp"].dt.date
grouped = df.groupby("date")

# Build daily summaries
daily_summaries = {}

for date, group in grouped:
    lines = []
    for convo_id, convo in group.groupby("conversation_id"):
        title = convo["title"].iloc[0]
        user_msgs = convo[convo["role"] == "user"]["text"]
        if user_msgs.empty:
            continue
        main_msg = max(user_msgs, key=lambda t: len(str(t)))[:80]
        lines.append(f"- {title}: \"{main_msg}\"")
    
    if lines:
        daily_summaries[date] = "\n".join(lines)

# Save to JSON file
output_path = Path("data/daily_summaries.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({str(k): v for k, v in daily_summaries.items()}, f, indent=2)

print(f"Saved daily summaries to {output_path}")
