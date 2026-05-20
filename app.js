/**
 * CFTasks - Codeforces Integration
 * Отслеживание решённых задач
 */

(function() {
    'use strict';

    // Константы
    const HANDLE_KEY = 'cftasks_handle';
    const SOLVED_KEY = 'cftasks_solved';

    // Состояние
    let currentHandle = null;

    console.log('=== CFTasks Init ===');
    console.log('URL:', window.location.href);
    console.log('Origin:', window.location.origin);

    /**
     * Загружает решённые задачи пользователя
     */
    async function loadSolvedTasks(handle) {
        console.log('📡 Loading tasks for:', handle);
        try {
            const res = await fetch(
                `https://codeforces.com/api/user.status?handle=${encodeURIComponent(handle)}&from=1&count=10000`
            );
            const data = await res.json();

            if (data.status !== 'OK') {
                throw new Error(data.comment || 'API error');
            }

            const solved = new Set();
            for (const sub of data.result) {
                if (sub.verdict === 'OK') {
                    const p = sub.problem;
                    const url1 = `https://codeforces.com/problemset/problem/${p.contestId}/${p.index}`;
                    const url2 = `https://codeforces.com/contest/${p.contestId}/problem/${p.index}`;
                    solved.add(url1);
                    solved.add(url2);
                }
            }

            // Сохраняем и в sessionStorage и в localStorage для надёжности
            const solvedArray = [...solved];
            localStorage.setItem(SOLVED_KEY + '_' + handle, JSON.stringify(solvedArray));

            console.log('✅ Loaded', solved.size, 'solved tasks');
            return solved;
        } catch (e) {
            console.error('❌ Failed to load:', e);
            alert('Не удалось загрузить задачи. Проверьте handle.');
            return null;
        }
    }

    function markSolvedOnIndex(solved) {
        document.querySelectorAll('.theme-card').forEach(card => {
            const urlsData = card.dataset.urls;
            if (!urlsData) return;

            try {
                const urls = JSON.parse(urlsData);
                const solvedCount = urls.filter(u => solved.has(u)).length;
                const total = urls.length;

                if (solvedCount === 0 || total === 0) return;

                let badge = card.querySelector('.card-solved-badge');
                if (!badge) {
                    badge = document.createElement('div');
                    badge.className = 'card-solved-badge';
                    card.querySelector('.theme-card-body').appendChild(badge);
                }
                badge.textContent = `✓ ${solvedCount} / ${total}`;

                if (solvedCount === total) {
                    card.classList.add('theme-card--all-solved');
                } else {
                    card.classList.add('theme-card--partial');
                }
            } catch (e) {
                console.error('Failed to parse URLs:', e);
            }
        });
    }

    function markSolvedOnThemePage(solved) {
        console.log('🎯 Marking solved on theme page, count:', solved.size);

        let markedCount = 0;
        document.querySelectorAll('tr[data-url]').forEach(row => {
            const url = row.dataset.url;
            if (solved.has(url)) {
                markedCount++;
                row.classList.add('task-solved');
                const nameCell = row.querySelector('.task-name a');
                if (nameCell) {
                    let mark = nameCell.querySelector('.solved-mark');
                    if (!mark) {
                        mark = document.createElement('span');
                        mark.className = 'solved-mark';
                        mark.textContent = '✓ ';
                        nameCell.prepend(mark);
                    }
                }
            }
        });
        console.log('✅ Marked', markedCount, 'tasks as solved');

        document.querySelectorAll('.subtag-section').forEach(section => {
            const rows = section.querySelectorAll('tr[data-url]');
            const total = rows.length;
            const solvedCount = [...rows].filter(r => solved.has(r.dataset.url)).length;

            if (solvedCount === 0) return;

            const header = section.querySelector('.subtag-header');
            let badge = header.querySelector('.subtag-solved-badge');
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'subtag-solved-badge';
                header.appendChild(badge);
            }
            badge.textContent = `✓ ${solvedCount}/${total}`;
            if (solvedCount === total) {
                badge.classList.add('subtag-solved-badge--all');
            }
        });
    }

    function markSolved(solved) {
        const isIndex = document.querySelector('.themes-grid') !== null;
        const isThemePage = document.querySelector('.subtag-section') !== null;

        console.log('📍 Page type:', isIndex ? 'index' : isThemePage ? 'theme' : 'unknown');

        if (isIndex) {
            markSolvedOnIndex(solved);
        } else if (isThemePage) {
            markSolvedOnThemePage(solved);
        }
    }

    function clearSolvedMarks() {
        document.querySelectorAll('.theme-card').forEach(card => {
            card.classList.remove('theme-card--all-solved', 'theme-card--partial');
            const badge = card.querySelector('.card-solved-badge');
            if (badge) badge.remove();
        });

        document.querySelectorAll('.task-solved').forEach(r => r.classList.remove('task-solved'));
        document.querySelectorAll('.solved-mark').forEach(m => m.remove());
        document.querySelectorAll('.subtag-solved-badge').forEach(b => b.remove());
    }

    function updateUI(hasHandle) {
        const submitBtn = document.getElementById('handleSubmit');
        const clearBtn = document.getElementById('handleClear');
        const input = document.getElementById('handleInput');

        if (!submitBtn || !clearBtn || !input) {
            console.error('❌ Widget elements not found!');
            return;
        }

        if (hasHandle) {
            submitBtn.style.display = 'none';
            clearBtn.style.display = 'flex';
            input.readOnly = true;
        } else {
            submitBtn.style.display = 'flex';
            clearBtn.style.display = 'none';
            input.readOnly = false;
        }
    }

    async function setHandle(handle) {
        console.log('💾 setHandle:', handle);

        if (!handle || handle.trim() === '') {
            clearHandle();
            return;
        }

        handle = handle.trim();
        currentHandle = handle;
        localStorage.setItem(HANDLE_KEY, handle);
        console.log('✅ Saved handle to localStorage');

        updateUI(true);

        const solved = await loadSolvedTasks(handle);

        if (solved) {
            solvedTasks = solved;
            markSolved(solved);
        }
    }

    function clearHandle() {
        console.log('🗑️ clearHandle');
        currentHandle = null;
        solvedTasks.clear();
        localStorage.removeItem(HANDLE_KEY);
        sessionStorage.removeItem(SOLVED_KEY);
        clearSolvedMarks();
        updateUI(false);

        const input = document.getElementById('handleInput');
        if (input) input.value = '';
    }

    async function loadSavedHandle() {
        const savedHandle = localStorage.getItem(HANDLE_KEY);
        console.log('🔍 Checking localStorage for handle:', savedHandle);

        if (!savedHandle) return false;

        currentHandle = savedHandle;
        const input = document.getElementById('handleInput');
        if (input) input.value = savedHandle;

        updateUI(true);

        // Пробуем загрузить из sessionStorage
        let solved = null;
        const cached = sessionStorage.getItem(SOLVED_KEY);

        if (cached) {
            console.log('📦 Loading from sessionStorage');
            solved = new Set(JSON.parse(cached));
        } else {
            // Пробуем из localStorage
            const localCached = localStorage.getItem(SOLVED_KEY + '_' + savedHandle);
            if (localCached) {
                console.log('📦 Loading from localStorage cache');
                solved = new Set(JSON.parse(localCached));
                sessionStorage.setItem(SOLVED_KEY, localCached);
            } else {
                console.log('🌐 Loading from API');
                solved = await loadSolvedTasks(savedHandle);
            }
        }

        if (solved) {
            solvedTasks = solved;
            markSolved(solved);
        }

        return true;
    }

    function setupEventListeners() {
        const submitBtn = document.getElementById('handleSubmit');
        const clearBtn = document.getElementById('handleClear');
        const input = document.getElementById('handleInput');

        console.log('🎧 Setting up event listeners');
        console.log('Elements:', {
            submitBtn: !!submitBtn,
            clearBtn: !!clearBtn,
            input: !!input
        });

        if (submitBtn) {
            submitBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🖱️ Submit clicked');
                const handleInput = document.getElementById('handleInput');
                if (handleInput) {
                    setHandle(handleInput.value);
                }
            });
        }

        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    console.log('⌨️ Enter pressed');
                    setHandle(input.value);
                }
            });
        }

        if (clearBtn) {
            clearBtn.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('🖱️ Clear clicked');
                clearHandle();
            });
        }
    }

    async function init() {
        console.log('🚀 CFTasks initializing...');
        console.log('📍 URL:', window.location.href);

        setupEventListeners();
        await loadSavedHandle();

        console.log('✅ CFTasks initialized');
    }

    // Запускаем
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();