# smartstore-parser

**잘 동작하는 "파서" + 스마트스토어 재고관리 편의 프로젝트**

<br><br>

## 라이브러리

**아나콘다 사용 -> conda 명령어 사용(conda list, conda install... 등)**

* `python : 3.11.5`
* `beautifulsoup4 : 4.12.2(최신)`
* `requests : 2.31.0`
* `selenium : 4.9.0`
  * 셀레니움3 -> 셀레니움4 를 사용! (**크롬드라이버 설치 자동으로 변경!!**)
  * 업그레이드 : `conda install -c conda-forge selenium`
  * 크롬드라이버 자동 : `conda install -c conda-forge webdriver-manager`
  * `webdriver-manager : 4.0.1`
* `pymysql : 1.0.2`
* `smtplib : 기본 내장 라이브러리`
* `lxml : 4.9.3`
* `openpyxl : 3.0.10`
* `pandas : 2.0.3`
* `pip : 23.2.1`
* `python-dotenv : 0.21.0`
  * `.env` 활용
* `pytz : 2022.1`
  * `timezone` 설정 - 깃액션 등 사용시 외국값으로 기본 설정되어있는데 한국으로 설정 가능(서울)

<br><br>

## 폴더 구조

* [`/main.py`](./main.py)
  * 메인함수 실행 파일
* [`/src/db`](./src/db)
  * 파일은 숨겼지만, 실제로 db에 접속하는 py를 만들어 둠
* [`/src/login/auth_mail.py`](./src/login/auth_mail.py)
  * 로그인이나 캡차나 등등 메일쓰기 or 읽기용 함수 개발
* [`/src/login/login.py`](./src/login/login.py)
  * 로그인 함수 개발 - 네이버 포함
* [`/src/smartstore/product.py`](./src/smartstore/product.py)
  * 스마트스토어의 상품정보.csv 다운함수
* [`/src/web_parse/parse_mamami.py`](./src/web_parse/parse_mamami.py)
  * 해당사이트 파싱하는 함수 개발
  * 다운받은 상품정보.csv와 비교해서 사용할 아이템만 db에 기록까지!
* [`/src/web_parse/parse_phonefriend.py`](./src/web_parse/parse_phonefriend.py)
  * 위와 마찬가지인 함수!
