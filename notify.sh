#!/bin/bash
# SmallTV Agent Hook Notification Trigger
# Usage:
#   ./notify.sh "작업 제목" "상세 메시지" [지속초, 기본 10초]
# Example:
#   ./notify.sh "빌드 완료!" "모든 유닛 테스트 통과" 10

TITLE="${1:-TASK COMPLETE!}"
MESSAGE="${2:-에이전트 작업이 성공적으로 완료되었습니다!}"
DURATION="${3:-10}"

curl -s -X POST http://localhost:8765/api/notify \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"$TITLE\", \"message\": \"$MESSAGE\", \"duration\": $DURATION}" \
  > /dev/null

echo "🎉 SmallTV로 작업 완료 알림 이펙트를 전송했습니다: [$TITLE] $MESSAGE (${DURATION}초간)"
