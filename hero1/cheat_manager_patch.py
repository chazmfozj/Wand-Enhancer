from pathlib import Path
import re, sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(p): return (root / p).read_text(encoding='utf-8')
def write(p, s): (root / p).write_text(s, encoding='utf-8')
def replace_once(s, old, new, label):
    if old not in s:
        raise SystemExit(f'patch failed: {label}')
    return s.replace(old, new, 1)

# Expand the CHEAT dialog with a reusable saved-cheat manager.
p = Path('wie-web/src/html/index.html')
s = read(p)
needle = '<button id="cheat-apply" type="button" class="primary-command" disabled style="margin-top:10px;width:100%">선택 주소에 적용</button>'
insert = needle + r'''
        <section class="cheat-manager-section">
          <h3>치트 등록</h3>
          <div class="cheat-register-row">
            <input id="cheat-name" type="text" maxlength="24" placeholder="이름 예: 골드, 경험치, 스탯포인트">
            <button id="cheat-save-item" type="button" class="secondary-command" disabled>현재 후보 등록</button>
          </div>
          <p class="cheat-help">등록한 항목은 앱을 다시 켜도 남습니다. 주소가 바뀌면 후보를 다시 찾고 ‘선택주소로 갱신’을 누르세요.</p>
          <div class="cheat-manager-actions">
            <button id="cheat-refresh-all" type="button" class="secondary-command">전체 값 새로고침</button>
            <button id="cheat-apply-all" type="button" class="primary-command">전체 적용</button>
          </div>
          <div id="cheat-saved-list" class="cheat-saved-list"></div>
        </section>'''
s = replace_once(s, needle, insert, 'cheat manager html')
write(p, s)

# Style the cheat manager for phone screens.
p = Path('wie-web/src/css/style.css')
css = read(p)
css += r'''

.cheat-manager-section { margin-top:14px; padding-top:12px; border-top:1px solid #e2e8f0; }
.cheat-manager-section h3 { margin:0 0 8px; font-size:1rem; }
.cheat-register-row { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:7px; }
.cheat-register-row input { min-width:0; min-height:40px; padding:7px 9px; font-size:15px; }
.cheat-help { margin:7px 0 10px !important; font-size:.78rem !important; line-height:1.4 !important; }
.cheat-manager-actions { display:flex; gap:7px; margin-bottom:10px; }
.cheat-manager-actions button { flex:1; min-width:0; }
.cheat-saved-list { display:grid; gap:8px; }
.cheat-card { border:1px solid #cbd5e1; border-radius:8px; padding:9px; background:#f8fafc; }
.cheat-card-top { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:8px; align-items:center; }
.cheat-card-name { font-weight:800; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.cheat-card-address { font-family:ui-monospace,SFMono-Regular,Consolas,monospace; color:#64748b; font-size:.76rem; }
.cheat-card-values { display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-top:8px; }
.cheat-card-values label { display:grid; gap:3px; font-size:.76rem; color:#475569; }
.cheat-card-values input { width:100%; min-width:0; min-height:36px; padding:5px 7px; font-size:14px; }
.cheat-current-value { display:flex; align-items:center; min-height:36px; padding:5px 7px; background:#fff; border:1px solid #cbd5e1; border-radius:4px; font-family:ui-monospace,SFMono-Regular,Consolas,monospace; font-size:14px; }
.cheat-last-change { margin:7px 0 0; min-height:1.25em; color:#64748b; font-size:.75rem; }
.cheat-card-actions { display:flex; flex-wrap:wrap; gap:6px; margin-top:8px; }
.cheat-card-actions button { flex:1 1 82px; min-height:34px; padding:5px 7px; font-size:.78rem; }
.cheat-freeze-label { display:flex; align-items:center; gap:5px; padding:0 3px; font-size:.78rem; white-space:nowrap; }
.cheat-card.invalid { border-color:#fca5a5; background:#fff7f7; }
'''
write(p, css)

# Enhance candidate rows to show the live value and enable registration.
p = Path('wie-web/src/ts/app.ts')
ts = read(p)
ts = replace_once(
    ts,
    'option.textContent = `0x${(address >>> 0).toString(16).padStart(8, "0")}`;',
    'option.textContent = `0x${(address >>> 0).toString(16).padStart(8, "0")} · 현재 ${wieWeb.cheat_read_u32(address >>> 0)}`;',
    'candidate current value',
)
ts = replace_once(
    ts,
    '    cheatApply.disabled = candidates.length === 0;\n    cheatRefine.disabled = candidates.length === 0;',
    '    cheatApply.disabled = candidates.length === 0;\n    cheatRefine.disabled = candidates.length === 0;\n    const saveButton = document.getElementById("cheat-save-item") as HTMLButtonElement | null;\n    if (saveButton) saveButton.disabled = candidates.length === 0;',
    'candidate save enable',
)

# Insert saved-cheat manager after the draggable overlay handlers, before mapping/save feature code.
anchor = '  cheatOpen.addEventListener("pointercancel", (event) => { if (cheatPointerId === event.pointerId) cheatPointerId = null; }, { signal: abortController.signal });'
if anchor not in ts:
    raise SystemExit('patch failed: cheat manager anchor')

manager_ts = r'''

  type SavedCheat = {
    id: string;
    name: string;
    address: number;
    target: number;
    freeze: boolean;
    lastBefore?: number;
    lastAfter?: number;
  };
  const SAVED_CHEATS_KEY = "hero1-saved-cheats-v2";
  const cheatName = document.getElementById("cheat-name") as HTMLInputElement;
  const cheatSaveItem = document.getElementById("cheat-save-item") as HTMLButtonElement;
  const cheatSavedList = document.getElementById("cheat-saved-list") as HTMLElement;
  const cheatRefreshAll = document.getElementById("cheat-refresh-all") as HTMLButtonElement;
  const cheatApplyAll = document.getElementById("cheat-apply-all") as HTMLButtonElement;

  const loadSavedCheats = (): SavedCheat[] => {
    try {
      const parsed = JSON.parse(localStorage.getItem(SAVED_CHEATS_KEY) || "[]");
      return Array.isArray(parsed) ? parsed.filter((x) => x && Number.isFinite(x.address)) : [];
    } catch (_) { return []; }
  };
  let savedCheats: SavedCheat[] = loadSavedCheats();
  const saveSavedCheats = () => localStorage.setItem(SAVED_CHEATS_KEY, JSON.stringify(savedCheats));
  const makeCheatId = () => `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,8)}`;
  const selectedCandidateAddress = (): number | null => cheatCandidates.value ? (Number(cheatCandidates.value) >>> 0) : null;

  const readCheatSafe = (address: number): number | null => {
    try { return wieWeb.cheat_read_u32(address >>> 0); }
    catch (_) { return null; }
  };
  const writeSavedCheat = (item: SavedCheat) => {
    const before = readCheatSafe(item.address);
    if (before === null) throw new Error(`${item.name}: 주소를 읽을 수 없습니다.`);
    wieWeb.cheat_write_u32(item.address >>> 0, item.target >>> 0);
    item.lastBefore = before;
    item.lastAfter = item.target >>> 0;
    saveSavedCheats();
  };

  const refreshSavedValues = () => {
    for (const item of savedCheats) {
      const card = cheatSavedList.querySelector<HTMLElement>(`[data-cheat-id="${CSS.escape(item.id)}"]`);
      if (!card) continue;
      const current = readCheatSafe(item.address);
      const currentEl = card.querySelector<HTMLElement>("[data-role=current]");
      const lastEl = card.querySelector<HTMLElement>("[data-role=last]");
      if (current === null) {
        card.classList.add("invalid");
        if (currentEl) currentEl.textContent = "읽기 실패";
      } else {
        card.classList.remove("invalid");
        if (currentEl) currentEl.textContent = String(current >>> 0);
      }
      if (lastEl) {
        lastEl.textContent = item.lastBefore === undefined
          ? "아직 적용 기록 없음"
          : `마지막 변경: ${item.lastBefore} → ${item.lastAfter}`;
      }
    }
  };

  const renderSavedCheats = () => {
    cheatSavedList.replaceChildren();
    if (savedCheats.length === 0) {
      const empty = document.createElement("p");
      empty.className = "cheat-help";
      empty.textContent = "등록된 치트가 없습니다.";
      cheatSavedList.append(empty);
      return;
    }
    for (const item of savedCheats) {
      const card = document.createElement("div");
      card.className = "cheat-card";
      card.dataset.cheatId = item.id;

      const top = document.createElement("div");
      top.className = "cheat-card-top";
      const titleWrap = document.createElement("div");
      const nameEl = document.createElement("div");
      nameEl.className = "cheat-card-name";
      nameEl.textContent = item.name;
      const addressEl = document.createElement("div");
      addressEl.className = "cheat-card-address";
      addressEl.textContent = `0x${(item.address >>> 0).toString(16).padStart(8,"0")}`;
      titleWrap.append(nameEl, addressEl);
      const freezeLabel = document.createElement("label");
      freezeLabel.className = "cheat-freeze-label";
      const freeze = document.createElement("input");
      freeze.type = "checkbox";
      freeze.checked = !!item.freeze;
      freeze.addEventListener("change", () => { item.freeze = freeze.checked; saveSavedCheats(); });
      freezeLabel.append(freeze, document.createTextNode("값 고정"));
      top.append(titleWrap, freezeLabel);

      const values = document.createElement("div");
      values.className = "cheat-card-values";
      const currentLabel = document.createElement("label");
      currentLabel.append(document.createTextNode("현재값"));
      const current = document.createElement("div");
      current.className = "cheat-current-value";
      current.dataset.role = "current";
      current.textContent = "-";
      currentLabel.append(current);
      const targetLabel = document.createElement("label");
      targetLabel.append(document.createTextNode("목표값"));
      const target = document.createElement("input");
      target.type = "number";
      target.min = "0";
      target.max = "4294967295";
      target.inputMode = "numeric";
      target.value = String(item.target >>> 0);
      target.addEventListener("change", () => {
        const value = Number(target.value);
        if (Number.isFinite(value) && value >= 0 && value <= 0xffffffff) {
          item.target = value >>> 0;
          saveSavedCheats();
        } else target.value = String(item.target >>> 0);
      });
      targetLabel.append(target);
      values.append(currentLabel, targetLabel);

      const last = document.createElement("p");
      last.className = "cheat-last-change";
      last.dataset.role = "last";

      const actions = document.createElement("div");
      actions.className = "cheat-card-actions";
      const apply = document.createElement("button");
      apply.type = "button";
      apply.className = "primary-command";
      apply.textContent = "적용";
      apply.addEventListener("click", () => runCheat(() => { writeSavedCheat(item); refreshSavedValues(); cheatStatus.textContent = `${item.name} 적용 완료`; }));
      const rebind = document.createElement("button");
      rebind.type = "button";
      rebind.className = "secondary-command";
      rebind.textContent = "선택주소로 갱신";
      rebind.addEventListener("click", () => runCheat(() => {
        const address = selectedCandidateAddress();
        if (address === null) throw new Error("먼저 후보 주소를 선택하세요.");
        item.address = address;
        saveSavedCheats();
        renderSavedCheats();
        refreshSavedValues();
        cheatStatus.textContent = `${item.name} 주소 갱신 완료`;
      }));
      const rename = document.createElement("button");
      rename.type = "button";
      rename.className = "secondary-command";
      rename.textContent = "이름변경";
      rename.addEventListener("click", () => {
        const next = window.prompt("치트 이름", item.name)?.trim();
        if (next) { item.name = next.slice(0,24); saveSavedCheats(); renderSavedCheats(); refreshSavedValues(); }
      });
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "secondary-command";
      remove.textContent = "삭제";
      remove.addEventListener("click", () => {
        savedCheats = savedCheats.filter((x) => x.id !== item.id);
        saveSavedCheats();
        renderSavedCheats();
        refreshSavedValues();
      });
      actions.append(apply, rebind, rename, remove);
      card.append(top, values, last, actions);
      cheatSavedList.append(card);
    }
    refreshSavedValues();
  };

  cheatCandidates.addEventListener("change", () => {
    const address = selectedCandidateAddress();
    if (address !== null) {
      const value = readCheatSafe(address);
      if (value !== null) cheatCurrent.value = String(value);
    }
  }, { signal: abortController.signal });

  cheatSaveItem.addEventListener("click", () => runCheat(() => {
    const address = selectedCandidateAddress();
    if (address === null) throw new Error("등록할 후보 주소를 선택하세요.");
    const target = parseValue(cheatNew);
    const name = (cheatName.value.trim() || `치트 ${savedCheats.length + 1}`).slice(0,24);
    const existing = savedCheats.find((x) => x.address === address);
    if (existing) {
      existing.name = name;
      existing.target = target;
    } else {
      savedCheats.push({ id: makeCheatId(), name, address, target, freeze: false });
    }
    saveSavedCheats();
    cheatName.value = "";
    renderSavedCheats();
    cheatStatus.textContent = `${name} 등록 완료`;
  }), { signal: abortController.signal });

  cheatRefreshAll.addEventListener("click", refreshSavedValues, { signal: abortController.signal });
  cheatApplyAll.addEventListener("click", () => runCheat(() => {
    for (const item of savedCheats) writeSavedCheat(item);
    refreshSavedValues();
    cheatStatus.textContent = `등록 치트 ${savedCheats.length}개 전체 적용 완료`;
  }), { signal: abortController.signal });

  let freezeTick = 0;
  const freezeTimer = window.setInterval(() => {
    freezeTick++;
    for (const item of savedCheats) {
      if (!item.freeze) continue;
      try { wieWeb.cheat_write_u32(item.address >>> 0, item.target >>> 0); } catch (_) {}
    }
    if (cheatDialog.open && freezeTick % 2 === 0) refreshSavedValues();
  }, 350);
  abortController.signal.addEventListener("abort", () => clearInterval(freezeTimer), { once: true });
  renderSavedCheats();
'''

ts = ts.replace(anchor, anchor + manager_ts, 1)
write(p, ts)
print('Hero1 persistent cheat manager patched')