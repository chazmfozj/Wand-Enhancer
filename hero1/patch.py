from pathlib import Path
import re, sys, json

root = Path(sys.argv[1] if len(sys.argv) > 1 else '.')

def read(p): return (root/p).read_text(encoding='utf-8')
def write(p,s): (root/p).write_text(s,encoding='utf-8')

def replace_once(text, old, new, label):
    if old not in text:
        raise SystemExit(f'patch failed: {label}')
    return text.replace(old,new,1)

p = Path('wie-app/tauri.conf.json')
conf = json.loads(read(p))
conf['productName'] = '영웅서기 1 - 솔티아의 바람'
conf['identifier'] = 'net.hero1.soltia.originalcheat'
if 'app' in conf and 'windows' in conf['app'] and conf['app']['windows']:
    conf['app']['windows'][0]['title'] = '영웅서기 1 - 솔티아의 바람'
write(p, json.dumps(conf, ensure_ascii=False, indent=2) + '\n')

p = Path('wie-ktf/src/emulator.rs')
s = read(p)
needle = 'impl KtfEmulator {\n'
insert = '''impl KtfEmulator {\n    /// Host-side access used by the standalone Hero1 cheat panel.\n    pub fn core(&self) -> ArmCore {\n        self.core.clone()\n    }\n\n'''
s = replace_once(s, needle, insert, 'ktf core getter')
write(p,s)

p = Path('wie-core-arm/src/core.rs')
s = read(p)
needle = '''    pub fn map(&mut self, address: u32, size: u32) -> Result<()> {\n        tracing::trace!("Map address: {address:#x}, size: {size:#x}");\n\n        let mut inner = self.inner.lock();\n\n        inner.engine.mem_map(address, size as usize, MemoryPermission::ReadWrite);\n\n        Ok(())\n    }\n'''
insert = needle + '''\n    pub fn cheat_read_u32(&self, address: u32) -> Result<u32> {\n        let mut inner = self.inner.lock();\n        let mut buf = [0u8; 4];\n        inner.engine.mem_read(address, 4, &mut buf)?;\n        Ok(u32::from_le_bytes(buf))\n    }\n\n    pub fn cheat_write_u32(&mut self, address: u32, value: u32) -> Result<()> {\n        let mut inner = self.inner.lock();\n        inner.engine.mem_write(address, &value.to_le_bytes())\n    }\n\n    pub fn cheat_scan_u32(&self, value: u32, full: bool, max_results: usize) -> Result<Vec<u32>> {\n        const PAGE: usize = 0x10000;\n        const FAST: &[(u32, u32)] = &[\n            (0x0010_0000, 0x0100_0000),\n            (0x4000_0000, 0x4100_0000),\n            (0x4800_0000, 0x4900_0000),\n        ];\n        const FULL: &[(u32, u32)] = &[\n            (0x0010_0000, 0x0100_0000),\n            (0x4000_0000, 0x5000_0000),\n        ];\n        let ranges = if full { FULL } else { FAST };\n        let mut inner = self.inner.lock();\n        let mut page_buf = vec![0u8; PAGE];\n        let mut out = Vec::new();\n        for &(start, end) in ranges {\n            let mut page = start & !0xffff;\n            while page < end {\n                if inner.engine.is_mapped(page, PAGE) {\n                    inner.engine.mem_read(page, PAGE, &mut page_buf)?;\n                    let begin = start.saturating_sub(page) as usize;\n                    let finish = ((end - page) as usize).min(PAGE);\n                    let mut off = (begin + 3) & !3;\n                    while off + 4 <= finish {\n                        if u32::from_le_bytes(page_buf[off..off + 4].try_into().unwrap()) == value {\n                            out.push(page + off as u32);\n                            if out.len() >= max_results { return Ok(out); }\n                        }\n                        off += 4;\n                    }\n                }\n                page = page.saturating_add(PAGE as u32);\n            }\n        }\n        Ok(out)\n    }\n'''
s = replace_once(s, needle, insert, 'ArmCore cheat helpers')
write(p,s)

p = Path('wie-web/Cargo.toml')
s = read(p)
needle = 'wie-backend = { workspace = true }\n'
s = replace_once(s, needle, needle + 'wie-core-arm = { workspace = true }\n', 'wie-web core dependency')
write(p,s)

p = Path('wie-web/src/rust/lib.rs')
s = read(p)
s = replace_once(s, 'use wie_backend::{Emulator, Event, Font, Instant, KeyCode, Options, Platform, Screen, extract_zip};\n',
'''use wie_backend::{Emulator, Event, Font, Instant, KeyCode, Options, Platform, Screen, extract_zip};\nuse wie_core_arm::ArmCore;\n''', 'import ArmCore')
s = replace_once(s,
'''pub struct WieWeb {\n    emulator: Box<dyn Emulator>,\n    audio_player: AudioPlayer,\n    should_redraw: Arc<AtomicBool>,\n    key_events: HashMap<KeyCode, f64>,\n}\n''',
'''pub struct WieWeb {\n    emulator: Box<dyn Emulator>,\n    ktf_core: Option<ArmCore>,\n    audio_player: AudioPlayer,\n    should_redraw: Arc<AtomicBool>,\n    key_events: HashMap<KeyCode, f64>,\n}\n''', 'WieWeb core field')
old = '''            let emulator: Box<dyn Emulator> = if filename.to_ascii_lowercase().ends_with(".zip") {\n                let (archive_platform, files) = parse_archive(buf)?;\n\n                match archive_platform {\n                    ArchivePlatform::Ktf => Box::new(KtfEmulator::from_archive(platform, files, options)?),\n                    ArchivePlatform::Lgt => Box::new(LgtEmulator::from_archive(platform, files, options)?),\n                    ArchivePlatform::Skt => Box::new(SktEmulator::from_archive(platform, files)?),\n                }\n'''
new = '''            let mut ktf_core: Option<ArmCore> = None;\n            let emulator: Box<dyn Emulator> = if filename.to_ascii_lowercase().ends_with(".zip") {\n                let (archive_platform, files) = parse_archive(buf)?;\n\n                match archive_platform {\n                    ArchivePlatform::Ktf => {\n                        let emulator = KtfEmulator::from_archive(platform, files, options)?;\n                        ktf_core = Some(emulator.core());\n                        Box::new(emulator)\n                    },\n                    ArchivePlatform::Lgt => Box::new(LgtEmulator::from_archive(platform, files, options)?),\n                    ArchivePlatform::Skt => Box::new(SktEmulator::from_archive(platform, files)?),\n                }\n'''
s = replace_once(s, old, new, 'capture KTF core')
s = replace_once(s,
'''            anyhow::Ok(Self {\n                emulator,\n                audio_player: audio_player.clone(),\n                should_redraw,\n                key_events: HashMap::new(),\n            })\n''',
'''            anyhow::Ok(Self {\n                emulator,\n                ktf_core,\n                audio_player: audio_player.clone(),\n                should_redraw,\n                key_events: HashMap::new(),\n            })\n''', 'store KTF core')
needle = '''    pub fn set_pcm_volume(&self, volume: f32) {\n        audio_sink::set_pcm_volume(volume);\n    }\n'''
insert = needle + '''\n    pub fn cheat_scan_u32(&self, value: u32, full: bool) -> Result<Vec<u32>, JsError> {\n        let core = self.ktf_core.as_ref().ok_or_else(|| JsError::new("KTF core is not available"))?;\n        core.cheat_scan_u32(value, full, 10000).map_err(|e| JsError::new(&e.to_string()))\n    }\n\n    pub fn cheat_read_u32(&self, address: u32) -> Result<u32, JsError> {\n        let core = self.ktf_core.as_ref().ok_or_else(|| JsError::new("KTF core is not available"))?;\n        core.cheat_read_u32(address).map_err(|e| JsError::new(&e.to_string()))\n    }\n\n    pub fn cheat_write_u32(&mut self, address: u32, value: u32) -> Result<(), JsError> {\n        let core = self.ktf_core.as_mut().ok_or_else(|| JsError::new("KTF core is not available"))?;\n        core.cheat_write_u32(address, value).map_err(|e| JsError::new(&e.to_string()))\n    }\n'''
s = replace_once(s, needle, insert, 'JS cheat exports')
write(p,s)

p = Path('wie-web/src/ts/index.ts')
write(p, r'''import { runApp } from "./app";
import { AppMetadata } from "./app_library_store";
import { initializeSettings } from "./settings";

const main = async () => {
  const playerView = document.getElementById("player-view") as HTMLElement;
  const settings = initializeSettings();
  const [fontResponse, gameResponse] = await Promise.all([
    fetch(new URL("../../../assets/neodgm.ttf", import.meta.url)),
    fetch(new URL("../assets/hero1_game.zip", import.meta.url)),
  ]);
  if (!fontResponse.ok) throw new Error(`Font load failed: ${fontResponse.status}`);
  if (!gameResponse.ok) throw new Error(`Hero1 load failed: ${gameResponse.status}`);
  const fontData = new Uint8Array(await fontResponse.arrayBuffer());
  const archive = new Uint8Array(await gameResponse.arrayBuffer());
  const app: AppMetadata = {
    id: "010100D5",
    title: "영웅서기 1 - 솔티아의 바람",
    filename: "hero1_game.zip",
    addedAt: 0,
  };
  playerView.hidden = false;
  runApp(app, archive, fontData, settings, (error) => {
    if (error !== undefined) {
      console.error(error);
      window.alert(`게임 실행 오류: ${String(error)}`);
    }
  });
};

const start = () => void main().catch((error) => {
  console.error(error);
  window.alert(`영웅서기1을 시작할 수 없습니다. ${String(error)}`);
});
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
else start();
''')

p = Path('wie-web/src/ts/app.ts')
s = read(p)
needle = '  appSettings.addEventListener("click", settings.open, { signal: abortController.signal });\n'
cheat_ts = r'''  appSettings.addEventListener("click", settings.open, { signal: abortController.signal });

  const cheatOpen = document.getElementById("cheat-open") as HTMLButtonElement;
  const cheatDialog = document.getElementById("cheat-dialog") as HTMLDialogElement;
  const cheatCurrent = document.getElementById("cheat-current") as HTMLInputElement;
  const cheatNew = document.getElementById("cheat-new") as HTMLInputElement;
  const cheatFull = document.getElementById("cheat-full") as HTMLInputElement;
  const cheatScan = document.getElementById("cheat-scan") as HTMLButtonElement;
  const cheatRefine = document.getElementById("cheat-refine") as HTMLButtonElement;
  const cheatApply = document.getElementById("cheat-apply") as HTMLButtonElement;
  const cheatCandidates = document.getElementById("cheat-candidates") as HTMLSelectElement;
  const cheatStatus = document.getElementById("cheat-status") as HTMLElement;
  let candidates: number[] = [];

  const parseValue = (input: HTMLInputElement) => {
    const text = input.value.trim();
    if (!/^\d+$/.test(text)) throw new Error("0 이상의 정수를 입력하세요.");
    const value = Number(text);
    if (!Number.isSafeInteger(value) || value < 0 || value > 0xffffffff) throw new Error("0~4294967295 범위만 가능합니다.");
    return value >>> 0;
  };
  const renderCandidates = () => {
    cheatCandidates.replaceChildren();
    for (const address of candidates.slice(0, 300)) {
      const option = document.createElement("option");
      option.value = String(address >>> 0);
      option.textContent = `0x${(address >>> 0).toString(16).padStart(8, "0")}`;
      cheatCandidates.append(option);
    }
    cheatApply.disabled = candidates.length === 0;
    cheatRefine.disabled = candidates.length === 0;
    cheatStatus.textContent = candidates.length > 300
      ? `후보 ${candidates.length}개 (앞 300개 표시)`
      : `후보 ${candidates.length}개`;
  };
  const runCheat = (fn: () => void) => {
    try { fn(); } catch (error) { cheatStatus.textContent = `오류: ${String(error)}`; }
  };

  cheatOpen.addEventListener("click", () => cheatDialog.showModal(), { signal: abortController.signal });
  cheatScan.addEventListener("click", () => runCheat(() => {
    cheatStatus.textContent = cheatFull.checked ? "전체 메모리 검색 중…" : "빠른 검색 중…";
    const value = parseValue(cheatCurrent);
    candidates = Array.from(wieWeb.cheat_scan_u32(value, cheatFull.checked) as Uint32Array, Number);
    renderCandidates();
  }), { signal: abortController.signal });
  cheatRefine.addEventListener("click", () => runCheat(() => {
    const value = parseValue(cheatCurrent);
    candidates = candidates.filter((address) => wieWeb.cheat_read_u32(address >>> 0) === value);
    renderCandidates();
  }), { signal: abortController.signal });
  cheatApply.addEventListener("click", () => runCheat(() => {
    if (!cheatCandidates.value) throw new Error("후보 주소를 선택하세요.");
    const address = Number(cheatCandidates.value) >>> 0;
    const value = parseValue(cheatNew);
    wieWeb.cheat_write_u32(address, value);
    cheatStatus.textContent = `적용 완료: 0x${address.toString(16)} → ${value}`;
  }), { signal: abortController.signal });
'''
s = replace_once(s, needle, cheat_ts, 'cheat UI behavior')
write(p,s)

p = Path('wie-web/src/html/index.html')
s = read(p)
s = s.replace('<title>wie - 피처폰 앱 에뮬레이터 (WIPI/J2ME)</title>', '<title>영웅서기 1 - 솔티아의 바람</title>')
s = s.replace('<div id="library-view" class="library-view">', '<div id="library-view" class="library-view" hidden>')
s = s.replace('<section id="player-view" class="player-view" hidden>', '<section id="player-view" class="player-view">')
s = s.replace('<button id="back-to-library" class="icon-button"', '<button id="back-to-library" class="icon-button" style="display:none"')
needle = '''        <button id="app-settings" class="icon-button" type="button" title="설정" aria-label="설정">\n          <i data-lucide="settings"></i>\n        </button>'''
replacement = '''        <button id="cheat-open" class="icon-button" type="button" title="CHEAT" aria-label="치트 메뉴" style="font-size:11px;font-weight:800;width:auto;padding:0 10px">CHEAT</button>\n''' + needle
s = replace_once(s, needle, replacement, 'cheat toolbar button')
cheat_dialog = r'''
    <dialog id="cheat-dialog" class="app-dialog">
      <form method="dialog" style="min-width:min(92vw,420px)">
        <header class="dialog-header">
          <h2>CHEAT</h2>
          <button class="icon-button dialog-close" value="cancel" aria-label="닫기">×</button>
        </header>
        <p style="margin-top:0">게임에 보이는 숫자를 검색한 뒤 값을 바꾸고 ‘좁히기’를 반복하세요.</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
          <label>현재 값<input id="cheat-current" type="number" inputmode="numeric" min="0" max="4294967295" value="0" style="width:100%;font-size:16px;padding:8px"></label>
          <label>바꿀 값<input id="cheat-new" type="number" inputmode="numeric" min="0" max="4294967295" value="9999999" style="width:100%;font-size:16px;padding:8px"></label>
        </div>
        <label style="display:flex;gap:8px;align-items:center;margin:12px 0"><input id="cheat-full" type="checkbox"> 전체 메모리 검색(느림)</label>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button id="cheat-scan" type="button" class="primary-command">새 검색</button>
          <button id="cheat-refine" type="button" class="secondary-command" disabled>현재 값으로 좁히기</button>
        </div>
        <label style="display:block;margin-top:12px">후보 주소
          <select id="cheat-candidates" size="6" style="width:100%;font-family:monospace;font-size:15px"></select>
        </label>
        <button id="cheat-apply" type="button" class="primary-command" disabled style="margin-top:10px;width:100%">선택 주소에 적용</button>
        <p id="cheat-status" role="status" aria-live="polite">후보 0개</p>
      </form>
    </dialog>
'''
marker = '    <dialog id="settings-dialog" class="app-dialog">'
s = replace_once(s, marker, cheat_dialog + '\n' + marker, 'cheat dialog')
s = re.sub(r'\s*<script\s+async\s+src="https://pagead2\.googlesyndication\.com/.*?</script>', '', s, flags=re.S)
s = re.sub(r'\s*<script async src="https://www\.googletagmanager\.com/.*?</script>\s*<script>.*?gtag\("config".*?</script>', '', s, flags=re.S)
write(p,s)

print('Hero1 standalone patches applied successfully')