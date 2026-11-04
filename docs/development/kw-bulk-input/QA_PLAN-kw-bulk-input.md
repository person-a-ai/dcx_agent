# QA Plan — 키워드 일괄 입력

| | |
|---|---|
| Source spec | [01-brainstorm.md](01-brainstorm.md) · [02-design.md](02-design.md) · [03-plan.md](03-plan.md) · [mockup/index.html](mockup/index.html) |
| Branch / version | 하네스 build worktree의 최신 task commit (base origin/main `fa71e31`) |
| Author | Controller (Claude Code) |
| Last updated | 2026-10-28 |
| Status | draft (계획 승인 대상) |

## 1. Scope

**In scope**
- 1단계 키워드 화면의 "키워드 일괄 추가" 카드: 붙여넣기·CSV 입력, 미리보기(중복·분류·자동 제안), 편집, 일괄 추가, 결과.
- API `POST /keywords/{sid}/bulk/preview`, `POST /keywords/{sid}/bulk`의 권한·검증·결과.
- 기존 키워드 화면 동작 회귀.

**Out of scope**
- 실제 OpenAI/Claude 분류 품질(가짜 LLM으로만 확인. 실제 모델 1회 확인은 계획 8절 항목으로 Controller가 별도 기록).
- .xlsx 업로드, 외부 크롤 결과 투입, 일괄 추가 되돌리기(기획 제외 범위).
- 입력 중 화면 이탈 시 내용 보존(저장 안 함이 승인된 동작).

**Open questions**
- 없음.

## 2. Acceptance Criteria

| # | Criterion (기획) | Covered by |
|---|---|---|
| AC1 | 붙여넣기(줄바꿈·쉼표·탭)·CSV(UTF-8/BOM/CP949), 빈 줄·공백 무시 | QA-E2E-001, QA-E2E-003, QA-E2E-004, QA-E2E-006, QA-EDGE-003 |
| AC2 | 머리글 인식(한·영), 없으면 첫 열 | QA-E2E-001, QA-E2E-003, QA-E2E-006 |
| AC3 | 축·하위분류 코드·화면 이름 인식, 못 하면 분류 없음 | QA-E2E-001, QA-EDGE-008 |
| AC4 | 분류 없는 행 LLM 제안, 실패·목록 밖은 "분류 필요"로 남고 추가 안 됨 | QA-E2E-001, QA-NEG-001 |
| AC5 | 행별 분류 변경·행 제외·"모두 이 그룹으로" | QA-E2E-002 |
| AC6 | 기존 중복 "이미 있음", 리스트 안 중복 첫 행만 | QA-E2E-001, QA-NEG-005 |
| AC7 | 행별 결과, 일부 실패가 나머지를 막지 않음 | QA-EDGE-004 |
| AC8 | 단건 추가와 같은 저장 형태 | QA-E2E-005, QA-REG-003 |
| AC9 | 최대 500행 + 안내 | QA-EDGE-001 |
| AC10 | 읽기 전용·편집 불가에서 막힘 | QA-NEG-002, QA-EDGE-007, QA-EDGE-010 |
| AC11 | pytest·lint·build·test | 하네스 verification 단계(브라우저 QA 범위 밖) |

## 3. Critical User Journeys

| # | Journey | Tier | Priority |
|---|---|---|---|
| J-1 | 섞인 리스트 붙여넣기 → 미리보기 확인 → 추가 → 그룹에서 확인 | data / core | P0 |
| J-2 | 엑셀 CSV 파일 올리기 → 미리보기 → 추가 | data | P0 |
| J-3 | 자동 분류 실패·부분 실패 → 직접 분류 → 추가 | data | P0 |
| J-4 | 읽기 전용 버전·생성 중에는 추가 불가 | access | P1 |

## 4. E2E Scenarios

```
QA-E2E-001
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: QA 세션의 R1 검토 화면, 기존 키워드에 "저소음"(물리 › 감각)이 있다
When: "일괄 추가하기" → 텍스트 영역에 아래를 붙여넣고 "미리보기"를 누른다
      키워드,축,하위분류
      층간소음,물리,감각
      퇴근 후 휴식,physical,time
      불안감
      수면 방해
      저 소음
      층간 소음
      정보 찾기,,정보탐색
Then:
  - 입력 상태에 "7행 인식"이 보인다
  - 미리보기 요약에 "추가 예정 5", "이미 있음 1", "리스트 안 중복 1", "분류 필요 0"이 보인다
  - "층간소음" 행의 분류가 "물리 › 감각", 출처가 "입력값"이다
  - "퇴근후휴식" 행의 분류가 "물리 › 시간"이다
  - "정보찾기" 행의 분류가 "행동 › 정보탐색", 출처가 "입력값"이다
  - "불안감" 행 출처가 "자동 제안", 분류가 "심리 › 감정"이다
  - "수면방해" 행 출처가 "자동 제안", 분류가 "행동 › 대처·우회"이다
  - "저소음" 행 상태가 "이미 있음"이고 보조 문구에 "“저소음”"이 있으며 체크가 비활성이다
  - "층간소음"(두 번째) 행 상태가 "리스트 안 중복", 보조 문구 "1행과 같음"이다
  - 추가 버튼 문구가 "5개 추가하기"이다
```

```
QA-E2E-002
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: QA-E2E-001의 미리보기 상태
When: "퇴근후휴식" 행 체크를 끄고, "불안감" 행 분류를 "심리 › 심리적 장벽"으로 바꾼 뒤 "4개 추가하기"를 누른다
Then:
  - 체크를 끈 직후 요약에 "제외 1"이 보이고 버튼이 "4개 추가하기"이다
  - "불안감" 행 출처가 "직접 선택"으로 바뀐다
  - 결과 배너 "키워드 4개를 추가했습니다."가 보인다
  - 3축 탭 "심리"의 "심리적 장벽" 그룹에 "불안감" 칩이 있다
  - 어떤 그룹에도 "퇴근후휴식" 칩이 없다
  - 축 분포 카드의 총 개수가 추가 전보다 4 늘어난다
```

```
QA-E2E-003
Priority: P0
Type: Acceptance / E2E
Journey: J-2
Given: R1 검토 화면, UTF-8 CSV 파일 `qa/utf8.csv`(머리글 `kw,axis,sub`, 3행: 습도/physical/sense, 환기/behavioral/coping, 곰팡이/<빈칸>/<빈칸>)
When: "일괄 추가하기" → "CSV 파일 선택하기"로 파일을 고른다 → "미리보기" → "3개 추가하기"
Then:
  - 파일 선택 직후 텍스트 영역에 "습도"가 들어 있다
  - 미리보기에 3행이 있고 "곰팡이" 출처가 "자동 제안"이다
  - 결과 배너 "키워드 3개를 추가했습니다."가 보인다
  - "물리 › 감각" 그룹에 "습도" 칩이 있다
```

```
QA-E2E-004
Priority: P0
Type: Acceptance / E2E
Journey: J-2
Given: R1 검토 화면, 엑셀에서 저장한 CP949 CSV `qa/cp949.csv`(머리글 `키워드,축,하위분류`, 행 `결로,물리,공간`)
When: 파일을 선택하고 "미리보기"를 누른다
Then:
  - 텍스트 영역 첫 줄이 "키워드,축,하위분류"로 깨지지 않고 보인다
  - 미리보기에 "결로" 행, 분류 "물리 › 공간", 출처 "입력값"이 보인다
```

```
QA-E2E-005
Priority: P0
Type: Acceptance / E2E
Journey: J-1
Given: QA-E2E-002의 결과 화면
When: "추가한 키워드 보기"를 누르고, 페이지를 새로고침한다
Then:
  - 3축 탭이 "전체", 배지 필터가 "전체"로 바뀐다
  - "물리 › 감각", "심리 › 심리적 장벽" 그룹이 펼쳐져 있다
  - 새로고침 후에도 "층간소음"(물리 › 감각) 칩이 있다
  - `GET /keywords/{sid}` 응답에서 "층간소음"의 `origin`이 "manual", `status`가 "approved", `id`가 "manual-"로 시작한다
  - 같은 응답의 "층간소음" `volume.source`가 존재한다("unconnected" 허용)
```

```
QA-E2E-006
Priority: P1
Type: Acceptance / E2E
Journey: J-1
Given: R1 검토 화면
When: 텍스트 영역에 한 줄 `베란다, 실외기 ,  ,소음 민원`을 붙여넣고 "미리보기"
Then:
  - "3행 인식"이 보인다
  - 미리보기 키워드가 "베란다", "실외기", "소음민원" 세 행이다
```

## 5. Negative Scenarios

```
QA-NEG-001
Priority: P0
Type: Negative
Journey: J-3
Given: 백엔드를 `LLM_BACKEND_OVERRIDES={"kw_bulk_classify":"broken"}`로 띄운 R1 검토 화면
When: `불안감\n수면 방해`를 붙여넣고 "미리보기"
Then:
  - 경고 배너 "자동 분류에 실패했습니다"와 "자동 분류 다시 하기" 버튼이 보인다
  - 두 행 상태가 "분류 필요", 출처가 "분류 실패"이다
  - 추가 버튼이 "0개 추가하기"이고 비활성이다
  - "불안감" 분류를 "심리 › 감정"으로 고르면 버튼이 "1개 추가하기"로 활성화된다
  - "수면방해" 행 체크를 끄고 "자동 분류 다시 하기"를 누른 뒤에도 "불안감"의 분류가 "심리 › 감정"으로, "수면방해" 행이 "제외"로 남는다
  - 추가하면 "불안감"만 추가되고 "수면방해"는 어떤 그룹에도 없다
```

```
QA-NEG-002
Priority: P1
Type: Negative / Permission
Journey: J-4
Given: QA 세션에 버전 v2를 만들어 활성화하고, v1을 읽기 전용으로 연다
When: 키워드 화면(v1)을 보고, API `POST /keywords/{sid}/bulk/preview?version=v1`, `POST /keywords/{sid}/bulk?version=v1`를 직접 호출한다
Then:
  - 카드에 "읽기 전용 버전에서는 키워드를 추가할 수 없습니다."만 있고 "일괄 추가하기" 버튼이 없다
  - 두 API 응답이 409이고 본문 `status`가 "error"이다
  - v1 `session.json`의 키워드 수가 호출 전과 같다
```

```
QA-NEG-003
Priority: P1
Type: Negative / Failure injection
Journey: J-1
Given: R1 검토 화면에서 입력 상태에 3행을 붙여넣은 뒤 백엔드 프로세스를 멈춘다
When: "미리보기"를 누른다
Then:
  - 입력 상태로 돌아와 위험 배너가 보인다
  - 텍스트 영역에 붙여넣은 3행이 그대로 있다
  - 백엔드를 다시 띄우고 "미리보기"를 누르면 미리보기 표가 나온다
```

```
QA-NEG-004
Priority: P1
Type: Negative
Journey: J-2
Given: R1 검토 화면, 이미지 파일을 `.csv`로 이름만 바꾼 `qa/broken.csv`, 빈 파일 `qa/empty.csv`
When: 각각 파일로 선택하고, 또 텍스트 영역을 공백·빈 줄만 남긴다
Then:
  - broken.csv: "파일을 읽지 못했습니다" 배너 또는 "키워드를 찾지 못했습니다" 중 하나가 보이고 미리보기 표가 생기지 않는다
  - empty.csv: "키워드를 찾지 못했습니다"가 보인다
  - 공백만 있을 때 "미리보기" 버튼이 비활성이다
```

```
QA-NEG-005
Priority: P1
Type: Negative
Journey: J-1
Given: QA-E2E-002로 추가가 끝난 세션
When: 같은 7행을 다시 붙여넣고 "미리보기", 이어서 "퇴근후휴식" 행 체크를 끈다
Then:
  - QA-E2E-002에서 추가한 4행이 모두 "이미 있음"이다
  - "퇴근후휴식"만 "추가 예정"이고 버튼이 "1개 추가하기"이다
  - 체크를 끈 뒤 버튼이 "0개 추가하기"이고 비활성이다
```

## 6. Edge Cases

```
QA-EDGE-001
Priority: P1
Family: Data volume
Given: R1 검토 화면
When: `단어001`~`단어520` 520줄을 붙여넣고 "미리보기"
Then:
  - 입력 상태에 "500행 인식"이 보인다
  - 미리보기에 정보 배너 "앞 500행만 불러왔습니다(나머지 20행 제외)"가 보인다
  - 표의 마지막 키워드가 "단어500"이다
  - 요약이 "추가 예정 10", "분류 필요 490"이다(가짜 LLM이 100개 묶음마다 앞 두 행만 분류 → 묶음 5개)
```

```
QA-EDGE-002
Priority: P1
Family: Input and boundary
Given: R1 검토 화면
When: 101자짜리 한 줄과 `소음` 한 줄을 붙여넣는다
Then:
  - "100자를 넘는 1개는 제외했습니다"가 보인다
  - "1행 인식"이고 미리보기에 "소음" 한 행만 있다
```

```
QA-EDGE-003
Priority: P1
Family: Input and boundary
Given: R1 검토 화면
When: 엑셀 형식 텍스트를 붙여넣는다: 첫 줄 `﻿키워드\t축\t하위분류\t`, 둘째 줄 `"창문, 문틈"\t물리\t공간\t\t`
Then:
  - "1행 인식"이 보인다
  - 미리보기 키워드가 "창문,문틈", 분류 "물리 › 공간"이다
  - "키워드"라는 키워드 행이 없다
```

```
QA-EDGE-004
Priority: P0
Family: Concurrency and repetition
Given: 같은 세션을 탭 A·B로 연다. 탭 A에서 `곰팡이 냄새`를 붙여넣고 미리보기(“추가 예정”)
When: 탭 B에서 "직접 추가하기"로 "곰팡이냄새"(물리 › 감각)를 추가한 뒤, 탭 A에서 "1개 추가하기"
Then:
  - 탭 A 결과 배너가 "키워드 0개를 추가했습니다. 1개는 건너뛰었습니다."이다
  - 건너뛴 행 표에 "곰팡이냄새"와 "이미 있음"이 있다
  - `GET /keywords/{sid}`에서 "곰팡이냄새"가 정확히 1개다
```

```
QA-EDGE-005
Priority: P2
Family: Navigation and lifecycle
Given: 모바일 375×812 뷰포트, QA-E2E-001과 같은 입력
When: 미리보기까지 진행한다
Then:
  - 표 머리글이 보이지 않고 행이 세로 블록으로 쌓인다
  - `document.documentElement.scrollWidth`가 `clientWidth`보다 크지 않다
  - "5개 추가하기" 버튼이 화면에 보이고 누를 수 있다
```

```
QA-EDGE-006
Priority: P1
Family: Concurrency and repetition
Given: 미리보기 상태(추가 예정 2)
When: "2개 추가하기"를 빠르게 두 번 누른다
Then:
  - 결과 배너 "키워드 2개를 추가했습니다."가 한 번 보인다
  - `POST /keywords/{sid}/bulk` 요청이 1번이다(네트워크 기록)
  - 두 키워드가 각각 1개씩만 있다
```

```
QA-EDGE-007
Priority: P1
Family: State and session
Given: R1을 저장한 뒤 "다음 라운드 생성"으로 R3 생성이 진행 중이다(R2는 잠긴 라운드라 건너뜀)
When: 키워드 화면을 본다
Then:
  - "키워드 일괄 추가" 카드가 보이지 않는다
  - 생성이 끝나면 카드가 다시 보인다
```

```
QA-EDGE-008
Priority: P2
Family: Input and boundary
Given: 사용자 정의 하위분류 "물리 › 설치환경"에 키워드가 하나 있는 세션
When: `창틀,물리,설치환경` 과 `벽지,심리,감각`을 붙여넣고 미리보기
Then:
  - "창틀" 분류가 "물리 › 설치환경", 출처 "입력값"이다
  - "벽지"는 출처가 "자동 제안"이다(축·하위분류 불일치 → 분류 없음으로 보고 자동 분류 대상)
  - 분류 선택 목록에 "물리 › 설치환경"이 있다
```

```
QA-EDGE-009
Priority: P2
Family: Navigation and lifecycle
Given: 백엔드 응답을 늦추기 위해 브라우저 개발 도구로 `/bulk/preview` 요청을 5초 지연(네트워크 조건 또는 요청 가로채기)
When: 리스트 A(`소음`)로 "미리보기" → 분류 중에 "닫기" → "일괄 추가하기" → 리스트 B(`환기`) 입력 상태로 둔다
Then:
  - 5초 뒤에도 입력 상태이고 텍스트 영역이 "환기"이다
  - 미리보기 표가 나타나지 않는다
```

```
QA-EDGE-010
Priority: P1
Family: Concurrency and repetition
Given: 미리보기 상태(추가 예정 2)
When: "2개 추가하기"를 누른 직후(요청 중) 화면 하단 버튼들을 본다
Then:
  - "다음 라운드 생성"·"생성하기" 버튼이 요청이 끝날 때까지 비활성이다
  - 그룹의 "직접 추가하기" 버튼이 요청이 끝날 때까지 비활성이다
```

## 7. Regression Scope

| ID | Existing behavior at risk | Why | Priority |
|---|---|---|---|
| QA-REG-001 | 그룹의 "직접 추가하기"로 1개 추가, 중복 시 "이미 있는 키워드입니다…" 배너와 "중복 키워드 확인하기" | `rounds.add_manual`의 round 계산을 `manual_round`로 분리(T2) | P0 |
| QA-REG-002 | "추천 단어 불러오기" → "추천 단어 모두 추가하기" | 같은 `add_manual` 경로 | P1 |
| QA-REG-003 | 일괄 추가 후 R1 "저장" → 커버리지 계산 완료 → "다음 라운드 생성"이 성공하고 R3 키워드가 나온다 | 일괄 키워드가 `manual`로 다음 라운드 입력(`prompts.py`의 manual/suggested)에 들어감 | P0 |
| QA-REG-004 | 일괄 추가한 칩을 M 키 또는 드래그로 다른 그룹에 옮기기, 거절·복원 | 이벤트·피드백 경로 공유 | P1 |
| QA-REG-005 | 축 분포 카드·"승인 예정 N · 거절 M" 숫자가 추가 직후 맞게 갱신 | 같은 `keywords` 배열·`reload` | P1 |

Searched: `add_manual`·`/manual`·`addKeyword` 호출처(`routers/keywords_v2.py`, `KeywordGroup.tsx`, `keywords/page.tsx`), `origin` 사용처(`prompts.py:123`, `rounds.py` llm 필터, coverage), `keywords.css` 공유 클래스, `page.tsx`의 `reload`·`reveal`.

## 8. Test Data / Preconditions

| Item | Value / source | Notes |
|---|---|---|
| 실행 환경 | build worktree 최신 task commit. 백엔드 `backend/.venv/bin/python -m uvicorn app.main:app --port 8000`(cwd `backend`), 프런트 `npm --prefix frontend run dev`(`NEXT_PUBLIC_API_URL=http://localhost:8000`) | QA 워커가 직접 띄운다 |
| 기본 환경 변수 | `STORAGE=local`, `LOCAL_DATA_DIR=<QA 전용 임시 폴더>`, `LLM_BACKEND=fake`, `EMBED_BACKEND=fake`, `AUTOCOMPLETE_BACKEND=fake`, `SEARCHAD_API_KEY=`(빈 값), `CORS_ORIGINS=http://localhost:3000` | 가짜 LLM: `kw_round_1.json`으로 R1, `kw_bulk_classify.json`(T4)으로 묶음의 앞 두 행만 분류 |
| 변형 환경 | QA-NEG-001: `LLM_BACKEND_OVERRIDES={"kw_bulk_classify":"broken"}` | 서버 재시작 |
| QA 세션 | 시작 화면에서 새 프로젝트 생성 → 키워드 R1 생성(가짜) → R1 검토 화면. 직접 추가로 "저소음"(물리 › 감각) 추가 | QA-EDGE-008은 "물리 › 설치환경" 하위분류를 만들고 "창문"을 직접 추가 |
| 파일 | `docs/development/kw-bulk-input/qa/utf8.csv`, `cp949.csv`(iconv로 생성), `broken.csv`, `empty.csv` | QA 워커가 만든다 |
| External services | 없음(가짜 LLM·임베더, 검색광고 미연결) | |
| 쓰기 가능 경로 | `docs/development/kw-bulk-input/qa/` | 제품 소스·Git 변경 금지 |

## 9. Priority

- **P0** — J-1·J-2·J-3 핵심 흐름(QA-E2E-001~005, QA-NEG-001), 미리보기 이후 중복(QA-EDGE-004), 단건 추가·다음 라운드 회귀(QA-REG-001, 003).
- **P1** — 권한·실패·빈 입력·재입력, 경계(500행·100자·엑셀), 이중 클릭, 생성 중 숨김, 나머지 회귀.
- **P2** — 모바일 배치, 사용자 정의 하위분류 인식.
- 규칙: 데이터가 잘못 저장되거나 중복 저장될 수 있는 경로는 P0.

## 10. Expected Result

- 각 시나리오는 모든 `Then` 항목이 관찰되면 PASS. 하나라도 다르면 FAIL과 실제 관찰값·화면·네트워크 근거를 `qa/<ID>.md`에 남긴다.
- 데이터 단언(origin·id·개수)은 화면 동작 후 `GET /keywords/{sid}` 응답으로 확인한다.
- 가짜 LLM으로는 분류 품질을 판단할 수 없다. 분류 품질은 이 계획의 판정 대상이 아니다.
- 커버리지 자기 점검: AC1~AC10 모두 시나리오가 있다(AC11은 verification 단계). P0 여정 J-1·J-2·J-3 모두 정상·실패 시나리오가 있다. 기존 자동 테스트와 겹치는 단언은 API 수준(T1·T2 pytest)이며 이 계획은 화면 흐름으로 확인한다.
