import sys
import logging
import os
import time
from pytz import timezone
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#############################################################
# global variable setting
LISTNAME = os.getenv("LISTNAME").split(",")
DOWNLOAD_FILES_PATH = os.getenv("DOWNLOAD_FILES_PATH")
DOWNLOAD_FILES_PATH = os.path.join(os.getcwd(),DOWNLOAD_FILES_PATH)
urlArr = os.getenv("NAVER_LOGIN_URL").split(",") # [url, name]

#############################################################

######## 스마트스토어 특징 정리
# 1. 브랜드명 사용 -> EX)"마마미"

#############################################################

def product(driver, idx):
  wait = WebDriverWait(driver, 10)
  driver.get(urlArr[0])
  wait.until(EC.presence_of_element_located((By.ID, "seller-content"))) # 페이지로딩
  time.sleep(1)
  # (1)브랜드명 기입
  driver.find_element(by=By.CSS_SELECTOR,value='#brand_name').send_keys(LISTNAME[idx])
  # (2)품절, 판매금지 체크 -> 판매중은 기본값으로 이미 체크
  searchLabel=driver.find_elements(by=By.TAG_NAME,value='label')
  for label in searchLabel:
    if label.text == "품절" or label.text == "판매중지":
      label.click()
  # (3)날짜 전체 선택 및 확인
  searchButtons=driver.find_elements(by=By.TAG_NAME,value="button")
  for i in range(0, len(searchButtons)):
    if searchButtons[i].text == "전체":
      searchButtons[i].click()
      break
    elif i==len(searchButtons)-1: # 마지막 때
      logging.debug("날짜 전체 선택에서 문제가 발생했습니다. 코드를 다시 확인해 주세요.")
      sys.exit()
  prevPanelTitle = driver.find_element(by=By.CLASS_NAME,value="panel-title").text
  for i in range(0, len(searchButtons)):
    if searchButtons[i].text == "검색":
      searchButton = searchButtons[i]
      break
  searchButton.click() # 검색 버튼
  # (4)엑셀 다운전 다운로드 폴더의 금일 csv파일 삭제
  todayDate = datetime.now(timezone('Asia/Seoul')).strftime("%Y%m%d")
  fileList = os.listdir(DOWNLOAD_FILES_PATH)
  fileListCsv = [file for file in fileList if file.endswith('.csv')]
  fileName = ""
  for file in fileListCsv:
    fileName = file
    if (fileName.find("스마트스토어상품_" + LISTNAME[idx] + todayDate) != -1):
      os.remove(os.path.join(DOWNLOAD_FILES_PATH,fileName))
      logging.info(f"기존 {fileName}를 삭제하고 새로 다운 받습니다.")
  # (5)엑셀 다운 - csv
  for i in range(0, 5): # 5초간 상품목록 로딩 완료인지 확인
    curPanelTitle = driver.find_element(by=By.CLASS_NAME,value="panel-title").text
    if prevPanelTitle != curPanelTitle: # 검색한것 로딩됐는지 확인
      panel=driver.find_elements(by=By.CLASS_NAME,value="panel-heading")[0]
      dropdown3=panel.find_elements(by=By.CLASS_NAME,value="selectize-dropdown-content")[2] # 3번째 dropdown
      parent = dropdown3.find_element(By.XPATH, '..') # 부모태그
      parent = parent.find_element(By.XPATH, '..') # 부모의 부모태그
      parent.click() # class : selectize-control excel ng-pristine 
      time.sleep(1)
      option = dropdown3.find_element(by=By.XPATH,value='//*[@data-value="PRODUCT_DOWNLOAD"]') # 제품 다운로드
      driver.execute_script("arguments[0].click();", option) # JS로 클릭
    time.sleep(1)
  # (6)csv 다운로드 완료 대기
  complete = False
  for i in range(0, 30): # 다운 최대 30초까지 대기
    if complete: break
    fileList = os.listdir(DOWNLOAD_FILES_PATH)
    fileListCsv = [file for file in fileList if file.endswith('.csv')]
    for file in fileListCsv:
      fileName = file # 다운받은 엑셀 이름
      if (fileName.find("스마트스토어상품_" + todayDate) != -1):
        curPath=os.path.join(DOWNLOAD_FILES_PATH,fileName)
        nxtPath=os.path.join(DOWNLOAD_FILES_PATH,"스마트스토어상품_" + LISTNAME[idx] + todayDate+".csv")
        os.rename(curPath,nxtPath) # 이름변경
        complete = True # 다운성공
        logging.debug("스마트스토어 마마미.csv 다운 완료")
        print("스마트스토어 마마미.csv 다운 완료")
    time.sleep(1)
  return None

