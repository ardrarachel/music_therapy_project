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

let recorder;
let audioChunks = [];
let audioContext = new (window.AudioContext || window.webkitAudioContext)();
let stream = null;

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
    const playlist = emotionPlaylists[emotion] || emotionPlaylists["Neutral"];
    musicPlayer.outerHTML =
        `<iframe id="musicPlayer" src="${playlist}" width="100%" height="120"
        frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen"></iframe>`;
}

// ---------------- FACE DETECTION ----------------
function startFaceDetection() {
    setInterval(async () => {
        const faceBlob = await captureFaceFrame();
        if (faceBlob) {
            sendFaceToBackend(faceBlob);
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
            }
        })
        .catch(err => console.error("Face detection error:", err));
}

// ---------------- RECORDING ----------------
let isRecording = false;

recordBtn.onclick = () => {
    if (isRecording) stopRecording();
    else startRecording();
};

async function startRecording() {
    try {
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        recorder = new MediaRecorder(stream);
        audioChunks = [];

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
            const faceBlob = await captureFaceFrame();
            sendAudioToBackend(wavBlob, faceBlob);
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
    if (recorder && recorder.state !== "inactive") recorder.stop();
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
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
