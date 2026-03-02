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
let faceDetectionInterval = null;

// --- WAV ENCODER VARIABLES ---
let audioDataBuffers = [];
let recordingSampleRate = 44100;

function mergeBuffers(channelBuffer, recordingLength) {
    let result = new Float32Array(recordingLength);
    let offset = 0;
    for (let i = 0; i < channelBuffer.length; i++) {
        result.set(channelBuffer[i], offset);
        offset += channelBuffer[i].length;
    }
    return result;
}

function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

function encodeWAV(samples) {
    let buffer = new ArrayBuffer(44 + samples.length * 2);
    let view = new DataView(buffer);

    // RIFF chunk descriptor
    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, 'WAVE');
    // FMT sub-chunk
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true); // chunkSize
    view.setUint16(20, 1, true); // wFormatTag
    view.setUint16(22, 1, true); // wChannels: stereo (2 channels)
    view.setUint32(24, recordingSampleRate, true); // dwSamplesPerSec
    view.setUint32(28, recordingSampleRate * 2, true); // dwAvgBytesPerSec
    view.setUint16(32, 2, true); // wBlockAlign
    view.setUint16(34, 16, true); // wBitsPerSample
    // data sub-chunk
    writeString(view, 36, 'data');
    view.setUint32(40, samples.length * 2, true);

    // PCM samples
    let offset = 44;
    for (let i = 0; i < samples.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, samples[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }
    return new Blob([view], { type: 'audio/wav' });
}
let audioAnalyser = null;
let audioDataArray = null;
let lastFaceTriggerTime = 0;

function startFaceDetection() {
    // Baseline Calibration
    let calibCount = 0;
    statusText.innerText = "Calibrating camera... Please look at the screen and keep a neutral face.";

    let calibInterval = setInterval(async () => {
        let blob = await captureFaceFrame();
        if (blob) {
            let fd = new FormData();
            fd.append("face_image", blob);
            fetch("/calibrate", { method: "POST", body: fd })
                .then(res => res.json())
                .then(data => {
                    if (data.calibrated) {
                        clearInterval(calibInterval);
                        statusText.innerText = "Calibration Complete! Ready to analyze.";
                        console.log("✅ Camera baseline calibrated");
                    }
                }).catch(e => console.error(e));
        }
        calibCount++;
        // Timeout
        if (calibCount > 10) {
            clearInterval(calibInterval);
            statusText.innerText = "Calibration timeout. Proceeding with defaults.";
        }
    }, 500);
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
                        <div><b>Happy (Smile):</b> ${m.smile} <span style="color:${m.smile > 0.005 ? 'green' : 'gray'}">(>0.005)</span></div>
                        <div><b>Sad (Frown):</b> ${m.smile} <span style="color:${m.smile < -0.010 ? 'green' : 'gray'}">(<-0.010)</span></div>
                        <div><b>Sad (EyeOpen):</b> ${m.eye_open} <span style="color:${m.eye_open < 0.03 ? 'green' : 'gray'}">(<0.03)</span></div>
                        <div><b>Surprise (Mouth):</b> ${m.mar} <span style="color:${m.mar > 0.15 ? 'green' : 'gray'}">(>0.15)</span></div>
                        <div><b>Angry (BrowDist):</b> ${m.glabella} <span style="color:${m.glabella < 0.28 ? 'green' : 'gray'}">(<0.28)</span></div>
                    `;
                    document.getElementById("face-metrics").innerHTML = html;
                }
            }
        })
        .catch(err => console.error("Face detection error:", err));
}

// --- (Removed old WebM bufferToWave decoder here) ---

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

            // Trigger Threshold = 0.015, Throttled to 1 face cap per 500ms
            if (rms > 0.015) {
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

        // --- NATIVE WAV RECORDER INITIATION ---
        audioDataBuffers = [];
        let recorderSource = audioContext.createMediaStreamSource(audioStream);
        let processor = audioContext.createScriptProcessor(4096, 1, 1);
        recordingSampleRate = audioContext.sampleRate;

        recorderSource.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = function (e) {
            if (!isRecording) return;
            audioDataBuffers.push(new Float32Array(e.inputBuffer.getChannelData(0)));
        };

        // Save reference so we can disconnect it
        recorder = { source: recorderSource, processor };

        isRecording = true;

        statusText.innerText = "Listening... (Click to Stop)";
        recordBtn.innerHTML = "⏹️ Stop Speaking";

        // Capture ONE face strictly while the user is *actually speaking* 
        // We'll give them 1 second to start talking and make an expression
        setTimeout(() => {
            if (isRecording) {
                console.log("📸 Triggering mid-speech Active Face Capture!");
                triggerVoiceSynchronizedFaceCapture();
            }
        }, 1000);

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
    try {
        if (!isRecording) return;
        isRecording = false;

        if (recorder) {
            if (recorder.source) recorder.source.disconnect();
            if (recorder.processor) recorder.processor.disconnect();
        }

        if (faceDetectionInterval) {
            clearInterval(faceDetectionInterval);
        }

        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }

        console.log("Recording stopped. Processing...");
        statusText.innerText = "Processing Your Request...";
        recordBtn.innerText = "⏳ Processing...";
        recordBtn.disabled = true;

        let mergedBytes = 0;
        for (let i = 0; i < audioDataBuffers.length; i++) {
            mergedBytes += audioDataBuffers[i].length;
        }

        console.log("Merged bytes: ", mergedBytes);

        if (mergedBytes === 0) {
            console.warn("No audio captured.");
            statusText.innerText = "No audio recorded. Please try again.";
            recordBtn.disabled = false;
            recordBtn.innerHTML = "🎙️ Start Speaking";
            return;
        }

        const mergedAudio = mergeBuffers(audioDataBuffers, mergedBytes);
        const wavBlob = encodeWAV(mergedAudio);

        console.log("Wav blob created size: ", wavBlob.size);
        sendAudioToBackend(wavBlob, activeFaceBlob);
    } catch (error) {
        console.error("Crash inside stopRecording:", error);
        statusText.innerText = "Error local processing: " + error.message;
        recordBtn.disabled = false;
        recordBtn.innerHTML = "🎙️ Start Speaking";
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
