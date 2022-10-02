import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

slack_conversation_limit = 100

#---------------------------------------
# SLACK
#---------------------------------------

def get_chat_history(client, channel_id, cursor=None):
    result = {}
    try:
        convo_list = []
        next_cursor = ""
        response = client.conversations_history(channel=channel_id, limit=slack_conversation_limit, cursor=cursor)

        for c in response["messages"]:
            if 'message' == c["type"]:
                # filter only spotify related messages
                if 'spotify' in c["text"]:
                    convo_list.append(c["text"])

        if response["has_more"]:
            next_cursor = response["response_metadata"]["next_cursor"]

        result['cursor'] = next_cursor
        result['conversations'] = convo_list
    except SlackApiError as e:
        print(e)
        result['error'] = e.response

    return result


def send_message(client, channel_id, message):
    try:
        response = client.chat_postMessage(channel=channel_id, text=message)
        print("msg successful")
    except SlackApiError as e:
        print(e)

    print("sleeping for 2 secs")
    time.sleep(2)

def build_slack_client():
    slack_token = os.getenv('SLACK_TOKEN')
    client = WebClient(token=slack_token)
    try:
        test_response = client.api_test()
    except SlackApiError as e:
        print(e)
        return None
    return client

#---------------------------------------
# SPOTIFY
#---------------------------------------

def get_spotify_client():
    spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
    spotify_secret = os.getenv('SPOTIFY_SECRET')

    # in order to modify playlist - must use user authorization path instead of client credentials
    scope = 'playlist-modify-public user-library-read playlist-modify-private'
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=spotify_client_id,
                                                   client_secret=spotify_secret,
                                                   redirect_uri='http://localhost',
                                                   scope=scope))

    return sp

def extract_spotify_link(raw_text):
    result = {}

    # print(f"raw: {raw_text}")
    if ('<' in raw_text) & ('>' in raw_text):
        # this is probably a spotify url, extract the url
        link = raw_text.split('<')
        link2 = link[1].split('>')
        spotify_link = link2[0]

        if 'spotify' in spotify_link:
            split_url = spotify_link.split('/')
            spotify_id_raw = split_url[4].split('?')
            spotify_id = spotify_id_raw[0]
            link_type = 'invalid'

            # https://open.spotify.com/album/2suR5CCbtL2Wq8ShFo8rFr?si=HSr9Q1PfT1qehjhfEWqVlQ
            if 'album' in spotify_link:
                link_type = 'album'
            # https://open.spotify.com/track/0X6iBhJmxTgJU5qKwqumMb?si=2ghBOUw2S1ShrR7qY5xrAA&context=spotify%3Aplaylist%3A3gtlfEFu92Bw4a07e3PUxS
            if 'track' in spotify_link:
                link_type = 'track'

            if link_type != 'invalid':
                return {"type": link_type, "id": spotify_id}

    return result

def get_spotify_tracks(client, prev_result):
    result = []
    # lets see if the current text has what we need
    if 'album' == prev_result["type"]:
        r = client.album_tracks(album_id=prev_result['id'])

        items = r["items"]
        for track in items:
            formatted_id = f"spotify:track:{track['id']}"
            #print(track)
            #print(f"popularity: {track['popularity']}")
            result.append(formatted_id)

    if 'track' == prev_result["type"]:
        formatted_id = f"spotify:track:{prev_result['id']}"
        result.append(formatted_id)

    return result

def add_spotify_tracks(client, spotify_playlist_id, list_tracks):
    r = client.playlist_add_items(playlist_id=spotify_playlist_id, items=list_tracks)
    print(f"adding {len(list_tracks)} to playlist...")

#---------------------------------------
# MAIN EXECUTION
#---------------------------------------

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    spotify_client = get_spotify_client()
    my_slack_client = build_slack_client()
    source_slack_channel = os.getenv('SOURCE_SLACK_CHANNEL')
    target_slack_channel = os.getenv('TARGET_SLACK_CHANNEL')

    #https://open.spotify.com/playlist/14PbUU74QbiyWEN1QTYZyw?si=db868b9731bf4218
    spotify_playlist_id = os.getenv('SPOTIFY_PLAYLIST_ID')

    spotify_set_list = set()

    my_cursor = ''
    is_first = True
    counter = 0;

    while is_first | len(my_cursor) > 0:
        is_first = False
        print("getting chat history...")
        results = get_chat_history(my_slack_client, source_slack_channel, my_cursor)

        if results.get("error"):
            print("got error. exiting")
            break

        print(f"got {len(results['conversations'])} messages...")

        for c in results['conversations']:
            # send_message(my_slack_client, target_slack_channel, c)
            ex_result = extract_spotify_link(c)
            if 'type' in ex_result.keys():
                track_list = get_spotify_tracks(spotify_client, ex_result)
                counter += len(track_list)
                for track in track_list:
                    spotify_set_list.add(track)

        my_cursor = results['cursor']
        if my_cursor:
            print(f"got next cursor: {my_cursor}")

    print(f"adding {len(spotify_set_list)} of {counter} tracks to playlist...")

    sub_list = []
    for set_track in spotify_set_list:
        sub_list.append(set_track)
        if len(sub_list) > 50:
            add_spotify_tracks(spotify_client, spotify_playlist_id, sub_list)
            sub_list = []
    # add everything else
    add_spotify_tracks(spotify_client, spotify_playlist_id, sub_list)

    print("done.")
