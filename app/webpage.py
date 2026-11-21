"""📱 手機網頁的整個頁面（HTML＋CSS＋JS 一個檔，不用網路上的東西）。V0.1.03 起外觀照 TikLive 手機版：
上面正中間浮動按鈕「📊 效能／🖥 背景／🎨 排隊」→ 浮動視窗（寬 70%、高度可拖）；分頁 生圖／歷史紀錄／設定；
設定裡分「設定／流程／更新包」，設定左邊分類（可搜尋）、右邊內容；更新包：選檔 → 先看改了什麼 → 確定更新；可以退回前面的版本。
__VER__／__NAME__／__TITLE__／__ACCENT__ 會換成 brand.json 和程式版本。"""

PAGE = r"""<!doctype html>
<html lang="zh-Hant" data-mode="dark"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0a0e13"><meta name="mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-capable" content="yes">
<link rel="manifest" href="manifest.webmanifest"><link rel="icon" href="icon-192.png"><link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>__NAME__</title>
<style>
/* ===== 顏色、字型：照 TikLive 手機版 ===== */
:root{--bg:#0e1116;--nav:#0a0e13;--panel:#11161c;--card:#151a21;--line:#252c35;--line2:#2a3340;--text:#e8ecf2;--strong:#fff;--sub:#8994a4;--muted:#7f8a99;--hover:#161e28;
--tab:#11161c;--tabon:#1d2733;--tabline:#4dc9ff;--track:#2a3038;--btn:#171d26;--btnh:#222b37;--sel:#263342;
--green:#45d483;--red:#ff4d6d;--purple:#9b6dff;--orange:#f0ad4e;--pink:#ff5c8a;--blue:#4dc9ff;--accent:__ACCENT__;--safe:env(safe-area-inset-bottom,0px)}
html[data-mode=light]{--bg:#f3f5f8;--nav:#e8ecf1;--panel:#fff;--card:#fff;--line:#d5dce4;--line2:#c2cbd6;--text:#1b2430;--strong:#0b121a;--sub:#5d6978;--muted:#6b7685;--hover:#dde4ec;
--tab:#fff;--tabon:#d3e6fb;--tabline:#0a84c6;--track:#dfe5ec;--btn:#fff;--btnh:#e7ecf2;--sel:#d3e6fb}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;background:var(--bg);color:var(--text);font:14px/1.4 system-ui,-apple-system,"Segoe UI","Microsoft JhengHei","PingFang TC",sans-serif}
button{font:inherit;cursor:pointer;color:inherit}
header{position:sticky;top:0;z-index:20;background:var(--nav);border-bottom:1px solid var(--line);padding-top:env(safe-area-inset-top,0px)}
.bar{display:flex;align-items:center;justify-content:space-between;padding:8px 12px 6px}
.logo{font-weight:800;font-size:15px;color:var(--strong);display:flex;align-items:center;gap:7px;letter-spacing:.2px;white-space:nowrap;flex:none}
.logo i{width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 8px var(--accent)}
.clk{font-size:11px;color:var(--sub);font-variant-numeric:tabular-nums}.rt{display:flex;align-items:center;justify-content:flex-end;gap:8px;min-width:0;flex:1;margin-left:8px}
.ver{font-size:11px;color:var(--sub);border:1px solid var(--line);border-radius:8px;padding:1px 6px;white-space:nowrap;font-variant-numeric:tabular-nums}
.topc{font-size:11px;color:var(--strong);text-decoration:none;font-weight:700;border:1px solid var(--line);border-radius:8px;padding:1px 6px;white-space:nowrap;background:transparent}
nav{display:flex;gap:6px;padding:0 10px 8px}
nav button{flex:2;background:var(--tab);border:1px solid var(--line);color:var(--sub);border-radius:9px;padding:8px 0;font-weight:700}
nav button.on{background:var(--tabon);border-color:var(--tabline);color:var(--strong)}nav button.tset{flex:1;font-size:13px;white-space:nowrap}
nav em{font-style:normal;margin-left:5px;background:var(--green);color:#06210f;border-radius:9px;padding:0 6px;font-size:11px}
main{padding:10px 10px calc(30px + var(--safe))}
.toast{position:fixed;left:50%;top:76px;transform:translateX(-50%);background:var(--panel);border:1px solid var(--line2);color:var(--text);padding:8px 14px;border-radius:10px;z-index:9900;font-size:13px;display:none;max-width:90vw;text-align:center;box-shadow:0 6px 20px rgba(0,0,0,.4)}
.empty{color:var(--sub);text-align:center;padding:34px 0}
.btn{display:block;width:100%;margin-top:10px;padding:13px;border:0;border-radius:10px;background:var(--accent);color:#fff;font-size:16px;font-weight:800;text-align:center;text-decoration:none}
.btn.s{background:var(--btn);border:1px solid var(--line);color:var(--text);font-size:15px}.btn:disabled{opacity:.5}
.seg{display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;flex:none}
.seg button{background:var(--card);border:0;border-left:1px solid var(--line);color:var(--sub);height:40px;min-width:34px;padding:0 9px;font-weight:800}
.seg button:first-child{border-left:0}.seg button.on{background:var(--tabon);color:var(--strong)}
/* ===== 設定：上面「設定／流程／更新包」，左邊分類（可搜尋）、右邊內容 ===== */
.stabs{display:flex;gap:6px;margin-bottom:10px}
.stabs button{flex:1;min-width:0;background:var(--tab);border:1px solid var(--line);color:var(--sub);border-radius:9px;padding:8px 2px;font-weight:700;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.stabs button[data-p=set]{flex:3}.stabs button.on{background:var(--tabon);border-color:var(--tabline);color:var(--strong)}
.s2{display:flex;gap:10px;align-items:flex-start}
.scat{position:sticky;top:calc(var(--hh,96px) + 8px);flex:none;width:clamp(92px,26vw,200px);display:flex;flex-direction:column;gap:5px;max-height:calc(100vh - var(--hh,96px) - 20px);overflow-y:auto}
.scat .sch{font-size:11px;color:var(--sub);margin:6px 4px 0;font-weight:700}
.scat button{text-align:left;background:var(--tab);border:1px solid var(--line);color:var(--sub);border-radius:9px;padding:9px 8px;font-weight:700;font-size:13px;line-height:1.25}
.scat button.on{background:var(--tabon);border-color:var(--tabline);color:var(--strong)}
.scat button small{display:block;font-size:10.5px;font-weight:400;opacity:.7;margin-top:2px;line-height:1.3}
@media (max-width:520px){.scat button small{display:none}
@media (max-width:620px){.s2{flex-direction:column;gap:8px}.scat{position:sticky;top:calc(var(--hh,96px) + 4px);z-index:5;width:100%;max-height:none;flex-direction:row;overflow-x:auto;overflow-y:hidden;gap:6px;padding:4px 0 6px;background:var(--bg);scrollbar-width:none}.scat::-webkit-scrollbar{display:none}
 .scat .sch{display:none}.scat button{flex:none;white-space:nowrap;padding:8px 12px;border-radius:999px}.scat .ssearch{flex:none;width:120px}#sbody{width:100%}}}
.ssearch{width:100%;height:34px;border-radius:9px;border:1px solid var(--line);background:var(--card);color:inherit;padding:0 8px;font-size:13px;margin-bottom:2px}
#sbody{flex:1;min-width:0}
.stt{font-size:19px;margin:2px 2px 12px;color:var(--strong)}
.ssec{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:6px 14px;margin-bottom:14px}
.ssec h3{font-size:13px;color:var(--accent);margin:10px 0 2px;letter-spacing:.5px}
.srow{padding:12px 2px;border-bottom:1px solid var(--line)}.srow:last-child{border-bottom:0}.srow>b{display:block;color:var(--strong);margin-bottom:8px}
.srow small{display:block;color:var(--sub);font-size:12px;margin-top:6px}.srow .seg{display:inline-flex;flex-wrap:wrap}.srow .seg button{height:36px}
.snote{color:var(--sub);font-size:12px;margin:12px 2px 0}
/* ===== 更新包 ===== */
.ufile{position:relative;overflow:hidden}.ufile input{position:absolute;inset:0;opacity:0;cursor:pointer;font-size:0}
.ucard{border:1px solid var(--accent);border-radius:12px;padding:12px;margin-top:10px}.ucard .uvs{font-size:17px;font-weight:800;color:var(--strong)}
.ucard ul,.upk ul{margin:8px 0 0;padding-left:18px;font-size:13.5px;line-height:1.55}
.utag{font-size:12px;padding:1px 8px;border-radius:99px;margin-left:6px;background:var(--accent);color:#fff;vertical-align:2px}.utag.old{background:var(--orange);color:#111}.utag.same{background:var(--btn);color:var(--text);border:1px solid var(--line)}
.uok{color:#45d483;font-weight:700;margin-top:8px}.ubad{color:#ff6577;margin-top:8px}.uwarn{color:#f0ad4e;font-size:13px;margin-top:8px}
.ubtns{display:flex;gap:8px}.ubtns .btn{flex:1}.umsg{margin-top:8px;min-height:18px;font-size:14px}
.upk{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-top:8px}.uh{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}.ut{font-size:12px;color:var(--sub)}.uh small{color:var(--sub);font-size:12px}
.upk details summary{color:var(--sub);font-size:12.5px;margin-top:4px;cursor:pointer}
/* ===== 上面正中間浮動按鈕＋浮動視窗（照 TikLive） ===== */
#sysFab{position:fixed;top:calc(env(safe-area-inset-top,0px) + 7px);left:50%;transform:translateX(-50%);z-index:9810;display:flex;gap:6px;pointer-events:none}
#sysFab button{pointer-events:auto;position:relative;height:24px;padding:0 8px;border-radius:12px;border:1px solid rgba(140,150,165,.5);background:rgba(18,22,30,.88);color:#fff;font-weight:800;font-size:11px;margin:0;cursor:pointer;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.35);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px)}
#sysFab button.on{background:#1f8ef1;border-color:#1f8ef1}
#sysFab em{position:absolute;top:-7px;right:-6px;font-style:normal;font-size:10px;line-height:14px;min-width:14px;padding:0 4px;border-radius:7px;background:#45d483;color:#06210f;font-weight:900}
#sysFab em[hidden]{display:none}
#sysPop{position:fixed;inset:0;z-index:9800;background:rgba(0,0,0,.28)}
.sysPopW{position:absolute;left:15%;width:70%;top:calc(env(safe-area-inset-top,0px) + 38px);height:50%;display:flex;flex-direction:column;background:var(--bg);color:var(--text);border:1px solid rgba(140,150,165,.45);border-radius:12px;box-shadow:0 14px 40px rgba(0,0,0,.6);overflow:hidden}
.sysPopW>*{zoom:.78}
@media (min-width:900px){.sysPopW{left:calc(50% - 360px);width:720px}}
@media (max-width:420px){.sysPopW{left:4%;width:92%}}
.sysPopH{display:flex;align-items:center;gap:8px;padding:8px 10px;border-bottom:1px solid rgba(127,127,127,.25)}.sysPopH b{font-size:15px;white-space:nowrap}.sysPopN{flex:1;font-size:11.5px;opacity:.6;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sysPopX{width:40px;height:32px;margin:0;border:0;border-radius:9px;background:rgba(127,127,127,.18);color:inherit;font-size:16px;cursor:pointer}
.sysPopB{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:8px 10px 12px;-webkit-overflow-scrolling:touch}.sysPopB .stt{display:none}
.sysPopR{flex:none;height:22px;display:flex;align-items:center;justify-content:center;cursor:ns-resize;touch-action:none;border-top:1px solid rgba(127,127,127,.25);background:rgba(127,127,127,.06)}
.sysPopR i{width:56px;height:5px;border-radius:3px;background:rgba(160,170,185,.6)}.sysPopR.on{background:rgba(31,142,241,.18)}.sysPopR.on i{background:#1f8ef1}
@media (pointer:coarse){.sysPopR{height:34px}.sysPopR i{width:70px;height:6px}}
/* ===== 電腦效能（照 TikLive：大圖＋小格子） ===== */
.pfbig canvas.pfcv{width:100%;height:170px;display:block;margin-top:6px}
.pfhd{display:flex;justify-content:space-between;align-items:baseline;padding-top:10px}.pfhd b{font-size:18px}.pfhd span{font-size:22px;font-weight:800;color:var(--strong)}
.pfax{display:flex;justify-content:space-between;font-size:11px;color:var(--sub);margin:3px 0 6px}
.pfdt{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px 14px;padding:6px 0 12px}.pfdt div{display:flex;flex-direction:column}.pfdt span{font-size:12px;color:var(--sub)}.pfdt b{font-size:15px;color:var(--strong);word-break:break-all}
.pft{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px;margin-bottom:14px}
.pftl{display:flex;gap:8px;align-items:center;text-align:left;background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px;color:var(--text)}
.pftl.on{border-color:var(--accent);background:var(--tabon)}.pftl canvas{width:56px;height:40px;flex:none}.pftl div{min-width:0;display:flex;flex-direction:column}
.pftl b{font-size:13px;color:var(--strong)}.pftl span{font-size:15px;font-weight:800}.pftl small{font-size:11px;color:var(--sub);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pftemp{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:8px;padding:8px 0 12px}
.pftemp div{background:var(--btn);border:1px solid var(--line);border-radius:10px;padding:8px 10px;display:flex;flex-direction:column}.pftemp span{font-size:12px;color:var(--sub)}.pftemp b{font-size:20px;color:var(--strong)}
.pftemp b.warm{color:#f0ad4e}.pftemp b.hot{color:#ff4d6d}
/* ===== 後台狀態（照 TikLive） ===== */
.bgs{display:flex;flex-direction:column;gap:8px;font-size:13.5px}.bgsHd{display:flex;align-items:baseline;gap:10px}.bgsHd b{font-size:16px}.bgsSum{font-size:13px;opacity:.85}.bgsNote{font-size:12px;opacity:.7}
.bgsC{border:1px solid var(--line);border-radius:12px;padding:8px 10px;background:var(--card)}.bgsC.idle{opacity:.6;padding:6px 10px}
.bgsCH{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.bgsCH b{flex:1}.bgsCH span{font-size:12px;opacity:.8}.bgsCN{font-size:11.5px;opacity:.65;margin:2px 0 4px}
.bgsI{display:flex;align-items:center;gap:8px;padding:6px 0;border-top:1px solid var(--line)}.bgsI>i{font-style:normal;flex:none;width:18px;text-align:center}.bgsI.run>i{color:#3ccf8e}.bgsI.wait>i{opacity:.7}
.bgsT{flex:1;min-width:0}.bgsT b{display:block;font-size:13px;font-weight:650;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.bgsT small{font-size:11.5px;opacity:.7}
.bgsT u{display:block;height:4px;border-radius:2px;background:rgba(127,127,127,.25);margin-top:4px;overflow:hidden}.bgsT u s{display:block;height:100%;background:#3fb6f2;text-decoration:none}
.bgsI button,.bgsB{flex:none;height:28px;padding:0 10px;border-radius:999px;border:1px solid rgba(255,101,119,.55);background:transparent;color:#ff6577;font-weight:700;cursor:pointer}
.bgsB.g{border-color:rgba(69,212,131,.6);color:#45d483}.bgsB.n{border-color:var(--line2);color:var(--text)}
.bgsLst{max-height:252px;overflow-y:auto;overscroll-behavior:contain}.bgsGuard{color:#f0ad4e;font-weight:700}
/* ===== 共用小元件（生圖、歷史用） ===== */
.grow{flex:1;min-width:0}.mu{color:var(--sub);font-size:12px}
.pill{background:var(--btn);border:1px solid var(--line2);border-radius:14px;padding:4px 11px;font-size:12.5px;color:var(--text)}
.pill:hover{background:var(--btnh)}.pill.ok{border-color:var(--green);color:var(--green)}.pill.wa{border-color:var(--orange);color:var(--orange)}.pill.er{border-color:var(--red);color:var(--red)}
.pill.acc{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:800}a.pill{text-decoration:none}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:10px 14px;margin:0 0 14px}
.panel h3{margin:4px 0 8px;font-size:13px;color:var(--accent);letter-spacing:.5px}
.row{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pg{height:6px;background:var(--track);border-radius:3px;overflow:hidden}.pg i{display:block;height:100%;background:var(--blue)}
.it{border-top:1px solid var(--line);padding:7px 0}.it:first-child{border-top:0}
input,select{background:var(--card);border:1px solid var(--line2);border-radius:8px;padding:6px 8px;color:var(--strong);font:inherit}
pre{white-space:pre-wrap;word-break:break-all;font-size:11.5px;background:var(--card);border-radius:8px;padding:8px;max-height:60vh;overflow:auto}
#login{max-width:320px;margin:18vh auto;text-align:center}#login input{width:100%;font-size:20px;text-align:center;letter-spacing:4px;margin:12px 0}
textarea{width:100%;background:var(--card);border:1px solid var(--line2);border-radius:10px;padding:9px 10px;color:var(--strong);font:inherit;font-size:15px;resize:vertical}
.gpicks{width:80%;margin:0 auto;display:flex;gap:8px;align-items:stretch}.gpicks .drop{flex:1;min-width:0;width:auto;margin:0 0 8px;padding:10px 6px}.gpicks.multi .drop img{max-height:22vh}
.slt{font-size:12px;font-weight:800;color:var(--strong);margin-bottom:4px}
.drop{width:80%;margin:0 auto 8px;border:2px dashed var(--line2);border-radius:12px;padding:18px 10px;text-align:center;color:var(--sub);cursor:pointer}   /* 80% 寬：左右留空，手指在邊邊滑才不會點到選照片 */
.drop img{max-width:100%;max-height:30vh;border-radius:8px;display:block;margin:0 auto}
.big{width:100%;padding:12px;font-size:16px;border-radius:12px;margin-top:8px}
.gsel{flex:1;min-width:0}
.job{border-top:1px solid var(--line);padding:9px 0}.job:first-child{border-top:0}
.clamp{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.th{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0;align-items:center}
.th img{height:120px;max-width:46%;object-fit:cover;border-radius:8px;cursor:pointer;background:var(--card)}.th img.src,.th video.src{height:60px;opacity:.75;border-radius:8px}
.vo{display:flex;flex-direction:column;gap:4px;align-items:flex-start}.vo video{max-height:46vh;max-width:100%;border-radius:8px;background:#000}
#gmod{margin-top:6px}#gmod .bgsC{border-color:var(--orange)}
/* 進度條 */.gpbw{display:flex;align-items:center;gap:8px;margin:6px 0 3px}.gpbw .gpb{flex:1;height:10px;border-radius:5px}.gpbw .gpb i{background:linear-gradient(90deg,#1f8ef1,#4dc9ff);border-radius:5px;transition:width .9s linear}.gpp{font-size:13px;color:var(--strong);min-width:42px;text-align:right;font-variant-numeric:tabular-nums}
/* 歷史：照日期收摺、精簡、選取 */
.hday{border-top:1px solid var(--line);padding:4px 0}.hday:first-child{border-top:0}.hday>summary{cursor:pointer;padding:6px 0;font-size:14px}
#hl.compact .job{padding:6px 0}#hl.compact .job:not(.open) .hx{display:none}#hl.compact .job:not(.open) .clamp{-webkit-line-clamp:1}
#hl.compact .job:not(.open) .th img,#hl.compact .job:not(.open) .th video{height:44px;max-width:30%}#hl.compact .job:not(.open) .vo .pill{display:none}#hl.compact .job{cursor:pointer}
.pill.on{background:var(--tabon);border-color:var(--tabline);color:var(--strong)}
.hck{width:20px;height:20px;margin:0 2px 0 0}
#hsb{position:fixed;left:8px;right:8px;bottom:calc(8px + var(--safe));z-index:9700;background:var(--panel);border:1px solid var(--tabline);border-radius:12px;padding:8px 10px;display:flex;flex-wrap:wrap;gap:6px;align-items:center;box-shadow:0 6px 24px rgba(0,0,0,.5)}
#hsb>span{flex:1 1 100%}
body.hsel main{padding-bottom:150px}
#gpar details{border-top:1px solid var(--line);padding:2px 0}#gwi{font-size:11.5px;line-height:1.35}#gpar summary{cursor:pointer;padding:3px 0;font-size:13px}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));grid-auto-flow:row dense;gap:5px 8px;padding:3px 0 6px}
.pc{display:flex;flex-direction:column;gap:1px;min-width:0}.pc>label{font-size:11px;color:var(--sub);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc input,.pc select{width:100%;min-width:0;height:32px;padding:3px 6px;font-size:13px;border-radius:7px}
.pc.w2{grid-column:span 2}.pc.wf{grid-column:1/-1}
.pc.b{flex-direction:row;align-items:center;gap:6px;font-size:12px;color:var(--text);cursor:pointer;align-self:end;height:32px}.pc.b input{width:18px;height:18px;flex:none}.pc.b span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#ov{position:fixed;inset:0;background:rgba(6,7,10,.97);z-index:9850;display:none;flex-direction:column;align-items:center;justify-content:center;padding:env(safe-area-inset-top,0) 8px env(safe-area-inset-bottom,0)}
#cmp{position:relative;display:none;touch-action:none;user-select:none;-webkit-user-select:none;max-width:100%;max-height:78vh;overflow:hidden;border-radius:6px}
#cmp img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;max-height:none;pointer-events:none}
#cmpb{position:absolute;inset:0;clip-path:inset(0 0 0 50%)}
#cmpl{position:absolute;top:0;bottom:0;left:50%;width:3px;margin-left:-1.5px;background:#fff;box-shadow:0 0 6px #000}
#cmpl i{position:absolute;top:50%;left:50%;width:38px;height:38px;margin:-19px 0 0 -19px;border-radius:50%;background:#fff;box-shadow:0 0 8px #000}
#cmpl i:after{content:'⇆';position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#222;font-size:20px;font-style:normal;font-weight:900}
#cmp .cl,#cmp .cr{position:absolute;top:8px;background:rgba(0,0,0,.55);color:#fff;border-radius:8px;padding:2px 8px;font-size:12px}#cmp .cl{left:8px}#cmp .cr{right:8px}
#ov>img{max-width:80vw;max-height:78vh;object-fit:contain}
#ov .ovnav{position:absolute;top:50%;margin-top:-28px;width:44px;height:56px;border:0;border-radius:10px;background:rgba(255,255,255,.14);color:#fff;font-size:28px;font-weight:900;z-index:2}
#ovp{left:4px}#ovnx{right:4px}#ovn{position:absolute;top:calc(8px + env(safe-area-inset-top,0px));left:0;right:0;text-align:center;color:#ccc;font-size:12.5px}
#fpk{position:fixed;inset:0;z-index:9860;background:#05080c;display:none;flex-direction:column;padding:calc(8px + env(safe-area-inset-top,0px)) 10px calc(10px + env(safe-area-inset-bottom,0px));overflow-y:auto}
#fpk video{width:100%;max-height:46vh;background:#000;border-radius:8px;object-fit:contain}
#fpk .fpn{font-size:22px;font-weight:900;text-align:center;margin:6px 0 2px}#fpk .fpn small{font-size:13px;color:var(--sub);font-weight:600}
#fpr{width:100%;height:34px;margin:4px 0}
#fpk .fpb{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}#fpk .fpb button{padding:12px 0;font-size:15px;font-weight:800}
#fpsel{display:flex;gap:6px;overflow-x:auto;padding:6px 0;min-height:86px}#fpsel .fc{position:relative;flex:0 0 auto;text-align:center;font-size:11.5px;color:var(--sub)}
#fpsel .fc img{height:64px;border-radius:6px;display:block;border:2px solid transparent}#fpsel .fc.cur img{border-color:var(--accent)}
#fpsel .fc i{position:absolute;top:-4px;right:-4px;width:20px;height:20px;border-radius:50%;background:var(--red);color:#fff;font-style:normal;font-size:12px;line-height:20px}
details.hgrp{border:1px solid var(--tabline);border-radius:12px;margin:6px 0;background:rgba(139,92,246,.05)}
details.hgrp>summary{list-style:none;padding:8px 10px;cursor:pointer}details.hgrp>summary::-webkit-details-marker{display:none}
details.hgrp>summary .gT{display:flex;gap:6px;align-items:center;flex-wrap:wrap}details.hgrp>summary .gT:before{content:'▸';color:var(--sub)}details.hgrp[open]>summary .gT:before{content:'▾'}
details.hgrp>summary .gS{display:flex;gap:3px;overflow:hidden;margin-top:5px}details.hgrp>summary .gS img{height:42px;border-radius:4px}
details.hgrp>.gB{padding:0 8px 8px}details.hgrp .job{margin-left:6px}
.mg{border:1px solid var(--tabline);border-radius:10px;padding:6px;margin:4px 0 8px;background:var(--panel)}
.mgH{display:flex;align-items:center;gap:6px;margin-bottom:5px}.mgH b{font-size:14px}
.mgPg{position:relative;overflow:hidden;background:#000;border-radius:6px}
.mgGrid{position:relative;margin:0 auto}.mgG{position:absolute;overflow:hidden;background:#111;cursor:zoom-in}
.mgG img{width:100%;height:100%;object-fit:cover;object-position:50% var(--mgfy,50%);display:block;pointer-events:none}
.mgLb{position:absolute;transform:translateY(-100%);background:rgba(0,0,0,.55);color:#fff;font-size:11px;font-weight:700;padding:0 5px;border-radius:4px;z-index:900;pointer-events:none;white-space:nowrap}
.mgGrip{height:20px;display:flex;align-items:center;justify-content:center;cursor:ns-resize;touch-action:none;margin-top:2px}.mgGrip i{width:56px;height:5px;border-radius:3px;background:var(--sub);opacity:.6}.mgGrip.on i{background:var(--accent);opacity:1}
.mgTool{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-top:4px}.mgTool button{padding:6px 9px;font-size:13px}
.mgFy{display:inline-flex;align-items:center;gap:2px;border:1px solid var(--tabline);border-radius:9px;padding:1px}.mgFy button{padding:5px 7px;border:0;background:transparent}.mgFy em{font-style:normal;min-width:28px;text-align:center;font-size:12px}
.mgLy{display:flex;flex-wrap:wrap;gap:4px;margin-top:5px}.mgLy button{padding:5px 9px;font-size:13px}.mgLy button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.mgOpt{margin-top:6px;border-top:1px dashed var(--tabline);padding-top:6px;display:grid;gap:6px}.mgOpt .r{display:flex;align-items:center;gap:6px;flex-wrap:wrap}.mgOpt .r>b{min-width:52px;font-size:12.5px}
.mgOpt .seg2 button{padding:4px 8px;font-size:12.5px}.mgOpt .seg2 button.on{background:var(--accent);color:#fff}
.ftag{display:inline-block;background:rgba(139,92,246,.18);color:#c4b5fd;border-radius:6px;padding:0 6px;font-size:11.5px;font-weight:700}
#ov .row{margin-top:10px;justify-content:center}
/* 🖥 網頁版：大螢幕置中、寬一點 */
body.pc main,body.pc header .bar,body.pc nav{max-width:1100px;margin-left:auto;margin-right:auto}

/* ===== 🎨 生圖頁 V2：卡片分段＋方格縮圖＋底部固定「開始」 ===== */
nav{gap:8px;padding:2px 12px 10px}
nav button{border-radius:12px;padding:9px 0;transition:background .15s,border-color .15s}
nav button.on{background:linear-gradient(180deg,rgba(124,92,255,.22),rgba(124,92,255,.08));border-color:rgba(140,110,255,.75);box-shadow:0 0 0 1px rgba(140,110,255,.18) inset}
#genv{display:flex;flex-direction:column;gap:12px;max-width:760px;margin:0 auto}
.gstat{display:flex;gap:6px;align-items:center;overflow-x:auto;scrollbar-width:none}.gstat::-webkit-scrollbar{display:none}
.gstat span{display:inline-flex;align-items:center;gap:6px;height:26px;padding:0 10px;border-radius:13px;background:var(--card);border:1px solid var(--line);font-size:12px;color:var(--sub);white-space:nowrap}
.gstat span.ok{color:var(--green);border-color:rgba(69,212,131,.35)}.gstat span.bad{color:var(--red);border-color:rgba(255,77,109,.4)}
.gstat i{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 6px currentColor}
.gcard{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px}
.ghd{display:flex;align-items:center;gap:8px;margin-bottom:12px}.ghd b{font-size:15px;color:var(--strong)}.ghd .mu{font-size:12px}
.gnum{width:22px;height:22px;border-radius:50%;flex:none;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#fff;background:linear-gradient(135deg,#8b5cf6,#4f7cff)}
#genv .gpicks{width:100%;margin:0}#genv .gpicks:not(.multi) #gpick{border:0;padding:0;margin:0;width:100%;cursor:default;text-align:left}
.gtiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(72px,1fr));gap:8px}
.gtiles.one{grid-template-columns:minmax(0,200px) 84px}
.gtile{position:relative;aspect-ratio:3/4;border-radius:12px;overflow:hidden;background:var(--card);border:1px solid var(--line)}
.gtile img{width:100%;height:100%;object-fit:cover;display:block}
.gtile .gx{position:absolute;top:5px;right:5px;width:26px;height:26px;border-radius:50%;border:0;background:rgba(10,12,16,.62);color:#fff;font-size:13px;line-height:26px;padding:0;-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px)}
.gtile .gx:active{background:var(--red)}
.gtile .gi{position:absolute;left:5px;top:5px;min-width:20px;height:20px;padding:0 6px;border-radius:10px;background:rgba(10,12,16,.6);color:#fff;font-size:11px;font-weight:800;line-height:20px;text-align:center}
.gtile .ftag{position:absolute;left:5px;bottom:5px;background:rgba(124,92,255,.85);color:#fff}
.gadd{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;border:1.5px dashed var(--line2);background:transparent;color:var(--sub);cursor:pointer;font-size:28px;font-weight:300}
.gadd small{font-size:11.5px;font-weight:600}.gadd:active{background:var(--hover)}
.gempty{display:flex;flex-direction:column;align-items:center;gap:6px;padding:28px 12px;border:1.5px dashed var(--line2);border-radius:14px;color:var(--sub);cursor:pointer;text-align:center}
.gempty .ic{width:52px;height:52px;border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:26px;background:linear-gradient(135deg,rgba(139,92,246,.25),rgba(79,124,255,.18))}
.gempty b{color:var(--strong);font-size:15px}
.gfoot{display:flex;align-items:center;gap:8px;margin-top:12px;flex-wrap:wrap}
.gbadge{display:inline-flex;align-items:center;gap:5px;height:26px;padding:0 10px;border-radius:13px;background:rgba(139,92,246,.16);color:#c4b5fd;font-size:12.5px;font-weight:800}
html[data-mode=light] .gbadge{color:#6d28d9}
.gclr{margin-left:auto;height:28px;padding:0 12px;border-radius:14px;border:1px solid rgba(255,77,109,.45);background:transparent;color:var(--red);font-size:12.5px;font-weight:700}
.gsrc{display:flex;gap:8px;margin-top:12px}
.gchip{flex:1;display:inline-flex;align-items:center;justify-content:center;gap:6px;height:38px;border-radius:12px;border:1px solid var(--line2);background:var(--btn);color:var(--text);font-size:13px;font-weight:600}
.gchip:active{background:var(--btnh)}
#genv textarea{border-radius:12px;padding:12px;font-size:16px;line-height:1.5;min-height:92px;background:var(--card);border-color:var(--line2)}
#genv textarea:focus,#genv select:focus,#genv input:focus{outline:none;border-color:#8b5cf6;box-shadow:0 0 0 3px rgba(139,92,246,.18)}
.gppl{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}.gppl:empty{display:none}
.gppl button{height:28px;padding:0 10px;border-radius:14px;border:1px solid rgba(77,201,255,.4);background:rgba(77,201,255,.08);color:var(--blue);font-size:12.5px;font-weight:700}
.gppl .mu{font-size:11.5px}
#gh3{margin-top:8px}#gh3 a{color:var(--blue);font-weight:700;text-decoration:none}
#gnd{margin-top:10px}#gnd summary{font-size:12.5px;cursor:pointer}#gnd textarea{min-height:60px;margin-top:6px;font-size:14px}
#genv select{-webkit-appearance:none;appearance:none;height:46px;border-radius:12px;padding:0 34px 0 14px;font-size:15px;background:var(--card) url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%238994a4' stroke-width='1.8' fill='none' stroke-linecap='round'/%3E%3C/svg%3E") no-repeat right 13px center}
.gbig{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px}.gbb{display:flex;flex-direction:column;align-items:flex-start;gap:2px;padding:12px 12px;border-radius:14px;border:1.5px solid var(--line);background:var(--card2,rgba(255,255,255,.04));color:var(--text);text-align:left;min-height:74px}
.gbb .ic{font-size:20px}.gbb b{font-size:14.5px}.gbb small{color:var(--sub);font-size:12px}.gbb.on{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 16%,transparent)}.gbb.both{grid-column:1/-1;flex-direction:row;align-items:center;gap:10px;min-height:0;padding:9px 12px}
.gtcat,.gtlist{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}
.gtcat,.gpls{flex-wrap:nowrap!important;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;padding-bottom:2px;mask-image:linear-gradient(90deg,#000 88%,transparent)}.gtcat::-webkit-scrollbar,.gpls::-webkit-scrollbar{display:none}.gtcat>*,.gpls>*{flex:none}.gtlist{padding:8px;border-radius:12px;background:rgba(255,255,255,.03);border:1px dashed var(--line)}
.gpc.on{border-color:var(--accent);color:var(--text);background:color-mix(in srgb,var(--accent) 18%,transparent)}.gpc.kp input{display:none}
.gqual{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0 2px}.gqual:empty{display:none}.gqual small{opacity:.6;font-size:11px}
#mkdot{position:absolute;border-radius:50%;border:2px solid #fff;background:rgba(255,45,85,.35);pointer-events:none}
.gcr.gmk{left:auto;right:6px}.gcr.gmk.on{background:#ff2d55}
.gcr{position:absolute;left:6px;bottom:6px;border:0;border-radius:999px;padding:4px 9px;font-size:12px;font-weight:700;background:rgba(0,0,0,.6);color:#fff;backdrop-filter:blur(4px)}
.crsc{overflow:auto;max-width:100%;max-height:calc(100vh - 230px);-webkit-overflow-scrolling:touch}
#crp{position:fixed;inset:0;z-index:100000;background:#0b0d12;display:flex;flex-direction:column;align-items:center;gap:10px;padding:12px;padding-bottom:calc(12px + env(safe-area-inset-bottom))}
.crtop{display:flex;gap:8px;align-items:center;width:100%;max-width:900px;color:#fff}.crwrap{position:relative;touch-action:none;flex:none}.crwrap canvas{display:block;border-radius:6px}
#crr{position:absolute;border:2px solid #fff;box-shadow:0 0 0 9999px rgba(0,0,0,.55);cursor:move;touch-action:none}#crr::after{content:attr(data-sz);position:absolute;left:4px;top:4px;font-size:11px;color:#fff;background:rgba(0,0,0,.5);padding:1px 5px;border-radius:6px}
#crr .crh{position:absolute;right:-14px;bottom:-14px;width:30px;height:30px;border-radius:50%;background:#fff;border:3px solid var(--accent);cursor:nwse-resize}
.crbar{display:flex;flex-wrap:wrap;gap:6px;justify-content:center;max-width:900px}#crp .gpc{color:#fff}
.slim{margin-top:10px;padding:10px;border:1px solid var(--line);border-radius:12px}.slr{gap:8px;padding:6px 0;border-bottom:1px dashed var(--line);font-size:13.5px}
.grcp{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:0 0 10px}.grcp:empty{display:none}.gpc.rc{border-color:var(--accent);font-weight:700}.gpc.rc i{font-style:normal;opacity:.5;margin-left:6px}
.gref{margin-top:8px}.grefh{display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:6px}.grefh img{width:44px;height:44px;object-fit:cover;border-radius:8px;cursor:pointer;border:1px solid var(--line)}.grefc{display:flex;gap:10px;align-items:center;padding:8px;border:1px solid var(--accent);border-radius:12px}.grefc img{width:54px;height:54px;object-fit:cover;border-radius:8px}.grefc .mu{font-size:12px}
#ovi.ovz,#cmp.ovz{transform:scale(2.5);transition:transform .15s;position:relative;z-index:2}#ovi,#cmp{transition:transform .15s}
.ovact{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:8px}.ovact .pill{display:inline-flex;align-items:center;justify-content:center;height:40px;padding:0 16px;font-size:14.5px}.ovact.sm .pill{height:34px;padding:0 12px;font-size:13px;background:rgba(255,255,255,.06)}.ovact.sm .pill.er{color:var(--red)}
.ovpt{cursor:pointer;color:#ddd;font-size:13px;max-width:min(92vw,720px);margin:0 auto 4px;text-align:center;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.gadv{margin-top:10px}.gadv>summary{cursor:pointer;padding:10px 12px;border:1px solid var(--line);border-radius:12px;font-weight:700;list-style:none}.gadv>summary::-webkit-details-marker{display:none}.gadv[open]>summary{margin-bottom:8px}
.gadv.flat>summary{display:none}#gwi.big{display:none}
.gmb{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-bottom:8px}.gmb .gbb{min-height:0;padding:9px 8px}.gmb .gbb b{font-size:13.5px}.gmb .gbb small{font-size:11px;line-height:1.3}
.gmode{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:0 0 12px}.gmo{display:flex;flex-direction:column;align-items:center;gap:2px;padding:10px 4px;border-radius:14px;border:1.5px solid var(--line);background:var(--card);color:var(--sub)}
.gmo span{font-size:22px}.gmo b{font-size:12.5px;color:var(--text)}.gmo.on{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 18%,var(--card))}.gmo.on b{color:var(--strong,#fff)}.gmo.off{opacity:.45}
.gvar{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}.gvar:empty{display:none}
.gtool{margin-bottom:8px}.tgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.tbtn{display:flex;flex-direction:column;align-items:center;gap:1px;padding:8px 2px;border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--text)}
.tbtn span{font-size:20px}.tbtn b{font-size:12.5px}.tbtn small{font-size:10px;color:var(--sub);line-height:1.2;text-align:center}.tbtn.on{border-color:var(--accent);background:color-mix(in srgb,var(--accent) 16%,var(--card))}
.gwrow{display:flex;gap:8px}.gwrow #gw{flex:1;min-width:0;font-weight:700}.gwrow #gc{flex:none;width:92px}
#gwi{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;font-size:12px}
#gwi .gt{display:inline-flex;align-items:center;height:24px;padding:0 9px;border-radius:12px;background:var(--card);border:1px solid var(--line);color:var(--sub);white-space:nowrap;max-width:100%;overflow:hidden;text-overflow:ellipsis}
#gpar{margin-top:12px;display:flex;flex-direction:column;gap:8px}
#genv #gpar details{border:1px solid var(--line);border-radius:12px;padding:0 12px;background:var(--card)}
#genv #gpar summary{list-style:none;display:flex;align-items:center;gap:6px;padding:11px 0;font-size:14px}
#genv #gpar summary::-webkit-details-marker{display:none}
#genv #gpar summary:after{content:'';margin-left:auto;width:8px;height:8px;border-right:2px solid var(--sub);border-bottom:2px solid var(--sub);transform:rotate(45deg);transition:transform .15s;margin-top:-4px}
#genv #gpar details[open]>summary:after{transform:rotate(-135deg);margin-top:4px}
#genv #gpar details[open]{padding-bottom:12px}
#genv .pgrid{grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:10px;padding:2px 0 0}
#genv .pc{gap:4px}#genv .pc>label{font-size:11.5px}
#genv .pc input,#genv .pc select{height:40px;border-radius:10px;font-size:14px;padding:0 10px;background-color:var(--panel)}
#genv .pc select{padding-right:28px;background-position:right 10px center}
#genv .pc.b{height:40px}
#gpr{height:30px;border-radius:15px}#gpc{font-size:12px}
#gmod .bgsC{border-radius:12px;margin-top:10px}
.ggobar{position:sticky;bottom:calc(10px + var(--safe));z-index:6;padding-top:4px}
.ggo{width:100%;height:56px;border:0;border-radius:16px;color:#fff;font-size:18px;font-weight:900;letter-spacing:2px;background:linear-gradient(135deg,#8b5cf6 0%,#6d5dfc 55%,#4f7cff 100%);box-shadow:0 10px 28px rgba(109,93,252,.45),0 0 0 1px rgba(255,255,255,.08) inset;transition:transform .08s}
.ggo:active{transform:scale(.985)}.ggo:disabled{opacity:.55}
.ggo small{display:block;font-size:11.5px;font-weight:600;letter-spacing:0;opacity:.85;margin-top:1px}
#gj .job{padding:12px 0}#gj .empty2{display:flex;flex-direction:column;align-items:center;gap:4px;padding:14px 4px;text-align:center;color:var(--sub);font-size:13px}
#gj .empty2 b{color:var(--text);font-size:14px}

/* ===== 🧪 比較 ===== */
nav button{font-size:13.5px;white-space:nowrap}
.chero{background:linear-gradient(135deg,rgba(139,92,246,.16),rgba(79,124,255,.08));border-color:rgba(139,92,246,.35)}.chero b{font-size:16px;color:var(--strong)}.chero .mu{margin-top:4px;line-height:1.5}
.crow{border:1px solid var(--line);border-radius:12px;background:var(--card);margin-bottom:8px;transition:border-color .15s}.crow.on{border-color:rgba(139,92,246,.6)}
.crow>summary{list-style:none;display:flex;align-items:center;gap:10px;padding:10px 12px;cursor:pointer}.crow>summary::-webkit-details-marker{display:none}
.crow>summary:after{content:'';flex:none;width:8px;height:8px;border-right:2px solid var(--sub);border-bottom:2px solid var(--sub);transform:rotate(45deg);margin:-4px 4px 0 0}.crow[open]>summary:after{transform:rotate(-135deg);margin-top:4px}
.cck input{width:22px;height:22px;accent-color:#8b5cf6}.cnm{flex:1;min-width:0}.cnm b{font-size:14.5px;color:var(--strong)}
.cbs{display:flex;flex-wrap:wrap;gap:5px;margin-top:4px}.cbadge{display:inline-flex;align-items:center;height:21px;padding:0 8px;border-radius:11px;font-size:11.5px;background:var(--panel);border:1px solid var(--line);color:var(--sub);white-space:nowrap}
.cbadge.ok{color:var(--green);border-color:rgba(69,212,131,.4)}.cbadge.er{color:var(--red);border-color:rgba(255,77,109,.4)}.cbadge.wa{color:var(--orange);border-color:rgba(240,173,78,.4)}.cbadge.bl{color:var(--blue);border-color:rgba(77,201,255,.4)}
.cbody{padding:0 12px 12px}.cnote{font-size:12.5px;color:var(--text);margin:2px 0 6px}.cmiss{font-size:12px;background:var(--panel);border-radius:8px;padding:6px 8px;margin:6px 0;line-height:1.6;word-break:break-all}
.cpar .pgrid{grid-template-columns:repeat(auto-fill,minmax(96px,1fr))}
.cmxw{overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid var(--line);border-radius:12px}
.cmxt{border-collapse:separate;border-spacing:0;font-size:12px}.cmxt th,.cmxt td{border-bottom:1px solid var(--line);padding:6px;vertical-align:top;text-align:center;background:var(--card)}
.cmxt th{position:sticky;top:0;z-index:2;min-width:120px;max-width:150px;font-weight:600;color:var(--sub)}.cmxt th b{display:block;color:var(--strong);font-size:12.5px;line-height:1.3}
.cmxt .c0{position:sticky;left:0;z-index:3;min-width:74px;background:var(--panel)}.cmxt td.c0 img{width:62px;height:78px;object-fit:cover;border-radius:6px;opacity:.85}
.cx img{width:126px;height:150px;object-fit:cover;border-radius:8px;cursor:zoom-in;display:block;margin:0 auto}.cx.wait,.cx.run,.cx.fail,.cx.none{color:var(--sub);min-height:150px;vertical-align:middle}.cx.run{color:var(--blue)}.cx.fail{color:var(--red)}
.ct{font-size:11px;color:var(--sub);margin-top:3px}.cbest{color:var(--green);font-weight:800}
.cstar{display:inline-flex;gap:1px;margin-top:2px}.cstar i{font-style:normal;font-size:19px;line-height:22px;color:var(--line2);cursor:pointer;padding:0 1px}.cstar i.on{color:#ffc53d}
.crank{margin-top:10px;border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:var(--card)}.csweet{font-size:14px;margin-bottom:6px;color:var(--strong)}.csweet b{color:var(--green)}
.crk{display:flex;align-items:center;gap:8px;padding:5px 0;border-top:1px solid var(--line);font-size:13px}.crk:first-of-type{border-top:0}.crk .cn{width:20px;height:20px;border-radius:50%;background:var(--panel);display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:800}.crk small{color:var(--sub)}
@media (max-width:460px){#sysFab{left:auto;right:76px;transform:none;gap:4px}#sysFab button{padding:0 6px;font-size:10.5px}.logo{font-size:14px}}
#ovs{margin-top:8px;color:#ddd;font-size:13.5px}.ovsb{display:flex;align-items:center;gap:8px;justify-content:center;flex-wrap:wrap}.ovsb b{color:#fff}#ovs .cstar i{font-size:28px;line-height:30px;padding:0 3px;color:#555}#ovs .cstar i.on{color:#ffc53d}
.crow.isvar{margin-left:18px;border-style:dashed}.cvar{color:var(--sub);font-weight:400}
.gpls{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}.gpc{display:inline-flex;align-items:center;gap:4px;height:28px;padding:0 10px;border-radius:14px;border:1px solid var(--line2);background:var(--card);color:var(--text);font-size:12.5px;cursor:pointer;max-width:100%;white-space:nowrap;overflow:hidden}
.gpc.sv{border-color:rgba(255,197,61,.45)}.gpc i{font-style:normal;color:var(--sub);margin-left:2px;padding:0 2px}.gpc.add{border-style:dashed;color:var(--sub)}.gpc.more{color:var(--blue);border-color:transparent;background:transparent}
.gmlb{display:flex;align-items:center;gap:8px;margin-top:10px;font-size:12.5px;color:var(--sub)}.gmlb input{width:18px;height:18px;flex:none}
.cprog{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:10px;background:var(--card)}
.cone .row{margin-bottom:8px}.cone0{display:flex;align-items:center;gap:10px;margin-bottom:10px}.cone0 img{width:70px;height:90px;object-fit:cover;border-radius:8px}
.cgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}.cgc{border:1px solid var(--line);border-radius:12px;padding:8px;background:var(--card);text-align:center}
.cgh{display:flex;align-items:baseline;gap:6px;margin-bottom:6px;text-align:left}.cgh b{flex:1;font-size:12.5px;line-height:1.3;color:var(--strong)}
.cgc img{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:8px;cursor:zoom-in;display:block}.cgx{aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;color:var(--sub);border-radius:8px;background:var(--panel)}
.cgc .cstar i{font-size:24px;line-height:28px}
/* ===== 歷史紀錄 V2：一筆一張卡片 ===== */
#hl .job{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px;margin:10px 0;border-top:1px solid var(--line)}
#hl .job:first-child{border-top:1px solid var(--line)}
#hl details.hgrp .job{margin:8px 0;background:var(--panel)}
#hl .job .row b:first-child{font-size:15px;color:var(--strong)}
#hl .job .clamp{margin-top:4px;color:var(--text);font-size:13.5px}
#hl .th{gap:8px;margin:10px 0}#hl .th img{border-radius:10px;box-shadow:0 2px 10px rgba(0,0,0,.25)}
#hl .job .row.hx .pill{height:32px;padding:0 11px;font-size:12.5px}
#hl details.hday>summary{list-style:none;display:flex;align-items:center;gap:8px;padding:10px 2px;font-size:15px}#hl details.hday>summary::-webkit-details-marker{display:none}
#hl details.hday>summary:before{content:'▸';color:var(--sub)}#hl details.hday[open]>summary:before{content:'▾'}
details.hgrp{border-radius:14px}
.gdh{display:flex;align-items:baseline;gap:8px;margin:12px 0 8px;border-top:1px solid var(--line);padding-top:12px}.gdh b{color:var(--strong)}
.gdi{position:relative;display:block}.gdv{display:block;width:100%;margin-top:4px;border:0;border-radius:8px;padding:6px 0;font-size:11.5px;font-weight:800;background:rgba(0,0,0,.65);color:#fff}.gdi i{position:absolute;left:4px;top:4px;font-style:normal;font-size:12px;background:rgba(0,0,0,.55);border-radius:8px;padding:1px 4px;pointer-events:none}.gdi i.m{left:auto;right:4px}.gdi i.v{top:auto;bottom:6px;color:#ffc53d;font-weight:800}.gdi i.n{left:auto;right:4px;top:auto;bottom:6px;font-weight:800}
.gds{display:grid;grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:8px}.gds img,.gds video{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:10px;cursor:zoom-in;background:var(--panel)}
.gwq{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:8px}.gwq:empty{display:none}.gwq .mu{font-size:12px}
body.dragon #gpick,body.dragon #cpick{outline:3px dashed #8b5cf6;outline-offset:6px;border-radius:14px}
.gnews{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:12px 14px;border-radius:14px;background:linear-gradient(135deg,rgba(69,212,131,.16),rgba(77,201,255,.1));border:1px solid rgba(69,212,131,.45)}.gnews b{color:var(--strong)}.gnews span{flex:1 1 100%;font-size:12.5px;color:var(--sub)}
.cgc.corig{border-style:dashed;opacity:.92}
/* 🖥 網頁版（大螢幕）：比較結果圖放大 */
body.pc #genv{max-width:1100px}body.pc .cx img{width:210px;height:260px}body.pc .cmxt th{min-width:200px;max-width:230px}body.pc .cgrid{grid-template-columns:repeat(auto-fill,minmax(240px,1fr))}
body.pc .gtiles{grid-template-columns:repeat(auto-fill,minmax(120px,1fr))}
.crec{display:grid;grid-template-columns:repeat(auto-fill,minmax(64px,1fr));gap:6px;margin-top:8px}.crec:empty{display:none}.crec img{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:8px;cursor:pointer;opacity:.7;border:2px solid transparent}.crec img.on{opacity:1;border-color:#8b5cf6}
.cgrid .cgc img,.cgrid .cgx{aspect-ratio:var(--ar,3/4)!important;object-fit:contain!important;background:#0b0e12}
.cgrid.wide{grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}
.cmxt .cx img{object-fit:contain;background:#0b0e12}.cmxt td.c0 img{object-fit:contain;background:#0b0e12}
/* 看大圖：上一張／下一張放在下面，單手大拇指按得到；兩邊的小箭頭只在電腦大螢幕顯示 */
.ovbot{display:flex;align-items:center;gap:10px;width:min(560px,94vw);margin:10px auto 4px}
.ovbot button{flex:1;height:52px;border-radius:14px;border:1px solid rgba(255,255,255,.22);background:#262b35;color:#fff;font-size:17px;font-weight:800}
.ovbot button:active{background:rgba(139,92,246,.55)}.ovbot button:disabled{opacity:.3}.ovbot span{min-width:64px;text-align:center;color:#ccc;font-size:13px}
@media (max-width:820px){.ovnav{display:none!important}}
@media (max-width:385px){.logo{font-size:0!important;gap:0}.logo i{margin-right:0}}@media (max-width:385px) and (min-width:0){#sysFab button{padding-left:8px!important;padding-right:8px!important}}
/* V0.3.44 提示詞區分頁＋最後送出預覽 */
@media(max-width:560px){#ver{display:none}#hslv .pct{display:none}#hslv{margin-right:0;padding:2px 7px}}   /* V0.3.60 手機：Lv 不要被上面的浮動鈕蓋住（版本號在設定看） */
@media(min-width:1100px){.hdg{display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:10px;align-items:start}.hdg>details.hgrp{grid-column:1/-1}.tkdG{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}#igd,.igdA{max-width:none}}   /* V0.3.59 平板：歷史紀錄、IG 多欄 */
@media(min-width:1100px){#genv:not(:has(>#gjsec)){max-width:1200px}#genv:has(>#gjsec){display:grid;grid-template-columns:minmax(0,1fr) minmax(360px,460px);max-width:1560px;align-items:start;column-gap:18px}#genv:has(>#gjsec)>*{grid-column:1;min-width:0}#genv>#gjsec{grid-column:2;grid-row:1/span 40;position:sticky;top:110px;max-height:calc(100vh - 200px);overflow:auto}body.pc main,body.pc header .bar,body.pc nav{max-width:1560px}}   /* V0.3.58 平板／寬螢幕：右邊固定「製作中」 */
.gtabs{display:flex;gap:6px;margin-top:10px;overflow-x:auto;scrollbar-width:none}.gtabs::-webkit-scrollbar{display:none}.gtabs button{flex:1;min-width:76px;padding:9px 6px;border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--text);font-weight:700;font-size:14px;white-space:nowrap}.gtabs button.on{background:color-mix(in srgb,var(--accent) 22%,var(--card));border-color:var(--accent);color:var(--strong)}.gtabs button[hidden]{display:none}.gtabs button small{font-weight:400;color:var(--sub);margin-left:3px}
.gtp{display:none;margin-top:8px}.gtp.on{display:block}.gtp .gadv{margin-top:0}.gtp .gadv>summary{display:none}
.gfin{margin-top:8px;border:1px solid var(--line);border-radius:12px;padding:8px 10px;font-size:13.5px;background:var(--card)}.gfin .h{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.gfin .h b{flex:1 1 100%;color:var(--strong);white-space:nowrap}.gfin ol{margin:6px 0 0;padding-left:22px}.gfin li{margin:3px 0;word-break:break-word}.gfin li i{font-style:normal;color:var(--accent)}
/* V0.3.41 🏷 提示詞積木／📚 整篇範本 */
.pkC{border:1px solid var(--line);border-radius:12px;padding:8px 10px;margin:6px 0;background:var(--card)}.pkCn{font-weight:700;font-size:13.5px;color:var(--strong);margin-bottom:6px;user-select:none;-webkit-user-select:none}.pkCn small{font-weight:400;color:var(--sub)}
.pkOs{display:flex;flex-wrap:wrap;gap:6px}.pkO{border:1px solid var(--line);background:transparent;color:var(--text);border-radius:999px;padding:6px 12px;font-size:14px;max-width:100%;text-align:left;user-select:none;-webkit-user-select:none;-webkit-touch-callout:none}.pkO.on{background:var(--accent);border-color:var(--accent);color:#fff}.pkAdd{border:1px dashed var(--line);background:transparent;color:var(--sub);border-radius:999px;padding:6px 12px}
.pkx{margin-top:6px;padding:8px 10px;border-radius:10px;border:1px dashed var(--accent);font-size:13.5px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}.pkx span{flex:1;min-width:160px}
.pdL{display:flex;flex-direction:column;gap:6px}.pdI{border:1px solid var(--line);border-radius:12px;padding:8px 10px;background:var(--card);user-select:none;-webkit-user-select:none;-webkit-touch-callout:none;cursor:pointer}.pdI b{color:var(--strong)}.pdI .mu{font-size:12.5px;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#pkOv{position:fixed;inset:0;z-index:2147482500;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;padding:14px}#pkOv .pkW{width:min(560px,100%);background:var(--bg);border:1px solid var(--line);border-radius:16px;padding:14px;display:flex;flex-direction:column;gap:10px;max-height:90vh}
#pkOv input,#pkOv textarea{width:100%;box-sizing:border-box;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--text);padding:10px;font-size:15px}#pkOv textarea{min-height:40vh}#pkOv .pkB{display:flex;gap:8px;flex-wrap:wrap}#pkOv .pkB .btn{flex:1;min-width:90px}
/* V0.3.40 🤝 握手 Lv */
.hslv{font-size:12px;font-weight:800;border:1px solid var(--line);background:var(--card);color:var(--strong);border-radius:9px;padding:2px 8px;margin-right:6px;white-space:nowrap}.hslv.boost{border-color:var(--green);color:var(--green)}.hslv.yield{border-color:var(--orange);color:var(--orange)}
#hsOv{position:fixed;inset:0;z-index:2147482000;background:rgba(0,0,0,.6);display:flex;align-items:flex-start;justify-content:center;padding:max(14px,env(safe-area-inset-top)) 10px 14px;overflow:auto}
#hsOv .hsW{width:min(560px,100%);background:var(--bg);border:1px solid var(--line);border-radius:16px;padding:14px}
#hsOv h3{margin:0 0 8px;font-size:17px;color:var(--strong);display:flex;align-items:center;gap:8px}#hsOv h3{flex-wrap:wrap}#hsOv .hsRow span{white-space:nowrap}
#hsOv .hsA{border:1px solid var(--line);border-radius:12px;padding:8px 10px;margin:6px 0;background:var(--card)}#hsOv .hsA.off{opacity:.5}
#hsOv .hsA .t{display:flex;gap:8px;align-items:center}#hsOv .hsA b{flex:1}#hsOv .hsA .pc{font-weight:800;font-size:16px}
#hsOv .hsBar{height:6px;border-radius:4px;background:var(--line);margin-top:6px;overflow:hidden}#hsOv .hsBar i{display:block;height:100%;background:var(--accent)}
#hsOv .hsRow{display:flex;gap:8px;align-items:center;margin:10px 0 4px;font-size:13.5px}#hsOv .hsRow input[type=range]{flex:1}
#hsOv .lvs{display:flex;gap:4px;flex-wrap:wrap;margin-top:6px}#hsOv .lvs button{flex:1;min-width:36px;padding:6px 0;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--text);font-weight:700}#hsOv .lvs button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
/* V0.3.36 ☁ 雲端更新 */
#tabs button.cun::after{content:"☁";font-size:12px;margin-left:3px;vertical-align:super}
.cup{border:1px solid var(--line);border-radius:12px;padding:10px 12px;margin-bottom:10px;background:var(--card)}.cup .cuh{font-weight:700;color:var(--strong)}.cup ul{margin:6px 0 0;padding-left:20px;font-size:13px}.cup .cubs{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.cup .cubs .btn{flex:1;min-width:110px}.cup .cuw{margin-top:8px;padding:8px;border-radius:10px;border:1px solid var(--orange);font-size:13px}.cup .cubar{height:6px;border-radius:4px;background:var(--line);margin-top:8px;overflow:hidden}.cup .cubar i{display:block;height:100%;background:var(--accent)}.cup label{display:flex;gap:8px;align-items:center;font-size:13px;margin-top:10px;color:var(--sub)}
/* V0.3.35 📸 IG（從 TikLive 搬過來） */
.tkdSelBar[hidden],#igd [hidden],.tkdOv [hidden]{display:none!important}
.tkdEmpty{padding:30px;text-align:center;color:var(--sub)}
.tkdTop{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.tkdTop input{flex:1 1 140px;min-width:0;padding:8px 10px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:inherit;font-size:14px}
.tkdTop select{padding:7px 6px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:inherit;font-size:13.5px;max-width:48%}
.tkdTop button{flex:0 0 auto;padding:7px 14px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:inherit;font-size:15px}
.tkdSub{font-size:11.5px;color:var(--sub);margin:6px 0}
.tkdG{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
@media (min-width:700px){.tkdG{grid-template-columns:repeat(6,1fr)}}
.tkdC{cursor:pointer;min-width:0}.tkdC b{display:block;font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:3px}.tkdC small{display:block;font-size:10.5px;color:var(--sub)}
.tkdIm{position:relative;height:0;padding-top:177.78%;background:#14171d;border-radius:8px;overflow:hidden}.tkdIm img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}
.tkdSrc{display:flex;gap:6px;margin-bottom:8px}.tkdSrc button{flex:1;padding:9px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:inherit;font-size:14.5px;font-weight:700}.tkdSrc button.on{background:#2a6b45;border-color:#45d483;color:#fff}
.tkdBar{display:flex;gap:6px;align-items:center;margin-top:6px}.tkdBar span{flex:1;font-size:12.5px;color:var(--sub)}.tkdBar button,.tkdSelBar button{padding:6px 10px;border-radius:9px;border:1px solid var(--line);background:var(--card);color:inherit;font-size:13px;white-space:nowrap}
.tkdSelBar{position:sticky;bottom:0;z-index:5;display:flex;gap:6px;align-items:center;padding:8px;margin-top:8px;border-radius:12px;background:var(--card);border:1px solid #45d483;box-shadow:0 -4px 14px rgba(0,0,0,.35)}.tkdSelBar span{flex:1;font-size:13px}.tkdSelBar #tkdSelSave{background:#2a6b45;border-color:#45d483;color:#fff;font-weight:700}
.tkdCk{display:none;position:absolute;left:4px;top:4px;width:22px;height:22px;border-radius:50%;border:2px solid #fff;background:rgba(0,0,0,.45);color:transparent;text-decoration:none;font-size:13px;line-height:18px;text-align:center}.tkdSelOn .tkdCk{display:block}.tkdC.on .tkdCk{background:#2ecc71;color:#fff}.tkdC.on .tkdIm{outline:3px solid #2ecc71;outline-offset:-3px}
.tkdGot{position:absolute;right:3px;top:3px;font-style:normal;font-size:11px;background:rgba(0,0,0,.6);border-radius:4px;padding:0 3px}
.tkdI{max-width:100%;max-height:100%;object-fit:contain}.tkdImg .tkdSk,.tkdImg .tkdCt [data-k=pp],.tkdImg .tkdRt,.tkdImg .tkdTm{display:none}
.tkdIm em{position:absolute;right:3px;bottom:3px;font-style:normal;font-size:10.5px;background:rgba(0,0,0,.65);color:#fff;padding:0 4px;border-radius:4px}
.tkdOv{position:fixed;inset:0;z-index:2147483000;padding-top:env(safe-area-inset-top,0px);background:#000;display:flex;flex-direction:column;color:#eee}
.tkdPh{display:flex;align-items:center;gap:8px;padding:6px 8px}
.tkdPh button{font-size:18px;padding:4px 12px;border-radius:10px;background:#1b1f27;border:1px solid #2b313c;color:#eee}
.tkdNm{flex:1;min-width:0;display:flex;flex-direction:column}.tkdNm small{font-size:11.5px;color:#9aa3b2}
.tkdDl{padding:8px 12px;border-radius:10px;background:#2a6b45;border:1px solid #45d483;color:#fff;text-decoration:none;font-size:14px;white-space:nowrap}
.tkdSt{position:relative;flex:1;min-height:0;touch-action:none;display:flex;align-items:center;justify-content:center}
.tkdV{max-width:100%;max-height:100%;width:100%;height:100%;object-fit:contain}.tkdN{display:none}
.tkdSw{display:none;position:absolute;left:50%;top:40%;transform:translate(-50%,-50%);background:rgba(0,0,0,.7);padding:10px 16px;border-radius:12px;text-align:center;pointer-events:none}
.tkdSw b{display:block;font-size:22px}.tkdSw small{font-size:12px;color:#ccc}.tkdSw i{display:block;height:4px;background:#333;border-radius:2px;margin-top:6px;width:140px}.tkdSw u{display:block;height:100%;background:#4dc9ff;border-radius:2px;width:0}
.tkdSk{width:calc(100% - 16px);margin:4px 8px}
.tkdCt{display:flex;gap:6px;align-items:center;padding:4px 8px}
.tkdCt button{font-size:16px;padding:6px 12px;border-radius:10px;background:#1b1f27;border:1px solid #2b313c;color:#eee}
.tkdCt select{padding:6px;border-radius:10px;background:#1b1f27;border:1px solid #2b313c;color:#eee}.tkdTm{margin-left:auto;font-size:12.5px;color:#9aa3b2}
.tkdTip{font-size:11px;color:#8a93a3;padding:2px 8px 10px}
.tkdSyncL{display:flex;gap:8px;align-items:center;margin:10px 2px 0;font-size:13.5px}.tkdSyncL input{width:20px;height:20px}.tkdGo{display:flex;gap:8px;margin-top:10px}.tkdGo .btn{flex:1;font-size:15px;padding:12px 6px}   /* TK_V1.0.82 */
.igck{margin-top:12px;border:1px solid var(--line2);border-radius:12px;padding:8px 12px}.igck summary{cursor:pointer;font-weight:700;font-size:14px}.igck summary small{font-weight:400;opacity:.7}.igckB{font-size:13px;line-height:1.6}.igckB ol{padding-left:20px;margin:6px 0}.igckB input{width:100%;box-sizing:border-box;padding:9px 10px;border-radius:9px;border:1px solid var(--line2);background:transparent;color:inherit;margin:6px 0}.igckR{display:flex;gap:8px}.igckR .btn{flex:1}   /* TK_V1.0.80 */
.igdA textarea{width:100%;min-height:84px;box-sizing:border-box;border-radius:12px;border:1px solid var(--line);background:var(--card);color:var(--text);padding:10px;font-size:15px}.igdA .btn{margin-top:8px;width:100%}#igm{display:none;margin-top:8px;padding:8px 10px;border-radius:10px;font-size:13.5px;background:var(--card);border:1px solid var(--line)}#igm.err{border-color:var(--red)}#igm.ok{border-color:var(--green)}.igdDir{font-size:12px;color:var(--sub);margin-top:8px;display:flex;gap:8px;align-items:center}.igdDir button{font-size:12px;padding:3px 8px;border-radius:8px;border:1px solid var(--line);background:transparent;color:var(--sub)}
</style></head><body>
<header><div class="bar"><div class="logo"><i></i>__NAME__</div><div class="rt"><button class="hslv" id="hslv" title="🤝 跟 SortCut、GoPro Fusion 360 分電腦效能">Lv–</button><span class="ver" id="ver" title="程式版本">V__VER__</span></div></div>
<nav id="tabs"></nav></header>
<main id="v"></main>
<div class="toast" id="toast"></div>
<div id="ov"><div id="ovn"></div><button class="ovnav" id="ovp" title="上一張（←）">‹</button><button class="ovnav" id="ovnx" title="下一張（→）">›</button><img id="ovi"><div id="cmp"><img id="cmpa"><div id="cmpb"><img id="cmpbi"></div><div id="cmpl"><i></i></div><span class="cl">舊</span><span class="cr">新</span></div><div id="ovs"></div><div class="ovbot"><button id="ovp2">‹ 上一張</button><span id="ovn2"></span><button id="ovnx2">下一張 ›</button></div><div class="ovact"><button class="pill" id="ovr">✏ 再改這張</button><button class="pill" id="ovpng" style="display:none" title="綠色背景變透明，存成去背 PNG">⬇ 透明 PNG</button><button class="pill acc" id="ovo" style="display:none"></button><a class="pill" id="ovd" download>⬇ 存</a><button class="pill" id="ovsh" style="display:none">📤 分享</button></div>
<div class="ovact sm"><button class="pill" id="ovm3" title="同一張照片、同一句，換隨機種子再做 3 張，挑最好的">🎲 再 3 張</button><button class="pill" id="ovc">⇆ 對比</button><button class="pill" id="ovab" style="display:none"></button><button class="pill" id="ovpair" style="display:none" title="原圖和結果拼成一張存到手機">🖼 拼圖</button><button class="pill" id="ovan" style="display:none" title="這張照片動起來（照片變影片）">🎬 動起來</button><button class="pill" id="ovfl" style="display:none" title="原圖當開始、這張當結束，做成影片">🎞 首尾幀</button><button class="pill" id="ovtpl" style="display:none" title="這張的提示詞存成「📚 範本」或加進「🏷 積木」">📌 存提示詞</button><button class="pill er" id="ovdel" style="display:none" title="放進回收桶">🗑</button><button class="pill" id="ovu" style="display:none">✨ 放大</button><button class="pill" id="ovx" title="關（也可以往下滑）">✖</button></div><div class="mu" style="margin-top:6px;color:#aaa">左右滑換張 · 往下滑關掉 · 點兩下放大</div></div>
<div id="fpk"><div class="row"><b style="font-size:16px">🎞 從影片挑格</b><span class="grow"></span><button class="pill" id="fpx">✖ 關</button></div>
 <div class="mu" id="fpi" style="margin:2px 0 6px"></div><video id="fpv" playsinline muted preload="auto"></video>
 <div class="fpn">第 <span id="fpn">0</span> 格 <small id="fpt"></small></div>
 <input type="range" id="fpr" min="0" max="0" step="1" value="0">
 <div class="fpb"><button class="pill" data-d="-10">⏪ −10</button><button class="pill" data-d="-1">◀ −1</button><button class="pill" data-d="1">+1 ▶</button><button class="pill" data-d="10">+10 ⏩</button></div>
 <button class="pill acc big" id="fpadd" style="margin-top:8px">＋ 選這一格</button>
 <div class="mu" style="margin-top:6px">已選（點縮圖跳回那一格，✕ 取消）：</div><div id="fpsel"></div>
 <div class="row" style="margin-top:4px"><span class="mu">每秒格數</span><select id="fpfps"></select><span class="mu" id="fpfn"></span></div>
 <button class="pill acc big" id="fpok" style="margin-top:8px" disabled>✔ 加到照片</button></div>
<script>
"use strict";
const $=s=>document.querySelector(s),$$=(s,e=document)=>[...e.querySelectorAll(s)];
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const lnk=s=>esc(s).replace(/https:\/\/[^\s<>()（）]+/g,u=>`<a href="${u}" target="_blank" rel="noopener" style="color:var(--blue)">${u}</a>`);   // 訊息裡的網址可以點
const LS={get:(k,d)=>{try{const v=localStorage.getItem('app_'+k);return v==null?d:JSON.parse(v)}catch(e){return d}},set:(k,v)=>{try{localStorage.setItem('app_'+k,JSON.stringify(v))}catch(e){}}};
let IMGDIAG=0;document.addEventListener('error',async e=>{const im=e.target;if(!im||!/^(IMG|VIDEO)$/.test(im.tagName))return;const src=im.currentSrc||im.src||'';if(!/\/api\/img/.test(src)||IMGDIAG)return;IMGDIAG=1;
  let a='?',b='?';try{const r=await fetch(src,{credentials:'same-origin'});a=r.status+' '+(r.headers.get('content-type')||'')+' '+(await r.blob()).size+'B'}catch(x){a='連不到：'+x}
  try{const r=await fetch(src,{headers:{'x-app-token':TOK}});b=r.status+''}catch(x){b='×'}
  const m=`🖼 圖片顯示不出來（診斷）：網址 ${a}／帶標頭 ${b}／登入碼 ${TOK?'有':'沒有'}／${navigator.userAgent.slice(0,90)}`;LS.set('imgdiag',m);toast(m+'　← 請截圖給 Claude',15000)},true);   // V0.3.32 圖片破圖時自動診斷一次
let TT;function toast(t,ms=2600){const d=$('#toast');d.textContent=t;d.style.display='block';clearTimeout(TT);TT=setTimeout(()=>d.style.display='none',ms)}
let TOK=LS.get('tok','');const S={stab:LS.get('stab','set'),scat:LS.get('scat','comfy'),setQ:''};
async function api(u,body,raw){const o={headers:{'x-app-token':TOK}};if(body!==undefined){o.method='POST';if(raw){o.body=body}else{o.body=JSON.stringify(body);o.headers['Content-Type']='application/json'}}
  const r=await fetch(u,o);let j={};try{j=await r.json()}catch(e){}if(r.status===401&&j.login){showLogin();throw new Error('login')}return j}
const U=(p,q)=>{q=Object.assign({},q||{});if(['/api/img','/api/zip','/api/igfile','/api/igthumb'].includes(p)&&TOK)q.k=TOK;return p+'?'+new URLSearchParams(q).toString()};   // V0.3.31 看圖／下載網址帶登入碼（有的平板、App 內瀏覽器不送 cookie）
const fmtB=b=>{b=+b||0;return b>=1e12?(b/1e12).toFixed(2)+' TB':b>=1e9?(b/1e9).toFixed(2)+' GB':b>=1e6?(b/1e6).toFixed(0)+' MB':(b/1e3).toFixed(0)+' KB'};
function setMode(m){document.documentElement.dataset.mode=m;LS.set('mode',m)}setMode(LS.get('mode','dark'));
function setView(v){document.body.classList.toggle('pc',v==='pc');LS.set('view',v)}            // 手機版／網頁版：設定 → 外觀
setView(new URLSearchParams(location.search).get('pc')?'pc':LS.get('view','m'));
const hh=()=>document.documentElement.style.setProperty('--hh',($('header').getBoundingClientRect().height|0)+'px');addEventListener('resize',hh);

function showLogin(){$('#tabs').innerHTML='';$('#v').innerHTML=`<div id="login"><h2>🔒 __NAME__</h2><div class="mu">輸入電腦上設定的 PIN</div><input id="pin" type="password" inputmode="text" autocomplete="current-password"><button class="btn" id="go">登入</button></div>`;
  const go=async()=>{const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:$('#pin').value})});const j=await r.json().catch(()=>({}));
    if(j.ok){TOK=j.token;LS.set('tok',TOK);boot()}else toast(j.message||'登入失敗',4000)};
  $('#go').onclick=go;$('#pin').onkeydown=e=>{if(e.key==='Enter')go()};setTimeout(()=>$('#pin').focus(),100)}

// ---- 分頁：生圖／歷史紀錄／設定（效能、背景、排隊在上面正中間的浮動按鈕）
const TABS=[['gen','🎨 生圖',rGen,''],['cmp','🧪 比較',rCmp,''],['hist','歷史紀錄',rHist,''],['ig','📸 IG',rIg,''],['set','設定',rSet,'tset']];
let CUR=new URLSearchParams(location.search).get('tab')||LS.get('tab','gen'),TIMER=null;if(!TABS.find(x=>x[0]===CUR))CUR='gen';
function tabs(){$('#tabs').innerHTML=TABS.map(([k,n,_f,c])=>`<button data-t="${k}" class="${k===CUR?'on':''} ${c}">${n}${k==='gen'?'<em id="nrun" hidden></em>':''}</button>`).join('');
  $$('#tabs button').forEach(b=>b.onclick=()=>{CUR=b.dataset.t;LS.set('tab',CUR);tabs();show();scrollTo(0,0)});hh();if(typeof cuBadge==='function'&&CUI)cuBadge()}
function show(){clearInterval(TIMER);if(CUR!=='hist'){HSEL=null;const b=$('#hsb');if(b)b.remove()}const t=TABS.find(x=>x[0]===CUR)||TABS[0];t[2]();TIMER=setInterval(()=>{if(!document.hidden)t[2](true)},2000)}

// ================= 🎨 生圖：選照片 → 打提示詞 → （調參數）→ 開始；電腦上的 ComfyUI 跑完結果自動出現在下面
let GLINE={},GSI=LS.get('gslots',[]),GSF=[],GACT=null,GIMGS=LS.get('gimgs',LS.get('gimg','')?[LS.get('gimg','')]:[]),GFILES=[],GWFS=[],GLAST='',GMP=2,GDEF=[],GOFF=0,GJ=[];
const GST={wait:['⏳ 排隊中','var(--orange)'],run:['▶ 生成中','var(--blue)'],done:['✔ 完成','var(--green)'],fail:['✖ 失敗','var(--red)'],stop:['⏹ 已取消','var(--sub)']};
const H3SK="Scene: (整體：地點、時間、人物外觀、氣氛。英文寫效果最好)\nShot 1 (0.00s): (畫面和動作), (鏡頭：close-up / medium shot / wide shot，slow push-in / handheld …).\nShot 2 (2.50s): The camera cuts to (新的畫面). (人物) says in Chinese, softly: \"我們走吧。\"\noverall_soundscape: (環境聲、音效，例如 rain on the window, footsteps)\nnon_diegetic_music: (配樂，例如 soft piano melody；不要配樂寫 N/A)";
const IMGU=f=>U('/api/img',{f});const IMGT=f=>U('/api/img',{f,w:480});const FTAG=n=>{const m=/_f(\d{4,})\.\w+$/.exec(String(n||''));return m?`<span class="ftag">🎞 第 ${+m[1]} 格</span> `:''};const ISV=f=>/\.(mp4|mov|webm|mkv|m4v)$/i.test(String(f||''));
const fmtT=s=>{s=Math.max(0,Math.round(+s||0));const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=s%60;return h?`${h}:${String(m).padStart(2,'0')}:${String(x).padStart(2,'0')}`:`${m}:${String(x).padStart(2,'0')}`};
const SNOW=()=>Date.now()/1000+GOFF;
// 每秒更新畫面上的計時（不用等下一次問電腦）
// ---- 進度條：一直都在（還沒開始跑＝0%）。有以前的時間紀錄 → 照時間每秒往前走；沒有 → 照節點＋步數
// V0.2.86 正在跑的時候顯示 ComfyUI 的即時預覽（ComfyUI 有開預覽才有；沒有就不顯示）
setInterval(()=>{if(document.hidden)return;$$('img.gpv[data-pv]').forEach(im=>{const u=U('/api/gen_prev',{id:im.dataset.pv,t:Date.now()});fetch(u,{headers:{'x-app-token':TOK}}).then(r=>r.status===200?r.blob():null).then(b=>{if(!b)return;const o=GPVU[im.dataset.pv];GPVU[im.dataset.pv]=URL.createObjectURL(b);$$(`img.gpv[data-pv="${im.dataset.pv}"]`).forEach(x=>{x.src=GPVU[im.dataset.pv];x.style.display=''});if(o)setTimeout(()=>URL.revokeObjectURL(o),5000)}).catch(()=>{})})},2500);const GPVU={};
// V0.3.08 失敗原因白話＋下一步
function gFailTip(m){m=String(m||'');const T=[[/out of memory|OOM|記憶體不足|CUDA error|allocate/i,'顯示卡記憶體不夠：畫質改 ⚡ 快、影片改短一點（3～4 秒）再跑；或先關掉電腦上其他吃顯卡的程式'],
  [/缺模型|missing|not found.*safetensors|找不到模型/i,'模型還沒下載：生圖頁流程下面有「⬇ 下載缺的模型」'],[/連不到|ComfyDown|Connection|refused/i,'電腦上的 ComfyUI 沒開或當掉了：打開 Comfy Desktop，工作會自動接著跑'],
  [/沒有這些節點|自訂節點/,'ComfyUI 少了這個流程要的節點：更新 ComfyUI，或到 設定 → 流程 重抓範本'],[/超過 \d+ 分鐘/,'跑太久被停掉：影片改短、畫質改快，或到 設定 → ComfyUI 把逾時調長'],[/照片不見了/,'照片被刪掉了：重新選一次']];
  const t=T.find(([re])=>re.test(m));return t?`<div class="mu" style="font-size:12.5px;margin-top:2px">💡 ${t[1]}</div>`:''}
function gBar(j){const p=j.prog||0,est=j.est&&j.est.sec&&j.prog_how==='time'?j.est.sec:'';
  return `<div class="gpbw"><div class="pg gpb" data-pts="${j.t_start||''}" data-pest="${est}"><i style="width:${p}%"></i></div><b class="gpp">${j.t_start?Math.round(p)+'%':'準備中'}</b></div>`}
setInterval(()=>{$$('.gpb[data-pest]').forEach(e=>{const ts=+e.dataset.pts,es=+e.dataset.pest;if(!ts||!es)return;const p=Math.min(99,(SNOW()-ts)/es*100);e.firstElementChild.style.width=p+'%';const t=e.nextElementSibling;if(t)t.textContent=Math.round(p)+'%'})},1000);
setInterval(()=>{$$('[data-ts]').forEach(e=>{const t=SNOW()-(+e.dataset.ts);let x='⏱ '+fmtT(t);const es=+e.dataset.est;
  if(es){x+=` ／ 預估 ${fmtT(es)}`;x+=t<es?`（還剩約 ${fmtT(es-t)}）`:'（比預估久）'}e.textContent=x})},1000);
function gWf(){return GWFS.find(x=>x.name===$('#gw').value)||{}}
// 最近用過的流程：一鍵切換
function gWq(){const b=$('#gwq');if(!b)return;const cur=$('#gw').value,H=LS.get('gwf_hist',[]).filter(n=>GWFS.some(w=>w.name===n)&&n!==cur).slice(0,4);
  b.innerHTML=H.length?'<span class="mu">最近用：</span>'+H.map(n=>`<button class="gpc" data-gwq="${esc(n)}">${esc(n)}</button>`).join(''):'';
  b.onclick=e=>{const x=e.target.closest('[data-gwq]');if(!x)return;$('#gw').value=x.dataset.gwq;gWfInfo()}}
// V0.2.37 最上面四個模式（你最常做的四件事）：🎨 改一張圖／🧩 兩張圖合併／🎬 照片變影片／🎞 首尾幀影片；點了自動選好流程，下面只顯示這個模式用得到的東西
const GMODES=[['edit','🎨','改一張圖',['GROK 改圖（INT8 快）','Qwen 2.1 Turbo 改圖']],['merge','🧩','兩張圖合併',['兩張圖合併（INT8 快）','兩張圖合併（Qwen 快）','三張圖合併（人物＋衣服＋場景）','兩張圖合併']],
 ['vid','🎬','照片變影片',['H3 照片動起來','H3 照片動起來（臉穩定）','H3 照片動起來（臉穩定＋聲音）','H3 圖生影片']],['fl','🎞','首尾幀影片',['H3 首尾幀生影片']]];
const gModeOf=n=>(GMODES.find(m=>m[3].includes(n))||[''])[0];
function gMode(){const box=$('#gmode');if(!box||!GWFS.length)return;const cur=gModeOf($('#gw').value),has=m=>m[3].some(n=>GWFS.some(w=>w.name===n));
  box.innerHTML=GMODES.map(m=>`<button class="gmo ${m[0]===cur?'on':''} ${has(m)?'':'off'}" data-gm="${m[0]}"><span>${m[1]}</span><b>${m[2]}</b></button>`).join('');
  box.onclick=e=>{const b=e.target.closest('[data-gm]');if(!b)return;const m=GMODES.find(x=>x[0]===b.dataset.gm),av=m[3].filter(n=>GWFS.some(w=>w.name===n));
    if(!av.length){const T={fl:['video_minimax_h3_i2v','H3 首尾幀生影片'],vid:['video_minimax_h3_i2v','H3 照片動起來']}[m[0]];if(!T)return toast('還沒有這個模式的流程',4000);
      if(!confirm(`「${m[2]}」的流程還沒做好。\n現在從你 ComfyUI 裡的官方範本做一個？（ComfyUI 要開著；模型沒有的話會再提示下載）`))return;toast('從範本做流程中…',15000);
      api(U('/api/gen_tpl',{tpl:T[0],name:T[1]}),{}).then(async r=>{toast(r.message||(r.ok?'好了':'失敗'),5000);if(r.ok){LS.set('gwf',T[1]);show()}});return}
    const last=LS.get('gmode_wf:'+m[0],''),pm=gModeOf($('#gw').value)||'other',g=$('#gp');if(pm!==m[0]&&g){LS.set('gprompt:'+pm,g.value);g.value=LS.get('gprompt:'+m[0],'');LS.set('gprompt',g.value)}   // 每個模式記自己的提示詞
    $('#gw').value=av.includes(last)?last:av[0];LS.set('gboth',false);gWfInfo();scrollTo({top:0,behavior:'smooth'})};
  const vs=$('#gvar');if(vs){const m=GMODES.find(x=>x[0]===cur),av=m?m[3].filter(n=>GWFS.some(w=>w.name===n)):[];
    vs.innerHTML=cur&&cur!=='edit'&&av.length>1?av.map(n=>`<button class="gpc ${n===$('#gw').value?'on':''}" data-gv="${esc(n)}">${esc(n.replace(/^H3 /,'').replace(/^兩張圖合併（INT8 快）/,'🏆 GROK 合併').replace(/^兩張圖合併（Qwen 快）/,'⚡ Qwen 合併').replace(/^兩張圖合併/,'合併（舊 fp8）').replace(/^三張圖合併.*/,'＋場景（三張）'))}</button>`).join(''):'';
    const MP=['兩張圖合併（INT8 快）','兩張圖合併（Qwen 快）'];if(cur==='merge'&&MP.every(n=>GWFS.some(x=>x.name===n))&&MP.includes($('#gw').value))vs.innerHTML+=`<button class="gpc ${LS.get('gboth_m',false)?'on':''}" data-gbm="1" title="GROK 和 Qwen 合併各做一次">🔁 兩個都跑</button>`;   // V0.2.85
    if(cur==='vid'&&GWFS.some(x=>x.name==='H3 首尾幀生影片'))vs.innerHTML+=`<button class="gpc" data-gloop="1" title="開始和結束是同一張，影片可以無限重播接不出縫">🔁 無縫循環</button>`;
    vs.onclick=e=>{if(e.target.closest('[data-gbm]')){LS.set('gboth_m',!LS.get('gboth_m',false));gMode();toast(LS.get('gboth_m')?'🔁 GROK、Qwen 合併各做一次':'只跑選的那個',1500);return}if(e.target.closest('[data-gloop]')){gLoop();return}const b=e.target.closest('[data-gv]');if(!b)return;$('#gw').value=b.dataset.gv;gWfInfo()}}
  if(cur)LS.set('gmode_wf:'+cur,$('#gw').value);
  const isE=cur==='edit'||!cur,ismulti=(gWf().n_img||0)>1;['#gbig'].forEach(q=>{const x=$(q);if(x)x.style.display=cur==='edit'?'':'none'});
  ['#gref','#gtpl'].forEach(q=>{const x=$(q);if(x)x.style.display=ismulti||/影片|H3/.test($('#gw').value)?'none':''});{const ml=$('.gmlb');if(ml)ml.style.display=cur==='vid'||cur==='fl'?'none':''}}
// V0.3.22 {紅色|藍色|白色} 變化寫法：一句展開成好幾句各做一張（最多 24 句）
function gExpand(t){const m=/\{([^{}]*\|[^{}]*)\}/.exec(t);if(!m)return [t];return m[1].split('|').flatMap(o=>gExpand(t.slice(0,m.index)+o.trim()+t.slice(m.index+m[0].length)))}
// V0.2.54 🪄 一鍵首尾幀：只有開始畫面時，先用 🏆 GROK 把它改成「結束的樣子」（同一句話），做好自動接著做首尾幀影片
async function gChainFL(w,p){if(!p)return toast('先打一句：中間發生什麼（例如：她從椅子上站起來）',4000);
  const ED=[LS.get('fl_ed','GROK 改圖（INT8 快）'),'GROK 改圖（INT8 快）','Qwen 2.1 Turbo 改圖'].find(n=>GWFS.some(x=>x.name===n));if(!ED)return toast('還沒選：🏁 尾幀（結束畫面）',4000);
  if(!confirm(`還沒選結束畫面。\n要不要先用「${ED}」把這張改成結束的樣子（照你寫的「${p}」），做好自動接著做首尾幀影片？\n\n兩段都會排進去（改圖約 1 分鐘＋影片幾分鐘）。\n（按取消可以改用另一個改圖流程）`)){const o=ED==='GROK 改圖（INT8 快）'?'Qwen 2.1 Turbo 改圖':'GROK 改圖（INT8 快）';if(GWFS.some(x=>x.name===o)&&confirm(`改用「${o}」做結束畫面？`)){LS.set('fl_ed',o);return gChainFL(w,p)}return}
  const b=$('#ggo');b.disabled=true;try{let nm=GIMGS[0];if(!nm&&GFILES[0]){const f=GFILES[0];f._taken=true;nm=f._p?await f._p.catch(()=>null):null;
      if(!nm){const bl=await shrink(f),r=await api('/api/gen_upload',await bl.arrayBuffer(),true);if(!r.ok)return toast('上傳失敗',4000);nm=r.img}GIMGS=[nm];GFILES=[];LS.set('gimgs',GIMGS)}
    const r=await api('/api/gen_run',{wf:ED,prompt:p+GKEEP+'，這是同一個場景過了幾秒之後的樣子',imgs:[nm],n:1,params:LS.get('gpar:'+ED,{}),chain:{kind:'fl',wf:w.name,prompt:p+(LS.get('vmusic',false)?' #music':''),params:LS.get('gpar:'+w.name,{})}});
    toast(r.ok?'🪄 排好了：先改圖做結束畫面，做好自動接著做影片':(r.message||'失敗'),5000);if(r.ok){gJobs();gPrev()}}finally{b.disabled=false}}
// V0.2.62 綠幕去背：越綠越透明，邊緣半透明＋去掉綠色反光（spill），存成 PNG
async function gKeyOut(u,id){toast('去背中…',8000);try{const im=await new Promise((ok,no)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=no;i.src=u});
  const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const g=c.getContext('2d');g.drawImage(im,0,0);const d=g.getImageData(0,0,c.width,c.height),a=d.data;
  for(let i=0;i<a.length;i+=4){const r=a[i],gg=a[i+1],b=a[i+2],m=Math.max(r,b),k=gg-m;if(k>40){const t=Math.min(1,(k-40)/60);a[i+3]=Math.round(255*(1-t))}if(gg>m)a[i+1]=m+Math.round((gg-m)*0.15)}
  g.putImageData(d,0,0);c.toBlob(bl=>{const x=document.createElement('a'),v=URL.createObjectURL(bl);x.href=v;x.download=`去背_${id||''}.png`;document.body.appendChild(x);x.click();x.remove();setTimeout(()=>URL.revokeObjectURL(v),30000);toast('✔ 透明 PNG 存好了',3000)},'image/png')}
  catch(e){toast('去背失敗：'+e,4000)}}
// V0.2.71 🔁 無縫循環影片：首尾幀用同一張（開始＝結束），做出來可以一直重播（動圖、桌布、商品展示）
async function gLoop(){let nm=GIMGS[0];if(!nm&&GFILES[0]){const f=GFILES[0];nm=f._p?await f._p.catch(()=>null):null}if(!nm)return toast('先選一張照片（已經傳好的）',3000);
  GIMGS=[nm];GFILES=[];LS.set('gimgs',GIMGS);GSI=[];GSI[1]=[nm];GSF=[];LS.set('gslots',GSI);$('#gw').value='H3 首尾幀生影片';const g=$('#gp');
  if(!g.value.trim()||/^(waves|slowly|walks|gently|dances|turns|stays|looks)/.test(g.value))g.value='gently moves and breathes naturally, a soft breeze moves the hair and clothes slightly, then returns to exactly the same pose';LS.set('gprompt',g.value);
  gWfInfo();gPrev();toast('🔁 開始＝結束＝同一張：做出來可以無縫重播（動作寫小一點效果最好）',4500)}
// V0.2.41 ⏭ 影片接下一段：瀏覽器把影片跳到最後、畫到畫布上存成照片（H3 單支最長約 15 秒，接龍做長片）
function vLastFrame(u){return new Promise((ok,no)=>{const v=document.createElement('video');v.muted=true;v.playsInline=true;v.preload='auto';v.src=u;
  const t=setTimeout(()=>no('逾時'),20000);v.onloadedmetadata=()=>{v.currentTime=Math.max(0,v.duration-0.05)};
  v.onseeked=()=>{clearTimeout(t);const c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0);c.toBlob(b=>b?ok(b):no('畫不出來'),'image/png')};v.onerror=()=>{clearTimeout(t);no('讀不到影片')}})}
// V0.2.56 🧰 圖生圖工具箱：一鍵設定好「提示詞＋要不要塗／裁＋建議流程」，有選項的先問一下（例如證件照底色、要改成什麼字）
const TOOLS=[
 {k:'erase',ic:'🧽',n:'消除',d:'塗掉不要的東西',kw:'路人 雜物 去掉 移除 刪掉',mask:1,cue:'gray',p:'把照片裡灰色的那一塊補好：補上跟周圍一致、自然連貫的背景，看不出來曾經有東西，其他地方不變'},
 {k:'id',ic:'🪪',n:'證件照',d:'白／藍底、正面',crop:3/4,ask:['底色',['白色','淺藍色','紅色']],p:'改成標準證件照：正面看鏡頭、表情自然、肩膀擺正，{0}純色背景，柔和均勻的攝影棚打光，穿著整齊的深色正裝，保持人物的臉、五官和髮型完全不變'},
 {k:'text',ic:'🔤',n:'改字',d:'招牌、海報上的字',ask:['新的字（指定哪段就寫：舊字→新字）',null],p:'把圖片裡的主要文字改成「{0}」，字型、顏色、粗細、大小、位置和透視都跟原本一樣，其他地方不變'},
 {k:'addt',ic:'🆎',n:'加標題',d:'在圖上加字',ask:['標題文字',null],p:'在圖片上方空白處加上大標題「{0}」，字體漂亮清楚、跟畫面風格搭配，不要擋到人物的臉'},
 {k:'old',ic:'🖼',n:'老照片修復',d:'去刮痕、上色',p:'修復這張老照片：去掉刮痕、污點、摺痕和雜訊，補上自然真實的顏色，讓畫面清楚，保持人物的臉和五官完全不變'},
 {k:'light',ic:'💡',n:'重新打光',d:'換光線氣氛',ask:['光線',['黃金時段暖光','柔和攝影棚光','電影感冷色調','夜晚霓虹燈','陰天柔光']],p:'把整張照片的光線改成{0}，陰影、反光和膚色自然，保持人物、姿勢和背景內容不變'},
 {k:'age',ic:'⏳',n:'年齡變化',d:'變老／變年輕',ask:['變成',['年輕 10 歲','老 20 歲','小時候的樣子','80 歲的樣子']],p:'讓圖中的人看起來{0}，一看就知道是同一個人，五官特徵、髮色、衣服和背景不變'},
 {k:'expr',ic:'😄',n:'換表情',d:'笑、驚訝…',ask:['表情',['開心大笑','自然微笑','驚訝','嘟嘴','閉眼微笑']],p:'讓圖中的人{0}，臉型、五官、髮型、衣服、姿勢和背景都不變'},
 {k:'toon',ic:'🧸',n:'頭像／貼圖',d:'Q 版、動漫、公仔',ask:['風格',['Q 版貼圖（白邊）','日系動漫頭像','3D 公仔','美式卡通']],p:'把圖中的人變成{0}，保留他的臉部特徵、髮型和衣服顏色，乾淨的白色背景'},
 {k:'beauty',ic:'✨',n:'自然美顏',d:'不假的那種',den:0.6,p:'自然地美化人物：皮膚乾淨有光澤、去掉痘痘和黑眼圈、牙齒自然白，保留皮膚質感，臉型和五官完全不變，不要過度磨皮'},
 {k:'body',ic:'🧍',n:'身材微調',d:'自然修身',ask:['調整',['看起來瘦一點','腿長一點','站姿挺一點']],p:'讓圖中的人{0}，自然不誇張，臉、衣服和背景不變，背景線條不要變形'},
 {k:'line',ic:'✏',n:'線稿上色',d:'素描→彩色',p:'把這張線稿或素描上色，變成完整精緻的彩色插畫，顏色自然協調，線條和構圖位置不變'},
 {k:'photo',ic:'📷',n:'畫變照片',d:'插畫→寫實',p:'把這張插畫或卡通變成寫實照片，真實的皮膚、布料和光影，人物特徵、姿勢和構圖不變'},
 {k:'room',ic:'🛋',n:'室內換風格',d:'裝潢設計',ask:['風格',['北歐風','日式無印風','工業風','現代奢華風','溫馨鄉村風']],p:'把這個房間的裝潢和家具改成{0}，保持房間的格局、窗戶和門的位置不變，光線自然'},
 {k:'season',ic:'🍂',n:'換季節天氣',d:'下雪、櫻花…',ask:['變成',['下雪的冬天','櫻花盛開的春天','金黃的秋天','下雨天','晴朗的夏天']],p:'把整個場景變成{0}，人物和建築不變，天空、地面、樹木和光線跟著季節天氣自然改變'},
 {k:'place',ic:'📦',n:'放進東西',d:'把參考圖的東西放進去',mask:1,ref:1,cue:'red',p:'把參考圖裡的東西自然地放在紅色那一塊的位置，紅色要完全去掉，東西的大小比例、角度、光線和陰影都跟場景一致'},
 {k:'cut',ic:'✂',n:'去背（透明）',d:'做貼圖、去背圖',kw:'背景 透明 PNG 摳圖',p:'把背景換成純綠色（#00FF00）的單色背景，主體完整保留、邊緣乾淨清楚，主體本身不要有綠色的反光'},
 {k:'sheet',ic:'🧾',n:'三視圖',d:'正面、側面、背面',p:'生成這個角色的三視圖：正面、側面、背面三個全身像並排，同一個人、同一套衣服和髮型，白色背景，比例一致'},
 {k:'sharp',ic:'🔍',n:'變清楚',d:'模糊、小圖變清晰',kw:'放大 畫質 高清 解析度',den:0.55,hq:1,p:'讓這張照片變清楚：提高清晰度、補上自然的細節（頭髮、皮膚、布料紋理），去掉模糊和雜訊，內容、構圖、顏色和人物長相完全不變'},
 {k:'filter',ic:'🎞',n:'濾鏡調色',d:'日系、復古、黑白',kw:'顏色 色調 調色',den:0.7,ask:['風格',['日系清新','復古底片','黑白經典','電影感','暖色溫馨','冷色高級']],p:'把整張照片調成{0}的色調和質感，只改顏色、光影和顆粒感，內容、構圖和人物長相完全不變'},
 {k:'pose',ic:'🤸',n:'換姿勢',d:'叉腰、比 YA、回眸…',kw:'動作 姿勢',ask:['姿勢',['雙手叉腰站著','比 YA 自拍','側身回眸看鏡頭','坐在椅子上翹腳','開心跳起來','雙手抱胸','手托下巴思考','走路的動態抓拍']],p:'讓圖中的人改成{0}的姿勢，臉、五官、髮型、衣服和背景完全不變，手指和身體比例自然'},
 {k:'hair',ic:'💇',n:'換髮型',d:'髮型、髮色',kw:'頭髮 染髮',ask:['換成',['短髮鮑伯頭','長直髮','大波浪捲髮','綁馬尾','丸子頭','金色頭髮','奶茶色頭髮','粉紅色頭髮','銀灰色頭髮']],p:'把圖中人物的頭髮換成{0}，髮絲自然、跟臉型搭配，臉、五官、衣服和背景完全不變'},
 {k:'makeup',ic:'💄',n:'換妝容',d:'淡妝、韓系、派對',kw:'化妝 口紅',ask:['妝容',['自然淡妝','韓系水光妝','日系可愛妝','歐美派對妝','復古紅唇','素顏感']],p:'幫圖中人物畫上{0}，五官和臉型完全不變，皮膚質感自然，其他地方不變'},
 {k:'set',ic:'📸',n:'寫真組圖',d:'同一人 6 種場景',multi:['在咖啡廳窗邊，自然光，拿著咖啡杯微笑','在海邊夕陽下，海風吹動頭髮','在城市街頭夜景，霓虹燈光，時尚穿搭','在花園裡，春天的花海，柔和光線','在純白攝影棚，專業棚拍光，正面半身','在圖書館書架前，溫暖的光線，看著鏡頭'],p:''},
 {k:'stk',ic:'😆',n:'LINE 貼圖組',d:'同一人 8 種表情',multi:['開心大笑比讚，旁邊寫「讚」','害羞摀臉，旁邊寫「害羞」','生氣跺腳，旁邊寫「哼」','驚訝張嘴，旁邊寫「蛤？」','哭哭流淚，旁邊寫「嗚嗚」','比愛心，旁邊寫「愛你」','鞠躬，旁邊寫「謝謝」','揮手，旁邊寫「掰掰」'],p:''},
 {k:'sky',ic:'🌅',n:'換天空',d:'藍天、晚霞、星空',ask:['天空',['晴朗藍天白雲','夕陽晚霞','滿天星空和銀河','雨後彩虹','戲劇性的雲']],p:'把照片裡的天空換成{0}，地面、建築、人物和其他東西不變，整體光線和色調跟著新天空自然調整'},
 {k:'pet',ic:'🐶',n:'寵物',d:'穿衣、擬人、頭像',ask:['變成',['穿上可愛的毛衣','戴上小帽子和圍巾','擬人化成穿西裝的紳士','卡通頭像（白底）','坐在小沙發上的寫真']],p:'讓照片裡的寵物{0}，保持牠的品種、毛色、花紋和臉完全不變'},
 {k:'prod',ic:'🛍',n:'商品組圖',d:'主圖＋情境＋特寫',multi:['商品放在純白背景上，乾淨的電商主圖，柔和陰影','商品放在溫馨的居家情境裡，自然光，生活感','商品特寫，看得清楚材質和細節，淺景深','商品放在大理石桌面上，高級感的光線','商品漂浮在柔和的漸層背景上，有倒影'],p:''},
 {k:'outfit',ic:'👔',n:'換衣服',d:'打字選，不用衣服圖',kw:'穿搭 服裝 衣服 西裝 洋裝',ask:['換成',['白襯衫配牛仔褲','黑色西裝','紅色晚禮服','休閒運動服','日式和服','韓系針織毛衣']],p:'把圖中人物的衣服換成{0}，衣服合身、布料皺褶和光影自然，臉、五官、髮型、姿勢和背景都不變'},
 {k:'bg',ic:'🏙',n:'換背景',d:'打字選，不用場景圖',kw:'背景 場景 地點',ask:['換到',['海邊沙灘','東京街頭','咖啡廳裡','雪山','純白攝影棚','森林小徑']],p:'把背景換成{0}，人物的臉、姿勢、衣服完全不變，光線方向、色調和陰影跟新背景一致，邊緣自然'},
 {k:'bw',ic:'🌈',n:'黑白上色',d:'黑白照變彩色',kw:'上色 彩色 黑白',den:0.7,p:'幫這張黑白照片上色：自然真實的膚色、衣服和背景顏色，色彩協調不過度飽和，內容、構圖和人物五官完全不變'},
 {k:'car',ic:'🚗',n:'換色／材質',d:'車、衣服、家具',ask:['改成',['亮紅色','消光黑','珍珠白','金屬銀','木紋']],p:'把圖中主要物品的顏色或材質改成{0}，形狀、細節、反光和背景不變'}];
let GCUE=null,TQ='';   // 工具要的局部提示方式（提示詞沒被換掉才算）
const TCAT=[['🧑 人像',['id','beauty','expr','pose','hair','makeup','outfit','age','body','toon','sheet','set','stk']],['🧹 修圖',['erase','place','sharp','old','bw','cut','filter']],['🔤 文字',['text','addt']],['🎨 場景風格',['bg','light','sky','season','room','car','line','photo','pet','prod']]];
function gTool(){const box=$('#gtool');if(!box)return;{const tp=$('#gtpl'),hm=$('#gref');if(tp&&hm&&tp.closest('#gtool'))hm.after(tp)}const w=gWf();if(gModeOf(w.name)!=='edit'&&!(w.need_img&&(w.n_img||0)<=1&&!/H3|影片/.test(w.name))){const tp=$('#gtpl'),hm=$('#gref');if(tp&&hm&&tp.closest('#gtool'))hm.after(tp);box.innerHTML='';return}const op=LS.get('gtool_o2',false);
  box.innerHTML=`<details class="gadv" ${op?'open':''} id="gtd"><summary>🧰 工具箱 <span class="mu">點一個，提示詞和要做的事自動設好</span></summary><div class="row" style="gap:6px;flex-wrap:wrap;margin-bottom:8px">${LS.get('trecent',[]).length?`<button class="gpc ${LS.get('tcat',0)===-1?'on':''}" data-tc2="-1">🕘 最近</button>`:''}${TCAT.map((c,i)=>`<button class="gpc ${i===LS.get('tcat',0)?'on':''}" data-tc2="${i}">${c[0]}</button>`).join('')}<input id="tq" class="gsel" placeholder="🔍 找工具" style="flex:1;min-width:90px;height:30px;padding:0 10px" value="${esc(TQ)}"></div><div class="tgrid">${(TQ?TOOLS.filter(t=>(t.n+t.d+(t.kw||'')).includes(TQ)).map(t=>t.k):LS.get('tcat',0)===-1?LS.get('trecent',[]):(TCAT[LS.get('tcat',0)]||TCAT[0])[1]).map(k=>TOOLS.find(t=>t.k===k)).filter(Boolean).map(t=>`<button class="tbtn" data-tk="${t.k}"><span>${t.ic}</span><b>${t.n}</b><small>${t.d}</small></button>`).join('')}</div><div id="task"></div><div id="gtplhost" style="margin-top:6px"></div></details>`;
  const tp=$('#gtpl');if(tp)$('#gtplhost').appendChild(tp);   // V0.2.72 常用改法收進工具箱裡（第二區少一排）
  box.querySelector('.row').onclick=e=>{const c=e.target.closest('[data-tc2]');if(!c)return;TQ='';LS.set('tcat',+c.dataset.tc2);gTool()};
  const tq=$('#tq');tq.oninput=()=>{TQ=tq.value.trim();gTool();const n=$('#tq');n.focus();n.setSelectionRange(n.value.length,n.value.length)};
  $('#gtd').ontoggle=()=>LS.set('gtool_o2',$('#gtd').open);
  box.querySelector('.tgrid').onclick=e=>{const b=e.target.closest('[data-tk]');if(!b)return;const t=TOOLS.find(x=>x.k===b.dataset.tk);LS.set('trecent',[t.k].concat(LS.get('trecent',[]).filter(k=>k!==t.k)).slice(0,8));$$('.tbtn',box).forEach(x=>x.classList.toggle('on',x===b));
    if(t.multi){const g=$('#gp'),keep=t.k==='set'?'，保持人物的臉、五官、髮型和身材完全不變':t.k==='stk'?'。把圖中的人畫成 Q 版可愛貼圖，保留他的臉部特徵和髮型，粗白邊，背景是純綠色（#00FF00），字是可愛的手寫字':'，商品的形狀、顏色、Logo 和細節完全不變';g.value=t.multi.map(x=>x+keep).join('\n\n');g.rows=12;LS.set('gprompt',g.value);$('#gml').checked=true;LS.set('gml',true);gMlInfo();GCUE=null;
      toast(`${t.ic} ${t.n}：${t.multi.length} 句各做一張（同一個種子、收成一組），可以刪掉不要的行`,4000);return}   // V0.2.91 組圖
    const go=v=>{const g=$('#gp');g.value=t.p.replace('{0}',v||'');if(t.k==='text'&&/→|->/.test(v||'')){const [o,n]=v.split(/→|->/).map(x=>x.trim());g.value=`把圖片裡的「${o}」改成「${n}」，字型、顏色、粗細、大小、位置和透視都跟原本一樣，其他文字和地方都不變`}GCUE=t.cue?{cue:t.cue,p:g.value.slice(0,12)}:null;
      setTimeout(()=>{let it=null;GDEF.forEach(G=>G.items.forEach(x=>{if(!it&&/\.denoise$/.test(x.id))it=x}));if(it){const O=LS.get(PK(),{});if(t.den)O[it.id]=t.den;else delete O[it.id];LS.set(PK(),O);gParams()}},t.k==='erase'||t.k==='id'?600:50);LS.set('gprompt',g.value);$('#task').innerHTML='';   // 工具建議的改動幅度（美顏用輕輕修）
      if(BIG.some(x=>x[0]==='GROK 改圖（INT8 快）')&&GWFS.some(x=>x.name==='GROK 改圖（INT8 快）')&&$('#gw').value!=='GROK 改圖（INT8 快）'&&['text','addt','id','old','erase'].includes(t.k)){$('#gw').value='GROK 改圖（INT8 快）';LS.set('gboth',false);gWfInfo()}
      if(t.hq)setTimeout(()=>{const b=$$('#gqual [data-gq]');if(b.length===3)b[2].click()},700);   // 變清楚：畫質自動用 🔍 精細
      if(!GIMGS.length&&!GFILES.length){toast(`${t.ic} ${t.n}：提示詞設好了，先選照片`,3000);return}
      if(t.ref&&!GREF){toast('📦 先按下面「📎 加參考圖」選要放進去的東西，再塗要放的位置',5000);$('#grf').click();setTimeout(()=>mkOpen(0),400);return}
      if(t.mask){toast(t.k==='erase'?'🧽 塗你要去掉的東西，塗好按「好了」再按開始':'塗要放東西的位置，塗好按「好了」再按開始',3500);mkOpen(0);return}
      if(t.crop){toast('🪪 先框出頭和肩膀（3:4），框好按「用這個範圍」再按開始',4000);crOpen(0,t.crop);return}
      toast(`${t.ic} ${t.n}：設好了，按開始（可以再改提示詞）`,2500)};
    if(!t.ask)return go();const [lab,opts]=t.ask,ta=$('#task');
    ta.innerHTML=opts?`<div class="row" style="gap:6px;flex-wrap:wrap;margin-top:8px"><span class="mu">${esc(lab)}：</span>${opts.map(o=>`<button class="gpc" data-to="${esc(o)}">${esc(o)}</button>`).join('')}</div>`
      :`<div class="row" style="gap:6px;margin-top:8px"><input id="tin" class="gsel" placeholder="${esc(lab)}"><button class="pill acc" id="tok">好</button></div>`;
    if(opts)ta.onclick=e=>{const o=e.target.closest('[data-to]');if(o)go(o.dataset.to)};else{const i=$('#tin');i.focus();$('#tok').onclick=()=>{if(!i.value.trim())return toast('先打字');go(i.value.trim())};i.onkeydown=e=>{if(e.key==='Enter')$('#tok').click()}}}}
// V0.2.38 🎬 影片常用動作：點一下填英文動作（H3 看英文最準；要說話可以寫中文對白）
const GVACT=[['👋 揮手打招呼','waves hello at the camera with a warm smile'],['😊 轉頭微笑','slowly turns their head toward the camera and smiles'],['🚶 走向鏡頭','walks slowly toward the camera'],
 ['💁 撥頭髮','gently brushes their hair behind the ear and smiles'],['🗣 對鏡頭說話','looks at the camera and smiles; the person (S1) says: <d>[Chinese] 大家好，歡迎來到我的頻道</d>'],['💃 輕輕跳舞','dances gently to soft music, swaying side to side'],
 ['🔄 轉一圈','turns around slowly in a full circle'],['🎥 鏡頭推近','stays still while the camera slowly pushes in to a close-up'],['🌀 鏡頭環繞','stays still while the camera slowly orbits around them'],
 ['🍃 微風吹動','stands still and breathes naturally while a gentle breeze moves their hair and clothes; leaves in the background sway softly'],['😂 開心大笑','bursts into natural, joyful laughter'],['📸 換幾個拍照姿勢','strikes three different relaxed poses for the camera, one after another'],['☕ 喝一口飲料','lifts the cup, takes a sip, and smiles']];
const GFACT=[['🚶 走過去','walks naturally from the first position to the last position'],['🪑 坐下／站起','smoothly changes posture from the first frame to the last frame'],['🔄 轉身','turns around slowly'],
 ['🎥 鏡頭移動','the camera moves smoothly from the first framing to the last framing'],['🌅 時間變化','the light and scene gradually change, like time passing'],['😄 表情變化','the facial expression changes naturally from the first frame to the last frame'],['✨ 變身換裝','spins once and the outfit magically transforms into the outfit in the last frame, with sparkling light']];
function gVact(){const box=$('#gvact');if(!box)return;const n=$('#gw').value,L=/首尾幀/.test(n)?GFACT:/H3/.test(n)?GVACT:null;if(!L){box.innerHTML='';return}
  box.innerHTML=`${/首尾幀/.test(n)?'':`<label class="gpc kp ${LS.get('vseq',false)?'on':''}" title="每一行是一段，做完一段用最後一格接下一段，最後自動接成一支長片"><input type="checkbox" id="gvseq" ${LS.get('vseq',false)?'checked':''}>🎞 長片（每行一段）</label>`}<button class="gpc" id="gsay">🗣 加一句台詞</button><label class="gpc kp ${LS.get('vmusic',false)?'on':''}"><input type="checkbox" id="gvmus" ${LS.get('vmusic',false)?'checked':''}>🎵 配樂</label><span class="mu">🎬 常用動作</span>${L.map(([z,e])=>`<button class="gpc" data-va="${esc(e)}">${z}</button>`).join('')}`;
  $('#gsay').onclick=()=>{const t=prompt('要說什麼？（中文就好，會用官方對白格式，嘴型和聲音比較對得上）');if(!t||!t.trim())return;const g=$('#gp');const base=g.value.trim().replace(/[.。]+$/,'')||'looks at the camera';
    g.value=base.replace(/;?\s*the person \(S1\) says: <d>.*?<\/d>/,'')+`; the person (S1) says: <d>[Chinese] ${t.trim()}</d>`;LS.set('gprompt',g.value);toast('🗣 加好了（影片 4 秒大約說一句短的）',2500)};   // V0.2.81
  const sq=$('#gvseq');if(sq)sq.onchange=()=>{LS.set('vseq',sq.checked);if(sq.checked){$('#gml').checked=false;LS.set('gml',false);const g=$('#gp');if(!g.value.includes('\n')){g.value=(g.value.trim()||'walks slowly toward the camera')+'\nstops and waves hello with a smile\nturns around and walks away';g.rows=5;LS.set('gprompt',g.value)}}gVact();toast(sq.checked?'🎞 長片：每一行一段（一段 3～4 秒），做完自動接成一支':'一般影片',3500)};
  $('#gvmus').onchange=()=>{LS.set('vmusic',$('#gvmus').checked);gVact();toast($('#gvmus').checked?'🎵 影片會加輕柔的背景配樂':'不加配樂（只有環境聲）',1800)};
  box.onclick=e=>{const b=e.target.closest('[data-va]');if(!b)return;const g=$('#gp');g.value=b.dataset.va;LS.set('gprompt',g.value);toast('填好了（英文 H3 比較聽得懂，可以直接改）',2500)}}
// V0.2.49 兩張圖的模式也能「從最近用過的挑」：先選要放進哪一格，再點小圖（不用每次從相簿找）
async function gMrec(w){const box=$('#gmrec');if(!box)return;const n=w.n_img||0;if(n<2||(w.kinds||[]).includes('video')){box.innerHTML='';return}
  const T=(w.slots||[]).map((t,i)=>String(t).replace(/^[^：:]*[：:]\s*/,'')||('圖'+(i+1)));let tg=Math.min(LS.get('gmrec_t',1),n-1);
  box.innerHTML=`<div class="row" style="gap:6px;margin-top:10px"><button class="gchip" id="gmrb">🕘 從最近用過的挑</button><button class="gchip" id="gmsw" title="圖一和圖二對調">⇄ 圖一圖二對調</button></div><div id="gmrl"></div>`;
  $('#gmsw').onclick=async()=>{let a0=GIMGS[0];if(!a0&&GFILES[0]){a0=GFILES[0]._p?await GFILES[0]._p.catch(()=>null):null}let b0=(GSI[1]||[])[0];if(!b0&&(GSF[1]||[])[0]){const f=GSF[1][0],bl=await shrink(f),r=await api('/api/gen_upload',await bl.arrayBuffer(),true);b0=r.ok?r.img:null}
    if(!a0||!b0)return toast('兩格都要先有照片（而且傳好了）');GIMGS=[b0];GFILES=[];LS.set('gimgs',GIMGS);GSI[1]=[a0];GSF[1]=[];LS.set('gslots',GSI);gPrev();gPrevSlot(1);toast('⇄ 對調了',1200)};
  $('#gmrb').onclick=async()=>{const L=$('#gmrl');if(L.innerHTML){L.innerHTML='';return}const r=await api(U('/api/cmp',{a:'recent'}));const I=r.imgs||[];
    const draw=()=>{L.innerHTML=`<div class="row" style="gap:6px;margin:8px 0 4px;flex-wrap:wrap"><span class="mu">放進：</span>${T.map((t,i)=>`<button class="gpc ${i===tg?'on':''}" data-mt="${i}">${['圖一','圖二','圖三','圖四'][i]||i+1}・${esc(t)}</button>`).join('')}</div>
      <div class="crec">${I.length?I.map(x=>`<img src="${IMGT('inputs/'+x)}" data-mi="${esc(x)}" loading="lazy">`).join(''):'<span class="mu">還沒有用過的照片</span>'}</div>${PP.length?`<div class="mu" style="margin:6px 0 2px">👤 人物庫</div><div class="crec">${PP.map(([c,f])=>`<img src="${IMGT('people/'+c+'/'+f)}" data-pp="${esc(c+'/'+f)}" title="${esc(c)}" loading="lazy">`).join('')}</div>`:''}`};
    const pr=await api('/api/people');const PP=((pr&&pr.people)||[]).filter(x=>x.photos.length).flatMap(x=>x.photos.slice(0,3).map(f=>[x.code,f]));draw();   // V0.2.93 人物庫的照片也能直接放進格子
    L.onclick=e=>{const t=e.target.closest('[data-mt]');if(t){tg=+t.dataset.mt;LS.set('gmrec_t',tg);draw();return}const m=e.target.closest('[data-mi]');if(!m)return;const x=m.dataset.mi;
      if(tg===0){GIMGS=[x];GFILES=[];LS.set('gimgs',GIMGS);gPrev()}else{GSI[tg]=[x];GSF[tg]=[];LS.set('gslots',GSI);gPrevSlot(tg)}toast(`✔ 放進${['圖一','圖二','圖三','圖四'][tg]}`,1200)};
    L.addEventListener('click',async e=>{const q=e.target.closest('[data-pp]');if(!q)return;const b=await (await fetch(IMGU('people/'+q.dataset.pp),{headers:{'x-app-token':TOK}})).blob();const r=await api('/api/gen_upload',await b.arrayBuffer(),true);if(!r.ok)return toast('放不進去：'+(r.message||''));
      if(tg===0){GIMGS=[r.img];GFILES=[];LS.set('gimgs',GIMGS);gPrev()}else{GSI[tg]=[r.img];GSF[tg]=[];LS.set('gslots',GSI);gPrevSlot(tg)}toast(`✔ 人物庫的照片放進${['圖一','圖二','圖三','圖四'][tg]}`,1500)})}}
// V0.3.15 新功能導覽：版本有大更新時，生圖頁最上面一張小卡（看過按 ✕ 就不再出現）
const TOUR_V='0.4';function gTour(){const b=$('#gtour');if(!b)return;if(LS.get('tour_seen','')===TOUR_V){b.innerHTML='';return}
  b.innerHTML=`<div class="gnews" style="flex-direction:column;align-items:stretch"><div class="row"><b class="grow">✨ 提示詞建議用法</b><button class="pill" id="gtx">✕ 知道了</button></div>
   <div class="mu" style="line-height:1.7;font-size:13px">① 打字框：寫這次臨時想要的（例如「人物面帶笑容」）。<br>② 🏷 積木：常換的東西建成分類（場景、上衣、動作…），點選就加在後面，不選就不加。<br>③ 📚 範本：整篇很多段的存起來，點一下帶上來，每段做一次（多篇文字）。<br>④ 送出前看「📝 會送出 N 個提示詞」確認。<br>⑤ 看了前一兩張不滿意：卡片上「⏹ 取消這一批」。<br>右上角「Lv」：跟 SortCut、GoPro 分電腦效能。</div></div>`;
  $('#gtx').onclick=()=>{LS.set('tour_seen',TOUR_V);gTour()}}
// V0.2.36 🧩 兩張圖合併：三種合法（圖一＝人物）——換衣服／換場景／照動作，點一下就填好寫得很完整的提示詞
const GMRG=[['👗 換衣服','圖二放衣服（模特兒穿的、平拍的都可以）','讓圖1的人穿上圖2的衣服。衣服的款式、顏色、圖案、材質都要跟圖2一樣，自然合身；圖1人物的臉、五官、髮型、身材、姿勢和背景完全不變'],
 ['🏞 換場景','圖二放場景（地點、房間、風景）','把圖1的人放進圖2的場景裡。圖1人物的臉、五官、髮型、衣服和身材完全不變；場景照圖2，光線、色調和陰影跟圖2一致，人的大小比例自然，像真的在那裡拍的'],
 ['🧍 照動作','圖二放想要的姿勢（任何人做的都可以）','讓圖1的人做出跟圖2一模一樣的姿勢和動作，手、腳、頭和身體的角度都一樣。圖1人物的臉、五官、髮型、衣服和背景完全不變，只改姿勢'],
 ['👫 兩人合照','圖二放另一個人（2511 最拿手的）','讓圖1的人和圖2的人站在一起自然地合照，圖1的人在左邊、圖2的人在右邊，兩個人的臉、五官、髮型和衣服都跟原圖完全一樣，背景用圖1的，光線一致'],
 ['🛍 拿著商品','圖二放商品（包包、飲料、手機…）','讓圖1的人自然地拿著圖2的商品，手勢自然、握法合理，商品的外型、顏色、文字和標誌都跟圖2一模一樣、大小比例正確；圖1人物的臉、五官、髮型、衣服和背景完全不變'],
 ['🎨 照畫風','圖二放想要的畫風（插畫、油畫…）','把圖1畫成圖2的畫風：筆觸、色彩、線條和質感都照圖2；圖1的人物特徵、姿勢、構圖和內容不變，不要畫進圖2裡的人或東西']];
function gMrg(w){const box=$('#gmrg');if(!box)return;if(/^三張圖合併/.test(w.name||'')){box.innerHTML='<div class="mu" style="margin-bottom:6px">👗＋🏞 圖一人物、圖二衣服、圖三場景，一次換好（提示詞已經寫好，可以補細節）</div>';const g=$('#gp');if(g&&(!g.value.trim()||GMRG.some(m=>m[2]===g.value.trim()))){g.value='讓圖1的人穿上圖2的衣服，站在圖3的場景裡。圖1人物的臉、五官、髮型和身材完全不變；衣服的款式、顏色、材質跟圖2一樣；場景、光線和色調跟圖3一致，看起來像真的在那裡拍的';LS.set('gprompt',g.value)}return}
  if(!/^兩張圖合併/.test(w.name||'')||(w.n_img||0)<2){box.innerHTML='';return}const cur=LS.get('gmrg_m',0);
  const g0=$('#gp');if(g0){g0.placeholder='點上面一種，或自己寫（圖1＝人物、圖2＝衣服／場景／動作）';if(!g0.value.trim()||/站在圖3的場景裡/.test(g0.value)){g0.value=GMRG[cur][2];LS.set('gprompt',g0.value)}}
  const PARTS=[['整套','衣服'],['上衣','上衣'],['褲子／裙子','下身（褲子或裙子）'],['外套','外套'],['鞋子','鞋子'],['包包／配件','包包和配件'],['帽子','帽子']];   // V0.2.89 只換某一件
  box.innerHTML=`<div class="gmb">${GMRG.map((m,i)=>`<button class="gbb ${i===cur?'on':''}" data-mg="${i}"><b>${m[0]}</b><small>${m[1]}</small></button>`).join('')}</div>`
   +(cur===0?`<div class="row" style="gap:6px;flex-wrap:wrap;margin:-2px 0 8px"><span class="mu">只換：</span>${PARTS.map(([n,w2])=>`<button class="gpc" data-mp="${esc(w2)}">${n}</button>`).join('')}</div>`:'')
   +(cur===1?`<div class="row" style="gap:6px;flex-wrap:wrap;margin:-2px 0 8px"><span class="mu">放哪裡：</span>${[['中間','站在畫面中間'],['左邊','站在畫面左邊三分之一處'],['右邊','站在畫面右邊三分之一處'],['坐著','自然地坐在場景裡適合坐的地方'],['遠一點','站在比較遠的地方，人小一點、看得到整個場景'],['近一點','靠近鏡頭，拍到上半身']].map(([n,w2])=>`<button class="gpc" data-ms="${esc(w2)}">${n}</button>`).join('')}</div>`:'');   // V0.2.90
  box.onclick=e=>{const sp=e.target.closest('[data-ms]');if(sp){const g=$('#gp');g.value=`把圖1的人放進圖2的場景裡，${sp.dataset.ms}。圖1人物的臉、五官、髮型、衣服和身材完全不變；場景照圖2，光線、色調和陰影跟圖2一致，人的大小比例自然，像真的在那裡拍的`;LS.set('gprompt',g.value);toast('位置設好了',1500);return}
    const pp=e.target.closest('[data-mp]');if(pp){const x=pp.dataset.mp,g=$('#gp');g.value=x==='衣服'?GMRG[0][2]:`讓圖1的人換上圖2的${x}，${x}的款式、顏色、圖案和材質都跟圖2一樣，自然合身；圖1人物身上其他的衣物、臉、五官、髮型、身材、姿勢和背景完全不變`;LS.set('gprompt',g.value);toast(`只換${x}（其他衣服不動）`,2000);return}
    const b=e.target.closest('[data-mg]');if(!b)return;const i=+b.dataset.mg,g=$('#gp');if(g.value.trim()&&!GMRG.some(m=>m[2]===g.value.trim())&&!confirm('換成「'+GMRG[i][0]+'」的提示詞？（現在的字會被換掉）'))return;
    LS.set('gmrg_m',i);g.value=GMRG[i][2];LS.set('gprompt',g.value);gMrg(w);
    const TIP=['想讓臉和背景一個像素都不動：按圖一下面「🖌 只改圖一的哪裡」塗衣服那塊','想讓人一個像素都不動：「🖌 只改圖一的哪裡」塗人物，再按「🔁 反過來：塗的保留」','圖二的姿勢越清楚（全身、正面）越準；可以再補一句「左手插口袋」這種細節','兩個人的照片光線、角度接近，合起來比較自然','商品圖越清楚（去背、正面）越準；有文字的商品用 INT8 品質比較好','圖二只要能看出畫風就好，越有特色越明顯'];
    toast(`${GMRG[i][0]}：${GMRG[i][1]}。💡 ${TIP[i]}`,6000)}}
function gWfInfo(){const w=gWf();gWq();gBig();gMrg(w);gMode();gVact();gTool();if((w.n_img||0)<=1)gPrev();if(GREF)gRef();const isB=BIG.some(b=>b[0]===w.name)||!!gModeOf(w.name),ad=$('#gadv');if(ad){ad.classList.toggle('flat',!isB);ad.open=!isB||LS.get('gadv_open',false);ad.ontoggle=()=>{if(!ad.classList.contains('flat'))LS.set('gadv_open',ad.open)}}setTimeout(()=>{const wi=$('#gwi');if(wi)wi.classList.toggle('big',isB&&!w.err)},0);const need=!!w.need_img;
  const T=x=>`<span class="gt">${x}</span>`;
  $('#gwi').innerHTML=w.err?`<span style="color:var(--red)">✖ ${esc(w.err)}</span>`:T(need?((w.kinds||[]).includes('video')?`📷 ${(w.kinds||[]).filter(k=>k==='image').length} 張照片＋🎬 ${(w.kinds||[]).filter(k=>k==='video').length} 支影片${w.segmented?' · 分段跑':''}`:(w.n_img||0)>1?`📷 要 ${w.n_img} 張照片`:'📷 要照片'):'不用照片')
    +(w.pos?`<span class="gt" title="${esc(w.pos)}">✏ 有吃提示詞</span>`:(w.cr||{}).blank_ok?'':T('⚠ 找不到提示詞欄位'))+(w.outputs&&w.outputs.length?`<span class="gt" title="${esc(w.outputs.join('、'))}">${(w.kinds_out||'')==='video'||/video/i.test(w.outputs.join(''))?'🎬 出影片':'🖼 出圖'}</span>`:'')+(GLINE[w.name]?`<span class="gt">${GLINE[w.name].steps} 步</span><span class="gt" title="${esc(GLINE[w.name].lic)}">${/Apache|MIT/.test(GLINE[w.name].lic)?'✔ 可商用':/不能商用|非商用|NC|研究/.test(GLINE[w.name].lic)?'⚠ 不能商用':'授權看說明'}</span><div class="mu" style="flex-basis:100%;margin-top:2px">${esc(GLINE[w.name].note)}</div>`:'');
  const cr=w.cr||{};$('#gh3').style.display=/H3|minimax/i.test(w.name||'')&&!cr.simple?'':'none';
  $('#gp').placeholder=cr.placeholder||'想怎麼改？例如：把衣服換成紅色連身裙';
  $('#gnd').style.display=w.neg?'':'none';$('#gcard1').style.display=need?'':'none';$('#gfolder').style.display=(w.n_img||0)>1?'none':'';gSlots(w);gMrec(w);gModels();LS.set('gwf',w.name||'');gParams()}
// ---- 參數：常用的打開，其他（模型／LoRA、各節點）收合；改過的會變色，記在這支手機（每個流程分開記）
const PK=()=>'gpar:'+$('#gw').value;
async function gParams(){const box=$('#gpar');box.innerHTML='<div class="mu">讀取參數中…</div>';const wf=$('#gw').value;if(!wf){box.innerHTML='';return}
  const r=await api(U('/api/gen_params',{wf}));if($('#gw').value!==wf)return;if(!r.ok){box.innerHTML=`<div class="mu">${esc(r.message||'讀不到參數')}</div>`;return}
  GDEF=r.groups||[];const O=LS.get(PK(),{});GDEF.forEach(g=>g.items.forEach(it=>{if(it.id in O&&String(O[it.id])===String(it.type==='seed'?'':it.value))delete O[it.id]}));LS.set(PK(),O);const GOK=BIG.some(b=>b[0]===wf)||gModeOf(wf)?'gopenB':'gopen',OPEN=LS.get(GOK,{});   // 定案的兩個流程：參數預設收起來（有畫質三段就夠），自己打開會記住
  const inp=it=>{const v=it.id in O?O[it.id]:(it.type==='seed'?'':it.value);const a=`data-p="${esc(it.id)}" data-t="${it.type}"`;
    if(it.type==='choice')return `<select ${a}>${it.choices.map(c=>`<option ${String(c)===String(v)?'selected':''}>${esc(c)}</option>`).join('')}</select>`;
    if(it.presets)return `<select ${a}>${[...new Set([...it.presets,+v])].sort((x,y)=>x-y).map(c=>`<option value="${c}" ${+c===+v?'selected':''}>${c}${c===it.value?' ✓':''}</option>`).join('')}</select>`;
    if(it.type==='bool')return `<input type="checkbox" ${a} ${v?'checked':''}>`;
    if(it.type==='int'||it.type==='float'||it.type==='seed')return `<input type="number" inputmode="decimal" ${a} value="${esc(v)}" ${it.type==='seed'?'placeholder="隨機"':''} ${it.min!=null?`min="${it.min}"`:''} ${it.max!=null?`max="${it.max}"`:''} step="${it.step||(it.type==='int'||it.type==='seed'?1:'any')}">`;
    return `<input ${a} value="${esc(v)}">`};
  // 一格一個參數、能擠就擠：短的一列放好幾個，名字很長的（模型檔名）佔兩格或整列
  const wid=it=>{const L=it.type==='choice'?Math.max(...it.choices.map(c=>String(c).length),0):it.type==='str'?String(it.value||'').length+6:0;return L>26?' wf':L>11?' w2':''};
  const short=t=>String(t).replace(/（[^）]*）/g,'').replace(/\([^)]*\)/g,'').trim()||t;
  const cell=it=>it.type==='bool'?`<label class="pc b" title="${esc(it.label+' · '+(it.node||''))}">${inp(it)}<span data-l="${esc(it.id)}">${esc(short(it.label))}</span></label>`
    :`<div class="pc${wid(it)}" title="${esc(it.label+' · '+(it.node||''))}"><label data-l="${esc(it.id)}">${esc(it.type==='seed'?'種子':short(it.label))}</label>${inp(it)}</div>`;
  const MAIN=GDEF.filter(g=>g.g==='常用'||g.g==='模型／LoRA'),NODE=GDEF.filter(g=>g.g!=='常用'&&g.g!=='模型／LoRA'),nN=NODE.reduce((a,g)=>a+g.items.length,0);
  const det=(k,title,n,inner)=>`<details data-g="${esc(k)}" ${(k in OPEN?OPEN[k]:k==='常用'&&!BIG.some(b=>b[0]===wf)&&!gModeOf(wf))?'open':''}><summary><b>${title}</b> <span class="mu">${n} 項</span></summary>${inner}</details>`;
  box.innerHTML=MAIN.map(g=>det(g.g,(g.g==='常用'?'⚙ ':'🧩 ')+esc(g.g),g.items.length,`<div class="pgrid">${g.items.map(cell).join('')}</div>`)).join('')   // 其他每個節點的設定都收在同一個「🔧 其他節點設定」裡
    +(NODE.length?det('_nodes','🔧 其他節點設定',nN,NODE.map(g=>`<div class="mu" style="font-weight:700;margin:6px 0 1px">${esc(g.g)}</div><div class="pgrid">${g.items.map(cell).join('')}</div>`).join('')):'')
    +`<div class="row" style="margin-top:4px"><span class="grow mu" id="gpc"></span><button class="pill" id="gpr">↺ 還原流程預設</button></div>`;
  $$('#gpar details').forEach(d=>d.ontoggle=()=>{const o=LS.get(GOK,{});o[d.dataset.g]=d.open;LS.set(GOK,o)});
  $$('#gpar [data-p]').forEach(x=>x.onchange=gParSave);$('#gpr').onclick=()=>{LS.set(PK(),{});gParams();toast('已還原成流程本來的設定')};gParMark()}
function gParVal(x){const t=x.dataset.t;if(t==='bool')return x.checked;if(t==='int'||t==='float')return x.value===''?null:+x.value;if(t==='seed')return x.value===''?'':+x.value;return x.value}
function gParSave(){const O={};const D={};GDEF.forEach(g=>g.items.forEach(it=>D[it.id]=it));
  $$('#gpar [data-p]').forEach(x=>{const it=D[x.dataset.p];const v=gParVal(x);if(it&&v!==null&&String(v)!==String(it.type==='seed'?'':it.value))O[x.dataset.p]=v});LS.set(PK(),O);gParMark()}
// V0.1.84 畫質三段：⚡ 快（邊長 ×0.75）／標準（流程本來的）／🔍 精細（×1.33）。改的是流程裡的輸出尺寸參數（GROK 輸出邊長、Qwen 2.1 resolution），跟下面參數同一份
function gQual(){const box=$('#gqual');if(!box)return;let it=null;GDEF.forEach(g=>g.items.forEach(x=>{if(!it&&/\.(scale_to_length|resolution|megapixels)$/.test(x.id)&&(x.type==='int'||x.type==='float'))it=x}));
  if(!it||!+it.value){box.innerHTML='';return}const O=LS.get(PK(),{}),d=+it.value,cur=it.id in O?+O[it.id]:d,mp=/megapixels$/.test(it.id),r64=v=>mp?Math.round(v*100)/100:Math.max(256,Math.round(v/64)*64);   // 影片（H3）改的是百萬像素：小一點快很多
  const L=mp?[[r64(d*.55),'⚡ 快','約一半時間、畫面小一點'],[d,'標準','流程本來的'],[r64(d*1.4),'🔍 精細','比較慢、比較吃記憶體']]:[[r64(d*.75),'⚡ 快','約 0.6 倍時間'],[d,'標準','流程本來的'],[r64(d*1.33),'🔍 精細','約 1.7 倍時間、細節多']];
  box.innerHTML=`<span class="mu">畫質</span>${L.map(([v,n,t])=>`<button class="gpc ${v===cur?'on':''}" data-gq="${v}" title="${t}">${n}<small> ${v}${mp?'MP':''}</small></button>`).join('')}${L.some(x=>x[0]===cur)?'':`<span class="mu">（自訂 ${cur}）</span>`}`;
  box.onclick=e=>{const b=e.target.closest('[data-gq]');if(!b)return;const v=+b.dataset.gq,O=LS.get(PK(),{});if(v===d)delete O[it.id];else O[it.id]=v;LS.set(PK(),O);gParams();toast(v===d?'畫質：標準':`畫質：輸出 ${v}`,1400)}}
// V0.2.38 影片長度快選：3／4／6／8 秒（H3 越長越久、越吃記憶體；先用短的試動作）
function gDur(){const box=$('#gdur');if(!box)return;let it=null;GDEF.forEach(g=>g.items.forEach(x=>{if(!it&&/duration|影片長度/i.test(x.id+' '+x.label)&&!/影片前幾秒/.test(x.label)&&(x.type==='int'||x.type==='float'))it=x}));
  if(!it){box.innerHTML='';return}const O=LS.get(PK(),{}),d=+it.value,cur=it.id in O?+O[it.id]:d;
  box.innerHTML=`<span class="mu">長度</span>${[3,4,6,8,10].map(v=>`<button class="gpc ${v===cur?'on':''}" data-gd="${v}">${v} 秒</button>`).join('')}<span class="mu" style="font-size:11.5px">越長越慢，先用短的試</span>`;
  box.onclick=e=>{const b=e.target.closest('[data-gd]');if(!b)return;const v=+b.dataset.gd,O=LS.get(PK(),{});if(v===d)delete O[it.id];else O[it.id]=v;LS.set(PK(),O);gParams();toast(`影片長度 ${v} 秒`,1200)}}
// V0.2.52 H3 Turbo 步數快選：官方 8 步 Turbo LoRA 也可以只跑 4 步（lightx2v 說明：8 或 4 步都能用），算圖時間大約一半
function gTst(){const box=$('#gtst');if(!box)return;let it=null;GDEF.forEach(g=>g.items.forEach(x=>{if(!it&&/turbo_steps|Turbo 步數/i.test(x.id+' '+x.label)&&x.type==='int')it=x}));
  if(!it){box.innerHTML='';return}const O=LS.get(PK(),{}),d=+it.value,cur=it.id in O?+O[it.id]:d;
  box.innerHTML=`<span class="mu">步數</span>${[[4,'⚡ 4 步','快一倍'],[8,'8 步','標準']].map(([v,n,t])=>`<button class="gpc ${v===cur?'on':''}" data-gt="${v}" title="${t}">${n}</button>`).join('')}<span class="mu" style="font-size:11.5px">4 步快一倍，動作細節少一點</span>`;
  box.onclick=e=>{const b=e.target.closest('[data-gt]');if(!b)return;const v=+b.dataset.gt,O=LS.get(PK(),{});if(v===d)delete O[it.id];else O[it.id]=v;LS.set(PK(),O);gParams();toast(`Turbo ${v} 步`,1200)}}
// V0.2.59 改動幅度（重繪強度）：輕輕修（0.6，保留更多原圖）／中（0.8）／完全照提示詞改（1.0）
function gDen(){const box=$('#gden');if(!box)return;let it=null;GDEF.forEach(g=>g.items.forEach(x=>{if(!it&&/\.denoise$/.test(x.id)&&x.type==='float')it=x}));const w=gWf();
  if(!it||/H3|影片/.test(w.name)||(w.n_img||0)>1){box.innerHTML='';return}const O=LS.get(PK(),{}),d=+it.value,cur=it.id in O?+O[it.id]:d;
  box.innerHTML=`<span class="mu">改動幅度</span>${[[0.6,'🪶 輕輕修'],[0.8,'中'],[1,'完全照提示詞']].map(([v,n])=>`<button class="gpc ${Math.abs(v-cur)<0.01?'on':''}" data-gn="${v}">${n}</button>`).join('')}`;
  box.onclick=e=>{const b=e.target.closest('[data-gn]');if(!b)return;const v=+b.dataset.gn,O=LS.get(PK(),{});if(Math.abs(v-d)<0.001)delete O[it.id];else O[it.id]=v;LS.set(PK(),O);gParams();toast(v<1?`改動幅度 ${v}：保留比較多原圖（美顏、調色、小修適合）`:'完全照提示詞改',2200)}}
function gParMark(){gQual();gDur();gTst();gDen();const O=LS.get(PK(),{});$$('#gpar [data-l]').forEach(e=>e.style.color=e.dataset.l in O?'var(--accent)':'');const n=Object.keys(O).length;$('#gpc').textContent=n?`改了 ${n} 項（紫色）`:'都是流程本來的設定'}
async function shrink(file){const mp=+GMP||0;let bmp;
  try{bmp=await createImageBitmap(file,{imageOrientation:'from-image'})}catch(e){bmp=await new Promise((ok,no)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=no;i.src=URL.createObjectURL(file)})}
  const w=bmp.width,h=bmp.height,k=mp>0?Math.min(1,Math.sqrt(mp*1e6/(w*h))):1;
  if(k>=1&&/jpe?g|png|webp/i.test(file.type))return file;
  const c=document.createElement('canvas');c.width=Math.max(8,Math.round(w*k));c.height=Math.max(8,Math.round(h*k));c.getContext('2d').drawImage(bmp,0,0,c.width,c.height);
  return await new Promise(ok=>c.toBlob(ok,'image/jpeg',0.92))}
// ---- ⬇ 這個流程缺哪些模型（問 ComfyUI 有沒有這個檔名，不翻你的資料夾）；可以一鍵下載到 ComfyUI 的模型資料夾
let GMT=null;
async function gModels(){const box=$('#gmod');if(!box)return;const wf=$('#gw').value;clearTimeout(GMT);let r;try{r=await api(U('/api/models',{wf}))}catch(e){return}
  if(!r.ok||$('#gw').value!==wf){box.innerHTML='';return}const M=r.items||[],miss=M.filter(m=>!m.ok),run=M.some(m=>m.dl&&(m.dl.state==='run'||m.dl.state==='wait'));
  if(!miss.length){box.innerHTML='';return}
  const can=miss.filter(m=>m.known&&!(m.dl&&(m.dl.state==='run'||m.dl.state==='wait'))),gb=can.reduce((a,m)=>a+(m.size||0),0);
  box.innerHTML=`<div class="bgsC"><div class="bgsCH"><b>⚠ 這個流程還缺 ${miss.length} 個模型</b></div>${miss.map(m=>{const d=m.dl||{};const p=d.size?Math.min(100,(d.got||0)/d.size*100):0;
    return `<div class="bgsI ${d.state==='run'?'run':''}"><i>${d.state==='done'?'✔':d.state==='run'?'⬇':d.state==='fail'?'✖':'·'}</i><div class="bgsT"><b>${esc(m.file)}</b><small>${esc(m.folder)}${m.size?' · '+fmtB(m.size):''}${d.msg?' · '+esc(d.msg):''}${m.known?'':' · 不知道去哪下載，請自己放進 ComfyUI'}</small>${d.state==='run'?`<u><s style="width:${p}%"></s></u>`:''}</div>${d.state==='run'?`<button data-mc="${esc(m.file)}">停</button>`:''}</div>`}).join('')}
    ${can.length?`<button class="pill acc" id="gmdl" style="margin-top:6px">⬇ 下載缺的模型（約 ${fmtB(gb)}，下載到 ComfyUI 的模型資料夾）</button>`:''}<div class="mu" style="margin-top:4px">下載在電腦上跑，手機可以關掉；中斷了再按會接著下載。進度也在「🖥 背景」。</div></div>`;
  const b=$('#gmdl');if(b)b.onclick=async()=>{const x=await api('/api/models',{a:'dl',files:can.map(m=>m.file)});toast(x.message||'失敗');gModels()};
  $$('[data-mc]',box).forEach(x=>x.onclick=async()=>{await api('/api/models',{a:'cancel',file:x.dataset.mc});gModels()});
  if(run)GMT=setTimeout(()=>{if(CUR==='gen')gModels()},3000)}
function gOne(name){GIMGS=name?[name]:[];GFILES=[];LS.set('gimgs',GIMGS)}
// ---- 好幾格照片（例如「兩張圖合併」：圖一＝場景、圖二＝人物）。第一格就是原本的照片格，其他格加在旁邊；每格都可以多選（每種組合各跑一次）
function gSlots(w){const box=$('#gpicks');if(!box)return;const n=w.n_img||0,T=w.slots||[];$$('.drop.sx',box).forEach(x=>x.remove());box.classList.toggle('multi',n>1);
  const hv=(w.kinds||[]).includes('video');
  $('#gp').placeholder=hv?'描述主角長相＋背景（不要寫動作，動作照影片）。例如：Character appearance description: 一隻白色小型貴賓狗，捲毛、黑眼睛。Background description: 明亮的現代廚房':(w.cr||{}).placeholder||(n>1?'例如：讓圖1的人穿上圖2的衣服':'想怎麼改？例如：把衣服換成紅色連身裙');
  for(let i=1;i<n;i++){const d=document.createElement('div');d.className='drop sx';d.dataset.i=i;box.appendChild(d);const vk=(w.kinds||[])[i]==='video';
    const f=document.createElement('input');f.type='file';f.accept=vk?'video/*':'image/*';f.multiple=true;f.style.display='none';d.after(f);d.onclick=()=>f.click();
    f.onchange=()=>{const F=[...f.files];if(F.length){GSF[i]=F;gPrevSlot(i)}};gPrevSlot(i)}gPrev()}
function gPrevSlot(i){const d=$(`#gpicks .drop.sx[data-i="${i}"]`);if(!d)return;const w=gWf(),t=(w.slots||[])[i]||('圖'+(i+1));const F=GSF[i]||[],I=GSI[i]||[];
  const src=F.length?F.map(f=>URL.createObjectURL(f)):I.map(n=>ISV(n)?IMGU('inputs/'+n):IMGT('inputs/'+n));const vk=(w.kinds||[])[i]==='video';
  d.innerHTML=`<div class="slt">${esc(t)}</div>`+(src.length?(vk?`<video src="${src[0]}#t=0.5" muted playsinline preload="metadata" style="max-width:100%;max-height:22vh;border-radius:8px;display:block;margin:0 auto"></video>`:`<img src="${src[0]}">`)+(src.length>1?`<div class="mu">共 ${src.length} 個</div>`:'<div class="mu">點一下換</div>'):`<div style="padding:16px 0">${vk?'🎬 點這裡選影片':'📷 點這裡選'}${/首尾幀/.test(w.name)&&i===1?'<div class="mu" style="font-size:11.5px;margin-top:6px">不選也可以：按開始會先用改圖做出結束畫面</div>':''}${/合併/.test(w.name)?'<div class="mu" style="font-size:11.5px;margin-top:6px">可以一次選好幾張（例如好幾件衣服），每張各做一次</div>':''}</div>`);
  const v=d.querySelector('video');if(v)v.onloadedmetadata=()=>{const m=d.querySelector('.mu');if(m&&v.duration)m.textContent=`影片 ${Math.round(v.duration)} 秒 · 點一下換`}}
// 已選照片：GIMGS＝已經上傳過的（之前選的、再跑一次帶回來的），GFILES＝這次新選、還沒上傳的；顯示時接在一起，新選的接在後面（不會換掉舊的），每張右上角 ✕ 拿掉
function gSrcList(){return GIMGS.map(n=>({u:IMGU('inputs/'+n),t:IMGT('inputs/'+n),tag:(/_f(\d{4,})\.\w+$/.exec(n)||[])[1]})).concat(GFILES.map(f=>({u:f._u||(f._u=URL.createObjectURL(f)),tag:f._tag&&f._tag.slice(1)})))}
// V0.2.22 選好照片就先在背景上傳到電腦（切去別的 App、頁面重新載入，選好的照片還在；按開始也比較快）
function gBgUp(f){if(f._p||!f||!(f instanceof Blob))return;f._p=(async()=>{const blob=await shrink(f);const r=await api(f._tag?U('/api/gen_upload',{tag:f._tag}):'/api/gen_upload',await blob.arrayBuffer(),true);if(!r.ok)throw new Error(r.message||'');return r.img})();
  f._p.then(nm=>{if(f._taken)return;const i=GFILES.indexOf(f);if(i<0)return;GFILES.splice(i,1);GIMGS.push(nm);LS.set('gimgs',GIMGS);if(GMASK.has(f)){const b=GMASK.get(f);GMASK.delete(f);GMASK.set(nm,b);gMaskSave(nm,b)}if(CUR==='gen')gPrev()}).catch(()=>{f._p=null})}
function gAddFiles(F){if(!F.length)return;GFILES=GFILES.concat(F);F.forEach(gBgUp);gPrev();const n=GIMGS.length+GFILES.length;if(n>F.length)toast(`✔ 加了 ${F.length} 張，現在共 ${n} 張（✕ 可以拿掉）`,2500)}
function gDel(k){GMASK.delete(gKey(k));{const M=LS.get('gmask',{});delete M[gKey(k)];LS.set('gmask',M)}if(k<GIMGS.length){GIMGS.splice(k,1);LS.set('gimgs',GIMGS)}else GFILES.splice(k-GIMGS.length,1);gPrev()}
function gPrev(){const d=$('#gpick');if(!d)return;setTimeout(gMlInfo,0);const L=gSrcList(),n=L.length;
  const w=gWf();if((w.n_img||0)>1){const t=(w.slots||[])[0]||'圖一';d.innerHTML=`<div class="slt">${esc(t)}</div>`+(n?`<img src="${L[0].t||L[0].u}">${n>1?`<div class="mu">共 ${n} 張</div>`:'<div class="mu">點一下換</div>'}${/^兩張圖合併/.test(w.name)&&n===1?`<button class="pill ${GMASK.has(gKey(0))?'acc':''}" data-gmask="0" style="margin-top:6px">🖌 ${GMASK.has(gKey(0))?'局部 ✔':'只改圖一的哪裡'}</button>`:''}`:'<div style="padding:16px 0">📷 點這裡選</div>');return}
  const cnt=$('#gcnt');if(cnt)cnt.textContent=n?`${n} 張`:'';
  if(!n){d.innerHTML=`<div class="gempty" data-gadd="1"><div class="ic">📷</div><b>點這裡選照片</b><span class="mu">相簿或拍照，可以一次選很多張</span></div>`;return}
  d.innerHTML=`<div class="gtiles${n===1?' one':''}">${L.map((x,k)=>`<div class="gtile"><img src="${x.t||x.u}" onerror="this.style.opacity=.3">${n>1?`<span class="gi">${k+1}</span>`:''}${x.tag?`<span class="ftag">🎞 ${+x.tag}</span>`:''}<button class="gx" data-gdel="${k}" title="拿掉">✕</button><button class="gcr" data-gcrop="${k}" title="裁切／轉向">✂ 裁切</button><button class="gcr gmk ${GMASK.has(gKey(k))?'on':''}" ${/H3|影片/.test(($('#gw')||{}).value||'')?'style="display:none"':''} data-gmask="${k}" title="只改塗到的地方">🖌 ${GMASK.has(gKey(k))?'局部 ✔':'局部'}</button></div>`).join('')}<div class="gtile gadd" data-gadd="1">＋<small>加照片</small></div></div>
   <div class="gfoot">${n>1?`<span class="gbadge">📚 批量 ${n} 張</span><span class="mu">每張用同一段提示詞各跑一次</span>`:'<span class="mu">1 張照片</span>'}${n===1&&LS.get('gimg_prev','')&&LS.get('gimg_prev','')!==GIMGS[0]?`<button class="gclr" data-gback="1" style="border-color:var(--accent);color:var(--accent)">↩ 換回上一張</button>`:''}<button class="gclr" data-gclr="1">清空</button></div>`}
// V0.1.85 ✂ 裁切／轉向：上傳前先把照片裁成想要的範圍（只改這次要用的，不動原本的檔案）。拖框移動、拖右下角改大小，比例可選
let CR=null;
async function crOpen(k,ar){const L=gSrcList(),x=L[k];if(!x)return;const im=new Image();im.onload=()=>{CR={k,im,rot:0,ar:ar||0,r:null};crUI()};im.onerror=()=>toast('讀不到這張');im.src=x.u}
function crSrc(){const {im,rot}=CR,c=document.createElement('canvas'),sw=rot%180?im.naturalHeight:im.naturalWidth,sh=rot%180?im.naturalWidth:im.naturalHeight;c.width=sw;c.height=sh;const g=c.getContext('2d');g.translate(sw/2,sh/2);if(CR.flip)g.scale(-1,1);g.rotate(rot*Math.PI/180);g.drawImage(im,-im.naturalWidth/2,-im.naturalHeight/2);return c}
function crUI(){let o=$('#crp');if(!o){o=document.createElement('div');o.id='crp';document.body.appendChild(o)}
  const ARS=[[0,'自由'],[1,'1:1'],[3/4,'3:4'],[4/3,'4:3'],[9/16,'9:16'],[16/9,'16:9']];
  o.innerHTML=`<div class="crtop"><b>✂ 裁切／轉向</b><span class="grow"></span><button class="pill" id="crx">取消</button><button class="pill acc" id="crok">✔ 用這個範圍</button></div>
   <div class="crwrap" id="crw"><canvas id="crc"></canvas><div id="crr"><i class="crh"></i></div></div>
   <div class="crbar">${ARS.map(([v,n])=>`<button class="gpc ${CR.ar===v?'on':''}" data-ar="${v}">${n}</button>`).join('')}<button class="gpc" id="crrot">↻ 轉 90°</button><button class="gpc ${CR.flip?'on':''}" id="crflip">⇋ 左右翻</button><button class="gpc" id="crall">整張</button>${CR.ar&&gSrcList().length>1?`<button class="gpc" id="crbat" style="border-color:var(--accent)">📐 全部 ${gSrcList().length} 張都裁成 ${({1:'1:1',0.75:'3:4',1.3333333333333333:'4:3',0.5625:'9:16',1.7777777777777777:'16:9'})[CR.ar]||'這個比例'}（置中）</button>`:''}</div>
   <div class="crbar"><span class="mu" style="color:#ccc">↔ 擴圖（往外補畫面）</span>${[[1,'1:1'],[4/5,'4:5'],[9/16,'9:16'],[16/9,'16:9'],[1.5,'加寬 1.5 倍']].map(([v,n])=>`<button class="gpc" data-ox="${v}" data-on="${n}">${n}</button>`).join('')}<button class="gpc" id="cromany" style="border-color:var(--accent)">📐 社群三種一次做</button></div>`;
  CR.src=crSrc();const cv=$('#crc'),W=Math.min(innerWidth-24,900),H=innerHeight-170,k=Math.min(W/CR.src.width,H/CR.src.height);CR.k2=k;
  cv.width=Math.round(CR.src.width*k);cv.height=Math.round(CR.src.height*k);cv.getContext('2d').drawImage(CR.src,0,0,cv.width,cv.height);$('#crw').style.width=cv.width+'px';$('#crw').style.height=cv.height+'px';
  if(!CR.r)CR.r={x:0,y:0,w:cv.width,h:cv.height};crFit();crDraw();
  $('#crx').onclick=()=>{o.remove();CR=null};$('#crok').onclick=crDone;
  const cb=$('#crbat');if(cb)cb.onclick=()=>crBatch(CR.ar);$('#crrot').onclick=()=>{CR.rot=(CR.rot+90)%360;CR.r=null;crUI()};$('#crflip').onclick=()=>{CR.flip=!CR.flip;crUI()};$('#crall').onclick=()=>{CR.ar=0;CR.r=null;crUI()};
  $$('[data-ar]',o).forEach(b=>b.onclick=()=>{CR.ar=+b.dataset.ar;CR.r=null;crUI()});$$('[data-ox]',o).forEach(b=>b.onclick=()=>crOut(+b.dataset.ox,b.dataset.on));$('#cromany').onclick=crOutMany;
  const rr=$('#crr');let st=null;
  rr.onpointerdown=e=>{e.preventDefault();rr.setPointerCapture(e.pointerId);st={x:e.clientX,y:e.clientY,r:{...CR.r},h:e.target.classList.contains('crh')}};
  rr.onpointermove=e=>{if(!st)return;const dx=e.clientX-st.x,dy=e.clientY-st.y,cw=cv.width,ch=cv.height,r=CR.r;
    if(st.h){let w=Math.max(40,Math.min(cw-st.r.x,st.r.w+dx)),h=Math.max(40,Math.min(ch-st.r.y,st.r.h+dy));if(CR.ar){h=w/CR.ar;if(st.r.y+h>ch){h=ch-st.r.y;w=h*CR.ar}}r.w=w;r.h=h}
    else{r.x=Math.max(0,Math.min(cw-r.w,st.r.x+dx));r.y=Math.max(0,Math.min(ch-r.h,st.r.y+dy))}crDraw()};
  rr.onpointerup=rr.onpointercancel=()=>{st=null}}
function crFit(){const cv=$('#crc'),r=CR.r;if(!CR.ar)return;let w=cv.width,h=w/CR.ar;if(h>cv.height){h=cv.height;w=h*CR.ar}w*=.9;h*=.9;r.w=w;r.h=h;r.x=(cv.width-w)/2;r.y=(cv.height-h)/2}
function crDraw(){const r=CR.r,e=$('#crr');Object.assign(e.style,{left:r.x+'px',top:r.y+'px',width:r.w+'px',height:r.h+'px'});
  e.dataset.sz=`${Math.round(r.w/CR.k2)}×${Math.round(r.h/CR.k2)}`}
// V0.1.91 ↔ 擴圖：畫布放大到指定比例，原圖放中間，四周先用模糊的原圖墊底，再自動塗好「🖌 局部」＝新長出來的地方（原圖範圍保證不變）
// V0.3.09 批量照片一次裁成同一個比例（置中），合併／影片批量時大小一致
async function crBatch(ar){const L=gSrcList(),out=[];toast(`裁切 ${L.length} 張中…`,20000);
  for(const x of L){const im=await new Promise((ok,no)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=no;i.src=x.u}).catch(()=>null);if(!im)continue;const w=im.naturalWidth,h=im.naturalHeight;let cw=w,ch=h;if(w/h>ar)cw=Math.round(h*ar);else ch=Math.round(w/ar);
    const c=document.createElement('canvas');c.width=cw;c.height=ch;c.getContext('2d').drawImage(im,(w-cw)/2,(h-ch)/2,cw,ch,0,0,cw,ch);const b=await new Promise(ok=>c.toBlob(ok,'image/jpeg',0.93));out.push(new File([b],'crop.jpg',{type:'image/jpeg'}))}
  GMASK.clear();GIMGS=[];LS.set('gimgs',[]);GFILES=out;out.forEach(gBgUp);$('#crp').remove();CR=null;gPrev();toast(`✔ ${out.length} 張都裁好了`,2500)}
// V0.2.83 📐 一次做社群三種比例（1:1、4:5、9:16）：同一張各擴一份，一起排
function crCanvas(S,ar){const w=S.width,h=S.height;let W=w,H=h;if(w/h<ar)W=Math.round(h*ar);else if(w/h>ar)H=Math.round(w/ar);else{W=Math.round(w*1.25);H=Math.round(h*1.25)}
  const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.filter='blur(40px)';g.drawImage(S,-W*.05,-H*.05,W*1.1,H*1.1);g.filter='none';const ox=Math.round((W-w)/2),oy=Math.round((H-h)/2);g.drawImage(S,ox,oy);
  const m=document.createElement('canvas');m.width=W;m.height=H;const q=m.getContext('2d');q.fillStyle='#fff';q.fillRect(0,0,W,H);const pad=Math.round(Math.min(w,h)*.02);q.fillStyle='#000';q.fillRect(ox+pad,oy+pad,w-2*pad,h-2*pad);
  return Promise.all([new Promise(ok=>c.toBlob(ok,'image/jpeg',0.93)),new Promise(ok=>m.toBlob(ok,'image/png'))])}
async function crOutMany(){const S=CR.src,i=CR.k,L=[[1,'1:1'],[4/5,'4:5'],[9/16,'9:16']];const F=[];
  for(const [ar,n] of L){const [b,mb]=await crCanvas(S,ar);const f=new File([b],`outpaint_${n.replace(':','x')}.jpg`,{type:'image/jpeg'});GMASK.set(f,mb);F.push(f)}
  GMASK.delete(gKey(i));if(i<GIMGS.length){GIMGS.splice(i,1);LS.set('gimgs',GIMGS)}else GFILES.splice(i-GIMGS.length,1);GFILES=GFILES.concat(F);F.forEach(gBgUp);
  $('#crp').remove();CR=null;gPrev();const t=$('#gp');if(t&&!t.value.trim()){t.value='把畫面往外延伸，四周補上自然連貫的背景和內容，光線和風格跟原圖一致';LS.set('gprompt',t.value)}
  toast('📐 做好三種比例（1:1、4:5、9:16），按開始三張一起補畫面',4000)}
function crOut(ar,name){const S=CR.src,w=S.width,h=S.height;let W=w,H=h;
  if(name.startsWith('加寬')){W=Math.round(w*1.5)}else if(w/h<ar)W=Math.round(h*ar);else if(w/h>ar)H=Math.round(w/ar);else{W=Math.round(w*1.25);H=Math.round(h*1.25)}
  const c=document.createElement('canvas');c.width=W;c.height=H;const g=c.getContext('2d');g.filter='blur(40px)';g.drawImage(S,-W*.05,-H*.05,W*1.1,H*1.1);g.filter='none';const ox=Math.round((W-w)/2),oy=Math.round((H-h)/2);g.drawImage(S,ox,oy);
  const m=document.createElement('canvas');m.width=W;m.height=H;const q=m.getContext('2d');q.fillStyle='#fff';q.fillRect(0,0,W,H);const pad=Math.round(Math.min(w,h)*.02);q.fillStyle='#000';q.fillRect(ox+pad,oy+pad,w-2*pad,h-2*pad);
  c.toBlob(b=>{const f=new File([b],'outpaint.jpg',{type:'image/jpeg'}),i=CR.k;GMASK.delete(gKey(i));if(i<GIMGS.length){GIMGS.splice(i,1);LS.set('gimgs',GIMGS);GFILES.unshift(f)}else GFILES[i-GIMGS.length]=f;
    m.toBlob(mb=>{GMASK.set(f,mb);$('#crp').remove();CR=null;gBgUp(f);gPrev();const t=$('#gp');if(t&&!t.value.trim()){t.value='把畫面往外延伸，四周補上自然連貫的背景和內容，光線和風格跟原圖一致';LS.set('gprompt',t.value)}
      toast(`✔ 擴成 ${W}×${H}：四周新的地方會自動補畫面，原圖不變（已自動「🖌 局部」）`,4000)},'image/png')},'image/jpeg',0.93)}
function crDone(){const r=CR.r,k=CR.k2,c=document.createElement('canvas');c.width=Math.round(r.w/k);c.height=Math.round(r.h/k);
  c.getContext('2d').drawImage(CR.src,r.x/k,r.y/k,c.width,c.height,0,0,c.width,c.height);
  GMASK.delete(gKey(CR.k));c.toBlob(b=>{const f=new File([b],'crop.jpg',{type:'image/jpeg'}),i=CR.k;if(i<GIMGS.length){GIMGS.splice(i,1);LS.set('gimgs',GIMGS);GFILES.unshift(f)}else GFILES[i-GIMGS.length]=f;
    $('#crp').remove();CR=null;gBgUp(f);gPrev();toast(`✔ 裁好了（${c.width}×${c.height}），按開始會用裁過的`,2500)},'image/jpeg',0.93)}
// V0.1.90 🖌 只改塗到的地方：在照片上塗要改的範圍（紅色），模型照樣改整張，但最後只把塗到的地方貼回原圖，其他地方一個像素都不動
const GMASK=new Map();{const _d=GMASK.delete.bind(GMASK);GMASK.delete=k=>{if(typeof k==='string'){const M=LS.get('gmask',{});if(k in M){delete M[k];LS.set('gmask',M)}}return _d(k)}}
// V0.2.21 手機切到別的 App 再回來，瀏覽器常常會重新載入頁面：已上傳過的照片的遮罩先存到電腦上，回來還在
async function gMaskSave(key,b){if(typeof key!=='string')return;try{const r=await api('/api/gen_upload',await b.arrayBuffer(),true);if(r.ok){b._srv=r.img;const M=LS.get('gmask',{});M[key]=[r.img,!!b._inv];LS.set('gmask',M)}}catch(e){}}
function gMaskLoad(){const M=LS.get('gmask',{}),keep={};Object.entries(M).forEach(([k,[srv,inv]])=>{if(!GIMGS.includes(k))return;keep[k]=[srv,inv];if(GMASK.has(k))return;
  fetch(IMGU('inputs/'+srv)).then(r=>r.ok?r.blob():null).then(b=>{if(!b)return;b._srv=srv;b._inv=inv;GMASK.set(k,b);gPrev()}).catch(()=>{})});LS.set('gmask',keep)}const gKey=k=>k<GIMGS.length?GIMGS[k]:GFILES[k-GIMGS.length];let MK=null;
async function mkOpen(k){const x=gSrcList()[k];if(!x)return;const im=new Image();im.onload=async()=>{MK={k,im,sz:LS.get('mk_sz',40),er:false,hist:[]};
    const old=GMASK.get(gKey(k));MK.inv=!!(old&&old._inv);if(old)try{const bm=await createImageBitmap(old),c=document.createElement('canvas');c.width=bm.width;c.height=bm.height;const g=c.getContext('2d');g.drawImage(bm,0,0);const d=g.getImageData(0,0,c.width,c.height),a=d.data;
      for(let i=0;i<a.length;i+=4){const v=MK.inv?255-a[i]:a[i];a[i]=255;a[i+1]=45;a[i+2]=85;a[i+3]=v}g.putImageData(d,0,0);MK.prev=c}catch(e){}
    mkUI()};im.onerror=()=>toast('讀不到這張');im.src=x.u}
function mkUI(){let o=$('#crp');if(!o){o=document.createElement('div');o.id='crp';document.body.appendChild(o)}
  o.innerHTML=`<div class="crtop"><b id="mkt">${MK.inv?'🖌 塗要保留的地方':'🖌 塗要改的地方'}</b><span class="grow"></span><button class="pill" id="mkx">取消</button><button class="pill acc" id="mkok">✔ 好了</button></div>
   <div class="crsc" id="crsc"><div class="crwrap" id="crw"><canvas id="crc" style="width:100%;height:100%"></canvas><canvas id="mkc" style="position:absolute;left:0;top:0;width:100%;height:100%;opacity:.55;touch-action:none"></canvas></div></div>
   <div class="crbar"><button class="gpc" id="mkz" title="放大看細節（再按換倍數）">🔍 ${MK.z||1}×</button><button class="gpc ${MK.pan?'on':''}" id="mkpan" title="放大後用手指移動畫面（這時候不會塗）">✋ 移動</button><span class="mu" style="color:#ccc">筆刷</span><input type="range" id="mksz" min="8" max="140" value="${MK.sz}" style="width:110px"><span class="mu" style="color:#ccc">邊緣柔和</span><input type="range" id="mkft" min="0" max="40" value="${LS.get('mk_ft',8)}" style="width:80px" title="越大邊緣越自然、越看不出接縫"><button class="gpc ${MK.rect?'on':''}" id="mkrc">▭ 拉框</button><button class="gpc" id="mker">🧽 橡皮擦</button><button class="gpc" id="mkun">↶ 復原</button><button class="gpc" id="mkcl">清掉</button><button class="gpc ${MK.inv?'on':''}" id="mkinv">🔁 反過來：塗的保留</button>${GMASK.has(gKey(MK.k))?'<button class="gpc" id="mkoff">✕ 不用局部</button>':''}</div>
   <div class="mu" style="color:#bbb;text-align:center;max-width:560px">塗要改的範圍（多塗一點邊沒關係）。提示詞照常寫「換成紅色洋裝」這樣就好；塗到以外的地方會保持原圖。</div>`;
  const im=MK.im,cv=$('#crc'),mc=$('#mkc'),W=Math.min(innerWidth-24,900),H=innerHeight-200,k=Math.min(W/im.naturalWidth,H/im.naturalHeight);MK.k2=k;
  cv.width=mc.width=Math.round(im.naturalWidth*k);cv.height=mc.height=Math.round(im.naturalHeight*k);cv.getContext('2d').drawImage(im,0,0,cv.width,cv.height);$('#crw').style.width=cv.width+'px';$('#crw').style.height=cv.height+'px';
  const g=mc.getContext('2d');if(MK.prev)g.drawImage(MK.prev,0,0,mc.width,mc.height);
  const snap=()=>{MK.hist.push(g.getImageData(0,0,mc.width,mc.height));if(MK.hist.length>20)MK.hist.shift()};
  let last=null;const pos=e=>{const r=mc.getBoundingClientRect();return [(e.clientX-r.left)*mc.width/r.width,(e.clientY-r.top)*mc.height/r.height]};   // V0.2.76 放大後座標要換算
  const zf=()=>{const z=MK.z||1;$('#crw').style.width=cv.width*z+'px';$('#crw').style.height=cv.height*z+'px';mc.style.touchAction=MK.pan?'auto':'none';$('#crw').style.touchAction=MK.pan?'auto':'none'};zf();
  $('#mkz').onclick=()=>{MK.z=({1:2,2:3,3:1})[MK.z||1];$('#mkz').textContent=`🔍 ${MK.z}×`;zf();if(MK.z>1&&!MK.pan)toast('放大了：按「✋ 移動」可以拖動畫面，再按一次回到塗抹',3000)};
  $('#mkpan').onclick=()=>{MK.pan=!MK.pan;$('#mkpan').classList.toggle('on',MK.pan);zf()};
  const line=(a,b)=>{g.globalCompositeOperation=MK.er?'destination-out':'source-over';g.strokeStyle='#ff2d55';g.lineWidth=MK.sz;g.lineCap=g.lineJoin='round';g.beginPath();g.moveTo(a[0],a[1]);g.lineTo(b[0],b[1]);g.stroke()};
  let r0=null,base=null;   // V0.2.19 ▭ 拉框：拖一個方框＝整塊塗滿（大範圍一下就好）
  mc.onpointerdown=e=>{if(MK.pan)return;e.preventDefault();mc.setPointerCapture(e.pointerId);snap();last=pos(e);if(MK.rect){r0=last;base=g.getImageData(0,0,mc.width,mc.height)}else line(last,last)};
  mc.onpointermove=e=>{if(!last)return;const p=pos(e);if(MK.rect&&r0){g.putImageData(base,0,0);g.globalCompositeOperation=MK.er?'destination-out':'source-over';g.fillStyle='#ff2d55';g.fillRect(Math.min(r0[0],p[0]),Math.min(r0[1],p[1]),Math.abs(p[0]-r0[0]),Math.abs(p[1]-r0[1]));return}line(last,p);last=p};
  mc.onpointerup=mc.onpointercancel=()=>{last=null;r0=null;base=null};
  $('#mkrc').onclick=()=>{MK.rect=!MK.rect;$('#mkrc').classList.toggle('on',MK.rect);toast(MK.rect?'▭ 拉框：拖一個方框整塊塗滿':'🖌 回到筆刷',1500)};
  $('#mksz').oninput=e=>{MK.sz=+e.target.value;LS.set('mk_sz',MK.sz);let d=$('#mkdot');if(!d){d=document.createElement('div');d.id='mkdot';$('#crw').appendChild(d)}
    Object.assign(d.style,{width:MK.sz+'px',height:MK.sz+'px',left:(mc.width-MK.sz)/2+'px',top:(mc.height-MK.sz)/2+'px'});clearTimeout(MK.dt);MK.dt=setTimeout(()=>d.remove(),700)};   // 拉筆刷大小時中間顯示一個圓（實際大小）
  $('#mker').onclick=()=>{MK.er=!MK.er;$('#mker').classList.toggle('on',MK.er)};
  $('#mkun').onclick=()=>{const d=MK.hist.pop();if(d)g.putImageData(d,0,0)};$('#mkcl').onclick=()=>{snap();g.clearRect(0,0,mc.width,mc.height)};
  const off=$('#mkoff');if(off)off.onclick=()=>{GMASK.delete(gKey(MK.k));o.remove();MK=null;gPrev();toast('不用局部了：整張照常改')};
  $('#mkx').onclick=()=>{o.remove();MK=null};
  $('#mkinv').onclick=()=>{MK.inv=!MK.inv;$('#mkinv').classList.toggle('on',MK.inv);$('#mkt').textContent=MK.inv?'🖌 塗要保留的地方':'🖌 塗要改的地方';toast(MK.inv?'塗到的地方保持原樣，其他地方照提示詞改（例如塗人物、換背景）':'塗到的地方照提示詞改，其他保持原樣',3000)};
  $('#mkok').onclick=()=>{const a=g.getImageData(0,0,mc.width,mc.height).data;let n=0;for(let i=3;i<a.length;i+=4)if(a[i]>20)n++;
    if(!n){GMASK.delete(gKey(MK.k));o.remove();MK=null;gPrev();return toast('沒有塗：整張照常改')}
    const out=document.createElement('canvas');out.width=im.naturalWidth;out.height=im.naturalHeight;const x=out.getContext('2d');x.fillStyle='#000';x.fillRect(0,0,out.width,out.height);
    const tmp=document.createElement('canvas');tmp.width=mc.width;tmp.height=mc.height;const t=tmp.getContext('2d');t.drawImage(mc,0,0);t.globalCompositeOperation='source-in';t.fillStyle='#fff';t.fillRect(0,0,tmp.width,tmp.height);
    const ft=+($('#mkft')||{}).value||0;LS.set('mk_ft',ft);if(ft)x.filter=`blur(${Math.round(ft/MK.k2)}px)`;x.drawImage(tmp,0,0,out.width,out.height);x.filter='none';if(MK.inv){x.globalCompositeOperation='difference';x.fillStyle='#fff';x.fillRect(0,0,out.width,out.height)}const key=gKey(MK.k);
    const inv=!!MK.inv;out.toBlob(b=>{b._inv=inv;GMASK.set(key,b);gMaskSave(key,b);o.remove();MK=null;gPrev();toast(`✔ 塗了 ${Math.round(n/(mc.width*mc.height)*100)}% 的範圍：只改這裡`,2500)},'image/png')}}
// ---- 常用提示詞：⭐ 存起來的＋最近常用的，點一下填進去
// V0.1.80 🪄 常用改法：分類點開，點一句就填進去（框裡已經有字就接在後面）；「🔒 保持臉不變」勾了會自動加在句尾
const GTPL=[['👗 衣服',['把衣服換成黑色西裝外套','換成白色連身裙','換成牛仔外套和白T恤','換成和服','換成運動服']],
 ['🏞 背景',['把背景換成海邊夕陽','背景換成東京街頭夜景','背景換成純白攝影棚','背景換成咖啡廳','把背景模糊（淺景深）']],
 ['💇 髮型妝容',['頭髮換成金色長捲髮','換成短髮','加上淡妝','換成紅色口紅']],
 ['💡 光線',['改成黃金時段的溫暖光線','改成柔和的攝影棚打光','改成電影感冷色調','改成晚上，有霓虹燈光']],
 ['🧹 修圖',['去掉背景裡的路人','去掉照片上的文字和浮水印','修復老照片：去掉刮痕、補上顏色','讓照片更清楚、細節更多','皮膚自然一點，去掉痘痘']],
 ['🎨 風格',['變成吉卜力動畫風格','變成3D皮克斯風格','變成水彩畫','變成鉛筆素描','變成寫實電影劇照']],
 ['🧍 姿勢表情',['讓她微笑','讓他雙手交叉站著','改成側身看鏡頭','改成坐在椅子上']],
 ['🎥 換角度',['鏡頭往左轉 45 度，從側前方拍','改成從正上方往下俯拍','改成低角度仰拍','鏡頭拉遠，拍到全身','鏡頭拉近，只拍上半身特寫']],
 ['📎 參考圖',['把衣服換成參考圖裡的衣服','把參考圖裡的商品放到她手上','背景換成參考圖裡的地方','照參考圖的畫風重畫','髮型換成參考圖裡的髮型']],
 ['🛍 商品',['把商品放在白色背景上，乾淨的電商主圖','商品放在木桌上，旁邊有植物，自然光','加上柔和的倒影和陰影','換成黑色款']]];
const GKEEP='，保持人物的臉、五官和身材完全不變';
function gTpl(){const box=$('#gtpl');if(!box)return;const open=LS.get('gtpl_o','');const keep=LS.get('gkeep',false);
  box.innerHTML=`<div class="gtcat"><span class="mu">🪄 常用改法</span>${GTPL.map(([c])=>`<button class="gpc ${open===c?'on':''}" data-tc="${esc(c)}">${c}</button>`).join('')}<label class="gpc kp ${keep?'on':''}"><input type="checkbox" id="gkeep" ${keep?'checked':''}>🔒 保持臉不變</label></div>`
   +(open?`<div class="gtlist">${(GTPL.find(x=>x[0]===open)||[0,[]])[1].map(t=>`<button class="gpc" data-tt="${esc(t)}">${esc(t)}</button>`).join('')}<button class="gpc add" data-tall="1">📚 這類全部各做一張</button></div>`:'');
  $('#gkeep').onchange=()=>{LS.set('gkeep',$('#gkeep').checked);gTpl();toast($('#gkeep').checked?'🔒 開始時會在提示詞後面加「保持臉不變」':'不加了',2000)};
  box.onclick=e=>{const c=e.target.closest('[data-tc]');if(c){LS.set('gtpl_o',open===c.dataset.tc?'':c.dataset.tc);gTpl();return}
    if(e.target.closest('[data-tall]')){const L=(GTPL.find(x=>x[0]===open)||[0,[]])[1],g=$('#gp');if(g.value.trim()&&!confirm(`換成「${open}」的 ${L.length} 句、每句各做一張？（現在框裡的字會被換掉）`))return;
      g.value=L.join('\n\n');g.rows=Math.min(12,L.length*2);LS.set('gprompt',g.value);$('#gml').checked=true;gMlInfo();LS.set('gml',true);toast(`📚 ${L.length} 句各做一張（「每一行當一個提示詞」已勾）：按開始`,3500);return}
    const t=e.target.closest('[data-tt]');if(!t)return;if(/參考圖/.test(t.dataset.tt)&&!GREF)setTimeout(()=>toast('記得按上面「📎 加參考圖」選那張圖',3500),1300);const g=$('#gp'),v=g.value.trim();g.value=v?v.replace(/[，。,.\s]+$/,'')+'，'+t.dataset.tt:t.dataset.tt;LS.set('gprompt',g.value);
    if(open==='🏞 背景'&&!GMASK.size&&!LS.get('tip_bgmask',false)){LS.set('tip_bgmask',true);toast('小技巧：想讓人物完全不變 → 照片右下角「🖌 局部」塗人物，再按「🔁 反過來：塗的保留」，就只換背景',7000)}else toast(v?'接在後面了':'已填入（可以再改）',1200)}}
// V0.2.12 開始按鈕上直接寫「會排幾張、大概多久」：照片數 × 張數 × 提示詞行數 × 流程數，時間用你實測的平均
function gGoLbl(){const b=$('#ggo');if(!b||b.disabled||!GWFS.length)return;const w=gWf();if(!w.name)return;const p=($('#gp')||{}).value||'';
  const np=w.need_img?Math.max(1,GIMGS.length+GFILES.length):1,nc=+($('#gc')||{}).value||1,nl=Math.max(1,/H3|minimax/i.test(w.name||'')?1:gFinal().length);
  const WL=gBoth()?gBigOn().map(x=>x[0]):[w.name];let n=0,sec=0;const PAIR=LS.get('gorder','txt')==='pair'&&np>1&&nl>1;WL.forEach(x=>{const k=(PAIR?Math.max(np,nl):np*nl)*nc;n+=k;sec+=k*(GSPD[x]||(BIG.find(y=>y[0]===x)||[])[3]||(/H3|影片/.test(x)?300:/合併/.test(x)?50:60))});
  const md=gModeOf(w.name),vb={edit:'改圖',merge:'合併',vid:'做影片',fl:'做影片'}[md]||'開始',un=md==='vid'||md==='fl'?'支':'張';const fl0=md==='fl'&&!(GSF[1]||[]).length&&!(GSI[1]||[]).length;
  const t=fl0?'▶ 先做結束畫面＋影片':(n>1||sec>=60?`▶ ${vb} · ${n} ${un} · 約 ${sec<90?Math.round(sec)+' 秒':Math.round(sec/60)+' 分'}`:`▶ ${vb}`);if(b.textContent!==t)b.textContent=t}
setInterval(()=>{if(CUR==='gen'&&!document.hidden)gGoLbl()},800);
// V0.2.44 提示詞框跟著字數長高（最多 10 行），長的提示詞不用在小框裡捲
setInterval(()=>{const g=$('#gp');if(!g||CUR!=='gen')return;const h=Math.min(260,Math.max(84,g.scrollHeight+2));if(Math.abs(g.offsetHeight-h)>4&&document.activeElement!==g||g.scrollHeight>g.clientHeight+4){g.style.height='auto';g.style.height=Math.min(260,Math.max(84,g.scrollHeight+2))+'px'}},700);
// V0.1.97 電腦瀏覽器：Ctrl＋V 直接貼上截圖／複製的圖當照片；Ctrl＋Enter 開始（在生圖頁）
document.addEventListener('paste',e=>{if(CUR!=='gen'||!$('#gpick'))return;const F=[...(e.clipboardData||{}).items||[]].filter(x=>x.kind==='file'&&/^image\//.test(x.type)).map(x=>x.getAsFile()).filter(Boolean);
  if(!F.length)return;e.preventDefault();F.forEach((f,i)=>{if(!f.name||f.name==='image.png'){try{Object.defineProperty(f,'name',{value:`貼上_${Date.now()}_${i}.png`})}catch(x){}}});gAddFiles(F);toast(`📋 貼上 ${F.length} 張`,1500)});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('#crp')){$('#crp').remove();CR=null;MK=null}});   // Esc 關掉裁切、局部
document.addEventListener('keydown',e=>{if(CUR==='gen'&&(e.ctrlKey||e.metaKey)&&e.key==='Enter'&&$('#ggo')&&!$('#ggo').disabled){e.preventDefault();gGo()}});
// V0.1.81 兩個定案流程互換：Qwen 做的覺得不夠好 → 一鍵「🏆 用 GROK 做一次」（同照片、同提示詞、GROK 自己的設定）；反過來也可以
function gOther(wf){const i=BIG.findIndex(b=>b[0]===wf);if(i>=0){const o=BIG[1-i];return [o[0],o[1]]}const M=[['兩張圖合併（INT8 快）','🏆'],['兩張圖合併（Qwen 快）','⚡']],j=M.findIndex(m=>m[0]===wf);if(j<0||!GWFS.some(x=>x.name===M[1-j][0]))return null;return M[1-j]}   // V0.2.85 合併也能互換
async function gOtherGo(id,wf){const r=await api('/api/gen_act',{a:'other',id,wf,params:LS.get('gpar:'+wf,{})});toast(r.ok?r.message:(r.message||'失敗'),3500);if(r.ok){if(CUR==='gen')gJobs();else hLoad(true)}}
// V0.2.08 📎 參考圖：第二張圖（衣服、商品、地點、畫風…），提示詞寫「參考圖」指它（例如：把衣服換成參考圖裡的衣服）；GROK、Qwen 2.1 都能用
let GREF=LS.get('gref','')||null;
function gRef(){const box=$('#gref');if(!box)return;const u=GREF?(GREF instanceof File?(GREF._u||(GREF._u=URL.createObjectURL(GREF))):IMGT('inputs/'+GREF)):'';
  box.innerHTML=GREF?`<div class="grefc"><img src="${u}"><div class="grow"><b>📎 參考圖</b><div class="mu">提示詞寫「參考圖」指它，例如：把衣服換成參考圖裡的衣服${/Qwen 2\.1/.test(($('#gw')||{}).value||'')?'<br><span style="color:var(--orange)">⚡ Qwen 帶參考圖比較弱，衣服／商品要像的話用 🏆 GROK</span>':''}</div></div><button class="pill" id="grefc">換</button><button class="pill er" id="grefx">✕</button></div>`:`<button class="gpc add" id="grefb">📎 加參考圖（衣服、商品、地點、畫風…）</button>${LS.get('gref_hist',[]).length?`<span class="grefh"><span class="mu">最近用過：</span>${LS.get('gref_hist',[]).map(n=>`<img src="${IMGT('inputs/'+n)}" data-rh="${esc(n)}" onerror="this.remove()">`).join('')}</span>`:''}`;
  $$('[data-rh]',box).forEach(i=>i.onclick=()=>{GREF=i.dataset.rh;LS.set('gref',GREF);gRef();if(!/參考圖/.test($('#gp').value)){LS.set('gtpl_o','📎 參考圖');gTpl()}toast('📎 用這張當參考圖',1500)});
  const b=$('#grefb')||$('#grefc');if(b)b.onclick=()=>$('#grf').click();const x=$('#grefx');if(x)x.onclick=()=>{GREF=null;LS.set('gref','');gRef()};
  $('#grf').onchange=()=>{const f=$('#grf').files[0];$('#grf').value='';if(!f)return;GREF=f;gRef();
    (async()=>{try{const bl=await shrink(f),r=await api('/api/gen_upload',await bl.arrayBuffer(),true);if(r.ok&&GREF===f){GREF=r.img;LS.set('gref',GREF);LS.set('gref_hist',[GREF].concat(LS.get('gref_hist',[]).filter(x=>x!==GREF)).slice(0,8));gRef()}}catch(e){}})();const g=$('#gp');if(!/參考圖/.test(g.value)){LS.set('gtpl_o','📎 參考圖');gTpl()}toast('📎 好了：提示詞裡寫「參考圖」指這張（下面有現成的句子）',3500)}}
// V0.1.98 📌 我的配方：最上面一排，點一下＝流程、提示詞、畫質等設定、保持臉不變一次套好（只差選照片）；長按（或右邊 ✕）刪掉
function gRcp(R){const box=$('#grcp');if(!box)return;if(!R.length){box.innerHTML='';return}
  box.innerHTML=`<span class="mu">📌 我的配方</span>${R.map((r,i)=>`<span class="gpc rc" data-ri="${i}" title="${esc(r.wf)}${r.both?'＋兩個都跑':''}：${esc(r.prompt)}">${r.ref?'📎 ':''}${esc(r.name)}<i data-rdel="${i}">✕</i></span>`).join('')}`;
  box.onclick=async e=>{const d=e.target.closest('[data-rdel]');if(d){e.stopPropagation();const r=R[+d.dataset.rdel];if(confirm(`刪掉配方「${r.name}」？`)){await api('/api/prompts',{a:'rdel',r});gPl()}return}
    const c=e.target.closest('[data-ri]');if(!c)return;const r=R[+c.dataset.ri];if(!GWFS.some(w=>w.name===r.wf))return toast('這個配方的流程不見了：'+r.wf,4000);
    Object.entries(r.params||{}).forEach(([w,o])=>LS.set('gpar:'+w,o));LS.set('gkeep',!!r.keep);LS.set('gboth',!!r.both);$('#gw').value=r.wf;$('#gp').value=r.prompt;LS.set('gprompt',r.prompt);if(r.ref){GREF=r.ref;LS.set('gref',GREF)}gRef();gWfInfo();gTpl();
    toast(`📌 套用「${r.name}」：選照片按開始就好`,2500);const pk=$('#gcard1');if(pk)pk.scrollIntoView({behavior:'smooth'})}}
async function gPl(){const box=$('#gpls');if(!box)return;const r=await api('/api/prompts');if(!r.ok||!$('#gpls'))return;const all=LS.get('gpl_all',false);
  const S=r.saved||[],R=r.recent||[],cut=t=>t.length>22?t.slice(0,22)+'…':t;
  const chips=S.map(t=>`<span class="gpc sv" data-pt="${esc(t)}" title="${esc(t)}">★ ${esc(cut(t))}<i data-pdel="${esc(t)}">✕</i></span>`).concat(R.map(t=>`<span class="gpc" data-pt="${esc(t)}" title="${esc(t)}">🕘 ${esc(cut(t))}</span>`));
  gRcp(r.recipes||[]);
  box.innerHTML=`<button class="gpc add" id="gpsave">⭐ 存這句</button><button class="gpc add" id="grsave">📌 存成配方</button>${chips.slice(0,all?99:6).join('')}${chips.length>6?`<button class="gpc more" id="gpmore">${all?'收起':'更多 '+(chips.length-6)}</button>`:''}`;
  $('#grsave').onclick=async()=>{const p=$('#gp').value.trim(),wf=$('#gw').value;if(!wf)return toast('先選流程');const nm=prompt('配方名稱（例如：換西裝、證件照、穿公司制服）\n會記住：流程'+(gBoth()?'（兩個都跑）':'')+'、提示詞、畫質和其他設定、保持臉不變'+(typeof GREF==='string'&&/參考圖/.test(p)?'、📎 參考圖':''),p.slice(0,12));if(!nm||!nm.trim())return;
    const W=gBoth()?gBigOn().map(b=>b[0]):[wf],params={};W.forEach(w=>params[w]=LS.get('gpar:'+w,{}));
    await api('/api/prompts',{a:'rsave',r:{name:nm.trim(),wf,both:gBoth(),prompt:p,params,keep:LS.get('gkeep',false),ref:typeof GREF==='string'&&/參考圖/.test(p)?GREF:''}});toast('📌 存好了：生圖頁最上面點一下就套用',3000);gPl()};
  $('#gpsave').onclick=async()=>{const t=$('#gp').value.trim();if(!t)return toast('先打提示詞');await api('/api/prompts',{a:'save',p:t});toast('⭐ 存起來了');gPl()};
  const m=$('#gpmore');if(m)m.onclick=()=>{LS.set('gpl_all',!all);gPl()};
  box.onclick=async e=>{const d=e.target.closest('[data-pdel]');if(d){e.stopPropagation();if(confirm('不要這句了？'))await api('/api/prompts',{a:'del',p:d.dataset.pdel});gPl();return}
    const c=e.target.closest('[data-pt]');if(c){$('#gp').value=c.dataset.pt;LS.set('gprompt',c.dataset.pt);toast('已填入（可以再改）',1200)}}}
// 早安提示：有比較做完了還沒看 → 上面一條橫幅，點了直接去打分數
async function gNews(){const r=await api(U('/api/cmp',{a:'runs'}));const b=$('#gnews');if(!r.ok||!b)return;const seen=LS.get('cmp_seen',0);
  const R=(r.runs||[]).find(x=>x.id>seen&&!((x.counts||{}).wait||(x.counts||{}).run));if(!R){b.innerHTML='';return}
  const c=R.counts||{};b.innerHTML=`<div class="gnews"><b>🧪 比較 #${R.id} 做完了</b><span>${(c.done||0)} 張完成${c.fail?` · ✖ ${c.fail} 張失敗`:''} · ${R.imgs.length} 張照片 × ${R.wfs.length} 欄</span><button class="pill acc" id="gnewsgo">去看結果、打星星 →</button><button class="pill" id="gnewsx">✕</button></div>`;
  $('#gnewsgo').onclick=()=>{LS.set('cmp_seen',R.id);CRUN=R.id;LS.set('cmp_run',R.id);LS.set('cmp_view','one');LS.set('cmp_pi',0);CUR='cmp';LS.set('tab','cmp');tabs();show();setTimeout(()=>{const m=$('#cmx');if(m)m.scrollIntoView()},900)};
  $('#gnewsx').onclick=()=>{LS.set('cmp_seen',R.id);b.innerHTML=''}}
async function gGo(){const w=gWf();if(!w.name)return toast('先選流程');const p0=$('#gp').value.trim(),PKX=pkSuffix(),p=pkJoin(p0);   // V0.3.41 🏷 積木加在後面
  if(w.need_img&&!GFILES.length&&!GIMGS.length)return toast('先選照片'+((w.n_img||0)>1?'：'+(w.slots||[])[0]:''));const NS=w.n_img||0;
  if(/首尾幀/.test(w.name)&&!(GSF[1]||[]).length&&!(GSI[1]||[]).length&&(GIMGS.length||GFILES.length))return gChainFL(w,p);   // V0.2.54 沒有尾幀：先用改圖做
  for(let i=1;i<NS;i++)if(!(GSF[i]||[]).length&&!(GSI[i]||[]).length)return toast('還沒選：'+((w.slots||[])[i]||'圖'+(i+1)));
  if(/首尾幀/.test(w.name)){const src=k=>k===0?(GFILES[0]?URL.createObjectURL(GFILES[0]):GIMGS[0]&&IMGU('inputs/'+GIMGS[0])):((GSF[1]||[])[0]?URL.createObjectURL(GSF[1][0]):(GSI[1]||[])[0]&&IMGU('inputs/'+GSI[1][0]));   // V0.2.51 首尾兩張比例差太多：影片會被拉歪或裁掉
    const dim=u=>new Promise(ok=>{if(!u)return ok(0);const im=new Image();im.onload=()=>ok(im.naturalWidth/im.naturalHeight);im.onerror=()=>ok(0);im.src=u});const [a1,a2]=await Promise.all([dim(src(0)),dim(src(1))]);
    if(a1&&a2&&Math.abs(Math.log(a1/a2))>0.15&&!confirm(`首幀和尾幀的比例差很多（${a1>1?'橫':'直'}的 vs ${a2>1?'橫':'直'}的），影片會照首幀的比例，尾幀可能被裁掉或拉歪。\n建議兩張用一樣比例的照片（例如尾幀用改圖從首幀做出來，比例就一定一樣）。還是要開始？`))return}
  let many=w.need_img?(GFILES.length+GIMGS.length):1;for(let i=1;i<NS;i++)many*=((GSF[i]||[]).length||(GSI[i]||[]).length);
  const NT=/H3|minimax/i.test(w.name)?1:Math.max(1,gFinal().length);   // V0.3.38 多篇文字
  if(many>1&&NT>1&&LS.get('gorder','txt')==='pair'){if(!confirm(`一對一：${many} 張照片配 ${NT} 篇文字（第 1 張配第 1 篇…，少的那邊從頭輪）＝ ${Math.max(many,NT)*+$('#gc').value} 個工作`))return}else if(many>1&&!confirm(NT>1?`批量：${many} 張照片 × ${NT} 篇文字 × ${$('#gc').value} 張 = ${many*NT*+$('#gc').value} 個工作。\n順序：${LS.get('gorder','txt')==='img'?'一張圖先跑完全部文字':'一篇文字先跑完全部圖'}（可以按「🔀 順序」切換）`:`批量：${many} 張照片 × ${$('#gc').value} 張 = ${many*+$('#gc').value} 個工作，都用同一段提示詞？`))return;if(!p&&!(w.cr||{}).blank_ok&&!confirm('沒有打提示詞，照流程原本的跑？'))return;
  const b=$('#ggo');b.disabled=true;try{
    if(GFILES.length&&w.need_img){const FS=GFILES.slice(),N=[];FS.forEach(f=>f._taken=true);for(let i=0;i<FS.length;i++){toast(`照片上傳中… ${i+1}／${FS.length}`,60000);let nm=null;
        if(FS[i]._p)try{nm=await FS[i]._p}catch(e){}
        if(!nm){let blob;try{blob=await shrink(FS[i])}catch(e){return toast(`第 ${i+1} 張讀不到${/heic|heif/i.test(FS[i].name)?'（HEIC 格式手機瀏覽器開不了，請先存成 JPG）':''}`,6000)}
          const r=await api(FS[i]._tag?U('/api/gen_upload',{tag:FS[i]._tag}):'/api/gen_upload',await blob.arrayBuffer(),true);if(!r.ok)return toast(`第 ${i+1} 張上傳失敗：${r.message||''}`,6000);nm=r.img}N.push(nm)}
      FS.forEach((f,i)=>{if(GMASK.has(f)){GMASK.set(N[i],GMASK.get(f));GMASK.delete(f)}});GIMGS=GIMGS.concat(N);GFILES=GFILES.filter(f=>!FS.includes(f));LS.set('gimgs',GIMGS)}
    for(let s=1;s<NS;s++){const F=GSF[s]||[];if(!F.length)continue;const N=[];for(let i=0;i<F.length;i++){toast(`${(w.slots||[])[s]||'圖'+(s+1)} 上傳中… ${i+1}／${F.length}${/^video/.test(F[i].type)?`（影片 ${fmtB(F[i].size)}，要等一下）`:''}`,600000);let blob;
        if(/^video\//.test(F[i].type)||(w.kinds||[])[s]==='video')blob=F[i];else try{blob=await shrink(F[i])}catch(e){return toast(`${(w.slots||[])[s]} 第 ${i+1} 張讀不到`,6000)}
        const r=await api('/api/gen_upload',await blob.arrayBuffer(),true);if(!r.ok)return toast(`上傳失敗：${r.message||''}`,6000);N.push(r.img)}GSI[s]=N;GSF[s]=[];LS.set('gslots',GSI)}
    const KP=(LS.get('gkeep',false)&&w.need_img&&!/H3|minimax/i.test(w.name)&&!/保持.{0,6}臉/.test(p)?GKEEP:'')+(LS.get('vmusic',false)&&/H3/.test(w.name)&&(w.cr||{}).simple?' #music':'');
    let REF='';if(GREF&&w.need_img&&NS<=1&&!/參考圖/.test(p))toast('📎 提示詞沒寫「參考圖」：這次不帶參考圖',3000);if(GREF&&w.need_img&&NS<=1&&/參考圖/.test(p)){if(GREF instanceof File){toast('參考圖上傳中…',30000);let bl;try{bl=await shrink(GREF)}catch(e){return toast('參考圖讀不到',5000)}const r=await api('/api/gen_upload',await bl.arrayBuffer(),true);if(!r.ok)return toast('參考圖上傳失敗：'+(r.message||''),5000);GREF=r.img;LS.set('gref',GREF);gRef()}REF=GREF;LS.set('gref_hist',[REF].concat(LS.get('gref_hist',[]).filter(x=>x!==REF)).slice(0,8))}
    const MKS={};if(w.need_img&&(NS<=1||/^兩張圖合併/.test(w.name)))for(const n of GIMGS){const b=GMASK.get(n);if(!b)continue;if(!b._srv){const r=await api('/api/gen_upload',await b.arrayBuffer(),true);if(!r.ok)return toast('遮罩上傳失敗：'+(r.message||''),5000);b._srv=r.img}MKS[n]=b._srv}
    const body={cue:GCUE&&Object.keys(MKS).length&&p.startsWith(GCUE.p)?GCUE.cue:'',ref:REF,masks:MKS,wf:w.name,prompt:p,neg:$('#gn').value,imgs:w.need_img?GIMGS:[],n:+$('#gc').value,params:LS.get(PK(),{})};if(NS>1)body.slots=[GIMGS].concat(Array.from({length:NS-1},(_,k)=>GSI[k+1]||[]));
    LS.set('gwf_hist',[w.name].concat(LS.get('gwf_hist',[]).filter(n=>n!==w.name)).slice(0,8));
    const SEQ=LS.get('vseq',false)&&/H3/.test(w.name)&&!/首尾幀/.test(w.name)&&p.includes('\n')?p.split('\n').map(x=>x.trim()).filter(Boolean):null;
    if(SEQ&&SEQ.length>1){body.chain={kind:'seq',wf:w.name,prompts:SEQ.slice(1).map(x=>x+KP),params:LS.get(PK(),{})}}
    const PL0=SEQ?[SEQ[0]]:/H3|minimax/i.test(w.name)?[p]:gFinal();let PL=SEQ?PL0:PL0.length?PL0:[p];let r={ok:true},tot=0;if(PL.some(q=>q.includes('〔🎲'))){const n=Math.max(1,+$('#gc').value||1);PL=PL.flatMap(q=>Array.from({length:n},()=>pkRoll(q))).slice(0,100);body.n=1}   // 每一行一個提示詞：各排一次
    const MP2=['兩張圖合併（INT8 快）','兩張圖合併（Qwen 快）'];const WL=gBoth()?gBigOn().map(b=>b[0]):LS.get('gboth_m',false)&&MP2.includes(w.name)&&MP2.every(n=>GWFS.some(x=>x.name===n))?MP2.slice():[w.name];   // 🔁 兩個都跑：快的先排，先看到結果
    WL.sort((a,b)=>(GSPD[a]||99)-(GSPD[b]||99));
    const FS=PL.length>1?Math.floor(Math.random()*2147483000)+1:0;   // V0.2.70 好幾種寫法一起試：用同一個種子，比較公平（差別只來自提示詞）
    let J0=0;for(const wn of WL){body.wf=wn;body.params=LS.get('gpar:'+wn,{});if(FS&&wn===$('#gw').value){const sid=(GDEF.flatMap(g=>g.items).find(it=>it.type==='seed')||{}).id;if(sid&&!(sid in body.params))body.params=Object.assign({},body.params,{[sid]:FS})}const PR=LS.get('gorder','txt')==='pair'&&PL.length>1&&NS<=1&&body.imgs.length>1;if(PR){const IM0=body.imgs,MK0=body.masks,N=Math.max(IM0.length,PL.length);for(let i=0;i<N;i++){const im=IM0[i%IM0.length];body.imgs=[im];body.masks=MK0[im]?{[im]:MK0[im]}:{};body.prompt=PL[i%PL.length]+KP;if(J0)body.join=J0;r=await api('/api/gen_run',body);if(!r.ok)break;tot+=(r.ids||[]).length;if(!J0)J0=(r.ids||[])[0]||0}body.imgs=IM0;body.masks=MK0;if(!r.ok)break;continue}   // V0.3.57 一對一
      const IMO=LS.get('gorder','txt')==='img'&&PL.length>1&&NS<=1&&body.imgs.length>1;   // V0.3.38 🔀 一張圖先跑完全部文字
      const IG=IMO?body.imgs.map(x=>[x]):[body.imgs],IM0=body.imgs,MK0=body.masks;
      for(const ig of IG){for(const q of PL){body.prompt=q+KP;body.imgs=ig;if(IMO){body.masks={};for(const n of ig)if(MK0[n])body.masks[n]=MK0[n]}const MANY=WL.length>1||PL.length>1;if(MANY&&J0)body.join=J0;r=await api('/api/gen_run',body);if(!r.ok)break;tot+=(r.ids||[]).length;if(MANY&&!J0)J0=(r.ids||[])[0]||0}if(!r.ok)break}body.imgs=IM0;body.masks=MK0;if(!r.ok)break}
    if(r.ok&&WL.length>1)r.message=`兩個流程都排了，共 ${tot} 張（快的先跑）`;
    toast(r.ok?(PL.length>1?`✔ ${PL.length} 篇文字 × 照片，共排了 ${tot} 個工作`:'✔ '+r.message)+'，電腦開始跑':(r.message||'失敗'),r.ok?3000:6000);if(r.ok){LS.set('gprompt',p);gJobs();gPl()}}catch(e){toast('失敗：'+e.message,5000)}finally{b.disabled=false}}
/* V0.3.38 多篇文字：有空行 → 用空行分篇（一篇可以有好幾行）；沒有空行 → 跟以前一樣每一行一篇。最多 50 篇 */
function gSplit(p){p=String(p||'').replace(/\r/g,'');const B=/\n[ \t]*\n/.test(p)?p.split(/\n[ \t]*\n+/):p.split('\n');return B.map(x=>x.trim()).filter(Boolean)}
function gMlInfo(){const e=$('#gmln');if(!e)return;const on=$('#gml')&&$('#gml').checked,n=on?gSplit($('#gp').value).length:0,ni=GIMGS.length+GFILES.length;
  e.textContent=on?(n?`共 ${n} 篇`+(ni>1?(LS.get('gorder','txt')==='pair'?`、${ni} 張圖一對一 ＝ ${Math.max(n,ni)} 次`:` × ${ni} 張圖 ＝ ${n*ni} 次`):''):'（還沒有文字）'):'';const o=$('#gord');if(o){o.hidden=!(on&&n>1&&ni>1);const go=LS.get('gorder','txt');o.textContent=go==='img'?'🔀 一張圖先跑完全部文字':go==='pair'?`🔀 一對一：第 1 張圖配第 1 篇…（${Math.max(n,ni)} 個）`:'🔀 一篇文字先跑完全部圖'}}
/* V0.3.39 ⏹ 批量取消：整批（同一次送出的）或全部，一次在電腦上取消（幾百個也是一下子） */
let GQS={n:0,b:{}},GBSEEN=new Set(),GEXP=new Set();
async function gCancelMany(batch){const n=batch?(GQS.b[String(batch)]||0):GQS.n,run=GJ.filter(x=>x.state==='run'&&(!batch||(x.batch||x.id)===batch));
  if(!n&&!run.length)return toast('沒有在排隊的');
  if(n&&!confirm(batch?`取消這一批還在排隊的 ${n} 個？`:`取消全部排隊中的 ${n} 個？`))return;
  const stop=run.length>0&&confirm(n?`正在跑的那 ${run.length} 張也要中斷嗎？\n（按「取消」＝讓它做完）`:`中斷正在跑的 ${run.length} 張？`);if(!n&&!stop)return;
  const r=await api('/api/gen_act',{a:'cancel_many',batch:batch||0,run:stop});toast(r.message||'已取消',3000);gJobs();if($('#sysPop')&&$('#sysPop').dataset.t==='q')qLoad($('#sysPop .sysPopB')||$('#sysPop'))}
function gTimes(j){if(j.state==='run')return j.t_start?`<span class="mu" data-ts="${j.t_start}" data-est="${j.est&&j.est.sec?j.est.sec:''}">⏱</span>`:'';
  if(j.state==='wait')return j.est&&j.est.sec?`<span class="mu">預估運算 ${fmtT(j.est.sec)}${j.eta?` · 大約 ${fmtT(j.eta)} 後開始`:''}</span>`:'<span class="mu">第一次跑這個設定，還沒有時間資料</span>';
  if(j.state==='done'&&j.run_s)return `<span class="mu">⏱ 運算 ${fmtT(j.run_s)}（全部 ${fmtT(j.dur)}）${j.cold===1?' · 有載入模型':''}${j.out_w?` · ${j.out_w}×${j.out_h}`:''}</span>`;return ''}
function gCard(j,hist){const [nm,col]=GST[j.state]||[j.state,'var(--sub)'];let st=nm;
  if(j.state==='wait')st+=j.qpos?` 第 ${j.qpos} 個`:'';if(j.state==='wait'&&j.msg)st+=' · '+esc(j.msg);if(j.state==='run')st=`▶ ${esc(j.msg||'生成中')}`;
  const tm=new Date(j.t*1000).toLocaleString('zh-TW',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});const busy=j.state==='wait'||j.state==='run';
  return `<div class="job" data-jid="${j.id}"><div class="row">${hist&&HSEL?`<input type="checkbox" class="hck" data-ck="${j.id}" ${HSEL.has(j.id)?'checked':''}>`:''}<b>#${j.id}</b><span style="color:${col};font-weight:800">${st}</span><span class="grow"></span><span class="mu">${esc(j.src)} ${tm}</span></div>
  <div class="mu clamp">${esc(j.prompt||'（沒有提示詞）')}</div><div class="mu hx" style="font-size:11.5px">${FTAG(j.img)}${j.mask?'🖌 局部 · ':''}${j.ref?'📎 參考圖 · ':''}${esc(j.wf)}${j.brief?' · '+esc(j.brief):''}${hist&&j.seed>=0?' · 種子 '+j.seed:''}</div>
  ${j.state==='run'?gBar(j)+`<img class="gpv" data-pv="${j.id}" onerror="this.style.display='none'" ${GPVU[j.id]?`src="${GPVU[j.id]}"`:''} style="${GPVU[j.id]?'':'display:none;'}max-height:180px;max-width:100%;border-radius:10px;margin-top:6px">`:''}<div class="hx">${gTimes(j)}</div>${j.pbrief?`<div class="mu hx" style="font-size:11.5px">⏱ ${esc(j.pbrief)}</div>`:''}${j.state==='fail'?`<div style="color:var(--red);font-size:12.5px">${esc(j.msg)}</div>${gFailTip(j.msg)}`:''}
  <div class="th">${(j.imgs&&j.imgs.length?j.imgs:[j.img]).filter(Boolean).map(x=>{const f=(j.tins&&j.tins['inputs/'+x])||('inputs/'+x);return ISV(x)?`<video class="src" src="${IMGU(f)}#t=0.5" muted playsinline preload="metadata"></video>`:`<img class="src" src="${IMGT(f)}" data-big="${esc(f)}" loading="lazy">`}).join('')}${j.img&&j.outs.length?'<span class="mu">→</span>':''}${j.outs.map((o,i)=>ISV(o)?`<div class="vo"><video src="${IMGU(o)}" controls playsinline preload="metadata"></video><div class="row"><a class="pill" href="${U('/api/img',{f:o,dl:1})}" download>⬇ 存影片</a><button class="pill" data-g="vnext" data-id="${j.id}" data-v="${esc(o)}" title="用這支影片的最後一格當新照片，接著做下一段">⏭ 接下一段</button><button class="pill" data-g="vlast" data-id="${j.id}" data-v="${esc(o)}" title="最後一格存成照片（可以拿去改圖）">🖼 最後一格</button><button class="pill" data-g="vgif" data-id="${j.id}" data-v="${esc(o)}" title="轉成 GIF（LINE、聊天軟體直接會動）">🎞 存 GIF</button></div></div>`:`<img src="${IMGT(o)}" data-big="${esc(o)}" data-id="${j.id}" data-i="${i}" loading="lazy">`).join('')}</div>
  <div class="row hx">${hist==='trash'?'':busy?`${j.stall?`<button class="pill" data-g="restart" data-id="${j.id}" title="ComfyUI 很久沒進度：中斷、清掉記憶體、放回排隊重來">🔄 中斷重來</button>`:''}${j.state==='wait'?`<button class="pill" data-g="top" data-id="${j.id}">⏫ 先做這個</button>`:''}<button class="pill er" data-g="cancel" data-id="${j.id}">⏹ 取消</button>${(()=>{const bk=j.batch||j.id,m=GQS.b[String(bk)]||0;if(hist||m<2||GBSEEN.has(bk))return '';GBSEEN.add(bk);return `<button class="pill er" data-g="cancelb" data-id="${bk}">⏹ 取消這一批（${m} 個）</button>`})()}`:`<button class="pill" data-g="rerun" data-id="${j.id}">↻ 再跑一次</button>`}
  ${busy||hist==='trash'?'':`<button class="pill" data-g="fill" data-id="${j.id}">✎ 用這組設定</button>`}${!busy&&j.state==='done'&&!j.cmp&&gOther(j.wf)?`<button class="pill acc" data-g="other" data-id="${j.id}">${gOther(j.wf)[1]} 換 ${/GROK|INT8/.test(gOther(j.wf)[0])?'GROK':'Qwen'}</button>`:''}${!busy&&!hist?`<button class="pill" data-g="hide" data-id="${j.id}">收起</button>`:''}${hist&&hist!=='trash'&&!busy&&j.img&&!ISV(j.img)&&!j.cmp?`<button class="pill" data-g="tocmp" data-id="${j.id}">🧪 拿去比較</button>`:''}${hist&&!busy?hBtns(hist):''}</div></div>`}
/* V0.3.45 連不到 ComfyUI／卡住：最上面一條提醒（等了多久、可能原因、再試一次、暫停） */
function gWaitBan(j){const e=$('#gwaitb');if(!e)return;const st=(j.jobs||[]).filter(x=>x.state==='run'&&x.stall);
  if(!j.wait&&!st.length){e.innerHTML='';return}const m=j.wait&&j.wait_t?Math.max(1,Math.round((j.now-j.wait_t)/60)):0;
  e.innerHTML=`<div class="gfin" style="border-color:var(--orange);margin-bottom:10px"><div class="h"><b>⚠ ${j.wait?`連不到 ComfyUI${m?' 已 '+m+' 分鐘':''}：排隊 ${(j.qsum||{}).n||0} 張在等`:`ComfyUI 卡住沒進度（#${st.map(x=>x.id).join('、#')}）`}</b></div>
  <div class="mu" style="font-size:13px;margin-top:4px">${j.wait?'可能是：①電腦上的 ComfyUI 沒開／正在更新或重開 ②開著但記憶體不夠，在用硬碟當記憶體，慢到回不了話（工作管理員看「記憶體」和「專用 GPU 記憶體」）。連上後會自動接著做；等的時候不會跟 SortCut／GoPro 要效能。':'多半是顯示卡記憶體或 RAM 不夠：已請 SortCut／GoPro 先放掉顯示卡；可以按卡片上的「🔄 中斷重來」，20 分鐘會自動重來一次。'}</div>
  <div class="row" style="gap:8px;margin-top:8px;flex-wrap:wrap">${j.wait?'<button class="pill" id="gwR">🔄 再連一次</button>':''}${j.wait&&j.cexe?'<button class="pill acc" id="gwL">🚀 打開 ComfyUI</button>':''}${j.wait&&j.cexe?`<label class="mu" style="font-size:12.5px;display:flex;gap:4px;align-items:center"><input type="checkbox" id="gwA" ${j.cauto?'checked':''}> 連不到 3 分鐘就自動打開</label>`:''}<button class="pill" id="gwP">⏸ 先暫停生圖</button></div></div>`;
  if($('#gwL'))$('#gwL').onclick=async()=>{const r=await api('/api/gen_act',{a:'launch',id:0});toast(r.message||'',5000)};if($('#gwA'))$('#gwA').onchange=async ev=>{const r=await api('/api/gen_act',{a:'autostart',id:0,on:ev.target.checked});toast(r.message||'',3000)};
  if($('#gwR'))$('#gwR').onclick=async()=>{const r=await api('/api/gen_act',{a:'recheck',id:0});toast(r.message||'',4000);gJobs()};
  $('#gwP').onclick=async()=>{const r=await api('/api/bgctl',{a:'pause',k:'gen'}).catch(()=>null);toast(r&&r.ok!==false?'⏸ 生圖暫停了（上面「背景」可以繼續）':'到上面「背景」按暫停',4000);gJobs()}}
async function gJobs(){const j=await api('/api/gen');if(!j.ok||!$('#gj'))return;GJ=j.jobs||[];GQS=j.qsum||{n:0,b:{}};GBSEEN=new Set();gWaitBan(j);GOFF=(j.now||Date.now()/1000)-Date.now()/1000;const c=j.comfy||{};
  const gpu=String(c.gpu||'').replace(/^cuda:\d+\s*/,'').replace(/\s*:\s*cuda\w*$/i,'').replace(/^NVIDIA\s+/,'').replace(/^GeForce\s+/,'');
  $('#gst').innerHTML=c.ok?`<span class="ok"><i></i>ComfyUI ${esc(c.ver||'')}</span>${gpu?`<span title="${esc(c.gpu)}">🎮 ${esc(gpu)}</span>`:''}${c.vram&&c.vram[1]?`<span>VRAM 剩 ${fmtB(c.vram[0])}</span>`:''}`:`<span class="bad"><i></i>連不到 ComfyUI</span>`;
  $('#gerr').innerHTML=(c.ok?'':`<div class="mu" style="color:var(--orange)">電腦上的 ComfyUI 要開著；工作會先排隊，ComfyUI 一開就自動接著跑</div>`)+(j.paused?'<div style="color:var(--orange)">⏸ 生圖在「後台」被暫停了</div>':'');
  const act=GJ.filter(x=>x.state==='run'||x.state==='wait').sort((a,b)=>(a.state!=='run')-(b.state!=='run')||(a.qpos||0)-(b.qpos||0));   // 正在跑的放最上面，排隊照順序                // 這一頁只放製作中的；做好的到「歷史紀錄」
  const was=GACT;GACT=new Set(act.map(x=>x.id));if(was){const fin=GJ.filter(x=>was.has(x.id)&&!GACT.has(x.id));
    const ok=fin.filter(x=>x.state==='done').length,bad=fin.filter(x=>x.state==='fail').length;if(ok||bad){toast((ok?`✔ 做好 ${ok} 個`:'')+(bad?` ✖ ${bad} 張失敗`:'')+' → 在「歷史紀錄」',4500);gNotify(ok,bad,!act.length)}}
  LS.set('gpend',act.length>0);{const ca=$('#gcanall');if(ca){ca.style.display=GQS.n>0?'':'none';ca.textContent=`⏹ 全部取消（${GQS.n}）`;ca.onclick=()=>gCancelMany(0)}}const ge=$('#geta');if(ge){const e=gEta(act);ge.textContent=e||'做好的在「歷史紀錄」'}
  const nd=GJ.filter(x=>x.state==='done').length;
  const hb=[],seenW=new Set();for(const x of act){const bk=x.batch||x.id;if(x.state==='wait'&&seenW.has(bk)&&!GEXP.has(bk))continue;if(x.state==='wait'){seenW.add(bk);const m=(GQS.b[String(bk)]||0)-1;hb.push(gCard(x));if(m>0&&!GEXP.has(bk))hb.push(`<div class="gfin gfold" data-gexp="${bk}" style="cursor:pointer;margin-top:-4px"><div class="h"><b style="flex:1 1 auto">📚 同一批還有 ${m} 張在排隊</b><span class="mu">點一下展開</span><button class="pill er" data-g="cancelb" data-id="${bk}">⏹ 取消這一批</button></div></div>`);continue}hb.push(gCard(x))}   // V0.3.61 批量的排隊卡片收成一張
  const h=hb.join('')||`<div class="empty2"><b>☕ 現在沒有在做的</b><span>選照片、打提示詞，按「開始」 · 做好的在「歷史紀錄」${nd?`（最近 ${nd} 張）`:''}</span></div>`;if(h!==GLAST){GLAST=h;$('#gj').innerHTML=h}
  // 剛做好的（最近 1 小時）：直接在這裡看，不用切到歷史紀錄
  const now=Date.now()/1000+GOFF,D=GJ.filter(x=>x.state==='done'&&x.outs&&x.outs.length&&now-(x.t1||x.t)<3600&&!x.cmp),DN=D.length;D.splice(12);
  const dh=D.length?`<div class="gdh"><b>✨ 剛做好</b><span class="mu" style="flex:1 1 auto">最近 1 小時 ${DN} 個 · 點圖放大（左右換）</span><button class="pill" data-g="gohist">📚 看全部</button></div><div class="gds">${D.map(x=>x.outs.slice(0,1).map(o=>ISV(o)?`<span class="gdi"><video src="${IMGU(o)}#t=0.5" muted playsinline preload="metadata" controls></video><button class="gdv" data-g="vnext" data-id="${x.id}" data-v="${esc(o)}">⏭ 接下一段</button></span>`:`<span class="gdi"><img src="${IMGT(o)}" data-big="${esc(o)}" data-id="${x.id}" data-i="0" loading="lazy">${(BIG.find(b=>b[0]===x.wf)||[])[1]?`<i>${BIG.find(b=>b[0]===x.wf)[1]}</i>`:''}${x.mask?'<i class="m">🖌</i>':''}${x.vote?`<i class="v">★${x.vote}</i>`:''}${x.outs.length>1?`<i class="n">+${x.outs.length-1}</i>`:''}</span>`).join('')).join('')}</div>`:'';
  const gd=$('#gdone');if(gd&&gd.dataset.h!==dh){gd.dataset.h=dh;gd.innerHTML=dh}}
// V0.1.82 做好通知＋全部做完的時間：手機震一下＋叮一聲（設定可關）；切到別的 App 時分頁標題會變「✅ 做好了」，回來看到就恢復
const TITLE0=document.title;let GAUD=null;
function gBeep(){if(!LS.get('nt_snd',true))return;try{GAUD=GAUD||new (window.AudioContext||window.webkitAudioContext)();const t=GAUD.currentTime;[880,1320].forEach((f,i)=>{const o=GAUD.createOscillator(),g=GAUD.createGain();o.frequency.value=f;o.connect(g);g.connect(GAUD.destination);g.gain.setValueAtTime(.0001,t+i*.16);g.gain.exponentialRampToValueAtTime(.25,t+i*.16+.02);g.gain.exponentialRampToValueAtTime(.0001,t+i*.16+.28);o.start(t+i*.16);o.stop(t+i*.16+.3)})}catch(e){}}
function gNotify(ok,bad,all){if(LS.get('nt_vib',true)&&navigator.vibrate)try{navigator.vibrate(bad&&!ok?[80,60,80,60,80]:[120,80,120])}catch(e){}
  if(all||document.hidden)gBeep();if(document.hidden)document.title=(ok?`✅ 做好 ${ok} 張`:`✖ ${bad} 張失敗`)+' · '+TITLE0}
document.addEventListener('pointerdown',()=>{if(!GAUD&&LS.get('nt_snd',true))try{GAUD=new (window.AudioContext||window.webkitAudioContext)()}catch(e){}},{once:true});   // 手機要先點過一下才能出聲
document.addEventListener('visibilitychange',()=>{if(!document.hidden)document.title=TITLE0});
// 分頁在背景：一般更新會停（省電），這裡每 15 秒輕輕問一次「做完了沒」，做完就改標題
let GBGW=null;setInterval(async()=>{if(!document.hidden||!LS.get('gpend',false)||!TOK)return;try{const j=await api('/api/gen');if(!j.ok)return;const A=new Set((j.jobs||[]).filter(x=>x.state==='run'||x.state==='wait').map(x=>x.id));
  if(GBGW){const fin=(j.jobs||[]).filter(x=>GBGW.has(x.id)&&!A.has(x.id));const ok=fin.filter(x=>x.state==='done').length,bad=fin.filter(x=>x.state==='fail').length;if(ok||bad)gNotify(ok,bad,!A.size)}GBGW=A;if(!A.size)LS.set('gpend',false)}catch(e){}},15000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)GBGW=null});
function gEta(act){if(!act.length)return '';const now=SNOW();let s=0;act.forEach(x=>{const e=(x.est&&x.est.sec)||GSPD[x.wf]||(/H3|影片/.test(x.wf)?300:60);s+=x.state==='run'&&x.t_start?Math.max(3,e-(now-x.t_start)):e});
  const d=new Date(Date.now()+s*1000);return `${act.length} 張 · 約 ${s<90?Math.round(s)+' 秒':Math.round(s/60)+' 分'}後全部做完（${d.toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit',hour12:false})}）`}
async function rGen(again){if(again)return gJobs();
  $('#v').innerHTML=`<div id="genv"><div class="gstat" id="gst"></div><div id="gwaitb"></div><div id="gerr"></div><div id="gnews"></div><div id="gtour"></div><div class="gmode" id="gmode"></div><div class="grcp" id="grcp"></div>
  <section class="gcard" id="gcard1"><div class="ghd"><span class="gnum">1</span><b>照片</b><span class="grow"></span><span class="mu" id="gcnt"></span></div>
  <div id="gpicks" class="gpicks"><div id="gpick" class="drop"></div></div><input type="file" id="gf" accept="image/*" multiple style="display:none"><input type="file" id="gf2" multiple style="display:none">
  <div class="gsrc" id="gfolder"><button class="gchip" id="gf2b">📁 從資料夾選</button><button class="gchip" id="gfvb">🎞 從影片挑格</button><button class="gchip" id="grcb">🕘 最近用過</button></div><div class="crec" id="grec"></div><div id="gmrec"></div><input type="file" id="gfv" accept="video/*" style="display:none"></section>
  <section class="gcard"><div class="ghd"><span class="gnum">2</span><b>想怎麼改</b><span class="grow"></span><button class="gclr" id="gpfix" title="依你寫的內容，自動補上「哪些地方要保持不變」" style="margin-right:6px;border-color:var(--accent);color:var(--accent)">🪄 補完整</button><button class="gclr" id="gpclr" title="清掉提示詞（可以復原）">清掉</button></div>
  <div class="gmrg" id="gmrg"></div><textarea id="gp" rows="3" placeholder="想怎麼改？例如：把衣服換成紅色連身裙（電腦：Ctrl＋Enter 直接開始）"></textarea>
  <label class="gmlb"><input type="checkbox" id="gml" ${LS.get('gml',false)?'checked':''}><span>多篇文字：用<b>空行</b>隔開，每篇做一次　<span class="mu" id="gmln"></span></span></label><button class="pill" id="gord" hidden title="多張圖＋多篇文字時，排隊的順序"></button>
  <div id="gpkx"></div>
  <div class="gtabs" id="gtabs"><button data-gt="pk">🏷 積木</button><button data-gt="pl">📚 範本</button><button data-gt="tool">🧰 工具箱</button><button data-gt="fav">⭐ 常用</button></div>
  <div class="gtp" data-gp="tool"><div class="gtool" id="gtool"></div></div><div class="gtp" data-gp="pk"><div id="gpk"></div></div><div class="gtp" data-gp="pl"><div id="gpl"></div></div><div class="gtp" data-gp="fav"><div class="gpls" id="gpls"></div></div>
  <div class="gtcat" id="gvact"></div><div class="gref" id="gref"></div><input type="file" id="grf" accept="image/*" style="display:none"><div class="gppl" id="gppl"></div><div class="gtpl" id="gtpl"></div>
  <div class="mu" id="gh3" style="display:none"><a href="javascript:void(0)" id="gh3b">📝 插入 H3 提示詞格式</a>　分鏡＋對白＋聲音寫在一起；英文描述效果最好，對白可以用中文</div>
  <details id="gnd"><summary class="mu">＋ 負面提示詞</summary><textarea id="gn" rows="2"></textarea></details></section>
  <section class="gcard"><div class="ghd"><span class="gnum">3</span><b>流程與設定</b></div>
  <div class="gbig" id="gbig"></div><div class="gvar" id="gvar"></div><div class="gwrow"><select id="gw" class="gsel"></select><select id="gc">${[1,2,3,4,6,8].map(x=>`<option value="${x}">${x} 張</option>`).join('')}</select></div>
  <div class="gqual" id="gqual"></div><div class="gqual" id="gdur"></div><div class="gqual" id="gtst"></div><div class="gqual" id="gden"></div><div class="gwq" id="gwq"></div><div id="gwi"></div><div id="gmod"></div><details id="gadv" class="gadv"><summary>⚙ 進階設定 <span class="mu">一般不用動</span></summary><div id="gpar"></div></details></section>
  <div class="ggobar"><button class="ggo" id="ggo">▶ 開始</button></div>
  <section class="gcard" id="gjsec"><div class="ghd"><b style="white-space:nowrap">⏳ 製作中</b><span class="grow"></span><button class="gclr" id="gcanall" style="display:none;white-space:nowrap">⏹ 全取消</button></div><div class="mu" id="geta" style="margin:-4px 0 8px">做好的在「歷史紀錄」</div><div id="gj"></div><div id="gdone"></div></section><div style="text-align:center;margin:4px 0 18px"><button class="gclr" id="greset" title="照片、提示詞、局部、參考圖、兩個都跑、保持臉不變都清掉（流程和畫質留著）">🧹 全部重來</button></div></div>`;
  GLAST='';$('#gp').value=LS.get('gprompt','');$('#gp').oninput=()=>{LS.set('gprompt',$('#gp').value);gMlInfo();pkPrev()};$('#gml').onchange=()=>{LS.set('gml',$('#gml').checked);gMlInfo();pkPrev()};$('#gord').onclick=()=>{const c=LS.get('gorder','txt');LS.set('gorder',c==='txt'?'img':c==='img'?'pair':'txt');gMlInfo();gGoLbl&&gGoLbl();toast($('#gord').textContent,2500)};setTimeout(gMlInfo,50);if(PKL){pkDraw();pdDraw();pkPrev()}else pkLoad();setTimeout(gTabs,60);gPl();gTpl();gRef();gMaskLoad();gTour();
  $('#greset').onclick=()=>{if(!confirm('全部重來？照片、提示詞、局部、參考圖、兩個都跑、保持臉不變都清掉（流程和畫質留著）'))return;
    GIMGS=[];GFILES=[];LS.set('gimgs',[]);GMASK.clear();LS.set('gmask',{});GREF=null;LS.set('gref','');LS.set('gboth',false);LS.set('gkeep',false);LS.set('gml',false);
    const g=$('#gp');g.value='';g.rows=3;LS.set('gprompt','');$('#gml').checked=false;gPrev();gRef();gTpl();gWfInfo();scrollTo(0,0);toast('🧹 清乾淨了，選新照片吧',2000)};
  setInterval(()=>{const f=$('#gpfix');if(f)f.style.display=/H3|影片/.test(($('#gw')||{}).value||'')?'none':''},800);   // 影片不用補完整
  $('#gpfix').onclick=()=>{const g=$('#gp'),v=g.value.trim();if(!v)return toast('先打一句想怎麼改',2000);if(/H3|影片/.test($('#gw').value))return toast('影片的提示詞會自動包成完整格式，不用補',2500);   // V0.2.68 規則式補完整（不多跑模型）
    const R=[[/衣|穿|裙|褲|外套|西裝|制服/,'衣服自然合身，保持人物的臉、五官、髮型和身材不變'],[/背景|場景|地方|街|海邊|房間/,'人物完全不變，光線和色調跟新背景一致，邊緣自然'],[/髮/,'臉和五官不變，髮絲自然'],
      [/光|燈|夕陽|夜/,'人物和內容不變，陰影和反光自然'],[/風格|畫風|動漫|卡通|水彩|素描|插畫/,'保留人物的特徵和構圖'],[/去掉|移除|刪/,'補上自然連貫的背景，看不出來曾經有東西'],[/字|文字|標題/,'字清楚、字型和風格跟畫面搭配']];
    let add=R.filter(([re])=>re.test(v)).map(x=>x[1]).filter(x=>!v.includes(x.slice(0,6)));if(!add.length&&!/不變/.test(v))add=['其他地方保持不變'];if(!add.length)return toast('已經很完整了',1500);
    g.value=v.replace(/[，。,.\s]+$/,'')+'，'+add.join('，');LS.set('gprompt',g.value);toast('🪄 補上了：'+add.join('、'),3000)};
  $('#gpclr').onclick=()=>{const g=$('#gp');if(g.dataset.undo!==undefined&&!g.value){g.value=g.dataset.undo;delete g.dataset.undo;$('#gpclr').textContent='清掉';LS.set('gprompt',g.value);return}if(!g.value)return;g.dataset.undo=g.value;g.value='';LS.set('gprompt','');$('#gpclr').textContent='↶ 復原';g.focus()};
  {const g=$('#gp'),fit=()=>{if(g.offsetParent===null)return;g.style.height='auto';g.style.height=Math.min(g.scrollHeight+2,Math.round(innerHeight*.6))+'px'};g.addEventListener('input',fit);g.addEventListener('focus',fit);setTimeout(fit,50);   // V0.3.66 提示詞框跟著字變高（最高半個螢幕多）
    g.addEventListener('keydown',e=>{if(e.key==='Enter'&&(e.ctrlKey||e.metaKey)){e.preventDefault();const b=$('#ggo');if(b&&!b.disabled)b.click()}})}   // Ctrl／⌘＋Enter＝開始
  $('#gp').addEventListener('input',()=>{const g=$('#gp');if(g.value&&g.dataset.undo!==undefined){delete g.dataset.undo;$('#gpclr').textContent='清掉'}});
  $('#gpick').addEventListener('click',e=>{if(!e.target.closest('[data-gback]'))return;e.stopPropagation();const p=LS.get('gimg_prev','');if(!p)return;LS.set('gimg_prev',GIMGS[0]||'');GIMGS=[p];GFILES=[];LS.set('gimgs',GIMGS);gPrev();toast('↩ 換回上一張了',1500)},true);   // V0.2.75
  $('#gpick').onclick=e=>{const cx=e.target.closest('[data-gcrop]');if(cx){e.stopPropagation();crOpen(+cx.dataset.gcrop);return}const mx=e.target.closest('[data-gmask]');if(mx){e.stopPropagation();mkOpen(+mx.dataset.gmask);return}const x=e.target.closest('[data-gdel]');if(x){e.stopPropagation();gDel(+x.dataset.gdel);return}
    if(e.target.closest('[data-gclr]')){e.stopPropagation();if(confirm('清空已選的照片？')){GIMGS=[];GFILES=[];LS.set('gimgs',GIMGS);gPrev()}return}
    if((gWf().n_img||0)<=1&&!e.target.closest('[data-gadd]'))return;    // 點縮圖不做事（用 ✕ 拿掉、＋ 加照片）
    $('#gf').click()};
  $('#gf').onchange=()=>{const F=[...$('#gf').files];$('#gf').value='';if(F.length){if((gWf().n_img||0)>1){GFILES=F;GIMGS=[];gPrev()}else gAddFiles(F)}};
  // Android 新版相片選擇器的「相簿」只列相機／截圖／下載幾個；不限檔案類型就會打開「檔案」，可以進任何資料夾（只收圖片）
  $('#gf2b').onclick=()=>$('#gf2').click();$('#gf2').onchange=()=>{const all=[...$('#gf2').files],F=all.filter(f=>/^image\//.test(f.type)||/\.(jpe?g|png|webp|heic|heif|bmp)$/i.test(f.name));$('#gf2').value='';
    if(all.length&&!F.length)return toast('選到的不是圖片');if(all.length>F.length)toast(`略過 ${all.length-F.length} 個不是圖片的檔案`);if(F.length)gAddFiles(F)};
  $('#gh3b').onclick=()=>{const t=$('#gp');if(t.value.trim()&&!confirm('換成 H3 提示詞格式？（現在的字會被蓋掉）'))return;t.value=H3SK;t.rows=8;t.focus()};
  api('/api/people').then(r=>{const L=((r&&r.people)||[]).filter(x=>x.photos.length);if(!L.length)return;$('#gppl').innerHTML=L.map(x=>`<button data-pc="${x.code}">👤 ${x.code}${x.name?' '+esc(x.name):''}</button>`).join('')+'<span class="mu">點一下插入；寫編號會自動帶他的照片</span>';
    $('#gppl').onclick=e=>{const a=e.target.closest('[data-pc]');if(!a)return;const t=$('#gp'),i=t.selectionStart??t.value.length;t.value=t.value.slice(0,i)+a.dataset.pc+t.value.slice(i);t.focus()}});
  $('#grcb').onclick=async()=>{const b=$('#grec');if(b.innerHTML){b.innerHTML='';return}const r=await api(U('/api/cmp',{a:'recent'}));const L=r.imgs||[];
    b.innerHTML=L.length?L.map(n=>`<img src="${IMGT('inputs/'+n)}" data-rec="${esc(n)}" class="${GIMGS.includes(n)?'on':''}" loading="lazy">`).join(''):'<span class="mu">還沒有用過的照片</span>';
    const pr=await api('/api/people');const PP=((pr&&pr.people)||[]).filter(x=>x.photos.length).flatMap(x=>x.photos.slice(0,3).map(f=>[x.code,f]));   // V0.2.94 人物庫也列出來
    if(PP.length)b.innerHTML+=`<div class="mu" style="flex-basis:100%;margin:6px 0 2px">👤 人物庫</div>`+PP.map(([c,f])=>`<img src="${IMGT('people/'+c+'/'+f)}" data-pp="${esc(c+'/'+f)}" title="${esc(c)}" loading="lazy">`).join('');
    b.onclick=async e=>{const q=e.target.closest('[data-pp]');if(q){const bl=await (await fetch(IMGU('people/'+q.dataset.pp),{headers:{'x-app-token':TOK}})).blob();const r=await api('/api/gen_upload',await bl.arrayBuffer(),true);if(r.ok){GIMGS.push(r.img);LS.set('gimgs',GIMGS);gPrev();toast('✔ 加進照片',1200)}return}
      const x=e.target.closest('[data-rec]');if(!x)return;const n=x.dataset.rec;if(GIMGS.includes(n)){GIMGS=GIMGS.filter(y=>y!==n);x.classList.remove('on')}else{GIMGS.push(n);x.classList.add('on')}LS.set('gimgs',GIMGS);gPrev()}};
  $('#gfvb').onclick=()=>$('#gfv').click();$('#gfv').onchange=()=>{const f=$('#gfv').files[0];$('#gfv').value='';if(f)fpOpen(f)};
  $('#ggo').onclick=gGo;$('#gj').onclick=gClick;$('#gdone').onclick=gClick;gPrev();gNews();
  const j=await api('/api/gen?full=1');if(!j.ok)return;GWFS=j.wfs||[];GMP=j.mp;const want=LS.get('gwf','')||j.wf;
  GLINE=j.lineup||{};const SPD=j.spd||{};GSPD=SPD;GSTAR=j.stars||{};const opt=w=>`<option value="${esc(w.name)}" ${w.name===want?'selected':''}>${esc(w.name)}${SPD[w.name]?` · 約 ${SPD[w.name]} 秒`:''}</option>`;
  // 分組：改圖／文字生圖／影片／其他（流程多了比較好找）
  const grp=w=>{const k=w.kinds||[];if(k.includes('video')||/影片|H3/.test(w.name))return '🎬 影片';if(!w.need_img)return '✏ 文字生圖（不用照片）';if((w.n_img||0)>1)return '🧩 好幾張圖';if(/去背/.test(w.name))return '✂ 去背';return '🎨 改圖'};
  const G={};GWFS.forEach(w=>(G[grp(w)]=G[grp(w)]||[]).push(w));const ORD=['🎨 改圖','✏ 文字生圖（不用照片）','🧩 好幾張圖','✂ 去背','🎬 影片'];
  $('#gw').innerHTML=ORD.filter(g=>G[g]).map(g=>`<optgroup label="${g}">${G[g].map(opt).join('')}</optgroup>`).join('')||'<option value="">（沒有流程：到 ⚙ 設定 匯入）</option>';
  $('#gw').onchange=gWfInfo;if(GWFS.length)gWfInfo();gJobs()}
// V0.1.79 兩個定案流程做成大按鈕（單手點），「🔁 兩個都跑」同一張照片兩個都排，直接比
const BIG=[['GROK 改圖（INT8 快）','🏆','效果最好',40],['Qwen 2.1 Turbo 改圖','⚡','速度最快',24]];let GSPD={},GSTAR={};
const gBigOn=()=>BIG.filter(b=>GWFS.some(w=>w.name===b[0]));
const gBoth=()=>LS.get('gboth',false)&&gBigOn().length===2&&BIG.some(b=>b[0]===$('#gw').value);
function gBig(){const box=$('#gbig');if(!box)return;const L=gBigOn(),cur=$('#gw').value;if(!L.length){box.innerHTML='';return}const both=gBoth();
  box.innerHTML=L.map(b=>`<button class="gbb ${(b[0]===cur||both)?'on':''}" data-gbig="${esc(b[0])}"><span class="ic">${b[1]}</span><b>${esc(b[0].replace(' 改圖',''))}</b><small>${b[2]} · 約 ${Math.round(GSPD[b[0]]||b[3])} 秒${GSTAR[b[0]]?` · <span style="color:#ffc53d">★ ${GSTAR[b[0]][0]}</span>（${GSTAR[b[0]][1]}）`:''}</small></button>`).join('')
   +(L.length===2?`<button class="gbb both ${both?'on':''}" data-gbig="*"><span class="ic">🔁</span><b>兩個都跑</b><small>同一張各做一次</small></button>`:'');
  box.onclick=e=>{const x=e.target.closest('[data-gbig]');if(!x)return;const n=x.dataset.gbig;
    if(n==='*'){const v=!LS.get('gboth',false);LS.set('gboth',v);if(v&&!BIG.some(b=>b[0]===$('#gw').value))$('#gw').value=L[0][0];gWfInfo();toast(v?'🔁 按開始會兩個流程都排':'只跑選的那個',1600);return}
    LS.set('gboth',false);$('#gw').value=n;gWfInfo()}}
// ================= 🧪 比較：同一批照片 × 好幾種流程（每一列一種流程，預設收起來，點開可以調參數）。照流程排：同一個模型的照片連著跑，模型只載入一次
let CI=LS.get('cmp_imgs',[]),CF=[],CROWS=[],CSEL=new Set(LS.get('cmp_wfs',['Qwen 2.1 Turbo 改圖','GROK 改圖（INT8 快）'])),CRUN=LS.get('cmp_run',0),CRT=0,CMX=null,CJ=[],CLAST='',CRLAST='';
const cSrc=()=>CI.map(n=>({u:IMGT('inputs/'+n),tag:(/_f(\d{4,})\.\w+$/.exec(n)||[])[1]})).concat(CF.map(f=>({u:f._u||(f._u=URL.createObjectURL(f)),tag:f._tag&&f._tag.slice(1)})));
function cPrev(){const d=$('#cpick');if(!d)return;const L=cSrc(),n=L.length;$('#ccnt').textContent=n?`${n} 張`:'';
  if(!n){d.innerHTML=`<div class="gempty" data-cadd="1"><div class="ic">📷</div><b>選要比較的照片</b><span class="mu">可以一次選很多張（例如 9 張）</span></div>`;cSum();return}
  d.innerHTML=`<div class="gtiles${n===1?' one':''}">${L.map((x,k)=>`<div class="gtile"><img src="${x.u}" onerror="this.style.opacity=.3"><span class="gi">${k+1}</span>${x.tag?`<span class="ftag">🎞 ${+x.tag}</span>`:''}<button class="gx" data-cdel="${k}">✕</button></div>`).join('')}<div class="gtile gadd" data-cadd="1">＋<small>加照片</small></div></div>
   <div class="gfoot"><span class="mu">每個流程都會把這 ${n} 張各改一次</span><button class="gclr" data-cclr="1">清空</button></div>`;cSum()}
const cMB=r=>r.miss.reduce((a,m)=>a+(m.size||0),0);
const cLic=l=>/Apache|MIT/.test(l)?'ok':/不能商用|非商用|NC|研究/.test(l)?'er':'wa';
function cRowHead(r){const on=CSEL.has(r.key);let st;
  if(!r.ready)st=`<span class="cbadge wa">${r.err?'✖ 流程有問題':'⏳ 還沒做好（ComfyUI 開著會自動做）'}</span>`;
  else if(r.miss.length){const dl=r.miss.filter(m=>m.state==='run'||m.state==='wait'),run=r.miss.find(m=>m.state==='run');
    st=dl.length?`<span class="cbadge bl">⬇ 下載中 ${run&&run.size?Math.round((run.got||0)/run.size*100)+'%':''} · 剩 ${r.miss.length} 個</span>`:`<span class="cbadge er">缺 ${r.miss.length} 個模型${cMB(r)?' · '+fmtB(cMB(r)):''}</span>`}
  else st='<span class="cbadge ok">✔ 模型齊了</span>';
  return `<label class="cck" onclick="event.stopPropagation()"><input type="checkbox" data-cw="${esc(r.key)}" ${on?'checked':''}></label><div class="cnm"><b>${r.var?'<span class="cvar">↳</span> ':''}${esc(r.key)}</b>
    <div class="cbs">${r.t2i?'<span class="cbadge bl">✏ 不用照片</span>':''}${r.steps?`<span class="cbadge">${r.steps} 步</span>`:''}${r.avg?`<span class="cbadge">⏱ 約 ${Math.round(r.avg)} 秒／張</span>`:''}${r.score?`<span class="cbadge" style="color:#ffc53d">★ ${r.score}（${r.nv}）</span>`:''}${st}</div></div>`}
function cRows(){const box=$('#crows');if(!box)return;const open=new Set($$('#crows details[open]').map(d=>d.dataset.w));
  const h=CROWS.map(r=>`<details class="crow ${CSEL.has(r.key)?'on':''} ${r.var?'isvar':''}" data-w="${esc(r.key)}" data-wf="${esc(r.wf)}" ${open.has(r.key)?'open':''}><summary>${cRowHead(r)}</summary><div class="cbody">
    ${r.var?`<div class="cnote">跟「${esc(r.wf)}」同一個模型，這一欄固定改：${Object.entries(r.var).map(([k,v])=>esc(k.replace(/^\d*\./,''))+' = '+esc(v)).join('、')}（其他設定一樣）</div>`:''}
    ${r.note?`<div class="cnote">${esc(r.note)}</div>`:''}${r.license?`<div class="cnote">授權：<span class="cbadge ${cLic(r.license)}">${esc(r.license)}</span></div>`:''}
    ${r.miss.length?`<div class="cmiss">${r.miss.map(m=>`<div>${m.state==='done'?'✔':m.state==='run'?'⬇':m.state==='fail'?'✖':'·'} ${esc(m.file)} <span class="mu">${m.size?fmtB(m.size):''}${m.msg?' · '+lnk(m.msg):''}${m.known?'':' · 不知道去哪下載'}</span></div>`).join('')}</div>`:''}
    ${r.var?(r.custom?`<button class="pill er" data-cxd="${esc(r.key)}">✕ 刪掉這個自訂欄</button>`:''):`<div class="cpar" data-cp="${esc(r.key)}" data-cpw="${esc(r.wf)}"><div class="mu">點開讀參數…</div></div><button class="pill" data-cxs="${esc(r.wf)}" style="margin-top:8px">＋ 用現在的參數另存成一欄（同模型不同設定一起比）</button>`}</div></details>`).join('');
  if(h!==CRLAST){CRLAST=h;box.innerHTML=h;$$('#crows details').forEach(d=>{d.ontoggle=()=>{if(d.open)cPar(d.dataset.w,d.dataset.wf)};if(d.open)cPar(d.dataset.w,d.dataset.wf)})}cSum()}
// 參數：跟「生圖」頁同一份（同一個流程在兩頁的設定一樣），只顯示常用＋模型
async function cPar(key,wf){wf=wf||key;const box=$(`#crows .cpar[data-cp="${CSS.escape(key)}"]`);if(!box||box.dataset.ok)return;const r=await api(U('/api/gen_params',{wf}));if(!r.ok){box.innerHTML=`<div class="mu">${esc(r.message||'讀不到參數（流程還沒做好？）')}</div>`;return}
  const K='gpar:'+wf,O=LS.get(K,{});box.dataset.ok=1;
  const G=(r.groups||[]).filter(g=>g.g==='常用'||g.g==='模型／LoRA');
  const inp=it=>{const v=it.id in O?O[it.id]:(it.type==='seed'?'':it.value);const a=`data-cpp="${esc(it.id)}" data-t="${it.type}"`;
    if(it.type==='choice')return `<select ${a}>${it.choices.map(c=>`<option ${String(c)===String(v)?'selected':''}>${esc(c)}</option>`).join('')}</select>`;
    if(it.presets)return `<select ${a}>${[...new Set([...it.presets,+v])].sort((x,y)=>x-y).map(c=>`<option value="${c}" ${+c===+v?'selected':''}>${c}${c===it.value?' ✓':''}</option>`).join('')}</select>`;
    if(it.type==='bool')return `<input type="checkbox" ${a} ${v?'checked':''}>`;
    if(it.type==='int'||it.type==='float'||it.type==='seed')return `<input type="number" inputmode="decimal" ${a} value="${esc(v)}" ${it.type==='seed'?'placeholder="隨機"':''} step="${it.step||(it.type==='int'||it.type==='seed'?1:'any')}">`;
    return `<input ${a} value="${esc(v)}">`};
  const short=t=>String(t).replace(/（[^）]*）/g,'').replace(/\([^)]*\)/g,'').trim()||t;
  box.innerHTML=G.map(g=>`<div class="mu" style="font-weight:700;margin:6px 0 2px">${esc(g.g)}</div><div class="pgrid">${g.items.filter(it=>it.type!=='seed').map(it=>it.type==='bool'?`<label class="pc b">${inp(it)}<span>${esc(short(it.label))}</span></label>`:`<div class="pc${(it.type==='choice'&&Math.max(...it.choices.map(c=>String(c).length))>22)?' wf':''}"><label>${esc(short(it.label))}</label>${inp(it)}</div>`).join('')}</div>`).join('')
    +`<div class="row" style="margin-top:6px"><span class="grow mu">${Object.keys(O).length?`改了 ${Object.keys(O).length} 項（跟生圖頁共用）`:'流程本來的設定（跟生圖頁共用）'}</span><button class="pill" data-cpr="${esc(wf)}">↺ 還原</button></div>`;
  const D={};(r.groups||[]).forEach(g=>g.items.forEach(it=>D[it.id]=it));
  $$('[data-cpp]',box).forEach(x=>x.onchange=()=>{const O=LS.get(K,{}),it=D[x.dataset.cpp];const v=gParVal(x);if(v===null||String(v)===String(it.value))delete O[x.dataset.cpp];else O[x.dataset.cpp]=v;LS.set(K,O);toast('✔ 記住了（生圖頁也一樣）',1200)});
  box.querySelector('[data-cpr]').onclick=()=>{LS.set(K,{});box.dataset.ok='';cPar(key,wf);toast('已還原')}}
function cEst(){const n=CI.length+CF.length;let s=0,unk=0;CROWS.filter(r=>CSEL.has(r.key)).forEach(r=>{const k=r.t2i?1:n;if(r.avg)s+=r.avg*k;else{unk++;s+=(r.steps>=20?240:60)*k}});return {s,unk}}
const cCount=()=>{const n=CI.length+CF.length;return CROWS.filter(r=>CSEL.has(r.key)&&r.ready).reduce((a,r)=>a+(r.t2i?1:n),0)};
function cSum(){const b=$('#cgo'),d=$('#cdlb');if(!b)return;const n=CI.length+CF.length,m=CROWS.filter(r=>CSEL.has(r.key)&&r.ready).length,E=cEst();
  const tot=cCount();b.innerHTML=`▶ 開始比較<small>${n} 張照片 × ${m} 欄 = ${tot*(+$('#cn').value||1)} 張${tot?` · 約 ${fmtT(E.s*(+$('#cn').value||1))}${E.unk?'（沒跑過的先用估的）':''}`:''}</small>`;b.disabled=!tot;
  const miss=CROWS.filter(r=>CSEL.has(r.key)&&r.miss.some(x=>x.known&&!x.state)),U={};miss.forEach(r=>r.miss.forEach(m=>{if(!m.state)U[m.file]=m.size||0}));const gb=Object.values(U).reduce((a,b)=>a+b,0);   // 同一個檔（共用的文字編碼器）只算一次
  d.style.display=miss.length?'':'none';d.innerHTML=`⬇ 下載勾選流程缺的模型（${miss.length} 個流程${gb?' · 約 '+fmtB(gb):''}）${CDISK?`<small style="display:block;font-weight:400;font-size:12px;margin-top:2px;color:${gb&&CDISK.free<gb+5e9?'var(--red)':'var(--sub)'}">模型硬碟剩 ${fmtB(CDISK.free)}${gb&&CDISK.free<gb+5e9?'，不夠放！先少勾幾個':''}</small>`:''}`}
let CDISK=null;async function cLoadRows(){const r=await api(U('/api/cmp',{a:'rows'}));if(!r.ok||CUR!=='cmp')return;CROWS=cMix(r.rows||[]);CDISK=r.disk||null;cRows()}
// 你自己存的變化欄（這支手機記著）：接在原本那個流程下面
function cMix(R){const C=LS.get('cmp_custom',[]),out=[];R.forEach(r=>{out.push(r);if(!r.var)C.filter(c=>c.wf===r.key).forEach(c=>out.push(Object.assign({},r,{key:c.key,name:c.key,var:c.params,custom:1,note:'你存的設定',avg:null,n:0})))});return out}
async function cUpload(){const N=[];for(let i=0;i<CF.length;i++){toast(`照片上傳中… ${i+1}／${CF.length}`,60000);const blob=await shrink(CF[i]);
    const r=await api(CF[i]._tag?U('/api/gen_upload',{tag:CF[i]._tag}):'/api/gen_upload',await blob.arrayBuffer(),true);if(!r.ok)throw new Error(`第 ${i+1} 張上傳失敗：${r.message||''}`);N.push(r.img)}
  CI=CI.concat(N);CF=[];LS.set('cmp_imgs',CI)}
async function cGo(){const cols=CROWS.filter(r=>CSEL.has(r.key)&&r.ready).map(r=>r.custom?{key:r.key,wf:r.wf,params:r.var}:{key:r.key,wf:r.wf}),wfs=[...new Set(cols.map(c=>c.wf))],n=CI.length+CF.length;if(!cols.length||!cCount())return;
  const p=$('#cp').value.trim();if(!p&&!confirm('沒有打提示詞，照各流程原本的跑？'))return;
  const miss=CROWS.filter(r=>!r.var&&wfs.includes(r.wf)&&r.miss.length);
  if(!confirm(`🧪 ${n} 張照片 × ${cols.length} 欄 = ${cCount()*(+$('#cn').value||1)} 張？\n${miss.length?`其中 ${miss.length} 個流程還缺模型：會先自動排下載，下載好才跑那些（其他的先跑）。\n`:''}同一個流程的照片會連著跑（模型只載入一次）。`))return;
  const b=$('#cgo');b.disabled=true;try{await cUpload();
    if(miss.length){const d=await api('/api/cmp',{a:'dl',wfs:miss.map(r=>r.name)});if(d.ok&&d.n)toast(d.message,3000)}
    const params={};wfs.forEach(w=>params[w]=LS.get('gpar:'+w,{}));
    const r=await api('/api/cmp',{a:'start',imgs:CI,prompt:p,neg:'',cols,n:+$('#cn').value||1,same_seed:$('#css').checked,params});
    toast(r.ok?'✔ '+r.message:(r.message||'失敗'),r.ok?4000:7000);if(r.ok){CRUN=r.id;LS.set('cmp_run',CRUN);LS.set('cmp_prompt',p);cRuns()}}catch(e){toast('失敗：'+e.message,6000)}finally{b.disabled=false;cPrev()}}
// ---- 結果：每次比較一張表（列＝照片、欄＝流程），點圖放大（左右換），點星星打分數；最上面一列是每個流程的平均秒數和平均分數
async function cRuns(){const r=await api(U('/api/cmp',{a:'runs'}));if(!r.ok||CUR!=='cmp')return;const R=r.runs||[];const box=$('#cruns');
  if(!R.length){box.innerHTML='<div class="mu">還沒有比較過。選照片、勾流程，按「開始比較」。</div>';$('#cmx').innerHTML='';return}
  if(!R.find(x=>x.id===CRUN))CRUN=R[0].id;
  box.innerHTML=R.map(x=>{const c=x.counts||{},bz=(c.wait||0)+(c.run||0);return `<button class="pill ${x.id===CRUN?'on':''}" data-crun="${x.id}">#${x.id} ${new Date(x.t*1000).toLocaleString('zh-TW',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'})} · ${x.imgs.length}×${x.wfs.length}${bz?` · ⏳ ${bz}${x.eta?` · 約 ${new Date(Date.now()+x.eta*1000).toLocaleTimeString('zh-TW',{hour:'2-digit',minute:'2-digit'})} 好`:''}`:' ✔'}</button>`}).join('');cRun()}
async function cRun(){if(!CRUN)return;const r=await api(U('/api/cmp',{a:'run',id:CRUN}));if(!r.ok||CUR!=='cmp')return;CMX=r;
  CJ=[];Object.entries(r.cells||{}).forEach(([img,W])=>Object.entries(W).forEach(([wf,L])=>L.forEach(c=>CJ.push({id:c.id,img,wf,vote:c.vote||0,run_s:c.run_s,cmp:1,state:c.state}))));
  const S={};(r.summary||[]).forEach(s=>S[s.wf]=s);const best=Math.min(...(r.summary||[]).filter(s=>s.avg).map(s=>s.avg));const top=Math.max(...(r.summary||[]).filter(s=>s.score).map(s=>s.score));
  const star=(c)=>`<span class="cstar">${[1,2,3,4,5].map(k=>`<i data-cv="${c.id}" data-k="${k}" class="${(c.vote||0)>=k?'on':''}">★</i>`).join('')}</span>`;
  const cell=c=>{if(!c)return '<td class="cx none">—</td>';if(c.state==='done'&&c.outs&&c.outs.length)return `<td class="cx"><img src="${IMGT(c.outs[0])}" data-big="${esc(c.outs[0])}" data-id="${c.id}" data-i="0" loading="lazy"><div class="ct">${c.run_s?Math.round(c.run_s)+' 秒'+(c.cold===1?'（載模型）':''):''}</div>${star(c)}</td>`;
    if(c.state==='fail')return `<td class="cx fail" title="${esc(c.msg||'')}">✖ 失敗<div class="ct">${esc((c.msg||'').slice(0,40))}</div></td>`;
    if(c.state==='run')return '<td class="cx run">▶ 生成中</td>';if(c.state==='stop')return '<td class="cx none">⏹</td>';return `<td class="cx wait">⏳${c.msg?'<div class="ct">'+esc(c.msg)+'</div>':''}</td>`};
  const SU=r.summary||[],dn=SU.reduce((a,x)=>a+x.done+x.fail,0),tt=SU.reduce((a,x)=>a+x.done+x.fail+x.wait,0);let runc='';
  Object.entries(r.cells||{}).forEach(([im,W])=>Object.entries(W).forEach(([w,L])=>L.forEach(c=>{if(c.state==='run')runc=`現在跑：${w} · 照片 ${r.imgs.indexOf(im)+1}`})));
  const prog=tt&&dn<tt?`<div class="cprog"><div class="row"><b>進度 ${dn}／${tt}</b><span class="grow"></span><span class="mu">${esc(runc||'排隊中（等模型下載或前面的工作）')}</span></div><div class="pg" style="margin-top:6px"><i style="width:${Math.round(dn/tt*100)}%"></i></div></div>`:'';
  const view=LS.get('cmp_view','one'),pi=Math.min(Math.max(0,LS.get('cmp_pi',0)),Math.max(0,r.imgs.length-1)),tg=`<div class="seg" style="display:inline-flex;margin-bottom:8px"><button data-cvw="one" class="${view==='one'?'on':''}">📱 逐張看</button><button data-cvw="tbl" class="${view==='tbl'?'on':''}">▦ 表格</button></div>`;
  const one=()=>{const im=r.imgs[pi];return `<div class="cone"><div class="row"><button class="pill" data-cpi="${pi-1}" ${pi?'':'disabled'}>‹ 上一張</button><span class="grow" style="text-align:center"><b>${im?'照片 '+(pi+1):'文字生圖'}／${r.imgs.length}</b></span><button class="pill" data-cpi="${pi+1}" ${pi<r.imgs.length-1?'':'disabled'}>下一張 ›</button></div>
    ${im?'':'<div class="cone0"><b>✏ 文字生圖（不用照片）</b></div>'}
    <div class="cgrid" style="--ar:${LS.get('car:'+im,'3/4')}">${im?`<div class="cgc corig"><div class="cgh"><b>📷 原圖</b></div><img src="${IMGT('inputs/'+im)}" data-big="inputs/${esc(im)}" onload="cAr(this,'${esc(im)}')"></div>`:''}${r.wfs.map(w=>{const c=((r.cells[im]||{})[w]||[])[0],s=S[w]||{};return `<div class="cgc"><div class="cgh"><b>${esc(w)}</b><span class="mu">${c&&c.run_s?Math.round(c.run_s)+' 秒':''}</span></div>${c&&c.state==='done'&&c.outs&&c.outs.length?`<img src="${IMGT(c.outs[0])}" data-big="${esc(c.outs[0])}" data-id="${c.id}" data-i="0" loading="lazy">${star(c)}`:`<div class="cgx">${!c?'—':c.state==='fail'?`<div>✖ 失敗<div class="ct" style="padding:0 8px">${esc((c.msg||'').replace(/（生圖頁.*$/,'').slice(0,60))}</div></div>`:c.state==='run'?'▶ 生成中':`<div>⏳ 排隊${c.msg?`<div class="ct">${esc(c.msg)}</div>`:''}</div>`}</div>`}</div>`}).join('')}</div></div>`};
  const h=prog+tg+(view==='one'?one():`<div class="cmxw"><table class="cmxt"><thead><tr><th class="c0">照片</th>${r.wfs.map(w=>{const s=S[w]||{};return `<th><b>${esc(w)}</b><div class="ct">${s.avg?`<span class="${s.avg===best?'cbest':''}">⏱ ${s.avg} 秒</span>`:''}${s.score?` ${s.avg?'· ':''}<span class="${s.score===top?'cbest':''}">★ ${s.score}</span>`:''}</div><div class="ct">${s.done||0}／${(s.done||0)+(s.fail||0)+(s.wait||0)}${s.fail?` · ✖ ${s.fail}`:''}</div></th>`}).join('')}</tr></thead>
    <tbody>${r.imgs.map((im,i)=>`<tr><td class="c0">${im?`<img src="${IMGT('inputs/'+im)}" data-big="inputs/${esc(im)}" loading="lazy"><div class="ct">${i+1}</div>`:'<div class="ct" style="padding-top:30px">✏ 文字生圖</div>'}</td>${r.wfs.map(w=>cell(((r.cells[im]||{})[w]||[])[0])).join('')}</tr>`).join('')}</tbody></table></div>`)+`
    ${cRank(r)}<div class="row" style="margin-top:8px"><button class="pill" id="cexp">🖼 存成一張比較圖</button><button class="pill" id="ccsv">📄 分數表（Excel）</button><button class="pill" id="cagain">↻ 用這組再比一次</button>${(r.summary||[]).some(x=>x.fail)?'<button class="pill er" id="cretry">↻ 失敗的重跑</button>':''}<span class="grow"></span>${(r.summary||[]).some(x=>x.wait)?'<button class="pill" id="cstop">⏹ 停掉剩下的</button>':''}<button class="pill er" id="cdel">🗑 刪掉這次</button></div>
    <div class="mu" style="margin-top:6px">「${esc(r.prompt||'（沒有提示詞）')}」 · ${r.seed>0?'同一個種子 '+r.seed:'每張隨機種子'} · 點圖放大（左右換）· 點星星打分數，最上面會算平均（最快／最高分會亮）</div>`;
  if(h!==CLAST){CLAST=h;const y=scrollY,sx=($('.cmxw')||{}).scrollLeft||0;$('#cmx').innerHTML=h;const w=$('.cmxw');if(w)w.scrollLeft=sx;scrollTo(0,y);
    $('#cexp').onclick=()=>cExport(r);$('#ccsv').onclick=()=>cCsv(r);const cs=$('#cstop');if(cs)cs.onclick=async()=>{if(!confirm('還沒跑的全部取消？做好的會留著'))return;const x=await api('/api/cmp',{a:'stop',id:r.id});toast(x.message||'失敗',3500);CLAST='';cRun()};$('#cdel').onclick=async()=>{if(!confirm(`刪掉比較 #${r.id}？\n還在排隊的會取消，結果放進回收桶（30 天內可以在歷史紀錄還原）`))return;const x=await api('/api/cmp',{a:'del',id:r.id});toast(x.message||'失敗',4000);CRUN=0;CLAST='';cRuns()};const rt=$('#cretry');if(rt)rt.onclick=async()=>{if(!confirm('失敗的那幾張重跑？（缺模型的先到上面按下載，或設定填 Hugging Face 金鑰）'))return;const x=await api('/api/cmp',{a:'retry',id:r.id});toast(x.message||'失敗',5000);CLAST='';cRun()};$('#cagain').onclick=()=>{CI=r.imgs.slice();CF=[];LS.set('cmp_imgs',CI);CSEL=new Set(r.wfs);LS.set('cmp_wfs',r.wfs);$('#cp').value=r.prompt||'';LS.set('cmp_prompt',r.prompt||'');CRLAST='';cRows();cPrev();scrollTo(0,0);toast('已填回照片、提示詞、流程，按「開始比較」')}}}
// 橫的、直的照片都完整看到：格子比例跟原圖一樣（記起來，下次一打開就對），圖用 contain 不裁切
function cAr(img,im){const w=img.naturalWidth,h=img.naturalHeight;if(!w||!h)return;const ar=`${w}/${h}`;if(LS.get('car:'+im)!==ar){LS.set('car:'+im,ar)}const g=img.closest('.cgrid');if(g)g.style.setProperty('--ar',ar);
  if(w>h*1.15&&g)g.classList.add('wide');}
// 排名：有打分數的照分數，沒打的照速度；「甜蜜點」＝分數夠高（≥ 最高分 −0.5）裡面最快的
function cRank(r){const S=(r.summary||[]).filter(s=>s.done);if(S.length<2)return '';const top=Math.max(0,...S.map(s=>s.score||0));
  const L=S.slice().sort((a,b)=>(b.score||0)-(a.score||0)||(a.avg||1e9)-(b.avg||1e9));
  const sweet=top?S.filter(s=>(s.score||0)>=top-0.5&&s.avg).sort((a,b)=>a.avg-b.avg)[0]:null;
  return `<div class="crank">${sweet?`<div class="csweet">🎯 甜蜜點：<b>${esc(sweet.wf)}</b> · ★ ${sweet.score} · 一張約 ${sweet.avg} 秒</div>`:'<div class="mu">打幾張星星，這裡會幫你挑「夠好又最快」的甜蜜點</div>'}
    ${L.map((s,i)=>`<div class="crk"><span class="cn">${i+1}</span><b>${esc(s.wf)}</b><span class="grow"></span>${s.score?`<span>★ ${s.score}<small>（${s.nv}）</small></span>`:''}<span>${s.avg?`⏱ ${s.avg}s`:'—'}</span></div>`).join('')}</div>`}
// 存成一張圖：表頭（流程名、平均秒數、分數）＋每列（原圖＋各流程結果＋星星）
// 分數表：每個模型一列（平均秒數、平均分數、完成／失敗），下面每格明細；Excel 直接開（UTF-8 BOM）
function cCsv(r){const q=v=>'"'+String(v==null?'':v).replace(/"/g,'""')+'"',L=[['模型','平均秒數','平均分數','評分張數','完成','失敗'].map(q).join(',')];
  (r.summary||[]).forEach(s=>L.push([s.wf,s.avg,s.score,s.nv,s.done,s.fail].map(q).join(',')));L.push('');L.push(['照片','模型','狀態','秒數','分數'].map(q).join(','));
  r.imgs.forEach((im,i)=>r.wfs.forEach(w=>{const c=((r.cells[im]||{})[w]||[])[0];if(c)L.push([im?'照片 '+(i+1):'文字生圖',w,c.state,c.run_s?Math.round(c.run_s):'',c.vote||''].map(q).join(','))}));
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\ufeff'+L.join('\r\n')],{type:'text/csv'}));a.download=`比較_${r.id}.csv`;document.body.appendChild(a);a.click();a.remove();toast('✔ 存好了（用 Excel 打開）')}
async function cExport(r){toast('做圖中…',20000);const load=u=>new Promise(ok=>{const i=new Image();i.onload=()=>ok(i);i.onerror=()=>ok(null);i.src=u});
  const W=260,H=340,HD=70,LW=150,pad=8,cols=r.wfs.length,rows=r.imgs.length;const c=document.createElement('canvas');c.width=LW+cols*(W+pad)+pad;c.height=HD+rows*(H+40+pad)+60;
  const g=c.getContext('2d');g.fillStyle='#0e1116';g.fillRect(0,0,c.width,c.height);g.textBaseline='top';const S={};(r.summary||[]).forEach(s=>S[s.wf]=s);
  const fit=(im,x,y,w,h)=>{if(!im)return;const k=Math.max(w/im.width,h/im.height),sw=w/k,sh=h/k;g.drawImage(im,(im.width-sw)/2,(im.height-sh)/2,sw,sh,x,y,w,h)};
  g.font='bold 20px sans-serif';g.fillStyle='#fff';g.fillText('🧪 比較 #'+r.id+'　'+(r.prompt||'').slice(0,60),pad,c.height-44);
  r.wfs.forEach((w,j)=>{const x=LW+pad+j*(W+pad),s=S[w]||{};g.fillStyle='#fff';g.font='bold 18px sans-serif';g.fillText(w.slice(0,16),x,10);g.font='15px sans-serif';g.fillStyle='#8994a4';g.fillText((s.avg?'⏱ '+s.avg+' 秒':'')+(s.score?'　★ '+s.score:''),x,38)});
  for(let i=0;i<rows;i++){const im=r.imgs[i],y=HD+i*(H+40+pad);fit(await load(IMGU('inputs/'+im)),pad,y,LW-pad,(LW-pad)*1.3);
    for(let j=0;j<cols;j++){const x=LW+pad+j*(W+pad),cl=((r.cells[im]||{})[r.wfs[j]]||[])[0];g.fillStyle='#151a21';g.fillRect(x,y,W,H);
      if(cl&&cl.outs&&cl.outs.length)fit(await load(IMGU(cl.outs[0])),x,y,W,H);
      g.font='15px sans-serif';g.fillStyle='#ffc53d';g.fillText(cl&&cl.vote?'★'.repeat(cl.vote):'',x,y+H+6);g.fillStyle='#8994a4';if(cl&&cl.run_s)g.fillText(Math.round(cl.run_s)+' 秒',x+W-60,y+H+6)}}
  c.toBlob(b=>{const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=`比較_${r.id}.jpg`;document.body.appendChild(a);a.click();a.remove();toast('✔ 存好了')},'image/jpeg',0.9)}
async function rCmp(again){
  if(again){CRT++;if(CRT%3===0&&CROWS.some(r=>r.miss.some(m=>m.state==='run'||m.state==='wait')))cLoadRows();
    const busy=CMX&&Object.values(CMX.cells||{}).some(W=>Object.values(W).some(L=>L.some(c=>c.state==='wait'||c.state==='run')));if(busy&&$('#ov').style.display!=='flex'){cRun();if(CRT%15===0)cRuns()}return}
  CLAST='';CRLAST='';
  $('#v').innerHTML=`<div id="genv"><div class="gcard chero"><b>🧪 比較</b><div class="mu">一批照片 × 勾的流程各做一次，做完打星星比哪個好（可以排一整晚）。</div></div>
  <section class="gcard"><div class="ghd"><span class="gnum">1</span><b>照片</b><span class="grow"></span><span class="mu" id="ccnt"></span></div><div id="cpick"></div>
   <div class="gsrc"><button class="gchip" id="cfb">📁 從資料夾選</button><button class="gchip" id="cvb">🎞 從影片挑格</button><button class="gchip" id="cgb">🎨 生圖頁的</button></div><button class="gpc" id="crcb" style="margin-top:8px">🕘 從最近用過的照片挑</button><div class="crec" id="crec2"></div>
   <input type="file" id="cf" accept="image/*" multiple style="display:none"><input type="file" id="cf2" multiple style="display:none"><input type="file" id="cfv" accept="video/*" style="display:none"></section>
  <section class="gcard"><div class="ghd"><span class="gnum">2</span><b>想怎麼改</b><span class="grow"></span><span class="mu">每個流程都用這一句</span></div><textarea id="cp" rows="3" placeholder="例如：改成粉色絲質睡衣連身裙"></textarea>
   <div class="row" style="margin-top:10px"><label class="row" style="gap:6px"><input type="checkbox" id="css" ${LS.get('cmp_same',true)?'checked':''} style="width:20px;height:20px"> 同一個種子（比較比較公平）</label><span class="grow"></span><span class="mu">每格</span><select id="cn" style="height:38px">${[1,2,3].map(x=>`<option value="${x}">${x} 張</option>`).join('')}</select></div></section>
  <section class="gcard"><div class="ghd"><span class="gnum">3</span><b>要比的流程</b></div><div class="row" style="flex-wrap:wrap;gap:6px;margin:-4px 0 8px"><button class="pill acc" id="crec">⭐ 定案的兩個</button><button class="pill" id="cfast">只選快的</button><button class="pill" id="call">全選</button><button class="pill" id="cnone">全不選</button></div>
   <div class="mu" style="margin:-4px 0 8px">點一列打開看說明、調參數（跟生圖頁共用）。上面幾個比較快，越下面越慢。</div><div id="crows"><div class="mu">讀取中…</div></div>
   <button class="btn s" id="cdlb" style="display:none;margin-top:10px"></button></section>
  <div class="ggobar"><button class="ggo" id="cgo" disabled>▶ 開始比較</button></div>
  <section class="gcard"><div class="ghd"><b>📊 比較結果</b><span class="grow"></span><span class="mu">一列一張照片、一欄一個流程</span></div><div class="row" id="cruns" style="margin-bottom:8px"></div><div id="cmx"></div></section></div>`;
  $('#cp').value=LS.get('cmp_prompt',LS.get('gprompt',''));$('#cp').oninput=()=>LS.set('cmp_prompt',$('#cp').value);$('#css').onchange=()=>LS.set('cmp_same',$('#css').checked);$('#cn').onchange=cSum;
  $('#cpick').onclick=e=>{const x=e.target.closest('[data-cdel]');if(x){const k=+x.dataset.cdel;if(k<CI.length){CI.splice(k,1);LS.set('cmp_imgs',CI)}else CF.splice(k-CI.length,1);cPrev();return}
    if(e.target.closest('[data-cclr]')){if(confirm('清空照片？')){CI=[];CF=[];LS.set('cmp_imgs',CI);cPrev()}return}if(e.target.closest('[data-cadd]'))$('#cf').click()};
  $('#cf').onchange=()=>{const F=[...$('#cf').files];$('#cf').value='';CF=CF.concat(F);cPrev()};
  $('#cfb').onclick=()=>$('#cf2').click();$('#cf2').onchange=()=>{const F=[...$('#cf2').files].filter(f=>/^image\//.test(f.type)||/\.(jpe?g|png|webp|bmp)$/i.test(f.name));$('#cf2').value='';CF=CF.concat(F);cPrev()};
  $('#cvb').onclick=()=>$('#cfv').click();$('#cfv').onchange=()=>{const f=$('#cfv').files[0];$('#cfv').value='';if(f)fpOpen(f)};
  $('#crcb').onclick=async()=>{const b=$('#crec2');if(b.innerHTML){b.innerHTML='';return}const r=await api(U('/api/cmp',{a:'recent'}));const L=(r.imgs||[]);
    b.innerHTML=L.length?L.map(n=>`<img src="${IMGT('inputs/'+n)}" data-rec="${esc(n)}" class="${CI.includes(n)?'on':''}" loading="lazy">`).join(''):'<span class="mu">還沒有用過的照片</span>';
    b.onclick=e=>{const x=e.target.closest('[data-rec]');if(!x)return;const n=x.dataset.rec;if(CI.includes(n)){CI=CI.filter(y=>y!==n);x.classList.remove('on')}else{CI.push(n);x.classList.add('on')}LS.set('cmp_imgs',CI);cPrev()}};
  $('#cgb').onclick=()=>{if(!GIMGS.length&&!GFILES.length)return toast('生圖頁還沒選照片');CI=CI.concat(GIMGS.filter(x=>!CI.includes(x)));CF=CF.concat(GFILES);LS.set('cmp_imgs',CI);cPrev();toast('✔ 加進來了')};
  $('#crows').onclick=e=>{const sv=e.target.closest('[data-cxs]');if(sv){const wf=sv.dataset.cxs,P=LS.get('gpar:'+wf,{});if(!Object.keys(P).length)return toast('先在上面改幾個參數（例如步數、照片大小），再另存');
      const nm=prompt('這一欄叫什麼？',`${wf}（${Object.entries(P).map(([k,v])=>k.split('.').pop()+'='+v).join('、').slice(0,30)}）`);if(!nm)return;
      const C=LS.get('cmp_custom',[]).filter(c=>c.key!==nm);C.push({key:nm,wf,params:P});LS.set('cmp_custom',C);LS.set('gpar:'+wf,{});CSEL.add(nm);LS.set('cmp_wfs',[...CSEL]);toast('✔ 多了一欄「'+nm+'」，原本那列的參數還原了');CRLAST='';cLoadRows();return}
    const dx=e.target.closest('[data-cxd]');if(dx){if(!confirm('刪掉這個自訂欄？'))return;LS.set('cmp_custom',LS.get('cmp_custom',[]).filter(c=>c.key!==dx.dataset.cxd));CSEL.delete(dx.dataset.cxd);CRLAST='';cLoadRows()}};
  $('#crows').onchange=e=>{const c=e.target.closest('[data-cw]');if(!c)return;c.checked?CSEL.add(c.dataset.cw):CSEL.delete(c.dataset.cw);LS.set('cmp_wfs',[...CSEL]);c.closest('details').classList.toggle('on',c.checked);cSum()};
  $('#call').onclick=()=>{CROWS.forEach(r=>CSEL.add(r.key));LS.set('cmp_wfs',[...CSEL]);CRLAST='';cRows()};$('#cnone').onclick=()=>{CSEL.clear();LS.set('cmp_wfs',[]);CRLAST='';cRows()};
  $('#cfast').onclick=()=>{CSEL.clear();CROWS.forEach(r=>{if(!r.var&&((r.avg&&r.avg<60)||(!r.avg&&r.steps&&r.steps<=16)))CSEL.add(r.key)});LS.set('cmp_wfs',[...CSEL]);CRLAST='';cRows()};
  $('#crec').onclick=()=>{CSEL=new Set(['Qwen 2.1 Turbo 改圖','GROK 改圖（INT8 快）'].filter(k=>CROWS.some(r=>r.key===k)));LS.set('cmp_wfs',[...CSEL]);CRLAST='';cRows();toast('選了你定案的 '+CSEL.size+' 個：GROK 改圖（INT8 快）＋Qwen 2.1 Turbo',3500)};
  $('#cdlb').onclick=async()=>{const w=[...new Set(CROWS.filter(r=>CSEL.has(r.key)&&r.miss.length).map(r=>r.wf))];const r=await api('/api/cmp',{a:'dl',wfs:w});toast(r.message||'失敗',4000);cLoadRows()};
  $('#cgo').onclick=cGo;
  $('#cruns').onclick=e=>{const b=e.target.closest('[data-crun]');if(!b)return;CRUN=+b.dataset.crun;LS.set('cmp_run',CRUN);CLAST='';$$('#cruns .pill').forEach(x=>x.classList.toggle('on',x===b));cRun()};
  $('#cmx').onclick=async e=>{const vw=e.target.closest('[data-cvw]');if(vw){LS.set('cmp_view',vw.dataset.cvw);CLAST='';cRun();return}
    const pp=e.target.closest('[data-cpi]');if(pp){LS.set('cmp_pi',+pp.dataset.cpi);CLAST='';cRun();return}
    const s=e.target.closest('[data-cv]');if(s){const k=+s.dataset.k,id=+s.dataset.cv;const cur=$$(`[data-cv="${id}"].on`).length;const v=cur===k?0:k;
      await api('/api/cmp',{a:'vote',id,v});$$(`[data-cv="${id}"]`).forEach(x=>x.classList.toggle('on',+x.dataset.k<=v));CLAST='';setTimeout(cRun,300);return}
    const im=e.target.closest('img[data-big]');if(im)ovOpen(im)};
  cPrev();cLoadRows();cRuns()}

// ---- 電腦瀏覽器：照片可以直接拖進來，或 Ctrl+V 貼上（截圖、複製的圖片）
function imgFilesOf(dt){return [...((dt&&dt.files)||[])].filter(f=>/^image\//.test(f.type))}
function dropAdd(F){if(!F.length)return;if(CUR==='cmp'){CF=CF.concat(F);cPrev()}else if(CUR==='gen'){if((gWf().n_img||0)>1){GFILES=F;GIMGS=[];gPrev()}else gAddFiles(F)}else return;toast(`✔ 加了 ${F.length} 張`)}
addEventListener('dragover',e=>{if(CUR==='gen'||CUR==='cmp'){e.preventDefault();document.body.classList.add('dragon')}});
addEventListener('dragleave',e=>{if(!e.relatedTarget)document.body.classList.remove('dragon')});
addEventListener('drop',e=>{document.body.classList.remove('dragon');if(CUR!=='gen'&&CUR!=='cmp')return;e.preventDefault();dropAdd(imgFilesOf(e.dataTransfer))});
addEventListener('paste',e=>{if(/INPUT|TEXTAREA/.test((e.target.tagName||''))&&!imgFilesOf(e.clipboardData).length)return;const F=imgFilesOf(e.clipboardData).map((f,i)=>new File([f],`貼上_${Date.now()}_${i}.png`,{type:f.type}));if(F.length){e.preventDefault();dropAdd(F)}});
// 比較「逐張看」：左右滑或鍵盤 ← → 換照片（大圖沒打開時）
addEventListener('keydown',e=>{if(CUR!=='cmp'||$('#ov').style.display==='flex'||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName||'')||LS.get('cmp_view','one')!=='one'||!CMX)return;
  if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;const pi=LS.get('cmp_pi',0)+(e.key==='ArrowRight'?1:-1);if(pi<0||pi>=CMX.imgs.length)return;e.preventDefault();LS.set('cmp_pi',pi);CLAST='';cRun()});
{let sx=0,sy=0;addEventListener('touchstart',e=>{const t=e.touches[0];sx=t.clientX;sy=t.clientY},{passive:true});
 addEventListener('touchend',e=>{if(CUR!=='cmp'||!e.target.closest||!e.target.closest('.cone')||$('#ov').style.display==='flex'||!CMX)return;const t=e.changedTouches[0],dx=t.clientX-sx,dy=t.clientY-sy;
   if(Math.abs(dx)<70||Math.abs(dy)>Math.abs(dx)*0.6)return;const pi=LS.get('cmp_pi',0)+(dx<0?1:-1);if(pi<0||pi>=CMX.imgs.length)return;LS.set('cmp_pi',pi);CLAST='';cRun()},{passive:true})}
function gFill(J){LS.set('gprompt',J.prompt||'');if(J.img)gOne(J.img);if(J.imgs&&J.imgs.length>1){GSI=[];J.imgs.forEach((x,i)=>{if(i)GSI[i]=[x]});GSF=[];LS.set('gslots',GSI)}LS.set('gwf',J.wf);
  const P={};const sk=new Set(['_seed']);Object.entries(J.params||{}).forEach(([k,v])=>{if(!sk.has(k))P[k]=v});LS.set('gpar:'+J.wf,P);
  CUR='gen';LS.set('tab','gen');tabs();show();scrollTo(0,0);toast('已填回：照片、提示詞、流程和參數')}
function ovList(){const box=CUR==='hist'?$('#hl'):CUR==='cmp'?$('#cmx'):$('#genv');return box?$$('img[data-big][data-id]',box).filter(x=>!x.closest('details:not([open])')&&!x.closest('.mg')):[]}
let OVCUR=null,CMPP=50;
async function ovStep(k){let L=ovList(),i=OVCUR?L.findIndex(x=>x.dataset.big===OVCUR.dataset.big&&x.dataset.id===OVCUR.dataset.id):-1;
  if(i+k>=L.length&&CUR==='hist'&&HOFF<HTOT){toast('載入更多…');await hLoad(false);L=ovList();i=L.findIndex(x=>x.dataset.big===OVCUR.dataset.big&&x.dataset.id===OVCUR.dataset.id)}
  const n=L[i+k];if(!n)return toast(k>0?'已經是最後一張':'已經是第一張',1500);ovOpen(n,true)}
function ovOpen(im,keep){OVCUR=im;$('#ovi').classList.remove('ovz');$('#cmp').classList.remove('ovz');const L=ovList(),i=L.indexOf(im);$('#ovn').textContent=i>=0&&L.length>1?`${i+1} ／ ${L.length}${CUR==='hist'&&HOFF<HTOT?'+':''}　#${im.dataset.id}`:'';
  $('#ovn2').textContent=i>=0&&L.length>1?`${i+1} ／ ${L.length}${CUR==='hist'&&HOFF<HTOT?'+':''}`:'';$('.ovbot').style.display=L.length>1?'':'none';$('#ovp2').disabled=i<=0;$('#ovnx2').disabled=i<0||(i>=L.length-1&&!(CUR==='hist'&&HOFF<HTOT));
  $('#ovp').style.visibility=$('#ovnx').style.visibility=im.dataset.id&&L.length>1?'visible':'hidden';{
  $('#ovi').src=IMGU(im.dataset.big);$('#ovd').href=U('/api/img',{f:im.dataset.big,dl:1});const r=$('#ovr');r.style.display=im.dataset.id?'':'none';
    const J=(CUR==='cmp'?CJ:GJ.concat(HJ)).find(x=>x.id===+im.dataset.id);const old=J&&J.img&&im.dataset.id?'inputs/'+J.img:'';$('#ovc').style.display=old?'':'none';
    // V0.1.86 🆚 兩個流程對比：同一張照片、同一句提示詞，另一個流程也做好了 → 拉桿左右比 GROK 和 Qwen
    const SB=J&&J.state==='done'&&gOther(J.wf)?GJ.concat(HJ).filter(x=>x.state==='done'&&x.outs&&x.outs.length&&x.wf===gOther(J.wf)[0]&&x.img===J.img&&(x.prompt||'')===(J.prompt||'')).sort((a,b)=>Math.abs(a.id-J.id)-Math.abs(b.id-J.id))[0]:null;
    const ab=$('#ovab'),AB=!!SB&&LS.get('ovab',false);ab.style.display=SB?'':'none';const nm=w=>/^GROK|合併（INT8/.test(w)?'GROK':/^Qwen|合併（Qwen/.test(w)?'Qwen':w.replace(/ 改圖.*/,'').replace(/（.*/,'');
    if(SB)ab.textContent=AB?'↩ 比原圖':`🆚 比 ${nm(SB.wf)}`;
    if(old||AB){$('#cmpa').src=IMGU(AB?SB.outs[0]:old);$('#cmpbi').src=IMGU(im.dataset.big)}$('#cmp .cl').textContent=AB?nm(SB.wf):'舊';$('#cmp .cr').textContent=AB?nm(J.wf):'新';
    ab.onclick=()=>{LS.set('ovab',!AB);if(!AB)LS.set('cmp',true);ovOpen(im,true)};
    const dl=$('#ovdel');dl.style.display=J&&J.id&&J.state==='done'&&CUR!=='cmp'?'':'none';dl.onclick=async()=>{   // V0.2.18 看大圖時直接刪（放回收桶），自動跳下一張
      const L=ovList(),i=L.indexOf(im),nx=L[i+1]||L[i-1];const x=await api('/api/hist_act',{a:'del',ids:[J.id]});if(!x.ok)return toast(x.message||'失敗');
      toast('🗑 放進回收桶了（30 天內可以還原）',1800);[GJ,HJ].forEach(A=>{const k=A.findIndex(y=>y.id===J.id);if(k>=0)A.splice(k,1)});
      $$(`img[data-id="${J.id}"]`).forEach(e=>{const c=e.closest('.gdi')||e;c.remove()});if(nx&&nx!==im&&nx.isConnected)ovOpen(nx);else $('#ovx').click();if(CUR==='hist')hLoad(true);else{GLAST='';gJobs()}};
    // V0.2.39 🎞 改好的圖當「尾幀」：原圖＝開始、這張＝結束，直接帶去首尾幀影片（例如 站著→用 GROK 改成坐著→做成坐下的影片）
    const fl=$('#ovfl'),FLW=GWFS.find(w=>w.name==='H3 首尾幀生影片');fl.style.display=FLW&&old&&J&&J.state==='done'&&!ISV(im.dataset.big)?'':'none';
    fl.onclick=async()=>{const x=await api('/api/gen_act',{a:'reuse',id:J.id,idx:+im.dataset.i||0});if(!x.ok)return toast(x.message||'失敗');
      GIMGS=[J.img];GFILES=[];LS.set('gimgs',GIMGS);GSI=[];GSI[1]=[x.img];GSF=[];LS.set('gslots',GSI);LS.set('gwf','H3 首尾幀生影片');$('#ov').style.display='none';
      if(CUR!=='gen'){CUR='gen';LS.set('tab','gen');tabs();show()}else{$('#gw').value='H3 首尾幀生影片';gWfInfo();gPrev()}scrollTo(0,0);toast('🎞 原圖＝開始、這張＝結束：打一句中間的動作就可以開始',4000)};
    const an=$('#ovan'),VW=GMODES[2][3].find(n=>GWFS.some(w=>w.name===n));an.style.display=VW&&J&&J.state==='done'&&!ISV(im.dataset.big)?'':'none';   // V0.2.42 這張直接動起來
    an.onclick=async()=>{const x=await api('/api/gen_act',{a:'reuse',id:J.id,idx:+im.dataset.i||0});if(!x.ok)return toast(x.message||'失敗');
      GIMGS=[x.img];GFILES=[];LS.set('gimgs',GIMGS);const wn=LS.get('gmode_wf:vid','');LS.set('gwf',GWFS.some(w=>w.name===wn)?wn:VW);$('#ov').style.display='none';
      if(CUR!=='gen'){CUR='gen';LS.set('tab','gen');tabs();show()}else{$('#gw').value=LS.get('gwf');gWfInfo();gPrev()}scrollTo(0,0);toast('🎬 這張放好了：選一個常用動作或打一句，按開始',3500)};
    const sh=$('#ovsh');sh.style.display=navigator.share&&navigator.canShare?'':'none';sh.onclick=async()=>{try{const b=await (await fetch(IMGU(im.dataset.big))).blob(),f=new File([b],(im.dataset.big.split('/').pop()||'image.png'),{type:b.type||'image/png'});
      if(navigator.canShare({files:[f]}))await navigator.share({files:[f]});else toast('這個瀏覽器不能直接分享圖片，用「⬇ 存」',3000)}catch(e){if(e.name!=='AbortError')toast('分享失敗：'+e.message,3000)}};   // V0.2.58 手機直接分享到 LINE 等（https 連線才有）
    const pg=$('#ovpng');pg.style.display=J&&/#00FF00/i.test(J.prompt||'')&&!ISV(im.dataset.big)?'':'none';pg.onclick=()=>gKeyOut(IMGU(im.dataset.big),J.id);   // V0.2.62 去背工具的結果：綠幕去掉存透明 PNG
    {const tb=$('#ovtpl');tb.style.display=J&&J.prompt?'':'none';tb.onclick=async()=>{if(!PKL)await pkLoad();const p=String(J.prompt||'').trim();   // V0.3.53 大圖：提示詞存起來
      const r=await pkAsk('這張的提示詞',p,[['📚 存成範本','g'],['🏷 加進積木的分類'],['取消']],true);if(r.i<0||r.i>1||!r.v.trim())return;const t=r.v.trim();
      if(r.i===0){const r2=await pkAsk('範本的標題',t.slice(0,16),[['💾 存','g'],['取消']]);if(r2.i!==0)return;PKT.docs.unshift({id:pkId(),title:r2.v.trim()||t.slice(0,16),text:t,t:Date.now()/1000});await pkSave();toast('📚 存成範本了',2500);return}
      if(!PKT.cats.length)return toast('還沒有積木分類：先到生圖頁「🏷 積木」按「＋ 新分類」',4000);
      const r3=await pkAsk('加到哪個分類？',null,PKT.cats.map(c=>[c.name]).concat([['取消']]));if(r3.i<0||r3.i>=PKT.cats.length)return;PKT.cats[r3.i].opts.push({id:pkId(),t});await pkSave();toast(`🏷 加進「${PKT.cats[r3.i].name}」了`,2500)}}
    const m3=$('#ovm3');m3.style.display=J&&J.id&&J.state==='done'&&!J.cmp?'':'none';m3.onclick=async()=>{const x=await api('/api/gen_act',{a:'rerun',id:J.id,n:3});toast(x.ok?'🎲 '+x.message:(x.message||'失敗'),3000);if(x.ok&&CUR==='gen')gJobs()};   // V0.2.57
    const pb=$('#ovpair');pb.style.display=(old||AB)?'':'none';pb.onclick=()=>{let X=null;try{const I=JSON.parse(JSON.stringify(J.imgs||[]));if(!AB&&I.length>1)X=I.slice(1).map((n,k)=>[IMGU('inputs/'+n),['圖二','圖三'][k]||'圖'])}catch(e){}ovPair(IMGU(AB?SB.outs[0]:old),IMGU(im.dataset.big),AB?nm(SB.wf):(X?'圖一':'原圖'),AB?nm(J.wf):(X?'結果':'改好'),J.id,X)};
    cmpShow((!!old&&LS.get('cmp',true))||AB,keep);ovStars(J);
    const o=$('#ovo'),OT=J&&J.state==='done'&&!J.cmp?gOther(J.wf):null;o.style.display=OT?'':'none';
    if(OT){o.textContent=OT[1]+' 換 '+(/GROK|INT8/.test(OT[0])?'GROK':'Qwen')+' 做';o.onclick=()=>gOtherGo(J.id,OT[0])}
    const u=$('#ovu');u.style.display='none';   // V0.1.78 放大功能收起來（只留兩個改圖流程）u.onclick=async()=>{const x=await api('/api/gen_act',{a:'upscale',id:+im.dataset.id,idx:+im.dataset.i||0});toast(x.ok?x.message:(x.message||'失敗'),4000)};
    r.onclick=async()=>{const x=await api('/api/gen_act',{a:'reuse',id:+im.dataset.id,idx:+im.dataset.i});if(x.ok){if(GIMGS[0])LS.set('gimg_prev',GIMGS[0]);gOne(x.img);$('#ov').style.display='none';
      if(x.mask)try{const b=await (await fetch(IMGU('inputs/'+x.mask))).blob();b._srv=x.mask;GMASK.set(x.img,b);setTimeout(()=>toast('🖌 帶著同一個局部範圍：可以直接改，或點「🖌 局部 ✔」調整／取消',4000),1600)}catch(e){}
      if(CUR!=='gen'){CUR='gen';LS.set('tab','gen');tabs();show()}else gPrev();scrollTo(0,0);toast('✔ 換成這張了，打新的提示詞再按開始')}else toast(x.message||'失敗')};
    $('#ov').style.display='flex'}}
// 比較頁看大圖：下面顯示是哪個流程、幾秒，直接點星星（或鍵盤 1～5、0 清掉）打分數，左右滑下一張接著打
// V0.1.94 🖼 存前後對比圖：左右兩張一樣高拼成一張（下面寫標籤），存到手機可以直接傳給別人
async function ovPair(a,b,la,lb,id,extra){toast('拼圖中…',8000);const ld=u=>new Promise((ok,no)=>{const i=new Image();i.onload=()=>ok(i);i.onerror=no;i.src=u});   // V0.2.55 可以拼三張（合併：人物＋衣服＝結果）
  try{const P=[[a,la]].concat(extra||[]).concat([[b,lb]]);const I=await Promise.all(P.map(x=>ld(x[0])));const H=Math.min(1600,Math.max(...I.map(x=>x.naturalHeight))),W=I.map(x=>Math.round(x.naturalWidth*H/x.naturalHeight)),gap=Math.round(H*.015),lab=Math.round(H*.07);
    const c=document.createElement('canvas');c.width=W.reduce((s,x)=>s+x,0)+gap*(I.length+1);c.height=H+gap*2+lab;const g=c.getContext('2d');g.fillStyle='#111';g.fillRect(0,0,c.width,c.height);
    g.font=`bold ${Math.round(lab*.5)}px system-ui,sans-serif`;g.textAlign='center';g.textBaseline='middle';let x=gap;
    I.forEach((im,k)=>{g.drawImage(im,x,gap,W[k],H);g.fillStyle='#fff';g.fillText(P[k][1],x+W[k]/2,gap+H+lab/2);if(k<I.length-1&&I.length>2){g.fillStyle='#aaa';g.fillText(k===I.length-2?'＝':'＋',x+W[k]+gap/2,gap+H/2)}x+=W[k]+gap});
    c.toBlob(bl=>{const u=URL.createObjectURL(bl),y=document.createElement('a');y.href=u;y.download=`前後對比_${id||''}.jpg`;document.body.appendChild(y);y.click();y.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);toast('✔ 存好了（在下載資料夾）',3000)},'image/jpeg',0.9)}
  catch(e){toast('拼不起來：'+e,4000)}}
function ovStars(J){const b=$('#ovs');if(!b)return;if(!J||!J.id||(J.state&&J.state!=='done')){b.innerHTML='';return}
  b.innerHTML=(J.prompt?`<div class="ovpt" data-ovpt="1" title="點一下：填進提示詞">${J.mask?'🖌 ':''}${J.ref?'📎 ':''}${esc(J.prompt)}</div>`:'')+`<div class="ovsb"><b>${esc(J.cmp_col||J.wf)}</b>${J.run_s?` · ${Math.round(J.run_s)} 秒`:''}<span class="cstar">${[1,2,3,4,5].map(k=>`<i data-ok="${k}" class="${J.vote>=k?'on':''}">★</i>`).join('')}</span></div>`;
  b.onclick=e=>{if(e.target.closest('[data-ovpt]')){LS.set('gprompt',J.prompt);const g=$('#gp');if(g)g.value=J.prompt;try{navigator.clipboard&&navigator.clipboard.writeText(J.prompt)}catch(_){}toast('✔ 這句填進提示詞了（也複製了）',2000);return}   // V0.3.01
    const x=e.target.closest('[data-ok]');if(x)ovVote(J,+x.dataset.ok===J.vote?0:+x.dataset.ok)}}
async function ovVote(J,v){await api('/api/cmp',{a:'vote',id:J.id,v});J.vote=v;ovStars(J);CLAST='';toast(v?'★'.repeat(v):'清掉分數',900)}
addEventListener('keydown',e=>{if($('#ov').style.display!=='flex'||!OVCUR||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName||''))return;if(!/^[0-5]$/.test(e.key))return;
  const J=(CUR==='cmp'?CJ:GJ.concat(HJ)).find(x=>x.id===+OVCUR.dataset.id);if(J){e.preventDefault();ovVote(J,+e.key)}});
async function gClick(e){{const fx=e.target.closest('[data-gexp]');if(fx&&!e.target.closest('button')){GEXP.add(+fx.dataset.gexp);GLAST='';gJobs();return}}const im=e.target.closest('img[data-big]');
  if(im){ovOpen(im);return}
  const b=e.target.closest('[data-g]');if(!b)return;const a=b.dataset.g,id=+b.dataset.id;
  if(a==='fill'){const J=GJ.concat(HJ).find(x=>x.id===id);if(J)gFill(J);return}
  if(a==='gohist'){CUR='hist';LS.set('tab','hist');tabs();show();scrollTo(0,0);return}   // V0.3.65 ✨剛做好 → 看全部
  if(a==='bench'){if(!confirm('用這張圖和提示詞，排一組速度測試？\n（GROK 改圖（INT8 快）、Qwen 2.1 Turbo 各跑一張比速度和畫質；同一個種子，每個模型先暖機一張；大約 5～10 分鐘）'))return;const r=await api(U('/api/bench',{id}),{});toast(r.message||'失敗',7000);return}
  if(a==='tocmp'){const J=GJ.concat(HJ).find(x=>x.id===id);if(!J)return;CI=[J.img];CF=[];LS.set('cmp_imgs',CI);LS.set('cmp_prompt',J.prompt||'');CUR='cmp';LS.set('tab','cmp');tabs();show();scrollTo(0,0);toast('已經把照片和提示詞帶過去了：勾想比的模型，按「開始比較」',3500);return}
  if(a==='vgif'){toast('轉 GIF 中（電腦上用 ffmpeg，幾秒鐘）…',30000);const x=await api('/api/gen_act',{a:'gif',id,f:b.dataset.v});if(!x.ok)return toast(x.message||'失敗',5000);
    const l=document.createElement('a');l.href=U('/api/img',{f:x.file,dl:1});l.download='';document.body.appendChild(l);l.click();l.remove();toast('✔ GIF 好了（在下載資料夾）',3000);return}   // V0.2.92
  if(a==='vnext'||a==='vlast'){toast('取最後一格中…',8000);try{const blob=await vLastFrame(IMGU(b.dataset.v));const r=await api('/api/gen_upload',await blob.arrayBuffer(),true);if(!r.ok)return toast(r.message||'失敗');
      GIMGS=[r.img];GFILES=[];LS.set('gimgs',GIMGS);
      if(a==='vnext'){const J=GJ.concat(HJ).find(x=>x.id===id),wn=J&&gModeOf(J.wf)==='vid'?J.wf:(GMODES[2][3].find(n=>GWFS.some(w=>w.name===n))||'');if(wn){LS.set('gwf',wn)}toast('⏭ 最後一格當開始畫面了：打下一段的動作，按開始',4000)}
      else{const ed=GMODES[0][3].find(n=>GWFS.some(w=>w.name===n));if(ed)LS.set('gwf',ed);toast('🖼 最後一格放進照片了，可以拿去改圖',3000)}
      if(CUR!=='gen'){CUR='gen';LS.set('tab','gen');tabs();show()}else{$('#gw').value=LS.get('gwf','');gWfInfo();gPrev()}scrollTo(0,0)}catch(e){toast('取不到最後一格：'+e,5000)}return}
  if(a==='other'){const J=GJ.concat(HJ).find(x=>x.id===id),OT=J&&gOther(J.wf);if(OT)gOtherGo(id,OT[0]);return}
  if(a==='interp'){const x=await api('/api/gen_act',{a:'interp',id,idx:+b.dataset.i||0});toast(x.ok?x.message:(x.message||'失敗'),4000);return}
  if(a==='cancelb'){gCancelMany(id);return}
  if(a==='restart'){const r=await api('/api/gen_act',{a:'restart',id});toast(r.message||'',4000);setTimeout(gJobs,1500);return}
  if(a==='cancel'&&!confirm('取消 #'+id+'？'))return;const r=await api('/api/gen_act',{a,id});toast(r.ok?'好了':(r.message||'失敗'));if(CUR==='gen')gJobs();else hLoad(true)}
// ---- ⇆ 對比：舊的（左）和新的（右）疊在一起，中間拉桿左右拉
function cmpShow(on,keep){$('#cmp').style.display=on?'block':'none';$('#ovi').style.display=on?'none':'';$('#ovc').textContent=on?'🖼 單張':'⇆ 對比';if(on){cmpFit();cmpSet(keep?CMPP:50)}}
function cmpFit(){const i=$('#cmpbi'),c=$('#cmp');const go=()=>{const w=i.naturalWidth||1,h=i.naturalHeight||1,mw=innerWidth*0.8,mh=innerHeight*0.78,k=Math.min(mw/w,mh/h);c.style.width=Math.round(w*k)+'px';c.style.height=Math.round(h*k)+'px'};
  if(i.complete&&i.naturalWidth)go();else i.onload=go}
function cmpSet(p){p=Math.max(0,Math.min(100,p));CMPP=p;$('#cmpb').style.clipPath=`inset(0 0 0 ${p}%)`;$('#cmpl').style.left=p+'%'}
(()=>{const c=$('#cmp');let drag=false;const at=e=>{const r=c.getBoundingClientRect();cmpSet((e.clientX-r.left)/r.width*100)};
  c.addEventListener('pointerdown',e=>{drag=true;c.setPointerCapture(e.pointerId);at(e)});c.addEventListener('pointermove',e=>{if(drag)at(e)});
  c.addEventListener('pointerup',()=>drag=false);c.addEventListener('pointercancel',()=>drag=false)})();
$('#ovc').onclick=()=>{const on=$('#cmp').style.display!=='block';LS.set('cmp',on);cmpShow(on)};
addEventListener('resize',()=>{if($('#cmp').style.display==='block')cmpFit()});
$('#ovx').onclick=()=>{$('#ov').style.display='none';if(CUR==='cmp')cRun()};
$('#ovp').onclick=e=>{e.stopPropagation();ovStep(-1)};$('#ovnx').onclick=e=>{e.stopPropagation();ovStep(1)};
$('#ovp2').onclick=e=>{e.stopPropagation();ovStep(-1)};$('#ovnx2').onclick=e=>{e.stopPropagation();ovStep(1)};
addEventListener('keydown',e=>{if($('#ov').style.display!=='flex'||/INPUT|TEXTAREA|SELECT/.test((e.target.tagName||'')))return;
  if(e.key==='ArrowLeft'){e.preventDefault();ovStep(-1)}else if(e.key==='ArrowRight'){e.preventDefault();ovStep(1)}else if(e.key==='Escape')$('#ov').style.display='none'});
(()=>{let x0=null,y0=0;const ov=$('#ov');ov.addEventListener('touchstart',e=>{if(e.target.closest('#cmp,button,a'))return x0=null;x0=e.touches[0].clientX;y0=e.touches[0].clientY},{passive:true});
  ov.addEventListener('touchend',e=>{if(x0===null)return;const dx=e.changedTouches[0].clientX-x0,dy=e.changedTouches[0].clientY-y0;x0=null;if(Math.abs(dx)>60&&Math.abs(dx)>Math.abs(dy)*1.5)ovStep(dx<0?1:-1);else if(dy>110&&Math.abs(dy)>Math.abs(dx)*1.5)$('#ovx').click()},{passive:true})})();   // V0.2.11 往下滑＝關掉（單手）
// V0.2.28 看大圖時點兩下：在點的地方放大 2.5 倍看細節（臉、手指、文字），再點兩下還原
(()=>{let lt=0;const zt=(el,x,y)=>{const r=el.getBoundingClientRect();if(el.classList.toggle('ovz')){el.style.transformOrigin=`${((x-r.left)/r.width*100).toFixed(1)}% ${((y-r.top)/r.height*100).toFixed(1)}%`}};
  ['#ovi','#cmp'].forEach(q=>{const el=$(q);if(!el)return;el.addEventListener('dblclick',e=>zt(el,e.clientX,e.clientY));
    el.addEventListener('touchend',e=>{const n=Date.now();if(n-lt<300&&e.changedTouches[0]){e.preventDefault();zt(el,e.changedTouches[0].clientX,e.changedTouches[0].clientY);lt=0}else lt=n},{passive:false})})})();

// ================= ▦ 合併（照 TikLive「截圖全覽」）：列×欄（剛好排滿的組合，也可以 1×N、N×1）、⇄ 對調、下面拉桿上下拖＝改每格比例（不是固定 9:16／16:9）、
// ▲▼ 每格裁切位置、⚙ 版面（每格下面顯示、間距可以負數重疊、誰疊誰）、⬇ 照畫面上的排版用原圖大小合成一張。每一組各自記住（這台手機）
const MGD={fy:0,gap:2,lab:'n',zh:'r',zv:'d',h:0,lay:null,opt:0};
function mgSt(b){return Object.assign({},MGD,LS.get('mg:'+b,{}))}
function mgSave(b,S){const o=Object.assign({},S);delete o.opt;LS.set('mg:'+b,o)}
function mgPairs(N){const P=[];for(let c=1;c<=N;c++){const r=Math.ceil(N/c);if(r*c===N)P.push([r,c])}
  if(P.length<=2&&N>3)for(let c=2;c<N;c++){const r=Math.ceil(N/c);if(r*c!==N&&r*c-N<c&&!P.some(p=>p[0]===r&&p[1]===c))P.push([r,c])}return P.sort((a,b)=>a[0]-b[0])}
function mgDefLay(N){const P=mgPairs(N),c0=Math.ceil(Math.sqrt(N));return P.reduce((a,x)=>Math.abs(x[1]-c0)<Math.abs(a[1]-c0)?x:a,P[0])}
function mgItems(b){return HJ.filter(x=>x.batch===b).sort((a,c)=>a.id-c.id).flatMap(x=>(x.outs||[]).filter(o=>!ISV(o)).map((o,i)=>({o,id:x.id,i,img:x.img})))}
function mgZ(S,c,r){return 1+(S.zv==='d'?r:500-r)*200+(S.zh==='r'?c:199-c)}
function mgVis(S,c,r,C,R,cw,th,gp){const x=c*(cw+gp),y=r*(th+gp);let vx=x,vw=cw,vy=y,vh=th;
  if(gp<0){if(S.zh==='r'){if(c<C-1)vw=cw+gp}else if(c>0){vx=x-gp;vw=cw+gp}if(S.zv==='d'){if(r<R-1)vh=th+gp}else if(r>0){vy=y-gp;vh=th+gp}}return {x:vx,y:vy,w:Math.max(8,vw),h:Math.max(8,vh)}}
function mgLabTxt(S,it,k){if(S.lab==='x')return '';if(S.lab==='f'){const m=/_f(\d{4,})\.\w+$/.exec(it.img||'');return m?'第 '+(+m[1])+' 格':'#'+it.id}return String(k+1)}
function mgMount(box){if(!box)return;const b=+box.dataset.b,I=mgItems(b),N=I.length;if(N<2){box.remove();return}const S=mgSt(b);if(!S.lay||!mgPairs(N).some(p=>p[0]===S.lay[0]&&p[1]===S.lay[1]))S.lay=mgDefLay(N);
  if(S.lab==='n'&&!LS.get('mg:'+b,null)&&I.some(x=>/_f\d{4,}\./.test(x.img||'')))S.lab='f';box._S=S;box._I=I;
  box.innerHTML=`<div class="mgH"><b>▦ 合併</b><span class="mu mgInf"></span></div><div class="mgPg"><div class="mgGrid">${I.map((x,k)=>`<div class="mgG" data-k="${k}"><img src="${IMGU(x.o)}" loading="lazy"></div>`).join('')}</div></div>
   <div class="mgGrip" title="上下拖：改每格的比例（點兩下恢復原圖比例）"><i></i></div>
   <div class="mgTool"><span class="mgFy" title="每一格的裁切位置一起往上／往下（▲▼ 一次 5、▴▾ 一次 1）"><button data-m="up">▲</button><button data-m="up1">▴</button><em class="mgFyV"></em><button data-m="dn1">▾</button><button data-m="dn">▼</button></span>
   <button class="pill" data-m="swap" title="欄列對調">⇄</button><button class="pill" data-m="opt">⚙ 版面</button><span class="grow"></span><button class="pill acc" data-m="dl">⬇ 下載合併圖</button></div>
   <div class="mgLy"></div><div class="mgOpt" hidden></div>`;
  box.onclick=e=>mgClick(box,e);mgGrip(box);mgDraw(box);
  const im=box.querySelector('.mgG img');if(im&&!im.complete)im.addEventListener('load',()=>mgFit(box),{once:true});
  try{box._ro&&box._ro.disconnect();box._ro=new ResizeObserver(()=>mgFit(box));box._ro.observe(box.querySelector('.mgPg'))}catch(e){}}
function mgDraw(box){const S=box._S,N=box._I.length;
  box.querySelector('.mgLy').innerHTML='<span class="mu" style="align-self:center">排列（列×欄）</span>'+mgPairs(N).map(([r,c])=>`<button class="pill ${S.lay[0]===r&&S.lay[1]===c?'on':''}" data-ly="${r}x${c}">${r}×${c}${r*c>N?`（空 ${r*c-N}）`:''}</button>`).join('');
  const sg=(k,L)=>`<span class="seg2">${L.map(([v,t])=>`<button class="pill ${String(S[k])===String(v)?'on':''}" data-k="${k}" data-v="${v}">${t}</button>`).join('')}</span>`,hasF=box._I.some(x=>/_f\d{4,}\./.test(x.img||''));
  const o=box.querySelector('.mgOpt');o.hidden=!S.opt;o.innerHTML=`<div class="r"><b>每格下面</b>${sg('lab',[['n','編號'],...(hasF?[['f','第幾格']]:[]),['x','不顯示']])}</div>
   <div class="r"><b>間距</b><button class="pill" data-g="-5">−5</button><button class="pill" data-g="-1">−1</button><em style="font-style:normal;min-width:26px;text-align:center">${S.gap}</em><button class="pill" data-g="1">＋1</button><button class="pill" data-g="5">＋5</button><button class="pill" data-g="0r">預設</button><span class="mu">負數＝圖跟圖疊在一起</span></div>
   <div class="r"><b>左右疊</b>${sg('zh',[['r','右搭左'],['l','左搭右']])}</div><div class="r"><b>上下疊</b>${sg('zv',[['d','下搭上'],['u','上搭下']])}</div>`;
  box.querySelector('.mgFyV').textContent=(S.fy>0?'+':'')+S.fy;mgFit(box)}
// 排位置（照 TK snFit）：寬度填滿；高度＝拉桿拉的（每格比例跟著變），沒拉過＝原圖比例
function mgFit(box){const S=box._S,I=box._I,N=I.length,pg=box.querySelector('.mgPg'),g=box.querySelector('.mgGrid');if(!pg||!g)return;
  const C=Math.max(1,S.lay[1]),R=Math.max(1,Math.ceil(N/C)),gp=+S.gap||0,W=pg.clientWidth||300,cw=Math.max(8,(W-(C-1)*gp)/C);
  const im=box.querySelector('.mgG img'),nr=im&&im.naturalWidth?im.naturalHeight/im.naturalWidth:1;let th=cw*nr;
  if(S.h>0)th=Math.max(12,(S.h*W-(R-1)*gp)/R);box._cw=cw;box._th=th;
  const T=g.querySelectorAll('.mgG');T.forEach((el,i)=>{const c=i%C,r=Math.floor(i/C);el.style.left=c*(cw+gp)+'px';el.style.top=r*(th+gp)+'px';el.style.width=cw+'px';el.style.height=th+'px';el.style.zIndex=mgZ(S,c,r)});
  g.querySelectorAll('.mgLb').forEach(x=>x.remove());if(S.lab!=='x')I.forEach((it,i)=>{const c=i%C,r=Math.floor(i/C),v=mgVis(S,c,r,C,R,cw,th,gp),l=document.createElement('b');l.className='mgLb';l.textContent=mgLabTxt(S,it,i);l.style.left=(v.x+3)+'px';l.style.top=(v.y+v.h-3)+'px';g.appendChild(l)});
  const H=R*th+(R-1)*gp;g.style.width=W+'px';g.style.height=Math.max(0,H)+'px';pg.style.height=Math.max(0,H)+'px';g.style.setProperty('--mgfy',(50-S.fy)+'%');
  box.querySelector('.mgInf').textContent=`${N} 張 · ${R}×${C} · 每格 ${(cw/th>=1?(cw/th).toFixed(2)+'：1':'1：'+(th/cw).toFixed(2))}${S.h>0?'（拉過）':'（原圖比例）'}`}
function mgGrip(box){const gr=box.querySelector('.mgGrip'),pg=box.querySelector('.mgPg');let d=null;
  gr.onpointerdown=e=>{gr.setPointerCapture(e.pointerId);d={y:e.clientY,h:pg.getBoundingClientRect().height};gr.classList.add('on');e.preventDefault();e.stopPropagation()};
  gr.onpointermove=e=>{if(!d)return;const W=pg.clientWidth||300,h=Math.max(40,Math.min(W*6,d.h+e.clientY-d.y));box._S.h=h/W;mgFit(box)};
  gr.onpointerup=gr.onpointercancel=()=>{gr.classList.remove('on');if(d)mgSave(+box.dataset.b,box._S);d=null};
  gr.ondblclick=()=>{box._S.h=0;mgSave(+box.dataset.b,box._S);mgFit(box)}}
function mgClick(box,e){e.stopPropagation();const S=box._S,b=+box.dataset.b,x=e.target.closest('button,[data-k].mgG,.mgG');if(!x)return;
  if(x.classList.contains('mgG')){const it=box._I[+x.dataset.k],gd=box.closest('details.hgrp');const im=gd&&[...gd.querySelectorAll('.job img[data-big]')].find(y=>y.dataset.big===it.o);if(im)ovOpen(im);return}
  const m=x.dataset.m;if(m){if(m==='dl')return mgMerge(box);if(m==='swap')S.lay=[S.lay[1],S.lay[0]];else if(m==='opt')S.opt=!S.opt;else S.fy=Math.max(-50,Math.min(50,S.fy+({up:5,dn:-5,up1:1,dn1:-1})[m]));
    if(m==='swap'&&!mgPairs(box._I.length).some(p=>p[0]===S.lay[0]&&p[1]===S.lay[1]))S.lay=[S.lay[1],S.lay[0]];mgSave(b,S);mgDraw(box);return}
  if(x.dataset.ly){S.lay=x.dataset.ly.split('x').map(Number);mgSave(b,S);mgDraw(box);return}
  if(x.dataset.g){S.gap=x.dataset.g==='0r'?2:Math.max(-80,Math.min(40,S.gap+ +x.dataset.g));mgSave(b,S);mgDraw(box);return}
  if(x.dataset.k){S[x.dataset.k]=x.dataset.v;mgSave(b,S);mgDraw(box)}}
// ⬇ 合成一張（照 TK snMerge）：原圖大小、跟畫面上一樣的比例、間距、誰疊誰、▲▼、編號
async function mgMerge(box){const S=box._S,I=box._I,N=I.length,C=Math.max(1,S.lay[1]),R=Math.ceil(N/C),ratio=(box._th||1)/(box._cw||1);toast('合成中…',20000);
  const imgs=await Promise.all(I.map(x=>new Promise(res=>{const im=new Image();im.onload=()=>res(im);im.onerror=()=>res(null);im.src=IMGU(x.o)})));
  const nat=imgs.find(Boolean);if(!nat)return toast('✖ 讀不到圖');let tw=nat.naturalWidth||1024,k=tw/(box._cw||1),gs=(+S.gap||0)*k,th=Math.round(tw*ratio);
  let CW=C*tw+(C-1)*gs,CH=R*th+(R-1)*gs;const f=Math.min(1,16000/Math.max(CW,CH),Math.sqrt(120e6/(CW*CH)));if(f<1){tw*=f;th*=f;gs*=f;CW*=f;CH*=f}
  const cv=document.createElement('canvas');cv.width=Math.max(1,Math.round(CW));cv.height=Math.max(1,Math.round(CH));const g=cv.getContext('2d');g.fillStyle='#000';g.fillRect(0,0,cv.width,cv.height);
  imgs.map((im,i)=>({im,i,c:i%C,r:Math.floor(i/C)})).sort((a,b)=>mgZ(S,a.c,a.r)-mgZ(S,b.c,b.r)).forEach(({im,c,r})=>{if(!im)return;const x=c*(tw+gs),y=r*(th+gs),s=Math.max(tw/im.naturalWidth,th/im.naturalHeight),dw=im.naturalWidth*s,dh=im.naturalHeight*s;
    g.save();g.beginPath();g.rect(x,y,tw,th);g.clip();g.drawImage(im,x+(tw-dw)/2,y+(th-dh)*(50-S.fy)/100,dw,dh);g.restore()});
  if(S.lab!=='x')I.forEach((it,i)=>{const c=i%C,r=Math.floor(i/C),v=mgVis(S,c,r,C,R,tw,th,gs),tx=mgLabTxt(S,it,i),fs=Math.max(14,Math.round(Math.min(tw,th)*0.06));g.font=`700 ${fs}px system-ui,sans-serif`;
    const mw=g.measureText(tx).width+fs*0.8,bx=v.x+fs*0.3,by=v.y+v.h-fs*1.6;g.fillStyle='rgba(0,0,0,.55)';g.fillRect(bx,by,mw,fs*1.3);g.fillStyle='#fff';g.textBaseline='middle';g.fillText(tx,bx+fs*0.4,by+fs*0.65)});
  cv.toBlob(bl=>{if(!bl)return toast('✖ 合成失敗（圖太大）');const a=document.createElement('a');a.href=URL.createObjectURL(bl);a.download=`批量_${I[0].id}_${R}x${C}.jpg`;document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove()},4000);toast(`✔ 已合成 ${R}×${C}（${cv.width}×${cv.height}）`,3500)},'image/jpeg',0.92)}

// ================= 🎞 從影片挑格：在手機上直接播（不用先上傳整支影片），拉時間軸／±1 ±10 找格，選好的格子截成 JPG 加到照片
let FP=null;
function fpOpen(file){const v=$('#fpv');if(FP&&FP.url)URL.revokeObjectURL(FP.url);FP={file,url:URL.createObjectURL(file),fps:30,n:0,N:1,sel:[],busy:null,auto:false};
  $('#fpi').textContent=`${file.name} · ${fmtB(file.size)} · 讀取中…`;$('#fpsel').innerHTML='';fpOkBtn();$('#fpk').style.display='flex';v.src=FP.url;
  v.onloadedmetadata=async()=>{FP.fps=await fpDetect(v);FP.auto=FP.fps>0;if(!FP.fps)FP.fps=30;fpFpsSel();fpRange();fpGo(0)};
  v.onerror=()=>toast('這支影片手機瀏覽器播不了（可能是格式不支援），可以改在電腦版挑格',6000)}
// 每秒幾格：瀏覽器不直接說，播一小段看相鄰兩格差多少秒（requestVideoFrameCallback）
function fpDetect(v){return new Promise(res=>{if(!('requestVideoFrameCallback' in HTMLVideoElement.prototype))return res(0);const T=[];let done=false;
  const fin=()=>{if(done)return;done=true;v.pause();const D=[];for(let i=1;i<T.length;i++){const d=T[i]-T[i-1];if(d>0.001&&d<0.2)D.push(d)}if(!D.length)return res(0);D.sort((a,b)=>a-b);const f=1/D[0];
    const C=[23.976,24,25,29.97,30,48,50,59.94,60,90,120];res(C.reduce((a,b)=>Math.abs(b-f)<Math.abs(a-f)?b:a))};
  const cb=(_n,m)=>{T.push(m.mediaTime);if(T.length>=14)fin();else v.requestVideoFrameCallback(cb)};v.requestVideoFrameCallback(cb);v.muted=true;v.play().catch(()=>fin());setTimeout(fin,2500)})}
function fpFpsSel(){const C=[23.976,24,25,29.97,30,50,59.94,60,120];if(!C.includes(FP.fps))C.push(FP.fps);
  $('#fpfps').innerHTML=C.map(x=>`<option value="${x}" ${x===FP.fps?'selected':''}>${x}</option>`).join('');$('#fpfn').textContent=FP.auto?'（自動偵測）':'（偵測不到，先當 30；不對可以改）';
  $('#fpfps').onchange=()=>{const t=(FP.n+0.5)/FP.fps;FP.fps=+$('#fpfps').value;FP.auto=false;$('#fpfn').textContent='（手動）';fpRange();fpGo(Math.floor(t*FP.fps))}}
function fpRange(){const v=$('#fpv');FP.N=Math.max(1,Math.round((v.duration||0)*FP.fps));$('#fpr').max=FP.N-1;
  $('#fpi').textContent=`${FP.file.name} · ${fmtB(FP.file.size)} · 共 ${FP.N} 格 · ${(v.duration||0).toFixed(1)} 秒 · ${v.videoWidth}×${v.videoHeight}`}
// 跳到第 n 格：拖很快時只跳最後一個位置（等上一個跳完再跳）
function fpGo(n){n=Math.max(0,Math.min(FP.N-1,Math.round(n)));FP.n=n;$('#fpr').value=n;$('#fpn').textContent=n;const t=(n+0.5)/FP.fps;
  $('#fpt').textContent=`${Math.floor(t/60)}:${(t%60).toFixed(2).padStart(5,'0')} ／ 共 ${FP.N} 格`;$$('#fpsel .fc').forEach(x=>x.classList.toggle('cur',+x.dataset.n===n));
  const v=$('#fpv');FP.want=n;if(FP.busy)return FP.busy;
  return FP.busy=new Promise(res=>{const step=()=>{const w=FP.want;v.onseeked=()=>{if(FP.want!==w)step();else{FP.busy=null;res(w)}};v.pause();v.currentTime=(w+0.5)/FP.fps};step()})}
async function fpAdd(){if(FP.busy)await FP.busy;const n=FP.n;if(FP.sel.some(x=>x.n===n))return toast(`第 ${n} 格已經選了`);
  const v=$('#fpv'),c=document.createElement('canvas');c.width=v.videoWidth;c.height=v.videoHeight;c.getContext('2d').drawImage(v,0,0,c.width,c.height);
  const blob=await new Promise(r=>c.toBlob(r,'image/jpeg',0.93));if(!blob)return toast('這一格截不到');
  FP.sel.push({n,blob,u:URL.createObjectURL(blob)});FP.sel.sort((a,b)=>a.n-b.n);fpSelDraw();toast(`✔ 選了第 ${n} 格（共 ${FP.sel.length} 格）`,1200)}
function fpSelDraw(){$('#fpsel').innerHTML=FP.sel.map(x=>`<div class="fc ${x.n===FP.n?'cur':''}" data-n="${x.n}"><img src="${x.u}"><i data-x="${x.n}">✕</i>${x.n}</div>`).join('')||'<span class="mu">還沒選</span>';fpOkBtn()}
function fpOkBtn(){const n=FP?FP.sel.length:0;const b=$('#fpok');b.disabled=!n;b.textContent=n?`✔ 加到照片（${n} 張）`:'✔ 加到照片'}
function fpClose(){$('#fpk').style.display='none';const v=$('#fpv');v.pause();v.removeAttribute('src');v.load();if(FP&&FP.url)URL.revokeObjectURL(FP.url)}
$('#fpr').oninput=()=>fpGo(+$('#fpr').value);
$('#fpk').querySelector('.fpb').onclick=e=>{const b=e.target.closest('[data-d]');if(b&&FP)fpGo(FP.n+ +b.dataset.d)};
$('#fpadd').onclick=fpAdd;$('#fpx').onclick=()=>{if(FP&&FP.sel.length&&!confirm('已選的格子不要了？'))return;fpClose()};
$('#fpsel').onclick=e=>{const x=e.target.closest('[data-x]');if(x){FP.sel=FP.sel.filter(s=>s.n!==+x.dataset.x);fpSelDraw();return}const c=e.target.closest('[data-n]');if(c)fpGo(+c.dataset.n)};
$('#fpok').onclick=()=>{if(!FP||!FP.sel.length)return;const base=FP.file.name.replace(/\.[^.]+$/,'');
  const F=FP.sel.map(x=>{const f=new File([x.blob],`${base}_f${String(x.n).padStart(4,'0')}.jpg`,{type:'image/jpeg'});f._tag='f'+String(x.n).padStart(4,'0');return f});
  if(CUR==='cmp'){CF=CF.concat(F);const k=F.length;fpClose();cPrev();return toast(`✔ 加了 ${k} 張`)}
  GFILES=GFILES.concat(F);const k=F.length;fpClose();gPrev();toast(`✔ 加了 ${k} 張（第 ${FP.sel.map(x=>x.n).join('、')} 格），現在共 ${GIMGS.length+GFILES.length} 張`,3500)};
addEventListener('keydown',e=>{if(!FP||$('#fpk').style.display!=='flex'||/INPUT|TEXTAREA|SELECT/.test(e.target.tagName||'')&&e.target.id!=='fpr')return;
  if(e.key==='ArrowLeft'||e.key==='ArrowRight'){e.preventDefault();fpGo(FP.n+(e.key==='ArrowLeft'?-1:1)*(e.shiftKey?10:1))}else if(e.key==='Enter'){e.preventDefault();fpAdd()}});$('#ov').onclick=e=>{if(e.target.id==='ov')$('#ov').style.display='none'};

// ================= 📜 歷史：全部跑過的（搜尋、篩選、照日期收摺、精簡模式、隱藏、刪除到回收桶、一次選很多筆）
let HJ=[],HOFF=0,HTOT=0,HVIEW=LS.get('hview',''),HSEL=null;
const hBtns=v=>v==='trash'?'<button class="pill" data-h="restore">↩ 還原</button><button class="pill er" data-h="purge">永久刪除</button>'
  :(v==='hidden'?'<button class="pill" data-h="unhide">👁 取消隱藏</button>':'<button class="pill" data-h="hide">🙈 隱藏</button>')+'<button class="pill er" data-h="del">🗑 刪除</button>';
const HACT={hide:'隱藏',unhide:'取消隱藏',del:'刪除（放進回收桶，30 天內可以還原）',restore:'還原',purge:'永久刪除（檔案真的刪掉，不能還原）'};
const hDay=t=>{const d=new Date(t*1000);return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')};
function hRender(){const shut=LS.get('hshut',{}),G=[];HJ.forEach(x=>{const k=hDay(x.t);let g=G.find(y=>y.k===k);if(!g)G.push(g={k,L:[]});g.L.push(x)});
  const today=hDay(Date.now()/1000),wk=['日','一','二','三','四','五','六'];
  $('#hl').innerHTML=G.map(g=>{const d=new Date(g.k+'T00:00:00');const nm=g.k===today?'今天':`${d.getMonth()+1}/${d.getDate()}（${wk[d.getDay()]}）`;
    return `<details class="hday" data-day="${g.k}" ${shut[g.k]?'':'open'}><summary><b>${nm}</b> <span class="mu">${hUnits(g.L).length} 筆</span></summary><div class="hdg">${hUnits(g.L).map(u=>u.length>1?hGroup(u):gCard(u[0],HVIEW||true)).join('')}</div></details>`}).join('')
    ||`<div class="mu" style="padding:10px 0">${HVIEW==='trash'?'回收桶是空的':HVIEW==='hidden'?'沒有隱藏的紀錄':'沒有符合的紀錄'}</div>`;
  $$('#hl details.hday').forEach(d=>d.ontoggle=()=>{const o=LS.get('hshut',{});if(d.open)delete o[d.dataset.day];else o[d.dataset.day]=1;LS.set('hshut',o)});
  $$('#hl details.hgrp').forEach(d=>{d.ontoggle=()=>{const o=LS.get('hgopen',{});if(d.open){o[d.dataset.b]=1;mgMount(d.querySelector('.mg'))}else delete o[d.dataset.b];LS.set('hgopen',o)};if(d.open)mgMount(d.querySelector('.mg'))});hSelBar()}
// 同一批（一次送出的批量照片、影片挑的好幾格）→ 一組：預設收起來；點開第一個是「合併」（照 TikLive 截圖全覽），下面是每一張
function hUnits(L){const U=[],M={};L.forEach(x=>{if(x.batch>0&&HVIEW!=='star'){if(M[x.batch])return M[x.batch].push(x);M[x.batch]=[x];U.push(M[x.batch])}else U.push([x])});
  U.forEach(u=>u.sort((a,b)=>a.id-b.id));return U}
function hGroup(u){const b=u[0].batch,open=LS.get('hgopen',{})[b],ok=u.filter(x=>x.state==='done').length,bad=u.filter(x=>x.state==='fail').length,run=u.filter(x=>x.state==='run'||x.state==='wait').length;
  const O=u.flatMap(x=>(x.outs||[]).filter(o=>!ISV(o))),ids=u.map(x=>x.id).join(','),sel=HSEL&&u.every(x=>HSEL.has(x.id));
  const tm=new Date(u[0].t*1000).toLocaleString('zh-TW',{month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
  return `<details class="hgrp" data-b="${b}" ${open?'open':''}><summary><div class="gT">${HSEL?`<input type="checkbox" class="hck" data-gck="${ids}" ${sel?'checked':''}>`:''}<b>${new Set(u.map(x=>x.wf)).size>1&&u.every(x=>BIG.some(b=>b[0]===x.wf))?`🔁 兩個流程 ${u.length} 張`:u.every(x=>ISV((x.outs||[])[0]||''))&&new Set(u.map(x=>x.img)).size>1&&new Set(u.map(x=>x.prompt)).size>1&&new Set(u.map(x=>x.wf)).size===1?`🎞 長片 ${u.length} 段`:new Set(u.map(x=>x.prompt)).size>1&&new Set(u.map(x=>x.img)).size===1?`📝 ${new Set(u.map(x=>x.prompt)).size} 種寫法 ${u.length} 張`:`📚 批量 ${u.length} 張`}</b>
   <span style="color:var(--green);font-weight:800">${ok?'✔ '+ok:''}</span>${bad?`<span style="color:var(--red);font-weight:800">✖ ${bad}</span>`:''}${run?`<span style="color:var(--orange);font-weight:800">⏳ ${run}</span>`:''}<span class="grow"></span><span class="mu">#${u[0].id}～#${u[u.length-1].id} · ${tm}</span></div>
   <div class="mu clamp">${esc(u[0].prompt||'（沒有提示詞）')}</div><div class="gS">${O.slice(0,10).map(o=>`<img src="${IMGT(o)}" loading="lazy">`).join('')}${O.length>10?`<span class="mu">+${O.length-10}</span>`:''}</div></summary>
   <div class="gB">${HVIEW==='trash'?'':`<div class="row" style="margin:0 0 4px"><span class="mu">整批：</span>${hBtns(HVIEW).replace(/data-h=/g,'data-hg="'+ids+'" data-h2=')}${u.filter(x=>x.state==='done').length>1?`<a class="pill" href="${U('/api/zip',{ids:u.filter(x=>x.state==='done').map(x=>x.id).join(',')})}" download>⬇ 整組 zip</a>`:''}${u.some(x=>/#00FF00/i.test(x.prompt||'')&&x.state==='done')?`<button class="pill" data-hkey="${u.filter(x=>/#00FF00/i.test(x.prompt||'')&&x.state==='done').map(x=>x.id).join(',')}">⬇ 全部存透明 PNG</button>`:''}${HVIEW!=='trash'&&u.some(x=>x.vote>0)&&u.some(x=>!x.vote&&x.state==='done')?`<button class="pill" data-hg="${u.filter(x=>!x.vote&&x.state!=='run'&&x.state!=='wait').map(x=>x.id).join(',')}" data-h2="del" title="沒打星星的放進回收桶（30 天內可以還原）">🧹 只留有打星的（刪 ${u.filter(x=>!x.vote&&x.state!=='run'&&x.state!=='wait').length} 張）</button>`:''}</div>`}
   ${u.some(x=>/^🔬/.test(x.src||''))?benchTable(u):''}${u[0].cmp?`<button class="pill acc" data-gocmp="${u[0].cmp}" style="margin:2px 0 8px">🧪 到比較頁看結果表（比較 #${u[0].cmp}）</button>`:O.length>1?`<div class="mg" data-b="${b}"></div>`:''}${u.map(x=>gCard(x,HVIEW||true)).join('')}</div></details>`}
function benchTable(u){const R=u.filter(x=>x.state==='done'&&x.run_s>0&&!/暖機/.test(x.src)).sort((a,b)=>a.run_s-b.run_s);
  return `<div class="mg" style="padding:8px"><b>🔬 測速結果</b>（暖機那張不算；同一個種子，可以點下面每張比畫質）<table style="width:100%;margin-top:6px;font-size:13px;border-collapse:collapse">${R.map((x,i)=>`<tr style="border-top:1px solid var(--tabline)"><td style="padding:4px 0">${i?'':'🏆 '}${esc(x.src.replace('🔬 ',''))}</td><td style="text-align:right;font-weight:800">${x.run_s.toFixed(0)} 秒</td><td class="mu" style="padding-left:8px">${esc(x.pbrief||'')}</td></tr>`).join('')||'<tr><td class="mu">還在跑…</td></tr>'}</table></div>`}
async function hLoad(reset){if(reset){HOFF=0;HJ=[]}hModeBar();const hm=LS.get('hmode','');const q={q:$('#hq').value.trim(),state:$('#hs').value,wf:hm?(GMODES.find(m=>m[0]===hm)||[0,0,0,[]])[3].join('|'):$('#hw').value,offset:HOFF,limit:30,view:HVIEW};{const n=[q.q,q.state,q.wf].filter(Boolean).length,f=$('#hfn');if(f)f.textContent=n?`（用了 ${n} 個條件）`:'';}
  const r=await api(U('/api/gen_hist',q));if(!r.ok)return toast(r.message||'讀不到');GOFF=(r.now||Date.now()/1000)-Date.now()/1000;
  HJ=HJ.concat(r.rows||[]);HOFF+=(r.units!=null?r.units:(r.rows||[]).length);HTOT=r.total;const c=r.counts||{};
  if(reset){const cur=$('#hw').value;$('#hw').innerHTML='<option value="">全部流程</option>'+(r.wfs||[]).map(w=>`<option ${w===cur?'selected':''}>${esc(w)}</option>`).join('')}
  $('#hvw').innerHTML=[['','全部'],['star',`⭐ 高分 ${c.star||0}`],['hidden',`🙈 已隱藏 ${c.hidden||0}`],['trash',`🗑 回收桶 ${c.trash||0}`]].map(([k,n])=>`<button data-v="${k}" class="${k===HVIEW?'on':''}">${n}</button>`).join('');
  $('#hn').textContent=`共 ${HTOT} 筆`;$('#hm').style.display=HOFF<HTOT?'':'none';
  $('#htip').textContent=HVIEW==='star'?'你打 4～5 星的結果（點圖放大可以打分數，電腦按 1～5）':HVIEW==='trash'?`放在回收桶 ${30} 天後會自動永久刪除；還原會把檔案搬回去`:HVIEW==='hidden'?'隱藏的紀錄不會出現在「全部」，檔案和時間統計都還在':'';hRender()}
function hSelBar(){let b=$('#hsb');document.body.classList.toggle('hsel',!!HSEL);if(!HSEL){if(b)b.remove();return}if(!b){b=document.createElement('div');b.id='hsb';document.body.appendChild(b)}
  b.innerHTML=`<span><b>已選 ${HSEL.size} 筆</b></span><button class="pill" data-s="all">全選</button>${HSEL.size===2?'<button class="pill acc" data-s="vs">🆚 比這兩張</button>':''}${HVIEW==='trash'?'':'<button class="pill" data-s="dl">⬇ 下載</button>'}${HVIEW==='trash'?'':'<button class="pill" data-s="tpl" title="把勾的這幾筆的提示詞存成一篇「📚 整篇範本」（每筆一段）">📚 存成範本</button>'}${hBtns(HVIEW).replace(/data-h=/g,'data-hs=')}<button class="pill" data-s="off">✕ 結束選取</button>`;
  b.onclick=async e=>{const x=e.target.closest('button');if(!x)return;if(x.dataset.s==='off'){HSEL=null;hRender();$('#hsel').classList.remove('on');return}
    if(x.dataset.s==='vs'){const [a,b2]=HJ.filter(j=>HSEL.has(j.id)).sort((p,q)=>p.id-q.id);const oa=(a.outs||[]).find(o=>!ISV(o)),ob=(b2.outs||[]).find(o=>!ISV(o));if(!oa||!ob)return toast('兩筆都要有圖片結果');
      const im=document.querySelector(`#hl img[data-big="${CSS.escape(ob)}"]`);if(!im)return toast('先把那一組展開');ovOpen(im);$('#cmpa').src=IMGU(oa);$('#cmp .cl').textContent='#'+a.id;$('#cmp .cr').textContent='#'+b2.id;cmpShow(true);return}
    if(x.dataset.s==='all'){HJ.forEach(j=>{if(j.state!=='run'&&j.state!=='wait')HSEL.add(j.id)});hRender();return}
    if(x.dataset.s==='tpl'){const P=[...new Set(HJ.filter(j=>HSEL.has(j.id)).sort((p,q)=>p.id-q.id).map(j=>(j.prompt||'').trim()).filter(Boolean))];if(!P.length)return toast('勾的紀錄沒有提示詞');   // V0.3.49 好的提示詞存起來下次用
      if(!PKL)await pkLoad();const r=await pkAsk(`把 ${P.length} 段提示詞存成範本：標題`,P[0].slice(0,16),[['💾 存','g'],['取消']]);if(r.i!==0)return;
      PKT.docs.unshift({id:pkId(),title:r.v.trim()||P[0].slice(0,16),text:P.join('\n\n'),t:Date.now()/1000});await pkSave();toast(`📚 存好了（${P.length} 段）：生圖頁「📚 範本」點一下就帶回來`,4000);return}
    if(x.dataset.s==='dl'){const O=HJ.filter(j=>HSEL.has(j.id)).flatMap(j=>j.outs||[]);if(!O.length)return toast('勾的紀錄沒有結果檔');
      if(O.length>2){const a=document.createElement('a');a.href=U('/api/zip',{ids:HJ.filter(j=>HSEL.has(j.id)).map(j=>j.id).join(',')});a.download='';document.body.appendChild(a);a.click();a.remove();toast(`⬇ ${O.length} 個打包成一個 zip 下載`,3000);return}
      if(O.length>1&&!confirm(`下載 ${O.length} 個檔案？（瀏覽器第一次可能會問「允許下載多個檔案」，按允許）`))return;
      for(let i=0;i<O.length;i++){const a=document.createElement('a');a.href=U('/api/img',{f:O[i],dl:1});a.download='';document.body.appendChild(a);a.click();a.remove();toast(`⬇ 下載 ${i+1}／${O.length}`);await new Promise(r=>setTimeout(r,700))}return}
    const a=x.dataset.hs;if(!a)return;if(!HSEL.size)return toast('先勾要處理的紀錄');await hAct(a,[...HSEL])}}
async function hAct(a,ids){if((a==='del'||a==='purge')&&!confirm(`${HACT[a]}：${ids.length} 筆？`))return;
  const r=await api('/api/hist_act',{a,ids});toast(r.ok?`✔ ${HACT[a].replace(/（.*/,'')} ${r.n} 筆`+(a==='del'&&r.n<ids.length?`（${ids.length-r.n} 筆還在跑／排隊，先取消）`:''):(r.message||'失敗'),3500);if(HSEL)HSEL.clear();hLoad(true)}
async function hClick(e){const gc=e.target.closest('[data-gocmp]');if(gc){CRUN=+gc.dataset.gocmp;LS.set('cmp_run',CRUN);CUR='cmp';LS.set('tab','cmp');tabs();show();setTimeout(()=>{const m=$('#cmx');if(m)m.scrollIntoView()},800);return}
const ck=e.target.closest('[data-ck]');if(ck){const id=+ck.dataset.ck;ck.checked?HSEL.add(id):HSEL.delete(id);hSelBar();return}
  const gk=e.target.closest('[data-gck]');if(gk){gk.dataset.gck.split(',').forEach(i=>gk.checked?HSEL.add(+i):HSEL.delete(+i));hRender();return}
  const hk=e.target.closest('[data-hkey]');if(hk){const ids=hk.dataset.hkey.split(',').map(Number);for(const id of ids){const J=HJ.find(x=>x.id===id);if(J&&J.outs&&J.outs[0]){await gKeyOut(IMGU(J.outs[0]),id);await new Promise(r=>setTimeout(r,400))}}return}   // V0.2.98 貼圖組一次全部去背
  const hg=e.target.closest('[data-hg]');if(hg){hAct(hg.dataset.h2,hg.dataset.hg.split(',').map(Number));return}
  if(e.target.closest('.mg'))return;
  const h=e.target.closest('[data-h]');if(h){const c=h.closest('[data-jid]');if(c)hAct(h.dataset.h,[+c.dataset.jid]);return}
  if($('#hl').classList.contains('compact')&&!e.target.closest('button,a,img,video,input,summary')){const c=e.target.closest('.job');if(c){c.classList.toggle('open');return}}
  gClick(e)}
async function hStats(){const r=await api('/api/gen_stats');const S=r.stats||[];
  $('#hst').innerHTML=S.length?S.map(s=>`<div class="it"><div class="row"><b class="grow">${esc(s.wf)}</b><span class="mu">${s.n} 次</span></div><div class="mu" style="font-size:12px">${esc(s.brief||'')}${s.size?' · '+esc(s.size):''}</div>
    <div class="row"><span>熱：<b>${s.warm!=null?fmtT(s.warm):'—'}</b><span class="mu">（${s.warm_n} 次）</span></span><span>載入模型：<b>${s.cold!=null?fmtT(s.cold):'—'}</b><span class="mu">（${s.cold_n} 次）</span></span></div></div>`).join(''):'<div class="mu">還沒有跑完的紀錄</div>'}
// ---- 掛在歷史紀錄頁也會自己更新：每 2 秒問一次電腦，有工作做好／失敗／新增 → 重讀目前看得到的那幾頁（不用切頁、不用重新整理）
let HSIG='',HPEND=false,HBUSY=false;
const hSig=L=>L.map(j=>`${j.id}:${j.state}:${(j.outs||[]).length}`).join(',');
async function hPoll(){if(HBUSY||!$('#hl'))return;HBUSY=true;try{
  const r=await api(U('/api/gen',{n:60}));if(!r.ok||CUR!=='hist')return;const J=r.jobs||[],have=new Map(HJ.map(j=>[j.id,j]));
  const maxId=HJ.reduce((m,j)=>Math.max(m,j.id),0);
  // 進度條、狀態文字：直接改，不整個重畫
  J.forEach(j=>{if(j.state!=='run')return;const c=$(`#hl .job[data-jid="${j.id}"]`);if(!c)return;const b=c.querySelector('.gpb i'),t=c.querySelector('.gpp');
    if(b&&!b.parentElement.dataset.pest){b.style.width=(j.prog||0)+'%';if(t)t.textContent=j.t_start?Math.round(j.prog||0)+'%':'準備中'}});
  const changed=J.some(j=>{const h=have.get(j.id);return h?(h.state!==j.state||(h.outs||[]).length!==(j.outs||[]).length):(!HVIEW&&j.id>maxId)});
  if(changed)HPEND=true;if(!HPEND)return;
  // 正在看大圖、播影片、打字、拖合併格子的時候先不重畫，等你停下來再更新
  const ov=$('#ov');if(ov&&ov.style.display==='flex')return;if($$('#hl video').some(v=>!v.paused))return;
  const ae=document.activeElement;if(ae&&ae.closest&&ae.closest('#hl')&&/INPUT|SELECT|TEXTAREA/.test(ae.tagName))return;if(document.querySelector('.mgGrip.on'))return;
  await hRefresh();HPEND=false}finally{HBUSY=false}}
async function hRefresh(){const hm=LS.get('hmode','');const q={q:$('#hq').value.trim(),state:$('#hs').value,wf:hm?(GMODES.find(m=>m[0]===hm)||[0,0,0,[]])[3].join('|'):$('#hw').value,offset:0,limit:Math.max(30,HOFF),view:HVIEW};
  const r=await api(U('/api/gen_hist',q));if(!r.ok||CUR!=='hist')return;const fresh=new Set(HJ.map(j=>j.id));
  const open=new Set($$('#hl .job.open').map(x=>+x.dataset.jid)),y=scrollY;
  HJ=r.rows||[];HOFF=r.units!=null?r.units:HJ.length;HTOT=r.total;$('#hn').textContent=`共 ${HTOT} 筆`;$('#hm').style.display=HOFF<HTOT?'':'none';
  hRender();open.forEach(id=>{const c=$(`#hl .job[data-jid="${id}"]`);if(c)c.classList.add('open')});scrollTo(0,y);
  const nw=HJ.filter(j=>!fresh.has(j.id)).length;if(nw&&!HVIEW)toast(`🆕 多了 ${nw} 筆`,1800)}
// V0.2.73 歷史紀錄最上面四個模式快篩：只看改圖／合併／影片／首尾幀
function hModeBar(){const b=$('#hmode');if(!b)return;const cur=LS.get('hmode','');b.innerHTML=[['','全部']].concat(GMODES.map(m=>[m[0],m[1]+' '+m[2]])).map(([k,n])=>`<button class="gpc ${k===cur?'on':''}" data-hm="${k}">${n}</button>`).join('');
  b.onclick=e=>{const x=e.target.closest('[data-hm]');if(!x)return;LS.set('hmode',x.dataset.hm);if(x.dataset.hm)$('#hw').value='';hLoad(true)}}
async function rHist(again){if(again)return hPoll();
  $('#v').innerHTML=`<div class="panel"><h3>📜 歷史紀錄　<span class="mu" id="hn"></span></h3>
  <div class="seg" id="hvw" style="margin-bottom:6px"></div><div class="mu" id="htip" style="margin:-2px 0 6px"></div>
  <div class="row" id="hmode" style="gap:6px;flex-wrap:wrap;margin:8px 0 2px"></div>
  <details class="gadv hflt" id="hflt"><summary>🔍 搜尋／篩選 <span class="mu" id="hfn"></span></summary>
  <div class="row"><input id="hq" class="gsel" placeholder="搜尋提示詞或 #編號"><button class="pill" id="hgo">🔍</button></div><div class="gtcat" id="hpk" style="margin-top:6px"></div>
  <div class="row" style="margin-top:6px"><select id="hs"><option value="">全部狀態</option><option value="done">✔ 完成</option><option value="fail">✖ 失敗</option><option value="stop">⏹ 取消</option><option value="wait">⏳ 排隊</option></select><select id="hw" class="gsel"><option value="">全部流程</option></select></div>
  <details id="hsd" style="margin-top:8px"><summary><b>📊 時間統計</b> <span class="mu">每種設定平均跑多久（拿來預估時間）</span></summary><div id="hst" class="mu">讀取中…</div></details></details></div>
  <div class="row" style="margin:0 0 8px"><button class="pill" id="hsel">☑ 選取</button><button class="pill" id="hcmp">▤ 精簡</button><span class="grow"></span><button class="pill" id="hfold" title="全部收起">⊟</button><button class="pill" id="hopen" title="全部展開">⊞</button></div>
  <div class="panel"><div id="hl"></div><button class="pill big" id="hm" style="display:none">載入更多</button></div>`;
  const cm=LS.get('hcompact',false);$('#hl').classList.toggle('compact',cm);$('#hcmp').classList.toggle('on',cm);
  $('#hcmp').onclick=()=>{const v=!$('#hl').classList.contains('compact');$('#hl').classList.toggle('compact',v);$('#hcmp').classList.toggle('on',v);LS.set('hcompact',v)};
  $('#hsel').onclick=()=>{HSEL=HSEL?null:new Set();$('#hsel').classList.toggle('on',!!HSEL);hRender()};
  $('#hfold').onclick=()=>{const o=LS.get('hshut',{});$$('#hl details.hday').forEach(d=>{d.open=false;o[d.dataset.day]=1});LS.set('hshut',o)};
  $('#hopen').onclick=()=>{LS.set('hshut',{});$$('#hl details.hday').forEach(d=>d.open=true)};
  $('#hvw').onclick=e=>{const b=e.target.closest('[data-v]');if(!b)return;HVIEW=b.dataset.v;LS.set('hview',HVIEW);if(HSEL)HSEL.clear();hLoad(true)};
  {const hk=async()=>{if(!PKL)await pkLoad();const e=$('#hpk');if(!e)return;const O=PKT.cats.flatMap(c=>c.opts.map(o=>o.t)).filter(t=>t.length<=20).slice(0,30);   // V0.3.56 用積木的字快速搜尋歷史
    e.innerHTML=O.length?'<span class="mu" style="font-size:12px;margin-right:4px">🏷 快速找：</span>'+O.map(t=>`<button class="gpc" data-hk="${esc(t)}">${esc(t)}</button>`).join(''):'';e.onclick=ev=>{const b=ev.target.closest('[data-hk]');if(!b)return;$('#hq').value=$('#hq').value===b.dataset.hk?'':b.dataset.hk;hLoad(true)}};hk()}
  $('#hgo').onclick=()=>hLoad(true);$('#hq').onkeydown=e=>{if(e.key==='Enter')hLoad(true)};$('#hs').onchange=$('#hw').onchange=()=>hLoad(true);
  $('#hm').onclick=()=>hLoad(false);$('#hl').onclick=hClick;$('#hsd').ontoggle=()=>{if($('#hsd').open)hStats()};hLoad(true)}


// ================= 上面正中間「📊 效能／🖥 背景／🎨 排隊」浮動按鈕 → 浮動視窗（照 TikLive：一次開一個，按另一顆切換、再按同一顆關；點旁邊關；下面拉桿調高度）
const SYSPOP_T={pf:'📊 電腦效能',bg:'🖥 後台狀態',q:'🎨 生圖排隊'};
function sysFabInit(){if($('#sysFab'))return;const b=document.createElement('div');b.id='sysFab';
  b.innerHTML='<button type="button" data-t="pf" title="電腦效能（浮動視窗，原本的頁面不會停）">📊 效能</button><button type="button" data-t="bg" title="後台狀態（浮動視窗）">🖥 背景</button><button type="button" data-t="q" title="正在跑、排隊中的生圖（浮動視窗）">🎨 排隊<em id="fbN" hidden></em></button>';
  b.onclick=e=>{const x=e.target.closest('[data-t]');if(!x)return;e.stopPropagation();const w=$('#sysPop');if(!w)sysPopOpen(x.dataset.t);else if(w.dataset.t===x.dataset.t)sysPopClose();else w._tab(x.dataset.t)};
  document.body.appendChild(b);fbPoll();setInterval(()=>{if(!document.hidden)fbPoll()},8000)}
async function fbPoll(){try{const j=await api('/api/gen?n=30');if(!j.ok)return;const n=(j.jobs||[]).filter(x=>x.state==='run'||x.state==='wait').length;
  const e=$('#fbN');if(e){e.hidden=!n;e.textContent=n}const t=$('#nrun');if(t){t.hidden=!n;t.textContent=n}}catch(e){}}
let PFX=null;
function sysPopOpen(t0){if($('#sysPop'))return;const w=document.createElement('div');w.id='sysPop';
  w.innerHTML=`<div class="sysPopW"><div class="sysPopH"><b class="sysPopTt"></b><span class="sysPopN">點旁邊回到原本的頁面</span><button type="button" class="sysPopX" title="關閉">✕</button></div><div class="sysPopB"><div class="empty">讀取中…</div></div><div class="sysPopR" title="上下拖：調整視窗高度（點兩下恢復 50%）"><i></i></div></div>`;
  document.body.appendChild(w);const body=w.querySelector('.sysPopB'),W=w.querySelector('.sysPopW');
  const setH=f=>{f=Math.max(.25,Math.min(.9,+f||.5));W.style.height=(f*100)+'%';return f};let hf=setH(LS.get('pop_h',.5));
  const gr=w.querySelector('.sysPopR');let dg=null;
  gr.onpointerdown=e=>{gr.setPointerCapture(e.pointerId);dg={y:e.clientY,h:W.getBoundingClientRect().height};gr.classList.add('on');e.preventDefault();e.stopPropagation()};
  gr.onpointermove=e=>{if(!dg)return;hf=setH((dg.h+e.clientY-dg.y)/w.getBoundingClientRect().height)};
  gr.onpointerup=gr.onpointercancel=()=>{if(!dg)return;dg=null;gr.classList.remove('on');LS.set('pop_h',+hf.toFixed(3));if(w.dataset.t==='pf'&&PF.d)pfRender(body)};
  gr.ondblclick=()=>{hf=setH(.5);LS.set('pop_h',.5)};
  const tick=()=>{if(!body.isConnected){clearInterval(PFX);PFX=null;return}if(document.hidden)return;const t=w.dataset.t;
    if(t==='pf')pfLoad(body);else if(t==='bg')bgsLoad(body);else if(t==='q')qLoad(body)};
  const tab=t=>{w.dataset.t=t;w.querySelector('.sysPopTt').textContent=SYSPOP_T[t]||'';$$('#sysFab [data-t]').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
    body.innerHTML='<div class="empty">讀取中…</div>';body.scrollTop=0;tick()};
  w._tab=tab;tab(SYSPOP_T[t0]?t0:'pf');clearInterval(PFX);PFX=setInterval(tick,2000);
  w.addEventListener('click',e=>{if(e.target===w)sysPopClose()});w.querySelector('.sysPopX').onclick=()=>sysPopClose();
  body.addEventListener('click',e=>{if(w.dataset.t==='q'&&e.target.closest('[data-qall]')){e.stopPropagation();gCancelMany(0);return}if(w.dataset.t==='q'){const im=e.target.closest('img[data-big]');if(im){gClick(e);return}const c=e.target.closest('[data-goto]');
      if(c&&!e.target.closest('button')){sysPopClose();if(CUR!=='gen'){CUR='gen';LS.set('tab','gen');tabs();show()}setTimeout(()=>{const x=$(`#gj [data-jid="${c.dataset.goto}"]`);if(x)x.scrollIntoView({block:'center'})},500);return}}
    bgsClick(e)})}
function sysPopClose(){const w=$('#sysPop');if(!w)return;w.remove();clearInterval(PFX);PFX=null;$$('#sysFab [data-t]').forEach(b=>b.classList.remove('on'))}

// ================= 📊 電腦效能（照 TikLive：上面一張大圖、下面小格子，點小格子換大圖）
const PF={d:null,sel:LS.get('pf_sel','cpu')};
async function pfLoad(host){try{PF.d=await api('/api/perf')}catch(e){if(!PF.d){host.innerHTML='<div class="empty">連不到電腦</div>';}return}pfRender(host)}
function pfSeries(P,k){const H=P.hist||{},g=P.gpu||{};return({cpu:{v:H.cpu,c:'#4dc9ff',max:100},ram:{v:H.ram,c:'#b48cff',max:100},gpu:{v:H.gpu,c:'#45d483',max:100},vram:{v:H.vram,c:'#f0ad4e',max:100},
  enc:{v:H.enc,c:'#ff9f43',max:100},dec:{v:H.dec,c:'#ff6577',max:100}})[k]||{v:[],c:'#888',max:100}}
function pfTiles(P){const g=P.gpu||{},T=[];const pct=x=>x==null?'—':Math.round(x)+'%';
  T.push({k:'cpu',t:'CPU',v:pct(P.cpu),sub:''});T.push({k:'ram',t:'記憶體',v:pct(P.ram),sub:P.ram_total?fmtB(P.ram_used)+' / '+fmtB(P.ram_total):''});
  if(g.name){T.push({k:'gpu',t:'GPU（NVIDIA）',v:pct(g.util),sub:(g.temp!=null?Math.round(g.temp)+'°C · ':'')+esc(g.name)});
    if(g.mem_t)T.push({k:'vram',t:'顯示卡記憶體',v:pct(100*g.mem/g.mem_t),sub:fmtB(g.mem*1048576)+' / '+fmtB(g.mem_t*1048576)});
    T.push({k:'enc',t:'影片編碼',v:pct(g.enc),sub:'NVENC'});T.push({k:'dec',t:'影片解碼',v:pct(g.dec),sub:'NVDEC'})}
  return T}
function pfDetail(P,k){const row=(a,b)=>`<div><span>${a}</span><b>${b}</b></div>`,g=P.gpu||{},pct=x=>x==null?'—':Math.round(x)+'%';
  if(k==='cpu')return row('使用率',pct(P.cpu));if(k==='ram')return row('使用率',pct(P.ram))+row('用掉',fmtB(P.ram_used))+row('總共',fmtB(P.ram_total));
  if(k==='gpu')return row('使用率',pct(g.util))+row('溫度',g.temp!=null?Math.round(g.temp)+'°C':'—')+row('型號',esc(g.name||'—'))+row('驅動程式',esc(g.drv||'—'));
  if(k==='vram')return row('使用率',g.mem_t?pct(100*g.mem/g.mem_t):'—')+row('用掉',fmtB((g.mem||0)*1048576))+row('總共',fmtB((g.mem_t||0)*1048576))+row('誰在用','ComfyUI 跑圖時模型放在這裡');
  return row('使用率',pct(k==='enc'?g.enc:g.dec))}
function pfDraw(cv,s,big){if(!cv)return;const r=cv.getBoundingClientRect(),dpr=window.devicePixelRatio||1,W=r.width,H=r.height;if(!W)return;
  cv.width=Math.round(W*dpr);cv.height=Math.round(H*dpr);const g=cv.getContext('2d');g.setTransform(dpr,0,0,dpr,0,0);g.clearRect(0,0,W,H);
  if(big){g.strokeStyle='rgba(128,128,128,.18)';g.lineWidth=1;for(let i=1;i<10;i++){const x=Math.round(W*i/10)+.5;g.beginPath();g.moveTo(x,0);g.lineTo(x,H);g.stroke()}
    for(let i=1;i<5;i++){const y=Math.round(H*i/5)+.5;g.beginPath();g.moveTo(0,y);g.lineTo(W,y);g.stroke()}}
  const N=180,v=s.v||[];if(v.length){g.beginPath();let st=false;const x0=W-(v.length-1)/(N-1)*W;
    v.forEach((y,i)=>{if(y==null)return;const X=x0+i/(N-1)*W,Y=H-Math.min(1,y/s.max)*(H-2)-1;st?g.lineTo(X,Y):(g.moveTo(X,Y),st=true)});
    if(st){g.strokeStyle=s.c;g.lineWidth=big?1.6:1.2;g.stroke();g.lineTo(W,H);g.lineTo(x0,H);g.closePath();g.globalAlpha=.18;g.fillStyle=s.c;g.fill();g.globalAlpha=1}}
  g.strokeStyle=s.c;g.globalAlpha=.55;g.lineWidth=1;g.strokeRect(.5,.5,W-1,H-1);g.globalAlpha=1}
function pfRender(host){const P=PF.d;if(!P||!host||!host.isConnected)return;const tiles=pfTiles(P);if(!tiles.find(t=>t.k===PF.sel))PF.sel='cpu';const sel=tiles.find(t=>t.k===PF.sel);
  const keep=host.scrollTop,g=P.gpu||{};
  host.innerHTML=`<h2 class="stt">📊 電腦效能 <small style="font-size:12px;color:var(--sub);font-weight:600">${esc(P.time)} · 每 2 秒</small></h2>
<section class="ssec pfbig"><div class="pfhd"><b style="color:${pfSeries(P,sel.k).c}">${esc(sel.t)}</b><span>${sel.v}</span></div><canvas class="pfcv"></canvas>
<div class="pfax"><span>3 分鐘</span><span>0–100%</span><span>現在</span></div><div class="pfdt">${pfDetail(P,sel.k)}</div></section>
<div class="pft">${tiles.map(t=>`<button class="pftl${t.k===PF.sel?' on':''}" data-pk="${t.k}"><canvas></canvas><div><b>${esc(t.t)}</b><span>${t.v}</span><small>${t.sub||''}</small></div></button>`).join('')}</div>
<section class="ssec"><h3>🌡 溫度</h3><div class="pftemp"><div><span>GPU</span><b class="${g.temp>=80?'hot':g.temp>=65?'warm':''}">${g.temp!=null?Math.round(g.temp)+'°C':'—'}</b></div></div>
<div class="snote" style="margin:0 2px 10px">${g.name?'顯示卡溫度從 nvidia-smi 讀的。CPU 溫度 Windows 沒有直接提供。':'沒有偵測到 NVIDIA 顯示卡（nvidia-smi）。'}</div></section>`;
  pfDraw(host.querySelector('.pfcv'),pfSeries(P,sel.k),true);$$('.pftl',host).forEach(b=>{pfDraw(b.querySelector('canvas'),pfSeries(P,b.dataset.pk),false);
    b.onclick=()=>{PF.sel=b.dataset.pk;LS.set('pf_sel',PF.sel);pfRender(host)}});host.scrollTop=keep}

// ================= 🖥 後台狀態（照 TikLive）：電腦現在在背景做什麼、排隊什麼；可以暫停／繼續／取消
const BCST={run:['▶ 進行中','#45d483'],idle:['— 沒事','var(--sub)'],pause:['⏸ 暫停中','#ff4d6d'],hold:['⚖ 讓路中','#f0ad4e']};
async function bgsLoad(host){let j,g;try{[j,g]=await Promise.all([api('/api/state'),api('/api/gen?n=40')])}catch(e){return}if(!j.ok||!host.isConnected)return;
  const c=j.ctl,G=(g.jobs||[]).filter(x=>x.state==='run'||x.state==='wait').sort((a,b)=>(a.state!=='run')-(b.state!=='run')||(a.qpos||0)-(b.qpos||0));
  const nrun=c.kinds.reduce((a,k)=>a+(k.running||0),0),nwait=G.filter(x=>x.state==='wait').length;const keep=host.scrollTop;
  const items=k=>k.k!=='gen'?(k.last?`<div class="bgsI ${k.running?'run':'wait'}"><i>${k.running?'▶':'·'}</i><div class="bgsT"><b>${esc(k.last)}</b>${k.pct!=null?`<small>${k.done}／${k.total}</small><u><s style="width:${k.pct}%"></s></u>`:''}</div></div>`:'')
    :G.map(x=>`<div class="bgsI ${x.state}"><i>${x.state==='run'?'▶':'⏳'}</i><div class="bgsT"><b>#${x.id} ${esc(x.prompt||'（沒有提示詞）')}</b><small>${x.state==='run'?esc(x.msg||'生成中'):(x.msg?esc(x.msg):'排隊第 '+(x.qpos||'?')+' 個')}${x.est&&x.est.sec?' · 預估 '+fmtT(x.est.sec):''}</small>${x.state==='run'?`<u><s style="width:${x.prog||0}%"></s></u>`:''}</div><button data-bc="${x.id}">取消</button></div>`).join('');
  host.innerHTML=`<div class="bgs"><div class="bgsHd"><b>🖥 後台狀態</b><span class="bgsSum">${nrun||nwait?`▶ ${nrun} 個在跑 · ⏳ ${nwait} 個排隊`:'現在沒有背景工作 ✔'}</span></div>
<div class="bgsNote">電腦現在在背景做的事。▶ 正在跑、⏳ 排隊中；可以直接暫停、取消。CPU 一直很高時，排在下面的先讓路。</div>
${c.kinds.map(k=>{const [nm,col]=BCST[k.state]||[k.state,'var(--sub)'];const its=items(k);return `<div class="bgsC${!k.running&&!its&&k.state==='idle'?' idle':''}"><div class="bgsCH"><b>${k.prio}. ${k.icon} ${esc(k.name)}</b><span style="color:${col};font-weight:800">${nm}</span>
 ${k.state==='pause'?`<button class="bgsB g" data-a="resume" data-k="${k.k}">▶ 繼續</button>`:`<button class="bgsB n" data-a="pause" data-k="${k.k}">⏸ 暫停</button>`}${k.running?`<button class="bgsB" data-a="stop" data-k="${k.k}">⏹ 立刻停</button>`:''}<button class="bgsB n" data-a="up" data-k="${k.k}">↑</button></div>
 ${k.held?`<div class="bgsCN bgsGuard">${esc(k.held)}</div>`:''}${its?`<div class="bgsLst">${its}</div>`:''}</div>`}).join('')}
<div class="bgsC"><div class="bgsCH"><b>⚖ 電腦太忙自動讓路</b><span>CPU ${c.cpu}%</span></div><div class="row" style="margin-top:6px"><div class="seg"><button data-a="guard" data-on="1" class="${c.guard?'on':''}">開</button><button data-a="guard" data-on="0" class="${c.guard?'':'on'}">關</button></div>
 <div class="seg">${[70,80,90,95].map(x=>`<button data-a="cpumax" data-v="${x}" class="${+c.cpu_max===x?'on':''}">${x}%</button>`).join('')}</div></div>${c.log&&c.log.length?`<div class="bgsCN" style="margin-top:6px">${c.log.slice(0,3).map(esc).join('<br>')}</div>`:''}</div>
<div class="bgsC"><div class="bgsCH"><b>最近的工作</b></div>${(j.tasks||[]).slice(0,8).map(t=>`<div class="bgsI"><i>${({done:'✔',fail:'✖',stop:'⏹',run:'▶'})[t.state]||'·'}</i><div class="bgsT"><b>${esc(t.title)}</b><small>${esc(t.msg||'')}</small></div></div>`).join('')||'<div class="bgsCN">還沒有</div>'}</div></div>`;
  host.scrollTop=keep}
async function bgsClick(e){const b=e.target.closest('[data-a],[data-bc]');if(!b)return;const host=b.closest('.sysPopB,#sbody');
  if(b.dataset.bc){if(!confirm('取消 #'+b.dataset.bc+'？'))return;const r=await api('/api/gen_act',{a:'cancel',id:+b.dataset.bc});toast(r.ok?'已取消':(r.message||'失敗'))}
  else{const a=b.dataset.a;if(a==='stop'&&!confirm('立刻停：正在做的也停掉、放回排隊？'))return;let body={a,k:b.dataset.k};
    if(a==='guard')body={a:'guard',on:b.dataset.on==='1'};if(a==='cpumax')body={a:'guard',cpu_max:+b.dataset.v};const r=await api('/api/bgctl',body);toast(r.ok?'好了':(r.message||'失敗'))}
  if(host)bgsLoad(host)}

// ================= 🎨 生圖排隊（浮動視窗）：正在跑、排隊中的；最近做好的幾張。點一筆回到「生圖」那一筆
async function qLoad(host){let j;try{j=await api('/api/gen?n=30')}catch(e){return}if(!j.ok||!host.isConnected)return;GOFF=(j.now||Date.now()/1000)-Date.now()/1000;
  const L=j.jobs||[];GJ=L;GQS=j.qsum||{n:0,b:{}};const A=L.filter(x=>x.state==='run'||x.state==='wait').sort((a,b)=>(a.state!=='run')-(b.state!=='run')||(a.qpos||0)-(b.qpos||0)),D=L.filter(x=>x.state==='done').slice(0,6);
  const c=j.comfy||{};const keep=host.scrollTop;
  host.innerHTML=`${GQS.n>0||A.some(x=>x.state==='run')?`<div style="display:flex;gap:8px;align-items:center;margin-bottom:8px"><b style="flex:1">排隊 ${GQS.n} 個</b><button class="pill er" data-qall="1">⏹ 全部取消</button></div>`:''}<div class="mu" style="margin-bottom:6px">${c.ok?`<span style="color:var(--green)">● ComfyUI ${esc(c.ver||'')}</span>${c.gpu?' · '+esc(c.gpu):''}`:'<span style="color:var(--red)">● 連不到 ComfyUI（工作會先排隊）</span>'}</div>
  ${A.length?A.map(x=>`<div class="bgsC" data-goto="${x.id}" style="margin-bottom:6px;cursor:pointer;${x.state==='run'?'border-color:#1f8ef1':''}"><div class="bgsCH"><b>#${x.id} ${x.state==='run'?'▶ '+esc(x.msg||'生成中'):'⏳ 排隊第 '+(x.qpos||'?')+' 個'}</b><span>${esc(x.src)}</span></div>
   <div class="bgsCN" style="opacity:.9">${esc(x.prompt||'（沒有提示詞）')}</div><div class="bgsCN">${esc(x.wf)}${x.brief?' · '+esc(x.brief):''}</div>
   ${x.state==='run'?gBar(x):''}<div>${gTimes(x)}</div></div>`).join(''):'<div class="empty" style="padding:16px 0">現在沒有在跑、也沒有排隊的 ✔</div>'}
  ${D.length?`<div class="mu" style="margin:8px 0 4px;font-weight:700">最近做好的</div><div class="th">${D.map(x=>x.outs.slice(0,1).map(o=>`<img src="${IMGT(o)}" data-big="${esc(o)}" data-id="${x.id}" data-i="0" loading="lazy" style="height:90px">`).join('')).join('')}</div>`:''}`;
  host.scrollTop=keep}

// ================= ⚙ 設定（照 TikLive）：上面「設定／流程／更新包」；設定裡左邊分類（可搜尋）、右邊內容
const CATS=[['電腦',[['diag','🩺','診斷','一頁看完哪裡要處理','診斷 檢查 問題 健康 金鑰 硬碟 下載'],['perf','📊','電腦效能','CPU、記憶體、顯示卡、溫度','效能 cpu gpu vram 溫度 記憶體 顯示卡'],['hs','🤝','效能分配（Lv）','跟 SortCut、GoPro 分電腦','握手 lv 效能 分配 讓路 sortcut gopro fusion tiklive'],['cloud','☁','雲端更新','檢查新版、自動更新','雲端 更新 github 版本 自動'],['comfy','🎨','ComfyUI','網址、照片大小、逾時','comfyui 網址 埠 照片 縮小 像素 逾時 超時 失敗'],['mdl','🧩','模型檔','佔多少空間、刪沒用到的','模型 硬碟 空間 刪除 safetensors'],
  ['bg','🖥','後台狀態','暫停、取消、自動讓路','後台 背景 暫停 繼續 取消 讓路 cpu 排隊'],['log','📜','LOG','程式紀錄、錯誤','log 紀錄 錯誤 error']]],
 ['這支手機（只影響這個瀏覽器）',[['look','🎨','外觀與通知','深色／淺色、做好時震動／叮一聲','外觀 深色 淺色 主題 網頁版 手機版 通知 震動 聲音'],['login','🔒','登入','登出這支手機','登入 登出 pin 密碼']]],
 ['其他',[['lab','🧪','實驗工作區','還在試的功能','實驗 lab'],['help','📖','使用說明','怎麼改圖、兩個流程怎麼選、比較','說明 教學 怎麼用 比較 模型 改圖 裁切 畫質 通知'],['about','ℹ','關於','版本、更新紀錄','關於 版本 更新紀錄 changelog']]]];
const CATK=CATS.flatMap(([_g,L])=>L);
/* TKD-BEGIN（TikLive TK_V1.0.83） */
const TKD={d:null,root:null,q:"",u:"",o:"new",L:[],i:-1,rate:1,src:"ig",ty:"",per:"",sel:null};   /* TK_V1.0.82 src tk／ig、ty 影片／照片、per 期間、sel 多選 */
try{TKD.o=localStorage.getItem("tkdO")||"dl";TKD.rate=+(localStorage.getItem("tkdR")||1)||1;}catch(e){}
const tkdB=()=>"";
const tkdE=s=>String(s==null?"":s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const tkdT=s=>{s=Math.max(0,Math.floor(+s||0));return Math.floor(s/60)+":"+String(s%60).padStart(2,"0");};
const tkdDl=x=>x.dl||x.t;   /* TK_V1.0.83 下載時間 */
const tkdD=t=>{const d=new Date(t*1000),p=n=>String(n).padStart(2,"0");return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;};
const tkdF=(f,dl)=>U("/api/igfile",dl?{f,dl:1}:{f});
function tkdMount(root,src){TKD.root=root;src=src==="ig"?"ig":"tk";if(src!==TKD.src){TKD.u="";TKD.q="";}TKD.src=src;TKD.sel=null;TKD.d=null;root.innerHTML='<div class="tkdEmpty">讀取中…</div>';tkdLoad();}
async function tkdLoad(){let d=null;const s0=TKD.src;try{d=await api("/api/iglist");}catch(e){}if(s0!==TKD.src)return;
  if(!TKD.root||!TKD.root.isConnected)return;if(!d||!d.ok){TKD.root.innerHTML='<div class="tkdEmpty">讀取失敗</div>';return;}TKD.d=d;tkdDraw();}
function tkdRows(){const d=TKD.d;if(!d)return [];const q=TKD.q.trim().toLowerCase(),now=Date.now()/1000,P={d1:86400,d7:7*86400,d30:30*86400}[TKD.per]||0,day0=new Date(new Date().toDateString()).getTime()/1000;
  let L=d.items.filter(x=>(!TKD.u||x.u===TKD.u)&&(!TKD.ty||(x.k||"v")===TKD.ty)&&(!TKD.per||(TKD.per==="d0"?tkdDl(x)>=day0:tkdDl(x)>=now-P))&&(!q||x.f.toLowerCase().includes(q)||x.u.toLowerCase().includes(q)));
  const o=TKD.o;L.sort(o==="dl"?(a,b)=>tkdDl(b)-tkdDl(a)||a.f.localeCompare(b.f):o==="dlo"?(a,b)=>tkdDl(a)-tkdDl(b)||a.f.localeCompare(b.f):o==="old"?(a,b)=>a.t-b.t||a.f.localeCompare(b.f):o==="big"?(a,b)=>b.mb-a.mb:o==="small"?(a,b)=>a.mb-b.mb:o==="long"?(a,b)=>b.d-a.d:o==="user"?(a,b)=>a.u.localeCompare(b.u)||b.t-a.t:(a,b)=>b.t-a.t||a.f.localeCompare(b.f));return L;}
/* TK_V1.0.82 存到手機：一個一個觸發下載（間隔 0.8 秒，Chrome 第一次會問「允許下載多個檔案」） */
async function tkdSave(list){let n=0;for(const [f,src] of list){const a=document.createElement("a");a.href=tkdF(f,true,src);a.download=f;a.rel="noopener";a.style.display="none";document.body.appendChild(a);a.click();a.remove();n++;tkdGotAdd(src+"/"+f);await new Promise(r=>setTimeout(r,800));}return n;}
function tkdGot(){try{return JSON.parse(localStorage.getItem("tkd_got")||"[]");}catch(e){return [];}}
function tkdGotAdd(k){try{const g=tkdGot().filter(x=>x!==k);g.push(k);localStorage.setItem("tkd_got",JSON.stringify(g.slice(-600)));}catch(e){}}
function tkdDraw(){const d=TKD.d,R=TKD.root;if(!d||!R)return;const us={};d.items.forEach(x=>us[x.u]=(us[x.u]||0)+1);
  const ig=TKD.src==="ig",nv=d.items.filter(x=>(x.k||"v")==="v").length,got=new Set(tkdGot());
  R.innerHTML=`<div class="tkdTop"><input id="tkdQ" placeholder="🔍 搜尋帳號／檔名" value="${tkdE(TKD.q)}"><select id="tkdU"><option value="">全部帳號（${d.items.length}）</option>${Object.keys(us).sort().map(u=>`<option value="${tkdE(u)}"${u===TKD.u?" selected":""}>@${tkdE(u)}（${us[u]}）</option>`).join("")}</select>
<select id="tkdO">${[["dl","⬇ 下載日期 新→舊"],["dlo","⬇ 下載日期 舊→新"],["new",ig?"📅 發文日期 新→舊":"📅 影片日期 新→舊"],["old",ig?"📅 發文日期 舊→新":"📅 影片日期 舊→新"],["big","檔案大→小"],["small","檔案小→大"],["long","長→短"],["user","依帳號"]].map(([v,t])=>`<option value="${v}"${v===TKD.o?" selected":""}>${t}</option>`).join("")}</select>
<select id="tkdP">${[["","全部時間"],["d0","今天下載"],["d7","7 天內下載"],["d30","30 天內下載"]].map(([v,t])=>`<option value="${v}"${v===TKD.per?" selected":""}>${t}</option>`).join("")}</select>${ig?`<select id="tkdTy">${[["","照片＋影片"],["i",`🖼 照片（${d.items.length-nv}）`],["v",`🎬 影片（${nv}）`]].map(([v,t])=>`<option value="${v}"${v===TKD.ty?" selected":""}>${t}</option>`).join("")}</select>`:""}<button class="pill" id="tkdRe" title="重新讀取">↻</button></div>
<div class="tkdBar"><span id="tkdCnt"></span><button id="tkdSelB">☑ 選取</button><button id="tkdAllB">⬇ 這些全存到手機</button></div>
<div class="tkdG" id="tkdG"></div><div class="tkdSelBar" id="tkdSelBar" hidden><span id="tkdSelN"></span><button id="tkdSelAll">全選</button><button id="tkdSelSave">⬇ 存到手機</button><button id="tkdSelX">取消</button></div>`;
  const selPaint=()=>{const b=R.querySelector("#tkdSelBar");if(!b)return;b.hidden=!TKD.sel;R.classList.toggle("tkdSelOn",!!TKD.sel);if(TKD.sel){const mb=TKD.L.filter(x=>TKD.sel.has(x.f)).reduce((s,x)=>s+x.mb,0);R.querySelector("#tkdSelN").textContent=`已選 ${TKD.sel.size} 個 · ${mb.toFixed(1)} MB`;}};
  const draw=()=>{TKD.L=tkdRows();const g=R.querySelector("#tkdG");const mb=TKD.L.reduce((s,x)=>s+x.mb,0);R.querySelector("#tkdCnt").textContent=`${TKD.L.length} 個 · ${mb>=1000?(mb/1000).toFixed(1)+" GB":mb.toFixed(1)+" MB"}`;
    g.innerHTML=TKD.L.length?TKD.L.map((x,i)=>`<div class="tkdC${TKD.sel&&TKD.sel.has(x.f)?" on":""}" data-i="${i}"><div class="tkdIm"><img loading="lazy" alt="" src="${U("/api/igthumb",{f:x.f})}" onerror="this.style.visibility='hidden'"><em>${(x.k||"v")==="i"?"🖼":x.d?"▶ "+tkdT(x.d):"▶"}</em>${got.has(TKD.src+"/"+x.f)?'<i class="tkdGot" title="這支手機存過了">📲</i>':""}<s class="tkdCk">✓</s></div><b>@${tkdE(x.u)}</b><small>${TKD.o==="dl"||TKD.o==="dlo"?"⬇ "+tkdD(tkdDl(x)):tkdD(x.t)} · ${x.mb} MB</small></div>`).join(""):`<div class="tkdEmpty">沒有符合的${ig?"照片／影片":"影片"}</div>`;selPaint();};
  draw();R.querySelector("#tkdQ").oninput=e=>{TKD.q=e.target.value;draw();};R.querySelector("#tkdU").onchange=e=>{TKD.u=e.target.value;draw();};
  R.querySelector("#tkdP").onchange=e=>{TKD.per=e.target.value;draw();};const ty=R.querySelector("#tkdTy");if(ty)ty.onchange=e=>{TKD.ty=e.target.value;draw();};
  R.querySelector("#tkdSelB").onclick=()=>{TKD.sel=TKD.sel?null:new Set();draw();};R.querySelector("#tkdSelX").onclick=()=>{TKD.sel=null;draw();};
  R.querySelector("#tkdSelAll").onclick=()=>{if(!TKD.sel)return;const all=TKD.L.every(x=>TKD.sel.has(x.f));TKD.sel=all?new Set():new Set(TKD.L.map(x=>x.f));draw();};
  const saveL=async L=>{if(!L.length){if(typeof toast==="function")toast("沒有選到檔案");return;}const mb=L.reduce((s,x)=>s+x.mb,0);if(L.length>1&&!confirm(`存 ${L.length} 個檔（${mb.toFixed(1)} MB）到這支手機？\n第一次 Chrome 可能會問「允許下載多個檔案」，請按允許。`))return;
    const n=await tkdSave(L.map(x=>[x.f,TKD.src]));if(typeof toast==="function")toast(`⬇ 已開始存 ${n} 個到手機（下載資料夾）`);TKD.sel=null;tkdDraw();};
  R.querySelector("#tkdSelSave").onclick=()=>saveL(TKD.L.filter(x=>TKD.sel&&TKD.sel.has(x.f)));R.querySelector("#tkdAllB").onclick=()=>saveL(TKD.L.slice());
  R.querySelector("#tkdO").onchange=e=>{TKD.o=e.target.value;try{localStorage.setItem("tkdO",TKD.o);}catch(x){}draw();};R.querySelector("#tkdRe").onclick=tkdLoad;
  R.querySelector("#tkdG").onclick=e=>{const c=e.target.closest(".tkdC");if(!c)return;const x=TKD.L[+c.dataset.i];if(TKD.sel&&x){if(TKD.sel.has(x.f))TKD.sel.delete(x.f);else TKD.sel.add(x.f);c.classList.toggle("on",TKD.sel.has(x.f));selPaint();return;}tkdPlay(+c.dataset.i);};}
function tkdPlay(i){let ov=document.getElementById("tkdOv");if(!ov){ov=document.createElement("div");ov.id="tkdOv";ov.className="tkdOv";
    ov.innerHTML=`<div class="tkdPh"><button data-k="x">✕</button><div class="tkdNm"></div><a class="tkdDl" data-k="dl">⬇ 存到手機</a></div>
<div class="tkdSt"><video class="tkdV" playsinline autoplay></video><img class="tkdI" alt="" hidden><video class="tkdN" playsinline muted preload="auto"></video><div class="tkdSw"><b></b><small></small><i><u></u></i></div></div>
<input type="range" class="tkdSk" min="0" max="1000" value="0"><div class="tkdCt"><button data-k="pp">⏯</button><button data-k="prev">⏮</button><button data-k="next">⏭</button><select class="tkdRt">${[0.5,1,1.5,2,3].map(x=>`<option value="${x}"${x===TKD.rate?" selected":""}>${x}×</option>`).join("")}</select><span class="tkdTm">0:00 / 0:00</span></div>
<div class="tkdTip">畫面上左右拖＝快轉／倒退（拖得快、拖得長＝跳得遠，慢慢拖＝細調）；上下滑＝換下一部／上一部</div>`;
    document.body.appendChild(ov);tkdBind(ov);try{if(typeof vgBackPush==="function")vgBackPush(fb=>{if(fb===true&&ov.isConnected)ov.remove();});}catch(e){}}
  TKD.i=i;const x=TKD.L[i];if(!x)return;const v=ov.querySelector(".tkdV"),im=ov.querySelector(".tkdI"),isI=(x.k||"v")==="i";TKD.img=isI;ov.classList.toggle("tkdImg",isI);
  if(isI){v.pause();v.removeAttribute("src");v.load();v.hidden=true;im.hidden=false;im.src=tkdF(x.f);}else{im.hidden=true;im.removeAttribute("src");v.hidden=false;v.src=tkdF(x.f);v.playbackRate=TKD.rate;v.play().catch(()=>{});}
  ov.querySelector(".tkdNm").innerHTML=`<b>@${tkdE(x.u)}</b><small>${i+1}／${TKD.L.length} · 📅 ${tkdD(x.t)} · ⬇ ${tkdD(tkdDl(x))} · ${x.mb} MB</small>`;
  const a=ov.querySelector(".tkdDl");a.href=tkdF(x.f,true);a.setAttribute("download",x.f);
  const n=TKD.L[i+1],nv=ov.querySelector(".tkdN");if(n&&(n.k||"v")==="v"){nv.src=tkdF(n.f);nv.load();}else{nv.removeAttribute("src");if(n){const p=new Image();p.src=tkdF(n.f);}}}   /* 下一部先載好 */
function tkdBind(ov){const v=ov.querySelector(".tkdV"),sk=ov.querySelector(".tkdSk"),tm=ov.querySelector(".tkdTm"),st=ov.querySelector(".tkdSt"),box=ov.querySelector(".tkdSw");
  const close=()=>{v.pause();v.removeAttribute("src");v.load();ov.remove();};
  v.ontimeupdate=()=>{if(!v.duration)return;if(!sk._drag)sk.value=Math.round(v.currentTime/v.duration*1000);tm.textContent=tkdT(v.currentTime)+" / "+tkdT(v.duration);};
  v.onended=()=>{if(TKD.i+1<TKD.L.length)tkdPlay(TKD.i+1);};v.onratechange=()=>{};
  sk.oninput=()=>{sk._drag=true;if(v.duration)v.currentTime=sk.value/1000*v.duration;};sk.onchange=()=>{sk._drag=false;};
  ov.querySelector(".tkdRt").onchange=e=>{TKD.rate=+e.target.value;v.playbackRate=TKD.rate;try{localStorage.setItem("tkdR",TKD.rate);}catch(x){}};
  ov.onclick=e=>{const b=e.target.closest("[data-k]");if(!b)return;const k=b.dataset.k;if(k==="dl")return;e.preventDefault();
    if(k==="x")close();else if(k==="pp")v.paused?v.play():v.pause();else if(k==="next"&&TKD.i+1<TKD.L.length)tkdPlay(TKD.i+1);else if(k==="prev"&&TKD.i>0)tkdPlay(TKD.i-1);};
  let g=null;   /* 跟影片快速瀏覽同一套：左右拖快轉（越快越遠，一次最多 10 分鐘或整部長度）、上下滑換部、點一下暫停 */
  st.addEventListener("pointerdown",e=>{if(TKD.img&&e.button===0){g={id:e.pointerId,x0:e.clientX,y0:e.clientY,t0:performance.now(),img:true};return;}if(!v.duration||e.button>0)return;g={id:e.pointerId,x0:e.clientX,y0:e.clientY,x:e.clientX,t:performance.now(),t0:performance.now(),base:v.currentTime,acc:0,on:false,max:Math.min(600,v.duration)};});
  st.addEventListener("pointermove",e=>{if(!g||e.pointerId!==g.id||g.img)return;const dx=e.clientX-g.x0,dy=e.clientY-g.y0;
    if(!g.on){if(Math.abs(dy)>14&&Math.abs(dy)>Math.abs(dx)){g.vert=true;return;}if(Math.abs(dx)<14||Math.abs(dx)<Math.abs(dy)*1.3)return;g.on=true;try{st.setPointerCapture(e.pointerId);}catch(x){}g.x=e.clientX;g.t=performance.now();box.style.display="block";}
    const now=performance.now(),ddx=e.clientX-g.x,dt=Math.max(8,now-g.t);g.x=e.clientX;g.t=now;const W=Math.max(200,st.getBoundingClientRect().width),sp=Math.abs(ddx)/dt,kk=Math.min(1,Math.max(0.12,(sp-0.05)/1.3));
    g.acc=Math.max(-g.max,Math.min(g.max,g.acc+ddx/W*g.max*1.6*kk));const tgt=Math.max(0,Math.min(v.duration-0.3,g.base+g.acc)),d=tgt-g.base,a=Math.abs(Math.round(d));
    box.querySelector("b").textContent=(d<0?"⏪ −":"⏩ +")+(a>=60?Math.floor(a/60)+":"+String(a%60).padStart(2,"0"):a+" 秒");box.querySelector("small").textContent=tkdT(tgt)+" / "+tkdT(v.duration);
    box.querySelector("u").style.width=Math.round(Math.abs(g.acc)/g.max*100)+"%";e.preventDefault();});
  st.addEventListener("pointerup",e=>{if(!g||e.pointerId!==g.id)return;const w=g;g=null;
    if(w.img){const dx=e.clientX-w.x0,dy=e.clientY-w.y0,ax=Math.abs(dx),ay=Math.abs(dy);if(Math.max(ax,ay)>50){const nx=(ax>ay?dx<0:dy<0);if(nx&&TKD.i+1<TKD.L.length)tkdPlay(TKD.i+1);else if(!nx&&TKD.i>0)tkdPlay(TKD.i-1);}return;}   /* 照片：左右或上下滑換張 */
    if(w.on){box.style.display="none";if(Math.abs(w.acc)>=0.5)v.currentTime=Math.max(0,Math.min(v.duration-0.3,w.base+w.acc));return;}
    const dy=e.clientY-w.y0;if(Math.abs(dy)>50&&performance.now()-w.t0<900){if(dy<0&&TKD.i+1<TKD.L.length)tkdPlay(TKD.i+1);else if(dy>0&&TKD.i>0)tkdPlay(TKD.i-1);return;}
    if(Math.abs(e.clientX-w.x0)<10&&Math.abs(dy)<10)v.paused?v.play():v.pause();});
  st.addEventListener("pointercancel",()=>{if(g&&g.on)box.style.display="none";g=null;});}

/* V0.3.35 📸 IG：貼 IG 貼文／Reels 網址 → 電腦下載（照片 JPG、影片 MP4）；下面是 IG 資料夾（從 TikLive 搬過來，功能一樣） */
function tkdSyncOn(){try{return localStorage.getItem("tkd_sync")!=="0";}catch(e){return true;}}
function tkdPend(){try{return JSON.parse(localStorage.getItem("tkd_pend")||"[]");}catch(e){return [];}}
function tkdPendSet(L){try{localStorage.setItem("tkd_pend",JSON.stringify(L));}catch(e){}}
let tkdPendBusy=false;
async function tkdPendTick(d){if(tkdPendBusy)return;let P=tkdPend();if(!P.length)return;const now=Date.now()/1000;P=P.filter(p=>now-p.t0<6*3600);
  if(!d){try{d=await api("/api/iginfo");}catch(e){return;}}if(!d)return;tkdPendBusy=true;
  try{const got=new Set(tkdGot()),todo=[];for(const r of (d.done||[]))for(const p of P)if(r.ok&&r.t>=p.t0&&p.txt.includes(r.url))for(const f of (r.files||(r.file?[r.file]:[]))){const k=(r.src||"ig")+"/"+f;if(!got.has(k)&&!todo.some(x=>x[0]===f)){todo.push([f,r.src||"ig"]);}}
    if(todo.length){const n=await tkdSave(todo);toast(`📲 已存 ${n} 個到這支手機（下載資料夾）`,5000);if(CUR==="ig")tkdLoad();}
    const busy=d.run||(d.q||[]).length;if(!busy)P=P.filter(p=>now-p.t0<120&&!(d.done||[]).some(r=>r.t>=p.t0&&p.txt.includes(r.url)));tkdPendSet(P);}finally{tkdPendBusy=false;}}
if(!window.__tkdPendIv){window.__tkdPendIv=setInterval(()=>{if(document.hidden||!tkdPend().length)return;tkdPendTick();},15000);document.addEventListener("visibilitychange",()=>{if(!document.hidden&&tkdPend().length)setTimeout(()=>tkdPendTick(),1500);});}
async function igckPaint(){const e=$("#igckS");if(!e)return;let j=null;try{j=await api("/api/igck");}catch(x){}e.textContent=j&&j.set?"（✔ 已存）":"（沒存）";}
async function rIg(again){if(again)return;
  $('#v').innerHTML=`<div class="gcard igdA"><b style="color:var(--strong)">📸 IG 下載</b><p class="mu" style="font-size:13px;margin:6px 0 10px">在 IG 按「分享 → 複製連結」，貼上後送出（可一次貼很多個）。照片存 JPG、影片存 MP4，下載到電腦的 IG 資料夾；只抓公開貼文。</p>
<textarea id="igt" placeholder="https://www.instagram.com/p/… 或 https://www.instagram.com/reel/…"></textarea><button class="btn" id="igb">送出</button><button class="btn s" id="igp">📋 從剪貼簿貼上並送出</button><div id="igm"></div>
<label class="tkdSyncL"><input type="checkbox" id="tkdSync"> 📲 電腦下載好，也自動存一份到這支手機（下載資料夾）</label>
<details class="igck" id="igck"><summary>🔐 IG 登入（選用）：IG 擋沒登入的下載時用 <small id="igckS"></small></summary>
<div class="igckB"><p>IG 最近常擋「沒登入」的下載。可以把你<b>自己的 IG 登入 Cookie（sessionid）</b>貼在這裡，下載時就用它。<b>不需要也不要給任何人密碼</b>；Cookie 只存在這台電腦，網頁不會讀回來。建議用<b>小帳</b>，下載太多 IG 可能暫時限制那個帳號。</p>
<ol><li>在<b>電腦的 Chrome</b> 打開 instagram.com，用你的帳號登入</li><li>按 <b>F12</b> → 上面選「<b>Application</b>（應用程式）」→ 左邊 <b>Cookies → https://www.instagram.com</b></li><li>找名稱 <b>sessionid</b>，點兩下右邊的值 → 全選複製</li><li>貼到下面按「儲存」（之後要停用就按「刪掉」）</li></ol>
<input id="igckV" type="password" autocomplete="off" placeholder="貼上 sessionid 的值"><div class="igckR"><button class="btn" id="igckSave">儲存</button><button class="btn s" id="igckDel">刪掉</button></div></div></details>
<div class="igdDir">📁 <span id="igdD"></span><button id="igdC">改資料夾</button></div></div><div class="gcard" id="igd" style="margin-top:10px"></div>`;
  igckPaint();api("/api/igdir").then(j=>{const e=$("#igdD");if(e&&j)e.textContent=j.dir||""}).catch(()=>{});
  $("#igdC").onclick=async()=>{const cur=$("#igdD").textContent;const v=prompt("IG 下載到電腦的哪個資料夾？（完整路徑，例如 E:\\IGDownloader；清空＝預設）",cur);if(v===null)return;const j=await api("/api/igdir",{dir:v});toast((j&&j.message)||"",4000);if(j&&j.ok){$("#igdD").textContent=j.dir;tkdLoad();}};
  const sy=$("#tkdSync");sy.checked=tkdSyncOn();sy.onchange=()=>{try{localStorage.setItem("tkd_sync",sy.checked?"1":"0");}catch(e){}};
  $("#igckSave").onclick=async()=>{const v=$("#igckV").value.trim();if(!v){toast("先貼上 sessionid");return;}const j=await api("/api/igck",{v});toast((j&&j.ok?"":"✖ ")+((j&&j.message)||""),4000);if(j&&j.ok){$("#igckV").value="";igckPaint();}};
  $("#igckDel").onclick=async()=>{if(!confirm("刪掉存在電腦裡的 IG 登入 Cookie？"))return;const j=await api("/api/igck",{v:""});toast((j&&j.message)||"已刪掉");igckPaint();};
  const show=(ok,t)=>{const m=$("#igm");if(!m)return;m.style.display="block";m.style.whiteSpace="pre-line";m.className=ok?"ok":"err";m.textContent=t;};
  const send=async v=>{if(!v.trim())return show(false,"請先貼上網址");show(true,"送出中…");let j=null;try{j=await api("/api/igadd",v,true);}catch(e){return show(false,"✖ 連不到電腦");}
    show(!!(j&&j.ok),((j&&j.ok)?"✔ ":"✖ ")+((j&&j.message)||""));if(!j||!j.ok)return;$("#igt").value="";
    const t0=Date.now()/1000-5,base=j.message;if(tkdSyncOn()){const P=tkdPend();P.push({t0,txt:v});tkdPendSet(P.slice(-20));}
    for(let k=0;k<600;k++){await new Promise(r=>setTimeout(r,2000));let d=null;try{d=await api("/api/iginfo");}catch(e){}if(!d)continue;if(tkdSyncOn())await tkdPendTick(d);
      const D=(d.done||[]).filter(x=>x.t>=t0);show(!D.some(x=>!x.ok),base+(D.length?"\n"+D.map(x=>x.message).join("\n"):"")+(d.run?"\n⏳ 下載中…":""));if(!d.run&&D.length){if(CUR==="ig")tkdLoad();const F=D.filter(x=>!x.ok&&x.url).map(x=>x.url);if(F.length&&$("#igm")){const b=document.createElement("button");b.className="btn s";b.style.marginTop="8px";b.textContent=`🔁 重試失敗的 ${F.length} 個`;b.onclick=()=>{b.remove();send(F.join("\n"))};$("#igm").after(b)}break;}}};   // V0.3.56 失敗的一鍵重試
  $("#igb").onclick=()=>send($("#igt").value);$("#igp").onclick=async()=>{try{const v=await navigator.clipboard.readText();$("#igt").value=v;send(v);}catch(e){show(false,"瀏覽器不允許讀剪貼簿，請長按格子手動貼上");}};
  tkdMount($("#igd"),"ig");}
/* TKD-END */
async function rSet(again){if(again){if(S.stab==='set'&&(S.scat==='perf'||S.scat==='bg')&&$('#sbody'))drawSetCat(true);return}
  $('#v').innerHTML=`<div class="stabs"><button data-p="set">設定</button><button data-p="wf">流程</button><button data-p="ppl">人物庫</button><button data-p="upd">更新包</button></div><div id="spane"></div>`;
  $$('.stabs button').forEach(b=>{b.classList.toggle('on',b.dataset.p===S.stab);b.onclick=()=>{S.stab=b.dataset.p;LS.set('stab',S.stab);rSet()}});
  if(S.stab==='wf')return wfPane();if(S.stab==='upd')return updPane();if(S.stab==='ppl')return pplPane();
  $('#spane').innerHTML=`<div class="s2"><div class="scat" id="scat"></div><div id="sbody"></div></div>`;drawScat();drawSetCat()}
function drawScat(){const q=S.setQ.trim().toLowerCase();const vis=([k,ic,n,d,kw])=>!q||(n+d+kw).toLowerCase().includes(q);
  $('#scat').innerHTML=`<input class="ssearch" id="ssq" placeholder="🔍 搜尋設定" value="${esc(S.setQ)}">`+CATS.map(([g,L])=>{const V=L.filter(vis);return V.length?`<div class="sch">${esc(g)}</div>`+V.map(([k,ic,n,d])=>`<button data-c="${k}" class="${k===S.scat?'on':''}">${ic} ${esc(n)}<small>${esc(d)}</small></button>`).join(''):''}).join('')||'<div class="mu" style="padding:6px">找不到</div>';
  const i=$('#ssq');i.oninput=()=>{S.setQ=i.value;const V=CATK.filter(vis);if(V.length&&!V.find(x=>x[0]===S.scat)){S.scat=V[0][0];drawSetCat()}drawScat();const n=$('#ssq');n.focus();n.setSelectionRange(n.value.length,n.value.length)};
  $$('#scat [data-c]').forEach(b=>b.onclick=()=>{S.scat=b.dataset.c;LS.set('scat',S.scat);drawScat();drawSetCat();scrollTo(0,0)})}
const segH=(k,cur,opts)=>`<div class="seg" data-sk="${k}">${opts.map(([v,n])=>`<button data-v="${esc(v)}" class="${String(cur)===String(v)?'on':''}">${esc(n)}</button>`).join('')}</div>`;
async function setVal(k,v){const r=await api('/api/settings',{[k]:v});toast(r.ok&&(r.changed||[]).includes(k)?'✔ 已儲存':'沒存到')}
async function drawSetCat(again){const sb=$('#sbody');if(!sb)return;const c=S.scat;sb.onclick=null;
  if(c==='perf'){await pfLoad(sb);return}
  if(c==='hs'){await hsGet();const I=HSI||{};sb.innerHTML=`<h2 class="stt">🤝 效能分配（Lv）</h2><div class="snote">${I.ok?`這邊 Lv${I.lv}${I.cap!=null?'，現在分到 '+Math.round(I.cap)+'%':''}。${esc(I.why||'')}`:'握手還沒開始'}</div><div class="snote">同一台電腦的 ComfyRemote、SortCut、GoPro Fusion 360 互相讓：ComfyRemote 在生圖時最優先，平常另外兩個照比例分，永遠留一點給你用電腦。設定三個程式共用。</div><button class="btn" id="hsGo" style="margin-top:10px">打開 Lv 畫面（勾誰參與、調分配、Lv 1～10）</button>`;$('#hsGo').onclick=hsOpen;return}   // V0.3.60
  if(c==='cloud'){S.stab='upd';LS.set('stab','upd');rSet();return}
  if(c==='bg'){if(!again)sb.innerHTML='<div class="empty">讀取中…</div>';sb.onclick=bgsClick;await bgsLoad(sb);return}
  if(again)return;
  if(c==='help'){sb.innerHTML=`<h2 class="stt">📖 使用說明</h2>
    <section class="ssec"><h3>🎯 四個模式（生圖頁最上面）</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    <b>🎨 改一張圖</b>：GROK（效果最好）或 Qwen（最快），下面有詳細說明。<br>
    <b>🧩 兩張圖合併</b>：圖一放人物，圖二放衣服／場景／姿勢／另一個人，點「👗 換衣服／🏞 換場景／🧍 照動作／👫 兩人合照／🛍 拿著商品／🎨 照畫風」就填好提示詞。圖一可以選好幾個人、圖二可以選好幾件衣服，每種組合各做一張。<br>
    <b>🎬 照片變影片</b>：一張照片＋點一個「常用動作」（或自己打），選長度（先用 3～4 秒）和畫質（先用 ⚡ 快）。要更像本人用「臉穩定」版。<br>
    <b>🎞 首尾幀影片</b>：🎬 首幀＝開始畫面、🏁 尾幀＝結束畫面，打一句中間發生什麼。最簡單：只選開始畫面就按開始，會先用 GROK 照那句話改出結束畫面，再自動做影片（🪄 一鍵首尾幀）。<br>
    <b>接龍做長片</b>：影片做好按「⏭ 接下一段」，最後一格當下一段的開始。</small></div></section>
    <section class="ssec"><h3>🧰 圖生圖工具箱（改一張圖模式）</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    <b>🕘 最近</b>：你最近用過的工具。<br>
    <b>🧑 人像</b>：證件照（選底色、自動框 3:4）、自然美顏（自動輕輕修）、換表情、🤸 換姿勢、💇 換髮型、💄 換妝容、年齡變化、身材微調、頭像／貼圖、三視圖、📸 寫真組圖（6 場景）、😆 LINE 貼圖組（8 張，綠幕可一鍵存透明 PNG）。<br>
    <b>🧹 修圖</b>：🧽 消除（塗掉不要的，模型會看到灰色那塊補背景）、📦 放進東西（參考圖＋塗位置）、🔍 變清楚、🖼 老照片修復、✂ 去背（存透明 PNG）、🎞 濾鏡調色。<br>
    <b>🔤 文字</b>：改字（可以寫「舊字→新字」只改那段）、加標題。<b>🎨 場景風格</b>：重新打光、換天空、換季節天氣、室內換風格、換色／材質、線稿上色、畫變照片、寵物、🛍 商品組圖。<br>
    <b>小幫手</b>：「🪄 補完整」幫短句補上要保持不變的地方；「改動幅度」🪶 輕輕修＝保留比較多原圖；看大圖「🎲 再 3 張」換種子多做幾張挑；改壞了照片下面「↩ 換回上一張」。<br>
    <b>變化寫法</b>：提示詞寫「穿{紅色|藍色|白色}洋裝」會展開成 3 張各做一次（可以疊好幾組，最多 24 張）。<br>
    <b>局部塗抹</b>：可以拉框、放大 2×／3× 塗細節、調邊緣柔和、反過來（塗的保留）。</small></div></section>
    <section class="ssec"><h3>🧩 合併與 🎬 影片的進階</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    合併有 🏆 GROK 合併（效果好）和 ⚡ Qwen 合併（快），可以「🔁 兩個都跑」。換衣服可以「只換：上衣／褲子／鞋子…」，換場景可以選「放哪裡」。「三張圖合併」＝人物＋衣服＋場景一次換好。合併的圖一可以「🖌 只改圖一的哪裡」保護臉和背景。圖二可以一次選好幾件衣服；「🕘 從最近用過的挑」也列出 👤 人物庫。<br>
    影片：「🔁 無縫循環」做可以一直重播的影片；步數 ⚡ 4 步快一倍；🎵 配樂；🗣 加一句台詞；🎞 首尾幀只給開始畫面會自動先用 GROK 做結束畫面（🪄 一鍵首尾幀）。做好的影片可以「⏭ 接下一段」「🖼 最後一格」「🎞 存 GIF」。<br>
    排隊：「⏫ 先做這個」插隊；「⏹ 取消這一批」一次取消同一次送出的全部、「⏹ 全部取消」取消所有排隊的（上面「🎨 排隊」浮動視窗也有），會再問正在跑的那張要不要一起停。做的時候卡片會出現即時預覽（ComfyUI 要開預覽，🩺 診斷會提醒）。失敗的會寫「💡 怎麼辦」。</small></div></section>
    <section class="ssec"><h3>🎨 改一張照片（最常用）</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    ① 選照片；要裁切或轉正按照片左下角「✂ 裁切」；只想改一小塊（衣服、背景某處）按右下角「🖌 局部」塗那一塊，其他地方保證跟原圖一模一樣。<br>② 打想怎麼改，或點「🪄 常用改法」挑一句（可以疊好幾句）；換衣服、換背景時打開「🔒 保持臉不變」。<br>
    ③ 點大按鈕選流程：🏆 GROK（效果最好）或 ⚡ Qwen（最快）；拿不定主意就按「🔁 兩個都跑」。「畫質」選 ⚡快／標準／🔍精細。<br>
    ④ 按開始。「⏳ 製作中」旁邊會寫幾點做完；做好手機會震一下、叮一聲，可以先去做別的事。<br>
    ⑤ 點結果放大：拉桿跟原圖比；兩個流程都做了就按「🆚 跟另一個比」。不滿意按「🏆 用 GROK 做一次」或「✏ 拿這張再改」接著改。</small></div></section>
    <section class="ssec"><h3>🧰 進階改法</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    <b>🖌 局部</b>：照片右下角，塗要改的那一塊，塗以外的地方一個像素都不動。按「🔁 反過來」＝塗的保留（塗人物 → 只換背景，最穩）。<br>
    <b>↔ 擴圖</b>：「✂ 裁切」裡選 16:9、9:16…，把畫面往外補（直的變橫的、做桌布）。<br>
    <b>📎 參考圖</b>：再給一張衣服／商品／地點／畫風的圖，提示詞寫「參考圖」指它，例如「把衣服換成參考圖裡的衣服」。<br>
    <b>📌 配方</b>：常做的改法（流程＋提示詞＋畫質＋保持臉）存起來，生圖頁最上面點一下套好。<br>
    <b>📚 一次試很多種</b>：常用改法任一類按「📚 這類全部各做一張」，或勾「多篇文字」（每篇用空行隔開，各做一次；多張圖時可以切換順序）；歷史紀錄會收成一組方便比。<br>
    <b>🖼 存前後對比圖</b>：看大圖時按，原圖和結果拼成一張存到手機。</small></div></section>
    <section class="ssec"><h3>🧪 比較模型（整晚跑、早上看）</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    ① 「🧪 比較」選好幾張照片、打一句提示詞。<br>② 勾想比的模型（或按「⭐ 推薦」）。點開一列可以看說明、授權、缺哪些模型、調參數；虛線框是「同模型不同設定」，也可以自己「＋ 另存成一欄」。<br>
    ③ 按「▶ 開始比較」：缺的模型自動下載，下載好就接著跑；同一個模型的照片連著跑。按完就可以去睡。<br>④ 早上生圖頁最上面會提示「比較做完了」，點進去「📱 逐張看」左右滑、點星星打分數；「🎯 甜蜜點」幫你挑夠好又最快的。<br>
    ⑤ 「🖼 存成一張比較圖」「📄 分數表」可以傳給別人；「↻ 失敗的重跑」補好模型後重跑。</small></div></section>
    <section class="ssec"><h3>⚡ GROK 再快一點（進階，要動電腦上的 ComfyUI）</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    GROK 是 20GB 的 Qwen-Image-Edit 2511，3060 的 12GB 放不下，每一步都要從記憶體搬，所以一張要 40 秒。三個方法，由簡單到難：<br>
    ① 「🩺 診斷」看「ComfyUI 啟動參數」有沒有黃色：拿掉 --lowvram／--reserve-vram 太大這類設定。<br>
    ② Sage Attention：ComfyUI 的 Python 環境裝 sageattention，啟動參數加 --use-sage-attention，網路實測快 10～14%；出現全黑的圖就拿掉。<br>
    ③ Nunchaku 4-bit：裝 ComfyUI-nunchaku 自訂節點，下載 nunchaku_qwen_image_edit_2511_balance_int4（RTX 30 系列要 int4 版，約 12GB），一樣的模型縮成 4-bit；網路上在高階顯卡測是快好幾倍，3060 還沒有公開數字，要試了才知道。裝好後「🩺 診斷」會顯示「已裝」，再叫 AI 幫你做成流程。</small></div></section>
    <section class="ssec"><h3>用哪個流程（你實測後選的）</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    🏆 效果最好：GROK 改圖（INT8 快），一張約 40 秒。⚡ 速度最快、效果可以：Qwen 2.1 Turbo 改圖，一張約 24 秒。<br>
    以前試過的其他模型可以在「設定 → 🧩 模型檔 → 🧹 精簡」一次收掉、刪掉模型省空間。</small></div></section>
    <section class="ssec"><h3>其他好用的</h3><div class="srow"><small style="font-size:13.5px;line-height:1.7;color:var(--text)">
    <b>提示詞</b>：打字框寫這次臨時想要的；下面四個分頁——🏷 積木（自己建分類和選項，點選就加在後面；長按改；「📚 選了幾個就各做一張」）、📚 範本（整篇很多段存起來，點一下帶上來）、🧰 工具箱、⭐ 常用（存這句、最近用過）；送出前看「📝 會送出 N 個提示詞」。勾「多篇文字」，每篇用空行隔開，各做一次。看大圖「📌 存提示詞」可以把好的那句存成範本或積木。<br>排隊：卡片上「⏹ 取消這一批」、上面「⏹ 全部取消」。右上角「Lv」：跟 SortCut、GoPro 分電腦效能。👤 人物庫：提示詞寫 a01 自動帶他的照片。<br>
    任何結果點開都能打 1～5 星，歷史紀錄「⭐ 高分」只看好的。臨時送的單張會插在比較那一大批前面先跑。</small></div></section>`;$$('.ssec',sb).forEach((x,i)=>{const h=x.querySelector('h3');if(!h)return;h.style.cursor='pointer';const set=o=>{x.querySelectorAll('.srow').forEach(r=>r.style.display=o?'':'none');h.dataset.o=o?'1':'';h.textContent=h.textContent.replace(/^[▸▾] /,'');h.textContent=(o?'▾ ':'▸ ')+h.textContent};set(i<2);h.onclick=()=>set(!h.dataset.o)});return}
  if(c==='diag'){sb.innerHTML='<h2 class="stt">🩺 診斷</h2><div class="empty">檢查中…</div>';const r=await api('/api/diag');if(S.scat!=='diag')return;
    const I={ok:'✔',warn:'⚠',bad:'✖'},C={ok:'var(--green)',warn:'var(--orange)',bad:'var(--red)'};
    sb.innerHTML=`<h2 class="stt">🩺 診斷</h2><section class="ssec">${(r.items||[]).map(x=>`<div class="srow"><div class="row"><b style="margin:0;color:${C[x.st]}">${I[x.st]} ${esc(x.title)}</b></div><div style="margin-top:4px;word-break:break-all">${lnk(x.val)}</div>${x.tip?`<small>👉 ${esc(x.tip)}</small>`:''}</div>`).join('')||'<div class="empty">'+esc(r.message||'讀不到')+'</div>'}</section><button class="btn s" id="dgr">↻ 再檢查一次</button>`;
    $('#dgr').onclick=()=>drawSetCat();return}
  if(c==='mdl'){sb.innerHTML='<h2 class="stt">🧩 模型檔</h2><div class="empty">讀取中…（ComfyUI 要開著）</div>';const r=await api('/api/mdl');if(S.scat!=='mdl')return;
    if(!r.ok){sb.innerHTML=`<h2 class="stt">🧩 模型檔</h2><div class="empty">${esc(r.message||'讀不到')}</div>`;return}
    const F=r.files||[],un=F.filter(f=>!f.used.length),ub=un.reduce((a,f)=>a+f.size,0);let flt=LS.get('mdl_flt','all');
    const draw=()=>{const L=flt==='un'?un:F;sb.innerHTML=`<h2 class="stt">🧩 模型檔</h2><section class="ssec"><div class="srow"><b>🧹 精簡：只留 GROK 改圖（INT8 快）和 Qwen 2.1 Turbo 改圖</b><small>把試過但不要的流程收掉（可以救回來），只有它們用到的模型檔刪掉省空間；你自己的其他流程（GROK 改圖（快速）、H3 影片…）預設留著，清單裡可以一個一個勾要不要也收掉，旁邊寫多省幾 GB。按了先給你看清單再確認。</small><button class="btn s" id="slimb" style="margin-top:8px">🧹 看要刪哪些</button><div id="slimp"></div></div></section><section class="ssec"><div class="srow"><b>總共 ${F.length} 個、${fmtB(r.total)}</b>
      <small>${Object.entries(r.free||{}).map(([d,f])=>`${esc(d)} 剩 ${fmtB(f)}`).join('　')}　·　沒有任何流程用到的：${un.length} 個、${fmtB(ub)}</small>
      <div class="seg" style="margin-top:8px;display:inline-flex"><button data-mf="all" class="${flt==='all'?'on':''}">全部</button><button data-mf="un" class="${flt==='un'?'on':''}">沒用到的</button></div></div></section>
      <section class="ssec">${L.map(f=>`<div class="srow mdlr"><div class="row"><b class="grow" style="margin:0;word-break:break-all">${esc(f.name)}</b><span style="font-weight:800">${fmtB(f.size)}</span></div>
        <small>${esc(f.kind)} · ${f.used.length?'用在：'+f.used.map(esc).join('、'):'<span style="color:var(--orange)">沒有流程用到</span>'}</small>
        <div class="row" style="margin-top:6px"><span class="grow mu" style="font-size:11px;word-break:break-all">${esc(f.path)}</span><button class="pill er" data-md="${esc(f.path)}" data-mu="${f.used.length}">🗑 刪</button></div></div>`).join('')||'<div class="empty">沒有</div>'}</section>
      <div class="snote">刪了就真的刪掉（不會進資源回收筒）。之後要用，流程頁按「⬇ 下載缺的模型」可以再下載。</div>`;
      $$('[data-mf]',sb).forEach(b=>b.onclick=()=>{flt=b.dataset.mf;LS.set('mdl_flt',flt);draw()})};
    draw();let SX=[];const slimUI=async()=>{const box=$('#slimp');box.innerHTML='<div class="mu">計算中…</div>';const P=await api('/api/mdl',{a:'slim_plan',extra:SX});if(!P.ok){box.innerHTML='';return toast(P.message||'失敗',5000)}
        box.innerHTML=`<div class="slim"><div class="mu" style="font-weight:700">一定收掉（以前試過的）：${P.wfs.filter(n=>!SX.includes(n)).map(esc).join('、')||'（沒有，已經收過了）'}</div>
         ${P.others.length?`<div class="mu" style="font-weight:700;margin-top:8px">也要收掉嗎？（你自己的流程，預設不勾）</div>${P.others.concat(SX.map(n=>({name:n,on:1}))).filter((x,i,A)=>A.findIndex(y=>y.name===x.name)===i).map(o=>`<label class="row slr"><input type="checkbox" data-sx="${esc(o.name)}" ${SX.includes(o.name)?'checked':''}><span class="grow">${esc(o.name)}</span>${o.size?`<b>多省 ${fmtB(o.size)}</b>`:'<span class="mu">不多省</span>'}</label>`).join('')}`:''}
         <div style="margin-top:8px"><b>會刪 ${P.files.length} 個模型檔，共 ${fmtB(P.total)}</b></div><div class="mu" style="font-size:12px;max-height:140px;overflow:auto">${P.files.map(f=>esc(f.name)+' · '+fmtB(f.size)).join('<br>')||'（沒有）'}</div>
         <div class="mu" style="margin-top:6px">留下：${P.keep.map(esc).join('、')}</div>
         <div class="row" style="margin-top:8px"><button class="btn s" id="slimgo" ${P.wfs.length||P.files.length?'':'disabled'}>🗑 確定收掉 ${P.wfs.length} 個流程、刪 ${fmtB(P.total)}</button><button class="pill" id="slimx">先不要</button></div></div>`;
        $$('[data-sx]',box).forEach(c=>c.onchange=()=>{SX=$$('[data-sx]:checked',box).map(x=>x.dataset.sx);slimUI()});$('#slimx').onclick=()=>{SX=[];box.innerHTML=''};
        $('#slimgo').onclick=async()=>{if(!confirm(`最後確認：模型檔刪了就沒了（流程移到 workflows\\_old 可以救回來）。\n收掉 ${P.wfs.length} 個流程、刪 ${P.files.length} 個模型（${fmtB(P.total)}）？`))return;toast('精簡中…',20000);const x=await api('/api/mdl',{a:'slim',extra:SX});toast(x.message||'失敗',6000);SX=[];drawSetCat()}};
    sb.onclick=async e=>{if(e.target.closest('#slimb')){slimUI();return}
      const b=e.target.closest('[data-md]');if(!b)return;const used=+b.dataset.mu;
      if(!confirm((used?'⚠ 這個模型有流程在用，刪了那些流程就要重新下載才能跑。\n\n':'')+'確定刪掉？\n'+b.dataset.md))return;b.disabled=true;
      const x=await api('/api/mdl',{a:'del',path:b.dataset.md});toast(x.message||'失敗',4000);if(x.ok)drawSetCat()};return}
  if(c==='comfy'){const [s,g]=await Promise.all([api('/api/settings'),api('/api/gen')]);const C=s.cfg||{},k=g.comfy||{};
    sb.innerHTML=`<h2 class="stt">🎨 ComfyUI</h2><section class="ssec"><div class="srow"><b>連線</b>${k.ok?`<span style="color:var(--green);font-weight:800">● 已連上</span> ${esc(k.url)}<small>ComfyUI ${esc(k.ver)} · ${esc(k.gpu)}${k.vram&&k.vram[1]?' · VRAM 剩 '+fmtB(k.vram[0])+'／'+fmtB(k.vram[1]):''}</small>`:`<span style="color:var(--red);font-weight:800">● 連不到</span><small>${esc(k.err||'')}</small>`}</div>
     <div class="srow"><b>ComfyUI 網址</b><div class="row"><input id="cu" class="gsel" value="${esc(C.comfy_url||'')}" placeholder="自動（Desktop 8000、免安裝版 8188）"><button class="pill acc" id="cus">儲存</button></div><small>空白＝自動找。ComfyUI 跟這個程式在同一台電腦，用 http://127.0.0.1:埠號。</small></div>
     <div class="srow"><b>照片上傳前縮小到</b>${segH('gen_mp',+C.gen_mp,[[0.5,'50 萬'],[1,'100 萬'],[2,'200 萬'],[4,'400 萬'],[0,'原圖']])}<small>像素數。縮小上傳比較快；流程裡本來就會再縮放（你的 GROK 流程縮到長邊 960）。</small></div>
     <div class="srow"><b>生圖時不讓電腦睡眠</b>${segH('keep_awake',C.keep_awake===false?0:1,[[1,'開'],[0,'關']])}<small>跑圖、跑影片、下載模型時叫 Windows 先不要睡眠（螢幕還是會照設定關）。顯示卡在跑的時候電腦去睡，可能會藍畫面（DRIVER_POWER_STATE_FAILURE）。</small></div>
     <div class="srow"><b>Hugging Face 金鑰（token）</b><div class="row"><input id="hft" class="gsel" type="password" autocomplete="off" placeholder="${C.hf_token?esc(C.hf_token)+'（已設定，要換再貼）':'hf_ 開頭的那串'}"><button class="pill acc" id="hfs">儲存</button></div><small>有些模型（例如 FLUX 3 Klein、FLUX Klein 9B）要先在 Hugging Face 網頁登入、到模型頁按同意授權，才能下載。到 huggingface.co → Settings → Access Tokens 建一個「Read」金鑰貼這裡。只存在你的電腦。</small></div>
     <div class="srow"><b>全部做完後清 ComfyUI 記憶體</b>${segH('gen_free_idle',C.gen_free_idle===false?0:1,[[1,'開'],[0,'關']])}<small>排隊的都做完 1 分鐘，叫 ComfyUI 把模型從顯示卡和記憶體清掉（整晚跑完電腦比較輕）。你同時在 ComfyUI 自己玩的話可以關。</small></div>
     <div class="srow"><b>記憶體不夠失敗時自動再試一次</b>${segH('gen_auto_retry',C.gen_auto_retry===false?0:1,[[1,'開'],[0,'關']])}<small>清乾淨記憶體再跑一次，整晚排隊不會因為偶爾一次就少一張。</small></div>
     <div class="srow"><b>一張超過幾分鐘算失敗</b>${segH('gen_timeout_min',+C.gen_timeout_min,[[10,'10'],[30,'30'],[60,'60'],[120,'120'],[240,'240']])}</div></section>`;
    $('#cus').onclick=()=>setVal('comfy_url',$('#cu').value.trim());$('#hfs').onclick=()=>{const v=$('#hft').value.trim();if(!v)return toast('先貼上金鑰');setVal('hf_token',v);$('#hft').value=''};}
  else if(c==='look'){sb.innerHTML=`<h2 class="stt">🎨 外觀與通知</h2><section class="ssec"><div class="srow"><b>深色／淺色</b>${segH('_mode',LS.get('mode','dark'),[['dark','🌙 深色'],['light','☀ 淺色']])}</div>
     <div class="srow"><b>版面</b>${segH('_view',document.body.classList.contains('pc')?'pc':'m',[['m','📱 手機版'],['pc','🖥 網頁版（大螢幕）']])}<small>只影響這支手機／這個瀏覽器。</small></div></section>
     <section class="ssec"><h3>做好通知</h3><div class="srow"><label class="row"><input type="checkbox" id="ntv" ${LS.get('nt_vib',true)?'checked':''}> <b>📳 震動</b></label><small>做好一張震一下（iPhone 的瀏覽器不支援震動）</small></div>
     <div class="srow"><label class="row"><input type="checkbox" id="nts" ${LS.get('nt_snd',true)?'checked':''}> <b>🔔 叮一聲</b></label><small>全部做完、或你切到別的 App 時才響；開著頁面時分頁標題也會變「✅ 做好了」</small><button class="pill" id="ntt" style="width:max-content">試聽</button></div></section>`;
    $('#ntv').onchange=()=>LS.set('nt_vib',$('#ntv').checked);$('#nts').onchange=()=>LS.set('nt_snd',$('#nts').checked);$('#ntt').onclick=()=>{gBeep();if(navigator.vibrate&&LS.get('nt_vib',true))navigator.vibrate([120,80,120])}}
  else if(c==='login'){sb.innerHTML=`<h2 class="stt">🔒 登入</h2><section class="ssec"><div class="srow"><b>登出這支手機</b><small>下次打開要重新輸入 PIN。PIN 在電腦上「⚙ 設定 → 📱 手機網頁」改。</small><button class="btn s" id="out">登出</button></div></section>`;
    $('#out').onclick=async()=>{await api('/api/logout',{});TOK='';LS.set('tok','');showLogin()}}
  else if(c==='log'){sb.innerHTML=`<h2 class="stt">📜 LOG</h2><section class="ssec"><div class="srow"><div class="row"><select id="lf" class="gsel"><option>app_log.txt</option><option>error_log.txt</option><option>ui_freeze_log.txt</option><option>update_log.txt</option></select><button class="pill acc" id="lg">讀取</button></div><small>出問題時：電腦上「📜 LOG → 📦 匯出最近 7 天」，把 zip 傳給 AI。</small></div><pre id="lt" style="display:none"></pre></section>`;
    $('#lg').onclick=async()=>{const r=await api(U('/api/log',{f:$('#lf').value}));const p=$('#lt');p.style.display='';p.textContent=r.text||'（空的）';p.scrollTop=p.scrollHeight}}
  else if(c==='lab'){const j=await api('/api/settings');const L=j.lab||{};
    sb.innerHTML=`<h2 class="stt">🧪 實驗工作區</h2><section class="ssec">${(j.labs||[]).map(([k,n,d])=>`<div class="srow"><b>${esc(n)}</b>${segH('lab:'+k,L[k]?1:0,[[1,'開'],[0,'關']])}<small>${esc(d||'')}</small></div>`).join('')||'<div class="empty">目前沒有實驗功能</div>'}</section>`}
  else if(c==='about'){const cl=await api('/api/changelog');sb.innerHTML=`<h2 class="stt">ℹ 關於</h2><section class="ssec"><div class="srow"><b>__TITLE__</b>目前 V${esc($('#ver').textContent.replace(/^V/,''))}<small>更新：上面「更新包」分頁。</small></div>
     ${(cl.log||[]).slice(0,10).map(x=>`<div class="srow"><b>V${esc(x.version)} <span class="mu">${esc(x.date||'')}</span></b><ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.55">${(x.items||[]).map(i=>`<li>${esc(i)}</li>`).join('')}</ul></div>`).join('')}</section>`}
  sb.onclick=sb.onclick||(async e=>{const b=e.target.closest('.seg[data-sk] button');if(!b)return;const k=b.closest('.seg').dataset.sk,v=b.dataset.v;
    $$('button',b.parentNode).forEach(x=>x.classList.toggle('on',x===b));
    if(k==='_mode')return setMode(v);if(k==='_view')return setView(v);
    if(k.startsWith('lab:')){const r=await api('/api/lab',{k:k.slice(4),on:v==='1'});return toast(r.ok?'✔ 已儲存':(r.message||'沒存到'))}
    setVal(k,k==='keep_awake'?v==='1':+v)})}

// ---- 流程：電腦上 Data\workflows 裡的 ComfyUI 流程；可以從手機匯入
async function wfPane(){const p=$('#spane');p.innerHTML='<div class="empty">讀取中…</div>';const j=await api('/api/gen?full=1');if(!j.ok)return;
  p.innerHTML=`<details class="gadv" style="margin-bottom:10px"><summary>➕ 匯入流程／從官方範本做 <span class="mu">偶爾才用</span></summary><section class="ssec"><div class="srow"><b>➕ 匯入 ComfyUI 流程</b><small style="margin:0 0 8px">ComfyUI 裡「另存」的一般 .json 或「Export (API)」都可以。同名的會換掉（舊的自動備份到 workflows\\_old）。</small>
   <label class="btn s ufile">📂 選擇流程檔（.json）<input type="file" id="wff" accept=".json,application/json"></label></div>
   <div class="srow"><b>📥 從 ComfyUI 官方範本做流程</b><small style="margin:0 0 8px">直接拿你 ComfyUI 裡內建的範本（ComfyUI 要開著）。子圖會自動展開。</small>
   <div class="row"><button class="btn s" data-tpl="video_minimax_h3_t2v" data-nm="H3 文字生影片">🎬 H3 文字生影片</button><button class="btn s" data-tpl="video_minimax_h3_i2v" data-nm="H3 圖生影片">🖼 H3 圖生影片</button></div>
   <div class="row" style="margin-top:6px"><input id="tpln" placeholder="其他範本名稱，例如 video_minimax_h3_r2v" style="flex:1"><button class="btn s" id="tplgo">做成流程</button></div></div></section></details>
   ${(j.wfs||[]).map(w=>`<div class="upk"><div class="uh"><b style="color:var(--strong);font-size:16px">${esc(w.name)}</b>${w.name===j.wf?'<span class="utag">目前用的</span>':''}<small>${esc(w.fmt||'')}格式 · ${w.nodes||0} 個節點</small></div>
   ${w.err?`<div class="ubad">✖ ${esc(w.err)}</div>`:`<div class="mu" style="margin-top:6px;line-height:1.6">${w.need_img?'📷 照片 → '+esc(w.img_node):'不用照片'}<br>✏ 提示詞 → ${esc(w.pos||'找不到')}${w.neg?'<br>✏ 負面 → '+esc(w.neg):''}<br>🖼 輸出 → ${esc((w.outputs||[]).join('、')||'沒有 SaveImage')}</div>`}</div>`).join('')||'<div class="empty">還沒有流程</div>'}`;
  const tpl=async(t,nm)=>{const ex=(j.wfs||[]).some(w=>w.name===(nm||t));if(ex&&!confirm(`已經有「${nm||t}」，重新抓範本換掉？（舊的會備份）`))return;toast('抓範本中…',8000);
    const r=await api(U('/api/gen_tpl',{tpl:t,name:nm||'',force:ex?1:''}),{});toast(r.message||'失敗',8000);if(r.ok)wfPane()};
  $$('[data-tpl]',p).forEach(b=>b.onclick=()=>tpl(b.dataset.tpl,b.dataset.nm));$('#tplgo').onclick=()=>{const t=$('#tpln').value.trim();if(t)tpl(t,'')};
  $('#wff').onchange=async()=>{const f=$('#wff').files[0];if(!f)return;const r=await api(U('/api/gen_wf',{name:f.name}),await f.arrayBuffer(),true);toast(r.message||'失敗',5000);if(r.ok)wfPane()}}

// ---- 👤 人物庫：很多張某人的照片存成編號 a01…；提示詞寫 a01 → 自動帶他的照片當參考
async function pplPane(){const p=$('#spane');p.innerHTML='<div class="empty">讀取中…</div>';const r=await api('/api/people');if(!r.ok)return p.innerHTML=`<div class="ubad">${esc(r.message||'讀不到')}</div>`;
  const L=r.people||[];
  p.innerHTML=`<section class="ssec"><div class="srow"><b>👤 人物庫</b><small style="margin:0 0 8px">把某個人的照片存成一個編號（a01、a02…）。之後提示詞寫到編號，例如「圖一女生與 a01 喝著咖啡」，就會自動把他的照片當參考圖帶進去。<br>
   能用的流程：<b>GROK 改圖</b>（帶 1 張，a01 變成「圖二中的人」）、<b>H3 照片動起來（臉穩定）／參考生影片</b>（每人帶 3 張）。<br>照片建議 5～10 張：臉清楚、只有他一個人、不同角度和表情；第一張（代表）放最清楚的正臉。</small>
   <button class="btn s" id="pnew">＋ 新增人物</button></div></section>
   ${L.map(x=>`<div class="upk" data-c="${x.code}"><div class="uh"><b style="color:var(--strong);font-size:18px">${x.code}</b><input class="pnm" value="${esc(x.name)}" placeholder="名字（可不填）" style="flex:1;margin-left:8px"><small>${x.photos.length} 張</small></div>
     <div style="display:flex;flex-wrap:wrap;gap:6px;margin:8px 0">${x.photos.map((f,i)=>`<div style="position:relative"><img src="${IMGU('people/'+x.code+'/'+f)}" data-cv="${esc(f)}" style="height:84px;border-radius:6px;${i?'':'outline:2px solid var(--accent)'}" title="點一下設成代表照"><i data-dp="${esc(f)}" style="position:absolute;top:-5px;right:-5px;width:20px;height:20px;border-radius:50%;background:var(--red);color:#fff;font-style:normal;font-size:12px;line-height:20px;text-align:center">✕</i>${i?'':'<span class="ftag" style="position:absolute;left:2px;bottom:4px">代表</span>'}</div>`).join('')||'<span class="mu">還沒有照片</span>'}</div>
     <div class="row"><label class="btn s ufile">📷 加照片（可多選）<input type="file" accept="image/*" multiple data-up="1"></label><span class="grow"></span><button class="btn s" data-pdel="1" style="color:var(--red)">🗑 刪除這個人</button></div></div>`).join('')||'<div class="empty">還沒有人物：按「＋ 新增人物」</div>'}`;
  $('#pnew').onclick=async()=>{const nm=prompt('名字（可不填，例如：小美）','');if(nm===null)return;const r=await api(U('/api/people',{a:'new',name:nm}),{});toast(r.message||'失敗');pplPane()};
  $$('.upk[data-c]',p).forEach(c=>{const code=c.dataset.c;
    c.querySelector('.pnm').onchange=e=>api(U('/api/people',{a:'name',code,name:e.target.value}),{}).then(()=>toast('✔ 存好'));
    c.querySelector('[data-up]').onchange=async e=>{const F=[...e.target.files];e.target.value='';for(let i=0;i<F.length;i++){toast(`上傳 ${i+1}／${F.length}…`,60000);let b;try{b=await shrink(F[i])}catch(x){toast(`第 ${i+1} 張讀不到`,4000);continue}
      const r=await api(U('/api/people',{a:'add',code}),await b.arrayBuffer(),true);if(!r.ok){toast(r.message||'失敗',5000);break}}toast(`✔ ${code} 加了照片`);pplPane()};
    c.onclick=async e=>{const d=e.target.closest('[data-dp]');if(d){if(!confirm('刪掉這張照片？'))return;await api(U('/api/people',{a:'del',code,f:d.dataset.dp}),{});return pplPane()}
      const cv=e.target.closest('[data-cv]');if(cv){await api(U('/api/people',{a:'cover',code,f:cv.dataset.cv}),{});toast('✔ 設成代表照');return pplPane()}
      if(e.target.closest('[data-pdel]')){if(!confirm(`刪除 ${code} 和他所有照片？（會搬到 people\\_old，可以救回）`))return;const r=await api(U('/api/people',{a:'del',code}),{});toast(r.message||'');pplPane()}}})}

// ---- 📦 更新包（照 TikLive）：選檔 → 上傳 → 先看這版改了什麼 → 按「確定更新」才更新；⏪ 退回前面的版本
async function updPane(){const p=$('#spane');const cur=$('#ver').textContent.replace(/^V/,'');
  p.innerHTML=`<div class="cup" id="cup">☁ 雲端更新：讀取中…</div><section class="ssec"><div class="srow" style="border-bottom:0"><b>📦 更新包（手動）</b><div class="snote" style="margin:0 0 8px">目前 V${esc(cur)}。選手機裡的 __PREFIX___V版本.zip，上傳後會先顯示更新內容，按「確定更新」才會開始。更新時程式不用關，正在跑的生圖不會中斷。</div>
   <label class="btn ufile">📦 選擇更新包（.zip）<input type="file" id="updF" accept=".zip,application/zip,application/x-zip-compressed,application/octet-stream"></label><div id="updR"></div></div>
   <div class="srow" style="border-bottom:0;margin-top:4px"><b>⏪ 退回前面的版本</b><div class="snote" style="margin:0 0 8px">更新後如果出問題，可以退回更新前的版本（用每次更新前自動做的備份，一樣不用關程式）。</div><div id="rbList">讀取中…</div></div></section>`;
  $('#updF').onchange=e=>{const f=e.target.files&&e.target.files[0];e.target.value='';if(f)updUpload(f)};rbLoad();cuDraw()}
/* V0.3.41 🏷 提示詞積木：自己建分類和選項（單選或可複選、不選就不加），選了的會加在上面那段後面；📚 整篇範本：存好的整篇文字。存在電腦上，每支手機都一樣 */
let PKT={cats:[],docs:[]},PKS=LS.get('pksel',{}),PKL=0,PKQ='';
const pkId=()=>Date.now().toString(36)+Math.random().toString(36).slice(2,6);
async function pkLoad(){try{const r=await api('/api/pkit');if(r&&r.ok){PKT={cats:r.cats||[],docs:r.docs||[]};PKL=1}}catch(e){}pkDraw();pdDraw();pkPrev()}
async function pkSave(){try{const r=await api('/api/pkit',{cats:PKT.cats,docs:PKT.docs});if(!r.ok)toast('✖ '+(r.message||'存不進去'),4000)}catch(e){toast('✖ 連不到電腦，沒存到',4000)}}
function pkCombos(){let C=[[]];for(const c of PKT.cats){const S=PKS[c.id]||[];const sel=c.opts.filter(o=>S.includes(o.id)).map(o=>o.t.trim());if(c.rand&&c.opts.length){C=C.map(cb=>[...cb,`〔🎲${c.name}〕`]);continue}if(!sel.length)continue;   // V0.3.47「各做一張」的分類：選了幾個就做幾種
  C=c.each&&c.multi&&sel.length>1?C.flatMap(cb=>sel.map(t=>[...cb,t])):C.map(cb=>[...cb,...sel])}return C.map(x=>x.join('，'))}
function pkSuffix(){return pkCombos()[0]||''}
function pkRoll(q){return String(q).replace(/〔🎲([^〕]+)〕/g,(m,n)=>{const c=PKT.cats.find(x=>x.name===n);if(!c||!c.opts.length)return '';const S=PKS[c.id]||[];const L=S.length?c.opts.filter(o=>S.includes(o.id)):c.opts;return L[Math.floor(Math.random()*L.length)].t.trim()})}   // V0.3.54 🎲 每張隨機一個
function pkJoinX(t,x){t=String(t||'').trim();if(!x)return t;if(!t)return x;return t.replace(/[，,。.、\s]+$/,'')+'，'+x}
function pkJoin(t){return pkJoinX(t,pkSuffix())}
function pkAll(t){return pkCombos().map(x=>pkJoinX(t,x))}
function pkLP(root,sel,fn){root.querySelectorAll(sel).forEach(el=>{let tm=0,x0=0,y0=0;const c=()=>clearTimeout(tm);
  el.addEventListener('pointerdown',e=>{x0=e.clientX;y0=e.clientY;el._lp=0;tm=setTimeout(()=>{el._lp=1;try{navigator.vibrate&&navigator.vibrate(25)}catch(_){}fn(el)},550)});
  el.addEventListener('pointerup',c);el.addEventListener('pointercancel',c);el.addEventListener('pointerleave',c);el.addEventListener('pointermove',e=>{if(Math.abs(e.clientX-x0)+Math.abs(e.clientY-y0)>12)c()});
  el.addEventListener('contextmenu',e=>e.preventDefault());el.addEventListener('click',e=>{if(el._lp){el._lp=0;e.stopImmediatePropagation();e.preventDefault()}},true)})}
function pkAsk(title,val,btns,multi){return new Promise(ok=>{const o=document.createElement('div');o.id='pkOv';
  o.innerHTML=`<div class="pkW"><b style="color:var(--strong)">${esc(title)}</b>${val==null?'':multi?'<textarea id="pkV"></textarea>':'<input id="pkV" autocomplete="off">'}<div class="pkB">${btns.map((b,i)=>`<button class="btn ${b[1]||'s'}" data-i="${i}">${esc(b[0])}</button>`).join('')}</div></div>`;
  document.body.appendChild(o);const v=o.querySelector('#pkV');if(v){v.value=val;setTimeout(()=>{v.focus();try{v.setSelectionRange(v.value.length,v.value.length)}catch(_){}},50)}
  o.onclick=e=>{const b=e.target.closest('[data-i]');if(e.target===o){o.remove();ok({i:-1})}else if(b){const r={i:+b.dataset.i,v:v?v.value:''};o.remove();ok(r)}}})}
function pkDraw(){const box=$('#gpk');if(!box)return;const op=LS.get('gpk_o',true);
  box.innerHTML=`<details class="gadv" id="gpkd" ${op?'open':''}><summary>🏷 提示詞積木 <span class="mu">點選項＝加在上面那段後面；不選就不加</span></summary>
  ${PKT.cats.length?'':'<div class="mu" style="font-size:13px;padding:4px 2px 8px">還沒有分類：按「＋ 新分類」建一個（例如：場景），再按它的「＋」加選項。</div>'}
  ${PKT.cats.reduce((a,c)=>a+c.opts.length,0)>20?`<input id="pkQ" class="gsel" placeholder="🔍 找選項（例如：教室）" value="${esc(PKQ)}" style="margin:4px 0 6px;width:100%">`:''}
  ${PKT.cats.map(c=>{const fold=(LS.get('pkfold',{}))[c.id],ns=(PKS[c.id]||[]).length,sn=c.opts.filter(o=>(PKS[c.id]||[]).includes(o.id)).map(o=>o.t).join('、');return `<div class="pkC"><div class="pkCn" data-cn="${c.id}">${fold?'▸':'▾'} ${esc(c.name)} <small>${c.rand?'🎲 每張隨機':c.each?'📚 選幾個做幾種':c.multi?'可複選':'單選'}・${c.opts.length} 個${ns?'・選了 '+ns:''}・長按改</small>${fold&&sn?`<div class="mu" style="font-weight:400;font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${esc(sn)}</div>`:''}</div>${fold?'':`<div class="pkOs">${c.opts.filter(o=>!PKQ||o.t.includes(PKQ)||(PKS[c.id]||[]).includes(o.id)).map(o=>`<button class="pkO${(PKS[c.id]||[]).includes(o.id)?' on':''}" data-c="${c.id}" data-o="${o.id}">${esc(o.t)}</button>`).join('')}<button class="pkAdd" data-add="${c.id}">＋</button></div>`}</div>`}).join('')}
  <div class="row" style="gap:8px;margin-top:6px;align-items:center;flex-wrap:wrap"><button class="pill" id="pkNew">＋ 新分類</button><button class="pill" id="pkExp" title="積木和範本存成一個檔（備份、搬到別台電腦）">⬇ 匯出</button><button class="pill" id="pkImp">⬆ 匯入</button><input type="file" id="pkImpF" accept=".json,application/json" style="display:none"><span class="mu" style="font-size:12px">點分類名稱收合；長按分類名稱或選項：改名、編輯、刪除</span></div></details>`;
  $('#gpkd').ontoggle=()=>LS.set('gpk_o',$('#gpkd').open);
  {const q=$('#pkQ');if(q)q.oninput=()=>{PKQ=q.value.trim();pkDraw();const n=$('#pkQ');n.focus();n.setSelectionRange(n.value.length,n.value.length)}}   // V0.3.63 選項多時可以搜尋
  box.querySelectorAll('[data-o]').forEach(b=>b.onclick=()=>{const c=PKT.cats.find(x=>x.id===b.dataset.c);if(!c)return;let S=PKS[c.id]||[];const id=b.dataset.o;
    S=S.includes(id)?S.filter(x=>x!==id):(c.multi?[...S,id]:[id]);PKS[c.id]=S;LS.set('pksel',PKS);pkDraw();pkPrev()});
  box.querySelectorAll('[data-cn]').forEach(b=>b.onclick=()=>{const F=LS.get('pkfold',{});F[b.dataset.cn]=!F[b.dataset.cn];LS.set('pkfold',F);pkDraw()});   // V0.3.51 點分類名稱收合
  box.querySelectorAll('[data-add]').forEach(b=>b.onclick=async()=>{const c=PKT.cats.find(x=>x.id===b.dataset.add);const r=await pkAsk(`「${c.name}」加一個選項`,'',[['加上去','g'],['取消']]);
    if(r.i!==0)return;const L=r.v.split(/\n+/).map(x=>x.trim()).filter(Boolean);if(!L.length)return;for(const t of L)c.opts.push({id:pkId(),t});pkSave();pkDraw()});
  $('#pkExp').onclick=()=>{const b=new Blob([JSON.stringify({app:'ComfyRemote',kind:'prompt_kit',v:1,cats:PKT.cats,docs:PKT.docs},null,1)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='ComfyRemote_積木範本_'+new Date().toISOString().slice(0,10)+'.json';document.body.appendChild(a);a.click();a.remove();toast('⬇ 匯出了（積木 '+PKT.cats.length+' 類、範本 '+PKT.docs.length+' 篇）',3000)};   // V0.3.52 匯出／匯入
  $('#pkImp').onclick=()=>$('#pkImpF').click();
  $('#pkImpF').onchange=async e=>{const f=e.target.files&&e.target.files[0];e.target.value='';if(!f)return;let d;try{d=JSON.parse(await f.text())}catch(x){return toast('✖ 不是積木的匯出檔')}if(!d||!Array.isArray(d.cats))return toast('✖ 不是積木的匯出檔');
    const r=await pkAsk(`匯入：積木 ${d.cats.length} 類、範本 ${(d.docs||[]).length} 篇`,null,[['合併（同名分類合在一起）','g'],['全部換掉','er'],['取消']]);if(r.i<0||r.i>1)return;
    if(r.i===1){PKT={cats:d.cats,docs:d.docs||[]};PKS={};LS.set('pksel',PKS)}else{for(const c of d.cats){const o=PKT.cats.find(x=>x.name===c.name);if(!o){PKT.cats.push({...c,id:pkId()});continue}for(const op of c.opts||[])if(!o.opts.some(x=>x.t===op.t))o.opts.push({id:pkId(),t:op.t})}
      for(const dc of d.docs||[])if(!PKT.docs.some(x=>x.text===dc.text))PKT.docs.push({...dc,id:pkId()})}
    await pkSave();pkDraw();pdDraw();pkPrev();toast('⬆ 匯入好了',2500)};
  $('#pkNew').onclick=async()=>{const r=await pkAsk('新分類的名稱（例如：場景、上衣、動作）','',[['單選（選一個）','g'],['可複選'],['取消']]);if(r.i<0||r.i>1||!r.v.trim())return;
    PKT.cats.push({id:pkId(),name:r.v.trim(),multi:r.i===1,opts:[]});pkSave();pkDraw();toast('建好了：按它的「＋」加選項',3000)};
  pkLP(box,'[data-cn]',async el=>{const i=PKT.cats.findIndex(x=>x.id===el.dataset.cn),c=PKT.cats[i];if(!c)return;
    const r=await pkAsk(`分類「${c.name}」`,c.name,[['✏ 改名','g'],[c.multi?'改成單選':'改成可複選'],['⬆ 往上移'],['🗑 刪除','er'],[c.each?'改回：選的全部加在同一張':'📚 選了幾個就各做一張'],[c.rand?'取消隨機':'🎲 每張隨機一個'],['取消']]);
    if(r.i===5){c.rand=!c.rand;pkSave();pkDraw();pkPrev();toast(c.rand?'這個分類每張隨機挑一個（有選的就從選的裡挑，沒選就全部裡挑）；「1 張」改成 5 張就是 5 種隨機':'取消隨機',4500);return}
    if(r.i===4){c.each=!c.each;if(c.each)c.multi=true;pkSave();pkDraw();pkPrev();toast(c.each?'這個分類選了幾個，就各做一張（例如 3 個場景 → 3 種）':'改回：選的全部加在同一張',3500);return}
    if(r.i===0&&r.v.trim())c.name=r.v.trim();else if(r.i===1){c.multi=!c.multi;if(!c.multi&&(PKS[c.id]||[]).length>1){PKS[c.id]=PKS[c.id].slice(0,1);LS.set('pksel',PKS)}}
    else if(r.i===2&&i>0){PKT.cats.splice(i,1);PKT.cats.splice(i-1,0,c)}else if(r.i===3){if(!confirm(`刪掉分類「${c.name}」和它的 ${c.opts.length} 個選項？`))return;PKT.cats.splice(i,1);delete PKS[c.id];LS.set('pksel',PKS)}else return;
    pkSave();pkDraw();pkPrev()});
  pkLP(box,'[data-o]',async el=>{const c=PKT.cats.find(x=>x.id===el.dataset.c);const j=c?c.opts.findIndex(x=>x.id===el.dataset.o):-1;if(j<0)return;const o=c.opts[j];
    const r=await pkAsk(`「${c.name}」的選項`,o.t,[['✏ 存','g'],['⬅ 往前移'],['🗑 刪除','er'],['取消']]);
    if(r.i===0&&r.v.trim())o.t=r.v.trim();else if(r.i===1&&j>0){c.opts.splice(j,1);c.opts.splice(j-1,0,o)}else if(r.i===2){c.opts.splice(j,1);PKS[c.id]=(PKS[c.id]||[]).filter(x=>x!==o.id);LS.set('pksel',PKS)}else return;
    pkSave();pkDraw();pkPrev()})}
function gFinal(noML){const g=$('#gp');if(!g)return [];const t=g.value.trim(),ml=!noML&&$('#gml')&&$('#gml').checked,x=pkSuffix();const B=ml?(t?gSplit(t):[]):(t?[t]:[]);const L=(B.length?B:(x?['']:[])).flatMap(pkAll).filter(Boolean);return (noML?L.slice(0,1):L).flatMap(gExpand).slice(0,50)}
function pkPrev(){const e=$('#gpkx');if(!e)return;const x=pkSuffix(),L=gFinal(),t=($('#gp')||{}).value||'';gTabCnt();
  if(!L.length){e.innerHTML='';return}if(L.length===1&&!x&&!/\{[^{}]*\|/.test(t)){e.innerHTML='';return}   // 只有自己打的一句：不用再顯示一次
  const op=LS.get('gfin_o',L.length<=3),hl=s=>{let h=esc(s);if(x)h=h.replace(esc(x),`<i>${esc(x)}</i>`);return h};
  e.innerHTML=`<div class="gfin"><div class="h"><b>📝 會送出 ${L.length} 個提示詞${L.some(q=>q.includes('〔🎲'))?`（🎲 每個做 ${+($('#gc')||{}).value||1} 張、各隨機）`:''}</b>${x?`<button class="pill" id="pkM" title="把積木的字寫進上面，之後可以自己改">⬆ 積木合併到上面</button><button class="pill er" id="pkC">清除積木</button>`:''}<button class="pill" id="gfinT">${op?'收起':'看全部'}</button></div>
  ${op?`<ol>${L.map(p=>`<li>${hl(p)}</li>`).join('')}</ol>`:`<div class="mu" style="margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${hl(L[0])}</div>`}${x?'<div class="mu" style="font-size:12px;margin-top:4px">紫色字＝🏷 積木加上去的</div>':''}</div>`;
  $('#gfinT').onclick=()=>{LS.set('gfin_o',!op);pkPrev()};
  if(x){$('#pkC').onclick=()=>{PKS={};LS.set('pksel',PKS);pkDraw();pkPrev()};
  $('#pkM').onclick=()=>{const g=$('#gp'),ml=$('#gml')&&$('#gml').checked,t=g.value.trim();const B=ml&&t?gSplit(t):[t];g.value=(B.length?B:['']).map(pkJoin).join(ml?'\n\n':'');PKS={};LS.set('pksel',PKS);LS.set('gprompt',g.value);g.dispatchEvent(new Event('input'));pkDraw();pkPrev();toast('寫進上面了，可以再自己改',2500)}}}
/* V0.3.44 提示詞區分頁：🏷 積木／📚 範本／🧰 工具箱／⭐ 常用，一次只開一個（再點一次收起） */
{const w=f=>function(){const r=f.apply(this,arguments);try{if($('#gtabs'))gTabs()}catch(e){}return r};gTool=w(gTool);pkDraw=w(pkDraw);pdDraw=w(pdDraw)}
function gTabCnt(){const T=$('#gtabs');if(!T)return;const n=Object.values(PKS).reduce((a,v)=>a+(v||[]).length,0),B=k=>T.querySelector(`[data-gt="${k}"]`);
  const set=(k,lbl,c)=>{const b=B(k);if(b)b.innerHTML=lbl+(c?`<small>${c}</small>`:'')};set('pk','🏷 積木',n?'選 '+n:'');set('pl','📚 範本',PKT.docs.length||'');
  const tl=$('#gtool');const b=B('tool');if(b)b.hidden=!(tl&&tl.innerHTML.trim())}
function gTabs(){const T=$('#gtabs');if(!T)return;const cur=LS.get('gptab','');T.querySelectorAll('[data-gt]').forEach(b=>b.classList.toggle('on',b.dataset.gt===cur));
  document.querySelectorAll('.gtp').forEach(p=>p.classList.toggle('on',p.dataset.gp===cur));document.querySelectorAll('.gtp details.gadv').forEach(d=>d.open=true);gTabCnt();
  if(!T._on){T._on=1;T.onclick=e=>{const b=e.target.closest('[data-gt]');if(!b)return;LS.set('gptab',LS.get('gptab','')===b.dataset.gt?'':b.dataset.gt);gTabs()}}}
function pdDraw(){const box=$('#gpl');if(!box)return;const op=LS.get('gpl_o',false);
  box.innerHTML=`<details class="gadv" id="gpld" ${op?'open':''}><summary>📚 整篇範本 <span class="mu">存好的整篇文字（可以很多段），點一下帶到上面</span></summary>
  <div class="pdL">${PKT.docs.length?PKT.docs.map(d=>{const n=gSplit(d.text).length;return `<div class="pdI" data-d="${d.id}"><b>${esc(d.title||'（沒有標題）')}</b>${n>1&&/\n[ \t]*\n/.test(d.text)?` <span class="badge">${n} 段</span>`:''}<span class="mu">${esc(d.text.slice(0,80).replace(/\s+/g,' '))}</span></div>`}).join(''):'<div class="mu" style="font-size:13px">還沒有：在上面打好一整篇（段落之間空一行），按下面的「💾 存成範本」。</div>'}</div>
  <div class="row" style="gap:8px;margin-top:8px;align-items:center"><button class="pill" id="pdSave">💾 把上面那段存成範本</button><span class="mu" style="font-size:12px">長按範本：改標題、編輯、刪除</span></div></details>`;
  $('#gpld').ontoggle=()=>LS.set('gpl_o',$('#gpld').open);
  $('#pdSave').onclick=async()=>{const t=$('#gp').value.trim();if(!t)return toast('上面還沒有字');const r=await pkAsk('範本的標題',t.split('\n')[0].slice(0,16),[['💾 存','g'],['取消']]);if(r.i!==0)return;
    PKT.docs.unshift({id:pkId(),title:r.v.trim()||t.slice(0,16),text:t,t:Date.now()/1000});pkSave();pdDraw();toast('存好了',2000)};
  box.querySelectorAll('[data-d]').forEach(el=>el.onclick=()=>{const d=PKT.docs.find(x=>x.id===el.dataset.d);if(!d)return;const g=$('#gp');
    if(g.value.trim()&&g.value.trim()!==d.text.trim()&&!confirm(`用「${d.title}」換掉上面現在的字？`))return;g.value=d.text;LS.set('gprompt',g.value);
    const multi=/\n[ \t]*\n/.test(d.text);if(multi&&$('#gml')&&!$('#gml').checked){$('#gml').checked=true;LS.set('gml',true)}g.rows=Math.min(12,Math.max(3,d.text.split('\n').length));g.dispatchEvent(new Event('input'));
    toast(multi?`帶到上面了：${gSplit(d.text).length} 段（已勾「多篇文字」，每段做一次）`:'帶到上面了',3000);g.scrollIntoView({block:'center',behavior:'smooth'})});
  pkLP(box,'[data-d]',async el=>{const i=PKT.docs.findIndex(x=>x.id===el.dataset.d),d=PKT.docs[i];if(!d)return;
    const r=await pkAsk(`範本「${d.title}」`,d.title,[['✏ 改標題','g'],['📝 編輯內容'],['⬆ 往上移'],['🗑 刪除','er'],['取消']]);
    if(r.i===0&&r.v.trim())d.title=r.v.trim();else if(r.i===1){const r2=await pkAsk(`編輯「${d.title}」（段落之間空一行）`,d.text,[['💾 存','g'],['取消']],true);if(r2.i!==0||!r2.v.trim())return;d.text=r2.v.trim();d.t=Date.now()/1000}
    else if(r.i===2&&i>0){PKT.docs.splice(i,1);PKT.docs.splice(i-1,0,d)}else if(r.i===3){if(!confirm(`刪掉範本「${d.title}」？`))return;PKT.docs.splice(i,1)}else return;
    pkSave();pdDraw()})}
/* V0.3.40 🤝 右上角 Lv：跟 SortCut、GoPro Fusion 360（FusionStitch）分電腦效能（共用規則第 3 版） */
let HSI=null;
async function hsGet(){try{HSI=await api('/api/hs')}catch(e){HSI=null}const b=$('#hslv');if(b&&HSI&&HSI.ok){b.innerHTML='Lv'+HSI.lv+(HSI.cap!=null?`<span class="pct"> · ${Math.round(HSI.cap)}%</span>`:'');b.className='hslv'+(HSI.mode==='lead'&&HSI.apps.find(a=>a.app===HSI.me&&a.want>=2)?' boost':HSI.mode==='yield'?' yield':'')}return HSI}
function hsUse(u){u=u||{};const L=[];if(u.vram_gb!=null)L.push(`佔顯示卡記憶體 ${u.vram_gb} GB`);if(u.vram_total_gb)L.push(`ComfyUI 看到顯示卡記憶體剩 ${u.vram_free_gb}／${u.vram_total_gb} GB`);if(u.ram_total_gb)L.push(`RAM 剩 ${u.ram_free_gb}／${u.ram_total_gb} GB`);return L.length?'<br>🧠 '+L.join('・'):''}
function hsInit(){const b=$('#hslv');if(!b||b._on)return;b._on=1;b.onclick=hsOpen;hsGet();setInterval(()=>{if(!document.hidden)hsGet()},10000)}
async function hsSet(d){const r=await api('/api/hs',d);if(r&&r.ok){HSI=r;hsDraw()}else toast((r&&r.message)||'改不了',3000)}
function hsOpen(){if($('#hsOv'))return;const o=document.createElement('div');o.id='hsOv';o.innerHTML='<div class="hsW" id="hsW">讀取中…</div>';o.onclick=e=>{if(e.target===o)o.remove()};document.body.appendChild(o);hsGet().then(hsDraw);
  const iv=setInterval(()=>{if(!$('#hsOv'))return clearInterval(iv);hsGet().then(()=>{if(!document.activeElement||document.activeElement.type!=='range')hsDraw()})},3000)}
function hsDraw(){const w=$('#hsW');if(!w)return;const I=HSI;if(!I||!I.ok){w.innerHTML='🤝 握手還沒開始（電腦上的 ComfyRemote 要開著）';return}const P=I.p3,WT=['閒著','背景小工作','在做事','使用者在等'];
  const fs=P.normal.FusionStitch||45,sc=P.normal.SortCut||45,fsp=Math.round(100*fs/(fs+sc));
  w.innerHTML=`<h3>🤝 電腦效能分配 <span class="mu" style="font-size:12px;font-weight:400">規則第 ${I.rules} 版${I.rules_from==='lib'?'（別的程式的新版）':''}</span><button class="pill" id="hsX" style="margin-left:auto">✖ 關閉</button></h3>
  <div class="mu" style="font-size:13px">同一台電腦的程式互相讓：ComfyRemote 在生圖時最優先（${P.boost}%），其他的各 ${P.boost_others}%；平常 FusionStitch／SortCut 照下面的比例分；永遠留 ${P.reserve}% 給你用電腦。</div>
  <div class="mu" style="margin:10px 0 2px;font-weight:700">這台電腦有誰參與（沒勾的不管它、也不限制它）</div>
  ${I.apps.filter(a=>a.on).map(a=>`<div class="hsA${a.member?'':' off'}"><div class="t"><input type="checkbox" data-mem="${esc(a.app)}" ${a.member?'checked':''}><b>${esc(a.name)}${a.app===I.me?'（這個）':''}</b><span class="mu">${a.on?'● 開著'+(a.ver?' V'+esc(a.ver):''):'○ 沒開'}</span><span class="pc">${a.member&&a.cap!=null&&a.on?Math.round(a.cap)+'%':''}</span></div>
    ${a.on&&a.member?`<div class="mu" style="font-size:12.5px;margin-top:3px">${esc(WT[a.want]||'')}${a.what?'：'+esc(a.what):''}　Lv${a.lv}${a.why?'　· '+esc(a.why):''}${hsUse(a.use)}${a.app!==I.me&&a.rules!=null&&a.rules<4?`<br>⚠ 這個程式自己的握手檔是第 ${a.rules} 版：CPU 會照分配，但還不會「放掉顯示卡記憶體」（要它更新到第 4 版）`:''}</div><div class="hsBar"><i style="width:${Math.min(100,a.cap||0)}%"></i></div>`:''}</div>`).join('')}
  ${I.apps.some(a=>!a.on)?`<div class="mu" style="font-size:12.5px;margin:6px 2px">沒偵測到（沒開或不在這台）：${I.apps.filter(a=>!a.on).map(a=>`<label style="margin-right:10px;white-space:nowrap"><input type="checkbox" data-mem="${esc(a.app)}" ${a.member?'checked':''}> ${esc(a.name)}</label>`).join('')}<br>沒偵測到的不會分效能、也不會讓路給它</div>`:''}
  <div class="hsRow"><span>平常分配</span><span>GoPro ${fsp}</span><input type="range" id="hsN" min="10" max="90" step="5" value="${fsp}"><span>${100-fsp} SortCut</span></div>
  <div class="hsRow"><span>留給你用電腦</span><input type="range" id="hsR" min="0" max="30" step="5" value="${P.reserve}"><b>${P.reserve}%</b></div>
  <div class="hsRow"><span>ComfyRemote 生圖時拿</span><input type="range" id="hsB" min="40" max="90" step="5" value="${P.boost}"><b>${P.boost}%</b></div>
  <div class="hsRow"><span>那時其他程式各</span><input type="range" id="hsO" min="0" max="20" step="1" value="${P.boost_others}"><b>${P.boost_others}%</b></div>
  <div class="mu" style="margin-top:12px;font-weight:700">ComfyRemote 的 Lv（最多跟別人要多少：Lv × 10%）</div>
  <div class="lvs">${[1,2,3,4,5,6,7,8,9,10].map(n=>`<button data-lv="${n}" class="${n===I.lv?'on':''}">${n}</button>`).join('')}</div>
  <div class="mu" style="font-size:12px;margin-top:10px">設定存在電腦的 %LOCALAPPDATA%\\AppHandshake\\policy3.json，三個程式共用：在哪一個改都一樣。${I.err?'<br>⚠ '+esc(I.err):''}</div>`;
  $('#hsX').onclick=()=>$('#hsOv').remove();
  w.querySelectorAll('[data-mem]').forEach(c=>c.onchange=()=>hsSet({members:[...w.querySelectorAll('[data-mem]')].filter(x=>x.checked).map(x=>x.dataset.mem)}));
  w.querySelectorAll('[data-lv]').forEach(b=>b.onclick=()=>hsSet({lv:{[I.me]:+b.dataset.lv}}));
  const rg=(id,f)=>{const e=$(id);e.oninput=()=>{const t=e.nextElementSibling;if(t&&t.tagName==='B')t.textContent=e.value+'%';else if(id==='#hsN'){e.previousElementSibling.textContent='GoPro '+e.value;t.textContent=(100-e.value)+' SortCut'}};e.onchange=()=>hsSet(f(+e.value))};
  rg('#hsN',v=>({normal:{FusionStitch:v*0.9,SortCut:(100-v)*0.9}}));rg('#hsR',v=>({reserve:v}));rg('#hsB',v=>({boost:v}));rg('#hsO',v=>({boost_others:v}))}
/* V0.3.36 ☁ 雲端更新（GitHub Releases）：有新版只提示，按「更新」才下載；要換 EXE 時，有生圖在做會先列出來 */
let CUI=null,CUT=0;
async function cuGet(){try{CUI=await api('/api/cloud')}catch(e){CUI=null}cuBadge();return CUI}
function cuBadge(){const b=$('#tabs [data-t="set"]');const c=CUI&&CUI.chk;const on=!!(c&&c.newer&&!c.skipped);if(b){b.classList.toggle('cun',on);b.title=on?'雲端有新版 V'+CUI.ver+'（設定 → 更新包）':''}
  if(on&&LS.get('cu_told')!==CUI.ver){LS.set('cu_told',CUI.ver);toast('☁ 有新版 V'+CUI.ver+'：到「設定 → 更新包」按更新',8000)}}
async function cuDraw(){const box=$('#cup');if(!box)return;const I=await cuGet();if(!$('#cup'))return;if(!I){box.textContent='☁ 雲端更新：讀不到';return}
  const c=I.chk||{},dl=I.dl,mb=n=>n?(n/1048576).toFixed(1)+' MB':'';let h='<div class="cuh">☁ 雲端更新</div>';
  if(I.busy||dl){const p=dl&&dl.size?Math.round(dl.got/dl.size*100):0;h+=`<div class="snote">${esc(I.msg||'下載中…')}${dl?`　${esc(dl.label||'')} ${p}%（${(dl.spd/1048576).toFixed(1)} MB/s）`:''}</div>${dl?`<div class="cubar"><i style="width:${p}%"></i></div>`:''}<div class="cubs"><button class="btn s" id="cuX">取消下載</button></div>`}
  else if(I.checking)h+='<div class="snote">檢查中…</div>';
  else if(!I.chk)h+='<div class="snote">還沒檢查（開程式 1 分鐘後會自動檢查，之後每 6 小時）</div>';
  else if(!c.ok)h+=`<div class="snote">${esc(c.message||'連不到 GitHub')}</div>`;
  else if(c.newer){h+=`<div class="snote"><b>雲端有新版 V${esc(I.ver)}</b>（現在 V${esc(I.cur)}${I.date?'，'+esc(I.date):''}）${c.need_shell?'<br>⚠ 這次要換 EXE：電腦上的程式會關掉再自動打開（約 1 分鐘），排隊的生圖會接著做':'<br>可以熱更新：程式不用關，生圖不中斷'}${c.skipped?'<br>（已略過這版）':''}</div>`;
    if(I.notes.length)h+=`<ul>${I.notes.slice(0,12).map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`;
    h+=`<div class="cubs"><button class="btn" id="cuU">更新（${esc(mb(c.need_shell?I.shell_size:I.zip_size))}）</button>${c.need_shell?'':`<button class="btn s" id="cuS">${c.skipped?'取消略過':'略過這版'}</button>`}</div><div id="cuW"></div>`}
  else h+=`<div class="snote">✔ 已經是最新（雲端 V${esc(I.ver||I.cur)}，${c.t?new Date(c.t*1000).toLocaleString():''} 檢查）</div>`;
  if(I.msg&&!I.busy)h+=`<div class="snote">${esc(I.msg)}</div>`;
  if(!I.busy&&!dl)h+=`<div class="cubs"><button class="btn s" id="cuC">☁ 檢查更新</button></div>`;
  h+=`<label><input type="checkbox" id="cuOn"${I.on?' checked':''}> 自動檢查更新（開程式 1 分鐘後、之後每 6 小時；只提示，不會自己更新）</label>`;box.innerHTML=h;
  const op=async(d,re=1500)=>{const r=await api('/api/cloud',d);toast((r.ok?'':'✖ ')+(r.message||''),5000);setTimeout(cuDraw,re);return r};
  const B=id=>box.querySelector(id);
  if(B('#cuC'))B('#cuC').onclick=()=>op({op:'check'},4000);
  if(B('#cuX'))B('#cuX').onclick=()=>op({op:'cancel'});
  if(B('#cuS'))B('#cuS').onclick=()=>op({op:c.skipped?'unskip':'skip'});
  B('#cuOn').onchange=e=>op({op:'on',v:e.target.checked});
  if(B('#cuU'))B('#cuU').onclick=async()=>{const r=await api('/api/cloud',{op:'update'});
    if(r.need_confirm){B('#cuW').innerHTML=`<div class="cuw">⚠ ${esc(r.message)}<div class="cubs"><button class="btn s" id="cuN">等做完再說</button><button class="btn" id="cuF">堅持現在更新</button></div></div>`;
      B('#cuN').onclick=()=>{B('#cuW').innerHTML=''};B('#cuF').onclick=async()=>{const r2=await api('/api/cloud',{op:'update',force:true});toast((r2.ok?'':'✖ ')+(r2.message||''),6000);cuDraw()};return}
    toast((r.ok?'':'✖ ')+(r.message||''),6000);cuDraw()};
  clearTimeout(CUT);if(I.busy||I.dl||I.checking)CUT=setTimeout(()=>{if($('#cup'))cuDraw()},1500)}
async function updUpload(f){const R=$('#updR');R.innerHTML=`<div class="umsg">上傳中…（${esc(f.name)}，${fmtB(f.size)}）</div>`;
  let j;try{j=await api(U('/api/update_check',{name:f.name}),await f.arrayBuffer(),true)}catch(e){R.innerHTML=`<div class="ubad">✖ 上傳失敗：${esc(e.message)}</div>`;return}
  if(!j.ok){R.innerHTML=`<div class="ubad">✖ ${esc(j.message||'不能用')}</div>`;return}
  const tag=j.way==='newer'?'<span class="utag">較新</span>':j.way==='same'?'<span class="utag same">同一版</span>':'<span class="utag old">較舊（降版）</span>';
  R.innerHTML=`<div class="ucard"><div class="uvs">V${esc(j.current)} → V${esc(j.version)}${tag}</div>${j.notes.length?`<ul>${j.notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul>`:'<div class="snote">（這個更新包沒有寫更新內容）</div>'}
   ${j.hot_ok?'':'<div class="uwarn">這版不能熱更新：會放進 UPDATE，下次重開程式時套用。</div>'}${j.way==='older'?'<div class="uwarn">⚠ 這是比較舊的版本（降版）。</div>':''}
   <div class="ubtns"><button class="btn s" id="uno">取消</button><button class="btn" id="uok">確定更新</button></div><div class="umsg"></div></div>`;
  $('#uno').onclick=()=>{R.innerHTML=''};
  $('#uok').onclick=async()=>{const m=R.querySelector('.umsg');$('#uok').disabled=$('#uno').disabled=true;m.textContent='更新中…';
    const r=await api('/api/update_apply',{name:j.name});m.innerHTML=r.ok?`<span class="uok">✔ ${esc(r.message)}</span>`:`<span class="ubad">✖ ${esc(r.message||'失敗')}</span>`;
    if(r.ok&&r.ver)setTimeout(()=>location.reload(),9000);if(!r.ok)$('#uok').disabled=$('#uno').disabled=false}}
async function rbLoad(){const L=$('#rbList');if(!L)return;let j;try{j=await api('/api/update_rollback')}catch(e){L.textContent='讀不到備份清單';return}
  if(!$('#rbList'))return;if(!j.items||!j.items.length){L.innerHTML='<div class="snote" style="margin:0">還沒有可以退回的版本（更新過一次之後才會有）。</div>';return}
  L.innerHTML=j.items.map((x,i)=>`<div class="upk"><div class="uh"><b style="color:var(--strong);font-size:16px">V${esc(x.version)}</b><span class="ut">${x.older?'前一版':'較新'}</span><small>${esc(x.time)} 更新前備份的</small></div>
   ${x.notes.length?`<details><summary>這版的更新內容</summary><ul>${x.notes.map(n=>`<li>${esc(n)}</li>`).join('')}</ul></details>`:''}<button class="btn s" data-i="${i}">退回 V${esc(x.version)}</button><div class="rbx"></div></div>`).join('');
  $$('#rbList button[data-i]').forEach(b=>b.onclick=()=>{const x=j.items[+b.dataset.i],w=b.nextElementSibling;b.remove();
    w.innerHTML=`<div class="uwarn">從 V${esc(j.current)} 換回 V${esc(x.version)}，程式不用關，正在跑的生圖不會中斷。</div><div class="ubtns"><button class="btn s rbno">取消</button><button class="btn rbok">確定退回</button></div><div class="umsg"></div>`;
    w.querySelector('.rbno').onclick=()=>rbLoad();
    w.querySelector('.rbok').onclick=async()=>{const m=w.querySelector('.umsg');w.querySelector('.rbok').disabled=true;const r=await api('/api/update_rollback',{i:+b.dataset.i});
      m.innerHTML=r.ok?`<span class="uok">✔ ${esc(r.message)}</span>`:`<span class="ubad">✖ ${esc(r.message||'失敗')}</span>`;if(r.ok)setTimeout(()=>location.reload(),9000)}})}

async function boot(){let h={};try{h=await (await fetch('/api/hello',{headers:{'x-app-token':TOK}})).json()}catch(e){$('#v').innerHTML='<div class="empty">連不到電腦（Tailscale 有開嗎？電腦開著嗎？）</div>';return}
  $('#ver').textContent='V'+h.ver;if(!h.authed)return showLogin();tabs();show();sysFabInit();hsInit();if(new URLSearchParams(location.search).get('hs'))setTimeout(hsOpen,500);setTimeout(cuGet,3000);setInterval(()=>{if(!document.hidden)cuGet()},600000)}
if('serviceWorker' in navigator)navigator.serviceWorker.register('sw.js').catch(()=>{});
boot();
</script></body></html>
"""
