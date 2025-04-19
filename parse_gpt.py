import json
from datetime import datetime
from rich import print
from rich.console import Console
from rich.panel import Panel

console = Console()

def load_conversations(path="conversations.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def format_timestamp(ts):
    dt = datetime.fromtimestamp(ts / 1000)
    return dt.strftime("%Y-%m-%d %H:%M")

def show_thread(thread):
    title = thread.get("title", "Untitled")
    console.rule(f"[bold cyan]{title}[/]")
    messages = thread.get("mapping", {})
    
    sorted_msgs = sorted(
        [msg for msg in messages.values() if msg.get("message")],
        key=lambda x: x["message"].get("create_time", 0)
    )

    for msg in sorted_msgs:
        content = msg["message"].get("content", {}).get("parts", [""])[0]
        role = msg["message"].get("author", {}).get("role", "unknown")
        time = msg["message"].get("create_time", 0)
        ts = format_timestamp(time)
        console.print(Panel(f"[bold]{role.capitalize()}[/] @ {ts}\n{content}", expand=False))

def main():
    data = load_conversations()
    for conv in data:
        show_thread(conv)
        input("\nPress Enter for next thread...\n")

if __name__ == "__main__":
    main()
