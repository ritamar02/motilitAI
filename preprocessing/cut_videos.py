#!/usr/bin/env python
import os
import csv
import subprocess
import shutil

# Paths to directories
input_videos_dir = "./data/raw/videos"
output_videos_dir = "./data/processed/cut-videos"
csv_file_path = "./data/video-cuts.csv"

# Ensure the output directories exist
os.makedirs(output_videos_dir, exist_ok=True)

# Paths for fold folders
fold_folders = {
    "fold_1": os.path.join(output_videos_dir, "fold_1"),
    "fold_2": os.path.join(output_videos_dir, "fold_2"),
    "fold_3": os.path.join(output_videos_dir, "fold_3"),
}

# Create fold folders if they don't exist
for fold in fold_folders.values():
    os.makedirs(fold, exist_ok=True)

# Function to get the duration of a video
def get_video_duration(video_path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Error getting duration of video: {video_path}, {e}")
        return 0

# Read the CSV file
with open(csv_file_path, mode='r') as csv_file:
    reader = csv.DictReader(csv_file)

    current_video_id = None
    cumulative_start_time = 0
    video_duration = 0

    for row in reader:
        index = int(row[''])  # First column
        video_id = row['video_id']
        scene_id = int(row['scene_id'])
        duration = float(row['duration'])

        # Determine the fold based on the index
        if index <= 240:
            fold = "fold_1"
        elif 241 <= index <= 480:
            fold = "fold_2"
        else:
            fold = "fold_3"

        # Extract video ID as the part before the first underscore
        video_id = video_id.split('_')[0]
        video_id = str(int(video_id))  # Remove leading zeros

        # If the video ID changes, reset cumulative time
        if video_id != current_video_id:
            current_video_id = video_id

            # Find the video file
            matching_videos = [
                file for file in os.listdir(input_videos_dir)
                if file.startswith(video_id) and file.endswith(".avi")
            ]

            if not matching_videos:
                print(f"No video found for video_id {video_id}")
                current_video_id = None
                continue

            input_video_path = os.path.join(input_videos_dir, matching_videos[0])
            video_duration = get_video_duration(input_video_path)
            cumulative_start_time = 0

        # Skip if not enough time left
        if cumulative_start_time + duration > video_duration:
            print(f"Not enough time left in video {current_video_id} for scene {scene_id}. Skipping.")
            continue

        # Define output video filename and path
        output_filename = f"{video_id}_scene{scene_id}_{duration:.2f}.avi"
        output_video_path = os.path.join(output_videos_dir, output_filename)

        # Run FFMPEG command to cut the video
        command = [
            "ffmpeg",
            "-i", input_video_path,
            "-ss", str(cumulative_start_time),
            "-t", str(duration),
            "-c:v", "copy",
            "-c:a", "copy",
            output_video_path
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Created: {output_video_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error processing video_id {video_id}, scene_id {scene_id}: {e}")
            continue

        # Move the processed video to the corresponding fold folder
        fold_folder_path = fold_folders[fold]
        shutil.move(output_video_path, os.path.join(fold_folder_path, output_filename))

        # Update cumulative start time
        cumulative_start_time += duration

print("Processing and grouping complete.")
