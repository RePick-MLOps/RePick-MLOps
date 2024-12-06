import logging
import os
import re
import requests
import sys
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError
from webdriver_manager.chrome import ChromeDriverManager

from src.data_collection.db.database_config import get_db_connection

# 로그 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# 환경 변수 로드
load_dotenv()

# 네이버 리서치 URL
url = "https://finance.naver.com/research/"


def setup_unique_index():
    try:
        db = get_db_connection()
        reports_collection = db["reports"]
        reports_collection.create_index("report_id", unique=True)
        logging.info("Database unique index 설정 완료")
    except Exception as e:
        logging.error(f"데이터베이스 연결 또는 인덱스 생성 실패: {e}")
        raise


# Chrome 드라이버 초기화
def init_driver():
    try:
        driver_service = Service(ChromeDriverManager().install())

        # Chrome 옵션 설정
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")  # Headless 모드
        chrome_options.add_argument("--no-sandbox")  # 샌드박스 비활성화
        chrome_options.add_argument(
            "--disable-dev-shm-usage"
        )  # 공유 메모리 사용 비활성화
        chrome_options.add_argument("--disable-gpu")  # GPU 하드웨어 가속 비활성화
        chrome_options.add_argument("--window-size=1920,1080")  # 윈도우 크기 설정
        chrome_options.add_argument("--disable-extensions")  # 확장 프로그램 비활성화
        chrome_options.add_argument("--disable-infobars")  # 정보 표시줄 비활성화
        chrome_options.add_argument("--remote-debugging-port=9222")  # 디버깅 포트 설정

        # Chrome 드라이버 초기화
        driver = webdriver.Chrome(service=driver_service, options=chrome_options)

        logging.info("Chrome driver 초기화 완료")
        return driver

    except Exception as e:
        logging.error(f"Chrome driver 초기화 실패: {str(e)}")
        # Chrome 버전 확인
        try:
            import subprocess

            chrome_version = subprocess.check_output(["chromium", "--version"]).decode()
            logging.info(f"Installed Chrome version: {chrome_version}")
        except Exception as chrome_error:
            logging.error(f"Chrome version check failed: {str(chrome_error)}")
        raise


# 종목분석 페이지 탐색
def navigate_company_report_page(driver):
    try:
        driver.get(url)

        company_report_tab = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='contentarea_left']/div[1]/h4/span/a")
            )
        )
        company_report_tab.click()

        company_url = driver.find_element(
            By.XPATH, "//meta[@property='og:url']"
        ).get_attribute("content")
        logging.info("종목분석 탭 클릭 완료")
        driver.get(company_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody")
            )
        )
        logging.info("종목분석 페이지 로딩 완료")
        return True
    except Exception as e:
        logging.error(f"페이지 탐색 오류: {e}")
        return False


# 산업분석 페이지 탐색
def navigate_industry_report_page(driver):
    try:
        driver.get(url)

        industry_report_tab = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='contentarea_left']/div[3]/h4/span/a")
            )
        )
        industry_report_tab.click()

        industry_url = driver.find_element(
            By.XPATH, "//meta[@property='og:url']"
        ).get_attribute("content")
        logging.info("산업분석 탭 클릭 완료")
        driver.get(industry_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody")
            )
        )
        logging.info("산업분석 페이지 로딩 완료")
        return True
    except Exception as e:
        logging.error(f"산업분석 페이지 탐색 오류: {e}")
        return False


# 리포트 데이터 추출
def extract_report_data(driver, report_type):
    report_data_list = []
    rows = driver.find_elements(
        By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody/tr"
    )

    for row in rows[2:47]:
        try:
            if report_type == "Company":
                company_name = row.find_element(By.XPATH, ".//td[1]/a").text
                report_title = row.find_element(By.XPATH, ".//td[2]").text
                securities_firm = row.find_element(By.XPATH, ".//td[3]").text
                pdf_link = row.find_element(By.XPATH, ".//td[4]/a").get_attribute(
                    "href"
                )
                report_date = row.find_element(By.XPATH, ".//td[5]").text

                href = row.find_element(By.XPATH, ".//td[1]/a").get_attribute("href")
                match = re.search(r"code=(\d+)", href)
                company_code = match.group(1) if match else None

                match = re.search(r"(\d+)\.pdf$", pdf_link)
                report_id = match.group(1) if match else None

                if company_code and report_id:
                    report_data = {
                        "report_id": int(report_id),
                        "company_name": company_name,
                        "company_code": company_code,
                        "report_title": report_title,
                        "securities_firm": securities_firm,
                        "report_date": datetime.strptime(
                            report_date, "%y.%m.%d"
                        ).strftime("%Y-%m-%d"),
                        "pdf_link": pdf_link,
                        "report_type": report_type,
                    }
                    report_data_list.append(report_data)

            elif report_type == "Industry":
                sector = row.find_element(By.XPATH, ".//td[1]").text
                report_title = row.find_element(By.XPATH, ".//td[2]").text
                securities_firm = row.find_element(By.XPATH, ".//td[3]").text
                pdf_link = row.find_element(By.XPATH, ".//td[4]/a").get_attribute(
                    "href"
                )
                report_date = row.find_element(By.XPATH, ".//td[5]").text

                match = re.search(r"(\d+)\.pdf$", pdf_link)
                report_id = match.group(1) if match else None

                if report_id:
                    report_data = {
                        "report_id": int(report_id),
                        "sector": sector,
                        "report_title": report_title,
                        "securities_firm": securities_firm,
                        "report_date": datetime.strptime(
                            report_date, "%y.%m.%d"
                        ).strftime("%Y-%m-%d"),
                        "pdf_link": pdf_link,
                        "report_type": report_type,
                    }
                    report_data_list.append(report_data)

        except Exception as e:
            logging.warning(f"데이터 추출 오류: {e}")

    return report_data_list


# 데이터베이스에 저장
def insert_to_db(report_data_list):
    db = get_db_connection()
    reports_collection = db["reports"]

    for report_data in report_data_list:
        try:
            reports_collection.insert_one(report_data)
            logging.info(f"{report_data['report_id']} 데이터베이스에 저장 완료")
        except DuplicateKeyError:
            logging.warning(
                f"{report_data['report_id']} 중복으로 인해 저장되지 않았습니다."
            )


# 다음 페이지 URL 가져오기
def get_next_page_url(driver, current_page, is_industry=False):
    try:
        current_page_element = driver.find_element(By.XPATH, "//td[@class='on']/a")
        current_page = int(current_page_element.text)

        next_page = current_page + 1

        if is_industry:
            next_page_url = f"https://finance.naver.com/research/industry_list.naver?&page={next_page}"
        else:
            next_page_url = f"https://finance.naver.com/research/company_list.naver?&page={next_page}"

        logging.info(
            f"현재 페이지: {current_page}, 다음 페이지로 이동: {next_page_url}"
        )
        return next_page_url
    except Exception as e:
        logging.error(f"다음 페이지 URL을 찾는 중 오류 발생: {e}")
        return None


def crawl_reports(driver, max_pages, report_type, get_page_url_func, extract_data_func):
    report_data_list = []
    current_page = 1

    while current_page <= max_pages:
        if current_page == 1:
            report_data_list.extend(extract_data_func(driver, report_type))
            logging.info(f"페이지 {current_page} 데이터 크롤링 완료")
        else:
            next_page_url = get_page_url_func(
                driver, current_page, report_type == "Industry"
            )
            if not next_page_url:
                logging.info("다음 페이지가 없거나 오류 발생")
                break

            driver.get(next_page_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody")
                )
            )
            logging.info(f"페이지 {current_page} 로딩 완료")
            report_data_list.extend(extract_data_func(driver, report_type))
            logging.info(f"페이지 {current_page} 데이터 크롤링 완료")

        current_page += 1

    return report_data_list


# 메인 크롤링 함수
def crawl_pdfs():
    driver = init_driver()

    if navigate_company_report_page(driver):
        company_report_data_list = crawl_reports(
            driver,
            max_pages=10,
            report_type="Company",
            get_page_url_func=get_next_page_url,
            extract_data_func=extract_report_data,
        )
        if company_report_data_list:
            insert_to_db(company_report_data_list)

    driver.get(url)
    if navigate_industry_report_page(driver):
        industry_report_data_list = crawl_reports(
            driver,
            max_pages=10,
            report_type="Industry",
            get_page_url_func=get_next_page_url,
            extract_data_func=extract_report_data,
        )
        if industry_report_data_list:
            insert_to_db(industry_report_data_list)

    driver.quit()


# 실행
if __name__ == "__main__":
    setup_unique_index()
    crawl_pdfs()
