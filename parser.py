from dotenv import load_dotenv
from graphparser.state import GraphState
import os
import graphparser.core as parser_core
import graphparser.pdf as pdf
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

load_dotenv()

# 문서 분할
split_pdf_node = pdf.SplitPDFFilesNode(batch_size=10)

# Layout Analyzer
layout_analyze_node = parser_core.LayoutAnalyzerNode(os.environ.get("UPSTAGE_API_KEY"))

# 페이지 요소 추출
page_element_extractor_node = parser_core.ExtractPageElementsNode()

# 이미지 자르기
image_cropper_node = parser_core.ImageCropperNode()

# 테이블 자르기
table_cropper_node = parser_core.TableCropperNode()

# 페이지별 텍스트 추출
extract_page_text = parser_core.ExtractPageTextNode()

# 페이지별 요약
page_summary_node = parser_core.CreatePageSummaryNode(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# 이미지 요약
image_summary_node = parser_core.CreateImageSummaryNode(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# 테이블 요약
table_summary_node = parser_core.CreateTableSummaryNode(
    api_key=os.environ.get("OPENAI_API_KEY")
)

# 테이블 Markdown 추출
table_markdown_extractor = parser_core.TableMarkdownExtractorNode()

# LangGraph을 생성
workflow = StateGraph(GraphState)

# 노드들을 정의합니다.
workflow.add_node("split_pdf_node", split_pdf_node)
workflow.add_node("layout_analyzer_node", layout_analyze_node)
workflow.add_node("page_element_extractor_node", page_element_extractor_node)
workflow.add_node("image_cropper_node", image_cropper_node)
workflow.add_node("table_cropper_node", table_cropper_node)
workflow.add_node("extract_page_text_node", extract_page_text)
workflow.add_node("page_summary_node", page_summary_node)
workflow.add_node("image_summary_node", image_summary_node)
workflow.add_node("table_summary_node", table_summary_node)
workflow.add_node("table_markdown_node", table_markdown_extractor)

# 각 노드들을 연결합니다.
workflow.add_edge("split_pdf_node", "layout_analyzer_node")
workflow.add_edge("layout_analyzer_node", "page_element_extractor_node")
workflow.add_edge("page_element_extractor_node", "image_cropper_node")
workflow.add_edge("page_element_extractor_node", "table_cropper_node")
workflow.add_edge("page_element_extractor_node", "extract_page_text_node")
workflow.add_edge("image_cropper_node", "page_summary_node")
workflow.add_edge("table_cropper_node", "page_summary_node")
workflow.add_edge("extract_page_text_node", "page_summary_node")
workflow.add_edge("page_summary_node", "image_summary_node")
workflow.add_edge("page_summary_node", "table_summary_node")
workflow.add_edge("image_summary_node", END)
workflow.add_edge("table_summary_node", "table_markdown_node")
workflow.add_edge("table_markdown_node", END)

workflow.set_entry_point("split_pdf_node")

memory = MemorySaver()
graph = workflow.compile()


def process_single_pdf(filepath="data/pdf/20241122_company_22650000.pdf"):
    if not os.path.exists(filepath):
        raise ValueError(f"PDF 파일을 찾을 수 없습니다: {filepath}")

    print(f"처리할 PDF 파일: {filepath}")

    # 초기 상태 설정
    initial_state = GraphState(
        filepath=filepath,
        filetype="pdf",
        language="ko",
        pdf_files=[filepath],
        current_page=0,
        processed_pages=[],
        summaries={},
        images=[],
        tables=[],
        text_summary={},
    )

    try:
        # 그래프 실행
        final_state = graph.invoke(initial_state)
        print("PDF 처리가 완료되었습니다.")
        return final_state
    except Exception as e:
        print(f"PDF 처리 중 오류 발생: {str(e)}")
        raise


def create_chatbot(state, persist_directory: str = "vectorstore"):
    """
    처리된 PDF 상태로부터 챗봇을 생성합니다.

    Args:
        state: PDF 처리 결과 상태
        persist_directory (str): 벡터스토어 저장 경로

    Returns:
        DocumentChatbot: 생성된 챗봇 인스턴스
    """
    from app.chatbot import DocumentChatbot

    # 문서 준비
    documents = []

    # 텍스트 요약 추가
    for page, summary in state.text_summary.items():
        documents.append(
            Document(
                page_content=summary, metadata={"type": "text_summary", "page": page}
            )
        )

    # 이미지 요약 추가
    for image_id, summary in state.image_summary.items():
        documents.append(
            Document(
                page_content=summary, metadata={"type": "image_summary", "id": image_id}
            )
        )

    # 테이블 요약 추가
    for table_id, summary in state.table_summary.items():
        documents.append(
            Document(
                page_content=summary, metadata={"type": "table_summary", "id": table_id}
            )
        )

    return DocumentChatbot(documents, persist_directory)


if __name__ == "__main__":
    # PDF 처리
    pdf_directory = "data/pdf"
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith(".pdf")]

    if not pdf_files:
        raise ValueError(f"'{pdf_directory}' 디렉토리에 PDF 파일이 없습니다.")

    first_pdf = os.path.join(pdf_directory, pdf_files[0])
    state = process_single_pdf(first_pdf)

    # 챗봇 생성 (벡터스토어 경로 지정)
    chatbot = create_chatbot(state, persist_directory="data/vectorstore")

    # 대화 루프
    print("챗봇이 준비되었습니다. 종료하려면 'quit' 또는 'exit'를 입력하세요.")
    while True:
        question = input("\n질문을 입력하세요: ")
        if question.lower() in ["quit", "exit"]:
            break

        answer = chatbot.chat(question)
        print("\n답변:", answer)
