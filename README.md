# Slack To Spotify Playlist
this python script attempts to read a slack channel and extract all the mentions of spotify tracks or albums and adds it to a spotify playlist

## Getting Started
1. take a look at `.env.example`, create a `.env` in the folder
2. fill out the values
   1. `slack_token` - can be obtained by creating an app using https://api.slack.com/apps
      1. under "Your Apps" > "OAuth & Permissions", you will find "User OAuth Token"
      2. need to add `channels:history`, `channels:read`, `chat:write`, `groups:history`, `im:history`, `mpim:history` to the "User Token Scopes"
   2. `source_slack_channel` - is the slack channel that you want to read. the id can be obtained by right-clicking on the channel in the slack app, choosing "Copy" > "Copy Link"
      1. you will get something like: `https://some-sub-domain.slack.com/archives/C044HP96123`, `C044HP96123` is your slack channel id
   3. `target_slack_channel` - this is no longer required, it was used for when i wanted to replay the messages to another channel in order to trigger pipedream workflows
   4. `spotify_playlist_id` - the id of the spotify playlist, this can be obtained by going to your public playlist (you must have access to modify this), clicking on the 3 dots, choosing "Share" > "Copy link to playlist"
      1. you will get something like: `https://open.spotify.com/playlist/14PbUU74QbiyWEN1123456?si=7cdf058253ab4422`, `14PbUU74QbiyWEN1123456` is your playlist id
   5. `spotify_client_id`, `spotify_secret` - these will be required to connect to spotify, since we are modifying a playlist, we will need to use the user authorization flow and not the client credential
      1. goto https://developer.spotify.com/ and login
      2. click on "Dashboard" and then "Create an App"
      3. Name the app whatever you want, you should now have access to a `Client ID` and "Show Client Secret"
      4. Click on "Edit Settings" to add a redirect url as `http://localhost`

## Usage
1. run `main.py` using your IDE or command-line via `python main.py`
2. you will eventually be asked to connect your account to Spotify, this will then redirect that browser to something that will error out.
3. Take the url that has errored out and paste it back into the terminal
4. the script should finish and output some basic stats