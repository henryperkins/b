// frontend/static/js/main.js

class ConversationExporter {
    static async exportToJSON(conversationId) {
        const response = await fetch(`/api/conversations/${conversationId}/export`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], 
            { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${conversationId}.json`;
        a.click();
    }

    static async exportToPDF(conversationId) {
        const content = await this.getConversationContent(conversationId);
        const pdf = await html2pdf().from(content).save();
    }
}
class MarkdownRenderer {
    constructor() {
        this.marked.setOptions({
            highlight: (code, lang) => {
                if (lang && hljs.getLanguage(lang)) {
                    return hljs.highlight(code, { language: lang }).value;
                }
                return hljs.highlightAuto(code).value;
            },
            breaks: true
        });
    }

    render(text) {
        return this.marked(text);
    }
}
class ChatApp {
    constructor(authManager) {
        this.authManager = authManager;
        this.setupAuthenticatedApp();
    }

    async setupAuthenticatedApp() {
        if (!this.authManager.tokens) {
            document.getElementById('chat-container').style.display = 'none';
            document.getElementById('auth-container').style.display = 'block';
            return;
        }

        try {
            await this.authManager.fetchUserProfile();
            this.initializeChat();
        } catch (error) {
            console.error('Failed to initialize authenticated app:', error);
            this.authManager.clearTokens();
            location.reload();
        }
    }

    initializeChat() {
        document.getElementById('auth-container').style.display = 'none';
        document.getElementById('chat-container').style.display = 'block';
        
        // Initialize WebSocket with authentication
        this.initializeWebSocket();
    }

    initializeWebSocket() {
        const wsUrl = `ws://localhost:8000/ws/chat/${this.conversationId}`;
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            // Send authentication message
            this.ws.send(JSON.stringify({
                type: 'authenticate',
                token: this.authManager.tokens.access_token
            }));
        };

        // Add other WebSocket handlers...
    }
}

// Initialize auth and chat
const authManager = new AuthManager();
const authForms = new AuthForms(authManager);
const chatApp = new ChatApp(authManager);