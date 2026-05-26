import { useEffect, useRef, useState } from 'react';

import { CONFIG } from './config.js';

const QUICK_ACTIONS = [
  {
    id: 'clean-ads',
    label: 'Clean recent 100 ads',
    command: 'Delete and unsubscribe from the most recent 100 advertisement emails.'
  },
  {
    id: 'quick-organize',
    label: 'Quick organize inbox',
    command: 'Analyze my unread messages and organize them into structured labels.'
  },
  {
    id: 'test-recent',
    label: 'Test recent 10 mail',
    command: 'Test recent 10 inbox emails.',
    options: {
      gmailQuery: 'in:inbox',
      maxResults: 10,
      showPreview: true
    }
  }
];

function createMessage(sender, text, emails = []) {
  return {
    id: `${sender}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    sender,
    text,
    emails
  };
}

function MessageBubble({ message }) {
  return (
    <div className={`message ${message.sender}`}>
      <p className="message-text">{message.text}</p>
      {message.emails.length > 0 ? (
        <div className="email-preview-list">
          {message.emails.map((email, index) => (
            <article className="email-card" key={email.message_id || index}>
              <div className="email-card-top">
                <span className="email-index">{index + 1}</span>
                <span className="email-date">{email.date || 'No date'}</span>
              </div>
              <h3 className="email-subject">{email.subject || 'No subject'}</h3>
              <p className="email-from">{email.from_address || 'Unknown sender'}</p>
              <p className="email-snippet">{email.snippet || 'No snippet available.'}</p>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
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

export default function App() {
  const [messages, setMessages] = useState([
    createMessage(
      'ai',
      "Hi! I'm your email assistant. What can I help you clean up or organize today?"
    )
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatBottomRef = useRef(null);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  function appendMessage(sender, text, emails = []) {
    setMessages((current) => [...current, createMessage(sender, text, emails)]);
  }

  function handleUserRequest(commandText, options = {}) {
    if (!commandText.trim() || isLoading) {
      return;
    }

    appendMessage('user', commandText);
    setInputValue('');
    appendMessage('ai', 'Authenticating and preparing pipeline...');
    setIsLoading(true);

    chrome.runtime.sendMessage({ action: 'getAuthToken' }, async (response) => {
      if (!response || !response.success) {
        appendMessage(
          'ai',
          `Authentication failed: ${response?.error || 'Unknown Error'}`
        );
        setIsLoading(false);
        return;
      }

      appendMessage('ai', 'Authenticated! Preparing Gmail data for AI...');

      try {
        const result = await sendToBackend(commandText, response.token, options);
        appendMessage(
          'ai',
          `Prepared ${result.total_emails} emails for AI processing.`
        );

        if (options.showPreview) {
          appendMessage(
            'ai',
            'Here are the most recent 10 emails returned by Gmail.',
            result.emails
          );
        }
      } catch (error) {
        appendMessage('ai', `Backend failed: ${error.message}`);
      } finally {
        setIsLoading(false);
      }
    });
  }

  function handleSubmit(event) {
    event.preventDefault();
    handleUserRequest(inputValue);
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Glooks</p>
          <h1>Mail AI Assistant</h1>
        </div>
        <div className={`status-pill ${isLoading ? 'active' : ''}`}>
          {isLoading ? 'Working' : 'Ready'}
        </div>
      </header>

      <section className="chat-container">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={chatBottomRef} />
      </section>

      <section className="quick-actions">
        {QUICK_ACTIONS.map((action) => (
          <button
            className="chip-btn"
            key={action.id}
            onClick={() => handleUserRequest(action.command, action.options)}
            type="button"
          >
            {action.label}
          </button>
        ))}
      </section>

      <form className="input-container" onSubmit={handleSubmit}>
        <input
          onChange={(event) => setInputValue(event.target.value)}
          placeholder="Ask me to sort, delete, or unsubscribe..."
          type="text"
          value={inputValue}
        />
        <button disabled={isLoading} id="sendBtn" type="submit">
          &gt;
        </button>
      </form>
    </main>
  );
}
