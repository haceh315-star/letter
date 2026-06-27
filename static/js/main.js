// Auto-dismiss flash messages after 4s
document.addEventListener('DOMContentLoaded', () => {
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity .4s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 400);
    }, 4000);
  });

  // Poll unread count every 30s and update badge
  function updateBadge() {
    fetch('/api/unread')
      .then(r => r.json())
      .then(data => {
        const links = document.querySelectorAll('.nav-link');
        links.forEach(link => {
          if (link.href.includes('/inbox')) {
            let badge = link.querySelector('.badge');
            if (data.unread > 0) {
              if (!badge) {
                badge = document.createElement('span');
                badge.className = 'badge';
                link.appendChild(badge);
              }
              badge.textContent = data.unread;
            } else if (badge) {
              badge.remove();
            }
          }
        });
      })
      .catch(() => {});
  }

  // Only poll when logged in
  if (document.querySelector('.nav-logo')) {
    setInterval(updateBadge, 30000);
  }
});
