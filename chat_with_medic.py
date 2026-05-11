import requests
import json
import sys

def chat():
    url = "http://localhost:11434/api/generate"
    print("\n" + "="*50)
    print("🚢 M-Medic 오프라인 AI 비서 테스트 모드")
    print("질문을 입력하세요 (종료하려면 'exit' 입력)")
    print("="*50)

    while True:
        user_input = input("\n[사용자]: ")
        if user_input.lower() in ['exit', 'quit', '종료']:
            break

        data = {
            "model": "llama3.2:1b",
            "prompt": f"당신은 선박 의료 AI 비서입니다. 한국어로 전문적이고 친절하게 답변하세요.\n\n질문: {user_input}",
            "stream": True # 실시간 타이핑 효과를 위해 스트림 활성화
        }

        print("[AI 비서]: ", end="", flush=True)
        try:
            response = requests.post(url, json=data, stream=True)
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    content = chunk.get("response", "")
                    print(content, end="", flush=True)
                    if chunk.get("done"):
                        print()
        except Exception as e:
            print(f"\n[!] 에러 발생: {e}")

if __name__ == "__main__":
    chat()
