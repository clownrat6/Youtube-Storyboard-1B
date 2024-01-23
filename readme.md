# Easy Downloading of Youtube-StoryBoard-1B

## Installation

```bash
bash scripts/install.sh
```

## Preparing [Youtube-Temporal-1B](https://rowanzellers.com/merlotreserve) dataset

1. Download Youtube ids CSV of Youtube-Temporal-1B:
```bash
wget https://storage.googleapis.com/merlot/yttemporal1b/yttemporal1b_ids_train.csv
wget https://storage.googleapis.com/merlot/yttemporal1b/yttemporal1b_ids_val.csv
```

2. Download

Google Drive Bucket usage reference:
* [convert bucket to direct link](https://cloud.google.com/storage/docs/discover-object-storage-console?hl=zh-cn)
* [download bucket via gsutil](https://cloud.google.com/storage/docs/downloading-objects?hl=zh-cn#cli-download-object)
* [download bucket via google cloud api](https://cloud.google.com/storage/docs/samples/storage-download-file?hl=zh-cn#storage_download_file-python)

3. Convert to url list:
```bash
# split train urls into 10 parts and the url lists are storaged as: "yt1b_urls_train_0.txt", "yt1b_urls_train_1.txt", ...
python url_extraction.py -i dataset/yt-1b/yttemporal1b_ids_train.csv -o dataset/yt-1b/yt1b_urls_train.txt -p 10

# acquire val urls and the url lists are storaged as: "yt1b_url_val.txt"
python url_extraction.py -i dataset/yt-1b/yttemporal1b_ids_val.csv -o dataset/yt-1b/yt1b_urls_val.txt
```

4. Download video (.webp format) from urls:
```bash
bash scripts/download.sh dataset/yt-1b/yt1b_urls_train_{i}.txt # i from 0 to 9 according to your part number

bash scripts/download.sh dataset/yt-1b/yt1b_urls_val.txt
```

## Prepareing subtitles files

1. Conduct script commands below:
```bash
# It is not recommended to open too many workers. Because the restriction of Youtube.
python get_transcript.py -i dataset/yt-1b/yt1b_urls_train_{i}.txt -o dataset/yt-1b/subtitles/train_{i} -w 8 # i from 0 to 9 according to your part number

python get_transcript.py -i dataset/yt-1b/yt1b_urls_val.txt -o dataset/yt-1b/subtitles/val -w 8
```

2. Generating subtitle file list

## Processing data to video-text interleaved samples

1. Downloading Yoube-Temporal-1B label files:
```bash
# for folds i between 0 and 1023.
wget f'gs://merlot/yttemporal1b/train_annotations/yttemporal1b_train_{i:04d}of1024.jsonl.gz'
wget https://storage.googleapis.com/merlot/yttemporal1b/yttemporal1b_val_0000of0001.jsonl.gz
```
