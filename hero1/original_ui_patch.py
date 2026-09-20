from pathlib import Path
import re, sys, json

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")

def read(p): return (root / p).read_text(encoding="utf-8")
def write(p, s): (root / p).write_text(s, encoding="utf-8")

p = Path("wie-app/tauri.conf.json")
conf = json.loads(read(p))
conf["productName"] = "영웅서기 1 - 솔티아의 바람"
conf["identifier"] = "net.hero1.soltia.originalui"
if conf.get("app", {}).get("windows"):
    conf["app"]["windows"][0]["title"] = "영웅서기 1 - 솔티아의 바람"
write(p, json.dumps(conf, ensure_ascii=False, indent=2) + "\n")

p = Path("wie-web/src/html/index.html")
s = read(p)
s = re.sub(r'\s*<button id="cheat-open"[^>]*>CHEAT</button>\s*', "\n", s, count=1)
old_keypad = re.search(r'<div class="button-container" aria-label="앱 키패드">.*?</div>\s*</main>', s, flags=re.S)
if not old_keypad:
    raise SystemExit("original WIE keypad block not found")
new_keypad = r'''<div class="button-container original-keypad" aria-label="앱 키패드">
          <div class="mainrow">
            <div class="leftpad">
              <div class="row3">
                <span></span>
                <button class="btn" data-key="CLR" type="button">C</button>
              </div>
              <div class="dpad">
                <span class="sp"></span><button class="btn" data-key="UP" type="button">▲</button><span class="sp"></span>
                <button class="btn" data-key="LEFT" type="button">◀</button><button class="btn" data-key="OK" type="button">OK</button><button class="btn" data-key="RIGHT" type="button">▶</button>
                <span class="sp"></span><button class="btn" data-key="DOWN" type="button">▼</button><span class="sp"></span>
                <span class="sp"></span><span class="sp"></span><span class="sp"></span>
              </div>
            </div>
            <div class="numpad">
              <button class="btn" data-key="1" type="button">1</button><button class="btn" data-key="2" type="button">2</button><button class="btn" data-key="3" type="button">3</button>
              <button class="btn" data-key="4" type="button">4</button><button class="btn" data-key="5" type="button">5</button><button class="btn" data-key="6" type="button">6</button>
              <button class="btn" data-key="7" type="button">7</button><button class="btn" data-key="8" type="button">8</button><button class="btn" data-key="9" type="button">9</button>
              <button class="btn" data-key="*" type="button">*</button><button class="btn" data-key="0" type="button">0</button><button class="btn" data-key="#" type="button">#</button>
            </div>
          </div>
        </div>
      </main>'''
s = s[:old_keypad.start()] + new_keypad + s[old_keypad.end():]
marker = '    <dialog id="cheat-dialog" class="app-dialog">'
if marker not in s:
    raise SystemExit("cheat dialog marker not found")
s = s.replace(marker, '    <button id="cheat-open" class="cheat-float" type="button" aria-label="치트 메뉴">CHEAT</button>\n\n' + marker, 1)
write(p, s)

p = Path("wie-web/src/css/style.css")
css = read(p)
css += r'''

/* Hero1 original-wrapper presentation */
html, body { margin:0; min-width:0; min-height:100%; overflow:hidden; background:#0d0d0f; overscroll-behavior:none; }
.player-view { position:fixed; inset:0; min-height:0; background:#0d0d0f; overflow:hidden; }
.player-toolbar { display:none !important; }
.player-main { width:100%; height:100dvh; display:flex; flex-direction:column; align-items:stretch; background:#0d0d0f; overflow:hidden; }
.canvas-wrapper { flex:1 1 auto; width:100%; min-height:0; aspect-ratio:auto; display:flex; align-items:center; justify-content:center; background:#000; overflow:hidden; }
#canvas { display:block; width:auto; height:100%; max-width:100%; max-height:100%; aspect-ratio:3/4; object-fit:contain; background:#000; image-rendering:auto; }
.original-keypad, .original-keypad * { box-sizing:border-box; -webkit-tap-highlight-color:transparent; -webkit-user-select:none; user-select:none; touch-action:none; }
.original-keypad { flex:0 0 auto; display:block; width:100%; padding:10px 12px calc(10px + env(safe-area-inset-bottom)); background:#0d0d0f; color:#e8e8e8; -webkit-touch-callout:none; }
.original-keypad .mainrow { display:flex; align-items:stretch; gap:8px; }
.original-keypad .leftpad { flex:0 0 auto; display:flex; flex-direction:column; justify-content:space-between; gap:10px; }
.original-keypad .row3 { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
.original-keypad .row3 .btn { height:34px; font-size:16px; }
.original-keypad .dpad { align-self:center; display:grid; grid-template-columns:repeat(3,34px); grid-template-rows:repeat(4,34px); gap:7px; }
.original-keypad .dpad .sp { visibility:hidden; }
.original-keypad .dpad .btn { font-size:20px; }
.original-keypad .numpad { flex:1 1 auto; display:grid; grid-template-columns:repeat(3,1fr); grid-template-rows:repeat(4,1fr); gap:10px; }
.original-keypad .numpad .btn { font-size:32px; font-weight:700; }
.original-keypad .btn { width:auto; min-width:0; height:auto; margin:0; padding:0; background:#1b1b20; color:#e8e8e8; border:1px solid #333; border-radius:8px; text-align:center; display:flex; align-items:center; justify-content:center; font-weight:600; line-height:1; transition:background .04s,transform .04s; appearance:none; }
.original-keypad .btn:active, .original-keypad .btn.pressed { background:#4caf50; color:#fff; border-color:#7be08a; box-shadow:0 0 0 2px #7be08a inset; transform:scale(.94); }
@media (orientation: landscape) {
  .player-main { position:fixed; inset:0; }
  .canvas-wrapper { position:absolute; inset:0; width:100%; height:100%; background:#000; }
  #canvas { width:auto; height:100%; max-width:100%; max-height:100%; }
  .original-keypad { position:fixed; inset:0; z-index:20; width:auto; padding:0; background:transparent; pointer-events:none; }
  .original-keypad .mainrow { display:block; }
  .original-keypad .btn { pointer-events:auto; background:rgba(27,27,32,.72); }
  .original-keypad .btn:active, .original-keypad .btn.pressed { background:rgba(76,175,80,.9); }
  .original-keypad .leftpad { position:absolute; left:max(2vw,env(safe-area-inset-left)); top:50%; transform:translateY(-50%); flex-direction:column; justify-content:flex-start; gap:12px; }
  .original-keypad .row3 { width:174px; grid-template-columns:1fr 1fr; gap:12px; }
  .original-keypad .row3 .btn { height:48px; font-size:18px; }
  .original-keypad .dpad { grid-template-columns:repeat(3,52px); grid-template-rows:repeat(3,52px); gap:9px; align-self:auto; }
  .original-keypad .dpad .btn { font-size:20px; }
  .original-keypad .dpad > .sp:nth-child(n+10) { display:none; }
  .original-keypad .dpad > .btn:nth-child(n+10) { grid-column:1/-1; justify-self:start; width:81px; height:48px; }
  .original-keypad .numpad { position:absolute; right:max(2vw,env(safe-area-inset-right)); top:50%; transform:translateY(-50%); width:auto; flex:none; grid-template-columns:repeat(3,56px); grid-template-rows:repeat(4,52px); gap:10px; }
  .original-keypad .numpad .btn { font-size:22px; }
}
.cheat-float { position:fixed; z-index:1000; right:max(12px,env(safe-area-inset-right)); top:44%; width:58px; height:36px; padding:0; color:#fff; background:rgba(20,20,24,.88); border:1px solid rgba(255,255,255,.28); border-radius:18px; box-shadow:0 4px 16px rgba(0,0,0,.35); font-size:11px; font-weight:800; letter-spacing:.3px; touch-action:none; user-select:none; -webkit-user-select:none; }
.cheat-float:active { transform:scale(.96); }
#cheat-dialog { position:fixed; z-index:1200; max-height:82dvh; overflow:auto; }
'''
write(p, css)

p = Path("wie-web/src/ts/app.ts")
ts = read(p)
old_down = '''        button.setPointerCapture(event.pointerId);\n        wieWeb.key_down(key);'''
new_down = '''        button.setPointerCapture(event.pointerId);\n        button.classList.add("pressed");\n        wieWeb.key_down(key);'''
if old_down not in ts: raise SystemExit("pointerdown block not found")
ts = ts.replace(old_down, new_down, 1)
old_release = '''      event.preventDefault();\n      wieWeb.key_up(key);'''
new_release = '''      event.preventDefault();\n      button.classList.remove("pressed");\n      wieWeb.key_up(key);'''
if old_release not in ts: raise SystemExit("pointer release block not found")
ts = ts.replace(old_release, new_release, 1)
old_cheat = '''  cheatOpen.addEventListener("click", () => cheatDialog.showModal(), { signal: abortController.signal });'''
if old_cheat not in ts: raise SystemExit("cheat click hook not found")
drag_code = r'''  // Floating CHEAT button: tap opens, drag moves. Position persists per app.
  const CHEAT_POS_KEY = "hero1-cheat-float-pos-v1";
  const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);
  const restoreCheatPosition = () => {
    try {
      const saved = JSON.parse(localStorage.getItem(CHEAT_POS_KEY) || "null");
      if (saved && Number.isFinite(saved.x) && Number.isFinite(saved.y)) {
        const r = cheatOpen.getBoundingClientRect();
        const vw = window.visualViewport?.width ?? window.innerWidth;
        const vh = window.visualViewport?.height ?? window.innerHeight;
        cheatOpen.style.right = "auto";
        cheatOpen.style.left = `${clamp(saved.x, 4, Math.max(4, vw - r.width - 4))}px`;
        cheatOpen.style.top = `${clamp(saved.y, 4, Math.max(4, vh - r.height - 4))}px`;
      }
    } catch (_) {}
  };
  requestAnimationFrame(restoreCheatPosition);
  let cheatPointerId: number | null = null;
  let cheatStartX = 0, cheatStartY = 0, cheatOriginX = 0, cheatOriginY = 0, cheatMoved = false;
  cheatOpen.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    cheatPointerId = event.pointerId;
    cheatMoved = false;
    cheatOpen.setPointerCapture(event.pointerId);
    const rect = cheatOpen.getBoundingClientRect();
    cheatStartX = event.clientX; cheatStartY = event.clientY; cheatOriginX = rect.left; cheatOriginY = rect.top;
    cheatOpen.style.right = "auto";
    cheatOpen.style.left = `${rect.left}px`; cheatOpen.style.top = `${rect.top}px`;
  }, { signal: abortController.signal });
  cheatOpen.addEventListener("pointermove", (event) => {
    if (cheatPointerId !== event.pointerId) return;
    const dx = event.clientX - cheatStartX, dy = event.clientY - cheatStartY;
    if (!cheatMoved && Math.hypot(dx, dy) >= 7) cheatMoved = true;
    if (!cheatMoved) return;
    event.preventDefault();
    const rect = cheatOpen.getBoundingClientRect();
    const vw = window.visualViewport?.width ?? window.innerWidth;
    const vh = window.visualViewport?.height ?? window.innerHeight;
    const x = clamp(cheatOriginX + dx, 4, Math.max(4, vw - rect.width - 4));
    const y = clamp(cheatOriginY + dy, 4, Math.max(4, vh - rect.height - 4));
    cheatOpen.style.left = `${x}px`; cheatOpen.style.top = `${y}px`;
  }, { signal: abortController.signal });
  const finishCheatPointer = (event: PointerEvent) => {
    if (cheatPointerId !== event.pointerId) return;
    event.preventDefault();
    try { cheatOpen.releasePointerCapture(event.pointerId); } catch (_) {}
    cheatPointerId = null;
    if (cheatMoved) {
      const rect = cheatOpen.getBoundingClientRect();
      try { localStorage.setItem(CHEAT_POS_KEY, JSON.stringify({ x: rect.left, y: rect.top })); } catch (_) {}
    } else if (!cheatDialog.open) {
      cheatDialog.showModal();
    }
  };
  cheatOpen.addEventListener("pointerup", finishCheatPointer, { signal: abortController.signal });
  cheatOpen.addEventListener("pointercancel", (event) => { if (cheatPointerId === event.pointerId) cheatPointerId = null; }, { signal: abortController.signal });'''
ts = ts.replace(old_cheat, drag_code, 1)
write(p, ts)

print("Hero1 original UI/keypad + draggable cheat overlay patch applied")