// PWA installation helper
let deferredPrompt;
const installButton = document.createElement('button');
installButton.style.display = 'none';
installButton.classList.add('install-button');
installButton.textContent = 'Install App';

// Add the button to the DOM when needed
document.addEventListener('DOMContentLoaded', () => {
  document.body.appendChild(installButton);
  
  installButton.addEventListener('click', async () => {
    if (!deferredPrompt) {
      return;
    }
    
    // Show the install prompt
    deferredPrompt.prompt();
    
    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    console.log(`User response to the install prompt: ${outcome}`);
    
    // We no longer need the prompt. Clear it up.
    deferredPrompt = null;
    
    // Hide the install button
    installButton.style.display = 'none';
  });
});

// Listen for the beforeinstallprompt event
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent Chrome 67 and earlier from automatically showing the prompt
  e.preventDefault();
  
  // Stash the event so it can be triggered later
  deferredPrompt = e;
  
  // Show the install button
  installButton.style.display = 'block';
});

// Listen for the appinstalled event
window.addEventListener('appinstalled', (e) => {
  console.log('PWA was installed');
  
  // Hide the install button after installation
  installButton.style.display = 'none';
  
  // Clear the deferredPrompt
  deferredPrompt = null;
});