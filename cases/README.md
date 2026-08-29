# cases/ —— 產線產物目錄

每一個需求一個資料夾，格式 `CASE-<三位數>`。**這裡的檔案就是層與層之間的交接契約。**

```
cases/CASE-001/
├── baseline.md        L1 產出 —— 現況事實，每條附來源
├── spec.yaml          L2 產出 —— 驗收條件 ＋ 非目標 ＋ YAGNI 裁決 ＋ 互審狀態
├── task-graph.yaml    L3 產出 —— 依賴圖 ＋ 風險 ＋ 每任務一條紅測試
├── run-log.md         L4 產出 —— 每節點的紅／綠／全測原始輸出
├── guard-report.md    L5 產出 —— 漂移、超譯、測試完整性、放行判定
└── verification-<代號>-<日期>.md   ★ 實跑回填（見 CONTRIBUTING.md）
```

**為什麼交接走檔案而不是對話：**
上下文被壓縮或 `/clear` 之後，對話裡的 baseline 會消失，而 `baseline.md` 不會。
這也是為什麼任何一層都可以單獨重跑。

---

## 目前這裡是空的

**這不是還沒整理，是本 repo 目前最誠實的狀態：**
本集群的六層是從 `research/SCAN-001` 那十家熱門架構的 README 歸納出來的，
**我方尚未跑完任何一個完整案例。** 見缺口 `DS-G3`。

**第一個 PR 如果是一個真的跑完的 CASE，它的價值高於再加一層。**
回填格式見 [`CONTRIBUTING.md`](../CONTRIBUTING.md)。
