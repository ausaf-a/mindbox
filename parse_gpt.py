from datetime import datetime
import json
from pathlib import Path
import re
import logging
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_extract(data: Dict, keys: List[str], default=None) -> Optional[Union[str, Dict]]:
    """Safely extract a value from nested dictionary."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def parse_conversation(convo: Dict) -> Dict:
    """Parse a single conversation into a structured format."""
    conversation = {
        "id": convo.get("conversation_id", "unknown"),
        "title": convo.get("title", "Untitled"),
        "created_at": convo.get("create_time"),
        "updated_at": convo.get("update_time"),
        "messages": []
    }

    messages = convo.get("mapping", {})
    sorted_messages = []
    
    # First, collect all valid messages
    for msg_id, msg in messages.items():
        try:
            message = msg.get("message", {})
            if not message:
                continue

            content_parts = safe_extract(message, ["content", "parts"], [])
            content = content_parts[0] if content_parts else ""
            
            if not content:
                continue

            create_time = message.get("create_time")
            timestamp = datetime.fromtimestamp(create_time).strftime('%Y-%m-%d %H:%M:%S') if create_time else None

            message_obj = {
                "timestamp": timestamp,
                "sender": {
                    "role": safe_extract(message, ["author", "role"], "unknown"),
                    "model": safe_extract(message, ["metadata", "model_slug"])
                },
                "text": content
            }

            sorted_messages.append((create_time or 0, message_obj))

        except (AttributeError, IndexError, TypeError) as e:
            logger.warning(f"Error parsing message {msg_id}: {str(e)}")
            continue

    # Sort messages by timestamp
    sorted_messages.sort(key=lambda x: x[0])
    conversation["messages"] = [msg[1] for msg in sorted_messages]

    return conversation

def save_conversation(conversation: Dict) -> Path:
    """Save a conversation to a JSON file."""
    # Create chats directory
    chats_dir = Path("data/chats")
    chats_dir.mkdir(parents=True, exist_ok=True)

    created_time = conversation.get("created_at")
    created_date = datetime.fromtimestamp(created_time).strftime('%Y-%m-%d') if created_time else "unknown-date"
    
    # Clean title for filename
    title = conversation["title"].lower()
    title = re.sub(r"[^\w\s-]", "", title)  # Keep alphanumeric, space, hyphen
    title = re.sub(r"\s+", "-", title)      # Replace spaces with hyphens
    title = title[:50]                      # Limit length
    
    # Extract a short ID from conversation_id (first 8 characters)
    conversation_id = conversation["id"]
    short_id = conversation_id[:8] if conversation_id != "unknown" else "unknown"
    
    # Create filename with title, date, and short ID
    filename = f"{created_date}-{title}-{short_id}.json"
    output_path = chats_dir / filename
    
    # Handle filename conflicts
    counter = 1
    while output_path.exists():
        filename = f"{created_date}-{title}-{short_id}-{counter}.json"
        output_path = chats_dir / filename
        counter += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)

    return output_path

def main():
    """Main execution function."""
    data_path = Path("data/conversations.json")
    
    if not data_path.exists():
        logger.error(f"File not found: {data_path}")
        return
    
    try:
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Processing {len(data)} conversations")
        
        for i, convo in enumerate(data, 1):
            try:
                parsed = parse_conversation(convo)
                output_path = save_conversation(parsed)
                logger.info(f"[{i}/{len(data)}] Saved to {output_path}")
                
            except Exception as e:
                logger.error(f"Error processing conversation {i}: {str(e)}")
                continue
        
        logger.info("Processing complete")
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {data_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()