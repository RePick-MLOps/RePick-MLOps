from langchain_community.tools import TavilySearchResults


def news_search_tool():
    news_search_tool = TavilySearchResults(
        include_domains=["hankyung.com"],
        search_depth="basic",
        topic="news",
        days=7,
        max_result=3,
        include_answer=True,
        include_raw_content=True,
        include_links=True,
        format_output=True,
    )
    news_search_tool.name = "news_search_tool"
    news_search_tool.description = (
        "이 도구는 한국경제 최근 7일 뉴스만 검색합니다.\n"
        "사용 규칙:\n"
        "1. retrieve_tool에서 기본 정보를 찾은 경우에만 사용 가능\n"
        "2. retrieve_tool에서 정보를 찾지 못했다면 즉시 '관련 정보를 찾을 수 없습니다'로 답변\n"
        "3. 1회만 사용 가능, 재시도 금지\n"
        "4. 검색 결과가 없으면 현재까지의 정보로만 답변\n"
        "입력: 검색하고자 하는 키워드나 문장\n"
        "출력: [언론사, 기사제목, 보도날짜] 형식으로 출처 표시\n"
        "주의: retrieve_tool에서 정보를 찾지 못한 경우 이 도구를 사용하지 말고 즉시 정보 없음으로 답변"
    )
    return news_search_tool
