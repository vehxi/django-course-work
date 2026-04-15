document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle?.querySelector('.theme-toggle__icon');
    const themeText = themeToggle?.querySelector('.theme-toggle__text');
    const storedTheme = localStorage.getItem('theme');
    const preferredTheme = storedTheme || (window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');

    const applyTheme = (theme) => {
        document.documentElement.dataset.theme = theme;

        if (!themeToggle || !themeIcon || !themeText) {
            return;
        }

        const isLight = theme === 'light';
        themeToggle.setAttribute('aria-pressed', String(isLight));
        themeIcon.textContent = isLight ? '🌙' : '☀️';
        themeText.textContent = isLight ? 'Темная тема' : 'Светлая тема';
    };

    applyTheme(preferredTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const nextTheme = document.documentElement.dataset.theme === 'light' ? 'dark' : 'light';
            applyTheme(nextTheme);
            localStorage.setItem('theme', nextTheme);
        });
    }

    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const searchResultsRegion = document.getElementById('search-results-region');
    const resetSearchBtn = document.getElementById('reset-search-btn');

    if (searchForm && searchInput && searchResultsRegion) {
        const searchUrl = searchInput.dataset.url || searchForm.action || window.location.pathname;
        let searchDebounceId = null;
        let searchController = null;

        const updateResetButton = (value) => {
            if (!resetSearchBtn) {
                return;
            }

            resetSearchBtn.classList.toggle('hidden', !value.trim());
        };

        const buildSearchUrl = (query) => {
            const url = new URL(searchUrl, window.location.origin);

            if (query) {
                url.searchParams.set('q', query);
            }

            return url;
        };

        const renderSearchResults = async (query, { pushState = true } = {}) => {
            if (searchController) {
                searchController.abort();
            }

            searchController = new AbortController();

            const normalizedQuery = query.trim();
            const requestUrl = buildSearchUrl(normalizedQuery);

            updateResetButton(normalizedQuery);

            try {
                const response = await fetch(requestUrl, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    signal: searchController.signal,
                });

                if (!response.ok) {
                    throw new Error(`Search request failed: ${response.status}`);
                }

                const html = await response.text();
                searchResultsRegion.innerHTML = html;

                if (pushState) {
                    window.history.replaceState({}, '', `${requestUrl.pathname}${requestUrl.search}`);
                }
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error(error);
                }
            }
        };

        searchInput.addEventListener('input', () => {
            window.clearTimeout(searchDebounceId);
            searchDebounceId = window.setTimeout(() => {
                renderSearchResults(searchInput.value);
            }, 260);
        });

        searchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            window.clearTimeout(searchDebounceId);
            renderSearchResults(searchInput.value);
        });

        if (resetSearchBtn) {
            resetSearchBtn.addEventListener('click', (event) => {
                event.preventDefault();
                window.clearTimeout(searchDebounceId);
                searchInput.value = '';
                renderSearchResults('', { pushState: true });
                searchInput.focus();
            });
        }
    }

    const catalogSearchForm = document.getElementById('catalog-search-form');
    const catalogSearchInput = document.getElementById('catalog-search-input');
    const catalogResultsRegion = document.getElementById('catalog-results-region');
    const catalogViewInput = document.getElementById('catalog-view-input');
    const catalogResetSearch = document.getElementById('catalog-reset-search');
    const catalogViewOptions = document.querySelectorAll('[data-catalog-view]');

    if (catalogSearchForm && catalogSearchInput && catalogResultsRegion && catalogViewInput) {
        const catalogUrl = catalogSearchInput.dataset.url || catalogSearchForm.action || window.location.pathname;
        let catalogDebounceId = null;
        let catalogController = null;

        const buildCatalogUrl = (query, viewMode = catalogViewInput.value || 'list') => {
            const url = new URL(catalogUrl, window.location.origin);
            const normalizedQuery = query.trim();

            if (normalizedQuery) {
                url.searchParams.set('q', normalizedQuery);
            }

            url.searchParams.set('view', viewMode);
            return url;
        };

        const updateCatalogControls = (query, viewMode) => {
            const hasQuery = query.trim().length > 0;
            catalogResetSearch?.classList.toggle('hidden', !hasQuery);

            if (catalogResetSearch) {
                catalogResetSearch.href = `${new URL(catalogUrl, window.location.origin).pathname}?view=${encodeURIComponent(viewMode)}`;
            }

            catalogViewOptions.forEach((option) => {
                const optionView = option.dataset.catalogView;
                option.classList.toggle('active', optionView === viewMode);
                option.href = `${new URL(catalogUrl, window.location.origin).pathname}?${hasQuery ? `q=${encodeURIComponent(query.trim())}&` : ''}view=${encodeURIComponent(optionView)}`;
            });
        };

        const renderCatalogResults = async (query, viewMode = catalogViewInput.value || 'list', { pushState = true } = {}) => {
            if (catalogController) {
                catalogController.abort();
            }

            catalogController = new AbortController();
            catalogViewInput.value = viewMode;

            const requestUrl = buildCatalogUrl(query, viewMode);
            updateCatalogControls(query, viewMode);

            try {
                const response = await fetch(requestUrl, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                    signal: catalogController.signal,
                });

                if (!response.ok) {
                    throw new Error(`Catalog request failed: ${response.status}`);
                }

                catalogResultsRegion.innerHTML = await response.text();

                if (pushState) {
                    window.history.replaceState({}, '', `${requestUrl.pathname}${requestUrl.search}`);
                }
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error(error);
                }
            }
        };

        catalogSearchInput.addEventListener('input', () => {
            window.clearTimeout(catalogDebounceId);
            catalogDebounceId = window.setTimeout(() => {
                renderCatalogResults(catalogSearchInput.value);
            }, 260);
        });

        catalogSearchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            window.clearTimeout(catalogDebounceId);
            renderCatalogResults(catalogSearchInput.value);
        });

        catalogResetSearch?.addEventListener('click', (event) => {
            event.preventDefault();
            window.clearTimeout(catalogDebounceId);
            catalogSearchInput.value = '';
            renderCatalogResults('', catalogViewInput.value || 'list');
            catalogSearchInput.focus();
        });

        catalogViewOptions.forEach((option) => {
            option.addEventListener('click', (event) => {
                event.preventDefault();
                renderCatalogResults(catalogSearchInput.value, option.dataset.catalogView || 'list');
            });
        });
    }

    const posterInput = document.querySelector('[data-poster-preview-target]');

    if (posterInput) {
        const posterPreview = document.getElementById(posterInput.dataset.posterPreviewTarget);

        posterInput.addEventListener('change', () => {
            const [file] = posterInput.files || [];

            if (!posterPreview || !file || !file.type.startsWith('image/')) {
                return;
            }

            const reader = new FileReader();

            reader.addEventListener('load', () => {
                posterPreview.innerHTML = '';

                const image = document.createElement('img');
                image.src = reader.result;
                image.alt = 'Предпросмотр постера';

                posterPreview.appendChild(image);
            });

            reader.readAsDataURL(file);
        });
    }
    
    const starsContainer = document.getElementById('stars-container');
    const hiddenRatingInput = document.getElementById('id_rating'); // Стандартный ID, который генерирует Django
    const ratingDisplay = document.getElementById('rating-display');
    
    if (starsContainer && hiddenRatingInput) {
        const stars = starsContainer.querySelectorAll('.star');
        let currentRating = hiddenRatingInput.value || 0;

        highlightStars(currentRating);

        stars.forEach(star => {
            star.addEventListener('mouseover', function() {
                const val = this.getAttribute('data-val');
                highlightStars(val);
            });

            star.addEventListener('mouseout', function() {
                highlightStars(currentRating);
            });

            star.addEventListener('click', function() {
                currentRating = this.getAttribute('data-val');
                hiddenRatingInput.value = currentRating;
                ratingDisplay.textContent = `${currentRating}/10`;
                highlightStars(currentRating);
            });
        });

        function highlightStars(val) {
            stars.forEach(s => {
                if (parseInt(s.getAttribute('data-val')) <= parseInt(val)) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });
        }
    }

    const readMoreBtn = document.getElementById('read-more-trigger');
    const modal = document.getElementById('desc-modal');
    const closeBtn = document.getElementById('modal-close-btn');
    const descriptionPreview = document.querySelector('.description-container--hero');
    const posterTrigger = document.getElementById('poster-open-trigger');
    const posterModal = document.getElementById('poster-modal');
    const posterCloseBtn = document.getElementById('poster-modal-close-btn');

    const setupModal = ({ trigger, modalElement, closeElement, onOpen, onClose }) => {
        if (!trigger || !modalElement || !closeElement) {
            return;
        }

        trigger.setAttribute('aria-expanded', 'false');

        const openModal = () => {
            modalElement.classList.add('active');
            trigger.setAttribute('aria-expanded', 'true');
            onOpen?.();
            document.body.style.overflow = 'hidden';
            closeElement.focus();
        };

        const closeModal = () => {
            modalElement.classList.remove('active');
            trigger.setAttribute('aria-expanded', 'false');
            onClose?.();
            document.body.style.overflow = '';
        };

        trigger.addEventListener('click', openModal);
        closeElement.addEventListener('click', closeModal);

        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape' && modalElement.classList.contains('active')) {
                closeModal();
            }
        });
        
        modalElement.addEventListener('click', (e) => {
            if (e.target === modalElement) {
                closeModal();
            }
        });
    };

    setupModal({
        trigger: readMoreBtn,
        modalElement: modal,
        closeElement: closeBtn,
        onOpen: () => descriptionPreview?.classList.add('is-open'),
        onClose: () => descriptionPreview?.classList.remove('is-open'),
    });

    setupModal({
        trigger: posterTrigger,
        modalElement: posterModal,
        closeElement: posterCloseBtn,
    });

    
    const toggleCastBtn = document.getElementById('toggle-cast-btn');
    if (toggleCastBtn) {
        toggleCastBtn.addEventListener('click', function() {
            const hiddenActors = document.querySelectorAll('.hidden-actor');
            hiddenActors.forEach(actor => {
                actor.style.display = 'block'; 
            });
            this.style.display = 'none'; 
        });
    }
});
