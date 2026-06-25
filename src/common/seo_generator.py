import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

# Try to import Google GenAI
try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

load_dotenv()

def _get_client():
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        return None
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )

def _extract_gemini_video_context(video_path: str) -> str:
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not HAS_GEMINI or not gemini_key or not video_path or not os.path.exists(video_path):
        return ""
        
    print(f"Deep Video Analysis: Uploading {video_path} to Gemini 1.5 Flash...")
    try:
        client = genai.Client(api_key=gemini_key)
        video_file = client.files.upload(file=video_path)
        
        # Wait for video processing
        while video_file.state.name == "PROCESSING":
            print("Waiting for video processing...")
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
            
        if video_file.state.name == "FAILED":
            print("Gemini Video processing failed.")
            return ""
            
        prompt = "Analyze this video completely. 1) Describe exactly what is happening visually. 2) If it is a meme, edit, or specific historical event, explicitly state what the true hidden subject is. 3) Read any on-screen text (OCR). 4) Transcribe any spoken words. Be extremely accurate."
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[video_file, prompt]
        )
        
        # Cleanup file from Gemini servers
        client.files.delete(name=video_file.name)
        
        print("Gemini Context Extraction Successful.")
        return response.text
    except Exception as e:
        print(f"Error extracting deep video context: {e}")
        return ""

def analyze_video_for_editing(context: dict) -> dict:
    """
    Stage 1: Analyzes video context and generates Hook Line, Short Headline, Overlay Text, and Category.
    """
    client = _get_client()
    
    original_title = context.get('title', '')
    fallback = {
        "category": "Highlight",
        "short_headline": original_title[:35] + "..." if len(original_title) > 35 else (original_title if original_title else "MUST WATCH"),
        "story": original_title if original_title else "Did you catch this incredible play?",
        "overlay_text": "EPIC NBA/NFL HIGHLIGHTS"
    }
    
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback analysis.")
        return fallback
        
    # Check if we should extract deep context via Gemini
    deep_context = ""
    local_path = context.get('local_path')
    if local_path and os.getenv("GEMINI_API_KEY"):
        deep_context = _extract_gemini_video_context(local_path)
        if deep_context:
            context['deep_context'] = deep_context  # Save for stage 2
            
    prompt = f"""
    You are an expert NBA and NFL social media manager. Your ONLY source of truth is the following original text from the downloaded video:
    Original Title/Text: {context.get('title', 'Unknown')}
    Source Profile: {context.get('source', 'Unknown')}
    
    INSTRUCTIONS:
    1. First, deeply analyze the "Original Title/Text". Understand the actual context, NBA/NFL players, teams, or game events mentioned.
    2. Generate a "short_headline". This must be very short, impactful, and written strictly in ENGLISH. (e.g., "UNBELIEVABLE DUNK! 🏀"). Include 1 emoji.
    3. Generate a "story". This is a short, 2-3 sentence paragraph explaining the context or building suspense, designed to make them watch the video. Include emojis. (e.g., "Nobody expected this to happen! Do you think it was a foul? 👇").
    4. Keep it highly clickable. Ban generic, boring phrases.
    5. Generate a "category" based on the real context (e.g., Highlight, Dunk, Touchdown, Skill, News).
    
    Return strictly ONLY a valid JSON object:
    - "category": The accurate video category.
    - "short_headline": The short, impactful headline.
    - "story": The contextual 2-3 sentence paragraph.
    """
    
    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
            timeout=45,
        )
        content = completion.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        data = json.loads(content.strip())
        
        for key in fallback.keys():
            if key not in data:
                data[key] = fallback[key]
                
        return data
    except Exception as e:
        print(f"Error calling NVIDIA LLM API for editing analysis: {e}")
        return fallback

def generate_upload_metadata(context: dict) -> dict:
    """
    Stage 2: Generates SEO metadata based on the full editing context.
    """
    client = _get_client()
    if not client:
        print("Warning: NVIDIA_API_KEY not found. Using fallback SEO data.")
        return _get_fallback_metadata(context)
        
    prompt = f"""
    You are an expert NBA and NFL social media manager. Your task is to generate SEO metadata based STRICTLY on the original text context of the video.
    
    ORIGINAL CONTEXT:
    Original Title/Text: {context.get('title', 'Unknown')}
    Source Profile: {context.get('source', 'Unknown')}
    Determined Category: {context.get('category', 'Highlight')}
    Headline Used in Video: {context.get('short_headline', '')}
    Story Used in Video: {context.get('story', '')}
    
    CRITICAL INSTRUCTION: Analyze the Original Title/Text. What is it really about? Generate the SEO Title, Description, and Hashtags to reflect this REAL context perfectly. Ensure hashtags are related to NBA, NFL, basketball, football, the teams, and the players mentioned. Do NOT use Hollywood or entertainment hashtags.
    
    Generate the following details and return ONLY a valid JSON object:
    - "title": A catchy, viral SEO title (under 60 characters) accurately reflecting the REAL original text context.
    - "description": An engaging YouTube Shorts description targeting NBA/NFL fans, summarizing the actual subject matter derived from the original text.
    - "facebook_caption": A short, punchy caption for Facebook Reels with a call to action based on the true context. Do NOT include hashtags in this field.
    - "hashtags": A string of 5-7 highly relevant viral NBA/NFL hashtags based on the true context (e.g., "#NBAHighlights #NFLHighlights #NBA #NFL").
    - "tags": A list of 5-8 SEO tags (strings) for YouTube based on the real content.
    """
    
    try:
        completion = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.95,
            max_tokens=1024,
        )
        
        content = completion.choices[0].message.content
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
            
        data = json.loads(content.strip())
        
        required_keys = ["title", "description", "facebook_caption", "hashtags", "tags"]
        for key in required_keys:
            if key not in data:
                data[key] = _get_fallback_metadata(context)[key]
                
        return data

    except Exception as e:
        print(f"Error calling NVIDIA LLM API for SEO: {e}")
        return _get_fallback_metadata(context)

def _get_fallback_metadata(context=None):
    if not context:
        context = {}
    original_title = context.get('title', 'Unbelievable NBA/NFL Play! 🏈🏀')
    
    return {
        "title": original_title[:60],
        "description": f"{original_title}\n\nWitness this incredible highlight from the world of basketball/football! If you love sports, you have to see this. Don't forget to like and subscribe for daily NBA/NFL updates! 🏈🏀",
        "facebook_caption": f"{original_title}\n\nWait for the end... Comment your thoughts below! 👇",
        "hashtags": "#NBAHighlights #NFLHighlights #NBA #NFL #Sports #Viral",
        "tags": ["NBA", "NFL", "Basketball", "Football", "Highlights", "Sports"]
    }

if __name__ == "__main__":
    dummy_context = {
        "title": "LeBron James Incredible Fadeaway Dunk",
        "source": "NBA",
        "source_url": "https://x.com/NBA/status/1234567890"
    }
    analysis = analyze_video_for_editing(dummy_context)
    print("Editing Analysis:")
    print(json.dumps(analysis, indent=4))
    
    # Merge for Stage 2
    dummy_context.update(analysis)
    
    print("\nGenerated Metadata:")
    print(json.dumps(generate_upload_metadata(dummy_context), indent=4))
