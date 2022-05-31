import functools
from queue import PriorityQueue

import numpy as np
import scipy.io.wavfile as wav
import scipy.signal

iso226_base = 40
iso226_freq = np.array([
           20. ,    25. ,    31.5,    40. ,    50. ,    63. ,    80. ,
          100. ,   125. ,   160. ,   200. ,   250. ,   315. ,   400. ,
          500. ,   630. ,   800. ,  1000. ,  1250. ,  1600. ,  2000. ,
         2500. ,  3150. ,  4000. ,  5000. ,  6300. ,  8000. , 10000. ,
        12500. , 20000. ])
iso226_espl = np.array([
        99.85392334, 93.94441144, 88.16590253, 82.62867609, 77.78487094,
        73.08254532, 68.47788682, 64.37114939, 60.58550325, 56.70224677,
        53.40873978, 50.3992414 , 47.5774866 , 44.97662259, 43.05067937,
        41.339195  , 40.06176083, 40.01004637, 41.81945508, 42.50756876,
        39.2296391 , 36.50900986, 35.60891914, 36.64917709, 40.00774113,
        45.82828132, 51.79680693, 54.28413025, 51.48590719, 99.85392334])


@functools.lru_cache(maxsize=4)
def get_sri(frequencies):  # sound recognition intensity
    upp_index = np.minimum(
        np.searchsorted(iso226_freq, frequencies, "left"), len(iso226_freq) - 1
    )
    low_index = np.where(upp_index == 0, 1, upp_index - 1)
    sri = (
        iso226_espl[upp_index] * (frequencies - iso226_freq[low_index])
        + iso226_espl[low_index] * (iso226_freq[upp_index] - frequencies)
    ) / (iso226_freq[upp_index] - iso226_freq[low_index])
    sri = 10 ** ((iso226_base - sri) / 10)
    return sri


def convert(data: np.ndarray):
    # data shape = [F, T]
    # data dtype = np.complex
    data.mean()


def det_width(power, volume, minimum):
    # Determination of width by frequency
    share = power / power.sum()
    l, m, r = 0, 0, 1
    for _ in range(60):
        m = (l + r) / 2
        if volume > np.maximum(np.floor_divide(share, m), minimum).sum():
            r = m
        else:
            l = m
    crit = l
    width = np.maximum(np.floor_divide(share, crit), minimum).astype(np.int32)
    remain_volume = volume - width.sum()
    if remain_volume > 0:
        remains = share - crit * width
        PQ = PriorityQueue()
        for i, I in enumerate(remains):
            PQ.put((-I, i))
        for _ in range(remain_volume):
            V, idx = PQ.get()
            width[idx] += 1
            PQ.put((V + crit, idx))

    assert volume == width.sum()
    return width


def convert(config):
    active_height = config.height - 2 * config.height_pad
    active_width = config.width - 2 * config.width_pad
    active_color = np.asarray(config.color, dtype=np.uint8)

    samplerate, samples = wav.read(config.input)
    if len(samples.shape) > 1:
        samples = samples[..., 0]
    frequencies, times, spectrogram = scipy.signal.stft(
        samples, samplerate, nperseg=config.nperseg
    )
    spectrogram = abs(spectrogram)
    indices = np.searchsorted(
        times, np.linspace(0, times[-1], int(times[-1] * config.fps)), side="left"
    )
    frame_datas = np.split(spectrogram, indices[1:-1], axis=1)
    F_power = np.stack([I.mean(axis=1) for I in frame_datas], axis=1)
    HPI = get_sri(tuple(frequencies.tolist()))
    F_width = det_width(
        HPI, active_width - (len(frequencies) - 1) * config.margin, config.minimum_width
    )

    T_power = (F_power * HPI[..., None]).sum(axis=0)
    idx_low, idx_upp = [int(len(T_power) * x) for x in [0.925, 0.975]]
    alpha = (
        np.partition(T_power, [idx_low, idx_upp])[idx_low : idx_upp + 1].mean()
        / 1.6622070511355758
    )

    dtype = np.int32
    info = np.iinfo(dtype)
    F_power *= active_height / alpha / 2
    F_power = np.clip(F_power, info.min, info.max).astype(dtype)

    arr = np.zeros((config.height, config.width, 3), dtype=np.uint8)
    try:
        assert not config.quite
        import tqdm

        RNG = tqdm.trange(F_power.shape[1])
    except:
        RNG = range(F_power.shape[1])
    for i in RNG:
        F_slice = F_power[:, i]
        arr[...] = 0
        write_x = config.width_pad
        for power, width in zip(F_slice, F_width):
            arr[
                config.height // 2 - power : config.height // 2 + power,
                write_x : write_x + width,
            ] = active_color
            write_x += width + config.margin
        yield arr
