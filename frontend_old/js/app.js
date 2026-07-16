document.addEventListener("DOMContentLoaded", () => {
    
    // ---- Navigation Logic ----
    const navLinks = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('.view-section');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            // Update active link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');

            // Show corresponding section
            const targetId = link.getAttribute('data-target');
            sections.forEach(sec => {
                sec.classList.remove('active');
                if(sec.id === targetId) {
                    sec.classList.add('active');
                }
            });

            // Special handling for graph resize bug
            if (targetId === 'graph-view' && window.currentResults) {
                setTimeout(() => {
                    kg.render(window.currentResults.intelligence.graph_data);
                }, 100);
            }
        });
    });

    // ---- Search Logic ----
    const searchBtn = document.getElementById('search-btn');
    const searchInput = document.getElementById('search-input');
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const dashboardGrid = document.getElementById('dashboard-grid');

    let isRunning = false;
    let pollInterval = null;

    searchBtn.addEventListener('click', startResearchFlow);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startResearchFlow();
    });

    async function startResearchFlow() {
        const topic = searchInput.value.trim();
        if (!topic || isRunning) return;

        // Get selected sources
        const sources = [];
        if (document.getElementById('src-arxiv').checked) sources.push('arxiv');
        if (document.getElementById('src-ss').checked) sources.push('semantic_scholar');
        if (document.getElementById('src-pubmed').checked) sources.push('pubmed');
        if (document.getElementById('src-oa').checked) sources.push('openalex');

        if (sources.length === 0) {
            alert("Please select at least one source.");
            return;
        }

        // Reset UI
        isRunning = true;
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
        dashboardGrid.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        updateProgress("Initializing AI agents...", 0.02);

        try {
            // Start via API
            const sessionId = await api.startResearch(topic, sources, (msg, prog) => {
                updateProgress(msg, prog);
            });

            // Poll for completion
            pollInterval = setInterval(async () => {
                const status = await api.checkStatus(sessionId);
                if (status) {
                    if (status.status === 'completed') {
                        clearInterval(pollInterval);
                        await fetchAndRenderResults(sessionId);
                    } else if (status.status === 'failed') {
                        clearInterval(pollInterval);
                        updateProgress("Analysis failed. See backend logs.", 1.0);
                        resetSearchButton();
                    }
                }
            }, 3000);

        } catch (error) {
            console.error(error);
            updateProgress("Failed to start research. Is backend running?", 0);
            resetSearchButton();
        }
    }

    function updateProgress(message, progress) {
        progressText.innerText = message;
        progressBar.style.width = `${progress * 100}%`;
    }

    function resetSearchButton() {
        isRunning = false;
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Synthesize';
    }

    // ---- Render Results ----
    async function fetchAndRenderResults(sessionId) {
        try {
            updateProgress("Fetching final results...", 0.98);
            const results = await api.getResults(sessionId);
            window.currentResults = results; // Store globally for graph resize

            renderDashboard(results);
            renderReport(results.report);
            kg.render(results.intelligence.graph_data);

            progressContainer.classList.add('hidden');
            dashboardGrid.classList.remove('hidden');
            resetSearchButton();

        } catch (error) {
            console.error(error);
            updateProgress("Failed to load results.", 1.0);
            resetSearchButton();
        }
    }

    function renderDashboard(results) {
        const { session, intelligence, papers } = results;

        // Render Gaps
        const gapsList = document.getElementById('gaps-list');
        gapsList.innerHTML = '';
        const gaps = intelligence.gaps || [];
        if (gaps.length === 0) gapsList.innerHTML = "<li>No specific gaps identified.</li>";
        gaps.slice(0, 3).forEach(g => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${g.gap}</strong> ${g.description}`;
            gapsList.appendChild(li);
        });

        // Render Hypotheses
        const hypoList = document.getElementById('hypotheses-list');
        hypoList.innerHTML = '';
        const hypotheses = intelligence.hypotheses || [];
        if (hypotheses.length === 0) hypoList.innerHTML = "<li>No hypotheses generated.</li>";
        hypotheses.slice(0, 3).forEach(h => {
            const li = document.createElement('li');
            li.innerHTML = `<strong>${h.hypothesis}</strong> ${h.rationale}`;
            hypoList.appendChild(li);
        });

        // Render Papers
        document.getElementById('paper-count').innerText = papers.length;
        const papersList = document.getElementById('papers-list');
        papersList.innerHTML = '';
        
        // Sort papers by relevance score
        const sortedPapers = papers.sort((a, b) => b.relevance_score - a.relevance_score);

        sortedPapers.forEach(p => {
            const authorsStr = p.authors.slice(0, 3).join(", ") + (p.authors.length > 3 ? " et al." : "");
            
            const pDiv = document.createElement('div');
            pDiv.className = 'paper-item';
            pDiv.innerHTML = `
                <div class="paper-title">${p.title} <span class="badge">Score: ${(p.relevance_score * 100).toFixed(0)}</span></div>
                <div class="paper-meta">
                    <span><i class="fa-solid fa-calendar"></i> ${p.year || 'N/A'}</span>
                    <span><i class="fa-solid fa-users"></i> ${authorsStr}</span>
                    <span><i class="fa-solid fa-quote-right"></i> ${p.citations} citations</span>
                    <span><i class="fa-solid fa-database"></i> ${p.source}</span>
                </div>
                <div class="paper-summary">${p.summary || p.abstract.substring(0, 200) + '...'}</div>
                <div class="paper-links">
                    ${p.url ? `<a href="${p.url}" target="_blank"><i class="fa-solid fa-link"></i> Source</a>` : ''}
                    ${p.pdf_url ? `<a href="${p.pdf_url}" target="_blank"><i class="fa-solid fa-file-pdf"></i> PDF</a>` : ''}
                </div>
            `;
            papersList.appendChild(pDiv);
        });
    }

    function renderReport(markdownContent) {
        const mdDiv = document.getElementById('markdown-content');
        if (markdownContent) {
            mdDiv.innerHTML = marked.parse(markdownContent);
        } else {
            mdDiv.innerHTML = `
                <div class="empty-state">
                    <i class="fa-solid fa-triangle-exclamation"></i>
                    <p>Report generation failed or returned empty.</p>
                </div>
            `;
        }
    }
});
