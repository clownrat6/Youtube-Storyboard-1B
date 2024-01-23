import argparse
import os

import pandas as pd
from tqdm import tqdm


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, default="dataset/yt-1b/yttemporal1b_ids_train.csv", help="youtube id input path")
    parser.add_argument("-o", "--output", type=str, default="dataset/yt-1b/yt1b_urls_train.txt", help="youtube url output path")
    parser.add_argument("-p", "--parts", type=int, default=1, help="How many parts do you split")

    return parser.parse_args()


def main():
    args = parse_args()

    assert args.output.endswith('.txt'), 'The extension format of output path should be .txt'

    yt_ids = pd.read_csv(args.input)["video_id"].values.tolist()

    part_len = len(yt_ids) // args.parts

    for i in range(args.parts):
        yt_ids_part = yt_ids[i * part_len:(i+1) * part_len]

        yt_urls_part = [f'https://www.youtube.com/watch?v={x}' for x in yt_ids_part]
        if args.parts > 1:
            # build video2dataset csv
            with open(args.output.replace('.txt', f'_{i}.txt'), "w") as fp:
                [fp.write(url + "\n") for url in tqdm(yt_urls_part)]
        else:
            # build video2dataset csv
            with open(args.output, "w") as fp:
                [fp.write(url + "\n") for url in tqdm(yt_urls_part)]


if __name__ == "__main__":
    main()
