"""Talk to the Second Look agent from a terminal, with no website involved.

Usage, from the repository root:

    python agent_chat.py
    python agent_chat.py --url http://127.0.0.1:8000

The agent is a service of its own (POST /agent). The website is one way to reach it; this
is another, and a WhatsApp or SMS bot could be a third. Like the website's agent button,
this sends the message you paste to Google or Groq.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "https://second-look-ai.onrender.com"
STEP_NAMES = {
    "check_warning_signs": "Checked for warning signs",
    "search_guidance": "Searched the official guidance",
    "estimate_language": "Estimated the language",
    "spam_signal": "Compared it with older SMS spam",
    "ask_user": "Asked you a question",
    "next_steps": "Looked up the official steps",
    "prepare_report": "Prepared a report for you",
    "finish": "Wrote a summary",
}


def ask_agent(url: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{url.rstrip('/')}/agent",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        return json.loads(response.read().decode("utf-8"))


def show_steps(response: dict) -> None:
    for step in response["trace"]:
        name = STEP_NAMES.get(step["action"], "Asked for something it is not allowed to do")
        outcome = "" if step["outcome"] == "ok" else f"  [{step['outcome'].upper()}]"
        print(f"  {step['step']}. {name}{outcome}  (via {step['provider']})")
        if step.get("reason"):
            print(f"       Why: {step['reason']}")
        print(f"       {step['detail']}")


def show_result(response: dict) -> None:
    print(f"\nAGENT: {response['text']}")
    for step in response["trace"]:
        result = step.get("result") or {}
        if result.get("kind") == "report":
            print("\n--- Report you can use when you call 1930 or file a complaint ---")
            print(result["text"])
            print("--- end of report ---")
        for item in result.get("steps", []):
            action = f"  ->  {item['action']['label']}" if item.get("action") else ""
            print(f"\nOFFICIAL STEP ({item['source']['publisher']}): {item['summary']}{action}")
    print(f"\nNote: {response['notice']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Talk to the Second Look agent from a terminal.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Address of the Second Look backend")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    print("Second Look agent. This sends your message to Google or Groq.")
    message = input("\nPaste the suspicious message and press Enter:\n> ").strip()
    if not message:
        print("No message given.")
        return

    try:
        print("\nThe agent is working...")
        response = ask_agent(args.url, {"message": message})
        show_steps(response)
        if response["status"] == "needs_input":
            print(f"\nAGENT: {response['question']}")
            for number, option in enumerate(response["options"], 1):
                print(f"  {number}. {option['label']}")
            choice = input("Type a number and press Enter: ").strip()
            if not choice.isdigit() or not 1 <= int(choice) <= len(response["options"]):
                print("That is not one of the choices.")
                return
            print("\nThe agent is working...")
            response = ask_agent(args.url, {"message": message, "situation": response["options"][int(choice) - 1]["id"]})
            show_steps(response)
        show_result(response)
    except urllib.error.HTTPError as error:
        print(f"The agent could not answer (HTTP {error.code}). Wait a minute and try again.")
    except (urllib.error.URLError, OSError):
        print("The agent could not be reached. Check the connection and try again.")


if __name__ == "__main__":
    main()
