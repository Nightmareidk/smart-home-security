"""Talk to Jarvis by typing, from a terminal. Handy for testing without the app.

    python chat.py                                (server on this laptop, token from HOME_API_TOKEN)
    python chat.py --server http://192.168.1.20:8000
"""
import argparse
import os

from server import ask


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
