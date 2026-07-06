document.addEventListener('DOMContentLoaded', () => {
    const searchForm = document.getElementById('search-form');
    const tickerInput = document.getElementById('ticker-input');
    const analyzeBtn = document.getElementById('analyze-btn');
    const consoleLogs = document.getElementById('console-logs');
    const logsCountBadge = document.getElementById('logs-count');
    const footerTime = document.getElementById('footer-time');

    // Agent 1 elements
    const agent1Content = document.getElementById('agent-1-content');
    const agent1StatusDot = document.querySelector('#agent-1-status .status-dot');
    const agent1StatusText = document.querySelector('#agent-1-status .status-text');

    // Agent 2 elements
    const agent2Content = document.getElementById('agent-2-content');
    const agent2StatusDot = document.querySelector('#agent-2-status .status-dot');
    const agent2StatusText = document.querySelector('#agent-2-status .status-text');

    // Agent 3 elements
    const agent3Content = document.getElementById('agent-3-content');
    const agent3StatusDot = document.querySelector('#agent-3-status .status-dot');
    const agent3StatusText = document.querySelector('#agent-3-status .status-text');

    let logCounter = 0;
    let eventSource = null;

    // Set up continuous system clock in footer
    function updateClock() {
        const now = new Date();
        footerTime.textContent = `System Time: ${now.toLocaleTimeString()}`;
    }
    setInterval(updateClock, 1000);
    updateClock();

    // Custom helper to append logs to console
    function addLogEntry(agent, message) {
        logCounter++;
        logsCountBadge.textContent = `${logCounter} Event${logCounter > 1 ? 's' : ''}`;

        // Remove empty state if present
        const emptyState = consoleLogs.querySelector('.empty-state-log');
        if (emptyState) {
            emptyState.remove();
        }

        const entry = document.createElement('div');
        // Match CSS classes (system, agent-1, agent-2, agent-3)
        const agentClass = agent.toLowerCase().replace(' ', '-');
        entry.className = `log-entry ${agentClass}`;

        const timestamp = new Date().toLocaleTimeString();

        entry.innerHTML = `
            <div class="log-header">
                <span class="log-sender ${agentClass}">${agent}</span>
                <span class="log-time">${timestamp}</span>
            </div>
            <div class="log-message">${message}</div>
        `;

        consoleLogs.appendChild(entry);
        consoleLogs.scrollTop = consoleLogs.scrollHeight;
    }

    // Helper to update agent status visual states
    function updateAgentStatus(agentNum, state, text) {
        let dot, textLabel;
        if (agentNum === 1) {
            dot = agent1StatusDot;
            textLabel = agent1StatusText;
        } else if (agentNum === 2) {
            dot = agent2StatusDot;
            textLabel = agent2StatusText;
        } else if (agentNum === 3) {
            dot = agent3StatusDot;
            textLabel = agent3StatusText;
        }

        if (!dot || !textLabel) return;

        // Reset classes
        dot.className = 'status-dot';
        
        if (state === 'idle') {
            dot.classList.add('dot-idle');
        } else if (state === 'searching') {
            dot.classList.add('dot-searching');
        } else if (state === 'generating') {
            dot.classList.add('dot-generating');
        } else if (state === 'complete') {
            dot.classList.add('dot-complete');
        }

        textLabel.textContent = text;
    }

    // Reset UI to clean initial states before a run
    function resetDashboard() {
        logCounter = 0;
        consoleLogs.innerHTML = '';
        logsCountBadge.textContent = '0 Events';
        
        // Agent 1 Reset
        updateAgentStatus(1, 'idle', 'Idle');
        agent1Content.innerHTML = `
            <div class="report-placeholder">
                <div class="placeholder-icon">🏢</div>
                <h3>Corporate Structure & Strategy</h3>
                <p>Retrieving updated financial performance and corporate metrics...</p>
            </div>
        `;

        // Agent 2 Reset
        updateAgentStatus(2, 'idle', 'Idle');
        agent2Content.innerHTML = `
            <div class="report-placeholder">
                <div class="placeholder-icon">📈</div>
                <h3>Macro Indicators & Industry Shifts</h3>
                <p>Analyzing industry environment and central bank policy implications...</p>
            </div>
        `;

        // Agent 3 Reset
        updateAgentStatus(3, 'idle', 'Idle');
        agent3Content.innerHTML = `
            <div class="report-placeholder">
                <div class="placeholder-icon">📊</div>
                <h3>Industry Size, CAGR & Key Trends</h3>
                <p>Estimating market size, projected growth cycles, and competitive forces...</p>
            </div>
        `;
    }

    // Submit handler
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const query = tickerInput.value.trim();
        if (!query) return;

        // Close any existing SSE stream
        if (eventSource) {
            eventSource.close();
        }

        resetDashboard();
        
        // Disable button & show running state
        analyzeBtn.disabled = true;
        analyzeBtn.querySelector('.btn-text').textContent = 'Analyzing...';
        analyzeBtn.classList.add('running');

        // Set status to searching/running
        updateAgentStatus(1, 'searching', 'Initializing');
        updateAgentStatus(2, 'searching', 'Initializing');
        updateAgentStatus(3, 'searching', 'Initializing');

        // Establish connection to Server-Sent Events backend endpoint
        const encodedQuery = encodeURIComponent(query);
        eventSource = new EventSource(`/api/analyze?query=${encodedQuery}`);

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'log') {
                    addLogEntry(data.agent, data.message);
                    
                    // Dynamically transition agent status dots based on log contents
                    const msg = data.message.toLowerCase();
                    const sender = data.agent;
                    
                    if (sender === 'Agent 1') {
                        if (msg.includes('initializing') || msg.includes('fetching')) {
                            updateAgentStatus(1, 'searching', 'Searching Web');
                        } else if (msg.includes('grounding') || msg.includes('running')) {
                            updateAgentStatus(1, 'generating', 'Analyzing');
                        } else if (msg.includes('completed')) {
                            updateAgentStatus(1, 'complete', 'Compiling');
                        }
                    } else if (sender === 'Agent 2') {
                        if (msg.includes('initializing') || msg.includes('checking')) {
                            updateAgentStatus(2, 'searching', 'Searching Web');
                        } else if (msg.includes('grounding') || msg.includes('running')) {
                            updateAgentStatus(2, 'generating', 'Analyzing');
                        } else if (msg.includes('completed')) {
                            updateAgentStatus(2, 'complete', 'Compiling');
                        }
                    } else if (sender === 'Agent 3') {
                        if (msg.includes('initializing') || msg.includes('checking')) {
                            updateAgentStatus(3, 'searching', 'Searching Web');
                        } else if (msg.includes('grounding') || msg.includes('running')) {
                            updateAgentStatus(3, 'generating', 'Analyzing');
                        } else if (msg.includes('completed')) {
                            updateAgentStatus(3, 'complete', 'Compiling');
                        }
                    }
                } 
                else if (data.type === 'report') {
                    const agent = data.agent;
                    const reportMarkdown = data.message;
                    
                    // Render using marked.js
                    const htmlContent = `<div class="report-markdown">${marked.parse(reportMarkdown)}</div>`;
                    
                    if (agent === 'Agent 1') {
                        agent1Content.innerHTML = htmlContent;
                        updateAgentStatus(1, 'complete', 'Complete');
                    } else if (agent === 'Agent 2') {
                        agent2Content.innerHTML = htmlContent;
                        updateAgentStatus(2, 'complete', 'Complete');
                    } else if (agent === 'Agent 3') {
                        agent3Content.innerHTML = htmlContent;
                        updateAgentStatus(3, 'complete', 'Complete');
                    }
                }
            } catch (err) {
                console.error("Error parsing message: ", err);
                addLogEntry('System', 'Error parsing event stream data.');
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE stream error: ", err);
            addLogEntry('System', 'Connection to analysis engine closed.');
            
            // Re-enable button
            analyzeBtn.disabled = false;
            analyzeBtn.querySelector('.btn-text').textContent = 'Run Analysis';
            analyzeBtn.classList.remove('running');
            
            // Update incomplete agents status
            if (agent1StatusText.textContent !== 'COMPLETE') {
                updateAgentStatus(1, 'idle', 'Disconnected');
            }
            if (agent2StatusText.textContent !== 'COMPLETE') {
                updateAgentStatus(2, 'idle', 'Disconnected');
            }
            if (agent3StatusText.textContent !== 'COMPLETE') {
                updateAgentStatus(3, 'idle', 'Disconnected');
            }
            
            eventSource.close();
        };
    });
});
