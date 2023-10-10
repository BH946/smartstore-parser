import os
import time
import logging
import sys
import email
import imaplib # 이메일 읽기
import smtplib # 이메일 쓰기
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

#############################################################
# global variable setting
GMAIL_ID = os.getenv("GMAIL_ID")
GMAIL_APP_PW = os.getenv("GMAIL_APP_PW")

#############################################################

# 메일 쓰기 - 캡차용
def auth_mail_write():
  # 메일전송 - smtp 실행 및 로그인
  smtp=smtplib.SMTP('smtp.gmail.com', 587)
  smtp.starttls()
  smtp.login(GMAIL_ID, GMAIL_APP_PW)
  MAIL=MIMEMultipart()
  MAIL['Subject'] = '스마트스토어 로그인 캡차' # 제목
  with open("./downloads/captcha.png", 'rb') as CAP:
    img = MIMEImage(CAP.read())
    img.add_header('Content-Disposition','attachment', filename="captcha.png")
    MAIL.attach(img)
  smtp.sendmail(GMAIL_ID, GMAIL_ID, MAIL.as_string()) # 내게쓰기
  time.sleep(10) # 메일 전송시간 대기
  smtp.quit()


# 메일 읽기
def auth_mail_read():
  # 사용자가 풀어낸 캡차 응답 메시지 읽기
  # 또는 인증 날라온 메일 읽기 -> 물론 이것도 사용자가 답장으로 응답
  imap = imaplib.IMAP4_SSL("imap.gmail.com")
  imap.login(GMAIL_ID, GMAIL_APP_PW)
  imap.select("INBOX") # 전체보관함(새로고침)
  status, messages = imap.uid('search', None, f'(FROM "{GMAIL_ID}")')
  if status != 'OK':
    logging.info("메일읽기 실패1")
    sys.exit()
  messages = messages[0].split() # uid를 배열형태로 이쁘게 바꿈
  msgLen = len(messages)
  for i in range(30): # 최대 150초 반복대기 -> 5*30 = 150초
    time.sleep(5) # 5초마다 확인
    imap.select("INBOX") # 전체보관함(새로고침)
    # FROM이 GMAIL_ID만 검색 (자신에게 쓴 메일임)
    status, messages = imap.uid('search', None, f'(FROM "{GMAIL_ID}")')
    if status != 'OK':
      logging.info("메일읽기 실패1")
      sys.exit()
    messages = messages[0].split() # uid를 배열형태로 이쁘게 바꿈
    if msgLen != len(messages): break
  if msgLen == len(messages):
    logging.info("캡차 답장을 안했습니다. 인증실패로 종료.")
    sys.exit()
  recent = messages[-1] # 제일 뒤가 최신 메일
  res, msg = imap.uid('fetch', recent, "(RFC822)") # 메일 읽기
  if res != 'OK':
    logging.info("메일읽기 실패2")
    sys.exit()
  # 읽은 메일 파싱
  raw = msg[0][1].decode('utf-8')
  emailMsg = email.message_from_string(raw)
  # 메일 내용..
  if emailMsg.is_multipart():
      for part in emailMsg.walk():
          ctype = part.get_content_type()
          cdispo = str(part.get('Content-Disposition'))
          if ctype == 'text/plain' and 'attachment' not in cdispo:
              body = part.get_payload(decode=True)  # decode
              break
  else:
      body = emailMsg.get_payload(decode=True)
  body = body.decode('utf-8')
  answer = body[:body.find('\r')]
  imap.logout()
  return answer