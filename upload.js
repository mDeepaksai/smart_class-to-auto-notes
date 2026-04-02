// ============================================================
//  js/upload.js
// ============================================================

// ✅ ALL imports must be at top — no code before them
// Change this
import { uploadWavFile, debugAudio, pingServer, showToast, API_BASE } from './api.js';

// No change needed — if both files are in root, ./api.js is correct ✅

// ════════════════════════════════════════════════════════════
//  SERVER PING
// ════════════════════════════════════════════════════════════
pingServer()
  .then(() => {
    document.getElementById('server-status').textContent = 'API online';
    const dot = document.getElementById('status-dot');
    if (dot) dot.style.background = 'var(--green)';
  })
  .catch(() => {
    document.getElementById('server-status').textContent = 'offline';
    const dot = document.getElementById('status-dot');
    if (dot) dot.style.background = 'var(--red)';
  });

// Show API URL in footer
const footerUrl = document.getElementById('footer-url');
if (footerUrl) footerUrl.textContent = API_BASE;

// ════════════════════════════════════════════════════════════
//  TABS
// ════════════════════════════════════════════════════════════
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const isUpload = btn.dataset.tab === 'upload';
    document.getElementById('tab-upload').classList.toggle('hidden', !isUpload);
    document.getElementById('tab-debug').classList.toggle('hidden',  isUpload);
  });
});

// ════════════════════════════════════════════════════════════
//  STAGE HELPER
// ════════════════════════════════════════════════════════════
function setStage(id, state, sub = '') {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `stage-item${state ? ' ' + state : ''}`;
  const subEl = document.getElementById(id + '-sub');
  if (subEl && sub) subEl.textContent = sub;
}

function resetStages() {
  ['stage-file', 'stage-upload', 'stage-whisper', 'stage-nlp', 'stage-save']
    .forEach(id => setStage(id, '', 'Waiting…'));
}

// ════════════════════════════════════════════════════════════
//  FILE SELECT
// ════════════════════════════════════════════════════════════
let selectedFile = null;

const fileInput = document.getElementById('file-input');
const dropZone  = document.getElementById('drop-zone');

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFileSelect(fileInput.files[0]);
});

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (!f) return;
  if (!f.name.toLowerCase().endsWith('.wav')) {
    showToast('Only .wav files are accepted', 'error');
    return;
  }
  handleFileSelect(f);
});

function handleFileSelect(f) {
  selectedFile = f;
  const sizeKB = (f.size / 1024).toFixed(1);
  const sizeMB = (f.size / 1024 / 1024).toFixed(2);

  document.getElementById('file-name-badge').textContent =
    `${f.name} · ${f.size < 1024*1024 ? sizeKB + ' KB' : sizeMB + ' MB'}`;
  document.getElementById('file-chosen').style.display = 'block';

  dropZone.classList.add('has-file');
  dropZone.querySelector('h3').textContent = f.name;
  dropZone.querySelector('p').textContent  = `${sizeKB} KB · ready to upload`;

  document.getElementById('btn-upload').disabled = false;
  setStage('stage-file', 'done', f.name);
}

// ════════════════════════════════════════════════════════════
//  UPLOAD BUTTON
// ════════════════════════════════════════════════════════════
document.getElementById('btn-upload').addEventListener('click', async () => {
  const title   = document.getElementById('up-title').value.trim();
  const subject = document.getElementById('up-subject').value.trim();
  const lang    = document.getElementById('up-language').value;
  const prompt  = document.getElementById('up-prompt').value.trim();

  if (!selectedFile) { showToast('Please select a WAV file', 'error'); return; }
  if (!title)        { showToast('Please enter a title', 'error');      return; }
  if (!subject)      { showToast('Please enter a subject', 'error');    return; }

  const btn = document.getElementById('btn-upload');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner"></div> Uploading…';

  setStage('stage-upload', 'active', 'Sending to server…');
  document.getElementById('progress-wrap').classList.remove('hidden');
  document.getElementById('result-card').classList.add('hidden');
  document.getElementById('progress-bar').style.width = '0%';

  try {
    const result = await uploadWavFile(
      { file: selectedFile, title, subject, language: lang, initial_prompt: prompt },
      (pct) => {
        document.getElementById('progress-pct').textContent = pct + '%';
        document.getElementById('progress-bar').style.width  = pct + '%';
        if (pct >= 100) {
          document.getElementById('progress-label').textContent = 'Processing…';
          setStage('stage-upload',  'done',   'Uploaded ✓');
          setStage('stage-whisper', 'active', 'Transcribing… (may take 1–2 min)');
          setStage('stage-nlp',     'active', 'Waiting for NLP pipeline…');
        }
      }
    );

    setStage('stage-whisper', 'done', 'Transcribed ✓');
    setStage('stage-nlp',     'done', 'Summarized ✓');
    setStage('stage-save',    'done', `Saved · ID #${result.id}`);

    document.getElementById('result-card').classList.remove('hidden');
    document.getElementById('result-info').innerHTML = `
      <div>
        <span class="text-mono text-xs text-muted" style="margin-right:8px">ID</span>
        <strong>#${result.id}</strong>
      </div>
      <div>
        <span class="text-mono text-xs text-muted" style="margin-right:8px">Title</span>
        ${escHtml(result.title)}
      </div>
      <div>
        <span class="text-mono text-xs text-muted" style="margin-right:8px">Subject</span>
        ${escHtml(result.subject)}
      </div>
      <div style="margin-top:8px;padding:10px 12px;background:var(--bg-3);
                  border-radius:8px;font-size:0.82rem;color:var(--text-2);
                  line-height:1.7;border:1px solid var(--border)">
        ${escHtml((result.summary || '').slice(0, 220))}…
      </div>
    `;
    document.getElementById('result-view').href = `lecture_detail.html?id=${result.id}`;
    showToast('Lecture saved successfully!', 'success');

  } catch (err) {
    setStage('stage-upload', 'error', err.message);
    showToast('Upload failed: ' + err.message, 'error');

  } finally {
    btn.disabled = false;
    btn.innerHTML = '↑ Upload &amp; Transcribe';
    document.getElementById('progress-wrap').classList.add('hidden');
  }
});

// ════════════════════════════════════════════════════════════
//  UPLOAD ANOTHER
// ════════════════════════════════════════════════════════════
document.getElementById('result-another').addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';

  document.getElementById('file-chosen').style.display = 'none';
  document.getElementById('btn-upload').disabled       = true;
  document.getElementById('result-card').classList.add('hidden');

  dropZone.classList.remove('has-file');
  dropZone.querySelector('h3').textContent = 'Drop WAV file here';
  dropZone.querySelector('p').textContent  = 'or click to browse · .wav files only';

  document.getElementById('up-title').value   = '';
  document.getElementById('up-subject').value = '';
  document.getElementById('up-prompt').value  = '';
  document.getElementById('progress-label').textContent = 'Uploading…';
  document.getElementById('progress-pct').textContent   = '0%';
  document.getElementById('progress-bar').style.width   = '0%';

  resetStages();
});

// ════════════════════════════════════════════════════════════
//  DEBUG TAB
// ════════════════════════════════════════════════════════════
let debugFile = null;

document.getElementById('debug-file-input').addEventListener('change', (e) => {
  debugFile = e.target.files[0];
  if (debugFile) {
    document.getElementById('debug-file-badge').textContent = debugFile.name;
    document.getElementById('debug-file-chosen').style.display = 'block';
    document.getElementById('btn-debug').disabled = false;
  }
});

document.getElementById('btn-debug').addEventListener('click', async () => {
  if (!debugFile) return;

  const btn  = document.getElementById('btn-debug');
  const body = document.getElementById('debug-result-body');

  btn.disabled  = true;
  btn.innerHTML = '<div class="spinner"></div> Analysing…';
  body.innerHTML = `<div class="loading-overlay"><div class="spinner"></div> Running Whisper…</div>`;

  try {
    const r = await debugAudio({
      file:            debugFile,
      sample_rate:     parseInt(document.getElementById('debug-samplerate').value) || 16000,
      channels:        parseInt(document.getElementById('debug-channels').value)   || 1,
      bits_per_sample: parseInt(document.getElementById('debug-bits').value)       || 16,
      language:        document.getElementById('debug-language').value,
      initial_prompt:  document.getElementById('debug-prompt').value.trim(),
    });

    const qClass = r.audio_quality.includes('GOOD') ? 'badge-green'
                 : r.audio_quality.includes('LOW')  ? 'badge-amber'
                 : 'badge-gray';

    body.innerHTML = `
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:1rem">
        <div class="stat-card" style="padding:0.75rem">
          <div class="stat-label">Duration</div>
          <div class="stat-value" style="font-size:1.4rem">${r.duration_s}s</div>
        </div>
        <div class="stat-card" style="padding:0.75rem">
          <div class="stat-label">Max Amplitude</div>
          <div class="stat-value" style="font-size:1.4rem">${Number(r.max_amplitude).toLocaleString()}</div>
        </div>
        <div class="stat-card" style="padding:0.75rem">
          <div class="stat-label">Avg Amplitude</div>
          <div class="stat-value" style="font-size:1.4rem">${Number(r.avg_amplitude).toLocaleString()}</div>
        </div>
        <div class="stat-card" style="padding:0.75rem">
          <div class="stat-label">Quality</div>
          <div style="margin-top:6px"><span class="badge ${qClass}">${escHtml(r.audio_quality)}</span></div>
        </div>
      </div>
      <div class="text-block-label">Whisper Transcript</div>
      <div class="text-block" style="max-height:200px">${escHtml(r.transcript || 'No speech detected')}</div>
      ${r.hint ? `<p class="text-xs text-muted mt-1" style="line-height:1.6">💡 ${escHtml(r.hint)}</p>` : ''}
      ${r.prompt_used ? `<p class="text-xs text-muted mt-1">Prompt: <em>${escHtml(r.prompt_used)}</em></p>` : ''}
    `;
    showToast('Analysis complete', 'success');

  } catch (err) {
    body.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>${escHtml(err.message)}</p></div>`;
    showToast('Analysis failed: ' + err.message, 'error');

  } finally {
    btn.disabled    = false;
    btn.textContent = '🔍 Analyse Audio';
  }
});

// ════════════════════════════════════════════════════════════
//  UTILITY
// ════════════════════════════════════════════════════════════
function escHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}