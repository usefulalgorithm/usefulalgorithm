from dataclasses import dataclass
import os
import sys
from typing import Any, Dict, List, Literal, Self, Tuple
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from loguru import logger


@dataclass
class Album:
    name: str
    artists: List[str]

    @classmethod
    def from_track(cls, track: Dict[str, Any]) -> Self:
        return Album(
            name=track["album"]["name"],
            artists=[artist["name"] for artist in track["album"]["artists"]],
        )


def _get_albums_from_tracks(tracks: List) -> List[Album]:
    return list(
        {track["album"]["id"]: Album.from_track(track) for track in tracks}.values()
    )


def _get_latest_albums(sp: spotipy.Spotify) -> List[Album]:
    # FIXME Spotify's `current_user_recently_played` only returns the most recent 50 songs, pagination is there
    # but doesn't really do anything.
    # https://community.spotify.com/t5/Spotify-for-Developers/Now-that-users-can-view-their-recently-played-tracks-in-the-apps/m-p/5181981
    return _get_albums_from_tracks(
        [it["track"] for it in sp.current_user_recently_played().get("items", [])]
    )


def _get_top_albums(
    sp: spotipy.Spotify, time_range: Literal["short_term", "medium_term", "long_term"]
) -> List[Album]:
    tracks = []
    offset = 0
    while True:
        response = sp.current_user_top_tracks(
            limit=50,
            offset=offset,
            time_range=time_range,
        )
        offset += response["total"]
        batch_items = response.get("items", [])
        if not batch_items:
            break
        tracks.extend(batch_items)
    return _get_albums_from_tracks(tracks)


def check_spotify() -> Tuple[List[Album], List[Album]]:
    """
    Returns the most recent albums I listened and top albums for the past month.
    """
    # Check env variables, load from env file if any of these do not exist
    variable_keys = [
        "SPOTIPY_CLIENT_ID",
        "SPOTIPY_CLIENT_SECRET",
        "SPOTIPY_REDIRECT_URI",
        "SPOTIPY_REFRESH_TOKEN",
    ]
    if any(k not in os.environ for k in variable_keys):
        load_dotenv()

    # Exit if any env variable is missing
    for k in variable_keys:
        if k not in os.environ:
            logger.error(f"Cannot find variable: {k}")
            sys.exit(1)

    auth_manager = SpotifyOAuth(
        show_dialog=False,
        scope=[
            "user-read-recently-played",
            "user-top-read",
        ],
    )
    # Use refresh_token to get new access token so that it doesn't need to validate
    # via browser.
    token_info = auth_manager.refresh_access_token(os.environ["SPOTIPY_REFRESH_TOKEN"])
    access_token = token_info["access_token"]
    sp = spotipy.Spotify(auth=access_token)

    latest_albums = _get_latest_albums(sp)
    logger.debug(latest_albums)

    top_albums = _get_top_albums(sp, "short_term")
    logger.debug(top_albums)

    return latest_albums, top_albums
