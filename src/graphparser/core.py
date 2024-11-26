from .base import BaseNode
from .layout_utils import LayoutAnalyzer, ImageCropper
from .state import GraphState
import os
import re
import json
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document


from .parser_chains import (
    extract_image_summary,
    extract_table_summary,
    table_markdown_extractor,
)


class LayoutAnalyzerNode(BaseNode):

    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = "LayoutAnalyzerNode"
        self.api_key = api_key
        self.layout_analyzer = LayoutAnalyzer(api_key)

    def execute(self, state: GraphState) -> GraphState:
        # 분할된 PDF 파일 목록을 가져옵니다.
        split_files = state["split_filepaths"]

        # LayoutAnalyzer 객체를 생성합니다. API 키는 환경 변수에서 가져옵니다.
        analyzer = LayoutAnalyzer(self.api_key)

        # 분석된 파일들의 경로를 저장할 리스트를 초기화합니다.
        analyzed_files = []

        # 각 분할된 PDF 파일에 대해 레이아웃 분석을 수행합니다.
        for file in split_files:
            # 레이아웃 분석을 실행하고 결과 파일 경로를 리스트에 추가합니다.
            analyzed_files.append(analyzer.execute(file))

        # 분석된 파일 경로들을 정렬하여 새로운 GraphState 객체를 생성하고 반환합니다.
        # 정렬은 파일들의 순서를 유지하기 위해 수행됩니다.
        return GraphState(analyzed_files=sorted(analyzed_files))


class ExtractPageElementsNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "ExtractPageElementsNode"

    def extract_start_end_page(self, filename):
        """
        파일 이름에서 시작 페이지와 끝 페이지 번호를 추출하는 함수입니다.

        :param filename: 분석할 파일의 이름
        :return: 시작 페이지 번호와 끝 페이지 번호를 튜플로 반환
        """
        file_name = os.path.basename(filename)
        file_name_parts = file_name.split("_")

        if len(file_name_parts) >= 3:
            start_page = int(re.findall(r"(\d+)", file_name_parts[-2])[0])
            end_page = int(re.findall(r"(\d+)", file_name_parts[-1])[0])
        else:
            start_page, end_page = 0, 0

        return start_page, end_page

    def execute(self, state: GraphState) -> GraphState:
        """
        분석된 JSON 파일들에서 페이지 메타데이터를 추출하고 페이지 요소를 추출하는 함수입니다.

        :param state: 현재의 GraphState 객체
        :return: 페이지 메타데이터, 페이지 요소, 페이지 번호가 추가된 새로운 GraphState 객체
        """
        json_files = state["analyzed_files"]
        page_metadata = dict()
        page_elements = dict()
        element_id = 0

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            start_page, _ = self.extract_start_end_page(json_file)

            for element in data["metadata"]["pages"]:
                original_page = int(element["page"])
                relative_page = start_page + original_page - 1

                metadata = {
                    "size": [
                        int(element["width"]),
                        int(element["height"]),
                    ],
                }
                page_metadata[relative_page] = metadata

            for element in data["elements"]:
                original_page = int(element["page"])
                relative_page = start_page + original_page - 1

                if relative_page not in page_elements:
                    page_elements[relative_page] = []

                element["id"] = element_id
                element_id += 1

                element["page"] = relative_page
                page_elements[relative_page].append(element)

        parsed_page_elements = self.extract_tag_elements_per_page(page_elements)
        page_numbers = list(parsed_page_elements.keys())
        return GraphState(
            page_metadata=page_metadata,
            page_elements=parsed_page_elements,
            page_numbers=page_numbers,
        )

    def extract_tag_elements_per_page(self, page_elements):
        # 파싱된 페이지 요소들을 저장할 새로운 딕셔너리를 생성합니다.
        parsed_page_elements = dict()

        # 각 페이지와 해당 페이지의 요소들을 순회합니다.
        for key, page_element in page_elements.items():
            # 이미지, 테이블, 텍스트 요소들을 저장할 리스트를 초기화합니다.
            image_elements = []
            table_elements = []
            text_elements = []

            # 페이지의 각 요소를 순회하며 카테고리별로 분류합니다.
            for element in page_element:
                if element["category"] == "chart":
                    # 이미지 요소인 경우 image_elements 리스트에 추가합니다.
                    image_elements.append(element)
                elif element["category"] == "table":
                    # 테이블 요소인 경우 table_elements 리스트에 추가합니다.
                    table_elements.append(element)
                else:
                    # 그 외의 요소는 모두 텍스트 요소로 간주하여 text_elements 리스트에 추가합니다.
                    text_elements.append(element)

            # 분류된 요소들을 페이지 키와 함께 새로운 딕셔너리에 저장합니다.
            parsed_page_elements[key] = {
                "image_elements": image_elements,
                "table_elements": table_elements,
                "text_elements": text_elements,
                "elements": page_element,  # 원본 페이지 요소도 함께 저장합니다.
            }

        return parsed_page_elements


class PageElementParserNode(BaseNode):
    """
    페이지 요소를 파싱하여 이미지, 테이블, 텍스트 요소로 분류합니다.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "PageElementParserNode"

    def execute(self, state: GraphState) -> GraphState:
        # GraphState 객체에서 페이지 요소들을 가져옵니다.
        page_elements = state["page_elements"]

        # 파싱된 페이지 요소들을 저장할 새로운 딕셔너리를 생성합니다.
        parsed_page_elements = dict()

        # 각 페이지와 해당 페이지의 요소들을 순회합니다.
        for key, page_element in page_elements.items():
            # 이미지, 테이블, 텍스트 요소들을 저장할 리스트를 초기화합니다.
            image_elements = []
            table_elements = []
            text_elements = []

            # 페이지의 각 요소를 순회하며 카테고리별로 분류합니다.
            for element in page_element:
                if element["category"] == "chart":
                    # 이미지 요소인 경우 image_elements 리스트에 추가합니다.
                    image_elements.append(element)
                elif element["category"] == "table":
                    # 테이블 요소인 경우 table_elements 리스트에 추가합니다.
                    table_elements.append(element)
                else:
                    # 그 외의 요소는 모두 텍스트 요소로 간주하여 text_elements 리스트에 추가합니다.
                    text_elements.append(element)

            # 분류된 요소들을 페이지 키와 함께 새로운 딕셔너리에 저장합니다.
            parsed_page_elements[key] = {
                "image_elements": image_elements,
                "table_elements": table_elements,
                "text_elements": text_elements,
                "elements": page_element,  # 원본 페이지 요소도 함께 저장합니다.
            }

        # 파싱된 페이지 요소들을 포함한 새로운 GraphState 객체를 반환합니다.
        return GraphState(page_elements=parsed_page_elements)


class ImageCropperNode(BaseNode):
    """
    PDF 파일에서 이미지를 추출하고 크롭하는 노드
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "ImageCropperNode"

    def execute(self, state: GraphState) -> GraphState:
        """
        PDF 파일에서 이미지를 추출하고 크롭하는 함수

        :param state: GraphState 객체
        :return: 크롭된 이미지 정보가 포함된 GraphState 객체
        """
        pdf_file = state["filepath"]  # PDF 파일 경로
        page_numbers = state["page_numbers"]  # 처리할 페이지 번호 목록
        output_folder = os.path.splitext(pdf_file)[0]  # 출력 폴더 경로 설정
        os.makedirs(output_folder, exist_ok=True)  # 출력 폴더 생성

        cropped_images = dict()  # 크롭된 이미지 정보를 저장할 딕셔너리
        for page_num in page_numbers:
            pdf_image = ImageCropper.pdf_to_image(
                pdf_file, page_num
            )  # PDF 페이지를 이미지로 변환
            for element in state["page_elements"][page_num]["image_elements"]:
                if element["category"] == "chart":
                    # 이미지 요소의 좌표를 정규화
                    normalized_coordinates = ImageCropper.normalize_coordinates(
                        element["bounding_box"],
                        state["page_metadata"][page_num]["size"],
                    )

                    # 크롭된 이미지 저장 경로 설정
                    output_file = os.path.join(output_folder, f"{element['id']}.png")
                    # 이미지 크롭 및 저장
                    ImageCropper.crop_image(
                        pdf_image, normalized_coordinates, output_file
                    )
                    cropped_images[element["id"]] = output_file
                    print(f"page:{page_num}, id:{element['id']}, path: {output_file}")
        return GraphState(
            images=cropped_images
        )  # 크롭된 이미지 정보를 포함한 GraphState 반환


class TableCropperNode(BaseNode):
    """
    Table 이미지를 추출하고 크롭하는 노드
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "TableCropperNode"

    def execute(self, state: GraphState) -> GraphState:
        """
        PDF 파일에서 표를 추출하고 크롭하는 함수

        :param state: GraphState 객체
        :return: 크롭된 표 이미지 정보가 포함된 GraphState 객체
        """
        pdf_file = state["filepath"]  # PDF 파일 경로
        page_numbers = state["page_numbers"]  # 처리할 페이지 번호 목록
        output_folder = os.path.splitext(pdf_file)[0]  # 출력 폴더 경로 설정
        os.makedirs(output_folder, exist_ok=True)  # 출력 폴더 생성

        cropped_images = dict()  # 크롭된 표 이미지 정보를 저장할 딕셔너리
        for page_num in page_numbers:
            pdf_image = ImageCropper.pdf_to_image(
                pdf_file, page_num
            )  # PDF 페이지를 이미지로 변환
            for element in state["page_elements"][page_num]["table_elements"]:
                if element["category"] == "table":
                    # 표 요소의 좌표를 정규화
                    normalized_coordinates = ImageCropper.normalize_coordinates(
                        element["bounding_box"],
                        state["page_metadata"][page_num]["size"],
                    )

                    # 크롭된 표 이미지 저장 경로 설정
                    output_file = os.path.join(output_folder, f"{element['id']}.png")
                    # 표 이미지 크롭 및 저장
                    ImageCropper.crop_image(
                        pdf_image, normalized_coordinates, output_file
                    )
                    cropped_images[element["id"]] = output_file
                    print(f"page:{page_num}, id:{element['id']}, path: {output_file}")
        return GraphState(
            tables=cropped_images
        )  # 크롭된 표 이미지 정보를 포함한 GraphState 반환


class ExtractPageTextNode(BaseNode):
    """
    페이지별 텍스트를 추출하는 노드
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "ExtractPageTextNode"

    def execute(self, state: GraphState) -> GraphState:
        # 상태 객체에서 페이지 번호 목록을 가져옵니다.
        page_numbers = state["page_numbers"]

        # 추출된 텍스트를 저장할 딕셔너리를 초기화합니다.
        extracted_texts = dict()

        # 각 페이지 번호에 대해 반복합니다.
        for page_num in page_numbers:
            # 현재 페이지의 텍스트를 저장할 빈 문자열을 초기화합니다.
            extracted_texts[page_num] = ""

            # 현재 페이지의 모든 텍스트 요소에 대해 반복합니다.
            for element in state["page_elements"][page_num]["text_elements"]:
                # 각 텍스트 요소의 내용을 현재 페이지의 텍스트에 추가합니다.
                extracted_texts[page_num] += element["text"]

        # 추출된 텍스트를 포함한 새로운 GraphState 객체를 반환합니다.
        return GraphState(texts=extracted_texts)


class CreatePageSummaryNode(BaseNode):
    """
    페이지별 요약을 생성하는 노드
    """

    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = "CreatePageSummaryNode"
        self.api_key = api_key
        self.cache = {}

    def create_text_summary_chain(self):
        # 요약을 위한 프롬프트 템플릿을 정의합니다.
        prompt = PromptTemplate.from_template(
            """문장을 다음 요청에 따라 요약해 주세요.

            요청:
            1. 주요 요점을 bullet point로 요약하세요.
            2. 요약은 문맥과 동일한 언어로 작성하세요.
            3. 기술 용어는 번역하지 마세요.
            4. 불필요한 정보를 포함하지 마세요.
            5. 요약에는 중요한 엔티티와 수치 값을 포함해야 합니다.

        CONTEXT:
        {context}

        SUMMARY:"
        """
        )

        # ChatOpenAI 모델의 또 다른 인스턴스를 생성합니다.
        llm = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0,
            api_key=self.api_key,
        )

        # 문서 요약을 위한 체인을 생성합니다.
        # 이 체인은 여러 문서를 입력받아 하나의 요약된 텍스트로 결합합니다.
        text_summary_chain = create_stuff_documents_chain(llm, prompt)

        return text_summary_chain

    def execute(self, state: GraphState) -> GraphState:
        # state에서 텍스트 데이터를 가져옵니다.
        texts = state["texts"]

        # 요약된 텍스트를 저장할 딕셔너리를 초기화합니다.
        text_summary = dict()

        # texts.items()를 페이지 번호(키)를 기준으로 오름차순 정렬합니다.
        sorted_texts = sorted(texts.items(), key=lambda x: x[0])

        # 각 페이지의 텍스트를 Document 객체로 변환하여 입력 리스트를 생성합니다.
        inputs = [
            {"context": [Document(page_content=text)]}
            for page_num, text in sorted_texts
        ]
        # 요약 체인 생성
        text_summary_chain = self.create_text_summary_chain()

        # text_summary_chain을 사용하여 일괄 처리로 요약을 생성합니다.
        summaries = text_summary_chain.batch(inputs)

        # 생성된 요약을 페이지 번호와 함께 딕셔너리에 저장합니다.
        for page_num, summary in enumerate(summaries):
            text_summary[page_num] = summary

        # 요약된 텍스트를 포함한 새로운 GraphState 객체를 반환합니다.
        return GraphState(text_summary=text_summary)


class CreateImageSummaryNode(BaseNode):
    """
    이미지 요약을 생성하는 노드
    """

    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = "CreateImageSummaryNode"
        self.api_key = api_key

    def create_image_summary_data_batches(self, state: GraphState):
        # 이미지 요약을 위한 데이터 배치를 생성하는 함수
        data_batches = []

        # 페이지 번호를 오름차순으로 정렬
        page_numbers = sorted(list(state["page_elements"].keys()))

        for page_num in page_numbers:
            # 각 페이지의 요약된 텍스트를 가져옴
            text = state["text_summary"][page_num]
            # 해당 페이지의 모든 이미지 요소에 대해 반복
            for image_element in state["page_elements"][page_num]["image_elements"]:
                # 이미지 ID를 정수로 변환
                image_id = int(image_element["id"])

                # 데이터 배치에 이미지 정보, 관련 텍스트, 페이지 번호, ID를 추가
                data_batches.append(
                    {
                        "image": state["images"][image_id],  # 이미지 파일 경로
                        "text": text,  # 관련 텍스트 요약
                        "page": page_num,  # 페이지 번호
                        "id": image_id,  # 이미지 ID
                        "language": state["language"],  # 언어
                    }
                )
        # 생성된 데이터 배치를 GraphState 객체에 담아 반환
        return data_batches

    def execute(self, state: GraphState):
        image_summary_data_batches = self.create_image_summary_data_batches(state)
        # 이미지 요약 추출
        # extract_image_summary 함수를 호출하여 이미지 요약 생성
        image_summaries = extract_image_summary.invoke(
            image_summary_data_batches,
        )

        # 이미지 요약 결과를 저장할 딕셔너리 초기화
        image_summary_output = dict()

        # 각 데이터 배치와 이미지 요약을 순회하며 처리
        for data_batch, image_summary in zip(
            image_summary_data_batches, image_summaries
        ):
            # 데이터 배치의 ID를 키로 사용하여 이미지 요약 저장
            image_summary_output[data_batch["id"]] = image_summary

        # 이미지 요약 결과를 포함한 새로운 GraphState 객체 반환
        return GraphState(image_summary=image_summary_output)


class CreateTableSummaryNode(BaseNode):
    """
    테이블 요약을 생성하는 노드
    """

    def __init__(self, api_key, **kwargs):
        super().__init__(**kwargs)
        self.name = "CreateTableSummaryNode"
        self.api_key = api_key

    def create_table_summary_data_batches(self, state: GraphState):
        # 테이블 요약을 위한 데이터 배치를 생성하는 함수
        data_batches = []

        # 페이지 번호를 오름차순으로 정렬
        page_numbers = sorted(list(state["page_elements"].keys()))

        for page_num in page_numbers:
            # 각 페이지의 요약된 텍스트를 가져옴
            text = state["text_summary"][page_num]
            # 해당 페이지의 모든 테이블 요소에 대해 반복
            for image_element in state["page_elements"][page_num]["table_elements"]:
                # 테이블 ID를 정수로 변환
                image_id = int(image_element["id"])

                # 데이터 배치에 테이블 정보, 관련 텍스트, 페이지 번호, ID를 추가
                data_batches.append(
                    {
                        "table": state["tables"][image_id],  # 테이블 데이터
                        "text": text,  # 관련 텍스트 요약
                        "page": page_num,  # 페이지 번호
                        "id": image_id,  # 테이블 ID
                        "language": state["language"],  # 언어
                    }
                )
        # 생성된 데이터 배치를 GraphState 객체에 담아 반환
        # return GraphState(table_summary_data_batches=data_batches)
        return data_batches

    def execute(self, state: GraphState):
        table_summary_data_batches = self.create_table_summary_data_batches(state)
        # 테이블 요약 추출
        table_summaries = extract_table_summary.invoke(
            table_summary_data_batches,
        )

        # 테이블 요약 결과를 저장할 딕셔너리 초기화
        table_summary_output = dict()

        # 각 데이터 배치와 테이블 요약을 순회하며 처리
        for data_batch, table_summary in zip(
            table_summary_data_batches, table_summaries
        ):
            # 데이터 배치의 ID를 키로 사용하여 테이블 요약 저장
            table_summary_output[data_batch["id"]] = table_summary

        # 테이블 요약 결과를 포함한 새로운 GraphState 객체 반환
        return GraphState(
            table_summary=table_summary_output,
            table_summary_data_batches=table_summary_data_batches,
        )


class TableMarkdownExtractorNode(BaseNode):
    """
    테이블 이미지를 마크다운 테이블로 변환하는 노드
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "TableMarkdownExtractorNode"

    def execute(self, state: GraphState):
        # table_markdown_extractor를 사용하여 테이블 마크다운 생성
        # state["table_summary_data_batches"]에 저장된 테이블 데이터를 사용
        table_markdowns = table_markdown_extractor.invoke(
            state["table_summary_data_batches"],
        )

        # 결과를 저장할 딕셔너리 초기화
        table_markdown_output = dict()

        # 각 데이터 배치와 생성된 테이블 마크다운을 매칭하여 저장
        for data_batch, table_summary in zip(
            state["table_summary_data_batches"], table_markdowns
        ):
            # 데이터 배치의 id를 키로 사용하여 테이블 마크다운 저장
            table_markdown_output[data_batch["id"]] = table_summary

        # 새로운 GraphState 객체 반환, table_markdown 키에 결과 저장
        return GraphState(table_markdown=table_markdown_output)
