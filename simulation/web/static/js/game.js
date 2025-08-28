// Beer Distribution Game - Frontend JavaScript

class BeerGame {
    constructor() {
        this.gameId = null;
        this.playerId = null;
        this.ws = null;
        this.chart = null;
        this.gameData = {
            weeks: [],
            inventory: {},
            costs: {},
            orders: {}
        };
        
        this.initializeEventListeners();
        this.loadScenarios();
    }

    initializeEventListeners() {
        // Setup controls
        document.getElementById('createGameBtn').addEventListener('click', () => this.createGame());
        
        // Play controls
        document.getElementById('submitOrderBtn').addEventListener('click', () => this.submitOrder());
        document.getElementById('pauseBtn').addEventListener('click', () => this.pauseGame());
        document.getElementById('resumeBtn').addEventListener('click', () => this.resumeGame());
        document.getElementById('endBtn').addEventListener('click', () => this.endGame());
        
        // Chart tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchChart(e.target.dataset.chart));
        });
        
        // Modal close
        document.querySelector('.close').addEventListener('click', () => this.closeModal());
    }

    async loadScenarios() {
        try {
            const response = await fetch('/api/scenarios');
            const data = await response.json();
            
            const select = document.getElementById('scenarioSelect');
            select.innerHTML = '';
            
            data.scenarios.forEach(scenario => {
                const option = document.createElement('option');
                option.value = scenario.id;
                option.textContent = scenario.name;
                select.appendChild(option);
            });
        } catch (error) {
            this.showMessage('Failed to load scenarios', 'error');
        }
    }

    async createGame() {
        const scenario = document.getElementById('scenarioSelect').value;
        const playerName = document.getElementById('playerName').value;
        const role = document.getElementById('roleSelect').value;
        
        if (!playerName) {
            this.showMessage('Please enter your name', 'error');
            return;
        }
        
        try {
            // Create game
            const gameResponse = await fetch('/api/games', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    scenario_id: scenario,
                    max_weeks: 52,
                    collaborative_mode: true
                })
            });
            
            if (!gameResponse.ok) {
                const errorData = await gameResponse.json();
                throw new Error(`Failed to create game: ${errorData.detail || gameResponse.statusText}`);
            }
            
            const gameData = await gameResponse.json();
            this.gameId = gameData.game_id;
            
            // Add player
            const playerResponse = await fetch(`/api/games/${this.gameId}/players`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: playerName,
                    role: role,
                    is_human: true
                })
            });
            
            if (!playerResponse.ok) {
                const errorData = await playerResponse.json();
                throw new Error(`Failed to add player: ${errorData.detail || playerResponse.statusText}`);
            }
            
            const playerData = await playerResponse.json();
            this.playerId = playerData.player_id;
            
            // Add AI players for other roles
            await this.addAIPlayers(role);
            
            // Start game
            await fetch(`/api/games/${this.gameId}/start`, {method: 'POST'});
            
            // Connect WebSocket
            this.connectWebSocket();
            
            // Update UI
            document.getElementById('gameId').textContent = this.gameId.substring(0, 8);
            document.getElementById('gameStatus').textContent = 'Running';
            document.getElementById('setupControls').style.display = 'none';
            document.getElementById('playControls').style.display = 'block';
            
            // Initialize chart
            this.initializeChart();
            
            this.showMessage('Game started successfully!', 'success');
            
        } catch (error) {
            console.error('Game creation error:', error);
            this.showMessage('Failed to create game: ' + error.message, 'error');
        }
    }

    async addAIPlayers(humanRole) {
        const roles = ['retailer', 'wholesaler', 'distributor', 'factory'];
        const policies = ['base_stock', 'forecast_based', 's_S', 'adaptive'];
        
        for (let i = 0; i < roles.length; i++) {
            if (roles[i] !== humanRole) {
                await fetch(`/api/games/${this.gameId}/players`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        name: `AI-${roles[i]}`,
                        role: roles[i],
                        is_human: false,
                        policy_type: policies[i]
                    })
                });
            }
        }
    }

    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/ws/${this.gameId}/${this.playerId}`;
        
        console.log('Connecting to WebSocket:', wsUrl);
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected successfully');
            this.showMessage('Connected to game server', 'success');
            this.ws.send(JSON.stringify({type: 'request_state'}));
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showMessage('WebSocket connection error - check console', 'error');
        };
        
        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected:', event.code, event.reason);
            if (event.code === 1006) {
                this.showMessage('WebSocket connection lost - server may be down', 'error');
            }
        };
    }

    handleWebSocketMessage(data) {
        switch(data.type) {
            case 'game_state':
                this.updateGameState(data.state);
                break;
            case 'week_complete':
                this.updateWeekData(data);
                break;
            case 'decision_request':
                this.showMessage(`Please submit your order for week ${data.week}`, 'info');
                break;
            case 'decision_confirmation':
                this.showMessage(data.message, 'success');
                break;
            case 'game_ended':
                this.handleGameEnd(data);
                break;
            case 'game_update':
                this.handleGameUpdate(data);
                break;
        }
    }

    updateGameState(state) {
        // Update week counter
        document.getElementById('currentWeek').textContent = state.current_week;
        document.getElementById('gameStatus').textContent = state.status;
        
        // Update metrics
        if (state.metrics) {
            document.getElementById('totalCost').textContent = `$${state.metrics.total_cost.toFixed(2)}`;
            document.getElementById('serviceLevel').textContent = `${(state.metrics.service_level * 100).toFixed(1)}%`;
            document.getElementById('bullwhipRatio').textContent = state.metrics.bullwhip_ratio.toFixed(2);
        }
        
        // Update node states
        if (state.nodes) {
            this.updateNodes(state.nodes);
        }
    }

    updateNodes(nodes) {
        Object.keys(nodes).forEach(nodeName => {
            const node = nodes[nodeName];
            const nodeElement = document.getElementById(`${nodeName.toLowerCase()}-node`);
            
            if (nodeElement) {
                nodeElement.querySelector('.inventory').textContent = node.inventory;
                nodeElement.querySelector('.backlog').textContent = node.backlog;
                nodeElement.querySelector('.last-order').textContent = node.last_order || 0;
            }
        });
    }

    updateWeekData(data) {
        // Store data for charts
        this.gameData.weeks.push(data.week);
        
        if (data.node_states) {
            Object.keys(data.node_states).forEach(nodeName => {
                if (!this.gameData.inventory[nodeName]) {
                    this.gameData.inventory[nodeName] = [];
                    this.gameData.costs[nodeName] = [];
                    this.gameData.orders[nodeName] = [];
                }
                
                const node = data.node_states[nodeName];
                this.gameData.inventory[nodeName].push(node.inventory);
                this.gameData.costs[nodeName].push(node.costs.total_cost);
                this.gameData.orders[nodeName].push(node.last_order || 0);
            });
        }
        
        // Update chart
        this.updateChart();
        
        // Update UI
        this.updateGameState({
            current_week: data.week,
            metrics: data.metrics,
            nodes: data.node_states
        });
    }

    async submitOrder() {
        const quantity = parseInt(document.getElementById('orderQuantity').value);
        
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'decision',
                order_quantity: quantity
            }));
        } else {
            // Fallback to REST API
            try {
                const response = await fetch(`/api/games/${this.gameId}/decisions`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        player_id: this.playerId,
                        order_quantity: quantity
                    })
                });
                
                if (response.ok) {
                    this.showMessage('Order submitted successfully', 'success');
                }
            } catch (error) {
                this.showMessage('Failed to submit order', 'error');
            }
        }
    }

    async pauseGame() {
        try {
            await fetch(`/api/games/${this.gameId}/pause`, {method: 'POST'});
            document.getElementById('pauseBtn').style.display = 'none';
            document.getElementById('resumeBtn').style.display = 'block';
            this.showMessage('Game paused', 'info');
        } catch (error) {
            this.showMessage('Failed to pause game', 'error');
        }
    }

    async resumeGame() {
        try {
            await fetch(`/api/games/${this.gameId}/resume`, {method: 'POST'});
            document.getElementById('pauseBtn').style.display = 'block';
            document.getElementById('resumeBtn').style.display = 'none';
            this.showMessage('Game resumed', 'info');
        } catch (error) {
            this.showMessage('Failed to resume game', 'error');
        }
    }

    async endGame() {
        if (confirm('Are you sure you want to end the game?')) {
            try {
                await fetch(`/api/games/${this.gameId}/stop`, {method: 'POST'});
                this.showMessage('Game ended', 'info');
            } catch (error) {
                this.showMessage('Failed to end game', 'error');
            }
        }
    }

    handleGameEnd(data) {
        // Show results modal
        const modal = document.getElementById('resultsModal');
        const content = document.getElementById('resultsContent');
        
        content.innerHTML = `
            <h3>Final Results</h3>
            <p><strong>Total Cost:</strong> $${data.results.total_cost.toFixed(2)}</p>
            <p><strong>Service Level:</strong> ${(data.results.service_level * 100).toFixed(1)}%</p>
            <p><strong>Bullwhip Ratio:</strong> ${data.results.bullwhip_ratio.toFixed(2)}</p>
            <h4>Leaderboard</h4>
            <table>
                ${data.results.leaderboard.map(player => `
                    <tr>
                        <td>${player.rank}</td>
                        <td>${player.name}</td>
                        <td>${player.score.toFixed(0)} points</td>
                    </tr>
                `).join('')}
            </table>
        `;
        
        modal.style.display = 'block';
        
        // Disconnect WebSocket
        if (this.ws) {
            this.ws.close();
        }
    }

    handleGameUpdate(data) {
        this.showMessage(`Update: ${data.update_type}`, 'info');
    }

    initializeChart() {
        const ctx = document.getElementById('chartCanvas').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        this.switchChart('inventory');
    }

    switchChart(type) {
        // Update active tab
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`.tab-btn[data-chart="${type}"]`).classList.add('active');
        
        // Update chart data
        let dataSource;
        let label;
        
        switch(type) {
            case 'inventory':
                dataSource = this.gameData.inventory;
                label = 'Inventory';
                break;
            case 'costs':
                dataSource = this.gameData.costs;
                label = 'Costs ($)';
                break;
            case 'orders':
                dataSource = this.gameData.orders;
                label = 'Orders';
                break;
        }
        
        this.updateChart(dataSource, label);
    }

    updateChart(dataSource = this.gameData.inventory, label = 'Inventory') {
        if (!this.chart) return;
        
        const colors = {
            'Factory': '#3498db',
            'Distributor': '#9b59b6',
            'Wholesaler': '#e67e22',
            'Retailer': '#2ecc71'
        };
        
        const datasets = Object.keys(dataSource).map(nodeName => ({
            label: nodeName,
            data: dataSource[nodeName],
            borderColor: colors[nodeName] || '#666',
            backgroundColor: 'transparent',
            tension: 0.1
        }));
        
        this.chart.data.labels = this.gameData.weeks;
        this.chart.data.datasets = datasets;
        this.chart.update();
    }

    showMessage(message, type = 'info') {
        const messageList = document.getElementById('messageList');
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        messageElement.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        messageList.appendChild(messageElement);
        messageList.scrollTop = messageList.scrollHeight;
    }

    closeModal() {
        document.getElementById('resultsModal').style.display = 'none';
    }
}

// Initialize game when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.game = new BeerGame();
});
