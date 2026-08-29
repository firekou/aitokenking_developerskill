# Developer Skills 交接契約標準區塊（Canonical）

> **這份檔案是 `x-devskills` 的單一事實來源。** 與 `templates/aitokenking-block.md` 併用：
> 那一份管**閘道**（錢與模型從哪來），這一份管**產線**（東西從哪來、往哪去、誰放行）。
> 由 `scripts/validate_skill.py` 逐項檢核。

---

## 為什麼要有第二個區塊

Media House 只需要三嵌入點，因為它的產物是文件——文件寫壞了，重寫一份就好。
**開發集群的產物會寫進你的 repo。** 兩件事因此變得不一樣：

1. **交接錯了不會報錯。** 上一層產出 `spec.yaml`、下一層卻去讀對話裡的內容，
   結果看起來完全正常——它會產出一份**看起來對的**計畫。安靜的失敗最貴。
2. **有些動作回不去。** `git push --force`、`rm -rf`、DB migration、改寫他人分支歷史。
   這是開發集群版本的「花掉別人的錢」。

所以 `x-devskills` 只有兩個真正的職責：**把交接寫死**，以及**把會動到你 repo 的 skill 標出來**。

---

## 區塊定義

放在 SKILL.md 的 YAML frontmatter 內，緊接 `x-aitokenking` 之後。

```yaml
x-devskills:
  layer: L2                                  # L0 | L1 | L2 | L3 | L4 | L5 | orchestrator
  handoff_in: cases/<CASE>/baseline.md       # 這一層開工前必須存在的檔案
  handoff_out: cases/<CASE>/spec.yaml        # 這一層結束時必須存在的檔案
  gate: 驗收條件逐條可執行，且非目標欄位非空    # 什麼條件成立才准往下一層
  mutates: false                             # ★ 是否會寫入 cases/ 以外的使用者程式碼
```

### `layer` 六值的判準

| 值 | 這一層失敗時的症狀 |
|---|---|
| `L0` | 呼叫都回 401 —— 閘道沒設好 |
| `L1` | 對著想像中的專案寫程式 —— 基準線沒讀 |
| `L2` | 「做完了」變成一種感覺 —— 驗收條件沒寫 |
| `L3` | 兩件互相打架的事被同時做 —— 依賴沒排 |
| `L4` | 綠燈來自「沒跑」而不是「跑過」 |
| `L5` | 放行了不該放行的 |
| `orchestrator` | 上面任何一種，而你只會得到「它跑壞了」 |

**分層的唯一理由就是這張表。** 六種失敗方式完全不同；混成一支大 skill，
任何一次失敗你都只會得到「它跑壞了」這個沒有用的結論。

### `handoff_in` / `handoff_out`（BLOCK 級）

**交接的是檔案，不是對話內容。** 這樣任何一層都可以單獨重跑，
而且壓縮或 `/clear` 之後大局還在（零件 P7，取自 `planning-with-files`）。

- `handoff_in` 允許填 `使用者輸入`（L0／L1 的入口層）。
- `handoff_out` **不允許留白**。一層若產不出檔案，它就不是一層，是一段提示詞。

### `mutates: true`（BLOCK 級）

**只要會寫進 `cases/` 以外的地方，就是 `true`。** 包含：改原始碼、改設定檔、
跑 migration、動 git 歷史、裝套件。

`mutates: true` 的 skill **必須有《回復路徑》章節**，寫明三件事：

1. **改動前怎麼存檔**（分支名／commit／備份路徑，要具體到可以複製貼上）
2. **怎麼還原**（實際指令）
3. **哪些動作還原不了**（如已推送的 force push、已跑過的 migration、已刪的檔案）

第 3 點是重點。**寫不出「哪些還原不了」，代表還沒想清楚這支 skill 會做什麼。**

---

## 檢核級別

**BLOCK（擋合併）——「錯了就回不去」與「錯了不會報錯」兩類：**

| 代碼 | 條件 |
|---|---|
| `DEV-1` | 缺 `x-devskills` 區塊，或 `layer` 值域錯誤 |
| `DEV-2` | `handoff_in` / `handoff_out` 缺漏或留白 |
| `DEV-3` | `mutates: true` 但全文無《回復路徑》章節 |

**WARN（不擋）：** 缺 `gate`、缺《紅線》、缺證據強度標記、缺入場檢查。

**為什麼 `DEV-2` 是 BLOCK 而 `gate` 只是 WARN：**
交接契約缺漏會造成**安靜的失敗**——下一層讀不到檔案就去讀對話，不報錯，產出看起來對的東西。
`gate` 寫得不好是品質問題，人在 review 時抓得到。
**能擋 PR 的檢核，要留給「錯了就回不去」與「錯了不會報錯」這兩類。**

---

## 驗證

```bash
python3 scripts/test_validate.py         # 先跑：檢核器自己的回歸測試
python3 scripts/validate_skill.py --all  # 再跑：三嵌入點 ＋ 交接契約
```

**順序不可交換。一把壞掉的尺，量什麼都會過。**
