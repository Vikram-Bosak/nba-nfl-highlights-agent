import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

def generate_ui_frame(output_path: str, source_name: str, headline: str, story: str, width=1080, height=1440):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    fb_blue = (59, 89, 152, 255)
    white = (255, 255, 255, 255)
    yellow = (255, 215, 0, 255)
    line_color = (255, 255, 255, 60)
    
    # 1. Outer yellow border (5px)
    draw.rectangle([0, 0, width, height], outline=yellow, width=5)
    
    # 2. Draw Top Banner (Using extracted exact asset)
    top_banner_path = os.path.join(os.path.dirname(__file__), "../../assets/top_banner_extracted.png")
    top_bar_height = 90
    if os.path.exists(top_banner_path):
        top_banner_img = Image.open(top_banner_path).convert("RGBA")
        top_banner_resized = top_banner_img.resize((width - 10, top_bar_height), Image.LANCZOS)
        img.paste(top_banner_resized, (5, 5), top_banner_resized)
    else:
        draw.rectangle([5, 5, width-5, top_bar_height+5], fill=fb_blue)
        
    # 3. Draw Bottom Banner
    bottom_bar_height = 340
    draw.rectangle([5, height - bottom_bar_height - 5, width - 5, height - 5], fill=fb_blue)
    
    # Fonts
    font_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font_reg = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    
    try:
        f_head = ImageFont.truetype(font_bold, 40)
        f_story = ImageFont.truetype(font_reg, 32)
        f_stats = ImageFont.truetype(font_bold, 35)
    except IOError:
        f_head = f_story = f_stats = ImageFont.load_default()
        
    with Pilmoji(img) as pilmoji:
        start_y = height - bottom_bar_height + 25
        
        # --- Main Headline ---
        try:
            f_sub = ImageFont.truetype(font_bold, 38)
        except IOError:
            f_sub = ImageFont.load_default()
            
        headline_text = headline.strip() if headline else ""
        pilmoji.text((30, start_y), headline_text, fill=white, font=f_sub)
        
        start_y += 60
        
        # --- Description and Hashtags ---
        story_text = story if story else "The team arrives to a massive crowd ahead of their crucial game! Can they go all the way?"
        
        # Extract hashtags and clean story text
        words = story_text.split()
        hashtags = [w for w in words if w.startswith('#')]
        clean_story = " ".join([w for w in words if not w.startswith('#')])
        
        story_lines = textwrap.wrap(clean_story, width=72)
        
        try:
            f_story = ImageFont.truetype(font_reg, 30)
            f_story_bold = ImageFont.truetype(font_bold, 30)
        except IOError:
            f_story = ImageFont.load_default()
            f_story_bold = ImageFont.load_default()
            
        for line in story_lines[:3]:  # Max 3 lines for description
            pilmoji.text((30, start_y), line, fill=white, font=f_story)
            start_y += 42
            
        # Draw hashtags on a new line with lighter color
        if hashtags:
            hashtag_text = " ".join(hashtags)
            pilmoji.text((30, start_y), hashtag_text, fill=(160, 176, 192, 255), font=f_story)
            start_y += 45
            
        # --- Separator Line ---
        sep_y = height - 100
        draw.line([(25, sep_y), (width - 25, sep_y)], fill=line_color, width=2)
        
        # --- 'Tap or hold...' Hint Text ---
        try:
            f_hint = ImageFont.truetype(font_reg, 22)
        except IOError:
            f_hint = ImageFont.load_default()
            
        hint_text = "Tap or hold to like and react with Love, Haha, Wow, or Sad!"
        hint_w = pilmoji.getsize(hint_text, font=f_hint)[0]
        # Align to the right side, just above the separator line
        pilmoji.text((width - hint_w - 30, sep_y - 35), hint_text, fill=(200, 200, 200, 255), font=f_hint)
        
        # --- ENGAGEMENT BAR ---
        engage_y = height - 80
        
        # Overlapping emojis
        draw.ellipse([30, engage_y, 30+40, engage_y+40], fill=(24,119,242,255))
        draw.ellipse([55, engage_y, 55+40, engage_y+40], fill=(240,40,73,255))
        draw.ellipse([80, engage_y, 80+40, engage_y+40], fill=(247,177,37,255))
        draw.ellipse([105, engage_y, 105+40, engage_y+40], fill=(247,177,37,255))
        
        pilmoji.text((35, engage_y+2), "👍", fill=white, font=f_stats)
        pilmoji.text((60, engage_y+2), "❤️", fill=white, font=f_stats)
        pilmoji.text((85, engage_y+2), "😂", fill=white, font=f_stats)
        pilmoji.text((110, engage_y+2), "😲", fill=white, font=f_stats)
        
        likes_num = random.randint(10000, 99999)
        formatted_likes = f"{likes_num:,} Likes"
        pilmoji.text((160, engage_y+2), formatted_likes, fill=white, font=f_stats)
        
        pilmoji.text((550, engage_y+2), "💬 Comment", fill=white, font=f_stats)
        pilmoji.text((820, engage_y+2), "↗️ Share", fill=white, font=f_stats)
        
        # --- VIDEO CREDIT OVERLAY ---
        # Draw on the transparent area so it overlays on the video
        credit_text = "Video Credit: NBA/NFL Highlights"
        try:
            f_credit = ImageFont.truetype(font_bold, 35)
        except IOError:
            f_credit = ImageFont.load_default()
            
        credit_w = pilmoji.getsize(credit_text, font=f_credit)[0]
        # Position at bottom right of the video area
        credit_x = width - credit_w - 30
        credit_y = height - bottom_bar_height - 50
        
        # Draw stroke/shadow for visibility
        shadow_color = (0, 0, 0, 200)
        for offset in [(2,2), (-2,-2), (2,-2), (-2,2), (0,2), (2,0), (-2,0), (0,-2)]:
            pilmoji.text((credit_x + offset[0], credit_y + offset[1]), credit_text, fill=shadow_color, font=f_credit)
        pilmoji.text((credit_x, credit_y), credit_text, fill=(230, 230, 230, 255), font=f_credit)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    generate_ui_frame(
        "temp/test_ui_frame.png", 
        "NBA/NFL HIGHLIGHTS", 
        "INCREDIBLE NBA PLAY! 🏀", 
        "The team arrives to a massive crowd ahead of their crucial game! Can they go all the way? #NBA #NFL #Highlights #SportsNews"
    )
