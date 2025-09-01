import base64
import threading
import time
import traceback
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Literal

import requests
from gevent import queue, lock
from playwright.sync_api import sync_playwright

import const
from helpers import css_escape

shared_event_queues = set()
queue_lock = lock.RLock()


@dataclass
class SpotifyState:
    track_id: str
    song_title: str
    artist: str
    cover_url: str
    duration_ms: int
    progress_ms: int
    is_playing: bool
    song_url: str
    polled_at: float

    def __eq__(self, other):
        # check if this is the same song
        if other is None:
            return False
        if not isinstance(other, SpotifyState):
            return False
        return (self.track_id == other.track_id and
                self.artist == other.artist and
                self.cover_url == other.cover_url)


def get_access_token(token_type: Literal["main", "fallback"]):
    if token_type == "main":
        refresh_token = const.SPOTIFY_REFRESH_TOKEN
        client_id = const.SPOTIFY_CLIENT_ID
        client_secret = const.SPOTIFY_CLIENT_SECRET
    else:
        refresh_token = const.SPOTIFY_FALLBACK_REFRESH_TOKEN
        client_id = const.SPOTIFY_FALLBACK_CLIENT_ID
        client_secret = const.SPOTIFY_FALLBACK_CLIENT_SECRET

    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    try:
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        if response.status_code == 404:
            return None, 0
        data = response.json()
        return data.get("access_token"), time.time() + data.get("expires_in", 3600)
    except requests.RequestException as e:
        print(f"Error refreshing access token for {token_type}: {e}")
        return None, 0


def get_account_bearer() -> (str, int) or None:
    # spotify keeps changing how their web player api works, this is normally *not* meant to be used by scripts,
    # and they are intentionally making it more difficult for programs
    try:
        result = {"token": None, "expires": None}
        done_event = threading.Event()
        closing = False

        def callback(response):
            if closing:
                return
            if response.url.startswith("https://open.spotify.com/api/token?"):
                if response.status == 200:
                    json_data = response.json()
                    result["token"] = json_data.get("accessToken")
                    result["expires"] = json_data.get("accessTokenExpirationTimestampMs") / 1000
                    done_event.set()
                else:
                    print(f"failed to get account bearer: {response.status} {response.text()}")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            context.add_cookies([{
                "name": "sp_dc",
                "value": const.SPOTIFY_ACCOUNT_DC,
                "domain": ".spotify.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax"
            }])
            page = context.new_page()
            page.on("response", callback)
            page.goto("https://open.spotify.com/intl-de/")

            done_event.wait(timeout=10)
            closing = True
            browser.close()

        if result["token"] and result["expires"]:
            return result["token"], result["expires"]
        return None, 0
    except Exception as e:
        print(f"Error getting account bearer: {e}")
        return None, 0


def fetch_lyrics(track_id: str, retried=False) -> dict[float, int] | None:
    global account_bearer, account_bearer_expires
    if time.time() > account_bearer_expires - 60:
        print("Account bearer expired or is close to expiring, refreshing...")
        account_bearer, account_bearer_expires = get_account_bearer()
        if not account_bearer:
            return None

    try:
        req = requests.get(
            f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{track_id}",
            headers={
                "Authorization": f"Bearer {account_bearer}",
                "app-platform": "WebPlayer",
                'spotify-app-version': '1.2.60.334.g09ff0619',
                "User-Agent": ""
            },
            params={
                "format": "json",
                "vocalRemoval": "false"
            }
        )
        if req.status_code in (401, 403) and not retried:
            account_bearer, account_bearer_expires = get_account_bearer()
            return fetch_lyrics(track_id, retried=True)
        if req.status_code == 404:
            return None
        req.raise_for_status()
        json_data = req.json()
    except (requests.exceptions.RequestException, JSONDecodeError) as e:
        print(f"Failed to fetch lyrics for {track_id}: {e}")
        return None

    lyric_data = json_data.get("lyrics")
    if not lyric_data or lyric_data.get("syncType") != "LINE_SYNCED":
        return None

    lines = {0.0: "♪"}
    for line in lyric_data.get("lines", []):
        words = line.get("words", "").strip()
        if not words:
            continue
        if "♪" not in words:
            words = "♪ " + words
        lines[int(line["startTimeMs"]) / 1000] = words

    return dict(sorted(lines.items()))


def get_spotify_status(token: str) -> dict | None:
    try:
        response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 204:  # no content, nothing playing
            return None
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error getting Spotify status: {e}")
        # rate limiting
        if e.response and e.response.status_code == 429:
            retry_after = max(e.response.headers.get("Retry-After", 3), 3)
            if retry_after > 1000:
                print("We are being rate limited for too long, using fallback")
                global current_token
                if current_token == "main":
                    current_token = "fallback"
                else:
                    current_token = "main"
            print(f"Rate limited. Waiting for {retry_after} seconds.")
            time.sleep(retry_after)
        return None


def build_not_playing_css() -> str:
    return """
    <style>
        .notification-content { display: none; }
        .not-playing { display: flex; }
    </style>
    """


def build_static_css(state: SpotifyState) -> str:
    return f"""
    <a href="{state.song_url}" class="open-song" target="_blank"><div><img src="/assets/open.svg" alt="Open"></div></a>
    <style>
        .notification-content {{ display: flex; }}
        .not-playing {{ display: none; }}
        .song-title::before {{ content: '{css_escape(state.song_title)}'; }}
        .song-artist::before {{ content: '{css_escape(state.artist)}'; }}
        .album-cover {{ background-image: url(/spotify-cover.png?h={hash(state.cover_url)}); }}
        .song-length::before {{ content: '{state.duration_ms // 60000}:{(state.duration_ms // 1000) % 60:02d}'; }}
    </style>
    """


def build_progress_css(state: SpotifyState) -> str:
    progress_s = state.progress_ms / 1000 + (time.time() - state.polled_at if state.is_playing else 0)
    duration_s = state.duration_ms / 1000
    remaining_s = max(0.0, duration_s - progress_s)
    unique_id = str(time.time()).replace(".", "")

    progress_keyframes = ""
    if state.is_playing:
        progress_keyframes = f"""
        @keyframes progress{unique_id} {{
            to {{ width: 100%; }}
        }}
        """

    seconds_keyframes = []
    minutes_keyframes = []
    # generate keyframes for a 10s timer
    for i in range(11):
        # if paused, keep the timer at the current progress
        current_progress_tick = progress_s + i if state.is_playing else progress_s
        if current_progress_tick > duration_s:
            current_progress_tick = duration_s

        seconds_keyframes.append(
            f"{i * 10}% {{ counter-increment: seconds{unique_id} {int(current_progress_tick) % 60}; }}")
        minutes_keyframes.append(
            f"{i * 10}% {{ counter-increment: minutes{unique_id} {int(current_progress_tick) // 60}; }}")

    return f"""
    <style>
        .progress-bar::before {{
            width: {progress_s * 100 / duration_s}%;
            animation: progress{unique_id} {remaining_s}s linear forwards;
        }}
        {progress_keyframes}

        .seconds-progress::before {{
            content: "0" counter(seconds{unique_id});
            animation: countSeconds{unique_id} 10s steps(10) forwards;
        }}
        @keyframes countSeconds{unique_id} {{ {" ".join(seconds_keyframes)} }}

        .minutes-progress::before {{
            content: "0" counter(minutes{unique_id});
            animation: countMinutes{unique_id} 10s steps(10) forwards;
        }}
        @keyframes countMinutes{unique_id} {{ {" ".join(minutes_keyframes)} }}

        .paused {{ visibility: {"hidden" if state.is_playing else "visible"}; }}
    </style>
    """


def build_lyrics_css(lyrics: dict[float, int], state: SpotifyState) -> str:
    if not lyrics or not state.is_playing:
        return "<style>.song-lyrics { display: none; }</style>"

    progress_s = state.progress_ms / 1000 + (time.time() - state.polled_at)
    duration_s = state.duration_ms / 1000
    unique_id = str(time.time()).replace(".", "")

    css = [
        f".song-lyrics::after {{ animation: lyrics{unique_id} {duration_s}s steps(1) forwards; animation-delay: {-progress_s}s; }}",
        f"@keyframes lyrics{unique_id} {{"
    ]
    for ts, line in lyrics.items():
        percentage = ts * 100 / duration_s
        css.append(f"{percentage:.4f}% {{ content: '{css_escape(line)}'; }}")
    css.append("}")
    css.append(".song-lyrics { display: block; }")
    return f"<style>{' '.join(css)}</style>"


def event_reader(start_html: str, skip_rest=False):
    yield start_html
    # new clients get the base state first and refresh later over the meta tag
    if last_state is None:
        yield build_not_playing_css()
    else:
        yield build_static_css(last_state)
        yield build_progress_css(last_state)
        if current_lyrics:
            yield build_lyrics_css(current_lyrics, last_state)
        else:
            yield "<style>.song-lyrics { display: none; }</style>"

    if skip_rest:
        return

    event_queue = queue.Queue(maxsize=20)
    with queue_lock:
        shared_event_queues.add(event_queue)

    try:
        while True:
            try:
                event = event_queue.get(timeout=10)
                if event is None:
                    break
                yield event
            except queue.Empty:
                yield " \n"  # keep connection alive
    finally:
        with queue_lock:
            shared_event_queues.discard(event_queue)


def event_writer(event: str):
    with queue_lock:
        # use a copy to avoid issues with modifying the set while iterating
        for q in list(shared_event_queues):
            try:
                q.put_nowait(event)
            except queue.Full:
                shared_event_queues.discard(q)


def spotify_status_updater():
    global access_token, expires_on, current_token, current_lyrics, cover_bytes, last_cover_url, last_state

    while True:
        try:
            if time.time() > expires_on - 60:
                access_token, expires_on = get_access_token(current_token)
                if not access_token:
                    print(f"Failed to get a valid token for {current_token}. Retrying in 30s.")
                    time.sleep(30)
                    continue

            status = get_spotify_status(access_token)

            if not status or not status.get("item"):
                if last_state is not None:
                    not_playing_css = build_not_playing_css()
                    event_writer(not_playing_css)
                    last_state = None
                    current_lyrics = None
                time.sleep(5)  # poll less frequently when idle
                continue

            current_state = SpotifyState(
                track_id=status["item"]["id"],
                song_title=status["item"]["name"],
                artist=", ".join(artist["name"] for artist in status["item"]["artists"]),
                cover_url=status["item"]["album"]["images"][0]["url"],
                duration_ms=status["item"]["duration_ms"],
                progress_ms=status.get("progress_ms", 0),
                is_playing=status["is_playing"],
                song_url=status["item"]["external_urls"]["spotify"],
                polled_at=time.time()
            )

            # song has changed
            if current_state != last_state:
                current_lyrics = None  # Reset lyrics for new song

                # update cover bytes if urt changed
                if current_state.cover_url != last_cover_url:
                    try:
                        cover_bytes = requests.get(current_state.cover_url).content
                        last_cover_url = current_state.cover_url
                    except requests.RequestException:
                        cover_bytes = None

                # send a full update with static info
                full_update_css = build_static_css(current_state)
                event_writer(full_update_css)

                # fetch and send lyrics as a separate update to not make the client wait
                lyrics = fetch_lyrics(current_state.track_id)
                if lyrics:
                    current_lyrics = lyrics
                    lyrics_update_css = build_lyrics_css(current_lyrics, current_state)
                    event_writer(lyrics_update_css)
                else:
                    # hide lyrics section if none are found
                    event_writer("<style>.song-lyrics { display: none; }</style>")

            last_state = current_state
            # always send a progress update to keep things synced
            progress_update_css = build_progress_css(current_state)
            event_writer(progress_update_css)

            time.sleep(2)  # regular poll interval

        except Exception:
            traceback.print_exc()
            time.sleep(5)


def get_cover_bytes():
    return cover_bytes


access_token: str | None = None
expires_on: float = 0
account_bearer: str | None = None
account_bearer_expires: float = 0
current_token: Literal["main", "fallback"] = "main"
current_lyrics: dict[float, int] | None = None
cover_bytes: bytes | None = None
last_cover_url: str | None = None
last_state: SpotifyState | None = None
