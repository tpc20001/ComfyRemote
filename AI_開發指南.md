# AI 開發指南（先讀這份再動手）

> 這一包已經是 **ComfyRemote（ComfyUI 手機遙控）**：id ComfyRemote、前綴 CR、手機埠 8761。生圖的部分看最後「11. 🎨 生圖」。

這是一個 **Windows 桌面程式的空架子**（PySide6 + Python）。基礎功能都已經做好、調好了。你（AI）的工作是在上面**加新程式的功能**，不要重寫已經有的東西。

使用者會把這整包（或之後的更新包 `XX_V0.1.05.zip`）丟給你，說要做什麼。你改好 `app\` 裡的檔案，打包成下一版的更新包給他。他把更新包丟進程式的 `UPDATE` 資料夾，程式會熱更新，不用關。

---

## 1. 使用者的固定規則（每一次都要遵守）

1. **用繁體中文回答**，口語、簡短。先說做了什麼，再說要注意什麼。程式裡給使用者看的字也都用繁體中文。
2. **只做他說的。** 你覺得好的新點子，放進「🧪 實驗工作區」（`LAB_LIST`，預設關），並在回答裡說一句。不要自己改掉他沒說要改的行為。
3. **熱更新絕對不能讓程式當掉。**
   - 任何新程式碼都要包 `try/except`，失敗就記 LOG（`ENG.log.err('哪裡')`），程式照常跑。
   - 新版載入失敗時，熱更新會自動還原。但你寫的東西不能讓它「載入成功、跑起來才壞」。
4. **相容 Python 3.11。** 只能用 `build\_deps.py` 列出的模組（標準函式庫＋PySide6）。
   - 不能 `pip install` 新套件，因為更新包只換 `app\`，EXE 裡沒有的模組就是沒有。
   - 真的需要新套件：要改 `_deps.py`，並請使用者重新跑 `BUILD_AND_INSTALL.bat`。必須先講清楚。
5. **Tailscale：**
   - 每個程式用自己的 HTTPS 埠，等於本機埠 + 1000。
   - **絕對不要** `tailscale serve reset`（會清掉他其他程式的設定）。
   - 不碰 443（TikLive 在用）。
   - 本機埠不能跟他其他程式撞：VideoSift 用 8461、FusionStitch 用 8361。`tools\rename.py` 的 `USED` 有列。
6. **手機要跟電腦一樣。** 電腦上新增的按鈕、功能，手機網頁也要有（`web.py` 的 API ＋ `webpage.py` 的畫面）。
7. **使用者的資料不能弄丟。**
   - `Data\`（設定、資料庫）和 `LOG\` 永遠不會被更新包換掉。
   - 改資料庫只能「加欄位」（`MIGRATE`），不刪不改舊的。
   - 會刪檔、搬檔的功能，一定要先問、記操作紀錄（`ENG.oplog`）、能復原就做復原。
8. **每一版都要：**
   - 版本加一（`tools\bump.py`），CHANGELOG 寫改了什麼。
   - 跑 `tools\check.py`，全部 ✔ 才打包（`tools\pack.py`）。
   - 給他 `out\<前綴>_V<版本>.zip`。
9. **看到使用者的截圖或問題時**：先確認你看懂了。要查問題時，請他用「📜 LOG → 📦 匯出最近 7 天」把 LOG 傳給你。

---

## 2. 資料夾

```
AppKit\                         ← 這整包（開發用）
  AI_開發指南.md                 ← 這份
  使用說明.txt                   ← 給使用者的
  BUILD_AND_INSTALL.bat          ← 第一次安裝／換 EXE 時跑（會自動裝 Python、PySide6、FFmpeg、做 EXE、裝到桌面、開程式）
  build\
    launcher.py                  ← EXE 本身（啟動器）：開程式前先套用 UPDATE\*.zip，再執行 app\app.py。通常不用改
    build.ps1                    ← 安裝腳本（名稱從 app\brand.json 讀）
    _deps.py                     ← EXE 裡包了哪些模組（更新包能用的模組只有這些）
  app\                           ← 程式本體（更新包換的就是這裡）
    brand.json                   ← 程式名稱、更新包前綴、手機網頁埠、主色
    app.py                       ← 畫面（PySide6）：主視窗、各頁、熱更新、看門狗、托盤
    core.py                      ← 引擎（不准 import Qt）：設定、LOG、資料庫、效能、背景工作、後台總控制
    web.py                       ← 手機網頁伺服器：PIN 登入、Tailscale、API
    webpage.py                   ← 手機網頁畫面（HTML＋CSS＋JS 一個字串）
    CHANGELOG.json               ← 更新紀錄（最上面＝目前版本）
    icon.ico / icon_192.png / icon_512.png（選用：有就用，沒有就自己畫）
  tools\
    rename.py                    ← 把空架子改成新程式（id、名稱、前綴、埠）
    bump.py                      ← 版本加一＋CHANGELOG 加一筆
    check.py                     ← 改完一定要跑：編譯、引擎、手機網頁、畫面＋熱更新
    pack.py                      ← 打包更新包到 out\
    qtstub\                      ← 假的 PySide6（你的環境沒有 PySide6 時，check.py 用它抓 Python 錯誤）

裝好之後（使用者電腦上，桌面\<id>\）：
  <id>.exe  _internal\  app\  Data\（settings.json、app.sqlite3、db_backup\）  LOG\  UPDATE\  app_backup\
```

---

## 3. 架構

- **啟動**：`<id>.exe`（launcher）先套用 `UPDATE\*.zip`，再 `runpy` 執行 `app\app.py`。
  - 新版開不起來會自動退回。
  - 只有 `app\` 會被換。
- **熱更新**（程式不用關），`app.py` 的 `hot_update()` 依序做：
  1. 備份 `app\`，寫入新檔。
  2. 用全新的模組載入新的 `app.py`。
  3. 呼叫新版的 `hot_start(舊引擎, 畫面狀態)`，建新引擎（`adopt=舊引擎`，接手同一份排隊／進行中的工作）和新視窗。
  4. 舊視窗 `handoff()`，舊引擎 `retire()`（手上的做完就停）。
  - 任何一步失敗，檔案和模組都還原，舊的照常用。
- **畫面和引擎分開**：
  - 畫面只做畫面。讀硬碟、查資料庫、跑外部程式，一律 `bg(在背景做的函式, 做完回到畫面的函式)`。
  - 背景執行緒要碰畫面，用 `ui(函式)`。
  - 畫面卡超過 2 秒會記到 `ui_freeze_log.txt`；卡更久（約 3 秒以上）會再寫出主執行緒卡在哪一行。
- **全域**：`ENG`＝目前的引擎；`QApplication.instance()._ak_main`／`_ak_eng`／`_ak_web`＝目前的主視窗／引擎／手機伺服器（熱更新後會換成新的）。
- **背景工作框架**（`core.Engine`）：
  - `BG_KINDS` 列出每一項背景工作。
  - 後台頁和手機自動有暫停／繼續／立刻停／先後順序、CPU 太忙自動讓路（`_gov_loop`）、慢慢加速（`bg_cap`）。
  - 示範：`demo_add` → `_demo_boss` → `_demo_job`。

---

## 4. 怎麼加功能（照抄這些做法）

### 新的一頁
1. 在 `app.py` 寫 `class XxxPage(QWidget)`，`__init__(self, win)`。
2. `Main.__init__` 的 `self.PAGES` 清單最後加上它（位置就是頁碼）。
3. `NavList.GROUPS` 放進某個分組：`(頁碼, '名稱', '圖示')`。可以加新分組 `('分組名', '#顏色', [...])`。
4. 想在封面放按鈕，就加到 `CoverPage.COVER_BTNS`。
5. 頁面裡會定時更新的東西：用 `QTimer`，並在 `refresh()` 開頭寫 `if not self.isVisible(): return`（看不到就不做）。

### 新的背景工作（會花時間、要排隊的）
1. `BG_KINDS` 加 `('代號', '圖示', '名稱')`。
2. 照 `_demo_boss`／`_demo_job` 寫自己的：
   - 開新工作前看 `self.bg_hold('代號')`。
   - 同時幾個用 `self.bg_cap('代號', 上限)`。
   - 記最近在做哪個：`self.bg_mark('代號', 名稱)`。
   - 工作清單：`t = self.task('代號', '標題')` … `self.done(t, 'done'/'fail'/'stop', '訊息')`。
3. `bg_running`、`bg_progress`、`bg_stop_now` 加上這一項。
4. 要跨熱更新保留的東西：`self.xxx = _keep(adopt, 'xxx', 建立函式)`。
5. 到 `start()` 開執行緒（`threading.Thread(target=..., daemon=True)`）。
6. 迴圈條件用 `while self.alive()`，熱更新退休或關閉時才會停。
7. 跑外部程式：用 `core.run([...])`，不會開黑視窗。

### 新的設定
1. `core.DEFAULTS` 加預設值。
2. 讀用 `ENG.cfg.get('key')`，存用 `ENG.cfg.set('key', 值)`（馬上存檔，自動記 LOG）。
3. 畫面放在 `SetPage`（或該功能自己的頁）。
4. 手機能改的加到 `web.WebServer.SETTABLE`，並在 `webpage.py` 的 `rSet` 加一列。

### 新的資料表／欄位
- 新表：寫在 `core.SCHEMA`（`CREATE TABLE IF NOT EXISTS`）。
- 舊表加欄位：加到 `core.MIGRATE`。
- 不要刪表、改欄位型態、改舊資料的意思。

### 手機網頁
- **API**：`web.WebServer` 裡加 `def api_xxx(self, req):`，回 `jresp({...})`。
  - 網址是 `/api/xxx`，登入檢查已經做好。
  - 讀參數用 `req.q('名稱')`，POST 的內容用 `req.json()`。
- **畫面**：`webpage.py` 的 `TABS` 加一頁，寫 `async function rXxx(again){...}`。
  - 每 2 秒會用 `again=true` 再叫一次，只想畫一次的頁面開頭寫 `if(again)return`。
  - 呼叫 API：`await api('/api/xxx')`，POST 用 `await api('/api/xxx', {…})`。
- **改了畫面要同步電腦**：`self._ui(lambda: ...)`。

### 實驗功能
1. `LAB_LIST` 加 `('代號', '名稱', '說明')`。
2. 程式裡用 `lab_cfg().get('代號')` 判斷有沒有打開。
3. 使用者說「變成正式的」再拿掉判斷。

---

## 5. 版本與更新包規則

- **版本**：`主.次.兩位數`，例如 `0.1.01 → 0.1.02 … 0.1.99 → 0.2.01`（不用 00）。用 `tools\bump.py` 加。
- **檔名**：`<前綴>_V<版本>.zip`，例如 `AK_V0.1.02.zip`。前綴在 `brand.json` 的 `prefix`。
- **內容**：
  - `manifest.json`：`{"app": "<id>", "version": "0.1.02", "requires_launcher": 1}`
  - `app/`：所有檔（app.py、core.py、web.py、webpage.py、brand.json、CHANGELOG.json、圖示…）
  - 只收這些副檔名：`.py .json .md .txt .css .js .html .png .ico .svg`。
  - 別的程式的更新包（`app` 不同）會被拒絕。
- **每一版的流程**：
  1. 改程式。
  2. `python tools\bump.py "改了什麼" "改了什麼"`
  3. `python tools\check.py`（全部 ✔）
  4. `python tools\pack.py`
  5. 把 `out\` 裡的 zip 給使用者。
- **需要重新安裝 EXE 的情況**（更新包不夠）：
  - 改了 `build\launcher.py`、`build\_deps.py`（新模組）、圖示要變成 EXE 的圖示。
  - 這時 manifest 的 `requires_launcher` 加一、launcher 的 `LAUNCHER_VERSION` 也加一，並請使用者跑 `BUILD_AND_INSTALL.bat`。

---

## 6. 熱更新要注意的

- `app.py` 一定要保留 `def hot_start(`。沒有它就不能熱更新，只能重開程式套用。
- 新版引擎是用 `Engine(ROOT, adopt=舊引擎, start=False)` 建出來的。`__init__` 裡用到 `adopt` 的地方都要能接受「舊版沒有這個屬性」（用 `_keep` 或 `getattr(adopt, 'x', 預設)`）。
- 畫面狀態要帶到新視窗：加在 `Main.export_state()`／`_adopt()`。
- 計時器、浮窗、托盤：`handoff()` 會全部停掉。你新加的其他東西（子程序、伺服器）要在 `handoff` 或 `shutdown` 收好。
- 手機伺服器在熱更新時會換成新版（`web_restart_new`）。

---

## 7. 測試（每次都跑，不要跳過）

```
python tools\check.py
```
- 會檢查：
  1. 編譯。
  2. 引擎：背景工作、暫停、熱更新交接。
  3. 手機網頁：登入、各 API、頁面 JS 語法（有 node 的話）。
  4. 畫面：建主視窗、跑一次熱更新，`error_log.txt` 要是空的。
- 沒有 PySide6 的環境會用 `tools\qtstub`（假的 Qt）跑第 4 項。它只抓得到 Python 錯誤（打錯字、少參數），抓不到畫面長得對不對。
- 你新加的功能：在 `check.py` 加一個 `t_xxx()` 測它的邏輯（引擎的部分不用 Qt，直接測）。
- 慢的完整測試可以背景跑，先用快的打包給使用者。不要讓使用者等很久。

---

## 8. LOG（出問題先看這裡）

| 檔案 | 內容 |
|---|---|
| `app_log.txt` | 什麼都記：操作、設定改了什麼、工作開始／結束、錯誤一行摘要 |
| `error_log.txt` | 錯誤＋完整位置（traceback） |
| `ui_freeze_log.txt` | 畫面卡住幾秒、卡在哪一行 |
| `crash_dump.txt` | 程式整個掛掉時，每條執行緒在做什麼 |
| `update_log.txt` | 更新／熱更新的每一步 |
| `qt_log.txt` | Qt 的警告 |

- 每個檔超過 20 MB 就換新的，留 10 個。
- 寫 LOG：`ENG.log.w('訊息')`；錯誤：在 `except` 裡 `ENG.log.err('在做什麼')`。

---

## 9. 從空架子開始一個新程式（清單）

1. `python tools\rename.py --id MyTool --name MyTool --title "我的新工具" --prefix MT --port 8661`
   - 埠不能跟其他程式一樣。
   - Tailscale 會用 9661。
2. 換圖示（選用）：放 `app\icon.ico`、`app\icon_192.png`、`app\icon_512.png`。
3. 把 `HomePage` 換成主要畫面。示範背景工作（`demo_*`、`BG_KINDS` 的 `demo`）換成真的工作，或留著當範例。
4. `CHANGELOG.json` 第一筆改成新程式的說明。
5. `python tools\check.py`，然後把整包給使用者。
   - 第一次安裝：他解壓縮後點 `BUILD_AND_INSTALL.bat`。
   - 之後每一版：給 `out\MT_V0.1.02.zip` 這種更新包。

---

## 10. 已經有的功能（不用再做、不要重寫）

- **左邊選單**：分組、點分組標題收合、記住收合；右邊的數字小標籤用 `nav.set_badge(頁碼, '3')`。
- **左下電腦狀態**：CPU／RAM／GPU／VRAM，點一下開「📊 效能」浮窗（可拖、記位置）。
- **上方按鈕**：📊 效能／🖥 後台／🌙 縮到背景（托盤）／🏠 封面（Ctrl+L，不露出內容）。
- **下方狀態列**：後台暫停中的項目、◐ 深色／淺色、介面大小 70～160%。
- **🖥 後台狀態**：總控制表格（暫停、繼續、立刻停、↑↓順序、進度、停在哪）、自動讓路設定、最近 80 個工作。
- **⚙ 設定**：一般（按 X 縮到托盤、封面、閒置回封面、閃退自動重開、卡頓紀錄門檻）、📱 手機網頁、資料夾按鈕。
- **⟳ 版本與更新**：選更新包、檢查內容（安全、能編譯、版本比較、這版改了什麼）、⚡ 熱更新、改用重開套用、更新紀錄。
  - UPDATE 資料夾一出現新的更新包，上方就會跳提示列。
- **📜 LOG**：看各個 LOG、匯出最近 7 天 zip。
- **🧪 實驗工作區**、**📖 使用說明**（F1）。
- **防當機**：
  - 未處理的錯誤只記 LOG、不關程式。
  - 背景執行緒錯誤、Qt 警告、畫面卡住都有紀錄，整個掛掉時會傾印。
  - 閃退自動重開（PowerShell 看門狗）：10 分鐘內第 2 次閃退時先把背景工作全部暫停，第 3 次就不再重開。
- **只能開一個**：第二次打開會叫出原本那個。Windows 關機時不擋、也不會被看門狗重開。
- **資料庫**：每天自動備份到 `Data\db_backup\`，留 7 份。
- **📱 手機網頁**：
  - PIN 登入（錯 5 次鎖 5 分鐘）、記住登入。
  - 可安裝成 App（PWA、離線時顯示提示）。
  - 分頁：首頁、⏯ 後台（跟電腦一樣的總控制）、📊 效能（含最近的曲線）、⚙ 設定（含實驗開關、上傳更新包熱更新、看 LOG、登出）。
  - 深色／淺色；🖥 網頁版／📱 手機版切換。

---

## 11. 🎨 生圖（ComfyRemote 自己的功能）

- `app\comfy.py`（不准 import Qt，只用標準函式庫）：
  - `Comfy`：ComfyUI HTTP API（/system_stats、/upload/image、/prompt、/history、/view、/queue、/interrupt）。
  - `WS`：最小 websocket 用戶端收進度；連不上自動改成定時查 /history。
  - `ui_to_api`：一般存檔（nodes／links）→ API 格式。widget 名稱用節點 inputs 裡的 `widget` 標記；舊檔沒有才問 `/object_info`。處理 Reroute、Set/Get、略過（bypass）、停用（mute）、PrimitiveNode、種子後面的 control_after_generate 值。
  - `prepare`：讀圖節點換成上傳的照片（不是 LoadImage 就整個換成 LoadImage）、提示詞填到 KSampler positive 往上找到的第一個文字欄位、種子隨機、`prune` 只留 STD_OUTPUTS 用得到的節點。
- `core.Engine`：`BG_KINDS` 的 `gen`；`gen_add／gen_cancel／gen_rerun／gen_reuse／gen_hide／gen_jobs／gen_workflows／gen_wf_save／gen_save_input／gen_file`；`_gen_boss`（一次送一個）、`_gen_job`。資料表 `gen_jobs`。
  - 檔案：`Data\workflows\*.json`（流程）、`Data\inputs`（上傳的照片）、`Data\outputs\日期\`（結果）。
  - 預設流程 `app\wf_GROK.json` 第一次開程式時複製成 `Data\workflows\GROK 改圖.json`（之後不再覆蓋）。
- 手機：`web.py` 的 `api_gen／api_gen_upload／api_gen_run／api_gen_act／api_gen_wf／api_img`；`webpage.py` 的 `rGen`。電腦：`app.py` 的 `GenPage`（第 0 頁）。
- 測試：`tools\fake_comfy.py` 是假的 ComfyUI（不打包），`check.py` 的 `t_gen` 用它跑完整流程。
