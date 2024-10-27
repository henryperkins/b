class AuthManager {
    constructor() {
        this.baseUrl = '/api/auth';
        this.tokens = this.loadTokens();
        this.user = null;
        this.setupAuthListeners();
    }

    loadTokens() {
        const tokens = localStorage.getItem('auth_tokens');
        return tokens ? JSON.parse(tokens) : null;
    }

    saveTokens(tokens) {
        localStorage.setItem('auth_tokens', JSON.stringify(tokens));
        this.tokens = tokens;
    }

    clearTokens() {
        localStorage.removeItem('auth_tokens');
        this.tokens = null;
        this.user = null;
    }

    async login(email, password) {
        try {
            const response = await fetch(`${this.baseUrl}/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    username: email,
                    password: password,
                }),
            });

            if (!response.ok) {
                throw new Error('Login failed');
            }

            const tokens = await response.json();
            this.saveTokens(tokens);
            await this.fetchUserProfile();
            return true;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    async register(userData) {
        try {
            const response = await fetch(`${this.baseUrl}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(userData),
            });

            if (!response.ok) {
                throw new Error('Registration failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    async refreshToken() {
        if (!this.tokens?.refresh_token) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await fetch(`${this.baseUrl}/refresh`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    refresh_token: this.tokens.refresh_token,
                }),
            });

            if (!response.ok) {
                throw new Error('Token refresh failed');
            }

            const newTokens = await response.json();
            this.saveTokens(newTokens);
            return true;
        } catch (error) {
            this.clearTokens();
            throw error;
        }
    }

    async fetchUserProfile() {
        try {
            const response = await fetch('/api/users/me', {
                headers: {
                    'Authorization': `Bearer ${this.tokens.access_token}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch user profile');
            }

            this.user = await response.json();
            return this.user;
        } catch (error) {
            console.error('Profile fetch error:', error);
            throw error;
        }
    }

    setupAuthListeners() {
        // Intercept fetch requests to handle token refresh
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                if (response.status === 401) {
                    // Token expired, try to refresh
                    const refreshed = await this.refreshToken();
                    if (refreshed) {
                        // Retry original request with new token
                        const [url, config] = args;
                        const newConfig = {
                            ...config,
                            headers: {
                                ...config?.headers,
                                'Authorization': `Bearer ${this.tokens.access_token}`,
                            },
                        };
                        return originalFetch(url, newConfig);
                    }
                }
                
                return response;
            } catch (error) {
                throw error;
            }
        };
    }
}

// Create auth forms
class AuthForms {
    constructor(authManager) {
        this.authManager = authManager;
        this.setupForms();
    }

    setupForms() {
        this.createLoginForm();
        this.createRegisterForm();
    }

    createLoginForm() {
        const form = `
            <form id="login-form" class="auth-form">
                <h2>Login</h2>
                <div class="form-group">
                    <input type="email" id="login-email" required placeholder="Email">
                </div>
                <div class="form-group">
                    <input type="password" id="login-password" required placeholder="Password">
                </div>
                <button type="submit">Login</button>
                <p class="form-switch">
                    Don't have an account? <a href="#" id="show-register">Register</a>
                </p>
            </form>
        `;
        
        document.getElementById('auth-forms').innerHTML = form;
        this.setupLoginHandlers();
    }

    createRegisterForm() {
        const form = `
            <form id="register-form" class="auth-form" style="display: none;">
                <h2>Register</h2>
                <div class="form-group">
                    <input type="text" id="register-username" required placeholder="Username">
                </div>
                <div class="form-group">
                    <input type="email" id="register-email" required placeholder="Email">
                </div>
                <div class="form-group">
                    <input type="password" id="register-password" required placeholder="Password">
                </div>
                <div class="form-group">
                    <input type="text" id="register-fullname" placeholder="Full Name (Optional)">
                </div>
                <button type="submit">Register</button>
                <p class="form-switch">
                    Already have an account? <a href="#" id="show-login">Login</a>
                </p>
            </form>
        `;
        
        document.getElementById('auth-forms').insertAdjacentHTML('beforeend', form);
        this.setupRegisterHandlers();
    }

    setupLoginHandlers() {
        // Add login form handlers
    }

    setupRegisterHandlers() {
        // Add register form handlers
    }
}