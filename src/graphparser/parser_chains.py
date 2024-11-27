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

    system_prompt = """You are an expert in extracting useful information from IMAGE.
With a given image, your task is to extract key entities, summarize them, and write useful information that can be used later for retrieval.
Also, provide five hypothetical questions based on the image that users can ask.
"""

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        context = data_batch["text"]
        image_path = data_batch["image"]
        language = data_batch["language"]
        user_prompt_template = f"""Here is the context related to the image: {context}
        
###

Output Format:

<image>
<title>
[title]
</title>
<summary>
[summary]
</summary>
<entities> 
[entities]
</entities>
<hypothetical_questions>
[hypothetical_questions]
</hypothetical_questions>
</image>

Output must be written in {language}.
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

    system_prompt = """You are an expert in extracting useful information from TABLE. 
With a given image, your task is to extract key entities, summarize them, and write useful information that can be used later for retrieval.
If the numbers are present, summarize important insights from the numbers.
Also, provide five hypothetical questions based on the image that users can ask.
"""

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        context = data_batch["text"]
        image_path = data_batch["table"]
        language = data_batch["language"]
        user_prompt_template = f"""Here is the context related to the image of table: {context}
        
###

Output Format:

<table>
<title>
[title]
</title>
<summary>
[summary]
</summary>
<entities> 
[entities]
</entities>
<data_insights>
[data_insights]
</data_insights>
<hypothetical_questions>
[hypothetical_questions]
</hypothetical_questions>
</table>

Output must be written in {language}.
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

    system_prompt = "You are an expert in converting image of the TABLE into markdown format. Be sure to include all the information in the table. DO NOT narrate, just answer in markdown format."

    image_paths = []
    system_prompts = []
    user_prompts = []

    for data_batch in data_batches:
        image_path = data_batch["table"]
        user_prompt_template = f"""DO NOT wrap your answer in ```markdown``` or any XML tags.
        
###

Output Format:

<table_markdown>

Output must be written in Korean.
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
