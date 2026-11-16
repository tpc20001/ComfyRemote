"""開發用：假 ComfyUI＋引擎＋網頁，用 headless Chrome 截手機畫面（不打包）。
python3 tools/preview.py out.png [tab] [js]   tab＝gen/hist/cmp/set；js＝截圖前在頁面跑的 JS"""
import sys, os, json, time, shutil, tempfile, pathlib, types, urllib.request
KIT = pathlib.Path(__file__).resolve().parent.parent; APP = KIT / 'app'
sys.path.insert(0, str(APP)); sys.path.insert(0, str(KIT / 'tools'))
import core, web, fake_comfy as F
from playwright.sync_api import sync_playwright


def main(out, tab='gen', js='', setup=''):
    port = 19000 + os.getpid() % 500; F.serve(port); F.STATE['step_sec'] = 0.05
    d = tempfile.mkdtemp(); E = core.Engine(d, version='0.0.1'); E.cfg.set('bg_ramp_sec', 0); E.cfg.set('comfy_url', f'http://127.0.0.1:{port}')
    E.comfy_status(True); E.gen_workflows()
    E.gen_wf_save('Qwen 2.1 Turbo 改圖', (APP / 'wf_GROK_int8.json').read_text(encoding='utf-8'))
    img = E.gen_save_input(F.png(64, 48), 't')
    if setup: exec(setup, {'E': E, 'img': img, 'F': F, 'time': time})
    E.cfg.set('web_pin_salt', 's'); E.cfg.set('web_pin_hash', web.pin_hash('1234', 's'))
    S = web.WebServer(lambda: E, lambda: None, lambda f: f(), lambda: types.SimpleNamespace(LAB_LIST=[]), '0.0.1', core.BRAND); wp = port + 600; S.start(wp)
    r = urllib.request.Request(f'http://127.0.0.1:{wp}/api/login', data=json.dumps({'pin': '1234'}).encode(), headers={'Content-Type': 'application/json'})
    tok = json.loads(urllib.request.urlopen(r).read())['token']
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        ctx = b.new_context(viewport={'width': int(os.environ.get('VW', '400')), 'height': 860}, device_scale_factor=2); ctx.add_cookies([{'name': 'app_t', 'value': tok, 'url': f'http://127.0.0.1:{wp}/'}]); pg = ctx.new_page()
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e))); pg.on('console', lambda m: m.type == 'error' and errs.append(m.text))
        pg.goto(f'http://127.0.0.1:{wp}/'); pg.evaluate(f"localStorage.clear();localStorage.setItem('app_tok',JSON.stringify({json.dumps(tok)}));localStorage.setItem('app_tab',JSON.stringify({json.dumps(tab)}));localStorage.setItem('app_gimgs',JSON.stringify([{json.dumps(img)}]))")
        pg.goto(f'http://127.0.0.1:{wp}/'); pg.wait_for_timeout(1500)
        if js: pg.evaluate(js); pg.wait_for_timeout(int(os.environ.get('WAIT', '1200')))
        pg.screenshot(path=out, full_page=os.environ.get('FULL') == '1'); b.close()
    print('errors:', errs or 'none')
    S.close(); E.shutdown(); shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__': main(*sys.argv[1:])
