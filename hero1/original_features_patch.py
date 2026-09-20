from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(p): return (root / p).read_text(encoding='utf-8')
def write(p, s): (root / p).write_text(s, encoding='utf-8')

def replace_once(s, old, new, label):
    if old not in s:
        raise SystemExit(f'patch failed: {label}')
    return s.replace(old, new, 1)

# HTML: add floating tools button + settings dialog + hidden import controls
p = Path('wie-web/src/html/index.html')
s = read(p)
marker = '    <button id="cheat-open" class="cheat-float" type="button" aria-label="치트 메뉴">CHEAT</button>\n'
insert = marker + '''    <button id="tools-open" class="tools-float" type="button" aria-label="패드 및 세이브 설정">설정</button>\n\n'''
s = replace_once(s, marker, insert, 'tools floating button')

dialog_marker = '    <dialog id="cheat-dialog" class="app-dialog">'
tools_dialog = r'''    <dialog id="tools-dialog" class="app-dialog hero-tools-dialog">
      <form method="dialog">
        <header class="dialog-header">
          <h2>패드 / 세이브</h2>
          <button class="icon-button dialog-close" value="cancel" aria-label="닫기">×</button>
        </header>

        <section class="hero-tool-section">
          <h3>패드 매핑</h3>
          <p>게임 동작을 고른 뒤 “입력 대기”를 누르고 게임패드 버튼을 누르세요.</p>
          <label class="hero-tool-label">게임 동작
            <select id="map-action">
              <option value="UP">위</option><option value="DOWN">아래</option>
              <option value="LEFT">왼쪽</option><option value="RIGHT">오른쪽</option>
              <option value="OK">OK</option><option value="CLR">C / 취소</option>
              <option value="1">1</option><option value="2">2</option><option value="3">3</option>
              <option value="4">4</option><option value="5">5</option><option value="6">6</option>
              <option value="7">7</option><option value="8">8</option><option value="9">9</option>
              <option value="*">*</option><option value="0">0</option><option value="#">#</option>
            </select>
          </label>
          <div class="hero-tool-row">
            <button id="map-capture" type="button" class="primary-command">입력 대기</button>
            <button id="map-clear" type="button" class="secondary-command">선택 해제</button>
            <button id="map-reset" type="button" class="secondary-command">기본값</button>
          </div>
          <p id="map-status" class="hero-tool-status">연결된 패드를 기다리는 중…</p>
          <div class="hero-tool-row">
            <button id="preset-export" type="button" class="secondary-command">매핑 내보내기</button>
            <button id="preset-import" type="button" class="secondary-command">매핑 가져오기</button>
          </div>
          <input id="preset-import-file" type="file" accept="application/json,.json" hidden>
        </section>

        <section class="hero-tool-section">
          <h3>세이브 데이터</h3>
          <p>영웅서기 DB와 파일 저장 데이터를 하나의 백업 파일로 내보내거나 복원합니다.</p>
          <div class="hero-tool-row">
            <button id="save-export" type="button" class="primary-command">세이브 내보내기</button>
            <button id="save-import" type="button" class="secondary-command">세이브 가져오기</button>
          </div>
          <input id="save-import-file" type="file" accept="application/json,.json" hidden>
          <p id="save-status" class="hero-tool-status"></p>
        </section>
      </form>
    </dialog>

'''
s = replace_once(s, dialog_marker, tools_dialog + dialog_marker, 'tools dialog')
write(p, s)

# CSS for tools UI and second floating button
p = Path('wie-web/src/css/style.css')
css = read(p)
css += r'''

.tools-float {
  position: fixed;
  z-index: 1000;
  left: max(12px, env(safe-area-inset-left));
  top: 44%;
  width: 58px;
  height: 36px;
  padding: 0;
  color: #fff;
  background: rgba(20,20,24,.88);
  border: 1px solid rgba(255,255,255,.28);
  border-radius: 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,.35);
  font-size: 11px;
  font-weight: 800;
  touch-action: manipulation;
}
.hero-tools-dialog form { max-height: 82dvh; overflow: auto; }
.hero-tool-section { padding: 10px 0 4px; border-top: 1px solid #e2e8f0; }
.hero-tool-section:first-of-type { border-top: 0; }
.hero-tool-section h3 { margin: 6px 0 4px; font-size: 1rem; }
.hero-tool-section p { margin: 4px 0 10px; font-size: .85rem; }
.hero-tool-label { display: grid; gap: 5px; font-size: .86rem; }
.hero-tool-label select { min-height: 40px; padding: 6px 8px; font-size: 1rem; }
.hero-tool-row { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 9px; }
.hero-tool-row button { flex: 1 1 110px; min-width: 0; }
.hero-tool-status { min-height: 1.4em; color: #475569 !important; }
'''
write(p, css)

# TypeScript feature implementation
p = Path('wie-web/src/ts/app.ts')
ts = read(p)
anchor = '''  cheatOpen.addEventListener("pointercancel", (event) => {\n    if (cheatPointerId === event.pointerId) cheatPointerId = null;\n  }, { signal: abortController.signal });\n'''
if anchor not in ts:
    raise SystemExit('patch failed: cheat drag anchor')

feature_ts = r'''

  // Original-wrapper style pad mapping + save backup/restore.
  const toolsOpen = document.getElementById("tools-open") as HTMLButtonElement;
  const toolsDialog = document.getElementById("tools-dialog") as HTMLDialogElement;
  const mapAction = document.getElementById("map-action") as HTMLSelectElement;
  const mapCapture = document.getElementById("map-capture") as HTMLButtonElement;
  const mapClear = document.getElementById("map-clear") as HTMLButtonElement;
  const mapReset = document.getElementById("map-reset") as HTMLButtonElement;
  const mapStatus = document.getElementById("map-status") as HTMLElement;
  const presetExport = document.getElementById("preset-export") as HTMLButtonElement;
  const presetImport = document.getElementById("preset-import") as HTMLButtonElement;
  const presetImportFile = document.getElementById("preset-import-file") as HTMLInputElement;
  const saveExport = document.getElementById("save-export") as HTMLButtonElement;
  const saveImport = document.getElementById("save-import") as HTMLButtonElement;
  const saveImportFile = document.getElementById("save-import-file") as HTMLInputElement;
  const saveStatus = document.getElementById("save-status") as HTMLElement;

  toolsOpen.addEventListener("click", () => toolsDialog.showModal(), { signal: abortController.signal });

  type PadMap = Record<string, number>;
  const PAD_MAP_KEY = "hero1-padmap-v1";
  const DEFAULT_PAD_MAP: PadMap = { OK: 0, CLR: 1, "1": 2, "3": 3, UP: 12, DOWN: 13, LEFT: 14, RIGHT: 15 };
  const loadPadMap = (): PadMap => {
    try { return { ...DEFAULT_PAD_MAP, ...JSON.parse(localStorage.getItem(PAD_MAP_KEY) || "{}") }; }
    catch (_) { return { ...DEFAULT_PAD_MAP }; }
  };
  let padMap: PadMap = loadPadMap();
  let captureAction: string | null = null;
  let captureIgnore = new Set<number>();
  const gamepadHeld = new Set<string>();

  const savePadMap = () => {
    localStorage.setItem(PAD_MAP_KEY, JSON.stringify(padMap));
    updateMapStatus();
  };
  const updateMapStatus = () => {
    const action = mapAction.value;
    const button = padMap[action];
    const pads = Array.from(navigator.getGamepads?.() || []).filter(Boolean);
    const padName = pads[0]?.id || "게임패드 미연결";
    mapStatus.textContent = `${padName} · ${action} = ${button === undefined ? "미지정" : `버튼 ${button}`}`;
  };
  mapAction.addEventListener("change", updateMapStatus, { signal: abortController.signal });
  mapCapture.addEventListener("click", () => {
    captureAction = mapAction.value;
    captureIgnore.clear();
    for (const gp of Array.from(navigator.getGamepads?.() || [])) {
      if (!gp) continue;
      gp.buttons.forEach((b, i) => { if (b.pressed) captureIgnore.add(i); });
    }
    mapStatus.textContent = `${captureAction}: 누를 게임패드 버튼을 기다리는 중…`;
  }, { signal: abortController.signal });
  mapClear.addEventListener("click", () => {
    delete padMap[mapAction.value];
    savePadMap();
  }, { signal: abortController.signal });
  mapReset.addEventListener("click", () => {
    padMap = { ...DEFAULT_PAD_MAP };
    savePadMap();
  }, { signal: abortController.signal });
  window.addEventListener("gamepadconnected", updateMapStatus, { signal: abortController.signal });
  window.addEventListener("gamepaddisconnected", updateMapStatus, { signal: abortController.signal });
  updateMapStatus();

  const pollGamepad = () => {
    const gp = Array.from(navigator.getGamepads?.() || []).find((p) => p && p.connected);
    if (!gp) return;

    if (captureAction) {
      for (let i = 0; i < gp.buttons.length; i++) {
        if (captureIgnore.has(i)) {
          if (!gp.buttons[i].pressed) captureIgnore.delete(i);
          continue;
        }
        if (gp.buttons[i].pressed) {
          // Keep one physical button assigned to one action, matching the old PadCfg behavior.
          for (const [action, idx] of Object.entries(padMap)) if (idx === i) delete padMap[action];
          padMap[captureAction] = i;
          const done = captureAction;
          captureAction = null;
          savePadMap();
          mapStatus.textContent = `${done} → 버튼 ${i}`;
          break;
        }
      }
    }

    const desired = new Set<string>();
    for (const [action, index] of Object.entries(padMap)) {
      if (gp.buttons[index]?.pressed) desired.add(action);
    }
    // Standard pad axes also work even before custom mapping.
    if ((gp.axes[1] ?? 0) < -0.55) desired.add("UP");
    if ((gp.axes[1] ?? 0) > 0.55) desired.add("DOWN");
    if ((gp.axes[0] ?? 0) < -0.55) desired.add("LEFT");
    if ((gp.axes[0] ?? 0) > 0.55) desired.add("RIGHT");

    for (const key of desired) {
      if (!gamepadHeld.has(key)) {
        gamepadHeld.add(key);
        wieWeb.key_down(key);
      }
    }
    for (const key of Array.from(gamepadHeld)) {
      if (!desired.has(key)) {
        gamepadHeld.delete(key);
        wieWeb.key_up(key);
      }
    }
  };

  const bytesToBase64 = (value: unknown): string => {
    const bytes = value instanceof Uint8Array ? value : value instanceof ArrayBuffer ? new Uint8Array(value) : new Uint8Array(value as ArrayBufferLike);
    let binary = "";
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) binary += String.fromCharCode(...bytes.subarray(i, i + chunk));
    return btoa(binary);
  };
  const base64ToBytes = (value: string): Uint8Array => {
    const binary = atob(value);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
    return bytes;
  };
  const openDb = (name: string): Promise<IDBDatabase> => new Promise((resolve, reject) => {
    const req = indexedDB.open(name);
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  const txDone = (tx: IDBTransaction): Promise<void> => new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error || new Error("IndexedDB transaction aborted"));
  });
  const reqResult = <T>(req: IDBRequest<T>): Promise<T> => new Promise((resolve, reject) => {
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  const downloadOrShare = async (filename: string, text: string) => {
    const file = new File([text], filename, { type: "application/json" });
    const nav = navigator as Navigator & { canShare?: (data: ShareData) => boolean; share?: (data: ShareData) => Promise<void> };
    if (nav.share && (!nav.canShare || nav.canShare({ files: [file] }))) {
      await nav.share({ files: [file], title: filename });
      return;
    }
    const url = URL.createObjectURL(file);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  };

  presetExport.addEventListener("click", () => void (async () => {
    await downloadOrShare(`hero1_padmap_${new Date().toISOString().slice(0,10)}.json`, JSON.stringify({ version: 1, padMap }, null, 2));
  })().catch((e) => { mapStatus.textContent = `내보내기 실패: ${String(e)}`; }), { signal: abortController.signal });
  presetImport.addEventListener("click", () => presetImportFile.click(), { signal: abortController.signal });
  presetImportFile.addEventListener("change", () => void (async () => {
    const file = presetImportFile.files?.[0]; if (!file) return;
    const data = JSON.parse(await file.text());
    if (!data || data.version !== 1 || typeof data.padMap !== "object") throw new Error("지원하지 않는 매핑 파일입니다.");
    padMap = { ...data.padMap };
    savePadMap();
    mapStatus.textContent = "매핑을 가져왔습니다.";
    presetImportFile.value = "";
  })().catch((e) => { mapStatus.textContent = `가져오기 실패: ${String(e)}`; }), { signal: abortController.signal });

  const AID = "010100D5";
  saveExport.addEventListener("click", () => void (async () => {
    saveStatus.textContent = "세이브를 읽는 중…";
    const dbName = `wie_${AID}`;
    const db = await openDb(dbName);
    const dbStoreName = db.objectStoreNames.contains(dbName) ? dbName : db.objectStoreNames[0];
    const dbTx = db.transaction(dbStoreName, "readonly");
    const dbStore = dbTx.objectStore(dbStoreName);
    const dbKeys = await reqResult(dbStore.getAllKeys());
    const database: Array<{ key: IDBValidKey; data: string }> = [];
    for (const key of dbKeys) {
      const value = await reqResult(dbStore.get(key));
      if (value !== undefined) database.push({ key, data: bytesToBase64(value) });
    }
    await txDone(dbTx);
    db.close();

    const fsDb = await openDb("wie_filesystem");
    const fsTx = fsDb.transaction("files", "readonly");
    const fsStore = fsTx.objectStore("files");
    const fsKeys = await reqResult(fsStore.getAllKeys());
    const filesystem: Array<{ key: IDBValidKey; data: string }> = [];
    for (const key of fsKeys) {
      if (!Array.isArray(key) || String(key[0]) !== AID) continue;
      const value = await reqResult(fsStore.get(key));
      if (value !== undefined) filesystem.push({ key, data: bytesToBase64(value) });
    }
    await txDone(fsTx);
    fsDb.close();

    const bundle = { format: "hero1-wie-save", version: 1, aid: AID, exportedAt: new Date().toISOString(), database, filesystem };
    const filename = `hero1_save_${new Date().toISOString().replace(/[:.]/g,"-")}.json`;
    await downloadOrShare(filename, JSON.stringify(bundle));
    saveStatus.textContent = `내보내기 완료 · DB ${database.length}개 / 파일 ${filesystem.length}개`;
  })().catch((e) => { saveStatus.textContent = `내보내기 실패: ${String(e)}`; }), { signal: abortController.signal });

  saveImport.addEventListener("click", () => saveImportFile.click(), { signal: abortController.signal });
  saveImportFile.addEventListener("change", () => void (async () => {
    const file = saveImportFile.files?.[0]; if (!file) return;
    saveStatus.textContent = "세이브를 복원하는 중…";
    const bundle = JSON.parse(await file.text());
    if (!bundle || bundle.format !== "hero1-wie-save" || bundle.version !== 1 || bundle.aid !== AID) throw new Error("영웅서기1 세이브 백업 파일이 아닙니다.");

    const dbName = `wie_${AID}`;
    const db = await openDb(dbName);
    const dbStoreName = db.objectStoreNames.contains(dbName) ? dbName : db.objectStoreNames[0];
    const dbTx = db.transaction(dbStoreName, "readwrite");
    const dbStore = dbTx.objectStore(dbStoreName);
    dbStore.clear();
    for (const item of bundle.database || []) dbStore.put(base64ToBytes(item.data), item.key);
    await txDone(dbTx);
    db.close();

    const fsDb = await openDb("wie_filesystem");
    const readTx = fsDb.transaction("files", "readonly");
    const readStore = readTx.objectStore("files");
    const existingFsKeys = await reqResult(readStore.getAllKeys());
    await txDone(readTx);
    const fsTx = fsDb.transaction("files", "readwrite");
    const fsStore = fsTx.objectStore("files");
    for (const key of existingFsKeys) if (Array.isArray(key) && String(key[0]) === AID) fsStore.delete(key);
    for (const item of bundle.filesystem || []) fsStore.put(base64ToBytes(item.data), item.key);
    await txDone(fsTx);
    fsDb.close();

    saveImportFile.value = "";
    saveStatus.textContent = "복원 완료. 게임을 다시 시작합니다…";
    setTimeout(() => location.reload(), 700);
  })().catch((e) => { saveStatus.textContent = `가져오기 실패: ${String(e)}`; }), { signal: abortController.signal });
'''
ts = ts.replace(anchor, anchor + feature_ts, 1)

# Poll mapped hardware controller every emulator frame.
update_anchor = '''    try {\n      wieWeb.update();\n      requestAnimationFrame(update);\n'''
if update_anchor not in ts:
    raise SystemExit('patch failed: update loop')
ts = ts.replace(update_anchor, '''    try {\n      pollGamepad();\n      wieWeb.update();\n      requestAnimationFrame(update);\n''', 1)
write(p, ts)

print('Hero1 mapping + save import/export features patched')