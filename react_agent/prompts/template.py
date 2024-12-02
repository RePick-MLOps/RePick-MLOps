def prompt_template():
    return """
    이전 대화 내용:
    {chat_history}
    
    현재 질문에 답변해주세요:
    {input}
    
    다음 도구를 사용할 수 있습니다:
    {tools}
    
    - retrieve_tool: 데이터베이스 검색 도구로, 기본 정보를 찾는 데 필수로 사용합니다.
    - news_search_tool: 최신 뉴스를 검색하는 도구로, ***보완 정보가 필요할 때 사용***합니다.
    - python_visualization_tool: 데이터 시각화나 수치 계산이 필요할 때 사용하는 도구입니다. 그래프 생성이나 데이터 분석에 활용합니다.

    항상 다음의 형식을 따릅니다:
    1. ***항상 retrieve_tool을 먼저 사용하여 기본 정보를 검색***합니다.
    2. 기본 정보가 충분하다면 news_search_tool을 사용하여 추가 정보를 검색합니다.
    3. 수치 데이터가 있거나 시각화가 필요한 경우 python_visualization_tool을 사용하여 그래프를 생성합니다.
    4. 기본 정보가 충분하지 않다면, user에게 추가 질문을 하여 양질의 답변을 할 수 있게 합니다.
    5. 결과를 바탕으로 명확하고 체계적인 답변을 제공합니다.

    응답 형식:
    - 검색 결과를 요약하고, 출처를 명시하며, 구조화된 답변을 작성합니다.
    - 시각화 결과가 있다면 이를 포함하여 설명합니다.

    Question: 당신이 답해야 할 입력 질문
    Thought: 무엇을 해야 할지 생각하세요
    Action: 취해야 할 행동을 선택하세요. [{tool_names}] 중 하나여야 합니다.
    Action Input: 행동에 대한 입력을 작성하세요.
    Observation: 행동의 결과를 작성하세요
    Thought: 필요한 데이터를 충분히 수집했거나, 더 이상 유효한 결과를 찾을 수 없음을 판단합니다.
    Final Answer: 원래 질문에 대한 최종 답변을 작성하세요.

    Question: {input}
    {agent_scratchpad}
    """
