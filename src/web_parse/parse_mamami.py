import logging
import os
import time
import pandas as pd
from pytz import timezone
from datetime import datetime
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
urlArr = os.getenv("MAMAMI_LOGIN_URL").split(",") # [url, name,baseUrl]
BASEURL=urlArr[2]
MAMAMI_ID = os.getenv("MAMAMI_ID")
MAMAMI_PW = os.getenv("MAMAMI_PW")
LISTNAME = os.getenv("LISTNAME").split(",")
DOWNLOAD_FILES_PATH = os.getenv("DOWNLOAD_FILES_PATH")
DOWNLOAD_FILES_PATH = os.path.join(os.getcwd(),DOWNLOAD_FILES_PATH)

errorList = [] # error 모음(log.info) -> 판매중지

#############################################################

######## 마마미 사이트 특징 정리
# 1. 마마미는 게시물 이름이 제품명이자 모델명으로 사용
# 2. PC,MOBILE따로 있어서 옵션 태그가 2배로 나옴 -> 나누기2 해서 사용하자
# 3. value(=name=옵션이름)는 무조건 있는데, quantity(=재고)의 경우 -1이나 없는경우 존재 -> -1로 기록하자(999재고!)
# 4. data-option-no 개수가 실제 재고가 DB에 저장될 옵션 개수 - '선택안함' 같은것도 포함(이것도 옵션이기 때문)

######## 마마미 파싱방법 정리
# 1. keyName 먼저 구하기 -> 동작:모든'data-combined-option-value-no' 검색해서 key:value로 저장 ex)번호:제품이름
# 이 과정에서 옵션들 {번호:제품이름} 모두 구하게 됨
# 2. 재고 기록 -> 동작:모든'data-option-no' 검색 후 data-combined-option-value-no 이것도 모두 검색
# 2-1. None이면 바로 value, quan..기록
# 2-2. None이 아니면 위에서 구한 key:value에 매칭되는 value기록 및 quantity 기록

#############################################################

def getCompare(itemList, prodList):
  results = []
  global errorList # 전역변수
  # (1) 순서는 prodList 기준
  for prod in prodList: # [상품명, 모델명, 판매상태, 상품번호]
    count=0
    data=[]
    modelProd = prod[1]
    for item in itemList: # [name, model, options, url]
      modelItem = item[1]
      if modelProd == modelItem:
        data=[prod[0], prod[1], prod[2], item[3], prod[3], item[2]]
        count+=1
    if count == 0: # 동일 모델명 없다는것 - 검색실패 or 오타
      logging.info(f"{prod} : 검색 실패 or 오타가 발생했습니다. 삭제해주세요.")
      errorList.append(prod)
      continue
    elif count > 1: # 중복이 있다는것
      logging.info(f"{prod} : 해당 제품은 중복이 있습니다. 삭제해주세요.")
      errorList.append(prod)
      continue
    results.append(data)
  return results 


def getProduct():
  todayDate = datetime.now(timezone('Asia/Seoul')).strftime("%Y%m%d")
  fileName="스마트스토어상품_" + LISTNAME[0] + todayDate+".csv"
  df = pd.read_csv(os.path.join(DOWNLOAD_FILES_PATH,fileName))
  # [상품명, 카탈로그명, 판매상태, 상품번호 기록] 형태로 반환할 것
  names=df["상품명"]
  models=df["카탈로그명"]
  sellStates=df["판매상태"]
  itemIds=df["상품번호(스마트스토어)"]
  datas=[]
  for i in range(0, len(names)):
    datas.append([names[i],models[i],sellStates[i],itemIds[i]])
  del df
  return datas


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
  # 2. 재고 기록 -> 동작:'data-option-no' 검색 (참고로 옵션3의 경우 data-option-no 만 존재)
  optionName3=[]
  for i in range(0,optionCount):
    # 옵션1,2 까지는 알아서 합쳐서 나오지만
    # 옵션3의 경우 다르게 처리해야하므로 따로 처리.. ex) '블랙,18mm,선택안함' (옵션1,2,3 합)
    innerBox = stockOptions[i]
    options = innerBox.find_all('div', attrs={'class':'custom-select-option'}) 
    for option in options: # data-option-no 검색 먼저
      optionKey = option.get('data-option-no') # 옵션인지 유무에 사용
      optionName = option.get('data-option-value')
      if optionKey is None: # None이면 사용하는 옵션이 아닌것 ex)선택하세요.
        continue
      optionKey = option.get('data-combined-option-value-no')
      # 재고수 기록
      optionStock = option.get('data-option-quantity') 
      if optionStock is None:
        optionStock = '-1'
      if i<2: # (1)옵션1,2까지 optionKey 활용됨
        # optionName 업데이트
        if optionKey is not None:
          # 이미 앞에서 key:name 다 구해놨기때문에 매칭 안될수가 없음(안된다면 에러)
          optionName = ""
          keySplit = [optionKey] # init
          if optionKey.find(',')!=-1: # key여러개... 경우
            keySplit = optionKey.split(',')
          for key in keySplit:
            optionName += keyName[key]
            optionName += "," # 옵션명은 ","로 구별해야함
          optionName = optionName[:-1] # 끝에 "," 제거
        optionArr.append([optionName, optionStock])
      elif i==2:
        # (2)예외처리
        # 옵션3개인 경우 optionArr에 현재옵션 이어붙이고 무조건 재고는 -1로 기록    
        # 이로직에서 하기는 어려워서 우선 이름만 따로 기록하고 탈출
        optionName3.append([optionName,optionStock])
  # (2)예외처리 -> 옵션3 합치기
  if optionCount==3:
    optionArrTemp=optionArr
    optionArr=[]
    for i in range(0, len(optionArrTemp)):
      for j in range(0, len(optionName3)):
        name = optionArrTemp[i][0] + ',' + optionName3[j][0]
        stock = optionName3[j][1] # 재고는 옵션3 재고로 덮어쓰기
        optionArr.append([name,stock])
  return optionArr
  

def getOptions(driver, s): # 재고 파싱
  wait = WebDriverWait(driver, 10) # 대기10초 설정
  itemList = []
  page = 1
  while(True):
    productList = [] # init시점
    driver.get(f"{BASEURL}/home?productListPage={page}")
    try:
      wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbDiv"))) # tag:div
    except Exception:
      break # 페이지 끝
    #
    # 1. 제품명, url 먼저 파싱
    soup = BeautifulSoup(driver.page_source, 'lxml') # html파서
    itemDiv=soup.find_all('div', attrs={'class':'thumbDiv'})
    for i in range(0,len(itemDiv)): # 현재 page의 item 전부 조회
      tagA = itemDiv[i].find_parent('a')
      url = BASEURL+tagA['href']
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
    print(f'{page}페이지 추출 완료')
    # if page == 2: # 테스트용! (주석필수)
    #   break
    page += 1
  print(f'{page-1}페이지까지 추출완료')
  return itemList


def parse_mamami(driver):
  wait = WebDriverWait(driver, 10) # 대기10초 설정
  session = login(driver, urlArr, MAMAMI_ID, MAMAMI_PW) # 로그인 세션 반환
  if session is None:
    return None # 로그인 실패
  
  # 1. 홈페이지 전체 데이터 파싱 및 메모리기록(itemList)
  itemList = getOptions(driver, session) # [[name, model, options, url],]
  # print(itemList)

  # 2. product csv 읽고 메모리 기록(prodList)
  prodList = getProduct() # [상품명, 모델명, 판매상태, 상품번호(스마트스토어)]
  # print(prodList) 

  # 3. itemList,prodList를 모델명(pk)비교 및 기록
  # => prodList 순서대로!!, 상품번호 필수 기록!!
  results = getCompare(itemList, prodList) # [name, model, sellState, url, itemId, options] -> options:[[옵션,재고],]

  # 4. 3에서 구한 값 db 저장(delete -> insert)
  # (4-1) delete
  sql = "delete from mamami_item"
  cur.execute(sql)
  db.commit() # 커밋시점에 삭제
  sql = "delete from mamami_item_part"
  cur.execute(sql)
  db.commit() # 커밋시점에 삭제
  print("db삭제")
  # (4-2) insert
  for i in range(0, len(results)):
    result = results[i]
    sql=f"insert into mamami_item(mamami_item_id, name, model, status, url, item_id) values({i+1},'{result[0]}','{result[1]}','{result[2]}','{result[3]}','{result[4]}')"
    cur.execute(sql)
    db.commit() # 커밋해야 아래 옵션들 외래키 가능!
    for option in result[5]: # 옵션은 무조건 존재!
      opts = option[0].replace(",/,", ",") # "18mm,블랙" 이런식으로 저장 -> 우선 ","형태로 미리 바꿔두겠음. 옵션명에 "," 가들어간건 애초에 사용안할거라서.
      stock = option[1]
      if option[1] == '-1': stock=999 # -1은 999재고로 사용할거라 이 형태 저장
      sqlPart=f"insert into mamami_item_part(mamami_item_id,option_name,stock) values({i+1},'{opts}',{stock})"
      try:
        cur.execute(sqlPart)
      except:
        # 옵션명 잘못받은 상품인것 -> 제거해주자
        print(f"아마 옵션명 잘못입력 상품.. : {result}")
        errorList.append(result)
        break # 다음상품으로 넘어가자
  db.commit() # insert 쿼리 전송
  print("db추가")
  logging.info(f"errorList : {errorList}")
  db.close()
  return None