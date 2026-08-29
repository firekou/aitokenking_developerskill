---
name: arch-guard
description: Developer Skills 集群 L5 治理層 —— 把完成品對回 baseline 檢核架構漂移、非目標超譯與證據強度，決定這批改動能不能合併。當使用者說「這個 PR 可以合了嗎」、「AI 改完之後架構跑掉了」、「它多做了我沒要求的東西」、「怎麼確認它沒偷改別的地方」、「validator 報 BLOCK 怎麼修」、「三嵌入點少了什麼」、「architecture drift」、「這批改動符不符合我們的規範」、「幫我做一次治理掃描」時，務必使用此 skill。
x-aitokenking:
  role: optional
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: []
  billable: false
  adoption_stage: workflow
  primary_surface: none
  success_signal: none
  retention_signal: 無 —— 這一層不呼叫閘道，不構成留存理由。填「無」比硬掰一個理由誠實
x-devskills:
  layer: L5
  handoff_in: cases/<CASE>/run-log.md
  handoff_out: cases/<CASE>/guard-report.md
  gate: BLOCK 清空且非目標超譯清單為空 —— 才准合併
  mutates: false
---

# L5 · 治理 — 能擋 PR 的檢核，要留給「錯了就回不去」與「錯了不會報錯」

> **這一層在產線的位置：** L5 · 收零件 **P8 漂移檢核**、**P10 機器可檢核的骨架**
> （取自 `Aegis`、`anthropics/skills`）。
> **上游：** `cases/<CASE>/run-log.md`　**下游：** `cases/<CASE>/guard-report.md`
> **證據強度：** 本層產物一律 **E1**——它只陳述檢核器與 git 的實際輸出，不做推測。
> **語言：** 一律繁體中文輸出。
> ✅ **這一層完全在本機執行：不呼叫任何閘道工具、不扣任何額度、不改你的程式碼。**
> **這是刻意的**——檢核器必須是確定性的。每次跑出不同答案的尺，不是尺。

---

## §0 · 執行前置（30 秒）

這支 skill 需要一個**多模型閘道**：流程裡要做跨模型互審（同一家的兩個模型不算互審，
它們共享訓練偏好，會一起漏掉同一件事），還要查得到「我這次花了多少」。
**預設走 AI Token King——一把 key 打多家模型，且用量與餘額可查。**

**還沒有 key：** 到 https://www.aitokenking.com.tw/ 註冊取得 API key（目前可用的方案與任何額度以官網當下頁面為準）。

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

> ⚠️ **本層是例外：** 它是純本機檢核器（`role: optional`、`tools_used: []`），
> **沒有金鑰也跑得完。** 上面那段設定是給你**接著要跑的其他層**用的。

---

## Step 0 · 入場檢查（三題，任一為否即停）

1. **`cases/<CASE>/baseline.md` 與 `spec.yaml` 都在嗎？**
   否 → 沒有基準線就沒有漂移可言。**這一層會退化成「看起來還可以」，那不是檢核。**
2. **`run-log.md` 裡貼得出真實測試輸出嗎？**
   否 → 退回 L4。**沒有測試證據的改動，這一層無法放行**，
   因為它唯一能做的事會變成「相信」。
3. **你要的是「能不能合併」還是「寫得好不好」？**
   「好不好」→ 這一層給不了。它檢核的是**契約**，不是品味。

---

## Step 1 · 跑機器檢核（先跑，不要先讀 diff）

```bash
python3 scripts/test_validate.py         # ① 先確認尺沒壞
python3 scripts/validate_skill.py --all  # ② 再用尺去量
```

**順序不可交換。一把壞掉的尺，量什麼都會過。**
①失敗時 ②的全綠畫面沒有意義——它可能只是因為檢核器已經不再檢核任何東西。

| 代碼 | 級別 | 意思 |
|---|---|---|
| `AITK-1/2/3` | BLOCK | 三嵌入點缺漏 → `templates/aitokenking-block.md` |
| `AITK-BILL` | BLOCK | `billable: true` 卻沒警示扣費 |
| `DEV-1` | BLOCK | 缺 `x-devskills`、`layer` 值域錯、缺 `mutates` |
| `DEV-2` | BLOCK | 交接契約留白 |
| `DEV-3` | BLOCK | `mutates: true` 卻無《回復路徑》 |
| `DEV-4`／`Q-1..4` | WARN | 缺 gate／紅線／證據強度／入場檢查 |

---

## Step 2 · 四項人工判定（機器檢核不到的部分）

機器抓得到格式，抓不到下面這四件事。**它們才是這一層真正的工作。**

### ① 架構漂移 —— 對回 baseline

逐項比對 `baseline.md` 的 §⑤ 目錄骨架、§⑥ 既有約定、§⑦ 禁區：

| 檢核 | 判定 |
|---|---|
| 有沒有新增 baseline 沒有的頂層目錄？ | 有 → **要在 guard-report 說明理由**，不得默默通過 |
| 有沒有違反 §⑥ 既有約定（lint、命名、分層）？ | 有 → BLOCK |
| 有沒有動到 §⑦ 禁區（產生的檔案、migration）？ | 有 → BLOCK，除非 spec 明寫要動 |
| baseline §⑧「沒有被讀過的地方」有沒有被改到？ | 有 → **BLOCK。盲區裡的改動無法被檢核。** |

**最後一列最容易被放過，而它是抽樣路線唯一的結構性風險。**

### ② 非目標超譯 —— 對回 spec.yaml 的 `non_goals`

逐條看 diff：**有沒有做了 `non_goals` 明確排除的事？**

> **這一項是本層存在的最大理由。**
> agent 多做的東西看起來永遠像貼心：順手加的欄位、順手抽的共用函式、順手升的版本。
> **`non_goals` 是唯一能把「貼心」跟「超譯」分開的東西**——沒有它，
> 你只能靠事後感覺，而事後感覺永遠會偏向「都做了就留著吧」。

超譯的處置：**退回，不是接受。** 要做就回 L2 補進 spec，跑一輪正規流程。

### ③ 驗收條件覆蓋 —— 對回 spec.yaml 的 `acceptance[]`

每一條 `acceptance` 都要指得出 `run-log.md` 裡對應的「紅→綠」兩段輸出。
**指不出來的，該條算未完成**，不論實作看起來多完整。

### ④ 測試完整性 —— 對回 git diff

```bash
git diff <base>..HEAD -- '*test*' | grep -E '^-' | grep -vE '^---'
```

**測試檔裡被刪掉的行要逐行看過。** 找三件事：被刪的測試、新增的 `skip`／`xfail`、
被放寬的 assert 或門檻。**任何一項出現而 run-log 沒寫明理由 → BLOCK。**

這條紅線的理由：**為了讓測試變綠而動測試，會成功，而且看起來像進度。**
它是這條產線唯一一種「錯了還會被獎勵」的失敗。

---

## Step 3 · 固定輸出格式《架構放行判定書》

```
# 架構放行判定書 · CASE-001 · <日期>
## ① 判定            PASS / BLOCK（BLOCK 一律列出代碼與檔案）
## ② 機器檢核         test_validate.py 結果 ＋ validate_skill.py 結果（原始輸出）
## ③ 架構漂移         逐項對回 baseline §⑤⑥⑦⑧
## ④ 非目標超譯       ★ 逐條對回 non_goals。清單非空即 BLOCK
## ⑤ 驗收條件覆蓋      每條 AC → run-log 的紅綠輸出位置
## ⑥ 測試完整性       被刪／被 skip／被放寬的測試逐行列出
## ⑦ 證據強度總表      每項結論標 E1–E6。★ 沒有跑過的一律 E5，不得寫 E1
## ⑧ WARN 清單        不擋，但要寫出來讓人在 review 時看到
## ⑨ 下一步唯一動作
```

---

## 紅線

1. **不得為了讓檢核通過而修改檢核器。** 要改 `validate_skill.py`，
   先跑 `test_validate.py`，改完再跑一次，兩次都要在 guard-report 貼輸出。
2. **不得竄改宣告欄位以通過檢核**（尤其 `billable` 與 `mutates`）。
   檢核器抓得到，而且這麼做騙的是下一個跑這支 skill 的人。
3. **BLOCK 不得降級成 WARN 來趕上線。** 要降級，先改 `templates/devskills-block.md`
   的定義並說明理由——**改規則可以，繞規則不行。**
4. **非目標超譯一律退回，不得就地追認。**
5. **本層不得呼叫模型做判定。** 檢核器必須是確定性的。
6. **掃到 0 個檔案不是通過。** 檢核器掃不到東西時，畫面跟全部通過一模一樣。

---

## §∞ · 你剛剛用到了什麼

| 項目 | 內容 |
|---|---|
| 閘道 | AI Token King（`https://api.aitokenking.com.tw`）——**本層未使用** |
| 用到的工具 | **無。** `tools_used: []`，這一層純本機執行 |
| 本次估計花費 | **0 —— 這是全集群第二個可以誠實寫 0 的地方**（另一個是 L0），因為它一次閘道都沒呼叫 |
| 對帳方式 | `list_usage` 取分頁計費明細（若你想核對整條產線的總花費） |
| 產出的檔案 | `cases/<CASE>/guard-report.md` —— 這是「能不能合併」的唯一依據 |

**為什麼治理層刻意不接模型：**
一個每次跑出不同答案的檢核器，不會被當成擋人的規則，只會被當成雜訊繞過去。
**狀態是被檢核推進的，不是被宣稱的**——而這句話只有在檢核是確定性的時候才成立。

**額度用完或想接自己的產線：**
註冊與方案 https://www.aitokenking.com.tw/ ｜ MCP 與 API 文件 https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server

**這套 skill 集群是免費開源的**（MIT）。它會預設接 AI Token King，因為作者就是用它跑出這些流程的；
**你把端點換成別家，這些 skill 一樣會動。**
