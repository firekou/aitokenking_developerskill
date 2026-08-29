#!/usr/bin/env bash
# Developer Skills 集群 —— AI Token King 全域設定
#
# 寫兩個檔案，缺一不可：
#   ~/.claude.json          → mcpServers.aitokenking（server 本身）
#   ~/.claude/settings.json → permissions.allow（A 組 9 支唯讀工具白名單）
#
# ★ 為什麼一定要兩件一起放：只放 server 是搬了一半 —— 新專案會有 MCP，
#   但那 9 支不扣額度的唯讀工具每次都要人工核准，等於把麻煩換了個地方。
#
# ★ 金鑰不入設定檔。 這裡寫的是 ${AITK_API_KEY} 這個「參照」，
#   金鑰本身只存在 shell 環境（~/.zshrc 或 ~/.bashrc 的 export）。
#   本腳本不接受、不寫入、不回顯金鑰值。
#
# 用法：
#   bash scripts/setup-aitokenking.sh            # 實際寫入（先備份）
#   bash scripts/setup-aitokenking.sh --dry-run  # 只看會做什麼

set -euo pipefail

DRY_RUN=0
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=1

MCP_URL="https://api.aitokenking.com.tw/mcp"
CLAUDE_JSON="$HOME/.claude.json"
SETTINGS_JSON="$HOME/.claude/settings.json"

# A 組 · 唯讀，不扣額度 → 進白名單
READONLY_TOOLS=(
  list_models get_model list_image_models list_video_models
  get_balance list_usage list_transactions
  get_image_generation get_video_generation
)
# B 組 · 每次呼叫都扣額度 → ★ 刻意不進白名單
BILLABLE_TOOLS=(
  chat_completion create_message create_response
  create_image_generation create_video_generation
)

command -v python3 >/dev/null || { echo "需要 python3"; exit 1; }

echo "AI Token King 全域設定"
echo "  MCP 端點 : $MCP_URL"
echo "  註冊     : https://www.aitokenking.com.tw/"
echo "  文件     : https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server"
echo "  模式     : $([[ $DRY_RUN == 1 ]] && echo 乾跑 || echo 寫入)"
echo

if [[ -z "${AITK_API_KEY:-}" ]]; then
  echo "⚠️  目前 shell 沒有 AITK_API_KEY。設定檔仍會寫入（它存的是參照不是金鑰），"
  echo "    但在 export 之前每次呼叫都會回 401。"
  echo
  echo "    到 https://www.aitokenking.com.tw/ 註冊取得 key，然後："
  echo "      echo \"export AITK_API_KEY='<你的 key>'\" >> ~/.zshrc && source ~/.zshrc"
  echo
  echo "    ⚠️ 寫進 .env 而沒有 export 是最常見的 401 原因 ——"
  echo "       \${AITK_API_KEY} 讀的是 process 環境變數，不是 .env 檔。"
  echo
fi

TOOLS_CSV=$(printf '%s,' "${READONLY_TOOLS[@]}")
BILL_CSV=$(printf '%s,' "${BILLABLE_TOOLS[@]}")

DRY_RUN=$DRY_RUN MCP_URL=$MCP_URL CLAUDE_JSON=$CLAUDE_JSON \
SETTINGS_JSON=$SETTINGS_JSON TOOLS_CSV=$TOOLS_CSV BILL_CSV=$BILL_CSV \
python3 <<'PY'
import json, os, pathlib, shutil, sys, time

dry       = os.environ["DRY_RUN"] == "1"
url       = os.environ["MCP_URL"]
readonly  = [t for t in os.environ["TOOLS_CSV"].split(",") if t]
billable  = [t for t in os.environ["BILL_CSV"].split(",") if t]
stamp     = time.strftime("%Y%m%d-%H%M%S")

def load(p):
    p = pathlib.Path(p)
    if not p.exists():
        return {}, p
    try:
        return json.loads(p.read_text() or "{}"), p
    except json.JSONDecodeError:
        print(f"✗ {p} 不是合法 JSON，已中止（不覆寫任何東西）")
        sys.exit(1)

def save(p, data):
    if dry:
        print(f"  [乾跑] 會寫入 {p}")
        return
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        bak = p.with_suffix(p.suffix + f".bak-{stamp}")
        shutil.copy2(p, bak)
        print(f"  已備份 → {bak}")
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"  已寫入 {p}")

# ① server 本身
cfg, path = load(os.environ["CLAUDE_JSON"])
cfg.setdefault("mcpServers", {})["aitokenking"] = {
    "type": "http",
    "url": url,
    # ★ 存的是參照不是金鑰
    "headers": {"X-AItokenKing-Api-Key": "${AITK_API_KEY}"},
}
print("① mcpServers.aitokenking")
save(path, cfg)

# ② A 組唯讀白名單
st, spath = load(os.environ["SETTINGS_JSON"])
allow = st.setdefault("permissions", {}).setdefault("allow", [])
added = 0
for t in readonly:
    entry = f"mcp__aitokenking__{t}"
    if entry not in allow:
        allow.append(entry)
        added += 1
print(f"\n② permissions.allow —— A 組唯讀 {len(readonly)} 支（新增 {added}）")
save(spath, st)

# ③ ★ 主動偵測 B 組有沒有被加進白名單
leaked = [t for t in billable if f"mcp__aitokenking__{t}" in allow]
if leaked:
    print("\n🔴 B 組扣費工具出現在白名單中：", ", ".join(leaked))
    print("   「機器可擬不可動錢」在此的具體形式是：生成類一律逐次人工核准，")
    print("   不因為「常用」而放行。請手動移除後重跑。")
    sys.exit(2)

print("\n✅ 完成。")
print("   驗證：重開一個 claude session，呼叫 list_models（唯讀，不扣額度）。")
print("   ⚠️ 看得到工具不等於用得到 —— 未設金鑰時 14 支工具照樣列得出來，但每次呼叫都 401。")
print("      判斷依據是實際呼叫，不是工具清單。")
PY

cat <<'EOF'

⚠️ 遠端 session 無效：Claude Code on the web／GitHub Action 等環境的容器用完即回收，
   在那裡跑這支腳本只對當次 session 有效。它要在你自己的機器上跑一次。
EOF
