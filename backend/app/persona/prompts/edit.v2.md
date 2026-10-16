현재 판 JSON과 사용자의 message를 읽고 요청한 target만 수정하세요.
insights 대상은 기존 insight.derive와 같은 {items: [...]} 스키마로 답하세요.
concept:{id} 대상은 editable의 insight.concept 스키마(persona_profile 문자열,
pain_points 근거 번호 3개, journey)를 유지하세요. 다른 컨셉은 수정하지 마세요.
입력에 존재하는 Context ID와 근거 번호만 사용하세요. 컨셉의 AS-IS context_id는
대상 인사이트의 context_ids에 속해야 합니다. 변경하지 않는 내용은 보존하세요.
레이더, ODI, 막대, 백분위, basis, 근거 원문, 출처, 등급, 4D 개수와 제약 판정은
코드가 채웁니다. 이 값이나 숫자를 만들어 답하지 마세요. JSON만 반환하세요.

insights 대상은 derive.v2의 새 필드 headline, statements, hashtags, flow를 포함할 수 있습니다.
예전 항목은 새 필드 4개를 모두 생략하거나 모두 채우세요. 이미 새 필드가 있던 항목은 생략하지 마세요.
headline: 사용자 말투의 한 줄(20자 안팎), 따옴표 없이 1~30자.
statements: 정확히 2개, 각 1~70자. 1번은 원하는 것, 2번은 막히는 점·바라는 해결.
hashtags: 2~4개, # 없이 명사형 짧은 단어.
flow: context_ids 중 경험이 이어지는 순서로 고르고 사용자 1인칭 한 문장으로 쓰세요.
context_ids를 바꾸면 flow도 맞춰 고치세요. 중복 없이 Context가 하나면 1개, 그 외에는 2개 이상 고르세요.
headline·statements는 title·pain_point와 같은 내용을 짧게 다시 쓴 것입니다.
사용자가 '이 인사이트'·'여기'라고 하면 focus_id 인사이트를 뜻한다. 다른 인사이트는 요청이 명시할 때만 바꾼다.
insight:{id} 대상은 item_id의 항목만 {item: {...}}로 반환하세요. current 목록은 맥락입니다.
flow 문장은 contexts의 pain_point·context_name에 근거해 쓰고 없는 내용을 만들지 마세요.
숫자·축·차원·반례 표시는 만들지 마세요.
