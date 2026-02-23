// 🎵 Multimodal Music Therapy Player (ISO Principle Version)
// Works independently of backend audio files
// Detects emotion text and switches Spotify playlists automatically

// -------- 🎧 MALAYALAM + GLOBAL ISO PLAYLIST FLOW --------
// Mood → Transition → Final Calm/Happy

const isoPlaylists = {
    "Angry": [
        "37i9dQZF1DWZUAeYvs88zc", // intense
        "37i9dQZF1DX7qK8ma5wgG1", // emotional release
        "37i9dQZF1DX3rxVfibe1L0"  // calm
    ],

    "Sad": [
        "37i9dQZF1DX7qK8ma5wgG1", // sad validation
        "37i9dQZF1DX4WYpdgoIcn6", // neutral
        "37i9dQZF1DX3rxVfibe1L0"  // calm
    ],

    "Fear": [
        "37i9dQZF1DWX83CujKHHOn", // soothing
        "37i9dQZF1DX4WYpdgoIcn6",
        "37i9dQZF1DX3rxVfibe1L0"
    ],

    "Neutral": [
        "37i9dQZF1DX4WYpdgoIcn6",
        "37i9dQZF1DX3rxVfibe1L0"
    ],

    "Happy": [
        "37i9dQZF1DXdPec7aLTmlC"
    ],

    "Calm": [
        "37i9dQZF1DX3rxVfibe1L0"
    ]
};


// -------- 🎵 MALAYALAM OPTIONAL BOOST --------
// You can replace playlist IDs later with Malayalam ones
const malayalamBoost = "37i9dQZF1DWYxwmBaMqxsl"; // Malayalam songs


// -------- CREATE PLAYER UI AUTOMATICALLY --------
function createMusicUI() {
    if (document.getElementById("spotifyPlayer")) return;

    const container = document.querySelector(".container");

    const section = document.createElement("div");
    section.style.marginTop = "20px";

    const title = document.createElement("h3");
    title.innerText = "🎵 Therapy Playlist";

    const iframe = document.createElement("iframe");
    iframe.id = "spotifyPlayer";
    iframe.style.borderRadius = "12px";
    iframe.width = "100%";
    iframe.height = "352";
    iframe.frameBorder = "0";
    iframe.allow = "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture";

    section.appendChild(title);
    section.appendChild(iframe);
    container.appendChild(section);
}


// -------- PLAY PLAYLIST --------
function playPlaylist(playlistId) {
    const iframe = document.getElementById("spotifyPlayer");
    if (!iframe) return;

    iframe.src =
        "https://open.spotify.com/embed/playlist/" +
        playlistId +
        "?utm_source=generator&autoplay=1";
}


// -------- ISO SEQUENCE PLAYER --------
let isoTimer = null;

function playIsoSequence(mood) {
    const sequence = isoPlaylists[mood] || isoPlaylists["Neutral"];

    let index = 0;

    clearInterval(isoTimer);

    playPlaylist(sequence[index]);

    isoTimer = setInterval(() => {
        index++;

        if (index >= sequence.length) {
            clearInterval(isoTimer);
            return;
        }

        playPlaylist(sequence[index]);

    }, 30000); // change playlist every 30 seconds
}


// -------- WATCH EMOTION TEXT --------
function watchEmotion() {
    const emotionElement = document.getElementById("emotion");
    if (!emotionElement) return;

    let lastMood = "";

    setInterval(() => {
        const mood = emotionElement.innerText.trim();

        if (!mood || mood === lastMood) return;

        lastMood = mood;
        console.log("🎭 Mood detected:", mood);

        playIsoSequence(mood);

    }, 1500);
}


// -------- INIT --------
window.addEventListener("DOMContentLoaded", () => {
    createMusicUI();
    watchEmotion();
});