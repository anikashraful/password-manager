// Store user session
let currentUser = null;
let masterPassword = null;

// Check if on login page
if (window.location.pathname === '/login') {
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                sessionStorage.setItem('userId', data.user_id);
                sessionStorage.setItem('masterPassword', password);
                window.location.href = '/index';
            } else {
                alert('Login failed: ' + data.error);
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

// Check if on signup page
if (window.location.pathname === '/signup') {
    document.getElementById('signupForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm-password').value;
        
        if (password !== confirmPassword) {
            alert('Passwords do not match!');
            return;
        }
        
        try {
            const response = await fetch('/api/signup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                alert('Account created successfully! Please login.');
                window.location.href = '/login';
            } else {
                alert('Signup failed: ' + data.error);
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

// Check if on index page
if (window.location.pathname === '/index') {
    const userId = sessionStorage.getItem('userId');
    const masterPassword = sessionStorage.getItem('masterPassword');
    
    if (!userId || !masterPassword) {
        window.location.href = '/login';
    }
    
    // Load passwords
    loadPasswords();
    
    // Add password form
    document.getElementById('addPasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const siteName = document.getElementById('site_name').value;
        const siteUrl = document.getElementById('site_url').value;
        const siteUsername = document.getElementById('site_username').value;
        const sitePassword = document.getElementById('site_password').value;
        
        try {
            const response = await fetch('/api/add-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    user_id: sessionStorage.getItem('userId'),
                    password: sessionStorage.getItem('masterPassword'),
                    site_name: siteName,
                    site_url: siteUrl,
                    username: siteUsername,
                    site_password: sitePassword
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                document.getElementById('addPasswordForm').reset();
                loadPasswords();
            } else {
                alert('Failed to add password: ' + data.error);
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
    
    // Search functionality
    document.getElementById('searchInput').addEventListener('input', filterPasswords);
    
    // Logout
    document.getElementById('logoutBtn').addEventListener('click', () => {
        sessionStorage.clear();
        window.location.href = '/login';
    });
}

async function loadPasswords() {
    const userId = sessionStorage.getItem('userId');
    const masterPassword = sessionStorage.getItem('masterPassword');
    
    try {
        const response = await fetch(`/api/passwords?user_id=${userId}&password=${encodeURIComponent(masterPassword)}`);
        const data = await response.json();
        
        if (data.success) {
            displayPasswords(data.passwords);
        } else {
            alert('Failed to load passwords: ' + data.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function displayPasswords(passwords) {
    const container = document.getElementById('passwordContainer');
    container.innerHTML = '';
    
    if (passwords.length === 0) {
        container.innerHTML = '<p class="no-passwords">No passwords saved yet.</p>';
        return;
    }
    
    passwords.forEach(pwd => {
        const div = document.createElement('div');
        div.className = 'password-item';
        div.dataset.name = pwd.site_name.toLowerCase();
        div.dataset.username = pwd.username.toLowerCase();
        
        div.innerHTML = `
            <div class="password-info">
                <h3>${pwd.site_name}</h3>
                <p>🔗 ${pwd.site_url || 'No URL'}</p>
                <p>👤 ${pwd.username}</p>
                <p>🔑 
                    <span class="password-hidden">••••••••</span>
                    <span class="password-visible" style="display:none;">${pwd.password}</span>
                    <span class="show-password" onclick="togglePassword(this)">👁️ Show</span>
                </p>
            </div>
            <button class="delete-btn" onclick="deletePassword(${pwd.id})">Delete</button>
        `;
        
        container.appendChild(div);
    });
}

function togglePassword(element) {
    const passwordDiv = element.parentElement;
    const hidden = passwordDiv.querySelector('.password-hidden');
    const visible = passwordDiv.querySelector('.password-visible');
    
    if (hidden.style.display !== 'none') {
        hidden.style.display = 'none';
        visible.style.display = 'inline';
        element.textContent = '👁️ Hide';
    } else {
        hidden.style.display = 'inline';
        visible.style.display = 'none';
        element.textContent = '👁️ Show';
    }
}

async function deletePassword(id) {
    if (!confirm('Are you sure you want to delete this password?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/delete-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id })
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadPasswords();
        } else {
            alert('Failed to delete password');
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function filterPasswords() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const items = document.querySelectorAll('.password-item');
    
    items.forEach(item => {
        const name = item.dataset.name;
        const username = item.dataset.username;
        
        if (name.includes(searchTerm) || username.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}