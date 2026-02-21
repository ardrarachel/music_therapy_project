// 🎵 ISO Principle Therapy Player
// Works with your existing index.html
// Only needs <span id="emotion">Mood</span>

const isoTherapyFlow = {
    "Angry": ["Angry", "Calm", "Happy"],
    "Sad": ["Sad", "Calm", "Happy"],
    "Fear": ["Fear", "Calm", "Happy"],
    "Neutral": ["Neutral", "Calm", "Happy"],
    "Calm": ["Calm", "Happy"],
    "Happy": ["Happy"]
};

// 🌍 Multi-language playlists (you can replace IDs later)
const moodPlaylists = {
    "Happy": "37i9dQZF1DX2apWzyECwyZ",     // Malayalam Feel Good
    "Sad": "37i9dQZF1DXdFesNN9TzXT",       // Malayalam Melody Therapy
    "Angry": "37i9dQZF1DX3Rj7nU9YQkT",     // Malayalam Energy / Motivation
    "Fear": "37i9dQZF1DWV7EzJMK2FUI",      // Soft Indian Instrumental Calm
    "Neutral": "37i9dQZF1DX6VDO8a6cQME",   // Peaceful Piano / Therapy base
    "Calm": "37i9dQZF1DWYcDQ1hSjOpY"       // Deep Relaxation Instrumental
};

let currentFlow = [];
let currentStep = 0;
let lastMood = "";

// Create UI automatically
function createMusicUI() {
    if (document.getElementById("spotifyPlayer")) return;

    const container = document.querySelector(".container");

    const section = document.createElement("div");
    section.style.marginTop = "20px";

    const title = document.createElement("h3");
    title.innerText = "🎵 Therapy Playlist (Click once to start)";

    const iframe = document.createElement("iframe");
    iframe.id = "spotifyPlayer";
    iframe.style.borderRadius = "12px";
    iframe.width = "100%";
    iframe.height = "352";
    iframe.frameBorder = "0";
    iframe.allow =
        "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture";

    section.appendChild(title);
    section.appendChild(iframe);
    container.appendChild(section);
}

// Load playlist
function loadPlaylist(mood) {
    const playlistId = moodPlaylists[mood] || moodPlaylists["Neutral"];
    const iframe = document.getElementById("spotifyPlayer");

    if (!iframe) return;

    iframe.src =
        "https://open.spotify.com/embed/playlist/" +
        playlistId +
        "?utm_source=generator";
}

// Start ISO therapy flow
function startTherapy(mood) {
    currentFlow = isoTherapyFlow[mood] || ["Neutral", "Calm", "Happy"];
    currentStep = 0;
    playNextStep();
}

// Move through therapy stages automatically
function playNextStep() {
    if (currentStep >= currentFlow.length) return;

    const mood = currentFlow[currentStep];
    loadPlaylist(mood);

    currentStep++;

    // Change mood stage every 60 seconds
    setTimeout(playNextStep, 60000);
}

// Watch emotion from backend
function watchEmotion() {
    const emotionElement = document.getElementById("emotion");
    if (!emotionElement) return;

    setInterval(() => {
        const mood = emotionElement.innerText.trim();

        if (mood !== lastMood) {
            lastMood = mood;
            startTherapy(mood);
        }
    }, 1000);
}

// Initialize
window.addEventListener("DOMContentLoaded", () => {
    createMusicUI();
    watchEmotion();
});