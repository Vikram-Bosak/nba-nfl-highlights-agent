import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agent_1_downloader import run_downloader, save_to_history
from src.agent_2_editor import process_video
from src.agent_3_uploader import run_upload
from src.common.limits import can_download, can_upload, increment_download, increment_edit, increment_upload
from src.common.telegram import (
    report_final_summary, 
    report_download_start, 
    report_download_complete, 
    report_edit_start, 
    report_edit_complete, 
    send_message
)

def run_single_sequence():
    print("\n--- STARTING SEQUENTIAL PIPELINE (SINGLE RUN) ---")
    
    if not can_download() or not can_upload():
        print("Daily upload limit reached. Exiting.")
        return False

    # 1. Download
    report_download_start()
    video_data, stats = run_downloader()
    if not video_data:
        print("No video found.")
        report_final_summary({}, stats)
        return False
        
    task_id = video_data['id']
    print(f"Downloaded Video: {task_id}")
    report_download_complete(video_data['source_url'])
    send_message(f"🆔 <b>Unique ID generated:</b> {task_id}")
    increment_download()
    
    # Save to history immediately to prevent infinite retry loops if edit/upload fails
    save_to_history(task_id)
    
    # IMMEDIATELY push to GitHub so if the user triggers another run during the 15-minute sleep, it won't duplicate!
    print("Pushing history to GitHub immediately to prevent race conditions...")
    try:
        import subprocess
        subprocess.run("git config --global user.name 'github-actions[bot]'", shell=True)
        subprocess.run("git config --global user.email 'github-actions[bot]@users.noreply.github.com'", shell=True)
        subprocess.run("git add downloaded_history.txt", shell=True)
        subprocess.run("git add temp/daily_limits.json", shell=True)
        subprocess.run("git commit -m 'Update history (mid-run)'", shell=True)
        subprocess.run("git pull origin main --rebase --strategy-option=ours", shell=True)
        subprocess.run("git push origin HEAD:main", shell=True)
        print("History pushed successfully.")
    except Exception as e:
        print(f"Warning: Mid-run history push failed: {e}")
    
    # 2. Edit
    report_edit_start()
    try:
        print(f"Editing Video {task_id}...")
        video_data = process_video(video_data)
        if video_data.get('editing_status') == 'Success':
            report_edit_complete()
            increment_edit()
            stats["videos_edited"] = 1
        else:
            send_message(f"❌ <b>Editing Failed for {task_id}</b>")
            stats["errors"].append(f"Editing Failed for {task_id}")
            report_final_summary(video_data, stats)
            return False
    except Exception as e:
        print(f"Editing failed: {e}")
        send_message(f"❌ <b>Editing Failed for {task_id}:</b>\n{e}")
        stats["errors"].append(f"Editing Exception: {str(e)}")
        report_final_summary(video_data, stats)
        return False
        
    # 3. Upload
    print(f"Uploading Video {task_id}...")
    video_data = run_upload(video_data)
    
    if video_data.get('upload_status') == 'Success':
        increment_upload()
        stats["videos_uploaded"] = 1
    
    # Final Report
    report_final_summary(video_data, stats)
    
    print("Pipeline run completed.")
    return True

if __name__ == "__main__":
    run_single_sequence()
