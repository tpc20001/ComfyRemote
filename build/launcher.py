"""Launcher（啟動器，做成 EXE）。名稱從 app/brand.json 讀，換程式不用改這個檔。

The EXE built from this file only contains Python + PySide6.
The real program lives in <ROOT>\\app\\*.py and is replaced by update packages:
drop  <PREFIX>_V0.1.02.zip  into  <ROOT>\\UPDATE\\  and start the EXE (the running app also hot-updates without restarting).
"""
import os, sys, json, shutil, zipfile, runpy, time, traceback, re
from pathlib import Path

import _deps  # noqa: F401  (forces PyInstaller to bundle every runtime dependency)

LAUNCHER_VERSION = 2          # V0.3.36 雲端自動更新：設環境變數 AK_LAUNCHER，程式才知道 EXE 要不要換；提示改成會自己關的（換 EXE 後自動打開不會卡住）
ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "app"
UPDATE_DIR = ROOT / "UPDATE"
BACKUP_DIR = ROOT / "app_backup"
LOG_DIR = ROOT / "LOG"


def _brand():
    try: return json.loads((APP_DIR / "brand.json").read_text(encoding="utf-8-sig"))
    except Exception: return {}


APP_NAME = _brand().get("name") or "App"


def log(msg):
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with (LOG_DIR / "update_log.txt").open("a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def msgbox(text, title=None, error=False, secs=20):
    """會自己關掉的提示（Windows MessageBoxTimeout）：換 EXE 後自動打開、沒人在電腦前也不會卡住."""
    title = title or APP_NAME
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxTimeoutW(None, str(text), title, 0x10 if error else 0x40, 0, int(secs * 1000))
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(text), title, 0x10 if error else 0x40)
        except Exception:
            print(title, text)


def vkey(name):
    return tuple(int(x) for x in re.findall(r"\d+", name)) or (0,)


def apply_updates():
    """Apply every UPDATE\\*.zip in version order. Returns backup path of the first applied update."""
    if not UPDATE_DIR.exists():
        return None, []
    zips = sorted(UPDATE_DIR.glob("*.zip"), key=lambda p: vkey(p.stem))
    first_backup = None; applied = []
    for z in zips:
        backup = None
        try:
            with zipfile.ZipFile(z) as zf:
                manifest = {}
                if "manifest.json" in zf.namelist():
                    manifest = json.loads(zf.read("manifest.json").decode("utf-8-sig"))
                need = int(manifest.get("requires_launcher", 1))
                if manifest.get("app") and _brand().get("id") and manifest["app"] != _brand().get("id"):
                    log(f"SKIP {z.name}: package for {manifest['app']}, this is {_brand().get('id')}")
                    continue
                if need > LAUNCHER_VERSION:
                    msgbox(f"更新檔 {z.name} 需要新版啟動器（EXE），請使用完整安裝包更新。\n\n目前程式維持原版本。", error=True)
                    log(f"SKIP {z.name}: requires launcher {need} > {LAUNCHER_VERSION}")
                    continue
                members = [m for m in zf.namelist() if m.startswith("app/") and not m.endswith("/")]
                for m in members:
                    if ".." in Path(m).parts or Path(m).is_absolute():
                        raise RuntimeError(f"unsafe path in update: {m}")
                if not members:
                    raise RuntimeError("update package has no app/ files")
                for m in members:
                    if m.endswith(".py"): compile(zf.read(m).decode("utf-8"), m, "exec")   # 壞掉的程式檔不套用
                stamp = time.strftime("%Y%m%d_%H%M%S")
                backup = BACKUP_DIR / f"{stamp}_before_{z.stem}"
                if APP_DIR.exists():
                    shutil.copytree(APP_DIR, backup, ignore=shutil.ignore_patterns("__pycache__"))
                first_backup = first_backup or backup
                for m in members:
                    dest = ROOT / m
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    tmp = dest.with_suffix(dest.suffix + ".new")
                    tmp.write_bytes(zf.read(m))
                    os.replace(tmp, dest)
                shutil.rmtree(APP_DIR / "__pycache__", ignore_errors=True)
            done = UPDATE_DIR / "applied"; done.mkdir(exist_ok=True)
            os.replace(z, done / z.name)
            applied.append(manifest.get("version") or z.stem)
            log(f"APPLIED {z.name} (backup {first_backup})")
        except Exception as e:
            log(f"FAILED {z.name}: {e}")
            if backup is not None and backup.exists():
                try: restore(backup); log(f"RESTORED {backup} after failed {z.name}")
                except Exception as e2: log(f"RESTORE FAILED: {e2}")
            msgbox(f"套用更新 {z.name} 失敗：\n{e}\n\n程式維持原版本。", error=True)
    # keep only the 5 newest backups
    try:
        olds = sorted(BACKUP_DIR.iterdir(), key=lambda p: p.name)[:-5]
        for d in olds: shutil.rmtree(d, ignore_errors=True)
    except Exception:
        pass
    return first_backup, applied


def restore(backup):
    shutil.rmtree(APP_DIR, ignore_errors=True)
    shutil.copytree(backup, APP_DIR)


def run_app():
    os.environ["AK_LAUNCHER"] = str(LAUNCHER_VERSION)
    sys.path.insert(0, str(APP_DIR))
    for mod in ("app", "core"):
        sys.modules.pop(mod, None)
    runpy.run_path(str(APP_DIR / "app.py"), run_name="__main__")


def cleanup_shell():
    """上次換 EXE 解壓縮用的暫存資料夾。_internal_old、.old 留給換 EXE 的 BAT：程式開起來回報（UPDATE\\shell_ok.flag）它才刪，開不起來它會換回舊的."""
    shutil.rmtree(UPDATE_DIR / "shell_new", ignore_errors=True)
    for z in UPDATE_DIR.glob("*_Shell_L*.zip") if UPDATE_DIR.exists() else []:
        try:
            if time.time() - z.stat().st_mtime > 3600: z.unlink()
        except Exception: pass


def selftest():
    """雲端打包完試一下這個 EXE：模組都在、Qt 外掛有打包（不開主程式、不開視窗）."""
    import importlib
    bad = []
    for m in ("_deps", "PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtMultimedia", "PySide6.QtNetwork", "PySide6.QtSvg",
              "sqlite3", "ssl", "zlib", "certifi", "ctypes.wintypes", "http.client", "urllib.request"):
        try: importlib.import_module(m)
        except BaseException as e: bad.append(f"{m}: {type(e).__name__}: {e}")
    try:
        from PySide6.QtCore import QLibraryInfo
        pl = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)) / "platforms"
        if not any(pl.glob("qwindows*.dll")): bad.append(f"找不到 Qt 畫面外掛 qwindows.dll（{pl}）")
    except Exception as e: bad.append(f"Qt 外掛: {e}")
    out = {"ok": not bad, "launcher": LAUNCHER_VERSION, "bad": bad}
    (ROOT / "selftest.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return 0 if not bad else 2


def main():
    if "--selftest" in sys.argv: return selftest()
    os.chdir(ROOT)
    log(f"啟動（啟動器第 {LAUNCHER_VERSION} 版）{sys.executable}")
    backup, applied = apply_updates()
    cleanup_shell()
    if not (APP_DIR / "app.py").exists():
        msgbox(f"找不到程式檔：\n{APP_DIR / 'app.py'}\n\n請重新安裝或放入更新檔。", error=True)
        return 1
    if applied:
        msgbox("已更新至：" + "、".join(applied) + "\n\n你的資料（Data）未受影響。")
    try:
        run_app()
    except SystemExit as e:
        return e.code or 0
    except Exception:
        err = traceback.format_exc(); log("START FAILED\n" + err)
        if backup is not None:
            restore(backup); log(f"ROLLED BACK to {backup}")
            msgbox("新版本啟動失敗，已自動退回更新前的版本。\n\n詳細錯誤記錄在 LOG\\update_log.txt。", error=True)
            os.execv(sys.executable, [sys.executable] + sys.argv[1:]) if getattr(sys, "frozen", False) else None
        else:
            msgbox("程式啟動失敗，詳細錯誤記錄在 LOG\\update_log.txt。\n\n" + err[-800:], error=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
