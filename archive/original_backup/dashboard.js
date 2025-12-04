// Dashboard JavaScript - Real-time WebSocket Updates

let ws = null;
let reconnectInterval = null;
let messageHistory = [];
let chartData = {
    labels: [],
    nodeA: [],
    nodeB: [],
    nodeC: []
};
let chart = null;
let uptimeStart = Date.now();

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    initWebSocket();
    initChart();
    startUptimeCounter();
});

// WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        updateConnectionStatus(true);
        
        // Send heartbeat every 30 seconds
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);
    };
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
        }
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateConnectionStatus(false);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
        updateConnectionStatus(false);
        
        // Reconnect after 3 seconds
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            initWebSocket();
        }, 3000);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    if (data.type === 'initial_data') {
        console.log('Received initial data:', data);
        updateDashboard(data.dashboard_data);
    } else if (data.type === 'mqtt_update') {
        console.log('MQTT update:', data.topic);
        updateDashboard(data.dashboard_data);
        
        // Update chart
        updateChart(data.topic);
    }
}

// Update entire dashboard
function updateDashboard(dashboardData) {
    updateNodeA(dashboardData.node_a);
    updateNodeB(dashboardData.node_b);
    updateNodeC(dashboardData.node_c);
    updateStatistics(dashboardData.statistics);
}

// Update Node A display
function updateNodeA(nodeData) {
    const statusEl = document.getElementById('nodeAStatus');
    const brokerEl = document.getElementById('nodeABroker');
    const failoverEl = document.getElementById('nodeAFailover');
    const reconnectEl = document.getElementById('nodeAReconnect');
    const msgCountEl = document.getElementById('nodeAMsgCount');
    const lastUpdateEl = document.getElementById('nodeALastUpdate');
    const dataEl = document.getElementById('nodeAData');
    
    // Update status badge
    statusEl.textContent = nodeData.status || 'Unknown';
    statusEl.className = 'status-badge';
    
    if (nodeData.status === 'connected' || nodeData.status === 'heartbeat') {
        statusEl.classList.add('online');
    } else if (nodeData.status === 'failover' || nodeData.status === 'self_healing') {
        statusEl.classList.add('error');
    } else {
        statusEl.classList.add('offline');
    }
    
    // Update metrics
    brokerEl.textContent = `Broker ${nodeData.broker || '-'}`;
    failoverEl.textContent = nodeData.failover_count || 0;
    reconnectEl.textContent = nodeData.reconnect_count || 0;
    msgCountEl.textContent = nodeData.data_count || 0;
    lastUpdateEl.textContent = formatTimestamp(nodeData.last_update);
    
    // Update data preview
    if (nodeData.latest_data && Object.keys(nodeData.latest_data).length > 0) {
        dataEl.innerHTML = `
            <strong>Latest Sensor Data:</strong><br>
            Temperature: ${nodeData.latest_data.temperature || '-'}°C<br>
            Humidity: ${nodeData.latest_data.humidity || '-'}%<br>
            Pressure: ${nodeData.latest_data.pressure || '-'} hPa
        `;
    }
}

// Update Node B display
function updateNodeB(nodeData) {
    const statusEl = document.getElementById('nodeBStatus');
    const modeEl = document.getElementById('nodeBMode');
    const offlineEl = document.getElementById('nodeBOffline');
    const retryEl = document.getElementById('nodeBRetry');
    const msgCountEl = document.getElementById('nodeBMsgCount');
    const lastUpdateEl = document.getElementById('nodeBLastUpdate');
    const dataEl = document.getElementById('nodeBData');
    
    // Update status badge
    statusEl.textContent = nodeData.status || 'Unknown';
    statusEl.className = 'status-badge';
    
    if (nodeData.mode === 'online') {
        statusEl.classList.add('online');
    } else if (nodeData.mode === 'offline') {
        statusEl.classList.add('offline');
    } else {
        statusEl.classList.add('error');
    }
    
    // Update metrics
    modeEl.textContent = (nodeData.mode || '-').toUpperCase();
    offlineEl.textContent = nodeData.offline_decisions || 0;
    retryEl.textContent = nodeData.retry_count || 0;
    msgCountEl.textContent = nodeData.data_count || 0;
    lastUpdateEl.textContent = formatTimestamp(nodeData.last_update);
    
    // Update data preview
    if (nodeData.latest_data && Object.keys(nodeData.latest_data).length > 0) {
        const data = nodeData.latest_data;
        let preview = '<strong>Edge Processing Result:</strong><br>';
        
        if (data.decision) {
            preview += `Decision: ${data.decision}<br>`;
            preview += `Action: ${data.action || 'none'}<br>`;
        }
        
        if (data.statistics) {
            preview += `Avg Temp: ${data.statistics.avg_temperature || '-'}°C<br>`;
            preview += `Avg Humidity: ${data.statistics.avg_humidity || '-'}%`;
        }
        
        dataEl.innerHTML = preview;
    }
}

// Update Node C display
function updateNodeC(nodeData) {
    const statusEl = document.getElementById('nodeCStatus');
    const rateEl = document.getElementById('nodeCRate');
    const totalEl = document.getElementById('nodeCTotal');
    const topicsEl = document.getElementById('nodeCTopics');
    const alertEl = document.getElementById('nodeCAlert');
    
    // Update status badge
    statusEl.textContent = (nodeData.status || 'idle').toUpperCase();
    statusEl.className = 'status-badge';
    
    if (nodeData.status === 'attacking') {
        statusEl.classList.add('attacking');
        alertEl.style.display = 'block';
        alertEl.querySelector('.alert-text').textContent = `⚠️ Attack in progress! ${nodeData.messages_per_second || 0} msg/s`;
    } else if (nodeData.status === 'ready') {
        statusEl.classList.add('online');
        alertEl.style.display = 'none';
    } else {
        statusEl.classList.add('idle');
        alertEl.style.display = 'none';
    }
    
    // Update metrics
    rateEl.textContent = formatNumber(nodeData.messages_per_second || 0);
    totalEl.textContent = formatNumber(nodeData.total_messages || 0);
    topicsEl.textContent = formatNumber(nodeData.topics_created || 0);
}

// Update statistics display
function updateStatistics(statsData) {
    const totalMsgEl = document.getElementById('statsTotalMsg');
    
    totalMsgEl.textContent = formatNumber(statsData.total_messages_received || 0);
}

// Update chart with new data point
function updateChart(topic) {
    const now = new Date().toLocaleTimeString();
    
    // Keep only last 20 data points
    if (chartData.labels.length >= 20) {
        chartData.labels.shift();
        chartData.nodeA.shift();
        chartData.nodeB.shift();
        chartData.nodeC.shift();
    }
    
    chartData.labels.push(now);
    
    // Increment counter based on topic
    if (topic.startsWith('/nodeA/')) {
        chartData.nodeA.push((chartData.nodeA[chartData.nodeA.length - 1] || 0) + 1);
        chartData.nodeB.push(chartData.nodeB[chartData.nodeB.length - 1] || 0);
        chartData.nodeC.push(chartData.nodeC[chartData.nodeC.length - 1] || 0);
    } else if (topic.startsWith('/nodeB/')) {
        chartData.nodeA.push(chartData.nodeA[chartData.nodeA.length - 1] || 0);
        chartData.nodeB.push((chartData.nodeB[chartData.nodeB.length - 1] || 0) + 1);
        chartData.nodeC.push(chartData.nodeC[chartData.nodeC.length - 1] || 0);
    } else if (topic.startsWith('/nodeC/') || topic.startsWith('/attack/') || topic.startsWith('/spam/')) {
        chartData.nodeA.push(chartData.nodeA[chartData.nodeA.length - 1] || 0);
        chartData.nodeB.push(chartData.nodeB[chartData.nodeB.length - 1] || 0);
        chartData.nodeC.push((chartData.nodeC[chartData.nodeC.length - 1] || 0) + 1);
    }
    
    if (chart) {
        chart.data.labels = chartData.labels;
        chart.data.datasets[0].data = chartData.nodeA;
        chart.data.datasets[1].data = chartData.nodeB;
        chart.data.datasets[2].data = chartData.nodeC;
        chart.update('none'); // Update without animation for better performance
    }
}

// Initialize Chart.js
function initChart() {
    const ctx = document.getElementById('messageChart');
    if (!ctx) return;
    
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        // Load Chart.js from CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
        script.onload = function() {
            createChart(ctx);
        };
        document.head.appendChild(script);
    } else {
        createChart(ctx);
    }
}

function createChart(ctx) {
    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: 'Node A',
                    data: chartData.nodeA,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Node B',
                    data: chartData.nodeB,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'Node C',
                    data: chartData.nodeC,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Message Count Over Time'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            animation: false
        }
    });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('wsStatus');
    if (connected) {
        statusEl.textContent = 'Connected';
        statusEl.className = 'connection-status connected';
    } else {
        statusEl.textContent = 'Disconnected';
        statusEl.className = 'connection-status disconnected';
    }
}

// Start uptime counter
function startUptimeCounter() {
    setInterval(() => {
        const uptimeSeconds = Math.floor((Date.now() - uptimeStart) / 1000);
        document.getElementById('statsUptime').textContent = formatDuration(uptimeSeconds);
    }, 1000);
}

// Utility functions
function formatTimestamp(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

// Log to console for debugging
console.log('Dashboard.js loaded successfully');
