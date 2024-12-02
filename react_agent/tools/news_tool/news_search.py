from langchain_community.tools import TavilySearchResults


def news_search_tool():
    news_search_tool = TavilySearchResults(
        include_domains=["hankyung.com"],
        search_depth="basic",
        topic="news",
        days=7,
        max_result=10,
        include_answer=True,
        include_raw_content=True,
        include_links=True,
        format_output=True,
    )
    news_search_tool.name = "news_search_tool"
    news_search_tool.description = (
        "이 도구는 웹에서 최근 뉴스 기사를 검색합니다. "
        "최신 정보를 보완할 때 사용하세요."
    )
    return news_search_tool
