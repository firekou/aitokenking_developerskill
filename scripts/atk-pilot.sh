#!/usr/bin/env bash
# AI Token King · E1 整合 pilot（回應 review DEV-GROWTH-003）
#
# ★ 這支腳本存在的理由：
#   本 repo 宣稱「AI Token King 是這條產線的結構性依賴」，但那句話目前是 E2/E6ㄧ
#   讀自官方文件與我方設計意圖，我方零實跑。缺口 DS-G6。
#   這支腳本把「跑一次來證明」的成本降到一行指令，讓缺口有一個關得掉的入口。
#
# ⚠️ 這支腳本會扣你的額度。 --dry-run 之外的每一次執行都會呼叫 B 組工具。
#    預設是 --dry-run，你必須明確加 --live 才會真的花錢。
#
# 用法：
#   bash scripts/atk-pilot.sh                       # 乾跑：只做 A 組唯讀檢查，不扣費
#   bash scripts/atk-pilot.sh --live                # 實跑：跑 Pilot A（1 次扣費呼叫）
#   bash scripts/atk-pilot.sh --live --cross-vendor # 實跑：加跑 Pilot B（2 次，需兩家模型）
#
# 產物：cases/PILOT-001/atk-integration.md —— 貼進 PR 就是 DS-G6 的關閉證據。

set -euo pipefail

LIVE=0
CROSS=0
for a in "$@"; do
  case "$a" in
    --live)         LIVE=1 ;;
    --cross-vendor) CROSS=1 ;;
    -h|--help)      sed -n '2,22p' "$0"; exit 0 ;;
    *) echo "未知參數：$a"; exit 2 ;;
  esac
done

BASE="${AITK_BASE_URL:-https://api.aitokenking.com.tw/api/v1}"
OUT_DIR="cases/PILOT-001"
OUT="$OUT_DIR/atk-integration.md"
STAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

command -v curl >/dev/null || { echo "需要 curl"; exit 1; }
command -v python3 >/dev/null || { echo "需要 python3"; exit 1; }

if [[ -z "${AITK_API_KEY:-}" ]]; then
  echo "✗ 目前 shell 沒有 AITK_API_KEY。"
  echo "  到 https://www.aitokenking.com.tw/ 取得 key，然後："
  echo "    export AITK_API_KEY='<你的 key>'"
  echo "  ⚠️ 寫進 .env 而沒有 export 沒有用 —— 讀的是 process 環境變數。"
  exit 1
fi

say() { printf '%s\n' "$*"; }
api() { curl -sS -m 60 -H "Authorization: Bearer $AITK_API_KEY" "$@"; }

mkdir -p "$OUT_DIR"
say "AI Token King · E1 pilot"
say "  端點 : $BASE"
say "  模式 : $([[ $LIVE == 1 ]] && echo '實跑（會扣額度）' || echo '乾跑（不扣額度）')"
say ""

# ── 階段 ① 連通性啟用（A 組唯讀，不扣額度）────────────────────────────
say "① 連通性啟用 —— list_models"
MODELS_RAW="$(api "$BASE/models" || true)"
MODEL_COUNT="$(printf '%s' "$MODELS_RAW" | python3 -c '
import json,sys
try:
    d = json.load(sys.stdin)
except Exception:
    print(-1); sys.exit()
items = d.get("data", d if isinstance(d, list) else [])
print(len(items) if isinstance(items, list) else -1)
' 2>/dev/null || echo -1)"

if [[ "$MODEL_COUNT" -le 0 ]]; then
  say "   ✗ 取不到模型清單。原始回應前 300 字："
  printf '%s\n' "${MODELS_RAW:0:300}"
  say ""
  say "   401 永遠是認證問題，不是 server 問題。排錯走 /aitokenking-setup 路線 D。"
  exit 1
fi
say "   ✓ 列得出 $MODEL_COUNT 支模型"
FIRST_MODEL="$(printf '%s' "$MODELS_RAW" | python3 -c '
import json,sys
d=json.load(sys.stdin); items=d.get("data", d if isinstance(d,list) else [])
print(items[0].get("id","") if items and isinstance(items[0],dict) else "")
')"
say "   取樣模型：$FIRST_MODEL"

BAL_BEFORE="$(api "$BASE/../balance" 2>/dev/null || echo "")"
[[ -z "$BAL_BEFORE" ]] && BAL_BEFORE="未量測"

if [[ $LIVE == 0 ]]; then
  say ""
  say "② 價值啟用 —— 乾跑，未執行"
  say "   ⚠️ 只有階段 ① 通過時，正確的說法是「裝好了，但還沒用過」。"
  say "   要真的關掉缺口 DS-G6，必須加 --live 跑一次扣費呼叫。"
  say ""
  say "   下一步：bash scripts/atk-pilot.sh --live"
  exit 0
fi

# ── 階段 ② 價值啟用（B 組，會扣額度）──────────────────────────────────
say ""
say "② 價值啟用 —— chat_completion（★ 這一步開始扣額度）"
REQ='{"model":"'"$FIRST_MODEL"'","messages":[{"role":"user","content":"回覆一個字：ok"}],"max_tokens":16}'
RESP="$(api -H 'Content-Type: application/json' -d "$REQ" "$BASE/chat/completions" || true)"
CONTENT="$(printf '%s' "$RESP" | python3 -c '
import json,sys
try:
    d=json.load(sys.stdin)
    print(d["choices"][0]["message"]["content"].strip()[:80])
except Exception:
    print("")
' 2>/dev/null || echo "")"

if [[ -z "$CONTENT" ]]; then
  say "   ✗ 扣費呼叫失敗。原始回應前 300 字："
  printf '%s\n' "${RESP:0:300}"
  say "   ★ 失敗也要寫進 pilot 報告 —— 失敗的那次比成功的更有價值。"
else
  say "   ✓ 模型回應：$CONTENT"
fi

BAL_AFTER="$(api "$BASE/../balance" 2>/dev/null || echo "")"
[[ -z "$BAL_AFTER" ]] && BAL_AFTER="未量測"

# ── Pilot B · 跨供應商互審（選配）────────────────────────────────────
CROSS_NOTE="未執行"
if [[ $CROSS == 1 ]]; then
  say ""
  say "③ Pilot B · 跨供應商互審 —— 需要第二家供應商的模型"
  SECOND_MODEL="$(printf '%s' "$MODELS_RAW" | python3 -c '
import json,sys
d=json.load(sys.stdin); items=d.get("data", d if isinstance(d,list) else [])
ids=[i.get("id","") for i in items if isinstance(i,dict)]
first=ids[0] if ids else ""
def vendor(m): return m.split("-")[0].split("/")[0].lower()
for m in ids[1:]:
    if vendor(m) != vendor(first):
        print(m); break
else:
    print("")
')"
  if [[ -z "$SECOND_MODEL" ]]; then
    CROSS_NOTE="✗ 找不到不同供應商的第二支模型 —— 互審無法成立，應標記 SINGLE_MODEL"
    say "   $CROSS_NOTE"
  else
    R2="$(api -H 'Content-Type: application/json' \
      -d '{"model":"'"$SECOND_MODEL"'","messages":[{"role":"user","content":"回覆一個字：ok"}],"max_tokens":16}' \
      "$BASE/chat/completions" || true)"
    if printf '%s' "$R2" | grep -q '"content"'; then
      CROSS_NOTE="✓ 第二家供應商模型 $SECOND_MODEL 呼叫成功 —— 互審前提成立"
    else
      CROSS_NOTE="✗ 第二家模型 $SECOND_MODEL 呼叫失敗"
    fi
    say "   $CROSS_NOTE"
  fi
fi

# ── 產出報告 ──────────────────────────────────────────────────────────
cat > "$OUT" <<REPORT
# AI Token King 整合 pilot · PILOT-001

**執行時間（UTC）：** $STAMP
**端點：** \`$BASE\`
**證據強度：** **E1（本機實跑）** —— 下列數字來自實際呼叫，非設計意圖。

| 階段 | 判準 | 結果 |
|---|---|---|
| ① 連通性啟用 | \`list_models\` 回得出清單 | ✓ $MODEL_COUNT 支模型 |
| ② 價值啟用 | 首次扣費呼叫成功 | $([[ -n "$CONTENT" ]] && echo "✓ 回應：\`$CONTENT\`" || echo "✗ 失敗，見下方原始回應") |
| ③ 跨供應商互審前提 | 找得到第二家供應商的模型 | $CROSS_NOTE |

## 成本

| 項目 | 值 |
|---|---|
| 呼叫前餘額 | $BAL_BEFORE |
| 呼叫後餘額 | $BAL_AFTER |
| 差額 | $([[ "$BAL_BEFORE" == "未量測" || "$BAL_AFTER" == "未量測" ]] && echo "**未量測**（端點未提供餘額查詢；照鐵律五不得寫 0）" || echo "見上方兩列相減") |

## 取樣模型

\`$FIRST_MODEL\`（取 \`list_models\` 回傳的第一支，非人工挑選）

## 這份報告關掉了什麼

- 若 ①② 皆 ✓：缺口 **DS-G6** 的「連通性 ＋ 價值啟用」部分可關閉。
- 若 ③ 為 ✓：\`spec-groom\` 的跨供應商互審**前提**成立，
  但**互審效果本身仍未驗證**——那需要對照實驗，不是一次 ping。

## 這份報告不能證明什麼

1. **不能證明多模型互審比單模型可靠。** 那需要對照組，見 review §9.5。
2. **不能證明 AI Token King 比別家好。** 它只證明這個端點在本機這一次跑得通。
3. **一次成功不是可重現。** 要 E1 級的可重現，至少跑三次並附全部輸出。
REPORT

say ""
say "✅ 報告已寫入 $OUT"
say "   貼進 PR 即可作為缺口 DS-G6 的關閉證據。"
say "   ⚠️ 一次成功不是可重現 —— 要 E1 級請至少跑三次並附全部輸出。"
