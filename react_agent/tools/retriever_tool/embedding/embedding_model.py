from langchain_huggingface import HuggingFaceEmbeddings


# 싱글톤 패턴 : 클래스의 인스턴스가 하나만 생성되도록 보장하는 디자인 패턴
class EmbeddingModelSingleton:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            model_name = "jhgan/ko-sbert-sts"
            cls._instance = HuggingFaceEmbeddings(model_name=model_name)
        return cls._instance


# @classmethod
# 클래스 메서드 데코레이터로, 인스턴스가 아닌 클래스 자체에서 호출할 수 있는 메서드를 정의합니다.
# 첫 번째 매개변수로 cls를 받아 클래스 자체를 참조합니다.

# _instance : 클래스 내부에서 클래스 변수로 사용되는 인스턴스
# 언더스코어()로 시작하는 변수는 "내부 사용" 변수임을 나타냅니다.
# 클래스 변수로서 모든 인스턴스가 공유합니다.
