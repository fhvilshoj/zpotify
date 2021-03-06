import re
import tekore as tk
import pathlib 
import pickle
import argparse 
import inquirer

def get_config():
    conf_path  = pathlib.Path.home().joinpath('.spotify.cnf')
    return tk.config_from_file(conf_path.as_posix())

def get_user_token():
    config = get_config()
    token_path = pathlib.Path.home().joinpath('.spotify.token.pkl')

    if not token_path.exists():
        user_token = tk.prompt_for_user_token( *config, scope=tk.scope.every)
        with open(token_path.as_posix(), 'wb') as f:
            pickle.dump({'refresh': user_token.refresh_token}, f)
    else:
        with open(token_path.as_posix(), 'rb') as f:
            d = pickle.load(f)
            refresh_token = d['refresh']
        refresher = tk.RefreshingCredentials(*config)
        user_token = refresher.refresh_user_token(refresh_token)
    return user_token

def play_top_k_tracks(spotify, k=10):
    tracks = spotify.current_user_top_tracks(limit=k).items
    spotify.playback_start_tracks([t.id for t in tracks])

def init():
    conf = get_config()
    app_token = tk.request_client_token(*conf[:2])
    spotify = tk.Spotify(app_token)
    spotify.token = get_user_token()
    return spotify

def albums(spotify, args):
    format_str = "%s - %s"
    def artists_str(artists):
        st = "%-30s" % ("; ".join([a.name for a in artists])[:30])
        return st

    albums = [a.album for a in spotify.saved_albums(limit=20).items]
    questions = [
      inquirer.List('choosen',
                    message="What album do you want to hear?",
                    choices=[format_str % (artists_str(a.artists), a.name) for a in albums],
                ),
    ]
    answers     = inquirer.prompt(questions)    
    context_uri = next( (a.uri for a in albums if format_str % (artists_str(a.artists), a.name) == answers['choosen']) )
    spotify.playback_start_context(context_uri)

def playlists(spotify, args):
    playlists = spotify.followed_playlists(limit=50).items
    questions = [
            inquirer.List('choosen',
                message="What playlist do you want to hear?",
                choices=[p.name for p in playlists]
                ),
        ]
    answers = inquirer.prompt(questions)
    context_uri = next( (p.uri for p in playlists if p.name == answers['choosen']) )
    spotify.playback_start_context(context_uri)

def status(spotify, args):
    pb = spotify.playback()
    print("%-15s" % "Playing:", pb.item.name, " by ", "; ".join([a.name for a in pb.item.artists]))
    print("%-15s" % "On device:", pb.device.name)

def next_track(spotify, args):
    spotify.playback_next()

def previous_track(spotify, args):
    spotify.playback_previous()

def analyze(spotify, args):
    playlist = spotify.followed_playlists(limit=1).items[0]
    track = spotify.playlist_items(playlist.id, limit=1).items[0].track
    name = f'"{track.name}" from {playlist.name}'
    if track.episode:
        print(f'Cannot analyse episodes!\nGot {name}.')
    elif track.track and track.is_local:
        print(f'Cannot analyse local tracks!\nGot {name}.')
    else:
        print(f'Analysing {name}...\n')
        analysis = spotify.track_audio_features(track.id)
        print(repr(analysis))

def play(spotify, args):
    spotify.playback_resume()

def pause(spotify, args):
    spotify.playback_pause()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    # Play pause
    p = subparsers.add_parser('play')
    p.set_defaults(func=play)

    p = subparsers.add_parser('pause')
    p.set_defaults(func=pause)

    p = subparsers.add_parser('next')
    p.set_defaults(func=next_track)

    p = subparsers.add_parser('previous')
    p.set_defaults(func=previous_track)

    p = subparsers.add_parser('analyze')
    p.set_defaults(func=analyze)

    p = subparsers.add_parser('albums')
    p.set_defaults(func=albums)

    p = subparsers.add_parser('playlists')
    p.set_defaults(func=playlists)
    
    p = subparsers.add_parser('status')
    p.set_defaults(func=status)

    spotify = init()

    args = parser.parse_args()
    args.func(spotify, args)


