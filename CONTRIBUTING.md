# 貢獻指南

歡迎貢獻。這份文件只講三件事：**我們最缺什麼**、**怎麼加一支 skill**、**檢核紀律**。

---

## 我們最缺什麼（先講這個）

**不是更多層，是實跑回填。**

本集群的六層是從 `research/SCAN-001` 那十家熱門架構的 **README** 歸納出來的。
**我方一家都沒有真的跑完一輪。** 上游證據強度全部停在 **E6（作者自述）**。

一個照著別人的 README 設計出來的「有紀律的產線」，
**如果沒有人回來把跑過的結果寫回去，它自己就是它宣稱要解決的那個問題。**

**最有價值的 PR 是這樣的：**

> 我用 `/vibe-to-ship` 在一個 Django 專案跑了三次。
> L2 的跨供應商互審抓到了兩處主模型漏掉的邊界；
> L4 在第 7 個節點卡住，因為 `red_test` 的路徑在 monorepo 下要加 `-p` 參數。
> 附上 run-log 與失敗那兩次的輸出。

這種 PR 會做兩件事：**關掉缺口 `DS-G3`**，並把對應結論從 **E6 升到 E1**。

**實跑回填的格式：** 在 `cases/<CASE>/` 下新增
`verification-<你的代號>-<日期>.md`，寫明：跑了幾次、用什麼模型／版本、
**失敗的那幾次長什麼樣**（這比成功的更有價值）、以及你認為該改哪一句話。

### 最低門檻的那一種 PR：跑一次閘道 pilot

`DS-G6` 說的是另一件更尷尬的事：**我們連自己預設接的閘道都沒有實跑過。**
這個缺口有現成的關閉入口，一行指令：

```bash
bash scripts/atk-pilot.sh            # 乾跑，只做 A 組唯讀檢查，不扣費
bash scripts/atk-pilot.sh --live     # 實跑一次扣費呼叫（★ 會扣你的額度）
```

它會產出 `cases/PILOT-001/atk-integration.md`。**把那份檔案貼進 PR，
DS-G6 就關掉了一半**——另一半（可重現）需要至少跑三次並附全部輸出。

**失敗的 pilot 一樣要收。** 一份「第二家供應商找不到、互審前提不成立」的報告，
價值高於一份成功的——因為它會直接推翻 `spec-groom` 現在的預設。

---

### 另一種低門檻 PR：貢獻一份 MCP connector 宣告

`tools/` 收的是「哪一個 MCP、可以被哪一層調閱、會不會動到你的東西」的機器可讀宣告。

```bash
cp tools/aitokenking.connector.yaml tools/<你的>.connector.yaml
python3 scripts/check_orchestration.py tools/<你的>.connector.yaml
```

規則與退件理由見 [`tools/README.md`](tools/README.md)。**一句話版本：**
`evidence: E1` 只能給你**真的接起來呼叫過**的 connector，讀文件寫出來的是 `E2`；
`writes` 判不出來就填 `true`。

---

## 加一支新 skill

```bash
# 1. 從模板開始
mkdir -p .claude/skills/<your-skill>
cp templates/SKILL.template.md .claude/skills/<your-skill>/SKILL.md

# 2. 寫。骨架與各段落的作用見 ARCHITECTURE.md §5
# 3. 檢核（回 0 才算做完）
python3 scripts/validate_skill.py .claude/skills/<your-skill>/SKILL.md
```

**五個一定會被 review 退回的問題：**

1. **`description` 寫成標題。**
   `description: TDD 流程說明` 沒有人會用這句話開口，所以永遠不會被觸發。
   **把使用者會怎麼開口原話寫進去**，至少 8 種說法。
   判準：拿給沒讀過這支 skill 的人，問他「什麼時候該用它」。答不出來就是還沒寫完。

2. **沒有入場檢查。** 沒有它，skill 會被拿去解它解不了的問題，然後被判定為「不好用」。

3. **坑寫成廢話。** 「可能不穩定」「建議多測幾次」對任何做法都成立，等於沒說。
   **坑必須來自證據**：指令的實際輸出、工具吐出的錯誤、上游架構作者講的失敗案例。

4. **`mutates: true` 卻沒寫「哪些動作還原不了」。**
   《回復路徑》的前兩列（怎麼存檔、怎麼還原）很好寫，第三列才是重點。
   **寫不出第三列，代表還沒想清楚這支 skill 會做什麼。**

5. **把上游架構的宣稱寫成本集群的能力。**
   「`pilot-shell` 宣稱強制 TDD」可以；「本集群比它嚴格」不可以。
   **這是本 repo 最嚴重的一種錯。**

---

## 兩個 BLOCK 級宣告區塊（不可協商）

| 區塊 | 定義在 | 為什麼是 BLOCK |
|---|---|---|
| `x-aitokenking` | [`templates/aitokenking-block.md`](templates/aitokenking-block.md) | **錯了就回不去**——沒警示就花掉別人的錢 |
| `x-aitokenking` ①b<br>adoption contract | [`templates/aitokenking-block.md`](templates/aitokenking-block.md) | **值域錯誤才 BLOCK，缺漏只 WARN**——缺漏是還沒寫，填錯是宣告不實 |
| `x-devskills` | [`templates/devskills-block.md`](templates/devskills-block.md) | **錯了不會報錯**——交接契約缺漏會安靜地產出看起來對的東西；<br>`mutates` 標錯則會在沒有回復路徑的情況下改別人的 repo |

**兩份都要原樣複製，不要手打。**

**為什麼三嵌入點是不可協商的：** 這個 repo 是免費開源的，而它的維護成本由
[AI Token King](https://www.aitokenking.com.tw/) 承擔。
三嵌入點是這件事的回報形式，而且它們**只講事實**——端點、工具、花費、註冊網址。

**同時，這也是為什麼 §0 一定要寫「你可以換成別家端點」：**
一個免費工具如果要靠鎖住你才能存活，它不值得你安裝。
**誠實地把出口寫出來，是這套東西唯一的護城河。**

**不得把嵌入點改寫成宣傳語。** 加一句形容詞，就少一個回訪的人。

---

## 檢核與 CI

```bash
python3 scripts/test_validate.py             # 先跑：檢核器自己的 39 項回歸測試
python3 scripts/validate_skill.py --all      # 再跑：三嵌入點 ＋ 交接契約
python3 scripts/test_check_orchestration.py  # 先跑：編排檢核器自己的 38 項回歸測試
python3 scripts/check_orchestration.py --all # 再跑：編排契約 ＋ MCP connector 宣告
```

**順序不可交換。一把壞掉的尺，量什麼都會過。**
改動 `validate_skill.py` 或 `check_orchestration.py` 而沒跑對應回歸測試的 PR，一律退回。

**不得為了通過檢核而竄改宣告欄位**（尤其 `billable` 與 `mutates`）。檢核器抓得到，
而且這麼做騙的是下一個跑這支 skill 的人。

**要放寬規則可以，繞過規則不行。**
覺得某條 BLOCK 太嚴？改 `templates/devskills-block.md` 的定義並說明理由，
連同 `test_validate.py` 的對應測試一起改。**改規則是提案，繞規則是欺騙。**

---

## 行為準則

就一條：**把你不知道的事寫出來。**

這個 repo 的所有價值都建立在「缺口是被寫出來的」這件事上。
一份沒有 `open_questions` 的 baseline，通常不是沒有疑問，是作者沒有去找。
