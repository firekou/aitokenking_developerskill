---
name: plan-decompose
description: Developer Skills 集群 L3 分解層 —— 把 spec.yaml 拆成有依賴、有風險等級、每一項都綁著一條會失敗的測試的 task-graph.yaml。當使用者說「這個規格要怎麼拆成任務」、「先做哪一個」、「任務依賴怎麼排」、「可以平行做嗎」、「幫我開 ticket」、「拆 story」、「這個功能要做幾天」、「AI 一次改太多我看不懂」、「PR 太大沒人想 review」時，務必使用此 skill。
x-aitokenking:
  role: required
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: [list_models, chat_completion, get_balance]
  billable: true
  adoption_stage: workflow
  primary_surface: mcp
  success_signal: value_activation
  retention_signal: routing 判準沿用同一份 references/model-routing.md，不必為每一層重新選型
x-devskills:
  layer: L3
  handoff_in: cases/<CASE>/spec.yaml
  handoff_out: cases/<CASE>/task-graph.yaml
  gate: 每個任務都綁得到一條驗收條件、依賴圖無環、最大任務估不超過一個工作天
  mutates: false
---

# L3 · 分解 — 任務是一等公民，不是待辦清單上的一行字

> **這一層在產線的位置：** L3 · 收零件 **P4 任務圖與依賴**、**P7 狀態落檔**
> （取自 `claude-task-master`、`planning-with-files`）。
> **上游：** `cases/<CASE>/spec.yaml`　**下游：** `cases/<CASE>/task-graph.yaml`
> **證據強度：** 工時估計一律 **E5（LLM 推測）**，除非有同類任務的實際紀錄可比對。
> **語言：** 一律繁體中文輸出。
> ⚠️ **這支 skill 會扣額度**（任務分解與依賴推導用 `chat_completion`）。
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

1. **`cases/<CASE>/spec.yaml` 存在，且 `acceptance[]` 每條都有 `verify_by` 嗎？**
   否 → 回 `/spec-groom`。**沒有驗收條件的規格拆不出任務，只拆得出願望。**
2. **`non_goals` 非空嗎？**
   否 → 回 L2。**沒有非目標，分解會無限膨脹**——每個任務都會長出三個「順便」。
3. **你打算讓 agent 一次做完全部，還是一次一個任務？**
   「一次做完」→ 停。**那不需要任務圖，你需要的是承擔後果的心理準備。**
   這一層的全部價值建立在「一次只推進一個節點」。

---

## Step 1 · 路線判定器

**問：這份 spec 的驗收條件有幾條？**

| 條數 | 走哪條 |
|---|---|
| 1–2 條 | 路線 A · 線性 |
| 3–8 條 | 路線 B · 依賴圖 |
| 9 條以上 | 路線 C · 先切階段，再對每階段跑 B |

**判不出來就 B。** A 是 B 的退化情況，多畫一張圖不會錯；
該用 B 卻用了 A，你會在第三個任務發現它其實依賴第五個。

---

## 路線 A · 線性 → 一串任務

```
① 每條 acceptance → 至少一個任務        產出：tasks[]
② 每個任務綁一條「現在會 fail 的測試」   產出：task.red_test
③ 排序，落檔
```

### ★ 這條路線的坑
**「綁一條現在會 fail 的測試」不是形式主義。**
沒有它，L4 開工時第一件事會是「先想想要怎麼驗」——而那時候他已經在寫實作了，
**於是測試會被寫成「證明我剛寫的東西是對的」，而不是「證明需求被滿足了」。**

---

## 路線 B · 依賴圖 → tasks ＋ DAG

```
① 分解        每條 acceptance 拆成 1–3 個任務          產出：tasks[]
② 依賴        逐對問「A 沒做完，B 能不能開始？」        產出：depends_on[]
③ ★ 環檢查    有環就是分解錯了，不是排序問題            產出：無環的 DAG
④ 風險等級    每個任務標 low/mid/high，判準見下表       產出：task.risk
⑤ 切分檢查    估超過一個工作天的任務一律再拆            產出：可執行的粒度
⑥ 平行標記    無依賴關係且不動同一批檔案 → parallel_ok
⑦ 落檔
```

### 風險等級的判準（不得憑感覺填）

| 等級 | 判準 |
|---|---|
| `high` | 動到資料格式、對外 API、認證、金流，或 baseline 的「禁區」清單 |
| `mid` | 動到多個模組共用的程式碼，或沒有既有測試覆蓋 |
| `low` | 單一模組內、已有測試覆蓋、可獨立回滾 |

**`high` 的任務不得標 `parallel_ok`。** 兩件高風險的事同時做，出事時你分不出是誰弄的。

### ★ 這條路線的坑

- **依賴圖有環，代表分解錯了。** 不要靠排序繞過去——回頭把那兩個任務合併或重切。
- **「不動同一批檔案」才算可平行。** 只看依賴不看檔案，兩個平行任務會在同一個檔案上打架，
  而衝突會出現在 L4 最忙的時候。
- **估超過一天的任務一定要再拆。** 這不是生產力主張，是**可回滾性**主張：
  一天的工作出錯，你丟掉一天；一週的工作出錯，你會捨不得丟，然後開始修補一個錯的地基。

### 邊界
任務圖不預測「什麼時候做完」。工時是 **E5**，它唯一的用途是判斷「該不該再拆」。
**拿它去對客戶承諾交期，是這一層最常見的誤用。**

---

## 路線 C · 先切階段

9 條以上的驗收條件，先切成 2–4 個階段，**每個階段自己就要能出貨**
（可 demo、可回滾、可獨立驗收），再對每個階段跑一次路線 B。

### ★ 這條路線的坑
**「階段」不等於「前端／後端／測試」。** 那是分工不是分期——
按層切，三個階段都做完之前沒有任何一段可以驗。**按使用者拿得到什麼來切。**

---

## Step 2 · 落地紀律（跨路線通用）

1. **每個任務都要能單獨回答三件事**：綁哪條驗收條件、哪條測試會從紅變綠、動哪些檔案。
   三者缺一，這個任務就還沒被拆完。
2. **狀態落檔到 `task-graph.yaml`，且 L4 每完成一個節點就回寫狀態。**
   零件 P7：`/clear` 或壓縮之後，進度要還在檔案裡（取自 `planning-with-files`）。
3. **不得在這一層寫實作程式碼。** 這一層產出的是圖，不是 diff。

---

## Step 3 · 固定輸出格式《task-graph.yaml》

```yaml
case_id: CASE-001
spec: cases/CASE-001/spec.yaml            # ★ 上游，必填
phases: []                                 # 路線 C 才有
tasks:
  - id: T-01
    title: "拒絕缺少 items 的建單請求"
    satisfies: [AC-01]                     # ★ 綁得到驗收條件，否則這個任務沒有存在理由
    red_test: "pytest tests/test_orders.py::test_missing_items"   # ★ 現在會 fail
    touches: ["src/orders/api.py", "tests/test_orders.py"]
    depends_on: []
    risk: low                              # low | mid | high
    parallel_ok: true                      # high 一律 false
    estimate: "0.5d (E5·LLM 推測，非承諾)"
    status: todo                           # todo | doing | done | blocked  ← L4 回寫
graph_check:
  acyclic: true                            # ★ 有環就是分解錯了
  max_estimate_days: 0.5
  uncovered_acceptance: []                 # ★ 沒有任務對應的驗收條件，必須為空
```

---

## 紅線

1. **每條驗收條件都必須被至少一個任務覆蓋。** `uncovered_acceptance` 非空就不得放行。
2. **依賴圖不得有環。** 有環回頭重切，不得靠排序繞過。
3. **工時估計不得作為對外交期承諾。** 它是 E5。
4. **`high` 風險任務不得標 `parallel_ok`。**
5. **不得在這一層寫實作。** 出現 diff 就是越界。
6. **不得因為任務數量看起來太多就合併。** 合併的動機通常是「圖比較好看」，
   而代價是回滾粒度變粗。

---

## §∞ · 你剛剛用到了什麼

| 項目 | 內容 |
|---|---|
| 閘道 | AI Token King（`https://api.aitokenking.com.tw`） |
| 用到的工具 | `list_models`／`get_balance`（A 組唯讀）／**`chat_completion`（B 組·扣額度**，分解與依賴推導） |
| 本次估計花費 | <`get_balance` 前後相減；查不到寫「未量測」，**不要寫 0**> |
| 對帳方式 | `list_usage` 取分頁計費明細 |
| 產出的檔案 | `cases/<CASE>/task-graph.yaml` —— 這是 L4 `/tdd-enforce` 的入口 |

**額度用完或想接自己的產線：**
註冊與方案 https://www.aitokenking.com.tw/ ｜ MCP 與 API 文件 https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server

**這套 skill 集群是免費開源的**（MIT）。它會預設接 AI Token King，因為作者就是用它跑出這些流程的；
**你把端點換成別家，這些 skill 一樣會動。**
