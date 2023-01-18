from flask import Flask, redirect, request

def create_app(user):
    """
    Creates a flask app to use as client handler

    :param user: A Spotify User instance
    :type user: spotifyimage.SpotifyUser
    """
    app = Flask(__name__)

    @app.route("/login")
    def login():
        """
        Redirects client to the Spotify login page
        Also saves the state of the session, security measure
        """
        url, user._state = user._get_log_in_link()
        return redirect(url)

    @app.route("/callback")
    def callback():
        """
        Checks if state is correct and shows if it was successful or not
        """
        error = request.args.get("error", default = None)
        auth_code = request.args.get("code", default = None)
        returned_state = request.args.get("state")
        if returned_state != user._state:
            return "Not right state, error"
        if error is not None:
            return f"Authentication Error: {error}"
        user._fetch_access_token(auth_code)
        return "Successfully linked Spotify account to spotifyimage!"

    return app
