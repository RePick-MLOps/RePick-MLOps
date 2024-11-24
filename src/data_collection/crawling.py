import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError
import requests
import sys
import os
import re
from datetime import datetime
from webdriver_manager.chrome import ChromeDriverManager

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.db.database_config import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()
driver_path = os.getenv("CHROME_DRIVER_PATH")
if not driver_path:
    raise ValueError("CHROME_DRIVER_PATH가 설정되지 않았습니다.")

url = "https://finance.naver.com/research/"

def setup_unique_index():
    db = get_db_connection()
    reports_collection = db['reports']
    
    reports_collection.create_index("report_id", unique=True)
    logging.info("Database unique index 설정 완료")

def init_driver():
    driver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=driver_service)
    logging.info("Chrome driver 초기화 완료")
    return driver

def navigate_stock_report_page(driver):
    try:
        driver.get(url)

        stock_report_tab = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='contentarea_left']/div[1]/h4/span/a"))
        )
        stock_report_tab.click()

        meta_url = driver.find_element(By.XPATH, "//meta[@property='og:url']").get_attribute('content')
        logging.info("종목분석 탭 클릭 완료")
        driver.get(meta_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody"))
        )
        logging.info("종목분석 페이지 로딩 완료")
        return True
    except Exception as e:
        logging.error(f"페이지 탐색 오류: {e}")
        return False

def extract_report_data(driver):
    stock_report_data_list = []
    rows = driver.find_elements(By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody/tr")

    for row in rows[2:47]:
        try:
            sector_name = row.find_element(By.XPATH, ".//td[1]/a").text
            if not sector_name:
                continue
            href = row.find_element(By.XPATH, ".//td[1]/a").get_attribute('href')
            company_name = row.find_element(By.XPATH, ".//td[2]/a").text
            report_title = row.find_element(By.XPATH, ".//td[3]").text
            pdf_link = row.find_element(By.XPATH, ".//td[4]/a").get_attribute('href')
            report_date = row.find_element(By.XPATH, ".//td[5]").text
            
            match = re.search(r'code=(\d+)', href)
            company_code = match.group(1) if match else None

            match = re.search(r'(\d+)\.pdf$', pdf_link)
            report_id = match.group(1) if match else None

            if company_code and report_id:
                report_data = {
                    "report_id": int(report_id),
                    "sector_name": sector_name,
                    "company_code": company_code,
                    "company_name": company_name,
                    "report_title": report_title,
                    "report_date": datetime.strptime(report_date, "%y.%m.%d").strftime("%Y-%m-%d"),
                    "pdf_link": pdf_link
                }
                stock_report_data_list.append(report_data)
        except Exception as e:
            logging.warning(f"데이터 추출 오류: {e}")

    return stock_report_data_list

def insert_to_db(stock_report_data_list):
    db = get_db_connection()
    reports_collection = db['reports']

    for report_data in stock_report_data_list:
        try:
            reports_collection.insert_one(report_data)
            logging.info(f"{report_data['report_id']} 데이터베이스에 저장 완료")
        except DuplicateKeyError:
            logging.warning(f"{report_data['report_id']} 중복으로 인해 저장되지 않았습니다.")

def get_next_page_url(driver, current_page):
    try:
        current_page_element = driver.find_element(By.XPATH, "//td[@class='on']/a")
        current_page = int(current_page_element.text)

        next_page = current_page + 1
        next_page_url = f"https://finance.naver.com/research/company_list.naver?&page={next_page}"
        logging.info(f"현재 페이지: {current_page}, 다음 페이지로 이동: {next_page_url}")
        return next_page_url
    except Exception as e:
        logging.error(f"다음 페이지 URL을 찾는 중 오류 발생: {e}")
        return None

def crawl_pdfs():
    driver = init_driver()

    if navigate_stock_report_page(driver):
        stock_report_data_list = extract_report_data(driver)

        current_page = 1
        max_pages = 5  # 최대 5페이지

        while current_page <= max_pages:
            next_page_url = get_next_page_url(driver, current_page)
            if not next_page_url:
                logging.info("다음 페이지가 없거나 오류 발생")
                break

            driver.get(next_page_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='contentarea_left']/div[2]/table[1]/tbody"))
            )
            logging.info(f"페이지 {current_page + 1} 로딩 완료")

            stock_report_data_list.extend(extract_report_data(driver))
            logging.info(f"페이지 {current_page + 1} 데이터 크롤링 완료")

            current_page += 1  # 페이지 번호 증가

        if stock_report_data_list:
            insert_to_db(stock_report_data_list)
        
        driver.quit()
    else:
        logging.error("종목분석 페이지 이동 실패로 데이터 수집 중단")

if __name__ == "__main__":
    setup_unique_index()
    crawl_pdfs()