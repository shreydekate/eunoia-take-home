# imports

import os
import re
from dataclasses import dataclass
import token
from typing import Dict, List, Tuple

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

# --------------------
# loading environment variables (api keys, etc.)
# --------------------

load_dotenv()

SONGS = [
    ("I Wanna Be Yours", "Arctic Monkeys", "https://open.spotify.com/track/5XeFesFbtLpXzIVDNQP22n"),
    ("Nice To Know You", "PinkPantheress", "https://open.spotify.com/track/39BYU2nLFR8Q1RcPdVvUMn"),
    ("PONTE NASTY", "Rauw", "https://open.spotify.com/track/1cNJ9ODOJF8b6AjhzoYdkv"),
    ("CHIHIRO", "Billie Eilish", "https://open.spotify.com/track/7BRD7x5pt8Lqa1eGYC4dzj"),
    ("Gimme More", "Britney Spears", "https://open.spotify.com/track/6ic8OlLUNEATToEFU3xmaH"),
    ("The Less I Know The Better", "Tame Impala", "https://open.spotify.com/track/6K4t31amVTZDgR3sKmwUJJ"),
    ("The Fate of Ophelia", "Taylor Swift", "https://open.spotify.com/track/53iuhJlwXhSER5J2IYYv1W"),
    ("Gabriela", "KATSEYE", "https://open.spotify.com/track/1xOqGUkyxGQRdCvGpvWKmL"),
    ("NOT CUTE ANYMORE", "ILLIT", "https://open.spotify.com/track/1k0JAiH11gHL9dc5dfQjQr"),
    ("Apocalypse", "Cigarettes After Sex", "https://open.spotify.com/track/1oAwsWBovWRIp7qLMGPIet"),
]

TRACK_ID_RE = re.compile(r"open\.spotify\.com/track/([A-Za-z0-9]{22})")

# --------------------
# instantiating Spotify client
# --------------------

def extract_track_id(url_or_id: str) -> str:
    """Takes in a Spotify track URL or a raw 22-character track ID, and returns the track ID."""

    s = url_or_id.strip()
    if re.fullmatch(r"[A-Za-z0-9]{22}", s):
        return s
    
    match = TRACK_ID_RE.search(s)
    if match:
        return match.group(1)
    
    raise ValueError(f"Could not extract track ID from: {url_or_id}")


def create_spotify_client() -> spotipy.Spotify:
    """Creates and returns a Spotify client using credentials from environment variables."""

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise RuntimeError(
            "Spotify API credentials not found in environment variables. " \
            "Ensure they exist in your .env file."
        )
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)

# --------------------
# instantiating helper functions and dataclasses
# --------------------

@dataclass
class Fingerprint:
    energy: str
    valence: str
    intensity: str
    complexity: str
    size: str


def clamp(x: float, low: float = 0.0, high: float = 1.0) -> float:
    """Clamps a float x to the range [low, high]."""
    return max(low, min(x, high))

def normalize_range(x: float, low: float, high: float) -> float:
    """Normalizes a float x from the range [low, high] to the range [0, 1]."""
    if high == low:
        return 0.0
    return clamp((x - low) / (high - low))

def bucket_3(x: float, labels: Tuple[str, str, str], t1: float = 0.33, t2: float = 0.66) -> str:
    """Buckets a float x in the range [0, 1] into one of three labels based on thresholds t1 and t2."""
    if x < t1:
        return labels[0]
    elif x < t2:
        return labels[1]
    else:
        return labels[2]


# --------------------
# actual emotional fingerprinting algorithmic logic (basic / preliminary version)
# 
# - making many assumptions and simplifications for the sake of this prototype, 
#   but the general idea is to combine Spotify audio features in a way that maps 
#   to the 5 dimensions of the emotional fingerprint idea:
#   (energy, valence, intensity, complexity, size)
# --------------------

def compute_fingerprint(audio_features: Dict) -> Fingerprint:
    """
    Uses Spotify audio features to compute:
    - Energy = energy + tempo + dancability
    - Valence = valence + normalized tempo
    - Intensity = energy + normalized loudness + normalized tempo
    - Complexity = time signature + key + mode
    - Size = valence + acousticness + instrumentalness
    """

    # inputs (Spotify audio features)
    tempo = float(audio_features.get("tempo", 0.0))  # in BPM
    dance = float(audio_features.get("danceability", 0.0))  # [0, 1]
    energy = float(audio_features.get("energy", 0.0))  # [0, 1]
    valence = float(audio_features.get("valence", 0.0))  # [0, 1]
    loudness = float(audio_features.get("loudness", -60.0))  # in dB, typically [-60, 0]
    time_signature = int(audio_features.get("time_signature", 4))  # in beats per bar
    key = int(audio_features.get("key", 0))  # 0-11, where 0=C, 1=C#/Db, ..., 11=B; -1 if no key detected
    mode = int(audio_features.get("mode", 1))  # 0=minor, 1=major
    acousticness = float(audio_features.get("acousticness", 0.0))  # [0, 1]
    instrumentalness = float(audio_features.get("instrumentalness", 0.0))  # [0, 1]

    # normalizations
    tempo_n = normalize_range(tempo, 50.0, 200.0)
    loudness_n = normalize_range(loudness, -30.0, 0.0)

    # energy: 45% energy + 35% tempo + 20% danceability
    energy_score = clamp((0.45 * energy) + (0.35 * tempo_n) + (0.20 * dance))
    energy_label = bucket_3(energy_score, ("low energy", "medium energy", "high energy"))   

    # valence: 85% valence + 15% tempo
    valence_score = clamp((0.85 * valence) + (0.15 * tempo_n))
    valence_label = bucket_3(valence_score, ("negative valence", "neutral valence", "positive valence"))

    # intensity: 45% energy + 35% loudness + 20% tempo
    intensity_score = clamp((0.45 * energy) + (0.35 * loudness_n) + (0.20 * tempo_n))
    intensity_label = bucket_3(intensity_score, ("low intensity", "medium intensity", "high intensity"))

    # complexity: time signature + key + mode
    # primitive calculation:
    # - time signature: 3/4 and 4/4 = basic/moderate, others = complex
    # - odd/uncommon meters push towards complex
    # - minor keys slightly increase complexity, major keys slightly decrease complexity
    complexity_raw = 0.0
    complexity_raw += 0.25 if time_signature in (3, 4) else 0.65
    if mode == 0:  # minor
        complexity_raw += 0.15
    if key == -1:  # no key detected
        complexity_raw += 0.1

    complexity_score = clamp(complexity_raw)
    complexity_label = bucket_3(complexity_score, ("low complexity", "medium complexity", "high complexity"), t1=0.40, t2=0.70)

    # size: 55% acousticness + 25% instrumentalness + 20% valence
    # preliminary idea:
    # - more acoustic => intimate/smaller
    # - less acoustic + less instrumental (more produced / vocal) => overwhelming/larger
    size_score = clamp((0.55 * (1.0 - acousticness)) + (0.25 * (1.0 - instrumentalness)) + (0.20 * valence))
    size_label = bucket_3(size_score, ("small size", "medium size", "large size"))

    return Fingerprint(
        energy=energy_label,
        valence=valence_label,
        intensity=intensity_label,
        complexity=complexity_label,
        size=size_label
    )


# --------------------
# fetching track info, features, genres, and printing results (proof of concept)
# --------------------

def get_artist_genre(spotify_client: spotipy.Spotify, artist_id: str) -> str:
    """Spotidy genres tend to be artist-level. Planning to pick the first genre, if available."""
    artist_info = spotify_client.artist(artist_id)
    genres = artist_info.get("genres", [])
    return genres[0] if genres else "Unknown Genre"

def print_rows(cols: List[str], widths: List[int]) -> None:
    """Prints a row of columns with given widths."""
    row = " | ".join(col.ljust(width) for col, width in zip(cols, widths))
    print(row)



def main():
    client = create_spotify_client()
    print("\n -- Spotify Client created successfully.") # debug

    # TOP_N = 5

    track_ids = [extract_track_id(url) for _, _, url in SONGS]
    tracks = client.tracks(track_ids)["tracks"]

    # debugging
    token = client.auth_manager.get_access_token(as_dict=False)
    print("\nToken starts with:", token[:15], "...\n")

    audio_features = client.audio_features(track_ids)

    rows = []
    for track, audio_feature in zip(tracks, audio_features):
        if track is None or audio_feature is None:
            continue
        
        song_name = track["name"]
        artist_name = track["artists"][0]["name"]
        release_date = track["album"].get("release_date", "Unknown")

        artist_id = track["artists"][0]["id"]
        genre = get_artist_genre(client, artist_id)

        fingerprint = compute_fingerprint(audio_feature)

        rows.append((
            song_name, 
            artist_name, 
            genre, 
            release_date,
            "Fingerprint:", 
            fingerprint.energy, 
            fingerprint.valence, 
            fingerprint.intensity, 
            fingerprint.complexity, 
            fingerprint.size  
        ))

    # printing results in a table format
    headers = ["Song", "Artist", "Genre", "Release Date", "Fingerprint", "Energy", "Valence", "Intensity", "Complexity", "Size"]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    print("\n --- Emotional Fingerprints for Sample Spotify Tracks --- \n")
    print_rows(headers, widths)
    print("-" * (sum(widths) + 3 * (len(headers) - 1)))

    for row in rows:
        print_rows(row, widths)


if __name__ == "__main__":
    main()