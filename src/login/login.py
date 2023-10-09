import requests
import logging
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

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
  #   time.sleep(5)
  #   browser.find_element_by_tag_name('button').click() # 첫번째 버튼!(로그인창 띄우기)
  #   time.sleep(5)
  #   # 참고로 새탭으로 생성이 됨!!!
  #   browser.switch_to.window(browser.window_handles[-1]) # 새 탭으로 이동
  #   browser.find_element_by_id('id')
  #   time.sleep(3)
  #   browser.execute_script(f"document.getElementById('id').value='{id}'")
  #   browser.execute_script(f"document.getElementById('pw').value='{pw}'")
  #   browser.find_element_by_id("log.login").click()
  #   # time.sleep(60*10) # 새창은 알아서 종료됨(넉넉히 10분간 기다려주기) ?????
  #   time.sleep(60) # 60초면 충분한거 아닌가
  #   browser.switch_to.window(browser.window_handles[-1]) # 이전 탭으로 이동
  #   browser.get(url[0])
  #   time.sleep(5)
  #   return None

  elif name == "mamami":
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.ID, "loginUid"))) # tag:input - id

    # 값 복사는 js가 수월
    driver.execute_script(f"document.getElementById('loginUid').value='{id}'")
    driver.execute_script(f"document.getElementById('loginPassword').value='{pw}'")

    driver.find_element(by=By.CLASS_NAME, value="designSettingElement button").click()

    # 페이지 로딩 대기 - 게시물 로딩을 대기
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "thumbDiv"))) # tag:div
    # 로그인 확인용 파싱 - 성공시 가격이 출력 : ??원
    loginText = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "productPriceSpan"))).text # tag:span

    if loginText.find('원') == -1:
      logging.debug("마마미 로그인 실패 ###############")  
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
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
  }
  s.headers.update(headers)
  for cookie in driver.get_cookies():
    c = {cookie['name'] : cookie['value']}
    s.cookies.update(c)
  return s # session 반환