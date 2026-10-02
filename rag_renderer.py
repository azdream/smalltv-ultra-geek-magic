import datetime
import io
import os
import math
from PIL import Image, ImageDraw, ImageFont

class RagMonitorRenderer:
    def __init__(self, fonts_dir="fonts"):
        self.width = 240
        self.height = 240
        
        try:
            self.font_main = ImageFont.truetype(os.path.join(fonts_dir, "Silkscreen.ttf"), 8)
            self.font_title = ImageFont.truetype(os.path.join(fonts_dir, "PressStart2P.ttf"), 9)
        except Exception:
            self.font_main = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            
        korean_font_candidates = [
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/NanumGothic.ttf"
        ]
        self.font_kr = None
        for kp in korean_font_candidates:
            if os.path.exists(kp):
                try:
                    self.font_kr = ImageFont.truetype(kp, 10)
                    break
                except Exception:
                    pass
        if not self.font_kr:
            self.font_kr = self.font_main

    def render_dashboard(self, sys_info, services, is_processing=False, num_frames=4):
        """
        RAG Ontology Server Theme:
        - Cyber/Hacker style (Green/Cyan on Dark Background)
        - CPU/RAM bars
        - Docker Service Status
        - Knowledge Graph animated wave
        """
        frames = []
        cpu = sys_info.get("cpu", 0)
        ram = sys_info.get("ram", 0)
        
        # Color Theme: Hacker Green / Cyan
        bg_color = (10, 15, 20)
        text_color = (0, 255, 170)
        alert_color = (255, 50, 80)
        panel_outline = (30, 80, 100)
        
        for f in range(num_frames):
            img = Image.new("RGB", (self.width, self.height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((10, 10), "RAG ONTOLOGY CORE", fill=text_color, font=self.font_title)
            draw.line([(10, 24), (230, 24)], fill=panel_outline, width=1)
            
            # System Resources (CPU & RAM)
            draw.text((10, 32), f"CPU: {cpu:02.0f}%", fill=text_color, font=self.font_main)
            draw.rectangle([60, 32, 160, 40], fill=(20, 30, 40), outline=panel_outline)
            c_w = int(100 * (cpu / 100.0))
            if c_w > 0:
                c_color = alert_color if cpu > 85 else text_color
                draw.rectangle([60, 32, 60 + c_w, 40], fill=c_color)
                
            draw.text((10, 46), f"RAM: {ram:02.0f}%", fill=text_color, font=self.font_main)
            draw.rectangle([60, 46, 160, 54], fill=(20, 30, 40), outline=panel_outline)
            r_w = int(100 * (ram / 100.0))
            if r_w > 0:
                r_color = alert_color if ram > 85 else text_color
                draw.rectangle([60, 46, 60 + r_w, 54], fill=r_color)
                
            # Docker Services
            draw.text((10, 64), "[ DOCKER SERVICES ]", fill=(0, 200, 255), font=self.font_main)
            y = 78
            for srv_name, srv_status in services.items():
                status_text = "RUNNING" if srv_status else "DOWN"
                col = text_color if srv_status else alert_color
                if not srv_status and f % 2 == 0:
                    col = bg_color  # Blink effect if down
                
                # Truncate long service names
                disp_name = srv_name[:14].ljust(14)
                draw.text((10, y), f" {disp_name}: {status_text}", fill=col, font=self.font_main)
                y += 12

            # Ontology Processing Animation (Knowledge Graph I/O Wave)
            y_graph = max(130, y + 10)
            draw.text((10, y_graph), "[ KNOWLEDGE GRAPH I/O ]", fill=(0, 200, 255), font=self.font_main)
            
            node_y = y_graph + 40
            for i in range(10):
                nx = 20 + i * 20
                ny = node_y + int(math.sin((f + i) * 1.5) * 10)
                
                # Active processing effect
                if is_processing:
                    node_col = (0, 255, 170) if (i + f) % 3 == 0 else (0, 100, 100)
                else:
                    node_col = (0, 100, 100)

                draw.ellipse([nx - 3, ny - 3, nx + 3, ny + 3], fill=node_col)
                if i > 0:
                    prev_x = 20 + (i - 1) * 20
                    prev_y = node_y + int(math.sin((f + i - 1) * 1.5) * 10)
                    draw.line([(prev_x, prev_y), (nx, ny)], fill=node_col, width=1)
            
            # Processing status text
            proc_text = "PROCESSING..." if is_processing else "IDLE"
            proc_color = (0, 255, 170) if is_processing else (100, 100, 100)
            draw.text((10, node_y + 20), f"STATUS: {proc_text}", fill=proc_color, font=self.font_main)
            
            # Blinking cursor for terminal effect
            if f % 2 == 0:
                draw.rectangle([220, 220, 228, 230], fill=text_color)
            
            # Quantize for SmallTV (keeps size small)
            frame_q = img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            frames.append(frame_q)
            
        buf = io.BytesIO()
        frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=250, loop=0, optimize=True)
        return buf.getvalue()
