import { CONFIG } from './config.js';

const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

function appendMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.innerText = text;
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function formatEmailPreview(emails) {
    if (!emails.length) {
        return 'No emails were returned by the API.';
    }

    return emails
        .map((email, index) => {
            const subject = email.subject || '(no subject)';
            const from = email.from_address || '(unknown sender)';
            const date = email.date || '(no date)';
            const snippet = email.snippet || '(no snippet)';

            return [
                `${index + 1}. ${subject}`,
                `From: ${from}`,
                `Date: ${date}`,
                `Snippet: ${snippet}`
            ].join('\n');
        })
        .join('\n\n');
}

async function sendToBackend(commandText, accessToken, options = {}) {
    const response = await fetch(`${CONFIG.BACKEND_URL}/api/gmail/prepare`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            access_token: accessToken,
            user_command: commandText,
            gmail_query: options.gmailQuery || null,
            max_results: options.maxResults || 10
        })
    });

    const payload = await response.json();

    if (!response.ok) {
        throw new Error(payload.detail || 'Backend request failed.');
    }

    return payload;
}

function handleUserRequest(commandText, options = {}) {
    if (!commandText.trim()) return;

    appendMessage(commandText, 'user');
    userInput.value = '';
    appendMessage('Authenticating and preparing pipeline...', 'ai');

    chrome.runtime.sendMessage({ action: 'getAuthToken' }, async (response) => {
        if (!response || !response.success) {
            appendMessage(
                `Authentication failed: ${response?.error || 'Unknown Error'}`,
                'ai'
            );
            return;
        }

        appendMessage('Authenticated! Preparing Gmail data for AI...', 'ai');

        try {
            const result = await sendToBackend(commandText, response.token, options);
            appendMessage(
                `Prepared ${result.total_emails} emails for AI processing.`,
                'ai'
            );

            if (options.showPreview) {
                appendMessage(formatEmailPreview(result.emails), 'ai');
            }
        } catch (error) {
            appendMessage(`Backend failed: ${error.message}`, 'ai');
        }
    });
}

sendBtn.addEventListener('click', () => handleUserRequest(userInput.value));

userInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        handleUserRequest(userInput.value);
    }
});

document.getElementById('cleanAdsBtn').addEventListener('click', () => {
    handleUserRequest(
        'Delete and unsubscribe from the most recent 100 advertisement emails.'
    );
});

document.getElementById('quickOrgBtn').addEventListener('click', () => {
    handleUserRequest(
        'Analyze my unread messages and organize them into structured labels.'
    );
});

document.getElementById('testRecentBtn').addEventListener('click', () => {
    handleUserRequest('Test recent 10 inbox emails.', {
        gmailQuery: 'in:inbox',
        maxResults: 10,
        showPreview: true
    });
});
