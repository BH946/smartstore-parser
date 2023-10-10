import logging
import os
import dotenv
dotenv.load_dotenv()
logging.basicConfig(level=logging.DEBUG, filename='./logs/dev.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s') # 개발용 debug 레벨 사용
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
# chromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"]) # 불필요한 에러 메시지 제거코드
# chromeOptions.add_argument("headless"); # 헤드리스 사용
chromeOptions.add_argument("disable-infobars") # 정보 표시줄 사용X
chromeOptions.add_argument("disable-extensions"); # 확장 사용안함
chromeOptions.add_argument("disable-popup-blocking"); #팝업 X
chromeOptions.add_argument("disable-gpu");	# gpu 비활성화
# chromeOptions.add_argument("blink-settings=imagesEnabled=false"); # 이미지 다운 안받음
chromeOptions.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36") # 사용자인척 위장
chromeOptions.add_argument('no-sandbox')
chromeOptions.add_argument('disable-dev-shm-usage')
chromeService = ChromeService(ChromeDriverManager().install()) # 크롬드라이버 자동

#############################################################
# global variable setting
DOWNLOAD_FILES_PATH = os.getenv("DOWNLOAD_FILES_PATH")
urlArr = os.getenv("NAVER_LOGIN_URL").split(",") # [url, name]
NAVER_ID = os.getenv("NAVER_ID")
NAVER_PW = os.getenv("NAVER_PW")

#############################################################

# selenium headless background download activate
def enable_download(driver):
  logging.debug('selenium headless 백그라운드 다운로드 기능 활성화')
  driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
  params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': f'{DOWNLOAD_FILES_PATH}'}}
  driver.execute("send_command", params)

def main():
  print("TEST env :"+os.getenv("LOG_FILES_PATH"))
  logging.debug("test dev log")
  driver = webdriver.Chrome(service=chromeService, options=chromeOptions)
  enable_download(driver) # 다운로드 경로 설정
  driver.maximize_window()
  driver.get_screenshot_as_file("test.png") # test

  # 네이버 로그인(2차 인증 포함) - 로그인된 driver 계속 사용예정
  login(driver, urlArr, NAVER_ID, NAVER_PW)

  # smartstore-products
  product(driver, 0) # 0:mamami, 1:phonefriend

  # web-parse
  parse_mamami(driver)

  logging.debug("파싱이 완료되었습니다. DB를 확인하세요.")
  driver.quit()
  

if __name__ == "__main__":
  main() # main 함수
