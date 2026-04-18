// ============================================================
//  Api.js — SmartClassroom API Layer
// ============================================================

export const API_BASE = 'https://smartclassroom-production.up.railway.app';

// ════════════════════════════════════════════════════════════
//  CORE FETCH WRAPPER
// ════════════════════════════════════════════════════════════
async function apiFetch(path, options = {})
{
  try
  {
    const res = await fetch(API_BASE + path, options);
    const data = await res.json();
    if (!res.ok)
    {
      throw new Error(data.detail || `HTTP ${res.status}`);
    }
    return data;
  } catch (err)
  {
    if (err.name === 'TypeError')
    {
      throw new Error('Cannot reach server. Make sure FastAPI is running at ' + API_BASE);
    }
    throw err;
  }
}

// ════════════════════════════════════════════════════════════
//  PING / HEALTH CHECK
// ════════════════════════════════════════════════════════════
export async function pingServer()
{
  const res = await fetch(API_BASE + '/', {
    signal: AbortSignal.timeout(15000)  // increased to 15s for Railway cold start
  });
  if (!res.ok) throw new Error('Server returned ' + res.status);
  return res.json();
}

// ════════════════════════════════════════════════════════════
//  GET ALL LECTURES
// ════════════════════════════════════════════════════════════
export async function getLectures()
{
  return apiFetch('/lectures/');
}

// ════════════════════════════════════════════════════════════
//  GET SINGLE LECTURE
// ════════════════════════════════════════════════════════════
export async function getLecture(id)
{
  return apiFetch(`/lectures/${id}`);
}

// ════════════════════════════════════════════════════════════
//  UPDATE LECTURE  (PATCH)
// ════════════════════════════════════════════════════════════
export async function updateLecture(id, data)
{
  return apiFetch(`/lectures/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
}

// ════════════════════════════════════════════════════════════
//  DELETE LECTURE
// ════════════════════════════════════════════════════════════
export async function deleteLecture(id)
{
  return apiFetch(`/lectures/${id}`, { method: 'DELETE' });
}

// ════════════════════════════════════════════════════════════
//  UPLOAD WAV FILE  →  POST /uploadfile/
//  Uses XHR for real upload progress %
// ════════════════════════════════════════════════════════════
export async function uploadWavFile(
  { file, title, subject, language = 'ta', initial_prompt = '' },
  onProgress
)
{
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('subject', subject);
  formData.append('language', language);
  formData.append('initial_prompt', initial_prompt);

  return new Promise((resolve, reject) =>
  {
    const xhr = new XMLHttpRequest();

    xhr.upload.onprogress = (e) =>
    {
      if (e.lengthComputable && onProgress)
      {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () =>
    {
      try
      {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300)
        {
          resolve(data);
        } else
        {
          reject(new Error(data.detail || `Server error ${xhr.status}`));
        }
      } catch
      {
        reject(new Error('Invalid JSON response from server'));
      }
    };

    xhr.onerror = () => reject(new Error('Network error — server unreachable'));
    xhr.ontimeout = () => reject(new Error('Request timed out (300s)'));

    xhr.open('POST', `${API_BASE}/uploadfile/`);
    xhr.timeout = 300000; // 5 minutes for Groq processing
    xhr.send(formData);
  });
}

// ════════════════════════════════════════════════════════════
//  DEBUG AUDIO  →  POST /debug_audio/
// ════════════════════════════════════════════════════════════
export async function debugAudio({
  file,
  sample_rate = 16000,
  channels = 1,
  bits_per_sample = 16,
  language = 'ta',
  initial_prompt = ''
})
{
  const formData = new FormData();
  formData.append('file', file);
  formData.append('sample_rate', sample_rate);
  formData.append('channels', channels);
  formData.append('bits_per_sample', bits_per_sample);
  formData.append('language', language);
  formData.append('initial_prompt', initial_prompt);

  return apiFetch('/debug_audio/', { method: 'POST', body: formData });
}

// ════════════════════════════════════════════════════════════
//  LANGUAGE MAP
// ════════════════════════════════════════════════════════════
export const LANGUAGES = {
  ta: 'Tamil', hi: 'Hindi', te: 'Telugu',
  kn: 'Kannada', ml: 'Malayalam', en: 'English'
};

export function getLangLabel(code)
{
  return LANGUAGES[code] || code;
}

// ════════════════════════════════════════════════════════════
//  DATE FORMATTERS
// ════════════════════════════════════════════════════════════
export function formatDate(dateStr)
{
  if (!dateStr) return '—';
  const d = new Date(dateStr.replace(' ', 'T'));
  return d.toLocaleDateString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric'
  });
}

export function formatDatetime(dateStr)
{
  if (!dateStr) return '—';
  const d = new Date(dateStr.replace(' ', 'T'));
  return d.toLocaleString('en-IN', {
    day: 'numeric', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

// ════════════════════════════════════════════════════════════
//  TRUNCATE TEXT
// ════════════════════════════════════════════════════════════
export function truncate(str, n = 120)
{
  if (!str) return '';
  return str.length > n ? str.slice(0, n) + '…' : str;
}

// ════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ════════════════════════════════════════════════════════════
export function showToast(message, type = 'info')
{
  let container = document.getElementById('toast-container');
  if (!container)
  {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✓', error: '✕', info: '◆' };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span class="toast-icon" style="font-size:0.9rem;flex-shrink:0">${icons[type] || '◆'}</span>
    <span>${message}</span>
  `;
  container.appendChild(toast);

  setTimeout(() =>
  {
    toast.classList.add('toast-out');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
  }, 3500);
}