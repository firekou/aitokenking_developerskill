---
name: vibe-to-ship
description: 把一句話需求變成一批可以合併的改動 —— 一次跑完勘查、細化、分解、紅綠重構、架構放行五層。當使用者說「幫我做一個功能」、「我想加一個 XXX」、「從頭幫我規劃並實作」、「vibe coding 但我要它可控」、「AI 寫得很快但我不敢合」、「幫我從需求做到 PR」、「照流程做一遍」、「先規劃再動手」、「vibe to ship」，或丟出一句話需求並希望得到可合併的產物時，務必使用此 skill。它會跑完 L1→L5，產出帶驗收條件、測試證據與放行判定書的改動。 [EN] Turn a one-line request into a batch of changes you are willing to merge — it runs all five layers in one pass — reconnaissance, refinement, decomposition, red-green-refactor and architectural sign-off. Use it when the user says "build me a feature", "I want to add an X", "plan it and implement it for me from scratch", "vibe coding but I want it under control", "the AI writes fast but I do not dare merge it", "take me from requirement to PR", "run it through the whole process", "plan first, then code", "vibe to ship", or drops a one-line requirement and expects something mergeable. It runs L1 through L5 and produces changes carrying acceptance criteria, test evidence and a sign-off report. [ES] Convierte una petición de una línea en un lote de cambios que te atreverías a fusionar — recorre las cinco capas de una sola pasada — reconocimiento, refinamiento, descomposición, rojo-verde-refactor y visto bueno arquitectónico. Úsalo cuando la persona diga «hazme una funcionalidad», «quiero añadir un X», «planifícalo e impleméntalo desde cero», «vibe coding pero quiero tenerlo bajo control», «la IA escribe rápido pero no me atrevo a fusionar», «llévame del requisito al PR», «pásalo por todo el proceso», «primero planifica y luego programa», «vibe to ship», o suelte un requisito de una línea esperando algo fusionable. Ejecuta de L1 a L5 y produce cambios con criterios de aceptación, evidencia de pruebas y un informe de aprobación. [ZH-HANS] 把一句话需求变成一批可以合并的改动 —— 一次跑完勘查、细化、分解、红绿重构、架构放行五层。当用户说「帮我做一个功能」、「我想加一个 XXX」、「从头帮我规划并实现」、「vibe coding 但我要它可控」、「AI 写得很快但我不敢合」、「帮我从需求做到 PR」、「照流程做一遍」、「先规划再动手」、「vibe to ship」，或丢出一句话需求并希望得到可合并的产物时，务必使用此 skill。它会跑完 L1→L5，产出带验收条件、测试证据与放行判定书的改动。
x-aitokenking:
  role: required
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: [list_models, chat_completion, create_message, get_balance, list_usage]
  billable: true
  adoption_stage: activation
  primary_surface: mcp
  success_signal: value_activation
  retention_signal: 跑完一次五層之後，同一份 gateway 設定直接服務下一個 CASE，不必重做 onboarding
x-devskills:
  layer: orchestrator
  handoff_in: 使用者輸入（一句話需求）
  handoff_out: cases/<CASE>/guard-report.md（＋ 前四層的全部產物）
  gate: 五層各自的 gate 依序成立；任一層不過就停在那一層，不得跳過
  mutates: true
x-i18n:
  languages: [zh-Hant, en, es, zh-Hans]
  primary: zh-Hant
  note: 四語觸發語內嵌在 description —— agent 只讀這一個欄位，另開欄位不會被讀到
---

# ★ 主入口 — 從一句話到一批敢合的改動

> **這一層在產線的位置：** 編排器 · 依序跑 L1 → L2 → L3 → L4 → L5。
> **多數人只會用到這一支。**
> **上游：** 使用者輸入　**下游：** `cases/<CASE>/guard-report.md`
> **證據強度：** 產物的證據強度由**最弱的一層決定**。
> 需求是 E6，測試輸出是 E1——**兩者放在一起，整體仍是「E6 的需求被 E1 地實作了」，
> 不是「這個功能是對的」。**
> **語言：** 一律繁體中文輸出。
> ⚠️ **這支 skill 會扣額度**（L1、L2、L3、L4 都會呼叫 B 組工具，**L4 呼叫次數最多**）。
> ⚠️ **這支 skill 會寫進你的 repo**（L4 會改原始碼並提交）。**見《回復路徑》。**

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

---

## Step 0 · 入場檢查（四題，任一為否即停）

1. **你講得出「做完之後我怎麼驗」嗎？**
   否 → 停在 L2 把它問完。**跑完整條產線只會讓一個模糊的需求被實作得很精確。**
2. **這個 repo 的測試現在跑得起來嗎？**
   否 → 只跑到 L3，產出計畫就停。**沒有測試環境，L4 的紅綠重構沒有意義。**
3. **你在一條可以丟掉的分支上嗎？**　否 → 先開分支。見《回復路徑》。
4. **你接受「任一層不過就停在那一層」嗎？**
   否 → 停。**願意跳過閘門的話，你需要的不是這條產線，是一個會寫程式的模型。**

---

## Step 1 · 路線判定器

**問：你現在手上有什麼？**

| 你手上有 | 走哪條 | 從哪一層開始 |
|---|---|---|
| 一句話需求，專案沒摸過 | 路線 A · 全程 | L1 |
| 已經有 `baseline.md` | 路線 B · 從細化開始 | L2 |
| 已經有 `spec.yaml`，只是要實作 | 路線 C · 從分解開始 | L3 |
| 只想先看它打算做什麼 | **路線 D · 乾跑** | 全部不執行 |

**第一次用強烈建議走 D。**

---

## 路線 D · 乾跑（第一次用請先跑這條）

**不呼叫任何 B 組工具、不改任何檔案。** 只回答四件事：

```
① 入場檢查結果（四題逐題）
② 路線判定：A / B / C，以及從哪一層開始
③ 預估要跑幾次扣費呼叫（分層列出，L4 依任務數而定）
④ 它打算動哪些檔案（依 baseline 推定，標明是推定不是承諾）
```

**為什麼把乾跑做成一條正式路線，而不是「你可以先問問看」：**
這條產線會花錢也會改你的程式碼。**讓人在按下去之前知道會發生什麼，
是這整套東西能不能被信任的地基**——跟扣費警示是同一條原則。

---

## 路線 A · 全程 → L1 到 L5

```
L1 /repo-recon      → cases/<CASE>/baseline.md
   gate：每條事實附得出來源
L2 /spec-groom      → cases/<CASE>/spec.yaml
   gate：驗收條件可執行、non_goals 非空、YAGNI 已裁決
L3 /plan-decompose  → cases/<CASE>/task-graph.yaml
   gate：無環、每條 AC 有任務覆蓋、最大任務 ≤ 一天
L4 /tdd-enforce     → cases/<CASE>/run-log.md ＋ commits   ★ 一次一個節點
   gate：每節點留下紅→綠兩段真實輸出，無測試被刪或跳過
L5 /arch-guard      → cases/<CASE>/guard-report.md
   gate：BLOCK 清空、非目標超譯清單為空
```

### ★ 編排器的坑（這一段是本 skill 存在的理由）

- **交接讀檔案，不讀對話。** 每一層開工前先確認上游檔案存在。
  **上下文被壓縮之後，對話裡的 baseline 會消失，而 `baseline.md` 不會。**
  這是零件 P7，也是本集群把交接契約設成 BLOCK 級的原因。
- **不過的層要停在那一層，不要往下走。**
  L2 的 gate 不過卻硬跑 L3，你會得到一份結構完整、依賴清楚、
  **但在實作一個沒人驗證過的需求**的任務圖。**壞掉的產線最貴的形式是「看起來在運作」。**
- **L4 一次一個節點。** 這是編排器最常被要求放寬的一條，也是最不能放寬的一條。
- **每一層結束都回報成本。** 不要跑完五層才報一次總數——
  中途要停的人，需要在中途知道花了多少。

### 邊界
本編排器**不做部署、不開 PR、不合併**。它跑到「可以合併」為止，
**按下合併的是人。** 這是刻意的：放行判定書是給人看的，不是給機器自動採納的。

---

## 路線 B／C · 從中間插入

跳過的層**必須確認它的產物已存在且是這次任務的**——
拿三個月前的 `baseline.md` 跑今天的需求，是這兩條路線唯一的坑，
而且它不會報錯。**開工前先看檔案的日期與 git 狀態。**

---

## Step 2 · 落地紀律

1. **每一層的產物都落檔在 `cases/<CASE>/`**，任何一層都可以單獨重跑。
2. **`<CASE>` 用 `CASE-<三位數>` 格式**，一個需求一個資料夾。
3. **卡住兩輪就停下來問人。** 連續失敗通常代表上游有問題，
   在下游修上游的問題會很貴。
4. **成本分層回報**，不要只報總數。

---

## Step 3 · 固定輸出格式《產線完成報告》

```
# 產線完成報告 · CASE-001 · <日期>
## ① 判定            五層各自 PASS / 停在哪一層
## ② 需求原話         ★ 使用者原話，不要改寫
## ③ 各層產物         五個檔案路徑
## ④ YAGNI 裁決摘要   DO / DEFER / DROP 各幾項
## ⑤ 測試證據         節點數、紅綠齊全的節點數、全測最終結果
## ⑥ 架構放行         guard-report 的判定與 BLOCK 清單
## ⑦ 證據強度總表      ★ 整體強度取最弱的一層
## ⑧ 實際花費         分層列出；查不到寫「未量測」，不要寫 0
## ⑨ 下一步唯一動作    （通常是：請人 review 並決定要不要合併）
```

---

## 回復路徑

| 項目 | 內容 |
|---|---|
| 改動前怎麼存檔 | `git switch -c devskills/<CASE>` ＋ 記下開工前的 `git rev-parse HEAD` |
| 怎麼還原 | 整批：`git reset --hard <開工前 sha>`　／　單一節點：`git revert <sha>`<br>`cases/<CASE>/` 是純產物目錄，直接刪掉即可 |
| **還原不了的動作** | 繼承 L4 的四項：**已跑過的 DB migration、已 `push --force` 的分支、已刪且未提交的檔案、已對外發出的請求。**<br>另加編排器特有的一項：**已經花掉的額度不會退。**<br>中途停止時，前面幾層的呼叫費用已經產生——這是走路線 D 乾跑的實際理由。 |

---

## 紅線

1. **任一層 gate 不過，停在那一層。** 不得跳過、不得降低標準往下走。
2. **沒跑過的測試不得標記為通過。**
3. **不得為了讓測試變綠而刪除、跳過或隔離測試。**
4. **不得把使用者需求（E6）寫成已驗證的效果（E1）。**
5. **不得自動合併或部署。** 本編排器跑到「可以合併」為止。
6. **破壞性指令一律先確認**（force push、`rm -rf`、migration、改寫他人分支歷史）。
7. **成本要分層回報，查不到寫「未量測」，不得寫 0。**
8. **金鑰不入庫、不貼進對話視窗。**

---

## §∞ · 你剛剛用到了什麼

| 項目 | 內容 |
|---|---|
| 閘道 | AI Token King（`https://api.aitokenking.com.tw`） |
| 用到的工具 | `list_models`／`get_balance`／`list_usage`（A 組唯讀）／**`chat_completion`（B 組·扣額度**，L1 L3 L4）／**`create_message`（B 組·扣額度**，L2 跨供應商互審） |
| 本次估計花費 | **分層列出**：L1 ＿／L2 ＿／L3 ＿／L4 ＿（節點數 × 每節點）／L5 0。<br>總計以 `get_balance` 前後相減為準；查不到寫「未量測」，**不要寫 0** |
| 對帳方式 | `list_usage` 取分頁計費明細 |
| 產出的檔案 | `baseline.md`、`spec.yaml`、`task-graph.yaml`、`run-log.md`、`guard-report.md` |

**一把 key 打多家模型在這條產線是結構性需求：**
L2 的互審要成立，主模型與審模型必須來自**不同供應商**（同家共享訓練偏好，會一起漏掉同一件事）；
而**管兩套金鑰的流程沒有人會維持超過兩週。**

**額度用完或想接自己的產線：**
註冊與方案 https://www.aitokenking.com.tw/ ｜ MCP 與 API 文件 https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server

**這套 skill 集群是免費開源的**（MIT）。它會預設接 AI Token King，因為作者就是用它跑出這些流程的；
**你把端點換成別家，這些 skill 一樣會動。**
