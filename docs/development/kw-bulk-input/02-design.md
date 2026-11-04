# 02 · 설계 — 키워드 일괄 입력

- 기획: [01-brainstorm.md](01-brainstorm.md) (제품 승인 2026-10-28) · 목업: [mockup/index.html](mockup/index.html)
- 기준 커밋: origin/main `fa71e31` · 상태 루트 `/Users/tech/code/dcx_agent-kw-bulk-input`

## 0. 목업 제작 방식

`/claude-design`은 쓰지 않았다. ① 이번 변경은 기존 키워드 화면에 카드 하나를 더하는 것이고 새 시각 언어가 없다. ② 코드베이스 맥락을 외부 서비스로 보내지 않는다. ③ 이전 기능(channel-expansion, v1-cleanup)과 같은 방식으로 승인 대상을 로컬 파일로 고정한다. 실제 앱 CSS(`frontend/src/styles/tokens.css`, `components/ds/ds.css`, `components/keywords/keywords.css` @`fa71e31`)를 `mockup/app.css`로 복사하고 그 CSS를 쓰는 로컬 HTML을 작성했다. 위쪽 도구 막대로 상태 8개(닫힘 · 입력 · 분류 중 · 미리보기 · 자동 분류 실패 · 요청 오류 · 추가 결과 · 읽기 전용) × 폭 2개(데스크톱 · 모바일 375)를 바꿔 본다. `kwb-*` 클래스는 제품 `keywords.css`에 들어갈 후보다. 승인 후 원하면 `/claude-design`으로 다시 만든다.

## 1. 화면

- 위치: 키워드 화면 왼쪽 열(`kw-main`), "다음 라운드 방향 지시" 카드와 3축 탭 카드 사이에 **"키워드 일괄 추가" 카드**. 처음엔 접힌 상태(제목·설명·"일괄 추가하기" 버튼).
- 표시 조건: `ui.canEdit && !running`일 때 카드 표시. 읽기 전용 버전이면 안내 문구만. 라운드 생성 중이면 숨긴다(기존 3축 탭 카드와 같은 조건).
- 상태 흐름: 닫힘 → 입력 → (미리보기 요청) 분류 중 → 미리보기 → (추가) 추가 결과 → "새 리스트 넣기"로 입력.
  - 입력: 텍스트 영역(붙여넣기), "CSV 파일 선택하기", 인식 행 수, "미리보기".
  - 미리보기: 요약 배지(추가 예정 · 이미 있음 · 리스트 안 중복 · 분류 필요 · 제외), 선택한 행 분류 일괄 변경 + "모두 이 그룹으로", 표(포함 체크 · 키워드 · 분류 선택 · 분류 출처 · 상태), "입력으로 돌아가기", "N개 추가하기"(N = 포함되고 분류가 있는 추가 예정 행 수).
  - 추가 결과: 성공 배너(추가 N · 건너뜀 M) + 건너뛴 행 표 + "추가한 키워드 보기"(탭·필터를 '전체'로) + "새 리스트 넣기".
- 분류 선택 목록: 기본 16개 하위분류 + 이 세션 키워드에 있는 `custom:` 하위분류. 표시 이름은 `taxonomy.ts`의 `groupLabel`.
- 모바일(≤640px): 표를 행 단위 세로 블록으로 쌓고 내부 스크롤을 없앤다. 데스크톱은 표 영역 최대 높이 420px 내부 스크롤, 머리글 고정.

## 2. 구조

### 2.1 새 모듈

| 파일 | 책임 | 공개 인터페이스 | 의존 |
|---|---|---|---|
| `backend/app/keywords/bulk.py` | 미리보기(중복·분류 판정, LLM 분류), 일괄 추가 | `preview(sid, rows, version=None) -> dict`, `add_many(sid, items, version=None) -> dict` | `rounds`(`_all_keywords`, `volumes`, `Duplicate` 규칙), `normalize.norm_key`, `taxonomy`, `llm.registry.run_task`, `store`, `events`, `feedback` |
| `frontend/src/lib/logic/bulkKeywords.ts` | 텍스트·CSV → 행, 머리글·값 인식, 500행 자르기 | `decodeCsv(buf: ArrayBuffer): string`, `parseBulk(text: string, groups: Destination[]): { rows: BulkRow[]; truncated: number }`, `resolveGroup(axis?: string, sub?: string, groups): Destination \| null` | `taxonomy.ts` |
| `frontend/src/components/keywords/BulkAdd.tsx` | 카드 UI와 상태 흐름 | `<BulkAdd sid version groups disabled onAdded(keywords) onReveal />` | ds 컴포넌트, `lib/api/keywords`, `bulkKeywords` |

### 2.2 기존 모듈 변경

| 파일 | 변경 |
|---|---|
| `backend/app/routers/keywords_v2.py` | `POST /keywords/{sid}/bulk/preview`, `POST /keywords/{sid}/bulk` 추가. 요청 모델 `BulkRow{kw: str(1..100), axis?: str, sub?: str}`, 목록 길이 1..500. 기존 `KeywordRoute` 오류 봉투 사용 |
| `frontend/src/lib/api/keywords.ts` | `previewBulk(sid, rows, version)`, `addBulk(sid, items, version)`와 타입 |
| `frontend/src/app/pipeline/keywords/page.tsx` | 방향 지시 카드 아래에 `<BulkAdd>` 배치. 추가 성공 시 `reload()` 후 탭·필터 '전체' |
| `frontend/src/components/keywords/keywords.css` | `kwb-*` 클래스(목업과 동일) |

## 3. 데이터 흐름

1. 프런트 `parseBulk`가 행을 만든다.
   - 따옴표를 지원하는 CSV 분해. 줄에 탭이 있으면 탭 구분, 아니면 쉼표 구분.
   - 첫 줄 셀 중 하나라도 머리글 별칭이면 머리글 모드: `키워드|kw|keyword`, `축|axis`, `하위분류|하위 카테고리|sub|subcategory` (앞뒤 공백·대소문자 무시). 키워드 열이 없으면 첫 열.
   - 머리글이 없으면: 줄이 하나뿐이면 그 줄의 모든 셀이 각각 키워드(“a, b, c” 리스트), 여러 줄이면 줄마다 첫 셀이 키워드이고 2·3번째 셀을 축·하위분류로 시도.
   - 빈 셀·빈 줄 제외, 앞뒤 공백 제거. 500행 초과분은 잘라 `truncated`로 알린다.
   - `resolveGroup`: 축은 코드 또는 `물리|심리|행동`. 하위분류는 코드, 표시 이름(`감각` 등), `custom:` 이름. 하위분류 코드는 축 사이에 겹치지 않으므로 축 없이 하위분류만 있어도 찾는다. 축만 있거나 못 찾으면 분류 없음.
   - CSV 파일: `TextDecoder('utf-8', {fatal:true})` 실패 시 `TextDecoder('euc-kr')`(브라우저에서 CP949 포함). BOM 제거.
2. `POST /bulk/preview { rows: [{kw, axis?, sub?}] }` (분류는 프런트가 코드로 바꾼 값 또는 비움).
   - `assert_writable`. 키워드는 `add_manual`과 같게 공백 제거(`''.join(kw.split())`), 비교는 `norm_key`.
   - 순서대로: 기존 키워드와 같으면 `existing`(+`duplicateOf{id,kw,axis,sub}`), 앞 행과 같으면 `in_list_duplicate`(+`firstRow`), 아니면 분류가 `is_valid`면 `new/source=input`, 아니면 LLM 대상.
   - LLM 대상만 100개씩 `LLMTask(task='kw_bulk_classify', output_schema=Classified{items:[{index:int, axis:str, sub:str}]})`, 첨부 `project_context.md`, 지시문에 허용 목록(기본 코드 + 세션의 `custom:` 하위분류와 이름). 결과가 허용 목록 밖이거나 빠진 행은 `needs_class/source=llm_failed`. 묶음 실패 시 그 묶음 행 전부 `needs_class`, 응답에 `classifyError{kind,message}`.
   - 응답: `{rows:[{row, kw, axis|null, sub|null, source:'input'|'llm'|'llm_failed'|null, status:'new'|'existing'|'in_list_duplicate'|'needs_class', duplicateOf?, firstRow?}], classifyError?}`. **저장하지 않는다.**
3. 미리보기에서 사람이 행 제외·분류 변경. 분류를 바꾸면 `source`는 화면에서 '직접 선택'으로 표시, `needs_class`는 `new`로 바뀐다.
4. `POST /bulk { items: [{kw, axis, sub}] }` — 포함되고 분류가 있는 `new` 행만 보낸다.
   - 각 항목 `is_valid` 검사(실패 → `invalid`). 유효 항목은 `volumes()` **한 번**으로 검색량 부착(잠금 밖).
   - 세션 잠금 안에서 한 번: 현재 키워드와 다시 중복 검사(미리보기 이후 생긴 중복 → `duplicate`+`duplicateOf`), 항목끼리 중복도 제외, round는 `add_manual`과 같은 규칙, `id='manual-'+uuid`, `origin='manual'`, `status='approved'`. `_update_locked(..., confirm_stage='stage1')` 한 번, 추가된 키워드마다 `add` 이벤트, `write_feedback_md` 한 번.
   - 응답: `{results:[{index, status:'added'|'duplicate'|'invalid', id?, duplicateOf?}], keywords: with_display(added)}`.
5. 프런트는 결과 화면을 보여 주고 `reload()`로 키워드·축 분포를 갱신한다.

## 4. API 계약

| 메서드·경로 | 요청 | 성공 | 오류 |
|---|---|---|---|
| `POST /keywords/{sid}/bulk/preview?version=` | `{rows: BulkRow[1..500]}` | 200 위 응답(LLM 실패도 200 + `classifyError`) | 404 세션 없음, 409 읽기 전용·다른 버전, 422 검증(빈 목록·500 초과·빈 키워드) |
| `POST /keywords/{sid}/bulk?version=` | `{items: {kw, axis, sub}[1..500]}` | 200 행별 결과 | 404, 409, 422(목록 형식), 500 저장 실패 |

오류 본문은 기존 `KeywordRoute` 봉투 `{status:'error', error:{kind, message}}`.

## 5. 오류 처리

| 상황 | 동작 |
|---|---|
| CSV 읽기 실패(빈 파일·디코딩 실패) | 입력 상태에 위험 배너 "파일을 읽지 못했습니다…", 텍스트 영역 유지 |
| 인식 행 0 | "미리보기" 비활성, 안내 "키워드를 찾지 못했습니다" |
| 500행 초과 | 앞 500행만 사용, 미리보기에 정보 배너 "앞 500행만 불러왔습니다(나머지 N행 제외)" |
| 미리보기 요청 실패(네트워크·409·422) | 입력 상태로 돌아가 위험 배너 + 메시지, 입력 유지 |
| LLM 분류 실패(전체·일부) | 미리보기 표시 + 경고 배너 "자동 분류에 실패했습니다(원인: …)" + "자동 분류 다시 하기"(현재 표의 행과 사람이 고른 분류를 입력값으로 다시 미리보기) |
| 추가 요청 실패 | 미리보기 유지 + 위험 배너, 표 편집 상태 보존 |
| 추가 중 일부 중복·오류 | 결과 화면에 건너뛴 행과 이유 |
| 다른 작업 진행 중(page `busy`) | "N개 추가하기" 비활성. 미리보기(LLM)는 페이지 잠금을 잡지 않는다 |

## 6. 권한·버전

- 두 API 모두 `store.assert_writable(sid, version)` — 읽기 전용 버전, 활성 아닌 버전, 구버전 세션은 단건 추가와 같은 409/오류.
- 미리보기는 저장하지 않지만 LLM 비용이 있으므로 쓰기 가능한 세션에서만 허용.

## 7. 테스트 전략

- 백엔드 pytest(`backend/tests/keywords/test_bulk.py`, 기존 `client`·가짜 LLM 픽스처 사용)
  - 미리보기: 입력 분류 유지, 기존 중복(`저 소음` vs `저소음`), 리스트 안 중복, LLM 분류 채택, 허용 목록 밖 값 → `needs_class`, LLM 실패 → `classifyError`, 100개 초과 시 묶음 분할, 저장 안 함, 500 초과 422, 읽기 전용 버전 409.
  - 추가: 단건 추가와 같은 필드·이벤트·피드백, 검색량 호출 1회, 미리보기 이후 생긴 중복 → `duplicate`, 항목끼리 중복, 잘못된 분류 → `invalid` 이고 나머지는 추가, 읽기 전용 409.
- 프런트 vitest(`bulkKeywords.test.ts`): 머리글 한글·영문, 머리글 없음 단일 줄 쉼표 리스트, 여러 줄 첫 열, 탭(엑셀 붙여넣기), 따옴표 셀, 표시 이름·코드·`custom:` 인식, 하위분류만 있는 행, 500행 자르기, BOM·CP949 디코딩.
- 브라우저 QA: 목업 상태 8개에 대응하는 실제 화면 흐름, 모바일 375.

## 8. 계획 단계로 넘기는 확인 항목

- `kw_bulk_classify` 작업이 `llm_backend_overrides`의 `kw_*` 패턴으로 키워드 작업과 같은 백엔드를 쓰는지 운영 설정 확인.
- LLM 지시문·묶음 크기(100)와 대기 시간 실측(가짜 백엔드 외 실제 1회).
- 입력 중 화면 이탈 시 내용 유실(저장 안 함)은 이번 범위에서 허용 — 계획에 명시.
