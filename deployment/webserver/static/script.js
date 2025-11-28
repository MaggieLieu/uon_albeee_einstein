const API_BASE = '/api';
let mediaRecorder;
let audioChunks = [];
let audioContext;
let audioQueue = [];
let isPlaying = false;
let isRecording = false;
let currentMessageDiv = null;
let isSpeaking = false;
let abortController = null;
let currentAudioSource = null;


const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const voiceBtn = document.getElementById('voiceBtn');
const statusBar = document.getElementById('statusBar');
const userIdInput = document.getElementById('userId');
const sessionIdInput = document.getElementById('sessionId');
const sessionBtn = document.getElementById('sessionBtn');

// Initialize audio context
function initAudio() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
}

// Show status message
function showStatus(message, duration = 3000) {
  statusBar.textContent = message;
  statusBar.classList.add('show');
  if (duration > 0) {
    setTimeout(() => {
      statusBar.classList.remove('show');
    }, duration);
  }
}

// Add message to chat
function addMessage(role, content, isPartial = false) {
  if (isPartial && currentMessageDiv) {
    // Update existing message
    currentMessageDiv.querySelector('.message-content').textContent += content;
  } else {
    // Create new message
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.innerHTML = `
                    <div>
                        <div class="message-label">${role === 'user' ? 'You' : 'Einstein'}</div>
                        <div class="message-content">${content}</div>
                    </div>
                `;
    chatMessages.appendChild(messageDiv);

    if (role === 'assistant' && isPartial) {
      currentMessageDiv = messageDiv;
    }
  }

  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Show typing indicator
function showTypingIndicator(role = 'einstein') {
  const msgLabel = (role === 'user') ? 'You' : 'Einstein';
  const typingDiv = document.createElement('div');
  typingDiv.className = `message ${role}`;
  typingDiv.id = 'typingIndicator';
  typingDiv.innerHTML = `
                <div>
                    <div class="message-label">${msgLabel}</div>
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            `;
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
  const typingDiv = document.getElementById('typingIndicator');
  if (typingDiv) {
    typingDiv.remove();
  }
}

// Play audio chunk
async function playAudioChunk(audioHex, sampleRate) {
  const audioBytes = new Uint8Array(audioHex.match(/.{1,2}/g).map(byte => parseInt(byte, 16)));
  const audioBuffer = audioContext.createBuffer(1, audioBytes.length / 2, sampleRate);
  const channelData = audioBuffer.getChannelData(0);

  for (let i = 0; i < audioBytes.length; i += 2) {
    const int16 = (audioBytes[i + 1] << 8) | audioBytes[i];
    const float = int16 < 0x8000 ? int16 / 0x8000 : (int16 - 0x10000) / 0x8000;
    channelData[i / 2] = float;
  }

  return new Promise(resolve => {
    currentAudioSource = audioContext.createBufferSource();   // <-- store reference
    currentAudioSource.buffer = audioBuffer;
    currentAudioSource.connect(audioContext.destination);

    currentAudioSource.onended = () => {
      if (currentAudioSource) {
        currentAudioSource.disconnect();
        currentAudioSource = null;
      }
      resolve();
    };

    currentAudioSource.start();
  });
}

// Process audio queue
async function processAudioQueue() {
  if (isPlaying || audioQueue.length === 0) return;

  isPlaying = true;
  while (audioQueue.length > 0) {
    const { audioHex, sampleRate } = audioQueue.shift();
    await playAudioChunk(audioHex, sampleRate);
  }
  isPlaying = false;

  if (audioQueue.length === 0) {
    setSpeakingState(false);
  }
}

// Update UI for speaking state
function setSpeakingState(speaking) {
  const sessionConfigRequired = sessionBtn.classList.contains('attention');

  isSpeaking = speaking;

  voiceBtn.disabled = speaking | sessionConfigRequired;


  if (speaking) {
    sendBtn.classList.add('stop-mode');
    sendBtn.innerHTML = '<span>⏹️</span> Stop';
  } else {
    sendBtn.classList.remove('stop-mode');
    sendBtn.disabled = sessionConfigRequired;
    sendBtn.innerHTML = '<span>📤</span> Send';
    abortController = null;
  }
}

// Stop Einstein from speaking
function stopSpeaking() {
  if (abortController) {
    abortController.abort();
  }

  // STOP AUDIO IMMEDIATELY
  if (currentAudioSource) {
    try { currentAudioSource.stop(); } catch (e) { }
    currentAudioSource.disconnect();
    currentAudioSource = null;
  }

  audioQueue = [];
  isPlaying = false;
  currentMessageDiv = null;
  removeTypingIndicator();
  setSpeakingState(false);
  statusBar.classList.remove('show');
}

// Send text message
async function sendMessage(text) {
  if (!text.trim()) return;

  const uid = userIdInput.value;
  const sid = sessionIdInput.value;

  // Add user message
  addMessage('user', text);
  messageInput.value = '';
  setSpeakingState(true);

  // Show typing indicator
  showTypingIndicator();
  currentMessageDiv = null;

  initAudio();
  abortController = new AbortController();

  try {
    const response = await fetch(`${API_BASE}/uid/${uid}/sid/${sid}/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: text }),
      signal: abortController.signal
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let sampleRate = 22050;
    let firstText = true;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const data = line.slice(6);
        if (!data.trim()) continue;

        try {
          const event = JSON.parse(data);

          switch (event.type) {
            case 'header':
              sampleRate = event.sampleRate;
              removeTypingIndicator();
              break;

            case 'text':
              if (firstText) {
                addMessage('assistant', event.content, true);
                firstText = false;
              } else {
                addMessage('assistant', event.content, true);
              }
              break;

            case 'audio':
              audioQueue.push({ audioHex: event.audio, sampleRate });
              processAudioQueue();
              break;

            case 'done':
              currentMessageDiv = null;
              // setSpeakingState(false);
              break;

            case 'error':
              setSpeakingState(false);
              removeTypingIndicator();
              showStatus('Error: ' + event.message);
              break;
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request aborted');
    } else {
      removeTypingIndicator();
      addMessage('assistant', 'Sorry, there was an error: ' + error.message);
    }
    setSpeakingState(false);
  }
}

// Send voice message
async function sendVoiceMessage(audioBlob) {
  const uid = userIdInput.value;
  const sid = sessionIdInput.value;

  setSpeakingState(true);
  showStatus('Transcribing your speech...', 0);

  initAudio();
  showTypingIndicator('user');
  currentMessageDiv = null;
  abortController = new AbortController();

  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');

  try {
    const response = await fetch(`${API_BASE}/uid/${uid}/sid/${sid}/speak`, {
      method: 'POST',
      body: formData,
      signal: abortController.signal
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let sampleRate = 22050;
    let firstText = true;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const data = line.slice(6);
        if (!data.trim()) continue;

        try {
          const event = JSON.parse(data);

          switch (event.type) {
            case 'transcription':
              removeTypingIndicator();
              addMessage('user', event.text);
              showStatus('Einstein is thinking...', 0);
              showTypingIndicator();
              break;

            case 'header':
              sampleRate = event.sampleRate;
              removeTypingIndicator();
              statusBar.classList.remove('show');
              break;

            case 'text':
              if (firstText) {
                addMessage('assistant', event.content, true);
                firstText = false;
              } else {
                addMessage('assistant', event.content, true);
              }
              break;

            case 'audio':
              audioQueue.push({ audioHex: event.audio, sampleRate });
              processAudioQueue();
              break;

            case 'done':
              currentMessageDiv = null;
              statusBar.classList.remove('show');
              // setSpeakingState(false);
              break;

            case 'error':
              setSpeakingState(false);
              removeTypingIndicator();
              if (event.message === "Could not understand audio") showStatus(event.message + ". Please try again");
              else showStatus('Error: ' + event.message);
              break;
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('Request aborted');
    } else {
      removeTypingIndicator();
      showStatus('Error: ' + error.message);
      addMessage('assistant', 'Sorry, there was an error processing your voice message.');
    }
    setSpeakingState(false);
  }
}

// Event listeners
sendBtn.addEventListener('click', () => {
  if (isSpeaking) {
    stopSpeaking();
  } else {
    sendMessage(messageInput.value);
  }
});

messageInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !isSpeaking && messageInput.disabled === false) {
    sendMessage(messageInput.value);
  } else if (e.key === 'Enter' && isSpeaking) {
    stopSpeaking();
  }
});

voiceBtn.addEventListener('click', async () => {

  if (isRecording) {
    // Stop recording
    mediaRecorder.stop();
    isRecording = false;
    removeTypingIndicator();
    voiceBtn.classList.remove('recording');
    voiceBtn.innerHTML = '<span>🎤</span> Voice';
  } else {
    // Start recording
    try {
      // Check if getUserMedia is available in secure context
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia not supported. Ensure you are using HTTPS or localhost.');
      }

      // Detect supported MIME type
      const getSupportedMimeType = () => {
        const types = ['audio/webm', 'audio/mp4', 'audio/ogg', 'audio/wav'];
        return types.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';
      };

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getSupportedMimeType();

      mediaRecorder = new MediaRecorder(stream, { mimeType });
      audioChunks = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunks.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: mimeType });
        await sendVoiceMessage(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      isRecording = true;
      showTypingIndicator('user');
      voiceBtn.classList.add('recording');
      voiceBtn.innerHTML = '<span>⏹️</span> Stop';
      showStatus('Recording... Click Stop when done', 0);
    } catch (error) {
      console.error('Microphone error:', error);
      showStatus('Error accessing microphone: ' + error.message);

      // Provide helpful guidance
      if (error.name === 'NotAllowedError') {
        showStatus('Microphone permission denied. Please allow access in your browser settings.');
      } else if (error.name === 'NotFoundError') {
        showStatus('No microphone found. Please connect a microphone.');
      } else if (error.message.includes('secure context')) {
        showStatus('Please access this page via HTTPS or localhost.');
      }
    }
  }
});

function getIdsFromUrl() {
  const path = window.location.pathname;
  const match = path.match(/^\/uid\/([^/]+)\/sid\/([^/]+)$/);
  if (match) {
    return { uid: decodeURIComponent(match[1]), sid: decodeURIComponent(match[2]) };
  }
  return null;
}

function generateRandomId(prefix = "id") {
  const random = Math.random().toString(36).substring(2);
  return `${prefix}_${random}`;
}

// Initialize on load — now supports URL-based uid/sid
window.addEventListener('load', async () => {
  const urlIds = getIdsFromUrl();
  let uid = generateRandomId("u");
  let sid = generateRandomId("s");

  if (urlIds) {
    uid = urlIds.uid;
    sid = urlIds.sid;
    userIdInput.value = uid;
    sessionIdInput.value = sid;
  }
  else {
    userIdInput.value = uid;
    sessionIdInput.value = sid;

    updateUrl();
  }

  // Optional: save to localStorage for persistence
  // localStorage.setItem('last_uid', uid);
  // localStorage.setItem('last_sid', sid);

  try {
    const response = await fetch(`${API_BASE}/uid/${uid}/sid/${sid}/init`);
    if (response.status === 409) {
      showStatus(`Info: Session already exists, resuming session...`, 5000);
    }
    else if (!response.ok) {
      showStatus(`Warning: Session init failed (${response.status})`, 5000);
    }
  } catch (error) {
    console.error('Failed to initialize session:', error);
  }
});

function cleanAndNormaliseSpaces(inputString) {
  return inputString.replace(/\s+/g, ' ').trim();
}

// Update the Config button to change URL properly
sessionBtn.addEventListener('click', () => {
  const uid = encodeURIComponent(cleanAndNormaliseSpaces(userIdInput.value) || 'user_demo');
  const sid = encodeURIComponent(cleanAndNormaliseSpaces(sessionIdInput.value) || 'session_demo');
  window.location.href = `/uid/${uid}/sid/${sid}`;
});

function setSessionConfigState() {
  voiceBtn.disabled = true;
  messageInput.disabled = true;
  sessionBtn.classList.add('attention');
}

userIdInput.addEventListener('input', () => {
  setSessionConfigState();
});

sessionIdInput.addEventListener('input', () => {
  setSessionConfigState();
});

sessionIdInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sessionBtn.click();
  }
});

function updateUrl() {
  const uid = encodeURIComponent(cleanAndNormaliseSpaces(userIdInput.value) || 'user_demo');
  const sid = encodeURIComponent(cleanAndNormaliseSpaces(sessionIdInput.value) || 'session_demo');
  const newUrl = `/uid/${uid}/sid/${sid}`;
  if (window.location.pathname !== newUrl) {
    window.history.replaceState({}, '', newUrl);
  }
}

[userIdInput, sessionIdInput].forEach(input => {
  input.addEventListener('input', () => {
    updateUrl();
  });
});
