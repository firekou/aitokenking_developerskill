#!/usr/bin/env python3
"""check_orchestration.py 的回歸測試。

★ 為什麼這個檔案必須存在：理由與 test_validate.py 一模一樣 ——
   一把壞掉的尺，量什麼都會過。編排契約的檢核尤其危險，因為它擋的是
   「沒有停止條件的鏈」與「扣費工具進白名單」這兩件事，
   而這兩件事壞掉的時候都不會有錯誤訊息，只會有帳單。

   test_ruler_actually_measured 專門防「掃到 0 份」看起來像全部通過。
"""
import sys
import copy
import tempfile
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_orchestration as C  # noqa: E402
import validate_skill as V       # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

GOOD_ORCH = {
    "case_id": "CASE-001",
    "spec": "cases/CASE-001/spec.yaml",
    "route": "B",
    "dry_run": False,
    "orchestrator": {
        "provider": "vendor-a", "model": "a-large",
        "selection_reason": "context_window 最大，要一次持有全部交棒產物",
    },
    "workers": [
        {"role": "code_generation", "provider": "vendor-a", "model": "a-small",
         "selection_reason": "單價最低且支援 function calling", "tool": "chat_completion"},
        {"role": "peer_review", "provider": "vendor-b", "model": "b-large",
         "selection_reason": "跨供應商互審", "tool": "create_message"},
    ],
    "steps": [
        {"id": "S-01", "title": "產出草稿", "worker": "code_generation",
         "input": "cases/CASE-001/spec.yaml", "output": "cases/CASE-001/draft.md",
         "done_when": "draft.md 存在且逐條回應驗收條件"},
    ],
    "triggers": [{"when": "parse_failed == true", "then": "retry_with: peer_review"}],
    "limits": {"max_rounds": 2, "budget_calls": 6, "stop_on": ["no_progress", "any_4xx"]},
    "review": {"status": "DUAL_VENDOR", "disagreements": []},
    "chain_log": "cases/CASE-001/chain-log.md",
    "cost": {"measurement_state": "unmeasured", "value": "未量測",
             "method": "get_balance 前後相減"},
    "terminated_by": "completed",
    "evidence": "E5",
    "open_questions": [],
}

GOOD_CONN = {
    "id": "demo",
    "name": "Demo MCP",
    "transport": "http",
    "url": "https://example.invalid/mcp",
    "auth": {"X-Api-Key": "${DEMO_API_KEY}"},
    "layers": ["L1"],
    "forbidden_layers": ["L5"],
    "tools_readonly": ["list_models"],
    "tools_billable": ["chat_completion"],
    "permissions_allow": ["mcp__demo__list_models"],
    "writes": False,
    "evidence": "E2",
    "source": "https://example.invalid/docs",
    "checked_at": "2026-09-01",
}

_results = []


def t(name):
    def deco(fn):
        _results.append((name, fn))
        return fn
    return deco


def _codes(findings):
    return ([x.code for x in findings if x.level == "BLOCK"],
            [x.code for x in findings if x.level == "WARN"])


def orch(**over):
    d = copy.deepcopy(GOOD_ORCH)
    for k, v in over.items():
        d[k] = v
    return _codes(C.check_orchestration(d))


def conn(**over):
    d = copy.deepcopy(GOOD_CONN)
    for k, v in over.items():
        d[k] = v
    return _codes(C.check_connector(d))


# ───────────────────────────── 編排契約 ORCH-* ─────────────────────────────

@t("完整的編排契約應完全通過")
def _():
    b, w = orch()
    assert b == [] and w == [], (b, w)


@t("缺必填欄位必須 BLOCK（ORCH-1）")
def _():
    b, _w = orch(steps=[])
    assert "ORCH-1" in b, b


@t("route 值域錯誤必須 BLOCK（ORCH-1）")
def _():
    b, _w = orch(route="D")
    assert "ORCH-1" in b, b


@t("worker 綁到非 B 組工具必須 BLOCK —— worker 一定是生成類呼叫")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["workers"][0]["tool"] = "list_models"
    b, _w = _codes(C.check_orchestration(d))
    assert "ORCH-1" in b, b


@t("★ 缺 max_rounds 必須 BLOCK —— 沒有上限的鏈不會 crash，它會一直扣錢")
def _():
    b, _w = orch(limits={"budget_calls": 6, "stop_on": ["no_progress"]})
    assert "ORCH-3" in b, b


@t("★ 缺 budget_calls 必須 BLOCK")
def _():
    b, _w = orch(limits={"max_rounds": 2, "stop_on": ["no_progress"]})
    assert "ORCH-3" in b, b


@t("★ stop_on 留白必須 BLOCK —— 你只有「跑完」一種結局")
def _():
    b, _w = orch(limits={"max_rounds": 2, "budget_calls": 6, "stop_on": []})
    assert "ORCH-3" in b, b


@t("max_rounds 為 0 必須 BLOCK")
def _():
    b, _w = orch(limits={"max_rounds": 0, "budget_calls": 6, "stop_on": ["x"]})
    assert "ORCH-3" in b, b


@t("★ 成本寫 0 而非 not_applicable 必須 BLOCK —— 0 看起來像量測結果")
def _():
    b, _w = orch(cost={"measurement_state": "unmeasured", "value": 0})
    assert "ORCH-4" in b, b


@t("一次都沒呼叫（not_applicable）寫 0 是合法的 —— 全集群唯二可以誠實寫 0 的地方")
def _():
    b, _w = orch(cost={"measurement_state": "not_applicable", "value": 0})
    assert b == [], b


@t("宣告 measured 卻寫「未量測」必須 BLOCK —— 宣告與事實不符")
def _():
    b, _w = orch(cost={"measurement_state": "measured", "value": "未量測"})
    assert "ORCH-4" in b, b


@t("宣告 unmeasured 卻填了數字必須 BLOCK")
def _():
    b, _w = orch(cost={"measurement_state": "unmeasured", "value": 3.5})
    assert "ORCH-4" in b, b


@t("cost.measurement_state 值域錯誤必須 BLOCK")
def _():
    b, _w = orch(cost={"measurement_state": "estimated", "value": "未量測"})
    assert "ORCH-4" in b, b


@t("★ 拿模型自評 confidence 當唯一閘門必須 BLOCK —— E5 且跨供應商不可比")
def _():
    b, _w = orch(triggers=[{"when": "confidence < 0.8", "then": "trigger debate"}])
    assert "ORCH-5" in b, b


@t("confidence 再 AND 一個可檢核訊號就放行 —— 不是不能用，是不能單獨用")
def _():
    b, _w = orch(triggers=[{"when": "confidence < 0.8 AND parse_failed == true",
                            "then": "escalate_to_human"}])
    assert b == [], b


@t("★ route B 但沒有 peer_review 角色必須 BLOCK —— 這條鏈沒有第二個腦袋")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["workers"] = [d["workers"][0]]
    d["review"] = {"status": "NOT_REVIEWED"}
    b, _w = _codes(C.check_orchestration(d))
    assert "ORCH-2" in b, b


@t("★ 宣告 DUAL_VENDOR 但審模型同一家必須 BLOCK —— 隱瞞降級才是錯誤")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["workers"][1]["provider"] = "vendor-a"
    b, _w = _codes(C.check_orchestration(d))
    assert "ORCH-2" in b, b


@t("同一家但誠實標 SINGLE_VENDOR 就放行 —— 降級不是錯誤")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["workers"][1]["provider"] = "vendor-a"
    d["review"] = {"status": "SINGLE_VENDOR", "disagreements": []}
    b, _w = _codes(C.check_orchestration(d))
    assert b == [], b


@t("review.status 值域錯誤必須 BLOCK")
def _():
    b, _w = orch(review={"status": "REVIEWED"})
    assert "ORCH-2" in b, b


@t("★ evidence 標 E1 卻沒有 chain_log 必須 BLOCK —— 沒有紀錄的實跑跟沒跑過長得一樣")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["evidence"] = "E1"
    del d["chain_log"]
    b, _w = _codes(C.check_orchestration(d))
    assert "ORCH-6" in b, b


@t("★ dry_run 乾跑卻宣告 E1 必須 BLOCK —— 乾跑的產物是假設")
def _():
    b, _w = orch(dry_run=True, evidence="E1")
    assert "ORCH-6" in b, b


@t("model 還是佔位字串應 WARN（不擋，但要看得出來還沒填實）")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["orchestrator"]["model"] = "<model-id>"
    _b, w = _codes(C.check_orchestration(d))
    assert "ORCH-W2" in w, w


@t("selection_reason 寫「比較強」應 WARN —— 印象會過期，判準不會")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["orchestrator"]["selection_reason"] = "這支比較強"
    _b, w = _codes(C.check_orchestration(d))
    assert "ORCH-W1" in w, w


@t("交棒交的是對話而不是產物應 WARN")
def _():
    d = copy.deepcopy(GOOD_ORCH)
    d["steps"][0]["input"] = "上一輪的對話內容"
    _b, w = _codes(C.check_orchestration(d))
    assert "ORCH-W5" in w, w


# ─────────────────────────── connector 宣告 CONN-* ───────────────────────────

@t("完整的 connector 宣告應完全通過")
def _():
    b, w = conn()
    assert b == [] and w == [], (b, w)


@t("★ 金鑰寫成本體而不是 ${ENV_VAR} 必須 BLOCK —— 入庫即視為外洩")
def _():
    b, _w = conn(auth={"X-Api-Key": "sk-live-abc123"})
    assert "CONN-2" in b, b


@t("★ writes: true 卻沒有 rollback 必須 BLOCK")
def _():
    b, _w = conn(writes=True)
    assert "CONN-3" in b, b


@t("writes: true 且寫得出 rollback 就放行")
def _():
    b, _w = conn(writes=True, rollback="改動前 git switch -c；還原 git restore；已送出的請求收不回")
    assert b == [], b


@t("★ 扣費工具出現在 permissions_allow 必須 BLOCK —— 機器可擬不可動錢")
def _():
    b, _w = conn(permissions_allow=["mcp__demo__list_models", "mcp__demo__chat_completion"])
    assert "CONN-4" in b, b


@t("同一支工具同時列為唯讀與扣費必須 BLOCK —— 宣告自相矛盾")
def _():
    b, _w = conn(tools_readonly=["list_models", "chat_completion"])
    assert "CONN-4" in b, b


@t("transport: stdio 卻沒有 command 必須 BLOCK")
def _():
    b, _w = conn(transport="stdio", url=None, command=None)
    assert "CONN-1" in b, b


@t("layers 出現未知層別必須 BLOCK")
def _():
    b, _w = conn(layers=["L9"])
    assert "CONN-1" in b, b


@t("缺 writes 必須 BLOCK —— 判不出來要填 true，不是留白")
def _():
    d = copy.deepcopy(GOOD_CONN)
    del d["writes"]
    b, _w = _codes(C.check_connector(d))
    assert "CONN-1" in b, b


@t("缺 checked_at 應 WARN —— 沒標時間的事實三週後沒有人知道還算不算數")
def _():
    d = copy.deepcopy(GOOD_CONN)
    del d["checked_at"]
    _b, w = _codes(C.check_connector(d))
    assert "CONN-W1" in w, w


# ─────────────────────────── 跨檔案漂移（repo 級）───────────────────────────

@t("★ 扣費工具清單必須與 validate_skill.py 同一份事實")
def _():
    assert C.BILLABLE_TOOLS == V.BILLABLE_TOOLS, (
        f"兩支檢核器對「哪些工具會扣費」的認知已經漂移："
        f"{C.BILLABLE_TOOLS ^ V.BILLABLE_TOOLS}")


@t("★ aitokenking connector 的白名單必須與 .claude/settings.json 一致")
def _():
    import json
    import yaml
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    declared = set(settings.get("permissions", {}).get("allow", []))
    doc = yaml.safe_load((ROOT / "tools" / "aitokenking.connector.yaml").read_text(encoding="utf-8"))
    manifest = set(doc.get("permissions_allow") or [])
    assert declared == manifest, (
        f"宣告與實際設定漂移 —— 只在其中一邊的項目：{declared ^ manifest}")


@t("★ repo 內既有的編排契約與 connector 必須全數無 BLOCK")
def _():
    targets = C.collect_all()
    assert targets, "掃到 0 份。這不是通過 —— 掃不到檔案的檢核器跟全部通過長得一模一樣。"
    assert C.main(["--all"]) == 0, "repo 內既有檔案未全數通過"


@t("★ 尺必須真的量到東西 —— 掃到 0 份不得看起來像全部通過")
def _():
    assert C.main([]) == 2, "掃到 0 份時必須回 2（不是 0）"


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
