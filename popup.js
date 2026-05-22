document.getElementById('sendBtn').addEventListener('click', () => {
    const commandText = document.getElementById('command').value;
    const statusDiv = document.getElementById('status');
    
    if (!commandText.trim()) {
        statusDiv.innerText = "Please type a command first.";
        return;
    }
    
    statusDiv.innerText = "Authenticating with Google...";
    
    // Send a message to background.js to kick off the OAuth flow
    chrome.runtime.sendMessage({ action: "getAuthToken" }, (response) => {
        if (response && response.success) {
            statusDiv.innerText = "Authenticated! Fetching email context...";
            
            // NEXT STEP CHALLENGE:
            // Now you have a valid token! We can use this token to either:
            // 1. Fetch emails directly right here via a standard JavaScript fetch() request.
            // 2. Pass this token to a trusted backend over HTTPS to do the heavy lifting.
            //
            // Important: never log access tokens or persist them outside the
            // browser session unless you have an explicit secure storage plan.
            
        } else {
            statusDiv.innerText = `Auth Error: ${response.error || 'Unknown error'}`;
        }
    });
});
