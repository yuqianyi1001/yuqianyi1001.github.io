import os
import subprocess

def convert_zh_tw_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith("_zh-tw.md"):
            file_path = os.path.join(folder_path, filename)

            # Convert Traditional Chinese to Simplified Chinese using opencc with -i and -o
            process = subprocess.Popen(['opencc', '-i', file_path, '-o', file_path, '-c', 'tw2s.json'], stderr=subprocess.PIPE)
            _, error = process.communicate()
            
            if process.returncode != 0:
                print(f"Error converting file {filename}: {error.decode('utf-8')}")
                continue
            
            # Convert Simplified Chinese to Traditional Chinese using opencc with -i and -o
            process = subprocess.Popen(['opencc', '-i', file_path, '-o', file_path, '-c', 's2tw.json'], stderr=subprocess.PIPE)
            _, error = process.communicate()
            
            if process.returncode != 0:
                print(f"Error converting file {filename} to Traditional Chinese: {error.decode('utf-8')}")
                continue
            
            print(f"Converted {filename} to Traditional Chinese")
# Define the folder path
posts_folder = "_posts"
convert_zh_tw_files(posts_folder)
