// ================= VIDEO & UI =================
const video = document.getElementById("video");
const emotionText = document.getElementById("emotion");
const recordBtn = document.getElementById("recordBtn");
const statusText = document.getElementById("status");

emotionText.innerText = "Initializing...";
statusText.innerText = "Idle";

// ================= CAMERA ACCESS =================
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => {
    alert("Camera access denied");
    console.error(err);
  });

// ================= FACE MESH SETUP =================
const faceMesh = new FaceMesh({
  locateFile: file =>
    `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
});

faceMesh.setOptions({
  maxNumFaces: 1,
  refineLandmarks: true,
  minDetectionConfidence: 0.6,
  minTrackingConfidence: 0.6
});

faceMesh.onResults(onFaceResults);

// ================= CAMERA UTILS =================
const camera = new Camera(video, {
  onFrame: async () => {
    await faceMesh.send({ image: video });
  },
  width: 640,
  height: 480
});
camera.start();

// ================= FACE CROP & SEND =================
let lastSent = 0;

function onFaceResults(results) {
  if (!results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
    emotionText.innerText = "No face detected";
    return;
  }

  // limit sending frames (every 800ms)
  const now = Date.now();
  if (now - lastSent < 800) return;
  lastSent = now;

  const landmarks = results.multiFaceLandmarks[0];

  let minX = 1, minY = 1, maxX = 0, maxY = 0;

  landmarks.forEach(pt => {
    minX = Math.min(minX, pt.x);
    minY = Math.min(minY, pt.y);
    maxX = Math.max(maxX, pt.x);
    maxY = Math.max(maxY, pt.y);
  });

  const x = minX * video.videoWidth;
  const y = minY * video.videoHeight;
  const w = (maxX - minX) * video.videoWidth;
  const h = (maxY - minY) * video.videoHeight;

  if (w < 50 || h < 50) return;

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;

  const ctx = canvas.getContext("2d");
  ctx.drawImage(video, x, y, w, h, 0, 0, w, h);

  canvas.toBlob(blob => {
    sendFaceToBackend(blob);
  }, "image/jpeg");
}

function sendFaceToBackend(faceBlob) {
  const formData = new FormData();
  formData.append("face_image", faceBlob);

  fetch("/detect_face", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.emotion) {
        emotionText.innerText = data.emotion;
      }
    })
    .catch(err => console.error("Face error:", err));
}

// ================= AUDIO RECORDING =================
let recorder;
let audioChunks = [];
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

recordBtn.onclick = async () => {
  try {
    if (audioContext.state === "suspended") {
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
      statusText.innerText = "Processing...";

      const webmBlob = new Blob(audioChunks, { type: "audio/webm" });
      const arrayBuffer = await webmBlob.arrayBuffer();

      try {
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const wavBlob = bufferToWave(audioBuffer, audioBuffer.length);
        sendAudioToBackend(wavBlob);
      } catch (e) {
        statusText.innerText = "Audio error";
        recordBtn.disabled = false;
      }
    };

    setTimeout(() => {
      recorder.stop();
      stream.getTracks().forEach(t => t.stop());
    }, 5000);

  } catch (err) {
    alert("Mic access error");
    recordBtn.disabled = false;
  }
};

// ================= SEND AUDIO =================
function sendAudioToBackend(audioBlob) {
  const formData = new FormData();
  formData.append("audio_data", audioBlob, "speech.wav");

  fetch("/process_voice_answer", {
    method: "POST",
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      statusText.innerText = data.bot_reply || "Done";
      recordBtn.disabled = false;
    })
    .catch(err => {
      statusText.innerText = "Server error";
      recordBtn.disabled = false;
    });
}

// ================= WAV ENCODER =================
function bufferToWave(abuffer, len) {
  const numOfChan = abuffer.numberOfChannels;
  const buffer = new ArrayBuffer(len * numOfChan * 2 + 44);
  const view = new DataView(buffer);
  let offset = 0, pos = 0;

  function writeUint16(d) { view.setUint16(pos, d, true); pos += 2; }
  function writeUint32(d) { view.setUint32(pos, d, true); pos += 4; }

  writeUint32(0x46464952);
  writeUint32(buffer.byteLength - 8);
  writeUint32(0x45564157);
  writeUint32(0x20746d66);
  writeUint32(16);
  writeUint16(1);
  writeUint16(numOfChan);
  writeUint32(abuffer.sampleRate);
  writeUint32(abuffer.sampleRate * 2 * numOfChan);
  writeUint16(numOfChan * 2);
  writeUint16(16);
  writeUint32(0x61746164);
  writeUint32(buffer.byteLength - pos - 4);

  const channels = [];
  for (let i = 0; i < numOfChan; i++)
    channels.push(abuffer.getChannelData(i));

  while (offset < len) {
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
