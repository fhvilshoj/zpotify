import re
import tekore as tk
import pathlib 
import pickle
import argparse 

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

    spotify = init()

    args = parser.parse_args()
    args.func(spotify, args)


