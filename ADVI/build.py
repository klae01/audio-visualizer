import av
import os

from .visualize import convert as v_convert
from .config import ADVI_CONFIG


def convert(config: ADVI_CONFIG):
    output = av.open(config.output_file, "w")
    ovstream = output.add_stream("libx264rgb", config.fps)
    ovstream.pix_fmt = "rgb24"
    ovstream.width = config.width
    ovstream.height = config.height
    oastream = output.add_stream("aac")

    v_frames = (
        av.VideoFrame.from_ndarray(img, format="rgb24") for img in v_convert(config)
    )
    v_frames = (ovstream.encode(frame) for frame in v_frames)

    for img_packet in v_frames:
        output.mux(img_packet)

    container = av.open(config.input_file, "r")
    stream = container.streams.audio[0]
    for packet in container.demux((stream,)):
        for frame in packet.decode():
            a_frames = oastream.encode(frame)
            output.mux(a_frames)

    output.mux(ovstream.encode())
    output.mux(oastream.encode())
    output.close()

    # os.system(f"ffmpeg -i intermediate.mp4 -i {config.input_file} -c:v copy -c:a aac {config.output_file} && rm intermediate.mp4 ")
