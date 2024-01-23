import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Function to write a single JSON object to a file
def write_json_object(json_object, target_directory, key):
    # Use the specified key to name the file
    file_name = f"{json_object.get(key, 'unknown')}.json"

    # Construct the path for the new JSON file
    json_file_path = os.path.join(target_directory, file_name)
    
    # Write the JSON object to the new file
    with open(json_file_path, 'w') as json_file:
        json.dump(json_object, json_file)
    
    return json_file_path

# Main function to split the JSONL file
def split_jsonl(jsonl_file_path, target_directory, key, max_workers=4):
    # Ensure the target directory exists
    os.makedirs(target_directory, exist_ok=True)
    
    # Open the JSONL file and read lines
    with open(jsonl_file_path, 'r') as jsonl_file:
        lines = jsonl_file.readlines()

    # Initialize the progress bar
    pbar = tqdm(total=len(lines), unit="file", desc="Processing")

    # Create a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the executor for each line in the file
        futures = {executor.submit(write_json_object, json.loads(line), target_directory, key): line for line in lines}
        
        # Process as tasks complete
        for future in as_completed(futures):
            pbar.update(1)  # Update progress bar

    # Close the progress bar
    pbar.close()

# Entry point of the script
if __name__ == "__main__":
    jsonl_file_path = 'dataset/yt-1b/labels/yttemporal1b_val_0000of0001.jsonl'  # Path to your JSONL file
    target_directory = 'dataset/yt-1b/label_jsons'  # Directory where the JSON files will be saved
    split_key = 'id'  # The key used to name the JSON files
    max_workers = 1024  # Adjust the number of threads as needed

    split_jsonl(jsonl_file_path, target_directory, split_key, max_workers)
