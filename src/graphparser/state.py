from typing import TypedDict


# GraphState 상태를 저장하는 용도로 사용합니다.
class GraphState(TypedDict):
    filepath: str  # path
    filetype: str  # pdf
    page_numbers: list[int]  # page numbers
    batch_size: int  # batch size
    split_filepaths: list[str]  # split files
    analyzed_files: list[str]  # analyzed files
    page_elements: dict[int, dict[str, list[dict]]]  # page elements
    page_metadata: dict[int, dict]  # page metadata
    page_summary: dict[int, str]  # page summary
    images: list[str]  # image paths
    image_summary: list[str]  # image summary
    tables: list[str]  # table
    table_summary: dict[int, str]  # table summary
    table_markdown: dict[int, str]  # table markdown
    texts: list[str]  # text
    text_summary: dict[int, str]  # text summary
    table_summary_data_batches: list[dict]  # table summary data batches
    language: str  # language
