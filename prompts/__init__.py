from langchain.prompts import PromptTemplate
from .template import create_prompt_template


def initialize_prompts():
    template = create_prompt_template()
    return PromptTemplate.from_template(template)
