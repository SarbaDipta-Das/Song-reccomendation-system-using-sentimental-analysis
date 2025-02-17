import streamlit as st
import speech_recognition as sr
import random
from typing import List, Dict
from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

# Initialize the recognizer for speech-to-text
recognizer = sr.Recognizer()

@dataclass
class Song:
    title: str
    artist: str
    mood: str
    language: str
    spotify_uri: str
    spotify_url: str
    preview_url: str

class MusicRecommender:
    def __init__(self, client_id: str, client_secret: str):
        """Initialize with Spotify credentials"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.initialize_spotify()
        
        self.mood_map = {
            "happy": {
                "english": {
                    "search_terms": ["happy", "upbeat", "dance", "party"],
                    "seed_genres": ["pop", "dance"]
                },
                "hindi": {
                    "search_terms": ["bollywood dance", "hindi party", "bollywood pop"],
                    "seed_genres": ["pop"]
                }
            },
            "sad": {
                "english": {
                    "search_terms": ["sad", "melancholic", "emotional", "slow", "heartbroken"],
                    "seed_genres": ["acoustic", "singer-songwriter"]
                },
                "hindi": {
                    "search_terms": ["bollywood sad", "hindi emotional", "bollywood classical", "dard bhare gane"],
                    "seed_genres": ["acoustic", "ghazal"]
                }
            }
        }

    def initialize_spotify(self):
        """Initialize Spotify client with error handling."""
        try:
            auth_manager = SpotifyClientCredentials(
                client_id=self.client_id, 
                client_secret=self.client_secret
            )
            self.spotify = spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, retries=3)
        except Exception as e:
            print(f"Error initializing Spotify client: {str(e)}")
            raise

    def detect_mood(self, user_mood: str) -> str:
        """Detect mood based on user input with better handling of negative phrases."""
        user_mood = user_mood.lower()
        mood_keywords = {
            "happy": ["happy", "joyful", "excited", "cheerful", "good", "great", "fantastic"],
            "sad": ["sad", "down", "depressed", "melancholic", "heartbroken", "not feeling good", "upset", "bad", "lonely", "stressed", "miserable", "empty", "blue", "low", "emotional", "feeling down"]
        }
        
        mood_scores = {mood: sum(1 for keyword in keywords if keyword in user_mood)
                       for mood, keywords in mood_keywords.items()}
        
        if "not" in user_mood or "no" in user_mood:
            mood_scores["happy"] = 0  # Reduce false positives for happy mood
        
        return max(mood_scores, key=mood_scores.get) if any(mood_scores.values()) else "happy"

    def search_songs_by_language(self, mood: str, language: str, num_songs: int = 3) -> List[Song]:
        """Enhanced search with randomization and shuffling."""
        try:
            songs = []
            mood_config = self.mood_map[mood][language]
            
            for search_term in mood_config["search_terms"]:
                market = "IN" if language == "hindi" else "US"
                offset = random.randint(0, 50)  # Random offset for variety
                query = f"{search_term}"
                
                try:
                    results = self.spotify.search(
                        q=query,
                        type='track',
                        market=market,
                        limit=10,
                        offset=offset
                    )
                    
                    if results and 'tracks' in results and 'items' in results['tracks']:
                        tracks = results['tracks']['items']
                        random.shuffle(tracks)  # Shuffle for randomness
                        
                        for track in tracks:
                            if len(songs) >= num_songs:
                                break
                            songs.append(self._create_song(track, mood, language))
                
                except Exception as e:
                    print(f"Error during search: {str(e)}")
                    continue
                
                if len(songs) >= num_songs:
                    break
            
            return songs[:num_songs]
        except Exception as e:
            print(f"Error searching songs: {str(e)}")
            return []

    def _create_song(self, track: Dict, mood: str, language: str) -> Song:
        """Create song object."""
        return Song(
            title=track["name"],
            artist=", ".join([artist["name"] for artist in track["artists"]]),
            mood=mood,
            language=language,
            spotify_uri=track["uri"],
            spotify_url=track["external_urls"]["spotify"],
            preview_url=track.get("preview_url", "")
        )

    def get_recommendations(self, mood: str, language: str, num_songs: int = 3) -> List[Song]:
        """Get song recommendations."""
        return self.search_songs_by_language(mood, language, num_songs)

# Initialize the recommender with Spotify credentials
CLIENT_ID = "8b929c8cbee04fe3b0d595867dda9ae1"
CLIENT_SECRET = "955e457253db4dea95f4257dc9b62635"
recommender = MusicRecommender(CLIENT_ID, CLIENT_SECRET)

# Streamlit App
st.title("Song Recommendation System with Voice Input")

# Voice input function
def get_voice_input():
    """Capture voice and return the recognized text"""
    with sr.Microphone() as source:
        st.write("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        try:
            text = recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I didn't catch that. Could you repeat?"
        except sr.RequestError as e:
            return f"Error with the speech recognition service: {e}"

# Create a single row with input, Send button, and voice icon button
col1, col2, col3 = st.columns([4, 1, 1])

with col1:
    # Text input for mood/query
    mood_text = st.text_input("Enter your mood (or use voice input)", "")

with col2:
    # Send button
    if st.button("Send"):
        st.write(f"Sent mood: {mood_text}")

with col3:
    # Voice icon button
    if st.button("🎤"):
        mood_text = get_voice_input()
        st.write(f"You said: {mood_text}")

# Detect mood using the updated method
if mood_text:
    mood = recommender.detect_mood(mood_text)  # Use the detect_mood method for better handling
    language = st.radio("Choose language", ["English", "Hindi"])
    language = language.lower()

    st.write(f"Detected mood: {mood} and language: {language}")

    recommendations = recommender.get_recommendations(mood, language)
    
    st.write("Here are some song recommendations for you:")
    for i, song in enumerate(recommendations, 1):
        col1, col2 = st.columns([3, 4])  # Layout for song name and link
        with col1:
            st.write(f"{i}. {song.title} by {song.artist}")
        with col2:
            st.write(f"[Spotify Link]({song.spotify_url})")

# Running the Streamlit app
if __name__ == "__main__":
    st.write("Interact with the voice input and get personalized song recommendations!")
