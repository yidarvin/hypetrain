import collections
import numpy as np
import pickle as pkl

DataItem = collections.namedtuple('DataItem',
                                  ['name', 'start_offset', 'length', 'data'])


class KaraokeDataLoader(object):
    def __init__(self,
                 data_file,
                 batch_size=24,
                 ignore_percentage=0.05,
                 sample_length=7056):
        self.batch_size = batch_size
        #ignore_percentage defines the area on either end of the song which we want to ignore.
        self.ignore_percentage = ignore_percentage
        self.sample_length = sample_length

        with open(data_file, 'rb') as file:
            self.data = pkl.load(file)
            self.N = len(self.data)
            self.song_lengths = {k: len(d[0]) for k, d in self.data.items()}

    def get_random_batch(self, sample_length=None):
        sample_length = sample_length or self.sample_length
        names = np.random.choice(list(self.data.keys()), self.batch_size)
        lengths = np.array([self.song_lengths[name] for name in names])
        if sample_length == -1:
            starts = [0] * self.batch_size
            sample_lengths = lengths
        else:
            max_start_offsets = (
                (1 - 2 * self.ignore_percentage) * lengths - sample_length)
            start_offsets = np.random.rand(self.batch_size) * max_start_offsets
            starts = (
                self.ignore_percentage * lengths + start_offsets).astype(int)
            sample_lengths = [sample_length] * self.batch_size
        return [
            DataItem(
                name=name,
                start_offset=start,
                length=length,
                data=(self.data[name][0][start:start + length],
                      self.data[name][1][start:start + length]))
            for name, start, length in list(
                zip(names, starts, sample_lengths))
        ]
