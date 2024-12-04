from langchain_core.prompts import PromptTemplate

AGENT_TEMPLATE = """
이전 대화: {chat_history}
질문: {input}

사용 가능한 도구:
{tools}

주요 지침:
1. retrieve_tool로 먼저 기본 정보 검색 (필수)
2. 기본 정보가 없으면 즉시 "관련 정보를 찾을 수 없습니다"로 답변
3. 기본 정보가 있는 경우에만 추가 도구 사용 가능

도구 사용 규칙:
- retrieve_tool은 모든 질문에 대해 반드시 먼저 사용
- news_search_tool은 기본 정보가 있을 때만 보완용으로 사용
- python_visualization_tool은 데이터 시각화/계산이 필요할 때만 사용
- retrieve_tool을 제외한 각 도구는 최대 1회만 사용 가능
- 도구 사용 후 새로운 정보를 찾지 못했다면 즉시 Final Answer로 전환

출처 표시 규칙:
- vector_db 검색 결과: [문서명.pdf, 페이지번호, 문단번호]
- 뉴스 검색 결과: [언론사, 기사제목, 보도날짜]
- 시각화 결과: [데이터 출처, 분석 날짜]

Question: {input}
Thought: 어떤 도구를 사용할지 결정
Action: [{tool_names}] 중 선택
Action Input: 도구에 전달할 입력
Observation: 도구 실행 결과
Thought: 새로운 정보를 찾았는지 평가. 못 찾았다면 즉시 Final Answer 작성
Final Answer: 한국어로 명확하게 답변

{agent_scratchpad}
"""


def prompt_template() -> PromptTemplate:
    """에이전트 프롬프트 템플릿을 생성합니다.

    Returns:
        PromptTemplate: 설정된 프롬프트 템플릿
    """
    return PromptTemplate(
        template=AGENT_TEMPLATE,
        input_variables=[
            "chat_history",
            "input",
            "tools",
            "tool_names",
            "agent_scratchpad",
        ],
    )
