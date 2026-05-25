import { auth } from '../utils/auth.js';

export function mountLogin(container, onLogin) {
    container.innerHTML = `
        <div class="login-screen torn-wrapper">
            <div class="login-card torn-container">
                <div class="card-header">
                    <span class="stamp">SIGN IN</span>
                    <h1 class="vintage-title">Global News Pulse</h1>
                </div>
                
                <div class="login-body">
                    <div id="loginError" class="error-msg hidden">Invalid credentials. Access denied.</div>
                    
                    <div class="input-group">
                        <label for="username">Username</label>
                        <input type="text" id="username" placeholder="Username" autocomplete="username">
                    </div>
                    
                    <div class="input-group">
                        <label for="password">Password</label>
                        <input type="password" id="password" placeholder="••••••••" autocomplete="current-password">
                    </div>
                    
                    <button id="loginBtn" class="btn-stamp primary-btn">SIGN IN</button>
                    
                    <div class="divider">OR</div>
                    
                    <button id="guestBtn" class="btn-stamp secondary-btn">ENTER AS GUEST</button>
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
            loginBtn.innerText = 'SIGNING IN...';
            await auth.login(usernameInput.value, passwordInput.value);
            onLogin();
        } catch (err) {
            errorMsg.classList.remove('hidden');
            loginBtn.innerText = 'SIGN IN';
        }
    };

    const handleGuest = async () => {
        try {
            guestBtn.innerText = 'LOADING...';
            await auth.guest();
            onLogin();
        } catch (err) {
            errorMsg.innerText = 'Guest system offline.';
            errorMsg.classList.remove('hidden');
            guestBtn.innerText = 'ENTER AS GUEST';
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
