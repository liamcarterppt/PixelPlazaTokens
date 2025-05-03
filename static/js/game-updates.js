/**
 * Game Updates Module
 * Provides functions to update the game UI without refreshing the page
 * Enhanced with better async handling and visual feedback
 */

// Track pending operations to avoid multiple simultaneous requests
let pendingGameAction = false;
let lastActionTime = 0;
const ACTION_COOLDOWN = 800; // ms

// Function to update UI elements with new game state (no page reload needed)
function updateGameStateUI(gameState, transactions, tasks) {
    console.log('Updating game state UI with:', gameState);
    
    // Provide visual indication of update
    const gameContainer = document.querySelector('.game-container');
    if (gameContainer) {
        gameContainer.classList.add('action-success');
        setTimeout(() => {
            gameContainer.classList.remove('action-success');
        }, 2000);
    }
    
    // Update token display with animation
    const tokenDisplay = document.getElementById('token-display');
    if (tokenDisplay) {
        // Save old value for animation
        const oldValue = parseFloat(tokenDisplay.textContent);
        const newValue = gameState.token_balance;
        
        // Animate the change
        if (oldValue !== newValue) {
            // Add appropriate class based on value change
            if (newValue > oldValue) {
                tokenDisplay.classList.add('text-success');
                tokenDisplay.classList.add('pulse');
            } else if (newValue < oldValue) {
                tokenDisplay.classList.add('text-danger');
                tokenDisplay.classList.add('pulse');
            }
            
            // Update the text and remove classes after animation
            tokenDisplay.textContent = newValue.toFixed(2);
            setTimeout(() => {
                tokenDisplay.classList.remove('pulse');
                tokenDisplay.classList.remove('text-success');
                tokenDisplay.classList.remove('text-danger');
            }, 1500);
        } else {
            tokenDisplay.textContent = newValue.toFixed(2);
        }
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

// Enhanced game action handler with cooldown and better error handling
function performGameAction(action, params = {}) {
    // Check if another action is pending or if we're in cooldown
    const now = Date.now();
    if (pendingGameAction) {
        showMessage('Please wait until the current action completes', 'warning');
        return Promise.reject('Action already in progress');
    }
    
    if (now - lastActionTime < ACTION_COOLDOWN) {
        showMessage('Please slow down your actions', 'warning');
        return Promise.reject('Action cooldown in effect');
    }
    
    // Set action as pending and update last action time
    pendingGameAction = true;
    lastActionTime = now;
    
    // Show loading spinner for the action
    const actionButton = document.querySelector(`[data-action="${action}"]`);
    let originalButtonContent = '';
    if (actionButton) {
        originalButtonContent = actionButton.innerHTML;
        actionButton.innerHTML = '<span class="loading-indicator me-2"></span> Processing...';
        actionButton.disabled = true;
    }
    
    // Get the CSRF token if present (for POST requests)
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    // Prepare the request options
    const requestOptions = {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken || ''
        },
        body: JSON.stringify({
            action: action,
            ...params
        })
    };
    
    // Send the request to the game action endpoint
    return fetch('/api/game-action', requestOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Reset pending action status
            pendingGameAction = false;
            
            if (data.success) {
                // Update the game state UI
                updateGameStateUI(data.game_state, data.transactions, data.tasks);
                
                // Show success message if present
                if (data.message) {
                    showMessage(data.message, 'success');
                }
                
                // Show any event messages
                if (data.event_message) {
                    showEventMessage(data.event_message);
                }
                
                // Return the processed data
                return data;
            } else {
                // Show error message
                showMessage(data.message || 'Action failed', 'danger');
                throw new Error(data.message || 'Action failed');
            }
        })
        .catch(error => {
            console.error('Error performing game action:', error);
            showMessage('An error occurred. Please try again.', 'danger');
            throw error;
        })
        .finally(() => {
            // Reset button state
            if (actionButton) {
                actionButton.innerHTML = originalButtonContent;
                actionButton.disabled = false;
            }
            
            // Release the pending action after a small delay (to prevent spam clicking)
            setTimeout(() => {
                pendingGameAction = false;
            }, ACTION_COOLDOWN / 2);
        });
}

// Helper function to show messages to the user
function showMessage(message, type = 'info') {
    // Look for existing message container or create one
    let messageContainer = document.getElementById('game-message-container');
    if (!messageContainer) {
        messageContainer = document.createElement('div');
        messageContainer.id = 'game-message-container';
        messageContainer.className = 'position-fixed top-0 end-0 p-3';
        messageContainer.style.zIndex = '1050';
        document.body.appendChild(messageContainer);
    }
    
    // Create the alert element
    const alertId = `game-alert-${Date.now()}`;
    const alert = document.createElement('div');
    alert.id = alertId;
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    messageContainer.appendChild(alert);
    
    // Auto-dismiss after 4 seconds
    setTimeout(() => {
        const alertElement = document.getElementById(alertId);
        if (alertElement) {
            alertElement.classList.remove('show');
            setTimeout(() => alertElement.remove(), 150);
        }
    }, 4000);
}

// Helper function to show event messages in a more prominent way
function showEventMessage(message) {
    // Create or find event message modal
    let modal = document.getElementById('event-message-modal');
    if (!modal) {
        const modalHtml = `
            <div class="modal fade" id="event-message-modal" tabindex="-1" aria-labelledby="eventMessageModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-info text-white">
                            <h5 class="modal-title" id="eventMessageModalLabel">Special Event!</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body" id="event-message-content"></div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">Got it!</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        const modalContainer = document.createElement('div');
        modalContainer.innerHTML = modalHtml;
        document.body.appendChild(modalContainer.firstChild);
        modal = document.getElementById('event-message-modal');
    }
    
    // Set the message content
    const contentElement = document.getElementById('event-message-content');
    if (contentElement) {
        contentElement.innerHTML = message;
    }
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Document ready function to add event listeners for game actions
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all game action buttons
    const actionButtons = document.querySelectorAll('[data-action]');
    actionButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            const action = this.getAttribute('data-action');
            const params = this.dataset.params ? JSON.parse(this.dataset.params) : {};
            
            performGameAction(action, params)
                .catch(error => console.error('Error in game action:', error));
        });
    });
    
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(tooltip => {
        new bootstrap.Tooltip(tooltip);
    });
});