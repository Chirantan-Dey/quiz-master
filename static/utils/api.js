import store from './store.js';

// Get CSRF token from meta tag
const getCsrfToken = () => document.querySelector('meta[name="csrf-token"]')?.content;

/**
 * Make an API request with proper headers
 * @param {string} url - The API endpoint URL
 * @param {Object} options - Request options (method, body, etc.)
 * @param {boolean} isProtected - Whether the endpoint requires auth token
 * @returns {Promise} - Fetch promise
 */
export const apiRequest = async (url, options = {}, isProtected = true) => {
    // Default headers
    const headers = {
        'Content-Type': 'application/json',
    };

    // Add auth token for protected routes
    if (isProtected) {
        headers['Authentication-Token'] = store.state.authToken;
        headers['X-CSRF-Token'] = getCsrfToken();
    }

    // Merge headers with any provided in options
    const requestOptions = {
        credentials: 'same-origin',  // Always send cookies
        ...options,
        headers: {
            ...headers,
            ...(options.headers || {})
        }
    };

    const response = await fetch(url, requestOptions);
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
};

// Common API methods
export const api = {
    // Protected routes (require auth token and CSRF)
    get: (url) => apiRequest(url, { method: 'GET' }, true),
    post: (url, data) => apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    }, true),
    put: (url, data) => apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    }, true),
    delete: (url) => apiRequest(url, {
        method: 'DELETE'
    }, true),

    // Auth routes (no auth token or CSRF needed)
    login: (data) => apiRequest('/', {
        method: 'POST',
        body: JSON.stringify(data)
    }, false),
    register: (data) => apiRequest('/register', {
        method: 'POST',
        body: JSON.stringify(data)
    }, false)
};