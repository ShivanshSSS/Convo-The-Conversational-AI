// static/script.js

document.addEventListener("DOMContentLoaded", () => {
  // Element refs
  const startBtn     = document.getElementById("start-btn");
  const nameInput    = document.getElementById("name");
  const ageInput     = document.getElementById("age");
  const ragCheckbox  = document.getElementById("rag");
  const setupPanel   = document.getElementById("setup");
  const chatContainer= document.getElementById("chat-container");
  const chatBox      = document.getElementById("chat-box");
  const micBtn       = document.getElementById("mic-btn");
  const recIndicator = document.getElementById("rec-indicator");
  const debugFlash   = document.getElementById("debug-flash");

  // Audio context & state
  const audioCtx     = new (window.AudioContext || window.webkitAudioContext)();
  let currentSource  = null;
  let mediaRecorder  = null;
  let audioStream    = null;
  let recordedChunks = [];
  let isRecording    = false;

  // Utility: append chat bubble
  function appendBubble(text, who) {
    const div = document.createElement("div");
    div.className = `message ${who}`;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  // Utility: debug flash
  function flashDebug() {
    debugFlash.style.opacity = "1";
    setTimeout(() => debugFlash.style.opacity = "0", 150);
  }

  // Play an audio URL, stopping any current playback first
  async function playAudio(url) {
    try {
      // --- STOP ANY ONGOING PLAYBACK ---
      if (currentSource) {
        currentSource.onended = null;
        currentSource.stop();
        currentSource.disconnect();
        currentSource = null;
      }

      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const buf = await res.arrayBuffer();
      const decoded = await audioCtx.decodeAudioData(buf);

      const src = audioCtx.createBufferSource();
      src.buffer = decoded;
      src.connect(audioCtx.destination);
      src.start();
      currentSource = src;
      src.onended = () => { currentSource = null; };
    } catch (err) {
      console.error("Playback error:", err);
    }
  }

  // — START CHAT —
  startBtn.addEventListener("click", async () => {
    const name = nameInput.value.trim();
    const age  = ageInput.value.trim();
    if (!name || !/^\d+$/.test(age)) {
      return alert("Enter a valid name and numeric age.");
    }
    startBtn.disabled = true;
    try {
      const res = await fetch("/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, age: Number(age), rag: ragCheckbox.checked })
      });
      if (!res.ok) throw new Error(`Start failed: ${res.status}`);
      const { greeting_text, greeting_audio } = await res.json();
      appendBubble(greeting_text, "bot");
      await playAudio(greeting_audio);
      setupPanel.style.display    = "none";
      chatContainer.style.display = "flex";
    } catch (e) {
      console.error("Start error:", e);
      alert("Failed to start chat.");
    } finally {
      startBtn.disabled = false;
    }
  });

  // — RECORDING —
  async function startRecording() {
    console.log("▶️ Recording start");
    try {
      // Also stop any playback right here to avoid overlap
      if (currentSource) {
        currentSource.onended = null;
        currentSource.stop();
        currentSource.disconnect();
        currentSource = null;
      }

      audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      recordedChunks = [];
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/ogg;codecs=opus";
      mediaRecorder = new MediaRecorder(audioStream, { mimeType: mime });
      mediaRecorder.ondataavailable = e => {
        if (e.data.size) recordedChunks.push(e.data);
      };
      mediaRecorder.start();
      isRecording = true;
      recIndicator.style.display = "block";
    } catch (e) {
      console.error("Mic access error:", e);
      alert("Microphone access denied.");
    }
  }

  function stopRecording() {
    console.log("⏹ Recording stop");
    mediaRecorder.onstop = async () => {
      recIndicator.style.display = "none";
      isRecording = false;
      const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType });
      if (!blob.size) return;

      try {
        const form = new FormData();
        form.append("audio_data", blob, "user_audio");
        const res1 = await fetch("/message", { method: "POST", body: form });
        if (!res1.ok) throw new Error(`Message failed: ${res1.status}`);
        const { user_text, bot_text } = await res1.json();
        appendBubble(user_text, "user");
        appendBubble(bot_text,   "bot");

        const res2 = await fetch("/tts", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: bot_text })
        });
        if (!res2.ok) throw new Error(`TTS failed: ${res2.status}`);
        const { audio_url } = await res2.json();
        await playAudio(audio_url);
      } catch (e) {
        console.error("Messaging error:", e);
        alert("Error processing audio.");
      }
    };
    mediaRecorder.stop();
    audioStream.getTracks().forEach(t => t.stop());
  }

  // — MIC BUTTON EVENTS (interrupt and record) —
  micBtn.addEventListener("mousedown", () => {
    flashDebug();
    if (!isRecording) startRecording();
  });
  micBtn.addEventListener("mouseup", () => {
    if (isRecording) stopRecording();
  });
  // For touch devices
  micBtn.addEventListener("touchstart", e => { e.preventDefault(); micBtn.dispatchEvent(new Event("mousedown")); });
  micBtn.addEventListener("touchend",   e => { e.preventDefault(); micBtn.dispatchEvent(new Event("mouseup")); });
});
