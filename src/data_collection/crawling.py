import logging
import os
import re
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
        chrome_options = webdriver.ChromeOptions()
        if os.getenv("JENKINS_URL"):
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.binary_location = "/usr/bin/google-chrome"

            # Chrome 버전 확인 및 맞는 ChromeDriver 설치
            from selenium.webdriver.chrome.service import Service as ChromeService
            from webdriver_manager.chrome import ChromeDriverManager

            driver_service = ChromeService(ChromeDriverManager().install())
        else:
            driver_service = Service("/usr/local/bin/chromedriver")

        driver = webdriver.Chrome(service=driver_service, options=chrome_options)
        logging.info("Chrome driver 초기화 완료")
        return driver

    except Exception as e:
        logging.error(f"Chrome driver 초기화 실패: {str(e)}")
        raise

# 페이지 이동 로직
def navigate_to_tab(driver, tab_xpath, content_xpath, description):
    try:
        driver.get(url)
        tab = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, tab_xpath))
        )
        tab.click()
        logging.info(f"{description} 탭 클릭 완료")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, content_xpath))
        )
        logging.info(f"{description} 페이지 로딩 완료")
        return True
    except Exception as e:
        logging.error(f"{description} 페이지 탐색 오류: {e}")
        return False


# 종목분석 페이지 탐색
def navigate_company_report_page(driver):
    return navigate_to_tab(
        driver,
        tab_xpath="//*[@id='contentarea_left']/div[1]/h4/span/a",
        content_xpath="//*[@id='contentarea_left']/div[2]/table[1]/tbody",
        description="종목분석",
    )


# 산업분석 페이지 탐색
def navigate_industry_report_page(driver):
    return navigate_to_tab(
        driver,
        tab_xpath="//*[@id='contentarea_left']/div[3]/h4/span/a",
        content_xpath="//*[@id='contentarea_left']/div[2]/table[1]/tbody",
        description="산업분석",
    )


# 공통 데이터 추출
def extract_common_data(row, field_mappings):
    extracted_data = {}
    for field, xpath in field_mappings.items():
        try:
            if field == "pdf_link":
                extracted_data[field] = row.find_element(By.XPATH, xpath).get_attribute(
                    "href"
                )
            else:
                extracted_data[field] = row.find_element(By.XPATH, xpath).text
        except Exception as e:
            logging.warning(f"{field} 추출 오류: {e}")
    return extracted_data
        description="종목분석"
    )


# 산업분석 페이지 탐색
def navigate_industry_report_page(driver):
    return navigate_to_tab(
        driver,
        tab_xpath="//*[@id='contentarea_left']/div[3]/h4/span/a",
        content_xpath="//*[@id='contentarea_left']/div[2]/table[1]/tbody",
        description="산업분석"
    )

# 공통 데이터 추출
def extract_common_data(row, field_mappings):
    extracted_data = {}
    for field, xpath in field_mappings.items():
        try:
            if field == "pdf_link":
                extracted_data[field] = row.find_element(By.XPATH, xpath).get_attribute("href")
            else:
                extracted_data[field] = row.find_element(By.XPATH, xpath).text
        except Exception as e:
            logging.warning(f"{field} 추출 오류: {e}")
    return extracted_data

# 리포트 데이터 추출
def extract_report_data(driver, report_type):
    report_data_list = []
    rows = driver.find_elements(
        By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody/tr"
    )

    field_mappings = {
        "Company": {
            "company_name": ".//td[1]/a",
            "report_title": ".//td[2]",
            "securities_firm": ".//td[3]",
            "pdf_link": ".//td[4]/a",
            "report_date": ".//td[5]",
        },
        "Industry": {
            "sector": ".//td[1]",
            "report_title": ".//td[2]",
            "securities_firm": ".//td[3]",
            "pdf_link": ".//td[4]/a",
            "report_date": ".//td[5]",
        },
    }

    for row in rows[2:47]:
        try:
            data = extract_common_data(row, field_mappings[report_type])
            # 추가 데이터 처리
            if "pdf_link" in data:
                match = re.search(r"(\d+)\.pdf$", data["pdf_link"])
                data["report_id"] = int(match.group(1)) if match else None
            if "report_date" in data:
                data["report_date"] = datetime.strptime(
                    data["report_date"], "%y.%m.%d"
                ).strftime("%Y-%m-%d")
            if data.get("report_id"):
                data["report_type"] = report_type
                report_data_list.append(data)
        except Exception as e:
            logging.warning(f"데이터 추출 오류: {e}")

    return report_data_list

def save_to_database(data_list, collection_name):
    db = get_db_connection()
    collection = db[collection_name]

    for data in data_list:
        try:
            collection.insert_one(data)
            logging.info(f"{data['report_id']} 데이터베이스에 저장 완료")
        except DuplicateKeyError:
            logging.warning(f"{data['report_id']} 중복으로 인해 저장되지 않았습니다.")


# 다음 페이지 URL 가져오기
def get_next_page_url(driver, current_page, base_url):
    try:
        next_page = current_page + 1
        next_page_url = f"{base_url}&page={next_page}"
        logging.info(
            f"현재 페이지: {current_page}, 다음 페이지로 이동: {next_page_url}"
        )
        logging.info(f"현재 페이지: {current_page}, 다음 페이지로 이동: {next_page_url}")
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
            next_page_url = get_page_url_func(driver, current_page)
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

# 중복 확인
def is_duplicate(report_id):
    db = get_db_connection()
    return db["reports"].find_one({"report_id": report_id}) is not None

# 중복 확인
def is_duplicate(report_id):
    db = get_db_connection()
    return db["reports"].find_one({"report_id": report_id}) is not None


def crawl_pdfs():
    driver = init_driver()
    duplicate_found = False

    for report_type, navigate_func, base_url in [
        (
            "Company",
            navigate_company_report_page,
            "https://finance.naver.com/research/company_list.naver?",
        ),
        (
            "Industry",
            navigate_industry_report_page,
            "https://finance.naver.com/research/industry_list.naver?",
        ),
        ("Company", navigate_company_report_page, "https://finance.naver.com/research/company_list.naver?"),
        ("Industry", navigate_industry_report_page, "https://finance.naver.com/research/industry_list.naver?")
    ]:
        if navigate_func(driver):
            for current_page in range(1, 11):  # max_pages=10
                if duplicate_found:
                    logging.info(
                        f"중복 발견으로 {report_type} 크롤링 중단. 페이지: {current_page}"
                    )
                    break  # 중복 발견 시 현재 타입의 크롤링 중단

                    logging.info(f"중복 발견으로 {report_type} 크롤링 중단. 페이지: {current_page}")
                    break  # 중복 발견 시 현재 타입의 크롤링 중단
                
                # URL 변경 및 페이지 이동
                if current_page > 1:
                    next_page_url = f"{base_url}&page={current_page}"
                    driver.get(next_page_url)

                # 데이터 추출
                report_data_list = extract_report_data(driver, report_type)

                
                # 데이터 추출
                report_data_list = extract_report_data(driver, report_type)

                # 중복 확인 로직
                for data in report_data_list:
                    report_id = data.get("report_id")
                    if is_duplicate(report_id):  # 중복 확인 함수 호출
                        logging.warning(f"중복된 report_id 발견: {report_id}")
                        duplicate_found = True
                        break  # 중복 발생 시 다음 페이지 크롤링 중단

                if not duplicate_found:
                    save_to_database(report_data_list, "reports")

            if duplicate_found and report_type == "Industry":
                break  # 산업 분석에서도 중복 발생 시 전체 크롤링 종료

    driver.quit()

# 실행
if __name__ == "__main__":
    setup_unique_index()
    crawl_pdfs()