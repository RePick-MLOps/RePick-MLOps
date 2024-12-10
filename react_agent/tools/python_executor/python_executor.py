from langchain_community.tools import Tool
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
import matplotlib.pyplot as plt
import io
import base64
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

def execute_python_code(code: str) -> str:
    """
    Python 코드를 실행하고 결과나 이미지를 반환하는 함수.
    """
    print("Executing code:")
    
    # 마크다운 코드 블록 제거
    code = code.replace("```python", "").replace("```", "").strip()
    
    print(code)  # 실행할 코드 출력
    
    output = io.StringIO()
    import sys

    stdout_backup = sys.stdout
    sys.stdout = output

    try:
        local_env = {}
        exec(code, globals(), local_env)
        output_str = output.getvalue()

        if plt.get_fignums():
            image_buffer = io.BytesIO()
            plt.savefig(image_buffer, format="png")
            image_buffer.seek(0)
            plt.close()
            image_base64 = base64.b64encode(image_buffer.getvalue()).decode()
            
            # 출력 문자열이 있는 경우에만 출력하고, 이미지는 별도 라인에 표시
            if output_str.strip():
                return f"{output_str}\n<img src='data:image/png;base64,{image_base64}' alt='Generated Plot'/>"
            return f"<img src='data:image/png;base64,{image_base64}' alt='Generated Plot'/>"

        return output_str
    finally:
        sys.stdout = stdout_backup
        output.close()


def create_python_executor():
    """
    Python 코드 실행 도구를 생성.
    """
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "당신은 Python 데이터 시각화 전문가입니다. 주어진 텍스트에서 명확히 언급된 수치 데이터를 사용하여 시각화합니다.\n"
            "***순수한 Python 코드만 반환하며, 출력 형식은 다음과 같습니다***:\n"
            "```python\n"
            "import matplotlib.pyplot as plt\n"
            "plt.plot([1, 2, 3], [4, 5, 6])\n"
            "plt.title('Sample Plot')\n"
            "plt.xlabel('X-axis')\n"
            "plt.ylabel('Y-axis')\n"
            "plt.show()\n"
            "```\n"
            "중요 규칙:\n"
            "1. 반드시 필요한 import 구문으로 시작하기\n"
            "2. 텍스트에서 명확하게 언급된 수치 데이터 사용하기\n"
            "3. 현재 데이터와 미래 예측 데이터를 구분하여 표시하기\n"
            "4. 최소 2개 이상의 관련 수치 데이터가 있다면 시각화 시도하기\n"
            "5. 시각화에 다음 요소들을 포함하기:\n"
                "- 명확한 제목\n"
                "- 축 레이블\n"
                "- 데이터 출처와 연도\n"
                "- 범례 (예측 데이터 구분)\n"
                "- 가독성을 위한 그리드\n"
            "6. plt.tight_layout()으로 마무리하기\n"
            "7. 관련된 수치 데이터가 전혀 없는 경우에만 '시각화에 필요한 충분한 수치 데이터가 없습니다.' 반환\n"
            "8. 설명이나 사과 대신 유효한 Python 코드나 에러 메시지만 반환하기"
        ),
        ("human", "{input}"),
    ])

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    chain = prompt | llm | StrOutputParser() | RunnableLambda(execute_python_code)

    return Tool(
        name="python_executor_tool",
        description=(
            "데이터 시각화를 위한 Python 실행 도구입니다.\n"
            "사용 규칙:\n"
            "1. 수치 데이터가 포함된 경우에만 사용\n"
            "2. matplotlib을 사용한 시각화 생성\n"
            "3. 그래프에는 제목, 축 레이블, 범례 필수 포함\n"
            "입력: 시각화하려는 데이터나 수치 정보\n"
            "출력: 시각화된 그래프 또는 결과\n"
            "주의: 시각화가 불가능 하거나 수치 데이터가 없는 경우 이 도구를 사용하지 말 것"
        ),
        func=chain.invoke,
    )


def test_matplotlib_generation():
    """
    LLM이 matplotlib 코드를 자동 생성하는지 테스트하는 함수
    """
    print("=== Python Executor 테스트 시작 ===")
    
    try:
        # Python Executor 도구 생성
        tool = create_python_executor()
        print("도구 생성 완료")
        
        # 테스트용 데이터
        test_prompt = """
        한국의 현재 명목 GDP는 1조6733억달러이며, 2050년에는 GDP가 28% 감소할 것으로 예상됩니다. 
        또한 생산가능인구는 2050년까지 34% 감소할 것으로 전망됩니다.
        출처: 한국경제(2023)
        """
        print("\n입력 데이터:")
        print(test_prompt)
        
        print("\nLLM 응답 생성 중...")
        response = tool.func(test_prompt)
        print("\n생성된 시각화:")
        print(response)
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == "__main__":
    test_matplotlib_generation()