import os
import requests
import random
import time
from dotenv import load_dotenv

# Ensure we can import existing modules
try:
    from src.facebook_uploader import upload_reel
    from src.youtube_uploader import upload_to_youtube
except ImportError:
    from facebook_uploader import upload_reel
    from youtube_uploader import upload_to_youtube

load_dotenv()

def run_upload(video_data):
    print("Starting Agent 3: Facebook & YouTube Uploader")
    
    edited_video_path = video_data.get('edited_path')
    title = video_data.get('title', 'Unknown Video')
    headline = video_data.get('seo_title', '')
    source_url = video_data.get('source_url', '')
    
    if not edited_video_path or not os.path.exists(edited_video_path):
        print("No edited video found to upload.")
        return video_data
        
    if video_data.get("editing_status") != "Success":
        print(f"Editing did not succeed (Status: {video_data.get('editing_status')}). Skipping upload.")
        if os.path.exists(edited_video_path):
            os.remove(edited_video_path)
        return video_data
        
    # Construct Facebook Caption dynamically
    try:
        from src.common.seo_generator import generate_upload_metadata
        task_id = video_data.get("id", "default")
        state_file = f"temp/state_upload_{task_id}.json"
        
        if os.path.exists(state_file):
            import json
            with open(state_file, "r") as f:
                context = json.load(f)
        else:
            context = video_data
            
        metadata = generate_upload_metadata(context)
        fb_caption = f"{metadata.get('facebook_caption', headline)}\n\n{metadata.get('hashtags', '#NBAHighlights #NFLHighlights')}\n\nSource: {source_url}"
    except Exception as e:
        print(f"Error generating dynamic SEO metadata: {e}")
        fb_caption = f"{headline}\n\n#NBAHighlights #NFLHighlights #Sports\n\nSource: {source_url}"
        
    video_data["description"] = fb_caption

    # Random delay to appear human (0-15 minutes)
    delay_seconds = random.randint(0, 900)
    delay_minutes = delay_seconds / 60
    print(f"Waiting for {delay_seconds} seconds ({delay_minutes:.1f} minutes) before uploading to appear human...")
    
    try:
        from src.common.telegram import report_upload_delay
        report_upload_delay(delay_minutes)
    except Exception as e:
        print(f"Failed to send delay report: {e}")
        
    time.sleep(delay_seconds)

    # Facebook Upload (skip gracefully if no API keys)
    try:
        print(f"Uploading to Facebook with caption: {fb_caption}")
        fb_url = upload_reel(edited_video_path, fb_caption)
        print(f"Successfully uploaded to Facebook: {fb_url}")
        video_data["fb_url"] = fb_url
    except Exception as e:
        print(f"Failed to upload to Facebook (API keys may not be configured): {e}")
        video_data["fb_err"] = str(e)
        
    # YouTube Upload (runs independently of Facebook, skip gracefully if no API keys)
    try:
        print("Waiting 2 seconds before uploading to YouTube Shorts...")
        time.sleep(2)
        
        yt_title = title[:100]  # YouTube title limit is 100 chars
        yt_desc = f"{fb_caption}\n#shorts"
        
        yt_url = upload_to_youtube(edited_video_path, yt_title, yt_desc)
        video_data["yt_url"] = yt_url
    except Exception as e:
        print(f"Failed to upload to YouTube (API keys may not be configured): {e}")
        video_data["yt_err"] = str(e)
        
    # Set overall status based on whether at least one upload succeeded
    if video_data.get("fb_url") or video_data.get("yt_url"):
        video_data["upload_status"] = "Success"
    else:
        # If both uploads failed but we have the video, mark as partial success
        # (the edit was successful, just no platform keys configured)
        if not video_data.get("fb_url") and not video_data.get("yt_url"):
            video_data["upload_status"] = "Skipped (No API Keys)"
        else:
            video_data["upload_status"] = "Failed"
        
    # Cleanup
    if os.path.exists(edited_video_path):
        os.remove(edited_video_path)
        
    return video_data

if __name__ == "__main__":
    pass
