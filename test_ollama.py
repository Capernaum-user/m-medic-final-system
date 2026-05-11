import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "llama3.2:1b",
        "prompt": "안녕하세요, 당신은 선박 의료 AI 비서입니다. 한국어로 짧게 인사해주세요.",
        "stream": False
    }
    
    try:
        print("[*] Sending request to Ollama...")
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            print("\n[AI 응답]:")
            print(result.get('response'))
        else:
            print(f"[!] Error: {response.status_code}")
    except Exception as e:
        print(f"[!] Exception: {e}")

if __name__ == "__main__":
    test_ollama()
