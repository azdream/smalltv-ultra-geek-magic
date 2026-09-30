import datetime
import math
import os
import psutil
import io
from PIL import Image, ImageDraw, ImageFont

class RetroDashboardRenderer:
    def __init__(self, fonts_dir="fonts"):
        self.width = 240
        self.height = 240
        self.fonts_dir = fonts_dir
        
        # Load pixel fonts
        try:
            self.font_clock = ImageFont.truetype(os.path.join(fonts_dir, "PressStart2P.ttf"), 11)
            self.font_title = ImageFont.truetype(os.path.join(fonts_dir, "PressStart2P.ttf"), 7)
            self.font_main = ImageFont.truetype(os.path.join(fonts_dir, "Silkscreen.ttf"), 8)
            self.font_sm = ImageFont.truetype(os.path.join(fonts_dir, "Silkscreen.ttf"), 7)
        except Exception:
            self.font_clock = ImageFont.load_default()
            self.font_title = ImageFont.load_default()
            self.font_main = ImageFont.load_default()
            self.font_sm = ImageFont.load_default()

        # Load Korean font
        korean_font_candidates = [
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/Library/Fonts/NanumGothic.ttf"
        ]
        self.font_kr = None
        self.font_kr_sm = None
        self.font_kr_lg = None
        for kp in korean_font_candidates:
            if os.path.exists(kp):
                try:
                    self.font_kr = ImageFont.truetype(kp, 10)
                    self.font_kr_sm = ImageFont.truetype(kp, 8)
                    self.font_kr_lg = ImageFont.truetype(kp, 14)
                    break
                except Exception:
                    pass
        if not self.font_kr:
            self.font_kr = self.font_main
            self.font_kr_sm = self.font_sm
            self.font_kr_lg = self.font_main

        # Prepare High-Resolution Crisp Tram Avatars for Conditions
        self.avatar_hires = self._prepare_hires_avatar()
        self.avatar_tired = self._prepare_tired_avatar()
        self.avatar_exhausted = self._prepare_exhausted_avatar()
        self.celeb_base = self._prepare_celeb_base()

    def _prepare_hires_avatar(self):
        hires_path = "avatar_hires_clean.png"
        if os.path.exists(hires_path):
            return Image.open(hires_path).convert("RGBA")

        base_path = "/Users/2510-n0001/.gemini/antigravity-ide/brain/46b75ad2-ba3c-4eb4-bd4b-35f002bdfea6/pixel_side_layout_avatar_1790730955531.jpg"
        orig = Image.open(base_path)
        crop_x1 = int(122 / 240.0 * 1024)
        crop_y2 = int(138 / 240.0 * 1024)
        clean_crop = orig.crop((crop_x1, 0, 1024, crop_y2))
        av = clean_crop.resize((118, 138), Image.Resampling.LANCZOS)
        av.save(hires_path)
        return av.convert("RGBA")

    def _prepare_tired_avatar(self):
        hires_path = "avatar_hires_tired.png"
        if os.path.exists(hires_path):
            return Image.open(hires_path).convert("RGBA")

        fallback = "/Users/2510-n0001/.gemini/antigravity-ide/brain/46b75ad2-ba3c-4eb4-bd4b-35f002bdfea6/avatar_tram_tired_1790736778783.jpg"
        if os.path.exists(fallback):
            orig = Image.open(fallback)
            crop_x1 = int(122 / 240.0 * 1024)
            crop_y2 = int(138 / 240.0 * 1024)
            clean_crop = orig.crop((crop_x1, 0, 1024, crop_y2))
            av = clean_crop.resize((118, 138), Image.Resampling.LANCZOS)
            av.save(hires_path)
            return av.convert("RGBA")

        return self.avatar_hires

    def _prepare_exhausted_avatar(self):
        hires_path = "avatar_hires_exhausted.png"
        if os.path.exists(hires_path):
            return Image.open(hires_path).convert("RGBA")

        fallback = "/Users/2510-n0001/.gemini/antigravity-ide/brain/46b75ad2-ba3c-4eb4-bd4b-35f002bdfea6/avatar_tram_exhausted_1790736797862.jpg"
        if os.path.exists(fallback):
            orig = Image.open(fallback)
            crop_x1 = int(122 / 240.0 * 1024)
            crop_y2 = int(138 / 240.0 * 1024)
            clean_crop = orig.crop((crop_x1, 0, 1024, crop_y2))
            av = clean_crop.resize((118, 138), Image.Resampling.LANCZOS)
            av.save(hires_path)
            return av.convert("RGBA")

        return self.avatar_hires

    def _prepare_celeb_base(self):
        local_path = "celeb_fullshot_base.jpg"
        if os.path.exists(local_path):
            return Image.open(local_path).convert("RGB").resize((self.width, self.height), Image.Resampling.LANCZOS)

        fallback_path = "/Users/2510-n0001/.gemini/antigravity-ide/brain/46b75ad2-ba3c-4eb4-bd4b-35f002bdfea6/pixel_task_complete_effect_1790731071936.jpg"
        if os.path.exists(fallback_path):
            img = Image.open(fallback_path).convert("RGB").resize((self.width, self.height), Image.Resampling.LANCZOS)
            img.save(local_path)
            return img

        return Image.new("RGB", (self.width, self.height), (15, 12, 22))

    def calculate_work_countdown(self, start_str="08:30", end_str="17:30"):
        now = datetime.datetime.now()
        today = now.date()
        try:
            start_h, start_m = map(int, start_str.split(":"))
            end_h, end_m = map(int, end_str.split(":"))
        except Exception:
            start_h, start_m = 8, 30
            end_h, end_m = 17, 30
            
        work_start = datetime.datetime.combine(today, datetime.time(start_h, start_m))
        work_end = datetime.datetime.combine(today, datetime.time(end_h, end_m))
        total_seconds = max(1.0, (work_end - work_start).total_seconds())
        
        if now < work_start:
            rem = (work_start - now).total_seconds()
            hours, remainder = divmod(int(rem), 3600)
            mins, _ = divmod(remainder, 60)
            return {
                "status": "BEFORE_WORK",
                "label": "일과 시작 전",
                "remaining_text": f"D-{hours:02d}h {mins:02d}m",
                "percent": 0.0
            }
        elif now >= work_end:
            return {
                "status": "OFF_WORK",
                "label": "일과 종료! ★",
                "remaining_text": "자유시간!",
                "percent": 100.0
            }
        else:
            elapsed = (now - work_start).total_seconds()
            rem = (work_end - now).total_seconds()
            hours, remainder = divmod(int(rem), 3600)
            mins, _ = divmod(remainder, 60)
            pct = min(100.0, max(0.0, (elapsed / total_seconds) * 100.0))
            return {
                "status": "WORKING",
                "label": "일과 종료",
                "remaining_text": f"D-{hours:02d}h {mins:02d}m",
                "percent": pct
            }

    def render_animated_dashboard(self, pomodoro_state=None, weather_info=None, work_config=None, num_frames=4):
        """
        Princess Maker 2 Classical Simulation Theme:
        - High-resolution, ultra-crisp Tram Princess avatar on the right
        - Antique Gold/Purple parameter frame
        - Twinkling night sky stars & blinking colon for subtle, elegant motion
        """
        now = datetime.datetime.now()
        if not pomodoro_state:
            pomodoro_state = {"completed": 0, "target": 12}
        if not work_config:
            work_config = {"start": "08:30", "end": "17:30"}
        if not weather_info:
            weather_info = {"temp": "20", "desc": "Clear"}

        completed_tasks = pomodoro_state.get("completed", 0)
        target_tasks = pomodoro_state.get("target", 12)
        idle_seconds = pomodoro_state.get("idle_seconds", 0)
        need_break = completed_tasks >= target_tasks
        work_data = self.calculate_work_countdown(work_config.get("start", "08:30"), work_config.get("end", "17:30"))
        
        cpu_pct = psutil.cpu_percent()
        ram_info = psutil.virtual_memory()
        ram_pct = ram_info.percent

        # Determine Character Condition based on Stress (POMO) & Load (CPU)
        if need_break or cpu_pct >= 95:
            avatar_to_use = self.avatar_exhausted
            condition_text = "탈진(휴식 요망) ♨"
            condition_color = (255, 60, 60)
        elif completed_tasks >= 8 or cpu_pct >= 90:
            avatar_to_use = self.avatar_tired
            condition_text = "피로 누적 중..." if completed_tasks >= 8 else "과부하 열일 중!"
            condition_color = (255, 170, 50)
        else:
            avatar_to_use = self.avatar_hires
            condition_text = "최상 (건강함) ★"
            condition_color = (120, 240, 150)

        # Classical dialogue selection according to condition
        dlg_name = "◆ 트램"
        if work_data["status"] == "OFF_WORK":
            dlg_msg = "오늘의 모든 일정이 끝났습니다! 수고 많으셨습니다. 태양님, 편안한 저녁 시간 보내세요."
        elif need_break or cpu_pct >= 95:
            dlg_msg = "태양님, 피로도가 한계에 도달했습니다. 업무 효율을 위해 잠시 휴식을 취해주세요."
        elif completed_tasks >= 8 or cpu_pct >= 85:
            dlg_msg = f"업무가 꽤 진행되었네요. 휴식(12완료)까지 {target_tasks - completed_tasks}개 남았습니다. 차 한 잔 어떠신가요?"
        elif completed_tasks == 1:
            dlg_msg = "첫 번째 작업이 완료되었습니다! 훌륭한 시작입니다. 오늘도 쾌조의 하루 되세요."
        elif idle_seconds > 300:
            idle_msgs = [
                "태양님, 너무 조용하네요! 잠시 기지개를 켜보는 건 어떨까요?",
                "(거울을 보며 단정하게 매무새를 가다듬고 있다)",
                "(창밖을 바라보며 가볍게 스트레칭을 한다)",
                "(주변을 이리저리 둘러보며 태양님의 다음 지시를 기다린다)",
                "조금 출출하시지 않나요? 가벼운 간식으로 리프레시할 시간입니다!",
                "태양님, 따뜻한 차 한 잔 내어 드릴까요?",
                "(가볍게 콧노래를 부르며 주변을 정돈하고 있다)",
                "(가벼운 산책을 다녀올까 고민하며 발을 굴러본다)"
            ]
            dlg_msg = idle_msgs[(idle_seconds // 300) % len(idle_msgs)]
        else:
            dlg_msg = f"태양님, 현재 시스템 컨디션 좋습니다. 계속해서 다음 업무를 진행해 주세요. (현재 {completed_tasks}개 태스크 완수)"

        star_positions = [(132, 20), (225, 30), (228, 90), (130, 85), (218, 140), (136, 160)]
        frames = []

        for f in range(num_frames):
            img = Image.new("RGB", (self.width, self.height), (15, 12, 22))
            
            # 1. Tram Avatar - Dynamically expresses condition (Normal, Tired, Exhausted)
            img.paste(avatar_to_use, (122, 0), avatar_to_use)
            
            overlay = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            ol_draw = ImageDraw.Draw(overlay)
            
            # 2. PM2 Classical Status Frame (X: 3 ~ 118, Y: 3 ~ 132)
            ol_draw.rectangle([0, 0, 120, 136], fill=(15, 12, 22, 255))
            ol_draw.rectangle([3, 3, 118, 133], fill=(20, 16, 28, 255), outline=(180, 140, 60, 255), width=1)
            ol_draw.rectangle([5, 5, 116, 131], outline=(60, 45, 80, 255), width=1)
            ol_draw.line([(120, 0), (120, 136)], fill=(180, 140, 60, 220), width=1)
            
            # Twinkling Stars in Avatar Background
            for i, (sx, sy) in enumerate(star_positions):
                phase = (i + f) % 4
                if phase == 0:
                    ol_draw.rectangle([sx-1, sy, sx+1, sy], fill=(255, 255, 255, 255))
                    ol_draw.rectangle([sx, sy-1, sx, sy+1], fill=(255, 255, 255, 255))
                    ol_draw.point((sx, sy), fill=(255, 240, 150, 255))
                elif phase == 1:
                    ol_draw.point((sx, sy), fill=(255, 255, 255, 240))
                elif phase == 2:
                    ol_draw.point((sx, sy), fill=(100, 160, 240, 180))

            # 3. PM2 Signature Dialogue Box at Bottom (X: 4 ~ 236, Y: 138 ~ 236)
            ol_draw.rectangle([4, 138, 236, 236], fill=(16, 12, 24, 255), outline=(200, 160, 70, 255), width=2)
            ol_draw.rectangle([7, 141, 233, 233], outline=(60, 45, 75, 255), width=1)
            ol_draw.rectangle([12, 134, 76, 150], fill=(180, 140, 60, 255))
            
            img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
            draw = ImageDraw.Draw(img)

            # Header
            draw.rectangle([6, 6, 115, 34], fill=(30, 24, 42))
            colon = ":" if f % 2 == 0 else " "
            time_hm = f"{now.strftime('%H')}{colon}{now.strftime('%M')}"
            draw.text((10, 8), time_hm, fill=(255, 230, 100), font=self.font_clock)
            
            # Weather Icon
            w_desc = weather_info.get("desc", "Clear").lower()
            wx, wy = 94, 8
            if "cloud" in w_desc:
                draw.rectangle([wx+2, wy+4, wx+10, wy+8], fill=(220, 220, 230))
                draw.rectangle([wx+4, wy+2, wx+8, wy+4], fill=(220, 220, 230))
            elif "rain" in w_desc:
                draw.rectangle([wx+2, wy+3, wx+10, wy+6], fill=(160, 170, 190))
                draw.rectangle([wx+4, wy+1, wx+8, wy+3], fill=(160, 170, 190))
                for rx in [3, 6, 9]:
                    draw.line([(wx+rx, wy+8), (wx+rx-1, wy+10)], fill=(120, 180, 255))
            else: # Sun
                draw.rectangle([wx+4, wy+3, wx+8, wy+7], fill=(255, 200, 50))
                draw.point((wx+6, wy+1), fill=(255, 220, 100))
                draw.point((wx+6, wy+9), fill=(255, 220, 100))
                draw.point((wx+2, wy+5), fill=(255, 220, 100))
                draw.point((wx+10, wy+5), fill=(255, 220, 100))
                draw.point((wx+3, wy+2), fill=(255, 220, 100))
                draw.point((wx+9, wy+8), fill=(255, 220, 100))
                draw.point((wx+9, wy+2), fill=(255, 220, 100))
                draw.point((wx+3, wy+8), fill=(255, 220, 100))

            k_weekdays = ["월", "화", "수", "목", "금", "토", "일"]
            wk_str = k_weekdays[now.weekday()]
            date_str = f"{now.month}월{now.day}일({wk_str})"
            draw.text((10, 22), date_str, fill=(220, 200, 160), font=self.font_kr_sm)
            draw.text((82, 22), f"{weather_info.get('temp', '20')}°C", fill=(255, 215, 80), font=self.font_sm)

            # Parameters
            # CPU
            draw.text((8, 40), f"CPU {cpu_pct:2.0f}%", fill=(255, 110, 100), font=self.font_kr_sm)
            draw.rectangle([8, 50, 113, 56], fill=(12, 10, 18), outline=(80, 60, 70))
            c_fill = int(103 * (cpu_pct / 100.0))
            if c_fill > 0:
                draw.rectangle([9, 51, 9 + c_fill, 55], fill=(230, 60, 60))

            # RAM
            draw.text((8, 62), f"RAM {ram_pct:2.0f}%", fill=(100, 200, 255), font=self.font_kr_sm)
            draw.rectangle([8, 72, 113, 78], fill=(12, 10, 18), outline=(50, 70, 90))
            r_fill = int(103 * (ram_pct / 100.0))
            if r_fill > 0:
                draw.rectangle([9, 73, 9 + r_fill, 77], fill=(50, 160, 230))

            # Exit
            draw.text((8, 84), f"퇴근까지 {work_data['remaining_text']}", fill=(255, 215, 80), font=self.font_kr_sm)
            draw.rectangle([8, 94, 113, 100], fill=(12, 10, 18), outline=(80, 70, 50))
            w_fill = int(103 * (work_data["percent"] / 100.0))
            if w_fill > 0:
                draw.rectangle([9, 95, 9 + w_fill, 99], fill=(255, 180, 40))
                if f % 2 == 1:
                    draw.rectangle([9 + w_fill - 1, 95, 9 + w_fill, 99], fill=(255, 240, 150))

            # Stress (POMO 12 blocks)
            p_color = (255, 60, 60) if need_break else (255, 130, 200)
            draw.text((8, 107), "스트레스", fill=p_color, font=self.font_kr_sm)
            
            for i in range(target_tasks):
                bx = 8 + i * 8
                if i < completed_tasks:
                    b_col = (255, 60, 60) if need_break else ((255, 180, 50) if i >= 9 else (255, 80, 120))
                    if i == completed_tasks - 1 and f % 2 == 1:
                        b_col = (255, 240, 150)
                    draw.rectangle([bx, 118, bx + 6, 126], fill=b_col)
                elif i == completed_tasks and not need_break:
                    pulse_col = (80, 50, 70) if f % 2 == 0 else (30, 20, 35)
                    draw.rectangle([bx, 118, bx + 6, 126], fill=pulse_col, outline=(255, 140, 180))
                else:
                    draw.rectangle([bx, 118, bx + 6, 126], fill=(25, 20, 35), outline=(60, 45, 70))

            # Status summary (Removed as per user request to drop condition/task counts)

            # Dialogue Box
            draw.text((16, 134), dlg_name, fill=(15, 10, 20), font=self.font_kr)
            import textwrap
            wrapped_lines = textwrap.wrap(dlg_msg, width=16)
            for idx, line in enumerate(wrapped_lines[:4]):  # Max 4 lines
                draw.text((14, 154 + (idx * 20)), line, fill=(255, 255, 255), font=self.font_kr_lg)

            # High quality quantization (colors=64) preserves crisp beauty and stays ultra-light (~45KB)
            frame_q = img.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            frames.append(frame_q)

        buf = io.BytesIO()
        frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=350, loop=0, optimize=True)
        return buf.getvalue()

    def render_animated_celebration(self, app_name="AGY", count=5, title="작업 완료!", num_frames=4):
        """
        Princess Maker 2 Fullshot Celebration Theme:
        - Full-screen center shot of Princess Tram celebrating with raised hands!
        - Top banner: Rainbow "TASK COMPLETE!" with glowing stars and confetti
        - Dynamic twinkling star sparkles
        - Bottom PM2 dialogue box: Butler Cube reporting job success, gold earned, and stress
        """
        sparkles = [(30, 75), (210, 80), (25, 125), (215, 125), (75, 45), (165, 45), (120, 30), (50, 155), (190, 155)]
        frames = []

        for f in range(num_frames):
            img = self.celeb_base.copy()
            draw = ImageDraw.Draw(img)

            # Twinkling sparkles on the congratulations stars & confetti
            for i, (sx, sy) in enumerate(sparkles):
                phase = (i + f) % 4
                if phase == 0:
                    draw.rectangle([sx-2, sy, sx+2, sy], fill=(255, 255, 255))
                    draw.rectangle([sx, sy-2, sx, sy+2], fill=(255, 255, 255))
                    draw.point((sx, sy), fill=(255, 255, 200))
                elif phase == 1:
                    draw.rectangle([sx-1, sy-1, sx+1, sy+1], fill=(255, 230, 70))
                elif phase == 2:
                    draw.point((sx, sy), fill=(255, 180, 0))

            # Bottom PM2 Butler Cube Report Dialogue Box (Solid dark for 100% clean readability)
            box_y1, box_y2 = 180, 236
            draw.rectangle([4, box_y1, 236, box_y2], fill=(16, 12, 24), outline=(220, 180, 70), width=2)
            draw.rectangle([7, box_y1 + 3, 233, box_y2 - 3], outline=(60, 45, 75), width=1)

            # Name badge: Housekeeper Cube
            badge_col = (200, 160, 60) if f % 2 == 0 else (240, 200, 80)
            draw.rectangle([10, box_y1 - 7, 85, box_y1 + 6], fill=badge_col)
            draw.text((14, box_y1 - 7), "◆ 집사 큐브", fill=(15, 10, 20), font=self.font_kr_sm)

            msg_line1 = f"태양님, [{app_name}] 작업이 완료되었습니다."
            if count >= 12:
                msg_line2 = f"누적 {count}번째 완료! 피로가 누적되었으니 잠시 휴식을 권장합니다."
            else:
                msg_line2 = f"오늘 {count}번째 태스크 완수. (스트레스 {count}/12)"
            
            import textwrap
            dlg_msg = f"{msg_line1} {msg_line2}"
            wrapped_lines = textwrap.wrap(dlg_msg, width=16)
            for idx, line in enumerate(wrapped_lines[:4]):
                draw.text((14, box_y1 + 16 + (idx * 20)), line, fill=(255, 255, 255), font=self.font_kr_lg)

            frame_q = img.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
            frames.append(frame_q)

        buf = io.BytesIO()
        frames[0].save(buf, format="GIF", save_all=True, append_images=frames[1:], duration=250, loop=0, optimize=True)
        return buf.getvalue()

    def render(self, pomodoro_state=None, weather_info=None, work_config=None):
        """Backward-compatible single-frame image"""
        gif_bytes = self.render_animated_dashboard(pomodoro_state, weather_info, work_config, num_frames=1)
        return Image.open(io.BytesIO(gif_bytes)).convert("RGB")

    def render_notification(self, title="작업 완료!", message="에이전트 작업 완료!", remaining_secs=0):
        """Backward-compatible single-frame notification"""
        gif_bytes = self.render_animated_celebration(title=title, count=1, num_frames=1)
        return Image.open(io.BytesIO(gif_bytes)).convert("RGB")
