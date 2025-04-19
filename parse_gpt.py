import json, os

def split_conversations(filepath="data/conversations.json", out_dir="split_chats"):
    os.makedirs(out_dir, exist_ok=True)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)  # No need to access ["conversations"]

    for i, convo in enumerate(data):
        title = convo.get("title", f"Untitled_{i}")
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{i:03d}_{safe_title[:40].replace(' ', '_')}.json"

        messages = convo.get("mapping", {})
        parsed = []
        for msg in messages.values():
            try:
                message = msg.get("message", {})
                if not message:  # Skip if message is None or empty
                    continue
                    
                content = message.get("content", {}).get("parts", [""])[0]
                role = message.get("author", {}).get("role", "unknown")
                if content: 
                    parsed.append({"role": role, "text": content})
            except (AttributeError, IndexError, TypeError):
                continue  # Skip malformed messages

        with open(os.path.join(out_dir, filename), "w", encoding="utf-8") as out_f:
            json.dump(parsed, out_f, indent=2)

    print(f"✅ Split {len(data)} conversations into files at {out_dir}/")

split_conversations()