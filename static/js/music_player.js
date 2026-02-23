// 🎵 Multimodal Music Therapy Player (ISO Principle Version)

// -------- 🎧 MALAYALAM + GLOBAL ISO PLAYLIST FLOW --------
const isoPlaylists = {
    "Angry": [
        "43j9sAZenNQcQ5A4ITyJ82", // intense
        "5ZEQJAi8ILoLT9OlSxjtE7", // emotional release
        "4hoQGGzv4M7f1YzfrIxPlL"  // calm
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
        "0iBa6VlxiX2W7CKkHNdnns?si=678fbcd4a25d41c6",
        "37i9dQZF1DX3rxVfibe1L0"
    ],
    "Happy": [
        "37i9dQZF1DXdPec7aLTmlC"
    ],
    "Calm": [
        "37i9dQZF1DX3rxVfibe1L0"
    ]
};

// -------- CREATE PLAYER UI --------
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

// -------- PLAY SINGLE PLAYLIST --------
function playPlaylist(playlistId) {
    const iframe = document.getElementById("spotifyPlayer");
    if (!iframe) return;

    iframe.src =
        "https://open.spotify.com/embed/playlist/" +
        playlistId +
        "?utm_source=generator&autoplay=1";
}

// -------- ISO SEQUENCE PLAYER (FULL FIRST SONG) --------
let isoTimer = null;

function playIsoSequence(mood) {
    const sequence = isoPlaylists[mood] || isoPlaylists["Neutral"];
    let index = 0;

    clearInterval(isoTimer);

    function playNext() {
        if (index >= sequence.length) return;

        playPlaylist(sequence[index]);
        console.log("🎵 Playing playlist:", sequence[index]);

        const iframe = document.getElementById("spotifyPlayer");

        // Wait for the song to finish before moving to next
        // Spotify embed autoplay doesn't give exact duration,
        // so we assume ~3:30 per playlist (210000ms)
        let waitTime = 210000;

        // For the first playlist, ensure full song
        if (index === 0) {
            waitTime = 210000; // adjust to actual first song duration in ms if needed
        }

        isoTimer = setTimeout(() => {
            index++;
            playNext();
        }, waitTime);
    }

    playNext();
}

// -------- WATCH EMOTION TEXT --------
function watchEmotion() {
    const emotionElement = document.getElementById("emotion");
    if (!emotionElement) return;

    let lastMood = "";

    isoTimer = setInterval(() => {
    index++;

    if (index >= sequence.length) {
        clearInterval(isoTimer);
        return;
    }

    playPlaylist(sequence[index]);

           }, 60000); // change playlist every 60 seconds
        }
// -------- INIT --------
window.addEventListener("DOMContentLoaded", () => {
    createMusicUI();
    watchEmotion();
});