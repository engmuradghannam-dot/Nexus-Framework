/* =====================================================
   Nexus-Framework Sidebar JavaScript
   Windows-style Control Panel Sidebar
   by @eng.Murad Alhassan
   ===================================================== */

(function() {
    'use strict';

    // DOM Elements
    const sidebar = document.getElementById('nexus-sidebar');
    const sidebarToggle = document.getElementById('nexus-sidebar-toggle');
    const menuBtn = document.getElementById('nexus-menu-btn');
    const overlay = document.getElementById('nexus-overlay');
    const navItems = document.querySelectorAll('.nexus-nav-item');
    const mainContent = document.querySelector('.nexus-main');

    // State
    let isCollapsed = localStorage.getItem('nexus-sidebar-collapsed') === 'true';
    let isMobile = window.innerWidth <= 1024;

    // Initialize
    function init() {
        // Apply initial state
        if (isCollapsed && !isMobile) {
            sidebar.classList.add('collapsed');
        }

        // Bind events
        bindEvents();

        // Handle responsive
        handleResponsive();

        // Initialize submenus
        initSubmenus();
    }

    function bindEvents() {
        // Sidebar toggle (desktop)
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', toggleSidebar);
        }

        // Menu button (mobile)
        if (menuBtn) {
            menuBtn.addEventListener('click', openSidebar);
        }

        // Overlay click
        if (overlay) {
            overlay.addEventListener('click', closeSidebar);
        }

        // Window resize
        window.addEventListener('resize', debounce(handleResponsive, 150));

        // Keyboard shortcut
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + B to toggle sidebar
            if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
                e.preventDefault();
                toggleSidebar();
            }
            // Escape to close sidebar on mobile
            if (e.key === 'Escape' && isMobile) {
                closeSidebar();
            }
        });
    }

    function toggleSidebar() {
        if (isMobile) return;

        isCollapsed = !isCollapsed;
        sidebar.classList.toggle('collapsed', isCollapsed);
        localStorage.setItem('nexus-sidebar-collapsed', isCollapsed);

        // Trigger custom event
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

    function handleResponsive() {
        const newIsMobile = window.innerWidth <= 1024;

        if (newIsMobile !== isMobile) {
            isMobile = newIsMobile;

            if (isMobile) {
                // Switch to mobile mode
                sidebar.classList.remove('collapsed');
                sidebar.classList.remove('open');
                overlay.classList.remove('active');
            } else {
                // Switch to desktop mode
                closeSidebar();
                sidebar.classList.toggle('collapsed', isCollapsed);
            }
        }
    }

    function initSubmenus() {
        navItems.forEach(item => {
            const link = item.querySelector('.nexus-nav-link');
            const submenu = item.querySelector('.nexus-submenu');

            if (link && submenu) {
                link.addEventListener('click', function(e) {
                    // Only toggle if clicking the arrow or if collapsed
                    if (isCollapsed || e.target.closest('.nexus-nav-arrow')) {
                        e.preventDefault();
                        item.classList.toggle('open');

                        // Close other open submenus
                        navItems.forEach(otherItem => {
                            if (otherItem !== item && otherItem.classList.contains('open')) {
                                otherItem.classList.remove('open');
                            }
                        });
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

    // Utility: Smooth scroll for sidebar
    function smoothScrollTo(element, target, duration) {
        const start = element.scrollTop;
        const change = target - start;
        const startTime = performance.now();

        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);

            // Ease out cubic
            const ease = 1 - Math.pow(1 - progress, 3);
            element.scrollTop = start + change * ease;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }

        requestAnimationFrame(animate);
    }

    // Auto-scroll active item into view
    function scrollActiveIntoView() {
        const activeLink = sidebar.querySelector('.nexus-nav-link.active');
        if (activeLink) {
            const item = activeLink.closest('.nexus-nav-item');
            if (item) {
                const sidebarNav = sidebar.querySelector('.nexus-sidebar-nav');
                const itemTop = item.offsetTop;
                const navHeight = sidebarNav.clientHeight;
                const itemHeight = item.clientHeight;

                if (itemTop < sidebarNav.scrollTop || 
                    itemTop + itemHeight > sidebarNav.scrollTop + navHeight) {
                    smoothScrollTo(sidebarNav, itemTop - navHeight / 2 + itemHeight / 2, 300);
                }
            }
        }
    }

    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Scroll active item after page load
    window.addEventListener('load', scrollActiveIntoView);

    // Expose API
    window.NexusSidebar = {
        toggle: toggleSidebar,
        open: openSidebar,
        close: closeSidebar,
        isCollapsed: () => isCollapsed,
        isMobile: () => isMobile
    };

})();
