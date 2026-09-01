# tools/ —— MCP connector 宣告目錄

**這裡放的是「哪一個 MCP、可以被哪一層調閱、會不會動到你的東西」的機器可讀宣告。**
一個檔案一個 connector，命名 `<id>.connector.yaml`，schema 見
[`schemas/mcp-connector.schema.yaml`](../schemas/mcp-connector.schema.yaml)。

```bash
python3 scripts/check_orchestration.py --all      # 檢核 tools/ 與 cases/ 的編排產物
```

---

## 為什麼這個目錄不是「愈多愈好」

[`references/mcp-inventory.md`](../references/mcp-inventory.md) §1 的立場沒有變：
**每多一個 MCP，agent 的工具清單就長一截，而工具愈多，選錯的機率愈高。**

所以這個目錄的用途不是收集 connector，是**把「這個 MCP 該給誰用」寫成擋得住的規則**。
`.mcp.json` 仍然只宣告 `aitokenking`；這裡的其他檔案是**你自己決定要不要接**的候選。

**加一份宣告之前先回答 `mcp-inventory.md` §4 那三題**——
「哪一層需要它、它會不會寫入、金鑰怎麼放」。答不出第一題就先不要加。

---

## 三條由檢核器擋住的規則

| | 規則 | 對應鐵律 |
|---|---|---|
| `CONN-2` | `auth` 的值一律 `${ENV_VAR}` 參照 | 鐵律 1 · **金鑰不入庫。入庫即視為外洩，只能輪替** |
| `CONN-3` | `writes: true` 必須寫得出 `rollback` | 鐵律 4 · 會動別人的東西就要寫怎麼還原 |
| `CONN-4` | B 組扣費工具不得出現在 `permissions_allow` | 鐵律 2 · **機器可擬不可動錢** |

**`CONN-4` 為什麼是 BLOCK 而不是建議：**
把生成類工具加進白名單的那一刻，「每次停下來看一眼」這個機制就消失了，
而**它消失的時候不會有任何錯誤訊息**——你會在對帳時才知道。

---

## 貢獻一份 connector 宣告

```bash
cp tools/aitokenking.connector.yaml tools/<你的>.connector.yaml
# 改完之後
python3 scripts/check_orchestration.py tools/<你的>.connector.yaml
```

**兩件會被退回的事：**

1. **`evidence` 標成 E1 但你沒接起來跑過。**
   讀官方文件寫出來的是 **E2**。**接起來實際呼叫過一次，貼得出回應，才是 E1。**
2. **`writes` 填 false 只因為「它主要是拿來讀的」。**
   判準是**它有沒有寫入能力**，不是你打算怎麼用它。**判不出來就填 true。**

**最有價值的貢獻不是多一個 connector，是一份「我接起來跑過，這裡會壞」的宣告。**
`notes` 欄位就是留給那句話的。
