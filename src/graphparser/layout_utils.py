import os
import json
import pickle
import requests
import pymupdf
from PIL import Image


class LayoutAnalyzer:
    def __init__(self, api_key):
        """
        LayoutAnalyzer 클래스의 생성자

        :param api_key: Upstage API 인증을 위한 API 키
        """
        self.api_key = api_key

    def _upstage_layout_analysis(self, input_file):
        """
        Upstage의 레이아웃 분석 API를 호출하여 문서 분석을 수행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
        # API 요청 헤더 설정
        headers = {"Authorization": f"Bearer {self.api_key}"}

        # API 요청 데이터 설정 (OCR 비활성화)
        data = {"ocr": False}

        # 분석할 PDF 파일 열기
        files = {"document": open(input_file, "rb")}

        # API 요청 보내기
        response = requests.post(
            "https://api.upstage.ai/v1/document-ai/layout-analysis",
            headers=headers,
            data=data,
            files=files,
        )

        # API 응답 처리 및 결과 저장
        if response.status_code == 200:
            # 분석 결과를 저장할 JSON 파일 경로 생성
            output_file = os.path.splitext(input_file)[0] + ".json"

            # 분석 결과를 JSON 파일로 저장
            with open(output_file, "w") as f:
                json.dump(response.json(), f, ensure_ascii=False)

            return output_file
        else:
            # API 요청이 실패한 경우 예외 발생
            raise ValueError(f"API 요청 실패. 상태 코드: {response.status_code}")

    def execute(self, input_file):
        """
        주어진 입력 파일에 대해 레이아웃 분석을 실행합니다.

        :param input_file: 분석할 PDF 파일의 경로
        :return: 분석 결과가 저장된 JSON 파일의 경로
        """
        return self._upstage_layout_analysis(input_file)


class ImageCropper:
    @staticmethod
    def pdf_to_image(pdf_file, page_num, dpi=300):
        """
        PDF 파일의 특정 페이지를 이미지로 변환하는 메서드

        :param page_num: 변환할 페이지 번호 (1부터 시작)
        :param dpi: 이미지 해상도 (기본값: 300)
        :return: 변환된 이미지 객체
        """
        with pymupdf.open(pdf_file) as doc:
            page = doc[page_num].get_pixmap(dpi=dpi)
            target_page_size = [page.width, page.height]
            page_img = Image.frombytes("RGB", target_page_size, page.samples)
        return page_img

    @staticmethod
    def normalize_coordinates(coordinates, output_page_size):
        """
        좌표를 정규화하는 정적 메서드

        :param coordinates: 원본 좌표 리스트
        :param output_page_size: 출력 페이지 크기 [너비, 높이]
        :return: 정규화된 좌표 (x1, y1, x2, y2)
        """
        x_values = [coord["x"] for coord in coordinates]
        y_values = [coord["y"] for coord in coordinates]
        x1, y1, x2, y2 = min(x_values), min(y_values), max(x_values), max(y_values)

        return (
            x1 / output_page_size[0],
            y1 / output_page_size[1],
            x2 / output_page_size[0],
            y2 / output_page_size[1],
        )

    @staticmethod
    def crop_image(img, coordinates, output_file):
        """
        이미지를 주어진 좌표에 따라 자르고 저장하는 정적 메서드

        :param img: 원본 이미지 객체
        :param coordinates: 정규화된 좌표 (x1, y1, x2, y2)
        :param output_file: 저장할 파일 경로
        """
        img_width, img_height = img.size
        x1, y1, x2, y2 = [
            int(coord * dim)
            for coord, dim in zip(coordinates, [img_width, img_height] * 2)
        ]
        cropped_img = img.crop((x1, y1, x2, y2))
        cropped_img.save(output_file)


def save_state(state, filepath):
    """상태를 pickle 파일로 저장합니다."""
    base, _ = os.path.splitext(filepath)
    with open(f"{base}.pkl", "wb") as f:
        pickle.dump(state, f)


def load_state(filepath):
    """pickle 파일에서 상태를 불러옵니다."""
    base, _ = os.path.splitext(filepath)
    with open(f"{base}.pkl", "rb") as f:
        return pickle.load(f)
