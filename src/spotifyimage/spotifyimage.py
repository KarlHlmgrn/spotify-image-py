import requests
import string
import random
import base64
import six
import qrcode
import socket
import threading
import time
from typing import Optional, Union, Tuple
from PIL import Image
from .clienthandler import create_app
from urllib.parse import urlencode

class SpotifyUser:
    """
    A class containting a specific Spotify user

    :param client_id: The ID of your Spotify API app
    :type client_id: str
    :param client_secret: The secret of your Spotify API app
    :type client_secret: str
    :param host: The host to start the Client Handler on, either "0.0.0.0" (default, only locally) or "127.0.0.1" (internet)
    :type host: str
    :param port: The port to listen on
    :type port: int
    :param refresh_token: Only use if you have a refresh token from Spotify API
    :type refresh_token: str
    """

    def __init__(self, client_id: str, client_secret: str, host: str = "0.0.0.0", port: int = 3030, refresh_token = None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._host = host
        self._port = port
        self._access_token = None
        if refresh_token is not None:
            self._refresh_token = refresh_token
            self._fetch_access_token(refresh = True)
        threading.Thread(
            target=lambda: create_app(self).run(
                host = self._host, 
                port = self._port, 
                debug = True, 
                use_reloader = False
            )
        ).start()

    def _get_log_in_link(self) -> Tuple[str, str]:
        """
        :return: A link to Spotify login page for the Client Handler
        :rtype: tuple[str, str]
        """
        OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
        self._state = "".join(random.choices(string.hexdigits, k = 16))
        params = {
            "client_id": self._client_id,
            "response_type": "code",
            "scope": "user-read-playback-state",
            "redirect_uri": f"http://localhost:{self._port}/callback",
            "state": self.state
        }
        return f"{OAUTH_AUTHORIZE_URL}?{urlencode(params)}", self.state

    def _fetch_access_token(self, auth_code = None, refresh = False) -> bool:
        """
        Fetches the access token from the Spotify API either with a authentication code or the stored refresh token

        :param auth_code: The authentication code from the Spotify API
        :type auth_code: str
        :param refresh: If to use the refresh token to fetch the access token
        :type refresh: bool

        :raises AssertionError: If auth_code is None or refresh is True and the stored refresh token is None

        :return: If it was successful or not
        :rtype: bool
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
            six.text_type(self._client_id + ":" + self._client_secret).encode("ascii")
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
        :return: A QR code for the login page
        :rtype: Image.Image
        """
        ip = socket.gethostbyname(socket.gethostname())
        return qrcode.make(f"http://{ip}:{self._port}/login")

    def _get_image_from_url(self, image_url: Union[str, None]) -> Union[Image.Image, None]:
        """
        Returns either the image of the currently playing song or a QR code for the login page associated with the client handler

        :param image_url: the image url to retrieve the image from
        :type image_url: Union[str, None]

        :return: Image or None
        :rtype: Union[Image, None]
        """
        if image_url is None:
            return None
        return Image.open(requests.get(image_url, stream=True).raw)

    def get_currently_playing_state(self) -> Tuple[Union[Image.Image, None], dict]:
        """
        Returns an image and dictionary of the state of the Spotify player.
        If the status code is 204 no song is playing
        Always check the status code first

        :return: Image (or None) and a dictionary of current state of the Spotify player
        :rtype: tuple[Union[Image.Image, None], dict]
        """
        if self._access_token is None or (time.time() - int(self._time_latest_access_token or 0) > 3600 and not self._fetch_access_token(refresh = True)):
            return self._get_log_in_qr_code(), {}
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
            return None, {
                "status_code": response.status_code
            }
        elif response.status_code == 204:
            return self._get_image_from_url(self._latest_image_url), {
                "image_url": self._latest_image_url,
                "is_playing": False,
                "status_code": 204
            }
        data = response.json()
        image_url = data["item"]["album"]["images"][0]["url"]
        self._latest_image_url = image_url
        return self._get_image_from_url(image_url), {
            "image_url": image_url,
            "name": data["item"]["name"],
            "artists": ", ".join([artist["name"] for artist in data["item"]["artists"]]),
            "is_playing": data["is_playing"],
            "volume": data["device"]["volume_percent"],
            "progress_ms": data["progress_ms"],
            "duration_ms": data["item"]["duration_ms"],
            "status_code": response.status_code
        }