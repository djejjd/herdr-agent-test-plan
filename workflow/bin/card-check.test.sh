#!/usr/bin/env bash
# card-check.test.sh：交付卡校验的回归测试。全过 exit 0。
set -uo pipefail

BIN="${BIN:-$HOME/ai/bin}"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
pass=0; fail=0
check() { # check <期望退出码> <文件名> <标签>
  local want=$1 file=$2 label=$3 got
  "$BIN/card-check" "$file" >/dev/null 2>&1; got=$?
  if [ "$got" -eq "$want" ]; then pass=$((pass+1)); printf '  ✓ %s\n' "$label"
  else fail=$((fail+1)); printf '  ✗ %s（期望 %s，实际 %s）\n' "$label" "$want" "$got"; fi
}

cat > "$tmp/ok.md" <<'EOF'
CARD｜T-1｜侧栏(t7)｜完成
EVIDENCE: cmd=`bash test/run.sh` exit=0; file=src/x.js:42
RULING: 无
NEXT: 无
EOF
check 0 "$tmp/ok.md" "完整卡通过"

cat > "$tmp/no-ev.md" <<'EOF'
CARD｜T-1｜侧栏(t7)｜完成
EVIDENCE:
RULING: 无
NEXT: 无
EOF
check 1 "$tmp/no-ev.md" "空 EVIDENCE 退回"

cat > "$tmp/bad-status.md" <<'EOF'
CARD｜T-1｜侧栏(t7)｜差不多好了
EVIDENCE: file=src/x.js:42
RULING: 无
NEXT: 无
EOF
check 1 "$tmp/bad-status.md" "非法状态退回"

cat > "$tmp/placeholder.md" <<'EOF'
CARD｜T-1｜侧栏(t7)｜完成
EVIDENCE: cmd=（填命令） exit=0
RULING: 无
NEXT: 无
EOF
check 1 "$tmp/placeholder.md" "未填占位符退回"

cat > "$tmp/bad-ev.md" <<'EOF'
CARD｜T-1｜侧栏(t7)｜阻塞
EVIDENCE: 我跑过了，没问题
RULING: 无
NEXT: 无
EOF
check 1 "$tmp/bad-ev.md" "不可复核证据退回"

"$BIN/card-check" >/dev/null 2>&1; [ $? -eq 2 ] && { pass=$((pass+1)); echo "  ✓ 缺参数返回 2"; } || { fail=$((fail+1)); echo "  ✗ 缺参数未返回 2"; }

printf 'card-check: %s 通过, %s 失败\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
