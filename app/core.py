"""核心引擎（不准 import Qt）：設定、LOG、資料庫、效能、背景工作（後台總控制）、熱更新交接。

規則（給接手的 AI）：
- 畫面（app.py）只做畫面；讀硬碟、跑外部程式、算東西都在這裡的背景執行緒，畫面用 bg() 拿結果。
- 熱更新：新的 Engine(adopt=舊引擎) 接手同一份排隊／進行中的工作；舊引擎 retire() 後不再接新工作，手上的做完就停。
  新加「要跨熱更新保留」的東西 → 用 _keep(adopt, '名字', 建立函式)。
- 新的背景工作類型：加到 BG_KINDS、寫一個 _xxx_boss 執行緒（每次開新工作前先看 self.bg_hold('xxx')），
  bg_running／bg_progress 補上那一項，後台頁和手機就自動有暫停／繼續／立刻停／先後順序／自動讓路。
"""
import urllib.parse, urllib.error
import os, sys, re, json, time, platform, shutil, sqlite3, threading, subprocess, traceback, zipfile, binascii, uuid, random, hashlib, statistics
from pathlib import Path
from collections import OrderedDict, deque

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))
import comfy  # noqa: E402


def load_brand():
    """app/brand.json：程式名稱、更新包前綴、手機網頁埠…（換成新程式只要改這個檔，或用 tools/rename.py）."""
    B = {'id': 'AppKit', 'name': 'AppKit', 'title': 'AppKit 新程式', 'prefix': 'AK', 'web_port': 8561, 'accent': '#e51e63', 'phone_id': 'appkit-phone'}
    try: B.update(json.loads((HERE / 'brand.json').read_text(encoding='utf-8-sig')))
    except Exception: pass
    return B


BRAND = load_brand()
APP_NAME = BRAND['name']
IS_WIN = os.name == 'nt'
NO_WINDOW = 0x08000000 if IS_WIN else 0
PRIO = {'idle': 0x00000040, 'below': 0x00004000, 'normal': 0x00000020} if IS_WIN else {'idle': 0, 'below': 0, 'normal': 0}

DEFAULTS = {
    'ui_theme': 'dark', 'ui_zoom': 100,          # 深色／淺色、介面大小（下方狀態列）
    'side_w': 210, 'nav_shut': [],               # 側邊欄寬度、收起來的分組
    'last_page': 0, 'cover_on_start': True, 'cover_on_restore': False, 'cover_idle_min': 0,
    'close_to_tray': True,                       # 按 X：縮到右下角（托盤「結束」才真的關）
    'perf_float': False, 'perf_pos': None,       # 📊 效能浮窗
    'freeze_log_s': 2.0,                         # 畫面卡超過幾秒記到 ui_freeze_log.txt
    'auto_restart': True,                        # 閃退自動重開（看門狗）
    'web_on': False, 'web_port': BRAND.get('web_port', 8561), 'web_lan': False, 'web_tokens': [], 'web_pin_hash': '', 'web_pin_salt': '',
    'cpu_guard': True, 'cpu_max': 90, 'bg_ramp_sec': 20, 'bg_pause': {}, 'bg_last': {}, 'bg_prio': [],
    'db_backup': True, 'db_backup_keep': 7,
    'lab': {},                                   # 🧪 實驗工作區的開關 {名稱: True/False}
    'demo_n': 2,                                 # 示範背景工作：同時幾個
    # 🎨 ComfyUI 生圖
    'comfy_cmd': {},                             # V0.3.74 學到的 ComfyUI 啟動指令（自動記）
    'comfy_direct': True,                        # V0.3.74 有學到就直接啟動，不經過 Comfy Desktop 首頁
    'comfy_restart_h': 24,                       # V0.3.72 每幾小時趁空檔重開 ComfyUI（0＝不要）
    'comfy_restart_stall': True,                 # V0.3.72 卡住第二次：先重開 ComfyUI 再試
    'comfy_url': '',                             # 空的＝自動找（Desktop 8000、免安裝版 8188）
    'gen_wf': 'GROK 改圖',                        # 預設用哪個流程（Data\workflows\<名稱>.json）
    'gen_timeout_min': 60,                       # 一張超過幾分鐘算失敗
    'comfy_exe': '',                             # V0.3.62 Comfy Desktop 的程式（空的＝找預設位置）
    'comfy_autostart': True,                     # V0.3.73 連不到 1 分鐘自動打開（沒在跑）或重開（卡住）ComfyUI
    'gen_stall_min': 8,                          # V0.3.42 跑到一半幾分鐘沒有任何進度 → 提醒（多半是記憶體不夠，ComfyUI 卡住）
    'gen_stall_auto_min': 20,                    # 卡住幾分鐘自動「中斷＋清記憶體＋重排」一次（0＝不要自動）
    'gen_mp': 2.0,                               # 手機上傳前縮成幾百萬像素（0＝原圖）
    'gen_last': {},                              # 電腦版上次填的（提示詞、流程…）
    'gen_preset_done': False,
    'keep_awake': True,
    'gen_free_switch': True,
    'gen_free_idle': True,                       # 排隊的全部做完 1 分鐘：叫 ComfyUI 清掉記憶體
    'gen_auto_retry': True,                      # 記憶體不夠失敗：清乾淨自動再試一次
    'hf_token': '',                              # Hugging Face 金鑰：要同意授權的模型（FLUX 3 Klein 等）才需要
    'model_src_x': {},                           # 官方範本裡寫的模型下載網址（自動記）
    'people_refs': 3,                            # 人物庫：H3 參考生影片每個人帶幾張照片                     # 換流程時先叫 ComfyUI 清掉上一個流程的模型（記憶體不夠的電腦很重要）                          # 生圖／下載模型進行中：不讓電腦睡眠（螢幕可以關）
}


def now_s(): return time.strftime('%Y-%m-%d %H:%M:%S')




def fmt_t(s):
    s = int(max(0, s or 0)); return f'{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}' if s >= 3600 else f'{s // 60}:{s % 60:02d}'


def fmt_b(b):
    b = float(b or 0)
    return f'{b / 1e12:.2f} TB' if b >= 1e12 else f'{b / 1e9:.2f} GB' if b >= 1e9 else f'{b / 1e6:.0f} MB' if b >= 1e6 else f'{b / 1e3:.0f} KB'


def vkey(v):
    """版本比大小：'0.1.99' < '0.2.01'."""
    return tuple(int(x) for x in re.findall(r'\d+', str(v or ''))) or (0,)


def next_version(v):
    """版本規則：0.1.01 → 0.1.02 … 0.1.99 → 0.2.01（最後一段兩位數、不用 00）."""
    a = list(vkey(v)) + [0, 0, 0]; ma, mi, pa = a[0], a[1], a[2]
    pa += 1
    if pa > 99: mi += 1; pa = 1
    return f'{ma}.{mi}.{pa:02d}'


def run(cmd, timeout=60, prio='normal'):
    """跑外部程式（不開黑視窗）：回傳 (returncode, stdout, stderr)."""
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, creationflags=NO_WINDOW | PRIO.get(prio, 0), stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout.decode('utf-8', 'replace'), p.stderr.decode('utf-8', 'replace')
    except subprocess.TimeoutExpired: return -9, '', '逾時'
    except Exception as ex: return -1, '', f'{type(ex).__name__}: {ex}'


# ---------------------------------------------------------------- LOG
class Log:
    """app_log.txt＝什麼都記（操作、設定變更、工作開始／結束、錯誤一行摘要）；error_log.txt＝錯誤＋完整位置；
    ui_freeze_log.txt＝畫面卡住（含卡在哪一行）；crash_dump.txt＝整個掛掉時每條執行緒在做什麼；update_log.txt＝更新／熱更新；qt_log.txt＝Qt 警告。
    每個檔超過 20 MB 換新的，舊的留最近 10 個。出問題時請使用者把整個 LOG 資料夾傳給 AI."""
    KEEP = 10

    def __init__(self, d):
        self.d = Path(d); self.d.mkdir(parents=True, exist_ok=True); self.lock = threading.Lock(); self.tail = deque(maxlen=600)

    def _rotate(self, p):
        try:
            if p.exists() and p.stat().st_size > 20e6:
                os.replace(str(p), str(p.with_name(f'{p.stem}_{time.strftime("%Y%m%d_%H%M%S")}{p.suffix}')))
                for o in sorted(self.d.glob(f'{p.stem}_2*{p.suffix}'))[:-self.KEEP]:
                    try: o.unlink()
                    except Exception: pass
        except Exception: pass

    def w(self, msg, f='app_log.txt'):
        th = threading.current_thread().name
        line = f'[{now_s()}] [{th}] {msg}' if f == 'app_log.txt' and th != 'MainThread' else f'[{now_s()}] {msg}'
        if f == 'app_log.txt': self.tail.append(line)
        with self.lock:
            try:
                p = self.d / f; self._rotate(p)
                with open(p, 'a', encoding='utf-8') as fh: fh.write(line + '\n')
            except Exception: pass

    def err(self, msg):
        tb = traceback.format_exc()
        if tb.strip() == 'NoneType: None': tb = ''.join(traceback.format_stack()[:-1])
        self.w(f'{msg}\n{tb}', 'error_log.txt'); self.w('✖ ' + msg + '　（詳細在 error_log.txt）')

    def export(self, out_zip, days=7):
        cut = time.time() - days * 86400; n = 0
        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
            for p in sorted(self.d.glob('*')):
                if p.is_file() and p.stat().st_mtime >= cut and p.suffix.lower() in ('.txt', '.jsonl', '.json', '.log'): z.write(p, p.name); n += 1
        self.w(f'匯出 LOG：{n} 個檔（最近 {days} 天）→ {out_zip}'); return n


# ---------------------------------------------------------------- 設定
class Settings:
    """Data/settings.json。get 沒有的就用 DEFAULTS；set 馬上存檔（先寫 .tmp 再換掉，不會寫到一半壞掉），每次改都記 LOG."""
    QUIET = {'perf_pos', 'side_w'}

    def __init__(self, path):
        self.path = Path(path); self.lock = threading.Lock(); self.d = dict(DEFAULTS); self.log = None
        try:
            j = json.loads(self.path.read_text(encoding='utf-8'))
            if isinstance(j, dict): self.d.update(j)
        except Exception: pass

    def get(self, k, default=None):
        v = self.d.get(k, DEFAULTS.get(k))
        return default if v is None and default is not None else v

    def set(self, k, v):
        old = self.d.get(k, DEFAULTS.get(k))
        if old == v: return
        if self.log and k not in self.QUIET:
            sv = lambda x: (json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else repr(x))[:300]
            self.log.w(f'設定：{k}　{sv(old)} → {sv(v)}')
        with self.lock:
            self.d[k] = v; self.path.parent.mkdir(parents=True, exist_ok=True); tmp = self.path.with_suffix('.tmp')
            tmp.write_text(json.dumps(self.d, ensure_ascii=False, indent=1), encoding='utf-8'); os.replace(str(tmp), str(self.path))


# ---------------------------------------------------------------- 資料庫
SCHEMA = """
CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT, t REAL);
CREATE TABLE IF NOT EXISTS items(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, state INTEGER DEFAULT 0, note TEXT DEFAULT '', t REAL DEFAULT 0);
CREATE TABLE IF NOT EXISTS oplog(id INTEGER PRIMARY KEY AUTOINCREMENT, t REAL, kind TEXT, detail TEXT DEFAULT '', ok INTEGER DEFAULT 1);
CREATE INDEX IF NOT EXISTS ix_oplog_t ON oplog(t);
CREATE TABLE IF NOT EXISTS gen_jobs(id INTEGER PRIMARY KEY AUTOINCREMENT, t REAL, src TEXT DEFAULT '', wf TEXT DEFAULT '', prompt TEXT DEFAULT '', neg TEXT DEFAULT '',
  img TEXT DEFAULT '', seed INTEGER DEFAULT -1, state TEXT DEFAULT 'wait', msg TEXT DEFAULT '', outs TEXT DEFAULT '[]', dur REAL DEFAULT 0, t1 REAL DEFAULT 0, hidden INTEGER DEFAULT 0);
"""
MIGRATE = [('items', 'tag', "TEXT DEFAULT ''"),
           # V0.1.02 生圖：參數、計時、冷／熱（要不要載入模型）、照片和結果的大小（拿來預估時間）
           ('gen_jobs', 'params', "TEXT DEFAULT '{}'"), ('gen_jobs', 'ekey', "TEXT DEFAULT ''"), ('gen_jobs', 'mkey', "TEXT DEFAULT ''"),
           ('gen_jobs', 'run_s', 'REAL DEFAULT 0'), ('gen_jobs', 't_start', 'REAL DEFAULT 0'), ('gen_jobs', 'cold', 'INTEGER DEFAULT -1'),
           ('gen_jobs', 'imgs', "TEXT DEFAULT '[]'"),
           ('gen_jobs', 'hist_hidden', 'INTEGER DEFAULT 0'), ('gen_jobs', 'deleted', 'REAL DEFAULT 0'), ('gen_jobs', 'trash', "TEXT DEFAULT '{}'"),   # V0.1.11 歷史：隱藏、刪除（回收桶）                          # V0.1.07 一個流程好幾張照片（圖一、圖二…）
           ('gen_jobs', 'in_w', 'INTEGER DEFAULT 0'), ('gen_jobs', 'in_h', 'INTEGER DEFAULT 0'), ('gen_jobs', 'out_w', 'INTEGER DEFAULT 0'), ('gen_jobs', 'out_h', 'INTEGER DEFAULT 0'),
           ('gen_jobs', 'batch', 'INTEGER DEFAULT 0'), ('gen_jobs', 'prof', "TEXT DEFAULT ''"),
           ('gen_jobs', 'vote', 'INTEGER DEFAULT 0'), ('gen_jobs', 'cmp', 'INTEGER DEFAULT 0'), ('gen_jobs', 'cmp_col', "TEXT DEFAULT ''"), ('gen_jobs', 'mask', "TEXT DEFAULT ''"), ('gen_jobs', 'ref', "TEXT DEFAULT ''"), ('gen_jobs', 'chain', "TEXT DEFAULT ''"), ('gen_jobs', 'cue', "TEXT DEFAULT ''")]   # V0.2.64 局部的提示方式（gray＝消除、red＝放東西）   # V0.2.54 做完接著排下一個（改圖 → 首尾幀影片）   # V0.2.08 📎 參考圖   # V0.1.90 🖌 只改塗到的地方（遮罩圖檔名，在 inputs）   # V0.1.34 🧪 比較：你給的分數（0 沒評、1～5 星）、屬於第幾次比較   # V0.1.27 每一步花幾秒（找慢在哪）                                   # V0.1.14 同一次送出的一批（批量照片、影片挑的好幾格）：歷史紀錄收成一組，可以合併成一張


def migrate_db(db):
    """建表＋補欄位（熱更新時舊的資料庫連線也要跑，所以獨立出來）."""
    with db.lock:
        db.con.executescript(SCHEMA); db.con.commit()
        for tb, col, decl in MIGRATE:
            have = {r[1] for r in db.con.execute(f'PRAGMA table_info({tb})').fetchall()}
            if col not in have: db.con.execute(f'ALTER TABLE {tb} ADD COLUMN {col} {decl}'); db.con.commit()          # 新欄位放這裡：舊資料庫打開時自動補（不動原本的資料）


class Store:
    """SQLite（WAL）。所有讀寫用同一把鎖；q／one 讀、x／xm 寫（失敗自動 rollback）."""
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True); self.lock = threading.RLock()
        self.con = sqlite3.connect(str(self.path), check_same_thread=False, timeout=30)
        self.con.execute('PRAGMA journal_mode=WAL'); self.con.execute('PRAGMA synchronous=NORMAL'); self.con.execute('PRAGMA busy_timeout=30000')
        with self.lock:
            self.con.executescript(SCHEMA); self.con.commit()
            for tb, col, decl in MIGRATE:
                have = {r[1] for r in self.con.execute(f'PRAGMA table_info({tb})').fetchall()}
                if col not in have: self.con.execute(f'ALTER TABLE {tb} ADD COLUMN {col} {decl}'); self.con.commit()
        self.con.row_factory = sqlite3.Row

    def q(self, sql, a=()):
        with self.lock: return self.con.execute(sql, a).fetchall()

    def one(self, sql, a=()):
        with self.lock: return self.con.execute(sql, a).fetchone()

    def x(self, sql, a=()):
        with self.lock:
            try:
                c = self.con.execute(sql, a); self.con.commit(); return c.rowcount
            except Exception:
                try: self.con.rollback()
                except Exception: pass
                raise

    def xm(self, sql, seq):
        with self.lock:
            try: self.con.executemany(sql, seq); self.con.commit()
            except Exception:
                try: self.con.rollback()
                except Exception: pass
                raise

    def backup_to(self, dst):
        with self.lock:
            b = sqlite3.connect(str(dst))
            try: self.con.backup(b)
            finally: b.close()

    def close(self):
        with self.lock:
            try: self.con.close()
            except Exception: pass


# ---------------------------------------------------------------- 效能（不用 psutil：Windows API／Linux /proc；顯示卡用 nvidia-smi）
class Perf:
    def __init__(self, log):
        self.log = log; self.cpu = 0.0; self.ram = 0.0; self.ram_used = 0; self.ram_total = 0; self.gpu = None
        self.H = {k: deque(maxlen=180) for k in ('cpu', 'ram', 'gpu', 'enc', 'dec', 'vram')}; self._ct = None; self.stop = False
        self.smi = shutil.which('nvidia-smi') or (r'C:\Windows\System32\nvidia-smi.exe' if IS_WIN and Path(r'C:\Windows\System32\nvidia-smi.exe').exists() else '')
        threading.Thread(target=self._loop, name='Perf', daemon=True).start()

    def _cpu_times(self):
        if IS_WIN:
            import ctypes
            from ctypes import wintypes
            i, k, u = wintypes.FILETIME(), wintypes.FILETIME(), wintypes.FILETIME()
            ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(i), ctypes.byref(k), ctypes.byref(u))
            f = lambda x: (x.dwHighDateTime << 32) | x.dwLowDateTime
            return f(i), f(k) + f(u)
        with open('/proc/stat') as fh: v = [int(x) for x in fh.readline().split()[1:]]
        return v[3] + v[4], sum(v)

    def _ram(self):
        if IS_WIN:
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong), ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('a', ctypes.c_ulonglong), ('b', ctypes.c_ulonglong), ('c', ctypes.c_ulonglong), ('d', ctypes.c_ulonglong), ('e', ctypes.c_ulonglong)]
            m = MS(); m.dwLength = ctypes.sizeof(MS); ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys - m.ullAvailPhys, m.ullTotalPhys
        d = {}
        with open('/proc/meminfo') as fh:
            for ln in fh:
                k, v = ln.split(':', 1); d[k] = int(v.split()[0]) * 1024
        return d['MemTotal'] - d.get('MemAvailable', 0), d['MemTotal']

    def _loop(self):
        k = 0
        while not self.stop:
            try:
                idle, tot = self._cpu_times()
                if self._ct:
                    di, dt = idle - self._ct[0], tot - self._ct[1]
                    self.cpu = max(0.0, min(100.0, 100.0 * (1 - di / dt))) if dt > 0 else 0.0
                self._ct = (idle, tot)
                self.ram_used, self.ram_total = self._ram(); self.ram = 100.0 * self.ram_used / self.ram_total if self.ram_total else 0
            except Exception: pass
            if self.smi and k % 2 == 0:
                rc, out, _e = run([self.smi, '--query-gpu=name,utilization.gpu,utilization.encoder,utilization.decoder,memory.used,memory.total,temperature.gpu,driver_version',
                                   '--format=csv,noheader,nounits'], timeout=8)
                try:
                    p = [x.strip() for x in out.strip().splitlines()[0].split(',')] if rc == 0 and out.strip() else None
                    self.gpu = {'name': p[0], 'util': float(p[1]), 'enc': float(p[2]), 'dec': float(p[3]), 'mem': float(p[4]), 'mem_t': float(p[5]), 'temp': float(p[6]), 'drv': p[7]} if p else None
                except Exception: self.gpu = None
            g = self.gpu or {}
            self.H['cpu'].append(self.cpu); self.H['ram'].append(self.ram); self.H['gpu'].append(g.get('util')); self.H['enc'].append(g.get('enc')); self.H['dec'].append(g.get('dec'))
            self.H['vram'].append(100.0 * g['mem'] / g['mem_t'] if g.get('mem_t') else None)
            k += 1; time.sleep(1.0)

    def view(self):
        g = dict(self.gpu or {})
        return {'cpu': round(self.cpu, 1), 'ram': round(self.ram, 1), 'ram_used': self.ram_used, 'ram_total': self.ram_total, 'gpu': g,
                'hist': {k: [None if x is None else round(float(x), 1) for x in list(v)] for k, v in self.H.items()}}


# ---------------------------------------------------------------- 引擎
def _keep(adopt, k, make):
    """熱更新接手：舊的有就共用同一個（空的也共用，所以不能用 or）."""
    v = getattr(adopt, k, None) if adopt is not None else None
    return v if v is not None else make()


class Engine:
    """root＝程式資料夾（EXE 旁邊）：Data\\（設定、資料庫）、LOG\\、UPDATE\\、app\\。
    adopt＝熱更新時的舊引擎；start=False：先建好、還不開始跑（熱更新時新視窗也建好才 start，失敗就 discard，舊的照常）."""
    PREV_GC_TICK, PREV_GC_WAIT = 15, 120
    # 後台總控制的項目：(代號, 圖示, 名稱)。新功能的背景工作加在這裡（順序＝預設先後）
    BG_KINDS = [('gen', '🎨', 'ComfyUI 生圖'), ('dl', '⬇', '下載模型')]
    GOV_EXEMPT = {'gen', 'dl'}       # 不參加「CPU 太忙自動讓路」：生圖是 ComfyUI 在顯示卡上跑、這個程式只是在等；不然 CPU 一直高時後面排隊的會卡住不開始                         # 示範背景工作（demo_*）留著當範例，不顯示在後台

    def __init__(self, root, adopt=None, start=True, version=''):
        self.root = Path(root); self.data = self.root / 'Data'; self.data.mkdir(parents=True, exist_ok=True); self.version = version
        self.log = _keep(adopt, 'log', lambda: Log(self.root / 'LOG')); self.cfg = Settings(self.data / 'settings.json'); self.cfg.log = self.log
        self.db = Store(self.data / 'app.sqlite3') if adopt is None else adopt.db
        try: migrate_db(self.db)
        except Exception: self.log.err('資料庫補欄位')
        self.stop_all = False; self.retired = False; self.started = False; self.prev = adopt
        self.perf = Perf(self.log)
        self.lock = _keep(adopt, 'lock', threading.RLock); self.tasks = _keep(adopt, 'tasks', OrderedDict); self._tid = (getattr(adopt, '_tid', 0) + 1000) if adopt else 0
        self.procs = _keep(adopt, 'procs', set)
        # 後台總控制：暫停（存在設定裡，重開還在）、電腦太忙時自動讓路、慢慢加速、最近在做哪一個
        self.bg_pause = {k: True for k, v in dict(self.cfg.get('bg_pause') or {}).items() if v}
        self.bg_auto = _keep(adopt, 'bg_auto', dict); self.bg_slow = _keep(adopt, 'bg_slow', dict); self.bg_ramp = _keep(adopt, 'bg_ramp', dict)
        self.bg_last = dict(self.cfg.get('bg_last') or {})
        self.bg_gov = _keep(adopt, 'bg_gov', lambda: {'hi_t': 0.0, 'lo_t': 0.0, 'log': deque(maxlen=200)})
        for k_ in self.GOV_EXEMPT: self.bg_auto.pop(k_, None); self.bg_slow.pop(k_, None)   # 舊版讓路卡住的，接手時放開
        # 示範背景工作（新程式把它換成真的工作）：排隊、進行中
        self.demo_q = _keep(adopt, 'demo_q', deque); self.demo_active = _keep(adopt, 'demo_active', dict); self.demo_done = _keep(adopt, 'demo_done', lambda: [0])
        # 🎨 ComfyUI 生圖：排隊（工作編號）、進行中 {編號: 狀態}
        self.gen_q = _keep(adopt, 'gen_q', deque); self.gen_active = _keep(adopt, 'gen_active', dict); self.gen_done = _keep(adopt, 'gen_done', lambda: [0])
        self.comfy_st = _keep(adopt, 'comfy_st', lambda: {'t': 0, 'url': '', 'stats': None, 'err': ''}); self.comfy_info = _keep(adopt, 'comfy_info', dict)
        self.dl = _keep(adopt, 'dl', OrderedDict)
        self.gen_crash = _keep(adopt, 'gen_crash', dict)                  # 跑某個工作時 ComfyUI 不見了幾次（同一個工作 2 次就跳過，後面的繼續）                          # ⬇ 下載模型 {檔名: 狀態}
        self.wf_cache = {}; self.par_cache = {}; self.est_cache = {}; self.info_fresh = set()
        self.gen_hot = getattr(adopt, 'gen_hot', None); self.gen_wait = ''
        if not self.comfy_info:
            try: self.comfy_info.update(json.loads((self.data / 'object_info.json').read_text(encoding='utf-8')))
            except Exception: pass
        for d in ('workflows', 'inputs', 'outputs'): (self.data / d).mkdir(exist_ok=True)
        self.info_c = {'t': 0, 'v': {}}
        if start: self.start()

    # ================================================================ 生命週期
    def alive(self): return not self.stop_all and not self.retired

    def start(self):
        if self.started: return
        self.started = True; old = self.prev
        if old is not None:
            try: old.cfg = self.cfg
            except Exception: pass
            try: old.retire()
            except Exception:
                try: old.retired = True
                except Exception: pass
        else:
            self.log_startup()
            try: self.gen_boot()
            except Exception: self.log.err('生圖：讀回沒做完的工作')
        for k_ in [k for k, _i, _n in self.BG_KINDS]:
            if old is None: self.bg_ramp[k_] = time.time()                     # 剛開程式：慢慢加速
        for nm, fn in (('Awake', self._awake_loop), ('DlBoss', self._dl_boss), ('GenBoss', self._gen_boss), ('DemoBoss', self._demo_boss), ('Governor', self._gov_loop), ('DbBackup', self._backup_loop)):
            threading.Thread(target=fn, name=nm, daemon=True).start()
        if old is not None: threading.Thread(target=self._prev_gc, name='PrevGC', daemon=True).start()

    def retire(self):
        """熱更新：不再接新工作（正在做的照做完）."""
        self.retired = True
        try: self.perf.stop = True
        except Exception: pass
        self.log.w(f'舊引擎 V{self.version or "?"} 退休：手上的做完就停')

    def discard(self):
        """熱更新失敗：這個沒開始跑的新引擎丟掉（舊的照常）."""
        self.stop_all = True
        try: self.perf.stop = True
        except Exception: pass

    def _prev_gc(self):
        """熱更新後：舊引擎手上的都做完了就放掉（不然每熱更新一次多留一份在記憶體）."""
        t0 = time.time()
        while self.alive():
            time.sleep(self.PREV_GC_TICK)
            e = self.prev
            if e is None: return
            if self.demo_active or self.gen_active or any(d['state'] == 'run' for d in self.dl.values()) or time.time() - t0 < self.PREV_GC_WAIT: continue
            try: e.prev = None
            except Exception: pass
            self.prev = None; self.log.w(f'熱更新：舊引擎 V{getattr(e, "version", "?")} 已釋放'); return

    def shutdown(self):
        self.stop_all = True
        try: self.perf.stop = True
        except Exception: pass
        busy = len(self.demo_active) + len(self.gen_active)
        for p in list(self.procs):
            try: p.kill()
            except Exception: pass
        e = self.prev
        while e is not None:
            try: e.stop_all = True
            except Exception: pass
            e = getattr(e, 'prev', None)
        self.log.w(f'關閉 {APP_NAME} V{self.version}（停掉做到一半的 {busy} 個工作，下次打開接著做）'); self.log.w('=' * 100); self.db.close()

    def log_startup(self):
        L = self.log.w; L('=' * 100)
        L(f'啟動 {APP_NAME} V{self.version}　{platform.platform()}　Python {platform.python_version()}　{"EXE" if getattr(sys, "frozen", False) else "原始碼"}　程式資料夾 {self.root}')
        try: L('設定：' + '　'.join(f'{k}={self.cfg.get(k)}' for k in ('ui_theme', 'ui_zoom', 'web_on', 'web_port', 'cpu_guard', 'cpu_max')))
        except Exception: pass

    # ================================================================ 工作清單（後台頁下方的「最近的工作」）
    def task(self, kind, title):
        with self.lock:
            self._tid += 1; t = {'id': self._tid, 'kind': kind, 'title': title, 'state': 'run', 'pct': None, 'msg': '', 't0': time.time(), 't1': 0}
            self.tasks[self._tid] = t
            while len(self.tasks) > 300: self.tasks.popitem(last=False)
            return t

    def done(self, t, state='done', msg=''):
        t['state'] = state; t['t1'] = time.time()
        if msg: t['msg'] = msg

    def tasks_list(self):
        with self.lock: return list(self.tasks.values())

    def oplog(self, kind, detail='', ok=True):
        try: self.db.x('INSERT INTO oplog(t,kind,detail,ok) VALUES(?,?,?,?)', (time.time(), kind, detail, 1 if ok else 0))
        except Exception: self.log.err('操作紀錄')

    # ================================================================ 後台總控制（每一項：暫停／繼續／立刻停／先後順序／自動讓路／慢慢加速）
    def bg_prio(self):
        K = [k for k, _i, _n in self.BG_KINDS]; L = [k for k in (self.cfg.get('bg_prio') or []) if k in K]
        return L + [k for k in K if k not in L]

    def bg_hold(self, kind):
        """這一項現在不要開新的工作：你按了暫停，或電腦太忙自動讓路."""
        return bool(self.bg_pause.get(kind)) or kind in self.bg_auto

    def bg_cap(self, kind, n):
        """慢慢加速：剛開始／剛繼續時同時只做 1 個，每過 bg_ramp_sec 秒多 1 個，直到上限 n."""
        if self.bg_slow.get(kind): n = max(1, min(n, int(self.bg_slow[kind])))
        t0 = self.bg_ramp.get(kind)
        if not t0: return n
        sec = max(0, int(self.cfg.get('bg_ramp_sec') if self.cfg.get('bg_ramp_sec') is not None else 20))
        if sec <= 0: return n
        k = 1 + int((time.time() - t0) / sec)
        if k >= n: self.bg_ramp.pop(kind, None); return n
        return max(1, k)

    def bg_running(self, kind):
        if kind == 'demo': return len(self.demo_active)
        if kind == 'gen': return len(self.gen_active)
        if kind == 'dl': return sum(1 for d in self.dl.values() if d['state'] == 'run')
        return 0

    def bg_progress(self):
        """每一項的總進度（完成的, 全部）."""
        d = self.demo_done[0]; g = self.gen_done[0]
        D = list(self.dl.values())
        return {'demo': (d, d + len(self.demo_q) + len(self.demo_active)), 'gen': (g, g + len(self.gen_q) + len(self.gen_active)),
                'dl': (sum(1 for x in D if x['state'] == 'done'), sum(1 for x in D if x['state'] in ('done', 'run', 'wait')))}

    def bg_mark(self, kind, name): self.bg_last[kind] = str(name or '')[:200]

    def bg_set_pause(self, kind, on, why='你按的'):
        on = bool(on); was = bool(self.bg_pause.get(kind))
        if on: self.bg_pause[kind] = True
        else: self.bg_pause.pop(kind, None); self.bg_auto.pop(kind, None); self.bg_ramp[kind] = time.time()
        try: self.cfg.set('bg_pause', dict(self.bg_pause)); self.cfg.set('bg_last', dict(self.bg_last))
        except Exception: pass
        if was != on:
            nm = dict((k, n) for k, _i, n in self.BG_KINDS).get(kind, kind)
            self.log.w(f'⏯ 後台：{nm} {"暫停" if on else "繼續（慢慢加速）"}（{why}）')
        return True

    def bg_stop_now(self, kind):
        """立刻停：暫停，正在做的也停掉、放回排隊."""
        self.bg_set_pause(kind, True, '立刻停'); n = 0
        if kind == 'demo':
            for J in list(self.demo_active.values()): J['cancel'] = True; n += 1
        if kind == 'gen':
            for J in list(self.gen_active.values()): J['requeue'] = True; J['cancel'] = True; n += 1
        if kind == 'dl':
            for D in self.dl.values():
                if D['state'] == 'run': D['cancel'] = True; n += 1
        self.log.w(f'⏹ 後台：{kind} 立刻停，{n} 個放回排隊'); return n

    def bg_all(self, on):
        for k, _i, _n in self.BG_KINDS: self.bg_set_pause(k, on, '全部' + ('暫停' if on else '繼續'))
        if not on:
            now = time.time()
            for i, k in enumerate(self.bg_prio()): self.bg_ramp[k] = now + i * 10

    def bg_move(self, kind, d):
        L = self.bg_prio()
        if kind not in L: return L
        i = L.index(kind); j = max(0, min(len(L) - 1, i + int(d))); L[i], L[j] = L[j], L[i]
        self.cfg.set('bg_prio', L); return L

    def bg_view(self):
        """給後台頁／手機：每一項的狀態、先後順序、進度、停在哪."""
        P = self.bg_progress(); L = []; nm = dict((k, (i, n)) for k, i, n in self.BG_KINDS)
        for idx, k in enumerate(self.bg_prio()):
            d, tot = P.get(k, (0, 0)); run_ = self.bg_running(k)
            st = 'pause' if self.bg_pause.get(k) else ('hold' if k in self.bg_auto else ('run' if run_ else 'idle'))
            L.append({'k': k, 'icon': nm[k][0], 'name': nm[k][1], 'state': st, 'running': run_, 'prio': idx + 1, 'held': self.bg_auto.get(k, ''),
                      'last': self.bg_last.get(k, ''), 'done': d, 'total': tot, 'pct': round(d * 100 / tot, 1) if tot else None,
                      'ramp': (self.bg_cap(k, 99) if self.bg_ramp.get(k) else None), 'slow': self.bg_slow.get(k)})
        G = self.bg_gov
        return {'kinds': L, 'cpu': round(float(self.perf.cpu or 0), 1), 'guard': (self.cfg.get('cpu_guard') is not False), 'cpu_max': int(self.cfg.get('cpu_max') or 90),
                'ramp_sec': int(self.cfg.get('bg_ramp_sec') if self.cfg.get('bg_ramp_sec') is not None else 20),
                'log': [f'{time.strftime("%H:%M:%S", time.localtime(t))} {m}' for t, m in list(G['log'])[-30:]][::-1]}

    def _gov_loop(self):
        """電腦太忙（CPU 一直很高）：從最不重要的開始自動讓路；閒下來照順序一項一項放回來."""
        nmf = lambda k: dict((a, c) for a, _b, c in self.BG_KINDS).get(k, k)
        while self.alive():
            try:
                time.sleep(2.0)
                if self.cfg.get('cpu_guard') is False:
                    for k in list(self.bg_auto): self.bg_auto.pop(k, None); self.bg_ramp[k] = time.time()
                    self.bg_slow.clear(); continue
                cpu = float(self.perf.cpu or 0); hi = float(self.cfg.get('cpu_max') or 90); lo = max(10.0, hi - 25); now = time.time(); G = self.bg_gov
                if cpu >= hi:
                    G['lo_t'] = 0.0; G['hi_t'] = G['hi_t'] or now
                    if now - G['hi_t'] >= 12:
                        PR = self.bg_prio()
                        for k in reversed(PR):
                            if k in self.GOV_EXEMPT or self.bg_hold(k) or not self.bg_running(k): continue
                            if not any(self.bg_running(x) and not self.bg_hold(x) and x not in self.GOV_EXEMPT for x in PR[:PR.index(k)]):
                                rn = self.bg_running(k)
                                if rn > 1:
                                    self.bg_slow[k] = rn - 1; G['hi_t'] = now; msg = f'⚖ CPU {cpu:.0f}% 持續 12 秒：{nmf(k)} 降速成同時最多 {rn - 1} 個'
                                    G['log'].append((now, msg)); self.log.w('⏯ 後台：' + msg); break
                                continue
                            self.bg_auto[k] = f'電腦很忙（CPU {cpu:.0f}%），先讓給前面的'; G['hi_t'] = now
                            msg = f'⚖ CPU {cpu:.0f}% 持續 12 秒：{nmf(k)} 先不開新的'; G['log'].append((now, msg)); self.log.w('⏯ 後台：' + msg); break
                        else: G['hi_t'] = now
                elif cpu <= lo:
                    G['hi_t'] = 0.0; G['lo_t'] = G['lo_t'] or now
                    if self.bg_slow and now - G['lo_t'] >= 30 and not self.bg_auto:
                        k = next(iter(self.bg_slow)); self.bg_slow.pop(k, None); self.bg_ramp[k] = now; G['lo_t'] = now
                        msg = f'⚖ CPU 降到 {cpu:.0f}%：{nmf(k)} 不降速了'; G['log'].append((now, msg)); self.log.w('⏯ 後台：' + msg)
                    if self.bg_auto and now - G['lo_t'] >= 30:
                        for k in self.bg_prio():
                            if k in self.bg_auto:
                                self.bg_auto.pop(k, None); self.bg_ramp[k] = now; G['lo_t'] = now
                                msg = f'⚖ CPU 降到 {cpu:.0f}%：{nmf(k)} 繼續'; G['log'].append((now, msg)); self.log.w('⏯ 後台：' + msg); break
                else: G['hi_t'] = 0.0; G['lo_t'] = 0.0
            except Exception: self.log.err('後台總控制'); time.sleep(5)

    # ================================================================ 示範背景工作（新程式照這個樣子寫自己的工作，然後刪掉這段）
    def demo_add(self, n=5, sec=8):
        """排 n 個假的工作（每個 sec 秒），用來看後台頁、手機、熱更新、自動讓路是不是都正常."""
        with self.lock:
            for i in range(int(n)): self.demo_q.append({'name': f'示範工作 #{self.demo_done[0] + len(self.demo_q) + len(self.demo_active) + 1}', 'sec': float(sec)})
        self.log.w(f'示範：排了 {n} 個工作（每個 {sec} 秒）'); return len(self.demo_q)

    def _demo_boss(self):
        while self.alive():
            try:
                n = self.bg_cap('demo', max(1, min(8, int(self.cfg.get('demo_n') or 2))))
                if self.demo_q and len(self.demo_active) < n and not self.bg_hold('demo'):
                    with self.lock: J = self.demo_q.popleft() if self.demo_q else None
                    if J:
                        J['id'] = id(J); self.demo_active[J['id']] = J; self.bg_mark('demo', J['name'])
                        threading.Thread(target=self._demo_job, args=(J,), name='DemoJob', daemon=True).start(); continue
                time.sleep(0.5)
            except Exception: self.log.err('示範工作排程'); time.sleep(5)

    def _demo_job(self, J):
        t = self.task('demo', J['name']); t0 = time.time()
        try:
            while time.time() - t0 < J['sec']:
                if J.get('cancel') or self.stop_all: raise InterruptedError
                t['pct'] = J['pct'] = round((time.time() - t0) / J['sec'] * 100); time.sleep(0.2)
            self.demo_done[0] += 1; self.done(t, 'done', f'{time.time() - t0:.1f} 秒')
        except InterruptedError:
            with self.lock: self.demo_q.appendleft({k: v for k, v in J.items() if k in ('name', 'sec')})
            self.done(t, 'stop', '停止（放回排隊）')
        except Exception as ex: self.log.err('示範工作'); self.done(t, 'fail', str(ex))
        finally: self.demo_active.pop(J['id'], None)

    # ================================================================ 🎨 ComfyUI 生圖（手機／電腦排工作 → 本機 ComfyUI 跑 → 結果存到 Data\outputs）
    GEN_IMG_EXT = {b'\xff\xd8\xff': '.jpg', b'\x89PNG': '.png', b'RIFF': '.webp'}
    VIDEO_EXT = ('.mp4', '.mov', '.webm', '.mkv', '.m4v')
    # ⬇ 內建流程用到的模型：檔名 → (資料夾, 下載網址, 大約大小)。都是 Comfy-Org 官方重新打包的版本
    MODEL_SRC = {
        'wan_animate_2_distill_int8_convrot.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/Wan-Animate-2/resolve/main/diffusion_models/wan_animate_2_distill_int8_convrot.safetensors', 15.5e9),
        'umt5_xxl_fp8_e4m3fn_scaled.safetensors': ('text_encoders', 'https://huggingface.co/Comfy-Org/Wan-Animate-2/resolve/main/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors', 6.27e9),
        'clip_vision_h.safetensors': ('clip_vision', 'https://huggingface.co/Comfy-Org/Wan-Animate-2/resolve/main/clip_vision/clip_vision_h.safetensors', 1.18e9),
        'Wan2_1_VAE_bf16.safetensors': ('vae', 'https://huggingface.co/Comfy-Org/Wan-Animate-2/resolve/main/vae/Wan2_1_VAE_bf16.safetensors', 0.242e9),
        # V0.1.15 MiniMax H3（官方範本用的檔；Comfy-Org 重新打包）＋ turbo 8 步 LoRA（lightx2v）
        'Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors': ('loras', 'https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors', 0.85e9),
        # V0.1.32 Qwen-Image-2.1 Turbo（7B，INT8）／FLUX.2 Klein 4B（4 步）：都塞得進 12GB
        'qwen_image_2.1_turbo_int8_convrot.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors', 7.3e9),
        'qwen3vl_8b_int8_convrot.safetensors': ('text_encoders', 'https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/text_encoders/qwen3vl_8b_int8_convrot.safetensors', 9.0e9),
        'qwen_image_2.1_vae_bf16.safetensors': ('vae', 'https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/vae/qwen_image_2.1_vae_bf16.safetensors', 0.5e9),
        'qwen3vl_8b_w4a8.safetensors': ('text_encoders', 'https://huggingface.co/Comfy-Org/Qwen-Image-2.1/resolve/main/text_encoders/qwen3vl_8b_w4a8.safetensors', 5.88e9),
        'flux-2-klein-4b-fp8.safetensors': ('diffusion_models', 'https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8/resolve/main/flux-2-klein-4b-fp8.safetensors', 4.0e9),
        'qwen_3_4b.safetensors': ('text_encoders', 'https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors', 8.0e9),
        'flux2-vae.safetensors': ('vae', 'https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors', 0.34e9),
        'qwen_image_edit_2511_int8_convrot.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_int8_convrot.safetensors', 20.4e9),
        'minimax_h3_fl2va_pruned_int8_convrot.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors', 19.5e9),
        'minimax_h3_fl2va_int8_convrot.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_int8_convrot.safetensors', 31.7e9),
        'qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors': ('text_encoders', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 14.6e9),
        'qwen3vl_32b_minimax_h3_int8_convrot.safetensors': ('text_encoders', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/text_encoders/qwen3vl_32b_minimax_h3_int8_convrot.safetensors', 25.3e9),
        'minimax_h3_video_vae_int8_convrot.safetensors': ('vae', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_int8_convrot.safetensors', 2.5e9),
        'minimax_h3_video_vae_fp16.safetensors': ('vae', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_video_vae_fp16.safetensors', 4.9e9),
        'minimax_h3_audio_vae_fp32.safetensors': ('vae', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/vae/minimax_h3_audio_vae_fp32.safetensors', 0.6e9),
        'minimax_h3_ref2va_pruned_int8_convrot.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors', 19.5e9),
        'minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors': ('loras', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors', 1.0e9),
        # ComfyUI 0.35 以上的「Fun ControlNet」（照原影片動作重做，例如加一頂帽子）會用到
        'minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors': ('model_patches', 'https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/model_patches/minimax_h3_fun_controlnet_union_pruned_int8_convrot.safetensors', 3.0e9),
        'sdpose_wholebody_fp16.safetensors': ('checkpoints', 'https://huggingface.co/Comfy-Org/SDPose/resolve/main/checkpoints/sdpose_wholebody_fp16.safetensors', 2.0e9),
        'rt_detr_v4-x-hgnet_fp16.safetensors': ('diffusion_models', 'https://huggingface.co/Comfy-Org/SDPose/resolve/main/diffusion_models/rt_detr_v4-x-hgnet_fp16.safetensors', 0.2e9),
        'minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors': ('loras', 'https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors', 1.0e9),
    }

    @classmethod
    def is_video_name(cls, n): return str(n or '').lower().endswith(cls.VIDEO_EXT)

    def gen_boot(self):
        """剛開程式：預設流程放進 Data\\workflows；上次沒做完的工作接著排隊."""
        self.gen_presets()
        try: self.gen_trash_purge_old()
        except Exception: self.log.err('回收桶清理')
        try:                                                                 # V0.2.15 縮圖快取：60 天沒用到的清掉（要看會再做）
            td = self.data / 'thumbs'; old = time.time() - 60 * 86400
            for f in (td.glob('*.jpg') if td.is_dir() else []):
                if f.stat().st_atime < old and f.stat().st_mtime < old: f.unlink()
        except Exception: pass
        try: crashed = json.loads((self.data / 'run_state.json').read_text(encoding='utf-8')).get('clean') is False   # 上次是當機／閃退（不是正常關掉）
        except Exception: crashed = False
        run = self.db.q("SELECT id FROM gen_jobs WHERE state='run'")
        if crashed and run:                                                    # 當機前正在跑的：不自動重跑（可能就是它把電腦弄當的），後面的先暫停，等你決定
            ids = [int(r['id']) for r in run]
            self.db.xm("UPDATE gen_jobs SET state='fail', msg=? WHERE id=?", [('上次電腦／程式意外關閉時正在跑這個（可能就是它把電腦弄當的），先不自動重跑；要的話按「↻ 再跑一次」，或先把寬高、每段幾格調小', i) for i in ids])
            self.bg_set_pause('gen', True, '上次意外關閉')
            self.log.w(f'⚠ 生圖：上次意外關閉時正在跑 #{"、#".join(map(str, ids))} → 標成失敗、不自動重跑；排隊的先暫停（到「🖥 後台」按繼續）')
        rows = self.db.q("SELECT id FROM gen_jobs WHERE state IN ('wait','run') ORDER BY id")
        if rows:
            self.db.x("UPDATE gen_jobs SET state='wait', msg='' WHERE state IN ('wait','run')")
            with self.lock:
                for r in rows: self.gen_q.append(int(r['id']))
            self.log.w(f'生圖：上次沒做完的 {len(rows)} 個接著排隊')

    def gen_presets(self):
        """內建的流程放進 Data\\workflows（每個只放一次，你改過、刪掉都不會再蓋回來；熱更新進來的新流程也會放）."""
        wd = self.data / 'workflows'
        if not self.cfg.get('gen_animate_removed'):                          # V0.1.15 影片換主角（Wan Animate 2）先拿掉：搬到 _old（要用可以搬回來）
            try:
                p = wd / '影片換主角.json'
                if p.exists():
                    bk = wd / '_old'; bk.mkdir(parents=True, exist_ok=True); shutil.move(str(p), str(bk / f'影片換主角_{time.strftime("%Y%m%d_%H%M%S")}.json'))
                    self.log.w('生圖：「影片換主角」流程先拿掉（搬到 Data\\workflows\\_old）')
                self.cfg.set('gen_animate_removed', True); self.cfg.set('gen_preset3_done', True)
            except Exception: self.log.err('拿掉影片換主角')
        for key, fn, nm in (('gen_preset_done', 'wf_GROK.json', 'GROK 改圖'), ('gen_preset2_done', 'wf_merge2.json', '兩張圖合併'),
                            ('gen_preset4_done', 'wf_GROK_fast.json', 'GROK 改圖（快速）'),
                            ('gen_preset5b_done', 'wf_GROK_int8.json', 'GROK 改圖（INT8 快）'),
                            ('gen_preset6_done', 'wf_merge_int8.json', '兩張圖合併（INT8 快）'),
                            ('gen_preset7_done', 'wf_merge3_int8.json', '三張圖合併（人物＋衣服＋場景）')):   # V0.2.69 一次換衣服又換場景   # V0.2.36 圖一人物＋圖二衣服／場景／動作，跟 GROK INT8 同一個模型   # 5b：加速 LoRA 換 2511 專用、取樣 euler／simple（舊的覆蓋，備份到 _old）   # 主模型換官方 INT8 ConvRot：RTX 30 沒有 fp8 運算，int8 直接算比較快   # 快速版：拿掉每張都清記憶體的節點（模型、LoRA、步數都一樣）   # 第一次才放，之後不覆蓋
            pre = HERE / fn
            if not self.cfg.get(key) and pre.exists():
                dst = wd / f'{nm}.json'
                if dst.exists() and key.endswith('b_done'):                 # 改版的預設流程：舊的備份後換掉
                    bk = wd / '_old'; bk.mkdir(exist_ok=True); shutil.copy2(str(dst), str(bk / f'{dst.stem}_{time.strftime("%Y%m%d_%H%M%S")}.json')); dst.unlink()
                if not dst.exists(): shutil.copy2(str(pre), str(dst)); self.log.w(f'生圖：放好預設流程 {nm}')
                self.cfg.set(key, True)

    # ---- 從 ComfyUI 內建的官方範本做流程（例如 MiniMax H3）：ComfyUI 本身就有範本檔（/templates/名字.json），抓下來、子圖展開、改成適合這台的預設
    TEMPLATES = [('video_minimax_h3_i2v', 'H3 照片動起來'), ('video_minimax_h3_multiframe_reference', 'H3 照片動起來（臉穩定）'), ('video_minimax_h3_multiframe_reference', 'H3 照片動起來（臉穩定＋聲音）'), ('video_minimax_h3_t2v', 'H3 文字生影片'), ('video_minimax_h3_i2v', 'H3 圖生影片'), ('video_minimax_h3_r2v', 'H3 參考生影片'),
                 ('video_minimax_h3_fun_controlnet_union', 'H3 照影片動作重做'),
                 ('video_minimax_h3_i2v', 'H3 首尾幀生影片'),                  # V0.2.35 兩張圖（開始、結束畫面）＋一句話 → 中間的動作
                 ('image_qwen_image_2_1_turbo_image_edit', 'Qwen 2.1 Turbo 改圖')]   # V0.1.78 實測後只留這個（23.6 秒、效果可以）＋你的 GROK INT8（40 秒、效果最好）
    # V0.1.33 🧪 比較用的改圖模型（官方範本自動做成流程；模型等你按下載才會抓）
    _OLD_LINEUP = [
        # (流程名字, 範本, 步數, 授權, 一句話)
        ('GROK 改圖（INT8 快）', '', 4, 'Apache 2.0（Qwen-Image-Edit 本身可商用；LoRA 看各自授權）', '你原本的：Qwen-Image-Edit 2511 20B＋Lightning＋snofs；12GB 放不下要邊搬邊算'),
        ('FLUX Klein 4B 改圖', 'image_flux2_klein_image_edit_4b_distilled', 4, 'Apache 2.0（可商用）', '4B 最快，3060 一張約 15 秒'),
        ('Qwen 2.1 Turbo 改圖', 'image_qwen_image_2_1_turbo_image_edit', 8, '研究用', 'Qwen 最新 7B，INT8 約 7GB'),
        ('Qwen 2.1 Turbo 改圖（省記憶體）', 'image_qwen_image_2_1_turbo_image_edit', 8, '研究用', '同上，但文字編碼器換官方 W4A8 版（8.7→5.9GB），12GB 顯卡搬進搬出少很多，「讀圖／提示詞」應該更快'),
        ('FLUX 3 Klein 改圖', 'image_flux3_klein_distilled_image_edit', 16, 'FLUX 社群授權（年收 500 萬美元以下可商用）', '2026/10 BFL 新款 5.6B，官方說改圖品質開源第一'),
        ('Mage-Flow Turbo 改圖', 'image_mage_flow_edit_turbo_int8', 4, 'MIT（可商用）', '微軟 4B，4 步，GEdit 開源前段班'),
        ('Fibo 2 Turbo 改圖', 'image_fibo2_edit_turbo_pe', 4, 'CC BY-NC（不能商用）', 'Bria 8B，Artificial Analysis 改圖榜開源第一'),
        ('FLUX Klein 9B 改圖', 'image_flux2_klein_9b_kv_image_edit', 4, 'FLUX 非商用', '9B＋KV 快取，比 4B 細一點'),
        ('Qwen 2.1 改圖（25 步）', 'image_qwen_image_2_1_image_edit', 25, '研究用', '2.1 原版，慢但最細，拿來當畫質參考'),
        ('FireRed 1.1 改圖', 'image_firered_image_edit1_1', 8, '看 FireRed 授權', '小紅書 Qwen 系 20B＋Lightning 8 步，人像好'),
        ('Boogu 改圖', 'image_boogu_image_0_1_edit_int8', 25, 'Apache 2.0（可商用）', '10B，25 步，慢（一張幾分鐘）'),
        ('JoyAI 改圖', 'image_joyai_image_edit', 40, 'Apache 2.0（可商用）', '京東 16B，40 步，很慢（一張可能 5～10 分鐘）'),
        ('MOSS 改圖', 'image_moss_image_edit', 30, '看 MOSS 授權', '復旦 MOSS，30 步'),
        ('P-H3 改圖', 'image_p_h3_image_edit', 8, '看 PrunaAI／MiniMax 授權', '用你影片已經下載的 H3 大模型（19.5GB）改圖，只要再下載文字編碼器＋VAE＋LoRA；8 步，但 12GB 放不下會邊搬邊算'),
    ]
    # 同一個模型、不同設定（比較頁一欄一種）：(欄名, 流程, {參數名結尾: 值}, 說明)
    _OLD_VARIANTS = [
        ('FLUX Klein 4B（1.5MP 高解析）', 'FLUX Klein 4B 改圖', {'.megapixels': 1.5}, '照片縮到 150 萬像素再改：細節多，慢一點'),
        ('Qwen 2.1 Turbo（768 快速）', 'Qwen 2.1 Turbo 改圖', {'.resolution': 768}, '照片縮到約 768×768：快很多，細節少一點'),
        ('FLUX 3 Klein（8 步快速）', 'FLUX 3 Klein 改圖', {'.steps': 8}, '步數砍一半：快一倍，看品質掉多少'),
        ('Qwen 2.1（12 步）', 'Qwen 2.1 改圖（25 步）', {'.steps': 12}, '原版 25 步砍一半：速度和畫質的中間值'),
        ('Mage-Flow Turbo（1.5MP）', 'Mage-Flow Turbo 改圖', {'.megapixels': 1.5}, '照片大一點再改'),
    ]
    # V0.1.40 其他好用的：文字生圖（不用照片）、去背
    _OLD_EXTRA = [('image_qwen_image_2_1_turbo_t2i', 'Qwen 2.1 Turbo 文字生圖'), ('image_z_image_turbo_int8', 'Z-Image Turbo 文字生圖'),
                 ('image_flux3_klein_distilled_t2i', 'FLUX 3 Klein 文字生圖'), ('image_qwen_image_2_1_background_removal', 'Qwen 2.1 去背'),
                 ('utility_seedvr2_3b_int8_upscale_image', 'SeedVR2 放大 2 倍'), ('utility_video_frame_interpolation', 'FILM 補幀（影片更順）')]
    UPSCALE_WF = 'SeedVR2 放大 2 倍'
    POST = {'upscale': ('SeedVR2 放大 2 倍', 'utility_seedvr2_3b_int8_upscale_image', '✨ 排好放大了（SeedVR2 2 倍）'),
            'interp': ('FILM 補幀（影片更順）', 'utility_video_frame_interpolation', '🎞 排好補幀了（每兩格中間補一格，變順 2 倍）')}
    TPL_CR = {'Qwen 2.1 去背': {'blank_ok': True, 'placeholder': '不用打字，直接按開始就會把背景去掉（輸出透明 PNG）。也可以寫要留下什麼，例如：只留下人'},
              'Qwen 2.1 Turbo 文字生圖': {'placeholder': '描述你要的畫面（中文可以），例如：清晨的台北街頭，一個穿紅色雨衣的女孩撐傘走過，電影感'},
              'Z-Image Turbo 文字生圖': {'placeholder': '描述你要的畫面，例如：一隻橘貓趴在窗邊曬太陽，柔和自然光，寫實照片'},
              'FLUX 3 Klein 文字生圖': {'placeholder': '描述你要的畫面，例如：極簡風海報，標題「夏日特賣」，粉色背景'},
              'FILM 補幀（影片更順）': {'blank_ok': True, 'placeholder': '不用打字：放一支影片，每兩格中間補一格（FILM），播起來更順。影片結果下面也有「🎞 補幀」按鈕'},
              'P-H3 改圖': {'prompt_tpl': 'Request: {action}', 'placeholder': '一句話寫要改什麼（英文效果最好），例如：change the dress to pink silk'},
              'SeedVR2 放大 2 倍': {'blank_ok': True, 'placeholder': '不用打字：照片放大 2 倍、補細節（SeedVR2 3B，1 步）。結果頁每張圖也有「✨ 放大」按鈕'}}
    TPL_SET = {'SeedVR2 放大 2 倍': {('ResizeImageMaskNode', 'resize_type.multiplier'): 2}}   # 範本做好後改的預設值
    VARIANTS = {}
    # V0.1.78 你實測後只要這兩個；其他試過的模型（流程＋模型檔）可以在「🧩 模型檔 → 🧹 精簡」一次刪掉
    LINEUP = [('GROK 改圖（INT8 快）', '', 4, 'Apache 2.0（Qwen-Image-Edit 本身可商用；LoRA 看各自授權）', '效果最好：Qwen-Image-Edit 2511＋Lightning＋snofs，實測一張約 40 秒'),
              ('Qwen 2.1 Turbo 改圖', 'image_qwen_image_2_1_turbo_image_edit', 8, '研究用', '速度最快、效果可以：Qwen 2.1 7B INT8，實測一張約 24 秒')]
    CMP_VARIANTS = []
    EXTRA_TPL = []
    RETIRED_WFS = sorted(({n for n, *_x in _OLD_LINEUP} | {n for _t, n in _OLD_EXTRA} | {'Qwen 2.1 Turbo 改圖（省記憶體）'}) - {'GROK 改圖（INT8 快）', 'Qwen 2.1 Turbo 改圖'})
    for _n, _t, *_x in LINEUP:
        if _t and (_t, _n) not in TEMPLATES: TEMPLATES.append((_t, _n))
    del _n, _t, _x
    TPL_VER = 4                                                              # 範本轉換方式改了 → 自動重抓一次（V0.1.17：子圖欄位對錯位置）

    def gen_from_template(self, tpl, name=None, force=False):
        """抓 ComfyUI 的官方範本存成流程。回傳流程名字；ComfyUI 沒開／沒有這個範本丟錯."""
        tpl = re.sub(r'[^0-9A-Za-z_.-]', '', str(tpl or '')).replace('.json', '')
        if not tpl: raise comfy.ComfyError('範本名稱不對')
        name = name or next((n for t, n in self.TEMPLATES if t == tpl and n not in (self.SIMPLE_NAME, self.FACE_NAME, self.VOICE_NAME, self.FL_NAME)), None) or tpl
        p = self.gen_wf_path(name)
        if p.exists() and not force: return name
        st = self.comfy_status(True)
        if not st['ok']: raise comfy.ComfyError('ComfyUI 沒開，抓不到範本（先開 ComfyUI）')
        C = comfy.Comfy(st['url']); data = None; err = ''
        for path in (f'/templates/{tpl}.json', f'/api/templates/{tpl}.json'):
            try:
                data = C._req(path, timeout=20)
                if data.lstrip()[:1] in (b'{', b'['): break
                data = None; err = '回來的不是範本檔'
            except Exception as ex: err = str(ex)
        if not data: raise comfy.ComfyError(f'你的 ComfyUI 裡找不到範本「{tpl}」（{err[:120]}）：ComfyUI 可能要更新')
        raw = json.loads(data.decode('utf-8-sig'))
        if tpl.startswith('video_minimax_h3'): raw = self._h3_defaults(raw, tpl, name)
        wf = comfy.load_workflow(json.dumps(raw))
        if tpl.startswith(('image_', 'utility_')): wf = self._img_defaults(wf, tpl)
        if name in self.TPL_CR: wf.setdefault('extra', {}).setdefault('cr', {}).update(self.TPL_CR[name])
        for (c, k), v in (self.TPL_SET.get(name) or {}).items():
            for n in wf.get('nodes') or []:
                if n.get('type') == c: n.setdefault('_wset', {})[k] = v
        for old, new in (self.VARIANTS.get(name) or {}).items():           # 同一個範本的變化版：換某個模型檔
            for n in wf.get('nodes') or []:
                wv = n.get('widgets_values')
                if isinstance(wv, list) and wv and wv[0] == old: wv[0] = new
                for k, v in list((n.get('_wset') or {}).items()):
                    if v == old: n['_wset'][k] = new
        self._tpl_models(raw)
        self.gen_wf_save(name, json.dumps(wf, ensure_ascii=False)); self.log.w(f'生圖：從 ComfyUI 官方範本 {tpl} 做好流程「{name}」')
        return name

    @staticmethod
    def _ui_drop(wf, ids):
        """（展開後的）流程拿掉一些節點，連到它們的線一起清掉."""
        ids = set(ids)
        wf['nodes'] = [n for n in wf.get('nodes') or [] if n['id'] not in ids]
        wf['links'] = [l for l in wf.get('links') or [] if l[1] not in ids and l[3] not in ids]
        keep = {l[0] for l in wf['links']}
        for n in wf['nodes']:
            for i in n.get('inputs') or []:
                if i.get('link') is not None and i['link'] not in keep: i['link'] = None
            for o in n.get('outputs') or []:
                if o.get('links'): o['links'] = [x for x in o['links'] if x in keep]
        return wf

    PE_NODES = {'TextGenerate', 'TextGenerateV2', 'PreviewAny'}                 # 「提示詞自動改寫」用的（多跑一個大語言模型，慢）
    SHOW_NODES = {'ImageCompare', 'PreviewAny', 'PreviewImage', 'MarkdownNote', 'Note'}  # 只是給人看的

    @classmethod
    def _tpl_clean(cls, wf, prefix='CR'):
        """官方「改圖」範本（已展開子圖）→ 適合 App 跑：
        ① 範本裡關掉的節點拿掉；② 提示詞如果經過「自動改寫」（TextGenerate → 開關 → PreviewAny）就剪掉，直接吃你打的字；
        ③ SaveImageAdvanced 換成一般 SaveImage；④ 只留跟「存圖」有關的節點（比較滑桿、改寫用的語言模型、沒接的讀圖都拿掉）."""
        N = {n['id']: n for n in wf.get('nodes') or []}; L = wf.get('links') or []; lk = {l[0]: l for l in L}
        for n in N.values():                                                 # 略過（bypass）的節點：後面接它的改接它前面同型別的來源（像 ComfyUI 一樣直通）
            if n.get('mode') != 4: continue
            for l in L:
                if l[1] != n['id']: continue
                outs = n.get('outputs') or []; ot = outs[l[2]].get('type') if l[2] < len(outs) else l[5] if len(l) > 5 else None
                src = next((lk[i['link']] for i in n.get('inputs') or [] if i.get('link') in lk and (i.get('type') == ot or ot in (None, '*'))), None)
                if src is not None and N.get(src[1], {}).get('mode') != 4: l[1], l[2] = src[1], src[2]
        cls._ui_drop(wf, [n['id'] for n in N.values() if n.get('mode') in (2, 4)])
        N = {n['id']: n for n in wf['nodes']}; L = wf['links']; lk = {l[0]: l for l in L}

        def from_pe(nid, depth=0):                                           # 這條線的來源是不是「改寫」那一串
            n = N.get(nid)
            if n is None or depth > 6: return False
            if n.get('type') in cls.PE_NODES: return True
            if n.get('type') in ('ComfySwitchNode', 'StringConcatenate', 'RegexReplace'):
                return any(i.get('link') in lk and from_pe(lk[i['link']][1], depth + 1) for i in n.get('inputs') or [])
            return False
        for n in N.values():
            if n.get('type') in cls.PE_NODES or n.get('type') == 'ComfySwitchNode': continue
            for i in n.get('inputs') or []:
                if i.get('link') in lk and str(i.get('type')) == 'STRING' and from_pe(lk[i['link']][1]):
                    i['link'] = None; (n.get('_wset') or {}).pop(i.get('name'), None)
                    if isinstance(i.get('widget'), dict) and isinstance(n.get('widgets_values'), list):
                        n.setdefault('_wset', {})[i['widget'].get('name') or i['name']] = ''
        wf['links'] = [l for l in L if any(i.get('link') == l[0] for i in (N.get(l[3]) or {}).get('inputs') or [])]
        for n in N.values():
            if n.get('type') == 'SaveImageAdvanced':
                n['type'] = 'SaveImage'; n['widgets_values'] = [prefix]; n['outputs'] = []; n.pop('_wset', None)
                n['inputs'] = [i for i in n.get('inputs') or [] if i.get('name') == 'images']
        for n in list(N.values()):                                           # 開關固定（沒接線）：直接接到選到的那邊，另一邊（例如沒用到的空白畫布）就會被清掉
            if n.get('type') != 'ComfySwitchNode': continue
            ins = {i.get('name'): i for i in n.get('inputs') or []}
            if (ins.get('switch') or {}).get('link') is not None: continue
            sw = (n.get('_wset') or {}).get('switch')
            if sw is None: wv = n.get('widgets_values'); sw = wv[0] if isinstance(wv, list) and wv else None
            if not isinstance(sw, bool): continue
            src = next((l for l in wf['links'] if l[0] == (ins.get('on_true' if sw else 'on_false') or {}).get('link')), None)
            if src is None: continue
            for l in wf['links']:
                if l[1] == n['id']: l[1], l[2] = src[1], src[2]
            for l in wf['links']:
                if l[3] == n['id']: l[3] = -1
            wf['links'] = [l for l in wf['links'] if l[3] != -1]; n['inputs'] = []
        outs = [n['id'] for n in N.values() if n.get('type') in comfy.STD_OUTPUTS and n.get('type') not in cls.SHOW_NODES]
        keep = set(outs); stack = list(outs); src = {}
        for l in wf['links']: src.setdefault(l[3], []).append(l[1])
        while stack:
            x = stack.pop()
            for y in src.get(x, []):
                if y not in keep: keep.add(y); stack.append(y)
        cls._ui_drop(wf, [n['id'] for n in wf['nodes'] if n['id'] not in keep])
        for n in wf['nodes']:
            if n.get('type') == 'LoadImage': n['title'] = '📷 照片'
            if n.get('type') == 'ImageScaleToTotalPixels' and isinstance(n.get('widgets_values'), list) and n['widgets_values'] and n['widgets_values'][0] == 'nearest-exact':
                n['widgets_values'][0] = 'lanczos'                             # 縮圖用 lanczos（nearest 邊緣會鋸齒）
        return wf

    IMG_PASS = {'ImageScaleToTotalPixels', 'ImageScale', 'ResizeImageMaskNode', 'VAEEncode', 'ImageScaleBy', 'FluxKontextImageScale'}

    @classmethod
    def _one_image(cls, wf):
        """範本示範「兩張圖合成」：只留第一張照片（一般改圖）。第二張那一串（縮放、VAE 編碼）拿掉；
        ReferenceLatent 接的是第二張的話直接跳過（條件照原本往下傳）."""
        loads = sorted([n for n in wf['nodes'] if n.get('type') == 'LoadImage'], key=lambda n: n['id'])
        if len(loads) < 2: return wf
        N = {n['id']: n for n in wf['nodes']}; L = wf['links']
        def first_slot(n):                                                    # 接到「image_1／image1／image0」的那張當第一張
            for l in L:
                if l[1] == n['id']:
                    tgt = N.get(l[3]) or {}; nm = next((i.get('name') for i in tgt.get('inputs') or [] if i.get('link') == l[0]), '')
                    if re.search(r'image_?[01]$', str(nm)): return 0
            return 1
        loads.sort(key=lambda n: (first_slot(n), n['id']))
        D = {n['id'] for n in loads[1:]}; ch = True
        while ch:
            ch = False
            for l in L:
                if l[1] in D and l[3] not in D and (N.get(l[3]) or {}).get('type') in cls.IMG_PASS: D.add(l[3]); ch = True
        for n in list(wf['nodes']):
            if n.get('type') != 'ReferenceLatent': continue
            lat = next((i for i in n.get('inputs') or [] if i.get('name') == 'latent'), None); cnd = next((i for i in n.get('inputs') or [] if i.get('name') == 'conditioning'), None)
            src_l = next((l for l in L if lat and l[0] == lat.get('link')), None); src_c = next((l for l in L if cnd and l[0] == cnd.get('link')), None)
            if src_l and src_l[1] in D and src_c:
                for l in L:
                    if l[1] == n['id']: l[1], l[2] = src_c[1], src_c[2]
                D.add(n['id'])
        return cls._ui_drop(wf, D)

    @classmethod
    def _img_defaults(cls, wf, tpl=''):
        """官方改圖範本 → 一張照片的一般改圖：清掉改寫／比較節點、只留第一張照片、加速 LoRA 打開、Qwen 2.1 照片縮到約 1024."""
        wf = cls._one_image(cls._tpl_clean(wf, re.sub(r'^image_', '', tpl)[:24] or 'CR'))
        for n in wf['nodes']:
            t = str(n.get('title') or '').lower(); wv = n.get('widgets_values')
            if n.get('type') == 'PrimitiveBoolean' and ('lightning' in t or 'turbo' in t) and isinstance(wv, list) and wv: wv[0] = True   # 例如 FireRed：開 Lightning 8 步
            if n.get('type') == 'TextEncodeQwenImage21':
                n.setdefault('_wset', {})['resolution'] = 1024
                if isinstance(wv, list) and wv: wv[0] = ''
        return wf

    def _tpl_models(self, raw):
        """範本裡寫的模型下載網址記下來（MODEL_SRC 沒列的也能一鍵下載）."""
        try:
            X = dict(self.cfg.get('model_src_x') or {}); n0 = len(X)
            for n in (raw.get('nodes') or []) + [m for g in (raw.get('definitions') or {}).get('subgraphs') or [] for m in g.get('nodes') or []]:
                for m in (n.get('properties') or {}).get('models') or []:
                    nm, url, d = m.get('name'), m.get('url'), m.get('directory')
                    if nm and url and d and url.startswith('https://huggingface.co/') and nm not in self.MODEL_SRC: X[nm] = [d, url, X.get(nm, [0, 0, None])[2]]
            if len(X) != n0: self.cfg.set('model_src_x', X)
        except Exception: self.log.err('記範本的模型網址')

    def model_src(self, fn):
        """模型檔名 → (資料夾, 網址, 大小或 None)."""
        b = os.path.basename(str(fn).replace('\\', '/'))
        s = self.MODEL_SRC.get(b)
        if s: return s
        x = (self.cfg.get('model_src_x') or {}).get(b)
        return tuple(x) if x else None

    SIMPLE_NAME = 'H3 照片動起來'
    # V0.2.40 照 MiniMax 官方提示詞指南（I2VA）：第一行固定的對齊句，空一行，再寫 integrated_multimodal_description／overall_soundscape／non_diegetic_music
    SIMPLE_TPL = ('For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n'
                  'integrated_multimodal_description: [Shot 1] Live-action, the person shown in <Picture 1> {action}. The video starts exactly from <Picture 1>: keep the same person, '
                  'face, hairstyle, outfit, background, lighting, colors and framing. Natural, smooth and realistic motion. Static camera, one continuous shot, no new people, no on-screen text.\n'
                  'overall_soundscape: Quiet natural ambience matching the scene.\nnon_diegetic_music: N/A')

    FL_NAME = 'H3 首尾幀生影片'
    FL_TPL = ('How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video, '
              'and Picture 2 (from Shot 1) aligns with the {end}-second mark of the target video.\n\n'
              'integrated_multimodal_description: [Shot 1] Live-action, the scene begins exactly as Picture 1; {action}, with natural, smooth and continuous motion, '
              'and ends exactly as Picture 2. Keep the same people, faces, hairstyles, outfits and place as in the two pictures. One continuous shot, no new people, no on-screen text.\n'
              'overall_soundscape: Quiet natural ambience matching the scene.\nnon_diegetic_music: N/A')
    FACE_NAME = 'H3 照片動起來（臉穩定）'
    FACE_TPL = ('subject_definitions:\n<Subject 1> is the person in <Picture 1>.\n<Picture 1> is the first frame of [Shot 1].\n\n'
                'summary:\n[keyframe completion + reference generation] The video starts exactly from <Picture 1>. <Subject 1> {action}.\n\n'
                "retention_analysis:\n<Subject 1> (appears in [Shot 1]): fully_preserved - <Subject 1>'s face, facial identity, facial features, skin tone, hairstyle, makeup and outfit "
                "stay exactly the same as in <Picture 1> for the whole video.\n<Picture 1> ([Shot 1] first frame): fully_preserved - the video starts exactly from <Picture 1>'s framing, "
                'subject state, background and lighting.\n\ndetailed_description:\n[Shot 1] The shot begins from <Picture 1>. Static camera. <Subject 1> {action}, with natural, smooth '
                'and realistic motion. The face stays clearly recognizable as the same person in every frame. No cuts, no new people, no text.\n\n'
                'overall_soundscape:\nQuiet natural ambience matching the scene.\n\nnon_diegetic_music:\nN/A')

    @classmethod
    def _h3_face(cls, wf):
        """官方多格參考範本 → 臉穩定版：照片同時是 <Picture 1> 參考圖（鎖住長相）和第 0 格的引導圖（第一格就是原圖）；其他引導格拿掉；參考圖精細度 max（臉更像）."""
        N = {n['id']: n for n in wf.get('nodes') or []}; L = wf.get('links') or []
        guides = sorted([n for n in N.values() if n.get('type') == 'MiniMaxH3AddGuide'], key=lambda n: n['id'])
        r2v = next((n for n in N.values() if n.get('type') == 'MiniMaxH3ReferenceToVideo'), None)
        if not guides or r2v is None: return wf
        lk = {l[0]: l for l in L}
        ref = next((lk[i['link']][1] for i in r2v.get('inputs') or [] if i.get('name') == 'ref_images.ref_image_0' and i.get('link') in lk), None)
        g0 = guides[0]; drop = set()
        for i in g0.get('inputs') or []:
            if i.get('name') == 'image' and i.get('link') in lk and ref is not None:
                drop.add(lk[i['link']][1]); lk[i['link']][1] = ref; lk[i['link']][2] = 0
            if i.get('name') == 'frame_idx' and i.get('link') in lk:      # 第幾秒 → 0（第一格）
                m = N.get(lk[i['link']][1])
                for j in (m or {}).get('inputs') or []:
                    src = N.get(lk[j['link']][1]) if j.get('link') in lk else None
                    if src is not None and src.get('type') == 'PrimitiveFloat': src['widgets_values'][0] = 0
        for l in L:
            if l[1] == guides[-1]['id'] and guides[-1] is not g0: l[1] = g0['id']; l[2] = 0   # 後面的引導拿掉：取樣直接接第一個引導的輸出
        for g in guides[1:]:
            drop.add(g['id'])
            for i in g.get('inputs') or []:
                if i.get('name') in ('image', 'frame_idx') and i.get('link') in lk:
                    src = lk[i['link']][1]; drop.add(src)
                    if i.get('name') == 'frame_idx':
                        for j in (N.get(src) or {}).get('inputs') or []:
                            if j.get('link') in lk: drop.add(lk[j['link']][1])
        drop.discard(ref); drop.discard(g0['id'])
        wf['nodes'] = [n for n in wf['nodes'] if n['id'] not in drop]
        wf['links'] = [l for l in L if l[1] not in drop and l[3] not in drop]
        keep = {l[0] for l in wf['links']}
        for n in wf['nodes']:
            for i in n.get('inputs') or []:
                if i.get('link') is not None and i['link'] not in keep: i['link'] = None
            for o in n.get('outputs') or []:
                if o.get('links'): o['links'] = [x for x in o['links'] if x in keep]
        if isinstance(r2v.get('widgets_values'), list) and len(r2v['widgets_values']) >= 5: r2v['widgets_values'][4] = 'max'
        if N.get(ref): N[ref]['title'] = '📷 照片（第一格＋臉的參考）'
        return wf

    VOICE_NAME = 'H3 照片動起來（臉穩定＋聲音）'

    @classmethod
    def _h3_voice(cls, wf):
        """臉穩定版再加一個 mp4 格子：GetVideoComponents 抽出聲音 → <Audio 1>（參考聲音：說話的嗓音照這段）."""
        nodes = wf.get('nodes') or []; L = wf.setdefault('links', [])
        r2v = next((n for n in nodes if n.get('type') == 'MiniMaxH3ReferenceToVideo'), None)
        if r2v is None: return wf
        nid = max(int(n['id']) for n in nodes) + 1; lid = max([int(l[0]) for l in L] + [int(wf.get('last_link_id') or 0)]) + 1
        ins = r2v.setdefault('inputs', [])
        k = next((i for i, x in enumerate(ins) if x.get('name') == 'ref_audios.ref_audio_0'), None)
        if k is None: ins.append({'name': 'ref_audios.ref_audio_0', 'type': 'AUDIO', 'link': None}); k = len(ins) - 1
        nodes.append({'id': nid, 'type': 'LoadVideo', 'title': '🎤 聲音來源（mp4，抓裡面的聲音）', 'mode': 0, 'inputs': [],
                      'outputs': [{'name': 'VIDEO', 'type': 'VIDEO', 'links': [lid]}], 'widgets_values': ['example.mp4', 'image'], 'properties': {}})
        nodes.append({'id': nid + 1, 'type': 'GetVideoComponents', 'mode': 0, 'inputs': [{'name': 'video', 'type': 'VIDEO', 'link': lid}],
                      'outputs': [{'name': 'images', 'type': 'IMAGE', 'links': []}, {'name': 'audio', 'type': 'AUDIO', 'links': [lid + 1]}, {'name': 'fps', 'type': 'FLOAT', 'links': []}],
                      'widgets_values': [], 'properties': {}})
        L.append([lid, nid, 0, nid + 1, 0, 'VIDEO']); L.append([lid + 1, nid + 1, 1, r2v['id'], k, 'AUDIO']); ins[k]['link'] = lid + 1
        wf['last_node_id'] = nid + 1; wf['last_link_id'] = lid + 1
        return wf

    @classmethod
    def _h3_defaults(cls, wf, tpl, name=''):
        """MiniMax H3 範本（還沒展開子圖）→ 12GB 顯示卡的預設：
        開 Turbo／Lightning LoRA（步數少很多）；「照影片動作重做」加一個參考圖格子（例如戴好帽子的人），影片／參考圖取好懂的名字."""
        SG = {str(g.get('id')): g for g in (wf.get('definitions') or {}).get('subgraphs') or []}
        nodes = wf.get('nodes') or []
        for n in nodes:
            g = SG.get(str(n.get('type'))); wv = n.get('widgets_values')
            if g and isinstance(wv, list):                                   # 子圖節點：照子圖輸入的順序找「turbo_mode」那一格
                ins = {x.get('name'): x for x in n.get('inputs') or []}; k = 0
                for gi in g.get('inputs') or []:
                    if str(gi.get('type')) not in comfy.WIDGET_TYPES: continue
                    lab = (ins.get(gi.get('name')) or {}).get('label') or gi.get('label') or ''
                    if lab == 'turbo_mode' and k < len(wv): wv[k] = True
                    if lab == 'duration' and name in (cls.SIMPLE_NAME, cls.FACE_NAME, cls.VOICE_NAME, cls.FL_NAME) and k < len(wv): wv[k] = 4      # 照片動起來：預設 4 秒
                    k += 1
            t = str(n.get('title') or '')
            if n.get('type') == 'PrimitiveBoolean' and 'lightning' in t.lower() and isinstance(wv, list) and wv: wv[0] = True
            if n.get('type') == 'LoadVideo': n['title'] = '🎬 原影片（照它的動作）'
            if n.get('type') == 'ResolutionSelector' and ('i2v' in tpl or name in (cls.FACE_NAME, cls.VOICE_NAME)) and isinstance(wv, list) and wv: wv[0] = comfy.MATCH_ASPECT   # 圖生影片：預設比例跟原圖一樣
            if name in (cls.FACE_NAME, cls.VOICE_NAME) and n.get('type') == 'PrimitiveFloat' and 'duration' in t.lower() and isinstance(wv, list) and wv: wv[0] = 4
        if name == cls.VOICE_NAME:                                          # 臉穩定＋聲音：<Audio 1> 是這個人的嗓音
            wf = cls._h3_voice(cls._h3_face(wf))
            vt = cls.FACE_TPL.replace('<Picture 1> is the first frame of [Shot 1].', "<Picture 1> is the first frame of [Shot 1].\n<Audio 1> is <Subject 1>'s voice: whenever <Subject 1> speaks, use exactly the same voice timbre, pitch and accent as <Audio 1>.")
            vt = vt.replace('overall_soundscape:\nQuiet natural ambience matching the scene.', "overall_soundscape:\nQuiet natural ambience matching the scene; any speech by <Subject 1> uses the voice from <Audio 1>.")
            wf.setdefault('extra', {})['cr'] = {'simple': True, 'prompt_tpl': vt, 'placeholder': '要他做什麼／說什麼？例如：揮手，笑著說「嗨，大家好」'}
        if name == cls.FACE_NAME:
            wf = cls._h3_face(wf)
            wf.setdefault('extra', {})['cr'] = {'simple': True, 'prompt_tpl': cls.FACE_TPL, 'placeholder': '要他做什麼動作？例如：揮手、轉頭對鏡頭微笑（這個版本臉比較不會跑掉）'}
        if name == cls.FL_NAME:                                              # V0.2.35 首尾幀：第二張圖接到 MiniMaxH3ImageToVideo 的 last_frame（在子圖裡，送出前才接）
            for n in nodes:
                if n.get('type') == 'LoadImage': n['title'] = '🎬 首幀（開始畫面）'
            wf.setdefault('extra', {})['cr'] = {'simple': True, 'prompt_tpl': cls.FL_TPL, 'placeholder': '中間發生什麼？例如：她從坐著慢慢站起來走向鏡頭',
                                                'xslots': [{'title': '🏁 尾幀（結束畫面）', 'cls': 'MiniMaxH3ImageToVideo', 'input': 'last_frame', 'like': 'first_frame'}]}
        if name == cls.SIMPLE_NAME:                                          # 只打動作：程式自己包成 H3 的提示詞；影片比例自動跟照片一樣
            wf.setdefault('extra', {})['cr'] = {'simple': True, 'prompt_tpl': cls.SIMPLE_TPL,
                                                'placeholder': '要他做什麼動作？例如：揮手、轉頭對鏡頭微笑、慢慢走過來'}
        if 'fun_controlnet' in tpl:                                          # 參考圖：接到 MiniMaxH3ReferenceToVideo 的 ref_image_0
            r2v = next((n for n in nodes if n.get('type') == 'MiniMaxH3ReferenceToVideo'), None)
            ins = (r2v or {}).get('inputs') or []
            k = next((i for i, x in enumerate(ins) if x.get('name') == 'ref_images.ref_image_0'), None)
            if r2v is not None and k is not None and ins[k].get('link') is None:
                nid = max(int(n['id']) for n in nodes) + 1; lid = max([int(L[0]) for L in wf.get('links') or []] + [int(wf.get('last_link_id') or 0)]) + 1
                nodes.append({'id': nid, 'type': 'LoadImage', 'title': '🧢 參考圖（例如戴好帽子的人）', 'mode': 0, 'pos': [0, 0], 'size': [300, 300],
                              'inputs': [], 'outputs': [{'name': 'IMAGE', 'type': 'IMAGE', 'links': [lid]}, {'name': 'MASK', 'type': 'MASK', 'links': []}],
                              'widgets_values': ['example.png', 'image'], 'properties': {}})
                wf.setdefault('links', []).append([lid, nid, 0, r2v['id'], k, 'IMAGE']); ins[k]['link'] = lid
                wf['last_node_id'] = nid; wf['last_link_id'] = lid
        return wf

    def gen_templates_auto(self):
        """ComfyUI 開著時：還沒有 H3 流程就自動抓一次（一分鐘最多試一次）."""
        if time.time() - getattr(self, '_tpl_try', 0) < 60: return
        self._tpl_try = time.time()
        old = int(self.cfg.get('tpl_ver') or 0) < self.TPL_VER
        for tpl, nm in self.TEMPLATES:
            key = 'tpl_done_' + nm; redo = old and (self.cfg.get(key) or self.cfg.get('tpl_done_' + tpl)) and self.gen_wf_path(nm).exists()   # 舊版轉錯的：重抓（舊的會備份到 _old）
            if (self.cfg.get(key) and not redo) or not self.comfy_status()['ok']: continue
            F = self.__dict__.setdefault('_tpl_fail', {})
            if time.time() - F.get(nm, 0) < 1800: continue                     # 做不了的（例如 ComfyUI 太舊沒有這個範本）：30 分鐘後再試，不要每分鐘洗 LOG
            try: self.gen_from_template(tpl, nm, force=bool(redo)); self.cfg.set(key, True); F.pop(nm, None)
            except Exception as ex: F[nm] = time.time(); self.log.w(f'生圖：範本 {tpl} 還做不了（30 分鐘後再試）：{ex}')
        if self.comfy_status()['ok']: self.cfg.set('tpl_ver', self.TPL_VER)

    def _awake_loop(self):
        """生圖、下載模型進行中（含排隊）：叫 Windows 不要睡眠。電腦在跑顯示卡時進入睡眠，顯示卡驅動來不及回應會藍畫面（DRIVER_POWER_STATE_FAILURE 0x9F）。
        螢幕還是可以照設定關掉；都做完就放開，Windows 照原本的設定睡眠."""
        if not IS_WIN: return
        import ctypes
        ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001; on = False
        try:
            while self.alive():
                want = self.cfg.get('keep_awake') is not False and bool(self.gen_active or self.gen_q or any(d['state'] in ('run', 'wait') for d in self.dl.values()))
                if want != on:
                    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if want else 0)); on = want
                    self.log.w('🔋 ' + ('生圖／下載進行中：先不讓電腦睡眠' if want else '都做完了：電腦照原本的設定睡眠'))
                time.sleep(5)
        except Exception: self.log.err('不讓電腦睡眠')
        finally:
            try: ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
            except Exception: pass

    # ---- ComfyUI 連線
    def comfy_status_bg(self):
        """手機每 2 秒問一次狀態用：直接回上次的結果，太舊就在背景重查（不讓手機頁面卡在等 ComfyUI 回話）."""
        if time.time() - self.comfy_st['t'] > 5 and not getattr(self, '_cst_busy', False):
            self._cst_busy = True
            def go():
                try: self.comfy_status()
                except Exception: pass
                finally: self._cst_busy = False
            threading.Thread(target=go, name='ComfyStatus', daemon=True).start()
        return self.comfy_status(cached=True)

    def comfy_status(self, force=False, cached=False):
        """{'ok','url','ver','gpu','vram','err'}（5 秒內不重查）。cached＝True：只看上次的結果，不連線（握手用，不能卡住）.
        V0.3.71 連過的網址先用比較長的等待（ComfyUI 正在載模型時會慢），連續 2 次、超過 20 秒都沒回才算「連不到」."""
        S = self.comfy_st
        if not cached and (force or time.time() - S['t'] > 5):
            known = S.get('url') or ''; url, st = '', ''; cu = str(self.cfg.get('comfy_url') or '')
            if cu != S.get('cfgu', cu): known = ''                          # 設定改了網址：重新找
            S['cfgu'] = cu
            if known:
                try: url, st = known, comfy.Comfy(known).get_json('/system_stats', timeout=8)
                except Exception as ex: url, st = '', str(ex)
            if not url and (not known or force or S.get('bad', 0) >= 1):
                url, st = comfy.find_url(self.cfg.get('comfy_url') or known)
            if url:
                if not S.get('url'): S['up_t'] = time.time()                    # 剛連上（剛開／重開過）：重新算「開了多久」
                S.update(url=url, stats=st, err='', bad=0, ok_t=time.time())
            else:
                S['bad'] = S.get('bad', 0) + 1
                if not known or S['bad'] >= 2 and time.time() - S.get('ok_t', 0) > 20: S.update(url='', stats=None, err=str(st))
            S['t'] = time.time()
            if S['url'] and S['url'] != S.get('logged'): S['logged'] = S['url']; self.log.w(f'生圖：連上 ComfyUI {S["url"]}'); threading.Thread(target=self._comfy_learn, name='ComfyLearn', daemon=True).start()
        st = S.get('stats') or {}; sysi = st.get('system') or {}; dev = (st.get('devices') or [{}])[0] if st.get('devices') else {}
        return {'ok': bool(S['url']), 'url': S['url'], 'err': S['err'], 'ver': sysi.get('comfyui_version', ''), 'gpu': dev.get('name', ''),
                'vram': [dev.get('vram_free'), dev.get('vram_total')] if dev else None, 'ram': [sysi.get('ram_free'), sysi.get('ram_total')] if sysi.get('ram_total') else None}

    def _obj_info(self, C):
        """ComfyUI 節點的說明（欄位型別、下拉選項）。連得上就問（每次開程式每個節點問一次），結果存到 Data\\object_info.json，ComfyUI 關著也有選單."""
        def get(cls):
            if C is not None and cls not in self.info_fresh:
                try:
                    v = C.object_info(cls); self.info_fresh.add(cls)
                    if v is not None or cls not in self.comfy_info: self.comfy_info[cls] = v; self._info_dirty = True
                except comfy.ComfyDown: pass
                except Exception: self.info_fresh.add(cls)
            return self.comfy_info.get(cls)
        return get

    def _info_save(self):
        if not getattr(self, '_info_dirty', False): return
        try:
            tmp = self.data / 'object_info.tmp'; tmp.write_text(json.dumps(self.comfy_info, ensure_ascii=False), encoding='utf-8'); os.replace(str(tmp), str(self.data / 'object_info.json'))
            self._info_dirty = False
        except Exception: self.log.err('存 object_info')

    # ---- 流程
    def gen_wf_path(self, name):
        n = re.sub(r'[\\/:*?"<>|]', '_', str(name or '')).strip().strip('.')
        return self.data / 'workflows' / (n + '.json') if n else None

    def gen_wf_load(self, name):
        p = self.gen_wf_path(name)
        if p is None or not p.exists(): raise comfy.ComfyError(f'找不到流程「{name}」（Data\\workflows 裡沒有這個檔）')
        return comfy.load_workflow(p.read_bytes())

    QM_NAME = '兩張圖合併（Qwen 快）'

    def _derive_qwen_merge(self):
        """V0.2.84 從「Qwen 2.1 Turbo 改圖」複製一份合併版：第二張圖送出前接到 TextEncodeQwenImage21 的 images.image_2（Qwen 2.1 原生支援多張參考圖），比 GROK 版快."""
        src, dst = self.gen_wf_path('Qwen 2.1 Turbo 改圖'), self.gen_wf_path(self.QM_NAME)
        if not src or not src.exists() or not dst or dst.exists() or self.cfg.get('qmerge_done'): return
        wf = comfy.load_workflow(src.read_bytes())
        if not comfy.is_ui_format(wf) or not any(n.get('type') == 'TextEncodeQwenImage21' for n in wf.get('nodes') or []): return
        for n in wf.get('nodes') or []:
            if n.get('type') == 'LoadImage': n['title'] = '圖一：人物'
        cr = wf.setdefault('extra', {}).setdefault('cr', {}); cr['xslots'] = [{'title': '圖二：衣服／場景／動作', 'cls': 'TextEncodeQwenImage21', 'input': 'images.image_2'}]
        cr['placeholder'] = '例如：讓圖1的人穿上圖2的衣服'
        self.gen_wf_save(self.QM_NAME, json.dumps(wf, ensure_ascii=False)); self.cfg.set('qmerge_done', True); self.log.w(f'生圖：做好「{self.QM_NAME}」（從 Qwen 2.1 Turbo 改圖複製）')

    COMFY_WF = [('ripple_push_done', 'wf_ltx_ripple.json', 'LTX-Ripple 影片換髮型（3060）.json')]   # V0.3.34 直接放進 ComfyUI 的工作流清單（在 ComfyUI 裡開來用）

    def comfy_push_workflows(self):
        """V0.3.34 內建的 ComfyUI 工作流（App 不跑、給你在 ComfyUI 裡用）放進 ComfyUI 左邊「工作流」清單；只放一次，你改過、刪掉都不會再蓋回來."""
        st = self.comfy_status()
        if not st.get('ok'): return
        C = comfy.Comfy(st['url'])
        for key, fn, nm in self.COMFY_WF:
            src = HERE / fn
            if self.cfg.get(key) or not src.exists(): continue
            try:
                new = C.userdata_put('workflows/' + nm, src.read_bytes())
                self.cfg.set(key, True); self.log.w(f'ComfyUI：工作流「{nm}」' + ('放好了（ComfyUI 左邊「工作流」清單）' if new else '已經有了，沒蓋掉'))
            except Exception as ex: self.log.w(f'ComfyUI：放工作流「{nm}」失敗，等一下再試：{ex}')

    def gen_workflows(self):
        """[{'name','need_img','pos','neg','outputs','err'}]（檔案沒變就用上次分析的）."""
        try: self.gen_presets()
        except Exception: self.log.err('生圖：放內建流程')
        try: self._derive_qwen_merge()
        except Exception: self.log.err('生圖：做 Qwen 合併流程')
        if not self.cfg.get('ripple_push_done') and time.time() - getattr(self, '_rip_try', 0) >= 60:
            self._rip_try = time.time(); threading.Thread(target=self.comfy_push_workflows, name='PushWF', daemon=True).start()
        if time.time() - getattr(self, '_tpl_try', 0) >= 60 and (int(self.cfg.get('tpl_ver') or 0) < self.TPL_VER or not all(self.cfg.get('tpl_done_' + n) for _t, n in self.TEMPLATES)):
            threading.Thread(target=self.gen_templates_auto, name='Templates', daemon=True).start()   # 背景抓，不卡畫面
        L = []
        for p in sorted((self.data / 'workflows').glob('*.json'), key=lambda x: x.stem.lower()):
            try:
                key = (p.stat().st_mtime, p.stat().st_size, len(self.comfy_info)); c = self.wf_cache.get(p.name)
                if not c or c[0] != key:
                    try:
                        wf = comfy.load_workflow(p.read_bytes()); api = comfy.ui_to_api(wf, self._obj_info(None)) if comfy.is_ui_format(wf) else wf
                        info = dict(comfy.summary(api), fmt='一般' if comfy.is_ui_format(wf) else 'API', err='',
                                    cr={k: v for k, v in (((wf.get('extra') or {}).get('cr') or {}) if isinstance(wf, dict) else {}).items() if k in ('simple', 'placeholder', 'match_aspect', 'blank_ok', 'xslots')})
                        xs = [x for x in (info['cr'].get('xslots') or []) if isinstance(x, dict) and x.get('cls') and x.get('input')]
                        if xs:                                               # V0.2.35 額外的照片格子（例如首尾幀的「尾幀」），送出前才接進流程
                            info['n_img'] = int(info.get('n_img') or 0) + len(xs); info['slots'] = list(info.get('slots') or []) + [str(x.get('title') or '圖') for x in xs]
                            info['kinds'] = list(info.get('kinds') or ['image'] * (info['n_img'] - len(xs))) + ['image'] * len(xs); info['need_img'] = True
                    except Exception as ex: info = {'err': str(ex)}
                    c = (key, info); self.wf_cache[p.name] = c
                L.append(dict(c[1], name=p.stem))
            except Exception: self.log.err(f'生圖：讀流程 {p.name}')
        return L

    def gen_wf_save(self, name, data):
        wf = comfy.load_workflow(data)                                      # 看不懂就丟例外
        nm = re.sub(r'\.json$', '', str(name or 'workflow'), flags=re.I); p = self.gen_wf_path(nm)
        if p is None: raise comfy.ComfyError('檔名不對')
        if p.exists():
            bk = self.data / 'workflows' / '_old'; bk.mkdir(exist_ok=True); shutil.copy2(str(p), str(bk / f'{p.stem}_{time.strftime("%Y%m%d_%H%M%S")}.json'))
        p.write_text(json.dumps(wf, ensure_ascii=False, indent=1), encoding='utf-8'); self.wf_cache.pop(p.name, None)
        self.oplog('匯入流程', p.name); self.log.w(f'生圖：匯入流程 {p.name}'); return p.stem

    def gen_params(self, wf):
        """這個流程可以調的參數（分組；常用的打開、其他收合）。ComfyUI 連得上時順便更新下拉選項."""
        p = self.gen_wf_path(wf)
        if p is None or not p.exists(): raise comfy.ComfyError(f'找不到流程「{wf}」')
        st = self.comfy_status(); C = comfy.Comfy(st['url']) if st['ok'] else None
        key = (p.stat().st_mtime, p.stat().st_size, bool(C), len(self.comfy_info)); c = self.par_cache.get(wf)
        if c and c[0] == key: return c[1]
        T = comfy.tunables(self.gen_wf_load(wf), self._obj_info(C)); self._info_save()
        self.par_cache[wf] = ((p.stat().st_mtime, p.stat().st_size, bool(C), len(self.comfy_info)), T); return T

    @staticmethod
    def _hash(x): return hashlib.sha1(json.dumps(x, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()[:12]

    @staticmethod
    def param_brief(P):
        """參數摘要（給清單看）：邊長 960・4 步・CFG 1・euler…"""
        P = P or {}; out = []
        for suf, fmt in (('.scale_to_length', '邊長 {}'), ('.megapixels', '{} MP'), ('.width', '寬 {}'), ('.height', '高 {}'), ('.steps', '{} 步'), ('.cfg', 'CFG {}'),
                         ('.denoise', '強度 {}'), ('.sampler_name', '{}'), ('.scheduler', '{}')):
            for k, v in P.items():
                if k.endswith(suf) and not k.startswith('_'): out.append(fmt.format(v)); break
        return '・'.join(out)

    # ---- ⬇ 模型：流程要哪些模型、ComfyUI 有沒有（問 ComfyUI 的下拉選單，不翻你的資料夾）、缺的一鍵下載
    def gen_models(self, wf, C=None):
        if C is None:
            st = self.comfy_status(); C = comfy.Comfy(st['url']) if st['ok'] else None
        get = self._obj_info(C); out = []
        for cls, inp, fn, folder in comfy.required_models(self.gen_wf_load(wf), get):
            typ, _o = comfy._spec(get(cls), inp); opts = typ if isinstance(typ, list) else (_o.get('options') if typ == 'COMBO' else None)
            ok = None if opts is None else (fn in opts or fn.replace('/', '\\') in opts or fn.replace('\\', '/') in opts)
            src = self.model_src(fn)
            out.append({'file': fn, 'folder': folder, 'node': cls, 'ok': ok, 'known': bool(src),
                        'size': src[2] if src else None, 'dl': {k: v for k, v in (self.dl.get(fn) or {}).items() if k != 'cancel'}})
        self._info_save()
        for m in out:                                                          # ComfyUI 沒開時不知道有沒有 → 當作有（不擋）
            if m['ok'] is None: m['ok'] = True; m['unknown'] = True
        return out

    def _models_dir(self, folder):
        """ComfyUI 放這種模型的資料夾：先問 ComfyUI（/internal/folder_paths），問不到看 ComfyUI Desktop 的設定."""
        try:
            st = self.comfy_status()
            if st['ok']:
                fp = comfy.Comfy(st['url']).get_json('/internal/folder_paths', timeout=10).get(folder)
                paths = fp[0] if isinstance(fp, list) and fp and isinstance(fp[0], list) else (fp if isinstance(fp, list) else [])
                paths = [x for x in paths if isinstance(x, str)]
                pick = next((x for x in paths if 'shared' in x.lower() and os.path.isdir(x)), None) or next((x for x in paths if os.path.isdir(x)), None)
                if pick: return Path(pick)
        except Exception: pass
        try:
            S = json.loads((Path(os.environ.get('APPDATA', '')) / 'Comfy Desktop' / 'settings.json').read_text(encoding='utf-8'))
            d = Path((S.get('modelsDirs') or [])[0]) / folder; d.mkdir(parents=True, exist_ok=True); return d
        except Exception: return None

    def dl_add(self, files):
        n = 0
        for fn in files:
            src = self.model_src(fn)
            if not src: continue
            D = self.dl.get(fn)
            if D and D['state'] in ('wait', 'run', 'done'): continue
            self.dl[fn] = {'file': fn, 'folder': src[0], 'url': src[1], 'size': src[2], 'got': 0, 'state': 'wait', 'msg': '排隊中', 'speed': 0}; n += 1
        if n: self.log.w(f'⬇ 下載模型：排了 {n} 個')
        return n

    def dl_cancel(self, fn):
        D = self.dl.get(fn)
        if not D: return False
        if D['state'] == 'run': D['cancel'] = True
        elif D['state'] == 'wait': D['state'] = 'stop'; D['msg'] = '已取消'
        return True

    def _dl_boss(self):
        while self.alive():
            try:
                D = next((d for d in self.dl.values() if d['state'] == 'wait'), None)
                if D and not self.bg_hold('dl') and not any(d['state'] == 'run' for d in self.dl.values()):
                    D['state'] = 'run'; self.bg_mark('dl', D['file']); threading.Thread(target=self._dl_job, args=(D,), name='DlJob', daemon=True).start()
                time.sleep(1.0)
            except Exception: self.log.err('下載模型排程'); time.sleep(5)

    def _hf_auth(self, url):
        tok = str(self.cfg.get('hf_token') or '').strip()
        return {'Authorization': 'Bearer ' + tok} if tok and urllib.parse.urlparse(url).hostname in ('huggingface.co', 'hf.co') else {}

    @staticmethod
    def _hf_opener():
        """轉址到別的網域（Hugging Face 的檔案伺服器）時，不要把金鑰帶過去（簽名網址會拒絕）."""
        import urllib.request
        class R(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                n = super().redirect_request(req, fp, code, msg, headers, newurl)
                if n is not None and urllib.parse.urlparse(newurl).hostname != urllib.parse.urlparse(req.full_url).hostname:
                    n.headers.pop('Authorization', None); n.unredirected_hdrs.pop('Authorization', None)
                return n
        return urllib.request.build_opener(R)

    def _size_later(self, fn):
        """背景問模型多大（不卡畫面）；問過的不再問."""
        Q = self.__dict__.setdefault('_szq', set())
        if fn in Q: return
        Q.add(fn); threading.Thread(target=self.model_size, args=(fn,), name='ModelSize', daemon=True).start()

    def model_size(self, fn):
        """還不知道大小的模型：問 Hugging Face（HEAD，不下載），記起來."""
        src = self.model_src(fn)
        if not src or src[2]: return src[2] if src else None
        b = os.path.basename(str(fn).replace('\\', '/')); X = dict(self.cfg.get('model_src_x') or {})
        try:
            import urllib.request
            class NoR(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, *a, **k): return None
            req = urllib.request.Request(src[1], method='HEAD', headers={'User-Agent': 'ComfyRemote', **self._hf_auth(src[1])})
            try: r = urllib.request.build_opener(NoR).open(req, timeout=15); h = r.headers
            except urllib.error.HTTPError as ex: h = ex.headers
            sz = int(h.get('X-Linked-Size') or h.get('Content-Length') or 0)
            if sz > 1000 and b in X: X[b][2] = sz; self.cfg.set('model_src_x', X); return sz
        except Exception: pass
        return None

    def _dl_job(self, D):
        """下載一個模型：先寫 .part（中斷了下次從斷的地方接著下載），完成才改名。下載好 ComfyUI 不用重開."""
        import urllib.request
        t = self.task('dl', f'⬇ {D["file"]}')
        try:
            d = self._models_dir(D['folder'])
            if d is None: raise RuntimeError('找不到 ComfyUI 的模型資料夾（ComfyUI 開著再試一次）')
            d.mkdir(parents=True, exist_ok=True); dst = d / os.path.basename(D['file']); part = dst.with_name(dst.name + '.part')
            if dst.is_file(): D.update(state='done', msg='已經有了', got=dst.stat().st_size); self.done(t, 'done', '已經有了'); return
            try:
                free = shutil.disk_usage(str(d)).free; need = (D.get('size') or 0) - (part.stat().st_size if part.is_file() else 0)
                if need > 0 and free < need + 2e9: raise RuntimeError(f'硬碟空間不夠：要 {fmt_b(need)}，{d.anchor or d} 只剩 {fmt_b(free)}（清一點空間再按下載）')
            except RuntimeError: raise
            except Exception: pass
            got = part.stat().st_size if part.is_file() else 0
            req = urllib.request.Request(D['url'], headers={'User-Agent': 'ComfyRemote', **({'Range': f'bytes={got}-'} if got else {}), **self._hf_auth(D['url'])})
            D['msg'] = '連線中…'; self.log.w(f'⬇ 下載 {D["file"]} → {dst}' + (f'（從 {fmt_b(got)} 接著下載）' if got else ''))
            try: r0 = self._hf_opener().open(req, timeout=60)
            except urllib.error.HTTPError as ex:
                if ex.code in (401, 403):
                    m = re.match(r'https://huggingface\.co/([^/]+/[^/]+)/', D['url']); page = f'https://huggingface.co/{m.group(1)}' if m else 'Hugging Face 模型頁'
                    raise RuntimeError(f'這個模型要先在 Hugging Face 同意授權：用瀏覽器登入後打開 {page} 按「Agree」，再到「⚙ 設定 → ComfyUI → Hugging Face 金鑰」貼上 Read token' + ('' if self.cfg.get('hf_token') else '（目前還沒填金鑰）'))
                raise
            with r0 as r:
                if got and r.status != 206: got = 0                                  # 伺服器不給接續：重新下載
                total = got + int(r.headers.get('Content-Length') or 0); D['size'] = total or D['size']
                with open(part, 'ab' if got else 'wb') as f:
                    t1 = time.time(); g1 = got
                    while True:
                        if D.get('cancel') or self.stop_all: raise InterruptedError
                        b = r.read(1 << 20)
                        if not b: break
                        f.write(b); got += len(b); D['got'] = got
                        if time.time() - t1 >= 1:
                            D['speed'] = (got - g1) / (time.time() - t1); t1 = time.time(); g1 = got
                            D['msg'] = f'{fmt_b(got)}／{fmt_b(total)}　{fmt_b(D["speed"])}/s'; t['pct'] = round(got * 100 / total) if total else None
            if total and got < total: raise RuntimeError(f'只下載到 {fmt_b(got)}／{fmt_b(total)}（網路斷了？再按一次會接著下載）')
            os.replace(str(part), str(dst)); D.update(state='done', msg=f'好了（{fmt_b(got)}）')
            for c in comfy.MODEL_INPUTS: self.info_fresh.discard(c)                  # 下拉選單要重新問
            self.par_cache.clear(); self.done(t, 'done', fmt_b(got)); self.log.w(f'⬇ 下載好了：{dst}（{fmt_b(got)}）')
        except InterruptedError: D.update(state='stop', msg='已停（下次按會接著下載）'); D.pop('cancel', None); self.done(t, 'stop', '已停')
        except Exception as ex:
            D.update(state='fail', msg=f'失敗：{ex}'); self.done(t, 'fail', str(ex)[:200]); self.log.w(f'⬇ 下載失敗 {D["file"]}：{ex}')

    # ---- 照片、結果檔
    def gen_save_input(self, data, name='', tag=''):
        ext = next((e for m, e in self.GEN_IMG_EXT.items() if bytes(data[:len(m)]) == m), None)
        if not ext and bytes(data[4:8]) == b'ftyp': ext = '.mov' if bytes(data[8:10]) == b'qt' else '.mp4'          # 影片（手機錄的 mp4／mov）
        elif not ext and bytes(data[:4]) == b'\x1a\x45\xdf\xa3': ext = '.webm'
        if not ext: raise comfy.ComfyError('這不是 JPG／PNG／WEBP 照片，也不是 MP4／MOV／WEBM 影片')
        if len(data) > (600e6 if ext in self.VIDEO_EXT else 60e6): raise comfy.ComfyError('檔案太大（照片 60 MB、影片 600 MB 以內）')
        tag = re.sub(r'[^0-9A-Za-z_-]', '', str(tag or ''))[:24]                  # 例如 f0067＝從影片取的第 67 格（歷史紀錄會標出來）
        nm = f'{time.strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:6]}{"_" + tag if tag else ""}{ext}'; (self.data / 'inputs' / nm).write_bytes(bytes(data))
        self.log.w(f'生圖：收到照片 {nm}（{fmt_b(len(data))}{"，" + name if name else ""}）'); return nm

    # ================================================================ 👤 人物庫：很多張某人的照片存成一個編號（a01、a02…）；提示詞提到編號 → 自動把他的照片當參考圖帶進去
    PEOPLE_RE = re.compile(r'(?<![A-Za-z0-9])([A-Za-z]\d{2,3})(?![0-9])')

    def _pdir(self): d = self.data / 'people'; d.mkdir(parents=True, exist_ok=True); return d

    def people_list(self):
        out = []
        for d in sorted(self._pdir().iterdir(), key=lambda x: x.name):
            if not d.is_dir() or d.name.startswith('_'): continue
            try: M = json.loads((d / 'meta.json').read_text(encoding='utf-8'))
            except Exception: M = {}
            ph = sorted(p.name for p in d.iterdir() if p.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp'))
            order = [x for x in M.get('order') or [] if x in ph] + [x for x in ph if x not in (M.get('order') or [])]
            out.append({'code': d.name, 'name': M.get('name') or '', 'photos': order, 'cover': order[0] if order else ''})
        return out

    def people_get(self, code):
        code = str(code or '').lower()
        return next((p for p in self.people_list() if p['code'] == code), None)

    def people_new(self, name=''):
        used = {p['code'] for p in self.people_list()}
        code = next(f'a{i:02d}' for i in range(1, 1000) if f'a{i:02d}' not in used)
        self.people_save(code, name); return code

    def people_save(self, code, name=None, order=None):
        code = str(code or '').lower()
        if not re.fullmatch(r'[a-z]\d{2,3}', code): raise comfy.ComfyError('編號要像 a01（一個英文字母＋2～3 個數字）')
        d = self._pdir() / code; d.mkdir(parents=True, exist_ok=True)
        try: M = json.loads((d / 'meta.json').read_text(encoding='utf-8'))
        except Exception: M = {}
        if name is not None: M['name'] = str(name)[:40]
        if order is not None: M['order'] = [str(x) for x in order]
        (d / 'meta.json').write_text(json.dumps(M, ensure_ascii=False), encoding='utf-8'); return code

    def people_add_photo(self, code, data):
        code = self.people_save(code)
        ext = self.GEN_IMG_EXT.get(bytes(data[:4]), None) or self.GEN_IMG_EXT.get(bytes(data[:3]), None)
        if not ext: raise comfy.ComfyError('看不懂這張照片（要 JPG／PNG／WEBP）')
        nm = f'{time.strftime("%Y%m%d_%H%M%S")}_{uuid.uuid4().hex[:6]}{ext}'; (self._pdir() / code / nm).write_bytes(bytes(data))
        self.log.w(f'👤 人物庫：{code} 加了一張照片'); return nm

    def people_del(self, code, photo=None):
        code = str(code or '').lower(); d = self._pdir() / code
        if not re.fullmatch(r'[a-z]\d{2,3}', code) or not d.is_dir(): raise comfy.ComfyError('沒有這個人')
        bk = self._pdir() / '_old'; bk.mkdir(exist_ok=True)
        if photo:
            p = d / os.path.basename(str(photo))
            if p.is_file(): shutil.move(str(p), str(bk / f'{code}_{p.name}'))
        else: shutil.move(str(d), str(bk / f'{code}_{time.strftime("%Y%m%d_%H%M%S")}')); self.log.w(f'👤 人物庫：刪除 {code}（搬到 people\\_old）')

    def people_in(self, text):
        """提示詞裡提到的人（照出現順序，不重複）."""
        have = {p['code']: p for p in self.people_list() if p['photos']}; out = []
        for m in self.PEOPLE_RE.finditer(str(text or '')):
            c = m.group(1).lower()
            if c in have and have[c] not in out: out.append(have[c])
        return out

    def _people_inject(self, C, api, jid):
        """送出前：提示詞提到 a01 → 把他的照片上傳到 ComfyUI，接成參考圖，提示詞裡的 a01 換成對應的「圖N」／<Picture N>。回傳說明（記到 LOG）."""
        A = comfy.analyze(api); pos = A.get('pos')
        if not pos: return ''
        text = api[pos[0]]['inputs'].get(pos[1])
        if not isinstance(text, str): return ''
        P = self.people_in(text)
        if not P: return ''
        nid = [max([int(k) for k in api if str(k).isdigit()] + [0]) + 1000]
        def load(code, fn):
            up = C.upload(f'cr_p_{code}_{fn}', (self._pdir() / code / fn).read_bytes())
            k = str(nid[0]); nid[0] += 1; api[k] = {'class_type': 'LoadImage', 'inputs': {'image': up}, '_meta': {'title': f'👤 {code}'}}; return k
        notes = []
        r2v = [k for k, v in api.items() if v.get('class_type') == 'MiniMaxH3ReferenceToVideo']
        qwen = [k for k, v in api.items() if str(v.get('class_type', '')).startswith('TextEncodeQwenImageEdit')]
        q21 = [k for k, v in api.items() if v.get('class_type') == 'TextEncodeQwenImage21']
        ag = None
        for k, v in api.items():                                            # 「images.image_1」這種可以一直加的入口
            hits = [(m.group(1), int(m.group(2))) for x in (v.get('inputs') or {}) for m in [re.match(r'^(images\.image_?)(\d+)$', x)] if m]
            if hits: ag = (k, hits[0][0], 0, [n for _p, n in hits]); break
        if r2v:                                                              # H3 參考生影片：每人最多 3 張（總共最多 9 張參考圖）
            ins = api[r2v[0]]['inputs']; used = sorted(int(x.rsplit('_', 1)[1]) for x in ins if x.startswith('ref_images.ref_image_'))
            nxt = (used[-1] + 1) if used else 0; defs = []
            for p in P:
                tags = []
                for fn in p['photos'][:max(1, int(self.cfg.get('people_refs') or 3))]:
                    if nxt >= 9: break
                    k = load(p['code'], fn); ins[f'ref_images.ref_image_{nxt}'] = [k, 0]; tags.append(f'<Picture {nxt + 1}>'); nxt += 1
                if not tags: continue
                defs.append(f'{p["code"]} is the person shown in {", ".join(tags)}; keep {p["code"]}\'s face, facial identity and features exactly the same as in {", ".join(tags)}.')
                notes.append(f'{p["code"]}（{len(tags)} 張）')
            if defs:
                t = text
                if 'subject_definitions:' in t: t = t.replace('subject_definitions:', 'subject_definitions:\n' + '\n'.join(defs), 1)
                else: t = '\n'.join(defs) + '\n\n' + t
                api[pos[0]]['inputs'][pos[1]] = t
        elif q21:                                                            # Qwen 2.1：images.image_2…image_10，每人一張
            ins = api[q21[0]]['inputs']; t = text
            for p in P:
                slot = next((n for n in range(2, 11) if f'images.image_{n}' not in ins), None)
                if slot is None: notes.append(f'{p["code"]}（放不下：最多 10 張圖）'); continue
                ins[f'images.image_{slot}'] = [load(p['code'], p['photos'][0]), 0]
                t = re.sub(rf'(?<![A-Za-z0-9]){re.escape(p["code"])}(?![0-9])', f'圖{slot}中的人', t, flags=re.I); notes.append(f'{p["code"]}→圖{slot}')
            api[pos[0]]['inputs'][pos[1]] = t
        elif qwen:                                                           # Qwen 改圖（GROK、兩張圖合併）：用空著的 image2／image3，每人一張
            enc = pos[0] if pos[0] in qwen else qwen[0]; t = text
            for p in P:
                slot = next((n for n in (2, 3) if f'image{n}' not in api[enc]['inputs']), None)
                if slot is None: notes.append(f'{p["code"]}（放不下：最多 3 張圖）'); continue
                k = load(p['code'], p['photos'][0])
                for e in qwen:
                    if f'image{slot}' not in api[e]['inputs']: api[e]['inputs'][f'image{slot}'] = [k, 0]
                t = re.sub(rf'(?<![A-Za-z0-9]){re.escape(p["code"])}(?![0-9])', '圖' + '一二三'[slot - 1] + '中的人', t, flags=re.I); notes.append(f'{p["code"]}→圖' + '一二三'[slot - 1])
            api[pos[0]]['inputs'][pos[1]] = t
        elif ag:                                                             # 新模型的「好幾張參考圖」入口（images.image_1、images.image0…）：接在後面，照片先縮到 100 萬像素
            k0, pre, base, used = ag; ins = api[k0]['inputs']; t = text; nxt = max(used) + 1; first1 = min(used)
            for p in P:
                if nxt - first1 >= 3: notes.append(f"{p['code']}（放不下：這個模型最多 3 張參考圖）"); continue
                k = load(p['code'], p['photos'][0]); sk = str(nid[0]); nid[0] += 1
                api[sk] = {'class_type': 'ImageScaleToTotalPixels', 'inputs': {'image': [k, 0], 'upscale_method': 'lanczos', 'megapixels': 1.0, 'resolution_steps': 16}, '_meta': {'title': f'👤 {p["code"]} 縮小'}}
                ins[f'{pre}{nxt}'] = [sk, 0]; num = nxt - first1 + 1
                t = re.sub(rf'(?<![A-Za-z0-9]){re.escape(p["code"])}(?![0-9])', f'圖{num}中的人', t, flags=re.I); notes.append(f'{p["code"]}→圖{num}'); nxt += 1
            api[pos[0]]['inputs'][pos[1]] = t
        else: notes.append('這個流程沒辦法帶人物照片（要用 GROK、Qwen 2.1 Turbo 或「H3 參考生影片／臉穩定」）')
        msg = '👤 人物庫：' + '、'.join(notes); self.log.w(f'生圖：#{jid} {msg}'); return msg

    @staticmethod
    def qwen21_tags(t):
        """「圖1／圖一／圖 2」→ <image1>／<image2>（Qwen-Image 2.1 官方的多圖寫法）."""
        N = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
        return re.sub(r'圖\s*([1-9]|10|[一二三四五六七八九十])(?![0-9])', lambda m: f'<image{N.get(m.group(1)) or int(m.group(1))}>', str(t))

    def _ref_inject(self, C, api, jid, fn):
        """V0.2.08 📎 參考圖：接到下一個空的圖片入口（GROK＝image2／image3，Qwen 2.1＝images.image_N），提示詞裡的「參考圖」換成「圖N」."""
        A = comfy.analyze(api); pos = A.get('pos')
        if not pos or not isinstance(api[pos[0]]['inputs'].get(pos[1]), str) or '參考圖' not in api[pos[0]]['inputs'][pos[1]]: return ''   # 提示詞沒提到「參考圖」就不帶（忘了拿掉也不會亂改）
        t = api[pos[0]]['inputs'][pos[1]]; up = C.upload('cr_r_' + fn, (self.data / 'inputs' / fn).read_bytes())
        k = str(max([int(x) for x in api if str(x).isdigit()] + [0]) + 2000); api[k] = {'class_type': 'LoadImage', 'inputs': {'image': up}, '_meta': {'title': '📎 參考圖'}}
        qwen = [x for x, v in api.items() if str(v.get('class_type', '')).startswith('TextEncodeQwenImageEdit')]
        q21 = [x for x, v in api.items() if v.get('class_type') == 'TextEncodeQwenImage21']
        tag = ''
        if q21:
            ins = api[q21[0]]['inputs']; slot = next((n for n in range(2, 11) if f'images.image_{n}' not in ins), None)
            if slot: ins[f'images.image_{slot}'] = [k, 0]; tag = f'圖{slot}'
        elif qwen:
            enc = pos[0] if pos[0] in qwen else qwen[0]; slot = next((n for n in (2, 3) if f'image{n}' not in api[enc]['inputs']), None)
            if slot:
                for e in qwen:
                    if f'image{slot}' not in api[e]['inputs']: api[e]['inputs'][f'image{slot}'] = [k, 0]
                tag = '圖' + '一二三'[slot - 1]
        if not tag: api.pop(k, None); self.log.w(f'生圖：#{jid} 📎 參考圖放不下（這個流程沒有空的圖片入口）'); return ''
        api[pos[0]]['inputs'][pos[1]] = t.replace('參考圖', tag)
        self.log.w(f'生圖：#{jid} 📎 參考圖 → {tag}'); return tag

    # ---- 🔬 測速度：同一張圖、同一句、同一個種子，排幾種組合（fp8／INT8 × 960／768 × 有沒有 snofs），看哪個最快、畫質能不能接受
    PROF_CAT = (('算圖', ('KSampler', 'SamplerCustom', 'Sampler')), ('讀圖／提示詞', ('TextEncode', 'CLIPTextEncode')),
                ('編碼／解碼', ('VAEEncode', 'VAEDecode', 'ReferenceLatent')), ('載入模型', ('Loader', 'Lora')), ('讀存圖', ('LoadImage', 'SaveImage', 'Save', 'Scale')))

    @classmethod
    def prof_brief(cls, prof):
        """{'類別': 秒} → 「算圖 38s · 讀圖／提示詞 9s …」（照時間多到少，太短的不列）."""
        C = {}
        for cl, sec in (prof or {}).items():
            cat = next((n for n, keys in cls.PROF_CAT if any(k in cl for k in keys)), '其他')
            C[cat] = C.get(cat, 0) + float(sec or 0)
        L = sorted(C.items(), key=lambda x: -x[1])
        return ' · '.join(f'{k} {v:.0f}s' if v >= 1 else f'{k} {v:.1f}s' for i, (k, v) in enumerate(L) if v >= 0.5 or i == 0)

    BENCH_WFS = [('GROK 改圖（INT8 快）', 'GROK INT8'), ('GROK 改圖（快速）', 'GROK fp8'), ('Qwen 2.1 Turbo 改圖', 'Qwen2.1 Turbo')]

    def gen_benchmark(self, img, prompt, src_wf=''):
        """🔬 測速度：同一張照片、同一個種子，每個模型先暖機一張（載入模型）再正式跑一張，排成同一批。
        GROK 有 INT8 就不測 fp8；模型沒下載完的流程跳過（說明裡會寫）。回傳 (ids, 說明)."""
        names = {w['name']: w for w in self.gen_workflows()}
        if not img or not (self.data / 'inputs' / img).is_file(): raise comfy.ComfyError('這筆沒有原圖可以測')
        V = []; skip = []; grok = False
        for wf, tag in self.BENCH_WFS:
            if wf not in names: continue
            if wf.startswith('GROK') and grok: continue
            if [m for m in self.gen_models(wf) if not m['ok']]: skip.append(tag); continue
            grok = grok or wf.startswith('GROK')
            V.append((wf, f'🔬 {tag}（暖機）')); V.append((wf, f'🔬 {tag}'))
        if not V: raise comfy.ComfyError('沒有可以測的流程（模型都還沒下載）')
        seed = random.randint(1, 2 ** 31); ids = []
        for wf, label in V: ids += self.gen_add(wf, prompt, img, src=label, seed=seed)
        self.gen_set_batch(ids)
        note = f'（{"、".join(skip)} 的模型還沒下載，這次先不測；到生圖頁選那個流程可以一鍵下載）' if skip else ''
        self.log.w(f'🔬 測速度：排了 {len(ids)} 個 {note}'); return ids, note

    # ================================================================ 🧪 比較：同一批照片 × 好幾種流程，排一整晚看哪個好
    def _wf_speed(self):
        """每個流程（熱的，不含載入模型）平均一張幾秒、跑過幾張."""
        R = {}
        for r in self.db.q("SELECT wf, AVG(run_s) a, COUNT(*) n FROM gen_jobs WHERE state='done' AND run_s>0 AND cold<>1 GROUP BY wf"): R[r['wf']] = (r['a'], r['n'])
        return R

    def cmp_rows(self):
        """比較頁的每一列：清單裡的模型（照推薦順序）＋你自己其他「一張照片改圖」的流程。附模型狀態、平均速度、說明."""
        W = {w['name']: w for w in self.gen_workflows()}; spd = self._wf_speed(); rows = []; seen = set()
        sc = {r[0]: (r[1], r[2]) for r in self.db.q("SELECT CASE WHEN cmp_col<>'' THEN cmp_col ELSE wf END k, AVG(vote), COUNT(*) FROM gen_jobs WHERE vote>0 AND deleted=0 GROUP BY k")}   # 你以前打的平均分數
        def one(nm, tpl='', steps=None, lic='', note=''):
            w = W.get(nm); seen.add(nm)
            r = {'name': nm, 'key': nm, 'wf': nm, 'tpl': tpl, 'steps': steps, 'license': lic, 'note': note, 'ready': bool(w and not w.get('err')), 'err': (w or {}).get('err', ''),
                 'miss': [], 'miss_b': 0, 'dl': 0, 'avg': None, 'n': 0}
            if w and not w.get('err'):
                try:
                    for m in self.gen_models(nm):
                        if m['ok']: continue
                        st = (m.get('dl') or {}).get('state'); sz = m.get('size') or 0
                        if not sz and m['known']: self._size_later(m['file'])
                        r['miss'].append({'file': m['file'], 'size': sz, 'known': m['known'], 'state': st or '', 'got': (m.get('dl') or {}).get('got', 0), 'msg': (m.get('dl') or {}).get('msg', '')})
                        r['miss_b'] += sz; r['dl'] += 1 if st in ('wait', 'run') else 0
                except Exception as ex: r['err'] = str(ex)[:120]
            if nm in spd: r['avg'], r['n'] = round(spd[nm][0], 1), spd[nm][1]
            rows.append(r)
        for nm, tpl, steps, lic, note in self.LINEUP:
            one(nm, tpl, steps, lic, note)
            for key, base, spec, vnote in self.CMP_VARIANTS:                 # 同模型不同設定：緊接在原本那列下面
                if base != nm: continue
                b = dict(rows[-1]); b.update(key=key, name=key, wf=nm, var=spec, note=vnote, avg=None, n=0)
                st = next((v for k, v in spec.items() if k.endswith('steps')), None)
                if st: b['steps'] = st
                rows.append(b)
        for _t, nm in self.EXTRA_TPL:                                        # 文字生圖也能比（不用照片：每個模型生一張，同一個種子）
            w = W.get(nm)
            if '文字生圖' in nm: one(nm, _t, None, '', '文字生圖（不用照片）：每個模型照提示詞生一張'); rows[-1]['t2i'] = True
        for nm, w in W.items():
            if nm in seen or w.get('err') or int(w.get('n_img') or 0) != 1 or 'video' in (w.get('kinds') or []) or not w.get('need_img'): continue
            if any(k in nm for k in ('H3', '影片', '去背', '放大', '補幀')): continue
            one(nm, '', None, '', '你自己的流程')
        for r in rows:
            if r['key'] in sc: r['score'], r['nv'] = round(sc[r['key']][0], 1), sc[r['key']][1]
        return rows

    def disk_free(self):
        """ComfyUI 模型資料夾那顆硬碟還剩多少（比較頁顯示）."""
        try:
            c = getattr(self, '_dfc', None)
            if c and time.time() - c[0] < 30: return c[1]
            d = self._models_dir('diffusion_models'); v = {'free': shutil.disk_usage(str(d)).free, 'path': str(d)} if d else None
            self._dfc = (time.time(), v); return v
        except Exception: return None

    MDL_FOLDERS = ('diffusion_models', 'unet', 'checkpoints', 'text_encoders', 'clip', 'vae', 'loras', 'model_patches', 'controlnet', 'upscale_models', 'clip_vision', 'audio_encoders', 'latent_upscale_models')

    def mdl_dirs(self):
        """ComfyUI 的模型資料夾（問 /internal/folder_paths）→ {種類: [資料夾…]}."""
        out = {}
        try:
            st = self.comfy_status()
            if st['ok']:
                FP = comfy.Comfy(st['url']).get_json('/internal/folder_paths', timeout=10) or {}
                for k in self.MDL_FOLDERS:
                    fp = FP.get(k); ps = fp[0] if isinstance(fp, list) and fp and isinstance(fp[0], list) else (fp if isinstance(fp, list) else [])
                    ps = [x for x in ps if isinstance(x, str) and os.path.isdir(x)]
                    if ps: out[k] = list(dict.fromkeys(ps))
        except Exception: self.log.err('問模型資料夾')
        return out

    def mdl_list(self):
        """模型檔清單：大小、在哪、哪些流程用到（沒用到的可以刪來省空間）."""
        D = self.mdl_dirs(); used = {}
        for w in self.gen_workflows():
            try:
                for _c, _i, fn, _f in comfy.required_models(self.gen_wf_load(w['name']), self._obj_info(None)): used.setdefault(os.path.basename(fn.replace('\\', '/')).lower(), []).append(w['name'])
            except Exception: pass
        files = []; seen = set()
        for kind, ps in D.items():
            for root in ps:
                for p in Path(root).rglob('*'):
                    try:
                        if not p.is_file() or not p.name.lower().endswith(comfy.MODEL_EXT): continue
                        rp = str(p.resolve())
                        if rp in seen: continue
                        seen.add(rp); st = p.stat()
                        files.append({'name': p.name, 'kind': kind, 'path': rp, 'size': st.st_size, 't': st.st_mtime, 'used': sorted(set(used.get(p.name.lower(), [])))})
                    except Exception: pass
        files.sort(key=lambda x: -x['size'])
        disks = {}
        for f in files:
            try:
                a = Path(f['path']).anchor or '/'
                if a not in disks: disks[a] = shutil.disk_usage(a).free
            except Exception: pass
        return {'files': files, 'total': sum(f['size'] for f in files), 'free': disks}

    def mdl_del(self, path):
        """刪一個模型檔（只能刪 ComfyUI 模型資料夾裡的）. 回傳省下的位元組."""
        p = Path(str(path)).resolve(); roots = [Path(x).resolve() for ps in self.mdl_dirs().values() for x in ps]
        if not p.is_file() or not p.name.lower().endswith(comfy.MODEL_EXT) or not any(r == p.parent or r in p.parents for r in roots): raise comfy.ComfyError('只能刪 ComfyUI 模型資料夾裡的模型檔')
        sz = p.stat().st_size; p.unlink()
        for c in comfy.MODEL_INPUTS: self.info_fresh.discard(c)
        self.par_cache.clear(); self.oplog('刪模型', p.name); self.log.w(f'🧩 刪掉模型 {p}（{fmt_b(sz)}）'); return sz

    SLIM_KEEP = ('GROK 改圖（INT8 快）', 'Qwen 2.1 Turbo 改圖')

    def slim_plan(self, extra=()):
        """🧹 精簡：試過但不要的流程（RETIRED_WFS）＋你勾的其他流程（extra）＋只有它們用到的模型檔（留下的流程還在用的不刪）.
        回傳 {wfs, files, total, keep, others:[{name, size}]}：others＝還可以勾的流程，size＝也收掉它可以多省多少."""
        names = {w['name'] for w in self.gen_workflows()}
        gone = [n for n in self.RETIRED_WFS if n in names] + [n for n in (extra or ()) if n in names and n not in self.SLIM_KEEP and n not in self.RETIRED_WFS]
        info = self._obj_info(None); M = {}
        def mods(n):
            if n not in M:
                try: M[n] = {os.path.basename(fn.replace('\\', '/')).lower() for _c, _i, fn, _f in comfy.required_models(self.gen_wf_load(n), info)}
                except Exception: M[n] = set()
            return M[n]
        keep = names - set(gone); used, cand = set(), set()
        for n in keep: used |= mods(n)
        for n in gone: cand |= mods(n)
        cand -= used
        FL = self.mdl_list()['files']; SZ = {}
        for f in FL: SZ[f['name'].lower()] = SZ.get(f['name'].lower(), 0) + f['size']
        files = [f for f in FL if f['name'].lower() in cand] if cand else []
        others = []
        for n in sorted(keep - set(self.SLIM_KEEP)):
            rest = set().union(*[mods(k) for k in keep if k != n]) if len(keep) > 1 else set()
            others.append({'name': n, 'size': sum(SZ.get(m, 0) for m in mods(n) - rest - cand)})
        return {'wfs': gone, 'files': files, 'total': sum(f['size'] for f in files), 'keep': sorted(keep), 'others': others}

    def slim_do(self, extra=()):
        """照 slim_plan 刪：流程檔移到 workflows/_old（可以救回來），模型檔直接刪. 回傳 (流程數, 省下的位元組, 錯誤)."""
        P = self.slim_plan(extra); freed = 0; err = []
        old = self.data / 'workflows' / '_old'; old.mkdir(parents=True, exist_ok=True)
        for n in P['wfs']:
            try:
                f = self.gen_wf_path(n)
                if f.exists(): shutil.move(str(f), str(old / f'{f.stem}_{int(time.time())}{f.suffix}'))
            except Exception as ex: err.append(f'{n}：{ex}')
        for f in P['files']:
            try: freed += self.mdl_del(f['path'])
            except Exception as ex: err.append(f'{f["name"]}：{ex}')
        self.par_cache.clear(); self.log.w(f'🧹 精簡：收掉 {len(P["wfs"])} 個流程、刪掉 {len(P["files"])} 個模型（省 {fmt_b(freed)}）' + (f'；{len(err)} 個失敗' if err else ''))
        return len(P['wfs']), freed, err

    def cmp_dl(self, wfs):
        """勾的流程缺的模型全部排下載（同一個檔只下載一次）."""
        files = []
        for nm in wfs:
            try: files += [m['file'] for m in self.gen_models(nm) if not m['ok'] and m['known']]
            except Exception: pass
        return self.dl_add(list(dict.fromkeys(files)))

    def _var_params(self, wf, spec):
        """變化版的設定（參數名結尾 → 值）換成這個流程真正的參數 id."""
        out = {}
        if not spec: return out
        for g in self.gen_params(wf):
            for it in g['items']:
                for suf, v in spec.items():
                    if it['id'].endswith(suf): out[it['id']] = v
        return out

    def cmp_start(self, imgs, prompt, wfs, n=1, same_seed=True, params=None, neg='', cols=None):
        """照片 × 欄（流程或「流程＋不同設定」）排成一批。照欄排（同一個模型的照片連著跑，模型只載入一次）。回傳 (比較編號, 工作 ids, 跳過的)."""
        imgs = [str(x) for x in imgs or [] if x][:60]
        VAR = {k: (b, sp) for k, b, sp, _n in self.CMP_VARIANTS}
        if not cols: cols = [{'key': w, 'wf': w} for w in wfs or []]
        cols = [c for c in cols if isinstance(c, dict) and c.get('key')][:40]
        for c in cols:
            if c['key'] in VAR: c['wf'], c['spec'] = VAR[c['key']]
            c['wf'] = str(c.get('wf') or c['key'])
        if not cols: raise comfy.ComfyError('至少勾一個流程')
        T2I = {w['name'] for w in self.gen_workflows() if not w.get('need_img')}
        if not imgs and any(c['wf'] not in T2I for c in cols): raise comfy.ComfyError('先選照片（只勾文字生圖的話可以不用照片）')
        names = {w['name'] for w in self.gen_workflows()}; skip = [c['key'] for c in cols if c['wf'] not in names]; cols = [c for c in cols if c['wf'] in names]
        if not cols: raise comfy.ComfyError('勾的流程都還沒做好（ComfyUI 開著會自動從官方範本做）')
        first = {}
        for i, c in enumerate(cols): first.setdefault(c['wf'], i)
        cols = sorted(cols, key=lambda c: first[c['wf']])                    # 同一個模型的欄排在一起（模型只載入一次）
        rid = int(self.cfg.get('cmp_seq') or 0) + 1; self.cfg.set('cmp_seq', rid)
        seed = random.randint(1, 2 ** 31) if same_seed else -1; ids = []; P = params if isinstance(params, dict) else {}; done = []
        for c in cols:
            pp = dict(P.get(c['wf']) if isinstance(P.get(c['wf']), dict) else {}); pp.update(self._var_params(c['wf'], c.get('spec')))
            if isinstance(c.get('params'), dict): pp.update(c['params'])          # 你自己存的變化欄：那時候的參數
            mine = []; t2i = not (next((w for w in self.gen_workflows() if w['name'] == c['wf']), {}) or {}).get('need_img')
            for im in ([''] if t2i else imgs):                                  # 文字生圖：不用照片，生一次（結果表放在「✏ 文字生圖」那一列）
                try: mine += self.gen_add(c['wf'], prompt, im, neg, n, src=f'🧪 比較 {rid} · {c["key"]}', seed=seed, params=pp or None)
                except comfy.ComfyError as ex: skip.append(f'{c["key"]}：{ex}'); break
            if mine:
                self.db.x(f'UPDATE gen_jobs SET cmp=?, cmp_col=? WHERE id IN ({",".join("?" * len(mine))})', [rid, c['key']] + mine); ids += mine; done.append(c)
        if not ids: raise comfy.ComfyError('一個都排不進去：' + '；'.join(skip[:3]))
        self.gen_set_batch(ids)
        R = list(self.cfg.get('cmp_runs') or [])
        R.insert(0, {'id': rid, 't': time.time(), 'prompt': prompt, 'imgs': imgs, 'wfs': [c['key'] for c in done], 'colwf': {c['key']: c['wf'] for c in done}, 'n': n, 'seed': seed}); self.cfg.set('cmp_runs', R[:50])
        self.log.w(f'🧪 比較 {rid}：{len(imgs)} 張照片 × {len(done)} 欄 = {len(ids)} 個工作' + (f'（跳過：{"；".join(skip)}）' if skip else ''))
        return rid, ids, skip

    def cmp_runs(self):
        out = []
        for R in self.cfg.get('cmp_runs') or []:
            c = {r['state']: r['c'] for r in self.db.q('SELECT state, COUNT(*) c FROM gen_jobs WHERE cmp=? AND deleted=0 GROUP BY state', (R['id'],))}
            if not c: continue
            eta = 0
            if c.get('wait') or c.get('run'):                                    # 還要多久：每個沒做完的照那個流程跑過的平均（沒跑過當 60 秒；步數多的 4 分鐘）
                spd = self._wf_speed(); st = {n: steps for n, _t, steps, *_ in self.LINEUP}
                for r in self.db.q("SELECT wf FROM gen_jobs WHERE cmp=? AND deleted=0 AND state IN ('wait','run')", (R['id'],)):
                    eta += spd[r['wf']][0] if r['wf'] in spd else (240 if (st.get(r['wf']) or 0) >= 20 else 60)
            out.append(dict(R, counts=c, total=sum(c.values()), eta=round(eta)))
        return out

    def cmp_run(self, rid):
        """一次比較的結果矩陣：列＝照片，欄＝流程；每格是那個工作（狀態、結果圖、秒數、分數）。另附每個流程的平均秒數、平均分數."""
        R = next((x for x in self.cfg.get('cmp_runs') or [] if int(x['id']) == int(rid)), None)
        if R is None: raise comfy.ComfyError('找不到這次比較')
        J = [self._row(r) for r in self.db.q('SELECT * FROM gen_jobs WHERE cmp=? AND deleted=0 ORDER BY id', (int(rid),))]
        cells = {}; S = {}
        for j in J:
            col = j.get('cmp_col') or j['wf']
            cells.setdefault(j['img'], {}).setdefault(col, []).append({k: j.get(k) for k in ('id', 'state', 'outs', 'run_s', 'cold', 'vote', 'msg', 'out_w', 'out_h', 'qpos')})
            s = S.setdefault(col, {'done': 0, 'fail': 0, 'wait': 0, 't': [], 'v': []})
            if j['state'] == 'done': s['done'] += 1; (s['t'].append(j['run_s']) if j['run_s'] and j.get('cold') != 1 else None)
            elif j['state'] == 'fail': s['fail'] += 1
            elif j['state'] in ('wait', 'run'): s['wait'] += 1
            if j.get('vote'): s['v'].append(j['vote'])
        summ = [{'wf': wf, 'done': S.get(wf, {}).get('done', 0), 'fail': S.get(wf, {}).get('fail', 0), 'wait': S.get(wf, {}).get('wait', 0),
                 'avg': round(statistics.mean(S[wf]['t']), 1) if S.get(wf, {}).get('t') else None,
                 'score': round(statistics.mean(S[wf]['v']), 2) if S.get(wf, {}).get('v') else None, 'nv': len(S.get(wf, {}).get('v', []))} for wf in R['wfs']]
        im = [i for i in R['imgs'] if i in cells] or list(R['imgs'])
        if '' in cells: im = im + ['']                                       # 文字生圖那一列
        return dict(R, imgs=im, cells=cells, summary=summ)

    def cmp_retry(self, rid):
        """這次比較裡失敗／取消的重跑一次（例如補好 Hugging Face 金鑰、下載好模型之後）。結果表會換成新的那張."""
        rows = self.db.q("SELECT * FROM gen_jobs WHERE cmp=? AND deleted=0 AND state IN ('fail','stop') ORDER BY id", (int(rid),)); ids = []; err = []
        b = (self.db.one('SELECT batch FROM gen_jobs WHERE cmp=? LIMIT 1', (int(rid),)) or [0])[0]
        for r in rows:
            j = self._row(r)
            try:
                new = self.gen_add(j['wf'], j['prompt'], j['img'], j.get('neg') or '', 1, src=j['src'], seed=j['seed'] if (j.get('seed') or -1) >= 0 else -1, params=j['params'] or None)
                self.db.x(f'UPDATE gen_jobs SET cmp=?, cmp_col=?, batch=? WHERE id IN ({",".join("?" * len(new))})', [int(rid), j.get('cmp_col') or '', b] + new)
                self.db.x('UPDATE gen_jobs SET deleted=? WHERE id=?', (time.time(), j['id'])); ids += new   # 舊的失敗紀錄收進回收桶
            except Exception as ex: err.append(str(ex)[:80])
        self.log.w(f'🧪 比較 {rid}：失敗的重跑 {len(ids)} 個' + (f'（{len(err)} 個排不進去：{err[0]}）' if err else ''))
        return ids, err

    def prompts(self):
        """常用提示詞：你存的（最上面）＋最近常用的（照次數）."""
        saved = [str(x) for x in self.cfg.get('saved_prompts') or []]
        rec = [r['prompt'] for r in self.db.q("SELECT prompt, COUNT(*) c, MAX(id) m FROM gen_jobs WHERE prompt<>'' AND deleted=0 GROUP BY prompt ORDER BY c DESC, m DESC LIMIT 30")]
        rec = [x for x in rec if x not in saved and len(x) < 400][:12]
        return {'saved': saved, 'recent': rec}

    def recipes(self): return [x for x in self.cfg.get('recipes') or [] if isinstance(x, dict) and x.get('name')]

    def recipe_save(self, r, on=True):
        """V0.1.98 📌 配方：流程＋提示詞＋設定（畫質等）＋保持臉不變，一鍵套用。存在電腦上，每支手機都看得到. 同名蓋掉."""
        nm = str((r or {}).get('name') or '').strip()[:30]
        L = [x for x in self.recipes() if x['name'] != nm]
        if on and nm:
            L.insert(0, {'name': nm, 'wf': str(r.get('wf') or ''), 'both': bool(r.get('both')), 'prompt': str(r.get('prompt') or '')[:2000],
                         'params': r.get('params') if isinstance(r.get('params'), dict) else {}, 'keep': bool(r.get('keep')),
                         'ref': str(r.get('ref') or '') if re.fullmatch(r'[^/\\]+', str(r.get('ref') or '_')) and '..' not in str(r.get('ref')) and (self.data / 'inputs' / str(r.get('ref') or '_')).is_file() else ''})   # V0.2.25 配方也記參考圖（例如公司制服）
        self.cfg.set('recipes', L[:40]); return L

    def prompt_save(self, p, on=True):
        L = [str(x) for x in self.cfg.get('saved_prompts') or [] if str(x) != p]
        if on and p.strip(): L.insert(0, p.strip())
        self.cfg.set('saved_prompts', L[:60]); return L

    def gen_post(self, jid, idx=0, kind='upscale', src='電腦'):
        """結果再加工：upscale＝SeedVR2 放大 2 倍；interp＝FILM 補幀。第一次用會自動做流程、排下載模型（下載好才跑）. 回傳 (ids, 說明)."""
        wf, tpl, msg = self.POST[kind]
        if not self.gen_wf_path(wf).exists():
            try: self.gen_from_template(tpl, wf)
            except Exception as ex: raise comfy.ComfyError(f'還沒有「{wf}」流程（{ex}）')
        img = self.gen_reuse(jid, idx)
        try: self.dl_add([m['file'] for m in self.gen_models(wf) if not m['ok'] and m['known']])
        except Exception: pass
        return self.gen_add(wf, '', img, src=src), msg

    def cmp_stop(self, rid):
        """這次比較還沒跑的全部取消（做好的留著）."""
        n = 0
        for (jid,) in self.db.q("SELECT id FROM gen_jobs WHERE cmp=? AND state IN ('wait','run')", (int(rid),)):
            try: self.gen_cancel(jid); n += 1
            except Exception: pass
        self.log.w(f'🧪 比較 {rid}：停掉剩下的 {n} 個'); return n

    def cmp_del(self, rid):
        """刪掉一次比較：還在排隊的取消、結果放進回收桶（30 天內可以在歷史紀錄還原），清單拿掉."""
        rid = int(rid)
        for (jid,) in self.db.q("SELECT id FROM gen_jobs WHERE cmp=? AND state IN ('wait','run')", (rid,)):
            try: self.gen_cancel(jid)
            except Exception: pass
        time.sleep(0.3)
        ids = [r[0] for r in self.db.q('SELECT id FROM gen_jobs WHERE cmp=? AND deleted=0', (rid,))]
        n = self.gen_hist_act(ids, 'del') if ids else 0
        self.cfg.set('cmp_runs', [x for x in self.cfg.get('cmp_runs') or [] if int(x['id']) != rid]); self.log.w(f'🧪 刪掉比較 {rid}（{n} 筆進回收桶）'); return n

    def diag(self):
        """🩺 一頁看完：ComfyUI、顯示卡、記憶體、硬碟、金鑰、模型、下載、排隊；每項 ok／warn／bad＋怎麼辦."""
        L = []
        def add(st, title, val, tip=''): L.append({'st': st, 'title': title, 'val': val, 'tip': tip})
        c = self.comfy_status(True); S = {}
        if c['ok']:
            try: S = comfy.Comfy(c['url']).stats() or {}
            except Exception: S = {}
            add('ok', 'ComfyUI', f'已連上 {c["url"]} · {c.get("ver") or ""}')
        else: add('bad', 'ComfyUI', '連不到', '電腦上打開 ComfyUI（Comfy Desktop）；工作會先排隊，開了就自動跑')
        sy = S.get('system') or {}; dv = (S.get('devices') or [{}])[0]
        if dv:
            vt, vf = dv.get('vram_total') or 0, dv.get('vram_free') or 0
            add('ok' if vt >= 11e9 else 'warn', '顯示卡', f'{dv.get("name", "")} · VRAM {fmt_b(vt)}（剩 {fmt_b(vf)}）', '' if vt >= 11e9 else '顯示卡記憶體小：用 Qwen 2.1 Turbo（7B，比較塞得下）')
        if sy.get('ram_total'):
            rt = sy['ram_total']; add('ok' if rt >= 30e9 else 'warn', '電腦記憶體', f'{fmt_b(rt)}（剩 {fmt_b(sy.get("ram_free") or 0)}）', '' if rt >= 30e9 else '記憶體 32GB 以下：大模型（GROK、H3）要靠虛擬記憶體，設大一點（例如 64GB）')
        if sy.get('argv'):
            lv, msg = self.launch_advice(sy['argv'], (dv or {}).get('vram_total') or 0)
            add(lv, 'ComfyUI 啟動參數', ' '.join(x for x in sy['argv'] if x.startswith('--')) or '（沒有）', msg)
        if c['ok']:                                                          # V0.1.95 GROK 再快的路：Nunchaku 4-bit（要自己裝自訂節點，App 不會動你的 ComfyUI）
            nk = []
            for cl in ('NunchakuQwenImageDiTLoader', 'NunchakuFluxDiTLoader'):
                try:
                    if comfy.Comfy(c['url']).object_info(cl): nk.append(cl)
                except Exception: pass
            oi = True
            if nk: add('ok', 'Nunchaku（4-bit 加速）', '已裝' + ('（有 Qwen 改圖用的節點）' if 'NunchakuQwenImageDiTLoader' in nk else '（但沒有 Qwen 用的節點：更新 ComfyUI-nunchaku）'), 'GROK 可以換 nunchaku_qwen_image_edit_2511_balance_int4（RTX 30 系列用 int4）；要做成流程跟 AI 說')
            elif oi: add('ok', 'Nunchaku（4-bit 加速）', '沒裝', 'GROK（20GB）塞不進 12GB 才慢；裝 ComfyUI-nunchaku 自訂節點＋下載 balance_int4 模型（約 12GB）有機會讓 GROK 快很多（網路上在高階顯卡測是好幾倍，3060 要試了才知道）。要裝的話照「使用說明 → GROK 再快一點」，或叫 AI 幫你')
        try:                                                                 # V0.2.15 App 自己的資料夾多大（結果圖、上傳的照片、縮圖）
            def dsz(p): return sum(f.stat().st_size for f in p.rglob('*') if f.is_file()) if p.is_dir() else 0
            o, i, t = dsz(self.data / 'outputs'), dsz(self.data / 'inputs'), dsz(self.data / 'thumbs')
            add('ok', 'App 用掉的空間', f'結果 {fmt_b(o)} · 照片 {fmt_b(i)} · 縮圖 {fmt_b(t)}', '' if o < 30e9 else '結果圖很多了：歷史紀錄「🧹 只留有打星的」或選取後刪除')
        except Exception: pass
        df = self.disk_free()
        if df: add('ok' if df['free'] > 50e9 else 'warn' if df['free'] > 15e9 else 'bad', '模型硬碟', f'剩 {fmt_b(df["free"])}（{df["path"]}）', '' if df['free'] > 50e9 else '空間不多：設定 →「🧩 模型檔」刪掉沒用到的')
        if self.cfg.get('hf_token'): add('ok', 'Hugging Face 金鑰', '已設定')   # V0.3.17 沒設定就不顯示（現在用不到）
        try:
            R = [r for r in self.cmp_rows() if not r.get('var')]; ready = [r for r in R if r['ready'] and not r['miss']]
            mb = {m['file']: m['size'] or 0 for r in R for m in r['miss'] if not m['state']}
            add('ok' if len(ready) == len(R) else 'warn', '比較清單的模型', f'{len(ready)}／{len(R)} 個流程模型齊了' + (f'，還缺 {len(mb)} 個檔（約 {fmt_b(sum(mb.values()))}）' if mb else ''), '' if not mb else '到「🧪 比較」勾想用的，按「⬇ 下載勾選流程缺的模型」')
        except Exception as ex: add('warn', '比較清單的模型', f'讀不到：{ex}')
        try:                                                                 # V0.3.17 四個模式能不能用
            names = {w['name']: w for w in self.gen_workflows()}
            for title, cands in (('🎨 改一張圖', ('GROK 改圖（INT8 快）', 'Qwen 2.1 Turbo 改圖')), ('🧩 兩張圖合併', ('兩張圖合併（INT8 快）', '兩張圖合併（Qwen 快）', '三張圖合併（人物＋衣服＋場景）')),
                                 ('🎬 照片變影片', ('H3 照片動起來', 'H3 照片動起來（臉穩定）')), ('🎞 首尾幀影片', ('H3 首尾幀生影片',))):
                have = [n for n in cands if n in names and not names[n].get('err')]
                if not have: add('warn', title, '流程還沒做好', 'ComfyUI 開著時會自動從官方範本做；也可以在生圖頁點那個模式，會問要不要現在做'); continue
                miss = sorted({m['file'] for n in have for m in self.gen_models(n) if not m['ok']})
                add('ok' if not miss else 'warn', title, f'{len(have)} 個流程可以用' + (f'，缺 {len(miss)} 個模型' if miss else ''), ('缺：' + '、'.join(miss[:3]) + '（生圖頁選那個流程，按「⬇ 下載缺的模型」）') if miss else '')
        except Exception as ex: add('warn', '四個模式', f'讀不到：{ex}')
        bad = [d for d in self.dl.values() if d['state'] == 'fail']; run = [d for d in self.dl.values() if d['state'] in ('wait', 'run')]
        if run: add('ok', '下載中', f'{len(run)} 個：' + '、'.join(d['file'] for d in run[:3]))
        for d in bad[:5]: add('bad', '下載失敗', f'{d["file"]}：{d.get("msg", "")}', '金鑰／網路問題補好後，到比較頁或生圖頁再按一次下載（會接著下載）')
        q = len(self.gen_q) + len(self.gen_active)
        if q: add('ok', '排隊', f'{q} 個工作（含正在跑的）')
        nf = int((self.db.one("SELECT COUNT(*) FROM gen_jobs WHERE state='fail' AND t>?", (time.time() - 86400,)) or [0])[0] or 0)
        if nf: add('warn', '最近 24 小時失敗', f'{nf} 張', '歷史紀錄篩「✖ 失敗」看原因；比較頁可以「↻ 失敗的重跑」')
        return L

    def cmp_vote(self, jid, v):
        v = max(0, min(5, int(v or 0))); self.db.x('UPDATE gen_jobs SET vote=? WHERE id=?', (v, int(jid))); return v

    def gen_file(self, rel):
        """'outputs/…' 或 'inputs/…' → 實際路徑（不能跑出這兩個資料夾）."""
        rel = str(rel or '').replace('\\', '/')
        top = rel.split('/')[0]
        if top not in ('outputs', 'inputs', 'trash', 'people') or '..' in rel.split('/'): return None
        p = (self.data / rel).resolve(); base = (self.data / top).resolve()
        if base not in p.parents or not p.is_file(): return None
        return p

    # ---- 工作
    def gen_add(self, wf, prompt, img='', neg='', n=1, src='電腦', seed=-1, params=None, imgs=None, mask='', ref='', chain=None, cue=''):
        """img＝一張照片；imgs＝好幾張（照順序給圖一、圖二…）."""
        imgs = [x for x in (imgs or [img]) if x]; img = imgs[0] if imgs else ''
        n = max(1, min(20, int(n or 1))); wf = str(wf or self.cfg.get('gen_wf') or '')
        W = next((x for x in self.gen_workflows() if x['name'] == wf), None)
        if W is None: raise comfy.ComfyError(f'找不到流程「{wf}」')
        if W.get('err'): raise comfy.ComfyError(f'流程「{wf}」不能用：{W["err"]}')
        need = int(W.get('n_img') or (1 if W.get('need_img') else 0))
        if need and len(imgs) < need: raise comfy.ComfyError('這個流程要先選一張照片' if need == 1 else f'這個流程要 {need} 張照片：' + '、'.join(W.get('slots') or []))
        imgs = imgs[:need] if need else []; img = imgs[0] if imgs else ''
        for x in imgs:
            if '..' in str(x) or re.search(r'[/\\]', str(x)) or not (self.data / 'inputs' / x).is_file(): raise comfy.ComfyError('照片不見了，請重新選一次')
        defs = self.gen_params(wf); eff, sd = comfy.cast_params(defs, params)
        if sd < 0 and seed is not None and int(seed) >= 0: sd = int(seed)
        mods = [it['id'] for g in defs if g['g'] == '模型／LoRA' for it in g['items']]
        ekey = self._hash([wf, eff]); mkey = self._hash([wf, {k: eff.get(k) for k in mods}])
        iw, ih = comfy.img_size((self.data / 'inputs' / img).read_bytes()[:300000]) if img else (0, 0)
        ids = []
        for i in range(n):
            with self.db.lock:
                c = self.db.con.execute('INSERT INTO gen_jobs(t,src,wf,prompt,neg,img,imgs,seed,state,params,ekey,mkey,in_w,in_h) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                        (time.time(), src, wf, str(prompt or ''), str(neg or ''), img or '', json.dumps(imgs), (sd + i) if sd >= 0 else -1, 'wait',
                                         json.dumps(eff, ensure_ascii=False), ekey, mkey, iw, ih))
                self.db.con.commit(); ids.append(int(c.lastrowid))
        def _safe(n): return bool(n) and re.fullmatch(r'[^/\\]+', str(n)) is not None and '..' not in str(n)   # 只收 inputs 裡的檔名
        mask = mask if _safe(mask) else ''; ref = ref if _safe(ref) else ''
        if mask and img and (self.data / 'inputs' / str(mask)).is_file() and not self.is_video_name(img):
            self.db.x(f'UPDATE gen_jobs SET mask=?, cue=? WHERE id IN ({",".join("?" * len(ids))})', [str(mask), cue if cue in ('gray', 'red') else ''] + ids)
        if isinstance(chain, dict) and chain.get('wf'):
            self.db.x(f'UPDATE gen_jobs SET chain=? WHERE id IN ({",".join("?" * len(ids))})', [json.dumps({k: chain.get(k) for k in ('kind', 'wf', 'prompt', 'params', 'prompts', 'segs')}, ensure_ascii=False)] + ids)
        if ref and (self.data / 'inputs' / str(ref)).is_file() and not self.is_video_name(ref):
            self.db.x(f'UPDATE gen_jobs SET ref=? WHERE id IN ({",".join("?" * len(ids))})', [str(ref)] + ids)
        with self.lock: self.gen_q.extend(ids)
        self.cfg.set('gen_wf', wf); self.log.w(f'生圖：{src}排了 {n} 張（{wf}；{self.param_brief(eff)}）：{str(prompt)[:80]}'); return ids

    def gen_set_batch(self, ids):
        """同一次送出、超過一個工作 → 標成同一批（用最小的編號當批號）."""
        ids = sorted({int(x) for x in ids or []})
        if len(ids) < 2: return 0
        self.db.x(f'UPDATE gen_jobs SET batch=? WHERE id IN ({",".join("?" * len(ids))})', [ids[0]] + ids); return ids[0]

    def gen_batch_rows(self, b):
        return [self._row(r) for r in self.db.q('SELECT * FROM gen_jobs WHERE batch=? AND deleted=0 ORDER BY id', (int(b),))]

    def gen_cancel(self, jid):
        jid = int(jid)
        with self.lock:
            if jid in self.gen_q:
                self.gen_q.remove(jid); self.db.x("UPDATE gen_jobs SET state='stop', msg='已取消' WHERE id=?", (jid,)); self.log.w(f'生圖：#{jid} 取消（還沒開始）'); return True
        J = self.gen_active.get(jid)
        if J: J['cancel'] = True; self.log.w(f'生圖：#{jid} 取消（中斷 ComfyUI）'); return True
        return False

    def comfy_exe(self):
        """ComfyUI 的程式在哪（設定 comfy_exe；沒設就找常見安裝位置）.
        V0.3.73 加「Comfy Desktop\\Comfy Desktop.exe」（新版 Comfy Desktop 的名字），再找 Programs 底下名字有 comfy 的資料夾."""
        c = str(self.cfg.get('comfy_exe') or '').strip().strip('"')
        if c and os.path.isfile(c): return c
        if getattr(self, '_cexe', None) and os.path.isfile(self._cexe): return self._cexe
        la = os.environ.get('LOCALAPPDATA', ''); L = []
        if la:
            pg = os.path.join(la, 'Programs')
            L += [os.path.join(pg, 'Comfy Desktop', 'Comfy Desktop.exe'), os.path.join(pg, '@comfyorgcomfyui-electron', 'ComfyUI.exe'), os.path.join(pg, 'ComfyUI', 'ComfyUI.exe')]
            try:
                for d in sorted(os.listdir(pg)):
                    if 'comfy' not in d.lower(): continue
                    for f in sorted(os.listdir(os.path.join(pg, d))):
                        if f.lower().endswith('.exe') and 'comfy' in f.lower() and 'uninst' not in f.lower(): L.append(os.path.join(pg, d, f))
            except Exception: pass
        for x in L:
            if os.path.isfile(x): self._cexe = x; return x
        return ''

    def _comfy_open(self, exe):
        """像在桌面上點兩下那樣打開（Windows 用 os.startfile；.bat 也可以），不行再用 cmd start."""
        if os.name == 'nt':
            try: os.startfile(exe); return
            except Exception as ex: self.log.w(f'生圖：直接打開失敗（{ex}），改用 cmd start')
            subprocess.Popen(['cmd', '/c', 'start', '', exe], cwd=os.path.dirname(exe), creationflags=0x08000000); return
        subprocess.Popen([exe], cwd=os.path.dirname(exe), close_fds=True)

    def comfy_can(self): return bool(self.comfy_exe() or self._comfy_cmd())

    def _comfy_cmd(self):
        """V0.3.74 學到的 ComfyUI 啟動指令（{'cmd','cwd'}）：有就直接開 ComfyUI 本體，不經過 Comfy Desktop 首頁."""
        c = self.cfg.get('comfy_cmd') or {}
        if self.cfg.get('comfy_direct') is False or not isinstance(c, dict) or 'main.py' not in str(c.get('cmd', '')): return None
        return c

    def _ps_proc(self, pid):
        out = subprocess.run(['powershell', '-NoProfile', '-Command', f"Get-CimInstance Win32_Process -Filter 'ProcessId={int(pid)}' | Select-Object ProcessId,ParentProcessId,ExecutablePath,CommandLine | ConvertTo-Json -Compress"],
                             capture_output=True, text=True, timeout=30, creationflags=0x08000000).stdout.strip()
        return json.loads(out) if out.startswith('{') else {}

    def _comfy_learn(self):
        """V0.3.74 ComfyUI 開著時，記下它是怎麼啟動的（佔著連接埠的 python 的完整指令；venv 的話用外層那個），下次直接用這個指令開，不用再點「打開 ComfyUI」."""
        if os.name != 'nt': return
        try:
            port = urllib.parse.urlsplit(self.comfy_st.get('url') or '').port
            if not port: return
            pid = next(iter(self._port_pids(port)), 0)
            if not pid: return
            P = self._ps_proc(pid); cl = str(P.get('CommandLine') or '')
            if 'main.py' not in cl: return
            par = self._ps_proc(P.get('ParentProcessId') or 0) if P.get('ParentProcessId') else {}
            pcl = str(par.get('CommandLine') or '')
            if 'main.py' in pcl and 'python' in str(par.get('ExecutablePath') or '').lower(): cl = pcl   # venv 的 python.exe 會再開一個真正的 python：用外層的（才有套件）
            m = re.search(r'"([^"]*main\.py)"', cl) or re.search(r'(\S*main\.py)', cl); cwd = os.path.dirname(m.group(1)) if m and os.path.isabs(m.group(1)) else ''
            new = {'cmd': cl, 'cwd': cwd, 't': int(time.time())}
            old = self.cfg.get('comfy_cmd') or {}
            if not isinstance(old, dict) or old.get('cmd') != cl:
                self.cfg.set('comfy_cmd', new); self.log.w(f'生圖：學到 ComfyUI 的啟動指令（下次自己直接開，不用點「打開 ComfyUI」）：{cl[:200]}')
        except Exception as ex: self.log.w(f'生圖：記 ComfyUI 啟動指令失敗（不影響）：{ex}')

    def _comfy_run(self, c):
        """用學到的指令直接啟動 ComfyUI（開一個縮小的黑視窗，看得到它的訊息；關掉那個視窗就是關 ComfyUI）."""
        si = None
        if os.name == 'nt':
            si = subprocess.STARTUPINFO(); si.dwFlags |= 1; si.wShowWindow = 7                    # SW_SHOWMINNOACTIVE
        subprocess.Popen(c['cmd'], cwd=c.get('cwd') or None, startupinfo=si, close_fds=True, creationflags=(0x00000010 | 0x00000200) if os.name == 'nt' else 0, shell=os.name != 'nt')

    def comfy_launch(self, why='手機'):
        """打開 ComfyUI。5 分鐘內開過就不再開（它可能正在啟動）."""
        exe = self.comfy_exe(); cmd = self._comfy_cmd()
        if not exe and not cmd: return {'ok': False, 'message': '找不到 ComfyUI 的程式：到「設定 → ComfyUI → ComfyUI 程式位置」填 Comfy Desktop.exe（或免安裝版的 run_nvidia_gpu.bat）的完整路徑'}
        if time.time() - getattr(self, '_comfy_launch_t', 0) < 300: return {'ok': False, 'message': '5 分鐘內已經叫它開過了，ComfyUI 可能還在啟動，等一下'}
        if cmd:
            try:
                self._comfy_launch_t = time.time(); self._comfy_run(cmd)
                self.log.w(f'生圖：直接啟動 ComfyUI（{why}）：{cmd["cmd"][:200]}')
                return {'ok': True, 'message': '🚀 直接啟動 ComfyUI 了（不用再點「打開 ComfyUI」；大約 1～2 分鐘，好了會自動接著做）'}
            except Exception as ex: self.log.w(f'生圖：直接啟動失敗（{ex}），改開 Comfy Desktop')
            if not exe: return {'ok': False, 'message': '直接啟動 ComfyUI 失敗，也找不到 Comfy Desktop'}
        try:
            self._comfy_launch_t = time.time(); self._comfy_open(exe)
            self.log.w(f'生圖：打開 ComfyUI（{why}）：{exe}' + ('' if cmd else '（還沒學到直接啟動的指令：新版 Comfy Desktop 可能要再點一次「打開 ComfyUI」；ComfyUI 開著時這邊會自動學）'))
            return {'ok': True, 'message': '🚀 叫 ComfyUI 打開了（啟動大約 1～2 分鐘，好了會自動接著做）' + ('' if cmd else '。如果停在 Comfy 首頁，請點右上角「打開 ComfyUI」一次，之後這邊就會自己直接啟動')}
        except Exception as ex: return {'ok': False, 'message': f'打不開 ComfyUI：{ex}'}

    def _comfy_autofix(self):
        """V0.3.73 連不到 ComfyUI 不空等：等 1 分鐘 → 程式沒在跑就打開、還開著（卡住）就重開；
        之後給它 5 分鐘啟動，還連不到再試一次，再來每 10 分鐘試一次."""
        if self.cfg.get('comfy_autostart') is False or not self.comfy_can() or getattr(self, '_comfy_rs_busy', False): return
        now = time.time(); w0 = getattr(self, 'gen_wait_t', now)
        if getattr(self, '_fix_w', None) != w0: self._fix_w, self._fix_n, self._fix_t = w0, 0, 0
        if now - w0 < 90 or (self._fix_n and now - self._fix_t < (300 if self._fix_n == 1 else 600)): return
        self._fix_n += 1; self._fix_t = now; m = max(1, round((now - w0) / 60))
        if self._comfy_pids(): self.comfy_restart(f'連不到 {m} 分鐘、程式還開著（多半卡住）')
        else: self._comfy_launch_t = 0; self.comfy_launch(f'連不到 {m} 分鐘，自動打開')

    def _port_pids(self, port):
        """Windows：哪些程式在聽這個連接埠（netstat）."""
        try:
            out = subprocess.run(['netstat', '-ano', '-p', 'TCP'], capture_output=True, text=True, timeout=15, creationflags=0x08000000).stdout
            return {int(f[4]) for f in (l.split() for l in out.splitlines()) if len(f) >= 5 and f[3].upper() == 'LISTENING' and f[1].rsplit(':', 1)[-1] == str(port) and f[4].isdigit()}
        except Exception as ex: self.log.w(f'生圖：查連接埠 {port} 失敗：{ex}'); return set()

    def _comfy_pids(self):
        """V0.3.72 ComfyUI 的程式：佔著 ComfyUI 連接埠的那個（python）＋Comfy Desktop 本體（ComfyUI.exe）."""
        if os.name != 'nt': return []
        NW = 0x08000000; P = set()
        try: port = urllib.parse.urlsplit(self.comfy_st.get('url') or self.cfg.get('comfy_url') or 'http://127.0.0.1:8000').port or 8000
        except Exception: port = 8000
        P.update(self._port_pids(port))
        exe = os.path.basename(self.comfy_exe() or 'ComfyUI.exe')
        if exe.lower().endswith('.exe'):
            try:
                out = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {exe}', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=15, creationflags=NW).stdout
                for l in out.splitlines():
                    f = [x.strip('"') for x in l.split('","')]
                    if len(f) > 1 and f[1].isdigit(): P.add(int(f[1]))
            except Exception: pass
        P.discard(os.getpid()); P.discard(0)
        return sorted(P)

    def comfy_restart(self, why='手機'):
        """V0.3.72 🔄 重開 ComfyUI：關掉（連子程式一起）→ 等它真的關了 → 再打開。正在做的工作會自動放回排隊，ComfyUI 好了接著做.
        只重開，不更新（要更新等你在電腦前自己決定）。"""
        if getattr(self, '_comfy_rs_busy', False): return {'ok': False, 'message': '正在重開 ComfyUI 了，等一下'}
        exe = self.comfy_can()
        if not exe: return {'ok': False, 'message': '找不到 ComfyUI 的程式：先到「設定 → 生圖」填 ComfyUI 的位置（Comfy Desktop 的 ComfyUI.exe，或免安裝版的 run_nvidia_gpu.bat），重開後才打得開'}
        self._comfy_rs_busy = True
        def go():
            try:
                P = self._comfy_pids(); self.log.w(f'生圖：🔄 重開 ComfyUI（{why}）：關掉 {P or "（沒找到在跑的）"}')
                for pid in P:
                    try: subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True, timeout=20, creationflags=0x08000000)
                    except Exception: pass
                for _ in range(30):                                              # 等它關乾淨（最多 30 秒）
                    if not self._comfy_pids(): break
                    time.sleep(1)
                time.sleep(3); self.comfy_st.update(t=0, url='', stats=None, err='重開中', bad=2, ok_t=0); self._comfy_launch_t = 0
                r = self.comfy_launch(why + '：重開'); self._comfy_rs_t = time.time()
                if not r.get('ok'): self.log.w('生圖：重開 ComfyUI：' + r.get('message', ''))
            except Exception: self.log.err('重開 ComfyUI')
            finally: self._comfy_rs_busy = False
        threading.Thread(target=go, name='ComfyRestart', daemon=True).start()
        return {'ok': True, 'message': '🔄 重開 ComfyUI 中：先關掉、再打開（大約 1～2 分鐘）。正在做的會放回排隊，好了自動接著做'}

    def _comfy_daily(self):
        """V0.3.72 每 comfy_restart_h 小時（預設 24）趁空檔重開一次 ComfyUI：這邊沒排隊、沒在做、閒了 10 分鐘以上才動."""
        h = float(self.cfg.get('comfy_restart_h') or 0)
        if h <= 0 or self.gen_q or self.gen_active or not self.comfy_can(): return
        S = self.comfy_st; now = time.time()
        if not S.get('url'): return
        up = S.setdefault('up_t', now)
        if now - up < h * 3600 or now - getattr(self, '_gen_idle_t', now) < 600: return
        if now - getattr(self, '_comfy_rs_t', 0) < h * 3600: S['up_t'] = getattr(self, '_comfy_rs_t', now); return
        try:
            q = comfy.Comfy(S['url']).queue()
            if q.get('queue_running') or q.get('queue_pending'): return       # ComfyUI 自己還有工作（別的地方送的）→ 不動
        except Exception: return
        S['up_t'] = now; self.comfy_restart(f'每 {h:g} 小時趁空檔重開')

    def gen_cancel_many(self, batch=0, run=False):
        """V0.3.39 ⏹ 批量取消：batch＝只取消這一批（同一次送出的），0＝全部；run＝連正在跑的也中斷。一次改完（幾百個也很快）."""
        b = int(batch or 0); n = 0
        with self.lock:
            Q = list(self.gen_q)
            if b:
                bs = {r[0] for r in self.db.q(f'SELECT id FROM gen_jobs WHERE batch=? OR id=?', (b, b))}
                Q = [j for j in Q if j in bs]
            for j in Q: self.gen_q.remove(j)
            for i in range(0, len(Q), 500):
                part = Q[i:i + 500]; self.db.x(f"UPDATE gen_jobs SET state='stop', msg='已取消（批量）' WHERE id IN ({','.join('?' * len(part))})", part)
            n = len(Q)
        k = 0
        if run:
            for jid, J in list(self.gen_active.items()):
                if not b or int(J.get('batch') or 0) == b or jid == b: J['cancel'] = True; k += 1
        if n or k: self.log.w(f'生圖：批量取消 {n} 個排隊' + (f'、中斷 {k} 個正在跑' if k else '') + (f'（第 #{b} 批）' if b else '（全部）'))
        return {'ok': True, 'n': n, 'run': k, 'message': f'⏹ 取消了 {n} 個排隊' + (f'，正在跑的 {k} 個也中斷' if k else '')}

    def gen_qsum(self):
        """排隊總數、每一批還有幾個在排（手機的「取消這一批」用）."""
        with self.lock: Q = list(self.gen_q)
        if not Q: return {'n': 0, 'b': {}}
        B = {}
        for i in range(0, len(Q), 500):
            part = Q[i:i + 500]
            for jid, bt in self.db.q(f"SELECT id, batch FROM gen_jobs WHERE id IN ({','.join('?' * len(part))})", part):
                k = str(int(bt or 0) or jid); B[k] = B.get(k, 0) + 1
        return {'n': len(Q), 'b': B}

    @staticmethod
    def launch_advice(argv, vram=0):
        """V0.1.83 ⚡ 加速檢查：看 ComfyUI 啟動參數有沒有拖慢的設定 → (ok/warn, 建議).
        3060 12GB：--lowvram／--novram／--reserve-vram 太大都會逼模型一直搬進搬出（Qwen 2.1 Turbo 7B 本來整顆放得下）；--cpu 根本沒用顯卡。"""
        A = [str(x) for x in argv or []]; tips = []; bad = False
        def val(k):
            for i, x in enumerate(A):
                if x == k and i + 1 < len(A): return A[i + 1]
                if x.startswith(k + '='): return x.split('=', 1)[1]
            return None
        if '--cpu' in A: bad = True; tips.append('有 --cpu：完全沒用顯示卡，會慢幾十倍，拿掉')
        for k in ('--novram', '--lowvram'):
            if k in A: bad = True; tips.append(f'有 {k}：會逼模型放在記憶體、每一步搬進顯卡，Qwen 2.1 Turbo 會變慢很多；12GB 顯卡拿掉讓 ComfyUI 自己判斷')
        rv = val('--reserve-vram')
        try:
            if rv is not None and float(rv) > 2: bad = True; tips.append(f'--reserve-vram {rv}：保留太多顯示卡記憶體給別人用，模型放不下就變慢；建議 1 以下或拿掉')
        except ValueError: pass
        if '--disable-smart-memory' in A: tips.append('有 --disable-smart-memory：每次都重新載入模型，連續做很多張時比較慢')
        if not any(x in A for x in ('--use-sage-attention', '--use-flash-attention')):
            tips.append('可以試：Python 環境裝 sageattention 後加 --use-sage-attention（網路實測 Qwen 改圖快 10～14%；如果出現全黑的圖就拿掉）')
        if not any(x.startswith('--preview-method') for x in A): tips.append('想在手機看到算到一半的即時預覽：加 --preview-method auto（不影響速度太多）')
        if bad: tips.append('改的地方：Comfy Desktop 左下 ⚙ 設定 → Server-Config（伺服器設定），改完重開 ComfyUI')
        return ('warn' if bad else 'ok'), '；'.join(tips)

    def gen_rerun(self, jid, src='電腦', wf=None, params=None, same_seed=False, n=1):
        """再跑一次；wf＝換另一個流程跑（V0.1.81「🏆 用 GROK 精修」：同一張照片、同一句提示詞），params 用那個流程自己的設定."""
        r = self.db.one('SELECT * FROM gen_jobs WHERE id=?', (int(jid),))
        if not r: raise comfy.ComfyError('找不到這個工作')
        try: P = json.loads(r['params'] or '{}')
        except Exception: P = {}
        try: I = json.loads(r['imgs'] or '[]')
        except Exception: I = []
        if wf and wf != r['wf']: P = dict(params or {})
        seed = r['seed'] if same_seed and 'seed' in r.keys() and r['seed'] is not None else -1
        return self.gen_add(wf or r['wf'], r['prompt'], r['img'], r['neg'], max(1, min(8, int(n or 1))), src, seed=seed, params=P, imgs=I or None, mask=(r['mask'] if 'mask' in r.keys() else '') or '', cue=(r['cue'] if 'cue' in r.keys() else '') or '', ref=(r['ref'] if 'ref' in r.keys() else '') or '')

    def gen_reuse(self, jid, idx=0):
        """拿結果當新的照片（再改一次）→ 回傳 inputs 裡的檔名."""
        r = self.db.one('SELECT outs FROM gen_jobs WHERE id=?', (int(jid),)); outs = json.loads(r['outs'] or '[]') if r else []
        if not outs: raise comfy.ComfyError('這個工作沒有結果圖')
        p = self.gen_file(outs[max(0, min(len(outs) - 1, int(idx or 0)))])
        if p is None: raise comfy.ComfyError('結果檔不見了')
        return self.gen_save_input(p.read_bytes(), f'#{jid} 的結果')

    def gen_thumb(self, p, w=480):
        """V0.1.96 縮圖：手機上清單只要小圖（原圖 1～3MB，縮圖 30～60KB），第一次做好存在 Data\\thumbs，之後直接給.
        用 PySide6 的 QImage（電腦版本來就有）；做不出來（沒有 Qt、壞圖）回 None＝給原圖."""
        try:
            w = max(96, min(1024, int(w))); st = p.stat()
            if self.is_video_name(p.name) or st.st_size < 150_000: return None
            t = self.data / 'thumbs' / (hashlib.sha1(f'{p}|{st.st_mtime_ns}|{w}'.encode()).hexdigest()[:20] + '.jpg')
            if t.is_file(): return t
            from PySide6.QtGui import QImage
            from PySide6.QtCore import Qt
            im = QImage(str(p))
            if im.isNull() or max(im.width(), im.height()) <= w: return None
            im = im.scaledToWidth(w, Qt.SmoothTransformation) if im.width() >= im.height() else im.scaledToHeight(w, Qt.SmoothTransformation)
            t.parent.mkdir(parents=True, exist_ok=True); tmp = t.with_suffix('.tmp')
            if not im.save(str(tmp), 'JPG', 82): return None
            os.replace(str(tmp), str(t)); return t
        except Exception: return None

    def gen_top(self, jid):
        """V0.3.05 ⏫ 排隊中的工作移到最前面（下一個就做它）."""
        jid = int(jid)
        with self.lock:
            if jid not in self.gen_q: return False
            self.gen_q.remove(jid); self.gen_q.appendleft(jid)
        self._pick_wf = None; self._jump = 0; return True

    def gen_preview(self, jid):
        """V0.2.86 正在跑的工作最新的預覽圖 bytes（沒有就 None）."""
        J = self.gen_active.get(int(jid)); pv = (J or {}).get('_pv')
        return pv[1] if pv and time.time() - pv[0] < 120 else None

    def gen_hide(self, jid):
        self.db.x('UPDATE gen_jobs SET hidden=1 WHERE id=?', (int(jid),)); self.oplog('生圖：從清單移除', f'#{jid}（檔案留著）'); return True

    def _row(self, r):
        d = {k: r[k] for k in r.keys()}
        for k, dv in (('outs', []), ('params', {}), ('imgs', [])):
            try: d[k] = json.loads(d.get(k) or json.dumps(dv))
            except Exception: d[k] = dv
        d['brief'] = self.param_brief(d['params'])
        try: d['pbrief'] = self.prof_brief(json.loads(d.get('prof') or '{}'))
        except Exception: d['pbrief'] = ''
        if d.get('deleted'):                                                   # 回收桶裡的：縮圖改指到 trash 裡的檔
            try: T = json.loads(d.get('trash') or '{}')
            except Exception: T = {}
            d['outs'] = [T.get(o, o) for o in d['outs']]; d['tins'] = {('inputs/' + x): T.get('inputs/' + x) for x in (d.get('imgs') or [])}
        return d

    @staticmethod
    def _px_guess(P, iw, ih):
        """照參數猜輸出大概幾個像素（預估時間用）."""
        r = (min(iw, ih) / max(iw, ih)) if iw and ih else 1.0
        for k, v in P.items():
            if k.endswith('.scale_to_length') and isinstance(v, (int, float)):
                side = P.get(k.rsplit('.', 1)[0] + '.scale_to_side', 'longest')
                return v * v * (r if side in ('longest', 'width', 'height') else 1 / max(r, 0.05))
            if k.endswith('.megapixels') and isinstance(v, (int, float)): return v * 1e6
        w = next((v for k, v in P.items() if k.endswith('.width') and isinstance(v, (int, float)) and v > 0), 0)
        h = next((v for k, v in P.items() if k.endswith('.height') and isinstance(v, (int, float)) and v > 0), 0)
        return w * h if w and h else None

    def gen_estimate(self, wf, ekey, mkey, P=None, iw=0, ih=0):
        """用以前跑過的紀錄預估「運算時間」：同流程同設定的中位數；沒有就用同流程、照像素×步數換算（僅供參考）。
        要載入模型（換了模型、ComfyUI 剛開）時優先看以前「冷啟動」的紀錄."""
        cold = self.gen_hot != mkey; ck = (wf, ekey, cold, iw * 7 + ih); c = self.est_cache.get(ck)
        if c and time.time() - c[0] < 15: return c[1]
        rows = self.db.q("SELECT run_s,cold,out_w,out_h,ekey,params FROM gen_jobs WHERE state='done' AND wf=? AND run_s>0 ORDER BY id DESC LIMIT 300", (wf,))
        med = lambda L: float(statistics.median(L)) if L else None
        def pick(L):
            if cold:
                C_ = [r for r in L if r['cold'] == 1]
                if C_: return C_
            return [r for r in L if r['cold'] != 1] or L
        out = None; same = [r for r in rows if r['ekey'] == ekey]
        if same:
            L = pick(same)[:15]; out = {'sec': med([r['run_s'] for r in L]), 'n': len(L), 'how': '同流程、同設定'}
        elif rows:
            L = pick(rows)[:40]; P = P or {}; steps = lambda Q: sum(v for k, v in Q.items() if k.endswith('.steps') and isinstance(v, (int, float))) or 1
            px = self._px_guess(P, iw, ih); rates = []
            for r in L:
                try: Q = json.loads(r['params'] or '{}')
                except Exception: Q = {}
                if r['out_w'] and r['out_h'] and px: rates.append(r['run_s'] * max(0.2, min(5.0, px * steps(P) / (r['out_w'] * r['out_h'] * steps(Q)))))
            if rates: out = {'sec': med(rates), 'n': len(rates), 'how': '同流程、照解析度×步數換算（僅供參考）'}
            else: out = {'sec': med([r['run_s'] for r in L]), 'n': len(L), 'how': '同流程、設定不同（僅供參考）'}
        if out is not None: out['cold'] = cold
        self.est_cache[ck] = (time.time(), out); return out

    @staticmethod
    def _prog(d, now):
        """整體進度（0～99%）：有以前的時間紀錄 → 照「已跑多久／預估多久」（最接近真的）；沒有 → 照跑到第幾個節點＋這個節點第幾步；都沒有 → 取樣步數."""
        est = (d.get('est') or {}).get('sec'); ts = d.get('t_start') or 0; tot = d.get('ntot') or 0
        if not ts: return {'prog': 0.0, 'prog_how': 'wait'}
        if est: return {'prog': round(min(99.0, (now - ts) / est * 100), 1), 'prog_how': 'time'}
        if tot:
            st = (d['step'] / d['max']) if d.get('max') else 0; inner = min(1.0, (d.get('ndone', 0) + d.get('ncached', 0) + st) / tot)
            if d.get('seg') and d.get('nseg'): return {'prog': round(min(99.0, (d['seg'] - 1 + inner) / d['nseg'] * 100), 1), 'prog_how': 'seg'}   # 影片分段：第幾段＋這段做到哪
            return {'prog': round(min(99.0, inner * 100), 1), 'prog_how': 'node'}
        return {'prog': float(d.get('pct') or 0), 'prog_how': 'step'}

    def gen_jobs(self, limit=30):
        rows = self.db.q('SELECT * FROM gen_jobs WHERE hidden=0 AND deleted=0 ORDER BY id DESC LIMIT ?', (int(limit),)); Q = list(self.gen_q); L = []; now = time.time()
        for r in rows:
            d = self._row(r); J = self.gen_active.get(d['id'])
            if J:
                d.update(state='run', stall=bool(J.get('stall')), pct=J.get('pct'), msg=J.get('msg', ''), step=J.get('step'), max=J.get('max'), t_start=J.get('t_start') or 0,
                         ndone=J.get('ndone') or 0, ncached=J.get('ncached') or 0, ntot=J.get('ntot') or 0, seg=J.get('seg') or 0, nseg=J.get('nseg') or 0)
            elif d['state'] == 'wait' and d['id'] in Q:
                d['qpos'] = Q.index(d['id']) + 1
                if self.gen_wait: d['msg'] = '等 ComfyUI 開…'
            if d['state'] in ('wait', 'run'):
                try: d['est'] = self.gen_estimate(d['wf'], d['ekey'], d['mkey'], d['params'], d['in_w'], d['in_h'])
                except Exception: d['est'] = None
            if d['state'] == 'run': d.update(self._prog(d, now))
            L.append(d)
        ahead = 0.0                                                         # 排隊的：前面的都做完大概要多久
        for d in sorted([x for x in L if x['state'] in ('wait', 'run')], key=lambda x: (x['state'] != 'run', x.get('qpos') or 0)):
            e = (d.get('est') or {}).get('sec')
            if d['state'] == 'run':
                if e: ahead += max(0.0, e - (now - (d.get('t_start') or now)))
            else:
                d['eta'] = ahead if ahead else None
                ahead += e or 0
        return L

    def gen_history(self, q='', state='', wf='', offset=0, limit=50, view=''):
        """歷史紀錄：搜尋提示詞、篩狀態／流程、分頁。view＝''（平常）／hidden（已隱藏）／trash（回收桶）."""
        W = ['deleted>0'] if view == 'trash' else ['deleted=0', 'vote>=4'] if view == 'star' else ['deleted=0', 'hist_hidden=1' if view == 'hidden' else 'hist_hidden=0']; A = []   # star＝⭐ 你打 4 星以上的
        if q: W.append('(prompt LIKE ? OR CAST(id AS TEXT)=?)'); A += [f'%{q}%', str(q).lstrip('#')]
        if state: W.append('state=?'); A.append(state)
        if wf and '|' in wf:                                                 # V0.2.73 好幾個流程一起篩（四個模式）
            L = [x for x in wf.split('|') if x][:20]; W.append(f'wf IN ({",".join("?" * len(L))})'); A += L
        elif wf: W.append('wf=?'); A.append(wf)
        where = (' WHERE ' + ' AND '.join(W)) if W else ''
        # 分頁照「組」算：同一批算一組，整批一起給（不會被分頁切開）；offset／limit／total 都是組數
        U = OrderedDict()
        for jid, b in self.db.q(f'SELECT id, batch FROM gen_jobs{where} ORDER BY id DESC', A): U.setdefault(-jid if view == 'star' else (b or -jid), []).append(jid)
        keys = list(U)[max(0, int(offset)):max(0, int(offset)) + max(1, min(200, int(limit)))]; total = len(U)
        ids = [i for k in keys for i in U[k]][:2000]
        rows = self.db.q(f'SELECT * FROM gen_jobs WHERE id IN ({",".join("?" * len(ids))}) ORDER BY id DESC', ids) if ids else []
        cnt = {k: int((self.db.one(f'SELECT COUNT(*) FROM gen_jobs WHERE {w}') or [0])[0] or 0) for k, w in (('hidden', 'deleted=0 AND hist_hidden=1'), ('trash', 'deleted>0'), ('star', 'deleted=0 AND vote>=4'))}
        return {'rows': [self._row(r) for r in rows], 'total': total, 'units': len(keys), 'counts': cnt, 'wfs': [r[0] for r in self.db.q('SELECT DISTINCT wf FROM gen_jobs ORDER BY wf')]}

    TRASH_DAYS = 30

    def gen_hist_act(self, ids, a):
        """歷史紀錄的動作（可以一次好幾筆）：hide 隱藏／unhide 取消隱藏／del 刪除（檔案搬進 Data\\trash，30 天內可以還原）／restore 還原／purge 永久刪除."""
        ids = [int(x) for x in ids or []][:500]; n = 0; busy = set(self.gen_active) | set(self.gen_q)
        for jid in ids:
            r = self.db.one('SELECT * FROM gen_jobs WHERE id=?', (jid,))
            if not r: continue
            if a == 'hide': self.db.x('UPDATE gen_jobs SET hist_hidden=1 WHERE id=?', (jid,)); n += 1
            elif a == 'unhide': self.db.x('UPDATE gen_jobs SET hist_hidden=0 WHERE id=?', (jid,)); n += 1
            elif a == 'del' and not r['deleted']:
                if jid in busy or r['state'] in ('wait', 'run'): continue          # 還在排隊／跑的不刪（先取消）
                n += self._trash_job(r)
            elif a == 'restore' and r['deleted']: n += self._untrash_job(r)
            elif a == 'purge' and r['deleted']:
                try: T = json.loads(r['trash'] or '{}')
                except Exception: T = {}
                for tr in T.values():
                    p = self.gen_file(tr)
                    if p is not None:
                        try: p.unlink()
                        except Exception: pass
                try: shutil.rmtree(self.data / 'trash' / str(jid), ignore_errors=True)
                except Exception: pass
                self.db.x('DELETE FROM gen_jobs WHERE id=?', (jid,)); n += 1
        if n: self.oplog(f'歷史紀錄：{a}', '、'.join(f'#{i}' for i in ids[:50])); self.log.w(f'歷史紀錄：{a} {n} 筆（{"、".join(f"#{i}" for i in ids[:20])}）')
        return n

    def _files_used_elsewhere(self, rel, jid):
        nm = rel.split('/')[-1]
        return bool(self.db.one("SELECT 1 FROM gen_jobs WHERE id<>? AND deleted=0 AND (img=? OR imgs LIKE ? OR outs LIKE ?) LIMIT 1", (jid, nm, f'%{nm}%', f'%{nm}%')))

    def _trash_job(self, r):
        jid = int(r['id']); T = {}; td = self.data / 'trash' / str(jid); td.mkdir(parents=True, exist_ok=True)
        try: outs = json.loads(r['outs'] or '[]')
        except Exception: outs = []
        try: ins = ['inputs/' + x for x in (json.loads(r['imgs'] or '[]') or ([r['img']] if r['img'] else [])) if x]
        except Exception: ins = []
        for rel in outs + ins:
            if rel.startswith('inputs/') and self._files_used_elsewhere(rel, jid): continue      # 照片別的工作還在用：不搬
            p = self.gen_file(rel)
            if p is None: continue
            dst = td / p.name
            try: shutil.move(str(p), str(dst)); T[rel] = f'trash/{jid}/{p.name}'
            except Exception: self.log.err(f'刪除 #{jid}：搬 {rel}')
        self.db.x('UPDATE gen_jobs SET deleted=?, trash=? WHERE id=?', (time.time(), json.dumps(T, ensure_ascii=False), jid)); return 1

    def _untrash_job(self, r):
        jid = int(r['id'])
        try: T = json.loads(r['trash'] or '{}')
        except Exception: T = {}
        for rel, tr in T.items():
            src = self.gen_file(tr); dst = self.data / rel
            if src is None or dst.exists(): continue
            try: dst.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(src), str(dst))
            except Exception: self.log.err(f'還原 #{jid}：搬回 {rel}')
        self.db.x("UPDATE gen_jobs SET deleted=0, trash='{}' WHERE id=?", (jid,)); return 1

    def gen_trash_purge_old(self):
        """回收桶放超過 30 天的：真的刪掉."""
        old = [int(r['id']) for r in self.db.q('SELECT id FROM gen_jobs WHERE deleted>0 AND deleted<?', (time.time() - self.TRASH_DAYS * 86400,))]
        if old: n = self.gen_hist_act(old, 'purge'); self.log.w(f'回收桶：超過 {self.TRASH_DAYS} 天的 {n} 筆永久刪除')

    def gen_stats(self):
        """時間統計：每個「流程＋設定」跑了幾次、平均（中位數）運算時間，冷啟動（要載入模型）分開算."""
        rows = self.db.q("SELECT wf,ekey,params,run_s,dur,cold,out_w,out_h,t FROM gen_jobs WHERE state='done' AND run_s>0 ORDER BY id DESC LIMIT 3000"); G = {}
        for r in rows:
            g = G.setdefault((r['wf'], r['ekey']), {'wf': r['wf'], 'params': r['params'], 'warm': [], 'cold': [], 'dur': [], 'px': [], 'last': r['t']})
            (g['cold'] if r['cold'] == 1 else g['warm']).append(r['run_s']); g['dur'].append(r['dur'])
            if r['out_w']: g['px'].append(f'{r["out_w"]}×{r["out_h"]}')
        out = []
        for g in G.values():
            try: P = json.loads(g['params'] or '{}')
            except Exception: P = {}
            med = lambda L: round(float(statistics.median(L)), 1) if L else None
            out.append({'wf': g['wf'], 'brief': self.param_brief(P), 'n': len(g['warm']) + len(g['cold']), 'warm': med(g['warm']), 'cold': med(g['cold']),
                        'warm_n': len(g['warm']), 'cold_n': len(g['cold']), 'dur': med(g['dur']), 'size': max(set(g['px']), key=g['px'].count) if g['px'] else '', 'last': g['last']})
        return sorted(out, key=lambda x: -x['last'])

    def _dl_pending(self, wf):
        """這個流程缺的模型裡，有沒有正在下載／排隊下載的（有 → 先跑別的，等它下載完）."""
        if not any(d['state'] in ('wait', 'run') for d in self.dl.values()): return False
        c = getattr(self, '_dlp_c', {}); now = time.time()
        if wf in c and now - c[wf][0] < 15: return c[wf][1]
        try: v = any((self.dl.get(m['file']) or {}).get('state') in ('wait', 'run') for m in self.gen_models(wf) if not m['ok'])
        except Exception: v = False
        c[wf] = (now, v); self._dlp_c = c; return v

    def _gen_pick(self):
        """下一個要跑的：照排隊順序，但模型還在下載的流程先跳過（可以「下載＋排隊」一起按了就去睡）.
        V0.1.87 同模型先跑：排隊前面幾個裡有跟剛剛同一個流程的，就先跑它（GROK 20GB 和 Qwen 互換一次要重新載入十幾秒）；
        最多連續插隊 6 次，別的流程不會一直等."""
        with self.lock: Q = list(self.gen_q)
        skip = set()
        if len(Q) > 1:                                                       # 你臨時送的單張（不是 🧪 比較那一大批）先跑：早上比較還沒跑完也不用等
            cm = {r[0]: r[1] for r in self.db.q(f'SELECT id, cmp FROM gen_jobs WHERE id IN ({",".join("?" * len(Q))})', Q)}
            Q = [j for j in Q if not cm.get(j)] + [j for j in Q if cm.get(j)]
        ok = []
        for jid in Q:
            r = self.db.one('SELECT wf, msg FROM gen_jobs WHERE id=?', (jid,))
            if r is None: break
            if r['wf'] in skip or self._dl_pending(r['wf']):
                skip.add(r['wf'])
                if r['msg'] != '等模型下載完': self.db.x("UPDATE gen_jobs SET msg='等模型下載完' WHERE id=?", (jid,))
                continue
            ok.append((jid, r['wf']))
            if len(ok) >= 8 or (len(ok) == 1 and ok[0][1] == getattr(self, '_pick_wf', None)): break
        if not ok: return None
        last = getattr(self, '_pick_wf', None); pick = ok[0]
        if last and pick[1] != last and getattr(self, '_jump', 0) < 6:
            same = next((x for x in ok if x[1] == last), None)
            if same: pick = same; self._jump = getattr(self, '_jump', 0) + 1
            else: self._jump = 0
        else: self._jump = 0
        with self.lock:
            try: self.gen_q.remove(pick[0])
            except ValueError: return None
        self._pick_wf = pick[1]; return pick[0]

    def _gen_boss(self):
        while self.alive():
            try:
                if self.gen_q or self.gen_active: self._gen_idle_t = time.time()
                elif time.time() - getattr(self, '_daily_ck', 0) > 60: self._daily_ck = time.time(); self._comfy_daily()   # V0.3.72 每天趁空檔重開 ComfyUI
                if self.gen_active: self.comfy_status()                       # V0.3.71 做的時候也更新顯示卡記憶體（握手只看這份，不自己連線）
                if self.gen_q or self.gen_active: self._gen_busy_t = time.time()
                elif getattr(self, '_gen_busy_t', 0) and time.time() - self._gen_busy_t > 60 and self.cfg.get('gen_free_idle') is not False:   # 全部做完 1 分鐘：叫 ComfyUI 把模型清出記憶體（整晚跑完，電腦不用一直佔著 12GB＋幾十 GB 記憶體）
                    self._gen_busy_t = 0
                    try:
                        st = self.comfy_status()
                        if st['ok']: comfy.Comfy(st['url']).free(); self._last_wf = None; self.log.w('生圖：排隊的都做完了，叫 ComfyUI 清掉記憶體')
                    except Exception as ex: self.log.w(f'生圖：做完清記憶體失敗（不影響）：{ex}')
                if self.gen_q and not self.gen_active and not self.bg_hold('gen'):
                    st = self.comfy_status()
                    if not st['ok']:
                        if not self.gen_wait: self.log.w(f'生圖：連不到 ComfyUI，{len(self.gen_q)} 個工作等它開'); self.gen_wait_t = time.time()
                        self.gen_wait = st['err'] or '連不到 ComfyUI'; self.gen_hot = None
                        self._comfy_autofix()                                 # V0.3.73 連不到就自動打開／重開，不空等
                        time.sleep(3); continue
                    if self.gen_wait: self.log.w('生圖：ComfyUI 回來了，繼續'); self.gen_wait = ''
                    jid = self._gen_pick()
                    if jid is None: time.sleep(2); continue
                    if jid:
                        r = self.db.one('SELECT * FROM gen_jobs WHERE id=?', (jid,))
                        if r and r['state'] in ('wait', 'run'):
                            J = {k: r[k] for k in r.keys()}; J.update(t0=time.time(), msg='準備中…', pct=None); self.gen_active[jid] = J; self.bg_mark('gen', f'#{jid} {J["prompt"][:40]}')
                            threading.Thread(target=self._gen_job, args=(J,), name='GenJob', daemon=True).start(); continue
                time.sleep(0.5)
            except Exception: self.log.err('生圖排程'); time.sleep(5)

    # ---- 跑一個 ComfyUI 工作（送出 → websocket 收進度 → 等 history）。分段影片會連續叫好幾次
    def _run_one(self, C, url, prompt, J, t, jid, t0):
        ws = None; cid = uuid.uuid4().hex; cached = set(); ok_end = True
        try:
            try: ws = comfy.WS(url, cid)
            except Exception as ex: self.log.w(f'生圖：websocket 連不上（改成定時查）：{ex}'); ws = None
            for k in ('nseen', 'max', 'step', 'pct', 'ndone', 'ncached'): J.pop(k, None)
            J['ntot'] = len(prompt)
            pid = C.queue_prompt(prompt, cid); J['pid'] = pid; J['submitted'] = True; t_sub = time.time(); ok_end = False
            dead = time.time() + max(1, int(self.cfg.get('gen_timeout_min') or 60)) * 60; last_h = 0; fin = False; fin_t = 0; H = None; started = False
            pre = f'第 {J["seg"]}／{J["nseg"] or "?"} 段 · ' if J.get('seg') else ''
            J['msg'] = pre + '送出了，等 ComfyUI…'
            act_t = J['act_t'] = time.time(); last_q = time.time(); lost = 0; J.pop('stall', None)
            stall_min = float(self.cfg.get('gen_stall_min') or 8); auto_min = float(self.cfg.get('gen_stall_auto_min') or 0)
            if re.search(r'H3|影片|video', J.get('wf') or '', re.I): stall_min *= 2; auto_min *= 1.5   # 影片一步比較久
            while True:
                if J.get('cancel') or self.stop_all: C.cancel(pid); raise InterruptedError
                # V0.3.42 卡住的處理：①ComfyUI 弄丟這個工作（重開／更新過）→ 馬上重新送出，不用等 60 分鐘 ②很久沒進度 → 提醒、可以按「中斷重來」，太久自動重來一次
                if time.time() - last_q > float(self.cfg.get('gen_lost_check_sec') or 15) and not fin:
                    last_q = time.time()
                    try:
                        q = C.queue(); ids = {x[1] for k in ('queue_running', 'queue_pending') for x in (q.get(k) or []) if len(x) > 1}
                        if pid in ids: lost = 0
                        elif not C.history(pid):
                            lost += 1
                            if lost >= 2: raise comfy.ComfyDown('ComfyUI 裡找不到這個工作了（多半重開或更新過），重新送出')
                    except comfy.ComfyDown as ex:
                        if 'ComfyUI 裡找不到' in str(ex): raise
                    except Exception: pass
                idle_m = (time.time() - act_t) / 60
                if started and idle_m >= stall_min and not J.get('stall'):
                    J['stall'] = time.time(); info = ''
                    try:
                        ss = C.get_json('/system_stats', timeout=8) or {}; dv = (ss.get('devices') or [{}])[0]; sy = ss.get('system') or {}
                        info = f"（顯示卡記憶體剩 {(dv.get('vram_free') or 0) / 2**30:.1f}／{(dv.get('vram_total') or 0) / 2**30:.0f} GB、RAM 剩 {(sy.get('ram_free') or 0) / 2**30:.1f}／{(sy.get('ram_total') or 0) / 2**30:.0f} GB）"
                    except Exception: info = '（ComfyUI 連問狀態都沒回：多半記憶體不夠，在用硬碟當記憶體）'
                    J['stall_info'] = info; J['msg'] = pre + f'⚠ {idle_m:.0f} 分鐘沒有進度{info}'; self.log.w(f'生圖：#{jid} ComfyUI {idle_m:.0f} 分鐘沒有進度{info}')
                if J.get('restart') or (started and auto_min and idle_m >= auto_min and not J.get('auto_rs')):
                    why = '你按了中斷重來' if J.get('restart') else f'{idle_m:.0f} 分鐘沒有進度，自動中斷、清記憶體、重排'
                    self.log.w(f'生圖：#{jid} {why}'); J['auto_rs'] = True
                    try: C.cancel(pid)
                    except Exception: pass
                    try: C.free(); self._last_wf = None
                    except Exception: pass
                    self.gen_restarted = getattr(self, 'gen_restarted', {}); n_ = self.gen_restarted.get(jid, 0)
                    self.gen_crs = getattr(self, 'gen_crs', set())
                    if J.get('auto_rs') and not J.get('restart') and n_ >= 1 and jid not in self.gen_crs and self.cfg.get('comfy_restart_stall') is not False and self.comfy_can():
                        self.gen_crs.add(jid); self.comfy_restart(f'#{jid} 清記憶體後又卡住')   # V0.3.72 第二次卡住：先重開 ComfyUI（多半是它的視窗卡住，例如跳出更新）再試，不算次數
                    else: self.gen_restarted[jid] = n_ + 1
                    J['requeue'] = True; J.pop('restart', None); raise InterruptedError
                if time.time() > dead: C.cancel(pid); raise comfy.ComfyError(f'超過 {self.cfg.get("gen_timeout_min")} 分鐘還沒好，先停掉')
                m = None
                if ws is not None:
                    try: m = ws.recv(1.0)
                    except Exception: ws.close(); ws = None
                else: time.sleep(1.0)
                if isinstance(m, dict) and (m.get('type') == '_preview' or (m.get('data') or {}).get('prompt_id') == pid):
                    if J.get('stall') and m.get('type') in ('progress', 'executing'): J.pop('stall', None)
                    act_t = J['act_t'] = time.time()
                if isinstance(m, dict) and m.get('type') == '_preview':
                    if started: J['_pv'] = (time.time(), m['data']['img'])   # 最新一張預覽（只放記憶體）
                    continue
                if isinstance(m, dict):
                    tp = m.get('type'); d = m.get('data') or {}; mine = d.get('prompt_id') in (None, pid)
                    if tp == 'status' and not started:
                        n = ((d.get('status') or {}).get('exec_info') or {}).get('queue_remaining')
                        if n: J['msg'] = pre + f'ComfyUI 排隊中（還有 {n} 個）'
                    elif tp == 'execution_start' and mine:
                        started = True; J['msg'] = pre + '開始跑…'
                        if not J.get('t_start'): J['t_start'] = time.time(); self.db.x('UPDATE gen_jobs SET t_start=? WHERE id=?', (J['t_start'], jid))
                    elif tp == 'execution_cached' and mine: cached.update(str(x) for x in (d.get('nodes') or []))
                    elif tp == 'executing' and mine and d.get('prompt_id') == pid:
                        started = True; J.setdefault('t_start', time.time()); now = time.time(); P_ = J.setdefault('_prof', {})
                        if J.get('_pn'): P_[J['_pn']] = P_.get(J['_pn'], 0) + now - J.get('_pt', now)   # 上一個節點花的時間（照節點類別加總）
                        J['_pn'] = (prompt.get(str(d.get('node'))) or {}).get('class_type') if d.get('node') is not None else None; J['_pt'] = now
                        if d.get('node') is None: fin = True
                        else:
                            J.setdefault('nseen', set()).add(str(d['node'])); J['ndone'] = len(J['nseen']) - 1; J['ncached'] = len(cached)   # 第幾個節點（算整體進度）
                            cls = (prompt.get(str(d['node'])) or {}).get('class_type', str(d['node'])); J['node'] = cls
                            if not J.get('max'): J['msg'] = pre + f'執行 {cls}…'
                    elif tp == 'progress' and mine:
                        v, mx = d.get('value') or 0, d.get('max') or 0
                        if mx: J['step'] = v; J['max'] = mx; J['pct'] = t['pct'] = round(v * 100 / mx); J['msg'] = pre + f'生成中 {v}／{mx} 步'
                    elif tp == 'execution_error' and mine:
                        raise comfy.ComfyError(comfy.mem_hint(f'{d.get("node_type", "")}：{d.get("exception_message", "執行錯誤")}'.strip('：')))
                    elif tp == 'execution_interrupted' and mine:
                        if J.get('cancel'): raise InterruptedError
                        raise comfy.ComfyError('ComfyUI 那邊中斷了這個工作')
                    elif tp == 'execution_success' and mine: fin = True
                if fin and not fin_t: fin_t = time.time()
                if fin or time.time() - last_h > (5 if ws is not None else 2):
                    last_h = time.time(); H = C.history(pid)
                    if H:
                        S = H.get('status') or {}
                        if S.get('status_str') == 'error':
                            em = next((x[1] for x in S.get('messages') or [] if isinstance(x, list) and len(x) > 1 and x[0] == 'execution_error'), {})
                            raise comfy.ComfyError(comfy.mem_hint(f'{em.get("node_type", "")}：{em.get("exception_message", "ComfyUI 執行失敗")}'.strip('：')))
                        if S.get('completed') or (H.get('outputs') and S.get('status_str') == 'success') or (H.get('outputs') and not S): break
                    if fin and not H and time.time() - fin_t > 30: raise comfy.ComfyError('ComfyUI 說做完了，但查不到結果')
            ok_end = True
            return H or {}, cached, (ws is not None or bool(cached)), t_sub
        finally:
            if ws is not None: ws.close()
            if J.get('pid') and not ok_end:               # 我們這邊失敗了：ComfyUI 那邊還在跑的要停掉，不然後面的工作要排在它後面等
                try: C.cancel(J['pid']); self.log.w(f'生圖：#{jid} 失敗，叫 ComfyUI 停掉還在跑的（prompt {J["pid"][:8]}）')
                except Exception: pass

    def igdl(self):
        """V0.3.35 📸 IG 下載（從 TikLive 搬過來，見 igdl.py）."""
        g = getattr(self, '_igdl', None)
        if g is None:
            import igdl as _ig
            g = self._igdl = _ig.IGDL(self)
        return g

    def _ffmpeg(self, name='ffmpeg'):
        for c in (self.root / f'{name}.exe', self.root / name, HERE.parent / f'{name}.exe'):
            if c.is_file(): return str(c)
        return shutil.which(name) or ''

    def video_last_frame(self, rel):
        """影片最後一格存成 inputs 裡的照片 → 檔名."""
        p = self.gen_file(rel); ff = self._ffmpeg()
        if p is None or not ff: raise comfy.ComfyError('取不到影片最後一格（沒有 ffmpeg？）')
        tmp = p.with_name(p.stem + '_last.png')
        subprocess.run([ff, '-v', 'error', '-y', '-sseof', '-0.2', '-i', str(p), '-frames:v', '1', '-update', '1', str(tmp)], capture_output=True, timeout=120, **({'creationflags': 0x08000000} if IS_WIN else {}))
        if not tmp.is_file(): raise comfy.ComfyError('取不到影片最後一格')
        try: return self.gen_save_input(tmp.read_bytes(), '長片接續')
        finally:
            try: tmp.unlink()
            except Exception: pass

    def video_concat(self, rels):
        """好幾段影片接成一支（同一個流程做的，格式一樣，直接接；接不起來就重新編碼）→ outputs 裡的相對路徑."""
        ff = self._ffmpeg(); P = [self.gen_file(r) for r in rels]
        if not ff or not all(P): raise comfy.ComfyError('接不起來（沒有 ffmpeg 或影片不見了）')
        out = P[-1].with_name(f'長片_{len(P)}段_{time.strftime("%H%M%S")}.mp4'); lst = out.with_suffix('.txt')
        lst.write_text(''.join(f"file '{str(x).replace(chr(39), chr(39) + chr(92) + chr(39) + chr(39))}'\n" for x in P), encoding='utf-8')
        kw = {'creationflags': 0x08000000} if IS_WIN else {}
        r = subprocess.run([ff, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c', 'copy', str(out)], capture_output=True, timeout=600, **kw)
        if r.returncode or not out.is_file():
            subprocess.run([ff, '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(lst), '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(out)], capture_output=True, timeout=1200, **kw)
        try: lst.unlink()
        except Exception: pass
        if not out.is_file(): raise comfy.ComfyError('接影片失敗')
        return str(out.relative_to(self.data)).replace('\\', '/')

    def gen_gif(self, rel, width=480, fps=12):
        """V0.2.92 影片 → GIF（LINE、聊天軟體可以直接動）：ffmpeg 兩段式調色盤，存在影片旁邊；做過就直接給."""
        p = self.gen_file(rel)
        if p is None or not self.is_video_name(p.name): raise comfy.ComfyError('找不到這支影片')
        ff = self._ffmpeg()
        if not ff: raise comfy.ComfyError('電腦上找不到 ffmpeg（影片功能需要它）')
        out = p.with_name(p.stem + f'_{int(width)}.gif')
        if not out.is_file():
            vf = f'fps={int(fps)},scale={int(width)}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=bayer:bayer_scale=4'
            r = subprocess.run([ff, '-v', 'error', '-y', '-i', str(p), '-vf', vf, '-loop', '0', str(out)], capture_output=True, timeout=300, **({'creationflags': 0x08000000} if IS_WIN else {}))
            if r.returncode or not out.is_file(): raise comfy.ComfyError('轉 GIF 失敗：' + (r.stderr.decode('utf-8', 'replace')[-200:] if r.stderr else ''))
        return str(out.relative_to(self.data)).replace('\\', '/')

    def _video_frames(self, path, start=0.0, dur=0.0):
        """影片有幾格、每秒幾格（ffprobe；沒有就回 (None, None)）。有設定「從第幾秒、只用幾秒」就照那段算."""
        fp = self._ffmpeg('ffprobe')
        if not fp: return None, None
        rc, out, _e = run([fp, '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets,r_frame_rate', '-of', 'json', str(path)], timeout=120)
        try:
            S = json.loads(out)['streams'][0]; n = int(S['nb_read_packets']); a, _, b = str(S['r_frame_rate']).partition('/'); fps = float(a) / float(b or 1)
        except Exception: return None, None
        n = max(0, n - int(round(float(start or 0) * fps)))
        if dur and dur > 0: n = min(n, int(float(dur) * fps))
        return n, fps

    # ---- 從影片挑格（電腦版用；手機版在瀏覽器裡直接截）
    def video_info(self, path):
        """影片：共幾格、每秒幾格、長度（秒）、寬高。沒有 ffprobe 會丟錯."""
        fp = self._ffmpeg('ffprobe')
        if not fp: raise comfy.ComfyError('找不到 ffprobe.exe（放在程式資料夾，和 ffmpeg.exe 一起）')
        rc, out, err = run([fp, '-v', 'error', '-select_streams', 'v:0', '-count_packets', '-show_entries', 'stream=nb_read_packets,r_frame_rate,width,height:format=duration', '-of', 'json', str(path)], timeout=180)
        try:
            J = json.loads(out); S = J['streams'][0]; a, _, b = str(S['r_frame_rate']).partition('/')
            return {'frames': int(S['nb_read_packets']), 'fps': float(a) / float(b or 1), 'dur': float((J.get('format') or {}).get('duration') or 0), 'w': int(S.get('width') or 0), 'h': int(S.get('height') or 0)}
        except Exception: raise comfy.ComfyError('讀不到這支影片：' + (err or out)[-200:])

    def video_frame(self, path, n, fps, side=960):
        """第 n 格（從 0 算）→ JPG bytes，拿來預覽（用時間跳，快）."""
        ff = self._ffmpeg()
        if not ff: raise comfy.ComfyError('找不到 ffmpeg.exe')
        t = max(0.0, (int(n) + 0.5) / max(1e-6, float(fps)))
        p = subprocess.run([ff, '-v', 'error', '-ss', f'{t:.4f}', '-i', str(path), '-frames:v', '1', '-vf', f"scale='min({side},iw)':-2", '-q:v', '3', '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'],
                           capture_output=True, timeout=60, creationflags=NO_WINDOW, stdin=subprocess.DEVNULL)
        if not p.stdout: raise comfy.ComfyError('這一格讀不到：' + p.stderr.decode('utf-8', 'replace')[-200:])
        return p.stdout

    def video_extract(self, path, frames):
        """把指定的第幾格（從 0 算）原尺寸存成 JPG 放進照片資料夾，回傳檔名（照 frames 的順序）。用 select 一格一格對，保證是那一格."""
        ff = self._ffmpeg()
        if not ff: raise comfy.ComfyError('找不到 ffmpeg.exe')
        F = sorted({max(0, int(x)) for x in frames})[:200]
        if not F: return []
        tmp = self.data / 'inputs' / f'_frames_{uuid.uuid4().hex[:6]}'; tmp.mkdir(parents=True, exist_ok=True)
        try:
            sel = '+'.join(f'eq(n\\,{x})' for x in F)
            rc, _o, err = run([ff, '-v', 'error', '-i', str(path), '-vf', f"select='{sel}'", '-vsync', '0', '-q:v', '2', str(tmp / '%04d.jpg')], timeout=900)
            got = sorted(tmp.glob('*.jpg'))
            if not got: raise comfy.ComfyError('取不出來：' + err[-200:])
            out = [self.gen_save_input(g.read_bytes(), f'{Path(path).name} 第 {x} 格', f'f{x:04d}') for x, g in zip(F, got)]
            self.log.w(f'生圖：從影片 {Path(path).name} 取了 {len(out)} 格：{F}'); return out
        finally: shutil.rmtree(tmp, ignore_errors=True)

    def _run_segments(self, C, url, prompt0, J, t, jid, t0, od, vid_local):
        """影片換主角（Wan Animate 2）：每段 length 格，第 2 段起用上一段最後一格接續（continue_motion），
        最後用 FFmpeg 接起來、放回原影片的聲音。ComfyUI 還沒有原生的迴圈節點，所以由這個程式一段一段送."""
        anim = next(k for k, v in prompt0.items() if v.get('class_type') == 'WanAnimate2ToVideo')
        L = int(prompt0[anim]['inputs'].get('length') or 81)
        sl = next((v['inputs'] for v in prompt0.values() if v.get('class_type') == 'Video Slice'), {})
        start = float(sl.get('start_time') or 0); dur = float(sl.get('duration') or 0)
        F, fps = self._video_frames(vid_local, start, dur) if vid_local else (None, None)
        nseg = (1 + -(-max(0, F - L) // max(1, L - 1))) if F else None
        J['nseg'] = nseg; segs = []; prev = ''; off = 0; first_cached = None; t_sub0 = 0
        self.log.w(f'生圖：#{jid} 影片分段：{F or "?"} 格、每段 {L} 格 → {nseg or "?"} 段')
        for k in range(nseg or 80):
            J['seg'] = k + 1; p = json.loads(json.dumps(prompt0)); p[anim]['inputs']['video_frame_offset'] = off
            if prev: p['9900'] = {'class_type': 'LoadImage', 'inputs': {'image': prev}}; p[anim]['inputs']['continue_motion'] = ['9900', 0]
            try: H, cached, okc, t_sub = self._run_one(C, url, p, J, t, jid, t0)
            except comfy.ComfyError as ex:
                if k and 'nothing left to read' in str(ex): break                # 不知道總格數時：讀到影片尾巴就停
                raise
            if first_cached is None: first_cached = (cached, okc, t_sub)
            vids = []; last = None
            for fn, sub, tp in comfy.output_files(H):
                if re.search(r'\.(mp4|webm|mov|mkv)$', fn, re.I): vids.append((fn, sub, tp))
                elif re.search(r'\.(png|jpg|webp)$', fn, re.I): last = (fn, sub, tp)
            if not vids: raise comfy.ComfyError(f'第 {k + 1} 段跑完了但沒有影片輸出')
            sp = od / f'{jid}_seg{k + 1:02d}.mp4'; sp.write_bytes(C.view(*vids[0])); segs.append(sp)
            eff = max(0, off - 1) if prev else off; off = eff + L                  # 下一段從哪一格開始讀動作影片（跟節點自己算的一樣）
            if F and off >= F: break
            if not last: break
            J['msg'] = f'第 {k + 1} 段好了，準備下一段…'; prev = C.upload(f'cr_last_{jid}_{k + 1:02d}.png', C.view(*last))
        J['msg'] = '把每一段接起來…'; ff = self._ffmpeg()
        if len(segs) == 1 and not ff: return [segs[0]], first_cached
        if not ff:
            self.log.w(f'生圖：#{jid} 找不到 FFmpeg，給你 {len(segs)} 段分開的影片'); return segs, first_cached
        lst = od / f'{jid}_list.txt'; lst.write_text(''.join(f"file '{x.as_posix()}'\n" for x in segs), encoding='utf-8')
        out = od / f'{jid}_final.mp4'
        cmd = [ff, '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', str(lst)]
        if vid_local:
            if start: cmd += ['-ss', f'{start:.3f}']
            cmd += ['-i', str(vid_local)]
        cmd += ['-map', '0:v:0'] + (['-map', '1:a:0?'] if vid_local else []) + ['-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k']
        if F and fps: cmd += ['-t', f'{F / fps:.3f}']
        cmd += ['-shortest', '-movflags', '+faststart', str(out)]
        rc, _o, er = run(cmd, timeout=3600, prio='below')
        try: lst.unlink()
        except Exception: pass
        if rc != 0 or not out.is_file():
            self.log.w(f'生圖：#{jid} 接影片失敗（給你分開的 {len(segs)} 段）：{er[-400:]}'); return segs, first_cached
        for x in segs:                                                          # 接好了，分段的檔搬到 _segments（留著，需要可以找）
            try: (od / '_segments').mkdir(exist_ok=True); os.replace(str(x), str(od / '_segments' / x.name))
            except Exception: pass
        return [out], first_cached

    def _gen_job(self, J):
        jid = J['id']; t = self.task('gen', f'🎨 #{jid} {J["prompt"][:40]}'); t0 = time.time(); C = None
        try:
            self.db.x("UPDATE gen_jobs SET state='run', msg='' WHERE id=?", (jid,))
            st = self.comfy_status()
            if not st['ok']: st = self.comfy_status(force=True)
            if not st['ok']: raise comfy.ComfyDown(st['err'] or '連不到 ComfyUI')       # 還沒送出：放回排隊等 ComfyUI，不算失敗
            C = comfy.Comfy(st['url']); wf = self.gen_wf_load(J['wf'])
            miss = [m for m in self.gen_models(J['wf'], C) if not m['ok']]
            if miss: raise comfy.ComfyError('還缺模型：' + '、'.join(m['file'] for m in miss) + '（生圖頁按「⬇ 下載缺的模型」）')
            try: L = [x for x in json.loads(J.get('imgs') or '[]') if x] or ([J['img']] if J['img'] else [])
            except Exception: L = [J['img']] if J['img'] else []
            img = []; vid_local = None
            for i, x in enumerate(L):
                J['msg'] = '上傳到 ComfyUI…' + (f'（{i + 1}／{len(L)}）' if len(L) > 1 else ''); img.append(C.upload('cr_' + x, (self.data / 'inputs' / x).read_bytes()))
                if self.is_video_name(x) and vid_local is None: vid_local = self.data / 'inputs' / x
            try: P = json.loads(J.get('params') or '{}')
            except Exception: P = {}
            cr = ((wf.get('extra') or {}).get('cr') or {}) if isinstance(wf, dict) else {}; ptxt = J['prompt']
            ptpl = {self.SIMPLE_NAME: self.SIMPLE_TPL, self.FL_NAME: self.FL_TPL}.get(J['wf']) or cr.get('prompt_tpl')   # V0.2.40 照官方 H3 提示詞格式（程式裡的最新版，不用重做流程）
            if ptpl and ptxt.strip() and not re.search(r'Scene\s*:|Shot\s*\d|<Picture|<Video|subject_definitions|integrated_multimodal_description', ptxt):
                dur = next((float(v) for k, v in (P or {}).items() if isinstance(v, (int, float)) and ('duration' in str(k).lower() or any('影片長度' in str(it.get('label')) and it['id'] == k for g in self.gen_params(J['wf']) for it in g['items']))), 4.0)
                mus = '#music' in ptxt; ptxt = ptxt.replace('#music', '').strip()                 # V0.2.53 🎵 配樂開關
                ptxt = ptpl.replace('{action}', ptxt.strip().rstrip('。.')).replace('{end}', f'{max(1.0, dur - 0.05):.2f}')
                if mus: ptxt = ptxt.replace('non_diegetic_music: N/A', 'non_diegetic_music: Soft, warm and gentle background music that fits the mood, at a low volume.')       # 只打動作（例如「揮手」）→ 包成完整的 H3 提示詞
            prompt, info = comfy.prepare(wf, img, ptxt, J['neg'], J['seed'], self._obj_info(C), params=P); self._info_save()
            xs = [x for x in (cr.get('xslots') or []) if isinstance(x, dict)]
            if xs:                                                           # V0.2.35 額外的照片格子：接到指定節點的指定入口（例如 H3 的 last_frame）
                base = len(comfy.analyze(prompt)['image'])
                for j, x in enumerate(xs):
                    if base + j >= len(img): raise comfy.ComfyError(f'還沒選：{x.get("title") or "第 " + str(base + j + 1) + " 張圖"}')
                    tgt = next((k for k, v in prompt.items() if v.get('class_type') == x.get('cls')), None)
                    if tgt is None: raise comfy.ComfyError(f'流程裡找不到 {x.get("cls")}（範本可能改版了，到 設定 → 流程 重抓）')
                    k = f'crx{j}'; prompt[k] = {'class_type': 'LoadImage', 'inputs': {'image': img[base + j]}, '_meta': {'title': str(x.get('title') or '')}}
                    lk = prompt[tgt]['inputs'].get(x.get('like') or ''); src = prompt.get(str(lk[0])) if isinstance(lk, list) else None
                    if src and isinstance(src.get('inputs', {}).get('image'), list):   # 照第一張的前處理（例如縮到同樣像素數）也做一份，兩張大小一致
                        prompt[k + 's'] = {'class_type': src['class_type'], 'inputs': dict(src['inputs'], image=[k, 0]), '_meta': {'title': '尾幀縮放'}}; k = k + 's'
                    prompt[tgt]['inputs'][x['input']] = [k, 0]
            try: self._people_inject(C, prompt, jid)
            except Exception as ex: self.log.w(f'生圖：#{jid} 人物庫帶入失敗（照原本的跑）：{ex}')
            if J.get('ref') and (self.data / 'inputs' / J['ref']).is_file():
                try: self._ref_inject(C, prompt, jid, J['ref'])
                except Exception as ex: self.log.w(f'生圖：#{jid} 參考圖帶入失敗（照原本的跑）：{ex}')
            try:                                                             # V0.3.23 Qwen 2.1 多張圖：官方寫法用 <image1> <image2> 指圖，把「圖1／圖一／圖二中的人」換成這種
                for k, v in prompt.items():
                    if v.get('class_type') == 'TextEncodeQwenImage21' and any(x.startswith('images.image_') and x != 'images.image_1' for x in v['inputs']) and isinstance(v['inputs'].get('prompt'), str):
                        v['inputs']['prompt'] = self.qwen21_tags(v['inputs']['prompt'])
            except Exception as ex: self.log.w(f'生圖：#{jid} 圖片標記轉換失敗（照原本的跑）：{ex}')
            if J.get('mask') and img and (self.data / 'inputs' / J['mask']).is_file():   # 🖌 只改塗到的地方：模型照常改整張，最後只把塗到的範圍貼回原圖（其他地方一個像素都不動）
                mk = C.upload('cr_' + J['mask'], (self.data / 'inputs' / J['mask']).read_bytes())
                if comfy.apply_mask(prompt, img[0], mk, cue=J.get('cue') or ''): self.log.w(f'生圖：#{jid} 只改塗到的地方（其他地方保持原圖）')
            marked = any(v.get('class_type') == 'ResolutionSelector' and (v.get('inputs') or {}).get('aspect_ratio') == comfy.MATCH_ASPECT for v in prompt.values())
            if marked or cr.get('match_aspect'):
                pic = next((x for x in L if not self.is_video_name(x)), None)
                wh = comfy.match_aspect(prompt, *comfy.img_size_shown((self.data / 'inputs' / pic).read_bytes()[:300000]), only_marked=not cr.get('match_aspect')) if pic else None
                if wh: self.log.w(f'生圖：#{jid} 影片比例跟照片一樣 → {wh[0]}×{wh[1]}')
                for v in prompt.values():                                    # 沒照片可以對：改回一般比例，ComfyUI 才認得
                    if v.get('class_type') == 'ResolutionSelector' and (v.get('inputs') or {}).get('aspect_ratio') == comfy.MATCH_ASPECT: v['inputs']['aspect_ratio'] = '16:9 (Widescreen)'
            if self.cfg.get('gen_free_switch') is not False and getattr(self, '_last_wf', None) not in (None, J['wf']):
                try: C.free(); self.log.w(f'生圖：換流程（{self._last_wf} → {J["wf"]}），先叫 ComfyUI 把上一個流程的模型清出記憶體')   # 大模型（H3 好幾十 GB）不會兩套一起塞在記憶體
                except Exception as ex: self.log.w(f'生圖：清記憶體失敗（不影響）：{ex}')
            self._last_wf = J['wf']
            loaders = [k for k, v in prompt.items() if 'loader' in str(v.get('class_type', '')).lower()]
            self.db.x('UPDATE gen_jobs SET seed=? WHERE id=?', (int(info['seed']), jid))
            self.log.w(f'生圖：#{jid} 送出（種子 {info["seed"]}）' + ('　' + '；'.join(info['notes']) if info['notes'] else ''))
            od = self.data / 'outputs' / time.strftime('%Y%m%d'); od.mkdir(parents=True, exist_ok=True); outs = []; ow = oh = 0
            if any(v.get('class_type') == 'WanAnimate2ToVideo' for v in prompt.values()):
                files, (cached, okc, t_sub) = self._run_segments(C, st['url'], prompt, J, t, jid, t0, od, vid_local)
                outs = [f'outputs/{od.name}/{p.name}' for p in files]
            else:
                H, cached, okc, t_sub = self._run_one(C, st['url'], prompt, J, t, jid, t0)
                J['msg'] = '下載結果…'
                for i, (fn, sub, tp) in enumerate(comfy.output_files(H)[:40]):
                    data = C.view(fn, sub, tp); safe = re.sub(r'[^\w.\-]', '_', fn); p = od / f'{jid}_{i}_{safe}'; p.write_bytes(data)
                    if not ow: ow, oh = comfy.img_size(data)
                    outs.append(f'outputs/{od.name}/{p.name}')
            if not outs: raise comfy.ComfyError('跑完了但沒有輸出（流程裡有 SaveImage／SaveVideo 嗎？）')
            t_end = time.time(); ts = J.get('t_start') or t_sub or t0; run_s = max(0.0, t_end - ts)
            cold = (1 if any(k not in cached for k in loaders) else 0) if okc and J.get('t_start') else -1
            dur = time.time() - t0; kind = '段影片' if J.get('nseg') or J.get('seg') else '張'
            self.db.x("UPDATE gen_jobs SET state='done', msg=?, outs=?, dur=?, t1=?, run_s=?, t_start=?, cold=?, out_w=?, out_h=? WHERE id=?",
                      (f'{len(outs)} {"支影片" if any(self.is_video_name(o) for o in outs) else "張"}', json.dumps(outs), dur, time.time(), run_s, ts, cold, ow, oh, jid))
            try: self.db.x('UPDATE gen_jobs SET prof=? WHERE id=?', (json.dumps({k: round(v, 2) for k, v in (J.get('_prof') or {}).items() if k}), jid))
            except Exception: pass
            self.gen_hot = J.get('mkey') or self.gen_hot; self.est_cache.clear()
            if J.get('chain'):                                               # V0.2.54 🪄 一鍵首尾幀：改好的圖當尾幀，原圖當首幀，接著排影片
                try:
                    c = json.loads(J['chain']); img0 = J.get('img') or ''
                    if c.get('kind') == 'fl' and img0 and outs and not self.is_video_name(outs[0]):
                        last = self.gen_reuse(jid, 0)
                        nid = self.gen_add(c['wf'], c.get('prompt') or J['prompt'], img0, '', 1, J.get('src') or '電腦', params=c.get('params') or None, imgs=[img0, last])
                        self.gen_set_batch([jid] + nid); self.log.w(f'生圖：#{jid} 尾幀做好了，接著排首尾幀影片 #{nid[0]}')
                    if c.get('kind') == 'seq' and outs and self.is_video_name(outs[0]):   # V0.3.13 🎞 長片：這段的最後一格接下一段，全部做完接成一支
                        segs = list(c.get('segs') or []) + [outs[0]]; rest = [x for x in (c.get('prompts') or []) if str(x).strip()]
                        if rest:
                            last = self.video_last_frame(outs[0])
                            nid = self.gen_add(c['wf'], rest[0], last, '', 1, J.get('src') or '電腦', params=c.get('params') or None,
                                               chain={'kind': 'seq', 'wf': c['wf'], 'prompts': rest[1:], 'params': c.get('params'), 'segs': segs})
                            b0 = int(J.get('batch') or 0) or jid; self.db.x(f'UPDATE gen_jobs SET batch=? WHERE id IN ({",".join("?" * (len(nid) + 1))})', [b0, jid] + nid)   # 整串同一組
                            self.log.w(f'生圖：#{jid} 長片第 {len(segs)} 段好了，接著排下一段 #{nid[0]}')
                        elif len(segs) > 1:
                            fin = self.video_concat(segs); outs.append(fin); self.db.x('UPDATE gen_jobs SET outs=? WHERE id=?', (json.dumps(outs), jid))
                            self.log.w(f'生圖：#{jid} 長片 {len(segs)} 段接好了：{fin}')
                except Exception as ex: self.log.w(f'生圖：#{jid} 接著排下一個失敗：{ex}')
            self.gen_done[0] += 1; self.done(t, 'done', f'{len(outs)} 個檔，運算 {run_s:.1f} 秒'); self.log.w(f'生圖：#{jid} 完成 {len(outs)} 個檔，運算 {run_s:.1f} 秒（全部 {dur:.1f} 秒，{"冷啟動" if cold == 1 else "熱" if cold == 0 else "?"}）　⏱ {self.prof_brief(J.get("_prof"))}')
        except InterruptedError:
            nrs = (getattr(self, 'gen_restarted', {}) or {}).get(jid, 0)
            if J.get('requeue') and not self.stop_all and nrs >= 2 and J.get('auto_rs'):   # V0.3.48 卡住兩次：改用比較省記憶體的流程重做；沒有可以換的就跳過，後面的繼續
                alt = {'GROK 改圖（INT8 快）': 'Qwen 2.1 Turbo 改圖', '兩張圖合併（INT8 快）': self.QM_NAME}.get(J.get('wf') or '')
                if alt and self.cfg.get('gen_stall_switch') is not False and (self.gen_wf_path(alt) or Path('/nonexist')).exists():
                    self.db.x("UPDATE gen_jobs SET state='wait', wf=?, params='{}', msg=? WHERE id=?", (alt, f'卡住兩次，改用「{alt}」（比較省記憶體）重做', jid))
                    with self.lock: self.gen_q.appendleft(jid)
                    self.log.w(f'生圖：#{jid} 卡住兩次，改用「{alt}」重做'); self.done(t, 'stop', f'卡住兩次，改用 {alt}'); J['requeue'] = False
                else:
                    msg = '卡住兩次（多半記憶體不夠），先跳過，後面的繼續'
                    self.db.x("UPDATE gen_jobs SET state='fail', msg=?, t1=? WHERE id=?", (msg, time.time(), jid)); self.log.w(f'生圖：#{jid} {msg}'); self.done(t, 'fail', msg)
                    J['requeue'] = False
            elif J.get('requeue') and not self.stop_all:
                self.db.x("UPDATE gen_jobs SET state='wait', msg='' WHERE id=?", (jid,))
                with self.lock: self.gen_q.appendleft(jid)
                self.done(t, 'stop', '停止（放回排隊）')
                if (getattr(self, 'gen_restarted', {}) or {}).get(jid): self.db.x("UPDATE gen_jobs SET msg='卡住了，清掉記憶體重新排' WHERE id=?", (jid,))
            elif self.stop_all: self.done(t, 'stop', '關程式，下次接著做')
            else: self.db.x("UPDATE gen_jobs SET state='stop', msg='已取消', t1=? WHERE id=?", (time.time(), jid)); self.done(t, 'stop', '已取消')
        except comfy.ComfyDown as ex:                                       # ComfyUI 關掉了：放回排隊最前面，等它回來
            self.comfy_st.update(t=0, ok_t=0, bad=max(1, self.comfy_st.get('bad', 0))); self.gen_hot = None
            n = self.gen_crash.get(jid, 0) + (1 if J.get('submitted') else 0); self.gen_crash[jid] = n
            if n >= 2:                                                         # 同一個工作跑到一半 ComfyUI 不見 2 次：多半是這個工作把它弄當了（顯存／記憶體不夠），跳過它
                msg = 'ComfyUI 跑這個工作時關掉／當掉了 2 次（多半是顯存或記憶體不夠：把寬高、每段幾格調小再試），先跳過，後面的繼續'
                self.log.w(f'生圖：#{jid} 失敗：{msg}')
                try: self.db.x("UPDATE gen_jobs SET state='fail', msg=?, dur=?, t1=? WHERE id=?", (msg, time.time() - t0, time.time(), jid))
                except Exception: pass
                self.done(t, 'fail', msg[:200])
            else:
                self.log.w(f'生圖：#{jid} ComfyUI 不見了，放回排隊（{ex}）')
                try: self.db.x("UPDATE gen_jobs SET state='wait', msg='', t_start=0 WHERE id=?", (jid,))
                except Exception: pass
                if not self.stop_all:
                    with self.lock: self.gen_q.appendleft(jid)
                self.done(t, 'stop', 'ComfyUI 斷線，放回排隊')
        except Exception as ex:
            msg = str(ex) if isinstance(ex, comfy.ComfyError) else f'{type(ex).__name__}: {ex}'
            R = self.__dict__.setdefault('gen_retry', {})
            if '👉' in msg and C is not None and R.get(jid, 0) < 1 and self.cfg.get('gen_auto_retry') is not False and not self.stop_all:   # 記憶體不夠：清乾淨再試一次（整晚排隊不要因為偶爾一次就掉一張）
                R[jid] = R.get(jid, 0) + 1
                try: C.free(); self._last_wf = None
                except Exception: pass
                self.log.w(f'生圖：#{jid} 記憶體不夠，清掉 ComfyUI 記憶體後自動再試一次'); time.sleep(3)
                self.db.x("UPDATE gen_jobs SET state='wait', msg='記憶體不夠，清乾淨再試一次', t_start=0 WHERE id=?", (jid,))
                with self.lock: self.gen_q.appendleft(jid)
                self.done(t, 'stop', '記憶體不夠，再試一次'); return
            if not isinstance(ex, comfy.ComfyError): self.log.err(f'生圖 #{jid}')
            else: self.log.w(f'生圖：#{jid} 失敗：{msg}')
            try: self.db.x("UPDATE gen_jobs SET state='fail', msg=?, dur=?, t1=? WHERE id=?", (msg[:1000], time.time() - t0, time.time(), jid))
            except Exception: pass
            self.done(t, 'fail', msg[:200])
            if '👉' in msg and C is not None:                                 # 記憶體不夠失敗：清一次，後面排隊的才有機會
                try: C.free(); self._last_wf = None
                except Exception: pass
        finally:
            self.gen_active.pop(jid, None)
            if self.gen_q: self.log.w(f'生圖：#{jid} 結束，接著做排隊的 {len(self.gen_q)} 個')

    # ================================================================ 資料庫每日備份
    def _backup_loop(self):
        for _ in range(60):
            if not self.alive(): return
            time.sleep(1)
        while self.alive():
            try:
                if self.cfg.get('db_backup') is not False:
                    d = self.data / 'db_backup'; d.mkdir(exist_ok=True); tag = time.strftime('%Y%m%d')
                    if not list(d.glob(f'app_{tag}_*.sqlite3')):
                        self.db.backup_to(d / f'app_{tag}_{time.strftime("%H%M%S")}.sqlite3'); shutil.copy2(str(self.data / 'settings.json'), str(d / f'settings_{tag}.json'))
                        keep = max(1, int(self.cfg.get('db_backup_keep') or 7))
                        for o in sorted(d.glob('app_*.sqlite3'))[:-keep]: o.unlink()
                        self.log.w(f'資料庫備份好了（{d}）')
            except Exception: self.log.err('資料庫備份')
            for _ in range(1800):
                if not self.alive(): return
                time.sleep(1)

    # ================================================================ 畫面／手機共用的狀態
    def info(self):
        if time.time() - self.info_c['t'] < 1.0: return self.info_c['v']
        v = {'demo_wait': len(self.demo_q), 'demo_run': len(self.demo_active), 'demo_done': self.demo_done[0],
             'gen_wait': len(self.gen_q), 'gen_run': len(self.gen_active), 'gen_done': self.gen_done[0],
             'items': int((self.db.one('SELECT COUNT(*) FROM items') or [0])[0] or 0), 'cpu': round(self.perf.cpu, 1), 'ram': round(self.perf.ram, 1)}
        self.info_c = {'t': time.time(), 'v': v}; return v
