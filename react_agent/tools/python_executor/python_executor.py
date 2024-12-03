from langchain_community.tools import Tool
from langchain.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnableLambda
import matplotlib.pyplot as plt
import io
import base64

def execute_python_code(code: str) -> str:
    """Python 코드를 실행하고 결과를 반환하는 함수"""
    output = io.StringIO()
    import sys
    stdout_backup = sys.stdout
    sys.stdout = output
    
    try:
        exec(code, globals(), locals())
        output_str = output.getvalue()
        
        if plt.get_fignums():
            image_buffer = io.BytesIO()
            plt.savefig(image_buffer, format='png')
            plt.close()
            image_buffer.seek(0)
            image_base64 = base64.b64encode(image_buffer.getvalue()).decode()
            return f"{output_str}\ndata:image/png;base64,{image_base64}"
        
        return output_str
    finally:
        sys.stdout = stdout_backup
        output.close()

def create_python_executor():  # 이 함수가 외부로 노출되어야 합니다
    """Python 코드 실행 도구 생성"""
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "파이썬 전문가로서 데이터 시각화와 분석을 위한 코드를 작성합니다. "
            "PEP8 스타일 가이드를 따르며, 간결하고 문서화가 잘된 코드를 작성합니다."
        ),
        ("human", "{input}")
    ])
    
    llm = ChatOpenAI(model="gpt-4", temperature=0)
    chain = prompt | llm | StrOutputParser() | RunnableLambda(execute_python_code)
    
    return Tool(
        name="python_executor_tool",
        description="데이터 시각화나 수치 시각화가 필요할 때 사용하는 도구입니다. matplotlib, pandas 등을 사용한 시각화 코드를 실행할 수 있습니다.",
        func=chain.invoke
    )