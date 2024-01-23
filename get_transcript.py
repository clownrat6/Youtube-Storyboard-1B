import os
import argparse

from tqdm import tqdm
from multiprocessing import Process

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter


def save_subtitle(video_id, save_folder):
    save_path = f'{save_folder}/{video_id}.json'
    if os.path.exists(save_path):
        return
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
    formatter = JSONFormatter()

    json_formatted = formatter.format_transcript(transcript)

    with open(f'{save_folder}/{video_id}.json', 'w', encoding='utf-8') as json_file:
        json_file.write(json_formatted)


def download(video_ids, i, save_folder):
    for v in tqdm(video_ids):
        try:
            save_subtitle(v, save_folder)
        except:
            print("error:", v)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, default="dataset/yt-1b/yt1b_urls_train_0.txt", help="youtube id input path")
    parser.add_argument("-o", "--output", type=str, default="dataset/yt-1b/subtitles/train_0", help="youtube subtitle output path")
    parser.add_argument("-w", "--workers", type=int, default=8, help="number of workers")

    return parser.parse_args()


# save_subtitle("Lj4jS6qFVPo")


if __name__ == '__main__':
    args = parse_args()

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    num_workers = args.workers
    video_ids = []

    # yt urls
    with open(args.input, 'r') as f:
        urls = f.readlines()
        video_ids = [u.replace("https://www.youtube.com/watch?v=", "").strip() for u in urls]

    print("video_ids", len(video_ids), video_ids[-1], video_ids[-2])
    
    video_ids = video_ids

    processes = [Process(target=download, args=(video_ids[i::num_workers], i, args.output)) for i in range(num_workers)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()
