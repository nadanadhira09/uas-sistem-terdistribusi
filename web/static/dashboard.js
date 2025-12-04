// Dashboard JavaScript (Improved Version) - Real-time WebSocket Updates with Dynamic Nodes

let ws = null;
let messageChart = null;
let latencyChart = null;
let uptimeStart = Date.now();

// Data tracking
let chartData = {
    labels: [],
    messages: [],
    latencies: []
};

// Event tracking
let eventLog = [];
let countdownInterval = null;
let nodeStates = {
    nodeA: { online: false, crashed: false },
    nodeB: { online: false, backupMode: false },
    nodeC: { online: false, attacking: false }
};

// Add event to timeline
function addEventToTimeline(icon, title, description, type = 'online') {
    const timeline = document.getElementById('eventTimeline');
    
    // Remove "waiting" message if exists
    if (timeline.querySelector('div[style*="text-align: center"]')) {
        timeline.innerHTML = '';
    }
    
    const eventItem = document.createElement('div');
    eventItem.className = `event-item ${type}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    eventItem.innerHTML = `
        <div class="event-icon">${icon}</div>
        <div class="event-content">
            <div class="event-title">${title}</div>
            <div class="event-desc">${description}</div>
        </div>
        <div class="event-time">${timestamp}</div>
    `;
    
    // Insert at the beginning
    timeline.insertBefore(eventItem, timeline.firstChild);
    
    // Keep only last 20 events
    eventLog.push({ icon, title, description, type, timestamp });
    if (eventLog.length > 20) {
        eventLog.shift();
        if (timeline.children.length > 20) {
            timeline.removeChild(timeline.lastChild);
        }
    }
}

// Clear event log
function clearEventLog() {
    const timeline = document.getElementById('eventTimeline');
    timeline.innerHTML = `
        <div style="text-align: center; color: #9ca3af; padding: 20px;">
            <p>🕐 Waiting for events...</p>
            <p style="font-size: 12px; margin-top: 5px;">System events will appear here</p>
        </div>
    `;
    eventLog = [];
}

// Start countdown timer for Node A recovery
function startRecoveryCountdown(seconds = 15) {
    let remaining = seconds;
    
    // Clear any existing countdown
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }
    
    // Add countdown event
    const countdownDiv = document.createElement('div');
    countdownDiv.id = 'recoveryCountdown';
    countdownDiv.className = 'event-item recovery';
    countdownDiv.innerHTML = `
        <div class="event-icon">⏱️</div>
        <div class="event-content">
            <div class="event-title">Node A Auto-Recovery in Progress</div>
            <div class="event-desc">
                Recovery countdown: <span class="countdown-timer" id="countdownValue">${remaining}s</span>
            </div>
        </div>
        <div class="event-time">${new Date().toLocaleTimeString()}</div>
    `;
    
    const timeline = document.getElementById('eventTimeline');
    if (timeline.querySelector('div[style*="text-align: center"]')) {
        timeline.innerHTML = '';
    }
    timeline.insertBefore(countdownDiv, timeline.firstChild);
    
    // Update countdown every second
    countdownInterval = setInterval(() => {
        remaining--;
        const countdownValue = document.getElementById('countdownValue');
        if (countdownValue) {
            countdownValue.textContent = `${remaining}s`;
        }
        
        if (remaining <= 0) {
            clearInterval(countdownInterval);
            const countdownElement = document.getElementById('recoveryCountdown');
            if (countdownElement) {
                countdownElement.remove();
            }
        }
    }, 1000);
}

// Show data sync progress
function showDataSyncProgress(totalMessages, synced = 0) {
    const syncDiv = document.createElement('div');
    syncDiv.id = 'dataSyncProgress';
    syncDiv.className = 'event-item sync';
    
    const percentage = totalMessages > 0 ? Math.round((synced / totalMessages) * 100) : 0;
    
    syncDiv.innerHTML = `
        <div class="event-icon">📤</div>
        <div class="event-content">
            <div class="event-title">Data Sync in Progress</div>
            <div class="event-desc">
                Transferring buffered data from Node B to Node A: ${synced}/${totalMessages} messages
                <div class="sync-progress">
                    <div class="sync-progress-bar" style="width: ${percentage}%">
                        ${percentage}%
                    </div>
                </div>
            </div>
        </div>
        <div class="event-time">${new Date().toLocaleTimeString()}</div>
    `;
    
    const timeline = document.getElementById('eventTimeline');
    
    // Remove old sync progress if exists
    const oldSync = document.getElementById('dataSyncProgress');
    if (oldSync) {
        oldSync.remove();
    }
    
    if (timeline.querySelector('div[style*="text-align: center"]')) {
        timeline.innerHTML = '';
    }
    timeline.insertBefore(syncDiv, timeline.firstChild);
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('📊 Improved Dashboard loaded');
    initWebSocket();
    initCharts();
    startUptimeCounter();
});

// WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log('🔌 Connecting to WebSocket:', wsUrl);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('✅ WebSocket connected');
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
            console.error('❌ Error parsing WebSocket message:', e);
        }
    };
    
    ws.onerror = function(error) {
        console.error('❌ WebSocket error:', error);
        updateConnectionStatus(false);
    };
    
    ws.onclose = function() {
        console.log('🔌 WebSocket disconnected');
        updateConnectionStatus(false);
        
        // Reconnect after 3 seconds
        setTimeout(() => {
            console.log('🔄 Attempting to reconnect...');
            initWebSocket();
        }, 3000);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    if (data.type === 'initial_data') {
        console.log('📥 Received initial data');
        updateDashboard(data.dashboard_data);
    } else if (data.type === 'mqtt_update') {
        updateDashboard(data.dashboard_data);
        updateCharts(data.dashboard_data);
    }
}

// Update entire dashboard
function updateDashboard(dashboardData) {
    // Track events from node updates
    trackNodeEvents(dashboardData.nodes);
    
    // Update system-wide failover alert first
    updateSystemFailoverAlert(dashboardData);
    
    updateSystemMetrics(dashboardData.system_metrics);
    updateCommunicationFlow(dashboardData.system_metrics.communication_flow);
    updateAttackResilience(dashboardData.attack_resilience);
    updateNodes(dashboardData.nodes);
}

// Track node events and add to timeline
function trackNodeEvents(nodes) {
    // Track Node A events
    if (nodes.nodeA) {
        const nodeA = nodes.nodeA;
        
        // Node A came online
        if (!nodeStates.nodeA.online && nodeA.status !== 'offline' && nodeA.status !== 'unknown') {
            nodeStates.nodeA.online = true;
            addEventToTimeline('✅', 'Node A Online', 'Primary sensor is now active and sending data', 'online');
        }
        
        // Node A crashed
        if (!nodeStates.nodeA.crashed && (nodeA.event === 'CRASHED' || nodeA.is_primary_active === false)) {
            nodeStates.nodeA.crashed = true;
            nodeStates.nodeA.online = false;
            addEventToTimeline('💥', 'Node A Down!', 'Primary sensor has crashed! Backup system should activate.', 'offline');
            startRecoveryCountdown(15);
        }
        
        // Node A recovered
        if (nodeStates.nodeA.crashed && (nodeA.event === 'RECOVERY_COMPLETE' || (nodeA.is_primary_active === true && nodeA.status !== 'offline'))) {
            nodeStates.nodeA.crashed = false;
            nodeStates.nodeA.online = true;
            addEventToTimeline('🎉', 'Node A Recovered!', 'Primary sensor is back online and operational', 'recovery');
            
            // Stop countdown
            if (countdownInterval) {
                clearInterval(countdownInterval);
                const countdownElement = document.getElementById('recoveryCountdown');
                if (countdownElement) {
                    countdownElement.remove();
                }
            }
        }
    }
    
    // Track Node B events
    if (nodes.nodeB) {
        const nodeB = nodes.nodeB;
        
        // Node B came online
        if (!nodeStates.nodeB.online && nodeB.status !== 'offline' && nodeB.status !== 'unknown') {
            nodeStates.nodeB.online = true;
            addEventToTimeline('✅', 'Node B Online', 'Backup sensor / Edge processor is ready', 'online');
        }
        
        // Node B entered backup mode
        if (!nodeStates.nodeB.backupMode && nodeB.is_backup_mode === true) {
            nodeStates.nodeB.backupMode = true;
            addEventToTimeline('🛡️', 'Node B Backup Activated!', 'Node B is now operating as primary sensor backup', 'backup');
        }
        
        // Node B exited backup mode (data sync)
        if (nodeStates.nodeB.backupMode && nodeB.is_backup_mode === false) {
            nodeStates.nodeB.backupMode = false;
            
            // Check if buffer size is available
            const bufferSize = nodeB.buffer_size || nodeB.data_count || 0;
            if (bufferSize > 0) {
                showDataSyncProgress(bufferSize, bufferSize);
                setTimeout(() => {
                    const syncElement = document.getElementById('dataSyncProgress');
                    if (syncElement) {
                        syncElement.remove();
                    }
                    addEventToTimeline('✅', 'Data Sync Complete', `Successfully transferred ${bufferSize} messages to Node A`, 'sync');
                }, 2000);
            }
            
            addEventToTimeline('🔙', 'Node B Normal Mode', 'Node B returned to edge computing operations', 'recovery');
        }
    }
    
    // Track Node C events
    if (nodes.nodeC) {
        const nodeC = nodes.nodeC;
        
        // Node C came online
        if (!nodeStates.nodeC.online && nodeC.status !== 'offline' && nodeC.status !== 'unknown') {
            nodeStates.nodeC.online = true;
            addEventToTimeline('✅', 'Node C Online', 'Attack simulation node is ready', 'online');
        }
        
        // Node C started attacking
        if (!nodeStates.nodeC.attacking && nodeC.status === 'attacking') {
            nodeStates.nodeC.attacking = true;
            addEventToTimeline('⚔️', 'Attack Started!', `Node C is sending ${nodeC.attack_rate || '10,000'} messages/sec to test system resilience`, 'attack');
        }
        
        // Node C stopped attacking
        if (nodeStates.nodeC.attacking && nodeC.status !== 'attacking') {
            nodeStates.nodeC.attacking = false;
            addEventToTimeline('🛑', 'Attack Stopped', 'Node C has stopped the attack simulation', 'recovery');
        }
    }
}

// Update system metrics
function updateSystemMetrics(metrics) {
    document.getElementById('totalMessages').textContent = formatNumber(metrics.total_messages_received || 0);
    document.getElementById('messagesPerSec').textContent = formatNumber(metrics.messages_per_second || 0);
    document.getElementById('avgLatency').textContent = (metrics.avg_system_latency || 0).toFixed(1) + 'ms';
}

// Update communication flow
function updateCommunicationFlow(flow) {
    document.getElementById('brokerAMessages').textContent = formatNumber(flow.broker_a_messages || 0);
    document.getElementById('brokerBMessages').textContent = formatNumber(flow.broker_b_messages || 0);
    document.getElementById('totalThroughput').textContent = formatNumber(flow.total_throughput || 0);
}

// Update attack resilience
function updateAttackResilience(resilience) {
    document.getElementById('attacksHandled').textContent = formatNumber(resilience.attacks_handled || 0);
}

// Update nodes dynamically
function updateNodes(nodes) {
    const nodesGrid = document.getElementById('nodesGrid');
    const activeCount = Object.values(nodes).filter(n => n.status !== 'unknown' && n.status !== 'offline').length;
    document.getElementById('activeNodes').textContent = activeCount;
    
    // Clear existing nodes
    nodesGrid.innerHTML = '';
    
    // Add each node
    Object.entries(nodes).forEach(([nodeId, nodeData]) => {
        const nodeCard = createNodeCard(nodeId, nodeData);
        nodesGrid.appendChild(nodeCard);
    });
}

// Create node card dynamically
function createNodeCard(nodeId, nodeData) {
    const card = document.createElement('div');
    card.className = 'card';
    card.id = `node-${nodeId}`;
    
    // Add visual class based on node state
    if (nodeData.event === 'CRASHED' || nodeData.is_primary_active === false) {
        card.classList.add('node-offline');
    } else if (nodeData.is_backup_mode === true) {
        card.classList.add('node-backup');
    } else if (nodeData.status === 'attacking') {
        card.classList.add('node-attacking');
    } else if (nodeData.status !== 'offline' && nodeData.status !== 'unknown') {
        card.classList.add('node-online');
    }
    
    const icon = getNodeIcon(nodeData.type);
    const statusClass = getStatusClass(nodeData.status);
    
    let metricsHTML = '';
    
    // Determine metrics based on node type
    if (nodeData.type === 'sensor') {
        // Check if Node A is crashed (from status message)
        if (nodeData.event === 'CRASHED' || nodeData.is_primary_active === false) {
            dataPreviewHTML = `
                <div class="alert-box danger" style="background: #fee2e2; border-left: 6px solid #dc2626; animation: pulseAlert 1.5s infinite; padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 48px;">💥</span>
                        <div style="flex: 1;">
                            <strong style="color: #991b1b; font-size: 20px; display: block; margin-bottom: 8px;">
                                ⚠️ PRIMARY SENSOR CRASHED!
                            </strong>
                            <div style="color: #7f1d1d; font-size: 14px; line-height: 1.6;">
                                <div>❌ <strong>Status:</strong> Node A is DOWN and disconnected</div>
                                <div>🔄 <strong>Failover:</strong> Node B activated as backup sensor</div>
                                <div>⏳ <strong>Recovery:</strong> Auto-recovery in progress (15 seconds)</div>
                                <div>📊 <strong>Messages:</strong> This node STOPPED sending (count frozen)</div>
                                <div>🛡️ <strong>System:</strong> Node B continues sending → Zero data loss!</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        // Check if Node A recovered
        else if (nodeData.event === 'RECOVERY_COMPLETE' || (nodeData.is_primary_active === true && nodeData.event === 'connected' && nodeData.failover_count > 0)) {
            dataPreviewHTML = `
                <div class="alert-box info" style="background: #dbeafe; border-left: 6px solid #3b82f6; padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 48px;">✅</span>
                        <div style="flex: 1;">
                            <strong style="color: #1e40af; font-size: 20px; display: block; margin-bottom: 8px;">
                                🎉 PRIMARY SENSOR RECOVERED!
                            </strong>
                            <div style="color: #1e3a8a; font-size: 14px; line-height: 1.6;">
                                <div>✅ <strong>Status:</strong> Node A is back ONLINE</div>
                                <div>📡 <strong>Connection:</strong> Reconnected to Broker A</div>
                                <div>📤 <strong>Data Sync:</strong> Receiving buffered data from Node B</div>
                                <div>🔙 <strong>Next:</strong> Node B returning to edge computing mode</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        // Failover to Broker B
        else if (nodeData.broker === 'B' && nodeData.failover_count > 0) {
            dataPreviewHTML = `
                <div class="alert-box warning" style="background: #fef3c7; border-left: 6px solid #f59e0b; padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 48px;">⚠️</span>
                        <div style="flex: 1;">
                            <strong style="color: #92400e; font-size: 18px; display: block; margin-bottom: 8px;">
                                🔄 FAILOVER ACTIVE
                            </strong>
                            <div style="color: #78350f; font-size: 14px; line-height: 1.6;">
                                <div>⚠️ <strong>Current Broker:</strong> Switched to Broker B (Backup)</div>
                                <div>📊 <strong>Failover Count:</strong> ${nodeData.failover_count} event(s)</div>
                                <div>✅ <strong>Status:</strong> Operating normally on backup broker</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        metricsHTML = `
            <div class="metric-row" style="background: ${nodeData.is_primary_active === false ? '#fee2e2' : 'transparent'}; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                <span class="metric-key" style="font-weight: 700;">🔌 Node Status</span>
                <span class="metric-val ${nodeData.is_primary_active === false ? 'danger' : 'success'}" style="font-size: 20px; font-weight: 700;">
                    ${nodeData.is_primary_active === false ? '💥 CRASHED' : '✅ ACTIVE'}
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Current Broker</span>
                <span class="metric-val ${nodeData.broker === 'B' ? 'warning' : 'success'}" style="font-size: 16px; font-weight: 600;">
                    ${nodeData.broker === 'B' ? '⚠️ Broker B (BACKUP)' : '✓ Broker A (PRIMARY)'}
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Connection State</span>
                <span class="metric-val ${nodeData.is_primary_active === false ? 'danger' : 'success'}">
                    ${nodeData.is_primary_active === false ? '❌ Disconnected' : '✅ Connected'}
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Failover Events</span>
                <span class="metric-val ${nodeData.failover_count > 0 ? 'warning' : ''} highlight">${nodeData.failover_count || 0}</span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Self-Healing Count</span>
                <span class="metric-val">${nodeData.reconnect_count || 0}</span>
            </div>
            ${nodeData.is_primary_active === false ? `
            <div class="metric-row" style="background: #fee2e2; padding: 10px; border-radius: 8px; margin-top: 8px;">
                <span class="metric-key" style="color: #991b1b; font-weight: 700;">⏳ Downtime Status</span>
                <span class="metric-val danger" style="font-weight: 700;">RECOVERY IN PROGRESS</span>
            </div>
            ` : ''}
            ${nodeData.recovery_metrics && nodeData.recovery_metrics.avg_recovery_time > 0 ? `
            <div class="metric-row">
                <span class="metric-key">Avg Recovery Time</span>
                <span class="metric-val success">${nodeData.recovery_metrics.avg_recovery_time}s</span>
            </div>
            ` : ''}
            ${nodeData.metrics ? `
            <div class="metric-row">
                <span class="metric-key">Message Success Rate</span>
                <span class="metric-val ${nodeData.metrics.success_rate >= 90 ? 'success' : 'warning'}">
                    ${(nodeData.metrics.success_rate || 100).toFixed(1)}%
                </span>
            </div>
            ` : ''}
        `;
    } else if (nodeData.type === 'edge') {
        // Add visual alert for backup mode
        if (nodeData.is_backup_mode) {
            dataPreviewHTML = `
                <div class="alert-box warning" style="background: #fef3c7; border-left: 6px solid #f59e0b; padding: 20px; animation: pulseAlert 2s infinite;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 48px;">🛡️</span>
                        <div style="flex: 1;">
                            <strong style="color: #92400e; font-size: 20px; display: block; margin-bottom: 8px;">
                                🔄 BACKUP MODE ACTIVATED!
                            </strong>
                            <div style="color: #78350f; font-size: 14px; line-height: 1.6;">
                                <div>🚨 <strong>Reason:</strong> Node A (Primary) is DOWN</div>
                                <div>✅ <strong>Role:</strong> Acting as PRIMARY sensor (backup)</div>
                                <div>📦 <strong>Data Buffer:</strong> ${nodeData.buffer_size || 0} messages stored for sync</div>
                                <div>🔄 <strong>Action:</strong> Collecting data until Node A recovers</div>
                                <div>📊 <strong>Next:</strong> Will sync all data to Node A after recovery</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        // Check for data sync event
        else if (nodeData.event === 'data_sync') {
            dataPreviewHTML = `
                <div class="alert-box info" style="background: #dbeafe; border-left: 6px solid #3b82f6; padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 48px;">📤</span>
                        <div style="flex: 1;">
                            <strong style="color: #1e40af; font-size: 20px; display: block; margin-bottom: 8px;">
                                📡 DATA SYNC IN PROGRESS
                            </strong>
                            <div style="color: #1e3a8a; font-size: 14px; line-height: 1.6;">
                                <div>📤 <strong>Transferring:</strong> ${nodeData.data_count || 0} buffered messages</div>
                                <div>📍 <strong>Destination:</strong> Node A (Primary sensor)</div>
                                <div>✅ <strong>Status:</strong> Sync operation active</div>
                                <div>🔙 <strong>Next:</strong> Return to edge computing mode</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        // Backup deactivated
        else if (nodeData.event === 'backup_deactivated') {
            dataPreviewHTML = `
                <div class="alert-box info" style="background: #d1fae5; border-left: 6px solid #10b981; padding: 20px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <span style="font-size: 48px;">✅</span>
                        <div style="flex: 1;">
                            <strong style="color: #065f46; font-size: 20px; display: block; margin-bottom: 8px;">
                                🔙 RETURNING TO NORMAL MODE
                            </strong>
                            <div style="color: #047857; font-size: 14px; line-height: 1.6;">
                                <div>✅ <strong>Node A:</strong> Primary sensor recovered</div>
                                <div>📤 <strong>Data Sync:</strong> Completed successfully</div>
                                <div>🔧 <strong>Mode:</strong> Back to edge computing</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        metricsHTML = `
            <div class="metric-row" style="background: ${nodeData.is_backup_mode ? '#fef3c7' : 'transparent'}; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                <span class="metric-key" style="font-weight: 700;">⚙️ Operation Mode</span>
                <span class="metric-val ${nodeData.is_backup_mode ? 'warning' : 'success'}" style="font-size: 20px; font-weight: 700;">
                    ${nodeData.is_backup_mode ? '🛡️ BACKUP SENSOR' : '🔧 EDGE COMPUTING'}
                </span>
            </div>
            <div class="metric-row" style="background: ${nodeData.node_a_status === 'crashed' ? '#fee2e2' : '#d1fae5'}; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                <span class="metric-key" style="font-weight: 700;">📡 Primary Node Status</span>
                <span class="metric-val ${nodeData.node_a_status === 'crashed' ? 'danger' : 'success'}" style="font-size: 18px; font-weight: 700;">
                    ${nodeData.node_a_status === 'crashed' ? '💥 NODE A CRASHED' : '✅ NODE A ACTIVE'}
                </span>
            </div>
            ${nodeData.is_backup_mode ? `
            <div class="metric-row" style="background: #fef3c7; padding: 10px; border-radius: 8px; margin-bottom: 8px;">
                <span class="metric-key" style="font-weight: 700;">📦 Buffered Messages</span>
                <span class="metric-val warning" style="font-size: 24px; font-weight: 700;">${nodeData.buffer_size || 0}</span>
            </div>
            <div class="metric-row">
                <span class="metric-key">🔄 Backup Role</span>
                <span class="metric-val warning">Acting as Primary Sensor</span>
            </div>
            <div class="metric-row">
                <span class="metric-key">📊 Data Collection</span>
                <span class="metric-val warning">Active (storing for sync)</span>
            </div>
            ` : ''}
            ${!nodeData.is_backup_mode ? `
            <div class="metric-row">
                <span class="metric-key">🔧 Edge Decisions</span>
                <span class="metric-val highlight">${nodeData.offline_decisions || 0}</span>
            </div>
            ` : ''}
            ${nodeData.metrics ? `
            <div class="metric-row">
                <span class="metric-key">Avg Latency</span>
                <span class="metric-val">${(nodeData.metrics.avg_latency * 1000 || 0).toFixed(1)}ms</span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Success Rate</span>
                <span class="metric-val ${nodeData.metrics.delivery_success_rate >= 90 ? 'success' : 'warning'}">
                    ${(nodeData.metrics.delivery_success_rate || 100).toFixed(1)}%
                </span>
            </div>
            ` : ''}
        `;
    } else if (nodeData.type === 'attacker') {
        // Extract duration from various sources
        const duration = nodeData.attack_duration || 
                        nodeData.details?.duration || 
                        (nodeData.attack_metrics?.duration) || 
                        0;
        
        const totalMessages = nodeData.total_messages || 
                             nodeData.attack_metrics?.messages_sent || 
                             0;
        
        const successRate = nodeData.attack_metrics?.success_rate || 0;
        
        const attackRate = nodeData.messages_per_second || 0;
        
        metricsHTML = `
            <div class="metric-row">
                <span class="metric-key">Attack Duration</span>
                <span class="metric-val highlight">${duration}s</span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Messages Sent</span>
                <span class="metric-val">${formatNumber(totalMessages)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Success Rate</span>
                <span class="metric-val ${successRate >= 90 ? 'success' : 'warning'}">
                    ${successRate.toFixed(1)}%
                </span>
            </div>
            <div class="metric-row">
                <span class="metric-key">Attack Rate</span>
                <span class="metric-val">${formatNumber(attackRate)} msg/s</span>
            </div>
        `;
    }
    
    // Build data preview
    let dataPreviewHTML = '';
    if (nodeData.latest_data && Object.keys(nodeData.latest_data).length > 0) {
        if (nodeData.type === 'sensor') {
            dataPreviewHTML = `
                <div class="data-preview">
                    <strong>Latest Sensor Data:</strong><br>
                    Temperature: ${nodeData.latest_data.temperature || '-'}°C<br>
                    Humidity: ${nodeData.latest_data.humidity || '-'}%<br>
                    Pressure: ${nodeData.latest_data.pressure || '-'} hPa
                </div>
            `;
        } else if (nodeData.type === 'edge' && nodeData.latest_data.decision) {
            const priorityClass = nodeData.latest_data.priority === 'high' ? 'danger' : 
                                 nodeData.latest_data.priority === 'medium' ? 'warning' : 'info';
            dataPreviewHTML = `
                <div class="alert-box ${priorityClass}">
                    <span>⚡</span>
                    <div>
                        <strong>Decision:</strong> ${nodeData.latest_data.decision}<br>
                        <small>Action: ${nodeData.latest_data.action || 'none'}</small>
                    </div>
                </div>
            `;
        }
    }
    
    // Determine big status indicator
    let bigStatusHTML = '';
    if (nodeData.event === 'CRASHED' || nodeData.is_primary_active === false) {
        bigStatusHTML = `
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border-radius: 12px; margin-bottom: 20px; border: 3px solid #dc2626;">
                <div style="font-size: 64px; margin-bottom: 10px;">💥</div>
                <div style="font-size: 24px; font-weight: 700; color: #991b1b; margin-bottom: 5px;">NODE DOWN</div>
                <div style="font-size: 14px; color: #7f1d1d;">Primary sensor crashed</div>
            </div>
        `;
    } else if (nodeData.is_backup_mode === true) {
        bigStatusHTML = `
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border-radius: 12px; margin-bottom: 20px; border: 3px solid #f59e0b;">
                <div style="font-size: 64px; margin-bottom: 10px;">🛡️</div>
                <div style="font-size: 24px; font-weight: 700; color: #92400e; margin-bottom: 5px;">BACKUP MODE</div>
                <div style="font-size: 14px; color: #78350f;">Operating as primary sensor</div>
            </div>
        `;
    } else if (nodeData.status === 'attacking') {
        bigStatusHTML = `
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #fca5a5 0%, #f87171 100%); border-radius: 12px; margin-bottom: 20px; border: 3px solid #dc2626; animation: pulseAttack 1s infinite;">
                <div style="font-size: 64px; margin-bottom: 10px;">⚔️</div>
                <div style="font-size: 24px; font-weight: 700; color: #7f1d1d; margin-bottom: 5px;">ATTACKING</div>
                <div style="font-size: 14px; color: #991b1b;">${nodeData.attack_rate || '10,000'} msg/s</div>
            </div>
        `;
    } else if (nodeData.status !== 'offline' && nodeData.status !== 'unknown') {
        bigStatusHTML = `
            <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border-radius: 12px; margin-bottom: 20px; border: 3px solid #10b981;">
                <div style="font-size: 64px; margin-bottom: 10px;">✅</div>
                <div style="font-size: 24px; font-weight: 700; color: #065f46; margin-bottom: 5px;">ONLINE</div>
                <div style="font-size: 14px; color: #047857;">System operational</div>
            </div>
        `;
    }
    
    card.innerHTML = `
        ${bigStatusHTML}
        
        <div class="card-header">
            <span class="card-title">${icon} ${nodeId.toUpperCase()}</span>
            <span class="status-badge ${statusClass}">${(nodeData.status || 'unknown').toUpperCase()}</span>
        </div>
        
        <div class="metric-grid">
            ${metricsHTML}
            ${nodeData.type !== 'attacker' ? `
            <div class="metric-row" style="${nodeData.event === 'CRASHED' || nodeData.is_primary_active === false ? 'background: #fee2e2; padding: 10px; border-radius: 8px;' : ''}">
                <span class="metric-key">${nodeData.event === 'CRASHED' || nodeData.is_primary_active === false ? '📛 Messages (FROZEN)' : 'Messages'}</span>
                <span class="metric-val ${nodeData.event === 'CRASHED' || nodeData.is_primary_active === false ? 'danger' : ''}" style="font-size: 18px; font-weight: 700;">
                    ${nodeData.data_count || 0}
                    ${nodeData.event === 'CRASHED' || nodeData.is_primary_active === false ? ' ⛔' : ''}
                </span>
            </div>
            ${nodeData.is_backup_mode === true ? `
            <div class="metric-row" style="background: #fef3c7; padding: 10px; border-radius: 8px; margin-top: 8px;">
                <span class="metric-key" style="color: #92400e; font-weight: 700;">🚀 Backup Messages</span>
                <span class="metric-val warning" style="font-size: 18px; font-weight: 700;">
                    ${nodeData.data_count || 0} ⬆️
                </span>
            </div>
            ` : ''}
            ` : ''}
            <div class="metric-row">
                <span class="metric-key">Last Update</span>
                <span class="metric-val timestamp">${formatTimestamp(nodeData.last_update)}</span>
            </div>
        </div>
        
        ${dataPreviewHTML}
        
        ${nodeData.metrics?.success_rate ? `
        <div class="progress-bar">
            <div class="progress-fill" style="width: ${nodeData.metrics.success_rate}%"></div>
        </div>
        ` : ''}
    `;
    
    return card;
}

// Get node icon based on type
function getNodeIcon(type) {
    switch(type) {
        case 'sensor': return '📡';
        case 'edge': return '🔧';
        case 'attacker': return '⚔️';
        default: return '📦';
    }
}

// Get status class
function getStatusClass(status) {
    if (!status || status === 'unknown') return 'offline';
    if (status === 'attacking') return 'attacking';
    if (status === 'connected' || status === 'online' || status === 'heartbeat') return 'online';
    if (status === 'failover' || status === 'self_healing') return 'error';
    return 'offline';
}

// Initialize Charts
function initCharts() {
    // Message rate chart
    const ctx1 = document.getElementById('messageChart');
    if (ctx1) {
        messageChart = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Messages/Second',
                    data: chartData.messages,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    title: { display: true, text: 'Message Rate Over Time' }
                },
                scales: {
                    y: { beginAtZero: true }
                },
                animation: { duration: 0 }
            }
        });
    }
    
    // Latency chart
    const ctx2 = document.getElementById('latencyChart');
    if (ctx2) {
        latencyChart = new Chart(ctx2, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Latency (ms)',
                    data: chartData.latencies,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true, position: 'top' },
                    title: { display: true, text: 'System Latency Over Time' }
                },
                scales: {
                    y: { beginAtZero: true }
                },
                animation: { duration: 0 }
            }
        });
    }
}

// Update charts
function updateCharts(dashboardData) {
    const now = new Date().toLocaleTimeString();
    
    // Keep only last 30 data points
    if (chartData.labels.length >= 30) {
        chartData.labels.shift();
        chartData.messages.shift();
        chartData.latencies.shift();
    }
    
    chartData.labels.push(now);
    chartData.messages.push(dashboardData.system_metrics?.messages_per_second || 0);
    chartData.latencies.push(dashboardData.system_metrics?.avg_system_latency || 0);
    
    if (messageChart) {
        messageChart.data.labels = chartData.labels;
        messageChart.data.datasets[0].data = chartData.messages;
        messageChart.update('none');
    }
    
    if (latencyChart) {
        latencyChart.data.labels = chartData.labels;
        latencyChart.data.datasets[0].data = chartData.latencies;
        latencyChart.update('none');
    }
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
        document.getElementById('systemUptime').textContent = formatDuration(uptimeSeconds);
    }, 1000);
}

// Utility functions
function formatTimestamp(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function formatNumber(num) {
    // Return number with comma separators (e.g., 98,659 instead of 98.7K)
    return num.toLocaleString('en-US');
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${secs}s`;
    return `${secs}s`;
}

// Update system-wide failover alert
function updateSystemFailoverAlert(data) {
    const alertDiv = document.getElementById('systemFailoverAlert');
    if (!alertDiv || !data.nodes) return;
    
    // Check for Node A crash
    const nodeA = data.nodes['A'];
    const nodeB = data.nodes['B'];
    
    if (nodeA && nodeA.is_primary_active === false) {
        // Node A is crashed - show critical alert
        alertDiv.style.display = 'block';
        alertDiv.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); border: 3px solid #dc2626; box-shadow: 0 8px 32px rgba(220, 38, 38, 0.3);">
                <div style="padding: 25px;">
                    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
                        <span style="font-size: 64px;">🚨</span>
                        <div style="flex: 1;">
                            <h2 style="margin: 0; color: #991b1b; font-size: 28px; font-weight: 800;">
                                ⚠️ SYSTEM FAILOVER ACTIVATED
                            </h2>
                            <p style="margin: 8px 0 0 0; color: #7f1d1d; font-size: 16px; font-weight: 600;">
                                Critical: Primary sensor failure detected • Backup system engaged
                            </p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; background: white; padding: 20px; border-radius: 12px; box-shadow: inset 0 2px 8px rgba(0,0,0,0.1);">
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Primary Sensor (Node A)</div>
                            <div style="font-size: 20px; font-weight: 700; color: #dc2626;">💥 CRASHED</div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Backup Sensor (Node B)</div>
                            <div style="font-size: 20px; font-weight: 700; color: #f59e0b;">
                                ${nodeB && nodeB.is_backup_mode ? '🛡️ ACTIVE' : '⏳ ACTIVATING...'}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Buffered Data</div>
                            <div style="font-size: 20px; font-weight: 700; color: #3b82f6;">
                                ${nodeB && nodeB.buffer_size !== undefined ? nodeB.buffer_size : 0} messages
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Recovery Status</div>
                            <div style="font-size: 20px; font-weight: 700; color: #f59e0b;">⏳ IN PROGRESS</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else if (nodeA && nodeA.event === 'RECOVERY_COMPLETE' && nodeA.is_primary_active === true) {
        // Node A recovered - show success alert
        alertDiv.style.display = 'block';
        alertDiv.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); border: 3px solid #10b981; box-shadow: 0 8px 32px rgba(16, 185, 129, 0.3);">
                <div style="padding: 25px;">
                    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
                        <span style="font-size: 64px;">✅</span>
                        <div style="flex: 1;">
                            <h2 style="margin: 0; color: #065f46; font-size: 28px; font-weight: 800;">
                                🎉 SYSTEM RECOVERED SUCCESSFULLY
                            </h2>
                            <p style="margin: 8px 0 0 0; color: #047857; font-size: 16px; font-weight: 600;">
                                Primary sensor restored • Data sync in progress • Normal operations resuming
                            </p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; background: white; padding: 20px; border-radius: 12px;">
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Primary Sensor (Node A)</div>
                            <div style="font-size: 20px; font-weight: 700; color: #10b981;">✅ ONLINE</div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Backup Sensor (Node B)</div>
                            <div style="font-size: 20px; font-weight: 700; color: #3b82f6;">
                                ${nodeB && nodeB.event === 'data_sync' ? '📤 SYNCING DATA' : '🔙 RETURNING TO EDGE MODE'}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Data Synced</div>
                            <div style="font-size: 20px; font-weight: 700; color: #10b981;">
                                ${nodeB && nodeB.data_count ? nodeB.data_count : '0'} messages
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">System Status</div>
                            <div style="font-size: 20px; font-weight: 700; color: #10b981;">✅ NORMAL</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Auto-hide success message after 10 seconds
        setTimeout(() => {
            if (alertDiv && nodeA.is_primary_active === true) {
                alertDiv.style.display = 'none';
            }
        }, 10000);
    } else if (nodeB && nodeB.is_backup_mode) {
        // Backup mode active - show warning alert
        alertDiv.style.display = 'block';
        alertDiv.innerHTML = `
            <div class="card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); border: 3px solid #f59e0b; box-shadow: 0 8px 32px rgba(245, 158, 11, 0.3);">
                <div style="padding: 25px;">
                    <div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
                        <span style="font-size: 64px;">🛡️</span>
                        <div style="flex: 1;">
                            <h2 style="margin: 0; color: #92400e; font-size: 28px; font-weight: 800;">
                                🔄 BACKUP MODE OPERATING
                            </h2>
                            <p style="margin: 8px 0 0 0; color: #78350f; font-size: 16px; font-weight: 600;">
                                Node B is currently acting as primary sensor • Collecting data for sync
                            </p>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; background: white; padding: 20px; border-radius: 12px;">
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Primary Sensor (Node A)</div>
                            <div style="font-size: 20px; font-weight: 700; color: #dc2626;">
                                ${nodeA && nodeA.is_primary_active === false ? '💥 DOWN' : '⏳ RECOVERING...'}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Backup Sensor (Node B)</div>
                            <div style="font-size: 20px; font-weight: 700; color: #f59e0b;">🛡️ ACTIVE</div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Buffered Messages</div>
                            <div style="font-size: 24px; font-weight: 800; color: #3b82f6;">
                                ${nodeB.buffer_size || 0}
                            </div>
                        </div>
                        <div>
                            <div style="font-size: 12px; color: #6b7280; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Data Collection</div>
                            <div style="font-size: 20px; font-weight: 700; color: #10b981;">✅ ACTIVE</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } else {
        // Normal operation - hide alert
        alertDiv.style.display = 'none';
    }
}

// Log to console
console.log('✅ Improved Dashboard.js loaded successfully');
console.log('📊 Features: Dynamic Nodes, Advanced Metrics, Real-time Charts, System-wide Failover Alerts');

