import os
import hashlib
import json
from tqdm import tqdm
import pandas as pd

def md5_hash(x):
    return int(hashlib.md5(x.encode()).hexdigest(), 16)

class Track:
    def __init__(self, track_id, artist_id, **kwargs):
        self.data = {
            **{"id": track_id, "artist_id": artist_id,},
            **kwargs,
        }
    def as_dict(self,):
        return self.data

class RowSplitter:
    def __init__(self, artist_path, output_path, n_shards=16):
        self.n_shards = n_shards
        os.makedirs(output_path, exist_ok=True,)
        self.outs = []
        for i in range(self.n_shards):
            self.outs.append(open(output_path + "/{:02d}.jsons".format(i), "w",))

        self.artists = pd.read_csv(artist_path, index_col=0).to_dict('index')
        self.artists = {k:v['artistId'] for k,v in self.artists.items()}
        # print(self.artists[333396])

    def finish(self,):
        for outs in self.outs:
            outs.close()

    def consume_row(self, row):
        # print(self.artists.to_dict())
        client_id = str(row.Index)
        tracks = [Track(int(track_id), self.artists[int(track_id)]) for track_id in row.list.split(' ')]
        track_target = tracks[-1]
        tracks = tracks[:-1]
        
        shard_idx = md5_hash(client_id) % self.n_shards
        data = {"client_id": client_id, "tracks": list(map(lambda track: track.as_dict(), tracks)), "target": track_target.as_dict()}
        self.outs[shard_idx].write(json.dumps(data) + "\n")


def split_data_to_chunks(input_path, artist_path, output_dir, n_shards=16):
    splitter = RowSplitter( artist_path=artist_path, output_path=output_dir, n_shards=n_shards,)
    print("split_data_to_chunks: {} -> {}".format(input_path, output_dir,))
    for df in tqdm(pd.read_csv(input_path, header=None, chunksize=500000,names=['list'])):
        for row in df.itertuples():
            splitter.consume_row(row)
    splitter.finish()


if __name__ == "__main__":
    likes_csv_path = 'train'
    output_jsons_dir = 'json'
    artist_path = 'track_artists.csv'

    split_data_to_chunks(likes_csv_path, artist_path, output_jsons_dir, n_shards=16)

    # check splitting for correctness
    # _from_input = calculate_unique_clients_from_input(purchases_csv_path)
    # _from_output = calculate_unique_clients_from_output(output_jsons_dir)
    # assert _from_input == _from_output

    # https://www.youtube.com/watch?v=NlNLtPqlCK0