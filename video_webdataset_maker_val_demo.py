import json
import os
import sys
import shutil
import numpy as np
import datetime
import webdataset as wds
from multiprocessing import Process
from PIL import Image
import time
from tqdm import tqdm
from video2numpy.frame_reader import FrameReader
import argparse
import csv

# python video_webdataset_maker_YT1b_sb.py --input /share/project/cyf/webvid/YT-1B-sb/YT-1B-sb_1 --output /share/project/cyf/data/YT-1b-sb-wd --workers 1 2>&1 | tee log_1.txt
# python video_webdataset_maker_YT1b_sb.py  --output /share/project/datasets/video/storyboard/YT-1b-sb-wd --workers 24 2>&1 | tee log_1.txt


# f"{output_path}/%07d.tar"
# 
#
# file_paths
# map_func=sampler
def make_wds_shards(pattern, num_shards, num_workers, samples, map_func, **kwargs):
    """
    Args:
        num_shards [int]: Decide how many pieces the sample should be cut into.
        num_workes [int]

    """
    
    samples_per_shards = [samples[i::num_shards] for i in range(num_shards)]
    shard_ids = list(range(num_shards))

    processes = [
        Process(
            target=write_partial_samples,
            args=(
                i,
                pattern,
                shard_ids[i::num_workers],
                samples_per_shards[i::num_workers],
                map_func,
                kwargs
            )
        )
        for i in range(num_workers)]
    for p in processes:
        p.start()
    for p in processes:
        p.join()


def write_partial_samples(id, pattern, shard_ids, samples, map_func, kwargs):
    for shard_id, samples in tqdm(zip(shard_ids, samples)):
        print(shard_id, samples)
        write_samples_into_single_shard(pattern, shard_id, samples, map_func, kwargs)

def write_samples_into_single_shard(pattern, shard_id, samples, map_func, kwargs):
    fname = pattern % shard_id
    url = '/'.join(fname.split('/')[-2:])

    sink = wds.TarWriter(fname, **kwargs)
    for item in samples:
        for content in map_func(item, url):
            sink.write(content)

    sink.close()


def subtitle_filelist_writer(subtitles_dir, path):
    if os.path.exists(path):
        return
    subtitles = os.listdir(subtitles_dir)
    with open(path, 'w') as f:
        for subtitle in tqdm(subtitles):
            f.write(subtitle + "\n")
    # subtitles = os.listdir(subtitles_dir)
    # print(len(subtitles))
    # with open(f"./subtitle_filelist/{i}.txt", 'w') as f:
    #     for subtitle in tqdm(subtitles):
    #         f.write(subtitle+"\n")


if __name__ == "__main__":

    # argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default='dataset/yt-1b/vids/val', type=str, help='input files')
    parser.add_argument("--output", default='dataset/output', type=str, help='output files')
    parser.add_argument("--workers", default=24, type=int, help='workers')
    opt = parser.parse_args()

    print(opt, flush=True)
    
    root = opt.input
    output_path = opt.output
    num_workers = opt.workers

    roots = [root]

    print(roots)
    filelist = []
    for root in roots:
        filelist.extend(os.listdir(root))
    filelist = sorted(filelist)

    # scan directory and push it into `file_paths` list 
    file_paths = []
    for i, fp in enumerate(filelist):
        if os.path.isdir(os.path.join(root, fp)):
            file_paths.append(os.path.join(root, fp))
    file_paths = file_paths
    file_paths = [file_paths[0]]
    num_shards = len(file_paths)
    print(f"There are total {num_shards} shards:\n", file_paths)

    # construct mapping from youtube video id to json path
    subtitle_dict = {}
    subtitles_dir_list = [
        'dataset/yt-1b/subtitles/val'
    ]
    subtitles_txt_list = [
        'dataset/yt-1b/subtitles/val.txt'
    ]
    [subtitle_filelist_writer(x, y) for x, y in zip(subtitles_dir_list, subtitles_txt_list)]
    for i, subtitles_dir in enumerate(subtitles_dir_list):
        with open(subtitles_txt_list[i], 'r') as f:
            subtitles = f.readlines()

        for subtitle in tqdm(subtitles):
            # 0:-6 removes ".json\n"
            subtitle_dict[subtitle[0:-6]] = os.path.join(subtitles_dir, subtitle.strip())

    print(f"The length of subtitle files: {len(subtitle_dict.keys())}")

    def sampler(fp, url):
        videos = []
        files = sorted(os.listdir(fp))
        files_st = set(files)

        for f in files:
            # 1. select single youtube video via json file path.
            if 'json' in f and f[:-5]+"_0.webp" in files_st:
                # [:-5] removes ".json", e.g., 000010000.json -> 000010000
                key = f[:-5]
                imgs = []
                for i in range(100):
                    if f"{key}_{i}.webp" in files_st:
                        imgs.append(os.path.join(fp, f"{key}_{i}.webp"))
                    else:
                        break
            else:
                continue

            # 2. read single json file and extract sb meta file
            final_meta = {}
            with open(os.path.join(fp, f), "r") as fread:
                label_str = fread.read()
                label_dict = json.loads(label_str)
                
                if label_dict["status"] != "success":
                    break

                vid = label_dict["url"].replace("https://www.youtube.com/watch?v=", "")

                final_meta["id"] = vid
                # meta data contains [height, width, num_horizon_grids, num_vertical_grids]
                final_meta["sb"] = label_dict["yt_meta_dict"]["sb"]

            # 3. injecting subtitle label
            if vid in subtitle_dict:
                with open(subtitle_dict[vid], "r") as fread:
                    subtitle_str = fread.read()
                    subtitle_list = json.loads(subtitle_str)
                    final_meta["subtitle"] = subtitle_list
            else:
                print(f"no subtitle in subtitle", vid, f, flush=True)
                continue

            # 4. injecting duration from origin yt-1b label
            if os.path.exists(f"dataset/yt-1b/label_jsons/{vid}.json"):
                with open(f"dataset/yt-1b/label_jsons/{vid}.json", "r") as fread:
                    meta_str = fread.read()
                    meta_dict = json.loads(meta_str)
                    final_meta["duration"] = meta_dict["duration"]
            else:
                print("no meta error:", vid, f, flush=True)
                continue

            # split
            final_meta_str = json.dumps(final_meta)
            sample = {
                "__key__": vid,
                "__url__": url, # path/to/xxx.tar
            }

            # extract frames from video thumbnail
            frame_num = 0
            frames = []
            for i, img in enumerate(imgs):
                # video thumbnail (.webp format)
                img_np = np.array(Image.open(img))
                # [width, height, num_horizon_grids, num_vertical_grids]
                label = final_meta["sb"][str(i)]
                frame_num += label[4]
                h, w, c = img_np.shape
                # [h, w] -> [nhg, hg, nwg, wg, c] -> [nhg, nwg, hg, wg, c] -> [nhg*nwg, hg, wg, c]
                img_np = img_np.reshape(label[3], h//label[3], label[2], w//label[2], c).transpose(0, 2, 1, 3, 4).reshape(-1, h//label[3], w//label[2], c)
                frames.append(img_np)
            frame_interval = round(final_meta["duration"] / frame_num)
            # filter empty frames at the end of video
            frames = np.concatenate(frames, 0)[0:frame_num]

            # intertwine frame and subtitle via timeline order
            frame_time_line = []
            subtitle_time_line = []

            for i, frame in enumerate(frames):
                frame_time_line.append((i*frame_interval, 'i', frame))
            for i, subtitle in enumerate(final_meta["subtitle"]):
                subtitle_time_line.append((subtitle["start"], 't', subtitle["text"]))

            time_line = sorted(frame_time_line + subtitle_time_line, key=lambda x:x[0])

            # the intertwine rule is like:
            # (text1 + " " + text2) + img1 + (text3 + " " + text4 + " " + text5) + img2 + ...
            index = 0
            stack_text = ""
            for i, tl in enumerate(time_line):
                if tl[1] == 'i': 
                    sample[f"{index}.txt"] = stack_text
                    sample[f"{index}.png"] = tl[2]
                    stack_text = ""
                    index += 1
                else:
                    if len(stack_text) == 0:
                        stack_text = tl[2]
                    else:
                        stack_text = stack_text + " " + tl[2]
            # process left text at the end of the video 
            if len(stack_text) > 0:
                sample[f"{index}.txt"] = stack_text

            final_meta["frame_num"] = frame_num
            final_meta_str = json.dumps(final_meta)
            sample["final_meta.json"] = final_meta_str
            yield sample

    make_wds_shards(
        pattern=f"{output_path}/%07d.tar",
        num_shards=num_shards, # 设置分片数量
        num_workers=num_workers, # 设置创建wds数据集的进程数
        samples=file_paths,
        map_func=sampler,
    )
