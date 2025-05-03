// Main JavaScript for Pixel Plaza Token Game

// Show toasts if available
document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize all popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                window.scrollTo({
                    top: target.offsetTop - 70, // Account for fixed navbar
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Initialize mini-games if the container exists
    if (document.getElementById('mini-games-container')) {
        miniGame.loadAvailableGames();
    }
    
    // Add loading indicators to all action buttons
    document.querySelectorAll('.btn[data-action]').forEach(button => {
        // Store original click event to prevent multiple handlers
        const originalClickEvent = button.onclick;
        
        // Replace with new handler that shows loading state
        button.onclick = function(e) {
            if (!button.disabled) {
                const originalContent = button.innerHTML;
                button.innerHTML = '<span class="loading-indicator me-2"></span> Processing...';
                button.disabled = true;
                
                // Execute original handler after a short delay for UX
                setTimeout(() => {
                    if (originalClickEvent) {
                        originalClickEvent.call(this, e);
                    }
                    
                    // Reset button state after a timeout in case the action fails
                    setTimeout(() => {
                        if (button.innerHTML.includes('loading-indicator')) {
                            button.innerHTML = originalContent;
                            button.disabled = false;
                        }
                    }, 5000);
                }, 200);
            }
            return false;
        };
    });
    
    // Enhanced animations when elements come into view with support for delay
    const animateOnScroll = () => {
        const elements = document.querySelectorAll('.animate-on-scroll');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight;
            
            if (elementPosition < screenPosition - 50) { // Apply a small offset for earlier animation trigger
                // Check if element is already animated
                if (!element.classList.contains('animate__animated')) {
                    // Add animation classes
                    element.classList.add('animate__animated', element.dataset.animation || 'animate__fadeIn');
                    
                    // Apply delay if specified
                    if (element.dataset.delay) {
                        element.style.animationDelay = `${element.dataset.delay}ms`;
                    }
                    
                    // Apply duration if specified
                    if (element.dataset.duration) {
                        element.style.animationDuration = `${element.dataset.duration}ms`;
                    }
                }
            }
        });
    };
    
    // Run once on load and then on scroll with throttling for performance
    let scrollTimeout;
    window.addEventListener('scroll', () => {
        if (!scrollTimeout) {
            scrollTimeout = setTimeout(() => {
                animateOnScroll();
                scrollTimeout = null;
            }, 10); // Throttle to every 10ms
        }
    });
    
    // Initial animation on page load
    animateOnScroll();
    
    // Animate number counters
    const animateCounters = () => {
        const counters = document.querySelectorAll('.counter');
        
        counters.forEach(counter => {
            // Get target number from text content
            const target = parseInt(counter.textContent, 10);
            
            // Reset counter content for animation
            counter.textContent = '0';
            
            // Create animation function
            const updateCounter = () => {
                const current = parseInt(counter.textContent, 10);
                
                // Calculate increment (faster for larger numbers)
                const increment = Math.ceil(target / 30);
                
                // If current is less than target, increment
                if (current < target) {
                    counter.textContent = Math.min(current + increment, target);
                    setTimeout(updateCounter, 50);
                }
            };
            
            // Start animation when element is in view
            const observer = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting) {
                    updateCounter();
                    observer.unobserve(counter);
                }
            }, { threshold: 0.5 });
            
            observer.observe(counter);
        });
    };
    
    // Initialize counter animations
    animateCounters();
});

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1,');
}

// Countdown timer function
function startCountdown(endDate, elementId) {
    const countdownElement = document.getElementById(elementId);
    if (!countdownElement) return;
    
    const interval = setInterval(() => {
        const now = new Date().getTime();
        const distance = new Date(endDate).getTime() - now;
        
        if (distance < 0) {
            clearInterval(interval);
            countdownElement.innerHTML = "Expired";
            return;
        }
        
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);
        
        countdownElement.innerHTML = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }, 1000);
}

// Mini-game functionality
const miniGame = {
    // Load available mini-games
    loadAvailableGames: function() {
        fetch('/api/mini-games/available')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.renderGamesList(data.games);
                } else {
                    showMessage(data.message || 'Failed to load mini-games', 'danger');
                }
            })
            .catch(error => {
                console.error('Error loading mini-games:', error);
                showMessage('An error occurred while loading mini-games', 'danger');
            });
    },
    
    // Render the list of available games
    renderGamesList: function(games) {
        const container = document.getElementById('mini-games-container');
        if (!container) return;
        
        // Clear container
        container.innerHTML = '';
        
        if (games.length === 0) {
            container.innerHTML = '<div class="alert alert-info">No mini-games available at the moment. Check back later!</div>';
            return;
        }
        
        // Create game cards with enhanced styling for mobile
        const row = document.createElement('div');
        row.className = 'row g-3';
        
        games.forEach(game => {
            const cooldownText = game.cooldown_remaining ? 
                `Available in ${this.formatCooldown(game.cooldown_remaining)}` : 
                'Available Now';
                
            const cooldownClass = game.cooldown_remaining ? 'text-warning' : 'text-success';
                
            const col = document.createElement('div');
            col.className = 'col-12 col-md-6 col-lg-4';
            
            col.innerHTML = `
                <div class="card mini-game-card h-100 ${game.cooldown_remaining ? 'disabled' : ''}">
                    <div class="card-header bg-primary bg-opacity-75 text-white">
                        <h5 class="card-title mb-0">
                            <i class="fas fa-gamepad me-2"></i>${game.name}
                        </h5>
                    </div>
                    <div class="card-body">
                        <p class="card-text">${game.description}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <span class="badge bg-info">
                                <i class="fas fa-star me-1"></i>Rewards: ${game.rewards_text}
                            </span>
                            <span class="${cooldownClass}">
                                <i class="fas fa-clock me-1"></i>${cooldownText}
                            </span>
                        </div>
                    </div>
                    <div class="card-footer bg-dark bg-opacity-25">
                        <button 
                            class="btn btn-primary w-100" 
                            onclick="miniGame.playGame('${game.type}')"
                            ${game.cooldown_remaining ? 'disabled' : ''}>
                            <i class="fas fa-play me-2"></i>Play Game
                        </button>
                    </div>
                </div>
            `;
            
            row.appendChild(col);
        });
        
        container.appendChild(row);
    },
    
    // Format cooldown time
    formatCooldown: function(seconds) {
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
        return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
    },
    
    // Play a mini-game
    playGame: function(gameType) {
        // Show loading state
        const gameContainer = document.getElementById('mini-games-container');
        if (gameContainer) {
            gameContainer.innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h5>Loading ${this.getGameName(gameType)}...</h5>
                </div>
            `;
        }
        
        // For demonstration, we'll use a timeout to simulate game loading
        // In a real implementation, we would load the game UI and logic here
        setTimeout(() => {
            // This is a placeholder for actual game implementation
            // Each game type would have its own UI and gameplay logic
            switch(gameType) {
                case 'pixel_match':
                    this.startPixelMatchGame();
                    break;
                case 'token_puzzle':
                    this.startTokenPuzzleGame();
                    break;
                case 'resource_rush':
                    this.startResourceRushGame();
                    break;
                case 'gem_hunter':
                    this.startGemHunterGame();
                    break;
                case 'pattern_predictor':
                    this.startPatternPredictorGame();
                    break;
                default:
                    gameContainer.innerHTML = '<div class="alert alert-danger">Unknown game type</div>';
            }
        }, 1000);
    },
    
    // Get display name for a game type
    getGameName: function(gameType) {
        const names = {
            'pixel_match': 'Pixel Matching',
            'token_puzzle': 'Token Puzzle',
            'resource_rush': 'Resource Rush',
            'gem_hunter': 'Gem Hunter',
            'pattern_predictor': 'Pattern Predictor'
        };
        return names[gameType] || 'Mini-Game';
    },
    
    // Submit game result to server
    submitGameResult: function(gameType, gameData) {
        const requestOptions = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                game_type: gameType,
                game_data: gameData
            })
        };
        
        fetch('/api/mini-games/play', requestOptions)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showGameResultModal(data);
                    
                    // Update game state if provided
                    if (data.game_state) {
                        updateGameStateUI(data.game_state, data.transactions, data.tasks);
                    }
                    
                    // Reload games list after a short delay
                    setTimeout(() => this.loadAvailableGames(), 2000);
                } else {
                    showMessage(data.message || 'Game submission failed', 'danger');
                }
            })
            .catch(error => {
                console.error('Error submitting game result:', error);
                showMessage('An error occurred while submitting game result', 'danger');
            });
    },
    
    // Show game result in a modal
    showGameResultModal: function(result) {
        // Create or find result modal
        let modal = document.getElementById('game-result-modal');
        if (!modal) {
            const modalHtml = `
                <div class="modal fade" id="game-result-modal" tabindex="-1" aria-labelledby="gameResultModalLabel" aria-hidden="true">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content">
                            <div class="modal-header bg-success text-white">
                                <h5 class="modal-title" id="gameResultModalLabel">Game Complete!</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body" id="game-result-content"></div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                <button type="button" class="btn btn-primary" data-bs-dismiss="modal" onclick="miniGame.loadAvailableGames()">Play Another</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            const modalContainer = document.createElement('div');
            modalContainer.innerHTML = modalHtml;
            document.body.appendChild(modalContainer.firstChild);
            modal = document.getElementById('game-result-modal');
        }
        
        // Set result content
        const contentElement = document.getElementById('game-result-content');
        if (contentElement) {
            let rewardsHtml = '';
            
            if (result.rewards) {
                rewardsHtml = `
                    <div class="mt-4">
                        <h5>Rewards Earned:</h5>
                        <ul class="list-group mini-game-reward">
                            ${result.rewards.tokens ? `<li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>Tokens</span>
                                <span class="badge bg-success rounded-pill">+${result.rewards.tokens} $PXPT</span>
                            </li>` : ''}
                            ${result.rewards.pixels ? `<li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>Pixels</span>
                                <span class="badge bg-info rounded-pill">+${result.rewards.pixels} pixels</span>
                            </li>` : ''}
                            ${result.rewards.xp ? `<li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>Experience</span>
                                <span class="badge bg-primary rounded-pill">+${result.rewards.xp} XP</span>
                            </li>` : ''}
                            ${result.rewards.materials ? `<li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>Materials</span>
                                <span class="badge bg-warning rounded-pill">+${result.rewards.materials} materials</span>
                            </li>` : ''}
                            ${result.rewards.gems ? `<li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>Gems</span>
                                <span class="badge bg-danger rounded-pill">+${result.rewards.gems} gems</span>
                            </li>` : ''}
                        </ul>
                    </div>
                `;
            }
            
            contentElement.innerHTML = `
                <div class="text-center mb-4">
                    <div class="display-1 mb-3">🎮</div>
                    <h4>${result.message || 'Game Completed Successfully!'}</h4>
                    <p>Score: <strong>${result.score || 0}</strong></p>
                </div>
                ${rewardsHtml}
            `;
        }
        
        // Show the modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    },
    
    // Placeholder functions for individual games
    // In a real implementation, these would contain the actual game logic
    startPixelMatchGame: function() {
        // Placeholder for Pixel Match game implementation
        // For now, just submit a placeholder result
        this.submitGameResult('pixel_match', { player_choices: [0, 3, 5, 6] });
    },
    
    startTokenPuzzleGame: function() {
        // Placeholder for Token Puzzle game implementation
        this.submitGameResult('token_puzzle', { player_solution: [1, 2, 3, 4, 5, 6, 7, 8, 9] });
    },
    
    startResourceRushGame: function() {
        // Placeholder for Resource Rush game implementation
        this.submitGameResult('resource_rush', { resources_collected: { pixels: 15, materials: 8 } });
    },
    
    startGemHunterGame: function() {
        // Placeholder for Gem Hunter game implementation
        this.submitGameResult('gem_hunter', { selected_cells: [[0, 1], [2, 3], [1, 2]] });
    },
    
    startPatternPredictorGame: function() {
        // Placeholder for Pattern Predictor game implementation
        this.submitGameResult('pattern_predictor', { player_answer: 5 });
    }
};
