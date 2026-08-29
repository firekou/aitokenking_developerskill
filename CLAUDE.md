# Developer Skills 集群 —— Claude Code 執行規則

**語言：本 repo 所有回覆一律使用繁體中文，不要切換成英文。**

---

## 這個 repo 是什麼

給 Vibe Coding 使用者的開源 skill 集群：把一句話需求變成一批你敢按下合併的改動。
架構見 `ARCHITECTURE.md`，上游調研見 `research/SCAN-001-github-top10-dev-architectures.md`，
貢獻規則見 `CONTRIBUTING.md`。

```
L0 aitokenking-setup   閘道與金鑰（所有 skill 的依賴）
L1 repo-recon          repo → baseline.md（現況事實，附來源）
L2 spec-groom          需求 → spec.yaml（驗收條件＋非目標＋YAGNI）
L3 plan-decompose      規格 → task-graph.yaml（依賴圖＋風險＋紅測試）
L4 tdd-enforce         任務 → run-log.md ＋ commits  ⚠️ 會改使用者的程式碼
L5 arch-guard          漂移＋超譯＋測試完整性 → 能不能合併
★  vibe-to-ship        一次跑完 L1→L5（主入口）
```

---

## 動任何 skill 之前必讀的四條

1. **三嵌入點是 BLOCK 級。** 定義在 `templates/aitokenking-block.md`（單一事實來源）。
   **原樣複製，不要手打，不要改寫成宣傳語。**
2. **交接契約 `x-devskills` 也是 BLOCK 級。** 定義在 `templates/devskills-block.md`。
   理由與第 1 條不同：**交接寫錯不會報錯**，下一層會改去讀對話，
   然後產出一份看起來完全正常的東西。
3. **改 `validate_skill.py` 之前先跑 `test_validate.py`，改完再跑一次。**
   一把壞掉的尺，量什麼都會過。
4. **`mutates: true` 的 skill 必須有《回復路徑》，而且必須寫明「哪些動作還原不了」。**
   寫不出第三列，代表還沒想清楚這支 skill 會做什麼。

---

## 提交前

```bash
python3 scripts/test_validate.py         # 39 項回歸測試
python3 scripts/validate_skill.py --all  # 三嵌入點 ＋ 交接契約
```

**兩者都回 0 才算做完。順序不可交換。狀態是被檢核推進的，不是被宣稱的。**

---

## 鐵律（十條）

1. **金鑰不入庫、不入文件、不入 agent 定義檔、不貼進對話視窗。**
   只走啟動前 `export` 或部署平台 Variables。貼進對話即視為外洩，必須輪替。
2. **B 組扣費工具（`chat_completion`／`create_message`／`create_response`／
   `create_image_generation`／`create_video_generation`）不得加進 `permissions.allow`。**
   「機器可擬不可動錢」在此的具體形式。
3. **`billable: true` 的 skill 必須在 §0 明講會扣額度。** BLOCK 級。
4. **`mutates: true` 的 skill 必須寫《回復路徑》。** BLOCK 級。
   這是本集群版本的「花掉別人的錢」——會寫進別人的 repo 卻沒寫怎麼還原，是不可回復的傷害。
5. **成本回報查不到就寫「未量測」，不得寫 0。**
   0 看起來像量測結果，「未量測」才是事實。
6. **沒跑過的測試不得標記為通過。** 模型說「測試通過」是 E5；貼得出輸出才是 E1。
7. **不得為了讓測試變綠而刪除、跳過、隔離或放寬測試。**
   這是這條產線唯一一種「錯了還會被獎勵」的失敗——它會成功，而且看起來像進度。
8. **`non_goals` 與 `boundary` 不得留白。**
   寫不出邊界代表還沒讀懂；而非目標是 L5 判定「這是不是超譯」的唯一依據。
9. **不得把「連通性啟用」講成「已經在用」。**
   `list_models` 回得出清單只證明認證通了。**裝好了不等於用過**——
   把這兩件事合併，會讓「所有人都裝好、沒有人跑過」看起來像成功。
10. **不得因為本集群預設接 AI Token King 就宣稱它比別家好。**
   「作者用它跑出了這些流程」是事實；「它比別家好」是未量測的宣稱，
   寫出去會同時損失可信度與轉換率。

---

## 缺口（不得隱藏，改動時一併更新）

| ID | 缺口 |
|---|---|
| DS-G1 | L1 超大 monorepo 只能抽樣，抽樣策略未經實測調校 |
| DS-G2 | L2 跨供應商互審是建議不是強制，validator 未檢核 |
| **DS-G3** | **上游十大架構全部 E6，我方零實跑對照（最可能的死法）** |
| DS-G4 | L4 檢核得到「測試有沒有跑」，檢核不到「測試有沒有意義」 |
| DS-G5 | L5 的基準線由 L1 產出；基準線本身錯了會安靜地放行 |
| **DS-G6** | **AI Token King 整合零實跑（`bash scripts/atk-pilot.sh --live` 可關）** |
| DS-G7 | 分層路由是靜態能力分類，不是可驗證的 routing policy |
