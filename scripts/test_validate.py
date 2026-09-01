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
description: 一支示範用的 skill，觸發條件寫滿。 [EN] A demo skill with its trigger phrases spelled out. [ES] Una skill de demostración con sus frases de activación. [ZH-HANS] 一支示范用的 skill，触发条件写满。
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
  adoption_stage: workflow
  primary_surface: mcp
  success_signal: value_activation
  retention_signal: 下一個 CASE 直接沿用同一份 gateway 設定
x-devskills:
  layer: L2
  handoff_in: cases/<CASE>/baseline.md
  handoff_out: cases/<CASE>/spec.yaml
  gate: 驗收條件逐條可執行，且非目標欄位非空
  mutates: false
x-i18n:
  languages: [zh-Hant, en, es, zh-Hans]
  primary: zh-Hant
  note: 四語觸發語內嵌在 description
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


# ─────────────── Adoption Contract ADOPT-*（回應 review DEV-GROWTH-002）───────────────

@t("adoption contract 缺欄位只 WARN —— v1 給既有 skill 遷移期")
def _():
    b, w = run(GOOD_FM.replace("  adoption_stage: workflow\n", ""), GOOD_BODY)
    assert b == [] and "ADOPT-1" in w, (b, w)


@t("★ adoption_stage 值域錯誤必須 BLOCK —— 缺漏是還沒寫，填錯是宣告不實")
def _():
    b, _w = run(GOOD_FM.replace("adoption_stage: workflow", "adoption_stage: growth"), GOOD_BODY)
    assert "ADOPT-2" in b, b


@t("primary_surface 值域錯誤必須 BLOCK")
def _():
    b, _w = run(GOOD_FM.replace("primary_surface: mcp", "primary_surface: grpc"), GOOD_BODY)
    assert "ADOPT-2" in b, b


@t("success_signal 值域錯誤必須 BLOCK")
def _():
    b, _w = run(GOOD_FM.replace("success_signal: value_activation",
                                "success_signal: it_works"), GOOD_BODY)
    assert "ADOPT-2" in b, b


@t("★ 會扣費卻宣告 connectivity_activation 必須 BLOCK —— 裝好了不等於用過")
def _():
    # 把 list_models 成功當成採用，是這套東西最容易騙到自己的地方：
    # 它會讓「所有人都裝好、沒有人跑過」看起來像成功。
    fm = (GOOD_FM.replace("tools_used: [list_models]", "tools_used: [chat_completion]")
                 .replace("billable: false", "billable: true")
                 .replace("success_signal: value_activation",
                          "success_signal: connectivity_activation"))
    body = GOOD_BODY.replace("## 內容", "## 內容\n這一步會扣額度。")
    b, _w = run(fm, body)
    assert "ADOPT-2" in b, b


@t("缺 retention_signal 只 WARN")
def _():
    b, w = run(GOOD_FM.replace(
        "  retention_signal: 下一個 CASE 直接沿用同一份 gateway 設定\n", ""), GOOD_BODY)
    assert b == [] and "ADOPT-1" in w, (b, w)


@t("primary_surface: none 卻列了工具 → WARN（宣告與事實不一致）")
def _():
    b, w = run(GOOD_FM.replace("primary_surface: mcp", "primary_surface: none"), GOOD_BODY)
    assert b == [] and "ADOPT-3" in w, (b, w)


@t("純本機層：primary_surface none ＋ tools_used 空 ＋ success_signal none → 全通過")
def _():
    fm = (GOOD_FM.replace("role: required", "role: optional")
                 .replace("tools_used: [list_models]", "tools_used: []")
                 .replace("primary_surface: mcp", "primary_surface: none")
                 .replace("success_signal: value_activation", "success_signal: none"))
    b, w = run(fm, GOOD_BODY)
    assert b == [] and w == [], (b, w)


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


@t("★ 兩階段啟用說明必須出現在每一支 skill 的 §0（canonical 對齊）")
def _():
    # DEV-GROWTH-005：把 list_models 成功等同於產品採用，是最容易騙到自己的地方。
    # 這條測試防的是「canonical 改了，但 skill 沒跟著改」這種安靜的漂移。
    missing = [p.parent.name for p in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
               if "連通性啟用" not in p.read_text(encoding="utf-8")
               or "價值啟用" not in p.read_text(encoding="utf-8")]
    assert not missing, f"這些 skill 的 §0 沒有兩階段啟用：{missing}"


@t("★ MCP／API surface 分流表必須出現在每一支 skill 的 §0")
def _():
    missing = [p.parent.name for p in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
               if "先選 surface" not in p.read_text(encoding="utf-8")]
    assert not missing, f"這些 skill 的 §0 沒有 surface 分流：{missing}"


# ───────────────────────── 多語描述 I18N-*（templates/i18n-block.md）─────────────────────────

@t("缺 x-i18n 區塊應 WARN —— 缺漏是還沒寫，不擋")
def _():
    fm = GOOD_FM.replace("x-i18n:\n  languages: [zh-Hant, en, es, zh-Hans]\n"
                         "  primary: zh-Hant\n  note: 四語觸發語內嵌在 description\n", "")
    b, w = run(fm, GOOD_BODY)
    assert b == [] and "I18N-1" in w, (b, w)


@t("★ 宣告了 es 但 description 沒有 [ES] 段必須 BLOCK —— 填錯是宣告不實")
def _():
    fm = GOOD_FM.replace(" [ES] Una skill de demostración con sus frases de activación.", "")
    b, _w = run(fm, GOOD_BODY)
    assert "I18N-2" in b, b


@t("description 有 [ES] 但 languages 沒宣告應 WARN")
def _():
    fm = GOOD_FM.replace("languages: [zh-Hant, en, es, zh-Hans]", "languages: [zh-Hant, en, zh-Hans]")
    b, w = run(fm, GOOD_BODY)
    assert b == [] and "I18N-3" in w, (b, w)


@t("languages 出現未支援的語言碼必須 BLOCK —— 改規則是提案，繞規則是欺騙")
def _():
    fm = GOOD_FM.replace("languages: [zh-Hant, en, es, zh-Hans]",
                         "languages: [zh-Hant, en, es, zh-Hans, klingon]")
    b, _w = run(fm, GOOD_BODY)
    assert "I18N-2" in b, b


@t("x-i18n.languages 留白必須 BLOCK")
def _():
    fm = GOOD_FM.replace("languages: [zh-Hant, en, es, zh-Hans]", "languages: []")
    b, _w = run(fm, GOOD_BODY)
    assert "I18N-2" in b, b


@t("★ description 含半形冒號＋空白必須 BLOCK —— 整段 frontmatter 會靜默壞掉（E1 實跑撞到）")
def _():
    fm = GOOD_FM.replace("[EN] A demo skill with", "[EN] A demo skill: with")
    b, _w = run(fm, GOOD_BODY)
    assert "I18N-4" in b, b


@t("全形冒號不受影響 —— 中文描述照常寫得下去")
def _():
    fm = GOOD_FM.replace("一支示範用的 skill，觸發條件寫滿。", "一支示範用的 skill：觸發條件寫滿。")
    b, _w = run(fm, GOOD_BODY)
    assert "I18N-4" not in b, b


@t("★ 全部 skill 的 description 都必須帶齊 [EN]／[ES]／[ZH-HANS] 三個標記")
def _():
    missing = {}
    for p in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md")):
        desc = next(l for l in p.read_text(encoding="utf-8").split("\n")
                    if l.startswith("description: "))
        lack = [m for m in ("[EN]", "[ES]", "[ZH-HANS]") if m not in desc]
        if lack:
            missing[p.parent.name] = lack
    assert not missing, f"這些 skill 的 description 少了語言段：{missing}"


@t("★ 全部 skill 都必須有 x-i18n 宣告區塊")
def _():
    missing = [p.parent.name for p in sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
               if V.parse_block(V.split_frontmatter(p.read_text(encoding="utf-8"))[0],
                                "x-i18n") is None]
    assert not missing, f"這些 skill 缺 x-i18n：{missing}"


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
