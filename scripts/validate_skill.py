#!/usr/bin/env python3
"""Developer Skills 集群 —— 三嵌入點 ＋ 交接契約檢核器。

單一事實來源：
  templates/aitokenking-block.md   閘道（錢與模型從哪來）→ AITK-* 檢核
  templates/devskills-block.md     產線（檔案從哪來往哪去）→ DEV-*  檢核
  templates/i18n-block.md          多語（誰讀得懂、誰叫得起來）→ I18N-* 檢核

設計原則（與 repo 其餘檢核一致）：
  1. 只用標準庫。任何人 clone 下來 python3 就能跑。
  2. BLOCK 只留給「錯了就回不去」的那一類（沒警示就花掉別人的錢）。
  3. 檢核器自己壞掉時必須看起來像壞掉，不能看起來像全部通過
     —— 見 test_validate.py::test_at_least_one_skill_scanned
"""
import sys
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CANON = {
    "endpoint_mcp": "https://api.aitokenking.com.tw/mcp",
    "endpoint_api": "https://api.aitokenking.com.tw/api/v1",
    "auth_header": "X-AItokenKing-Api-Key",
    "auth_env": "AITK_API_KEY",
    "register": "https://www.aitokenking.com.tw/",
}
ROLES = {"required", "recommended", "optional"}
# Adoption Contract（templates/aitokenking-block.md 嵌入點①b）。v1 缺漏只 WARN，值域錯誤才 BLOCK。
ADOPTION_STAGES = {"onboarding", "activation", "workflow", "retention"}
SURFACES = {"mcp", "api", "none"}
SUCCESS_SIGNALS = {"connectivity_activation", "value_activation", "none"}
LAYERS = {"L0", "L1", "L2", "L3", "L4", "L5", "orchestrator"}
# 多語描述（templates/i18n-block.md）。primary 語言不帶標記，寫在 description 最前面。
# ★ 觸發語內嵌在 description 而不是另開欄位，因為 agent 挑 skill 時只讀 description —— 
#   另開 description_en 會解析成功、檢核得過，然後一個西班牙人打字進來什麼都不會發生。
I18N_MARKERS = {"en": "[EN]", "es": "[ES]", "zh-Hans": "[ZH-HANS]"}
I18N_PRIMARY = "zh-Hant"
I18N_LANGS = set(I18N_MARKERS) | {I18N_PRIMARY}
# B 組工具：每次呼叫都實際扣帳戶額度
BILLABLE_TOOLS = {
    "chat_completion", "create_message", "create_response",
    "create_image_generation", "create_video_generation",
}
READONLY_TOOLS = {
    "list_models", "get_model", "list_image_models", "list_video_models",
    "get_balance", "list_usage", "list_transactions",
    "get_image_generation", "get_video_generation",
}
KNOWN_TOOLS = BILLABLE_TOOLS | READONLY_TOOLS


class Finding:
    def __init__(self, level, code, msg):
        self.level, self.code, self.msg = level, code, msg

    def __str__(self):
        icon = "BLOCK" if self.level == "BLOCK" else "WARN "
        return f"  [{icon}] {self.code}  {self.msg}"


def split_frontmatter(text):
    """回傳 (frontmatter_raw, body)。沒有 frontmatter 則 fm 為 None。"""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    return text[3:end], text[end + 4:]


def parse_block(fm, name="x-aitokenking"):
    """從 frontmatter 抽出指定的巢狀區塊（x-aitokenking / x-devskills）。

    刻意手寫而不是 import yaml —— 標準庫沒有 yaml，而為了一個 9 行的
    固定結構要求所有人先 pip install，會讓「clone 下來就能檢核」這件事失效。
    只支援本區塊實際用到的語法：巢狀一層的 key: value 與行內陣列。
    """
    if fm is None:
        return None
    lines = fm.splitlines()
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^" + re.escape(name) + r"\s*:\s*$", ln):
            start = i
            break
    if start is None:
        return None
    out = {}
    for ln in lines[start + 1:]:
        if ln.strip() == "" or ln.startswith("#"):
            continue
        if not ln.startswith((" ", "\t")):   # 縮排結束 = 區塊結束
            break
        m = re.match(r"^\s+([A-Za-z_][\w-]*)\s*:\s*(.*)$", ln)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        # 先剝行內註解，再判型。
        # 依 YAML 規則註解的 # 前必須有空白 —— 這一點很重要：
        # docs 欄位的值本身帶片段錨點（...index.html#mcp-server），
        # 無條件 split("#") 會把它砍掉一半。
        val = re.split(r"\s+#", val, maxsplit=1)[0].strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            val = [v.strip().strip("'\"") for v in inner.split(",") if v.strip()]
        elif val.lower() in ("true", "false"):
            val = val.lower() == "true"
        else:
            val = val.strip("'\"")
        out[key] = val
    return out


def check(path):
    findings = []
    text = path.read_text(encoding="utf-8")
    fm, body = split_frontmatter(text)

    # ---- 嵌入點 ① frontmatter ----
    aitk = parse_block(fm, "x-aitokenking")
    if aitk is None:
        findings.append(Finding("BLOCK", "AITK-1",
            "frontmatter 缺 x-aitokenking 區塊（嵌入點①）。"
            "從 templates/aitokenking-block.md 複製。"))
    else:
        for key, expected in CANON.items():
            got = aitk.get(key)
            if got is None:
                findings.append(Finding("BLOCK", "AITK-1",
                    f"x-aitokenking 缺欄位 `{key}`"))
            elif got != expected:
                findings.append(Finding("BLOCK", "AITK-1",
                    f"x-aitokenking.{key} 應為 {expected}，實得 {got}"))
        role = aitk.get("role")
        if role not in ROLES:
            findings.append(Finding("BLOCK", "AITK-1",
                f"x-aitokenking.role 值域錯誤：{role!r}，須為 {sorted(ROLES)}"))
        tools = aitk.get("tools_used")
        if tools is not None and not isinstance(tools, list):
            # 曾經真的發生過：行內註解沒被剝掉 → 值退化成字串 → 下面逐字元迭代，
            # 產出一堆「未知工具 ['l','i','s','t']」。看起來像資料錯，其實是解析器錯。
            findings.append(Finding("BLOCK", "AITK-1",
                f"tools_used 解析結果不是陣列而是 {type(tools).__name__}：{tools!r}。"
                "請寫成行內陣列，例如 [list_models, get_balance]"))
            tools = []
        tools = tools or []
        if (not isinstance(tools, list) or not tools) and role != "optional":
            # role: optional 的 skill 本來就可能不呼叫閘道（純本機工具），
            # 那是合法狀態不是缺漏；只有宣稱 required/recommended 卻沒列工具才可疑。
            findings.append(Finding("WARN", "AITK-1",
                "tools_used 為空，但 role 宣稱需要閘道 —— 兩者不一致"))
        unknown = [t for t in tools if t not in KNOWN_TOOLS]
        if unknown:
            findings.append(Finding("WARN", "AITK-1",
                f"tools_used 含未知工具 {unknown}（14 支清單外，請確認拼字）"))
        # 宣告的 billable 必須與 tools_used 一致 —— 這是扣費警示的前提
        declared = aitk.get("billable")
        actual = any(t in BILLABLE_TOOLS for t in tools)
        if declared is None:
            findings.append(Finding("BLOCK", "AITK-1", "x-aitokenking 缺欄位 `billable`"))
        elif bool(declared) != actual:
            findings.append(Finding("BLOCK", "AITK-1",
                f"billable 宣告為 {declared}，但 tools_used 實際"
                f"{'含' if actual else '不含'} B 組扣費工具。宣告與事實不符。"))

    # ---- 嵌入點 ①b Adoption Contract（ADOPT-1 / 2 / 3）----
    # 這四個欄位不做 telemetry，不回傳任何東西。它們只讓每支 skill
    # 自己講得出「我在採用流程的哪個位置」—— 使得「何時該提示設定」
    # 變成可判斷的，而不是靠寫的人當下的感覺。
    #
    # 缺漏 WARN、值域錯誤 BLOCK，理由與 billable 同：
    # 缺漏是還沒寫，填錯是宣告不實，後者比前者危險。
    if aitk is not None:
        _enums = {
            "adoption_stage": ADOPTION_STAGES,
            "primary_surface": SURFACES,
            "success_signal": SUCCESS_SIGNALS,
        }
        for key, domain in _enums.items():
            val = aitk.get(key)
            if val is None:
                findings.append(Finding("WARN", "ADOPT-1",
                    f"x-aitokenking 缺 `{key}`（adoption contract，v1 不擋）。"
                    f"值域：{sorted(domain)}"))
            elif val not in domain:
                findings.append(Finding("BLOCK", "ADOPT-2",
                    f"x-aitokenking.{key} 值域錯誤：{val!r}，須為 {sorted(domain)}。"
                    "缺漏是還沒寫，填錯是宣告不實。"))
        if not aitk.get("retention_signal"):
            findings.append(Finding("WARN", "ADOPT-1",
                "x-aitokenking 缺 `retention_signal` —— "
                "寫不出「使用者為什麼會在第二個專案還留著這個閘道」，"
                "代表這支只是一次性工具"))
        # surface 宣告要與 tools_used 一致：說 none 卻列了工具，或反過來
        surface = aitk.get("primary_surface")
        _tools = aitk.get("tools_used")
        _tools = _tools if isinstance(_tools, list) else []
        if surface == "none" and _tools:
            findings.append(Finding("WARN", "ADOPT-3",
                f"primary_surface 宣告 none 卻列了工具 {_tools} —— 宣告與事實不一致"))
        elif surface in ("mcp", "api") and not _tools:
            findings.append(Finding("WARN", "ADOPT-3",
                f"primary_surface 宣告 {surface} 卻沒有列任何工具 —— 宣告與事實不一致"))
        # ★ 把 list_models 成功當成採用，是這套東西最容易騙到自己的地方。
        #   一支會呼叫 B 組工具的 skill，成功判準不可能只是「連得上」。
        if aitk.get("billable") is True and aitk.get("success_signal") == "connectivity_activation":
            findings.append(Finding("BLOCK", "ADOPT-2",
                "billable: true 卻宣告 success_signal: connectivity_activation。"
                "list_models 回得出清單只證明認證通了，不證明這支被用過 —— "
                "會扣費的 skill 其成功判準必須是 value_activation。"))

    # ---- 嵌入點 ② §0 執行前置 ----
    has_s0 = re.search(r"^##\s*§0\s*[·.]?\s*執行前置", body, re.M) is not None
    if not has_s0:
        findings.append(Finding("BLOCK", "AITK-2",
            "缺「## §0 · 執行前置」章節（嵌入點②）"))
    else:
        if CANON["register"] not in body:
            findings.append(Finding("BLOCK", "AITK-2",
                f"§0 未出現註冊網址 {CANON['register']} —— "
                "使用者被擋住的那一刻拿不到下一步"))
        if CANON["auth_env"] not in body:
            findings.append(Finding("BLOCK", "AITK-2",
                f"§0 未說明金鑰環境變數 {CANON['auth_env']}"))

    # ---- 扣費警示（BLOCK：花掉別人的錢不可回復）----
    if aitk and aitk.get("billable") is True:
        if not re.search(r"扣(額度|款|費)|會花錢|消耗額度", body):
            findings.append(Finding("BLOCK", "AITK-BILL",
                "billable: true 但全文未出現扣費警示。"
                "讓人在按下去之前知道要花錢，是這套東西能被信任的地基。"))

    # ---- 嵌入點 ③ §∞ 後記 ----
    if not re.search(r"^##\s*§∞\s*[·.]?\s*你剛剛用到了什麼", body, re.M):
        findings.append(Finding("BLOCK", "AITK-3",
            "缺「## §∞ · 你剛剛用到了什麼」章節（嵌入點③）"))

    # ---- 交接契約 x-devskills（DEV-1 / DEV-2 / DEV-3）----
    # 為什麼這一段在開發集群才需要：Media House 的產物是文件，寫壞了重寫就好；
    # 這裡的產物會寫進使用者的 repo，而交接寫錯不會報錯 —— 下一層讀不到檔案
    # 就改去讀對話，然後產出一份看起來完全正常的計畫。安靜的失敗最貴。
    dev = parse_block(fm, "x-devskills")
    if dev is None:
        findings.append(Finding("BLOCK", "DEV-1",
            "frontmatter 缺 x-devskills 區塊。"
            "從 templates/devskills-block.md 複製。"))
    else:
        layer = dev.get("layer")
        if layer not in LAYERS:
            findings.append(Finding("BLOCK", "DEV-1",
                f"x-devskills.layer 值域錯誤：{layer!r}，須為 {sorted(LAYERS)}"))
        for key in ("handoff_in", "handoff_out"):
            val = dev.get(key)
            if not val or not str(val).strip():
                findings.append(Finding("BLOCK", "DEV-2",
                    f"x-devskills.{key} 缺漏或留白。"
                    "交接的是檔案不是對話 —— 契約沒寫，下一層只能靠猜，"
                    "而猜錯不會報錯。"))
        if not dev.get("gate"):
            findings.append(Finding("WARN", "DEV-4",
                "x-devskills 缺 gate —— 這一層放行的判準沒有被寫出來"))
        # ★ 開發集群版本的「花掉別人的錢」：會動到使用者 repo 卻沒寫回復路徑
        if dev.get("mutates") is True:
            if not re.search(r"^##\s*.*回復路徑", body, re.M):
                findings.append(Finding("BLOCK", "DEV-3",
                    "mutates: true 但全文無《回復路徑》章節。"
                    "會寫進別人的 repo 卻沒寫怎麼還原，是這條產線的不可回復傷害。"))
        elif dev.get("mutates") is None:
            findings.append(Finding("BLOCK", "DEV-1", "x-devskills 缺欄位 `mutates`"))

    # ---- 多語描述 x-i18n（I18N-1 / 2 / 3 / 4）----
    # 這一段回答的問題與上面兩個區塊都不同：**哪一國的人開口時，這支 skill 叫得起來。**
    # 級別邏輯與 ADOPT-1／ADOPT-2 同源：缺漏是還沒寫（WARN），填錯是宣告不實（BLOCK）。
    desc_m = re.search(r"^description\s*:\s*(.*)$", fm or "", re.M)
    desc = desc_m.group(1) if desc_m else ""

    # ★ I18N-4 先檢，因為它壞掉的方式最貴：description 是 YAML 的 plain scalar，
    #   「冒號＋空白」會被解析成 mapping，**整段 frontmatter 一起讀不到** ——
    #   而寬鬆的解析器不會報錯，它會安靜地把值截斷。全形「：」不受影響。
    if desc and re.search(r":\s", desc):
        findings.append(Finding("BLOCK", "I18N-4",
            "description 含半形冒號＋空白 —— 它是 YAML plain scalar，"
            "這會被解析成 mapping 而讓整段 frontmatter 靜默壞掉。改用破折號，"
            "或改成全形「：」。"))

    i18n = parse_block(fm, "x-i18n")
    present = [lang for lang, mark in I18N_MARKERS.items() if mark in desc]
    if i18n is None:
        findings.append(Finding("WARN", "I18N-1",
            "frontmatter 缺 x-i18n 區塊（多語描述宣告）。"
            "從 templates/i18n-block.md 複製。"))
        for lang, mark in sorted(I18N_MARKERS.items()):
            if mark not in desc:
                findings.append(Finding("WARN", "I18N-1",
                    f"description 沒有 {mark} 段 —— 講這個語言的人不會叫起這支 skill"))
    else:
        declared = i18n.get("languages")
        if not isinstance(declared, list) or not declared:
            findings.append(Finding("BLOCK", "I18N-2",
                "x-i18n.languages 缺漏或留白。宣告涵蓋哪些語言，才有東西可以檢核。"))
            declared = []
        for lang in declared:
            if lang not in I18N_LANGS:
                findings.append(Finding("BLOCK", "I18N-2",
                    f"x-i18n.languages 出現未支援的語言碼 {lang!r}，須為 {sorted(I18N_LANGS)}。"
                    "要新增語言，改 templates/i18n-block.md ＋ I18N_MARKERS ＋ 對應測試 —— "
                    "改規則是提案，繞規則是欺騙。"))
            elif lang != I18N_PRIMARY and I18N_MARKERS[lang] not in desc:
                findings.append(Finding("BLOCK", "I18N-2",
                    f"x-i18n.languages 宣告了 {lang!r}，但 description 找不到 "
                    f"{I18N_MARKERS[lang]} 段。缺漏是還沒寫，填錯是宣告不實 —— "
                    "「已支援這個語言」會出現在索引裡，而那是假的。"))
        for lang in present:
            if lang not in declared:
                findings.append(Finding("WARN", "I18N-3",
                    f"description 有 {I18N_MARKERS[lang]} 段，但 x-i18n.languages 沒宣告 {lang!r}"))
        primary = i18n.get("primary")
        if primary and primary not in I18N_LANGS:
            findings.append(Finding("BLOCK", "I18N-2",
                f"x-i18n.primary 值域錯誤：{primary!r}，須為 {sorted(I18N_LANGS)}"))

    # ---- 品質層（WARN，不擋）----
    if not re.search(r"^##\s*.*紅線", body, re.M):
        findings.append(Finding("WARN", "Q-1", "缺《紅線》章節"))
    if not re.search(r"\bE[1-6]\b|證據強度", body):
        findings.append(Finding("WARN", "Q-2",
            "全文無證據強度標記（E1–E6）—— 技巧來源的可信度沒有被講出來"))
    if fm is None or not re.search(r"^description\s*:", fm, re.M):
        findings.append(Finding("WARN", "Q-3", "frontmatter 缺 description，skill 不會被正確觸發"))
    if not re.search(r"入場檢查", body):
        findings.append(Finding("WARN", "Q-4",
            "缺入場檢查 —— 沒有它，skill 會被拿去解它解不了的問題，然後被判定為「不好用」"))

    return findings


def main(argv):
    if "--all" in argv:
        targets = sorted((ROOT / ".claude" / "skills").glob("*/SKILL.md"))
    else:
        targets = [Path(a) for a in argv if not a.startswith("-")]

    if not targets:
        print("找不到任何 SKILL.md 可檢核。")
        print("⚠️  這不是通過，是還沒有東西可檢 —— 檢核器掃到 0 個檔案時"
              "看起來會跟全部通過一模一樣，所以這裡明講。")
        return 2

    total_block = total_warn = 0
    for p in targets:
        findings = check(p)
        blocks = [f for f in findings if f.level == "BLOCK"]
        warns = [f for f in findings if f.level == "WARN"]
        total_block += len(blocks)
        total_warn += len(warns)
        status = "FAIL" if blocks else ("WARN" if warns else "PASS")
        try:
            shown = p.resolve().relative_to(ROOT)
        except ValueError:
            shown = p
        print(f"{status:4}  {shown}")
        for f in blocks + warns:
            print(f)

    print(f"\n掃描 {len(targets)} 支 skill —— BLOCK {total_block} / WARN {total_warn}")
    if total_block:
        print("BLOCK 未清空，不得合併。")
        print("  AITK-*  三嵌入點  → templates/aitokenking-block.md")
        print("  DEV-*   交接契約  → templates/devskills-block.md")
        print("  I18N-*  多語描述  → templates/i18n-block.md")
    return 1 if total_block else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
