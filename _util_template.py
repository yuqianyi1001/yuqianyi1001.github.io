import datetime
import shutil

# Get the current date
current_date = datetime.datetime.now().strftime("%Y-%m-%d")

# Define the source and destination paths
source_path = "_unfinished_posts/_2024-08-21-TBD-template.md"
destination_path = f"_posts/{current_date}-TBD.md"

# Copy the file to the destination
shutil.copyfile(source_path, destination_path)
