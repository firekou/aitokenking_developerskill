# SCAN-001 · GitHub 開發者架構 Top 10 掃描報告

**掃描日：** 2026-08-29
**方法：** GitHub Search API（`mcp__github__search_repositories`），依 `stars` 排序。
**查詢式：** `topic:spec-driven-development`、`topic:agent-skills`、`topic:context-engineering`、
`topic:claude-code stars:>1000`、`topic:tdd topic:ai-agents`、`spec-kit in:name`、`BMAD in:description`、
`claude-task-master in:name`。
**證據強度：** ⛔ **全部 E3（倉庫事實）** —— star 數與 topic 由 API 直接讀出、可複查；
**但每一支的「效果」都來自它自己的 README，屬 E6，我方零實跑。**
**這份報告不是評測，是選型掃描。** 見缺口 `DS-G3`。

---

## §1 篩選規則（先講，免得排名看起來像憑感覺）

搜出來的高 star 專案裡有一大類**不是開發方法架構**：記憶體（claude-mem）、
token 壓縮（headroom、rtk、caveman）、閘道（OmniRoute）、知識圖譜（graphify）、
IDE／ADE（orca、agtx）。它們很熱，但它們解的不是「怎麼規劃、怎麼檢核、怎麼守住架構」。

**入選判準（三條全中才算）：**

1. 它規定**流程的形狀**（階段、交接物、放行條件），而不只是提供工具。
2. 它的產物是**可被下一個人接手的檔案**（spec／plan／task／規則），不是對話。
3. 它對「什麼時候不准往下走」有明講的判準。

依此，`wshobson/agents`（39,234 ★）雖然 star 高於名單末位，**仍被排除** ——
它是 agent／plugin 市集，不規定流程形狀。**寫出來是因為排除也要可複查。**

---

## §2 Top 10（依 star 數，2026-08-29 讀取）

| # | 專案 | ★ | 它真正貢獻的**結構零件** |
|---|---|---|---|
| 1 | [`anthropics/skills`](https://github.com/anthropics/skills) | 172,329 | **骨架標準本身**：frontmatter ＋ 固定章節 ＋ 漸進揭露。所有其他家的 skill 都長成這個形狀 |
| 2 | [`github/spec-kit`](https://github.com/github/spec-kit) | 132,084 | **規格驅動四拍**：`/specify → /plan → /tasks → /implement`，外加 `constitution`（專案不可違反的憲法） |
| 3 | [`DietrichGebert/ponytail`](https://github.com/DietrichGebert/ponytail) | 115,627 | **YAGNI 閘門**：最好的程式碼是你沒寫的那些。唯一一支主張「先證明需要寫」的熱門架構 |
| 4 | [`addyosmani/agent-skills`](https://github.com/addyosmani/agent-skills) | 90,555 | **工程實務 skill 化**：把 code review／效能／可及性等既有實務寫成可觸發的 skill |
| 5 | [`Fission-AI/OpenSpec`](https://github.com/Fission-AI/OpenSpec) | 66,590 | **變更提案（change proposal）**：規格不是一次寫完，是以 diff 的形式演進並被審 |
| 6 | [`shanraisshan/claude-code-best-practice`](https://github.com/shanraisshan/claude-code-best-practice) | 65,314 | **從 vibe coding 到 agentic engineering 的過渡教材**：把「感覺對了就送」拆成可教的步驟 |
| 7 | [`gsd-build/get-shit-done`](https://github.com/gsd-build/get-shit-done) | 64,627 | **meta-prompting ＋ 長時自主**：讓 agent 跑很久而不丟失大局。⚠️ **已封存**，後繼 [`open-gsd/gsd-core`](https://github.com/open-gsd/gsd-core)（8,862 ★） |
| 8 | [`bmad-code-org/BMAD-METHOD`](https://github.com/bmad-code-org/BMAD-METHOD) | 52,429 | **角色分工與 Grooming**：Analyst／PM／Architect／SM／Dev／QA 六角色，story 由 SM 細化後才進 Dev |
| 9 | [`eyaltoledano/claude-task-master`](https://github.com/eyaltoledano/claude-task-master) | 28,032 | **PRD → 任務圖**：任務分解、依賴、複雜度評分，任務是一等公民 |
| 10 | [`OthmanAdi/planning-with-files`](https://github.com/OthmanAdi/planning-with-files) | 26,409 | **狀態落檔**：計畫寫成 markdown 檔、逐輪重新注入、`/clear` 與壓縮後可復原、完成閘門是確定性的 |

---

## §3 補位名單（star 較低，但補上 Top 10 缺的那一塊）

Top 10 由 star 決定，**而 star 高的那一群集中在「規劃」，不在「檢核」。**
以下五支 star 低一到兩個量級，卻是唯一認真處理「怎麼證明它真的對」的：

| 專案 | ★ | 補的是什麼 |
|---|---|---|
| [`gemini-cli-extensions/conductor`](https://github.com/gemini-cli-extensions/conductor) | 3,713 | SDD 的跨 agent 移植（Antigravity／Claude Code） |
| [`gotalab/cc-sdd`](https://github.com/gotalab/cc-sdd) | 3,645 | **核准過的規格才能進長時自主實作**（approved spec 是閘門） |
| [`maxritter/pilot-shell`](https://github.com/maxritter/pilot-shell) | 2,056 | **強制 TDD**（enforced，不是建議）＋ 各層品質強制 |
| [`modu-ai/moai-adk`](https://github.com/modu-ai/moai-adk) | 1,191 | **TRUST 5 品質閘門** ＋ 多模型成本控制（Claude×GLM 路由） |
| [`GanyuanRan/Aegis`](https://github.com/GanyuanRan/Aegis) | 1,145 | **架構漂移檢核**：baseline-first、evidence-verified、drift-checked |
| [`AmazingAng/old-coder`](https://github.com/AmazingAng/old-coder) | 699 | **證據優先**：不要讀碼，讓它跑過刑場（mutation／property-based testing） |

**這一節是本掃描最重要的發現：**
**熱度集中在「怎麼開始」，冷清的地方是「怎麼證明它沒壞」。**
一個只抄 Top 10 的集群，會複製同一個偏斜。

---

## §4 十家共同收斂出來的十個結構零件

把十家（含補位）的流程攤平對齊之後，重複出現的零件只有這些：

| # | 零件 | 誰在做 | 少了它會怎樣 |
|---|---|---|---|
| P1 | **基準線先行** —— 先讀出現況事實，再談要改什麼 | Aegis、spec-kit `constitution` | agent 對著想像中的專案寫程式 |
| P2 | **規格與計畫分離** —— 規格講「要什麼」，計畫講「怎麼做」 | spec-kit、OpenSpec、cc-sdd | 需求與實作綁死，換做法就得重寫需求 |
| P3 | **驗收條件先於實作** —— Given/When/Then 寫在寫碼之前 | BMAD、spec-kit | 「做完了」變成一種感覺 |
| P4 | **任務圖與依賴** —— 任務是一等公民，有依賴、有複雜度 | task-master、BMAD | 平行做兩件互相打架的事 |
| P5 | **角色分工** —— 細化的人與實作的人不同 | BMAD | 寫規格的人自己放行自己 |
| P6 | **測試先行與品質閘門** | pilot-shell、moai-adk、old-coder | 綠燈來自「沒跑」而不是「跑過」 |
| P7 | **狀態落檔** —— 交接的是檔案，不是對話 | planning-with-files、GSD | 壓縮／`/clear` 之後大局消失 |
| P8 | **漂移檢核** —— 拿完成品對回基準線 | Aegis | 三十次小改之後架構已經是另一個東西 |
| P9 | **最小化紀律（YAGNI）** | ponytail | 規格驅動最典型的失敗：規格寫得很完整，然後全部做了 |
| P10 | **機器可檢核的骨架** | anthropics/skills | 規範靠人記，而人會忘 |

---

## §5 對本集群的設計結論

**P1–P10 不是十支 skill，是六層加一個編排器。** 對應關係：

| 本集群的層 | 收哪些零件 | 取自 |
|---|---|---|
| L1 `repo-recon` | P1 | Aegis、spec-kit |
| L2 `spec-groom` | P2 P3 P5 P9 | BMAD、OpenSpec、ponytail |
| L3 `plan-decompose` | P4 P7 | task-master、planning-with-files |
| L4 `tdd-enforce` | P6 | pilot-shell、old-coder、moai-adk |
| L5 `arch-guard` | P8 P10 | Aegis、anthropics/skills |
| L0 `aitokenking-setup` | 跨層：模型路由與成本可查 | moai-adk 的多模型成本控制 |

**沒有被收進來的東西，也要講：**
BMAD 的六角色（P5）在本集群**被降級為 L2 內部的「兩人規則」**（細化的模型與審的模型不得同家），
因為一個人維護不起六個角色的往返；spec-kit 的 `constitution` 被併入 L1 的 `baseline.md`。
**這兩個都是取捨，不是改良。**

---

## §6 這份掃描的邊界

1. **star 數不是品質。** 它衡量的是「多少人按了收藏」，不是「多少人跑完並回來」。
2. **我方零實跑。** 上表所有「它貢獻什麼」都讀自 README 與 topic，屬 **E6 作者自述**。
   要升到 E1 需要有人真的各跑一輪並回填，見 `CONTRIBUTING.md`。
3. **時間點會過期。** 2026-08-29 的排名，三個月後會不一樣。
   重跑方式：本檔 §首的查詢式原樣再跑一次。
4. **搜尋語法有偏誤。** 依賴 topic 標記；沒打 topic 的專案搜不到。
   已知漏網：只在 `awesome-*` 清單裡被收錄、自己沒有 topic 的架構。
