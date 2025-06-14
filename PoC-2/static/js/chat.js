// AI Multi-Agent Chat Support System - Frontend JavaScript

class ChatApp {
    constructor() {
        this.sessionId = null;
        this.isProcessing = false;
        this.messageCounter = 0;
        
        this.initializeApp();
        this.setupEventListeners();
        this.generateSessionId();
        this.checkAgentStatus();
    }
    
    initializeApp() {
        // Initialize UI elements
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.chatContainer = document.getElementById('chatContainer');
        this.sessionIdDisplay = document.getElementById('sessionId');
        this.currentAgentDisplay = document.getElementById('currentAgent');
        this.lastIntentDisplay = document.getElementById('lastIntent');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.messageCounterDisplay = document.getElementById('messageCounter');
        
        // Focus on input
        this.messageInput.focus();
    }
    
    setupEventListeners() {
        // Message input handlers
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.messageInput.addEventListener('input', () => {
            this.updateMessageCounter();
        });
        
        // Send button
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Window resize handler
        window.addEventListener('resize', () => {
            this.scrollToBottom();
        });
    }
    
    generateSessionId() {
        this.sessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        this.sessionIdDisplay.textContent = this.sessionId;
    }
    
    updateMessageCounter() {
        const length = this.messageInput.value.length;
        this.messageCounterDisplay.textContent = `${length}/1000 characters`;
        
        if (length > 900) {
            this.messageCounterDisplay.className = 'text-warning';
        } else if (length > 950) {
            this.messageCounterDisplay.className = 'text-danger';
        } else {
            this.messageCounterDisplay.className = 'text-muted';
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isProcessing) {
            return;
        }
        
        // Disable input during processing
        this.setProcessingState(true);
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Clear input
        this.messageInput.value = '';
        this.updateMessageCounter();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Prepare request data
            const requestData = {
                message: message,
                session_id: this.sessionId,
                customer_email: document.getElementById('customerEmail').value || null,
                customer_phone: document.getElementById('customerPhone').value || null
            };
            
            // Send request to API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add bot response to chat
            this.addMessage(data.response, 'bot', {
                agent: data.agent_type,
                intent: data.intent,
                ticketNumber: data.ticket_number
            });
            
            // Update UI with agent info
            this.updateAgentInfo(data.agent_type, data.intent);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            this.addMessage(
                'Sorry, I encountered an error processing your request. Please try again.',
                'bot',
                { agent: 'System', intent: 'error' }
            );
        } finally {
            this.setProcessingState(false);
            this.messageInput.focus();
        }
    }
    
    addMessage(text, sender, metadata = {}) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const headerDiv = document.createElement('div');
        headerDiv.className = 'message-header';
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        
        if (sender === 'user') {
            headerDiv.innerHTML = `
                <strong>You</strong>
                <small class="text-muted">${this.formatTime(new Date())}</small>
            `;
            textDiv.textContent = text;
        } else {
            const agentName = this.getAgentDisplayName(metadata.agent);
            const intentBadge = metadata.intent ? this.createIntentBadge(metadata.intent) : '';
            
            headerDiv.innerHTML = `
                <div>
                    <strong>${agentName}</strong>
                    ${intentBadge}
                </div>
                <small class="text-muted">${this.formatTime(new Date())}</small>
            `;
            
            // Handle markdown-like formatting
            textDiv.innerHTML = this.formatBotMessage(text);
            
            // Add ticket number if available
            if (metadata.ticketNumber) {
                const ticketDiv = document.createElement('div');
                ticketDiv.className = 'mt-2 p-2 bg-light border-start border-primary border-3';
                ticketDiv.innerHTML = `<small><strong>Ticket Created:</strong> ${metadata.ticketNumber}</small>`;
                textDiv.appendChild(ticketDiv);
            }
        }
        
        contentDiv.appendChild(headerDiv);
        contentDiv.appendChild(textDiv);
        messageDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatBotMessage(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>')
            .replace(/•/g, '&bull;');
    }
    
    getAgentDisplayName(agent) {
        const agentNames = {
            'FAQAgent': 'FAQ Assistant',
            'TicketAgent': 'Support Specialist',
            'AccountAgent': 'Account Assistant',
            'System': 'System'
        };
        return agentNames[agent] || 'AI Assistant';
    }
    
    createIntentBadge(intent) {
        const intentClasses = {
            'faq': 'intent-faq',
            'complaint': 'intent-complaint',
            'account_inquiry': 'intent-account',
            'general': 'intent-general'
        };
        
        const intentLabels = {
            'faq': 'FAQ',
            'complaint': 'Complaint',
            'account_inquiry': 'Account',
            'general': 'General'
        };
        
        const className = intentClasses[intent] || 'intent-general';
        const label = intentLabels[intent] || intent;
        
        return `<span class="badge ${className} badge-intent ms-2">${label}</span>`;
    }
    
    showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'typingIndicatorMessage';
        typingDiv.className = 'message bot-message';
        typingDiv.innerHTML = `
            <div class="typing-indicator">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
                <span class="ms-2 text-muted">AI is thinking...</span>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicatorMessage');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }
    
    setProcessingState(processing) {
        this.isProcessing = processing;
        this.sendButton.disabled = processing;
        this.messageInput.disabled = processing;
        
        if (processing) {
            this.sendButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.typingIndicator.classList.remove('d-none');
        } else {
            this.sendButton.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.typingIndicator.classList.add('d-none');
        }
    }
    
    updateAgentInfo(agent, intent) {
        this.currentAgentDisplay.textContent = this.getAgentDisplayName(agent);
        this.lastIntentDisplay.textContent = intent ? intent.replace('_', ' ').toUpperCase() : '-';
    }
    
    async checkAgentStatus() {
        try {
            const response = await fetch('/api/agent-status');
            const data = await response.json();
            
            this.updateAgentStatusDisplay(data);
            
        } catch (error) {
            console.error('Error checking agent status:', error);
            this.updateAgentStatusDisplay({ system_status: 'error' });
        }
    }
    
    updateAgentStatusDisplay(statusData) {
        const statusContainer = document.getElementById('agentStatus');
        
        if (statusData.system_status === 'operational') {
            const agents = statusData.agents;
            let statusHtml = '';
            
            Object.keys(agents).forEach(agentKey => {
                const agent = agents[agentKey];
                const displayName = this.getAgentDisplayName(agentKey);
                const statusIcon = agent.status === 'active' ? 'text-success' : 'text-danger';
                
                statusHtml += `
                    <div class="agent-status-item">
                        <i class="fas fa-circle ${statusIcon}"></i>
                        <small>${displayName}</small>
                    </div>
                `;
            });
            
            // Add notification capabilities
            if (agents.notify_agent && agents.notify_agent.capabilities) {
                const caps = agents.notify_agent.capabilities;
                statusHtml += '<hr class="my-2">';
                statusHtml += '<div class="mb-1"><small class="text-muted">Notifications:</small></div>';
                
                Object.keys(caps).forEach(capKey => {
                    const enabled = caps[capKey];
                    const statusIcon = enabled ? 'text-success' : 'text-muted';
                    statusHtml += `
                        <div class="agent-status-item">
                            <i class="fas fa-${capKey === 'email' ? 'envelope' : 'sms'} ${statusIcon}"></i>
                            <small class="${enabled ? '' : 'text-muted'}">${capKey.toUpperCase()}</small>
                        </div>
                    `;
                });
            }
            
            statusContainer.innerHTML = statusHtml;
        } else {
            statusContainer.innerHTML = `
                <div class="agent-status-item">
                    <i class="fas fa-circle text-danger"></i>
                    <small>System Error</small>
                </div>
            `;
        }
    }
    
    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }
    
    formatTime(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            this.chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-content">
                        <div class="message-header">
                            <strong>AI Support Assistant</strong>
                            <small class="text-muted">System</small>
                        </div>
                        <div class="message-text">
                            Chat cleared. How can I help you today?
                        </div>
                    </div>
                </div>
            `;
            this.generateSessionId();
        }
    }
}

// Intent classification test functionality
async function testIntentClassification() {
    const modal = new bootstrap.Modal(document.getElementById('intentModal'));
    modal.show();
}

async function classifyTestIntent() {
    const testMessage = document.getElementById('testMessage').value.trim();
    const resultDiv = document.getElementById('intentResult');
    
    if (!testMessage) {
        alert('Please enter a message to test');
        return;
    }
    
    try {
        const response = await fetch('/api/classify-intent', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: testMessage })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        document.getElementById('detectedIntent').textContent = data.intent;
        document.getElementById('intentConfidence').textContent = `${(data.confidence * 100).toFixed(1)}%`;
        document.getElementById('intentReasoning').textContent = data.reasoning || 'No reasoning provided';
        
        resultDiv.classList.remove('d-none');
        
    } catch (error) {
        console.error('Error classifying intent:', error);
        alert('Error classifying intent. Please try again.');
    }
}

// Global functions for buttons
function clearChat() {
    if (window.chatApp) {
        window.chatApp.clearChat();
    }
}

function checkAgentStatus() {
    if (window.chatApp) {
        window.chatApp.checkAgentStatus();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatApp = new ChatApp();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && window.chatApp) {
        // Refresh agent status when page becomes visible
        setTimeout(() => {
            window.chatApp.checkAgentStatus();
        }, 1000);
    }
});
