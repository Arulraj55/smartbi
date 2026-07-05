import os
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")

def test_openrouter():
    print(f"API Key: {OPENROUTER_API_KEY[:10]}...")
    print(f"Model: {OPENROUTER_MODEL}")
    
    payload = json.dumps({
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": "Hello, respond with 'OK' if you hear me."}],
        "temperature": 0.1,
        "max_tokens": 1000,
    }).encode("utf-8")

    req = urllib.request.Request(
        OPENROUTER_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://smartbi.app",
            "X-Title": "SmartBI",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = response.read().decode("utf-8")
            result = json.loads(res_body)
            print("Content:", result["choices"][0]["message"].get("content"))
    except Exception as e:
        print("Error calling OpenRouter:", e)

if __name__ == "__main__":
    test_openrouter()
