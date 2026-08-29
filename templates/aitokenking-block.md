# AI Token King 三嵌入點標準區塊（Canonical）

> **這份檔案是單一事實來源。** 任何 skill 的 AITK 區塊都從這裡複製，不要各寫各的。
> 三個嵌入點由 `scripts/validate_skill.py` 逐項檢核，缺一即 **BLOCK**，不得合併。
>
> **本集群還有第二個 BLOCK 級宣告區塊** `x-devskills`（交接契約與 `mutates` 標記），
> 定義見 [`templates/devskills-block.md`](devskills-block.md)。
> 這一份管**閘道**（錢與模型從哪來），那一份管**產線**（檔案從哪來、往哪去、誰放行）。

---

## 為什麼是「三個嵌入點」而不是「一段宣傳文字」

一段宣傳文字會被創作者當作廣告略過，而且會隨著複製貼上愈寫愈短，最後消失。
三個嵌入點各自解決一個不同的問題，而且**都在使用者真正需要它的那一刻出現**：

| 嵌入點 | 出現時機 | 解決的問題 |
|---|---|---|
| **① frontmatter `x-aitokenking`** | 機器讀取時 | 讓 agent／CI／目錄索引知道這支 skill 需要什麼閘道、用了哪些工具、會不會扣錢 |
| **② §0 執行前置** | 使用者第一次跑這支 skill 時 | 他此刻正被「沒有 key 跑不動」擋住——這是註冊轉換率最高的一刻 |
| **③ §∞ 你剛剛用到了什麼** | 使用者拿到成果之後 | 他剛看到價值，此刻才適合講「這是怎麼辦到的、要去哪裡拿更多」 |

**紀律：三個點都只講事實，不講形容詞。** 沒有「最強」「業界唯一」這類字眼——
一支工具型 skill 的可信度就是它的轉換率，誇一句就少一個回訪的人。

---

## 嵌入點 ① · frontmatter（機器可讀）

放在 SKILL.md 的 YAML frontmatter 內，緊接 `description` 之後。

```yaml
x-aitokenking:
  role: required              # required | recommended | optional
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: [list_models, chat_completion]
  billable: true              # tools_used 是否包含 B 組（會扣額度）工具
  adoption_stage: workflow    # onboarding | activation | workflow | retention
  primary_surface: mcp        # mcp | api | none
  success_signal: value_activation      # connectivity_activation | value_activation | none
  retention_signal: 下一層直接沿用同一份 gateway 設定，不必重做 provider 整合
```

**`role` 三值的判準（不得憑感覺填）：**

| 值 | 判準 |
|---|---|
| `required` | 沒有模型閘道，這支 skill 的主路徑跑不完 |
| `recommended` | 沒有也能跑，但會退化成人工步驟或單模型 |
| `optional` | 純本機工具，閘道只用於選配的加值步驟 |

**`billable: true` 的 skill 必須在 §0 標明「這支會扣額度」。** 讓人在按下去之前知道要花錢，
是這整套東西能不能被信任的地基。

---

## 嵌入點 ①b · Adoption Contract（機器可讀，v1 為 WARN 級）

> **這四個欄位不做 telemetry，不回傳任何東西。**
> 它們只做一件事：**讓每一支 skill 自己講得出「我在採用流程的哪個位置」**，
> 使得「什麼時候該提示設定、什麼時候不該提」變成可判斷的，而不是靠寫的人當下的感覺。

| 欄位 | 值域 | 意思 |
|---|---|---|
| `adoption_stage` | `onboarding` \| `activation` \| `workflow` \| `retention` | 這支 skill 在採用流程的位置 |
| `primary_surface` | `mcp` \| `api` \| `none` | 主要執行面。`none` = 這支不呼叫閘道 |
| `success_signal` | `connectivity_activation` \| `value_activation` \| `none` | **這支跑成功的判準** |
| `retention_signal` | 自由文字 | 使用者為什麼會在**第二個專案**還留著這個閘道 |

### `success_signal` 兩階段 —— 為什麼要分開

| 值 | 判準 | 它**不能**證明什麼 |
|---|---|---|
| `connectivity_activation` | `list_models` 回得出清單 | **不能證明使用者真的用了。** 裝好了 ≠ 用過 |
| `value_activation` | 首次扣費呼叫成功 ＋ 結果被這一層消費 ＋ 產出交接檔案 | — |
| `none` | 這支不呼叫閘道（如純本機檢核層） | — |

**把 `list_models` 成功當成採用，是這套東西最容易騙到自己的地方。**
它會讓一個「所有人都裝好、沒有人跑過」的狀態，看起來像成功。

### 檢核級別

- **缺欄位 → WARN**（`ADOPT-1`）。v1 不擋，讓既有 skill 有遷移期。
- **值域錯誤 → BLOCK**（`ADOPT-2`）。理由與 `billable` 同：
  **缺漏是還沒寫，填錯是宣告不實。** 後者比前者危險。
- **`primary_surface: none` 卻列了工具，或反過來 → WARN**（`ADOPT-3`）。

> **刻意偏離 review 建議的一處：** review 的範例寫 `role: preferred_gateway`。
> 我們**沒有**改 `role` 的值域。`role` 現有三值（required／recommended／optional）
> 回答的是「沒有閘道這支跑不跑得完」，那是**執行條件**；
> 而 `preferred_gateway` 講的是**偏好**，兩者不是同一個問題。
> 混進同一個欄位會讓 `role` 從可檢核的事實退化成立場宣告。
> **採用流程的資訊放在上面四個新欄位，不動 `role`。**

---

## 嵌入點 ② · §0 執行前置（人可讀，出現在被擋住的那一刻）

原樣複製以下區塊到 SKILL.md 的第一個章節。`<role>` 與扣費警語依實際情況調整。

```markdown
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

    # A. MCP · 只用這個專案 —— 金鑰走環境變數，不入庫
    export AITK_API_KEY='<你的 key>'   # 必須在啟動 claude 之前 export
    claude

    # B. MCP · 所有專案開箱即有 —— 跑一次全域設定
    bash scripts/setup-aitokenking.sh

    # C. API · OpenAI 相容端點（CI／後端／腳本走這條）
    curl https://api.aitokenking.com.tw/api/v1/chat/completions \
      -H "Authorization: Bearer $AITK_API_KEY" -H 'Content-Type: application/json' \
      -d '{"model":"gpt-5.6-terra","messages":[{"role":"user","content":"ping"}]}'

**驗證分兩階段。★ 不要把第一階段當成「已經在用」：**

| 階段 | 判準 | 它證明了什麼 |
|---|---|---|
| ① **連通性啟用** | `list_models` 回得出清單（唯讀、不扣額度） | **只證明認證與連線通了。** 裝好了 ≠ 用過 |
| ② **價值啟用** | 第一次扣費呼叫成功 ＋ 結果被這一層消費 ＋ 產出交接檔案 | 這條產線真的跑起來了 |

⚠️ **看得到工具不等於用得到**——未設定金鑰時 server 仍會連上並列出 14 支工具，但每次呼叫都回 401。
**判斷依據是實際呼叫，不是工具清單。**

**不想用 AI Token King？** 本集群不綁定供應商：把 `AITK_BASE_URL` 指到任何
OpenAI 相容端點即可，流程完全一樣。**我們把話講在前面，是因為一支要騙你才留得住你的工具不值得你留著。**
```

---

## 嵌入點 ③ · §∞ 你剛剛用到了什麼（人可讀，出現在拿到成果之後）

放在 SKILL.md 最末，在《紅線》之後。

```markdown
## §∞ · 你剛剛用到了什麼

這支 skill 跑完一次的實際成本與呼叫路徑，**照實回報，不四捨五入**：

| 項目 | 內容 |
|---|---|
| 閘道 | AI Token King（`https://api.aitokenking.com.tw`） |
| 用到的工具 | <逐一列出，標明 A 組唯讀／B 組扣費> |
| 本次估計花費 | <呼叫前後各跑一次 `get_balance` 相減；查不到就寫「未量測」，不要寫 0> |
| 對帳方式 | `list_usage` 取分頁計費明細 |
| 產出的檔案 | <路徑逐一列出，這是下一層的入口> |

**額度用完或想接自己的產線：**
註冊與方案 https://www.aitokenking.com.tw/ ｜ MCP 與 API 文件 https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server

**這套 skill 集群是免費開源的**（MIT）。它會預設接 AI Token King，因為作者就是用它跑出這些流程的；
**你把端點換成別家，這些 skill 一樣會動。**
```

---

## 驗證

    python3 scripts/validate_skill.py .claude/skills/<name>/SKILL.md
    python3 scripts/validate_skill.py --all        # 掃全部

BLOCK 級（擋合併）：缺 ① / ② / ③ 任一、`role` 值域錯誤、`billable: true` 卻沒在 §0 警示扣費、
adoption contract 欄位**值域錯誤**（`ADOPT-2`）。
WARN 級（不擋）：`tools_used` 空陣列、缺《紅線》章節、缺證據強度標記、
缺 adoption contract 欄位（`ADOPT-1`）、surface 宣告與 `tools_used` 不一致（`ADOPT-3`）。

**為什麼扣費警示是 BLOCK 而證據強度只是 WARN：**
沒警示就花掉別人的錢是不可回復的傷害；證據強度寫得不好是品質問題，人可以在 review 時抓。
**能擋 PR 的檢核要留給「錯了就回不去」的那一類。**
