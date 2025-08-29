# Outify
Export Spotify playlists to local m3u playlists

## Howto

Install Spotipy libary (better use venv using the provided requirements.txt)

Create Spotify API credentials (exemple on how to do that is available in the Spotipy API documentation : https://spotipy.readthedocs.io/en/2.25.1/#)
- Set the following environment variables : 
  - SPOTIPY_CLIENT_ID
  - SPOTIPY_CLIENT_SECRET
  - SPOTIPY_REDIRECT_URI

Run the app

```python3 outify.py --dir /path/to/you/local/music/library```

At the first launch, it will open a web browser where you have to authenticate using your Spotify account. Then copy-paste the redirected URL to your terminal and you're good to go !

Playlists starting with "outify-" will be automatically created in your library directory
