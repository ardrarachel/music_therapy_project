// 🎵 Music Therapy Player — ISO Principle + Malayalam Priority

const ISO_FLOW = {
    "Sad":     ["Sad", "Neutral", "Happy"],
    "Angry":   ["Angry", "Neutral", "Calm"],
    "Fear":    ["Fear", "Calm", "Neutral"],
    "Neutral": ["Neutral", "Calm"],      // ✅ gentle, no sudden Happy
    "Happy":   ["Happy"],
    "Calm":    ["Calm"]
};

// Malayalam + multilingual playlists
const moodPlaylists = {
    "Sad": "37i9dQZF1DX7qK8ma5wgG1",
    "Neutral": "5ffac613ed33406d",
    "Calm": "37i9dQZF1DX3rxVfibe1L0",
    "Happy": "37i9dQZF1DXdPec7aLTmlC",
    "Angry": "37i9dQZF1DWZUAeYvs88zc",
    "Fear": "37i9dQZF1DWX83CujKHHOn"
};

let lastMood = "";
let isoIndex = 0;
let isoSequence = [];

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
    iframe.allow = "autoplay; encrypted-media";

    section.appendChild(title);
    section.appendChild(iframe);
    container.appendChild(section);
}

function playMood(mood) {
    const iframe = document.getElementById("spotifyPlayer");
    if (!iframe) return;

    const playlistId = moodPlaylists[mood] || moodPlaylists["Neutral"];

    iframe.src =
        `https://open.spotify.com/embed/playlist/${playlistId}?utm_source=generator&autoplay=1`;

    console.log("🎵 Playing:", mood);
}

function startISOFlow(mood) {
    isoSequence = ISO_FLOW[mood] || ["Neutral"];
    isoIndex = 0;
    playMood(isoSequence[isoIndex]);

    const interval = setInterval(() => {
        isoIndex++;

        if (isoIndex >= isoSequence.length) {
            clearInterval(interval);
            return;
        }

        playMood(isoSequence[isoIndex]);

    }, 60000); // shift mood every 60s (therapy progression)
}

function detectMoodChange() {
    const emotionElement = document.getElementById("emotion");

    if (!emotionElement) {
        console.log("❌ Emotion element missing");
        return;
    }

    setInterval(() => {
        const currentMood = emotionElement.innerText.trim();

        if (!currentMood) return;

        if (currentMood !== lastMood) {
            lastMood = currentMood;
            console.log("🧠 Mood detected:", currentMood);
            startISOFlow(currentMood);
        }

    }, 1000);
}

window.addEventListener("load", () => {
    createMusicUI();
    detectMoodChange();
});