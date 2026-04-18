// ═══════════════════════════════════════════════════════════
//  index.js — Dashboard page logic
// ═══════════════════════════════════════════════════════════
import { getLectures, pingServer, formatDate, truncate, showToast } from './Api.js';

async function init()
{
  await checkServer();
  await loadLectures();
}
  (function () {
    var btn   = document.getElementById('nav-hamburger');
    var links = document.getElementById('nav-links');
    if (!btn || !links) return;
    btn.addEventListener('click', function () {
      var open = links.classList.toggle('open');
      btn.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open);
    });
    links.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        links.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      });
    });
    document.addEventListener('click', function (e) {
      if (!btn.contains(e.target) && !links.contains(e.target)) {
        links.classList.remove('open');
        btn.classList.remove('open');
        btn.setAttribute('aria-expanded', 'false');
      }
    });
  })();
// ── Server ping ──────────────────────────────────────────
async function checkServer()
{
  try
  {
    await pingServer();
    document.getElementById('server-status').textContent = 'API online';
    document.getElementById('stat-api').textContent = '✓ Online';
    document.getElementById('stat-api').style.color = 'var(--green)';
  } catch
  {
    document.getElementById('server-status').textContent = 'offline';
    document.getElementById('stat-api').textContent = '✕ Offline';
    document.getElementById('stat-api').style.color = 'var(--red)';
    document.querySelector('.status-dot').style.background = 'var(--red)';
  }
}

// ── Load lectures & populate dashboard ──────────────────
async function loadLectures()
{
  try
  {
    const lectures = await getLectures();

    // Stats
    document.getElementById('stat-total').textContent = lectures.length;
    const subjects = new Set(lectures.map(l => l.subject));
    document.getElementById('stat-subjects').textContent = subjects.size;

    if (lectures.length > 0)
    {
      const latest = lectures[0];
      document.getElementById('stat-latest').textContent = truncate(latest.title, 18);
      document.getElementById('stat-latest-sub').textContent = formatDate(latest.created_at);
    } else
    {
      document.getElementById('stat-latest').textContent = '—';
    }

    renderRecentLectures(lectures.slice(0, 6));
  } catch (err)
  {
    document.getElementById('recent-list').innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h3>Could not load lectures</h3>
        <p>${err.message}</p>
      </div>`;
    showToast(err.message, 'error');
  }
}

// ── Render recent lecture cards ──────────────────────────
function renderRecentLectures(lectures)
{
  const container = document.getElementById('recent-list');

  if (lectures.length === 0)
  {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🎙️</div>
        <h3>No lectures yet</h3>
        <p>Press BOOT on your ESP32 to start recording, or upload a WAV file.</p>
      </div>`;
    return;
  }

  container.innerHTML = '';
  const wrap = document.createElement('div');
  wrap.className = 'stagger';
  wrap.style.cssText = 'display:flex;flex-direction:column;gap:10px';

  lectures.forEach(lecture =>
  {
    const card = document.createElement('div');
    card.className = 'lecture-card';
    card.innerHTML = `
      <div class="lecture-card-body">
        <div class="lecture-card-title">${lecture.title}</div>
        <div class="lecture-card-meta">
          <span class="badge badge-amber">${lecture.subject || '—'}</span>
          <span class="text-mono text-xs text-muted">${formatDate(lecture.created_at)}</span>
        </div>
        <div class="lecture-card-excerpt">${truncate(lecture.summary || lecture.transcript, 110)}</div>
      </div>
      <div class="lecture-card-actions">
        <span class="btn btn-ghost btn-sm">→</span>
      </div>`;

    // ✅ FIX: was 'lecture_detail.html' — corrected to match the actual filename
    card.addEventListener('click', () =>
    {
      window.location.href = `Lecturedetail.html?id=${lecture.id}`;
    });

    wrap.appendChild(card);
  });

  container.appendChild(wrap);
}

// Boot
init();