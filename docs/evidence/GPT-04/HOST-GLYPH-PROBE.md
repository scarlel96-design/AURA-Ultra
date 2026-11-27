# Host glyph probe — GPT-04 round 02
Date: 2026-11-28 KST. Candidate b68a78233db16e4f35a73a03ce4117f830722dca. This is a host font-fit probe, not a Wear OS screenshot or renderer test. The rectangles reproduce signature-draft.json and the two subregions in generate_basic_face.py. Use the synthetic labels only. No personal data.
Environment: Linux container, Pillow 12.3.0, fontTools 4.63.0. Debian fonts-noto-cjk 1:20240730+repack1-1; Noto Sans CJK KR Regular index 1 of NotoSansCJK-Regular.ttc, version 2.004; SIL OFL 1.1 (installed Debian copyright metadata, upstream https://github.com/notofonts/noto-cjk). Font SHA-256 b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a. No font is copied into the repository or packaged. Pillow/fontTools are preinstalled host tools only, not runtime or CI dependencies.
## Reproduction
Use the same font file and versions. Run the following Python code. The actual executed probe used these rectangles and strings; the cmap verification was a separate command.
```python
from PIL import ImageFont, __version__
from hashlib import sha256
from pathlib import Path
p=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
print('Pillow',__version__,'font',sha256(p.read_bytes()).hexdigest())
regions={'brand':(145,42,160,24,15),'date':(90,78,174,32,23),'battery':(274,78,86,32,23),'time':(44,124,362,110,96),'weather_title':(62,247,158,18,14),'weather_value':(62,265,158,34,25),'heart_title':(230,247,158,18,14),'heart_value':(230,265,158,34,25),'steps':(98,312,254,35,23),'rain':(127,357,196,29,23)}
samples={'brand':['AURA ULTRA'],'date':['12.31 · Wed','12.31 · 수','01.01 · 일'],'battery':['0%','100%'],'time':['00:00','09:59','12:59','23:59','08:08'],'weather_title':['Thunderstorm','Heavy snow','Partly cloudy','천둥번개 동반 비','매우 강한 눈','흐림','WX'],'weather_value':['-40°C','! -40°C','! 122°F','ERR','--'],'heart_title':['HR'],'heart_value':['240 bpm','-- bpm'],'steps':['0 / 1000','999999 / 999999'],'rain':['P 0%','P ! 100%','P --']}
print('total strings',sum(map(len,samples.values())))
for d in [432,438,480,498]:
    failures=[];min_x=999;min_y=999;n=0
    for key,strings in samples.items():
        x,y,w,h,f=regions[key]
        W=((x+w)*d+449)//450-x*d//450
        H=((y+h)*d+449)//450-y*d//450
        font=ImageFont.truetype(str(p),f*d//450,index=1)
        for s in strings:
            a,b,c,e=font.getbbox(s)
            width=max(c-a,font.getlength(s))
            height=e-b
            n+=1;min_x=min(min_x,W-width);min_y=min(min_y,H-height)
            if width>W or height>H:
                failures.append((key,s,W,H,width,height))
    print(d,n,'fit',n-len(failures),'min remaining',round(min_x,3),min_y,'failures',failures)
```
## Actual stdout
```
Pillow 12.3.0 font b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a
total strings 31
432 31 fit 31 min remaining 26 4 failures []
438 31 fit 31 min remaining 28 4 failures []
480 31 fit 31 min remaining 29.953 4 failures []
498 31 fit 31 min remaining 31 4 failures []
```
Separate fontTools TTFont(fontNumber=1).getBestCmap() check of the sample character set: Missing characters: []; Font version: Version 2.004;hotconv 1.0.118;makeotfexe 2.5.65603; fontTools 4.63.0. These are 124 host fit checks, not 124 Android test cases. Measured width is max of advance width and bounding box width; height is bbox height. Remaining width/height is total unoccupied extent, not per-edge margin. This is not a proof of baseline centering, exact device glyphs, all text, locale time formatting, contrast, AOD pixels, or accessibility. Runtime checks NOT RUN. No font license or product font selection is finalized. Future: use actual device screenshot bounds, worst-case localized strings and 12/24-hour transitions.
