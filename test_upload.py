import requests
import io
import time

IP = "10.100.1.145"

with open("/Users/2510-n0001/.gemini/antigravity-ide/brain/46b75ad2-ba3c-4eb4-bd4b-35f002bdfea6/live_celebration_animated.gif", "rb") as f:
    gif_bytes = f.read()

print(f"Uploading {len(gif_bytes)} bytes...")
res = requests.post(f"http://{IP}/doUpload?dir=/image/", files={'file': ('cel.gif', gif_bytes, 'image/gif')})
print("Upload status:", res.status_code, res.text)

if res.status_code == 200:
    print("Setting image...")
    res2 = requests.get(f"http://{IP}/set?img=%2Fimage%2Fcel.gif")
    print("Set status:", res2.status_code, res2.text)
