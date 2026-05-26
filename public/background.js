chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getAuthToken') {
    chrome.identity.getAuthToken({ interactive: true }, (token) => {
      if (chrome.runtime.lastError || !token) {
        sendResponse({
          success: false,
          error: chrome.runtime.lastError?.message
        });
        return;
      }

      sendResponse({ success: true, token });
    });

    return true;
  }

  return false;
});
