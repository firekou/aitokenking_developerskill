#!/usr/bin/env python3
"""編排契約 ＋ MCP connector 宣告檢核器。

單一事實來源：
  schemas/orchestration.schema.yaml    cases/<CASE>/orchestration.yaml → ORCH-* 檢核
  schemas/mcp-connector.schema.yaml    tools/*.connector.yaml          → CONN-* 檢核

★ 為什麼要有這支：
  一份沒有人檢核的編排契約，跟一段提示詞沒有差別 —— 它會被寫得很漂亮，
  然後在跑起來的時候被忽略，而且不會有任何錯誤訊息。
  「狀態是被檢核推進的，不是被宣稱的」這句話，只有在檢核是確定性的時候才成立。

設計原則（與 validate_skill.py 一致）：
  1. BLOCK 只留給「錯了就回不去」（金鑰入庫、扣費工具進白名單、沒有停止條件的鏈）
     與「錯了不會報錯」（宣告與事實不符）這兩類。
  2. 檢核器自己壞掉時必須看起來像壞掉，不能看起來像全部通過
     —— 掃到 0 個檔案回 2，缺 PyYAML 回 2，兩者都明講「這不是通過」。

用法：
  python3 scripts/check_orchestration.py --all
  python3 scripts/check_orchestration.py cases/CASE-001/orchestration.yaml
"""
import sys
import re
from pathlib import Path

try:
    import yaml
except ImportError:                                     # pragma: no cover
    print("缺 PyYAML，無法解析編排契約。")
    print("⚠️  這不是通過，是沒有尺 —— 請先 pip install pyyaml 再跑一次。")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

ROUTES = {"A", "B", "C"}
EVIDENCE = {"E1", "E2", "E3", "E4", "E5", "E6"}
COST_STATES = {"measured", "unmeasured", "not_applicable"}
REVIEW_STATES = {"DUAL_VENDOR", "SINGLE_VENDOR", "NOT_REVIEWED"}
TERMINATED = {"completed", "max_rounds", "budget_calls", "stop_on", "error"}
LAYERS = {"L0", "L1", "L2", "L3", "L4", "L5", "orchestrator"}
TRANSPORTS = {"http", "sse", "stdio"}
# B 組：每次呼叫都實際扣帳戶額度。與 validate_skill.py 的 BILLABLE_TOOLS 同一份事實。
BILLABLE_TOOLS = {
    "chat_completion", "create_message", "create_response",
    "create_image_generation", "create_video_generation",
}
# 可檢核訊號：有實際輸出可以貼出來的那一類。confidence 這種模型自評不在裡面。
CHECKABLE_SIGNALS = (
    "parse_failed", "test_failed", "test_passed", "exit_code", "diff_items",
    "4xx", "5xx", "status_code", "schema_invalid", "timeout", "red", "green",
)
PLACEHOLDER = re.compile(r"^<.*>$")
# 「比較強」這一類講不出判準的選型理由。印象會過期，判準不會。
VAGUE_REASON = re.compile(r"比較強|最強|更好|比較聰明|效果好|表現佳|業界最")


class Finding:
    def __init__(self, level, code, msg):
        self.level, self.code, self.msg = level, code, msg

    def __str__(self):
        icon = "BLOCK" if self.level == "BLOCK" else "WARN "
        return f"  [{icon}] {self.code}  {self.msg}"


def _load(path):
    """回傳 (doc, finding)。解析失敗時 doc 為 None。"""
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        return None, Finding("BLOCK", "YAML-1", f"YAML 解析失敗：{e}")
    if not isinstance(doc, dict):
        return None, Finding("BLOCK", "YAML-1", "檔案頂層不是一個 mapping")
    return doc, None


# ───────────────────────────── 編排契約 ORCH-* ─────────────────────────────

def check_orchestration(doc):
    f = []

    # ORCH-1 骨架與值域
    for key in ("case_id", "route", "orchestrator", "workers", "steps", "limits", "cost", "evidence"):
        if doc.get(key) in (None, "", [], {}):
            f.append(Finding("BLOCK", "ORCH-1", f"缺必填欄位 `{key}`"))
    route = doc.get("route")
    if route is not None and route not in ROUTES:
        f.append(Finding("BLOCK", "ORCH-1", f"route 值域錯誤：{route!r}，須為 {sorted(ROUTES)}"))
    ev = doc.get("evidence")
    if ev is not None and ev not in EVIDENCE:
        f.append(Finding("BLOCK", "ORCH-1", f"evidence 值域錯誤：{ev!r}，須為 {sorted(EVIDENCE)}"))
    tb = doc.get("terminated_by")
    if tb is not None and tb not in TERMINATED:
        f.append(Finding("BLOCK", "ORCH-1", f"terminated_by 值域錯誤：{tb!r}，須為 {sorted(TERMINATED)}"))

    orch = doc.get("orchestrator") or {}
    providers = []
    if isinstance(orch, dict):
        for key in ("provider", "model", "selection_reason"):
            if not orch.get(key):
                f.append(Finding("BLOCK", "ORCH-1", f"orchestrator 缺 `{key}`"))
        if orch.get("provider"):
            providers.append(orch["provider"])
        if VAGUE_REASON.search(str(orch.get("selection_reason", ""))):
            f.append(Finding("WARN", "ORCH-W1",
                "orchestrator.selection_reason 講不出判準（「比較強」這一類）—— "
                "要寫命中了哪一條：context_window 最大／支援 JSON mode／單價最低"))
        if PLACEHOLDER.match(str(orch.get("model", ""))):
            f.append(Finding("WARN", "ORCH-W2",
                "orchestrator.model 還是佔位字串 —— 跑之前要換成 list_models 回應裡實際有的那一支"))

    workers = doc.get("workers") or []
    if not isinstance(workers, list) or not workers:
        f.append(Finding("BLOCK", "ORCH-1", "workers 至少要有一個"))
        workers = []
    roles = {}
    for i, w in enumerate(workers):
        if not isinstance(w, dict):
            f.append(Finding("BLOCK", "ORCH-1", f"workers[{i}] 不是 mapping"))
            continue
        for key in ("role", "provider", "model", "selection_reason", "tool"):
            if not w.get(key):
                f.append(Finding("BLOCK", "ORCH-1", f"workers[{i}] 缺 `{key}`"))
        if w.get("tool") and w["tool"] not in BILLABLE_TOOLS:
            f.append(Finding("BLOCK", "ORCH-1",
                f"workers[{i}].tool 值域錯誤：{w['tool']!r}。"
                f"worker 一定是生成類呼叫，須為 {sorted(BILLABLE_TOOLS & {'chat_completion', 'create_message', 'create_response'})}"))
        if w.get("provider"):
            providers.append(w["provider"])
        if w.get("role"):
            roles.setdefault(w["role"], []).append(w)
        if VAGUE_REASON.search(str(w.get("selection_reason", ""))):
            f.append(Finding("WARN", "ORCH-W1",
                f"workers[{i}].selection_reason 講不出判準（「比較強」這一類）"))
        if PLACEHOLDER.match(str(w.get("model", ""))):
            f.append(Finding("WARN", "ORCH-W2", f"workers[{i}].model 還是佔位字串"))

    # ORCH-2 互審必須跨供應商 —— 判準是 provider 不同，不是模型名稱不同
    review = doc.get("review") or {}
    status = review.get("status") if isinstance(review, dict) else None
    if route == "B":
        if not isinstance(review, dict) or not status:
            f.append(Finding("BLOCK", "ORCH-2", "route: B（互審鏈）但缺 review.status"))
        if "peer_review" not in roles:
            f.append(Finding("BLOCK", "ORCH-2",
                "route: B 但 workers 裡沒有 peer_review 角色 —— 這條鏈沒有第二個腦袋"))
    if status is not None and status not in REVIEW_STATES:
        f.append(Finding("BLOCK", "ORCH-2",
            f"review.status 值域錯誤：{status!r}，須為 {sorted(REVIEW_STATES)}"))
    reviewer_providers = {w.get("provider") for w in roles.get("peer_review", []) if w.get("provider")}
    other_providers = {w.get("provider") for w in workers
                       if w.get("role") != "peer_review" and w.get("provider")}
    if orch.get("provider"):
        other_providers.add(orch["provider"])
    if status == "DUAL_VENDOR":
        if not reviewer_providers:
            f.append(Finding("BLOCK", "ORCH-2",
                "review.status 宣告 DUAL_VENDOR 但沒有 peer_review worker —— 宣告與事實不符"))
        elif reviewer_providers <= other_providers:
            f.append(Finding("BLOCK", "ORCH-2",
                f"review.status 宣告 DUAL_VENDOR，但審模型的 provider {sorted(reviewer_providers)} "
                f"與主線 {sorted(other_providers)} 是同一家。同家的兩支盲點是同一組 —— "
                "這要標 SINGLE_VENDOR。降級不是錯誤，隱瞞降級才是。"))

    # ORCH-3 停止條件 —— 這一層版本的「錯了就回不去」
    limits = doc.get("limits") or {}
    if not isinstance(limits, dict):
        limits = {}
    for key in ("max_rounds", "budget_calls"):
        v = limits.get(key)
        if v is None:
            f.append(Finding("BLOCK", "ORCH-3",
                f"limits 缺 `{key}` —— 沒有上限的鏈不會 crash，它會一直跑，"
                "而且每一輪都在扣額度"))
        elif not isinstance(v, int) or isinstance(v, bool) or v < 1:
            f.append(Finding("BLOCK", "ORCH-3", f"limits.{key} 須為 >= 1 的整數，實得 {v!r}"))
    stop_on = limits.get("stop_on")
    if not stop_on or not isinstance(stop_on, list):
        f.append(Finding("BLOCK", "ORCH-3",
            "limits.stop_on 缺漏或留白 —— 你只有「跑完」一種結局"))

    # ORCH-4 成本 —— 0 看起來像量測結果，「未量測」才是事實
    cost = doc.get("cost") or {}
    if not isinstance(cost, dict):
        cost = {}
    state = cost.get("measurement_state")
    value = cost.get("value")
    if state is None:
        f.append(Finding("BLOCK", "ORCH-4", "cost 缺 `measurement_state`"))
    elif state not in COST_STATES:
        f.append(Finding("BLOCK", "ORCH-4",
            f"cost.measurement_state 值域錯誤：{state!r}，須為 {sorted(COST_STATES)}"))
    if state in ("measured", "unmeasured") and _is_zero(value):
        f.append(Finding("BLOCK", "ORCH-4",
            "cost.value 寫 0 但 measurement_state 不是 not_applicable。"
            "查不到要寫「未量測」—— 0 看起來像量測結果，「未量測」才是事實。"))
    if state == "measured" and isinstance(value, str) and "未量測" in value:
        f.append(Finding("BLOCK", "ORCH-4",
            "cost.measurement_state 宣告 measured 但 value 是「未量測」—— 宣告與事實不符"))
    if state == "unmeasured" and isinstance(value, (int, float)) and not _is_zero(value):
        f.append(Finding("BLOCK", "ORCH-4",
            f"cost.measurement_state 宣告 unmeasured 卻填了數字 {value!r} —— 宣告與事實不符"))

    # ORCH-5 觸發條件 —— 模型自評 confidence 是 E5 且跨供應商不可比
    triggers = doc.get("triggers") or []
    if not triggers:
        f.append(Finding("WARN", "ORCH-W3",
            "沒有 triggers —— 這條鏈只有一種走法。確定不需要任何回頭再審的條件？"))
    for i, tg in enumerate(triggers if isinstance(triggers, list) else []):
        if not isinstance(tg, dict) or not tg.get("when") or not tg.get("then"):
            f.append(Finding("BLOCK", "ORCH-1", f"triggers[{i}] 缺 when 或 then"))
            continue
        when = str(tg["when"])
        low = when.lower()
        if "confidence" in low:
            has_conj = (" and " in low) or ("&&" in low) or ("且" in when)
            has_checkable = any(s in low for s in CHECKABLE_SIGNALS)
            if not (has_conj and has_checkable):
                f.append(Finding("BLOCK", "ORCH-5",
                    f"triggers[{i}] 拿模型自評 confidence 當唯一閘門：{when!r}。"
                    "自評信心值是 E5，且 A 家的 0.8 與 B 家的 0.8 不是同一把尺 —— "
                    "必須再 AND 一個可檢核訊號（parse_failed／diff_items／4xx／測試紅綠）。"))

    # ORCH-6 evidence 宣告不實 —— 沒跑過的契約不得標 E1
    if ev == "E1" and not doc.get("chain_log"):
        f.append(Finding("BLOCK", "ORCH-6",
            "evidence 宣告 E1 但沒有 chain_log。E1 的定義是「我方實跑，貼得出輸出」——"
            "沒有紀錄的實跑跟沒跑過在檔案裡長得一模一樣。"))
    if ev in ("E1", "E2", "E3") and doc.get("dry_run") is True:
        f.append(Finding("BLOCK", "ORCH-6",
            f"dry_run: true（一次都沒真的呼叫）卻宣告 evidence: {ev}。乾跑的產物是假設。"))

    # 品質層（WARN）
    if route == "C" and not (doc.get("fanout") or {}).get("subtasks"):
        f.append(Finding("WARN", "ORCH-W4", "route: C（扇出鏈）但 fanout.subtasks 留白"))
    for i, s in enumerate(doc.get("steps") or []):
        if isinstance(s, dict) and re.search(r"對話|上一輪|conversation|上下文", str(s.get("input", ""))):
            f.append(Finding("WARN", "ORCH-W5",
                f"steps[{i}].input 看起來是在交棒對話而不是產物 —— "
                "交棒交的是檔案或欄位，不然下一步會附和上一步，而不是重新判斷"))
    if not doc.get("chain_log"):
        f.append(Finding("WARN", "ORCH-W6",
            "沒有 chain_log —— 跑完之後沒有人答得出「哪一步是誰做的」。見缺口 DS-G7"))
    return f


def _is_zero(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return v == 0
    return isinstance(v, str) and v.strip() in ("0", "0.0", "$0", "0 元")


# ─────────────────────────── connector 宣告 CONN-* ───────────────────────────

def check_connector(doc):
    f = []
    for key in ("id", "transport", "layers", "evidence", "source"):
        if doc.get(key) in (None, "", [], {}):
            f.append(Finding("BLOCK", "CONN-1", f"缺必填欄位 `{key}`"))
    if doc.get("writes") is None:
        f.append(Finding("BLOCK", "CONN-1",
            "缺 `writes` —— 判不出來就填 true。這個欄位決定要不要寫 rollback"))
    tp = doc.get("transport")
    if tp is not None and tp not in TRANSPORTS:
        f.append(Finding("BLOCK", "CONN-1", f"transport 值域錯誤：{tp!r}，須為 {sorted(TRANSPORTS)}"))
    if tp in ("http", "sse") and not doc.get("url"):
        f.append(Finding("BLOCK", "CONN-1", f"transport: {tp} 但沒有 url"))
    if tp == "stdio" and not doc.get("command"):
        f.append(Finding("BLOCK", "CONN-1", "transport: stdio 但沒有 command"))
    ev = doc.get("evidence")
    if ev is not None and ev not in EVIDENCE:
        f.append(Finding("BLOCK", "CONN-1", f"evidence 值域錯誤：{ev!r}"))
    for lay in (doc.get("layers") or []) + (doc.get("forbidden_layers") or []):
        if lay not in LAYERS:
            f.append(Finding("BLOCK", "CONN-1", f"layers 出現未知層別：{lay!r}，須為 {sorted(LAYERS)}"))

    # CONN-2 金鑰不入庫 —— 入庫即視為外洩，只能輪替，不能撤回
    auth = doc.get("auth") or {}
    if isinstance(auth, dict):
        for k, v in auth.items():
            v = str(v)
            if not re.fullmatch(r"\$\{[A-Z0-9_]+\}", v.strip()):
                f.append(Finding("BLOCK", "CONN-2",
                    f"auth.{k} 不是 ${{ENV_VAR}} 參照而是 {v!r}。"
                    "金鑰不入庫 —— 一旦寫進檔案就視為已外洩，只能輪替，不能撤回。"))

    # CONN-3 會寫入就要寫得出怎麼還原
    if doc.get("writes") is True and not str(doc.get("rollback") or "").strip():
        f.append(Finding("BLOCK", "CONN-3",
            "writes: true 但沒有 rollback。會動別人的東西卻沒寫怎麼還原，"
            "是這條產線的不可回復傷害。"))

    # CONN-4 機器可擬不可動錢 —— B 組不得進白名單
    billable = set(doc.get("tools_billable") or [])
    allow = doc.get("permissions_allow") or []
    leaked = [a for a in allow if a.rsplit("__", 1)[-1] in (billable | BILLABLE_TOOLS)]
    if leaked:
        f.append(Finding("BLOCK", "CONN-4",
            f"扣費工具出現在 permissions_allow：{leaked}。"
            "白名單的判準不是「常不常用」，是「錯了回不回得去」—— "
            "加進去的那一刻，「每次停下來看一眼」就消失了，而且不會有錯誤訊息。"))
    overlap = set(doc.get("tools_readonly") or []) & billable
    if overlap:
        f.append(Finding("BLOCK", "CONN-4",
            f"同一支工具被同時列為唯讀與扣費：{sorted(overlap)} —— 宣告自相矛盾"))

    if not doc.get("checked_at"):
        f.append(Finding("WARN", "CONN-W1",
            "缺 checked_at —— 外部資料會變，沒標時間的事實三週後沒有人知道還算不算數"))
    if ev == "E1" and not str(doc.get("notes") or "").strip():
        f.append(Finding("WARN", "CONN-W2",
            "evidence 標 E1（我方實跑）但 notes 空白 —— 跑過的人才寫得出「這裡會壞」"))
    return f


# ───────────────────────────────── 入口 ─────────────────────────────────

def check(path):
    doc, err = _load(path)
    if err:
        return [err]
    if path.name.endswith(".connector.yaml"):
        return check_connector(doc)
    return check_orchestration(doc)


def collect_all():
    return (sorted((ROOT / "tools").glob("*.connector.yaml"))
            + sorted((ROOT / "templates").glob("orchestration*.yaml"))
            + sorted((ROOT / "cases").glob("*/orchestration.yaml")))


def main(argv):
    targets = collect_all() if "--all" in argv else [Path(a) for a in argv if not a.startswith("-")]

    if not targets:
        print("找不到任何編排契約或 connector 宣告可檢核。")
        print("⚠️  這不是通過，是還沒有東西可檢 —— 檢核器掃到 0 個檔案時"
              "看起來會跟全部通過一模一樣，所以這裡明講。")
        return 2

    total_block = total_warn = 0
    for p in targets:
        findings = check(p)
        blocks = [x for x in findings if x.level == "BLOCK"]
        warns = [x for x in findings if x.level == "WARN"]
        total_block += len(blocks)
        total_warn += len(warns)
        status = "FAIL" if blocks else ("WARN" if warns else "PASS")
        try:
            shown = p.resolve().relative_to(ROOT)
        except ValueError:
            shown = p
        print(f"{status:4}  {shown}")
        for x in blocks + warns:
            print(x)

    if "--all" in argv and not list((ROOT / "cases").glob("*/orchestration.yaml")):
        print("\n註：cases/ 底下還沒有任何 orchestration.yaml。")
        print("    這代表這條鏈還沒有人真的跑過（缺口 DS-G8），不代表檢核通過。")

    print(f"\n掃描 {len(targets)} 份 —— BLOCK {total_block} / WARN {total_warn}")
    if total_block:
        print("BLOCK 未清空，不得合併。")
        print("  ORCH-*  編排契約  → schemas/orchestration.schema.yaml")
        print("  CONN-*  connector → schemas/mcp-connector.schema.yaml")
    return 1 if total_block else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
