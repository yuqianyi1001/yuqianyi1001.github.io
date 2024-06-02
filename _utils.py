import re
import sys
import os
import shutil

def replace_image_paths(file_path):
    # Read the input file
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Define the regex pattern to match image paths
    pattern = r'!\[([^\]]+)\]\(([^)]+)\)'

    # Define the replacement function
    def replacement(match):
        alt_text = match.group(1)
        image_name = match.group(2).split('/')[-1]  # Get the image name from the path
        new_path = f'../images/{image_name}'
        return f'![{alt_text}]({new_path})'

    # Replace all image paths in the content
    updated_content = re.sub(pattern, replacement, content)

    # Write the updated content to the same file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)

def move_images(source_dir, destination_dir):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)
    for filename in os.listdir(source_dir):
        if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            source_path = os.path.join(source_dir, filename)
            destination_path = os.path.join(destination_dir, filename)
            shutil.move(source_path, destination_path)
            print(f"Moved {source_path} to {destination_path}")

# Main function to handle command line argument
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py <file_path>")
    else:
        file_path = sys.argv[1]
        replace_image_paths(file_path)
        print(f"Updated image paths in {file_path}")

        source_dir = "_post"
        destination_dir = "images"
        move_images(source_dir, destination_dir)
        print(f"Moved images from {source_dir} to {destination_dir}")

