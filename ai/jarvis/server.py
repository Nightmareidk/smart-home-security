import json
import urllib.error
import urllib.request


def ask(server: str, token: str, text: str) -> str:
    """Send a sentence to the house server and get Jarvis's answer back as text."""
    req = urllib.request.Request(
        f"{server.rstrip('/')}/api/jarvis",
        data=json.dumps({"text": text}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            return json.load(res)["reply"]
    except urllib.error.HTTPError as e:
        return "The server did not accept the token." if e.code == 401 else f"The house server had a problem ({e.code})."
    except (urllib.error.URLError, TimeoutError):
        return "I could not reach the house server."
