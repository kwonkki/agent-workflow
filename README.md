# Agentic Engineering Workflow — CI 자동화 샘플

PR이 열리거나 이슈가 등록되면 **AI 에이전트가 자동으로 코드를 리뷰하고, 수정하고, 트리아지**하는
CI/자동화 파이프라인 샘플입니다. 작은 Python 프로젝트(`calculator`)를 대상으로 전체 흐름을 시연합니다.

> 핵심 아이디어: 사람은 *의도*만 PR/이슈로 표현하고, 반복적인 리뷰·수정·분류는 에이전트가 CI에서 처리합니다.

---

## 워크플로우 한눈에 보기

```
                         ┌─────────────────────────────────────────────┐
   개발자 push / PR 생성  │              GitHub (origin)                │
  ───────────────────►   │                                             │
                         │   PR opened / synchronize  ──┐              │
                         │   issue opened             ──┤  trigger     │
                         │   PR comment "@claude ..."  ──┘             │
                         └───────────────┬─────────────────────────────┘
                                         │ GitHub Actions
                         ┌───────────────▼─────────────────────────────┐
                         │            에이전트 작업 (CI 러너)            │
                         │                                             │
                         │  1) claude-code-review.yml                  │
                         │     └ 변경 diff 자동 리뷰 → 인라인 코멘트    │
                         │  2) claude-dispatch.yml                     │
                         │     └ @claude 멘션 → 코드 수정 후 커밋/푸시  │
                         │  3) claude-issue-triage.yml                 │
                         │     └ 이슈 분류 → 라벨 부여 + 요약 코멘트     │
                         │                                             │
                         │  (대안) scripts/agentic_review.py           │
                         │     └ Anthropic SDK 직접 호출형 리뷰         │
                         └───────────────┬─────────────────────────────┘
                                         │ 결과 반영
                         ┌───────────────▼─────────────────────────────┐
                         │  리뷰 코멘트 / 라벨 / 새 커밋 / 상태 체크     │
                         └─────────────────────────────────────────────┘
```

---

## 단계별 에이전틱 루프

이 샘플이 따르는 엔지니어링 루프는 다음과 같습니다.

| 단계 | 트리거 | 에이전트가 하는 일 | 산출물 |
|------|--------|-------------------|--------|
| **Plan** | 이슈 등록 | 이슈를 읽고 영향 범위/작업 항목을 분류 | 라벨 + 요약 코멘트 |
| **Implement** | PR 코멘트 `@claude ...` | 요청대로 코드 수정, 테스트 추가 | 새 커밋 (PR 브랜치) |
| **Review** | PR open / 갱신 | diff를 정적·논리적으로 검토 | 인라인 리뷰 코멘트 |
| **Verify** | 매 PR push | 단위 테스트 + 린트 실행 | 상태 체크(녹/적) |

사람은 각 게이트(merge 승인)에서만 개입하고, 나머지 반복 작업은 에이전트가 수행합니다.

---

## 디렉토리 구조

```
agent-workflow/
├── README.md                       이 문서
├── CLAUDE.md                       에이전트용 프로젝트 규약 (CI 에이전트가 읽음)
├── requirements.txt
├── .github/
│   └── workflows/
│       ├── ci.yml                  테스트 + 린트 (Verify 게이트)
│       ├── claude-code-review.yml  PR 자동 리뷰 (Review)
│       ├── claude-dispatch.yml     @claude 멘션 처리 (Implement)
│       └── claude-issue-triage.yml 이슈 자동 트리아지 (Plan)
├── scripts/
│   └── agentic_review.py           Anthropic SDK 직접 호출형 리뷰 (대안 구현)
├── src/
│   └── calculator.py               시연 대상 코드
└── tests/
    └── test_calculator.py
```

---

## 사전 준비

1. **API 키 등록** — 리포지토리 Settings → Secrets and variables → Actions 에 추가:
   - `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com) 에서 발급

2. **권한** — 워크플로우가 코멘트/커밋을 작성할 수 있도록 각 워크플로우에 `permissions` 블록이 선언되어 있습니다.
   기본 `GITHUB_TOKEN` 으로 동작합니다.

3. (선택) **GitHub App 설치** — `@claude` 멘션 워크플로우를 쓰려면
   [Claude GitHub App](https://github.com/apps/claude) 을 설치하면 권한 관리가 더 깔끔합니다.

---

## 로컬에서 직접 돌려보기

CI 없이 SDK 리뷰 스크립트만 따로 실행할 수 있습니다.

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...

# 작업 트리의 변경분(diff)을 main 기준으로 리뷰
python scripts/agentic_review.py --base main

# 테스트
pytest -q
```

---

## 사용 모델

모든 에이전트 단계는 기본적으로 **Claude Opus 4.8 (`claude-opus-4-8`)** 를 사용합니다.
가볍고 빠른 트리아지에는 `claude-haiku-4-5` 로 낮춰도 됩니다 (워크플로우 파일의 `model:` 참고).
