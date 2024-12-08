from react_agent.tools.news_tool.news_search import news_search_tool
from react_agent.tools.retriever_tool.retriever_tool import retriever_tool
from react_agent.tools.python_executor.python_executor import create_python_executor, execute_python_code
from typing import List
from langchain_community.tools import BaseTool
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# .env 파일 로드
load_dotenv()


def tool_list(db_path: str) -> List[BaseTool]:
    """
    다양한 도구들을 생성하고 리스트로 반환하는 함수.

    Args:
        db_path (str): 문서 검색에 사용할 벡터 데이터베이스 경로

    Returns:
        List[BaseTool]: 생성된 도구들의 리스트
    """
    tools = []  # 생성된 도구들을 저장할 리스트

    # 뉴스 검색 도구 생성
    try:
        tools.append(news_search_tool())  # 뉴스 검색 도구를 생성하여 리스트에 추가
    except Exception as e:
        print(f"Failed to create news_search_tool: {e}")  # 도구 생성 실패 시 오류 메시지 출력

    # 문서 검색 도구 생성
    try:
        tools.append(retriever_tool(db_path=db_path, name="retrieve_tool"))  # db_path를 기반으로 retriever_tool 생성
    except Exception as e:
        print(f"Failed to create retriever_tool: {e}")  # 도구 생성 실패 시 오류 메시지 출력

    # Python 코드 실행 도구 생성
    try:
        tools.append(create_python_executor())  # Python 실행 도구를 생성하여 리스트에 추가
    except Exception as e:
        print(f"Failed to create python_executor: {e}")  # 도구 생성 실패 시 오류 메시��� 출력

    return tools  # 생성된 도구 리스트 반환

# 메인 실행부
if __name__ == "__main__":
    # 테스트용 벡터 데이터베이스 경로 설정
    test_db_path = "/Users/jeonghyeran/Desktop/RePick-MLOps/data/vectordb"
    
    # 도구 생성 함수 호출
    created_tools = tool_list(test_db_path)
    
    # 생성된 도구 출력
    print("생성된 도구들:")
    for tool in created_tools:
        print(f"- {tool.name}: {tool.description}")
        try:
            if tool.name == "python_executor_tool":
                # execute_python_code 함수를 직접 import
                from react_agent.tools.python_executor.python_executor import execute_python_code
                
                # 샘플 경제 데이터를 사용한 시각화 테스트 코드
                test_code = """
def create_gdp_visualization(years, gdp_growth):
    # 입력값이 숫자인지 확인
    try:
        years = [int(year) for year in years]  # 문자열을 정수로 변환 시도
        gdp_growth = [float(value) for value in gdp_growth]  # 문자열을 실수로 변환 시도
    except (ValueError, TypeError):
        print("Error: 입력값이 올바른 숫자 형식이 아닙니다.")
        return
        
    # 데이터 유효성 검사
    if len(years) != len(gdp_growth):
        print("Error: 연도와 GDP 성장률 데이터의 길이가 일치하지 않습니다.")
        return

    if not years or not gdp_growth:
        print("Error: 빈 데이터가 입력되었습니다.")
        return

    # 그래프 설정
    plt.figure(figsize=(10, 6))

    # 막대 그래프 생성
    bars = plt.bar(years, gdp_growth, color='skyblue')
    plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)

    # 각 막대 위에 값 표시
    for bar, value in zip(bars, gdp_growth):
        plt.text(bar.get_x() + bar.get_width()/2, 
                value + (0.1 if value >= 0 else -0.3),
                f'{value}%',
                ha='center', va='bottom')

    # 그래프 꾸미기
    plt.title('한국 GDP 성장률 추이 (2019-2023)', pad=20)
    plt.xlabel('연도')
    plt.ylabel('GDP 성장률 (%)')
    plt.grid(True, alpha=0.3)

    # 여백 조정
    plt.tight_layout()

# 테스트용 데이터로 함수 호출
years = [2019, 2020, 2021, 2022, 2023]
gdp_growth = [2.2, -0.7, 4.1, 2.6, 1.4]
create_gdp_visualization(years, gdp_growth)
"""
                result = execute_python_code(test_code)
                print("\n시각화 결과:")
                print(result)  # 콘솔에 출력
                
                # 결과를 HTML 파일로 저장
                with open('test_visualization.html', 'w') as f:
                    f.write(f"""
                    <html>
                        <body>
                            {result}
                        </body>
                    </html>
                    """)
                
                # HTML 파일 자동으로 열기
                import webbrowser
                webbrowser.open('test_visualization.html')
            else:
                tool.run("test_input")
        except Exception as e:
            print(f"Tool {tool.name} failed during test: {e}")