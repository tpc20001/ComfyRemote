# ComfyRemote

ComfyUI 手機遙控（電腦上的 PySide6 程式＋手機網頁）。

- `app/`：真正的程式（`app.py` 電腦版、`core.py`、`web.py`／`webpage.py` 手機網頁、`cloudupd.py` 雲端更新…）
- `build/`：啟動器（EXE 外殼，`launcher.py`）和本機一鍵打包安裝（`BUILD_AND_INSTALL.bat`）
- `tools/`：`bump.py`（改版本、寫更新說明）、`pack.py`（做更新包）、`check.py`（自動測試）、`make_release.py`（雲端打包用）

## 發新版

1. `python tools/bump.py "改了什麼"`（改 `APP_VERSION`、`CHANGELOG.json` 加一筆）
2. `python tools/check.py`（全部通過才推）
3. 推到 `main` → GitHub Actions 在 Windows 上打包 → 放到 Releases（標籤 `v<版本>`，同一版只發一次）
4. 電腦上的 ComfyRemote 會自己發現新版（只提示），按「☁ 更新」才下載、熱更新

要換 EXE：改 `build/launcher.py` 的 `LAUNCHER_VERSION`；程式會提示「這次要換 EXE」，按更新會自動關掉、換好、再打開。
