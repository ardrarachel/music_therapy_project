const video = document.getElementById("video");
const faceEmotionDisplay = document.getElementById("emotion");
const musicPlayer = document.getElementById("musicPlayer");

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
        startFaceDetection();
    })
    .catch(err => {
        console.error("Camera access denied:", err);
        alert("Camera access denied. Please allow camera access for emotion detection.");
    });

const recordBtn = document.getElementById("recordBtn");
const statusText = document.getElementById("status");
// --- GLOBAL AUDIO VARIABLES ---
let recorder;
let audioChunks = [];
let audioStream = null; // Renamed to avoid confusion with video stream
let isRecording = false;
let audioContext = new (window.AudioContext || window.webkitAudioContext)();

// 🎵 SPOTIFY PLAYLISTS FOR EACH EMOTION
const emotionPlaylists = {
    Happy: "https://open.spotify.com/embed/playlist/37i9dQZF1DXdPec7aLTmlC",
    Sadness: "https://open.spotify.com/embed/playlist/37i9dQZF1DX7qK8ma5wgG1",
    Anger: "https://open.spotify.com/embed/playlist/37i9dQZF1DWYxwmBaMqxsl",
    Excited: "https://open.spotify.com/embed/playlist/37i9dQZF1DX1g0iEXLFycr",
    Calm: "https://open.spotify.com/embed/playlist/37i9dQZF1DX4sWSpwq3LiO",
    Neutral: "https://open.spotify.com/embed/playlist/37i9dQZF1DX4WYpdgoIcn6"
};

function playEmotionMusic(emotion) {
    console.log(`🎵 Triggering Spotify Update for Mood: ${emotion}`);

    // Call the built-in Sequence Player from music_player.js directly
    if (typeof playIsoSequence === "function") {
        playIsoSequence(emotion);
    } else {
        console.warn("music_player.js is missing or not loaded!");
    }
}

// ---------------- FACE DETECTION & VOICE TRIGGER ----------------
let faceDetectionInterval = null; // We'll keep a reference to a poll loop for AudioContext
let audioAnalyser = null;
let audioDataArray = null;
let lastFaceTriggerTime = 0;

function startFaceDetection() {
    // We no longer trigger unconditionally. We wait for user to start recording
    // and let the voice trigger capture it.
}

function captureFaceFrame() {
    if (!video.videoWidth) return null;

    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    return new Promise(resolve => {
        canvas.toBlob(blob => resolve(blob), "image/jpeg");
    });
}

function sendFaceToBackend(faceBlob) {
    const formData = new FormData();
    formData.append("face_image", faceBlob);

    fetch("/detect_face", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.emotion) {
                faceEmotionDisplay.innerText = data.emotion;

                // Render Metrics if available
                if (data.metrics) {
                    const m = data.metrics;
                    const html = `
                        <div><b>Happy (Smile):</b> ${m.smile} <span style="color:${m.smile > 0.015 ? 'green' : 'gray'}">(>0.015)</span></div>
                        <div><b>Sad (Frown):</b> ${m.smile} <span style="color:${m.smile < -0.002 ? 'green' : 'gray'}">(<-0.002)</span></div>
                        <div><b>Sad (EyeOpen):</b> ${m.eye_open} <span style="color:${m.eye_open < 0.03 ? 'green' : 'gray'}">(<0.03)</span></div>
                        <div><b>Surprise (Mouth):</b> ${m.mar} <span style="color:${m.mar > 0.20 ? 'green' : 'gray'}">(>0.20)</span></div>
                        <div><b>Angry (BrowDist):</b> ${m.glabella} <span style="color:${m.glabella < 0.285 ? 'green' : 'gray'}">(<0.285)</span></div>
                    `;
                    document.getElementById("face-metrics").innerHTML = html;
                }
            }
        })
        .catch(err => console.error("Face detection error:", err));
}

// --- WAV ENCODING HELPERS ---
function bufferToWave(abuffer, len) {
    let numOfChan = abuffer.numberOfChannels,
        length = len * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [], i, sample,
        offset = 0,
        pos = 0;

    // write WAVE header
    setUint32(0x46464952);                         // "RIFF"
    setUint32(length - 8);                         // file length - 8
    setUint32(0x45564157);                         // "WAVE"

    setUint32(0x20746d66);                         // "fmt " chunk
    setUint32(16);                                 // length = 16
    setUint16(1);                                  // PCM (uncompressed)
    setUint16(numOfChan);
    setUint32(abuffer.sampleRate);
    setUint32(abuffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
    setUint16(numOfChan * 2);                      // block-align
    setUint16(16);                                 // 16-bit (hardcoded in this example)

    setUint32(0x61746164);                         // "data" - chunk
    setUint32(length - pos - 4);                   // chunk length

    // write interleaved data
    for (i = 0; i < abuffer.numberOfChannels; i++)
        channels.push(abuffer.getChannelData(i));

    while (pos < len) {
        for (i = 0; i < numOfChan; i++) {             // interleave channels
            sample = Math.max(-1, Math.min(1, channels[i][offset])); // clamp
            sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0; // scale to 16-bit signed int
            view.setInt16(pos, sample, true);          // write 16-bit sample
            pos += 2;
        }
        offset++;                                     // next source sample
    }

    // create Blob
    return new Blob([buffer], { type: "audio/wav" });

    function setUint16(data) {
        view.setUint16(pos, data, true);
        pos += 2;
    }

    function setUint32(data) {
        view.setUint32(pos, data, true);
        pos += 4;
    }
}

// Toggle Button Logic
recordBtn.onclick = () => {
    if (isRecording) stopRecording();
    else startRecording();
};

async function startRecording() {
    try {
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        // 1. Request Microphone Access
        // IMPORTANT: Assign to GLOBAL audioStream, do not use 'const'
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // --- VISUAL TRIGGER (AUDIO ANALYZER) SETUP ---
        const source = audioContext.createMediaStreamSource(audioStream);
        audioAnalyser = audioContext.createAnalyser();
        audioAnalyser.fftSize = 256;
        source.connect(audioAnalyser);

        let bufferLength = audioAnalyser.frequencyBinCount;
        audioDataArray = new Float32Array(bufferLength);

        // Polling loop for acoustic threshold
        faceDetectionInterval = setInterval(() => {
            if (!isRecording) return;

            audioAnalyser.getFloatTimeDomainData(audioDataArray);

            // Calculate RMS (Root Mean Square) Energy
            let sumSquares = 0.0;
            for (let i = 0; i < audioDataArray.length; i++) {
                sumSquares += audioDataArray[i] * audioDataArray[i];
            }
            let rms = Math.sqrt(sumSquares / audioDataArray.length);

            // Trigger Threshold = 0.02, Throttled to 1 face cap per 500ms
            if (rms > 0.02) {
                let now = Date.now();
                if (now - lastFaceTriggerTime > 500) {
                    lastFaceTriggerTime = now;
                    triggerVoiceSynchronizedFaceCapture();
                }
            }
        }, 100);
        // ---------------------------------------------

        activeFaceBlob = null; // Clear previous active speaking face

        // --- UI RESET FOR FACE MEMORY ---
        if (faceEmotionDisplay) faceEmotionDisplay.innerText = "Tracking...";
        const metricsDisplay = document.getElementById("face-metrics");
        if (metricsDisplay) metricsDisplay.innerHTML = "Waiting for face data...";

        recorder = new MediaRecorder(audioStream);
        audioChunks = []; // Reset chunks

        recorder.ondataavailable = e => audioChunks.push(e.data);

        recorder.onstop = async () => {
            isRecording = false;
            statusText.innerText = "Processing audio...";
            recordBtn.innerText = "Record Answer";
            recordBtn.disabled = true;

            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const arrayBuffer = await webmBlob.arrayBuffer();
            const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
            const wavBlob = bufferToWave(audioBuffer, audioBuffer.length);

            statusText.innerText = "Sending data...";

            // We no longer capture an empty/resting face frame here at the end.
            // We rely on the acoustic trigger that fired WHILE the user was speaking.
            sendAudioToBackend(wavBlob, activeFaceBlob);
        };

        recorder.start();
        isRecording = true;

        statusText.innerText = "Listening... (Click to Stop)";
        recordBtn.innerText = "Stop Listening";

        setTimeout(() => {
            if (isRecording) stopRecording();
        }, 6000);

    } catch (err) {
        console.error("Microphone Error:", err);
        statusText.innerText = "⚠️ Mic Access Denied";
        recordBtn.disabled = false;
        isRecording = false;
    }
}

function stopRecording() {
    // Only stop if the recorder exists and is active
    if (recorder && recorder.state !== "inactive") {
        recorder.stop();

        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
        }

        // IMPORTANT: Stop all tracks in the stream to turn off the mic light
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }

        console.log("Recording stopped.");
    }
}

let activeFaceBlob = null; // Store the face frame captured during active speaking

async function triggerVoiceSynchronizedFaceCapture() {
    console.log("🎤 Voice Threshold Triggered -> 📸 Capturing Face");
    const faceBlob = await captureFaceFrame();
    if (faceBlob) {
        activeFaceBlob = faceBlob; // Save it for the final compilation
        sendFaceToBackend(faceBlob);
    }
}

// ---------------- SEND TO BACKEND ----------------
function sendAudioToBackend(audioBlob, faceBlob) {
    const formData = new FormData();
    formData.append("audio_data", audioBlob, "response.wav");

    const typedText = document.getElementById("userText").value;
    formData.append("typed_text", typedText);

    if (faceBlob) formData.append("face_data", faceBlob);

    fetch("/process_voice_answer", {
        method: "POST",
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            statusText.innerHTML =
                `${data.bot_reply}<br><b>Final Mood:</b> ${data.new_mood}<br><small>${data.reasoning}</small>`;

            faceEmotionDisplay.innerText = data.new_mood;

            if (data.user_said) {
                document.getElementById("youSaidDisplay").innerText = `"${data.user_said}"`;
            }
            if (data.confidence !== undefined) {
                document.getElementById("scoreDisplay").innerText = (data.confidence * 100).toFixed(0) + "%";
            }

            window.postMessage({
                type: "FINAL_MOOD",
                mood: data.new_mood
            });
            // 🎵 PLAY MUSIC BASED ON FINAL EMOTION
            playEmotionMusic(data.new_mood);


            recordBtn.disabled = false;
        })
        .catch(err => {
            console.error(err);
            statusText.innerText = "Error processing response.";
            recordBtn.disabled = false;
        });
}

// ---------------- TEXT SUBMISSION (WAIT FOR VOICE/FACE) ----------------
const submitTextBtn = document.getElementById("submitTextBtn");
const userTextInput = document.getElementById("userText");

if (submitTextBtn) {
    submitTextBtn.onclick = () => {
        const textVal = userTextInput.value.trim();
        if (textVal === "") return;

        // Visual feedback to let user know text is locked in
        statusText.innerHTML = `<b>Text saved:</b> "${textVal}"<br><i>Waiting for you to 🎤 Speak to complete analysis...</i>`;

        // We do NOT send a separate /process_text POST.
        // The text is grabbed down inside sendAudioToBackend().
    };
}

if (userTextInput) {
    userTextInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault(); // prevent new line
            if (submitTextBtn) submitTextBtn.click();
        }
    });
}

// ---------------- WAV CONVERTER ----------------
function bufferToWave(abuffer, len) {
    let numOfChan = abuffer.numberOfChannels,
        length = len * numOfChan * 2 + 44,
        buffer = new ArrayBuffer(length),
        view = new DataView(buffer),
        channels = [],
        offset = 0,
        pos = 0;

    function setUint16(data) { view.setUint16(pos, data, true); pos += 2; }
    function setUint32(data) { view.setUint32(pos, data, true); pos += 4; }

    setUint32(0x46464952);
    setUint32(length - 8);
    setUint32(0x45564157);

    setUint32(0x20746d66);
    setUint32(16);
    setUint16(1);
    setUint16(numOfChan);
    setUint32(abuffer.sampleRate);
    setUint32(abuffer.sampleRate * 2 * numOfChan);
    setUint16(numOfChan * 2);
    setUint16(16);

    setUint32(0x61746164);
    setUint32(length - pos - 4);

    for (let i = 0; i < abuffer.numberOfChannels; i++)
        channels.push(abuffer.getChannelData(i));

    while (pos < length) {
        for (let i = 0; i < numOfChan; i++) {
            let sample = Math.max(-1, Math.min(1, channels[i][offset]));
            sample = sample < 0 ? sample * 32768 : sample * 32767;
            view.setInt16(pos, sample, true);
            pos += 2;
        }
        offset++;
    }

    return new Blob([buffer], { type: "audio/wav" });
}
