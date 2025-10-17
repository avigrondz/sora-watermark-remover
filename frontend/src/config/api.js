/**
 * Centralized API configuration
 * Defaults to production API, falls back to localhost for development
 */

// Determine if we're in development mode
const isDevelopment = process.env.NODE_ENV === 'development' || 
                     window.location.hostname === 'localhost' || 
                     window.location.hostname === '127.0.0.1';

// API URL priority: Environment variable > Production > Localhost
const getApiUrl = () => {
  // First priority: Environment variable
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // Second priority: Production API
  if (!isDevelopment) {
    return 'https://api.sorawatermarks.com';
  }
  
  // Third priority: Localhost for development
  return 'http://localhost:8000';
};

export const API_BASE_URL = getApiUrl();

// Log the API URL being used (helpful for debugging)
console.log('API Configuration:', {
  NODE_ENV: process.env.NODE_ENV,
  hostname: window.location.hostname,
  isDevelopment,
  API_BASE_URL
});

export default API_BASE_URL;
