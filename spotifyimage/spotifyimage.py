import requests
import string
import random
import base64
import six
import qrcode
import socket
import threading
import time
from PIL import Image
from .clienthandler import create_app
from urllib.parse import urlencode

class SpotifyUser:
    """
    A class containting a specific Spotify user

    Params:
        client_id: str
            The ID of your Spotify API app
        client_secret: str
            The secret of your Spotify API app
        host: str
            The host to start the Client Handler on, either "0.0.0.0" (default, only locally) or "127.0.0.1" (internet)
        port: int
            The port to listen on
            (Default: 3030)
        refresh_token: str
            Only use if you have a refresh token from Spotify API
    """

    CLIENT_ID = None
    CLIENT_SECRET = None
    HOST = None
    PORT = None

    state = None
    _access_token = None
    _refresh_token = None
    _time_latest_access_token = 0
    _latest_image_url = None

    def __init__(self, client_id: str, client_secret: str, host: str = "0.0.0.0", port: int = 3030, refresh_token = None):
        """
        Initialize a user instance and start the Client Handler
        """
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.HOST = host
        self.PORT = port
        if refresh_token is not None:
            self._refresh_token = refresh_token
            self._fetch_access_token(refresh = True)
        threading.Thread(
            target=lambda: create_app(self).run(
                host = self.HOST, 
                port = self.PORT, 
                debug = True, 
                use_reloader = False
            )
        ).start()

    def _get_log_in_link(self) -> tuple[str, str]:
        """
        Returns a link to Spotify login page for the Client Handler

        Returns: tuple[str, str]
        """
        OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
        self.state = "".join(random.choices(string.hexdigits, k = 16))
        params = {
            "client_id": self.CLIENT_ID,
            "response_type": "code",
            "scope": "user-read-playback-state",
            "redirect_uri": f"http://localhost:{self.PORT}/callback",
            "state": self.state
        }
        return f"{OAUTH_AUTHORIZE_URL}?{urlencode(params)}", self.state

    def _fetch_access_token(self, auth_code = None, refresh = False) -> bool:
        """
        Fetches the access token from the Spotify API either with a authentication code or the stored refresh token

        Params:
            auth_code: str
                The authentication code from the Spotify API
            refresh: bool
                If to use the refresh token to fetch the access token

        Returns: bool
            If true it was successful, otherwise it failed

        Exception:
            AssertionError:
                Raised if auth_code is None or refresh is True and the stored refresh token is None
        """
        OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"
        assert auth_code is not None or (refresh and self._refresh_token is not None)
        params = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": f"http://localhost:{self.PORT}/callback"
        }
        if refresh:
            params = {
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token
            }
        auth_header = base64.b64encode(
            six.text_type(self.CLIENT_ID + ":" + self.CLIENT_SECRET).encode("ascii")
        )
        headers = {
            "Authorization": "Basic %s" % auth_header.decode("ascii"),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(
            url = OAUTH_TOKEN_URL,
            params = params,
            headers = headers
        )
        if response.status_code != 200:
            return False
        data = response.json()
        self._access_token = data["access_token"]
        self._refresh_token = data["refresh_token"]
        self._time_latest_access_token = time.time()
        return True

    def _get_log_in_qr_code(self) -> Image.Image:
        """
        Returns a QR code for the login page

        Returns: instance of Image.Image
        """
        ip = socket.gethostbyname(socket.gethostname())
        return qrcode.make(f"http://{ip}:{self.PORT}/login")

    def _get_currently_playing_image(self) -> Image.Image:
        """
        Returns: Image | None
            Image: Is either the image of the currently playing song or a QR code for the login page associated with the client handler
            None: If no image could be found
        """
        data = self.get_currently_playing_state()
        image_url = data["image_url"]
        if image_url is None:
            return None
        return Image.open(requests.get(image_url, stream=True).raw)

    def get_currently_playing_state(self) -> dict:
        """
        Returns a dictionary of the state of the Spotify player.
        If the status code is 204 no song is playing
        
        Returns: dict

        If the status code is 200:
        returns dict {
            "image_url": str,
            "name": str,
            "artists": str,
            "is_playing": bool,
            "volume": int,
            "progress_ms": int,
            "duration_ms": int,
            "status_code": int
        }

        If the status code is 204:
        returns dict {
            "image_url": str | None,
            "is_playing": bool,
            "status_code": int
        }

        If neither
        returns dict {
            "status_code": int
        }
        """
        if (time.time() - self._time_latest_access_token > 3600 and not self._fetch_access_token(refresh = True)) or self._access_token is None:
            return self._get_log_in_qr_code()
        CURRENTLY_PLAYING_URL = "https://api.spotify.com/v1/me/player"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self._access_token
        }
        response = requests.get(
            url = CURRENTLY_PLAYING_URL,
            headers = headers
        )
        if response.status_code not in (200, 204):
            return {
                "status_code": response.status_code
            }
        elif response.status_code == 204:
            return {
                "image_url": self._latest_image_url,
                "is_playing": False,
                "status_code": 204
            }
        data = response.json()
        image_url = data["item"]["album"]["images"][0]["url"]
        self._latest_image_url = image_url
        return {
            "image_url": image_url,
            "name": data["item"]["name"],
            "artists": ", ".join([artist["name"] for artist in data["item"]["artists"]]),
            "is_playing": data["is_playing"],
            "volume": data["device"]["volume_percent"],
            "progress_ms": data["progress_ms"],
            "duration_ms": data["item"]["duration_ms"],
            "status_code": response.status_code
        }