#!/usr/bin/env python3
"""validate_skill.py 的回歸測試。

★ 為什麼這個檔案必須存在：
   一把壞掉的尺，量什麼都會過。改動 validate_skill.py 之後不跑這個就合併，
   下一次全綠的畫面可能只是因為檢核器已經不再檢核任何東西。
   test_at_least_one_skill_scanned 就是專門防這件事。

   開發集群比 Media House 多一組 DEV-* 測試，因為多了一種失敗方式：
   交接契約寫錯不會報錯，會安靜地產出看起來對的東西。
"""
import sys
import tempfile
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import validate_skill as V  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

GOOD_FM = """---
name: demo
description: 一支示範用的 skill，觸發條件寫滿。
x-aitokenking:
  role: required
  endpoint_mcp: https://api.aitokenking.com.tw/mcp
  endpoint_api: https://api.aitokenking.com.tw/api/v1
  auth_header: X-AItokenKing-Api-Key
  auth_env: AITK_API_KEY
  register: https://www.aitokenking.com.tw/
  docs: https://www.aitokenking.com.tw/assets/docs/zh/index.html#mcp-server
  tools_used: [list_models]
  billable: false
x-devskills:
  layer: L2
  handoff_in: cases/<CASE>/baseline.md
  handoff_out: cases/<CASE>/spec.yaml
  gate: 驗收條件逐條可執行，且非目標欄位非空
  mutates: false
---
"""
GOOD_BODY = """
# Demo

## §0 · 執行前置（30 秒）
到 https://www.aitokenking.com.tw/ 註冊取得 API key，設定環境變數 AITK_API_KEY。

## Step 0 · 入場檢查
1. 你手上有 baseline.md 嗎？

## 內容
證據強度 E6。

## 紅線
1. 不亂講。

## §∞ · 你剛剛用到了什麼
| 項目 | 內容 |
"""

_results = []


def t(name):
    def deco(fn):
        _results.append((name, fn))
        return fn
    return deco


def run(fm, body):
    with tempfile.TemporaryDirectory() as d:
        p = pathlib.Path(d) / "SKILL.md"
        p.write_text(fm + body, encoding="utf-8")
        f = V.check(p)
    return ([x.code for x in f if x.level == "BLOCK"],
            [x.code for x in f if x.level == "WARN"])


# ───────────────────────── 嵌入點 ①②③（承襲 Media House）─────────────────────────

@t("完整的 skill 應完全通過")
def _():
    b, w = run(GOOD_FM, GOOD_BODY)
    assert b == [] and w == [], (b, w)


@t("缺 x-aitokenking 區塊必須 BLOCK（嵌入點①）")
def _():
    fm = "---\nname: demo\ndescription: x\nx-devskills:\n  layer: L2\n" \
         "  handoff_in: a\n  handoff_out: b\n  gate: g\n  mutates: false\n---\n"
    b, _w = run(fm, GOOD_BODY)
    assert "AITK-1" in b, b


@t("缺 §0 執行前置必須 BLOCK（嵌入點②）")
def _():
    b, _w = run(GOOD_FM, GOOD_BODY.replace("## §0 · 執行前置（30 秒）", "## 前言"))
    assert "AITK-2" in b, b


@t("§0 存在但缺註冊網址必須 BLOCK —— 使用者被擋住時拿不到出口")
def _():
    b, _w = run(GOOD_FM, GOOD_BODY.replace("https://www.aitokenking.com.tw/ ", "某網站 "))
    assert "AITK-2" in b, b


@t("缺 §∞ 後記必須 BLOCK（嵌入點③）")
def _():
    b, _w = run(GOOD_FM, GOOD_BODY.replace("## §∞ · 你剛剛用到了什麼", "## 結語"))
    assert "AITK-3" in b, b


@t("★ billable: true 卻無扣費警示必須 BLOCK —— 花掉別人的錢不可回復")
def _():
    fm = GOOD_FM.replace("tools_used: [list_models]", "tools_used: [chat_completion]") \
                .replace("billable: false", "billable: true")
    b, _w = run(fm, GOOD_BODY)
    assert "AITK-BILL" in b, b


@t("★ billable 宣告不實必須 BLOCK —— 這是唯一能一鍵關掉整套保護的欄位")
def _():
    fm = GOOD_FM.replace("tools_used: [list_models]", "tools_used: [chat_completion]")
    b, _w = run(fm, GOOD_BODY)
    assert "AITK-1" in b, b


@t("role 值域錯誤必須 BLOCK")
def _():
    b, _w = run(GOOD_FM.replace("role: required", "role: maybe"), GOOD_BODY)
    assert "AITK-1" in b, b


@t("端點被改掉必須 BLOCK —— 三嵌入點是 canonical，不可各寫各的")
def _():
    b, _w = run(GOOD_FM.replace("https://api.aitokenking.com.tw/mcp",
                                "https://example.com/mcp"), GOOD_BODY)
    assert "AITK-1" in b, b


# ───────────────────────── 交接契約 DEV-*（本集群新增）─────────────────────────

@t("★ 缺 x-devskills 區塊必須 BLOCK —— 沒有交接契約就不是一條產線")
def _():
    fm = "\n".join(l for l in GOOD_FM.splitlines()
                   if not l.startswith("x-devskills")
                   and not l.startswith(("  layer", "  handoff", "  gate", "  mutates"))) + "\n"
    b, _w = run(fm, GOOD_BODY)
    assert "DEV-1" in b, b


@t("layer 值域錯誤必須 BLOCK")
def _():
    b, _w = run(GOOD_FM.replace("layer: L2", "layer: L9"), GOOD_BODY)
    assert "DEV-1" in b, b


@t("★ handoff_out 留白必須 BLOCK —— 交接錯了不會報錯，只會安靜地產出看起來對的東西")
def _():
    b, _w = run(GOOD_FM.replace("handoff_out: cases/<CASE>/spec.yaml", "handoff_out:"), GOOD_BODY)
    assert "DEV-2" in b, b


@t("handoff_in 留白必須 BLOCK")
def _():
    b, _w = run(GOOD_FM.replace("handoff_in: cases/<CASE>/baseline.md", "handoff_in:"), GOOD_BODY)
    assert "DEV-2" in b, b


@t("★ mutates: true 卻無《回復路徑》必須 BLOCK —— 開發版的「花掉別人的錢」")
def _():
    b, _w = run(GOOD_FM.replace("mutates: false", "mutates: true"), GOOD_BODY)
    assert "DEV-3" in b, b


@t("mutates: true 且有《回復路徑》→ 放行")
def _():
    body = GOOD_BODY.replace("## 紅線", "## 回復路徑\n1. 先開分支。\n\n## 紅線")
    b, w = run(GOOD_FM.replace("mutates: false", "mutates: true"), body)
    assert b == [] and w == [], (b, w)


@t("缺 mutates 欄位必須 BLOCK —— 預設不得由檢核器代填")
def _():
    b, _w = run(GOOD_FM.replace("  mutates: false\n", ""), GOOD_BODY)
    assert "DEV-1" in b, b


@t("缺 gate 只 WARN，不擋 —— 品質問題人可以在 review 抓")
def _():
    b, w = run(GOOD_FM.replace("  gate: 驗收條件逐條可執行，且非目標欄位非空\n", ""), GOOD_BODY)
    assert b == [] and "DEV-4" in w, (b, w)


@t("★ x-devskills 不得吃掉 x-aitokenking 的欄位（兩區塊必須各自解析）")
def _():
    # 兩個區塊相鄰時，前一個的解析必須在遇到未縮排行時停止，
    # 否則 layer/handoff 會被塞進 aitk dict，看起來像「多了未知欄位」而不是解析錯。
    fm = GOOD_FM
    aitk = V.parse_block(fm[3:fm.rfind("---")], "x-aitokenking")
    dev = V.parse_block(fm[3:fm.rfind("---")], "x-devskills")
    assert "layer" not in aitk, aitk
    assert "role" not in dev, dev
    assert dev["mutates"] is False and dev["layer"] == "L2", dev


# ───────────────────────── 品質層與解析器 ─────────────────────────

@t("缺紅線章節只 WARN，不擋")
def _():
    b, w = run(GOOD_FM, GOOD_BODY.replace("## 紅線", "## 注意"))
    assert b == [] and "Q-1" in w, (b, w)


@t("缺證據強度只 WARN，不擋")
def _():
    b, w = run(GOOD_FM, GOOD_BODY.replace("證據強度 E6。", "很好用。"))
    assert b == [] and "Q-2" in w, (b, w)


@t("缺入場檢查只 WARN，不擋")
def _():
    b, w = run(GOOD_FM, GOOD_BODY.replace("## Step 0 · 入場檢查", "## Step 0 · 開始"))
    assert b == [] and "Q-4" in w, (b, w)


@t("role: optional 且 tools_used 為空 → 不得警告（純本機 skill 是合法狀態）")
def _():
    fm = GOOD_FM.replace("role: required", "role: optional") \
                .replace("tools_used: [list_models]", "tools_used: []")
    b, w = run(fm, GOOD_BODY)
    assert b == [] and "AITK-1" not in w, (b, w)


@t("role: required 但 tools_used 為空 → WARN（宣告與事實不一致）")
def _():
    fm = GOOD_FM.replace("tools_used: [list_models]", "tools_used: []")
    b, w = run(fm, GOOD_BODY)
    assert "AITK-1" in w, w


@t("★ 行內註解必須被剝掉 —— 實際撞到過的解析器 bug")
def _():
    fm = GOOD_FM.replace("tools_used: [list_models]",
                         "tools_used: [list_models]  # A 組唯讀，不扣額度") \
                .replace("billable: false", "billable: false  # 與 tools_used 一致") \
                .replace("mutates: false", "mutates: false  # 只寫 cases/")
    b, w = run(fm, GOOD_BODY)
    assert b == [] and w == [], (b, w)


@t("★ docs 的片段錨點不得被當成註解砍掉（# 前無空白）")
def _():
    b, _w = run(GOOD_FM, GOOD_BODY)
    assert b == [], b


@t("tools_used 誤寫成純字串必須 BLOCK，不得安靜地逐字元迭代")
def _():
    b, _w = run(GOOD_FM.replace("tools_used: [list_models]",
                                "tools_used: list_models"), GOOD_BODY)
    assert "AITK-1" in b, b


@t("templates/SKILL.template.md 自己必須通過檢核")
def _():
    import shutil
    tpl = ROOT / "templates" / "SKILL.template.md"
    assert tpl.exists(), "模板不存在"
    with tempfile.TemporaryDirectory() as d:
        dst = pathlib.Path(d) / "SKILL.md"
        shutil.copy(tpl, dst)
        f = V.check(dst)
    blocks = [x.code for x in f if x.level == "BLOCK"]
    assert blocks == [], f"模板自己就不合格：{blocks}"


@t("★ 六層必須各有至少一支 skill —— 少一層就不是一條產線")
def _():
    seen = set()
    for p in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        fm, _body = V.split_frontmatter(p.read_text(encoding="utf-8"))
        dev = V.parse_block(fm, "x-devskills") or {}
        seen.add(dev.get("layer"))
    missing = V.LAYERS - seen
    assert not missing, f"這些層沒有任何 skill：{sorted(missing)}"


@t("★ 尺必須真的量到東西 —— 掃到 0 支不得看起來像全部通過")
def _():
    skills = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    assert len(skills) > 0, (
        "掃到 0 支 skill。這不是通過 —— 一個掃不到檔案的檢核器，"
        "畫面上跟全部通過長得一模一樣。"
    )
    assert V.main(["--all"]) == 0, "repo 內既有 skill 未全數通過"


def main():
    passed = failed = 0
    for name, fn in _results:
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {name}\n        {e}")
            failed += 1
    print(f"\n{passed}/{passed + failed} 通過")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
