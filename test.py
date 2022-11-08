from inky.auto import auto
from spotifyimage import SpotifyUser
from time import sleep

display = auto()

user = SpotifyUser("08cc3846fc9642eab3c13529f9fd51a5", "1358882b916248d98bc662363cb2f33e", "127.0.0.1")

while True:
    img, data = user.get_currently_playing_state()
    img = img.resize(display.resolution)
    display.set_image(img)
    display.show()
    sleep(5)