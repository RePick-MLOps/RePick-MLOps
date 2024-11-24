from langchain_openai import ChatOpenAI
from langchain_core.runnables import chain
from .models import MultiModal
from .state import GraphState


@chain
def extract_image_summary(data_batches):
    # 객체 생성
    llm = ChatOpenAI(
        temperature=0,  # 창의성 (0.0 ~ 2.0)
        model_name="gpt-4o-mini",  # 모델명
    )

    system_prompt = """당신은 이미지에서 유용한 정보를 추출하는 전문가입니다.
주어진 이미지에서 핵심 개체들을 추출하고, 요약하여, 나중에 검색에 사용할 수 있는 유용한 정보를 작성하는 것이 당신의 임무입니다.
또한, 사용자가 이미지에 대해 물어볼 수 있는 가상의 질문 5개를 제공해주세요.
"""

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        context = data_batch["text"]
        image_path = data_batch["image"]
        language = data_batch["language"]
        user_prompt_template = f"""다음은 표 이미지와 관련된 컨텍스트입니다: {context}
        
###

출력 형식:

<image>
<title>
[제목]
</title>
<summary>
[요약]
</summary>
<entities> 
[개체들]
</entities>
<hypothetical_questions>
[가상 질문들]
</hypothetical_questions>
</image>

출력은 반드시 {language}로 작성되어야 합니다.
"""
        image_paths.append(image_path)
        system_prompts.append(system_prompt)
        user_prompts.append(user_prompt_template)

    # 멀티모달 객체 생성
    multimodal_llm = MultiModal(llm)

    # 이미지 파일로 부터 질의
    answer = multimodal_llm.batch(
        image_paths, system_prompts, user_prompts, display_image=False
    )
    return answer


@chain
def extract_table_summary(data_batches):
    # 객체 생성
    llm = ChatOpenAI(
        temperature=0,  # 창의성 (0.0 ~ 2.0)
        model_name="gpt-4o-mini",  # 모델명
    )

    system_prompt = """당신은 표(TABLE)에서 유용한 정보를 추출하는 전문가입니다.
주어진 이미지에서 핵심 개체들을 추출하고, 요약하여, 나중에 검색에 사용할 수 있는 유용한 정보를 작성하는 것이 당신의 임무입니다.
숫자가 있다면, 숫자들로부터 중요한 인사이트를 요약해주세요.
또한, 사용자가 이미지에 대해 물어볼 수 있는 가상의 질문 5개를 제공해주세요.
"""

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        context = data_batch["text"]
        image_path = data_batch["table"]
        language = data_batch["language"]
        user_prompt_template = f"""다음은 표 이미지와 관련된 컨텍스트입니다: {context}
        
###

출력 형식:

<table>
<title>
[제목]
</title>
<summary>
[요약]
</summary>
<entities> 
[개체들]
</entities>
<data_insights>
[데이터 인사이트]
</data_insights>
<hypothetical_questions>
[가상 질문들]
</hypothetical_questions>
</table>

출력은 반드시 {language}로 작성되어야 합니다.
"""
        image_paths.append(image_path)
        system_prompts.append(system_prompt)
        user_prompts.append(user_prompt_template)

    # 멀티모달 객체 생성
    multimodal_llm = MultiModal(llm)

    # 이미지 파일로 부터 질의
    answer = multimodal_llm.batch(
        image_paths, system_prompts, user_prompts, display_image=False
    )
    return answer


@chain
def table_markdown_extractor(data_batches):
    # 객체 생성
    llm = ChatOpenAI(
        temperature=0,  # 창의성 (0.0 ~ 2.0)
        model_name="gpt-4o-mini",  # 모델명
    )

    system_prompt = "당신은 표(TABLE) 이미지를 마크다운 형식으로 변환하는 전문가입니다. 표의 모든 정보를 반드시 포함해야 합니다. 설명하지 말고, 마크다운 형식으로만 답변하세요."

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        image_path = data_batch["table"]
        user_prompt_template = f"""답변을 ```markdown``` 또는 XML 태그로 감싸지 마세요.
        
###

출력 형식:

<table_markdown>

출력은 반드시 한국어로 작성되어야 합니다.
"""
        image_paths.append(image_path)
        system_prompts.append(system_prompt)
        user_prompts.append(user_prompt_template)

    # 멀티모달 객체 생성
    multimodal_llm = MultiModal(llm)

    # 이미지 파일로 부터 질의
    answer = multimodal_llm.batch(
        image_paths, system_prompts, user_prompts, display_image=False
    )
    return answer
