document.addEventListener('DOMContentLoaded', () => {
    // 1. Subtle Animations (Stagger fade in)
    const fadeItems = document.querySelectorAll('.fade-in');
    fadeItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 50}ms`;
    });

    // 2. CountUp Animation for Money
    const counters = document.querySelectorAll('[data-countup]');
    counters.forEach(counter => {
        const target = parseFloat(counter.getAttribute('data-countup'));
        if(isNaN(target)) return;
        const duration = 600; 
        const frames = 30;
        const step = target / frames;
        let current = 0;
        
        const timer = setInterval(() => {
            current += step;
            if (current >= target) {
                counter.innerText = target.toFixed(2);
                clearInterval(timer);
            } else {
                counter.innerText = current.toFixed(2);
            }
        }, duration / frames);
    });

    // 3. Avatar Color Generator
    const avatars = document.querySelectorAll('.user-avatar');
    const colors = ['var(--avatar-1)', 'var(--avatar-2)', 'var(--avatar-3)', 'var(--avatar-4)', 'var(--avatar-5)'];
    avatars.forEach(avatar => {
        const name = avatar.getAttribute('data-name') || 'U';
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = name.charCodeAt(i) + ((hash << 5) - hash);
        }
        const index = Math.abs(hash) % colors.length;
        avatar.style.backgroundColor = colors[index];
    });

    // 4. Notifications Fetch & Live Polling
    const notifBadge = document.getElementById('notifBadge');
    
    
    
    window.markNotifsRead = function() {
        localStorage.setItem('notifReadTimestamp', Date.now());
        const badge = document.getElementById('notifBadge');
        if (badge) badge.classList.add('d-none');
        fetchNotifications();
    };
    
    function fetchNotifications() {
        if(!notifBadge) return;
        
        fetch('/api/notifications')
            .then(res => res.json())
            .then(data => {
                if(data.notifications && data.notifications.length > 0) {
                    const readTs = parseInt(localStorage.getItem('notifReadTimestamp')) || 0;
                    const unread = data.notifications.filter(n => {
                        let dObj = new Date(n.timestamp.replace(' ', 'T'));
                        return !isNaN(dObj) && dObj.getTime() > readTs;
                    });
                    
                    if (unread.length > 0) {
                        notifBadge.classList.remove('d-none');
                    } else {
                        notifBadge.classList.add('d-none');
                    }
                    
                    const menu = document.getElementById('notifMenu');
                    menu.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center p-3 border-bottom border-subtle">
                            <span class="fw-bold">Notifications</span>
                            <button class="btn btn-sm btn-ghost text-primary py-0" onclick="markNotifsRead()">Mark all as read</button>
                        </div>
                    `; 
                    
                    data.notifications.forEach(n => {
                        let dObj = new Date(n.timestamp.replace(' ', 'T'));
                        let d = isNaN(dObj) ? "" : dObj.toLocaleDateString('en-US', {month: 'short', day: 'numeric', hour: '2-digit', minute:'2-digit'});
                        const isUnread = !isNaN(dObj) && dObj.getTime() > readTs;
                        
                        let icon = 'bi-bell-fill text-warning';
                        if (n.type === 'payment') icon = 'bi-cash-coin text-positive';
                        if (n.type === 'expense') icon = 'bi-receipt text-primary';
                        
                        menu.innerHTML += `
                            <li class="border-bottom border-subtle" style="background-color: ${isUnread ? 'var(--surface-2)' : 'transparent'};">
                                <div class="dropdown-item p-3 text-wrap" style="white-space: normal;">
                                    <div class="d-flex align-items-center mb-1">
                                        <i class="bi ${icon} me-2"></i>
                                        <strong class="small">${n.actor}</strong>
                                        ${isUnread ? '<span class="badge bg-danger ms-auto rounded-pill" style="font-size: 0.6rem;">NEW</span>' : ''}
                                    </div>
                                    <p class="mb-1 small text-muted">${n.action} <b>${n.group_name}</b></p>
                                    <small class="text-muted" style="font-size: 0.7rem;">${d}</small>
                                </div>
                            </li>
                        `;
                    });

                    const latest = data.notifications[0];
                    const latestKey = latest.type + '_' + latest.id;
                    const prevKey = sessionStorage.getItem('latestNotifKey');
                    
                    if (prevKey && latestKey !== prevKey) {
                        // A brand new notification arrived!
                        let msg = `${latest.actor} ${latest.action} ${latest.group_name}`;
                        if (latest.type === 'reminder') msg = `${latest.actor} sent you a reminder for ${latest.group_name}!`;
                        
                        if (window.triggerToast) window.triggerToast(msg, false, 60000); 
                        
                        // Safe Auto-Sync (Reload balances)
                        const modalOpen = document.querySelector('.modal.show');
                        if (!modalOpen) {
                            setTimeout(() => {
                                const url = new URL(window.location.href);
                                url.searchParams.set('_sync', Date.now());
                                window.location.replace(url.toString());
                            }, 2500);
                        }
                    }
                    // Only set it AFTER the check, so on initial page load it just sets the state without triggering reload.
                    sessionStorage.setItem('latestNotifKey', latestKey);
                }
                
                
            })
            .catch(err => console.log('Notification fetch error:', err));
    }

    fetchNotifications();
    setInterval(fetchNotifications, 10000);

    // 5. Toast & Sound Notification System
    window.triggerToast = function(text, isError, duration=3500) {
        const soundUrl = isError ? 
            'https://assets.mixkit.co/active_storage/sfx/2955/2955-preview.mp3' : 
            'https://assets.mixkit.co/active_storage/sfx/1114/1114-preview.mp3'; 
        const audio = new Audio(soundUrl);
        audio.volume = 0.5;
        audio.play().catch(e => console.log('Audio autoplay blocked', e));

        const tc = document.createElement('div');
        tc.style.position = 'fixed';
        tc.style.bottom = '20px';
        tc.style.right = '20px';
        tc.style.zIndex = '9999';
        tc.style.transition = 'all 0.3s ease';
        
        const t = document.createElement('div');
        t.className = `alert ${isError ? 'alert-danger' : 'alert-success'} shadow-lg d-flex align-items-center justify-content-between m-0`;
        t.style.borderRadius = '12px';
        t.style.minWidth = '300px';
        t.style.animation = 'slideInUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards';
        
        t.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="bi ${isError ? 'bi-exclamation-octagon-fill' : 'bi-check-circle-fill'} fs-4 me-3"></i>
                <div class="fw-bold">${text}</div>
            </div>
            <button type="button" class="btn-close ms-3" aria-label="Close"></button>
        `;
        
        t.querySelector('.btn-close').addEventListener('click', () => {
            t.style.animation = 'fadeOutDown 0.3s ease forwards';
            setTimeout(() => tc.remove(), 300);
        });
        
        tc.appendChild(t);
        document.body.appendChild(tc);
        
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.innerHTML = `@keyframes slideInUp { from { transform: translateY(150%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
                               @keyframes fadeOutDown { from { transform: translateY(0); opacity: 1; } to { transform: translateY(150%); opacity: 0; } }`;
            document.head.appendChild(style);
        }

        if(duration > 0) {
            setTimeout(() => {
                if(tc.parentNode) {
                    t.style.animation = 'fadeOutDown 0.3s ease forwards';
                    setTimeout(() => { if(tc.parentNode) tc.remove(); }, 300);
                }
            }, duration);
        }
    };

    if (window.flashMessage || window.flashError) {
        const isError = window.flashError && window.flashError.length > 0;
        const text = window.flashMessage || window.flashError;
        triggerToast(text, isError, 3500); 
    }

});


// Helper for Pay Modal
function setPaymentData(userId, userName, amount) {
    const payUserId = document.getElementById('pay_user_id');
    const payUserName = document.getElementById('pay_user_name');
    const payAmount = document.getElementById('pay_amount');
    if(payUserId) payUserId.value = userId;
    if(payUserName) payUserName.innerText = userName;
    if(payAmount) payAmount.value = parseFloat(amount).toFixed(2);
}


    // Prevent double submissions on all forms
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if(btn) {
                btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
                btn.disabled = true;
                // Allow form to submit natively
            }
        });
    });
