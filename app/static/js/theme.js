/**
 * Theme Management & Chart Synchronization
 */
function setTheme(theme) {
    const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    const appliedTheme = isDark ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', appliedTheme);
    document.documentElement.setAttribute('data-bs-theme', appliedTheme);
    localStorage.setItem('theme', theme);
    
    updateThemeIcon(theme);
    window.dispatchEvent(new Event('themeChanged'));
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (!icon) return;
    icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : (theme === 'light' ? 'bi bi-sun-fill' : 'bi bi-circle-half');
}

window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (localStorage.getItem('theme') === 'system' || !localStorage.getItem('theme')) {
        setTheme('system');
    }
});

// Run immediately on load (inline script handles the pre-paint logic, this syncs the UI icon)
window.addEventListener('DOMContentLoaded', () => {
    setTheme(localStorage.getItem('theme') || 'system');
    
    // Bind the toggle button
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            setTheme(currentTheme === 'light' ? 'dark' : 'light');
        });
    }
});