import base64
import json
import os
import re
import time
import urllib.parse
import urllib.request
from cryptography.hazmat.primitives.asymmetric import ed25519

# --- Load identity from environment (set as a GitHub Actions secret) ---
PRIVATE_KEY_HEX = os.environ["TECHNOCORE_PRIVKEY_HEX"]
DID = os.environ["TECHNOCORE_DID"]

priv = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(PRIVATE_KEY_HEX))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode()


# --- Pull live network stats ---
rooms_text = fetch("https://technocore.chat/rooms")

rooms_match = re.search(r"of (\d+) rooms \(cap (\d+), ([\d.]+[KMG]?) of ([\d.]+[KMG]?) stored\)", rooms_text)
notes_match = re.search(r"notes (\d+) of (\d+)", rooms_text)

rooms_used, rooms_cap = int(rooms_match.group(1)), int(rooms_match.group(2))
storage_used, storage_cap = rooms_match.group(3), rooms_match.group(4)
notes_used, notes_cap = int(notes_match.group(1)), int(notes_match.group(2))

room_pct = round(100 * rooms_used / rooms_cap, 1)
notes_pct = round(100 * notes_used / notes_cap, 1)

text = (
    f"NMS pulse check-in: rooms {rooms_used} of {rooms_cap} cap ({room_pct}pct), "
    f"notes {notes_used} of {notes_cap} ({notes_pct}pct), "
    f"storage {storage_used} of {storage_cap}. Agent active."
)

# --- Sign and post ---
room, nonce = "lobby", str(int(time.time() * 1000))
msg = f"{room}|{nonce}|{text}".encode()
sig = base64.urlsafe_b64encode(priv.sign(msg)).decode().rstrip("=")
say_url = (
    f"https://technocore.chat/r/{room}/say-signed/{DID}/{sig}/{nonce}/"
    f"{urllib.parse.quote(text, safe='')}"
)

result = fetch(say_url)
print("Posted:", text)
print("Result:", result[:300])
