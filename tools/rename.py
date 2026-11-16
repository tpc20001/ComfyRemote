"""把空架子變成你的新程式：python tools/rename.py --id MyTool --name MyTool --title "我的新工具" --prefix MT --port 8661
id：英文、不能有空白（EXE 名稱、安裝資料夾、只能開一個的識別）；prefix：更新包檔名前綴（MT_V0.1.01.zip）；
port：手機網頁本機埠（每個程式要不一樣；Tailscale 用 port+1000）。只改 app/brand.json，其他檔都從這裡讀。"""
import sys, json, argparse, pathlib
KIT = pathlib.Path(__file__).resolve().parent.parent; F = KIT / 'app' / 'brand.json'
USED = {8461: 'VideoSift', 8361: 'FusionStitch', 8561: 'AppKit 空架子', 8761: 'ComfyRemote'}                     # 已經被你其他程式用掉的本機埠（新程式不要撞到；有新的就加進來）

ap = argparse.ArgumentParser(); ap.add_argument('--id'); ap.add_argument('--name'); ap.add_argument('--title'); ap.add_argument('--prefix'); ap.add_argument('--port', type=int); ap.add_argument('--accent')
a = ap.parse_args(); B = json.loads(F.read_text(encoding='utf-8-sig'))
for k, v in (('id', a.id), ('name', a.name), ('title', a.title), ('prefix', a.prefix), ('web_port', a.port), ('accent', a.accent)):
    if v is not None: B[k] = v
if a.id: B['phone_id'] = a.id.lower() + '-phone'
if ' ' in B['id']: sys.exit('✖ id 不能有空白')
if B['web_port'] in USED: sys.exit(f'✖ 埠 {B["web_port"]} 已經是 {USED[B["web_port"]]} 在用，換一個')
F.write_text(json.dumps(B, ensure_ascii=False, indent=1), encoding='utf-8'); print('✔ brand.json：', json.dumps(B, ensure_ascii=False))
