"""🤝 跟同一台電腦的 SortCut、GoPro Fusion 360（FusionStitch）握手（V0.3.40，共用 app_handshake.py 規則第 3 版）.

- ComfyRemote 有生圖在做或排隊 → want 2，而且是「最優先的程式」：其他程式降到各 5%，這邊 80%，留 10% 給你。
- 沒在生圖 → want 0：另外兩個照平常 45／45 分（只有一個在做就給它 90）。
- 右上角 Lv：看三個程式現在各分到多少、勾這台電腦有誰參與、調分配、這邊的 Lv 1～10。
- ComfyRemote 本身幾乎不吃電腦（重的是 ComfyUI），所以這邊的 Lv 是「最多跟別人要幾 %」，讓出來的給另外兩個。
沒有 Qt。熱更新會重新載入這個模組：握手物件放在 builtins 裡，新舊版本共用（不會斷線、不會重寫檔）。
"""
import builtins
import time

import app_handshake as HS

APP = 'ComfyRemote'
_S = builtins.__dict__.setdefault('_ak_hslink', {'hs': None, 'ctx': {}})


def bind(**kw):
    """eng（引擎）、ver、port."""
    _S['ctx'].update(kw)
    hs = _S.get('hs')
    if hs is None:
        hs = _S['hs'] = HS.Handshake(APP, 'ComfyRemote', str(kw.get('ver') or ''), port=int(kw.get('port') or 0), state=state)
        hs.start()
    else:
        hs.ver = str(kw.get('ver') or hs.ver); hs.state = state
    return hs


def state():
    """V0.3.43 只在「真的有在做」時才跟別人要效能（不要讓另外兩個為了一個卡住的 ComfyUI 一直跑 5%）：
    - 連不到 ComfyUI（排隊在等它開）→ want 1：不跟別人要
    - 生圖暫停 → want 0
    - 有工作、ComfyUI 有在動 → want 2（最優先）
    - 卡住（8 分鐘沒進度）→ 先請別人放掉顯示卡 10 分鐘（規則第 4 版 starved）；還是沒動 → want 1，別人照常全速（20 分鐘會自動中斷重來）"""
    E = _S['ctx'].get('eng'); a = q = 0
    try: A = list(E.gen_active.values()); a = len(A); q = len(E.gen_q)
    except Exception: A = []
    P3 = HS.policy3(); base = {'on': True, 'prio': 5, 'lv': P3['lv'].get(APP, 10), 'use': _mem(E), 'max': {}, 'need': {}}
    if not (a or q): return {**base, 'want': 0, 'what': ''}
    try:
        if E.bg_hold('gen'): return {**base, 'want': 0, 'what': f'生圖暫停中（排隊 {q} 張）'}
    except Exception: pass
    if getattr(E, 'gen_wait', '') and not a: return {**base, 'want': 1, 'what': f'等 ComfyUI（連不到）：排隊 {q} 張，先不跟別人要效能'}
    now = time.time(); stall = [J for J in A if J.get('stall')]
    what = f'生圖：正在做 {a} 張' + (f'、排隊 {q} 張' if q else '')
    if stall:
        age = (now - min(J['stall'] for J in stall)) / 60
        if age >= 10:
            return {**base, 'want': 1, 'what': f'ComfyUI 卡住沒進度（已請別人讓顯示卡 10 分鐘還是沒動）：先不跟別人要效能，會自動中斷重來'}
        return {**base, 'want': 2, 'what': what + '（卡住：請別人先讓顯示卡）', 'need': {'starved': True, 'why': 'ComfyUI 卡住沒進度', 'vram_free_gb': _vram(E)}}
    vf = _vram(E)
    if a and vf is not None and vf < 1.0:
        return {**base, 'want': 2, 'what': what, 'need': {'starved': True, 'vram_free_gb': vf, 'why': f'顯示卡記憶體只剩 {vf:.1f} GB'}}
    return {**base, 'want': 2, 'what': what}


def _mem(E):
    """ComfyUI 回報的顯示卡記憶體、RAM（給 Lv 畫面看是誰佔住）."""
    try:
        st = E.comfy_status() or {}; v = st.get('vram') or [None, None]; r = st.get('ram') or [None, None]; G = 2**30; out = {}
        if v[1]: out.update(vram_free_gb=round((v[0] or 0) / G, 1), vram_total_gb=round(v[1] / G, 1))
        if r[1]: out.update(ram_free_gb=round((r[0] or 0) / G, 1), ram_total_gb=round(r[1] / G, 1))
        return out
    except Exception: return {}


def _vram(E):
    try:
        v = (E.comfy_status() or {}).get('vram') or [None, None]
        return round(v[0] / 2**30, 2) if v[0] is not None else None
    except Exception: return None


def stop(remove=True):
    hs = _S.get('hs')
    if hs is not None: hs.stop(remove=remove); _S['hs'] = None


def info():
    """手機／電腦的 Lv 畫面用：三個程式在不在、各分到多少、設定."""
    hs = _S.get('hs')
    if hs is None: return {'ok': False, 'message': '握手還沒開始'}
    try: hs.read()
    except Exception: pass
    d = hs.decide(); P3 = HS.policy3(); me = hs.me or {}
    states = {APP: me} if me else {}
    for p in hs.peers(): states.setdefault(str(p.get('app') or ''), p)
    A = HS.alloc3(states, P3) if P3.get('on', True) else {}
    apps = []
    seen = {str(p.get('app')): p for p in hs.peers()}
    for k, nm in HS.KNOWN:
        p = me if k == APP else seen.get(k)
        apps.append({'app': k, 'name': nm, 'on': p is not None, 'ver': (p or {}).get('ver', ''), 'want': int((p or {}).get('want') or 0),
                     'what': (p or {}).get('what', ''), 'member': (not P3['members']) or k in P3['members'], 'lv': P3['lv'].get(k, 10),
                     'cap': (A.get(k) or {}).get('cap'), 'mode': (A.get(k) or {}).get('mode', ''), 'why': (A.get(k) or {}).get('why', ''),
                     'rules': (p or {}).get('rules'), 'use': dict((p or {}).get('use') or {})})
    for k, p in seen.items():                                                   # 不認得的程式也列出來
        if k not in dict(HS.KNOWN):
            apps.append({'app': k, 'name': p.get('name') or k, 'on': True, 'ver': p.get('ver', ''), 'want': int(p.get('want') or 0), 'what': p.get('what', ''),
                         'member': (not P3['members']) or k in P3['members'], 'lv': P3['lv'].get(k, 10), 'cap': (A.get(k) or {}).get('cap'),
                         'mode': (A.get(k) or {}).get('mode', ''), 'why': (A.get(k) or {}).get('why', ''), 'rules': p.get('rules')})
    return {'ok': True, 'me': APP, 'lv': P3['lv'].get(APP, 10), 'mode': d.get('mode'), 'why': d.get('why'), 'cap': d.get('cpu_cap'),
            'rules': d.get('rules'), 'rules_from': d.get('rules_from'), 'p3': P3, 'apps': apps, 'err': hs.err}


def set_(d, by=APP):
    """手機／電腦改設定：members（勾選）、normal（平常分配）、reserve、boost、boost_others、lv {app: 1~10}、on."""
    kw = {}
    if isinstance(d.get('members'), list):
        M = [str(x) for x in d['members']]
        kw['members'] = [] if set(M) >= {k for k, _ in HS.KNOWN} else M
    for k in ('normal', 'lv'):
        if isinstance(d.get(k), dict): kw[k] = d[k]
    for k in ('reserve', 'boost', 'boost_others'):
        if d.get(k) is not None:
            try: kw[k] = float(d[k])
            except (TypeError, ValueError): pass
    if 'on' in d: kw['on'] = bool(d['on'])
    HS.set_policy3(by, **kw)
    try:
        E = _S['ctx'].get('eng'); E.log.w('🤝 握手設定：' + '、'.join(f'{k}={v}' for k, v in kw.items()))
    except Exception: pass
    return {'ok': True, **info()}
