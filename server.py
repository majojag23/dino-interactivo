#!/usr/bin/env python3
"""Servidor estatico + proxy /api/chat (OpenRouter) y /api/tts-el (ElevenLabs) para Dino."""
import os, sys, json, urllib.request, urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 9000

def load_keys():
    """Carga claves desde api_keys.json (prioridad) o variables de entorno."""
    keyfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys.json")
    keys = {}
    if os.path.exists(keyfile):
        try:
            with open(keyfile, "r") as f:
                keys = json.load(f)
        except Exception:
            pass
    return {
        "or_key": keys.get("or_key") or os.environ.get("OR_KEY", ""),
        "el_key": keys.get("el_key") or os.environ.get("EL_KEY", ""),
        "el_voice_id": keys.get("el_voice_id") or os.environ.get("EL_VOICE_ID", "U9tZtg3uJtVgXPkvosWR"),
    }

KEYS = load_keys()

class DinoHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if self.path == "/api/chat":
            reply = proxy_openrouter(body.get("text", ""))
            self._json_reply({"reply": reply})
            return

        if self.path == "/api/tts-el":
            audio = proxy_elevenlabs(body.get("text", ""))
            if audio:
                self.send_response(200)
                self.send_header("Content-Type", "audio/mpeg")
                self.send_header("Content-Length", str(len(audio)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(audio)
            else:
                self.send_error(503, "TTS no disponible")
            return

        # Tambien acepta guardar claves via POST /api/keys
        if self.path == "/api/keys":
            save_keys(body)
            self._json_reply({"saved": list(body.keys())})
            return

        self.send_error(404, "Not found")

    def do_GET(self):
        path = urllib.parse.unquote(self.path.split("?")[0])
        if path == "/" or path == "":
            path = "/index.html"
        if path == "/api/keys":
            self._json_reply({"or_key": "***" if KEYS["or_key"] else "", "el_key": "***" if KEYS["el_key"] else "", "el_voice_id": KEYS["el_voice_id"]})
            return
        super().do_GET()

    def _json_reply(self, data):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), format % args))


def save_keys(data):
    global KEYS
    keyfile = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_keys.json")
    existing = {}
    if os.path.exists(keyfile):
        try:
            with open(keyfile, "r") as f:
                existing = json.load(f)
        except Exception:
            pass
    for k in ("or_key", "el_key", "el_voice_id"):
        if data.get(k):
            existing[k] = data[k]
    with open(keyfile, "w") as f:
        json.dump(existing, f)
    KEYS = load_keys()


def proxy_openrouter(text):
    if not KEYS["or_key"]:
        return "Falta OR_KEY. Guardala en api_keys.json o como variable de entorno."
    body = json.dumps({
        "model": "mistralai/mistral-small-24b-instruct-2501",
        "max_tokens": 500,
        "messages": [
            {"role": "system", "content": "Eres Dino, un dinosaurio bebe amigable y divertido. Responde en espanol con frases MUY cortas (1 oracion maximo), tiernas, con entusiasmo infantil. Usa emojis de vez en cuando. Nunca digas que eres una IA."},
            {"role": "user", "content": text}
        ]
    }).encode("utf-8")
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + KEYS["or_key"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data.get("choices", [{}])[0].get("message", {}).get("content", "Dino no sabe que decir...")
    except Exception as e:
        return "Dino se quedo sin palabras..."


def proxy_elevenlabs(text):
    if not KEYS["el_key"]:
        return None
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.65, "similarity_boost": 0.88}
    }).encode("utf-8")
    url = "https://api.elevenlabs.io/v1/text-to-speech/" + KEYS["el_voice_id"]
    req = urllib.request.Request(url, data=body,
        headers={"xi-api-key": KEYS["el_key"], "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        print("TTS error:", e)
        return None


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    print("Keys cargadas: OR_KEY=" + ("SI" if KEYS["or_key"] else "NO") + " EL_KEY=" + ("SI" if KEYS["el_key"] else "NO"))
    server = HTTPServer(("", PORT), DinoHandler)
    print("Dino server en http://127.0.0.1:" + str(PORT))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nApagando...")
        server.shutdown()
