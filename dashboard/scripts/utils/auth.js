const API_BASE = '/auth';

export const auth = {
    async login(username, password) {
        const res = await fetch(`${API_BASE}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!res.ok) throw new Error('Authentication failed');
        const data = await res.json();
        this.setToken(data.access_token);
        this.setRole(data.role);
        return data;
    },

    async guest() {
        const res = await fetch(`${API_BASE}/guest`, { method: 'POST' });
        if (!res.ok) throw new Error('Guest session failed');
        const data = await res.json();
        this.setToken(data.access_token);
        this.setRole(data.role);
        return data;
    },

    setToken(token) {
        localStorage.setItem('gnp_token', token);
    },

    setRole(role) {
        localStorage.setItem('gnp_role', role);
    },

    getToken() {
        return localStorage.getItem('gnp_token');
    },

    getRole() {
        return localStorage.getItem('gnp_role');
    },

    logout() {
        localStorage.removeItem('gnp_token');
        localStorage.removeItem('gnp_role');
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    async getMe() {
        const token = this.getToken();
        if (!token) return null;
        const res = await fetch(`${API_BASE}/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            this.logout();
            return null;
        }
        return res.json();
    }
};
