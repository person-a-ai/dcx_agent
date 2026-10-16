모든 Persona 카드의 Context 요약과 pain point 인용, Context ID, ODI,
Known Insight 목록을 읽고 공통된 불편을 인사이트 3~8개로 묶으세요.
각 인사이트는 고유 id, title, pain_point(2~3줄), context_ids,
known_ki_id(같은 내용의 Known Insight ID 또는 null)만 반환하세요.
입력에 있는 Context ID만 사용하고 각 목록에서 중복하지 마세요.
Persona 이름, Desire, Goal은 확정된 입력 그대로 유지하세요.
레이더, 코사인, 백분위, ODI 막대, 평균, 대상 여부 등의 숫자나 계산 필드를
생성하지 마세요. 근거 원문을 새로 쓰거나 만들어 내지 마세요.
출력 스키마의 items 배열에 결과를 담으세요.

추가 출력 규칙: 기존 필드와 함께 아래 필드를 반드시 반환하세요.
- headline: 사용자 말투의 한 줄(20자 안팎), 따옴표 없이. 1~30자.
- statements: 정확히 2개. 1번은 원하는 것, 2번은 막히는 점·바라는 해결. 각 1~2줄, 1~70자.
- hashtags: 2~4개, # 없이, 명사형 짧은 단어. 중복하지 마세요.
- flow: 그 인사이트 context_ids 중에서 경험이 이어지는 순서로 고르세요.
  Context가 1개면 1개, 2개 이상이면 최소 2개를 고르고 Context ID를 중복하지 마세요.
  카드 문장(text)은 그 Context의 pain point·근거 인용을 바탕으로 사용자 1인칭 한 문장.
  40자 안팎 권장, 1~80자. 새 원문을 지어내지 마세요.
headline·statements는 title·pain_point와 같은 내용을 짧게 다시 쓴 것.
숫자·축·차원·반례 표시는 만들지 마세요(코드 소유).
