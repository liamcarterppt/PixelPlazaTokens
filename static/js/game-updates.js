/**
 * Game Updates Module
 * Provides functions to update the game UI without refreshing the page
 */

// Function to update UI elements with new game state (no page reload needed)
function updateGameStateUI(gameState, transactions, tasks) {
    console.log('Updating game state UI with:', gameState);
    
    // Update token display
    const tokenDisplay = document.getElementById('token-display');
    if (tokenDisplay) {
        tokenDisplay.textContent = gameState.token_balance.toFixed(2);
        tokenDisplay.classList.add('pulse');
        setTimeout(() => {
            tokenDisplay.classList.remove('pulse');
        }, 1000);
    }
    
    // Update resource bars
    const energyBar = document.querySelector('.resource-bar.energy .progress-bar');
    const pixelsBar = document.querySelector('.resource-bar.pixels .progress-bar');
    if (energyBar) {
        const energyPercent = Math.min(100, Math.max(0, gameState.energy));
        energyBar.style.width = `${energyPercent}%`;
        energyBar.setAttribute('aria-valuenow', energyPercent);
        const energyValue = document.getElementById('energy-value');
        if (energyValue) energyValue.textContent = gameState.energy;
    }
    
    if (pixelsBar) {
        const pixelsPercent = Math.min(100, gameState.pixels / 10);
        pixelsBar.style.width = `${pixelsPercent}%`;
        pixelsBar.setAttribute('aria-valuenow', pixelsPercent);
        const pixelsValue = document.getElementById('pixels-value');
        if (pixelsValue) pixelsValue.textContent = gameState.pixels;
    }
    
    // Update experience/level
    const levelDisplay = document.getElementById('level-display');
    const xpBar = document.querySelector('.resource-bar.xp .progress-bar');
    if (levelDisplay) {
        levelDisplay.textContent = gameState.level;
    }
    
    if (xpBar) {
        const xpNeeded = gameState.level * 100; // Simplified XP calculation
        const xpPercent = Math.min(100, (gameState.experience / xpNeeded) * 100);
        xpBar.style.width = `${xpPercent}%`;
        xpBar.setAttribute('aria-valuenow', xpPercent);
        const xpValue = document.getElementById('xp-value');
        if (xpValue) xpValue.textContent = `${gameState.experience}/${xpNeeded}`;
    }
    
    // Update stats
    const buildingsDisplay = document.getElementById('buildings-stat');
    const pixelArtDisplay = document.getElementById('pixel-art-stat');
    const streakDisplay = document.getElementById('streak-stat');
    const referralsDisplay = document.getElementById('referrals-stat');
    
    if (buildingsDisplay) buildingsDisplay.textContent = gameState.buildings_owned;
    if (pixelArtDisplay) pixelArtDisplay.textContent = gameState.pixel_art_created;
    if (streakDisplay) streakDisplay.textContent = gameState.daily_streak;
    if (referralsDisplay) referralsDisplay.textContent = gameState.referral_count;
    
    // Update transactions
    updateTransactions(transactions);
    
    // Update tasks
    updateTasks(tasks);
}

// Helper function to update transactions list
function updateTransactions(transactions) {
    const container = document.getElementById('transactions-container');
    if (!container || !transactions || transactions.length === 0) return;
    
    // Clear existing transactions
    container.innerHTML = '';
    
    // Add new transactions with animation
    transactions.forEach((tx, index) => {
        const txElement = document.createElement('div');
        txElement.className = `transaction-item ${tx.amount >= 0 ? 'income' : 'expense'} ${index === 0 ? 'new' : ''}`;
        
        txElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <span class="transaction-title fw-semibold">${tx.description}</span>
                    <div class="text-muted small">${formatTimestamp(tx.timestamp)}</div>
                </div>
                <div class="transaction-amount ${tx.amount >= 0 ? 'text-success' : 'text-danger'} fw-bold">
                    ${tx.amount >= 0 ? '+' : ''}${tx.amount.toFixed(2)} $PXPT
                </div>
            </div>
        `;
        
        container.appendChild(txElement);
    });
}

// Helper function to update tasks list
function updateTasks(tasks) {
    const container = document.getElementById('tasks-preview');
    if (!container || !tasks || tasks.length === 0) return;
    
    // Clear existing tasks
    container.innerHTML = '';
    
    // Add only incomplete tasks with animation
    let taskCount = 0;
    for (const task of tasks) {
        if (taskCount >= 3) break; // Only show 3 tasks in preview
        
        // Skip completed tasks
        if (task.completed) continue;
        
        const progress = Math.min(100, (task.current_progress / task.objective_value) * 100);
        
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item mb-3';
        
        taskElement.innerHTML = `
            <div class="d-flex justify-content-between align-items-center mb-1">
                <span class="task-name fw-semibold">${task.name}</span>
                <span class="task-progress small">${task.current_progress}/${task.objective_value}</span>
            </div>
            <div class="progress" style="height: 6px;">
                <div class="progress-bar bg-info" role="progressbar" style="width: ${progress}%" 
                     aria-valuenow="${progress}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
            <div class="task-reward mt-1 small text-success">
                Reward: +${task.token_reward} $PXPT
                ${task.pixel_reward > 0 ? ` +${task.pixel_reward} pixels` : ''}
                ${task.experience_reward > 0 ? ` +${task.experience_reward} XP` : ''}
            </div>
        `;
        
        container.appendChild(taskElement);
        taskCount++;
    }
    
    // If no incomplete tasks, show a message
    if (taskCount === 0) {
        container.innerHTML = '<div class="text-center text-muted py-3">No active tasks. Check back later!</div>';
    }
}

// Helper function to format timestamps
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}