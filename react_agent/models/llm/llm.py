from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


def llm_model():
    """
    Chat_GPT 언어 모델 인스턴스를 생성하는 함수
    """
    return ChatOpenAI(
        model_name="gpt-4",
        streaming=True,  # 스트리밍 응답 활성화
        temperature=0,  # 분석이 중요하기 때문에 낮은 랜덤성 부여
        callbacks=[
            StreamingStdOutCallbackHandler()
        ],  # 생성된 응답을 실시간으로 콘솔에 출력
    )
