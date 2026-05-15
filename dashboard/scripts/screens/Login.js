import { auth } from '../utils/auth.js';

export function mountLogin(container, onLogin) {
    container.innerHTML = `
        <div class="login-screen torn-wrapper">
            <div class="login-card torn-container">
                <div class="card-header">
                    <span class="stamp">SECURITY CLEARANCE REQUIRED</span>
                    <h1 class="vintage-title">Global News Pulse</h1>
                </div>
                
                <div class="login-body">
                    <div id="loginError" class="error-msg hidden">Invalid credentials. Access denied.</div>
                    
                    <div class="input-group">
                        <label for="username">Operator ID</label>
                        <input type="text" id="username" placeholder="Username" autocomplete="username">
                    </div>
                    
                    <div class="input-group">
                        <label for="password">Access Code</label>
                        <input type="password" id="password" placeholder="••••••••" autocomplete="current-password">
                    </div>
                    
                    <button id="loginBtn" class="btn-stamp primary-btn">AUTHORIZE ACCESS</button>
                    
                    <div class="divider">OR</div>
                    
                    <button id="guestBtn" class="btn-stamp secondary-btn">GUEST ACCESS (READ-ONLY)</button>
                </div>
                
                <div class="card-footer">
                    <p class="small italic">Warning: All access is logged and monitored. Unauthorised entry attempt will trigger a lockdown.</p>
                </div>
            </div>
        </div>
    `;

    const loginBtn = container.querySelector('#loginBtn');
    const guestBtn = container.querySelector('#guestBtn');
    const usernameInput = container.querySelector('#username');
    const passwordInput = container.querySelector('#password');
    const errorMsg = container.querySelector('#loginError');

    const handleLogin = async () => {
        try {
            loginBtn.innerText = 'AUTHORIZING...';
            await auth.login(usernameInput.value, passwordInput.value);
            onLogin();
        } catch (err) {
            errorMsg.classList.remove('hidden');
            loginBtn.innerText = 'AUTHORIZE ACCESS';
        }
    };

    const handleGuest = async () => {
        try {
            guestBtn.innerText = 'REQUESTING...';
            await auth.guest();
            onLogin();
        } catch (err) {
            errorMsg.innerText = 'Guest system offline.';
            errorMsg.classList.remove('hidden');
            guestBtn.innerText = 'GUEST ACCESS (READ-ONLY)';
        }
    };

    loginBtn.addEventListener('click', handleLogin);
    guestBtn.addEventListener('click', handleGuest);
    
    // Allow enter key
    passwordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleLogin();
    });
}

export function unmountLogin() {
    // No cleanup
}
