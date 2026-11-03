"""Talk to Jarvis by typing, from a terminal. Handy for testing without the app.

    python chat.py                                (server on this laptop, token from HOME_API_TOKEN)
    python chat.py --server http://192.168.1.20:8000
"""
import argparse
import json
import os
import urllib.error
import urllib.request


def ask(server: str, token: str, text: str) -> str:
    req = urllib.request.Request(
        f"{server.rstrip('/')}/api/jarvis",
        data=json.dumps({"text": text}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            return json.load(res)["reply"]
    except urllib.error.HTTPError as e:
        return "The server did not accept the token." if e.code == 401 else f"The server answered with an error ({e.code})."
    except (urllib.error.URLError, TimeoutError):
        return "Could not reach the server."


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--server", default="http://localhost:8000")
    p.add_argument("--token", default=os.environ.get("HOME_API_TOKEN", ""))
    args = p.parse_args()
    print("Jarvis: Hi. Type a command or a question (empty line to quit).")
    while True:
        try:
            text = input("you:    ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            break
        print("Jarvis:", ask(args.server, args.token, text))


if __name__ == "__main__":
    main()
