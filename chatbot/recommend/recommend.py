from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import List

# LLM 모델 초기화
llm = OpenAI(
    temperature=0.5,                # 출력의 무작위성 조절 (0.0-2.0, 높을수록 창의적)
    model_name="gpt-3.5-turbo"    # 사용할 모델 지정
)

# 추천 질문을 위한 프롬프트 템플릿 정의
recommend_prompt = PromptTemplate(
    input_variables=["response"],
    template="""다음 응답을 바탕으로 사용자가 물어볼 만한 후속 질문 3개를 생성해주세요.
    
응답: {response}

질문은 다음과 같은 형식으로 작성해주세요:
1. [질문1]
2. [질문2]
3. [질문3]

질문:"""
)

# LLMChain 구성
recommend_chain = LLMChain(
    llm=llm,
    prompt=recommend_prompt
)

# 추천 질문 생성 및 처리
def get_recommendations(response: str) -> List[str]:
    # 1. LLMChain을 실행하여 GPT 모델로부터 추천 질문들을 생성
    result = recommend_chain.run(response=response)
    
    # 2. 결과 문자열을 처리하여 질문 리스트 생성
    questions = [q.strip()[3:] for q in result.split('\n') if q.strip()]
    
    # 3. 최대 3개의 질문만 반환
    return questions[:3]
