#!/usr/bin/env bash
# 验证合并门只放行与 PR 当前 head 一致的独立复核和用户授权。
set -euo pipefail
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
mkdir "$root/bin"
printf '#!/usr/bin/env bash\nprintf "%%s\\n" "$MERGE_GATE_PR_JSON"\n' > "$root/bin/gh"
chmod +x "$root/bin/gh"
export PATH="$root/bin:$PATH" MERGE_GATE_LEDGER="$root/pending.md"
head=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
title='feat(agents): 新增示例面板'
export MERGE_GATE_PR_JSON="$(jq -nc --arg title "$title" --arg head "$head" '{number:12,title:$title,state:"OPEN",headRefOid:$head,baseRefName:"main",author:{login:"fixture-author"}}')"
script="$(dirname "$0")/merge-gate.sh"
assert_rejected() {
  if bash "$script" 12 >/dev/null 2>&1; then echo "unexpected gate pass: $1" >&2; exit 1; fi
}
printf '%s\n' 'no approval' > "$MERGE_GATE_LEDGER"
assert_rejected 'missing approval'
printf '| PR-Approval #12：%s | 授权 | 已处理（用户原话「批准合并」；Approval-Time:2026-11-15T20:26:34+08:00；Message-ID:abcd1234；Reviewer:other；Review-SHA:old） |\n' "$title" > "$MERGE_GATE_LEDGER"
assert_rejected 'stale review'
printf '| PR-Approval #12：%s | 授权 | 已处理（用户原话「批准合并」；Approval-Time:2026-11-15T20:26:34+08:00；Message-ID:abcd1234；Reviewer:fixture-author；Review-SHA:%s） |\n' "$title" "$head" > "$MERGE_GATE_LEDGER"
assert_rejected 'self review'
printf '| PR-Approval #12：%s | 授权 | 已处理（用户原话「批准合并」；Message-ID:abcd1234；Reviewer:AgentsPRFinalReviewer；Review-SHA:%s） |\n' "$title" "$head" > "$MERGE_GATE_LEDGER"
assert_rejected 'missing time'
printf '| PR-Approval #12：%s | 授权 | 已处理（用户原话「批准合并」；Approval-Time:2026-11-15T20:26:34+08:00；Message-ID:abcd1234；Reviewer:AgentsPRFinalReviewer；Review-SHA:%s） |\n' "$title" "$head" > "$MERGE_GATE_LEDGER"
bash "$script" 12 >/dev/null
printf 'merge-gate: rejected missing/stale/self approval, accepted exact independent review\n'
