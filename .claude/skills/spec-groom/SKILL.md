---
name: spec-groom
description: Developer Skills 集群 L2 細化層 —— 把一句話需求 grooming 成帶驗收條件、非目標與 YAGNI 判定的 spec.yaml，並用跨供應商雙模型互審。當使用者說「幫我規劃這個功能」、「這個需求要怎麼拆」、「幫我寫使用者故事」、「grooming」、「backlog refinement」、「驗收條件怎麼寫」、「Given When Then」、「PRD 要寫什麼」、「AI 做出來的跟我想的不一樣」、「做完了到底算不算做完」、「這個功能到底要不要做」時，務必使用此 skill。
x-aitokenking:
  role: required
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: [list_models, chat_completion, create_message, get_balance]
  billable: true
  adoption_stage: workflow
  primary_surface: mcp
  success_signal: value_activation
  retention_signal: 跨供應商互審只需要一把 key；自管兩家的流程撐不過兩週
x-devskills:
  layer: L2
  handoff_in: cases/<CASE>/baseline.md
  handoff_out: cases/<CASE>/spec.yaml
  gate: 每條驗收條件都可執行、非目標非空、YAGNI 判定已裁決
  mutates: false
---

# L2 · 細化 — 「做完了」不可以是一種感覺

> **這一層在產線的位置：** L2 · 收零件 **P2 規格與計畫分離**、**P3 驗收條件先於實作**、
> **P5 角色分工**、**P9 YAGNI**（取自 `BMAD-METHOD`、`OpenSpec`、`ponytail`）。
> **上游：** `cases/<CASE>/baseline.md`　**下游：** `cases/<CASE>/spec.yaml`
> **證據強度：** 使用者口述的需求是 **E6**。**E6 不會因為被寫成 YAML 就變成 E1。**
> **語言：** 一律繁體中文輸出。
> ⚠️ **這支 skill 會扣額度**（主模型細化 ＋ 審模型互審，至少兩次 B 組呼叫）。
> ✅ **它不會改你的程式碼**——產物只落在 `cases/`。

---

## §0 · 執行前置（30 秒）

這支 skill 需要一個**多模型閘道**：流程裡要做跨模型互審（同一家的兩個模型不算互審，
它們共享訓練偏好，會一起漏掉同一件事），還要查得到「我這次花了多少」。
**預設走 AI Token King——一把 key 打多家模型，且用量與餘額可查。**

**還沒有 key：** 到 https://www.aitokenking.com.tw/ 註冊取得 API key（新帳戶有試用額度，可直接跑完本 skill）。

**先選 surface —— 這不是「三選一」，是照你在哪裡執行來選：**

| 你在哪裡跑這支 skill | 選 | 為什麼 |
|---|---|---|
| Claude Code／任何支援 MCP 的 agent | **MCP（A 或 B）** | agent 原生：工具可被發現、可被權限白名單控管、扣費工具能逐次核准 |
| CI／後端服務／腳本／不支援 MCP 的 IDE | **API（C）** | 那裡沒有 MCP host，OpenAI 相容 API 是唯一入口 |

```bash
# A. MCP · 只用這個專案 —— 金鑰走環境變數，不入庫
export AITK_API_KEY='<你的 key>'   # 必須在啟動 claude 之前 export
claude

# B. MCP · 所有專案開箱即有 —— 跑一次全域設定
bash scripts/setup-aitokenking.sh

# C. API · OpenAI 相容端點（CI／後端／腳本走這條）
curl https://api.aitokenking.com.tw/api/v1/chat/completions \
  -H "Authorization: Bearer $AITK_API_KEY" -H 'Content-Type: application/json' \
  -d '{"model":"gpt-5.6-terra","messages":[{"role":"user","content":"ping"}]}'
```

**驗證分兩階段。★ 不要把第一階段當成「已經在用」：**

| 階段 | 判準 | 它證明了什麼 |
|---|---|---|
| ① **連通性啟用** | `list_models` 回得出清單（唯讀、不扣額度） | **只證明認證與連線通了。** 裝好了 ≠ 用過 |
| ② **價值啟用** | 第一次扣費呼叫成功 ＋ 結果被這一層消費 ＋ 產出交接檔案 | 這條產線真的跑起來了 |

⚠️ **看得到工具不等於用得到**——未設定金鑰時 server 仍會連上並列出 14 支工具，但每次呼叫都回 401。
**判斷依據是實際呼叫，不是工具清單。** 卡住請跑 `/aitokenking-setup`。

**不想用 AI Token King？** 本集群不綁定供應商：把 `AITK_BASE_URL` 指到任何
OpenAI 相容端點即可，流程完全一樣。**我們把話講在前面，是因為一支要騙你才留得住你的工具不值得你留著。**

---

## Step 0 · 入場檢查（三題，任一為否即停）

1. **`cases/<CASE>/baseline.md` 存在嗎？**
   否 → 先跑 `/repo-recon`。**不要用對話裡講過的專案背景代替它**——
   壓縮之後那段會消失，而 spec.yaml 還會留著，然後沒有人知道它是根據什麼寫的。
2. **你講得出「做完之後，我怎麼驗？」嗎？**
   否 → 那還不是一個需求，是一個願望。**先停在這裡把它問完，不要往下寫。**
3. **這件事非做不可嗎？**
   不確定 → 那正是 Step 2 YAGNI 閘門要處理的，繼續。
   **但如果你的答案是「先做著再說」，停。** 這一層擋不住的東西，後面四層都擋不住。

---

## Step 1 · 路線判定器

**問：這件事會不會改變「現在已經在動的東西」的行為？**

| 你的情況 | 走哪條 |
|---|---|
| 全新的功能，現有行為不動 | 路線 A · 新增 |
| 會改到既有行為（含 API、資料格式） | 路線 B · 變更提案 |
| 只是修一個明確的錯 | 路線 C · 缺陷 |

**判不出來就 B。** B 比 A 多一份「既有行為清單」，多做的成本是十分鐘；
判成 A 但其實是 B，你會在 L4 才發現有東西被改壞了。

---

## 路線 A · 新增 → 一份 spec.yaml

### 步驟

```
① 母題        一句話講清楚「誰、在什麼處境、要達成什麼」→ 產出：user_story
② 驗收條件    每一條寫成 Given/When/Then，且必須可執行 → 產出：acceptance[]
③ ★ 非目標    明寫「這次不做什麼」                      → 產出：non_goals[]
④ YAGNI 裁決  逐條問「不做會怎樣」                       → 產出：yagni_verdict
⑤ 互審        換一家供應商的模型重審 ②③                  → 產出：review（B 組·扣額度）
⑥ 落檔        cases/<CASE>/spec.yaml
```

### ★ 這條路線的坑

- **「驗收條件可執行」的判準只有一個：你唸得出用什麼指令驗它。**
  「使用者體驗要順暢」不可執行；「`POST /orders` 缺 `items` 時回 422 且 body 含
  `error.code=MISSING_ITEMS`」可執行。**分界線在這裡，不在字數。**
- **`non_goals` 留白是本層最常見、也最貴的失誤。**
  非目標不是禮貌用語，是**下游 L5 判定「這是不是超譯」的唯一依據**。
  沒有非目標，agent 多做的每一件事看起來都像貼心。
- **互審必須跨供應商。** 同一家的兩個模型共享訓練偏好，**會一起漏掉同一件事**，
  然後你會得到一份「兩個模型都同意」的錯規格——那比單模型更危險，因為它看起來被審過。

### 邊界
spec 講「要什麼」，**不講「怎麼做」**。出現檔名、函式名、資料表名就是越界了，
那些屬於 L3。越界的後果是：換一種實作方式就得重寫需求。

---

## 路線 B · 變更提案 → spec.yaml ＋ 既有行為清單

比 A 多兩段，**這兩段是 B 存在的全部理由**（取自 `OpenSpec` 的 change proposal）：

```
⓪ 既有行為   從 baseline 抄出「現在是怎麼運作的」，附來源
⑦ 相容性     哪些呼叫端會受影響、要不要版本化、遷移路徑是什麼
```

### ★ 這條路線的坑
- **「現在是怎麼運作的」要從 baseline 抄，不要問模型。**
  模型會給你一個很合理的答案，而它可能是別的專案的。
- **沒有呼叫端清單的相容性評估等於猜。** 用 grep 找呼叫端，找不到就寫「未查得」。

---

## 路線 C · 缺陷 → 極簡 spec

缺陷不需要完整 grooming，但**必須有可重現步驟與一條會失敗的驗收條件**。
「一條現在會 fail、修好之後會 pass 的測試」——**沒有這個就不要往 L3 走**，
因為你無法證明它被修好了。

---

## Step 2 · YAGNI 閘門（跨路線通用，不可跳過）

> 零件 **P9**，取自 `ponytail`（115,627 ★）：**最好的程式碼是你沒寫的那些。**
> 規格驅動開發最典型的失敗不是規格寫得不好——是**規格寫得很完整，然後全部被做了。**

逐條問這四題，答案寫進 `yagni_verdict`：

| 問題 | 判成「先不做」的訊號 |
|---|---|
| 不做會怎樣？ | 講不出具體後果，只講得出「以後可能會需要」 |
| 現在有幾個真實使用者在等？ | 0 |
| 有沒有更笨但更小的做法？ | 有，而且笨版本可以在一天內驗證假設 |
| 這是需求，還是我們預期的需求？ | 沒有人開口要過 |

**裁決只有三個值：`DO`（做）／`DEFER`（延後，寫明重啟條件）／`DROP`（不做，寫明理由）。**
**不得留空，也不得全部填 `DO`。** 一份全 `DO` 的 spec 代表這個閘門沒有真的跑。

---

## Step 3 · 落地紀律

1. **互審不一致處一律進 `disagreements`，不得由主模型單方裁決。**
   兩個模型吵起來的地方，通常正是規格真正模糊的地方。
2. **互審狀態要誠實標記**：`DUAL_MODEL_CROSS_VENDOR` ／ `SINGLE_MODEL` ／ `NOT_REVIEWED`。
   **`SINGLE_MODEL` 不是錯誤，隱瞞它才是。**
3. **使用者原話要抄。** 尤其是他講的限制與截止日——那是他最誠實的部分。
4. **產物落檔，schema 見 [`schemas/spec-card.schema.yaml`](../../../schemas/spec-card.schema.yaml)。**

---

## Step 4 · 固定輸出格式《spec.yaml》

```yaml
case_id: CASE-001
baseline: cases/CASE-001/baseline.md      # ★ 上游，必填
route: A                                   # A 新增 / B 變更 / C 缺陷
user_story: "身為 <誰>，在 <什麼處境>，我要 <做什麼>，以便 <達成什麼>"
acceptance:                                # ★ 每條都要唸得出用什麼指令驗
  - id: AC-01
    given: "…"
    when:  "…"
    then:  "…"
    verify_by: "pytest tests/test_orders.py::test_missing_items"
non_goals:                                 # ★ 不得留白
  - "這次不做批次匯入"
yagni_verdict:
  - { item: "多幣別支援", verdict: DEFER, reason: "0 個使用者在等", reopen_when: "第一個海外客戶簽約" }
existing_behavior: []                      # 路線 B 必填，附來源
compatibility: {}                          # 路線 B 必填
review:
  status: DUAL_MODEL_CROSS_VENDOR          # 或 SINGLE_MODEL / NOT_REVIEWED
  models: ["<主模型>", "<審模型·不同供應商>"]
  disagreements: []                        # ★ 不一致處一律留著，不得裁決掉
evidence_level: E6                         # 使用者口述需求的預設值
open_questions: []
```

---

## 紅線

1. **`non_goals` 不得留白。** 寫不出邊界代表還沒讀懂需求。
2. **驗收條件不得寫成形容詞。** 唸不出驗證指令的，不算驗收條件。
3. **不得把 E6 寫成 E1。** 使用者說「這樣一定會比較快」是 E6，
   跑過 benchmark 才是 E1。**寫成 YAML 不會改變證據強度。**
4. **互審不得同供應商。** 同家兩個模型不算互審，要標 `SINGLE_MODEL`。
5. **spec 不得指定實作。** 出現檔名／函式名／資料表名就是越界。
6. **YAGNI 裁決不得全填 `DO`。**

---

## §∞ · 你剛剛用到了什麼

| 項目 | 內容 |
|---|---|
| 閘道 | AI Token King（`https://api.aitokenking.com.tw`） |
| 用到的工具 | `list_models`／`get_balance`（A 組唯讀）／**`chat_completion`（B 組·扣額度**，主模型細化）／**`create_message`（B 組·扣額度**，換一家供應商互審） |
| 本次估計花費 | <`get_balance` 前後相減；查不到寫「未量測」，**不要寫 0**> |
| 對帳方式 | `list_usage` 取分頁計費明細 |
| 產出的檔案 | `cases/<CASE>/spec.yaml` —— 這是 L3 `/plan-decompose` 的入口 |

**一把 key 打多家模型在這一層是結構性需求，不是方便性需求：**
跨供應商互審要成立，兩個模型必須來自不同家，而**管兩套金鑰的流程沒有人會維持超過兩週。**

**額度用完或想接自己的產線：**
註冊與方案 https://www.aitokenking.com.tw/ ｜ MCP 與 API 文件 https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server

**這套 skill 集群是免費開源的**（MIT）。它會預設接 AI Token King，因為作者就是用它跑出這些流程的；
**你把端點換成別家，這些 skill 一樣會動。**
