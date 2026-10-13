/**
 * Smart Freight Interactive Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggle
  const menuToggle = document.getElementById('mobileMenuToggle');
  const sidebar = document.querySelector('.sidebar');
  if (menuToggle && sidebar) {
    menuToggle.addEventListener('click', () => {
      sidebar.classList.toggle('mobile-open');
    });
  }

  // Populate live badge from /health API
  const badgeText = document.getElementById('liveBadgeText');
  if (badgeText) {
    fetch('/health')
      .then(r => r.json())
      .then(data => {
        const meta = data.checks && data.checks.model_metadata_loaded;
        if (meta && meta.status === 'ok') {
          badgeText.textContent =
            `${meta.selected_model} — MAE ${meta.mae}d / RMSE ${meta.rmse}`;
        }
      })
      .catch(() => { /* keep default text on error */ });
  }

  // Auto-dismiss alerts
  setTimeout(() => {
    document.querySelectorAll('.alert-dismissible').forEach(el => {
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    });
  }, 4000);

  // Initialize tooltips / copy buttons if any
  document.querySelectorAll('.btn-copy').forEach(btn => {
    btn.addEventListener('click', () => {
      const text = btn.getAttribute('data-copy');
      if (text) {
        navigator.clipboard.writeText(text).then(() => {
          showToast('Copied to clipboard!', 'success');
        });
      }
    });
  });
});

/**
 * Toast Notification System
 */
function showToast(message, type = 'info') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
    `;
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  const bg = type === 'success' ? '#10b981' : type === 'error' ? '#f43f5e' : '#0ea5e9';
  toast.style.cssText = `
    background: #0f172a;
    border: 1px solid ${bg};
    border-left: 5px solid ${bg};
    color: #f8fafc;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 0.86rem;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    display: flex;
    align-items: center;
    gap: 10px;
    opacity: 0;
    transform: translateY(10px);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  `;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.opacity = '1';
    toast.style.transform = 'translateY(0)';
  });

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}
