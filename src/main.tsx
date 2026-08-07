import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

if (window.location.hash.includes('figmacapture')) {
  document.documentElement.classList.add('figma-capture');
  const captureScript = document.createElement('script');
  captureScript.src = 'https://mcp.figma.com/mcp/html-to-design/capture.js';
  captureScript.async = true;
  document.head.appendChild(captureScript);
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
