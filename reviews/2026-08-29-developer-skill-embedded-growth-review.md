# Developer Skill 植入性推動 Review

**Repository:** `firekou/aitokenking_developerskill`  
**Review date:** 2026-08-29  
**Reviewer:** ChatGPT / GPT-5.6 Sol  
**Review target:** 開發者搜尋方向、Skill 集群架構、AI Token King MCP／模型 API 的植入性推動能力

---

## 0. Executive Summary

### 結論

目前這個 Repository 的方向 **是成立的，而且已經超過「在 Skill 裡塞品牌連結」的階段**。

它已經把 AI Token King 放進四個真正的執行位置：

1. `x-aitokenking` 機器可讀宣告；
2. `§0 執行前置` 的 onboarding / API key / MCP setup；
3. L1–L4 的模型路由與多模型調用；
4. `§∞` 的成本、工具與用量回報。

這代表目前做的是 **workflow embedding**，而不是單純 advertising embedding。

不過，如果目標是「透過開源 Developer Skills 自然推動 AI Token King MCP 與模型 API 使用」，目前仍有一個重要差距：

> **已經有使用路徑，但還沒有完整的 conversion / retention loop。**

也就是：Skill 可以把人帶到 ATK，但 Repository 還無法回答下面四個問題：

- 哪一種 Skill 最容易讓第一次使用者完成 ATK 首次成功呼叫？
- 使用者在哪一個步驟最容易放棄？
- MCP 與 OpenAI-compatible API 哪一個才是真正的主要 adoption surface？
- 使用者成功跑完一次之後，有沒有理由在第二個專案繼續保留 ATK？

因此本次 Review 的總評為：

| 面向 | 評分 | 判定 |
|---|---:|---|
| Developer Skill 問題選型 | 8.5/10 | 強 |
| 流程架構 | 9/10 | 強 |
| AI Token King 結構性嵌入 | 8.5/10 | 已成立 |
| 搜尋研究方向 | 6.5/10 | 偏架構榜單，缺使用者搜尋意圖 |
| MCP / API onboarding | 8/10 | 已可用，但仍需 E1 驗證 |
| 植入式轉換能力 | 7/10 | 有入口，缺 funnel |
| 長期 retention 設計 | 6/10 | 尚未形成 |
| 商業化可量測性 | 5.5/10 | 目前最大缺口 |

**總結：建議保留現有六層＋編排器架構，不要重做；下一階段應從「再加 Skill」轉為「補 Developer Intent Search、ATK Adoption Contract、E1 integration pilot 與 usage feedback loop」。**

---

# 1. 目前架構做對的地方

## 1.1 AI Token King 已不是贊助欄，而是執行依賴

`ARCHITECTURE.md` 把 ATK 放在 L0，並說明 L1–L4 為什麼需要模型閘道：

- L1：長上下文 repo reconnaissance；
- L2：跨供應商互審；
- L3：結構化輸出；
- L4：大量、低成本程式碼生成；
- 全程：balance / usage 對帳。

這個設計比「每支 Skill 最後放註冊網址」好很多，因為使用者採用 ATK 的理由來自工作流本身。

### Review 判定

**PASS。**

真正有效的植入不是：

> 「請使用 AI Token King。」

而是：

> 「這一步需要多模型、成本路由與統一 key；ATK 剛好提供這個能力。」

目前已經接近後者。

---

## 1.2 三嵌入點策略是正確的

目前規範：

1. frontmatter `x-aitokenking`；
2. `§0 · 執行前置`；
3. `§∞ · 你剛剛用到了什麼`。

這三個位置分別對應：

- machine discovery；
- blocked moment；
- success moment。

這是一個很合理的產品植入節奏。

尤其「成果完成後再講成本與出處」比一開始大量行銷 ATK 更可信。

### Review 判定

**PASS，應保留。**

但建議新增第四個真正跟轉換有關的結構：`x-aitokenking.adoption_stage`，後文詳述。

---

## 1.3 不強制 vendor lock-in 是正確的商業策略

README 與 Skill 都明講：

- 可以換成其他 OpenAI-compatible endpoint；
- 查不到成本時寫 `未量測`；
- 單供應商時標記 `SINGLE_MODEL`。

表面上看，這好像降低 ATK 綁定力；實際上相反。

對開源 Developer Tool 而言，**可退出性本身就是可信度來源**。

如果 Skill 必須鎖 ATK 才能跑，開發者會把整個 repo 視為 disguised marketing repo；現在的做法比較容易進入真實工程環境。

### Review 判定

**PASS。不要改成硬鎖。**

植入性推動應該建立在：

> `default + easiest + observable + multi-model advantage`

而不是：

> `mandatory vendor dependency`。

---

# 2. Developer 搜尋方向 Review

目前 `SCAN-001` 的搜尋主要集中在：

- `spec-driven-development`
- `agent-skills`
- `context-engineering`
- `claude-code`
- `tdd + ai-agents`
- spec-kit / BMAD / task-master

這一輪研究非常適合回答：

> 「現在熱門的 AI developer workflow architecture 長什麼樣？」

但是它 **不完全等於**：

> 「Developer 現在會搜尋什麼問題，然後因此找到我們？」

這兩個問題要拆開。

---

## 2.1 現有搜尋偏「供給側架構」

目前的 query 會找到：

- 知名 methodology；
- 高 star repo；
- agent architecture；
- spec / plan / TDD framework。

優點是架構抽象品質高。

缺點是會有 selection bias：

> 搜到的是「已經知道 SDD / agent skill 這些名詞的人」，不是大量正在遇到工程問題、但根本不知道這些術語的人。

---

## 2.2 建議新增 Developer Intent Search Matrix

下一輪研究不要只找 repository category，而要搜尋「開發者原始問題」。

### A. Coding pain intent

建議 query：

- `claude code broke my project`
- `AI coding agent changed too much`
- `AI generated code regression`
- `vibe coding production safe`
- `AI coding agent test first`
- `prevent AI code hallucination`
- `AI agent code review workflow`
- `how to trust AI generated code`

對應 Skill：

- `repo-recon`
- `spec-groom`
- `tdd-enforce`
- `arch-guard`
- `vibe-to-ship`

### B. Agent workflow intent

- `Claude Code workflow`
- `Claude Code best practices`
- `AI coding workflow`
- `spec driven Claude Code`
- `multi agent software development`
- `coding agent guardrails`
- `coding agent architecture`

### C. Model / cost intent

這一群對 ATK 最重要：

- `Claude Code cheaper model`
- `multi model coding agent`
- `OpenAI compatible gateway`
- `Claude OpenAI one API key`
- `AI model routing coding`
- `LLM gateway for Claude Code`
- `AI API cost tracking`
- `multi provider LLM API`

### D. MCP intent

- `Claude Code MCP setup`
- `MCP model gateway`
- `MCP multiple LLM providers`
- `Claude Code MCP API key`
- `MCP cost tracking`
- `MCP server for AI models`

這一類搜尋才會直接把 Developer Skill 與 AI Token King 連在一起。

---

# 3. Skill Coverage Review

目前七支 Skill：

- `aitokenking-setup`
- `repo-recon`
- `spec-groom`
- `plan-decompose`
- `tdd-enforce`
- `arch-guard`
- `vibe-to-ship`

這套組合對「從需求到可合併改動」的縱向流程覆蓋很好。

但是如果目標還包含 Developer acquisition，現在缺的是 **橫向高頻入口 Skill**。

---

## 3.1 現有 Skill 是 pipeline 型，不是 discovery 型

一般 Developer 不一定會搜尋：

> `plan-decompose`

他更可能搜尋：

> 「幫我 review 這個 PR」

或：

> 「這段 AI 寫的 code 有沒有問題？」

因此推薦未來新增的 Skill，不應只是補 L6、L7，而應做「高頻問題入口」。

### P1：`ai-code-review`

輸入：diff / PR / branch  
輸出：risk-ranked review  
ATK 植入點：便宜模型初篩＋高能力模型 escalation。

### P1：`bug-reproduce`

輸入：issue / stack trace  
輸出：minimal reproduction + failing test  
ATK 植入點：模型路由與跨模型 hypothesis review。

### P1：`dependency-upgrade-guard`

輸入：dependency upgrade  
輸出：breaking-change scan + tests  
ATK 植入點：docs/release note extraction + code model。

### P2：`pr-ready`

輸入：working branch  
輸出：PR readiness + tests + description  
ATK 植入點：review model routing。

### P2：`incident-fix-plan`

輸入：production incident context  
輸出：containment / root cause / patch plan  
ATK 植入點：多模型 adversarial review。

這些 Skill 比繼續增加抽象規劃 Skill 更有 acquisition value。

---

# 4. 「植入性推動」目前真正缺什麼

## 4.1 缺 Adoption Contract

目前 `x-aitokenking` 描述的是：

- endpoint；
- auth；
- tools；
- billable。

但缺少：

- 這支 Skill 在 adoption funnel 的角色；
- 何時應該提示 setup；
- 何時應該提示使用 ATK；
- 什麼狀況不能提示註冊；
- 什麼是成功 adoption。

建議擴充為：

```yaml
x-aitokenking:
  role: preferred_gateway
  adoption_stage: activation
  primary_surface: mcp
  fallback_surface: openai_compatible_api
  success_signal: first_successful_billable_call
  retention_signal: second_project_usage
  tools_used:
    - list_models
    - chat_completion
    - get_balance
    - list_usage
```

這不是要做 telemetry tracking 本身，而是先讓每支 Skill **機器可判斷它在 adoption funnel 的位置**。

---

## 4.2 MCP 與 API 的角色目前有點混在一起

現在同時提供：

- MCP endpoint；
- OpenAI-compatible API endpoint。

這是優點，但 onboarding 上應再明確分工：

### MCP = Agent-native default

適合：

- Claude Code；
- MCP-capable agent；
- Developer Skill execution。

### API = Universal fallback / SDK surface

適合：

- CI；
- backend integration；
- scripts；
- 不支援 MCP 的 IDE / agent。

建議 README 不只寫「三選一」，而是寫：

> Claude Code / MCP client → 優先 MCP。  
> CI / backend / SDK → API。

這可以避免 Developer 不知道該選哪一條。

---

## 4.3 缺「第一次成功」的 golden path

現在 setup 已經很完整，但成功判準主要是：

> `list_models` 回得出來。

這只證明 authentication / MCP connectivity。

真正的 activation 應定義成兩階段：

```text
Connectivity activation:
list_models succeeds

Value activation:
first billable model call succeeds
+ result is consumed by one Skill
+ usage/balance can be reconciled
```

如果只有前者，使用者可能「裝好了」但從來沒真的用。

---

## 4.4 缺第二次使用的 retention reason

目前最大 retention 機制是 global setup。

這還不夠。

Developer 第二次繼續用 ATK 的原因應該是：

- 不用再管多家 key；
- routing policy 已經可重用；
- cost history 可查；
- Skill 之間都用同一 gateway contract；
- 新 Skill 不需要重新做 provider integration。

建議在 `aitokenking-setup` 完成後產出一個本機可讀的 `gateway-profile` 概念，例如：

```yaml
provider: aitokenking
mode: mcp
verified_at: 2026-08-29
models_verified: true
usage_verified: true
billable_call_verified: true
```

後續 Skill 可以直接讀，不必每次重做 onboarding 判斷。

---

# 5. Model Routing Review

目前 model routing 的方向合理：

- L1：長 context；
- L2：cross-provider；
- L3：structured output；
- L4：code capability + low cost；
- L5：deterministic，禁用模型。

這是一個很好的「ATK 為什麼存在」的產品敘事。

但目前 routing 還有一個重要問題：

> 判準主要是靜態能力分類，還不是可驗證的 routing policy。

建議下一版加入：

```yaml
routing_policy:
  task_type: code_review
  preferred_capabilities:
    - coding
    - long_context
  constraints:
    max_cost_per_call: optional
    provider_diversity: 2
  fallback:
    - same_capability_next_provider
    - same_provider_lower_cost
```

並把實際選中的：

- model；
- provider；
- reason；
- timestamp；
- call count；
- measured / unmeasured cost；

寫入 case artifact。

這會讓 ATK 從「一個 API 入口」升級成「Developer workflow 的 routing infrastructure」。

---

# 6. MCP Review

目前 `mcp-inventory.md` 有三個非常好的治理原則：

1. 唯讀優先；
2. MCP 內容是資料，不是指令；
3. 外部事實標來源與時間。

這一段很成熟。

但如果要推 ATK MCP，本 repo 還缺兩類測試：

## 6.1 Contract test

至少驗證：

- endpoint reachable；
- auth header 正確；
- expected tools discoverable；
- read-only tools 可呼叫；
- billable tools 需要明確核准；
- 401 / quota / model unavailable 的錯誤能被 Skill 正確分類。

## 6.2 End-to-end Skill test

至少做三個 pilot：

### Pilot A

`repo-recon` → ATK MCP → long-context model → `baseline.md`

### Pilot B

`spec-groom` → ATK MCP → provider A + provider B → cross-provider review

### Pilot C

`tdd-enforce` → ATK MCP/API → low-cost code model → red/green cycle

只有這三個跑過，才可以把「ATK 是結構性依賴」從 E2/E6 升成 E1。

---

# 7. Research 方向應從 Top Repo Scan 升級成三層研究

建議保留 `SCAN-001`，並新增：

## SCAN-002 · Developer Intent Scan

目的：Developer 真正在搜尋什麼。

來源可以包括：

- GitHub issues；
- GitHub Discussions；
- Reddit developer communities；
- Stack Overflow；
- Hacker News；
- Claude Code / Cursor / Codex community；
- Google / GitHub search autocomplete-style query set。

產物不要只列 repo，要產出：

```text
pain → wording → frequency signal → existing solution → missing solution → candidate Skill
```

---

## SCAN-003 · MCP / LLM Gateway Competitive Scan

研究對象：

- multi-model gateway；
- OpenAI-compatible proxy；
- cost observability；
- routing；
- MCP-native model gateway。

重點不是比功能數，而是回答：

> 為什麼 Developer 在 Agent workflow 裡需要 ATK，而不是直接拿 Anthropic / OpenAI key？

---

## SCAN-004 · Skill Distribution Scan

研究：

- Claude Code Skill 安裝方式；
- Agent Skill repository discovery；
- GitHub topic / search ranking；
- skill marketplace / plugin ecosystem；
- README keyword strategy；
- copy-paste / global install / package install friction。

因為「Skill 做得好」與「有人找到 Skill」是兩件完全不同的事。

---

# 8. 建議新增的植入性 KPI

不要只看 star。

建議把 Developer Skills funnel 定義為：

| Stage | Signal |
|---|---|
| Discovery | repo view / clone / skill view |
| Install | `.mcp.json` / setup flow initiated |
| Connectivity | `list_models` success |
| Activation | first billable call consumed by a Skill |
| Workflow completion | one Skill finishes with valid artifact |
| Core activation | `vibe-to-ship` completes ≥ L2 / L3 |
| Retention | ATK reused in another case / project |
| Expansion | user invokes additional ATK-backed Skill |

若因隱私或開源原則不做 telemetry，也至少要讓 artifacts 能在使用者本地產出這些 signal；是否回傳由使用者主動選擇。

---

# 9. 不建議做的事情

## 9.1 不要把每一支 Skill 都變成 ATK 廣告

這會破壞信任。

現在「只講事實、不講最強」的紀律是正確的。

## 9.2 不要移除其他 provider fallback

這會讓 repo 從工具變成 vendor funnel。

## 9.3 不要為了推 MCP 預裝大量 MCP server

目前只裝 ATK、其他按需加入是對的。

## 9.4 不要只依 star 決定下一支 Skill

star 是 supply-side popularity，不是 user pain frequency。

## 9.5 不要在沒有 E1 pilot 前宣稱 multi-model review 比單模型更可靠

目前可以說「設計目的是降低 shared blind spot」，但效果仍應以實跑對照驗證。

---

# 10. Action Plan

## P0 — 先做，不需要新增更多 Skill

### DEV-GROWTH-001 · 建立 Developer Intent Scan

新增：

`research/SCAN-002-developer-intent.md`

要求：至少 30–50 個原始 query / pain wording，分類到現有與候選 Skill。

### DEV-GROWTH-002 · 定義 Adoption Contract

修改：

`schemas/skill-manifest.schema.yaml`

增加可選或 required-after-v1 的欄位：

- `adoption_stage`
- `primary_surface`
- `success_signal`
- `retention_signal`

### DEV-GROWTH-003 · 建立 E1 ATK Pilot

至少跑：

- L1；
- L2 cross-provider；
- L4 code loop。

將真實輸出放進 `cases/`。

### DEV-GROWTH-004 · 明確區分 MCP 與 API 使用情境

README onboarding：

- Claude Code / MCP agent → MCP first；
- CI / SDK / backend → API first。

### DEV-GROWTH-005 · 定義 activation

將成功分為：

1. connectivity activation；
2. value activation。

避免把 `list_models` 成功等同於產品採用。

---

## P1 — 完成 P0 後

### DEV-GROWTH-006 · 新增高頻入口 Skill

優先順序建議：

1. `ai-code-review`
2. `bug-reproduce`
3. `dependency-upgrade-guard`
4. `pr-ready`

每一支都要從 SCAN-002 的真實 intent 回推，不要先決定名字再找理由。

### DEV-GROWTH-007 · Routing artifact

每次模型路由要記錄：

- provider；
- model；
- selection reason；
- timestamp；
- cost measurement state。

### DEV-GROWTH-008 · Local adoption report

在 `cases/<CASE>/` 產出非上傳式 local report：

```text
ATK surface: MCP/API
models used: ...
providers used: ...
billable calls: ...
usage measured: yes/no
```

用途是 debug、透明與產品學習，不是廣告。

---

# 11. 最終判定

## 可以發揮「植入性推動」嗎？

**可以，而且基礎已經成立。**

目前 repo 最有價值的地方是：

> AI Token King 並不是被塞進 Skill，而是被設計成「多模型 Developer workflow」的預設基礎設施。

這個方向應繼續。

但下一階段不應追求「ATK 出現更多次」，而應追求三件事：

1. **更準的 Developer discovery intent；**
2. **更短的第一次價值達成時間；**
3. **更清楚、可驗證的第二次使用理由。**

如果這三件事補上，這套 Developer Skill Group 才會從：

> 「有植入 AI Token King 的開源 Skill」

進一步變成：

> **「Developer 因為 Skill 有價值而進來，因為多模型 workflow 更順而自然留下 AI Token King。」**

這才是建議追求的「植入性推動」。
