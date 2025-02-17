import random
from typing import List, Dict
from dataclasses import dataclass
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

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
            "sad": ["sad", "down", "depressed", "melancholic", "heartbroken", "I am not feeling good", "upset", "bad", "lonely", "stressed"]
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

def main():
    CLIENT_ID = "8b929c8cbee04fe3b0d595867dda9ae1"
    CLIENT_SECRET = "955e457253db4dea95f4257dc9b62635"
    
    try:
        print("=== Spotify Music Recommendation System ===")
        recommender = MusicRecommender(CLIENT_ID, CLIENT_SECRET)
        
        while True:
            user_input = input("\nHow are you feeling? (or type 'quit' to exit): ").lower()
            if user_input == 'quit':
                break
            
            print("\nSelect language for recommendations:")
            print("1) English")
            print("2) Hindi")
            
            while True:
                try:
                    lang_choice = int(input("Enter number (1 or 2): "))
                    if lang_choice in [1, 2]:
                        break
                    print("Please enter 1 or 2.")
                except ValueError:
                    print("Please enter a valid number.")
            
            language = "english" if lang_choice == 1 else "hindi"
            mood = recommender.detect_mood(user_input)
            print(f"\nDetected mood: {mood}")
            print("Searching for songs...")
            
            recommendations = recommender.get_recommendations(mood, language)
            
            if recommendations:
                print("\nHere are some songs you might enjoy:")
                for i, song in enumerate(recommendations, 1):
                    print(f"\n{i}. {song.title} by {song.artist}")
                    print(f"   Listen on Spotify: {song.spotify_url}")
                    if song.preview_url:
                        print(f"   Preview URL: {song.preview_url}")
            else:
                print("\nSorry, couldn't find recommendations. Please try again.")
            
            print("\n" + "=" * 40)
    
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Please check your Spotify credentials and internet connection.")
    except KeyboardInterrupt:
        print("\nThank you for using the Spotify Music Recommendation System!")

if __name__ == "__main__":
    main()
