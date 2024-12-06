from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


def llm_model():
    """
    Chat_GPT 언어 모델 인스턴스를 생성하는 함수
    """
    return ChatOpenAI(
        model_name="gpt-4",
        streaming=True,
        temperature=0,
        callbacks=[StreamingStdOutCallbackHandler()],
    )

if __name__ == "__main__":
    # 모델 인스턴스 생성
    model = llm_model()
    
    # 모델을 사용하여 간단한 대화 테스트
    try:
        response = model.invoke("안녕하세요, 당신은 누구 인가요?")
        print("AI 응답:", response)
    except Exception as e:
        print("모델 호출 중 오류 발생:", e)
