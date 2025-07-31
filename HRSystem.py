OPEN_AI_KEY = "${YOUR_KEY}"

descriptions = """
# HR System
## Search employee
 - 단순 검색(Keyword, SQL)
 - 자연어 질의에 대해서, Database에 있는 내용을 기반으로 답변
   ex) 백엔드 담당자는 어느 부서에 있지?
 - SQL생성 기능 : Prompt에 현재 데이터베이스 구조를 전달해야함

## Resume Review
 - 다양한 기능을 수행 : Task에 적합한 Prompt를 분류
 - Task는 미리 구성되어있어야함
 - 기능을 요청할 경우, 적절한 Task Prompt를 선정(의도분류)
 - 프롬프트 검색기능 추가
 
 
직원 데이터를 임의로 생성해줘. 나이는 24~60세 중 랜덤으로 부여해줘. 직급은 '사원','대리','과장','차장','부장','이사'
회사는 은행이라는 가정, 영업,경영,인사,IT,보안 부서가 있음. 학력은 고졸, 대졸, 대학원졸로 구성, 입사년차는 숫자로 작성해줘, 결혼 여부는 했으면 Treu, 안했으면 False로 설정하고, 이렇게 20개의 데이터를 생성해줘

출력 포멧은 아래와 같음. 키 값은 데이터 필드를 영문으로 바꿔서 작성해줘.
[{"name":"홍길동","age":26,...},...}]

#직원 데이터 필드
이름, 나이, 직급, 소속부서, 전문기술, 학력, 입사년차, 취미, 결혼여부, 자격증, 사내수상내역, 주소

(...)

위에서 실행한 생성 및 데이터입력을 기반으로, 새로운 테이블인 EMPLOYEE_INFO를 만들려고해.

출력 포멧은 아래와 같음. 키 값은 데이터 필드를 영문으로 작성해줘.
[{"name":"홍길동","age":26,...},...}]

#직원정보(EMPLOYEE_INFO)데이터 필드
이름, 나이, 부서, 연락처, 이메일(name, age, department, phone, email)
"""

import openai
import pymysql
import pandas as pd
import streamlit as st

openai.api_key = OPEN_AI_KEY

model = "gpt-4o"

def chatgpt_generate(query):
    messages = [
        {
            "role": "system",
            "content": "you are a helpful assistant."
        },
        {
            "role": "user",
            "content": query
        },
    ]

    response = openai.ChatCompletion.create(model=model,messages=messages)
    answer = response['choices'][0]['message']['content']
    return answer

def query_to_sql(natural_query):
    api_query = f'''
데이터 베이스에 테이블 정보가 아래와같이 주어졌을때, Query에 해당하는 SQL문을  작성하시오.
SQL 부분만 출력하세요. SQL끝에 세미콜론(;)을 붙여주세요.

#테이블1
테이블명:EMPLOYEE
테이블컬럼:
('name', 'varchar(50)', 'YES', '', None, '')
('age', 'int(11)', 'YES', '', None, '')
('position', 'varchar(20)', 'YES', '', None, '')
('department', 'varchar(20)', 'YES', '', None, '')
('skills', 'text', 'YES', '', None, '')
('education', 'varchar(20)', 'YES', '', None, '')
('years_at_company', 'int(11)', 'YES', '', None, '')
('hobbies', 'text', 'YES', '', None, '')
('married', 'tinyint(1)', 'YES', '', None, '')
('certifications', 'text', 'YES', '', None, '')
('awards', 'text', 'YES', '', None, '')
('address', 'varchar(100)', 'YES', '', None, '')

#테이블2
테이블명:EMPLOYEE_INFO
테이블컬럼:
('name', 'varchar(50)', 'YES', '', None, '')
('age', 'int(11)', 'YES', '', None, '')
('department', 'varchar(20)', 'YES', '', None, '')
('phone', 'varchar(20)', 'YES', '', None, '')
('email', 'varchar(100)', 'YES', '', None, '')

#Query:{natural_query}
    '''
    answer_sql = chatgpt_generate(api_query)
    start = answer_sql.index("SELECT")
    end = answer_sql.index(";")
    return answer_sql[start:end+1]

def go_db(sql):
    print(sql)
    #Connection Open
    connection = pymysql.connect(
        host="127.0.0.1",
        user='victory',
        password="${PWD}",
        db='victory',
        charset='utf8mb4'
    )
    with connection.cursor() as cur:
        cur.execute(sql)
        result = cur.fetchall()
    # ---------------------------- 여기가, 엑셀 저장 포인트 ---------------------------- #

    pd.DataFrame(result).to_excel("./chat_sql_result.xlsx",engine='openpyxl')

    # ---------------------------- 여기가, 엑셀 저장 포인트 ---------------------------- #
    return result

def make_natural_answer(query, sql_result):
    #sql_result = "\n".join(sql_result)
    prompt = f'''
다음과 같은 Query가 주어졌을때, Query로 조회한 Database Result가 있다.
Query와 Database Result로 답변 문장을 생성하세요.

#Query : {query}
#Database Result : {sql_result}
    '''
    answer = chatgpt_generate(prompt)
    return answer

#query = "전체 사원들 중에서 IT부서와 경영 부서에 있으면서, 20대인 사람들의 이름과 이메일을 출력해주세요."

def get_answer(query):
    sql_result = go_db(query_to_sql(query))
    answer = make_natural_answer(query,sql_result)
    return answer

st.title("🍌System of Searching Employees")


if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input("Input want to search employee"):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role":"user","content":prompt})
    response = f"Bot : {get_answer(prompt.strip())}"
    with st.chat_message("assistant"):
        st.markdown(response)

    st.session_state.messages.append({"role":"assistant","content":response})
