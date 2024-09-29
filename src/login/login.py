import sys
import time
import requests
import logging
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from src.db.db_proc import db # db 접속 함수

import email
import imaplib # 이메일 읽기
import smtplib # 이메일 쓰기
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from src.login.auth_mail import auth_mail_read, auth_mail_write

#############################################################
# global variable setting



#############################################################

# naver, mamami, phonefriend
def login(driver, urlArr, id, pw):
  wait = WebDriverWait(driver, 10)
  url = urlArr[0]
  name = urlArr[1]
  if name == "naver":
    driver.get(url)
    loadings=wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, "button"))) # tag:button
    # 처음 웹 로딩 때는 한번씩 기회를 더 주자
    if len(loadings) == 0: 
      loading=wait.until(EC.presence_of_element_located((By.TAG_NAME, "button"))) # tag:button
      loading.click() # (1)"네이버 아이디로 로그인" 클릭
    else:
      loadings[0].click() # (1)"네이버 아이디로 로그인" 클릭
    # 새탭으로 생성이 됨
    for i in range(0,5): # 최대 5초 대기
      if len(driver.window_handles)==2: break
      time.sleep(1)
    driver.switch_to.window(driver.window_handles[-1]) # 탭이동
    wait.until(EC.presence_of_element_located((By.ID, "id"))) # tag:input
    # 값 복사는 js가 수월
    driver.execute_script(f"document.getElementById('id').value='{id}'")
    driver.execute_script(f"document.getElementById('pw').value='{pw}'")
    driver.find_element(by=By.CLASS_NAME,value="btn_login").click()
    try:
      wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login_form"))) # (2)새로운 기기 등록 여부 확인 new.save
      driver.find_element(by=By.ID,value="new.dontsave").click() # 등록X
    except Exception: # 탭 handler 에러도 있어서 그냥 Exception로 처리
      # (2-1)캡차인지 확인
      try:
        captchas=driver.find_elements(by=By.ID,value="captcha")
      except Exception:
        pass # 캡차X & 기기 이미 등록
      else:
        if len(captchas)==1:
          # (2-2)캡차처리
          logging.info("캡차 처리 시작")
          # 캡처 -> 메일전송 -> 값 반환
          cap=driver.find_element(by=By.CLASS_NAME,value="captcha_wrap")
          cap.screenshot("./downloads/captcha.png")
          time.sleep(3) # 이미지 생성 대기
          # 메일 쓰기 -> 캡차 이미지 보내기
          auth_mail_write()
          # 메일 읽기 -> 캡차 풀이 응답 읽기
          answer = auth_mail_read()
          # 다시로그인 시도
          driver.execute_script(f"document.getElementById('id').value='{id}'")
          driver.execute_script(f"document.getElementById('pw').value='{pw}'")
          captchas[0].send_keys(answer)
          driver.find_element(by=By.CLASS_NAME,value="btn_login").click()
          try:
            # (2-3)새로운 기기 등록 여부 다시 확인
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "login_form")))
            driver.find_element(by=By.ID,value="new.dontsave").click()
          except Exception: pass # 기기 이미 등록
          
    # 최대 180초 대기 - 로그인 + 휴대폰 2단계 인증 추가로 인해 대기시간 3분으로 늘리겠음
    for i in range(0,180):
      if len(driver.window_handles)==1: break
      time.sleep(1)
    driver.switch_to.window(driver.window_handles[-1]) # 탭이동
    # (3)2단계 인증 - "휴대폰방식", 동일IP 접속은 90일까지 인증 유지
    time.sleep(60) # 페이지 redirect 대기(생각보다 오래걸려서 꼭 대기) + 본주 휴대폰 인증하면 애초에 통과 됨(1분 대기)
    if driver.current_url.find('accounts.commerce.naver.com')==-1:
      # 이미 인증 완료된 상태
      logging.info("스마트스토어 2단계가 이미 인증되었습니다.")
      driver.get_screenshot_as_file("2단계 인증.png") # login test
      pass
    else:
      # 인증 해야하는 상태
      logging.info("스마트스토어 2단계 인증이 필요합니다.")
      # (3-1)인증번호 전송
      emails=wait.until(EC.presence_of_all_elements_located((By.ID, "email"))) # tag:input
      parent = emails[0].find_element(By.XPATH, '..') # 부모태그
      parent.click() # 이메일 인증 토글 활성화
      parent.find_element(by=By.TAG_NAME,value="button").click() # 인증버튼
      wait.until(EC.presence_of_element_located((By.CLASS_NAME, "icon"))).click() # 팝업닫기
      input=parent.find_elements(by=By.TAG_NAME,value="input")[-1] # 인증번호 입력란
      # (3-2)메일 읽기
      # 메일 읽기 -> 날라온 인증번호 읽기 (물론 사용자가 답장으로 다시 인증번호 적어서 보내야함)
      answer = auth_mail_read()
      authNum=answer
      input.send_keys(authNum)
      time.sleep(1)
      driver.find_elements(by=By.TAG_NAME,value="button")[-1].click() # 확인
      time.sleep(1)

    # 최대 5번 홈페이지 새로고침(팝업창이 많아서 그럼)
    for i in range(0, 5): 
      driver.get(url)
      time.sleep(1)
      if driver.current_url.find('sell.smartstore.naver.com/#/products/origin-list')!=-1: break
    # 내용 : 오늘 하루동안 보지않기 체크
    try:
      wait.until(EC.presence_of_element_located((By.CLASS_NAME, "text-sub"))).click()
      time.sleep(1)
    except:
      pass # 없으면 이미 한거니까 pass
    return None 

  elif name == "mamami":
    driver.get(url)
    loadings=wait.until(EC.presence_of_all_elements_located((By.ID, "loginUid"))) # tag:input - id
    # 처음 웹 로딩 때는 한번씩 기회를 더 주자
    if len(loadings) == 0: 
      loading=wait.until(EC.presence_of_element_located((By.ID, "loginUid"))) # tag:input - id

    # 값 복사는 js가 수월
    driver.execute_script(f"document.getElementById('loginUid').value='{id}'")
    driver.execute_script(f"document.getElementById('loginPassword').value='{pw}'")
    time.sleep(1) # 로그인 클릭이 안먹힐때가 있어서 좀 더 수정
    btn=driver.find_element(by=By.CLASS_NAME, value="btn-wrapper") # 첫번째꺼
    btn.find_element(by=By.TAG_NAME, value="button").click()

    # 페이지 로딩 대기 - 게시물 로딩을 대기
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbDiv"))) # tag:div
    # 로그인 확인용 파싱 - 성공시 가격이 출력 : ??원
    loginText = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "productPriceSpan"))).text # tag:span

    if loginText.find('원') == -1:
      logging.debug("마마미 로그인 실패 ###############")  
      sys.exit() # 강제종료
      return None
    logging.debug("마마미 로그인 완료 ###############")

  # elif name == "phonefriend":
  #   browser.get(url[0])
  #   browser.execute_script(f"document.getElementById('member_id').value='{id}'")
  #   browser.execute_script(f"document.getElementById('member_passwd').value='{pw}'")
  #   # browser.execute_script("MemberAction.login(); return false;") # 로그인확인
  #   a = browser.find_element_by_class_name('login')
  #   a.find_element_by_tag_name('a').click()
  #   time.sleep(5)
  
  # 로그인 세션 저장
  s = requests.Session()
  headers = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36'
  }
  s.headers.update(headers)
  for cookie in driver.get_cookies():
    c = {cookie['name'] : cookie['value']}
    s.cookies.update(c)
  return s # session 반환
