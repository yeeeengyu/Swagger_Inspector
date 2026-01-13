# SWAGGER 인스펙터

<img width="1125" height="851" alt="main" src="https://github.com/user-attachments/assets/af8ac357-ce95-4171-a6e2-13ca3bf5464b" />

## 개요
- 프론트엔드 분들, 협업하는 백엔드분들은 다른 개발자분들에 이어 개발을 시작하려면 협업자분들의 코드들을 이해해야 합니다.
- 여기에 시간을 할애하는 비율을 확고히 줄이기 위해 **RAG기반 기능 인스펙터**를 개발하였습니다.
- Swagger Inspector는 openAPI 데이터 기반 기능들의 목록과 스키마 목록을 가져와 기능을 요약해드립니다.

## 기능 및 사용자 플로우
```
- 기능을 알고싶은 사이트 링크 입력
  ( JWT 등의 Authorization이 걸려 있을 시 Headers에 따로 넣을 수 있음 )
→ VectorDB에 Swagger기반 API 자동추출 & 저장
  ( Operation || Schema 분리하여 입력 가능 )
  
→ 아래 실시간 로그를 통하여 진행상황 알 수 있음

→ 챗봇을 이용하여 각 기능들에 대해 설명받기
```

## 예상질문
### 1. API문서 링크를 잘못 넣었어요. 어떻게 해야하나요? 
- 임베딩 DB를 초기화할 수 있습니다. Reset 버튼으로 한 번에 해결이 가능합니다.

### 2. 결과를 어떻게 믿나요?
- 입력을 임베딩하여 벡터디비의 임베딩 값과 유사도를 비교하여 THRESHOLD값( 임계치 )을 추출합니다.

- 임계치의 일정 값을 넘어가면 근거가 있는 정보라고 판단 후 LLM 출력에 참고합니다.

- 임계치를 넘지 못하면 LLM 호출이 제한되고, 고정된 출력값을 return합니다.

### 3. 무조건 Swagger URL을 입력해야하나요?
- 아니요, 기본 URL을 입력하면 Swagger로 통하는 대표 경로들을 대입하여 찾아냅니다.

- 또한, 단순한 HTML크롤링이 아닌 OpenAPI Spec을 통째로 가져옵니다. ( JSON / YAML 형식, 쿠키 / 토큰 포함 )

## 사용법
1. 환경변수 설정
```
MONGODB_URI=몽고디비 Atlas 접속주소 ( 비번포함 )
MONGODB_DB= DB이름
MONGODB_COL= 컬렉션이름
VECTOR_INDEX= Vector Search 설정된 이름

OPENAI_API_KEY= GPT KEY
OPENAI_EMBED_MODEL= 임베딩모델 ( text-embedding-3-small )
OPENAI_CHAT_MODEL= 챗봇 모델 ( gpt-4o-mini )

DEFAULT_TOP_K=3 ( 근거 문서 몇개 뽑을지 )
DEFAULT_THRESHOLD=0.63 ( 임계치 설정 )
FALLBACK_MESSAGE= LLM 호출 거부 시 메시지
```

2. 가상환경 실행 & 라이브러리 설치
- powershell
```
python -m venv .venv
or
python3 -m venv .venv

.venv/Scripts/activate

pip install -r requirements.txt
or
pip3 install -r requirements.txt
```
- bash
```
python3 -m venv .venv

.venv/bin/activate

pip3 install -r requirements.txt
```

3. 실행 
- 백엔드 ( FastAPI )
```
uvicorn main:app 
```
- 프론트엔드 ( HTML )
```
python -m http.server 5173
```
