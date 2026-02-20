// ISO PRINCIPLE PLAYLISTS
const isoPlaylists = {
    "Happy": "37i9dQZF1DXdPec7aLTmlC",
    "Sad": "37i9dQZF1DX7qK8ma5wgG1",
    "Angry": "37i9dQZF1DX1s9knjP51Oa",
    "Neutral": "37i9dQZF1DX4WYpdgoIcn6"
};

// Play therapy playlist
function playTherapyMusic(mood) {
    const player = document.getElementById("spotifyPlayer");

    if (!player) {
        console.log("Spotify player not found");
        return;
    }

    if (isoPlaylists[mood]) {
        player.src = `https://open.spotify.com/embed/playlist/${isoPlaylists[mood]}`;
        console.log("🎵 Playing therapy playlist for:", mood);
    }
}

// Listen for FINAL mood from main system
window.addEventListener("message", function(event) {
    if (event.data.type === "FINAL_MOOD") {
        playTherapyMusic(event.data.mood);
    }
});