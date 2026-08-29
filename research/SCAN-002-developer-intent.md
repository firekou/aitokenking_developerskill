# SCAN-002 · 開發者意圖掃描（Developer Intent Scan）

**掃描日：** 2026-08-29
**回應：** `reviews/2026-08-29-developer-skill-embedded-growth-review.md` §2、§10 DEV-GROWTH-001
**方法：** Web 搜尋六輪，取回結果中**實際存在的措辭**（標題、文內用語），逐條分群。

---

## §0 先講這份掃描不能做什麼（否則後面每一條都會被誤讀）

SCAN-001 的問題是 **selection bias**：它搜到的是「已經知道 SDD／agent skill 這些名詞的人」。
這一份補的是「還不知道術語、但正在痛的人會怎麼講話」。

**但它有一個結構性的限制，必須寫在最前面：**

> **我們沒有關鍵字流量工具，所以這份掃描量不到 frequency。**
> 下表的「訊號」欄位是**該措辭是否在多個獨立來源重複出現**，
> **不是搜尋量、不是排名、不是熱度。**

Review §2.2 要求的產物格式是
`pain → wording → frequency signal → existing solution → missing solution → candidate Skill`。
**`frequency signal` 這一欄我們填不出來，全部標記「未量測」。**
照鐵律五：查不到就寫「未量測」，不得寫 0，**也不得用「看起來很多人在問」代替。**

**證據強度：** 措辭本身 **E3（可複查的公開文本）**；
分群與「對應哪支 skill」的判斷 **E5（我方推論）**；
「這個痛點有多少人有」**未量測**。

---

## §1 A 群 · 工程痛點意圖（不知道術語的人怎麼講）

| # | 原始措辭 | 重複訊號 | 現有解法 | 缺的是什麼 | 對應 skill |
|---|---|---|---|---|---|
| A-01 | 「改一個功能，PR 卻動了 14 個檔案」 | 多來源重複 | change budget、拆 run | 沒有把「該動哪些檔案」事先寫死的地方 | `plan-decompose`（`touches`） |
| A-02 | keep coding agents from changing too much code | 多來源 | 分次跑、限縮 intent | — | `plan-decompose`、`arch-guard` |
| A-03 | how to keep an AI agent from breaking existing code | 多來源 | 測試、review | 沒有「改之前先鎖住現在的行為」 | `tdd-enforce` 路線 C 特徵測試 |
| A-04 | how to stop AI coding agents from overwriting your work | 單一來源 | git 紀律 | 回復路徑通常沒寫 | `tdd-enforce`《回復路徑》 |
| A-05 | AI 改完之後架構跑掉了 | 我方轉譯（E5） | — | **對回基準線的檢核** | `arch-guard`、`repo-recon` |
| A-06 | agent 只看得到 context window 裡的那一塊就下決定 | 多來源 | 索引、RAG | 沒有落檔的現況事實 | `repo-recon` |
| A-07 | 「它多做了我沒要求的東西」 | 我方轉譯（E5） | — | **非目標欄位** | `spec-groom` → `arch-guard` |
| A-08 | AI 寫的 code 有沒有問題 / 我不敢合 | 多來源 | code review | — | **候選：`ai-code-review`** |

**A 群的共同結構：使用者描述的是「症狀」，不是「方法」。**
他不會搜 `plan-decompose`，他會搜「它改太多」。
**這代表 `description` 欄位裡的觸發語應該以症狀為主、術語為輔**——現有七支 skill 已照此寫，
但 A-08 目前**沒有任何一支 skill 接得住**。

---

## §2 B 群 · 信任與驗證意圖（本集群最強的一群）

| # | 原始措辭 | 重複訊號 | 現有解法 | 缺的是什麼 | 對應 skill |
|---|---|---|---|---|---|
| B-01 | how to trust AI generated code | 多來源 | 人工 review | — | `arch-guard` |
| B-02 | review AI-generated code before merging | 多來源 | checkpoint workflow | — | **候選：`ai-code-review`** |
| B-03 | 「84% 用 AI，只有 33% 信任它的輸出」 | 多來源引用同一調查 | — | **這是本集群的市場敘事** | 全部 |
| B-04 | AI agent lies about success / confident green lie | 多來源 | 確定性檢查器 | — | `tdd-enforce` 紅線 1 |
| B-05 | AI-generated tests that pass but don't assert anything | 多來源 | mutation testing | **我方未接**（缺口 DS-G4） | `tdd-enforce`（邊界已明寫） |
| B-06 | ban deletions, no @skip, no commenting out assertions | 多來源 | prompt 禁令 | **我方已做成 L5 逐行檢查** | `arch-guard` Step 2 ④ |
| B-07 | your AI agent says "done" — make it prove it | 多來源 | 可證偽宣稱 | — | `tdd-enforce`（E5 vs E1） |
| B-08 | AI agent 跑了窄測試卻宣稱全套通過 | 多來源 | — | — | `tdd-enforce` 步驟 ③ |

> **B 群是這個集群命中率最高的一群，而現有 skill 幾乎全部接得住。**
> B-04／B-06／B-07 的措辭與 `tdd-enforce` 的紅線幾乎逐條對應——
> **這不是巧合，是因為那些紅線本來就是從同一種失敗歸納出來的。**
> **README 與 skill description 應該把這一群的原話再放進去**（見 §6 行動項）。

---

## §3 C 群 · 模型與成本意圖（對 AI Token King 最直接）

| # | 原始措辭 | 重複訊號 | 現有解法 | 缺的是什麼 | 對應 |
|---|---|---|---|---|---|
| C-01 | LLM gateway | 多來源（大量競品） | 眾多 gateway | — | L0 |
| C-02 | access multiple LLMs through a single API key | 多來源 | gateway | — | L0、`references/model-routing.md` |
| C-03 | cost-based routing / route high-volume to cheaper providers | 多來源 | gateway routing | **我方 routing 是靜態分類，不是可驗證 policy** | 缺口 DS-G7 |
| C-04 | 「不到收到帳單才發現超支」 | 多來源 | 成本監控 | — | §∞ 成本回報 |
| C-05 | token usage monitoring / per-request attribution | 多來源 | 觀測工具 | 我方只做到 `get_balance` 前後相減 | `references/model-routing.md` |
| C-06 | OpenAI-compatible proxy | 多來源 | — | — | 路線 C 換端點 |
| C-07 | multi provider LLM API | 多來源 | — | — | L2 互審 |

> ⚠️ **C 群同時是最誠實的一群：它顯示 LLM gateway 是一個擁擠的市場。**
> 本集群**不得**因此宣稱 AI Token King 比別家好（鐵律九）。
> 我方可以站得住的說法只有一句：
> **「這條產線的 L2 需要跨供應商互審，而管兩套金鑰的流程沒有人會維持超過兩週。」**
> 那是**流程需求**，不是產品比較。

---

## §4 D 群 · MCP 與安裝意圖（第一次被擋住的那一刻）

| # | 原始措辭 | 重複訊號 | 現有解法 | 缺的是什麼 | 對應 |
|---|---|---|---|---|---|
| D-01 | Claude Code MCP server error / 401 | 多來源 | 官方錯誤文件 | — | L0 路線 D |
| D-02 | **「MCP server 在剝離過的環境裡跑；終端機的環境變數、`.env`、shell 設定不會被繼承」** | 多來源，且被描述為**最常見**的「server 起得來但工具失敗」成因 | 明寫 `env` 區塊 | — | **L0 路線 A 的坑，已寫** |
| D-03 | 401 是認證問題，永遠不是 server 問題 | 多來源 | — | — | L0 路線 D 表格 |
| D-04 | adding and configuring an MCP server in Claude Code | 多來源 | 教學文 | — | L0 |
| D-05 | MCP cost tracking | 單一來源 | — | — | §∞ |

> **D-02 是這份掃描對現有實作最強的一次外部佐證。**
> `aitokenking-setup` 路線 A 的坑寫著「寫進 `.env` 而沒有 `export` 是最常見的 401 原因」——
> 外部來源獨立地把同一件事描述為最常見成因。**這一條可以從 E5 升到 E3。**

---

## §5 E 群 · 候選 skill 的意圖依據（Review §3.1 的四支）

Review 建議新增四支高頻入口 skill，並要求**從真實 intent 回推，不要先決定名字再找理由**。
本節就是那個回推。**尚未動工——這是 P1。**

| 候選 skill | 意圖依據 | 判定 |
|---|---|---|
| `ai-code-review` | A-08、B-01、B-02、B-03 | **依據最強。** 四條獨立措辭指向同一入口，且現有七支**沒有一支接得住** |
| `bug-reproduce` | 本輪未取得直接措辭 | **依據不足。** 不得因為 review 提到就開工——先補搜 |
| `dependency-upgrade-guard` | B-02 附帶提到「不要只因為助理推薦就裝套件」 | **依據弱。** 只有一條，且是別的主題的附註 |
| `pr-ready` | A-01（PR 太大）間接相關 | **依據弱。** |

> **這一節刻意不把四支都寫成「該做」。**
> Review 自己說了「不要先決定名字再找理由」——
> 那麼在只有一支拿得出四條獨立依據的情況下，**把另外三支寫成待補搜，才是照著它做。**
> 這也是本 repo 的 L2 YAGNI 閘門對自己的套用。

---

## §6 本次掃描的行動結論

| 編號 | 結論 | 狀態 |
|---|---|---|
| S2-01 | B 群措辭應補進 README 與相關 skill 的 `description` | 本次一併做 |
| S2-02 | D-02 的證據強度由 E5 升 E3，來源記於本檔 | 本次一併做 |
| S2-03 | `ai-code-review` 意圖依據充分，列為下一支 skill 的第一順位 | **P1，未動工** |
| S2-04 | `bug-reproduce` 等三支依據不足，需 SCAN-002b 補搜 | **P1，未動工** |
| S2-05 | C-03 顯示我方 routing 是靜態分類而非可驗證 policy | **開新缺口 DS-G7** |

---

## §7 這份掃描的邊界

1. **量不到 frequency。** 沒有關鍵字流量工具，全部「未量測」。
   任何「這個痛點很多人有」的說法，在本 repo 都不成立。
2. **語言偏誤。** 六輪全部是英文查詢。中文開發者社群的措辭**完全沒有掃到**。
3. **來源偏向內容行銷。** 回傳結果大量是工具商的部落格與比較文，
   **它們描述痛點的動機是賣東西**——痛點的存在可信，嚴重程度不可信。
4. **時間點會過期。** 2026-08-29 的措辭，三個月後會不一樣。
   重跑方式：本檔 §首的六輪查詢原樣再跑。
5. **`bug-reproduce` 等三支候選缺乏依據，本輪不補。** 見 §5。
