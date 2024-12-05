from langchain_community.tools import Tool
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
import matplotlib.pyplot as plt
import io
import base64


def execute_python_code(code: str) -> str:
    """
    Python 코드를 실행하고 결과나 이미지를 반환하는 함수.

    Args:
        code (str): 실행할 Python 코드

    Returns:
        str: 실행 결과 문자열 또는 Base64로 인코딩된 이미지
    """
    output = io.StringIO()
    import sys

    stdout_backup = sys.stdout
    sys.stdout = output  # stdout을 StringIO로 임시 변경

    try:
        # 실행 환경 생성
        local_env = {}
        exec(code, globals(), local_env)  # 코드 실행
        output_str = output.getvalue()  # 실행 결과를 문자열로 저장

        # 플롯이 있는 경우 처리
        if plt.get_fignums():  # 열린 플롯 확인
            image_buffer = io.BytesIO()
            plt.savefig(image_buffer, format="png")  # 이미지를 버퍼에 저장
            image_buffer.seek(0)
            plt.close()  # 플롯 닫기
            image_base64 = base64.b64encode(image_buffer.getvalue()).decode()  # Base64 인코딩
            return f"{output_str}\n\n<img src='data:image/png;base64,{image_base64}' alt='Generated Plot'/>"

        return output_str
    finally:
        sys.stdout = stdout_backup  # stdout 원래대로 복원
        output.close()


def create_python_executor():
    """
    Python 코드 실행 도구를 생성.

    Returns:
        Tool: LangChain에서 사용할 도구 객체
    """
    # LLM 프롬프트 설정
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "파이썬 전문가로서 데이터 시각화와 분석을 위한 코드를 작성합니다. "
                "PEP8 스타일 가이드를 따르며, 간결하고 문서화가 잘된 코드를 작성합니다.\n"
                "사용 규칙:\n"
                "1. retrieve_tool에서 데이터/수치 정보를 찾은 경우에만 사용\n"
                "2. 시각화나 계산이 필요하지 않으면 사용하지 않음\n"
                "3. 1회만 사용 가능, 재시도 금지\n"
                "4. 실행 실패시 현재까지의 정보로만 답변\n"
                "출력: [데이터 출처, 분석 날짜] 형식으로 출처 표시",
            ),
            ("human", "{input}"),
        ]
    )

    # OpenAI LLM 설정
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    # LLM 실행 체인 생성
    chain = prompt | llm | StrOutputParser() | RunnableLambda(execute_python_code)

    # 도구 생성 및 반환
    return Tool(
        name="python_executor_tool",
        description="데이터 시각화나 수치 계산이 필요할 때 사용하는 도구입니다. matplotlib, pandas 등을 사용한 시각화 코드를 실행할 수 있습니다.",
        func=chain.invoke,
    )