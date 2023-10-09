# smartstore-parser

**빠르고 잘 동작하는 "파서"를 만드는 프로젝트 + 스마트스토어 자동 재고관리 구현**

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
* `lxml : 4.9.3`
* `openpyxl : 3.0.10`
* `pandas : 2.0.3`
* `pip : 23.2.1`
* `python-dotenv : 0.21.0`
  * `.env` 활용
* `pytz : 2022.1`
  * `timezone` 설정 - 깃액션 등 사용시 외국값으로 기본 설정되어있는데 한국으로 설정 가능(서울)

<br><br>



















## 필요한 지식

**깃허브 액션의 경로를 자세히 모르기 때문에 `os 라이브러리` 를 활용해서 경로를 다룬다.**

* `os.getcwd(), os.chdir('경로지정')` 대표적으로 이 2개를 활용할 수 있다.



**또한 파일 구조를 세분화 하며, 그 파일들에 공통으로 사용할 변수들의 경우 `.env` 에 저장해서 다룬다.**

* `load_dotenv()` 를 `main.py` 에 작성해서 `.env` 파일을 로드하여 어디서든 사용하게 만든다.
* `.env` 파일을 코드 수행중에 getter(), setter() 을 할 수 있다.
  * 실제 로컬의 `.env`파일의 내용이 setter()를 해도 변하진 않지만 코드 사용중에선 변화한다.
  * setter() 방식 - `os.environ["pathDir"] = "12345"`
    getter() 방식 - `os.environ.get("pathDir")` 
* git에 안올릴려면 `.gitignore` 파일에 `.env` 코드 한줄 추가!



**셀레니움에서 headless 사용 시 다운로드 하려면 반드시 설정해줘야 할게 있다.   
`백그라운드에서 다운`받을 경로를 꼭 잘 설정해줘야 에러가 발생하지 않는다.**

* 추가로 내 생각이지만 분명 os 활용하면 경로들 잘 먹히는데, 아래 함수 만든거에서는  
  이상하게 경로를 다른걸로 지정해도 안먹히고 처음 초기 경로로 고정이 되어있음 ..
* 그래서 그냥 기본 경로로 온다는걸 인지하고 사용

```python
# downloadPath 부분의 경로를 꼭 잘 설정해줄것
def enable_download(driver): 
  print('백그라운드 다운로드 기능 활성화')
  driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
  params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': os.getcwd()}}
  driver.execute("send_command", params)
```



**`셀레니움` 에서는 BMP이상 범위의 문자들(예:이모티콘)을 인식하지 못한다.(지원하지 않음)  
따라서 이들을 제거해서 사용해줘야 `send_keys` 가 가능하다.**

* 아래 코드를 함수로 작성해서 활용하는것을 추천
* 0000-FFFF 까지가 BMP 범위이고, 10FFFF까지 SMP, SIP, TIP, SSP, PUA 공간이 잡혀있어서  
  10000-10FFFF까지 제거하는 것으로 정규식을 작성한 것이다.
  * [참고 문서](https://studyprogram.tistory.com/1)

```python
import re # 정규식

text = '안녕하세요 반갑습니다🐶' # 예시
print(text) 
only_BMP_pattern = re.compile("["
        u"\U00010000-\U0010FFFF"  #BMP characters 이외
                           "]+", flags=re.UNICODE)
print(only_BMP_pattern.sub(r'', text))# BMP characters만
```



* 셀레니움에서 요소 찾을때 도움받은 문서 : [xpath 도움](https://blog.daum.net/sualchi/13721873)

* 로그는 log.txt로 따로 찍게 만들었다. (간단한 txt 저장 문법 사용했음)

<br>

## 폴더 구조

* [`/.github/workflows/python-package.yml`](./.github/workflows/python-package.yml)
  * CI/CD 구조를 위한 설정
* [`/complete_files`](./complete_files)
  * 파싱 성공한 파일들 저장
* [`/log`](./log)
  * 로그 모음
* [`/nothing_files`](./nothing_files)
  * 올바르지 않은 파싱한 파일들 저장
* [`/src/naver_product/product_mamami.py`](./src/naver_product/product_mamami.py)
  * 엑셀 다운 받을때 : `브랜드명 - 마마미, 품절&판매중지 체크, 날짜 - 전체 선택`
  * `csv -> product_mamami.xlsx`로 변경할때 : `모델 열, 판매상태 열 사용`
* [`/src/naver_product/product_phonefriend.py`](./src/naver_product/product_phonefriend.py)
  * 엑셀 다운 받을때 : `브랜드명 - 마마미, 품절&판매중지 체크, 날짜 - 전체 선택`
  * `csv -> product_mamami.xlsx`로 변경할때 : `모델 열, 판매상태 열 사용`
* [`/src/web_parse/parse_mamami.py`](./src/web_parse/parse_mamami.py)
  * 마마미 파싱을 하고나서 이전 `parse_mamami_prev.csv` 파일과 비교하는게 특징
  * 이전 파일 비교 후 sample생성하고, 현재꺼가 이전 파일로 바뀐다.
  * `parse_mamami_prev.csv`가 아예 없는경우는 위 과정필요없이 바로 sample생성
* [`/src/web_parse/parse_phonefriend.py`](./src/web_parse/parse_phonefriend.py)
  * 폰프랜드 파싱 성공시 바로 sample생성
  * 마마미처럼 이전 파일과 비교하지 않는다(재고수정이 아닌 판매중<->판매중지만 할거라서)
* [`/src/smartstore_action/smartstore_mamami.py`](./src/smartstore_action/smartstore_mamami.py)
  * 재고 수정을 위주로 한다.
  * 재고가 전부 0이면 알아서 품절로 바뀌기 때문에 판매중지로 바꿀 필요가 없다.
* [`/src/smartstore_action/smartstore_phonefriend.py`](./src/smartstore_action/smartstore_phonefriend.py)
  * 판매중<->판매중지를 위주로 한다.
  * 재고를 일일이 수정하지 않고 품절인지만 파싱해서 판매중지하는 형식이다.
* [`/src/.env`](./src/.env)
  * 로그인 개인정보, 파일경로, 파일명 등등 자주 사용하는 변수들 저장해서 활용
* [`/src/log.py`](./src/log.py)
  * 프로그램 동작내용들 로그찍기 위해서 작성한 파일
* [`/src/login.py`](./src/login.py)
  * 셀레니움 사용하면서 웹 로그인하는 경우들을 따로 작성한 파일
* [`/src/main.py`](./src/main.py)
  * 이 프로그램을 실행하는 루트 파일
* [`/src/test.py`](./src/test.py)
  * 무슨 내용이든 상관없이 그저 테스트를 위해 사용되고 있는 파일
