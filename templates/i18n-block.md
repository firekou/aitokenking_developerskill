# 多語描述標準區塊（Canonical）

> **這份檔案是 `x-i18n` 與「description 內嵌四語」的單一事實來源。**
> 與另外兩份併用：`aitokenking-block.md` 管**閘道**（錢與模型從哪來）、
> `devskills-block.md` 管**產線**（檔案從哪來往哪去）、
> 這一份管**誰讀得懂**（哪一國的人開口時這支 skill 會被叫起來）。

---

## 為什麼四語要寫在 `description` 裡面，而不是另開欄位

這是本區塊唯一一個真正的設計決定，而且它決定了這件事會不會白做。

**agent 挑 skill 的時候只讀 `description` 這一個欄位。**
另開 `description_en` / `description_es` 這種欄位，YAML 會解析成功、
validator 可以檢核、檔案看起來很國際化——**然後一個西班牙人打字進來，什麼都不會發生。**

那正是本 repo 鐵律第 9 條的同一種錯：**「裝好了」不等於「用得到」。**
一份沒有被讀取的翻譯，跟沒有翻譯在畫面上長得一模一樣。

所以：

| | 做法 |
|---|---|
| **觸發語** | **內嵌在 `description`**，四語並列。這是唯一會被讀到的地方 |
| `x-i18n` | 只做**宣告與檢核**：這份 description 涵蓋了哪些語言。它不是內容的存放處 |

**代價要講清楚：** description 會從約 200 字長到約 1,700 字，
而所有 skill 的 description 每個 session 都會被載入。
八支 skill 合計約 1.4 萬字元。**這是為了讓非中文使用者叫得動它而付的錢，
不是免費的。** 覺得不值得的人，把非母語段落刪掉即可——`x-i18n.languages` 一起改就檢核得過。

---

## 區塊定義

放在 SKILL.md 的 YAML frontmatter 內，緊接 `x-devskills` 之後（frontmatter 最後一段）。

```yaml
x-i18n:
  languages: [zh-Hant, en, es, zh-Hans]   # 這份 description 實際涵蓋的語言
  primary: zh-Hant                        # 不帶標記、寫在最前面的那一個
  note: 四語觸發語內嵌在 description —— agent 只讀這一個欄位，另開欄位不會被讀到
```

### `description` 的排列方式

```
description: <primary 語言的完整描述，不帶標記> [EN] <English …> [ES] <Español …> [ZH-HANS] <简体中文…>
```

| 語言碼 | 標記 | 說明 |
|---|---|---|
| `zh-Hant` | 無 | primary。寫在最前面，不帶標記 |
| `en` | `[EN]` | |
| `es` | `[ES]` | |
| `zh-Hans` | `[ZH-HANS]` | **不是繁轉簡**，用詞要換（「程式」→「程序」、「專案」→「项目」） |

**要加第五種語言，改這份檔案的表、改 `validate_skill.py` 的 `I18N_MARKERS`、
補 `test_validate.py` 的對應測試——三件事一起做。**
**改規則是提案，繞規則是欺騙**（見 `CONTRIBUTING.md`）。

---

## ★ 一個實跑撞到的坑（E1）

**`description` 內不得出現「冒號＋空白」。**

寫英文或西班牙文的時候很容易寫出 `in one pass: reconnaissance, refinement…`。
那一行是 YAML 的 plain scalar，**冒號加空白會被解析成 mapping**，於是：

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**整段 frontmatter 一起壞掉**——不只是 description，`x-aitokenking` 與 `x-devskills`
也一併讀不到。**而寬鬆一點的解析器不會報錯，它會安靜地把值截斷。**

這是本 repo 最貴的那一類失敗：**錯了不會報錯。**
所以 `validate_skill.py` 用 `I18N-4` 把它擋成 BLOCK。
中文全形冒號「：」不受影響，可以照用。

---

## 檢核級別

| 代碼 | 級別 | 條件 |
|---|---|---|
| `I18N-1` | **WARN** | 缺 `x-i18n` 區塊，或 description 缺某個語言標記 |
| `I18N-2` | **BLOCK** | `x-i18n.languages` 宣告了某語言，但 description 找不到它的標記；或語言碼不在支援清單；或 `languages` 留白 |
| `I18N-3` | WARN | description 有某個標記，但 `x-i18n.languages` 沒宣告它 |
| `I18N-4` | **BLOCK** | description 含「冒號＋空白」——會讓整段 frontmatter 靜默壞掉 |

**為什麼 `I18N-2` 是 BLOCK 而 `I18N-1` 只是 WARN：**
與 `ADOPT-1`／`ADOPT-2` 同一條理由——**缺漏是還沒寫，填錯是宣告不實。**
一支只寫了中文的 skill 只是還沒國際化；
一支宣告 `es` 卻沒有西班牙文的 skill，**會讓「已支援西班牙文」出現在索引裡，而那是假的。**

---

## 驗證

```bash
python3 scripts/test_validate.py         # 先跑：檢核器自己的回歸測試
python3 scripts/validate_skill.py --all  # 再跑：三嵌入點 ＋ 交接契約 ＋ 多語宣告
```
