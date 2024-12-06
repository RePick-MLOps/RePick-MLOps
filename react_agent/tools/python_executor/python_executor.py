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
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are Raymond Hettinger, an expert Python programmer specializing in data visualization. "
                "IMPORTANT: Return ONLY raw Python code without any markdown formatting, code blocks, or backticks.\n"
                "Rules:\n"
                "1. NO markdown formatting (```, backticks, etc.)\n"
                "2. NO explanations or comments before/after code\n"
                "3. Use only English in code and comments\n"
                "4. Follow PEP8 style guide\n"
                "5. Use matplotlib for visualization\n"
                "6. Include proper labels and titles\n"
                "7. Start directly with 'import' statements\n"
                "8. End with plt.tight_layout()"
            ),
            ("human", "{input}"),
        ]
    )

    llm = ChatOpenAI(model="gpt-4", temperature=0)
    chain = prompt | llm | StrOutputParser() | RunnableLambda(execute_python_code)

    return Tool(
        name="python_executor_tool",
        description="데이터 시각화나 수치 계산이 필요할 때 사용하는 도구입니다. matplotlib, pandas 등을 사용한 시각화 코드를 실행할 수 있습니다.",
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
        한국의 GDP 변화 추이에 대한 정보를 찾지 못했습니다. 하지만, 최근 한국경제 뉴스에 따르면, 한국의 명목 GDP는 1조6733억달러로, 강한 달러 환율 영향으로 세계 13위로 추락하였다고 합니다. 또한, 한국의 가계부채가 GDP의 100%에 육박하며 전 세계 주요국 대비 유난히 빠른 속도로 증가하고 있다고 보고되었습니다. 또한, 2050년에는 생산 가능 인구가 34% 줄어들어 GDP가 28% 감소할 것으로 예상되고 있습니다.📌 출처: [한국경제, 강달러에…한국, gdp 세계 13위로 추락, 2021-07-12], [한국경제, 조세연구원, 국가별 부채 변화추이 비교 보고서, 2021-04-05], [한국경제, 韓 생산가능인구, 2050년엔 34% 줄어…gdp 28% 감소할 것, 2023-05-18
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