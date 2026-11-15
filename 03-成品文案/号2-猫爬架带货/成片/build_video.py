# -*- coding: utf-8 -*-
"""猫爬架带货视频合成：edge-tts 配音 + PIL 帧 + ffmpeg 拼接"""
import os, subprocess, wave, sys

BASE = r"D:\姜胡说笔记\03-成品文案\号2-猫爬架带货"
MAT = os.path.join(BASE, "素材")
OUT = os.path.join(BASE, "成片")
TMP = os.path.join(OUT, "tmp")
os.makedirs(TMP, exist_ok=True)
FF = r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\Lib\site-packages\imageio_ffmpeg\binaries\ffmpeg-win-x86_64-v9.0.2.exe"

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

# 找中文字体
FONT = None
for c in [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
    if os.path.exists(c):
        FONT = c; break
assert FONT, "找不到中文字体"

SEGS = [
 ("01-开场-主图全景.png", "猫爬架别乱买，买错了猫不上去，白占地方。", "猫爬架别乱买"),
 ("07-卖点6-多猫各一层不打架.png", "家里猫多的都懂：俩猫抢一个窝，猫抓板买了五六个，沙发照样抓烂。", "俩猫抢窝 · 沙发遭殃"),
 ("03-卖点2-只占一小角42cm.png", "大个子爬架往客厅一放，人都没地方走。", "还特别占地方"),
 ("04-卖点3-全剑麻1.27平米.png", "挑猫爬架，就看三点。第一，看剑麻面积。猫磨爪只认剑麻，这种全身包裹剑麻的，1.27个平方，从头抓到尾，沙发才算保住了。", "检查点一：剑麻面积 1.27平米"),
 ("02-卖点1-承重20KG.png", "第二，看占地和承重。底座42公分，就占墙角一小块；高96公分，承重20公斤，肥猫大猫，照样爬得稳。", "检查点二：占地小 · 承重20公斤"),
 ("05-卖点4-顶部瞭望台.png", "第三，看层数。三层每层独立空间，家里几只猫各有各的窝，互不打扰，顶上还有瞭望台。", "检查点三：三层独立空间"),
 ("06-卖点5-肥猫大猫也稳.png", "这样的配置，289块9起，白色灰色两个色，带棉垫的规格也有。一个爬架用三年，一天不到三毛钱。", "289.9起 · 一天不到三毛"),
 ("08-信任-权威检测报告.png", "小黄车1号链接，7天无理由，48小时发货。", "7天无理由 · 48小时发货"),
 ("01-开场-主图全景.png", "给你家猫，安排上。", "1号链接 · 安排上"),
]

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("FAIL:", " ".join(cmd)[:200]); print(r.stderr[-800:]); sys.exit(1)

def tts(text, path):
    run([sys.executable, "-m", "edge_tts", "--voice", "zh-CN-YunjianNeural",
         "--text", text, "--write-media", path])

def audio_wav(mp3, wav):
    run([FF, "-y", "-i", mp3, "-ar", "44100", "-ac", "1", wav])

def wav_dur(p):
    with wave.open(p, "rb") as w:
        return w.getnframes() / w.getnframes() and (w.getnframes() / float(w.getframerate()))

def make_frame(img_name, caption, out_png):
    W, H = 1080, 1920
    src = Image.open(os.path.join(MAT, img_name)).convert("RGB")
    # 背景：放大铺满+模糊+压暗
    bg = src.copy()
    ratio = max(W/bg.width, H/bg.height)
    bg = bg.resize((int(bg.width*ratio)+1, int(bg.height*ratio)+1))
    x = (bg.width-W)//2; y = (bg.height-H)//2
    bg = bg.crop((x, y, x+W, y+H)).filter(ImageFilter.GaussianBlur(26))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    canvas = bg
    # 前景：宽1080居中
    fg = src.resize((W, int(src.height*W/src.width)))
    fy = max(120, (H-fg.height)//2 - 160)
    if fy + fg.height > H - 260: fy = H - 260 - fg.height
    canvas.paste(fg, (0, fy))
    d = ImageDraw.Draw(canvas)
    # 底部字幕条
    font = ImageFont.truetype(FONT, 58)
    tw = d.textlength(caption, font=font)
    bx = (W-tw)//2; by = H-300
    d.rounded_rectangle([bx-36, by-30, bx+tw+36, by+86], radius=24, fill=(0,0,0,180))
    d.text((bx, by), caption, font=font, fill=(255,255,255), stroke_width=2, stroke_fill=(0,0,0))
    canvas.save(out_png, quality=92)

durs = []
for i, (img, text, cap) in enumerate(SEGS, 1):
    mp3 = os.path.join(TMP, f"seg{i}.mp3"); wav = os.path.join(TMP, f"seg{i}.wav")
    frame = os.path.join(TMP, f"frame{i}.png")
    print(f"[{i}/9] 配音: {text[:18]}...")
    tts(text, mp3); audio_wav(mp3, wav)
    dur = wav_dur(wav) + 0.5
    durs.append(dur)
    print(f"    时长 {dur:.1f}s, 画面: {img}")
    make_frame(img, cap, frame)

print("合成视频段...")
for i, dur in enumerate(durs, 1):
    out = os.path.join(TMP, f"part{i}.mp4")
    run([FF, "-y", "-loop", "1", "-framerate", "30", "-t", f"{dur:.2f}",
         "-i", os.path.join(TMP, f"frame{i}.png"),
         "-i", os.path.join(TMP, f"seg{i}.wav"),
         "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-shortest", out])

lst = os.path.join(TMP, "list.txt")
with open(lst, "w") as f:
    for i in range(1, len(SEGS)+1):
        f.write(f"file 'part{i}.mp4'\n")
final = os.path.join(OUT, "猫爬架-别乱买看这3处-成片.mp4")
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", final])
print("DONE:", final, os.path.getsize(final)//1024, "KB, 总时长约", f"{sum(durs):.0f}s")
