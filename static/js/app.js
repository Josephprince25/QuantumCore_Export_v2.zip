document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scan-btn');
    const scanStatus = document.getElementById('scan-status');
    const resultsBody = document.getElementById('results-body');
    const profitCount = document.getElementById('profit-count');
    const exchCount = document.getElementById('exch-count');
    const exchangeList = document.getElementById('exchange-list');

    // Global state for this session
    let lastResults = null;

    // Fetch config on load
    fetchConfig();

    scanBtn.addEventListener('click', async () => {
        // Gather selected exchanges
        const selected = Array.from(document.querySelectorAll('input[name="exchange"]:checked')).map(el => el.value);
        if (selected.length === 0) {
            alert("Please select at least one exchange.");
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('/api/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ exchanges: selected })
            });
            const data = await response.json();

            if (data.status === 'success') {
                lastResults = data; // Store for modal
                renderTable(data.opportunities, 'results-body', true);
                renderTable(data.all_opportunities, 'all-results-body', false);
                profitCount.textContent = data.count;
                // Fix: Update total analyzed count correctly
                document.getElementById('paths-analyzed').textContent = data.total_analyzed || data.all_opportunities.length;
            } else {
                alert('Error: ' + data.message);
            }
        } catch (error) {
            console.error('Scan failed:', error);
            alert('Failed to connect to scanner.');
        } finally {
            setLoading(false);
        }
    });

    async function fetchConfig() {
        try {
            const res = await fetch('/api/config');
            const conf = await res.json();
            document.getElementById('min-profit-val').textContent = conf.min_profit_percent + '%';

            // Build Exchange Checkboxes
            exchangeList.innerHTML = conf.supported_exchanges.map(ex => `
                <div class="checkbox-item">
                    <input type="checkbox" id="ex-${ex}" name="exchange" value="${ex}" checked>
                    <label for="ex-${ex}">${ex}</label>
                </div>
            `).join('');

            exchCount.textContent = conf.supported_exchanges.length;

        } catch (e) {
            console.warn("Failed to fetch config");
        }
    }

    function setLoading(isLoading) {
        if (isLoading) {
            scanBtn.disabled = true;
            scanBtn.innerHTML = '<ion-icon name="sync-outline" class="spin"></ion-icon> Scanning...';
            scanStatus.textContent = 'Scanning...';
            scanStatus.className = 'status-pill scanning';

            const loadingRow = `
                <tr class="empty-state">
                    <td colspan="8">
                        <div class="scanner-loader">
                            <div class="scanner-radar"></div>
                            <div class="loading-text">ANALYZING MARKET DATA...</div>
                        </div>
                    </td>
                </tr>
            `;
            resultsBody.innerHTML = loadingRow;
            document.getElementById('all-results-body').innerHTML = loadingRow;
        } else {
            scanBtn.disabled = false;
            scanBtn.innerHTML = '<ion-icon name="scan-circle-outline"></ion-icon> Start Scan';
            scanStatus.textContent = 'Idle';
            scanStatus.className = 'status-pill idle';
        }
    }

    function renderTable(opportunities, elementId, onlyProfitable) {
        const tbody = document.getElementById(elementId);

        if (!opportunities || opportunities.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-state">
                    <td colspan="8">
                        <div class="empty-message">
                            <ion-icon name="alert-circle-outline"></ion-icon>
                            <p>No data found.</p>
                        </div>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = opportunities.map((op, i) => {
            const pathBadges = op.trade_path.map(p => {
                return `<span class="path-badge">${p}</span>`;
            }).join(' <ion-icon name="arrow-forward-outline" style="font-size: 10px; vertical-align: middle;"></ion-icon> ');

            let statusClass = '';
            let statusText = op.status || 'UNKNOWN';

            if (statusText === 'PROFITABLE') statusClass = 'profit-pos';
            else if (statusText === 'LOSS') statusClass = 'profit-neg';
            else if (statusText === 'LOW_PROFIT') statusClass = 'profit-mid';

            return `
                <tr>
                    <td><span class="exch-badge">${op.exchange || 'N/A'}</span></td>
                    <td>${new Date(op.timestamp).toLocaleTimeString()}</td>
                    <td style="max-width: 300px; white-space: normal;">
                        ${pathBadges}
                    </td>
                    <td>${op.start_amount} ${op.start_coin}</td>
                    <td>${op.end_amount} ${op.end_coin}</td>
                    <td style="color: var(--text-secondary); font-size: 0.85rem;">
                        ${op.fees_str || 'N/A'}
                        <button class="btn-icon" style="font-size: 1rem; vertical-align: middle; margin-left: 4px;" onclick="window.viewFeeDetails(${i}, ${onlyProfitable})">
                            <ion-icon name="information-circle-outline"></ion-icon>
                        </button>
                    </td>
                    <td class="${op.profit_percent >= 0 ? 'profit-pos' : 'profit-neg'}">${op.profit_percent > 0 ? '+' : ''}${op.profit_percent}%</td>
                    <td><span class="status-pill status-${statusText.toLowerCase()}" style="font-size: 0.75rem;">${statusText}</span></td>
                </tr>
            `;
        }).join('');
    }

    // Modal Logic
    const modal = document.getElementById('fee-modal');
    const closeModalBtn = document.getElementById('close-modal');
    const modalBody = document.getElementById('fee-modal-body');

    closeModalBtn.addEventListener('click', () => {
        modal.classList.add('hidden');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    });

    // Expose viewFeeDetails to window for onclick handlers
    window.viewFeeDetails = function (index, isProfitable) {
        if (!lastResults) return;

        const list = isProfitable ? lastResults.opportunities : lastResults.all_opportunities;
        const op = list[index];
        if (!op || !op.fee_breakdown) return;

        modalBody.innerHTML = op.fee_breakdown.map(f => `
            <tr>
                <td>${f.step}</td>
                <td><span class="path-badge">${f.symbol}</span></td>
                <td><span style="color: ${f.action === 'BUY' ? 'var(--accent-green)' : 'var(--accent-red)'}">${f.action}</span></td>
                <td>${f.fee_percent}</td>
            </tr>
        `).join('');

        modal.classList.remove('hidden');
    };
});
