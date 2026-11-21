"""主程式（PySide6）＝畫面殼。新程式的功能頁加在 PAGES／NavList.GROUPS，畫面只做畫面，重的事交給 core.Engine（背景執行緒）。

已經做好、不用再調的（給接手的 AI：不要重寫這些，只在需要時小改）：
  - 左邊分組選單（點分組標題收合）、左下電腦狀態（點了開📊效能浮窗）、上方 📊效能／🖥後台／🌙縮到背景／🏠封面、下方深色／淺色＋介面大小
  - 🖥 後台狀態：每一項背景工作 暫停／繼續／立刻停／先後順序／CPU 太忙自動讓路／慢慢加速；最近的工作
  - ⚙ 設定：一般、📱 手機網頁（PIN、Tailscale HTTPS 自己的埠）、資料夾；⟳ 版本與更新（熱更新，程式不用關）
  - 📜 LOG、🧪 實驗工作區（LAB_LIST）、📖 使用說明、托盤、只能開一個、閃退自動重開（看門狗）、畫面卡住記錄、Windows 關機不擋
"""
import os, sys, re, json, time, math, shutil, zipfile, threading, traceback, subprocess, faulthandler, importlib, importlib.util
from pathlib import Path
from collections import deque

from PySide6.QtCore import Qt, QTimer, QObject, Signal, Slot, QRect, QRectF, QPoint, QSize, QUrl, QEvent, qInstallMessageHandler
from PySide6.QtGui import QPainter, QColor, QPixmap, QIcon, QFont, QPen, QKeySequence, QShortcut, QDesktopServices, QPainterPath, QFontMetrics, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
                               QSplitter, QStackedWidget, QScrollArea, QComboBox, QSpinBox, QCheckBox, QLineEdit, QFileDialog, QMessageBox, QTableWidget,
                               QTableWidgetItem, QHeaderView, QAbstractItemView, QProgressBar, QDialog, QMenu, QSystemTrayIcon, QFormLayout, QGroupBox,
                               QPlainTextEdit, QTextBrowser, QFrame, QSizePolicy, QStyledItemDelegate, QStyle, QSlider, QInputDialog)

APP_VERSION = '0.3.58'
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import core  # noqa: E402
import web  # noqa: E402
import cloudupd  # noqa: E402
import hslink  # noqa: E402
from core import fmt_t, fmt_b, BRAND  # noqa: E402

APP_TITLE = BRAND['title']
ROOT = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else HERE.parent
SELFTEST = bool(os.environ.get('APP_SELFTEST'))
SINGLE = f'{BRAND["id"]}_single_v1'
PKG_GLOB = f'{BRAND["prefix"]}_V*.zip'

# 🧪 實驗工作區：(代號, 名稱, 說明)。新推薦的功能先放這裡（預設關），使用者試過說好再變正式功能
LAB_LIST = []

# ============================================================ 顏色、字型（深色／淺色同一套 token）
THEMES = {
    'dark': {'bg': '#0e1116', 'side': '#090c10', 'nav': '#0a0e13', 'panel': '#11161c', 'card': '#151a21', 'input': '#151a21', 'button': '#171d26', 'button_hover': '#222b37',
             'border': '#252c35', 'border_strong': '#2a3340', 'text': '#e8ecf2', 'text_strong': '#ffffff', 'subtext': '#8994a4', 'muted': '#7f8a99', 'nav_text': '#b9c2cf',
             'hover': '#161e28', 'header_bg': '#191f27', 'header_text': '#aeb7c4', 'grid': '#222933', 'alt_row': '#151a21', 'selection': '#263342', 'selection_text': '#ffffff',
             'scroll': '#3a4654', 'track': '#2a3038', 'accent': BRAND.get('accent', '#e51e63'), 'viewer_line': '#43d9ff', 'sub_accent': '#f0ad4e'},
    'light': {'bg': '#f3f5f8', 'side': '#e8ecf1', 'nav': '#e8ecf1', 'panel': '#ffffff', 'card': '#ffffff', 'input': '#ffffff', 'button': '#ffffff', 'button_hover': '#e7ecf2',
              'border': '#d5dce4', 'border_strong': '#c2cbd6', 'text': '#1b2430', 'text_strong': '#0b121a', 'subtext': '#5d6978', 'muted': '#6b7685', 'nav_text': '#334050',
              'hover': '#dde4ec', 'header_bg': '#eef1f5', 'header_text': '#3d4856', 'grid': '#e4e9ef', 'alt_row': '#f7f9fb', 'selection': '#d3e6fb', 'selection_text': '#0b121a',
              'scroll': '#b6c0cb', 'track': '#dfe5ec', 'accent': BRAND.get('accent', '#e51e63'), 'viewer_line': '#0a84c6', 'sub_accent': '#c77700'},
}
THEME = dict(THEMES['dark'])
THEME_MODE = {'mode': 'dark', 'zoom': 100}


def set_theme_mode(mode):
    mode = 'light' if str(mode) == 'light' else 'dark'
    THEME.clear(); THEME.update(THEMES[mode]); THEME_MODE['mode'] = mode
    return mode


def TC(key): return QColor(THEME.get(key, '#ff00ff'))


def theme_qss(mode=None, zoom=None):
    if mode is not None: set_theme_mode(mode)
    if zoom is not None: THEME_MODE['zoom'] = max(70, min(160, int(zoom)))
    t = THEME; fs = round(13 * THEME_MODE['zoom'] / 100); ac = t['accent']
    return f"""
QMainWindow,QWidget,QDialog{{background:{t['bg']};color:{t['text']};font-family:"Yu Gothic UI","Microsoft JhengHei","PingFang TC";font-size:{fs}px}}
QFrame#side{{background:{t['side']};border-right:1px solid {t['border']}}}
QLabel#title{{font-weight:800;font-size:{round(fs * 1.3)}px;color:{t['text_strong']}}} QLabel#sub,QLabel#muted{{color:{t['subtext']}}}
QLabel#ptitle{{font-weight:850;font-size:{round(fs * 1.35)}px;color:{t['text_strong']};background:transparent}}
QPushButton{{background:{t['button']};border:1px solid {t['border_strong']};border-radius:8px;padding:5px 8px;color:{t['text']}}}
QPushButton:hover{{background:{t['button_hover']}}} QPushButton:disabled{{color:{t['muted']}}}
QPushButton:checked{{background:{t['selection']};border-color:{t['viewer_line']};color:{t['text_strong']}}}
QPushButton#start{{background:{ac};border:0;font-weight:900;min-height:32px;color:#ffffff}}
QPushButton#net_btn{{text-align:left;padding:5px 8px;border-radius:9px;background:{t['card']};border:1px solid {t['border']}}} QPushButton#net_btn:hover{{background:{t['button_hover']}}}
QPushButton#pill{{border-radius:11px;padding:2px 10px;font-size:{round(fs * 0.9)}px}}
QListWidget#workspace_nav{{background:{t['nav']};border:0;border-radius:9px;padding:2px 1px;outline:0}} QListWidget#workspace_nav::item{{border:0;background:transparent}}
QLineEdit,QSpinBox,QDoubleSpinBox,QComboBox{{background:{t['input']};border:1px solid {t['border_strong']};border-radius:7px;padding:4px 7px;color:{t['text_strong']}}}
QPlainTextEdit,QTextBrowser,QTextEdit{{background:{t['panel']};border:1px solid {t['border']};border-radius:8px;color:{t['text']}}}
QComboBox QAbstractItemView{{background:{t['panel']};color:{t['text']};selection-background-color:{t['selection']};selection-color:{t['selection_text']}}}
QMenu{{background:{t['panel']};color:{t['text']};border:1px solid {t['border']}}} QMenu::item{{padding:5px 18px}} QMenu::item:selected{{background:{t['selection']};color:{t['selection_text']}}}
QListWidget,QTreeWidget,QTableWidget,QTableView,QListView{{background:{t['panel']};border:1px solid {t['border']};border-radius:8px;alternate-background-color:{t['alt_row']};outline:0}}
QListWidget::item:selected,QTreeWidget::item:selected,QTableWidget::item:selected{{background:{t['selection']};color:{t['selection_text']}}}
QTableWidget,QTableView{{gridline-color:{t['grid']}}}
QHeaderView::section{{background:{t['header_bg']};color:{t['header_text']};padding:5px;border:0;font-weight:700}} QTableCornerButton::section{{background:{t['header_bg']};border:0}}
QFrame#card{{background:{t['card']};border:1px solid {t['border']};border-radius:11px}} QFrame#topbar{{background:{t['bg']};border-bottom:1px solid {t['border']}}}
QGroupBox{{background:{t['panel']};border:1px solid {t['border']};border-radius:11px;margin-top:16px;padding:10px 8px 8px 8px}}
QGroupBox::title{{subcontrol-origin:margin;left:12px;padding:0 4px;color:{ac};font-weight:800}}
QGroupBox QWidget{{background:transparent}} QGroupBox QLineEdit,QGroupBox QSpinBox,QGroupBox QComboBox{{background:{t['input']}}} QGroupBox QPushButton{{background:{t['button']}}}
QCheckBox,QRadioButton{{color:{t['text']};background:transparent}} QToolTip{{background:{t['panel']};color:{t['text']};border:1px solid {t['border']}}}
QStatusBar{{color:{t['subtext']};background:{t['bg']};border-top:1px solid {t['border']}}} QStatusBar QLabel{{background:transparent}}
QProgressBar{{border:0;border-radius:4px;text-align:center;background:{t['track']};color:{t['text_strong']};max-height:14px}} QProgressBar::chunk{{background:{t['viewer_line']};border-radius:4px}}
QTabWidget::pane{{border:1px solid {t['border']};border-radius:9px;top:-1px}} QTabBar::tab{{background:{t['panel']};border:1px solid {t['border']};padding:6px 14px;border-radius:8px;margin:2px;color:{t['subtext']}}}
QTabBar::tab:selected{{background:{t['selection']};color:{t['text_strong']};border-color:{t['viewer_line']}}}
QScrollArea{{border:0;background:transparent}}
QScrollBar:vertical{{background:transparent;width:8px}} QScrollBar::handle:vertical{{background:{t['scroll']};border-radius:4px;min-height:28px}}
QScrollBar:horizontal{{background:transparent;height:8px}} QScrollBar::handle:horizontal{{background:{t['scroll']};border-radius:4px;min-width:28px}}
QScrollBar::add-line,QScrollBar::sub-line{{width:0;height:0}} QScrollBar::add-page,QScrollBar::sub-page{{background:transparent}}
QSplitter::handle{{background:{t['border']}}}
"""


STYLE = theme_qss('dark', 100)


# ============================================================ 執行緒工具：bg(背景做, 回到畫面執行緒的 cb)、ui(交給畫面執行緒)
H3SK = 'Scene: (整體：地點、時間、人物外觀、氣氛。英文寫效果最好)\nShot 1 (0.00s): (畫面和動作), (鏡頭：close-up / medium shot / wide shot，slow push-in / handheld …).\nShot 2 (2.50s): The camera cuts to (新的畫面). (人物) says in Chinese, softly: "我們走吧。"\noverall_soundscape: (環境聲、音效，例如 rain on the window, footsteps)\nnon_diegetic_music: (配樂，例如 soft piano melody；不要配樂寫 N/A)'


class Bus(QObject):
    call = Signal(object)

    def __init__(self):
        super().__init__(); self.call.connect(self._run, Qt.QueuedConnection)

    @Slot(object)
    def _run(self, fn):
        try: fn()
        except Exception:
            try: ENG.log.err('畫面更新')
            except Exception: pass


BUS = None
ENG = None


def ui(fn):
    """在畫面執行緒執行（從背景執行緒呼叫）."""
    BUS.call.emit(fn)


def bg(fn, cb=None, err=None):
    """在背景做 fn()，做完在畫面執行緒呼叫 cb(結果)。畫面上任何會讀硬碟／查資料庫／跑程式的動作都用這個（畫面才不會卡）."""
    def work():
        try: r = fn()
        except Exception as ex:
            r = ex
            try: ENG.log.err(f'背景工作 {getattr(fn, "__qualname__", fn)}')
            except Exception: pass
        if cb is not None: ui(lambda r=r: (cb(r) if not isinstance(r, Exception) else (err(r) if err else None)))
    threading.Thread(target=work, daemon=True).start()


def lab_cfg(): return dict(ENG.cfg.get('lab') or {})


def esc_html(t): return str(t).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _ti(text, tip='', align=None, color=None):
    it = QTableWidgetItem(str(text)); it.setToolTip(str(tip or text))
    if align is not None: it.setTextAlignment(align)
    if color: it.setForeground(QColor(color))
    return it


def scroll_wrap(w):
    """每一頁包一層捲動：視窗太窄時出現捲軸，不會把視窗撐寬."""
    sa = QScrollArea(); sa.setWidgetResizable(True); sa.setFrameShape(QFrame.NoFrame); sa.setWidget(w); return sa


def note(text):
    l = QLabel(text); l.setObjectName('muted'); l.setWordWrap(True); return l


# ============================================================ 🏠 首頁（新程式的主畫面放這裡：目前只是示範）
class HomePage(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win
        v = QVBoxLayout(self); v.setContentsMargins(12, 12, 12, 12)
        t = QLabel(f'🏠 {APP_TITLE}'); t.setObjectName('title'); v.addWidget(t)
        v.addWidget(note('這是空架子的首頁。新程式的主要畫面放在這裡（HomePage），或在 NavList.GROUPS 加新的頁面。\n'
                         '下面的按鈕排幾個「示範背景工作」，用來看後台總控制、手機網頁、熱更新是不是都正常。'))
        r = QHBoxLayout(); v.addLayout(r); b = QPushButton('＋ 排 5 個示範背景工作（每個 8 秒）'); b.setObjectName('start'); r.addWidget(b); r.addStretch(1)
        b.clicked.connect(lambda: bg(lambda: ENG.demo_add(5, 8), lambda n: self.win.msg(f'排好了，排隊中 {n} 個（看「🖥 後台狀態」）')))
        self.info = QLabel(''); self.info.setTextFormat(Qt.RichText); self.info.setWordWrap(True); v.addWidget(self.info)
        self.lab_l = QLabel('🧪 示範實驗開關是打開的（實驗工作區可以關）'); self.lab_l.setStyleSheet('color:#f0ad4e'); v.addWidget(self.lab_l)
        v.addStretch(1)
        self.tm = QTimer(self); self.tm.timeout.connect(self.refresh); self.tm.start(1000)

    def refresh(self):
        if not self.isVisible(): return
        self.lab_l.setVisible(bool(lab_cfg().get('demo_lab')))
        bg(ENG.info, lambda I: self.info.setText(f"CPU <b>{I['cpu']}%</b>　RAM <b>{I['ram']}%</b>　示範工作：進行中 <b>{I['demo_run']}</b>・排隊 {I['demo_wait']}・完成 {I['demo_done']}"))


# ============================================================ 🎨 生圖（主畫面）：選照片 → 打提示詞 → 開始 → 本機 ComfyUI 跑 → 結果在下面（手機網頁一樣的功能）
GEN_ST = {'wait': ('⏳ 排隊中', '#f0ad4e'), 'run': ('▶ 生成中', '#4dc9ff'), 'done': ('✔ 完成', '#45d483'), 'fail': ('✖ 失敗', '#ff4d6d'), 'stop': ('⏹ 已取消', '#7f8a99')}


def _img_small(path, side):
    """背景執行緒：讀圖（照 EXIF 轉正）縮成 side 大小的 QImage."""
    from PySide6.QtGui import QImageReader
    r = QImageReader(str(path)); r.setAutoTransform(True); sz = r.size()
    if sz.isValid() and max(sz.width(), sz.height()) > side:
        k = side / max(sz.width(), sz.height()); r.setScaledSize(QSize(max(1, int(sz.width() * k)), max(1, int(sz.height() * k))))
    return r.read()


def _photo_bytes(path, mp):
    """背景執行緒：電腦選的照片 → 縮到 mp 百萬像素的 JPG bytes（0＝原檔）."""
    from PySide6.QtGui import QImageReader
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    raw = Path(path).read_bytes()
    r = QImageReader(str(path)); r.setAutoTransform(True); sz = r.size()
    k = math.sqrt(mp * 1e6 / (sz.width() * sz.height())) if mp and sz.isValid() and sz.width() * sz.height() > 0 else 1
    if k >= 1 and raw[:3] in (b'\xff\xd8\xff', b'\x89PN', b'RIF'): return raw
    if k < 1: r.setScaledSize(QSize(max(8, int(sz.width() * k)), max(8, int(sz.height() * k))))
    img = r.read()
    if img.isNull(): raise RuntimeError('讀不到這張照片：' + r.errorString())
    ba = QByteArray(); buf = QBuffer(ba); buf.open(QIODevice.WriteOnly); img.save(buf, 'JPG', 92); buf.close()
    return bytes(ba)


class GenPage(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win; self.img = ''; self.imgs = []; self.wfs = []; self.sig = None; self.icons = {}; self.loading = set(); self.jobs = []
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10)
        g0 = QGroupBox('🔌 ComfyUI'); r0 = QHBoxLayout(g0); v.addWidget(g0)
        self.st = QLabel('連線中…'); self.st.setTextFormat(Qt.RichText); self.st.setWordWrap(True); r0.addWidget(self.st, 1)
        self.url = QLineEdit(ENG.cfg.get('comfy_url') or ''); self.url.setPlaceholderText('自動（8000／8188）'); self.url.setFixedWidth(210); r0.addWidget(self.url)
        b_re = QPushButton('🔍 重新連線'); b_out = QPushButton('📂 結果'); b_wfd = QPushButton('📂 流程'); b_imp = QPushButton('➕ 匯入流程'); b_tpl = QPushButton('📥 官方範本'); b_ppl = QPushButton('👤 人物庫')
        b_ppl.setToolTip('某人的照片存成編號 a01…，提示詞寫 a01 就自動帶他的照片'); b_ppl.clicked.connect(lambda: PeopleDlg(self).exec())
        b_tpl.setToolTip('拿 ComfyUI 內建的官方範本做流程（例如 MiniMax H3 文字生影片）'); b_tpl.clicked.connect(self.import_tpl)
        b_cmp = QPushButton('🧪 比較模型'); b_cmp.setToolTip('同一批照片讓好幾種模型各改一次，排一整晚比速度和畫質（在瀏覽器開大螢幕版）'); b_cmp.clicked.connect(self.open_cmp)
        for b_ in (b_re, b_out, b_wfd, b_imp, b_tpl, b_ppl, b_cmp): r0.addWidget(b_)
        self.url.editingFinished.connect(lambda: (ENG.cfg.set('comfy_url', self.url.text().strip()), self.status(True)))
        b_re.clicked.connect(lambda: self.status(True)); b_imp.clicked.connect(self.import_wf)
        b_out.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(ENG.data / 'outputs'))))
        b_wfd.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(ENG.data / 'workflows'))))
        g1 = QGroupBox('🎨 新的工作'); h1 = QHBoxLayout(g1); v.addWidget(g1)
        lc = QVBoxLayout(); h1.addLayout(lc)
        self.pv = QLabel('（還沒選照片）\n可以一次選很多張'); self.pv.setFixedSize(240, 240); self.pv.setAlignment(Qt.AlignCenter); self.pv.setObjectName('muted')
        self.pv.setStyleSheet('border:2px dashed #3a4654;border-radius:10px'); lc.addWidget(self.pv)
        self.sel = QListWidget(); self.sel.setViewMode(QListWidget.IconMode); self.sel.setFlow(QListWidget.LeftToRight); self.sel.setWrapping(False)
        self.sel.setIconSize(QSize(56, 56)); self.sel.setFixedSize(240, 84); self.sel.setSelectionMode(QListWidget.ExtendedSelection); self.sel.setVisible(False)
        self.sel.setToolTip('已選的照片：選起來按「✕ 拿掉」或 Delete；再選照片會接在後面'); lc.addWidget(self.sel)
        rs = QHBoxLayout(); lc.addLayout(rs); self.b_rm = QPushButton('✕ 拿掉選的'); self.b_clr = QPushButton('清空')
        for b_ in (self.b_rm, self.b_clr): b_.setVisible(False); rs.addWidget(b_)
        self.b_rm.clicked.connect(self.rm_sel); self.b_clr.clicked.connect(lambda: QMessageBox.question(self, '照片', '清空已選的照片？') == QMessageBox.Yes and self.set_imgs([]))
        QShortcut(QKeySequence(Qt.Key_Delete), self.sel, activated=self.rm_sel)
        b_pick = QPushButton('📷 加照片（可多選）'); lc.addWidget(b_pick); b_pick.clicked.connect(self.pick)
        b_vf = QPushButton('🎞 從影片挑格'); b_vf.setToolTip('選一支影片，拉時間軸／±1 ±10 找格子，選好的幾格變成照片（每格各跑一次）'); lc.addWidget(b_vf); b_vf.clicked.connect(self.pick_frames)
        self.slot_box = QWidget(); self.slot_l = QHBoxLayout(self.slot_box); self.slot_l.setContentsMargins(0, 0, 0, 0); h1.addWidget(self.slot_box)   # 圖二、圖三…（流程要好幾張照片時）
        self.slot_imgs = {}; self.slot_w = {}; self.slot_n = 0; lc.addStretch(1)
        rc = QVBoxLayout(); h1.addLayout(rc, 1)
        self.prompt = QPlainTextEdit(); self.prompt.setPlaceholderText('想怎麼改？例如：把衣服換成紅色連身裙'); self.prompt.setMinimumHeight(90); rc.addWidget(self.prompt)
        self.b_h3 = QPushButton('📝 插入 H3 提示詞格式（分鏡＋對白＋聲音；英文描述效果最好）'); self.b_h3.setVisible(False); rc.addWidget(self.b_h3)
        self.b_h3.clicked.connect(lambda: (not self.prompt.toPlainText().strip() or QMessageBox.question(self, 'H3', '換成 H3 提示詞格式？（現在的字會被蓋掉）') == QMessageBox.Yes) and self.prompt.setPlainText(H3SK))
        self.neg = QPlainTextEdit(); self.neg.setPlaceholderText('負面提示詞'); self.neg.setMaximumHeight(60); rc.addWidget(self.neg)
        qb = QHBoxLayout(); rc.addLayout(qb)                                 # V0.2.03 定案的兩個流程一鍵換（跟手機一樣）＋常用改法
        for nm, lab in (('GROK 改圖（INT8 快）', '🏆 GROK'), ('Qwen 2.1 Turbo 改圖', '⚡ Qwen'), ('兩張圖合併（INT8 快）', '🧩 合併'), ('H3 照片動起來', '🎬 影片'), ('H3 首尾幀生影片', '🎞 首尾幀')):   # V0.2.82 跟手機四個模式一樣
            b = QPushButton(lab); b.setToolTip(nm); b.clicked.connect(lambda _=False, n=nm: self.wf.findText(n) >= 0 and self.wf.setCurrentIndex(self.wf.findText(n))); qb.addWidget(b)
        self.tpl = QComboBox(); self.tpl.addItem('🪄 常用改法…')
        for t in ('把衣服換成黑色西裝外套', '換成白色連身裙', '把背景換成海邊夕陽', '背景換成純白攝影棚', '頭髮換成金色長捲髮', '改成黃金時段的溫暖光線', '去掉背景裡的路人', '修復老照片：去掉刮痕、補上顏色',
                  '變成吉卜力動畫風格', '鏡頭往左轉 45 度，從側前方拍', '把商品放在白色背景上，乾淨的電商主圖', '保持人物的臉、五官和身材完全不變',
                  # V0.2.61 跟手機「🧰 工具箱」一樣的完整提示詞
                  '改成標準證件照：正面看鏡頭、表情自然、肩膀擺正，白色純色背景，柔和均勻的攝影棚打光，穿著整齊的深色正裝，保持人物的臉、五官和髮型完全不變',
                  '修復這張老照片：去掉刮痕、污點、摺痕和雜訊，補上自然真實的顏色，讓畫面清楚，保持人物的臉和五官完全不變',
                  '自然地美化人物：皮膚乾淨有光澤、去掉痘痘和黑眼圈、牙齒自然白，保留皮膚質感，臉型和五官完全不變，不要過度磨皮',
                  '讓圖中的人自然微笑，臉型、五官、髮型、衣服、姿勢和背景都不變',
                  '把圖中的人變成Q 版貼圖（白邊），保留他的臉部特徵、髮型和衣服顏色，乾淨的白色背景',
                  '把這張線稿或素描上色，變成完整精緻的彩色插畫，顏色自然協調，線條和構圖位置不變',
                  '把這個房間的裝潢和家具改成北歐風，保持房間的格局、窗戶和門的位置不變，光線自然',
                  '把整個場景變成下雪的冬天，人物和建築不變，天空、地面、樹木和光線跟著季節天氣自然改變'): self.tpl.addItem(t)
        def _tpl(i):
            if i <= 0: return
            t = self.tpl.itemText(i); cur = self.prompt.toPlainText().strip().rstrip('，。,.')
            self.prompt.setPlainText(cur + '，' + t if cur else t); self.tpl.setCurrentIndex(0)
        self.tpl.currentIndexChanged.connect(_tpl); qb.addWidget(self.tpl, 1)
        rw = QHBoxLayout(); rc.addLayout(rw); self.wf = QComboBox(); self.wf.setMinimumWidth(220); self.n = QSpinBox(); self.n.setRange(1, 20); self.n.setSuffix(' 張')
        rw.addWidget(QLabel('流程')); rw.addWidget(self.wf, 1); rw.addWidget(self.n)
        self.wfi = note(''); rc.addWidget(self.wfi)
        mr = QHBoxLayout(); self.mod_l = QLabel(''); self.mod_l.setWordWrap(True); self.mod_l.setTextFormat(Qt.RichText); self.mod_b = QPushButton('⬇ 下載缺的模型'); self.mod_b.hide()
        mr.addWidget(self.mod_l, 1); mr.addWidget(self.mod_b); rc.addLayout(mr); self.mod_b.clicked.connect(self.models_dl); self._mods = []
        self.mod_t = QTimer(self); self.mod_t.timeout.connect(lambda: self.isVisible() and any((m.get('dl') or {}).get('state') in ('run', 'wait') for m in self._mods) and self.models_check()); self.mod_t.start(3000)
        self.parw = QWidget(); self.parl = QVBoxLayout(self.parw); self.parl.setContentsMargins(0, 0, 0, 0); self.parl.setSpacing(2); rc.addWidget(self.parw)
        self.pdefs = []; self.pw = {}; self.par_inner = None
        self.go = QPushButton('▶ 開始'); self.go.setObjectName('start'); rc.addWidget(self.go); self.go.clicked.connect(self.start)
        self.wf.currentIndexChanged.connect(self.wf_info)
        g2 = QGroupBox('⏳ 製作中（做好的在「📜 歷史紀錄」：點兩下＝新舊對比）'); v2 = QVBoxLayout(g2); v.addWidget(g2, 1)
        self.lst = QListWidget(); self.lst.setIconSize(QSize(80, 80)); self.lst.setMinimumHeight(180); self.lst.setWordWrap(True); v2.addWidget(self.lst)
        self.lst.itemDoubleClicked.connect(lambda _it: self.act('cmp') if any(x['id'] == self.sel_id() and x.get('img') and x['outs'] for x in self.jobs) else self.open_out())
        r2 = QHBoxLayout(); v2.addLayout(r2)
        acts = (('⇆ 對比', 'cmp'), ('⏹ 取消', 'cancel'), ('↻ 再跑一次', 'rerun'), ('✏ 拿結果再改', 'reuse'), ('✎ 用這組設定', 'fill'), ('▶ 看／播放', 'open'), ('收起', 'hide'))
        for t_, a_ in acts:
            b_ = QPushButton(t_); b_.clicked.connect(lambda _c=False, a_=a_: self.act(a_)); r2.addWidget(b_)
        r2.addStretch(1)
        L = dict(ENG.cfg.get('gen_last') or {}); self.prompt.setPlainText(L.get('prompt', '')); self.neg.setPlainText(L.get('neg', ''))
        LI = [x for x in (L.get('imgs') or [L.get('img')]) if x and (ENG.data / 'inputs' / x).is_file()]
        if LI: self.set_imgs(LI)
        self.load_wfs(); self.status(True)
        self.tm = QTimer(self); self.tm.timeout.connect(self.refresh); self.tm.start(1000)
        self.tm2 = QTimer(self); self.tm2.timeout.connect(lambda: self.isVisible() and self.status()); self.tm2.start(5000)

    # ---- 連線、流程
    def status(self, force=False):
        bg(lambda: ENG.comfy_status(force), self._st)

    def _st(self, c):
        if c['ok']:
            vr = f'　VRAM 剩 {fmt_b(c["vram"][0])}／{fmt_b(c["vram"][1])}' if c.get('vram') and c['vram'][1] else ''
            self.st.setText(f'<span style="color:#45d483">● 已連上</span> {esc_html(c["url"])}　ComfyUI {esc_html(c["ver"])}　{esc_html(c["gpu"])}{vr}')
        else: self.st.setText(f'<span style="color:#ff4d6d">● 連不到 ComfyUI</span>　{esc_html(c["err"])}<br><small>ComfyUI 要開著；工作會先排隊，連上就開始跑</small>')

    def load_wfs(self):
        bg(ENG.gen_workflows, self._wfs)

    def _wfs(self, L):
        self.wfs = L; cur = self.wf.currentText() or ENG.cfg.get('gen_wf'); self.wf.blockSignals(True); self.wf.clear()
        def grp(w):                                                          # 跟手機一樣分組：改圖／文字生圖／好幾張圖／去背、放大／影片
            if 'video' in (w.get('kinds') or []) or any(k in w['name'] for k in ('影片', 'H3', '補幀')): return 4
            if not w.get('need_img'): return 1
            if int(w.get('n_img') or 0) > 1: return 2
            if any(k in w['name'] for k in ('去背', '放大')): return 3
            return 0
        prev = None
        for w in sorted(L, key=lambda w: (grp(w), w['name'].lower())):
            g = grp(w)
            if prev is not None and g != prev: self.wf.insertSeparator(self.wf.count())
            prev = g; self.wf.addItem(w['name'])
        i = self.wf.findText(cur); self.wf.setCurrentIndex(max(0, i)); self.wf.blockSignals(False); self.wf_info()

    def cur_wf(self): return next((w for w in self.wfs if w['name'] == self.wf.currentText()), None)

    def wf_info(self, *_a):
        w = self.cur_wf()
        cr = (w or {}).get('cr') or {}
        self.b_h3.setVisible(bool(w) and bool(re.search(r'H3|minimax', w.get('name') or '', re.I)) and not cr.get('simple'))
        self.prompt.setPlaceholderText(cr.get('placeholder') or '想怎麼改？例如：把衣服換成紅色連身裙')
        if not w: self.wfi.setText('沒有流程：按上面「➕ 匯入流程」'); return
        if w.get('err'): self.wfi.setText('✖ ' + w['err']); return
        self.wfi.setText(f"{'📷 要照片（' + w['img_node'] + ' 會換成你的照片）' if w['need_img'] else '不用照片'}　✏ 提示詞 → {w['pos'] or '找不到（提示詞不會用到）'}"
                         f"　🖼 {'、'.join(w['outputs']) or '沒有 SaveImage'}　（{w.get('fmt', '')}格式，{w.get('nodes', 0)} 個節點）")
        self.neg.setVisible(bool(w.get('neg'))); self._slots(w); self.models_check()
        wf = w['name']; bg(lambda: ENG.gen_params(wf), lambda T, wf=wf: self._params(wf, T), lambda ex: self.wfi.setText(self.wfi.text() + f'　（參數讀不到：{ex}）'))

    # ---- 參數：常用打開、其他收合；改過的變紫色；每個流程分開記（Data\\settings.json 的 gen_par）
    def _ov(self, wf=None):
        return dict((ENG.cfg.get('gen_par') or {}).get(str(wf or self.wf.currentText() or ''), {}))

    def _ov_set(self, O, wf=None):
        A = dict(ENG.cfg.get('gen_par') or {}); A[str(wf or self.wf.currentText() or '')] = O; ENG.cfg.set('gen_par', A)

    def _params(self, wf, T):
        if not SELFTEST and wf != self.wf.currentText(): return
        self.pdefs = T; self.pw = {}; O = self._ov(wf); D = {it['id']: it for g in T for it in g['items']}
        O = {k: v for k, v in O.items() if k in D and str(v) != str('' if D[k]['type'] == 'seed' else D[k]['value'])}; self._ov_set(O, wf)
        if self.par_inner is not None: self.par_inner.setParent(None); self.par_inner.deleteLater()
        self.par_inner = QWidget(); v = QVBoxLayout(self.par_inner); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(2); self.parl.addWidget(self.par_inner)
        OPEN = dict(ENG.cfg.get('gen_open') or {})
        for g in T:
            hb = QPushButton(); hb.setCheckable(True); hb.setStyleSheet('text-align:left;font-weight:800;border:0;background:transparent;padding:3px 2px')
            body = QWidget(); f = QGridLayout(body); f.setContentsMargins(14, 0, 4, 4); f.setHorizontalSpacing(10); f.setVerticalSpacing(2); col = 0; row = 0; NC = 4
            for it in g['items']:                                          # 能擠就擠：一列 4 格，名字很長的（模型檔名）佔 2 格
                lab = QLabel(re.sub(r'（[^）]*）', '', it['label']) or it['label']); lab.setObjectName('muted'); lab.setToolTip(f"{it['label']}　{it.get('node', '')}　{it['id']}")
                w_ = self._pwidget(it, O.get(it['id'], '' if it['type'] == 'seed' else it['value'])); w_.setToolTip(lab.toolTip())
                span = 2 if (it['type'] == 'choice' and max((len(str(c)) for c in it['choices']), default=0) > 14) or it['type'] == 'str' else 1
                if col + span > NC: col = 0; row += 2
                self.pw[it['id']] = (w_, lab, it); f.addWidget(lab, row, col, 1, span); f.addWidget(w_, row + 1, col, 1, span); col += span
                if col >= NC: col = 0; row += 2
            for c_ in range(NC): f.setColumnStretch(c_, 1)
            op = bool(OPEN.get(g['g'], g['open']))
            def tog(on, hb=hb, body=body, g=g):
                body.setVisible(on); hb.setText(f"{'▾' if on else '▸'} {g['g']}　（{len(g['items'])} 項）")
                A = dict(ENG.cfg.get('gen_open') or {}); A[g['g']] = bool(on); ENG.cfg.set('gen_open', A)
            hb.setChecked(op); body.setVisible(op); hb.setText(f"{'▾' if op else '▸'} {g['g']}　（{len(g['items'])} 項）"); hb.toggled.connect(tog)
            v.addWidget(hb); v.addWidget(body)
        r = QHBoxLayout(); self.pcount = note(''); r.addWidget(self.pcount, 1); b = QPushButton('↺ 還原流程預設'); r.addWidget(b); v.addLayout(r)
        b.clicked.connect(lambda: (self._ov_set({}, wf), self._params(wf, T))); self._pmark()

    def _pwidget(self, it, val):
        t = it['type']; ch = lambda *_a: self._pchanged()
        if t == 'choice' or it.get('presets'):
            w_ = QComboBox(); L = list(it['choices']) if t == 'choice' else sorted(set(list(it['presets']) + [val]), key=float)
            w_._vals = L; w_.addItems([str(x) + ('（預設）' if t != 'choice' and x == it['value'] else '') for x in L]); w_.setMaximumWidth(420)
            try: w_.setCurrentIndex([str(x) for x in L].index(str(val)))
            except ValueError: pass
            w_.currentIndexChanged.connect(ch)
        elif t == 'bool': w_ = QCheckBox(); w_.setChecked(bool(val)); w_.toggled.connect(ch)
        elif t == 'int':
            w_ = QSpinBox(); w_.setRange(int(max(-2 ** 31 + 1, it.get('min', -2 ** 31 + 1))), int(min(2 ** 31 - 1, it.get('max', 2 ** 31 - 1))))
            try: w_.setValue(int(float(val)))
            except Exception: w_.setValue(int(it['value']))
            w_.valueChanged.connect(ch)
        elif t == 'float':
            from PySide6.QtWidgets import QDoubleSpinBox
            w_ = QDoubleSpinBox(); w_.setDecimals(3); w_.setRange(float(it.get('min', -1e9)), float(it.get('max', 1e9))); w_.setSingleStep(float(it.get('step') or 0.05))
            try: w_.setValue(float(val))
            except Exception: w_.setValue(float(it['value']))
            w_.valueChanged.connect(ch)
        else:
            w_ = QLineEdit(str(val if val is not None else '')); w_.setMaximumWidth(420); w_.editingFinished.connect(ch)
            if t == 'seed': w_.setPlaceholderText('隨機'); w_.setMaximumWidth(200)
        return w_

    def _pval(self, w_, it):
        t = it['type']
        if hasattr(w_, '_vals'): return w_._vals[max(0, w_.currentIndex())] if w_._vals else it['value']
        if t == 'bool': return w_.isChecked()
        if t in ('int', 'float'): return w_.value()
        if t == 'seed':
            x = w_.text().strip(); return int(x) if x.lstrip('-').isdigit() else ''
        return w_.text()

    def _pchanged(self):
        O = {}
        for k, (w_, _l, it) in self.pw.items():
            v = self._pval(w_, it)
            if str(v) != str('' if it['type'] == 'seed' else it['value']): O[k] = v
        self._ov_set(O); self._pmark()

    def _pmark(self):
        O = self._ov(); n = 0
        for k, (_w, lab, _it) in self.pw.items():
            on = k in O; n += on; lab.setStyleSheet('color:#a78bfa;font-weight:700' if on else '')
        try: self.pcount.setText(f'改了 {n} 項（紫色）' if n else '都是流程本來的設定')
        except Exception: pass

    def _slots(self, w):
        """流程要好幾張照片（例如「兩張圖合併」：圖一＝場景、圖二＝人物）→ 第一張用左邊原本的格子，其他的格子加在旁邊."""
        n = int(w.get('n_img') or 0); T = w.get('slots') or []
        hv = 'video' in (w.get('kinds') or [])
        self.prompt.setPlaceholderText('描述主角長相＋背景（不要寫動作，動作照影片）。例如：Character appearance description: 一隻白色小型貴賓狗，捲毛、黑眼睛。Background description: 明亮的現代廚房' if hv
                                       else '例如：讓圖2的人坐在圖1的場景裡，拿著咖啡杯喝咖啡' if n > 1 else '想怎麼改？例如：把衣服換成紅色連身裙')
        if n == self.slot_n and getattr(self, '_slot_t', None) == T: return
        self.slot_n = n; self._slot_t = T
        while self.slot_l.count():
            it = self.slot_l.takeAt(0); ww = it.widget()
            if ww is not None: ww.setParent(None); ww.deleteLater()
        self.slot_w = {}
        for i in range(1, n):
            col = QWidget(); v = QVBoxLayout(col); v.setContentsMargins(0, 0, 0, 0); t = QLabel(f'<b>{esc_html(T[i] if i < len(T) else f"圖{i + 1}")}</b>'); t.setTextFormat(Qt.RichText)
            pv = QLabel('（還沒選）'); pv.setFixedSize(200, 200); pv.setAlignment(Qt.AlignCenter); pv.setStyleSheet('border:2px dashed #3a4654;border-radius:10px')
            vk = (w.get('kinds') or [])[i:i + 1] == ['video']
            b = QPushButton('🎬 選影片' if vk else '📷 選照片（可多選）'); b.clicked.connect(lambda _c=False, i=i, vk=vk: self.pick_slot(i, vk))
            for x in (t, pv, b): v.addWidget(x)
            v.addStretch(1); self.slot_l.addWidget(col); self.slot_w[i] = pv
            if self.slot_imgs.get(i): self._slot_show(i)
        self.slot_box.setVisible(n > 1)

    def pick_slot(self, i, video=False):
        if video: P, _ = QFileDialog.getOpenFileNames(self, '選影片', ldir('video', Path.home() / 'Videos'), '影片 (*.mp4 *.mov *.webm *.mkv *.m4v)'); sdir('video', P)
        else: P, _ = QFileDialog.getOpenFileNames(self, '選照片', ldir('photo', Path.home() / 'Pictures'), '圖片 (*.jpg *.jpeg *.png *.webp *.bmp)'); sdir('photo', P)
        if not P: return
        mp = float(ENG.cfg.get('gen_mp') or 0); self.win.msg('讀檔中…', 60000)
        def work():
            N = []
            for p in P:
                try: N.append(ENG.gen_save_input(Path(p).read_bytes() if video else _photo_bytes(p, mp), Path(p).name))
                except Exception as ex: ENG.log.w(f'生圖：照片讀不到 {p}：{ex}')
            return N
        bg(work, lambda N: (self.slot_imgs.__setitem__(i, N), self._slot_show(i)) if N else QMessageBox.warning(self, '照片', '這些照片都讀不到'))

    def _slot_show(self, i):
        pv = self.slot_w.get(i); N = self.slot_imgs.get(i) or []
        if pv is None or not N: return
        if ENG.is_video_name(N[0]):
            pv.setText(f'🎬 影片\n{N[0]}\n{fmt_b((ENG.data / "inputs" / N[0]).stat().st_size)}' + (f'\n共 {len(N)} 支' if len(N) > 1 else '')); pv.setWordWrap(True); return
        def show(im):
            if im.isNull(): pv.setText('（讀不到）'); return
            pm = QPixmap.fromImage(im)
            if len(N) > 1:
                p = QPainter(pm); p.setBrush(QColor(0, 0, 0, 170)); p.setPen(Qt.NoPen); p.drawRect(0, pm.height() - 30, pm.width(), 30); p.setPen(QColor('#fff'))
                f = QFont(self.font()); f.setBold(True); f.setPixelSize(14); p.setFont(f); p.drawText(QRectF(0, pm.height() - 30, pm.width(), 30), Qt.AlignCenter, f'共 {len(N)} 張'); p.end()
            pv.setPixmap(pm)
        bg(lambda: _img_small(ENG.data / 'inputs' / N[0], 196), show)

    def models_check(self):
        w = self.cur_wf()
        if not w: return
        wf = w['name']; bg(lambda: ENG.gen_models(wf), lambda M, wf=wf: self._models(wf, M), lambda ex: None)

    def _models(self, wf, M):
        if wf != self.wf.currentText(): return
        self._mods = M; miss = [m for m in M if not m['ok']]
        if not miss: self.mod_l.setText(''); self.mod_b.hide(); return
        rows = []
        for m in miss:
            d = m.get('dl') or {}
            rows.append(f"{ {'run': '⬇', 'done': '✔', 'fail': '✖'}.get(d.get('state'), '·') } {esc_html(m['file'])}（{esc_html(m['folder'])}{'，' + fmt_b(m['size']) if m.get('size') else ''}）{'　' + esc_html(d.get('msg', '')) if d.get('msg') else ''}{'' if m['known'] else '　不知道去哪下載，請自己放進 ComfyUI'}")
        self.mod_l.setText(f'<span style="color:#f0ad4e"><b>⚠ 這個流程還缺 {len(miss)} 個模型</b></span><br>' + '<br>'.join(rows))
        can = [m for m in miss if m['known'] and (m.get('dl') or {}).get('state') not in ('run', 'wait')]
        self.mod_b.setVisible(bool(can)); self.mod_b.setText(f'⬇ 下載缺的模型（約 {fmt_b(sum(m.get("size") or 0 for m in can))}）')

    def models_dl(self):
        can = [m['file'] for m in self._mods if not m['ok'] and m['known']]
        if not can: return
        if QMessageBox.question(self, '下載模型', '下載到 ComfyUI 的模型資料夾：\n\n' + '\n'.join(can) + '\n\n很大，要一段時間；中斷了再按會接著下載。開始？') != QMessageBox.Yes: return
        bg(lambda: ENG.dl_add(can), lambda n: (self.win.msg(f'開始下載 {n} 個模型（進度在「🖥 後台」）'), self.models_check()))

    def open_cmp(self):
        """🧪 比較頁做在網頁版（手機、電腦瀏覽器都能用）：手機網頁沒開就提示."""
        if not ENG.cfg.get('web_on'):
            if not ENG.cfg.get('web_pin_hash'):
                QMessageBox.information(self, '🧪 比較模型', '比較頁在「手機網頁」裡（電腦瀏覽器也能開大螢幕版）。\n先到「⚙ 設定 → 📱 手機網頁」設一個 PIN、打開手機網頁，再按一次。'); return
            if QMessageBox.question(self, '🧪 比較模型', '比較頁在「手機網頁」裡（電腦瀏覽器開大螢幕版）。\n現在幫你打開手機網頁？（用你設好的 PIN 登入）') != QMessageBox.Yes: return
            ENG.cfg.set('web_on', True); web_apply()
        ENG.cfg.set('web_tab_hint', 'cmp')
        QDesktopServices.openUrl(QUrl(f'http://127.0.0.1:{int(ENG.cfg.get("web_port") or BRAND["web_port"])}/?pc=1&tab=cmp'))

    def import_tpl(self):
        L = [f'{t}　（{n}）' for t, n in ENG.TEMPLATES]
        t, ok = QInputDialog.getItem(self, '📥 從 ComfyUI 官方範本做流程', 'ComfyUI 要開著。選一個，或打其他範本名稱：', L, 0, True)
        if not ok or not t.strip(): return
        tpl = t.split('　')[0].strip(); nm = dict(ENG.TEMPLATES).get(tpl) or tpl
        force = ENG.gen_wf_path(nm).exists() and QMessageBox.question(self, '官方範本', f'已經有「{nm}」，重新抓換掉？（舊的會備份）') == QMessageBox.Yes
        if ENG.gen_wf_path(nm).exists() and not force: return
        def done(n): self.win.msg(f'✔ 做好流程「{n}」'); self.load_wfs(); QTimer.singleShot(300, lambda: self.wf.setCurrentIndex(max(0, self.wf.findText(n))))
        bg(lambda: ENG.gen_from_template(tpl, nm, force), done, lambda ex: QMessageBox.warning(self, '官方範本', str(ex)))

    def import_wf(self):
        p, _ = QFileDialog.getOpenFileName(self, '匯入 ComfyUI 流程', ldir('wf', Path.home() / 'Downloads'), 'ComfyUI 流程 (*.json)'); sdir('wf', p)
        if not p: return
        def done(nm): self.win.msg(f'已匯入流程「{nm}」'); self.load_wfs(); QTimer.singleShot(300, lambda: self.wf.setCurrentIndex(max(0, self.wf.findText(nm))))
        bg(lambda: ENG.gen_wf_save(Path(p).stem, Path(p).read_bytes()), done, lambda ex: QMessageBox.warning(self, '匯入流程', str(ex)))

    # ---- 照片
    def pick(self):
        """可以一次選很多張（批量：每張都用同一段提示詞各跑一次）."""
        P, _ = QFileDialog.getOpenFileNames(self, '選照片（可以一次選很多張）', ldir('photo', Path.home() / 'Pictures'), '圖片 (*.jpg *.jpeg *.png *.webp *.bmp)'); sdir('photo', P)
        if not P: return
        self.win.msg(f'讀照片中…（{len(P)} 張）', 60000); mp = float(ENG.cfg.get('gen_mp') or 0)
        def work():
            N = []
            for p in P:
                try: N.append(ENG.gen_save_input(_photo_bytes(p, mp), Path(p).name))
                except Exception as ex: ENG.log.w(f'生圖：照片讀不到 {p}：{ex}')
            return N
        bg(work, lambda N: (self.set_imgs(self.cur_imgs() + N), self.win.msg(f'加了 {len(N)} 張，現在共 {len(self.cur_imgs())} 張' + (f'（{len(P) - len(N)} 張讀不到）' if len(N) < len(P) else ''))) if N else QMessageBox.warning(self, '照片', '這些照片都讀不到'))

    def pick_frames(self):
        p, _ = QFileDialog.getOpenFileName(self, '選影片（從裡面挑格）', ldir('video', Path.home() / 'Videos'), '影片 (*.mp4 *.mov *.webm *.mkv *.m4v *.avi)'); sdir('video', p)
        if not p: return
        d = FramePicker(self, p)
        def add(N):
            old = [x for x in self.cur_imgs() if not ENG.is_video_name(x)]
            self.set_imgs(old + N); self.win.msg(f'✔ 加了 {len(N)} 格照片，現在共 {len(self.cur_imgs())} 張（已選的照片下面可以拿掉）')
        d.done_cb = add; d.show()

    def cur_imgs(self): return [x for x in (self.imgs or ([self.img] if self.img else [])) if x]

    def rm_sel(self):
        rows = sorted({self.sel.row(it) for it in self.sel.selectedItems()}, reverse=True)
        if not rows: self.win.msg('先點要拿掉的照片（Ctrl 可以選很多張）'); return
        L = self.cur_imgs()
        for r in rows:
            if r < len(L): L.pop(r)
        self.set_imgs(L)

    def _sel_refresh(self):
        L = self.cur_imgs(); self.sel.clear(); vis = len(L) >= 1
        for w_ in (self.sel, self.b_rm, self.b_clr): w_.setVisible(vis)
        for i, n in enumerate(L):
            m = re.search(r'_f(\d{4,})\.\w+$', n); it = QListWidgetItem(f'🎞{int(m.group(1))}' if m else str(i + 1)); self.sel.addItem(it)
            p = ENG.data / 'inputs' / n
            bg(lambda p=p: _img_small(p, 120), lambda im, it=it: it.setIcon(QIcon(QPixmap.fromImage(im))))

    def set_imgs(self, names):
        names = [n for n in names if n]
        if len(names) <= 1: self.set_img(names[0] if names else ''); self._sel_refresh(); return
        self.set_img(names[0]); self.imgs = list(names); self._sel_refresh()

    def set_img(self, name):
        self.img = name; self.imgs = [name] if name else []; self.pv.setText('讀取中…')
        if not name: self.pv.setText('（還沒選照片）'); return
        def show(im):
            if im.isNull(): self.pv.setText('（讀不到）'); return
            pm = QPixmap.fromImage(im)
            if len(self.imgs) > 1:                                          # 批量：第一張上面標「共 N 張」
                p = QPainter(pm); p.setBrush(QColor(0, 0, 0, 170)); p.setPen(Qt.NoPen); p.drawRect(0, pm.height() - 34, pm.width(), 34)
                p.setPen(QColor('#fff')); f = QFont(self.font()); f.setBold(True); f.setPixelSize(15); p.setFont(f)
                p.drawText(QRectF(0, pm.height() - 34, pm.width(), 34), Qt.AlignCenter, f'📚 批量：共 {len(self.imgs)} 張'); p.end()
            self.pv.setPixmap(pm)
        bg(lambda: _img_small(ENG.data / 'inputs' / name, 236), show)

    # ---- 開始
    def start(self):
        w = self.cur_wf()
        if not w: QMessageBox.information(self, '生圖', '還沒有流程：按「➕ 匯入流程」'); return
        if w.get('need_img') and not self.imgs: QMessageBox.information(self, '生圖', '這個流程要先選照片'); return
        NS = int(w.get('n_img') or 0)
        for i in range(1, NS):
            if not self.slot_imgs.get(i): QMessageBox.information(self, '生圖', '還沒選：' + ((w.get('slots') or [])[i] if i < len(w.get('slots') or []) else f'圖{i + 1}')); return
        pr = self.prompt.toPlainText().strip(); ng = self.neg.toPlainText().strip(); n = self.n.value()
        import itertools
        combos = [list(c) for c in itertools.product(list(self.imgs), *[self.slot_imgs[i] for i in range(1, NS)])][:200] if NS > 1 else [[x] for x in (list(self.imgs) if w.get('need_img') else [''])]
        imgs = combos
        if len(imgs) > 1 and QMessageBox.question(self, '批量', f'{len(imgs)} 組照片 × {n} 張 = {len(imgs) * n} 個工作，都用同一段提示詞？') != QMessageBox.Yes: return
        ENG.cfg.set('gen_last', {'prompt': pr, 'neg': ng, 'img': self.img, 'imgs': self.imgs})
        P = self._ov(w['name'])
        def add():
            ids = []
            for c in imgs: ids += ENG.gen_add(w['name'], pr, c[0], ng, n, '電腦', params=P, imgs=[x for x in c if x] or None)
            ENG.gen_set_batch(ids)
            if len(imgs) > 1: ENG.log.w(f'生圖：批量 {len(imgs)} 張照片 → {len(ids)} 個工作')
            return ids
        bg(add, lambda ids: (self.win.msg(f'排好了 {len(ids)} 張'), self.refresh(True)),
           lambda ex: QMessageBox.warning(self, '生圖', str(ex)))

    # ---- 結果清單
    def refresh(self, force=False):
        if not force and not self.isVisible(): return
        bg(lambda: sorted([j for j in ENG.gen_jobs(80) if j['state'] in ('wait', 'run')], key=lambda j: (j['state'] != 'run', j.get('qpos') or 0)), self._jobs)   # 這一頁只放製作中的；做好的在「📜 歷史紀錄」

    def _icon(self, rel):
        if ENG.is_video_name(rel): return None
        if rel in self.icons: return self.icons[rel]
        if rel not in self.loading:
            self.loading.add(rel); p = ENG.gen_file(rel)
            if p is not None: bg(lambda: _img_small(p, 220), lambda im, rel=rel: (self.icons.__setitem__(rel, QIcon(QPixmap.fromImage(im))), setattr(self, 'sig', None)))
        return None

    def _jobs(self, J):
        self.jobs = J; sig = tuple((j['id'], j['state'], j.get('msg'), j.get('pct'), len(j['outs']), j.get('qpos'), int(time.time()) if j['state'] == 'run' else 0) for j in J) + (len(self.icons),)
        if sig == self.sig: return
        ids = [j['id'] for j in J]; same = ids == [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count())]
        self.sig = sig; sel = self.sel_id()
        if not same: self.lst.clear()
        for row, j in enumerate(J):
            nm, col = GEN_ST.get(j['state'], (j['state'], None)); st = nm
            if j['state'] == 'wait' and j.get('qpos'): st += f' 第 {j["qpos"]} 個'
            est = (j.get('est') or {}).get('sec')
            if j['state'] == 'run':
                st = f'▶ {round(j.get("prog") or 0)}%　' + (j.get('msg') or '生成中')
                if j.get('t_start'):
                    el = time.time() - j['t_start']; st += f'　⏱ {fmt_t(el)}'
                    if est: st += f' ／ 預估 {fmt_t(est)}' + (f'（還剩約 {fmt_t(est - el)}）' if el < est else '（比預估久）')
            if j['state'] == 'wait': st += (f'　{j["msg"]}' if j.get('msg') else '') + (f'　預估運算 {fmt_t(est)}' + (f'・大約 {fmt_t(j["eta"])} 後開始' if j.get('eta') else '') if est else '　（這個設定第一次跑，還沒有時間資料）')
            if j['state'] == 'done':
                st += f'　{len(j["outs"])} 張　⏱ 運算 {fmt_t(j["run_s"])}（全部 {fmt_t(j["dur"])}）' if j.get('run_s') else f'　{j["dur"]:.0f} 秒　{len(j["outs"])} 張'
                if j.get('cold') == 1: st += '　有載入模型'
                if j.get('out_w'): st += f'　{j["out_w"]}×{j["out_h"]}'
            if j['state'] == 'fail': st += '　' + (j.get('msg') or '')[:160]
            tm = time.strftime('%m/%d %H:%M', time.localtime(j['t']))
            txt = f'#{j["id"]}　{st}\n{j["prompt"] or "（沒有提示詞）"}\n{j["src"]}　{tm}　{j["wf"]}　{j.get("brief", "")}'
            it = self.lst.item(row) if same else QListWidgetItem(txt)
            if same and it.text() != txt: it.setText(txt)
            it.setData(Qt.UserRole, j['id'])
            if col: it.setForeground(QColor(col))
            ic = self._icon(j['outs'][0]) if j['outs'] else (self._icon('inputs/' + j['img']) if j.get('img') else None)
            if ic is not None: it.setIcon(ic)
            if not same:
                self.lst.addItem(it)
                if j['id'] == sel: self.lst.setCurrentItem(it)

    def sel_id(self):
        it = self.lst.currentItem(); return int(it.data(Qt.UserRole)) if it is not None and it.data(Qt.UserRole) is not None else None

    def open_out(self):
        jid = self.sel_id(); j = next((x for x in self.jobs if x['id'] == jid), None)
        if not j or not j['outs']: self.win.msg('這個工作還沒有結果圖'); return
        MediaDlg.open(self, [ENG.gen_file(o) for o in j['outs']], f'#{j["id"]} {j.get("prompt", "")[:30]}')   # 主程式裡直接看／播

    def act(self, a):
        jid = self.sel_id()
        if jid is None: self.win.msg('先在清單點一個工作'); return
        j = next((x for x in self.jobs if x['id'] == jid), {})
        if a == 'open': self.open_out(); return
        if a == 'cmp':
            if j.get('outs') and ENG.is_video_name(j['outs'][0]): self.open_out(); return
            if j.get('img') and j.get('outs'): show_compare(self, 'inputs/' + j['img'], j['outs'][0])
            else: self.win.msg('這個工作沒有原圖或還沒有結果')
            return
        if a == 'fill':
            self.prompt.setPlainText(j.get('prompt', '')); self.neg.setPlainText(j.get('neg', ''))
            if j.get('img'): self.set_img(j['img'])
            self._ov_set(dict(j.get('params') or {}), j.get('wf'))
            for k_, x_ in enumerate(j.get('imgs') or []):
                if k_: self.slot_imgs[k_] = [x_]; self._slot_show(k_)
            i = self.wf.findText(j.get('wf', ''))
            if i >= 0:
                if i == self.wf.currentIndex(): self.wf_info()
                else: self.wf.setCurrentIndex(i)
            self.win.msg('已填回：照片、提示詞、流程和參數'); return
        if a == 'cancel' and QMessageBox.question(self, '取消', f'取消 #{jid}？') != QMessageBox.Yes: return
        fn = {'cancel': lambda: ENG.gen_cancel(jid), 'rerun': lambda: ENG.gen_rerun(jid, '電腦'), 'reuse': lambda: ENG.gen_reuse(jid), 'hide': lambda: ENG.gen_hide(jid)}[a]
        def done(r):
            if a == 'reuse': self.set_img(r); self.win.msg('✔ 換成這張結果了，打新的提示詞再按開始')
            self.refresh(True)
        bg(fn, done, lambda ex: QMessageBox.warning(self, '生圖', str(ex)))


# ============================================================ ⇆ 對比：舊的（左）和新的（右）疊在一起，中間拉桿左右拉
class CompareView(QWidget):
    def __init__(self, old_im, new_im):
        super().__init__(); self.a = QPixmap.fromImage(old_im); self.b = QPixmap.fromImage(new_im); self.x = 0.5; self.setMinimumSize(300, 300); self.setCursor(Qt.SizeHorCursor)

    def _rect(self):
        w, h = max(1, self.b.width()), max(1, self.b.height()); k = min(self.width() / w, self.height() / h)
        return QRectF((self.width() - w * k) / 2, (self.height() - h * k) / 2, w * k, h * k)

    def paintEvent(self, _e):
        p = QPainter(self); p.setRenderHint(QPainter.SmoothPixmapTransform); r = self._rect()
        p.fillRect(self.rect(), QColor('#000')); p.drawPixmap(r, self.a, QRectF(self.a.rect()))
        cx = r.left() + r.width() * self.x; p.save(); p.setClipRect(QRectF(cx, r.top(), r.right() - cx, r.height())); p.drawPixmap(r, self.b, QRectF(self.b.rect())); p.restore()
        p.setPen(QPen(QColor('#fff'), 3)); p.drawLine(int(cx), int(r.top()), int(cx), int(r.bottom()))
        p.setBrush(QColor('#fff')); p.setPen(Qt.NoPen); p.drawEllipse(QPoint(int(cx), int(r.center().y())), 18, 18)
        p.setPen(QColor('#222')); f = QFont(self.font()); f.setPixelSize(20); f.setBold(True); p.setFont(f)
        p.drawText(QRectF(cx - 18, r.center().y() - 18, 36, 36), Qt.AlignCenter, '⇆')
        f.setPixelSize(13); p.setFont(f)
        for txt, x_ in (('舊', r.left() + 8), ('新', r.right() - 36)):
            p.setBrush(QColor(0, 0, 0, 150)); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(x_, r.top() + 8, 28, 22), 6, 6); p.setPen(QColor('#fff')); p.drawText(QRectF(x_, r.top() + 8, 28, 22), Qt.AlignCenter, txt)
        p.end()

    def _set(self, e):
        r = self._rect(); px = e.position().x() if hasattr(e, 'position') else e.x(); self.x = max(0.0, min(1.0, (px - r.left()) / max(1.0, r.width()))); self.update()

    def mousePressEvent(self, e): self._set(e)

    def mouseMoveEvent(self, e): self._set(e)


def ldir(kind, default):
    """選檔視窗：上次在這一類（照片／影片／流程…）用的資料夾；沒有或不見了就用預設."""
    try:
        d = (ENG.cfg.get('last_dirs') or {}).get(kind)
        if d and Path(d).is_dir(): return str(d)
    except Exception: pass
    return str(default)


def sdir(kind, picked):
    """記住這次選的資料夾（picked＝檔案、檔案清單或資料夾）."""
    try:
        x = picked[0] if isinstance(picked, (list, tuple)) else picked
        if not x: return picked
        d = Path(x); d = d if d.is_dir() else d.parent
        D = dict(ENG.cfg.get('last_dirs') or {}); D[kind] = str(d); ENG.cfg.set('last_dirs', D)
    except Exception: pass
    return picked


def _mm():
    """Qt 的影片播放元件（PySide6 內建，Qt 6.5 起用 FFmpeg）；載入失敗回 None."""
    try:
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PySide6.QtMultimediaWidgets import QVideoWidget
        return QMediaPlayer, QAudioOutput, QVideoWidget
    except Exception: return None


class MediaDlg(QDialog):
    """▶ 主程式裡直接看結果：影片（播放／暫停、拉進度、循環、音量）和圖片。← → 換上一個／下一個（這筆看完接上一筆／下一筆紀錄）、空白鍵播放／暫停、Esc 關."""
    inst = None

    @classmethod
    def open(cls, parent, files, title='', nav=None, idx=0):
        files = [str(f) for f in files if f]
        if not files: return None
        d = cls.inst
        try:
            if d is None or not d.isVisible(): d = cls.inst = cls(parent)
        except RuntimeError: d = cls.inst = cls(parent)
        d.nav = nav; d.files = files; d.title = title; d.i = max(0, min(idx, len(files) - 1)); d.load(); d.show(); d.raise_(); d.activateWindow(); return d

    def __init__(self, parent):
        super().__init__(parent); self.resize(1000, 820); self.files = []; self.i = 0; self.nav = None; self.title = ''
        v = QVBoxLayout(self); v.setContentsMargins(6, 6, 6, 6); self.stack = QStackedWidget(); v.addWidget(self.stack, 1)
        self.pic = QLabel(); self.pic.setAlignment(Qt.AlignCenter); self.pic.setStyleSheet('background:#000;border-radius:6px'); self.pic.setMinimumSize(200, 200); self.stack.addWidget(self.pic)
        M = _mm(); self.player = None
        if M:
            QMediaPlayer, QAudioOutput, QVideoWidget = M
            self.vw = QVideoWidget(); self.vw.setStyleSheet('background:#000'); self.stack.addWidget(self.vw)
            self.player = QMediaPlayer(self); self.audio = QAudioOutput(self); self.player.setAudioOutput(self.audio); self.player.setVideoOutput(self.vw)
            self.audio.setVolume(float(ENG.cfg.get('play_vol') if ENG.cfg.get('play_vol') is not None else 0.8))
            self.player.positionChanged.connect(self._pos); self.player.durationChanged.connect(self._dur)
            self.player.playbackStateChanged.connect(lambda *_a: self.bp.setText('⏸ 暫停' if self._playing() else '▶ 播放'))
            try: self.player.errorOccurred.connect(lambda *_a: self.inf.setText('✖ 播不了：' + self.player.errorString()))
            except Exception: pass
        r = QHBoxLayout(); v.addLayout(r)
        self.bprev = QPushButton('◀ 上一個（←）'); self.bp = QPushButton('▶ 播放'); self.sl = QSlider(Qt.Horizontal); self.tm = QLabel('0:00 / 0:00')
        self.loop = QCheckBox('🔁 循環'); self.loop.setChecked(ENG.cfg.get('play_loop') is not False)
        self.vol = QSlider(Qt.Horizontal); self.vol.setRange(0, 100); self.vol.setFixedWidth(90); self.vol.setValue(int(100 * float(ENG.cfg.get('play_vol') if ENG.cfg.get('play_vol') is not None else 0.8)))
        self.bnext = QPushButton('下一個（→） ▶')
        for w_ in (self.bprev, self.bp, self.sl, self.tm, self.loop, QLabel('🔊'), self.vol, self.bnext): r.addWidget(w_, 1 if w_ is self.sl else 0)
        for b in (self.bprev, self.bp, self.bnext, self.loop): b.setFocusPolicy(Qt.NoFocus)
        self.sl.setFocusPolicy(Qt.NoFocus); self.vol.setFocusPolicy(Qt.NoFocus)
        r2 = QHBoxLayout(); v.addLayout(r2); self.inf = note(''); r2.addWidget(self.inf, 1)
        b_dir = QPushButton('📂 打開資料夾'); b_ext = QPushButton('↗ 用外部程式開'); r2.addWidget(b_dir); r2.addWidget(b_ext)
        self.bprev.clicked.connect(lambda: self.step(-1)); self.bnext.clicked.connect(lambda: self.step(1)); self.bp.clicked.connect(self.toggle)
        self.sl.sliderMoved.connect(lambda x: self.player and self.player.setPosition(x))
        self.loop.toggled.connect(self._loop); self.vol.valueChanged.connect(self._vol)
        b_dir.clicked.connect(lambda: self.files and QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.files[self.i]).parent))))
        b_ext.clicked.connect(lambda: self.files and QDesktopServices.openUrl(QUrl.fromLocalFile(self.files[self.i])))

    def _playing(self):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            return self.player is not None and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        except Exception: return False

    def _loop(self, on):
        ENG.cfg.set('play_loop', bool(on))
        if self.player is not None:
            try: self.player.setLoops(-1 if on else 1)
            except Exception: pass

    def _vol(self, x):
        ENG.cfg.set('play_vol', x / 100)
        if self.player is not None: self.audio.setVolume(x / 100)

    def _pos(self, ms):
        if not self.sl.isSliderDown(): self.sl.setValue(int(ms))
        self.tm.setText(f'{fmt_ms(ms)} / {fmt_ms(self.player.duration())}')

    def _dur(self, ms): self.sl.setRange(0, int(ms)); self.tm.setText(f'0:00 / {fmt_ms(ms)}')

    def load(self):
        f = self.files[self.i]; vid = ENG.is_video_name(f)
        self.setWindowTitle(f'▶ {self.title}　{Path(f).name}' + (f'　（{self.i + 1}／{len(self.files)}）' if len(self.files) > 1 else ''))
        for w_ in (self.bp, self.sl, self.tm, self.loop, self.vol): w_.setVisible(vid)
        if self.player is not None: self.player.stop()
        if vid:
            if self.player is None:
                self.inf.setText('這台電腦的 Qt 沒有影片播放元件，改用外部程式開'); QDesktopServices.openUrl(QUrl.fromLocalFile(f)); return
            self.stack.setCurrentWidget(self.vw); self.player.setSource(QUrl.fromLocalFile(f)); self._loop(self.loop.isChecked()); self.player.play()
            self.inf.setText('空白鍵＝播放／暫停　← →＝上一個／下一個　Esc＝關')
        else:
            self.stack.setCurrentWidget(self.pic); self._pm = QPixmap(f); self._fit()
            self.inf.setText(f'{self._pm.width()}×{self._pm.height()}　← →＝上一個／下一個　Esc＝關')

    def _fit(self):
        pm = getattr(self, '_pm', None)
        if pm is not None and not pm.isNull() and self.stack.currentWidget() is self.pic:
            self.pic.setPixmap(pm.scaled(self.pic.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, e): super().resizeEvent(e); self._fit()

    def toggle(self):
        if self.player is None: return
        self.player.pause() if self._playing() else self.player.play()

    def step(self, k):
        j = self.i + k
        if 0 <= j < len(self.files): self.i = j; self.load(); return
        if self.nav is not None and self.nav(k): return
        self.inf.setText('已經是最後一個' if k > 0 else '已經是第一個')

    def keyPressEvent(self, e):
        k = e.key()
        if k in (Qt.Key_Left, Qt.Key_Up): self.step(-1)
        elif k in (Qt.Key_Right, Qt.Key_Down): self.step(1)
        elif k == Qt.Key_Space: self.toggle()
        else: super().keyPressEvent(e)

    def closeEvent(self, e):
        if self.player is not None:
            self.player.stop(); self.player.setSource(QUrl())
        super().closeEvent(e)


def fmt_ms(ms):
    s = max(0, int(ms or 0) // 1000); return f'{s // 60}:{s % 60:02d}'


class CompareDlg(QDialog):
    """對比視窗；nav(k) 有給的話：← → 鍵或按鈕看上一筆／下一筆（不用關掉再選）."""
    def __init__(self, parent, nav=None):
        super().__init__(parent); self.nav = nav; self.resize(1000, 880); v = QVBoxLayout(self); v.setContentsMargins(6, 6, 6, 6)
        self.cv = CompareView(QPixmap(1, 1).toImage(), QPixmap(1, 1).toImage()); v.addWidget(self.cv, 1)
        r = QHBoxLayout(); v.addLayout(r); self.bp = QPushButton('◀ 上一筆（←）'); self.bn = QPushButton('下一筆（→） ▶'); self.lab = note('')
        r.addWidget(self.bp); r.addWidget(self.lab, 1); r.addWidget(self.bn)
        self.bp.clicked.connect(lambda: self.step(-1)); self.bn.clicked.connect(lambda: self.step(1))
        for b in (self.bp, self.bn): b.setVisible(nav is not None); b.setFocusPolicy(Qt.NoFocus)

    def step(self, k):
        if self.nav: self.nav(k, self)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Left, Qt.Key_Up): self.step(-1)
        elif e.key() in (Qt.Key_Right, Qt.Key_Down): self.step(1)
        else: super().keyPressEvent(e)

    def load(self, old_rel, new_rel, info=''):
        po, pn = ENG.gen_file(old_rel), ENG.gen_file(new_rel)
        if po is None or pn is None: self.lab.setText('找不到原圖或結果圖'); return
        self.setWindowTitle(f'⇆ 對比：左＝舊　右＝新　（{Path(str(pn)).name}）'); self.lab.setText((info + '　' if info else '') + '滑鼠在圖上按住左右拉；← → 看上一筆／下一筆')
        key = new_rel; self._want = key
        def ok(r):
            if getattr(self, '_want', None) != key: return
            x = self.cv.x; self.cv.a = QPixmap.fromImage(r[0]); self.cv.b = QPixmap.fromImage(r[1]); self.cv.x = x; self.cv.update()
        bg(lambda: (_img_small(po, 2000), _img_small(pn, 2000)), ok)


def show_compare(parent, old_rel, new_rel, nav=None, info=''):
    """背景讀兩張圖（照 EXIF 轉正、縮到 2000 內），讀好開對比視窗."""
    if ENG.gen_file(old_rel) is None or ENG.gen_file(new_rel) is None: QMessageBox.information(parent, '對比', '找不到原圖或結果圖'); return None
    d = CompareDlg(parent, nav); d.load(old_rel, new_rel, info); d.show(); return d


def _mg_pairs(N):
    P = [(-(-N // c), c) for c in range(1, N + 1) if N % c == 0]
    if len(P) <= 2 and N > 3: P += [(-(-N // c), c) for c in range(2, N) if N % c and -(-N // c) * c - N < c]
    return sorted(set(P), key=lambda x: x[1])


def mg_compose(imgs, C, ratio, fy, gap, lab, zh, zv, labels, cw=None):
    """▦ 合併（照 TikLive 截圖全覽）：imgs＝QImage 清單；ratio＝每格 高／寬；gap＝間距（以每格寬 300 為準，可以負數重疊）；fy＝裁切位置 −50～50；
    cw＝每格寬（None＝用第一張原寬）。回傳 QImage."""
    N = len(imgs); R = -(-N // C); nat = next((im for im in imgs if not im.isNull()), None)
    tw = float(cw or (nat.width() if nat else 1024)); th = tw * ratio; gs = gap * tw / 300.0
    W = C * tw + (C - 1) * gs; H = R * th + (R - 1) * gs; f = min(1.0, 16000 / max(W, H, 1), math.sqrt(120e6 / max(1.0, W * H)))
    tw, th, gs, W, H = tw * f, th * f, gs * f, W * f, H * f
    from PySide6.QtGui import QImage
    out = QImage(max(1, round(W)), max(1, round(H)), QImage.Format_RGB32); out.fill(QColor('#000'))
    z = lambda c, r: 1 + ((r if zv == 'd' else 500 - r) * 200) + (c if zh == 'r' else 199 - c)
    p = QPainter(out); p.setRenderHint(QPainter.SmoothPixmapTransform)
    for i in sorted(range(N), key=lambda i: z(i % C, i // C)):
        im = imgs[i]
        if im.isNull(): continue
        c, r = i % C, i // C; x, y = c * (tw + gs), r * (th + gs); s_ = max(tw / im.width(), th / im.height()); dw, dh = im.width() * s_, im.height() * s_
        p.save(); p.setClipRect(QRectF(x, y, tw, th)); p.drawImage(QRectF(x + (tw - dw) / 2, y + (th - dh) * (50 - fy) / 100, dw, dh), im); p.restore()
    if lab != 'x':
        fs = max(12, round(min(tw, th) * 0.06)); fnt = QFont(); fnt.setBold(True); fnt.setPixelSize(fs); p.setFont(fnt); fm = QFontMetrics(fnt)
        for i in range(N):
            c, r = i % C, i // C; x, y, w_, h_ = c * (tw + gs), r * (th + gs), tw, th
            if gs < 0:
                if zh == 'r' and c < C - 1: w_ = tw + gs
                elif zh == 'l' and c > 0: x -= gs; w_ = tw + gs
                if zv == 'd' and r < R - 1: h_ = th + gs
                elif zv == 'u' and r > 0: y -= gs; h_ = th + gs
            t = labels[i]; mw = fm.horizontalAdvance(t) + fs * 0.8; bx, by = x + fs * 0.3, y + h_ - fs * 1.6
            p.fillRect(QRectF(bx, by, mw, fs * 1.3), QColor(0, 0, 0, 140)); p.setPen(QColor('#fff')); p.drawText(QRectF(bx, by, mw, fs * 1.3), Qt.AlignCenter, t)
    p.end(); return out


class MergeDlg(QDialog):
    """▦ 合併這一批（照 TikLive 截圖全覽）：列×欄、⇄、每格比例（拉桿＝上下拉）、▲▼ 裁切位置、間距（負數重疊）、誰疊誰、每格下面顯示，存成一張原圖大小的 JPG."""
    def __init__(self, parent, batch, items):
        super().__init__(parent); self.b = batch; self.items = items; N = len(items); self.small = [None] * N
        self.setWindowTitle(f'▦ 合併：批量 #{batch}（{N} 張）'); self.resize(1100, 900)
        S = ENG.cfg.get('mg_' + str(batch)) or {}; P = _mg_pairs(N); c0 = math.ceil(math.sqrt(N))
        lay = tuple(S.get('lay') or min(P, key=lambda x: abs(x[1] - c0)))
        hasf = any(re.search(r'_f\d{4,}\.', x.get('img') or '') for _o, x in items)
        v = QVBoxLayout(self); r1 = QHBoxLayout(); v.addLayout(r1)
        self.ly = QComboBox()
        for rr, cc in P: self.ly.addItem(f'{rr}×{cc}' + (f'（空 {rr * cc - N}）' if rr * cc > N else ''), (rr, cc))
        self.ly.setCurrentIndex(max(0, self.ly.findData(lay))); b_sw = QPushButton('⇄ 欄列對調')
        r1.addWidget(QLabel('排列（列×欄）')); r1.addWidget(self.ly); r1.addWidget(b_sw)
        self.rt = QSlider(Qt.Horizontal); self.rt.setRange(15, 400); self.rt.setValue(int(S.get('ratio') or 0) or 100); self.rt_l = QLabel(''); b_nat = QPushButton('原圖比例')
        r1.addWidget(QLabel('　每格高÷寬')); r1.addWidget(self.rt, 1); r1.addWidget(self.rt_l); r1.addWidget(b_nat)
        r2 = QHBoxLayout(); v.addLayout(r2)
        self.fy = QSpinBox(); self.fy.setRange(-50, 50); self.fy.setValue(int(S.get('fy') or 0)); self.fy.setPrefix('▲▼ ')
        self.gap = QSpinBox(); self.gap.setRange(-80, 40); self.gap.setValue(int(S.get('gap', 2))); self.gap.setPrefix('間距 ')
        self.lab = QComboBox()
        for t_, k_ in [('編號', 'n')] + ([('第幾格', 'f')] if hasf else []) + [('不顯示', 'x')]: self.lab.addItem('每格下面：' + t_, k_)
        self.lab.setCurrentIndex(max(0, self.lab.findData(S.get('lab') or ('f' if hasf else 'n'))))
        self.zh = QComboBox(); self.zh.addItem('右搭左', 'r'); self.zh.addItem('左搭右', 'l'); self.zh.setCurrentIndex(max(0, self.zh.findData(S.get('zh', 'r'))))
        self.zv = QComboBox(); self.zv.addItem('下搭上', 'd'); self.zv.addItem('上搭下', 'u'); self.zv.setCurrentIndex(max(0, self.zv.findData(S.get('zv', 'd'))))
        for w_ in (self.fy, self.gap, self.lab, QLabel('疊：'), self.zh, self.zv): r2.addWidget(w_)
        r2.addWidget(note('（▲▼＝每格裁切位置往上／往下；間距負數＝疊在一起）')); r2.addStretch(1)
        self.pv = QLabel('讀圖中…'); self.pv.setAlignment(Qt.AlignCenter); self.pv.setStyleSheet('background:#000;border-radius:8px'); self.pv.setMinimumHeight(500)
        sa = QScrollArea(); sa.setWidgetResizable(True); sa.setWidget(self.pv); v.addWidget(sa, 1)
        r3 = QHBoxLayout(); v.addLayout(r3); self.inf = note(''); r3.addWidget(self.inf, 1); b_sv = QPushButton('💾 存成一張（原圖大小）'); r3.addWidget(b_sv)
        self.t = QTimer(self); self.t.setSingleShot(True); self.t.setInterval(60); self.t.timeout.connect(self.draw)
        for w_ in (self.fy, self.gap): w_.valueChanged.connect(lambda *_a: self.t.start())
        for w_ in (self.ly, self.lab, self.zh, self.zv): w_.currentIndexChanged.connect(lambda *_a: self.t.start())
        self.rt.valueChanged.connect(lambda *_a: (setattr(self, 'natr', False), self.t.start()))
        b_nat.clicked.connect(self._nat); b_sv.clicked.connect(self.save)
        b_sw.clicked.connect(lambda: (lambda d: self.ly.setCurrentIndex(self.ly.findData((d[1], d[0]))) if self.ly.findData((d[1], d[0])) >= 0 else self.win_msg('這個張數沒有對調後剛好排滿的排法'))(self.ly.currentData()))
        self.natr = not S.get('ratio')
        def got(L):
            self.small = L
            if self.natr: self._nat()
            else: self.draw()
        bg(lambda: [_img_small(ENG.gen_file(o), 600) if ENG.gen_file(o) is not None else QPixmap(1, 1).toImage() for o, _x in items], got)

    def win_msg(self, t): self.inf.setText(t)

    def _nat(self):
        im = next((x for x in self.small if x is not None and not x.isNull()), None)
        if im is None: return
        self.rt.blockSignals(True); self.rt.setValue(max(15, min(400, round(im.height() * 100 / max(1, im.width()))))); self.rt.blockSignals(False); self.natr = True; self.draw()

    def _labels(self):
        k = self.lab.currentData(); out = []
        for i, (_o, x) in enumerate(self.items):
            m = re.search(r'_f(\d{4,})\.', x.get('img') or '')
            out.append(f'第 {int(m.group(1))} 格' if k == 'f' and m else f'#{x["id"]}' if k == 'f' else str(i + 1))
        return out

    def _args(self):
        rr, cc = self.ly.currentData(); return dict(C=cc, ratio=self.rt.value() / 100, fy=self.fy.value(), gap=self.gap.value(), lab=self.lab.currentData(), zh=self.zh.currentData(), zv=self.zv.currentData(), labels=self._labels())

    def draw(self):
        if not self.small or self.small[0] is None: return
        A = self._args(); rr, cc = self.ly.currentData(); self.rt_l.setText(f'{A["ratio"]:.2f}' + ('（原圖）' if self.natr else ''))
        ENG.cfg.set('mg_' + str(self.b), {'lay': [rr, cc], 'ratio': 0 if self.natr else self.rt.value(), 'fy': A['fy'], 'gap': A['gap'], 'lab': A['lab'], 'zh': A['zh'], 'zv': A['zv']})
        Wv = max(300, self.pv.width() - 10); cw = max(20, (Wv - (cc - 1) * A['gap'] * 0) / cc)
        img = mg_compose(self.small, cw=cw, **A); self.pv.setPixmap(QPixmap.fromImage(img))
        self.inf.setText(f'{len(self.items)} 張 · {rr}×{cc} · 每格 高÷寬 {A["ratio"]:.2f}　（預覽是縮小的；存的是原圖大小）')

    def save(self):
        A = self._args(); rr, cc = self.ly.currentData()
        d = ENG.data / 'outputs' / 'merged'; d.mkdir(parents=True, exist_ok=True); dst = d / f'批量_{self.b}_{rr}x{cc}_{time.strftime("%H%M%S")}.jpg'
        paths = [ENG.gen_file(o) for o, _x in self.items]
        def work():
            from PySide6.QtGui import QImageReader
            L = []
            for p_ in paths:
                if p_ is None: L.append(QPixmap(1, 1).toImage()); continue
                r_ = QImageReader(str(p_)); r_.setAutoTransform(True); L.append(r_.read())
            im = mg_compose(L, **A)
            if not im.save(str(dst), 'JPG', 92): raise RuntimeError('存不了：' + str(dst))
            return im.width(), im.height()
        self.inf.setText('合成中…')
        bg(work, lambda wh: (self.inf.setText(f'✔ 存好了 {wh[0]}×{wh[1]}：{dst}'), QDesktopServices.openUrl(QUrl.fromLocalFile(str(d)))), lambda ex: QMessageBox.warning(self, '合併', str(ex)))

    def resizeEvent(self, e):
        super().resizeEvent(e); self.t.start()


class PeopleDlg(QDialog):
    """👤 人物庫：某人的照片存成編號（a01…）；提示詞寫編號 → 自動帶他的照片當參考圖."""
    def __init__(self, parent):
        super().__init__(parent); self.setWindowTitle('👤 人物庫'); self.resize(980, 640); v = QVBoxLayout(self)
        v.addWidget(note('把某個人的照片存成編號（a01、a02…）。提示詞寫到編號（例如「圖一女生與 a01 喝著咖啡」）就會自動帶他的照片當參考圖。'
                         '能用：GROK 改圖（帶 1 張，a01→圖二中的人）、H3 照片動起來（臉穩定）／參考生影片（每人帶 3 張）。照片 5～10 張、臉清楚、只有他一個人；第一張＝代表照。'))
        h = QHBoxLayout(); v.addLayout(h, 1)
        lv = QVBoxLayout(); h.addLayout(lv); self.lst = QListWidget(); self.lst.setFixedWidth(220); lv.addWidget(self.lst, 1)
        b_new = QPushButton('＋ 新增人物'); b_del = QPushButton('🗑 刪除這個人'); lv.addWidget(b_new); lv.addWidget(b_del)
        rv = QVBoxLayout(); h.addLayout(rv, 1)
        r1 = QHBoxLayout(); rv.addLayout(r1); self.code = QLabel(''); self.code.setStyleSheet('font-size:20px;font-weight:900'); self.nm = QLineEdit(); self.nm.setPlaceholderText('名字（可不填）')
        r1.addWidget(self.code); r1.addWidget(self.nm, 1)
        self.ph = QListWidget(); self.ph.setViewMode(QListWidget.IconMode); self.ph.setIconSize(QSize(140, 140)); self.ph.setResizeMode(QListWidget.Adjust); self.ph.setSelectionMode(QListWidget.ExtendedSelection)
        rv.addWidget(self.ph, 1)
        r2 = QHBoxLayout(); rv.addLayout(r2); b_add = QPushButton('📷 加照片（可多選）'); b_cv = QPushButton('⭐ 設成代表照'); b_dp = QPushButton('✕ 刪除選的照片')
        for b in (b_add, b_cv, b_dp): r2.addWidget(b)
        r2.addStretch(1)
        b_new.clicked.connect(self.new); b_del.clicked.connect(self.delp); b_add.clicked.connect(self.add); b_cv.clicked.connect(self.cover); b_dp.clicked.connect(self.delph)
        self.lst.currentRowChanged.connect(lambda *_a: self.show_one()); self.nm.editingFinished.connect(lambda: self.cur() and ENG.people_save(self.cur(), self.nm.text()) and self.load(self.cur()))
        self.load()

    def cur(self):
        it = self.lst.currentItem(); return it.data(Qt.UserRole) if it else None

    def load(self, pick=None):
        self.P = ENG.people_list(); self.lst.blockSignals(True); self.lst.clear()
        for p in self.P:
            it = QListWidgetItem(f'{p["code"]}  {p["name"]}（{len(p["photos"])} 張）'); it.setData(Qt.UserRole, p['code']); self.lst.addItem(it)
        self.lst.blockSignals(False)
        i = next((k for k, p in enumerate(self.P) if p['code'] == pick), 0 if self.P else -1); self.lst.setCurrentRow(i); self.show_one()

    def show_one(self):
        c = self.cur(); p = next((x for x in self.P if x['code'] == c), None); self.ph.clear()
        self.code.setText(c or '（還沒有人物）'); self.nm.setText((p or {}).get('name') or '')
        for k, f in enumerate((p or {}).get('photos') or []):
            it = QListWidgetItem(('⭐ 代表' if k == 0 else '')); it.setData(Qt.UserRole, f); self.ph.addItem(it)
            path = ENG.data / 'people' / c / f
            bg(lambda path=path: _img_small(path, 280), lambda im, it=it: it.setIcon(QIcon(QPixmap.fromImage(im))))

    def new(self):
        nm, ok = QInputDialog.getText(self, '新增人物', '名字（可不填，例如：小美）：')
        if ok: self.load(ENG.people_new(nm))

    def add(self):
        c = self.cur()
        if not c: QMessageBox.information(self, '人物庫', '先按「＋ 新增人物」'); return
        F, _ = QFileDialog.getOpenFileNames(self, f'加照片到 {c}', ldir('photo', Path.home() / 'Pictures'), '照片 (*.jpg *.jpeg *.png *.webp)'); sdir('photo', F)
        if not F: return
        bg(lambda: [ENG.people_add_photo(c, _photo_bytes(f, 1.5)) for f in F], lambda _r: self.load(c), lambda ex: QMessageBox.warning(self, '人物庫', str(ex)))

    def cover(self):
        c = self.cur(); it = self.ph.currentItem()
        if not c or not it: return
        p = next(x for x in self.P if x['code'] == c); f = it.data(Qt.UserRole); ENG.people_save(c, order=[f] + [x for x in p['photos'] if x != f]); self.load(c)

    def delph(self):
        c = self.cur(); S = [it.data(Qt.UserRole) for it in self.ph.selectedItems()]
        if not c or not S or QMessageBox.question(self, '人物庫', f'刪掉 {len(S)} 張照片？') != QMessageBox.Yes: return
        for f in S: ENG.people_del(c, f)
        self.load(c)

    def delp(self):
        c = self.cur()
        if not c or QMessageBox.question(self, '人物庫', f'刪除 {c} 和他所有照片？（搬到 people\\_old，可以救回）') != QMessageBox.Yes: return
        ENG.people_del(c); self.load()


class FramePicker(QDialog):
    """🎞 從影片挑格：拉時間軸、±1 ±10（鍵盤 ← → ，Shift 一次 10 格）找格子，Enter／按鈕選，最後用 FFmpeg 原尺寸取出來變成照片."""
    def __init__(self, parent, path):
        super().__init__(parent); self.path = path; self.fps = 30.0; self.N = 1; self.n = 0; self.sel = {}; self.done_cb = None; self._seq = 0
        self.setWindowTitle(f'🎞 從影片挑格：{Path(path).name}'); self.resize(980, 820); v = QVBoxLayout(self)
        self.inf = note('讀影片中…'); v.addWidget(self.inf)
        self.pv = QLabel('讀取中…'); self.pv.setAlignment(Qt.AlignCenter); self.pv.setMinimumHeight(420); self.pv.setStyleSheet('background:#000;border-radius:8px'); v.addWidget(self.pv, 1)
        self.lab = QLabel(''); self.lab.setAlignment(Qt.AlignCenter); self.lab.setStyleSheet('font-size:20px;font-weight:900'); v.addWidget(self.lab)
        self.sl = QSlider(Qt.Horizontal); self.sl.setRange(0, 0); v.addWidget(self.sl); self.sl.valueChanged.connect(self.go)
        r = QHBoxLayout(); v.addLayout(r)
        for t, d_ in (('⏪ −10', -10), ('◀ −1', -1), ('+1 ▶', 1), ('+10 ⏩', 10)):
            b = QPushButton(t); b.setFocusPolicy(Qt.NoFocus); b.clicked.connect(lambda _c=False, d_=d_: self.sl.setValue(self.n + d_)); r.addWidget(b)
        b_add = QPushButton('＋ 選這一格（Enter）'); b_add.setFocusPolicy(Qt.NoFocus); b_add.setStyleSheet('font-weight:800'); b_add.clicked.connect(self.add); r.addWidget(b_add)
        v.addWidget(note('已選（點一下跳回那一格；選了按 Delete 取消）：'))
        self.lst = QListWidget(); self.lst.setViewMode(QListWidget.IconMode); self.lst.setFlow(QListWidget.LeftToRight); self.lst.setWrapping(False)
        self.lst.setIconSize(QSize(96, 64)); self.lst.setFixedHeight(110); self.lst.setFocusPolicy(Qt.NoFocus); v.addWidget(self.lst)
        self.lst.itemClicked.connect(lambda it: self.sl.setValue(it.data(Qt.UserRole)))
        r2 = QHBoxLayout(); v.addLayout(r2); r2.addStretch(1); self.ok = QPushButton('✔ 加到照片'); self.ok.setEnabled(False); b_x = QPushButton('取消')
        r2.addWidget(self.ok); r2.addWidget(b_x); self.ok.clicked.connect(self.finish); b_x.clicked.connect(self.reject)
        self.t = QTimer(self); self.t.setSingleShot(True); self.t.setInterval(90); self.t.timeout.connect(self._show)
        bg(lambda: ENG.video_info(path), self._info, lambda ex: (self.inf.setText(f'<span style="color:#e74c3c">{esc_html(ex)}</span>'), self.pv.setText('讀不到')))

    def _info(self, I):
        self.fps = I['fps'] or 30.0; self.N = max(1, I['frames']); self.sl.setRange(0, self.N - 1)
        self.inf.setText(f'共 {self.N} 格 · 每秒 {self.fps:g} 格 · {I["dur"]:.1f} 秒 · {I["w"]}×{I["h"]}　（預覽是縮小的，取出來是原尺寸）'); self.go(0)

    def go(self, n):
        self.n = max(0, min(self.N - 1, int(n))); t = (self.n + 0.5) / self.fps
        self.lab.setText(f'第 {self.n} 格　<span style="font-size:13px;color:#8994a4">{int(t // 60)}:{t % 60:05.2f} ／ 共 {self.N} 格{"　✔ 已選" if self.n in self.sel else ""}</span>')
        self.lab.setTextFormat(Qt.RichText); self.t.start()

    def _show(self):
        self._seq += 1; seq = self._seq; n = self.n
        def put(b):
            if seq != self._seq: return
            pm = QPixmap(); pm.loadFromData(b); self._pm = (n, pm)
            self.pv.setPixmap(pm.scaled(self.pv.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        bg(lambda: ENG.video_frame(self.path, n, self.fps), put, lambda ex: seq == self._seq and self.pv.setText(f'這一格讀不到：{ex}'))

    def add(self):
        n = self.n
        if n in self.sel: self.win_msg(f'第 {n} 格已經選了'); return
        pm = self._pm[1] if getattr(self, '_pm', (None,))[0] == n else QPixmap()
        self.sel[n] = True; it = QListWidgetItem(QIcon(pm.scaled(96, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)) if not pm.isNull() else QIcon(), f'{n}'); it.setData(Qt.UserRole, n)
        R = sorted(self.sel); self.lst.insertItem(R.index(n), it); self._okt(); self.go(n)

    def win_msg(self, t): self.inf.setToolTip(t); QMessageBox.information(self, '挑格', t)

    def _okt(self):
        self.ok.setEnabled(bool(self.sel)); self.ok.setText(f'✔ 加到照片（{len(self.sel)} 張）' if self.sel else '✔ 加到照片')

    def keyPressEvent(self, e):
        k = e.key(); step = 10 if e.modifiers() & Qt.ShiftModifier else 1
        if k == Qt.Key_Left: self.sl.setValue(self.n - step)
        elif k == Qt.Key_Right: self.sl.setValue(self.n + step)
        elif k in (Qt.Key_Return, Qt.Key_Enter): self.add()
        elif k == Qt.Key_Delete:
            for it in self.lst.selectedItems() or ([self.lst.currentItem()] if self.lst.currentItem() else []):
                self.sel.pop(it.data(Qt.UserRole), None); self.lst.takeItem(self.lst.row(it))
            self._okt(); self.go(self.n)
        else: super().keyPressEvent(e)

    def finish(self):
        F = sorted(self.sel)
        if not F: return
        self.ok.setEnabled(False); self.ok.setText(f'取出 {len(F)} 格中…')
        def done(N):
            if self.done_cb and N: self.done_cb(N)
            self.accept()
        bg(lambda: ENG.video_extract(self.path, F), done, lambda ex: (QMessageBox.warning(self, '挑格', str(ex)), self._okt()))


# ============================================================ 📜 歷史紀錄：全部跑過的（搜尋、篩選、分頁、詳細、時間統計）
class HistPage(QWidget):
    PER = 50

    def __init__(self, win):
        super().__init__(); self.win = win; self.off = 0; self.rows = []; self.total = 0; self.icons = {}
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10)
        r = QHBoxLayout(); v.addLayout(r)
        self.q = QLineEdit(); self.q.setPlaceholderText('搜尋提示詞或 #編號'); self.st = QComboBox(); self.wfc = QComboBox()
        for t_, k_ in (('全部狀態', ''), ('✔ 完成', 'done'), ('✖ 失敗', 'fail'), ('⏹ 取消', 'stop'), ('⏳ 排隊', 'wait')): self.st.addItem(t_, k_)
        self.wfc.addItem('全部流程', ''); b_go = QPushButton('🔍 搜尋'); self.cnt = note('')
        self.vw = QComboBox()
        for t_, k_ in (('全部', ''), ('🙈 已隱藏', 'hidden'), ('🗑 回收桶', 'trash')): self.vw.addItem(t_, k_)
        r.addWidget(self.vw); self.vw.currentIndexChanged.connect(lambda *_a: (self.load(0), self._act_btns()))
        self.b_prev = QPushButton('◀ 上一頁'); self.b_next = QPushButton('下一頁 ▶')
        for w_ in (self.q, self.st, self.wfc, b_go, self.cnt, self.b_prev, self.b_next): r.addWidget(w_)
        r.setStretch(0, 1)
        self.q.returnPressed.connect(lambda: self.load(0)); b_go.clicked.connect(lambda: self.load(0))
        self.st.currentIndexChanged.connect(lambda *_a: self.load(0)); self.wfc.currentIndexChanged.connect(lambda *_a: self.load(0))
        self.b_prev.clicked.connect(lambda: self.load(max(0, self.off - self.PER))); self.b_next.clicked.connect(lambda: self.load(self.off + self.PER))
        sp = QSplitter(Qt.Vertical); v.addWidget(sp, 1)
        self.tb = QTableWidget(0, 10); self.tb.setHorizontalHeaderLabels(['#', '時間', '狀態', '流程', '提示詞', '參數', '運算', '全部', '模型', '來源'])
        self.tb.verticalHeader().setVisible(False); self.tb.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tb.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tb.setSelectionMode(QAbstractItemView.ExtendedSelection);   # Ctrl／Shift 可以選很多筆一起隱藏、刪除 self.tb.setIconSize(QSize(56, 56)); self.tb.verticalHeader().setDefaultSectionSize(60)
        for i, w in enumerate((90, 110, 80, 110, 300, 260, 70, 70, 80, 50)): self.tb.setColumnWidth(i, w)
        self.tb.itemSelectionChanged.connect(self.detail); self.tb.itemDoubleClicked.connect(lambda _i: self.act('cmp')); sp.addWidget(self.tb)
        dw = QWidget(); dh = QHBoxLayout(dw); dh.setContentsMargins(0, 6, 0, 0); sp.addWidget(dw)
        self.pv = QLabel(''); self.pv.setFixedSize(260, 260); self.pv.setAlignment(Qt.AlignCenter); self.pv.setStyleSheet('border:1px solid #2a3340;border-radius:8px'); dh.addWidget(self.pv)
        dv = QVBoxLayout(); dh.addLayout(dv, 1)
        self.info = QLabel('點上面一筆看詳細'); self.info.setWordWrap(True); self.info.setTextFormat(Qt.RichText); self.info.setTextInteractionFlags(Qt.TextSelectableByMouse); dv.addWidget(self.info, 1)
        rb = QHBoxLayout(); dv.addLayout(rb)
        for t_, a_ in (('⇆ 對比', 'cmp'), ('▶ 看／播放', 'open'), ('📂 打開資料夾', 'folder'), ('✎ 用這組設定', 'fill'), ('↻ 再跑一次', 'rerun'), ('✏ 拿結果再改', 'reuse')):
            b_ = QPushButton(t_); b_.clicked.connect(lambda _c=False, a_=a_: self.act(a_)); rb.addWidget(b_)
        b_bn = QPushButton('🔬 測速度'); b_bn.setToolTip('用這筆的原圖和提示詞，排一組速度測試（GROK INT8、Qwen 2.1 Turbo 各跑一張，比速度和畫質）'); b_bn.clicked.connect(self.bench); rb.addWidget(b_bn)
        b_up = QPushButton('✨ 放大'); b_up.setVisible(False)  # V0.1.78 放大功能收起來（只留兩個改圖流程）
        b_up.setToolTip('這筆的結果用 SeedVR2 放大 2 倍（影片就是 🎞 補幀：每兩格中間補一格）；第一次用會自動下載模型'); b_up.clicked.connect(self.post); rb.addWidget(b_up)
        self.star = QComboBox(); self.star.addItems(['☆ 打分數', '★ 1', '★★ 2', '★★★ 3', '★★★★ 4', '★★★★★ 5']); self.star.setToolTip('給這筆打分數（歷史紀錄網頁版可以看「⭐ 高分」）')
        self.star.activated.connect(self.vote); rb.addWidget(self.star)
        b_mg = QPushButton('▦ 合併這一批'); b_mg.setToolTip('同一次送出的批量（好幾張照片、影片挑的好幾格）：選列×欄、拉比例，合成一張'); b_mg.clicked.connect(self.merge); rb.addWidget(b_mg)
        b_sv = QPushButton('⬇ 存選取的結果…'); b_sv.setToolTip('Ctrl／Shift 選好幾筆，把結果檔複製到你選的資料夾'); b_sv.clicked.connect(self.save_sel); rb.addWidget(b_sv)
        rb.addStretch(1)
        rh = QHBoxLayout(); dv.addLayout(rh); self.hbtn = {}
        for t_, a_ in (('🙈 隱藏', 'hide'), ('👁 取消隱藏', 'unhide'), ('🗑 刪除（放回收桶）', 'del'), ('↩ 還原', 'restore'), ('永久刪除', 'purge')):
            b_ = QPushButton(t_); b_.clicked.connect(lambda _c=False, a_=a_: self.hact(a_)); rh.addWidget(b_); self.hbtn[a_] = b_
        rh.addWidget(note('（可以 Ctrl／Shift 選很多筆）')); rh.addStretch(1); self._act_btns()
        self.sb = QPushButton('▸ 📊 時間統計（每種設定平均跑多久，拿來預估時間）'); self.sb.setCheckable(True); self.sb.setStyleSheet('text-align:left;font-weight:800;border:0;background:transparent')
        v.addWidget(self.sb); self.stt = QTableWidget(0, 7); self.stt.setHorizontalHeaderLabels(['流程', '設定', '次數', '熱（中位數）', '有載入模型', '全部（中位數）', '輸出大小'])
        self.stt.verticalHeader().setVisible(False); self.stt.setEditTriggers(QAbstractItemView.NoEditTriggers); self.stt.horizontalHeader().setStretchLastSection(True)
        for i, w in enumerate((120, 420, 60, 110, 110, 110)): self.stt.setColumnWidth(i, w)
        self.stt.setMinimumHeight(160); self.stt.hide(); v.addWidget(self.stt)
        self.sb.toggled.connect(lambda on: (self.stt.setVisible(on), self.sb.setText(('▾' if on else '▸') + ' 📊 時間統計（每種設定平均跑多久，拿來預估時間）'), on and self.stats()))

    def showEvent(self, e):
        super().showEvent(e); self.load(self.off)

    def _act_btns(self):
        v = self.vw.currentData() or ''
        show = {'': ('hide', 'del'), 'hidden': ('unhide', 'del'), 'trash': ('restore', 'purge')}[v]
        for k, b in self.hbtn.items(): b.setVisible(k in show)

    def sel_rows(self):
        return [self.rows[i] for i in sorted({ix.row() for ix in self.tb.selectedIndexes()}) if 0 <= i < len(self.rows)]

    def hact(self, a):
        R = self.sel_rows()
        if not R: self.win.msg('先點要處理的紀錄（Ctrl／Shift 可以選很多筆）'); return
        ids = [j['id'] for j in R]; nm = {'hide': '隱藏', 'unhide': '取消隱藏', 'del': '刪除（放進回收桶，30 天內可以還原）', 'restore': '還原', 'purge': '永久刪除（檔案真的刪掉，不能還原）'}[a]
        if a in ('del', 'purge') and QMessageBox.question(self, '歷史紀錄', f'{nm}：{len(ids)} 筆？') != QMessageBox.Yes: return
        bg(lambda: ENG.gen_hist_act(ids, a), lambda n: (self.win.msg(f'✔ {nm.split("（")[0]} {n} 筆' + (f'（{len(ids) - n} 筆還在跑／排隊，先取消）' if a == 'del' and n < len(ids) else '')), self.load(0)))

    def load(self, off=0):
        self.off = off; q, st, wf = self.q.text().strip(), self.st.currentData() or '', self.wfc.currentData() or ''
        vw = self.vw.currentData() or ''
        bg(lambda: ENG.gen_history(q, st, wf, off, self.PER, vw), self._got)

    def _got(self, H):
        self.rows = H['rows']; self.total = H['total']; cur = self.wfc.currentData() or ''
        self.wfc.blockSignals(True); self.wfc.clear(); self.wfc.addItem('全部流程', '')
        for w in H.get('wfs') or []: self.wfc.addItem(w, w)
        self.wfc.setCurrentIndex(max(0, self.wfc.findData(cur))); self.wfc.blockSignals(False)
        self.cnt.setText(f'共 {self.total} 筆　第 {self.off + 1}～{self.off + len(self.rows)} 筆'); self.b_prev.setEnabled(self.off > 0); self.b_next.setEnabled(self.off + len(self.rows) < self.total)
        self.tb.setRowCount(len(self.rows))
        for i, j in enumerate(self.rows):
            nm, col = GEN_ST.get(j['state'], (j['state'], None))
            vals = (f'#{j["id"]}' + (f'  📚{j["batch"]}' if j.get('batch') else ''), time.strftime('%m/%d %H:%M', time.localtime(j['t'])), nm, j['wf'], j['prompt'], j.get('brief', ''),
                    fmt_t(j['run_s']) if j.get('run_s') else '', fmt_t(j['dur']) if j.get('dur') else '', {1: '有載入', 0: '熱'}.get(j.get('cold'), ''),
                    j['src'] + (lambda m: f' 🎞{int(m.group(1))}' if m else '')(re.search(r'_f(\d{4,})\.\w+$', j.get('img') or '')))
            for c_, val in enumerate(vals): self.tb.setItem(i, c_, _ti(val, val, None, col if c_ == 2 else None))
            rel = j['outs'][0] if j['outs'] else (((j.get('tins') or {}).get('inputs/' + j['img']) or ('inputs/' + j['img'])) if j.get('img') else '')
            if rel and not ENG.is_video_name(rel): self._icon(i, rel)

    def _icon(self, row, rel):
        def put(ic, row=row, rel=rel):
            self.icons[rel] = ic; it = self.tb.item(row, 0)
            if it is not None and row < len(self.rows): it.setIcon(ic)
        if rel in self.icons: put(self.icons[rel]); return
        p = ENG.gen_file(rel)
        if p is not None: bg(lambda: _img_small(p, 120), lambda im: put(QIcon(QPixmap.fromImage(im))))

    def cur(self):
        r = self.tb.currentRow(); return self.rows[r] if 0 <= r < len(self.rows) else None

    def detail(self):
        j = self.cur()
        if not j: return
        P = j.get('params') or {}
        ps = '<br>'.join(f'<span style="color:#8994a4">{esc_html(k)}</span>　{esc_html(v)}' for k, v in list(P.items())[:60])
        tt = lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x)) if x else '—'
        self.info.setText(f"<b>#{j['id']}　{esc_html(GEN_ST.get(j['state'], (j['state'],))[0])}</b>　{esc_html(j['wf'])}　{esc_html(j['src'])}<br>"
                          f"<b>提示詞：</b>{esc_html(j['prompt'] or '（沒有）')}" + (f"<br><b>負面：</b>{esc_html(j['neg'])}" if j.get('neg') else '') +
                          f"<br>排進來 {tt(j['t'])}　開始運算 {tt(j.get('t_start'))}　結束 {tt(j.get('t1'))}"
                          f"<br>⏱ 運算 {fmt_t(j.get('run_s') or 0)}　全部 {fmt_t(j.get('dur') or 0)}　{ {1: '有載入模型（冷啟動）', 0: '模型已在記憶體（熱）'}.get(j.get('cold'), '') }"
                          + (f"<br>⏱ 時間花在：{j.get('pbrief')}" if j.get('pbrief') else '') + ""
                          f"<br>種子 {j['seed']}　照片 {j.get('in_w') or '?'}×{j.get('in_h') or '?'}　結果 {j.get('out_w') or '?'}×{j.get('out_h') or '?'}　{len(j['outs'])} 張"
                          + (f"<br><span style='color:#ff4d6d'>{esc_html(j['msg'])}</span>" if j['state'] == 'fail' else '') + f"<br><small>{ps}</small>")
        rel = j['outs'][0] if j['outs'] else (('inputs/' + j['img']) if j.get('img') else ''); p = ENG.gen_file(rel) if rel else None
        if p is not None and ENG.is_video_name(p.name): self.pv.setText(f'🎬 影片\n{p.name}\n{fmt_b(p.stat().st_size)}\n（點兩下播放）'); self.pv.setWordWrap(True); return
        if p is None: self.pv.setText('（沒有圖）'); return
        bg(lambda: _img_small(p, 256), lambda im: self.pv.setPixmap(QPixmap.fromImage(im)))

    def _media_step(self, k):
        """播放視窗看完這筆的檔：往上／下找下一筆有結果的紀錄接著看."""
        r = self.tb.currentRow() + k
        while 0 <= r < len(self.rows):
            j = self.rows[r]
            if j.get('outs'):
                self.tb.selectRow(r); self.tb.setCurrentCell(r, 0); F = [ENG.gen_file(o) for o in j['outs']]
                MediaDlg.open(self, F, f'#{j["id"]} {j.get("prompt", "")[:30]}', self._media_step, 0 if k > 0 else len(F) - 1); return True
            r += k
        return False

    def _cmp_info(self, j):
        r = self.tb.currentRow(); m = re.search(r'_f(\d{4,})\.\w+$', j.get('img') or '')
        return f'#{j["id"]}　第 {self.off + r + 1}／{self.total} 筆' + (f'　🎞 第 {int(m.group(1))} 格' if m else '')

    def _cmp_step(self, k, dlg):
        """對比視窗按 ← →：表格往上／下找下一筆有原圖＋結果圖的，跟著選起來."""
        r = self.tb.currentRow() + k
        while 0 <= r < len(self.rows):
            j = self.rows[r]
            if j.get('img') and j.get('outs') and not ENG.is_video_name(j['outs'][0]):
                self.tb.selectRow(r); self.tb.setCurrentCell(r, 0); dlg.load('inputs/' + j['img'], j['outs'][0], self._cmp_info(j)); return
            r += k
        dlg.lab.setText(('已經是這一頁的最後一筆（下一頁按「下一頁 ▶」）' if k > 0 else '已經是這一頁的第一筆') + '　← → 看上一筆／下一筆')

    def post(self):
        j = self.cur()
        if not j or not j.get('outs'): self.win.msg('先點一筆有結果的紀錄'); return
        kind = 'interp' if ENG.is_video_name(j['outs'][0]) else 'upscale'
        bg(lambda: ENG.gen_post(j['id'], 0, kind), lambda r: self.win.msg(r[1] + '，做好會出現在這裡'), lambda ex: QMessageBox.warning(self, '再加工', str(ex)))

    def vote(self, i):
        j = self.cur()
        if not j: return
        ENG.cmp_vote(j['id'], i); self.win.msg(f'#{j["id"]} ' + ('清掉分數' if not i else '★' * i))

    def bench(self):
        j = self.cur()
        if not j or not j.get('img'): self.win.msg('先點一筆有原圖的 GROK 紀錄'); return
        if QMessageBox.question(self, '🔬 測速度', '用這張圖和提示詞排一組速度測試？\n（GROK INT8、Qwen 2.1 Turbo 各跑一張；同一個種子，每個模型先暖機；大約 5～10 分鐘）') != QMessageBox.Yes: return
        bg(lambda: ENG.gen_benchmark(j['img'], j['prompt']), lambda r: self.win.msg(f'🔬 排了 {len(r[0])} 個測速工作{r[1]}，做完看這一批的「運算」欄和下面的時間分佈'),
           lambda ex: QMessageBox.warning(self, '測速度', str(ex)))

    def merge(self):
        j = self.cur()
        if not j or not j.get('batch'): self.win.msg('先點一筆「📚 批量」的紀錄（同一次送出好幾張的）'); return
        R = ENG.gen_batch_rows(j['batch']); I = [(o, x) for x in R for o in x.get('outs') or [] if not ENG.is_video_name(o)]
        if len(I) < 2: self.win.msg('這一批做好的圖還不到兩張'); return
        MergeDlg(self, j['batch'], I).show()

    def save_sel(self):
        O = [o for j in self.sel_rows() for o in j.get('outs') or []]
        if not O: self.win.msg('先選有結果的紀錄（Ctrl／Shift 可以選很多筆）'); return
        d = sdir('save', QFileDialog.getExistingDirectory(self, f'把 {len(O)} 個結果檔存到…', ldir('save', Path.home() / 'Pictures')))
        if not d: return
        def work():
            n = 0
            for o in O:
                p = ENG.gen_file(o)
                if p is None: continue
                dst = Path(d) / p.name; k = 1
                while dst.exists(): dst = Path(d) / f'{p.stem}_{k}{p.suffix}'; k += 1
                shutil.copy2(p, dst); n += 1
            return n
        bg(work, lambda n: (self.win.msg(f'✔ 存了 {n} 個檔到 {d}'), QDesktopServices.openUrl(QUrl.fromLocalFile(d))))

    def act(self, a):
        j = self.cur()
        if not j: self.win.msg('先點一筆紀錄'); return
        if a == 'cmp':
            if j['outs'] and ENG.is_video_name(j['outs'][0]): a = 'open'
            elif j.get('img') and j['outs']: self.cmpd = show_compare(self, 'inputs/' + j['img'], j['outs'][0], self._cmp_step, self._cmp_info(j)); return
            else: self.win.msg('這筆沒有原圖或結果圖'); return
        if a == 'open':
            if not j['outs']: self.win.msg('這筆沒有結果圖'); return
            MediaDlg.open(self, [ENG.gen_file(o) for o in j['outs']], f'#{j["id"]} {j.get("prompt", "")[:30]}', self._media_step); return   # 主程式裡直接看／播
        if a == 'folder':
            for o in j['outs'][:1]:
                p = ENG.gen_file(o)
                if p is not None: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p.parent)))
            if not j['outs']: self.win.msg('這筆沒有結果圖')
            return
        G = self.win.gen
        if a == 'fill':
            self.win.nav.setCurrentRow(0); G.jobs = [j] + [x for x in G.jobs if x['id'] != j['id']]
            G.prompt.setPlainText(j.get('prompt', '')); G.neg.setPlainText(j.get('neg', ''))
            if j.get('img'): G.set_img(j['img'])
            for k_, x_ in enumerate(j.get('imgs') or []):
                if k_: G.slot_imgs[k_] = [x_]; G._slot_show(k_)
            G._ov_set(dict(j.get('params') or {}), j.get('wf')); i = G.wf.findText(j.get('wf', ''))
            if i >= 0:
                if i == G.wf.currentIndex(): G.wf_info()
                else: G.wf.setCurrentIndex(i)
            self.win.msg('已填回：照片、提示詞、流程和參數'); return
        fn = {'rerun': lambda: ENG.gen_rerun(j['id'], '電腦'), 'reuse': lambda: ENG.gen_reuse(j['id'])}[a]
        def done(r):
            if a == 'reuse': self.win.nav.setCurrentRow(0); G.set_img(r); self.win.msg('✔ 換成這張結果了，打新的提示詞再按開始')
            else: self.win.msg('排好了'); self.load(0)
        bg(fn, done, lambda ex: QMessageBox.warning(self, '歷史紀錄', str(ex)))

    def stats(self):
        def got(S):
            self.stt.setRowCount(len(S))
            for i, x in enumerate(S):
                vals = (x['wf'], x['brief'], str(x['n']), (fmt_t(x['warm']) + f'（{x["warm_n"]} 次）') if x['warm'] is not None else '—',
                        (fmt_t(x['cold']) + f'（{x["cold_n"]} 次）') if x['cold'] is not None else '—', fmt_t(x['dur']) if x['dur'] else '', x['size'])
                for c_, val in enumerate(vals): self.stt.setItem(i, c_, _ti(val))
        bg(ENG.gen_stats, got)


def make_icons(src):
    """背景執行緒：任何圖片 → Data\\\\icon_512.png、icon_192.png、icon.ico（置中、透明底）."""
    from PySide6.QtGui import QImage, QImageReader
    r = QImageReader(str(src)); r.setAutoTransform(True); im = r.read()
    if im.isNull(): raise RuntimeError('讀不到這張圖：' + r.errorString())
    out = {}
    for n in (512, 192, 256):
        sc = im.scaled(n, n, Qt.KeepAspectRatio, Qt.SmoothTransformation); c = QImage(n, n, QImage.Format_ARGB32); c.fill(Qt.transparent)
        p = QPainter(c); p.drawImage((n - sc.width()) // 2, (n - sc.height()) // 2, sc); p.end(); out[n] = c
    out[512].save(str(ENG.data / 'icon_512.png'), 'PNG'); out[192].save(str(ENG.data / 'icon_192.png'), 'PNG')
    if not out[256].save(str(ENG.data / 'icon.ico'), 'ICO'): out[256].save(str(ENG.data / 'icon.ico.png'), 'PNG')
    ENG.log.w(f'換程式圖示：{src}'); return True


# ============================================================ 🖥 後台狀態（總控制＋最近的工作）
class BgPage(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win; self.ct_sig = None; self.ct_w = {}
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10)
        g = QGroupBox('⏯ 總控制：每一項都可以暫停／繼續／立刻停、調先後順序（電腦太忙時從最下面的先讓路）'); gv = QVBoxLayout(g); v.addWidget(g)
        self.ct = QTableWidget(0, 9); self.ct.setHorizontalHeaderLabels(['順序', '項目', '狀態', '總進度', '停在／最近在做', '', '', '', ''])
        self.ct.verticalHeader().setVisible(False); self.ct.setEditTriggers(QAbstractItemView.NoEditTriggers); self.ct.setSelectionMode(QAbstractItemView.NoSelection)
        for i, w in enumerate((50, 170, 120, 200, 260, 80, 90, 36, 36)): self.ct.setColumnWidth(i, w)
        self.ct.setMinimumHeight(140); gv.addWidget(self.ct)
        r = QHBoxLayout(); gv.addLayout(r)
        ba = QPushButton('⏸ 全部暫停'); bb = QPushButton('▶ 全部繼續（照順序慢慢加）'); self.guard = QCheckBox('電腦太忙自動讓路'); self.cmax = QSpinBox(); self.cmax.setRange(50, 100); self.cmax.setPrefix('CPU 超過 '); self.cmax.setSuffix('%')
        self.ramp = QSpinBox(); self.ramp.setRange(0, 300); self.ramp.setPrefix('慢慢加速：每 '); self.ramp.setSuffix(' 秒多開 1 個')
        for w_ in (ba, bb, self.guard, self.cmax, self.ramp): r.addWidget(w_)
        r.addStretch(1)
        self.glog = QLabel(''); self.glog.setObjectName('muted'); self.glog.setWordWrap(True); gv.addWidget(self.glog)
        ba.clicked.connect(lambda: (ENG.bg_all(True), self.refresh())); bb.clicked.connect(lambda: (ENG.bg_all(False), self.refresh()))
        self.guard.toggled.connect(lambda on: ENG.cfg.set('cpu_guard', bool(on))); self.cmax.valueChanged.connect(lambda x: ENG.cfg.set('cpu_max', int(x)))
        self.ramp.valueChanged.connect(lambda x: ENG.cfg.set('bg_ramp_sec', int(x)))
        g2 = QGroupBox('最近的工作'); g2v = QVBoxLayout(g2); v.addWidget(g2, 1)
        self.tb = QTableWidget(0, 5); self.tb.setHorizontalHeaderLabels(['時間', '工作', '狀態', '進度', '結果']); self.tb.verticalHeader().setVisible(False)
        self.tb.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tb.horizontalHeader().setStretchLastSection(True)
        for i, w in enumerate((80, 320, 80, 70)): self.tb.setColumnWidth(i, w)
        self.tb.setMinimumHeight(220); g2v.addWidget(self.tb)
        self.load_guard(); self.tm = QTimer(self); self.tm.timeout.connect(self.refresh); self.tm.start(1000)

    def load_guard(self):
        for w_, val in ((self.guard, ENG.cfg.get('cpu_guard') is not False), (self.cmax, int(ENG.cfg.get('cpu_max') or 90)), (self.ramp, int(ENG.cfg.get('bg_ramp_sec') if ENG.cfg.get('bg_ramp_sec') is not None else 20))):
            w_.blockSignals(True); (w_.setChecked(val) if isinstance(w_, QCheckBox) else w_.setValue(val)); w_.blockSignals(False)

    def refresh(self):
        if not self.isVisible(): return
        bg(lambda: (ENG.bg_view(), ENG.tasks_list()[-80:]), self._got)

    def _got(self, r):
        V, T = r; L = V['kinds']; sig = tuple(k['k'] for k in L)
        if sig != self.ct_sig:
            self.ct_sig = sig; self.ct.setRowCount(len(L)); self.ct_w = {}
            for i, k in enumerate(L):
                pb = QProgressBar(); pb.setRange(0, 1000); pb.setTextVisible(True); self.ct.setCellWidget(i, 3, pb)
                bp = QPushButton(); bs = QPushButton('⏹ 立刻停'); bu = QPushButton('↑'); bd = QPushButton('↓')
                for c_, w_ in ((5, bp), (6, bs), (7, bu), (8, bd)): self.ct.setCellWidget(i, c_, w_)
                kk = k['k']
                bp.clicked.connect(lambda _c=False, kk=kk: (ENG.bg_set_pause(kk, not ENG.bg_pause.get(kk)), self.refresh()))
                bs.clicked.connect(lambda _c=False, kk=kk: (QMessageBox.question(self, '立刻停', '正在做的也停掉，放回排隊？') == QMessageBox.Yes) and (ENG.bg_stop_now(kk), self.refresh()))
                bu.clicked.connect(lambda _c=False, kk=kk: (ENG.bg_move(kk, -1), self.refresh())); bd.clicked.connect(lambda _c=False, kk=kk: (ENG.bg_move(kk, 1), self.refresh()))
                self.ct_w[i] = (pb, bp, bs)
        STN = {'run': ('▶ 進行中', '#45d483'), 'idle': ('— 沒事', '#7f8a99'), 'pause': ('⏸ 暫停中', '#ff4d6d'), 'hold': ('⚖ 讓路中', '#f0ad4e')}
        for i, k in enumerate(L):
            nm, col = STN.get(k['state'], (k['state'], None))
            if k.get('ramp'): nm += f'（慢慢加速 {k["ramp"]}）'
            if k.get('slow'): nm += f'（降速：最多 {k["slow"]} 個）'
            last = (('⏸ 停在：' if k['state'] == 'pause' else '') + k['last']) if k['last'] else ''
            if k.get('held'): last = k['held'] + ('　' + last if last else '')
            for c_, val in enumerate((str(k['prio']), f"{k['icon']} {k['name']}", nm, None, last)):
                if val is None: continue
                it = self.ct.item(i, c_)
                if it is None or it.text() != val: self.ct.setItem(i, c_, _ti(val, val, None, col if c_ == 2 else None))
            w3 = self.ct_w.get(i)
            if w3 is not None:
                bar_, bpz, bsz = w3; bar_.setVisible(k['pct'] is not None)
                if k['pct'] is not None: bar_.setValue(int(k['pct'] * 10)); bar_.setFormat(f"{k['pct']:.1f}%（{k['done']:,}／{k['total']:,}）")
                bpz.setText('▶ 繼續' if k['state'] == 'pause' else '⏸ 暫停'); bsz.setEnabled(bool(k['running']))
        self.glog.setText(f"CPU 現在 {V['cpu']:.0f}%　" + ('　'.join(V['log'][:3]) if V.get('log') else '（自動讓路的紀錄會顯示在這裡）'))
        T = list(reversed(T)); self.tb.setRowCount(len(T)); SC = {'run': '#4dc9ff', 'done': '#45d483', 'fail': '#ff4d6d', 'stop': '#f0ad4e'}
        for i, t in enumerate(T):
            vals = (time.strftime('%H:%M:%S', time.localtime(t['t0'])), t['title'], t['state'], f"{t['pct']}%" if t.get('pct') is not None and t['state'] == 'run' else '', t.get('msg') or '')
            for j, val in enumerate(vals):
                it = self.tb.item(i, j)
                if it is None or it.text() != str(val): self.tb.setItem(i, j, _ti(val, val, None, SC.get(t['state']) if j == 2 else None))


# ============================================================ ⚙ 設定
class SetPage(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10)
        g = QGroupBox('一般'); f = QFormLayout(g); v.addWidget(g)
        self.tray = QCheckBox('按右上角 X：縮到右下角（背景繼續做；托盤右鍵「結束」才真的關）'); self.cover = QCheckBox('打開程式先顯示封面（不露出內容）')
        self.restore = QCheckBox('從右下角叫回來時先顯示封面'); self.idle = QSpinBox(); self.idle.setRange(0, 240); self.idle.setSuffix(' 分鐘沒動作回封面（0＝不要）')
        self.autor = QCheckBox('閃退自動重開（看門狗；10 分鐘內閃退 3 次就先不重開）'); self.frz = QSpinBox(); self.frz.setRange(1, 30); self.frz.setSuffix(' 秒（畫面卡超過就記到 ui_freeze_log.txt）')
        for w_ in (self.tray, self.cover, self.restore, self.idle, self.autor, self.frz): f.addRow(w_)
        self._web_box(v)
        gi = QGroupBox('🖼 程式圖示'); ri = QHBoxLayout(gi); v.addWidget(gi)
        self.ic_l = QLabel(); self.ic_l.setFixedSize(48, 48); ri.addWidget(self.ic_l); b_ic = QPushButton('選圖片…'); b_ir = QPushButton('還原預設'); ri.addWidget(b_ic); ri.addWidget(b_ir)
        ri.addWidget(note('視窗、右下角托盤、手機 App 的圖示（PNG／JPG／ICO 都可以，正方形最好）。手機已經安裝的 App 要移除再安裝一次才會換。桌面捷徑／EXE 的圖示要重新跑 BUILD_AND_INSTALL.bat。'), 1)
        b_ic.clicked.connect(self._icon_pick); b_ir.clicked.connect(self._icon_reset); self._icon_show()
        g3 = QGroupBox('資料夾'); r3 = QHBoxLayout(g3); v.addWidget(g3)
        for t_, d_ in (('📂 程式資料夾', ROOT), ('📂 Data（設定、資料庫）', ROOT / 'Data'), ('📂 LOG', ROOT / 'LOG'), ('📂 UPDATE（更新包）', ROOT / 'UPDATE')):
            b_ = QPushButton(t_); b_.clicked.connect(lambda _c=False, d_=d_: (Path(d_).mkdir(exist_ok=True), QDesktopServices.openUrl(QUrl.fromLocalFile(str(d_))))); r3.addWidget(b_)
        r3.addStretch(1)
        v.addStretch(1); self.load()
        self.tray.toggled.connect(lambda on: ENG.cfg.set('close_to_tray', bool(on))); self.cover.toggled.connect(lambda on: ENG.cfg.set('cover_on_start', bool(on)))
        self.restore.toggled.connect(lambda on: ENG.cfg.set('cover_on_restore', bool(on))); self.idle.valueChanged.connect(lambda x: ENG.cfg.set('cover_idle_min', int(x)))
        self.autor.toggled.connect(lambda on: ENG.cfg.set('auto_restart', bool(on))); self.frz.valueChanged.connect(lambda x: ENG.cfg.set('freeze_log_s', float(x)))

    def load(self):
        for w_, val in ((self.tray, bool(ENG.cfg.get('close_to_tray'))), (self.cover, ENG.cfg.get('cover_on_start') is not False), (self.restore, bool(ENG.cfg.get('cover_on_restore'))),
                        (self.idle, int(ENG.cfg.get('cover_idle_min') or 0)), (self.autor, ENG.cfg.get('auto_restart') is not False), (self.frz, int(float(ENG.cfg.get('freeze_log_s') or 2)))):
            w_.blockSignals(True); (w_.setChecked(val) if isinstance(w_, QCheckBox) else w_.setValue(val)); w_.blockSignals(False)

    def _icon_show(self):
        try: self.ic_l.setPixmap(app_icon().pixmap(48, 48))
        except Exception: pass

    def _icon_apply(self):
        ic = app_icon(); W = self.win; W.icon = ic; W.setWindowIcon(ic); QApplication.instance().setWindowIcon(ic)
        if getattr(W, 'tray', None): W.tray.setIcon(ic)
        self._icon_show()

    def _icon_pick(self):
        p, _ = QFileDialog.getOpenFileName(self, '選程式圖示', ldir('icon', Path.home() / 'Pictures'), '圖片 (*.png *.jpg *.jpeg *.ico *.webp *.bmp *.svg)'); sdir('icon', p)
        if p: bg(lambda: make_icons(p), lambda _r: (self._icon_apply(), self.win.msg('✔ 圖示換好了')), lambda ex: QMessageBox.warning(self, '程式圖示', str(ex)))

    def _icon_reset(self):
        for n in ('icon_512.png', 'icon_192.png', 'icon.ico', 'icon.ico.png'):
            try: (ENG.data / n).unlink()
            except Exception: pass
        ENG.log.w('程式圖示還原預設'); self._icon_apply(); self.win.msg('圖示還原成預設')

    # ---------- 📱 手機網頁
    def _web_box(self, v):
        g = QGroupBox('📱 手機網頁（用手機遙控，透過 Tailscale）'); f = QFormLayout(g); v.addWidget(g)
        self.web_on = QCheckBox('開啟手機網頁'); self.web_port = QSpinBox(); self.web_port.setRange(1025, 64000); self.web_port.setValue(int(ENG.cfg.get('web_port') or BRAND['web_port']))
        self.web_hp = QLabel(''); self.web_hp.setObjectName('muted'); rp = QHBoxLayout(); rp.addWidget(self.web_port); rp.addWidget(self.web_hp, 1)
        self.web_pin = QLineEdit(); self.web_pin.setMaxLength(20); self.web_pin.setPlaceholderText('自己設 PIN：4～20 個字，數字、英文都可以，不能有空白')
        self.web_pin_l = QLabel(''); rpin = QHBoxLayout(); rpin.addWidget(self.web_pin, 1); rpin.addWidget(self.web_pin_l)
        self.web_lan = QCheckBox('也允許用 Tailscale IP／區網直接連 http（不能安裝成 App；不建議）')
        rb = QHBoxLayout(); b_app = QPushButton('📱 手機 App（Tailscale HTTPS）'); b_app.setObjectName('start'); b_copy = QPushButton('🔗 複製網址'); b_off = QPushButton('關掉 Tailscale 上的這個埠'); b_out = QPushButton('登出所有手機')
        for b_ in (b_app, b_copy, b_off, b_out): rb.addWidget(b_)
        rb.addStretch(1); self.web_st = QLabel(''); self.web_st.setWordWrap(True); self.web_st.setTextFormat(Qt.RichText); self.web_st.setTextInteractionFlags(Qt.TextSelectableByMouse)
        f.addRow(self.web_on); f.addRow('本機埠', rp); f.addRow('PIN', rpin); f.addRow(self.web_lan); f.addRow(rb); f.addRow(self.web_st)
        f.addRow(note('跟你的其他程式錯開、不會互相蓋掉：每個程式在 Tailscale 上用自己的 HTTPS 埠＝本機埠 + 1000（TikLive 用 443、VideoSift 9461…）。'
                      '只設定／關掉自己的埠，不碰別人的、不會 reset。每個程式的本機埠也要不一樣（brand.json 的 web_port）。'))
        self.web_on.setChecked(bool(ENG.cfg.get('web_on'))); self.web_lan.setChecked(bool(ENG.cfg.get('web_lan'))); self._pin_label()
        self.web_on.toggled.connect(lambda on: (ENG.cfg.set('web_on', bool(on)), web_apply(), self._web_status()))
        self.web_lan.toggled.connect(lambda on: (ENG.cfg.set('web_lan', bool(on)), web_apply(), self._web_status()))
        self.web_port.editingFinished.connect(self._port_changed); self.web_pin.editingFinished.connect(self._pin_save)
        b_app.clicked.connect(self._web_app); b_copy.clicked.connect(self._web_copy); b_off.clicked.connect(self._web_off)
        b_out.clicked.connect(lambda: (ENG.cfg.set('web_tokens', []), self.win.msg('所有手機都登出了，下次要重新輸入 PIN')))
        self._ts = {}; self._web_status(True)

    def _pin_label(self): self.web_pin_l.setText('🔒 已設定' if ENG.cfg.get('web_pin_hash') else '<span style="color:#ffb02e">還沒設 PIN</span>')

    def _pin_save(self):
        pin = self.web_pin.text().strip()
        if not pin: return
        if not web.pin_ok_format(pin): self.web_pin_l.setText('<span style="color:#ff5d6c">4～20 個字、不能有空白</span>'); return
        salt = web.rand_hex(8); ENG.cfg.set('web_pin_salt', salt); ENG.cfg.set('web_pin_hash', web.pin_hash(pin, salt)); self.web_pin.clear(); self.web_pin_l.setText('✔ 已儲存')

    def _port_changed(self):
        old = int(ENG.cfg.get('web_port') or BRAND['web_port']); new = int(self.web_port.value())
        if new == old: return
        ENG.cfg.set('web_port', new); was = self._ts.get('serving'); web_apply()
        if was: bg(lambda: (web.tailscale_serve_off(old), web.tailscale_serve_on(new)), lambda _r: self._web_status(True))
        self._web_status()

    def _web_status(self, ts=False):
        port = int(ENG.cfg.get('web_port') or BRAND['web_port']); self.web_hp.setText(f'→ Tailscale HTTPS 用 :{web.https_port(port)}')
        s = web_server(create=False); T = self._ts
        st = ('✔ 手機網頁開著：127.0.0.1:' + str(port) if s is not None and s.running else ('⚠ ' + s.err if s is not None and s.err else '手機網頁關著'))
        if T.get('installed') is False: st += '<br>Tailscale：這台電腦還沒裝（tailscale.com 下載，登入同一個帳號）'
        elif T.get('url'): st += f'<br>📱 手機 App 網址：<b>{esc_html(T["url"])}</b>' + ('　✔ Tailscale 已設定' if T.get('serving') else '　（還沒設定 → 按「📱 手機 App」）')
        if T.get('others'): st += f'<br><small>Tailscale 上其他程式用的 HTTPS 埠：{"、".join(T["others"])}（不會動它們）</small>'
        self.web_st.setText(st)
        if ts: bg(lambda: web.tailscale_info(port), lambda r: (setattr(self, '_ts', r), self._web_status()))

    def _web_app(self):
        if not web.tailscale_exe(): QMessageBox.information(self, '手機 App', '這台電腦還沒偵測到 Tailscale：\n\n1. 到 tailscale.com 下載 Windows 版安裝\n2. 右下角 Tailscale 圖示 → Log in\n3. 手機裝 Tailscale、登入同一個帳號'); return
        if not ENG.cfg.get('web_pin_hash'): QMessageBox.information(self, '手機 App', '先在上面設一個 PIN'); return
        if not ENG.cfg.get('web_on'): self.web_on.setChecked(True)
        port = int(ENG.cfg.get('web_port') or BRAND['web_port']); self.win.msg('設定 Tailscale HTTPS 中…（第一次可能要 10～30 秒）', 30000)
        bg(lambda: (web.tailscale_serve_on(port), web.tailscale_info(port)), self._web_app_done)

    def _web_app_done(self, r):
        (rc, out), T = r; self._ts = T; self._web_status(); ENG.log.w(f'手機網頁：tailscale serve → {rc}：{(out or "")[-400:]}')
        m = re.search(r'https://login\.tailscale\.com/\S+', out or '')
        if m: QDesktopServices.openUrl(QUrl(m.group(0))); QMessageBox.information(self, '手機 App', 'Tailscale 要你先在網頁上同意開啟 HTTPS（已經幫你打開），按完再按一次「📱 手機 App」'); return
        if not T.get('serving'): QMessageBox.warning(self, '手機 App', f'Tailscale 設定沒成功：\n{(out or "")[-600:]}\n\n常見原因：Tailscale 還沒登入、管理後台沒開 HTTPS（DNS → Enable HTTPS）。'); return
        QApplication.clipboard().setText(T['url'])
        QMessageBox.information(self, '手機 App', f'好了！網址已複製：\n\n{T["url"]}\n\n用手機（Tailscale 開著）打開 → 輸入 PIN → Chrome 右上「⋮」→「安裝應用程式」。')

    def _web_copy(self):
        u = self._ts.get('url')
        if not u: self._web_status(True); self.win.msg('還沒拿到 Tailscale 網址（先按「📱 手機 App」）'); return
        QApplication.clipboard().setText(u); self.win.msg(f'已複製：{u}')

    def _web_off(self):
        port = int(ENG.cfg.get('web_port') or BRAND['web_port'])
        if QMessageBox.question(self, 'Tailscale', f'把 Tailscale 上的 :{web.https_port(port)} 關掉？（只關這個程式自己的）') != QMessageBox.Yes: return
        bg(lambda: web.tailscale_serve_off(port), lambda r: (self._web_status(True), self.win.msg('已關掉 Tailscale 上這個程式的埠')))


# ============================================================ 📜 LOG
class LogPage(QWidget):
    FILES = ('app_log.txt', 'error_log.txt', 'ui_freeze_log.txt', 'update_log.txt', 'crash_dump.txt', 'qt_log.txt')

    def __init__(self, win):
        super().__init__(); self.win = win
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10); r = QHBoxLayout(); v.addLayout(r)
        self.f = QComboBox(); self.f.addItems(self.FILES); b1 = QPushButton('🔄 重新讀'); b2 = QPushButton('📦 匯出最近 7 天（給 AI 看）'); b3 = QPushButton('📂 開 LOG 資料夾')
        for w_ in (self.f, b1, b2, b3): r.addWidget(w_)
        r.addStretch(1); self.tx = QPlainTextEdit(); self.tx.setReadOnly(True); self.tx.setLineWrapMode(QPlainTextEdit.NoWrap); v.addWidget(self.tx, 1)
        self.f.currentIndexChanged.connect(lambda _i: self.load()); b1.clicked.connect(self.load)
        b3.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(ENG.log.d))))
        b2.clicked.connect(self._export)

    def showEvent(self, e):
        super().showEvent(e); self.load()

    def load(self):
        p = ENG.log.d / self.f.currentText()
        def rd():
            try:
                sz = p.stat().st_size
                with open(p, 'rb') as fh: fh.seek(max(0, sz - 400000)); return fh.read().decode('utf-8', 'replace')
            except Exception: return '（還沒有這個檔）'
        bg(rd, lambda t: (self.tx.setPlainText(t), self.tx.verticalScrollBar().setValue(self.tx.verticalScrollBar().maximum())))

    def _export(self):
        out, _ = QFileDialog.getSaveFileName(self, '匯出 LOG', str(Path.home() / 'Desktop' / f'{BRAND["id"]}_LOG_{time.strftime("%Y%m%d_%H%M")}.zip'), 'ZIP (*.zip)')
        if out: bg(lambda: ENG.log.export(out, 7), lambda n: self.win.msg(f'匯出好了：{n} 個檔 → {out}'))


# ============================================================ 🧪 實驗工作區
class LabPage(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win; self.cbs = {}
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10)
        t = QLabel('🧪 實驗工作區'); t.setObjectName('title'); v.addWidget(t)
        v.addWidget(note('新推薦的功能先放這裡（預設關）。試過覺得好，再說「變成正式功能」。程式裡用 lab_cfg().get("代號") 判斷有沒有打開。'))
        g = QGroupBox('開關'); self.fl = QVBoxLayout(g); v.addWidget(g)
        for k, nm, desc in LAB_LIST:
            cb = QCheckBox(nm); cb.setToolTip(desc); self.fl.addWidget(cb); self.fl.addWidget(note(desc)); self.cbs[k] = cb
            cb.toggled.connect(lambda on, k=k: self._set(k, on))
        if not LAB_LIST: self.fl.addWidget(note('目前沒有實驗功能'))
        v.addStretch(1); self.load()

    def _set(self, k, on):
        L = lab_cfg(); L[k] = bool(on); ENG.cfg.set('lab', L); self.win.msg(f'🧪 {k}：{"開" if on else "關"}')

    def load(self):
        L = lab_cfg()
        for k, cb in self.cbs.items(): cb.blockSignals(True); cb.setChecked(bool(L.get(k))); cb.blockSignals(False)


# ============================================================ 📖 使用說明
class HelpPage(QWidget):
    def __init__(self, win):
        super().__init__(); v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10); tx = QTextBrowser(); v.addWidget(tx, 1)
        tx.setHtml(f"""<h2>📖 {esc_html(APP_TITLE)}</h2>
<h3>🎨 生圖（用手機遙控電腦上的 ComfyUI）</h3>
<ol><li>電腦上打開 ComfyUI（Desktop 版或免安裝版都可以；這個程式會自動找 8000／8188 埠）。</li>
<li>「🎨 生圖」頁上方顯示 <b>● 已連上</b> 就可以用。工作也可以先排，ComfyUI 一開就自動開始跑。</li>
<li>選照片 → 打提示詞 → 選流程 → ▶ 開始。結果存在 Data\\outputs，手機和電腦都看得到。</li>
<li>流程：ComfyUI 裡「另存」的一般 .json 或「Export (API)」都可以丟進來（➕ 匯入流程）。程式會自動：
<ul><li>把讀圖節點（LoadImage、Load Image Batch…）換成你上傳的照片</li><li>把提示詞填進 KSampler 正向條件接到的文字節點（例如 TextEncodeQwenImageEditPlus 的 prompt）</li>
<li>每張種子隨機；只留 SaveImage／PreviewImage 用得到的節點（批次計數器、寫到別的資料夾的 Image Save 都會略過）</li></ul></li>
<li>結果的「✏ 拿結果再改」：把那張結果當新照片，再打一次提示詞接著改。</li></ol>
<h3>🧪 比較模型（手機網頁或電腦瀏覽器的「🧪 比較」分頁）</h3>
<ol><li>選好幾張照片、打一句提示詞，勾想比的模型（每一列一種，點開看說明、授權、缺哪些模型、調參數）。虛線框的是「同一個模型、不同設定」（例如 768 快速版、8 步快速版）。</li>
<li>按「▶ 開始比較」：缺的模型先自動下載，下載好就接著跑；同一個模型的照片連著跑（模型只載入一次）。可以按完就去睡。</li>
<li>早上看「📊 比較結果」：一列一張照片、一欄一個模型，點圖放大左右滑、點星星（或鍵盤 1～5）打分數。表頭有平均秒數和平均分數，「🎯 甜蜜點」幫你挑「夠好又最快」的。</li>
<li>「🖼 存成一張比較圖」可以傳給別人看；「↻ 失敗的重跑」補好模型後一鍵重跑。</li></ol>
<h3>手機生圖頁最上面的四個模式</h3>
<ul><li><b>🎨 改一張圖</b>：GROK（效果最好）或 Qwen（最快）。</li>
<li><b>🧩 兩張圖合併</b>：圖一人物＋圖二衣服／場景／姿勢／另一個人／商品／畫風，在手機頁點「👗 換衣服／🏞 換場景／🧍 照動作／👫 兩人合照／🛍 拿著商品／🎨 照畫風」填好提示詞。</li>
<li><b>🎬 照片變影片</b>：一張照片＋常用動作，長度先用 3～4 秒、畫質先用 ⚡ 快。</li>
<li><b>🎞 首尾幀影片</b>：開始畫面＋結束畫面＋一句中間發生什麼；結束畫面可以用改圖做（看大圖按「🎞 首尾幀」）。</li>
<li>影片做好按「⏭ 接下一段」可以接龍做長片。</li></ul>
<h3>手機改一張照片（最常用）</h3>
<ol><li>選照片；要裁切或轉正按照片左下角「✂ 裁切」。</li>
<li>打想怎麼改，或點「🪄 常用改法」挑一句；換衣服、換背景時打開「🔒 保持臉不變」。</li>
<li>點大按鈕選流程：🏆 GROK（效果最好）或 ⚡ Qwen（最快），或「🔁 兩個都跑」；「畫質」選 ⚡快／標準／🔍精細。</li>
<li>按開始，「⏳ 製作中」會寫幾點做完；做好手機會震一下、叮一聲。</li>
<li>點結果放大：拉桿跟原圖比，兩個流程都做了就「🆚 跟另一個比」；不滿意按「🏆 用 GROK 做一次」或「✏ 拿這張再改」。</li></ol>
<h3>手機上的進階改法</h3>
<ul><li><b>🖌 局部</b>：照片右下角塗要改的那一塊，其他地方一個像素都不動；「🔁 反過來」＝塗的保留（塗人物、只換背景）。</li>
<li><b>↔ 擴圖</b>：「✂ 裁切」裡選比例，把畫面往外補。<b>📎 參考圖</b>：再給一張圖，提示詞寫「參考圖」指它。</li>
<li><b>📌 配方</b>：常做的改法存起來一鍵套用。<b>📚 一次試很多種</b>：常用改法「這類全部各做一張」。</li></ul>
<h3>用哪個流程（你實測後定案的）</h3>
<ul><li><b>🏆 效果最好</b>：GROK 改圖（INT8 快），一張約 40 秒。<b>⚡ 速度最快、效果可以</b>：Qwen 2.1 Turbo 改圖，一張約 24 秒。</li>
<li>GROK（Qwen-Image-Edit 2511，20GB）塞不進 12GB 顯卡，每一步都要從記憶體搬，所以比較慢；Qwen 2.1 Turbo 是 7B，整顆放得進顯卡。</li>
<li>以前試過的其他模型：設定 →「🧩 模型檔」→「🧹 精簡」一次收掉、刪模型省空間。</li></ul>
<h3>其他小技巧</h3>
<ul><li>提示詞下面的「⭐ 存這句」把常用的存起來，點一下就填回去；勾「每一行當一個提示詞」可以一次試好幾種寫法。</li></ul>
<h3>其他</h3>
<ul><li>右上「📊 效能」：CPU／RAM／顯示卡浮窗（拖到你要的地方）；左下電腦狀態點一下也可以。</li>
<li>「🖥 後台」：每一項背景工作暫停／繼續／立刻停、先後順序；電腦太忙時自動讓路。</li>
<li>「🌙 縮到背景」：縮到右下角，背景繼續做。「🏠 封面」（Ctrl+L）：畫面上不留內容。</li>
<li>下方：深色／淺色、介面大小。</li>
<li>📱 手機：設定 → 手機網頁 → 打勾、設 PIN → 「📱 手機 App」，用手機打開網址、安裝成 App。</li>
<li>更新：把 {esc_html(BRAND['prefix'])}_V….zip 丟進 UPDATE 資料夾（上方會跳提示），或「⟳ 版本與更新」選它 → ⚡ 熱更新，程式不用關。</li>
<li>出問題：「📜 LOG」→「📦 匯出最近 7 天」，把 zip 傳給 AI。</li></ul>""")


# ============================================================ ⟳ 版本與更新（熱更新）
def vkey(v): return core.vkey(v)


def load_pkg(path):
    """讀更新包、檢查（只讀，不寫任何檔）：有 app/app.py、路徑安全、副檔名認得、每個 .py 都能編譯。回傳 {'path','files','version','notes','hot_ok'}."""
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        man = json.loads(zf.read('manifest.json').decode('utf-8-sig')) if 'manifest.json' in names else {}
        files = {m[4:]: zf.read(m) for m in names if m.startswith('app/') and not m.endswith('/')}
    if 'app.py' not in files: raise RuntimeError('這不是更新包（裡面沒有 app/app.py）')
    if man.get('app') and str(man['app']) != str(BRAND['id']): raise RuntimeError(f'這是別的程式（{man["app"]}）的更新包，不是 {BRAND["id"]} 的')
    for n in files:
        if '..' in Path(n).parts or Path(n).is_absolute() or '/' in n or '\\' in n: raise RuntimeError(f'更新包裡有不安全的路徑：{n}')
        if Path(n).suffix.lower() not in ('.py', '.json', '.md', '.txt', '.css', '.js', '.html', '.png', '.ico', '.svg'): raise RuntimeError(f'更新包裡有不認得的檔案：{n}')
    for n, data in files.items():
        if n.endswith('.py'):
            try: compile(data.decode('utf-8'), n, 'exec')
            except SyntaxError as ex: raise RuntimeError(f'{n} 第 {ex.lineno} 行有語法錯誤：{ex.msg}')
    if int(man.get('requires_launcher', 1)) > 1: raise RuntimeError('這個更新需要新的啟動器（EXE），請用完整安裝包（BUILD_AND_INSTALL.bat）更新')
    ver = str(man.get('version') or '')
    if not ver:
        m = re.search(r"APP_VERSION\s*=\s*'([^']+)'", files['app.py'].decode('utf-8', 'ignore')); ver = m.group(1) if m else '?'
    notes = []
    try:
        C = json.loads(files['CHANGELOG.json'].decode('utf-8-sig')) if 'CHANGELOG.json' in files else []
        notes = list((next((e for e in C if str(e.get('version')) == ver), None) or {}).get('items') or [])
    except Exception: pass
    return {'path': str(path), 'files': files, 'version': ver, 'notes': notes, 'hot_ok': b'def hot_start(' in files['app.py']}


def list_backups(limit=12):
    """⏪ 可以退回的版本：每次熱更新前自動備份的 app_backup\\*（新的在前）。回傳 [{'path','version','time','notes','older'}]."""
    out = []; d = ROOT / 'app_backup'
    if not d.is_dir(): return out
    for b in sorted([x for x in d.iterdir() if x.is_dir() and (x / 'app.py').is_file()], key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            m = re.search(r"APP_VERSION\s*=\s*'([^']+)'", (b / 'app.py').read_text(encoding='utf-8', errors='ignore')); ver = m.group(1) if m else '?'
            if any(o['version'] == ver for o in out): continue
            try: C = json.loads((b / 'CHANGELOG.json').read_text(encoding='utf-8-sig'))
            except Exception: C = []
            notes = list((next((e for e in C if str(e.get('version')) == ver), None) or {}).get('items') or [])
            out.append({'path': str(b), 'version': ver, 'time': time.strftime('%Y-%m-%d %H:%M', time.localtime(b.stat().st_mtime)), 'notes': notes, 'older': vkey(ver) < vkey(APP_VERSION)})
        except Exception: pass
        if len(out) >= limit: break
    return out


def backup_pkg(path):
    """把一個備份資料夾當成更新包（給 hot_update 用）."""
    b = Path(path); files = {}
    for f in b.iterdir():
        if f.is_file() and f.suffix.lower() in ('.py', '.json', '.md', '.txt', '.css', '.js', '.html', '.png', '.ico', '.svg'): files[f.name] = f.read_bytes()
    if 'app.py' not in files: raise RuntimeError('這個備份不完整（沒有 app.py）')
    for n, data in files.items():
        if n.endswith('.py'): compile(data.decode('utf-8'), n, 'exec')
    m = re.search(r"APP_VERSION\s*=\s*'([^']+)'", files['app.py'].decode('utf-8', 'ignore')); ver = m.group(1) if m else '?'
    try: notes = list((next((e for e in json.loads(files['CHANGELOG.json'].decode('utf-8-sig')) if str(e.get('version')) == ver), None) or {}).get('items') or [])
    except Exception: notes = []
    return {'path': str(b), 'files': files, 'version': ver, 'notes': notes, 'hot_ok': b'def hot_start(' in files['app.py'], 'rollback': True}


def upd_log(msg):
    try:
        (ROOT / 'LOG').mkdir(exist_ok=True)
        with open(ROOT / 'LOG' / 'update_log.txt', 'a', encoding='utf-8') as fh: fh.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {msg}\n')
    except Exception: pass
    try: ENG.log.w('更新：' + msg.splitlines()[0][:300])
    except Exception: pass


def hot_update(win, pkg):
    """熱更新：寫入新程式 → 用全新的模組建新引擎、新視窗 → 交接 → 收掉舊視窗。背景工作不停、程式不關。
    任何一步失敗：檔案還原、模組還原，舊視窗照常用（更新包留在 UPDATE，下次開程式時再試）。回傳 True／False."""
    code = HERE; ver = pkg['version']; t0 = time.time(); name = ''
    upd_log(f'熱更新開始：V{APP_VERSION} → V{ver}（{Path(pkg["path"]).name}）')
    backup = ROOT / 'app_backup' / f'{time.strftime("%Y%m%d_%H%M%S")}_before_hot_V{ver}'
    try:
        shutil.copytree(code, backup, ignore=shutil.ignore_patterns('__pycache__'))
        for n, data in pkg['files'].items():
            dst = code / n; tmp = dst.with_name(dst.name + '.new'); tmp.write_bytes(data); os.replace(str(tmp), str(dst))
        shutil.rmtree(code / '__pycache__', ignore_errors=True)
    except Exception as ex:
        _restore_files(backup); upd_log(f'熱更新失敗（寫檔）：{ex}\n{traceback.format_exc()}')
        QMessageBox.warning(win, '更新失敗', f'寫入新程式失敗，已還原，程式照常使用：\n{ex}'); return False
    mods = sorted({p.stem for p in code.glob('*.py')} - {'app'}); saved = {m: sys.modules.get(m) for m in mods}; new_eng = None
    try:
        for m in mods: sys.modules.pop(m, None)
        importlib.invalidate_caches()
        name = f'app_hot_{int(time.time() * 1000)}'
        spec = importlib.util.spec_from_file_location(name, str(code / 'app.py')); mod = importlib.util.module_from_spec(spec); sys.modules[name] = mod
        spec.loader.exec_module(mod)
        if not hasattr(mod, 'hot_start'): raise RuntimeError('這個版本不支援熱更新')
        state = win.export_state(); state.update(hot_from=APP_VERSION, hot_to=ver, hot_notes=pkg.get('notes') or [])
        new_win, new_eng = mod.hot_start(ENG, state)
    except Exception as ex:
        err = traceback.format_exc()
        if new_eng is not None:
            try: new_eng.discard()
            except Exception: pass
        for m, v in saved.items():
            if v is not None: sys.modules[m] = v
            else: sys.modules.pop(m, None)
        sys.modules.pop(name, None); _restore_files(backup)
        try:
            d = ROOT / 'UPDATE'; d.mkdir(exist_ok=True)
            if Path(pkg['path']).parent.resolve() != d.resolve(): shutil.copy2(pkg['path'], d / Path(pkg['path']).name)
        except Exception: pass
        upd_log(f'熱更新失敗（新版載入）：{ex}\n{err}')
        QMessageBox.warning(win, '無法熱更新', f'新版沒辦法在執行中載入，已經還原成 V{APP_VERSION}，背景工作沒有受影響。\n\n更新包放在 UPDATE 資料夾，下次打開程式時會自動套用（失敗會自動退回）。\n\n{ex}')
        return False
    try: win.handoff()
    except Exception: upd_log('舊視窗交接時有錯誤（不影響新版）：\n' + traceback.format_exc())
    try: new_eng.start()
    except Exception: upd_log('新引擎啟動時有錯誤：\n' + traceback.format_exc())
    try: new_win.show_after_hot(state)
    except Exception: upd_log('新視窗顯示時有錯誤：\n' + traceback.format_exc()); new_win.show()
    app = QApplication.instance(); app._ak_main = new_win; app._ak_eng = new_eng
    try:
        p = Path(pkg['path']); d = ROOT / 'UPDATE'
        if p.parent.resolve() == d.resolve(): (d / 'applied').mkdir(exist_ok=True); os.replace(str(p), str(d / 'applied' / p.name))
    except Exception: pass
    upd_log(f'熱更新完成：V{APP_VERSION} → V{ver}，{time.time() - t0:.1f} 秒（備份 {backup.name}）')
    try: win.close(); win.deleteLater()
    except Exception: pass
    return True


def _restore_files(backup):
    try:
        if backup and Path(backup).exists():
            keep = {f.name for f in Path(backup).iterdir() if f.is_file()}
            for f in Path(backup).iterdir():
                if f.is_file(): shutil.copy2(f, HERE / f.name)
            for f in HERE.iterdir():
                if f.is_file() and f.name not in keep and f.suffix in ('.py', '.json'):
                    try: f.unlink(); upd_log(f'還原：移除更新包新加的 {f.name}')
                    except Exception: pass
            shutil.rmtree(HERE / '__pycache__', ignore_errors=True)
    except Exception: upd_log('還原檔案失敗：\n' + traceback.format_exc())


class UpdPage(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win; self.pkg = None
        v = QVBoxLayout(self); v.setContentsMargins(10, 10, 10, 10)
        t = QLabel(f'⟳ 版本與更新　目前 V{APP_VERSION}'); t.setObjectName('title'); v.addWidget(t)
        cg = QGroupBox('☁ 雲端更新（GitHub）'); cl = QVBoxLayout(cg); v.addWidget(cg)          # V0.3.36
        self.cu_l = QLabel('☁ 讀取中…'); self.cu_l.setWordWrap(True); self.cu_l.setTextFormat(Qt.RichText); cl.addWidget(self.cu_l)
        cr = QHBoxLayout(); cl.addLayout(cr)
        self.cu_chk = QPushButton('☁ 檢查更新'); self.cu_up = QPushButton('更新'); self.cu_up.setObjectName('start'); self.cu_skip = QPushButton('略過這版'); self.cu_x = QPushButton('取消下載')
        self.cu_on = QCheckBox('自動檢查更新（開程式 1 分鐘後、之後每 6 小時；只提示，不會自己更新）')
        for w in (self.cu_chk, self.cu_skip, self.cu_x, self.cu_up): cr.addWidget(w)
        cr.addStretch(1); cl.addWidget(self.cu_on)
        self.cu_chk.clicked.connect(lambda: (cloudupd.op({'op': 'check'}), self.win.msg('☁ 檢查雲端更新中…', 4000), QTimer.singleShot(300, self.cu_paint)))
        self.cu_up.clicked.connect(lambda: (self.win.cloud_update(self), self.cu_paint()))
        self.cu_skip.clicked.connect(lambda: (self.win.msg('☁ ' + cloudupd.op({'op': 'unskip' if (cloudupd.info().get('chk') or {}).get('skipped') else 'skip'}).get('message', ''), 8000), self.cu_paint()))
        self.cu_x.clicked.connect(lambda: (cloudupd.op({'op': 'cancel'}), self.cu_paint()))
        self.cu_on.toggled.connect(lambda b: cloudupd.op({'op': 'on', 'v': b}))
        self.cu_t = QTimer(self); self.cu_t.timeout.connect(self.cu_paint); self.cu_t.start(2000); QTimer.singleShot(50, self.cu_paint)
        v.addWidget(note(f'⚡ 熱更新：選更新包（{BRAND["prefix"]}_V….zip）或丟進 UPDATE 資料夾 → 確認 → 程式不用關，畫面直接換成新版；背景工作不中斷。新版載入不了會自動還原。'))
        g = QGroupBox('📦 更新包規則（給 AI／給你自己看）'); gl = QVBoxLayout(g); v.addWidget(g)
        gl.addWidget(note(f'檔名：{BRAND["prefix"]}_V0.1.01.zip（版本最後一段兩位數：0.1.01 → 0.1.02 … 0.1.99 → 0.2.01，不用 00）\n'
                          '內容：manifest.json（{"app": "' + BRAND['id'] + '", "version": "0.1.02", "requires_launcher": 1}）＋ app\\ 底下所有程式檔（app.py、core.py、web.py、webpage.py、brand.json、CHANGELOG.json…）\n'
                          '每一版：app.py 的 APP_VERSION 改成新版本、CHANGELOG.json 最上面加一筆（版本、日期、改了什麼）；用 tools\\pack.py 打包會自動檢查這些。\n'
                          '只有 app\\ 的檔會被換；Data\\（設定、資料庫）、LOG\\ 永遠不動。換 EXE（build\\launcher.py）才需要重新跑 BUILD_AND_INSTALL.bat。'))
        r = QHBoxLayout(); v.addLayout(r); b1 = QPushButton('📦 選更新包…'); self.b_go = QPushButton('⚡ 熱更新'); self.b_go.setEnabled(False); self.b_go.setObjectName('start')
        b3 = QPushButton('🔁 改用重開程式套用'); b2 = QPushButton('📂 開 UPDATE 資料夾')
        for w in (b1, self.b_go, b3, b2): r.addWidget(w)
        r.addStretch(1)
        self.info = QLabel('（還沒選更新包）'); self.info.setWordWrap(True); self.info.setTextFormat(Qt.RichText); v.addWidget(self.info)
        gr = QGroupBox('⏪ 退回前面的版本（每次更新前自動備份的；一樣不用關程式）'); self.rbl = QVBoxLayout(gr); v.addWidget(gr); self._rb_w = None
        self.tx = QTextBrowser(); self.tx.setMinimumHeight(240); v.addWidget(self.tx, 1); self._cl(); self.rb_load()
        b1.clicked.connect(self.pick); self.b_go.clicked.connect(self.go); b3.clicked.connect(self.restart_way)
        b2.clicked.connect(lambda: (Path(ROOT / 'UPDATE').mkdir(exist_ok=True), QDesktopServices.openUrl(QUrl.fromLocalFile(str(ROOT / 'UPDATE')))))

    def cu_paint(self):
        if not self.isVisible() and getattr(self, '_cu_once', False): return
        self._cu_once = True
        try:
            I = cloudupd.info(); c = I.get('chk') or {}; dl = I.get('dl') or {}
            if I['busy'] or dl:
                p = (dl.get('got', 0) / dl['size'] * 100) if dl.get('size') else 0
                t = f"☁ {esc_html(I['msg'] or '下載中')}" + (f"　{esc_html(dl.get('label', ''))} {p:.0f}%（{dl.get('spd', 0) / 1048576:.1f} MB/s）" if dl else '')
            elif I['checking']: t = '☁ 檢查中…'
            elif not c: t = '☁ 還沒檢查（開程式 1 分鐘後會自動檢查，之後每 6 小時）'
            elif not c.get('ok'): t = '☁ ' + esc_html(c.get('message') or '連不到 GitHub')
            elif c.get('newer'):
                t = f"☁ <b>雲端有新版 V{esc_html(I['ver'])}</b>（現在 V{APP_VERSION}）" + ('　⚠ 這次要換 EXE（程式會關掉再自動打開；排隊的生圖會接著做）' if c.get('need_shell') else '　熱更新、生圖不中斷') + (' · 已略過這版' if c.get('skipped') else '')
                if I['notes']: t += '<br>' + '<br>'.join('• ' + esc_html(x) for x in I['notes'][:10])
            else: t = f"☁ ✔ 已經是最新（雲端 V{esc_html(I['ver'])}，{time.strftime('%m-%d %H:%M', time.localtime(c.get('t') or time.time()))} 檢查）"
            if I['msg'] and not I['busy']: t += '<br>' + esc_html(I['msg'])
            t += f"<br><small style='color:#8994a4'>啟動器（EXE）第 {I['launcher']} 版" + ('' if I['frozen'] else '・原始碼模式') + '</small>'
            self.cu_l.setText(t); idle = not I['busy'] and not dl
            self.cu_up.setEnabled(bool(c.get('newer')) and idle); self.cu_skip.setVisible(bool(c.get('newer')) and not c.get('need_shell') and idle)
            self.cu_skip.setText('取消略過' if c.get('skipped') else '略過這版'); self.cu_x.setVisible(not idle); self.cu_chk.setEnabled(idle and not I['checking'])
            if self.cu_on.isChecked() != I['on']: self.cu_on.blockSignals(True); self.cu_on.setChecked(I['on']); self.cu_on.blockSignals(False)
        except Exception: pass

    def _cl(self):
        try: C = json.loads((HERE / 'CHANGELOG.json').read_text(encoding='utf-8'))
        except Exception: C = []
        self.tx.setHtml(''.join(f"<h3>V{x.get('version')}　<small>{x.get('date', '')}</small></h3><ul>" + ''.join(f'<li>{esc_html(i)}</li>' for i in x.get('items') or []) + '</ul>' for x in C) or '（沒有更新紀錄）')

    def rb_load(self):
        bg(list_backups, self._rb)

    def _rb(self, L):
        if self._rb_w is not None: self._rb_w.setParent(None); self._rb_w.deleteLater()
        self._rb_w = QWidget(); l = QVBoxLayout(self._rb_w); l.setContentsMargins(0, 0, 0, 0); self.rbl.addWidget(self._rb_w)
        if not L: l.addWidget(note('還沒有可以退回的版本（熱更新過一次之後才會有）。')); return
        for x in L[:8]:
            r = QHBoxLayout(); lab = QLabel(f"<b>V{esc_html(x['version'])}</b>　{'前一版' if x['older'] else '較新'}　<small>{x['time']} 更新前備份的</small>"); lab.setTextFormat(Qt.RichText)
            if x['notes']: lab.setToolTip('\n'.join('• ' + n for n in x['notes']))
            b = QPushButton(f"退回 V{x['version']}"); b.clicked.connect(lambda _c=False, x=x: self.rollback(x)); r.addWidget(lab, 1); r.addWidget(b); l.addLayout(r)

    def rollback(self, x):
        if QMessageBox.question(self, '退回', f"從 V{APP_VERSION} 換回 V{x['version']}？程式不用關，背景工作不會中斷。") != QMessageBox.Yes: return
        try: pkg = backup_pkg(x['path'])
        except Exception as ex: QMessageBox.warning(self, '退回', f'這個備份不能用：{ex}'); return
        upd_log(f'退回：V{APP_VERSION} → V{pkg["version"]}（{x["path"]}）'); hot_update(self.win, pkg)

    def pick(self):
        p, _ = QFileDialog.getOpenFileName(self, '選更新包', ldir('pkg', Path.home() / 'Downloads'), f'更新包 ({PKG_GLOB} *.zip)'); sdir('pkg', p)
        if p: self.load(p)

    def load(self, p):
        self.pkg = None; self.b_go.setEnabled(False)
        try: pkg = load_pkg(p)
        except Exception as ex:
            self.info.setText(f'<b>{esc_html(Path(p).name)}</b><br><span style="color:#ff6577">不能用這個更新包：{esc_html(ex)}</span>'); upd_log(f'更新包不能用：{p}：{ex}'); return False
        self.pkg = pkg; d = vkey(pkg['version']); c = vkey(APP_VERSION)
        way = '升級' if d > c else ('相同版本（重新套用）' if d == c else '⚠ 降版（退回舊版）')
        h = f'<b>{esc_html(Path(p).name)}</b>　V{APP_VERSION} → <b>V{esc_html(pkg["version"])}</b>（{way}）'
        if pkg['notes']: h += '<br>' + '<br>'.join('• ' + esc_html(x) for x in pkg['notes'])
        h += ('<br><span style="color:#45d483">可以熱更新：程式不用關。</span>' if pkg['hot_ok'] else '<br><span style="color:#f0ad4e">這個版本不支援熱更新，要用「🔁 改用重開程式套用」。</span>')
        self.info.setText(h); self.b_go.setEnabled(pkg['hot_ok']); upd_log(f'選了更新包：{p}（V{pkg["version"]}，{way}）'); return True

    def go(self, confirm=True):
        if not self.pkg: return
        busy = sum(ENG.bg_running(k) for k, _i, _n in ENG.BG_KINDS)
        if confirm and QMessageBox.question(self, '熱更新', f'從 V{APP_VERSION} 更新到 V{self.pkg["version"]}？\n\n程式不用關；' + (f'正在做的 {busy} 個工作不會中斷（做完由新版接手）。' if busy else '')) != QMessageBox.Yes: return
        hot_update(self.win, self.pkg)

    def restart_way(self):
        if not self.pkg: self.win.msg('先選更新包'); return
        try:
            d = ROOT / 'UPDATE'; d.mkdir(exist_ok=True)
            if Path(self.pkg['path']).parent.resolve() != d.resolve(): shutil.copy2(self.pkg['path'], d / Path(self.pkg['path']).name)
        except Exception as ex: QMessageBox.warning(self, '更新', str(ex)); return
        if QMessageBox.question(self, '更新', '更新包放好了。現在重新開程式套用？') == QMessageBox.Yes: self.win.restart()


# ============================================================ 📊 效能浮窗、左邊選單、左下電腦狀態、封面
class PerfFloat(QWidget):
    def __init__(self):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint); self.setAttribute(Qt.WA_TranslucentBackground); self.resize(250, 150); self.drag = None
        self.tm = QTimer(self); self.tm.timeout.connect(self._tick); self.tm.start(1000)

    def _tick(self):
        h = 8 + 20 * (6 if ENG.perf.gpu else 2) + (22 if ENG.perf.gpu else 2)
        if self.height() != h: self.setFixedHeight(h)
        self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(12, 15, 20, 225)); p.setPen(QColor('#2f3a4a')); p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 10, 10)
        P = ENG.perf; g = P.gpu or {}
        rows = [('CPU', P.cpu, '#4dc9ff', P.H['cpu']), ('RAM', P.ram, '#b48cff', P.H['ram'])]
        if g: rows += [('GPU', g.get('util'), '#45d483', P.H['gpu']), ('壓縮', g.get('enc'), '#f0ad4e', P.H['enc']), ('解碼', g.get('dec'), '#ff6577', P.H['dec']),
                       ('VRAM', 100 * g['mem'] / g['mem_t'] if g.get('mem_t') else None, '#9aa5b3', P.H['vram'])]
        f = QFont(); f.setPixelSize(11); p.setFont(f); y = 8
        for nm, val, col, H in rows:
            p.setPen(QColor('#cfd6e0')); p.drawText(QRect(10, y, 40, 16), Qt.AlignLeft | Qt.AlignVCenter, nm)
            bx = QRect(52, y + 3, 120, 10); p.setPen(Qt.NoPen); p.setBrush(QColor('#1d2430')); p.drawRoundedRect(bx, 4, 4)
            if val is not None: p.setBrush(QColor(col)); p.drawRoundedRect(QRect(bx.x(), bx.y(), int(bx.width() * max(0, min(100, val)) / 100), bx.height()), 4, 4)
            pts = list(H)[-60:]
            if pts:
                p.setPen(QPen(QColor(col), 1)); x0 = 180; w = 60
                for i in range(1, len(pts)):
                    if pts[i] is None or pts[i - 1] is None: continue
                    p.drawLine(int(x0 + (i - 1) * w / 60), int(y + 14 - pts[i - 1] / 100 * 13), int(x0 + i * w / 60), int(y + 14 - pts[i] / 100 * 13))
            p.setPen(QColor('#ffffff')); p.drawText(QRect(52, y, 120, 16), Qt.AlignCenter, '—' if val is None else f'{val:.0f}%'); y += 20
        if g: p.setPen(QColor('#8a96a8')); p.drawText(QRect(10, y, 230, 16), Qt.AlignLeft, f"{g.get('name', '')[:22]} {g.get('temp', 0):.0f}°C")
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self.drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self.drag is not None: self.move(e.globalPosition().toPoint() - self.drag)

    def mouseReleaseEvent(self, e):
        self.drag = None
        try: ENG.cfg.set('perf_pos', [self.x(), self.y()])
        except Exception: pass


class NavDelegate(QStyledItemDelegate):
    """側邊選單：分組標題（彩色小字＋細線，點了收合）和選項（圖示欄＋選到時左邊彩色條）."""
    def sizeHint(self, option, index):
        h = QFontMetrics(option.font).height(); return QSize(option.rect.width(), (h + 9) if index.data(Qt.UserRole + 2) == 'header' else (h + 12))

    def paint(self, painter, option, index):
        painter.save(); painter.setRenderHint(QPainter.Antialiasing)
        kind = index.data(Qt.UserRole + 2); text = str(index.data(Qt.DisplayRole) or ''); color = QColor(str(index.data(Qt.UserRole + 1) or '#4dc9ff')); r = option.rect
        if kind == 'header':
            f = QFont(option.font); f.setBold(True); px = option.font.pixelSize()
            if px > 0: f.setPixelSize(max(9, round(px * 0.82)))
            else: f.setPointSizeF(max(7.0, f.pointSizeF() * 0.82))
            painter.setFont(f); fm = QFontMetrics(f); y = r.bottom() - 6
            painter.setPen(color); painter.drawText(QRectF(r.left() + 10, r.top(), r.width() - 14, r.height() - 4), Qt.AlignLeft | Qt.AlignBottom, text)
            x0 = r.left() + 14 + fm.horizontalAdvance(text)
            if x0 < r.right() - 8:
                c = QColor(color); c.setAlpha(70); painter.setPen(QPen(c, 1)); painter.drawLine(int(x0), int(y - fm.height() / 2 + 3), int(r.right() - 8), int(y - fm.height() / 2 + 3))
        else:
            selected = bool(option.state & QStyle.State_Selected); hover = bool(option.state & QStyle.State_MouseOver)
            box = QRectF(r.left() + 4, r.top() + 2, r.width() - 8, r.height() - 4)
            if selected:
                bgc = QColor(color); bgc.setAlpha(38); painter.setPen(Qt.NoPen); painter.setBrush(bgc); painter.drawRoundedRect(box, 7, 7)
                painter.setBrush(color); painter.drawRoundedRect(QRectF(box.left(), box.top() + 5, 3.5, box.height() - 10), 2, 2)
            elif hover: painter.setPen(Qt.NoPen); painter.setBrush(TC('hover')); painter.drawRoundedRect(box, 7, 7)
            f = QFont(option.font); f.setBold(selected); painter.setFont(f)
            icon = str(index.data(Qt.UserRole + 3) or ''); badge = str(index.data(Qt.UserRole + 4) or '')
            painter.setPen(color if selected else TC('muted')); painter.drawText(QRectF(box.left() + 10, box.top(), 22, box.height()), Qt.AlignCenter, icon)
            painter.setPen(TC('text_strong') if selected else (TC('text') if hover else TC('nav_text')))
            painter.drawText(QRectF(box.left() + 38, box.top(), box.width() - 42, box.height()), Qt.AlignLeft | Qt.AlignVCenter, text)
            if badge:
                fb = QFont(option.font); fb.setBold(True); painter.setFont(fb); fmb = QFontMetrics(fb)
                bw = fmb.horizontalAdvance(badge) + 12; br = QRectF(box.right() - bw - 6, box.center().y() - 8, bw, 16)
                c = QColor(color); c.setAlpha(60); painter.setPen(Qt.NoPen); painter.setBrush(c); painter.drawRoundedRect(br, 8, 8)
                painter.setPen(TC('text_strong')); painter.drawText(br, Qt.AlignCenter, badge)
        painter.restore()


class NavList(QListWidget):
    """左邊選單。GROUPS：(分組名稱, 顏色, [(頁碼, 名稱, 圖示)])。頁碼＝Main.PAGES 的位置。對外 setCurrentRow(頁)、currentRow() 都用頁碼."""
    GROUPS = [('總覽', '#4dc9ff', [(0, '生圖', '🎨'), (7, '歷史紀錄', '📜'), (1, '後台狀態', '🖥')]),
              ('電腦與檔案', '#45d483', [(2, '🧪 實驗工作區', '🧪'), (3, 'LOG', '📜')]),
              ('設定', '#9aa5b3', [(4, '設定', '⚙'), (5, '版本與更新', '⟳'), (6, '使用說明', '📖')])]
    NAMES = {pg: (ic, nm) for _g, _c, L in GROUPS for pg, nm, ic in L}

    def __init__(self, on_page):
        super().__init__(); self.on_page = on_page; self._page = -1; self._items = {}; self._groups = []
        self.setObjectName('workspace_nav'); self.setItemDelegate(NavDelegate(self)); self.setMouseTracking(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel); self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        for gname, col, L in self.GROUPS:
            h = QListWidgetItem(gname); h.setFlags(Qt.ItemIsEnabled); h.setData(Qt.UserRole, -1); h.setData(Qt.UserRole + 1, col); h.setData(Qt.UserRole + 2, 'header'); self.addItem(h)
            its = []
            for pg, nm, ic in L:
                it = QListWidgetItem(nm); it.setData(Qt.UserRole, pg); it.setData(Qt.UserRole + 1, col); it.setData(Qt.UserRole + 2, 'item'); it.setData(Qt.UserRole + 3, ic)
                it.setToolTip(nm); self.addItem(it); self._items[pg] = it; its.append(it)
            self._groups.append((h, gname, its))
        self.currentRowChanged.connect(self._row_changed); self.itemClicked.connect(self._clicked)
        QTimer.singleShot(0, self.apply_collapse)

    def page_name(self, pg): return self.NAMES.get(int(pg), ('', ''))[1]

    def page_icon(self, pg): return self.NAMES.get(int(pg), ('', ''))[0]

    def _row_changed(self, row):
        try: it = self.item(row); pg = int(it.data(Qt.UserRole)) if it is not None else -1
        except Exception: return
        if pg >= 0 and pg != self._page: self._page = pg; self.on_page(pg)

    def setCurrentRow(self, pg, *a):
        pg = int(pg); it = self._items.get(pg)
        if it is None: return
        try: super().setCurrentItem(it)
        except Exception: pass
        if pg != self._page: self._page = pg; self.on_page(pg)
        self.apply_collapse()

    def currentRow(self): return self._page

    def set_badge(self, pg, txt):
        it = self._items.get(int(pg))
        if it is not None and str(it.data(Qt.UserRole + 4) or '') != str(txt or ''): it.setData(Qt.UserRole + 4, str(txt or ''))

    def _shut(self):
        v = ENG.cfg.get('nav_shut'); return set(v) if isinstance(v, list) else set()

    def apply_collapse(self):
        try:
            shut = self._shut(); cur = self._items.get(self._page)
            for h, nm, its in self._groups:
                off = nm in shut and cur not in its
                for it in its: it.setHidden(off)
                h.setText(nm + ('　▸ ' + str(len(its)) if off else ''))
        except Exception: pass

    def _clicked(self, item):
        try:
            if item is None or int(item.data(Qt.UserRole)) >= 0: return
            nm = item.text().split('　')[0]; shut = self._shut(); shut.symmetric_difference_update({nm}); ENG.cfg.set('nav_shut', sorted(shut)); self.apply_collapse()
            cur = self._items.get(self._page)
            if cur is not None: QListWidget.setCurrentItem(self, cur)
        except Exception: pass


class SysPanel(QWidget):
    """左下角電腦狀態：每項一列（名稱、彩色進度條、數值、溫度），點一下開／關📊效能浮窗."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent); self.rows = []; self.setCursor(Qt.PointingHandCursor); self.setMinimumHeight(40)

    def set_rows(self, rows):
        if rows != self.rows: self.rows = rows; self.setFixedHeight(10 + 19 * max(1, len(rows))); self.update()

    def mousePressEvent(self, e): self.clicked.emit()

    def paintEvent(self, _e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing, True); W = self.width()
        p.setPen(QPen(TC('border'), 1)); p.setBrush(TC('card')); p.drawRoundedRect(QRectF(0.5, 0.5, W - 1, self.height() - 1), 9, 9)
        f = QFont(self.font()); f.setPointSizeF(8.2); fb = QFont(f); fb.setBold(True)
        lw, vw, tw = 40, 46, 30; bx = 8 + lw; bw = max(20, W - 8 - lw - vw - tw - 10)
        if not self.rows: p.setPen(TC('subtext')); p.drawText(self.rect(), Qt.AlignCenter, '電腦狀態讀取中…'); p.end(); return
        for i, (lab, pct, val, temp, col) in enumerate(self.rows):
            y = 5 + i * 19; cy = y + 9.5
            p.setFont(fb); p.setPen(TC('subtext')); p.drawText(QRectF(8, y, lw, 19), Qt.AlignLeft | Qt.AlignVCenter, lab)
            if pct is not None:
                p.setPen(Qt.NoPen); p.setBrush(TC('track')); p.drawRoundedRect(QRectF(bx, cy - 3, bw, 6), 3, 3)
                p.setBrush(QColor(col)); p.drawRoundedRect(QRectF(bx, cy - 3, max(3.0, bw * min(100.0, max(0.0, pct)) / 100.0), 6), 3, 3)
            p.setPen(TC('text_strong')); p.drawText(QRectF(bx + bw + 4, y, vw, 19), Qt.AlignRight | Qt.AlignVCenter, val)
            if temp:
                p.setPen(QColor('#ff5c5c' if temp >= 85 else '#f0ad4e' if temp >= 70 else '#45d483')); p.setFont(f)
                p.drawText(QRectF(W - 8 - tw, y, tw, 19), Qt.AlignRight | Qt.AlignVCenter, f'{temp:.0f}°')
        p.end()


class CoverPage(QWidget):
    """開機封面：不露出任何內容；你按了才進去（Ctrl+L 或上方🏠封面隨時回來）。COVER_BTNS＝(頁碼, 圖示, 名稱, 說明)."""
    COVER_BTNS = [(0, '🎨', '生圖', '照片＋提示詞 → ComfyUI'), (7, '📜', '歷史', '跑過的全部、時間統計'), (1, '🖥', '後台', '背景工作'), (4, '⚙', '設定', '手機網頁、一般'), (5, '⟳', '版本與更新', '熱更新')]

    def __init__(self, win):
        super().__init__(); self.win = win; self.t0 = time.time()
        v = QVBoxLayout(self); v.setContentsMargins(40, 0, 40, 24); v.addStretch(5)
        self.resume = QPushButton(''); self.resume.setMinimumHeight(48)
        self.resume.setStyleSheet('QPushButton{background:rgba(77,201,255,0.18);border:1px solid #4dc9ff;border-radius:24px;font-size:16px;font-weight:700;padding:8px 28px;color:#ffffff}QPushButton:hover{background:rgba(77,201,255,0.32)}')
        rr = QHBoxLayout(); rr.addStretch(1); rr.addWidget(self.resume); rr.addStretch(1); v.addLayout(rr); v.addSpacing(22)
        grid = QGridLayout(); grid.setHorizontalSpacing(14); grid.setVerticalSpacing(14)
        for k, (page, ic, nm, sub) in enumerate(self.COVER_BTNS):
            b = QPushButton(f'{ic}\n{nm}' + (f'\n{sub}' if sub else '')); b.setMinimumSize(190, 96)
            b.setStyleSheet('QPushButton{background:rgba(20,28,40,0.72);border:1px solid rgba(120,160,210,0.35);border-radius:16px;font-size:13px;color:#dfe9f5;padding:10px}QPushButton:hover{background:rgba(40,60,90,0.85);border-color:#4dc9ff;color:#ffffff}')
            b.clicked.connect(lambda _c=False, page=page: self.win.enter(page)); grid.addWidget(b, k // 4, k % 4)
        gw = QWidget(); gw.setLayout(grid); gw.setStyleSheet('background:transparent'); gr = QHBoxLayout(); gr.addStretch(1); gr.addWidget(gw); gr.addStretch(1); v.addLayout(gr)
        v.addStretch(3)
        self.hint = QLabel('Ctrl+L 或上方「🏠 封面」隨時回到這裡'); self.hint.setAlignment(Qt.AlignCenter); self.hint.setStyleSheet('QLabel{color:#4f6178;font-size:11px;background:transparent}'); v.addWidget(self.hint)
        self.resume.clicked.connect(lambda: self.win.enter(int(ENG.cfg.get('last_page') or 0)))
        self.tm = QTimer(self); self.tm.timeout.connect(lambda: self.update() if self.isVisible() else None); self.tm.start(1000)

    def showEvent(self, e):
        super().showEvent(e); self.refresh()

    def refresh(self):
        lp = int(ENG.cfg.get('last_page') or 0); self.resume.setText(f'↩  進入（上次停在：{NavList.NAMES.get(lp, ("", "首頁"))[1]}）'); self.resume.setFocus()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); W, H = self.width(), self.height()
        g = QLinearGradient(0, 0, W, H); g.setColorAt(0, QColor('#070b12')); g.setColorAt(0.55, QColor('#0f1a2b')); g.setColorAt(1, QColor('#1a1430')); p.fillRect(self.rect(), g)
        ph = (time.time() - self.t0) * 0.15
        for cx, cy, r, col in ((0.25 + 0.04 * math.sin(ph), 0.28, 0.55, QColor(77, 201, 255, 46)), (0.78, 0.7 + 0.04 * math.cos(ph * 1.3), 0.5, QColor(180, 140, 255, 40))):
            rg = QRadialGradient(W * cx, H * cy, max(W, H) * r); rg.setColorAt(0, col); rg.setColorAt(1, QColor(0, 0, 0, 0)); p.fillRect(self.rect(), rg)
        cy = H * 0.2; lw = 74; R = QRectF(W / 2 - lw / 2, cy - lw / 2, lw, lw); lg = QLinearGradient(R.topLeft(), R.bottomRight())
        lg.setColorAt(0, QColor(THEME['accent'])); lg.setColorAt(1, QColor('#8b6cff')); p.setBrush(lg); p.setPen(Qt.NoPen); p.drawRoundedRect(R, 20, 20)
        p.setBrush(QColor('#0b0e13')); p.drawEllipse(R.center(), 14, 14)
        f = QFont(); f.setPixelSize(48); f.setBold(True); p.setFont(f); p.setPen(QColor('#f2f6fb')); p.drawText(QRectF(0, cy + lw / 2 + 10, W, 62), Qt.AlignCenter, BRAND['name'])
        f2 = QFont(); f2.setPixelSize(15); p.setFont(f2); p.setPen(QColor('#8ea4bf')); p.drawText(QRectF(0, cy + lw / 2 + 72, W, 24), Qt.AlignCenter, f'{APP_TITLE}　·　V{APP_VERSION}')
        f3 = QFont(); f3.setPixelSize(13); p.setFont(f3); p.setPen(QColor('#9fb3c8')); wd = '一二三四五六日'[time.localtime().tm_wday]
        p.drawText(QRectF(0, 18, W - 28, 20), Qt.AlignRight | Qt.AlignVCenter, time.strftime('%Y-%m-%d') + f'（{wd}）　' + time.strftime('%H:%M'))
        p.end()


def app_icon():
    """設定裡換的圖示（Data）→ app\\icon.ico（有的話）；沒有就自己畫一個."""
    dd = getattr(ENG, 'data', ROOT / 'Data')
    for p_ in (dd / 'icon_512.png', HERE / 'icon.ico', ROOT / 'icon.ico', HERE / 'icon_512.png'):
        if p_.exists(): return QIcon(str(p_))
    pm = QPixmap(64, 64); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor(THEME['accent'])); p.setPen(Qt.NoPen); p.drawRoundedRect(4, 4, 56, 56, 14, 14); p.setBrush(QColor('#0b0e13')); p.drawEllipse(QPoint(32, 32), 11, 11); p.end()
    return QIcon(pm)


# ============================================================ 主視窗
class Main(QMainWindow):
    def __init__(self, adopt=None):
        try: QApplication.instance().setStyleSheet(theme_qss(ENG.cfg.get('ui_theme') or 'dark', ENG.cfg.get('ui_zoom') or 100))
        except Exception: pass
        super().__init__(); self.setWindowTitle(f'{APP_TITLE}  V{APP_VERSION}'); self.resize(1400, 880); self.quitting = False; self._handoff = False; self._upd_seen = set()
        self.icon = app_icon(); self.setWindowIcon(self.icon)
        try: QApplication.instance().setWindowIcon(self.icon)
        except Exception: pass
        cw = QWidget(); self.setCentralWidget(cw); v = QVBoxLayout(cw); v.setContentsMargins(0, 0, 0, 0); v.setSpacing(0)
        self.outer = QStackedWidget(); v.addWidget(self.outer, 1); self.mainw = QWidget(); mv = QVBoxLayout(self.mainw); mv.setContentsMargins(0, 0, 0, 0); mv.setSpacing(0)
        self._cover_ready = False
        split = QSplitter(Qt.Horizontal); split.setChildrenCollapsible(False); mv.addWidget(split, 1)
        side = QFrame(); side.setObjectName('side'); side.setMinimumWidth(180); side.setMaximumWidth(320); sl = QVBoxLayout(side); sl.setContentsMargins(10, 6, 10, 10); sl.setSpacing(5)
        self.nav = NavList(self._page); sl.addWidget(self.nav, 1)
        self.sys_panel = SysPanel(); self.sys_panel.setToolTip('電腦狀態：點一下打開／關掉「📊 效能」浮窗'); sl.addWidget(self.sys_panel)
        split.addWidget(side)
        content = QWidget(); cv_ = QVBoxLayout(content); cv_.setContentsMargins(0, 0, 0, 0); cv_.setSpacing(0)
        topf = QFrame(); topf.setObjectName('topbar'); top = QHBoxLayout(topf); top.setContentsMargins(12, 7, 10, 7); top.setSpacing(6); cv_.addWidget(topf)
        self.ptitle = QLabel(''); self.ptitle.setObjectName('ptitle'); top.addWidget(self.ptitle)
        self.stat = QLabel(''); self.stat.setObjectName('muted'); self.stat.setMinimumWidth(10); self.stat.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred); top.addWidget(self.stat, 1)
        self.b_perf = QPushButton('📊 效能'); self.b_perf.setCheckable(True); self.b_perf.setToolTip('電腦效能浮窗（左下角電腦狀態點一下也可以）')
        self.b_bg = QPushButton('🖥 後台'); self.b_hide = QPushButton('🌙 縮到背景'); self.b_hide.setToolTip('縮到右下角，背景繼續做')
        self.b_cover = QPushButton('🏠 封面'); self.b_cover.setToolTip('回到封面（Ctrl+L）：畫面上不留任何內容，背景照常做')
        for b_ in (self.b_perf, self.b_bg, self.b_hide, self.b_cover): b_.setObjectName('pill'); top.addWidget(b_)
        self.stack = QStackedWidget(); cv_.addWidget(self.stack, 1); split.addWidget(content); split.setStretchFactor(1, 1)
        try: split.setSizes([int(ENG.cfg.get('side_w') or 210), 1190])
        except Exception: pass
        self._sw_t = QTimer(self); self._sw_t.setSingleShot(True); self._sw_t.timeout.connect(lambda: ENG.cfg.set('side_w', int(split.sizes()[0])))
        split.splitterMoved.connect(lambda *_a: self._sw_t.start(600))
        # ---- 頁面（順序＝頁碼，NavList.GROUPS 用這個號碼）
        self.gen = GenPage(self); self.home = self.gen; self.hist = HistPage(self); self.bgp = BgPage(self); self.lab = LabPage(self); self.logp = LogPage(self); self.setp = SetPage(self); self.upd = UpdPage(self); self.helpp = HelpPage(self)
        self.PAGES = [self.home, self.bgp, self.lab, self.logp, self.setp, self.upd, self.helpp, self.hist]
        for w in self.PAGES: self.stack.addWidget(w if w in (self.logp, self.hist) else scroll_wrap(w))
        self.stack.setMinimumWidth(420)
        self.sys_panel.clicked.connect(lambda: self.b_perf.toggle()); self.b_bg.clicked.connect(lambda: self.nav.setCurrentRow(1))
        self.b_hide.clicked.connect(self.to_tray); self.b_perf.toggled.connect(self.perf); self.b_cover.clicked.connect(self.show_cover)
        self.nav.setCurrentRow(0)
        # ---- 下面狀態列：後台暫停中的項目、深色／淺色、介面大小
        sb = self.statusBar(); self.b_theme = QPushButton('◐ 深色／淺色'); self.b_theme.setObjectName('pill')
        self.b_zm = QPushButton('－'); self.b_zp = QPushButton('＋'); self.zoom_l = QLabel(f"{THEME_MODE['zoom']}%"); self.zoom_l.setObjectName('muted')
        for b_ in (self.b_zm, self.b_zp): b_.setObjectName('pill'); b_.setFixedWidth(34)
        zl = QLabel('介面大小'); zl.setObjectName('muted')
        self.b_bgst = QPushButton(''); self.b_bgst.setObjectName('pill'); self.b_bgst.setToolTip('後台：暫停中／讓路中的項目（點一下到「後台狀態」）'); self.b_bgst.hide()
        self.b_bgst.clicked.connect(lambda: self.nav.setCurrentRow(1))
        self.b_hs = QPushButton('🤝 Lv'); self.b_hs.setObjectName('pill'); self.b_hs.setToolTip('🤝 跟 SortCut、GoPro Fusion 360 分電腦效能（Lv 1～10、誰參與、分配）')   # V0.3.40
        self.b_hs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f'http://127.0.0.1:{int(ENG.cfg.get("web_port") or BRAND["web_port"])}/?pc=1&hs=1')))
        self._hs_t = QTimer(self); self._hs_t.timeout.connect(self._hs_paint); self._hs_t.start(5000)
        for w_ in (self.b_hs, self.b_bgst, self.b_theme, zl, self.b_zm, self.zoom_l, self.b_zp): sb.addPermanentWidget(w_)
        self.b_theme.clicked.connect(lambda: self.set_theme('light' if THEME_MODE['mode'] == 'dark' else 'dark'))
        self.b_zm.clicked.connect(lambda: self.set_zoom(THEME_MODE['zoom'] - 10)); self.b_zp.clicked.connect(lambda: self.set_zoom(THEME_MODE['zoom'] + 10))
        self.pf = None
        QTimer.singleShot(3000, arm_watchdog)
        if ENG.cfg.get('perf_float'): self.b_perf.setChecked(True)
        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable() and not SELFTEST:
            self.tray = QSystemTrayIcon(self.icon, self); m = QMenu(self)
            m.addAction('顯示視窗', self.from_tray); m.addAction('⏸ 背景工作全部暫停', lambda: ENG.bg_all(True)); m.addAction('▶ 背景工作全部繼續', lambda: ENG.bg_all(False))
            m.addSeparator(); m.addAction('結束', self.really_quit); self.tray_menu = m
            self.tray.setContextMenu(m); self.tray.activated.connect(lambda r: self.from_tray() if r in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
            self.tray.setToolTip(BRAND['name']); self.tray.show()
        self.lag_last = time.time(); self.lag = QTimer(self); self.lag.timeout.connect(self._lag); self.lag.start(500)
        self.st_t = QTimer(self); self.st_t.timeout.connect(self._status); self.st_t.start(1000)
        self.hb = QTimer(self); self.hb.timeout.connect(lambda: setattr(QApplication.instance(), '_ak_hb', time.time())); self.hb.start(250)
        # ---- 更新提示列：UPDATE 資料夾裡出現新的更新包
        self.ubar = QFrame(); self.ubar.setStyleSheet('QFrame{background:#1f3550;border-bottom:1px solid #4dc9ff}'); ub = QHBoxLayout(self.ubar); ub.setContentsMargins(10, 4, 10, 4)
        self.ubar_l = QLabel(''); ub.addWidget(self.ubar_l, 1); self.ubar_go = QPushButton('⚡ 立即熱更新'); self.ubar_skip = QPushButton('略過這版'); self.ubar_no = QPushButton('稍後')
        ub.addWidget(self.ubar_go); ub.addWidget(self.ubar_skip); ub.addWidget(self.ubar_no); self.ubar_skip.hide()
        v.insertWidget(0, self.ubar); self.ubar.hide(); self._ubar_path = ''; self._ubar_cloud = False
        self.ubar_go.clicked.connect(self._ubar_apply); self.ubar_no.clicked.connect(lambda: (self._upd_seen.add(self._ubar_path), self.ubar.hide()))
        self.ubar_skip.clicked.connect(lambda: (self.msg('☁ ' + cloudupd.op({'op': 'skip'}).get('message', ''), 8000), self.ubar.hide()))
        self._cloud_bind()
        self.ut = QTimer(self); self.ut.timeout.connect(self._watch_update); self.ut.start(5000)
        self.cover = CoverPage(self); self.outer.addWidget(self.cover); self.outer.addWidget(self.mainw)
        sc = QShortcut(QKeySequence('Ctrl+L'), self); sc.setContext(Qt.ApplicationShortcut); sc.activated.connect(self.show_cover)
        sc2 = QShortcut(QKeySequence('F1'), self); sc2.activated.connect(lambda: self.enter(6))
        self.last_act = time.time(); QApplication.instance().installEventFilter(self)
        self.idle_t = QTimer(self); self.idle_t.timeout.connect(self._idle_check); self.idle_t.start(15000)
        self.outer.setCurrentIndex(0 if ENG.cfg.get('cover_on_start') is not False else 1); self._cover_ready = True
        if adopt: self._adopt(adopt)

    # ---------- 熱更新：狀態交出去／接過來（新功能有要保留的畫面狀態就加在這兩個函式）
    def export_state(self):
        return {'page': self.nav.currentRow(), 'cover': self.outer.currentIndex() == 0, 'geo': bytes(self.saveGeometry()), 'max': self.isMaximized(),
                'visible': self.isVisible(), 'perf': self.b_perf.isChecked(), 'seen': list(self._upd_seen)}

    def _adopt(self, st):
        try:
            self._upd_seen = set(st.get('seen') or [])
            if st.get('geo'):
                from PySide6.QtCore import QByteArray
                self.restoreGeometry(QByteArray(st['geo']))
            self.nav.setCurrentRow(int(st.get('page') or 0)); self.outer.setCurrentIndex(0 if st.get('cover') else 1)
        except Exception: ENG.log.err('熱更新：接手畫面狀態')

    def show_after_hot(self, st):
        if st.get('visible', True): (self.showMaximized() if st.get('max') else self.show()); self.raise_(); self.activateWindow()
        notes = st.get('hot_notes') or []
        self.msg(f'⚡ 已熱更新：V{st.get("hot_from")} → V{APP_VERSION}（程式沒有關、背景工作沒有中斷）', 15000)
        if st.get('visible', True):
            QTimer.singleShot(400, lambda: QMessageBox.information(self, '已熱更新', f'V{st.get("hot_from")} → V{APP_VERSION}\n\n' + '\n'.join('• ' + str(x) for x in notes[:12]) + ('\n…' if len(notes) > 12 else '') + '\n\n程式沒有關，背景工作照常進行。'))

    def handoff(self):
        """舊視窗要被新版取代：停計時器、收托盤、關浮窗；不碰引擎."""
        self._handoff = True; self.quitting = True
        for t in self.findChildren(QTimer):
            try: t.stop()
            except Exception: pass
        for d in self.findChildren(QDialog):
            try: d.close()
            except Exception: pass
        try:
            if self.pf is not None: self.pf.close()
        except Exception: pass
        try:
            if self.tray: self.tray.hide()
        except Exception: pass
        try: QApplication.instance().removeEventFilter(self)
        except Exception: pass
        self.hide()

    def _watch_update(self):
        d = ROOT / 'UPDATE'; seen = set(self._upd_seen); cache = self.__dict__.setdefault('_pkg_cache', {})
        def look():
            new_seen = []
            try: Z = sorted([z for z in d.glob('*.zip') if '_Shell_L' not in z.name], key=lambda p: vkey(p.stem))   # V0.3.37 EXE 外殼不是程式更新包
            except Exception: Z = []
            for z in reversed(Z):
                if str(z) in seen: continue
                try: ck = (str(z), z.stat().st_mtime, z.stat().st_size)
                except Exception: continue
                if ck not in cache:
                    try: pk = load_pkg(z); cache[ck] = (pk['version'], pk['hot_ok'])
                    except Exception as ex: return ('bad', str(z), str(ex), False, new_seen)
                ver_, hot_ = cache[ck]
                if vkey(ver_) > vkey(APP_VERSION): return ('ok', str(z), ver_, hot_, new_seen)
                new_seen.append(str(z))
            return ('none', '', '', False, new_seen)
        bg(look, self._upd_found)

    def _upd_found(self, r):
        if not r: return
        self._upd_seen.update(r[-1])
        if r[0] == 'none' or self._handoff or r[1] in self._upd_seen or self.ubar.isVisible(): return
        self._ubar_path = r[1]
        if r[0] == 'bad': self._upd_seen.add(r[1]); self.msg(f'UPDATE 資料夾裡的 {Path(r[1]).name} 不能用：{r[2]}', 15000); return
        self.ubar_l.setText(f'🆕 發現更新包 <b>{esc_html(Path(r[1]).name)}</b>：V{APP_VERSION} → V{esc_html(r[2])}' + ('（可以熱更新，程式不用關）' if r[3] else '（要重開程式套用）'))
        self.ubar_go.setText('⚡ 立即熱更新' if r[3] else '🔁 重開程式套用'); self.ubar.show(); upd_log(f'發現更新包：{r[1]}（V{r[2]}）')

    # ---------- V0.3.36 ☁ 雲端更新（GitHub Releases）：有新版只提示；按「更新」才下載（背景、低優先、限速）
    def _cloud_bind(self):
        def busy():
            out = []
            try:
                a = len(ENG.gen_active); q = len(ENG.gen_q); d = ENG.bg_running('dl')
                if a: out.append(f'🎨 正在生圖 {a} 張')
                if q: out.append(f'排隊 {q} 張')
                if d: out.append(f'⬇ 正在下載模型 {d} 個')
            except Exception: pass
            return out
        cloudupd.bind(eng=ENG, ver=APP_VERSION, brand=BRAND, busy=busy, notify=lambda m: ui(lambda m=m: self._cloud_bar(m)),
                      apply_zip=lambda p: ui(lambda p=p: self._cloud_apply(p)), swap=lambda z: ui(lambda z=z: self._cloud_swap(z)))
        try:                                                                    # V0.3.37 V0.3.36 把 EXE 外殼放在 UPDATE → 啟動器每次開都說「套用失敗」：移到 Data\\cloud
            for z in (ROOT / 'UPDATE').glob('*_Shell_L*.zip'):
                (ENG.data / 'cloud').mkdir(parents=True, exist_ok=True); os.replace(str(z), str(ENG.data / 'cloud' / z.name)); upd_log(f'把 UPDATE 裡的 {z.name} 移到 Data\\cloud（它是 EXE 外殼，不是程式更新包）')
        except Exception: pass
        try: hslink.bind(eng=ENG, ver=APP_VERSION, port=int(ENG.cfg.get('web_port') or BRAND['web_port']))   # V0.3.40 🤝 跟 SortCut／FusionStitch 握手
        except Exception: ENG.log.err('握手：啟動')
        try: cloudupd.shell_ok_later(ROOT, BRAND['id'] + '.exe'); cloudupd.loop_start()
        except Exception: ENG.log.err('雲端更新：啟動')

    def _hs_paint(self):
        try:                                                                    # V0.3.55 連不到 ComfyUI 3 分鐘／卡住：狀態列＋托盤通知一次
            w = getattr(ENG, 'gen_wait', '') and len(ENG.gen_q) and time.time() - getattr(ENG, 'gen_wait_t', time.time()) > 180
            st = [j for j, J in list(ENG.gen_active.items()) if J.get('stall')]
            key = ('w' if w else '') + ','.join(map(str, st))
            if key and key != getattr(self, '_stall_told', ''):
                m = (f'連不到 ComfyUI 已 {int((time.time() - ENG.gen_wait_t) / 60)} 分鐘，排隊 {len(ENG.gen_q)} 張在等（ComfyUI 有開嗎？記憶體夠嗎？）' if w else
                     f'ComfyUI 卡住沒進度（#{"、#".join(map(str, st))}）：多半記憶體不夠，可以按手機卡片的「🔄 中斷重來」，20 分鐘會自動重來')
                self.msg('⚠ ' + m, 60000)
                try:
                    if self.tray: self.tray.showMessage(BRAND['name'] + ' · 生圖卡住了', m, QSystemTrayIcon.Warning, 15000)
                except Exception: pass
            self._stall_told = key
        except Exception: pass
        try:
            I = hslink.info()
            if I.get('ok'): self.b_hs.setText(f"🤝 Lv{I['lv']}" + (f" · {I['cap']:.0f}%" if I.get('cap') is not None else '')); self.b_hs.setToolTip('🤝 ' + str(I.get('why') or '') + '\n點一下：Lv 1～10、這台有誰參與、分配')
        except Exception: pass

    def _cloud_bar(self, m):
        if self._handoff: return
        I = cloudupd.info(); c = I.get('chk') or {}
        if not c.get('newer') or c.get('skipped'): return
        self._ubar_cloud = True; self._ubar_path = 'cloud:' + str(I.get('ver'))
        self.ubar_l.setText(f"☁ 雲端有新版 <b>V{esc_html(I.get('ver'))}</b>（現在 V{APP_VERSION}）" + ('　⚠ 這次要換 EXE（程式會關掉再自動打開）' if c.get('need_shell') else '　可以熱更新，生圖不中斷'))
        self.ubar_go.setText('☁ 更新'); self.ubar_skip.setVisible(not c.get('need_shell')); self.ubar.show()
        try:
            if self.tray: self.tray.showMessage(BRAND['name'] + ' · 有新版', m, QSystemTrayIcon.Information, 10000)
        except Exception: pass
        self.msg('☁ ' + m + '：按上面的「☁ 更新」，或到「⟳ 版本與更新」', 30000)

    def cloud_update(self, parent=None):
        """桌面按「更新」：要換 EXE 又有工作在做 → 先問（列出在做什麼）."""
        r = cloudupd.op({'op': 'update'})
        if r.get('need_confirm'):
            if QMessageBox.question(parent or self, '要換 EXE（程式會關掉再自動打開）', r['message'] + '\n\n確定現在更新？', QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes: return
            r = cloudupd.op({'op': 'update', 'force': True})
        self.msg(('☁ ' if r.get('ok') else '✖ ') + r.get('message', ''), 15000)

    def _cloud_apply(self, path):
        """下載好的程式更新包（SHA-256 對過）→ 熱更新（不用關程式）；這版不能熱更新 → 放 UPDATE，下次開程式套用（不會自己重開）."""
        try: pkg = load_pkg(path)
        except Exception as ex: upd_log(f'雲端更新包不能用：{ex}'); self.msg(f'✖ 雲端更新包不能用：{ex}', 15000); return
        if not pkg.get('hot_ok'):
            try: d = ROOT / 'UPDATE'; d.mkdir(exist_ok=True); shutil.copy2(path, d / Path(path).name)
            except Exception: pass
            self.msg(f"☁ V{pkg['version']} 下載好了，這版要重開程式才會套用（已放進 UPDATE）", 30000); return
        try: self.upd.pkg = pkg
        except Exception: pass
        hot_update(self, pkg)

    def _cloud_swap(self, shell_zip):
        """換 EXE：寫 BAT → 開 BAT（程式關了它還在跑）→ 正常關掉程式（下次開排隊的生圖接著做）→ BAT 換好 EXE 再打開."""
        try:
            bat = cloudupd.write_bat(ROOT, shell_zip, os.getpid(), BRAND['id'] + '.exe')
            B = cloudupd.busy(); cloudupd.log('換 EXE：程式先關掉' + ('（' + '、'.join(B) + '；開起來排隊的會接著做）' if B else '') + '，BAT 換好會自動打開')
            cloudupd.run_bat(bat)
        except Exception as ex:
            cloudupd._S['busy'] = False; cloudupd._S['msg'] = f'換 EXE 準備失敗（程式沒關）：{ex}'; cloudupd.log(f'換 EXE 準備失敗（程式照常執行）：{ex}'); return
        threading.Thread(target=lambda: (time.sleep(15), os._exit(0)), daemon=True).start()   # 萬一關不掉：15 秒後強制結束（BAT 在等）
        self.quitting = True
        try: self.close()
        except Exception: os._exit(0)

    def _ubar_apply(self):
        if self._ubar_cloud:
            self._ubar_cloud = False; self.ubar.hide(); self.cloud_update(); return
        self.ubar.hide(); self._upd_seen.add(self._ubar_path)
        if not self.upd.load(self._ubar_path): self.nav.setCurrentRow(5); return
        if self.upd.pkg.get('hot_ok'): self.upd.go()
        else: self.upd.restart_way()

    # ---------- 封面、切頁
    def show_cover(self):
        self.outer.setCurrentIndex(0); self.cover.refresh(); ENG.log.w('畫面：回到封面')

    def enter(self, page):
        self.outer.setCurrentIndex(1); was_ = self.nav.currentRow(); self.nav.setCurrentRow(int(page))
        if was_ == int(page): self._page(int(page))

    def eventFilter(self, obj, e):
        try:
            if e.type() in (QEvent.MouseButtonPress, QEvent.KeyPress, QEvent.Wheel): self.last_act = time.time()
        except Exception: pass
        return False

    def _idle_check(self):
        m = int(ENG.cfg.get('cover_idle_min') or 0)
        if m and self.outer.currentIndex() == 1 and time.time() - self.last_act > m * 60: self.show_cover(); ENG.log.w(f'閒置 {m} 分鐘，自動回到封面')

    def _page(self, i):
        i = int(i)
        if not hasattr(self, 'stack') or not (0 <= i < self.stack.count()): return
        self.stack.setCurrentIndex(i)
        if self._cover_ready and self.outer.currentIndex() == 0: self.outer.setCurrentIndex(1)
        if self._cover_ready and i not in (3, 5): ENG.cfg.set('last_page', i)
        try: self.ptitle.setText(f'{self.nav.page_icon(i)} {self.nav.page_name(i)}'.strip())
        except Exception: pass
        ENG.log.w(f'畫面：切到「{self.nav.page_name(i)}」')

    # ---------- 外觀
    def set_theme(self, mode):
        mode = set_theme_mode(mode); ENG.cfg.set('ui_theme', mode); QApplication.instance().setStyleSheet(theme_qss(mode)); self.update()
        for w_ in self.findChildren(QWidget):
            try: w_.update()
            except Exception: pass
        self.msg('主題：' + ('☀ 淺色' if mode == 'light' else '🌙 深色'), 3000)

    def set_zoom(self, z):
        z = max(70, min(160, int(z))); ENG.cfg.set('ui_zoom', z); QApplication.instance().setStyleSheet(theme_qss(None, z)); self.zoom_l.setText(f'{z}%'); self.msg(f'介面大小 {z}%', 2500)

    def msg(self, s, ms=6000):
        self.statusBar().showMessage(str(s), ms); ENG.log.w('畫面：' + str(s))

    def perf(self, on):
        ENG.cfg.set('perf_float', bool(on))
        if on:
            if self.pf is None:
                self.pf = PerfFloat(); pos = ENG.cfg.get('perf_pos')
                if pos: self.pf.move(int(pos[0]), int(pos[1]))
                else: self.pf.move(self.x() + self.width() - 280, self.y() + 70)
            self.pf.show()
        elif self.pf is not None: self.pf.hide()

    def _status(self):
        bg(ENG.info, self._st)
        try:
            nm = dict((k, n) for k, _i, n in ENG.BG_KINDS); P = [nm.get(k, k) for k, v_ in list(ENG.bg_pause.items()) if v_]; H = [nm.get(k, k) for k in list(ENG.bg_auto)]
            t_ = ('⏸ ' + '、'.join(P) if P else '') + ('　' if P and H else '') + ('⚖ 讓路：' + '、'.join(H) if H else '')
            self.b_bgst.setText(t_); self.b_bgst.setVisible(bool(t_))
        except Exception: pass

    def _st(self, I):
        txt = f"　生圖：進行中 {I.get('gen_run', 0)}・排隊 {I.get('gen_wait', 0)}・這次開程式完成 {I.get('gen_done', 0)}"
        self.stat.setText(txt); n_ = I.get('gen_wait', 0) + I.get('gen_run', 0); self.nav.set_badge(0, str(n_) if n_ else '')
        P = ENG.perf; g = P.gpu or {}
        rows = [('CPU', P.cpu, f'{P.cpu:.0f}%', None, '#4dc9ff'), ('RAM', P.ram, f'{P.ram:.0f}%', None, '#b48cff')]
        if g:
            rows.append(('GPU', g.get('util'), f'{g.get("util", 0):.0f}%', g.get('temp'), '#45d483'))
            if g.get('mem_t'): rows.append(('VRAM', 100 * g['mem'] / g['mem_t'], f'{100 * g["mem"] / g["mem_t"]:.0f}%', None, '#9aa5b3'))
        self.sys_panel.set_rows(rows)
        if self.tray: self.tray.setToolTip(BRAND['name'] + txt.replace('　', '\n'))

    def _lag(self):
        now = time.time(); gap = now - self.lag_last - 0.5; self.lag_last = now
        try: lim = float(ENG.cfg.get('freeze_log_s') or 2)
        except Exception: lim = 2.0
        if gap >= lim: ENG.log.w(f'畫面卡了 {gap:.1f} 秒　頁面={self.nav.currentRow()}　CPU {ENG.perf.cpu:.0f}%', 'ui_freeze_log.txt')

    # ---------- 托盤、關閉、重開
    def to_tray(self):
        if self.tray: self.hide(); self.tray.showMessage(BRAND['name'], '在背景繼續做；點右下角圖示打開', QSystemTrayIcon.Information, 3000)
        else: self.showMinimized()

    def from_tray(self):
        if ENG.cfg.get('cover_on_restore'): self.show_cover()
        self.show(); self.setWindowState(self.windowState() & ~Qt.WindowMinimized); self.raise_(); self.activateWindow()

    def closeEvent(self, e):
        if self._handoff: e.accept(); return
        if not self.quitting and self.tray and ENG.cfg.get('close_to_tray'): e.ignore(); self.to_tray(); return
        self.quitting = True
        if self.pf is not None: self.pf.close()
        if self.tray: self.tray.hide()
        try:
            s_ = web_server(create=False)
            if s_ is not None: s_.close()
        except Exception: pass
        mark_clean_exit()
        try: hslink.stop()
        except Exception: pass
        ENG.shutdown(); e.accept(); QApplication.instance().quit()

    def really_quit(self):
        busy = sum(ENG.bg_running(k) for k, _i, _n in ENG.BG_KINDS)
        if busy and QMessageBox.question(self, '結束', f'還有 {busy} 個工作在做（下次打開會接著做）。確定結束？') != QMessageBox.Yes: return
        self.quitting = True; self.close()

    def restart(self):
        self.quitting = True; mark_clean_exit()
        exe = sys.executable; rest = [a for a in sys.argv[1:] if a != '--restart' and not a.startswith('--oldpid=')] + ['--restart', f'--oldpid={os.getpid()}']
        args = rest if getattr(sys, 'frozen', False) else [str(HERE / 'app.py')] + rest
        try: subprocess.Popen([exe] + args, cwd=str(ROOT), creationflags=0x00000008 if core.IS_WIN else 0)
        except Exception as ex: QMessageBox.warning(self, '重新開啟', f'沒辦法自己重開，請手動打開程式：{ex}')
        self.close()


# ============================================================ 防當機／查問題
def _install_guards(app):
    """程式整個掛掉的傾印、背景執行緒的錯誤、Qt 的警告、畫面卡住時卡在哪一行。熱更新時新版也會叫一次（不重複裝）."""
    sys.excepthook = lambda t, v, tb: _eng_log('未處理的錯誤（程式沒有關）：\n' + ''.join(traceback.format_exception(t, v, tb)), 'error_log.txt')
    threading.excepthook = lambda a: _eng_log(f'背景執行緒 {getattr(a.thread, "name", "?")} 出錯（程式沒有關）：\n' + ''.join(traceback.format_exception(a.exc_type, a.exc_value, a.exc_traceback)), 'error_log.txt')
    seen = {}
    def qt_msg(mode, ctx, msg):
        try:
            k = str(msg)[:200]; now = time.time()
            if now - seen.get(k, 0) < 60: return
            seen[k] = now
            if len(seen) > 500: seen.clear()
            _eng_log(f'Qt：{msg}', 'qt_log.txt')
        except Exception: pass
    try: qInstallMessageHandler(qt_msg)
    except Exception: pass
    if getattr(app, '_ak_guards', False): return
    app._ak_guards = True
    try:
        (ROOT / 'LOG').mkdir(exist_ok=True); fh = open(ROOT / 'LOG' / 'crash_dump.txt', 'a', encoding='utf-8')
        fh.write(f'\n===== {time.strftime("%Y-%m-%d %H:%M:%S")} 啟動 V{APP_VERSION}（如果程式整個掛掉，這下面會有每條執行緒在做什麼）=====\n'); fh.flush()
        faulthandler.enable(file=fh, all_threads=True); app._ak_fault_fh = fh
    except Exception: pass
    app._ak_hb = time.time()
    def watchdog():
        dumped = 0
        while True:
            time.sleep(0.5)
            try:
                gap = time.time() - float(getattr(app, '_ak_hb', time.time())); e = getattr(app, '_ak_eng', None)
                lim = max(3.0, float(e.cfg.get('freeze_log_s') or 2) + 1.0) if e else 4.0
                if gap >= lim and not dumped:
                    fr = sys._current_frames().get(threading.main_thread().ident)
                    _eng_log(f'⚠ 畫面已經卡住 {gap:.1f} 秒，主執行緒現在卡在：\n' + (''.join(traceback.format_stack(fr)[-14:]) if fr else '（讀不到）'), 'ui_freeze_log.txt'); dumped = 1
                elif gap < 1 and dumped: dumped = 0
            except Exception: pass
    threading.Thread(target=watchdog, name='UiWatchdog', daemon=True).start()


def _eng_log(msg, f='app_log.txt'):
    try: (getattr(QApplication.instance(), '_ak_eng', None) or ENG).log.w(msg, f)
    except Exception:
        try:
            with open(ROOT / 'LOG' / f, 'a', encoding='utf-8') as fh: fh.write(f'[{time.strftime("%Y-%m-%d %H:%M:%S")}] {msg}\n')
        except Exception: pass


def _connect_peer(app):
    """只能開一個：第二次打開時叫出原本那個的視窗."""
    srv = getattr(app, '_ak_srv', None)
    if srv is None: return
    try: srv.newConnection.disconnect()
    except Exception: pass
    def _peer():
        c = srv.nextPendingConnection()
        if c: c.disconnectFromServer(); c.deleteLater()
        w = getattr(app, '_ak_main', None)
        if w is not None and not w.quitting: w.from_tray()
    srv.newConnection.connect(_peer)


# ============================================================ 📱 手機網頁伺服器（放在 QApplication 上，熱更新時換成新版的）
def web_server(create=True):
    app = QApplication.instance(); s = getattr(app, '_ak_web', None)
    if type(s).__name__ != 'WebServer': s = None
    if s is None and create:
        s = web.WebServer(lambda: QApplication.instance()._ak_eng, lambda: QApplication.instance()._ak_main, ui, lambda: sys.modules[__name__], APP_VERSION, BRAND); app._ak_web = s
    return s


def web_apply():
    """照設定開／關手機網頁（埠、區網選項改了就重開）."""
    try:
        on = bool(ENG.cfg.get('web_on')); port = int(ENG.cfg.get('web_port') or BRAND['web_port']); lan = bool(ENG.cfg.get('web_lan'))
        s = web_server(create=on)
        if s is None: return
        if not on: s.close(); return
        if s.running and s.port == port and s.bind == ('0.0.0.0' if lan else '127.0.0.1'): return
        s.start(port, lan)
    except Exception: ENG.log.err('手機網頁 開／關')


def web_restart_new():
    """熱更新：舊版的伺服器關掉，換成新版的（同一個埠）。埠還沒放開就 1 秒後再試."""
    app = QApplication.instance(); old = getattr(app, '_ak_web', None)
    if type(old).__name__ == 'WebServer':
        try: old.close()
        except Exception: pass
        app._ak_web = None
    def again(n=0):
        web_apply(); s = web_server(create=False)
        if s is not None and ENG.cfg.get('web_on') and not s.running and n < 5: QTimer.singleShot(1000, lambda: again(n + 1))
    again()


def hot_start(old_eng, state):
    """熱更新進來的入口（舊版呼叫）：新引擎（還沒開始跑）＋新視窗。失敗就丟例外，舊版會還原."""
    global BUS, ENG
    app = QApplication.instance(); BUS = Bus()
    ENG = core.Engine(ROOT, adopt=old_eng, start=False, version=APP_VERSION)
    old_main = getattr(app, '_ak_main', None); old_e = getattr(app, '_ak_eng', None); before = set(map(id, QApplication.topLevelWidgets())); w = None
    try:
        w = Main(adopt=state); app._ak_main = w; app._ak_eng = ENG; _install_guards(app); _connect_peer(app)
        try: app.commitDataRequest.disconnect()
        except Exception: pass
        app.commitDataRequest.connect(_on_commit)
        if state.get('perf'): w.b_perf.setChecked(True)
        try: web_restart_new()
        except Exception: ENG.log.err('熱更新：手機網頁換新版')
    except Exception:
        for tw in QApplication.topLevelWidgets():
            if id(tw) in before: continue
            try:
                if isinstance(tw, Main): tw.handoff()
                tw.close(); tw.deleteLater()
            except Exception: pass
        app._ak_main = old_main; app._ak_eng = old_e
        try:
            if old_main is not None: app.commitDataRequest.connect(_on_commit)
        except Exception: pass
        ENG.discard(); raise
    return w, ENG


# ============================================================ 閃退自動重開（Windows：另外一個 PowerShell 看著，主程式不見又沒有正常結束的記號就重開）
WATCHDOG_PS1 = r'''param([int]$procid, [string]$flag, [string]$exe, [string]$argline, [string]$cwd, [string]$log, [long]$ft = 0)
try {
  $p = Get-Process -Id $procid -ErrorAction SilentlyContinue
  if ($p -and ($ft -eq 0 -or [math]::Abs($p.StartTime.ToFileTimeUtc() - $ft) -lt 20000000)) { $p.WaitForExit() }
} catch {}
Start-Sleep -Seconds 4
if (Test-Path -LiteralPath $flag) { Remove-Item -LiteralPath $flag -ErrorAction SilentlyContinue; exit }
$t = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content -LiteralPath $log -Value "[$t] watchdog: PID $procid did not exit normally -> restarting" -Encoding UTF8
if ($argline) { Start-Process -FilePath $exe -ArgumentList $argline -WorkingDirectory $cwd } else { Start-Process -FilePath $exe -WorkingDirectory $cwd }
'''


def run_state_path(): return ENG.data / 'run_state.json'


def _on_commit(_m=None):
    """Windows 關機／登出：標記正常結束（不要重開）；關機被取消的話 1 分鐘後把記號拿掉."""
    try: setattr(getattr(QApplication.instance(), '_ak_main', None), 'quitting', True)
    except Exception: pass
    mark_clean_exit()
    try: QTimer.singleShot(60000, _commit_cancelled)
    except Exception: pass


def _commit_cancelled():
    try: (ENG.data / f'clean_exit_{os.getpid()}.flag').unlink()
    except Exception: pass
    try:
        st = json.loads(run_state_path().read_text(encoding='utf-8')) if run_state_path().exists() else {}
        st.update(clean=False); run_state_path().write_text(json.dumps(st), encoding='utf-8')
        w = getattr(QApplication.instance(), '_ak_main', None)
        if w is not None: w.quitting = False
    except Exception: pass


def _proc_ft():
    try:
        import ctypes
        from ctypes import wintypes
        a, b, c, d = (wintypes.FILETIME() for _ in range(4))
        if ctypes.windll.kernel32.GetProcessTimes(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(a), ctypes.byref(b), ctypes.byref(c), ctypes.byref(d)):
            return (a.dwHighDateTime << 32) | a.dwLowDateTime
    except Exception: pass
    return 0


def mark_clean_exit():
    try:
        (ENG.data / f'clean_exit_{os.getpid()}.flag').write_text(time.strftime('%Y-%m-%d %H:%M:%S'), encoding='utf-8')
        st = json.loads(run_state_path().read_text(encoding='utf-8')) if run_state_path().exists() else {}
        st.update(clean=True, t_end=time.time()); run_state_path().write_text(json.dumps(st), encoding='utf-8')
    except Exception: pass


def arm_watchdog(win=None):
    """①上次是不是閃退 → 記 LOG、提醒（10 分鐘內第 2 次：背景工作先全部暫停）②開看門狗（10 分鐘內閃退 3 次就先不開，避免一直重開）."""
    app = QApplication.instance()
    if getattr(app, '_ak_wd_armed', False) or SELFTEST: return
    app._ak_wd_armed = True; app.aboutToQuit.connect(mark_clean_exit)
    try: st = json.loads(run_state_path().read_text(encoding='utf-8')) if run_state_path().exists() else {}
    except Exception: st = {}
    crashes = [t for t in (st.get('crashes') or []) if time.time() - t < 600]
    if st and st.get('clean') is False:
        crashes.append(time.time()); ENG.log.w(f'⚠ 上次（PID {st.get("pid")}）沒有正常結束（閃退／當機）' + ('，看門狗自動重開了' if '--after-crash' in sys.argv else ''))
        if len(crashes) >= 2:
            try: ENG.bg_all(True); ENG.log.w('⚠ 10 分鐘內閃退 2 次以上：背景工作先全部暫停（到「🖥 後台」按繼續）')
            except Exception: pass
        QTimer.singleShot(5000, lambda: (getattr(QApplication.instance(), '_ak_main', None) or type('N', (), {'msg': lambda *a: None})()).msg('⚠ 上次程式意外關閉（閃退），LOG 有紀錄', 20000))
    try: run_state_path().write_text(json.dumps({'pid': os.getpid(), 't': time.time(), 'clean': False, 'crashes': crashes, 'ver': APP_VERSION}), encoding='utf-8')
    except Exception: pass
    if not core.IS_WIN or ENG.cfg.get('auto_restart') is False: return
    if len(crashes) >= 3: ENG.log.w(f'⚠ 10 分鐘內閃退 {len(crashes)} 次：這次先不開看門狗'); return
    try:
        ps1 = ENG.data / 'watchdog.ps1'; ps1.write_text(WATCHDOG_PS1, encoding='utf-8-sig')
        exe = sys.executable; rest = [a for a in sys.argv[1:] if a not in ('--restart', '--after-crash') and not a.startswith('--oldpid=')] + ['--restart', '--after-crash']
        args = rest if getattr(sys, 'frozen', False) else [str(HERE / 'app.py')] + rest
        flag = ENG.data / f'clean_exit_{os.getpid()}.flag'
        try: flag.unlink()
        except Exception: pass
        psx = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe')
        if not os.path.isfile(psx): psx = 'powershell'
        if not getattr(sys, 'frozen', False) and exe.lower().endswith('python.exe') and os.path.isfile(exe[:-10] + 'pythonw.exe'): exe = exe[:-10] + 'pythonw.exe'
        cmd = [psx, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', str(ps1), '-procid', str(os.getpid()), '-flag', str(flag),
               '-exe', exe, '-argline', subprocess.list2cmdline(args), '-cwd', str(ROOT), '-log', str(ROOT / 'LOG' / 'app_log.txt'), '-ft', str(_proc_ft())]
        for fl in (0x08000000 | 0x00000200 | 0x01000000, 0x08000000 | 0x00000200):
            try: app._ak_wd = subprocess.Popen(cmd, creationflags=fl, close_fds=True, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); ENG.log.w('看門狗開好了：閃退會自動重開'); break
            except OSError: continue
        for old in ENG.data.glob('clean_exit_*.flag'):
            if old.name != flag.name:
                try:
                    if time.time() - old.stat().st_mtime > 3600: old.unlink()
                except Exception: pass
    except Exception: ENG.log.err('看門狗')


def _pid_gone(pid):
    try:
        if core.IS_WIN:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x00100000, False, int(pid))
            if not h: return True
            try: return ctypes.windll.kernel32.WaitForSingleObject(h, 0) == 0
            finally: ctypes.windll.kernel32.CloseHandle(h)
        os.kill(int(pid), 0); return False
    except Exception: return True


def main():
    global BUS, ENG
    t_boot = time.time()
    app = QApplication.instance() or QApplication(sys.argv); app.setApplicationName(BRAND['id']); app.setStyleSheet(STYLE); app.setQuitOnLastWindowClosed(False)
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    if not SELFTEST:
        t_end = time.time() + (25 if '--restart' in sys.argv else 0)
        opid = next((int(a.split('=', 1)[1]) for a in sys.argv if a.startswith('--oldpid=') and a.split('=', 1)[1].isdigit()), 0)
        if opid: t_end = time.time() + 120
        while True:                                                             # 只能開一個（重開時等舊的關掉）
            s = QLocalSocket(); s.connectToServer(SINGLE)
            if not s.waitForConnected(300): break
            s.abort()
            if opid and time.time() <= t_end and _pid_gone(opid): time.sleep(0.5); continue
            if time.time() > t_end: QMessageBox.information(None, BRAND['name'], f'{BRAND["name"]} 已經開著了（看右下角的圖示）。'); return 0
            time.sleep(0.5)
        srv = QLocalServer(); QLocalServer.removeServer(SINGLE); srv.listen(SINGLE); app._ak_srv = srv
    BUS = Bus(); ENG = core.Engine(ROOT, version=APP_VERSION); app._ak_eng = ENG
    _install_guards(app)
    try: arm_watchdog()
    except Exception: ENG.log.err('看門狗')
    w = Main(); w.show(); app._ak_main = w
    web_apply()
    ENG.log.w(f'啟動完成：畫面出來花 {time.time() - t_boot:.1f} 秒')
    app.commitDataRequest.connect(_on_commit)
    if not SELFTEST: _connect_peer(app)
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
