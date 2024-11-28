from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from models.chatbot import DocumentChatbot
import os


def test_chatbot():
    print("=== 챗봇 테스트 시작 ===")

    # 벡터스토어 디렉토리 설정
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    vectordb_path = os.path.join(project_root, "data", "vectordb")

    print(f"벡터스토어 경로: {vectordb_path}")

    # 1. 초기화 테스트
    print("\n1. 챗봇 초기화 테스트")
    try:
        chatbot = DocumentChatbot(
            persist_directory=vectordb_path,
            documents=None,  # 기존 벡터스토어를 사용하므로 documents는 None
        )
        print("✓ 챗봇 초기화 성공")
    except Exception as e:
        print(f"✗ 챗봇 초기화 실패: {str(e)}")
        return

    # 2. 기본 질문 테스트
    print("\n2. 기본 질문 테스트")
    test_queries = [
        "24년에 가장 핫한 산업을 추천해줘",
        # "애널리스트 이름은 무엇인가?",
        # "23년 현황은 어떻게 되나요?",
    ]

    for query in test_queries:
        print(f"\n질문: {query}")
        try:
            response = chatbot.chat(query)
            print(f"응답: {response}")
            print("✓ 응답 성공")
        except Exception as e:
            print(f"✗ 응답 실패: {str(e)}")

    print("\n=== 챗봇 테스트 완료 ===")


if __name__ == "__main__":
    test_chatbot()
