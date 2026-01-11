const video = document.getElementById("video");

navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => video.srcObject = stream)
    .catch(() => alert("Camera access denied"));


const recordBtn = document.getElementById("recordBtn");
const statusText = document.getElementById("status");
    let recorder;
let audioChunks = [];

function captureFaceFrame() {
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0);

    return new Promise(resolve => {
        canvas.toBlob(blob => resolve(blob), "image/jpeg");
    });
}

recordBtn.onclick = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

    recorder = new MediaRecorder(stream);
    audioChunks = [];

    recorder.start();
    statusText.innerText = "Listening...";

    recorder.ondataavailable = e => audioChunks.push(e.data);

    recorder.onstop = async () => {
        statusText.innerText = "Sending data...";

        const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
        const faceBlob = await captureFaceFrame();

        sendToBackend(audioBlob, faceBlob);
    };

    setTimeout(() => {
        recorder.stop();
        statusText.innerText = "Analyzing emotion...";
    }, 5000);
};

function sendToBackend(audioBlob, faceBlob) {
    const formData = new FormData();
    formData.append("audio", audioBlob);
    formData.append("face", faceBlob);

    fetch("/analyze", {
        method: "POST",
        body: formData
    });
}