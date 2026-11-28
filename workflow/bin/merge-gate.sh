#!/usr/bin/env bash
# 核对 PR 当前 head、用户逐项授权及独立复核；不执行合并。
set -euo pipefail
pr=${1:-}
if [[ ! $pr =~ ^[1-9][0-9]*$ ]]; then echo 'usage: merge-gate.sh <PR number>' >&2; exit 2; fi
ledger=${MERGE_GATE_LEDGER:-$HOME/ai/collab/pending.md}
info=$(gh pr view "$pr" --json number,title,state,headRefOid,baseRefName,author)
number=$(jq -er '.number' <<< "$info")
title=$(jq -er '.title' <<< "$info")
head=$(jq -er '.headRefOid' <<< "$info")
author=$(jq -er '.author.login' <<< "$info")
if [[ $number != "$pr" || $(jq -r '.state' <<< "$info") != OPEN || $(jq -r '.baseRefName' <<< "$info") != main || ! $head =~ ^[a-f0-9]{40}$ ]]; then
  echo 'merge gate: PR identity, state, base, or head invalid' >&2; exit 1
fi
rows=$(grep -F "| PR-Approval #${pr}：" "$ledger" || true)
if [[ $(grep -c '^|' <<< "$rows") != 1 || $rows != *"$title"* || $rows != *'| 授权 | 已处理（用户原话「'* ]]; then
  echo 'merge gate: one approved PR-Approval row with exact title required' >&2; exit 1
fi
if [[ ! $rows =~ Approval-Time:[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+-][0-9]{2}:[0-9]{2} || ! $rows =~ Message-ID:[a-f0-9]{8} ]]; then
  echo 'merge gate: approval time and message ID required' >&2; exit 1
fi
if [[ ! $rows =~ Reviewer:([[:alnum:]_-]+) ]]; then echo 'merge gate: reviewer required' >&2; exit 1; fi
reviewer=${BASH_REMATCH[1]}
if [[ $reviewer == "$author" || $rows != *"Review-SHA:$head"* ]]; then
  echo 'merge gate: independent reviewer at current PR head required' >&2; exit 1
fi
printf 'merge gate passed: PR #%s head %s reviewer %s\n' "$pr" "${head:0:12}" "$reviewer"
