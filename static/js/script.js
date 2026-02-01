const video = document.getElementById("video");
const faceEmotionDisplay = document.getElementById("emotion");

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

recordBtn.onclick = async () => {
    try {
        // Resume context if suspended
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        recorder = new MediaRecorder(stream);
        audioChunks = [];

        recorder.start();
        statusText.innerText = "Listening...";
        recordBtn.disabled = true;

        recorder.ondataavailable = e => audioChunks.push(e.data);

        recorder.onstop = async () => {
            statusText.innerText = "Processing audio...";

            // 1. Get WebM/Ogg Blob
            const webmBlob = new Blob(audioChunks, { type: 'audio/webm' });
            // Note: 'audio/webm' is typical default, hopefully browser supports it or 'audio/ogg'

            // 2. Convert to ArrayBuffer
            const arrayBuffer = await webmBlob.arrayBuffer();

            // 3. Decode to AudioBuffer (PCM)
            try {
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

                // 4. Encode to WAV
                const wavBlob = bufferToWave(audioBuffer, audioBuffer.length);

                statusText.innerText = "Sending data...";
                const faceBlob = await captureFaceFrame();
                sendAudioToBackend(wavBlob, faceBlob);

            } catch (e) {
                console.error("Error decoding audio", e);
                statusText.innerText = "Error converting audio.";
                recordBtn.disabled = false;
            }
        };

        setTimeout(() => {
            recorder.stop();
            // Stop stream tracks
            stream.getTracks().forEach(track => track.stop());
        }, 5000);

    } catch (err) {
        console.error(err);
        alert("Microphone access denied or error: " + err.message);
        recordBtn.disabled = false;
    }
};

function sendAudioToBackend(audioBlob, faceBlob) {
    const formData = new FormData();
    formData.append("audio_data", audioBlob, "response.wav"); // Explicit filename
    if (faceBlob) {
        formData.append("face_data", faceBlob);
    }

    fetch("/process_voice_answer", {
        method: "POST",
        body: formData
    })
        .then(res => res.json())
        .then(data => {
            statusText.innerHTML = `${data.bot_reply}<br><b>Final Mood:</b> ${data.new_mood}<br><small>${data.reasoning}</small>`;
            faceEmotionDisplay.innerText = data.new_mood;
            recordBtn.disabled = false;
        })
        .catch(err => {
            console.error(err);
            statusText.innerText = "Error processing response.";
            recordBtn.disabled = false;
        });
}