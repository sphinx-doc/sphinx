/**
 * Sphinx theme toggle - Manual dark/light mode switcher
 *
 * This script provides a toggle button to manually switch between light and dark modes,
 * overriding the system preference when desired.
 */

(function() {
    'use strict';

    // Check for saved theme preference or default to system preference
    function getThemePreference() {
        const saved = localStorage.getItem('sphinx-theme');
        if (saved) {
            return saved;
        }
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('sphinx-theme', theme);
    }

    // Create and insert toggle button
    function createToggleButton() {
        const button = document.createElement('button');
        button.id = 'theme-toggle';
        button.className = 'theme-toggle-button';
        button.setAttribute('aria-label', 'Toggle dark mode');
        button.title = 'Toggle dark/light mode';

        // Add button text/icon
        button.innerHTML = '<span class="theme-toggle-icon">🌙</span>';

        button.addEventListener('click', function() {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
            updateButtonIcon(next);
        });

        // Insert button into the page (try multiple locations)
        const insertLocations = [
            '.sphinxsidebar',
            '.related',
            'body'
        ];

        for (const selector of insertLocations) {
            const container = document.querySelector(selector);
            if (container) {
                if (selector === '.sphinxsidebar') {
                    // Insert at top of sidebar
                    container.insertBefore(button, container.firstChild);
                } else if (selector === '.related') {
                    // Insert into navigation
                    const nav = container.querySelector('ul');
                    if (nav) {
                        const li = document.createElement('li');
                        li.className = 'right';
                        li.appendChild(button);
                        nav.appendChild(li);
                    }
                } else {
                    // Fallback: fixed position button
                    button.style.position = 'fixed';
                    button.style.bottom = '20px';
                    button.style.right = '20px';
                    button.style.zIndex = '1000';
                    container.appendChild(button);
                }
                break;
            }
        }

        return button;
    }

    // Update button icon based on current theme
    function updateButtonIcon(theme) {
        const button = document.getElementById('theme-toggle');
        if (button) {
            const icon = button.querySelector('.theme-toggle-icon');
            if (icon) {
                icon.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
        }
    }

    // Initialize on page load
    function init() {
        const theme = getThemePreference();
        applyTheme(theme);

        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                createToggleButton();
                updateButtonIcon(theme);
            });
        } else {
            createToggleButton();
            updateButtonIcon(theme);
        }

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                // Only apply if user hasn't set a manual preference
                if (!localStorage.getItem('sphinx-theme')) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    applyTheme(newTheme);
                    updateButtonIcon(newTheme);
                }
            });
        }
    }

    init();
})();
