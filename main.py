print("start") # 디버깅은 헤드리스(자유), main쪽 한줄 주석 하기, .env 본인 id,pw로 수정
import logging
from logging import handlers
import os
import pathlib
os.chdir(pathlib.Path(__file__).parent.absolute())
import dotenv

# 최우선 : env 설정, log 설정
dotenv.load_dotenv()
log_handler = handlers.RotatingFileHandler(os.path.join('logs','dev-parser.log'), mode='a', maxBytes=1024*1000, backupCount=5) # 1000KB=1MB 백업5개까지 최대로 Rotate
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log_handler.setFormatter(log_formatter)
root_logger=logging.getLogger() # root
root_logger.setLevel(logging.INFO)
root_logger.addHandler(log_handler)

from pytz import timezone
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager # 자동
from src.web_parse.parse_mamami import parse_mamami # parse_mamami 함수
from src.smartstore.product import product
from src.login.login import login

# 자동 드라이버 설치하므로 경로 필요X
chromeOptions = ChromeOptions()
# chromeOptions.add_argument("window-size=1920x1200") # window-size 설정
# chromeOptions.add_experimental_option("detach", True) # 브라우저 꺼짐 방지 옵션
chromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"]) # 불필요한 에러 메시지 제거코드
chromeOptions.add_argument("headless=old"); # 헤드리스 사용 (old로 기존 헤드리스 사용)
chromeOptions.add_argument("disable-infobars") # 정보 표시줄 사용X
chromeOptions.add_argument("disable-extensions"); # 확장 사용안함
chromeOptions.add_argument("disable-popup-blocking"); #팝업 X
chromeOptions.add_argument("disable-gpu");	# gpu 비활성화
# chromeOptions.add_argument("blink-settings=imagesEnabled=false"); # 이미지 다운 안받음
chromeOptions.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36") # 사용자인척 위장
chromeOptions.add_argument('no-sandbox')
chromeOptions.add_argument('disable-dev-shm-usage')
chromedriverPath = ChromeDriverManager().install()
# chromedriver 경로 확인 및 명시적으로 실행 파일 경로 지정 -> THIRD_PARTY_NOTICES.chromedriver 로 선택되는 문제 해결
if os.path.isfile(os.path.join(os.path.dirname(chromedriverPath), "chromedriver")):
    chromedriverPath = os.path.join(os.path.dirname(chromedriverPath), "chromedriver")
chromeService = ChromeService(chromedriverPath) # 크롬드라이버 자동
print(f"Installed ChromeDriver path: {chromedriverPath}")

#############################################################
# global variable setting
DOWNLOAD_FILES_PATH = os.getenv("DOWNLOAD_FILES_PATH")
DOWNLOAD_FILES_PATH = os.path.join(os.getcwd(),DOWNLOAD_FILES_PATH)
urlArr = os.getenv("NAVER_LOGIN_URL").split(",") # [url, name]
NAVER_ID = os.getenv("NAVER_ID")
NAVER_PW = os.getenv("NAVER_PW")
LISTNAME = os.getenv("LISTNAME").split(",")

#############################################################

# 다운로드 경로설정
chromeOptions.add_experimental_option("prefs", {
  "download.default_directory": DOWNLOAD_FILES_PATH,
  "download.prompt_for_download": False,
  "download.directory_upgrade": True,
  "safebrowsing.enabled": True
})

def main():
  try:
    logging.debug("test dev log")
    driver = webdriver.Chrome(service=chromeService, options=chromeOptions)
    driver.maximize_window()
    driver.get_screenshot_as_file("test.png") # test

    # (디버깅도움)금일의 product.csv 존재여부 파악
    count = -1
    # count = findProduct() # 첨부터 실행을 반드시 하려면 이곳 주석
    if count == len(LISTNAME):
      logging.info(f"이미 product들이 존재하므로 parse로 넘어갑니다.")
      # web-parse
      logging.info("parse_mamami() 함수 입장")
      parse_mamami(driver)
      logging.info("parse_mamami() 함수 끝")
    else:
      # 네이버 로그인(2차 인증 포함) - 로그인된 driver
      logging.info("login() 함수 입장")
      login(driver, urlArr, NAVER_ID, NAVER_PW)
      logging.info("login() 함수 끝")

      # smartstore-products
      logging.info("product() 함수 입장")
      product(driver, 0) # 0:mamami, 1:phonefriend
      logging.info("product() 함수 끝")

      # web-parse
      logging.info("parse_mamami() 함수 입장")
      parse_mamami(driver)
      logging.info("parse_mamami() 함수 끝")

    logging.info("파싱이 완료되었습니다. DB를 확인하세요.")
  except Exception as e:
    logging.error(f"예외 발생: {e}", exc_info=True) # exc_info: stack 트레이스 정보도 포함
    print(f"예외 발생(자세한 내용은 로그 참고): {e}")
  finally:
    driver.quit() # 항상 실행


def findProduct():
  count=0
  todayDate = datetime.now(timezone('Asia/Seoul')).strftime("%Y%m%d")
  for lstName in LISTNAME:
    fileList = os.listdir(DOWNLOAD_FILES_PATH)
    fileListCsv = [file for file in fileList if file.endswith('.csv')]
    fileName = ""
    for file in fileListCsv:
      fileName = file
      if (fileName.find("스마트스토어상품_" + lstName + todayDate) != -1):
        count+=1
  return count


if __name__ == "__main__":
  main() # main 함수
