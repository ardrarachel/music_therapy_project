// 🎵 Multimodal Music Therapy Player (ISO Principle Version)
// Auto-starts when emotion text updates

// -------- 🎧 ISO PLAYLIST FLOW --------
const isoPlaylists = {
    "Angry": [
        "0iBa6VlxiX2W7CKkHNdnns", // Malayalam emotional release
        "37i9dQZF1DX3rxVfibe1L0"  // calm
    ],

    "Sad": [
        "37i9dQZF1DX7qK8ma5wgG1",
        "37i9dQZF1DX4WYpdgoIcn6",
        "37i9dQZF1DX3rxVfibe1L0"
    ],

    "Fear": [
        "37i9dQZF1DWX83CujKHHOn",
        "37i9dQZF1DX4WYpdgoIcn6",
        "37i9dQZF1DX3rxVfibe1L0"
    ],

    "Neutral": [
        "37i9dQZF1DX4WYpdgoIcn6",
        "37i9dQZF1DX3rxVfibe1L0"
    ],

    "Happy": [
        "37i9dQZF1DXdPec7aLTmlC"
    ]
};


// -------- PLAY PLAYLIST --------
function playPlaylist(playlistId) {
    const iframe = document.getElementById("spotifyPlayer");
    if (!iframe) {
        console.log("❌ Spotify iframe not found");
        return;
    }

    iframe.src =
        "https://open.spotify.com/embed/playlist/" +
        playlistId +
        "?utm_source=generator&autoplay=1";

    console.log("🎵 Playing playlist:", playlistId);
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

    }, 60000); // ✅ 1 minute per playlist
}


// -------- AUTO WATCH EMOTION --------
function watchEmotion() {
    const emotionElement = document.getElementById("emotion");
    if (!emotionElement) {
        console.log("❌ emotion element not found");
        return;
    }

    let lastMood = "";

    setInterval(() => {
        const mood = emotionElement.innerText.trim();

        if (!mood || mood === lastMood) return;

        lastMood = mood;
        console.log("🎭 Detected mood:", mood);

        playIsoSequence(mood);

    }, 1500);
}


// -------- INIT --------
window.addEventListener("DOMContentLoaded", () => {
    watchEmotion();   // ✅ THIS WAS MISSING
});