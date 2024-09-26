import os
import subprocess

def convert_zh_tw_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith("_zh-tw.md"):
            file_path = os.path.join(folder_path, filename)
            
            # Read the content of the file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Convert Simplified Chinese to Traditional Chinese using opencc
            process = subprocess.Popen(['opencc', '-c', 's2t.json'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            traditional_content, error = process.communicate(input=content.encode('utf-8'))
            
            if process.returncode != 0:
                print(f"Error converting file {filename}: {error.decode('utf-8')}")
                continue
            
            # Save the converted content back to the same file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(traditional_content.decode('utf-8'))
            print(f"Converted {filename} to Traditional Chinese")

# Define the folder path
posts_folder = "_posts"
convert_zh_tw_files(posts_folder)
