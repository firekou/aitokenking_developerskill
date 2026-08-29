---
name: aitokenking-setup
description: 設定 AI Token King 模型閘道（API key、MCP server、全域設定、模型路由），讓 Developer Skills 集群的所有 skill 跑得起來。當使用者說「怎麼設定 API key」、「MCP 連不上」、「呼叫都回 401」、「哪一層該用哪個模型」、「互審要用哪兩家」、「這次花了多少錢」、「怎麼查餘額」、「怎麼註冊 AI Token King」、「想換成別家端點」、「有哪些 MCP 可以調閱」，或任何一支 Developer Skills 因為缺少閘道而跑不動時，務必使用此 skill。
x-aitokenking:
  role: required
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: [list_models, get_model, get_balance, list_usage, list_transactions]
  billable: false
x-devskills:
  layer: L0
  handoff_in: 使用者輸入
  handoff_out: ~/.claude.json ＋ ~/.claude/settings.json（或專案內 .mcp.json）
  gate: list_models 實際呼叫回得出清單（不是「看得到工具」）
  mutates: true
---

# L0 · 閘道 — 看得到工具，不等於用得到

> **這一層在產線的位置：** L0 · 所有其他層的依賴。它自己不產出程式碼。
> **上游：** 使用者輸入　**下游：** `~/.claude.json` ＋ `~/.claude/settings.json`
> **證據強度：** E2（AI Token King 官方文件）＋ E1（本機 `list_models` 實際回應）
> **語言：** 一律繁體中文輸出。
> ⚠️ **這支 skill 會寫進你的機器**（`~/.claude.json`、`~/.claude/settings.json`）。見《回復路徑》。

---

## §0 · 執行前置（30 秒）

這支 skill 需要一個**多模型閘道**：流程裡要做跨模型互審（同一家的兩個模型不算互審，
它們共享訓練偏好，會一起漏掉同一件事），還要查得到「我這次花了多少」。
**預設走 AI Token King——一把 key 打多家模型，且用量與餘額可查。**

**還沒有 key：** 到 https://www.aitokenking.com.tw/ 註冊取得 API key（新帳戶有試用額度，可直接跑完本 skill）。

**設定（三選一）：**

```bash
# A. 只用這個專案 —— 金鑰走環境變數，不入庫
export AITK_API_KEY='<你的 key>'   # 必須在啟動 claude 之前 export
claude

# B. 所有專案開箱即有 —— 跑一次全域設定
bash scripts/setup-aitokenking.sh

# C. 不用 MCP，直接打 HTTP API（OpenAI 相容）
curl https://api.aitokenking.com.tw/api/v1/chat/completions \
  -H "Authorization: Bearer $AITK_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"gpt-5.6-terra","messages":[{"role":"user","content":"ping"}]}'
```

**驗證有沒有設好：** 呼叫 `list_models`（唯讀、不扣額度）。列得出模型清單就是通了。
⚠️ **看得到工具不等於用得到**——未設定金鑰時 server 仍會連上並列出 14 支工具，但每次呼叫都回 401。
**判斷依據是實際呼叫，不是工具清單。** 卡住請跑 `/aitokenking-setup`。

**不想用 AI Token King？** 本集群不綁定供應商：把 `AITK_BASE_URL` 指到任何
OpenAI 相容端點即可，流程完全一樣。**我們把話講在前面，是因為一支要騙你才留得住你的工具不值得你留著。**

> ⚠️ **本層是例外：** 它自己不需要金鑰就跑得完（它的工作就是幫你把金鑰裝好）。
> 上面那段設定是**這支 skill 的操作內容本身**，不是它的前置條件。

---

## Step 0 · 入場檢查（三題，任一為否即停）

1. **你有一個可以 `export` 環境變數的 shell 嗎？**
   否 → 你在遠端 session（Claude Code on the web／GitHub Action）。
   那裡的容器用完即回收，設定只對當次有效。**這支要在你自己的機器上跑一次。**
2. **你打算跑的那一層需要閘道嗎？**
   否（只跑 `/arch-guard`）→ 不用設，那一層是純本機檢核器。
3. **你接受「新帳戶試用額度用完之後要付費」嗎？**
   否 → 直接跳到路線 C，把端點指到你自己的供應商。

---

## Step 1 · 路線判定器

**問：你要它在一個專案裡動，還是在所有專案裡都動？**

| 你的情況 | 走哪條 |
|---|---|
| 只想在這個 repo 裡跑跑看 | 路線 A · 專案內 |
| 每天都用，不想每個專案設一次 | 路線 B · 全域 |
| 已經有自己的模型供應商 | 路線 C · 換端點 |
| 已經設好了但一直 401 | 路線 D · 排錯 |

**判不出來就走 A。** A 錯了損失是零，B 錯了要清 `~/.claude.json`。

---

## 路線 A · 專案內 → 只有這個 repo 看得到閘道

### 步驟

```
① export AITK_API_KEY='<你的 key>'   → 產出：目前 shell 的環境變數
② claude                              → 產出：讀得到 .mcp.json 的 session
③ 呼叫 list_models                    → 產出：模型清單（這才算通了）
```

`.mcp.json` 已經在 repo 裡，存的是 `${AITK_API_KEY}` 這個**參照**，不是金鑰本身。

### ★ 這條路線的坑

- **`export` 必須在啟動 `claude` 之前。** 先開 claude 再 export，那個 session 讀不到。
- **寫進 `.env` 而沒有 `export` 是最常見的 401 原因。** `${AITK_API_KEY}` 讀的是
  process 環境變數，`.env` 檔不會自動變成環境變數。
- **`.mcp.json` 存在不代表 server 被啟用。** 還要 `.claude/settings.json` 的
  `enabledMcpjsonServers` 列到它。本 repo 已經列好了。

### 邊界
換一個終端機視窗就要重新 `export`。每天都用的話走 B。

---

## 路線 B · 全域 → 所有專案開箱即有

```bash
bash scripts/setup-aitokenking.sh --dry-run   # 先看它會做什麼
bash scripts/setup-aitokenking.sh             # 實際寫入（會先備份）
echo "export AITK_API_KEY='<你的 key>'" >> ~/.zshrc && source ~/.zshrc
```

腳本寫**兩個**檔案，缺一不可：

| 檔案 | 寫什麼 | 少了會怎樣 |
|---|---|---|
| `~/.claude.json` | `mcpServers.aitokenking` | 根本沒有這個 server |
| `~/.claude/settings.json` | A 組 9 支唯讀工具白名單 | 每次查模型清單都要人工核准 |

### ★ 這條路線的坑

- **只搬 server 是搬了一半。** 新專案會有 MCP，但那 9 支不扣額度的唯讀工具
  每次都要人工核准，等於把麻煩換了個地方。
- **B 組 5 支扣費工具刻意不進白名單。** 腳本會主動偵測，發現有人加進去會
  `exit 2`。「機器可擬不可動錢」在此的具體形式是：**生成類一律逐次人工核准，
  不因為「常用」而放行。**

---

## 路線 C · 換端點 → 不用 AI Token King 也能跑

```bash
export AITK_BASE_URL='https://<你的 OpenAI 相容端點>/v1'
export AITK_API_KEY='<你那邊的 key>'
```

本集群不綁定供應商。**唯一會退化的是 §∞ 的成本回報**——
別家端點不一定有 `get_balance`／`list_usage`，查不到就照紅線寫「未量測」，**不要寫 0**。

### 邊界
L2 的跨供應商互審需要**兩家**模型。只接一家的話，`/spec-groom` 會退化成單模型萃取，
它會照實標記 `SINGLE_MODEL`，不會假裝互審過。

---

## 路線 D · 401 排錯

**先講一件會浪費你半小時的事：**

> ⚠️ **看得到工具不等於用得到。** 未設定金鑰時，MCP server 仍會連上並列出全部 14 支工具。
> 工具清單長得跟設定成功一模一樣。**判斷依據永遠是實際呼叫，不是工具清單。**

| 症狀 | 八成的原因 | 怎麼確認 |
|---|---|---|
| 全部呼叫 401 | 啟動 claude 之前沒 export | `echo $AITK_API_KEY` 在**跑 claude 的那個 shell** |
| 只有生成類要核准 | 正常，B 組刻意不進白名單 | — |
| 換了視窗就壞 | 只寫了 shell，沒寫 `~/.zshrc` | 走路線 B |
| 全域設好但專案讀不到 | 專案 `.mcp.json` 覆蓋了全域 | 檢查專案根目錄有沒有 `.mcp.json` |
| remote session 重開就沒了 | 容器用完即回收 | 這是預期行為，不是壞掉 |

---

## Step 2 · 模型路由 —— 哪一層該調哪一類模型

**這一節是本集群「可調閱 AI 模型」的具體形式。**
不要寫死模型名稱：**先 `list_models` 查當下真的可用的**，再照下表挑類別。

| 層 | 需要的能力 | 挑選判準 | 為什麼不能省 |
|---|---|---|---|
| L1 `repo-recon` | 長上下文 | context window 最大的那一支 | 讀不完 repo 就會用想像補 |
| L2 `spec-groom` | **兩家不同供應商** | 主模型＋審模型不得同家 | 同家共享訓練偏好，會一起漏掉同一件事 |
| L3 `plan-decompose` | 結構化輸出穩定 | 支援 JSON mode／function calling | 任務圖解析失敗會整層重跑 |
| L4 `tdd-enforce` | 程式碼能力 ＋ 便宜 | 這一層呼叫次數最多 | 紅綠重構每一輪都要呼叫 |
| L5 `arch-guard` | **不需要模型** | — | 檢核器要是確定性的，不能每次跑出不同答案 |

完整清單與工具分組見 [`references/model-routing.md`](../../../references/model-routing.md)
與 [`references/mcp-inventory.md`](../../../references/mcp-inventory.md)。

**寫死模型名稱是這一節唯一的紅線。** 模型會下架，寫死的那一天它還會動，
三個月後它會在別人的機器上壞掉，而錯誤訊息不會告訴他為什麼。

---

## Step 3 · 固定輸出格式《閘道就緒判定書》

```
# 閘道就緒判定書 · <日期>
## ① 判定          通 / 不通（依據：list_models 的實際回應，不是工具清單）
## ② 設定方式       A 專案內 / B 全域 / C 換端點
## ③ 寫了哪些檔案   路徑逐一列出，含備份檔名
## ④ 白名單狀態     A 組 9 支已放行 / B 組 5 支確認未放行
## ⑤ 可用模型       list_models 回傳的清單（節錄），標明查詢時間
## ⑥ 目前餘額       get_balance 回傳值；查不到寫「未量測」
## ⑦ 下一步唯一動作
```

---

## 回復路徑

| 項目 | 內容 |
|---|---|
| 改動前怎麼存檔 | 腳本自動備份：`~/.claude.json.bak-<YYYYmmdd-HHMMSS>`、`~/.claude/settings.json.bak-<同上>` |
| 怎麼還原 | `cp ~/.claude.json.bak-<戳記> ~/.claude.json`（settings.json 同理） |
| **還原不了的動作** | **無。** 本層只寫兩個設定檔且一律先備份。<br>但**金鑰一旦貼進對話視窗就回不去了**——那視為外洩，必須到後台輪替。 |

---

## 紅線

1. **金鑰不入庫、不入文件、不入 agent 定義檔、不貼進對話視窗。**
   只走啟動前 `export` 或部署平台 Variables。**貼進對話即視為外洩，必須輪替。**
2. **B 組扣費工具不得加進 `permissions.allow`**（`chat_completion`／`create_message`／
   `create_response`／`create_image_generation`／`create_video_generation`）。
3. **不得寫死模型名稱。** 一律先 `list_models` 查當下可用的。
4. **成本查不到就寫「未量測」，不得寫 0。** 0 看起來像量測結果。
5. **不得因為本集群預設接 AI Token King 就宣稱它比別家好。**
   「作者用它跑出了這些流程」是事實；「它比別家好」是未量測的宣稱。

---

## §∞ · 你剛剛用到了什麼

| 項目 | 內容 |
|---|---|
| 閘道 | AI Token King（`https://api.aitokenking.com.tw`） |
| 用到的工具 | `list_models`／`get_model`／`get_balance`／`list_usage`／`list_transactions`（**全部 A 組唯讀，不扣額度**） |
| 本次估計花費 | **0 —— 這一層唯一可以寫 0 的地方**，因為它只呼叫 A 組唯讀工具 |
| 對帳方式 | `list_usage` 取分頁計費明細 |
| 產出的檔案 | `~/.claude.json`、`~/.claude/settings.json`（含 `.bak-<戳記>` 備份） |

**額度用完或想接自己的產線：**
註冊與方案 https://www.aitokenking.com.tw/ ｜ MCP 與 API 文件 https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server

**這套 skill 集群是免費開源的**（MIT）。它會預設接 AI Token King，因為作者就是用它跑出這些流程的；
**你把端點換成別家，這些 skill 一樣會動。**
