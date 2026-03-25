from google import genai
import os

def call_gemini(prompt):
    # API 키를 환경 변수에서 가져옵니다.
    # $env:GOOGLE_API_KEY = "내_키" 로 미리 설정하거나 아래에 직접 입력할 수도 있습니다.
    api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyCUhpeOwP6G2QJAFAEokIa84EZYrJ7aMZw")
    
    # 제미나이 클라이언트를 생성합니다.
    client = genai.Client(api_key=api_key)

    # 텍스트 답변 생성
    print(f"\n[질문]: {prompt}")
    print("-" * 30)
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        print(f"[답변]:\n{response.text}")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    user_input = input("제미나이에게 물어볼 내용을 입력하세요: ")
    call_gemini(user_input)
