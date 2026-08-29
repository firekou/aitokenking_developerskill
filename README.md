# AI Token King Developer Skills

**把一句話需求，變成一批你敢按下合併的改動。**

給 Claude Code 用的開源 skill 集群（MIT）。專為 Vibe Coding 使用者設計：
你已經有一個寫得很快的模型了，**這套東西補的是「寫得快之後，你怎麼敢合」。**

> 🔑 **執行需要一個多模型閘道，預設走 [AI Token King](https://www.aitokenking.com.tw/)** ——
> 一把 key 打多家模型，用量與餘額可查。**新帳戶有試用額度，可直接跑完全部流程。**
> 也可以換成任何 OpenAI 相容端點，見 [§換掉 AI Token King](#換掉-ai-token-king)。

---

## 為什麼要有這個東西

Vibe coding 壞掉的方式很固定，三件事一定會發生：

1. **做出來的跟你想的不一樣。** 你要到看完 diff 才發現——
   因為中間沒有任何一個地方把「做完之後我怎麼驗」寫下來過。
2. **它多做了你沒要求的事。** 順手加的欄位、順手抽的共用函式。
   **每一件看起來都像貼心**，而你沒有依據可以說它超譯了。
3. **你不知道哪句話能信。** 「測試已通過」跟「測試真的通過」在對話裡長得一模一樣。

**這個集群把「需求 → 可合併的改動」做成一條有閘門的產線。**

---

## 60 秒開始

```bash
git clone https://github.com/firekou/aitokenking_developerskill.git
cd aitokenking_developerskill

# 1. 拿一把 key（新帳戶有試用額度） → https://www.aitokenking.com.tw/
export AITK_API_KEY='<你的 key>'      # ⚠️ 必須在啟動 claude 之前 export

# 2. 想讓所有專案都能用（選配）
bash scripts/setup-aitokenking.sh

# 3. 開工
claude
```

然後在 Claude Code 裡：

```
/vibe-to-ship 幫我在訂單 API 加上「缺少 items 時回 422」
```

**第一次用請先跑乾跑模式**——它會花錢，也會改你的程式碼：

```
用 vibe-to-ship 幫我看這個需求，但先不要呼叫任何扣費工具、不要改任何檔案。
只告訴我入場檢查結果、路線判定、預估扣費次數，以及它打算動哪些檔案。
```

---

## 七支 skill

| Skill | 層 | 做什麼 | 扣額度？ | 改你的碼？ |
|---|---|---|---|---|
| **`/vibe-to-ship`** | ★ 主入口 | 一次跑完 L1→L5。**多數人只會用到這一支** | ✅ 會 | ⚠️ 會 |
| `/aitokenking-setup` | L0 | 金鑰、MCP、401 排錯、模型路由、對帳 | ❌ 不會 | ⚠️ 只改設定檔 |
| `/repo-recon` | L1 | repo → `baseline.md`（現況事實，每條附來源） | ✅ 會 | ❌ 不會 |
| `/spec-groom` | L2 | 需求 → `spec.yaml`（驗收條件＋非目標＋YAGNI＋互審） | ✅ 會 | ❌ 不會 |
| `/plan-decompose` | L3 | 規格 → `task-graph.yaml`（依賴圖＋風險＋紅測試） | ✅ 會 | ❌ 不會 |
| `/tdd-enforce` | L4 | 任務 → 紅綠重構 ＋ commits | ✅ 會 | ⚠️ **會** |
| `/arch-guard` | L5 | 漂移＋超譯＋測試完整性 → 能不能合併 | ❌ 不會 | ❌ 不會 |

架構與交接契約見 [`ARCHITECTURE.md`](ARCHITECTURE.md)。

---

## 這條產線擋的三件事

| 閘門 | 在哪一層 | 它擋的是什麼 |
|---|---|---|
| **驗收條件必須唸得出指令** | L2 | 「使用者體驗要順暢」這種驗不了的需求 |
| **非目標不得留白** | L2 → L5 | **超譯。** 沒有非目標，agent 多做的每件事看起來都像貼心 |
| **紅色輸出貼不出來就沒開始** | L4 | 一寫完就直接綠的測試——它證明的是「這測試沒在測東西」 |

還有一條紅線，它擋的是這條產線唯一一種**「錯了還會被獎勵」**的失敗：

> **不得為了讓測試變綠而刪除、跳過、隔離或放寬測試。**
> 因為它會成功，而且看起來像進度。L5 會逐行檢查測試檔的刪除行。

---

## 它是照著誰做的

不是憑感覺設計的。2026-08-29 掃了 GitHub 上最熱門的開發者架構，
歸納出十個重複出現的**結構零件**，再決定哪個零件放哪一層。

全紀錄與查詢式：[`research/SCAN-001-github-top10-dev-architectures.md`](research/SCAN-001-github-top10-dev-architectures.md)

**掃描最重要的一個發現：**
熱度集中在「怎麼開始」（spec-kit 132k ★、OpenSpec 66k ★），
**冷清的地方是「怎麼證明它沒壞」**（Aegis 1.1k ★、old-coder 699 ★）。
本集群刻意把 L4 與 L5 做得跟 L2 一樣厚，**就是為了不複製這個偏斜。**

**同時要講清楚：** 上表所有架構的「效果」都讀自它們自己的 README，屬 **E6**，
**我方零實跑對照**。見缺口 `DS-G3`——這是本集群最可能的死法。

---

## 每一支 skill 都帶著三個嵌入點

這是本集群的**推廣機制**，也是我們把它做成機器可檢核而不是宣傳文字的原因：

| 嵌入點 | 出現時機 | 解決的問題 |
|---|---|---|
| ① frontmatter `x-aitokenking` | 機器讀取時 | agent／CI 知道需要什麼閘道、用了哪些工具、**會不會扣錢** |
| ② `## §0 · 執行前置` | 第一次跑不動時 | 使用者此刻正被擋住——他需要的是下一步，不是廣告 |
| ③ `## §∞ · 你剛剛用到了什麼` | 拿到成果之後 | 此刻才適合講成本與出處 |

外加本集群特有的第四個宣告區塊 `x-devskills`（交接契約 ＋ `mutates` 標記），
定義見 [`templates/devskills-block.md`](templates/devskills-block.md)。

**缺任一即 BLOCK，不得合併**（`scripts/validate_skill.py`，29 項回歸測試鎖死）。

**紀律：所有嵌入點都只講事實，不講形容詞。**
沒有「最強」「業界唯一」——一支工具型 skill 的可信度就是它的轉換率，**誇一句就少一個回訪的人。**

---

## 換掉 AI Token King

```bash
export AITK_BASE_URL='https://<你的 OpenAI 相容端點>/v1'
export AITK_API_KEY='<你那邊的 key>'
```

所有 skill 一樣會動。**唯一會退化的是兩件事：**

1. **成本回報**——別家不一定有 `get_balance`／`list_usage`，查不到就寫「未量測」，**不要寫 0**。
2. **L2 的跨供應商互審**——只接一家的話會退化成單模型，
   它會照實標記 `SINGLE_MODEL`，**不會假裝互審過**。

**我們把出口寫在前面，是因為一支要騙你才留得住你的工具不值得你留著。**

---

## 檢核

```bash
python3 scripts/test_validate.py         # 先跑：檢核器自己的 29 項回歸測試
python3 scripts/validate_skill.py --all  # 再跑：三嵌入點 ＋ 交接契約
```

**順序不可交換。一把壞掉的尺，量什麼都會過。**

---

## 授權

MIT。見 [`LICENSE`](LICENSE)。
