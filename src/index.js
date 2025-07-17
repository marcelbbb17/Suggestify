import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './pages/App.js'


const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Backend API URL configuration
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';


