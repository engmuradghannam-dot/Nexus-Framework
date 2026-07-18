import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// Register the PWA service worker in production only.
// In dev it serves no purpose (assets live under '/', not '/static/') and its
// activation used to seize the freshly-loaded page and swallow the first click.
if (import.meta.env.PROD && 'serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker
      .register('/sw.js', { scope: '/' })
      .then((reg) => {
        // Pull any updated worker so a returning user isn't stuck on an old one,
        // but let it activate on the NEXT load rather than claiming this page.
        reg.update();
      })
      .catch(() => {});
  });
} else if ('serviceWorker' in navigator) {
  // Dev (or after removing the PWA): unregister any worker a previous build
  // left controlling this origin, so it can't keep interfering.
  navigator.serviceWorker.getRegistrations().then((regs) => {
    regs.forEach((r) => r.unregister());
  });
}
