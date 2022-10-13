# spotify-image-py
### Simple library to get currently playing song from Spotify, optimal for small projects
---
- Do you need a simple way to get the cover art of the song you are currently listening to? 
- Are you tired of having to code everything by yourself?  
  
##### Look no further as spotify-image-py is the solution!
---
### Spotify-image-py is perfect for:
- Raspberry Pi projects
- E-ink displays
- And everything else you can think of
### What makes spotify-image-py different?  
Spotify-image-py uses Spotify's proprietary API to log you safely into the application via a QR-code.
---
### Well, how do I get started?  
Create a new application at https://developer.spotify.com/dashboard/ and copy your client ID as well as client secret.
Then you simply use spotify-image-py as such:
``` python
from spotifyimage import SpotifyUser
from PIL import Image

spotify_user = SpotifyUser(client_id, client_secret, "0.0.0.0", 3030)

spotify_user.get_currently_played_image().show()
```
##### And ta-da you have now created your first program using spotify-image-py.
---
### Limitations  
Spotify-image-py cannot store your access token between different sessions. You will have to log in every time your restart your script.
### Issues and contributions  
Please log issues here on GitHub and contribute if you can!
