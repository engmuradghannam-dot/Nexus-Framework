/* =====================================================
   Nexus-Framework Sidebar JavaScript
   Windows Style with Theme Toggle
   by @eng.Murad Alhassan
   ===================================================== */

(function() {
    'use strict';

    // DOM Elements
    const sidebar = document.getElementById('nexus-sidebar');
    const sidebarToggle = document.getElementById('nexus-sidebar-toggle');
    const menuBtn = document.getElementById('nexus-menu-btn');
    const overlay = document.getElementById('nexus-overlay');
    const startItems = document.querySelectorAll('.nexus-start-item');
    const themeBtn = document.getElementById('nexus-theme-btn');
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    const html = document.documentElement;

    // State
    let isCollapsed = localStorage.getItem('nexus-sidebar-collapsed') === 'true';
    let isMobile = window.innerWidth <= 1024;
    let currentTheme = localStorage.getItem('nexus-theme') || 'light';

    // Initialize
    function init() {
        // Apply theme
        applyTheme(currentTheme);

        // Apply sidebar state
        if (isCollapsed && !isMobile) {
            sidebar.classList.add('collapsed');
        }

        bindEvents();
        handleResponsive();
        initMobileFlyouts();
    }

    function bindEvents() {
        // Sidebar toggle
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleSidebar);
        }

        // Menu button (mobile)
        if (menuBtn) {
            menuBtn.addEventListener('click', openSidebar);
        }

        // Overlay
        if (overlay) {
            overlay.addEventListener('click', closeAll);
        }

        // Theme toggle
        if (themeBtn) {
            themeBtn.addEventListener('click', toggleTheme);
        }

        // Window resize
        window.addEventListener('resize', debounce(handleResponsive, 150));

        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                toggleSidebar();
            }
            if (e.key === 'Escape') {
                closeAll();
            }
        });

        // Close flyout when clicking outside
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.nexus-start-item')) {
                startItems.forEach(item => item.classList.remove('open'));
            }
        });
    }

    // Theme functions
    function applyTheme(theme) {
        currentTheme = theme;
        html.setAttribute('data-theme', theme);
        localStorage.setItem('nexus-theme', theme);

        if (themeIcon && themeText) {
            if (theme === 'dark') {
                themeIcon.textContent = '☀️';
                themeText.textContent = 'Light Mode';
            } else {
                themeIcon.textContent = '🌙';
                themeText.textContent = 'Dark Mode';
            }
        }
    }

    function toggleTheme() {
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        applyTheme(newTheme);
    }

    // Sidebar functions
    function toggleSidebar() {
        if (isMobile) return;

        isCollapsed = !isCollapsed;
        sidebar.classList.toggle('collapsed', isCollapsed);
        localStorage.setItem('nexus-sidebar-collapsed', isCollapsed);

        window.dispatchEvent(new CustomEvent('nexus-sidebar-toggle', {
            detail: { collapsed: isCollapsed }
        }));
    }

    function openSidebar() {
        if (!isMobile) return;
        sidebar.classList.add('open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    function closeAll() {
        closeSidebar();
        startItems.forEach(item => item.classList.remove('open'));
    }

    function handleResponsive() {
        const newIsMobile = window.innerWidth <= 1024;

        if (newIsMobile !== isMobile) {
            isMobile = newIsMobile;

            if (isMobile) {
                sidebar.classList.remove('collapsed');
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
            } else {
                closeAll();
                sidebar.classList.toggle('collapsed', isCollapsed);
            }
        }
    }

    // Mobile flyouts
    function initMobileFlyouts() {
        startItems.forEach(item => {
            const link = item.querySelector('.nexus-start-link');

            if (link) {
                link.addEventListener('click', function(e) {
                    if (isMobile) {
                        e.preventDefault();
                        startItems.forEach(other => {
                            if (other !== item) other.classList.remove('open');
                        });
                        item.classList.toggle('open');
                    }
                });
            }
        });
    }

    // Utility: Debounce
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose API
    window.NexusSidebar = {
        toggle: toggleSidebar,
        open: openSidebar,
        close: closeAll,
        toggleTheme: toggleTheme,
        setTheme: applyTheme,
        isCollapsed: () => isCollapsed,
        isMobile: () => isMobile,
        getTheme: () => currentTheme
    };

})();
