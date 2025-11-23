// Main application logic

// Toggle history sidebar
function toggleHistory() {
    const sidebar = document.getElementById('historySidebar');
    sidebar.classList.toggle('open');

    // Load history when opening
    if (sidebar.classList.contains('open')) {
        loadHistory();
    }
}

// Toggle activity log
function toggleActivityLog() {
    const header = document.querySelector('.activity-header');
    header.classList.toggle('collapsed');
}

// Download report as PDF
function downloadPDF() {
    window.print();
}

// Copy report to clipboard
function copyReport() {
    const markdown = document.getElementById('reportMarkdown').getAttribute('data-markdown');
    if (!markdown) {
        // Fallback to text content if data attribute not set
        const text = document.getElementById('reportMarkdown').innerText;
        navigator.clipboard.writeText(text);
    } else {
        navigator.clipboard.writeText(markdown);
    }

    const btn = document.querySelector('.action-btn span'); // The clipboard icon
    // Temporary visual feedback could be added here if we had a specific ID or class for the icon
    // but since we querySelector'd generically, let's just alert or console log for now 
    // or rely on user knowing it worked.
    // Actually, let's find the specific button that was clicked if possible, but for now simple is fine.
}

// Clear search history
async function clearHistory() {
    if (!confirm('Are you sure you want to clear your search history?')) {
        return;
    }

    try {
        const response = await fetch('/api/history/clear', { method: 'POST' });
        if (response.ok) {
            loadHistory();
        } else {
            console.error('Failed to clear history');
        }
    } catch (error) {
        console.error('Error clearing history:', error);
    }
}

// Load and render stock chart
// Load and render stock chart
async function loadChart(query) {
    const canvas = document.getElementById('stockChart');
    if (!canvas) return;

    // Clear previous chart if exists
    if (window.stockChartInstance) {
        window.stockChartInstance.destroy();
        window.stockChartInstance = null;
    }

    try {
        const response = await fetch(`/api/chart/${encodeURIComponent(query)}`);
        if (!response.ok) {
            console.log('No chart data available');
            // Show placeholder or empty state
            canvas.style.display = 'none';
            canvas.parentElement.innerHTML += '<div class="chart-content">No Data</div>';
            return;
        }

        const data = await response.json();
        if (data.error) {
            console.log('Chart error:', data.error);
            return;
        }

        const ctx = canvas.getContext('2d');
        canvas.style.display = 'block';

        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(91, 122, 229, 0.5)');
        gradient.addColorStop(1, 'rgba(91, 122, 229, 0.0)');

        window.stockChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: `${data.symbol} Price`,
                    data: data.prices,
                    borderColor: '#5b7ae5',
                    backgroundColor: gradient,
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#5b7ae5',
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(10, 22, 40, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#a8b3cf',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: function (context) {
                                return '$' + context.parsed.y.toFixed(2);
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        ticks: {
                            maxTicksLimit: 8,
                            color: '#6b7a99',
                            font: {
                                size: 10
                            }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#6b7a99',
                            font: {
                                size: 10
                            },
                            callback: function (value) {
                                return '$' + value;
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

    } catch (error) {
        console.error('Failed to load chart:', error);
    }
}

// Add activity log entry
function addActivityLog(data) {
    const container = document.getElementById('activityLogContent');
    const entry = document.createElement('div');
    entry.className = 'log-entry';

    const time = new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

    const agentClass = `agent-${data.agent.toLowerCase()}`;

    let detailsHtml = '';
    if (data.details) {
        detailsHtml = `<div class="log-details">${data.details}</div>`;
    }

    entry.innerHTML = `
        <div class="log-time">${time}</div>
        <div class="log-agent ${agentClass}">${data.agent}</div>
        <div class="log-message">
            ${data.action}
            ${detailsHtml}
        </div>
    `;

    container.appendChild(entry);
    container.scrollTop = container.scrollHeight;
}

// Load search history
async function loadHistory() {
    const historyList = document.getElementById('historyList');
    historyList.innerHTML = '<div class="history-loading">Loading...</div>';

    try {
        const response = await fetch('/api/history?limit=20');
        const data = await response.json();

        if (data.history && data.history.length > 0) {
            historyList.innerHTML = '';
            data.history.forEach(item => {
                const historyItem = createHistoryItem(item);
                historyList.appendChild(historyItem);
            });
        } else {
            historyList.innerHTML = '<div class="history-loading">No history yet</div>';
        }
    } catch (error) {
        console.error('Failed to load history:', error);
        historyList.innerHTML = '<div class="history-loading">Failed to load history</div>';
    }
}

// Create history item element
function createHistoryItem(item) {
    const div = document.createElement('div');
    div.className = 'history-item';
    div.onclick = () => loadHistoricalResearch(item.id);

    const date = new Date(item.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    div.innerHTML = `
        <div class="history-item-header">
            <span class="history-company">${item.company_name || 'Unknown'}</span>
            <span class="history-recommendation ${item.recommendation.toLowerCase()}">${item.recommendation}</span>
        </div>
        <div class="history-query">${item.query}</div>
        <div class="history-date">${date}</div>
    `;

    return div;
}

// Load a historical research result
async function loadHistoricalResearch(id) {
    try {
        const response = await fetch(`/api/history/${id}`);
        const data = await response.json();

        // Close sidebar
        document.getElementById('historySidebar').classList.remove('open');

        // Display the historical result
        const resultData = {
            short_summary: data.short_summary,
            markdown_report: data.full_report,
            follow_up_questions: data.follow_up_questions,
            verification: data.verification
        };

        displayResults(resultData);
    } catch (error) {
        console.error('Failed to load historical research:', error);
        showError('Failed to load historical research');
    }
}

// Toggle full report
function toggleReport() {
    const content = document.getElementById('fullReportContent');
    const arrow = document.querySelector('.toggle-report .arrow');

    if (content.style.display === 'none') {
        content.style.display = 'block';
        arrow.classList.add('rotated');
    } else {
        content.style.display = 'none';
        arrow.classList.remove('rotated');
    }
}

// Update progress stepper
function updateProgress(stage, isDone = false) {
    const step = document.getElementById(`step-${stage}`);

    if (step) {
        if (isDone) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else {
            step.classList.add('active');
        }
    }
}

// Extract company name from query
function extractCompanyName(query) {
    const words = query.toLowerCase().split(' ');
    const companies = ['amazon', 'apple', 'google', 'microsoft', 'tesla', 'meta', 'nvidia'];

    for (const company of companies) {
        if (query.toLowerCase().includes(company)) {
            return company.charAt(0).toUpperCase() + company.slice(1);
        }
    }

    return 'Company';
}

// Display results
function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';

    // Extract company name from summary
    const companyName = extractCompanyName(data.short_summary);
    document.getElementById('stockName').textContent = companyName;

    // Set recommendation badge
    const badge = document.getElementById('recommendationBadge');
    const summary = data.short_summary.toLowerCase();

    if (summary.includes('buy') || summary.includes('strong') || summary.includes('positive')) {
        badge.textContent = 'Buy';
        badge.className = 'recommendation-badge buy';
    } else if (summary.includes('sell') || summary.includes('negative') || summary.includes('avoid')) {
        badge.textContent = 'Sell';
        badge.className = 'recommendation-badge sell';
    } else {
        badge.textContent = 'Hold';
        badge.className = 'recommendation-badge hold';
    }

    // Create sample metrics (in real implementation, extract from report)
    const metricsGrid = document.getElementById('metricsGrid');
    metricsGrid.innerHTML = `
        <div class="metric-card">
            <div class="metric-label">Analysis</div>
            <div class="metric-value">Complete</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Sources</div>
            <div class="metric-value">Multiple</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Verified</div>
            <div class="metric-value">${data.verification ? (data.verification.verified ? 'Yes' : 'No') : 'Pending'}</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Recommendation</div>
            <div class="metric-value">${badge.textContent}</div>
        </div>
    `;

    // Set recommendation text
    document.getElementById('recommendationText').textContent = data.short_summary;

    // Full report - Using marked.js
    const reportDiv = document.getElementById('reportMarkdown');
    if (window.marked) {
        reportDiv.innerHTML = marked.parse(data.markdown_report);
    } else {
        // Fallback if marked.js fails to load
        reportDiv.textContent = data.markdown_report;
    }
    reportDiv.setAttribute('data-markdown', data.markdown_report);

    // Follow-up questions
    const questionsList = document.getElementById('followUpQuestions');
    questionsList.innerHTML = '';
    data.follow_up_questions.forEach(question => {
        const li = document.createElement('li');
        li.textContent = question;
        questionsList.appendChild(li);
    });

    // Verification
    const verificationContent = document.getElementById('verificationContent');

    let factChecksHtml = '';
    if (data.verification.fact_checks && data.verification.fact_checks.length > 0) {
        factChecksHtml = '<div style="margin-top: 1rem;"><h4>Fact Checks</h4><ul style="list-style: none; margin: 0; padding: 0;">';
        data.verification.fact_checks.forEach(check => {
            const icon = check.verified ? '✅' : '❌';
            factChecksHtml += `
                <li style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255, 255, 255, 0.03); border-radius: 4px;">
                    <div style="display: flex; align-items: start; gap: 0.5rem;">
                        <span>${icon}</span>
                        <div>
                            <div style="font-weight: 500;">${check.claim}</div>
                            <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.2rem;">${check.evidence}</div>
                            ${check.source_url ? `<a href="${check.source_url}" target="_blank" style="font-size: 0.8rem; color: var(--accent-primary);">Source</a>` : ''}
                        </div>
                    </div>
                </li>
            `;
        });
        factChecksHtml += '</ul></div>';
    }

    verificationContent.innerHTML = `
        <div class="verification-placeholder">
            <p>Verification has not been run yet.</p>
            <button class="verify-btn-small" onclick="startVerification()">Run Verification</button>
        </div>
    `;

    if (data.verification) {
        displayVerificationResult(data.verification);
    }
}

// Show error
function showError(message) {
    const errorSection = document.getElementById('errorSection');
    const errorMessage = document.getElementById('errorMessage');

    errorMessage.textContent = message;
    errorSection.style.display = 'block';
}

// Reset UI
function resetUI() {
    document.getElementById('progressSection').style.display = 'none';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('errorSection').style.display = 'none';
    document.getElementById('activitySection').style.display = 'none';
    document.getElementById('activityLogContent').innerHTML = '';

    // Reset progress steps
    ['planning', 'searching', 'writing', 'verifying'].forEach(stage => {
        const step = document.getElementById(`step-${stage}`);
        if (step) {
            step.classList.remove('active', 'completed');
        }
    });

    // Reset button
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = 'Analyze';

    // Clear chart instance
    if (window.stockChartInstance) {
        window.stockChartInstance.destroy();
        window.stockChartInstance = null;
    }
}

// Handle analyze button click
document.getElementById('analyzeBtn').addEventListener('click', async () => {
    const query = document.getElementById('queryInput').value.trim();
    if (!query) return;

    // Reset UI
    resetUI();

    // Start loading chart in background
    loadChart(query);

    // Show progress and activity log
    document.getElementById('progressSection').style.display = 'block';
    document.getElementById('activitySection').style.display = 'block';

    // Disable button
    const analyzeBtn = document.getElementById('analyzeBtn');
    analyzeBtn.disabled = true;
    analyzeBtn.textContent = 'Analyzing...';

    try {
        const response = await fetch('/api/research', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query }),
        });

        if (!response.ok) {
            throw new Error('Failed to start research');
        }

        // Read SSE stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();

            if (done) break;

            buffer += decoder.decode(value, { stream: true });

            // Process complete events
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;

                // Parse SSE format
                const eventMatch = line.match(/^event: (.+)$/m);
                const dataMatch = line.match(/^data: (.+)$/m);

                if (eventMatch && dataMatch) {
                    const eventType = eventMatch[1];
                    const data = JSON.parse(dataMatch[1]);

                    if (eventType === 'status') {
                        updateProgress(data.stage, data.done);
                    } else if (eventType === 'agent_log') {
                        addActivityLog(data);
                    } else if (eventType === 'complete') {
                        displayResults(data);
                        // Try to load chart again if it wasn't loaded (e.g. if extracted ticker changed based on result)
                        // But we passed query to loadChart, which should be enough usually.
                        analyzeBtn.disabled = false;
                        analyzeBtn.textContent = 'Analyze New Query';
                    } else if (eventType === 'error') {
                        showError(data.message);
                        analyzeBtn.disabled = false;
                        analyzeBtn.textContent = 'Try Again';
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error:', error);
        showError('An error occurred while processing your request. Please try again.');
        analyzeBtn.disabled = false;
        analyzeBtn.textContent = 'Try Again';
    }
});

// Handle enter key on input
document.getElementById('queryInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        document.getElementById('analyzeBtn').click();
    }
});

// Start manual verification
async function startVerification() {
    const reportText = document.getElementById('reportMarkdown').getAttribute('data-markdown');
    if (!reportText) return;

    const verificationContent = document.getElementById('verificationContent');
    verificationContent.innerHTML = `
        <div class="verification-loading">
            <div class="spinner"></div>
            <p>Verifying report... This may take a moment.</p>
        </div>
    `;

    // Show activity log if hidden
    document.getElementById('activitySection').style.display = 'block';

    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ report: reportText }),
        });

        if (!response.ok) {
            throw new Error('Failed to start verification');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                const eventMatch = line.match(/^event: (.+)$/m);
                const dataMatch = line.match(/^data: (.+)$/m);

                if (eventMatch && dataMatch) {
                    const eventType = eventMatch[1];
                    const data = JSON.parse(dataMatch[1]);

                    if (eventType === 'agent_log') {
                        addActivityLog(data);
                    } else if (eventType === 'complete') {
                        displayVerificationResult(data);
                    } else if (eventType === 'error') {
                        verificationContent.innerHTML = `<div class="error-message">${data.message}</div>`;
                    }
                }
            }
        }
    } catch (error) {
        console.error('Verification error:', error);
        verificationContent.innerHTML = `<div class="error-message">Failed to verify report</div>`;
    }
}

function displayVerificationResult(data) {
    const verificationContent = document.getElementById('verificationContent');

    let factChecksHtml = '';
    if (data.fact_checks && data.fact_checks.length > 0) {
        factChecksHtml = '<div style="margin-top: 1rem;"><h4>Fact Checks</h4><ul class="fact-check-list">';
        data.fact_checks.forEach(check => {
            const icon = check.verified ? '✅' : '❌';
            factChecksHtml += `
                <li class="fact-check-item">
                    <div class="fact-check-icon">${icon}</div>
                    <div class="fact-check-content">
                        <div class="fact-check-claim">${check.claim}</div>
                        <div class="fact-check-evidence">${check.evidence}</div>
                        ${check.source_url ? `<a href="${check.source_url}" target="_blank" class="fact-check-source">Source</a>` : ''}
                    </div>
                </li>
            `;
        });
        factChecksHtml += '</ul></div>';
    }

    verificationContent.innerHTML = `
        <div class="verification-result ${data.verified ? 'verified' : 'issues'}">
            <div class="verification-header">
                <span class="verification-status-icon">${data.verified ? '✓' : '⚠'}</span>
                <h4 class="verification-status-title">${data.verified ? 'Verification Passed' : 'Issues Found'}</h4>
            </div>
            <p class="verification-summary">${data.issues}</p>
            ${factChecksHtml}
        </div>
    `;

    // Update metric
    const metricValue = document.querySelector('.metric-card:nth-child(3) .metric-value');
    if (metricValue) {
        metricValue.textContent = data.verified ? 'Yes' : 'No';
    }
}
