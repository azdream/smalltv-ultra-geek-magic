import os
import math
import random
import datetime
from PIL import Image, ImageDraw, ImageFont

def create_animated_dashboard(output_path="test_dashboard_live.gif", pomo_completed=5, pomo_target=12, agent_running=None):
    width, height = 240, 240
    fonts_dir = "fonts"
    
    font_clock = ImageFont.truetype(os.path.join(fonts_dir, "PressStart2P.ttf"), 14)
    font_title = ImageFont.truetype(os.path.join(fonts_dir, "PressStart2P.ttf"), 7)
    font_sm = ImageFont.truetype(os.path.join(fonts_dir, "Silkscreen.ttf"), 7)
    font_kr = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 9)
    font_kr_sm = ImageFont.truetype("/System/Library/Fonts/Supplemental/AppleGothic.ttf", 8)
    
    # Load chunky avatars
    avatar_open = Image.open('scale_52x96.jpg').convert("RGBA")
    avatar_blink = Image.open('test_blink_cute.jpg').convert("RGBA")
    
    # Twinkling night stars coordinates (relative to full 240x240, on the avatar side)
    stars = [
        (130, 20), (160, 12), (185, 25), (220, 18),
        (140, 60), (225, 55), (135, 140), (228, 120),
        (125, 90), (218, 95), (145, 170), (222, 175)
    ]
    
    frames = []
    num_frames = 4
    now = datetime.datetime.now()
    time_str_colon = now.strftime("%H:%M")
    time_str_space = now.strftime("%H %M")
    
    for f in range(num_frames):
        # Base canvas: dark retro navy
        img = Image.new("RGBA", (width, height), (8, 12, 22, 255))
        
        # 1. Place Avatar with subtle breathing/bounce
        # f=0: Y=0, open
        # f=1: Y=-2, open (inhale)
        # f=2: Y=-1, blink (eyes closed)
        # f=3: Y=0, open (exhale)
        y_offsets = [0, -2, -1, 0]
        cur_avatar = avatar_blink if f == 2 else avatar_open
        y_off = y_offsets[f]
        
        # Paste avatar at (110, y_off)
        img.paste(cur_avatar, (110, y_off), cur_avatar)
        
        # 2. Draw Twinkling Stars on the avatar background
        draw_stars = ImageDraw.Draw(img)
        for i, (sx, sy) in enumerate(stars):
            # Each star has a cycle phase
            phase = (i + f) % 4
            if phase == 0:
                # Dim dot
                draw_stars.point((sx, sy), fill=(100, 140, 190, 180))
            elif phase == 1:
                # Bright 1px dot
                draw_stars.point((sx, sy), fill=(200, 240, 255, 255))
            elif phase == 2:
                # Cross star (+)
                draw_stars.point((sx, sy), fill=(255, 255, 255, 255))
                draw_stars.point((sx - 1, sy), fill=(180, 220, 255, 200))
                draw_stars.point((sx + 1, sy), fill=(180, 220, 255, 200))
                draw_stars.point((sx, sy - 1), fill=(180, 220, 255, 200))
                draw_stars.point((sx, sy + 1), fill=(180, 220, 255, 200))
            else:
                # Fading
                draw_stars.point((sx, sy), fill=(70, 90, 140, 120))
                
        # If breathing high (f=1 or 2), small magic sparkle near Tram's hair
        if f in (1, 2):
            mx, my = 122, 70 + y_off
            draw_stars.point((mx, my), fill=(255, 230, 100, 255))
            draw_stars.point((mx-1, my), fill=(255, 200, 50, 180))
            draw_stars.point((mx+1, my), fill=(255, 200, 50, 180))
            draw_stars.point((mx, my-1), fill=(255, 200, 50, 180))
            draw_stars.point((mx, my+1), fill=(255, 200, 50, 180))

        # 3. Left HUD Panel (X: 3 ~ 114)
        overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        ol_draw = ImageDraw.Draw(overlay)
        left_w = 114
        ol_draw.rectangle([3, 3, left_w, 236], fill=(10, 14, 24, 235), outline=(35, 60, 95, 250), width=1)
        ol_draw.line([(6, 48), (left_w - 3, 48)], fill=(30, 50, 80, 200), width=1)
        ol_draw.line([(6, 86), (left_w - 3, 86)], fill=(30, 50, 80, 200), width=1)
        ol_draw.line([(6, 126), (left_w - 3, 126)], fill=(30, 50, 80, 200), width=1)
        ol_draw.line([(6, 190), (left_w - 3, 190)], fill=(30, 50, 80, 200), width=1)
        
        # Divider line with slight neon shimmer
        div_alpha = 180 if f % 2 == 0 else 240
        ol_draw.line([(left_w + 1, 0), (left_w + 1, 240)], fill=(0, 220, 255, div_alpha), width=1)
        
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)
        
        # Section 1: Clock & Weather (Blinking colon)
        cur_time_str = time_str_colon if (f % 2 == 0) else time_str_space
        draw.text((8, 8), cur_time_str, fill=(0, 255, 230), font=font_clock)
        draw.text((8, 30), f"{now.strftime('%a').upper()} | SEOUL 20°C", fill=(255, 215, 0), font=font_sm)
        
        # Section 2: Work Countdown
        draw.text((8, 54), "EXIT 06h 06m", fill=(255, 200, 50), font=font_title)
        wb_x, wb_y, wb_w, wb_h = 8, 68, 100, 8
        draw.rectangle([wb_x, wb_y, wb_x + wb_w, wb_y + wb_h], fill=(20, 28, 40), outline=(50, 70, 100))
        draw.rectangle([wb_x + 1, wb_y + 1, wb_x + 1 + 32, wb_y + wb_h - 1], fill=(255, 170, 0))
        
        # Section 3: Pomodoro Task Counter (12-blocks)
        need_break = (pomo_completed >= pomo_target)
        if need_break:
            p_color = (0, 255, 200) if f % 2 == 0 else (100, 255, 230)
            p_title = "[REST] 12/12"
        else:
            p_color = (255, 95, 95)
            p_title = f"POMO {pomo_completed}/{pomo_target}"
        draw.text((8, 92), p_title, fill=p_color, font=font_title)
        
        block_y = 105
        block_h = 8
        for i in range(pomo_target):
            bx = 8 + i * 8
            if i < pomo_completed:
                b_color = (0, 240, 160) if need_break else ((255, 200, 50) if i >= 9 else (255, 110, 50))
                draw.rectangle([bx, block_y, bx + 6, block_y + block_h], fill=b_color)
            elif i == pomo_completed and not need_break:
                # Currently active next task pulse!
                pulse_color = (80, 120, 160) if f % 2 == 0 else (30, 45, 65)
                draw.rectangle([bx, block_y, bx + 6, block_y + block_h], fill=pulse_color, outline=(0, 200, 255))
            else:
                draw.rectangle([bx, block_y, bx + 6, block_y + block_h], fill=(16, 22, 32), outline=(40, 55, 80))
                
        if need_break:
            draw.text((8, 116), "휴식 권장! 푹 쉬어요~", fill=(0, 255, 180), font=font_kr_sm)
        else:
            rem = max(0, pomo_target - pomo_completed)
            draw.text((8, 116), f"휴식까지 {rem}개 남음", fill=(170, 185, 210), font=font_kr_sm)
            
        # Section 4: CPU & RAM
        draw.text((8, 136), "CPU  32%", fill=(0, 255, 120), font=font_title)
        draw.rectangle([wb_x, 147, wb_x + wb_w, 147 + 7], fill=(16, 26, 36), outline=(45, 75, 105))
        draw.rectangle([wb_x + 1, 148, wb_x + 1 + 32, 147 + 6], fill=(0, 230, 120))
        
        draw.text((8, 160), "RAM  68%", fill=(0, 200, 255), font=font_title)
        draw.rectangle([wb_x, 171, wb_x + wb_w, 171 + 7], fill=(16, 26, 36), outline=(45, 75, 105))
        draw.rectangle([wb_x + 1, 172, wb_x + 1 + 68, 171 + 6], fill=(0, 180, 255))
        
        # Section 5: RPG Dialogue Box at Center-Bottom
        if pomo_completed == 1:
            dialogue_info = {
                "badge": "▶ 트램 [업무 시작]" if f % 2 == 0 else "▷ 트램 [업무 시작]",
                "badge_color": (0, 220, 255),
                "border_color": (0, 220, 255, 240),
                "line1": "새 세션 시작! 오늘도 힘내보자구~ ★",
                "line2": "첫 번째 작업 완료! 멋진 스타트야!"
            }
        elif need_break:
            dialogue_info = {
                "badge": "▶ 트램 [휴식 권장]" if f % 2 == 0 else "▷ 트램 [휴식 권장]",
                "badge_color": (5, 223, 114),
                "border_color": (5, 223, 114, 240),
                "line1": "12개 완료 대단해! 이제 푹 쉬어~",
                "line2": "스트레칭하고 물 한잔 마시고 오자~"
            }
        else:
            dialogue_info = None
            
        if dialogue_info:
            box_x1, box_y1, box_x2, box_y2 = 8, 196, 232, 236
            ol_box = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            box_draw = ImageDraw.Draw(ol_box)
            box_draw.rectangle([box_x1, box_y1, box_x2, box_y2], fill=(10, 15, 26, 242), outline=dialogue_info["border_color"], width=1)
            box_draw.rectangle([box_x1 + 2, box_y1 + 2, box_x2 - 2, box_y2 - 2], outline=(30, 50, 80, 180), width=1)
            
            badge_w = 96
            box_draw.rectangle([box_x1 + 6, box_y1 - 7, box_x1 + badge_w, box_y1 + 4], fill=dialogue_info["badge_color"])
            
            img = Image.alpha_composite(img, ol_box)
            draw = ImageDraw.Draw(img)
            
            draw.text((box_x1 + 8, box_y1 - 7), dialogue_info["badge"], fill=(10, 14, 24), font=font_kr_sm)
            draw.text((box_x1 + 8, box_y1 + 8), dialogue_info["line1"], fill=(255, 255, 255), font=font_kr)
            draw.text((box_x1 + 8, box_y1 + 22), dialogue_info["line2"], fill=(255, 230, 130), font=font_kr_sm)

        # Convert RGBA to RGB with 256 colors for clean GIF
        frames.append(img.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT))
        
    frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=280, loop=0, optimize=True)
    print(f"Generated animated dashboard: {output_path} ({os.path.getsize(output_path)} bytes)")

if __name__ == "__main__":
    create_animated_dashboard("test_dashboard_live.gif", pomo_completed=5)
    create_animated_dashboard("test_dashboard_start.gif", pomo_completed=1)
    create_animated_dashboard("test_dashboard_rest.gif", pomo_completed=12)
