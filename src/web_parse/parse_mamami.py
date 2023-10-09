import logging
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from src.login.login import login # login 함수
from src.db.db_proc import db # db 접속 함수

#############################################################
# global variable setting
cur = db.cursor()
urlArr = os.getenv("MAMAMI_LOGIN_URL").split(",") # [url, name]
MAMAMI_ID = os.getenv("MAMAMI_ID")
MAMAMI_PW = os.getenv("MAMAMI_PW")

errorList = [] # error 모음(log.info) -> 판매중지

#############################################################

# 마마미는 게시물 이름이 제품명이자 모델명
# 옵션은 custom-select-box-list-inner 로 구별 및 PC,MOBILE따로 있어서 2배로 나와서 나누기2 해서 사용
# value는 무조건 있는데, quantity의 경우 -1이나 없는경우 : -1로 기록!(999재고!)
# data-option-no 개수가 실제 저장될 옵션 개수임 - '선택안함' 개수0

# 리리리리뉴얼 -> 위주석들 참고하면서... 진행
# data-combined-option-value-no 검색해서 key:value로 저장(재고는 X)
# 이때 "," 가 있을때 앞에 옵션들에서 구한 값들을 key비교해서 value값 기록
# => 이과정에서 옵션들마다 key:value(이름=name) 들로 다 구했다고 생각
# 이후 data-option-no 가 실제 "재고있는" 총 옵션개수가 될테니 검색후 
# data-combined-option-value-no 검색및 None이면 바로 value, quan..기록
# None이 아니면 위에서 구한 key:value에 맞는 value기록 및 quantity 기록
# 만약 맞는게 없으면?? 이상함. 예외임. 그냥무시.
# 값 구분에 ",/," 를 사용했음. 평범한 "," 는 이름에 사용될까봐.


def getOption(s, url):
  optionArr = []
  res = s.get(url)
  res.encoding=None
  html = res.text
  soup = BeautifulSoup(html, 'html.parser', from_encoding='utf-8') # lxml
  stockOptions = soup.find_all('div', attrs={'class':'custom-select-box-list-inner'})
  optionCount = int(len(stockOptions)/2) 
  stockOptions = stockOptions[:optionCount]
  #
  # 옵션파싱 1~개 시작
  # 1. keyName 먼저 구하기 -> 동작:'data-combined-option-value-no' 검색
  keyName = {} # dict - 옵션요소 key:name 기록목적
  for i in range(0,optionCount):
    innerBox = stockOptions[i]
    options = innerBox.find_all('div', attrs={'class':'custom-select-option'})
    for option in options:
      optionKey = option.get('data-combined-option-value-no')
      optionName = option.get('data-option-value')
      if optionKey is None:
        continue
      if optionKey.find(',')!=-1: # key여러개... 경우
        keySplit = optionKey.split(',')
        for key in keySplit:
          if keyName.get(key) is None: # 없는 키만 추가
            keyName[key]=optionName
      else: # key1개... 경우
        keyName[optionKey]=optionName # ex) '14724396':'블랙'
  #
  # 2. 재고 기록 -> 동작:'data-option-no' 검색
  for i in range(0,optionCount):
    innerBox = stockOptions[i]
    options = innerBox.find_all('div', attrs={'class':'custom-select-option'}) 
    for option in options: # data-option-no 검색 먼저
      optionKey = option.get('data-option-no') # 실체 유무에만 사용
      optionName = option.get('data-option-value')
      if optionKey is None:
        continue
      optionKey = option.get('data-combined-option-value-no')
      # 재고수 기록
      optionStock = option.get('data-option-quantity') 
      if optionStock is None:
        optionStock = '-1'
      # optionName 업데이트
      if optionKey is not None:
        # 이미 앞에서 key:name 다 구해놨기때문에 매칭 안될수가 없음(안된다면 에러)
        optionName = ""
        keySplit = [optionKey] # init
        if optionKey.find(',')!=-1: # key여러개... 경우
          keySplit = optionKey.split(',')
        for key in keySplit:
          optionName += keyName[key]
          optionName += ",/," # 혹시나 이름에 , 가 들어갈수도있으니 ,/,사용
        optionName = optionName[:-3] # 끝에 ",/," 제거
      optionArr.append([optionName, optionStock])
  return optionArr
  

def getOptions(driver, s): # 재고 파싱
  wait = WebDriverWait(driver, 10) # 대기10초 설정
  productList = []; itemList = []
  page = 1
  while(True):
    driver.get(f"https://mamami.co.kr/home?productListPage={page}")
    try:
      wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbDiv"))) # tag:div
    except TimeoutError:
      break # 페이지 끝
    #
    # 1. 제품명, url 먼저 파싱
    soup = BeautifulSoup(driver.page_source, 'lxml') # html파서
    itemDiv=soup.find_all('div', attrs={'class':'thumbDiv'})
    for i in range(0,len(itemDiv)): # 현재 page의 item 전부 조회
      tagA = itemDiv[i].find_parent('a')
      url = 'https://mamami.co.kr'+tagA['href']
      name = tagA.find('div', attrs={'class':'shopProduct productName'}).text # name & model
      productList.append([name, url])
    #
    # 2. 재고 추출
    for product in productList:
      name = product[0]
      model = product[0]
      url = product[1]
      options = getOption(s, url)
      itemList.append([name, model, options, url])
    #
    logging.info(f'{page}페이지 추출 완료')
    if page == 1: # 테스트용! (주석필수)
      break
    page += 1
  return itemList


def parse_mamami(driver):
  wait = WebDriverWait(driver, 10) # 대기10초 설정
  session = login(driver, urlArr, MAMAMI_ID, MAMAMI_PW) # 로그인 세션 반환
  if session is None:
    return None # 로그인 실패
  
  # 1. 홈페이지 전체 데이터 파싱
  itemList = getOptions(driver, session) # [[name, model, options, url],]
  # print(itemList)
  

  # # 2. DB기록 - 메모리비교는 데이터가 순서대로인것을 이용해서 속도 UP
  # sql = "select * from mamami_item order by mamami_item_id desc" # 내림차순
  # sql = "select * from mamami_item p join mamami_item_part c on p.mamami_item_id=c.mamami_item_id order by p.mamami_item_id desc"
  # cur.execute(sql) # 조회 개수 반환
  # results = cur.fetchall()
  # lastId = 0
  # if len(results) != 0:
  #   lastId = results[0][0] # [[id, name, model, status, url],]
  
  # # 2-1. db update
  # insertIdx = []
  # idx = 0 # 속도 UP
  # for i in range(0, len(itemList)): # parse data - 오름차순 1(최신),2,3,4,5
  #   dbCheck = 0
  #   itemModel = itemList[i][1] # model
  #   for j in range(idx, len(results)): # db data - 내림차순 5(최신),4,3,2,1
  #     if itemModel == results[i][2]: # [[id, name, model, status, url],]
  #       sql = "update..."
  #       cur.execute(sql)
  #       dbCheck = 1 # db에 존재
  #       idx = j
  #       break
  #   if dbCheck == 0: # db에 존재X
  #     insertIdx.append(i) # 오름차순 1(최신),2,3,4

  # # 2-2. db insert
  # for i in range(len(insertIdx)-1, -1, -1):
  #   lastId+=1
  #   item = itemList[insertIdx[i]] # [name, model, options, url]
  #   sql = f"insert into mamami_item values('{lastId}', '{item[0]}', '{item[1]}', 'test', '{item[3]}')"
  #   cur.execute(sql)
  #   sql = f"insert into mamami_item_part values('{}', '{}')"
  

  # db.commit()
  # db.close()

