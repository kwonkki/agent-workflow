#!/usr/bin/env python3
"""에이전틱 코드 리뷰 — Anthropic SDK 직접 호출형.

claude-code-action 대신 컴퓨팅을 직접 호스팅하고 싶을 때 쓰는 대안 구현이다.
git diff를 모아 Claude에게 리뷰를 요청하고, 발견 사항을 JSON으로 받아 출력한다.
CI에서는 출력된 findings를 `gh pr comment` 등으로 후처리할 수 있다.

사용법:
    export ANTHROPIC_API_KEY=sk-ant-...
    python scripts/agentic_review.py --base main
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys

from anthropic import Anthropic

MODEL = "claude-opus-4-8"

SYSTEM = """\
너는 시니어 코드 리뷰어다. 주어진 git diff만 보고 리뷰한다.
- 정확성 버그(경계 조건, 0으로 나누기, 빈 입력, None, 잘못된 타입)를 최우선으로 본다.
- 사소한 스타일 지적은 하지 않는다.
- 추측하지 말고 diff에 실제로 드러난 문제만 보고한다.

반드시 아래 JSON 스키마로만 응답한다. 다른 텍스트는 출력하지 않는다.
{
  "summary": "<전체 한 줄 평>",
  "findings": [
    {
      "file": "<파일 경로>",
      "line": <라인 번호 또는 null>,
      "severity": "high|medium|low",
      "issue": "<무엇이 문제인지>",
      "suggestion": "<어떻게 고칠지>"
    }
  ]
}
문제가 없으면 findings는 빈 배열로 둔다.
"""


def get_diff(base: str) -> str:
    """base 기준 작업 트리의 변경 diff를 반환한다."""
    try:
        return subprocess.run(
            ["git", "diff", f"{base}...HEAD"] if "..." not in base else ["git", "diff", base],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as e:
        sys.exit(f"git diff 실패: {e.stderr}")


def extract_text(message) -> str:
    """응답에서 text 블록만 이어붙인다 (adaptive thinking 블록은 건너뜀)."""
    return "".join(block.text for block in message.content if block.type == "text")


def review(diff: str) -> dict:
    client = Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용

    # 긴 입력/출력 대비 스트리밍 사용 후 최종 메시지를 받는다.
    with client.messages.stream(
        model=MODEL,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        system=SYSTEM,
        messages=[
            {
                "role": "user",
                "content": f"다음 diff를 리뷰하라:\n\n```diff\n{diff}\n```",
            }
        ],
    ) as stream:
        message = stream.get_final_message()

    raw = extract_text(message).strip()
    # 모델이 코드펜스로 감쌀 수 있으니 방어적으로 벗겨낸다.
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="에이전틱 코드 리뷰")
    parser.add_argument("--base", default="main", help="비교 기준 ref (기본: main)")
    parser.add_argument(
        "--fail-on-high",
        action="store_true",
        help="high severity 발견 시 비정상 종료(코드 1) — CI 게이트용",
    )
    args = parser.parse_args()

    diff = get_diff(args.base)
    if not diff.strip():
        print("변경 사항 없음 — 리뷰 생략.")
        return 0

    result = review(diff)

    print(f"\n요약: {result.get('summary', '(없음)')}\n")
    findings = result.get("findings", [])
    if not findings:
        print("발견된 문제 없음. LGTM ✅")
        return 0

    for f in findings:
        loc = f"{f['file']}:{f.get('line') or '?'}"
        print(f"[{f['severity'].upper()}] {loc}\n  문제: {f['issue']}\n  제안: {f['suggestion']}\n")

    if args.fail_on_high and any(f["severity"] == "high" for f in findings):
        print("high severity 발견 — CI 실패 처리.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
