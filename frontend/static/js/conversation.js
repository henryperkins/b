class ConversationManager {
    constructor(authManager) {
        this.authManager = authManager;
        this.currentConversation = null;
        this.folders = new Map();
        this.tags = new Map();
        this.conversations = new Map();
        
        this.initializeUI();
        this.loadFolders();
        this.loadTags();
    }

    async initializeUI() {
        this.sidebar = document.getElementById('conversation-sidebar');
        this.conversationList = document.getElementById('conversation-list');
        this.folderList = document.getElementById('folder-list');
        this.tagList = document.getElementById('tag-list');
        
        this.setupEventListeners();
        await this.loadConversations();
    }

    setupEventListeners() {
        // New conversation button
        document.getElementById('new-conversation-btn').addEventListener('click', 
            () => this.createNewConversation());

        // New folder button
        document.getElementById('new-folder-btn').addEventListener('click', 
            () => this.showNewFolderDialog());

        // New tag button
        document.getElementById('new-tag-btn').addEventListener('click', 
            () => this.showNewTagDialog());

        // Search input
        document.getElementById('conversation-search').addEventListener('input', 
            debounce((e) => this.searchConversations(e.target.value), 300));
    }

    async loadConversations(params = {}) {
        try {
            const queryParams = new URLSearchParams(params).toString();
            const response = await fetch(`/api/conversations?${queryParams}`, {
                headers: {
                    'Authorization': `Bearer ${this.authManager.tokens.access_token}`
                }
            });
            
            if (!response.ok) throw new Error('Failed to load conversations');
            
            const conversations = await response.json();
            this.conversations.clear();
            conversations.forEach(conv => this.conversations.set(conv.id, conv));
            
            this.renderConversationList();
        } catch (error) {
            console.error('Error loading conversations:', error);
            showError('Failed to load conversations');
        }
    }

    async createNewConversation() {
        const dialog = document.createElement('div');
        dialog.className = 'dialog';
        dialog.innerHTML = `
            <div class="dialog-content">
                <h2>New Conversation</h2>
                <form id="new-conversation-form">
                    <input type="text" name="title" placeholder="Conversation Title" required>
                    <textarea name="description" placeholder="Description (optional)"></textarea>
                    <select name="folder_id">
                        <option value="">No Folder</option>
                        ${Array.from(this.folders.values()).map(folder => 
                            `<option value="${folder.id}">${folder.name}</option>`
                        ).join('')}
                    </select>
                    <div class="tag-selection">
                        ${Array.from(this.tags.values()).map(tag => `
                            <label>
                                <input type="checkbox" name="tags" value="${tag.id}">
                                <span class="tag" style="background-color: ${tag.color}">${tag.name}</span>
                            </label>
                        `).join('')}
                    </div>
                    <div class="dialog-buttons">
                        <button type="submit">Create</button>
                        <button type="button" onclick="this.closest('.dialog').remove()">Cancel</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(dialog);

        dialog.querySelector('form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            
            try {
                const response = await fetch('/api/conversations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${this.authManager.tokens.access_token}`
                    },
                    body: JSON.stringify({
                        title: formData.get('title'),
                        description: formData.get('description'),
                        folder_id: formData.get('folder_id'),
                        tags: Array.from(formData.getAll('tags'))
                    })
                });

                if (!response.ok) throw new