#!/usr/bin/env python3
"""Render the code-native Little Night Workshop banners.

Source of truth: the SVG geometry in this file. No original screenshot is
cropped, repainted or used as a texture. Every frame is rendered from SVG.

Install: python -m pip install pillow
Renderer: install Inkscape and put its command line executable on PATH.
Run: python scripts/render_banners.py
Use --poster-only for a quick SVG + PNG proof without GIF encoding.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageChops

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "profile"
PREVIEW = ROOT / "assets" / "preview"
W = 960
HERO_H = 360
FOOTER_H = 112
LOOP_MS = 16_000
FRAME_MS = 80
FPS = 1000 / FRAME_MS
LOOP_S = LOOP_MS / 1000
P = {
    "sky": "#111c29", "far": "#26394a", "near": "#304b50",
    "tree": "#182e32", "ground": "#4e5843", "grass": "#82906b",
    "ink": "#182830", "cream": "#f2e7cf", "moon": "#e8d4a1",
    "muted": "#becbcc", "star": "#becae0", "hat": "#7772a8",
    "robe": "#61639a", "face": "#e7c4a0", "staff": "#b8976e",
    "mint": "#9bcbb4", "dragon": "#76ae8b", "wing": "#b6d69a",
    "cat": "#65717a", "cat_dark": "#3c4b57", "apricot": "#d9b198",
    "ear": "#e9c5b5", "owl": "#a29dc2", "owl_face": "#dad3df",
    "wisp": "#b6dcd0", "cheek": "#dca9ab", "gold": "#dab97c",
}


def rect(x, y, w, h, color, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" {extra}/>'


def path(d, color, extra=""):
    return f'<path d="{d}" fill="{color}" {extra}/>'


def grp(body, x=0, y=0, scale=1):
    return f'<g transform="translate({x} {y}) scale({scale})" shape-rendering="crispEdges">{body}</g>'


def placed(body, x, y, scale, height, *, dx=0, dy=0, sx=1, sy=1):
    """Scale about the feet; jumping changes position, breathing does not slide."""
    xx=round(x+dx,2);yy=round(y+dy+height*scale*(1-sy),2)
    return f'<g transform="translate({xx} {yy}) scale({scale*sx:.3f} {scale*sy:.3f})" shape-rendering="crispEdges">{body}</g>'


def eyes(xs, y, closed=False, color=None):
    color = color or P["ink"]
    return "".join(rect(x, y + (1 if closed else 0), 2, 1 if closed else 2, color) for x in xs)


def pulse(t, start, length=0.2):
    return start <= (t % LOOP_S) < start + length


def progress(t, start, length):
    return ((t % LOOP_S)-start)/length if pulse(t,start,length) else None


def wave(t,period=4,phase=0):
    return math.sin(2*math.pi*(t+phase)/period)


def hop(t,start,length,height):
    u=progress(t,start,length)
    return 0 if u is None else round(height*math.sin(math.pi*u))


def blink(t,*times):
    return any(pulse(t,s,0.16) for s in times)


def blend(a,b,amount):
    aa=tuple(int(a[i:i+2],16) for i in (1,3,5));bb=tuple(int(b[i:i+2],16) for i in (1,3,5))
    return '#'+''.join(f'{round(x+(y-x)*amount):02x}' for x,y in zip(aa,bb))


def glow_color(t, bright, dim):
    # Quantized, slow color breathing keeps the flat palette stable.
    level=round(((wave(t,4,-1)+1)/2)*6)/6
    return blend(dim,bright,level)


def sparkle(x,y,size=4,color=None):
    color=color or P['cream']; arm=max(1,size//3)
    return rect(x-arm/2,y-size/2,arm,size,color)+rect(x-size/2,y-arm/2,size,arm,color)


def mage(t=0, resting=False):
    if resting:
        return (path("M9 0H18V4H22V8H26V11H0V8H5V4H9Z", P["hat"])
                + rect(7,11,14,9,P["face"]) + eyes([15],14,True)
                + path("M6 20H20V28H26V32H2V27H6Z",P["robe"])
                + rect(19,29,10,3,P["cat_dark"]))
    nod=1 if pulse(t,7.84,0.32) or pulse(t,10.88,0.32) else 0
    head=path("M10 0H20V5H25V11H30V16H0V11H6V5H10Z",P["hat"])
    head+=rect(9,16,15,11,P["face"])+eyes([20],20,blink(t,0.8,5.36,10.88,14.4))
    s=grp(head,0,nod)
    hem=round(wave(t,4)*1.4)
    s+=path(f"M7 27H24V39H{28+hem}V42H{3+hem}V39H7Z",P['robe'])
    s += rect(9,42,6,4,P["ink"]) + rect(21,42,6,4,P["ink"])
    spell=progress(t,8.64,2.0)
    lift=0 if spell is None else round(3*math.sin(math.pi*spell))
    angle=round(1.5*wave(t,4)-(0 if spell is None else 7*math.sin(math.pi*spell)),1)
    staff=rect(35,16-lift,3,30,P['staff'])+rect(32,12-lift,9,9,glow_color(t,'#cef5df','#92c4b2'))
    s+=f'<g transform="rotate({angle} 36 46)">{staff}</g>'
    s+=path(f'M24 28H29V{26-lift}H35V{30-lift}H30V31H24Z',P['face'])
    return s


def dragon(t=0, sleeping=False):
    # Tiny, rounded body, short muzzle, single folded wing.
    tail_up=(wave(t,4)>0.4) and not sleeping
    s = path("M0 20H6V15H10V10H17V7H25V10H31V21H27V26H10V23H0Z",P["dragon"])
    if tail_up: s += path("M0 20V13H3V17H7V23H0Z",P["dragon"])
    else: s += rect(-3,19,6,4,P["dragon"])
    poses=['M12 14V3H18V7H23V17Z','M12 15V0H16V3H21V7H24V17Z','M12 16V-5H17V-2H21V3H23V17Z','M13 17L3 7V1H9V4H15V9H24V17Z']
    flap=[0,1,2,3,2,1][int(((t-1.6)%0.96)/0.16)%6] if pulse(t,1.6,2.24) and not sleeping else 0
    s+=path(poses[flap],P['wing'])
    s += rect(23,7,3,3,P["wing"]) + eyes([25],13,sleeping or blink(t,1.12,3.68,8.0,13.12))
    s += rect(10,26,5,3,P["dragon"]) + rect(22,26,5,3,P["dragon"])
    s += rect(27,19,2,1,P["wing"])
    return s


def cat(t=0, sleeping=False):
    if sleeping:
        return (path("M2 14V7H6V3H10V7H15V4H18V10H23V19H1V16Z",P["cat"])
                + rect(7,12,10,6,P["cream"]) + eyes([8,14],12,True)
                + path("M19 17H26V12H29V20H18Z",P["cat_dark"]))
    ear=2 if pulse(t,4.64,0.24) or pulse(t,4.96,0.24) else 0
    s=path(f'M3 8V{ear}H7V4H15V0H19V8H21V19H17V26H5V22H1V10Z',P['cat'])
    look=1 if pulse(t,4.56,1.68) else 0
    face=rect(5,10,13,10,P['cream'])+eyes([7+look,14+look],12,blink(t,0.96,5.44,9.12,14.72))+rect(10+look,17,3,2,P['apricot'])
    s+=grp(face,look,-1 if pulse(t,4.8,0.64) else 0)
    s+=rect(5,25,4,3,P['cat_dark'])+rect(14,25,4,3,P['cat_dark'])
    tails=['M19 21H25V18H29V24H24V27H18Z','M19 21H24V16H22V13H28V23H24V27H18Z','M19 20H24V9H21V6H28V23H22V26H18Z']
    tail_index=round(wave(t,4)+1)
    s+=path(tails[tail_index],P['cat_dark'])
    if tail_index==2:s+=rect(21,6,4,3,P['cat'])
    return s


def bunny(t=0, sleeping=False):
    if sleeping:
        return (path("M4 9H18V13H23V22H2V17H0V12H4Z",P["apricot"])
                + path("M4 9V2H8V6H14V9Z",P["apricot"])
                + rect(5,10,14,9,P["ear"]) + eyes([8,15],13,True)
                + rect(21,17,5,5,P["cream"]))
    ears_bent=pulse(t,6.16,0.24) or pulse(t,6.8,0.32) or pulse(t,11.52,0.24) or pulse(t,12.0,0.24)
    s=path('M3 15H18V15H21V19H23V27H19V31H4V27H1V19H3Z',P['apricot'])
    if ears_bent:
        s+=path('M3 15V6H0V2H6V4H10V15H13V5H17V2H21V6H18V15Z',P['apricot'])
        s+=rect(5,6,3,8,P['ear'])+rect(15,7,2,7,P['ear'])
    else:
        s+=path('M3 15V2H8V0H10V15H13V3H18V15Z',P['apricot'])
        s+=rect(5,4,3,10,P['ear'])+rect(15,6,2,8,P['ear'])
    s += rect(4,17,15,10,P["ear"]) + eyes([7,14],20,blink(t,1.28,6.0,11.36,14.88))
    s += rect(10,25,3,2,P["cheek"]) + rect(5,30,5,3,P["apricot"]) + rect(16,30,5,3,P["apricot"])
    s += rect(22,25,4,4,P["cream"])
    return s


def owl(t=0, sleeping=False):
    s = path("M3 5V1H7V4H16V1H20V5H23V19H20V24H4V21H1V8H3Z",P["owl"])
    s += rect(4,7,16,12,P["owl_face"]) + eyes([7,15],10,sleeping or blink(t,1.44,6.24,11.68,15.04))
    s += rect(11,14,3,3,P["gold"]) + rect(7,24,4,2,P["staff"]) + rect(15,24,4,2,P["staff"])
    flutter=pulse(t,6.4,1.28) or pulse(t,11.84,0.8)
    wing_pose=int(t/0.16)%3 if flutter and not sleeping else 0
    if wing_pose==1:
        s+=path('M3 11H-2V8H-6V13H-2V19H3Z',P['hat'])+path('M21 11H26V8H30V13H26V19H21Z',P['hat'])
    elif wing_pose==2:
        s+=path('M3 11H-2V7H-6V4H-9V10H-5V16H3Z',P['hat'])+path('M21 11H26V7H30V4H33V10H29V16H21Z',P['hat'])
    else:s+=rect(1,12,3,8,P['hat'])+rect(21,12,3,8,P['hat'])
    return s


def wisp(t=0, sleeping=False):
    s = path("M8 0H13V4H18V8H21V19H18V24H5V22H1V10H4V5H8Z",P["wisp"])
    s += eyes([6,14],12,sleeping or blink(t,1.6,6.56,11.92,15.2))
    s += rect(4,17,3,2,P["cheek"]) + rect(16,17,3,2,P["cheek"])
    return s


def svg_start(h, title):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img"><title>{title}</title><desc>Quiet flat mountain silhouettes and a small pixel wizard with five original companions.</desc>'


def tree(x, y, scale=1):
    return grp(path("M0 0L-21 30H-12L-30 51H-10V66H10V51H30L12 30H21Z",P["tree"]),x,y,scale)


def fireflies(t,footer=False):
    points=[(272,276),(306,292),(706,268),(755,291)] if not footer else [(316,77),(645,67),(683,85)]
    s=''
    for i,(x,y) in enumerate(points):
        x+=round((5 if footer else 8)*wave(t,8,i*1.2))
        y+=round((3 if footer else 5)*wave(t,4,i*0.7))
        c=glow_color(t+i*0.72,'#d8dfac','#728f7a')
        s+=rect(x-2,y-2,7,7,c,'opacity="0.12"')+rect(x,y,3,3,c)
    return s


def hero_text(t):
    title=f'<text x="480" y="70" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="39" font-weight="700" letter-spacing="3">JAEHYEONG KO</text>'
    subtitle=f'<text x="480" y="105" text-anchor="middle" font-family="DejaVu Sans, Arial, sans-serif" font-size="18" letter-spacing="1.5">AI × CODE × PLAY</text>'
    s=f'<g fill="{P["cream"]}">{title}</g><g fill="{P["muted"]}">{subtitle}</g>'
    u=progress(t,12.64,2.56)
    if u is not None:
        x=round(256+448*u)
        s+=f'<defs><clipPath id="letterShine"><rect x="{x}" y="35" width="42" height="77"/></clipPath></defs>'
        s+=f'<g clip-path="url(#letterShine)" fill="#f3d99e">{title}</g>'
        s+=f'<g clip-path="url(#letterShine)" fill="#c7e9d8">{subtitle}</g>'
        if 0.1<u<0.55:s+=sparkle(697,54,5 if u<0.35 else 3,P['gold'])
    return s


def hero_characters(t):
    s=''
    dragon_lift=hop(t,1.84,1.6,6)
    s+=rect(351,306,28,2,'#405247')
    s+=placed(dragon(t),340,267,1.4,29,dy=-dragon_lift)
    s+=placed(cat(t),402,271,1.3,28,sy=1+(0.025 if wave(t,4)>0.6 else 0))
    s+=grp(mage(t),460,224,1.8)
    bunny_lift=hop(t,6.16,0.8,12)+hop(t,11.52,0.64,9)
    squash=0.87 if pulse(t,6.0,0.16) or pulse(t,6.96,0.16) or pulse(t,11.36,0.16) or pulse(t,12.16,0.16) else 1
    s+=rect(557,306,23,2,'#405247')
    s+=placed(bunny(t),551,264,1.3,33,dy=-bunny_lift,sy=squash)
    owl_lift=hop(t,6.48,0.8,4)+hop(t,11.84,0.64,3)
    s+=rect(608,306,20,2,'#405247')
    s+=placed(owl(t),601,273,1.3,26,dy=-owl_lift)
    wdx=round(7*wave(t,8));wdy=round(-8*wave(t,4))
    # Keep a small gap even when the owl's right wing opens and Lumi drifts left.
    s+=grp(wisp(t),650+wdx,251+wdy,1.1)
    # A single little star bubble from the dragon's nose; no fire or beams.
    bubble=progress(t,3.36,1.2)
    if bubble is not None:
        bx=round(384+12*bubble);by=round(280-27*bubble)
        s+=rect(bx-3,by-3,7,7,'none',f'stroke="{P["wing"]}" stroke-width="1"')
        s+=sparkle(bx+0.5,by+0.5,3,P['cream'])
    spell=progress(t,8.64,2.0)
    if spell is not None:
        # Small orbiting squares gather and rise above the raised staff.
        for i in range(4):
            a=2*math.pi*(spell+i/4)
            x=round(525+math.cos(a)*(10+spell*10))
            y=round(244-22*spell+math.sin(a)*7)
            s+=sparkle(x,y,4 if i%2 else 5,P['mint'] if i%2 else P['gold'])
        if 0.3<spell<0.75:s+=sparkle(524,216-round(6*spell),7,P['cream'])
    return s


def hero_svg(t=0):
    t %= LOOP_S
    s=svg_start(HERO_H,"JAEHYEONG KO — AI × Code × Play")
    s+=rect(0,0,W,HERO_H,P["sky"])
    for i,(x,y) in enumerate([(52,54),(117,111),(253,35),(350,26),(708,55),(742,28),(905,62),(874,152),(197,145),(685,127)]):
        level=wave(t,8,i*0.64)
        c=glow_color(t+i*0.8,'#e1e6ed','#8291ab')
        if i in (0,3,4,6,8) and level>0.65:s+=sparkle(x+1,y+1,7 if level>0.9 else 5,c)
        else:s+=rect(x,y,3 if i%3 else 4,3 if i%3 else 4,c)
    comet=progress(t,10.88,1.28)
    if comet is not None:
        cx=round(75+138*comet);cy=round(26+63*comet)
        for j in range(4):s+=rect(cx-j*5,cy-j*2,3 if j else 4,2 if j else 3,blend('#d8e5dc',P['sky'],j/4))
    s+='<circle cx="820" cy="84" r="47" fill="'+P["moon"]+'"/>'
    s+=path("M0 247L118 133L190 215L327 110L443 240L608 156L748 259L876 132L960 220V329H0Z",P["far"])
    s+=path("M0 278L136 229L257 284L401 199L537 282L694 225L826 277L960 213V329H0Z",P["near"])
    s+=tree(42,207,1.3)+tree(98,217,1.05)+tree(882,209,1.25)+tree(939,205,1.35)
    # The camera, mountains and floor stay fixed. Poses move within the scene.
    s+=rect(0,307,960,6,P["grass"])+rect(0,313,960,47,P["ground"])
    s+=hero_text(t)+fireflies(t)+hero_characters(t)
    # Small static grass tufts echo the coarse geometry of the source.
    s+=grp(path("M0 5V0H3V5H7V2H10V8H0Z",P["grass"]),239,302)
    s+=grp(path("M0 5V0H3V5H7V2H10V8H0Z",P["grass"]),731,302)
    return s+'</svg>'


def footer_svg(t=0):
    t%=LOOP_S
    s=svg_start(FOOTER_H,"The workshop rests — five little companions asleep")
    s+=rect(0,0,W,FOOTER_H,P["sky"])
    s+=path("M0 79L101 49L181 76L300 38L418 84L534 52L636 75L766 37L884 77L960 55V112H0Z","#1e303b")
    s+=path("M0 93L123 75L237 94L396 66L534 91L689 74L810 92L960 70V112H0Z","#263e42")
    for i,(x,y) in enumerate([(117,24),(265,17),(738,19),(857,31)]):
        c=glow_color(t+i,'#aebace','#718298')
        s+=sparkle(x,y,4,c) if wave(t,8,i*0.8)>0.8 else rect(x,y,2,2,c)
    s+=rect(0,92,W,3,"#65745c")+rect(0,95,W,17,"#38453a")
    s+=placed(mage(t,True),354,60,1,32,sy=1+0.035*round(wave(t,4)*2)/2)
    s+=placed(dragon(t,True),399,63,1,29,sy=1+0.05*round(wave(t,4,0.4)*2)/2)
    s+=placed(cat(t,True),441,73,1,20,sy=1+0.06*round(wave(t,4,0.8)*2)/2)
    s+=placed(bunny(t,True),482,70,1,22,sy=1+0.045*round(wave(t,4,1.2)*2)/2)
    s+=placed(owl(t,True),523,66,1,26,sy=1+0.04*round(wave(t,4,1.6)*2)/2)
    s+=grp(wisp(t,True),562+round(4*wave(t,8)),58-round(4*wave(t,4)),0.9)
    s+=fireflies(t,True)
    # Warm lantern breathing is visible, but remains lower-key than the header.
    s+=rect(603,69,26,26,glow_color(t,'#ddc78b','#a9956c'),'opacity="0.08"')
    s+=rect(611,73,10,17,P["staff"])+rect(613,76,6,10,glow_color(t,"#e8d49b","#ac9267"))
    s+=path("M612 73V69H620V73H618V71H614V73Z",P["staff"])
    return s+'</svg>'


def pets_svg():
    s='<svg xmlns="http://www.w3.org/2000/svg" width="960" height="300" viewBox="0 0 960 300"><rect width="960" height="300" fill="'+P["sky"]+'"/>'
    labels=[("SPROUT",dragon,"Mint dragon"),("MISO",cat,"Cloud-bellied cat"),("PEACH",bunny,"Apricot rabbit"),("MOMO",owl,"Lavender owlet"),("LUMI",wisp,"Tiny mint wisp")]
    for i,(name,fn,note) in enumerate(labels):
        cx=96+i*192
        s+=grp(fn(),cx-48,76,3.2)
        s+=f'<text x="{cx}" y="211" text-anchor="middle" fill="{P["cream"]}" font-family="DejaVu Sans, Arial, sans-serif" font-size="14" font-weight="700" letter-spacing="2">{name}</text>'
        s+=f'<text x="{cx}" y="236" text-anchor="middle" fill="{P["muted"]}" font-family="DejaVu Sans, Arial, sans-serif" font-size="10">{note}</text>'
    return s+'</svg>'


def pet_motion_svg():
    s='<svg xmlns="http://www.w3.org/2000/svg" width="960" height="760" viewBox="0 0 960 760">'+rect(0,0,960,760,P['sky'])
    s+=f'<text x="40" y="36" fill="{P["cream"]}" font-family="DejaVu Sans" font-size="20" font-weight="700">V2.1 / character motion proof</text>'
    rows=[('Wizard',mage,9.60,'Staff lift, sleeve, robe and spell'),('Sprout',dragon,2.16,'Wing shape and a little lift'),('Miso',cat,5.12,'Curled tail, head and ear reaction'),('Peach',bunny,6.56,'12 px jump and landing squash'),('Momo',owl,6.56,'Wings open after the rabbit'),('Lumi',wisp,1.04,'Figure-eight float: horizontal + vertical')]
    for i,(name,fn,t,note) in enumerate(rows):
        y=58+i*114
        s+=f'<text x="40" y="{y+29}" fill="{P["cream"]}" font-family="DejaVu Sans" font-size="16">{name}</text>'
        s+=f'<text x="40" y="{y+53}" fill="{P["muted"]}" font-family="DejaVu Sans" font-size="11">{note}</text>'
        scale=1.7 if name=='Wizard' else 2.1
        height=46 if name=='Wizard' else 33
        by=y+88-height*scale
        s+=rect(334,y+88,126,2,P['near'])+rect(620,y+88,126,2,P['near'])
        s+=grp(fn(0),370,by,scale)
        dy=0;dx=0
        if name=='Sprout':dy=-hop(t,1.84,1.6,6)*1.5
        elif name=='Peach':dy=-hop(t,6.16,0.8,12)*1.5
        elif name=='Momo':dy=-hop(t,6.48,0.8,4)*1.5
        elif name=='Lumi':dy=-round(8*wave(t,4))*1.5;dx=round(7*wave(t,8))*1.5
        s+=grp(fn(t),656+dx,by+dy,scale)
        s+=f'<text x="384" y="{y+106}" fill="{P["muted"]}" font-family="DejaVu Sans" font-size="11">0.00 s</text>'
        s+=f'<text x="670" y="{y+106}" fill="{P["muted"]}" font-family="DejaVu Sans" font-size="11">{t:.2f} s</text>'
    return s+'</svg>'


def rasterize(svg, cache_dir):
    key=hashlib.sha256(svg.encode()).hexdigest()
    source=cache_dir/(key+'.svg'); target=cache_dir/(key+'.png')
    if not target.exists():
        source.write_text(svg,encoding='utf-8')
        subprocess.run([shutil.which('inkscape') or 'inkscape',str(source),'--export-type=png','--export-filename='+str(target)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return Image.open(target).convert('RGB')


def save_gif(frames, output):
    # A single palette learned from representative states prevents shimmering.
    sample_indices=[0,20,40,60,80,100,120,140,160,170,180,199]
    palette_proof=Image.new("RGB",(W,frames[0].height*len(sample_indices)))
    for i,idx in enumerate(sample_indices):
        palette_proof.paste(frames[min(idx,len(frames)-1)],(0,i*frames[0].height))
    palette=palette_proof.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(output,save_all=True,append_images=indexed[1:],duration=FRAME_MS,loop=0,optimize=True,disposal=1)


def pixel_changes(a,b):
    delta=ImageChops.difference(a.convert('RGB'),b.convert('RGB'))
    r,g,b=delta.split();mask=ImageChops.lighter(ImageChops.lighter(r,g),b)
    return sum(mask.histogram()[1:])


def gif_metrics(f):
    im=Image.open(f);frames=[];durations=[]
    for i in range(im.n_frames):
        im.seek(i);frames.append(im.convert('RGB'));durations.append(im.info.get('duration',0))
    diffs=[pixel_changes(frames[i-1],frames[i]) for i in range(1,len(frames))]
    boundary=pixel_changes(frames[-1],frames[0])
    return {'width':im.width,'height':im.height,'frames':im.n_frames,'duration_ms':sum(durations),
        'frame_duration_min_ms':min(durations),'frame_duration_max_ms':max(durations),
        'first_last_equal':boundary==0,'boundary_changed_pixels':boundary,
        'max_adjacent_changed_pixels':max(diffs,default=0),
        'mean_adjacent_changed_pixels':round(sum(diffs)/len(diffs),2) if diffs else 0,
        'boundary_within_adjacent_max':boundary<=max(diffs,default=0)}


def main(poster_only=False):
    OUT.mkdir(parents=True,exist_ok=True); PREVIEW.mkdir(parents=True,exist_ok=True)
    (OUT/'header.svg').write_text(hero_svg(),encoding='utf-8')
    (OUT/'footer.svg').write_text(footer_svg(),encoding='utf-8')
    (PREVIEW/'companions.svg').write_text(pets_svg(),encoding='utf-8')
    (PREVIEW/'pet-motion-proof.svg').write_text(pet_motion_svg(),encoding='utf-8')
    source_dir=ROOT/'assets'/'source'; source_dir.mkdir(exist_ok=True)
    pet_dir=source_dir/'pets';pet_dir.mkdir(exist_ok=True)
    for name,fn in [('sprout',dragon),('miso',cat),('peach',bunny),('momo',owl),('lumi',wisp)]:
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 48 48"><title>'+name+'</title>'+grp(fn(),9,8,1)+'</svg>'
        (pet_dir/(name+'.svg')).write_text(svg,encoding='utf-8')
        subprocess.run([shutil.which('inkscape') or 'inkscape',str(pet_dir/(name+'.svg')),'--export-type=png','--export-filename='+str(pet_dir/(name+'.png'))],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    (source_dir/'palette.json').write_text(json.dumps(P,indent=2),encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='koeje-svg-') as d:
        cache_dir=Path(d)
        poster=rasterize(hero_svg(),cache_dir); poster.save(OUT/'header.png')
        foot=rasterize(footer_svg(),cache_dir); foot.save(OUT/'footer.png')
        pets=rasterize(pets_svg(),cache_dir); pets.save(PREVIEW/'companions.png')
        pet_motion=rasterize(pet_motion_svg(),cache_dir);pet_motion.save(PREVIEW/'pet-motion-proof.png')
        if poster_only:
            print('Posters rendered.'); return
        hero_sources=[hero_svg(i*FRAME_MS/1000) for i in range(LOOP_MS//FRAME_MS)]
        footer_sources=[footer_svg(i*FRAME_MS/1000) for i in range(LOOP_MS//FRAME_MS)]
        unique_sources=list(dict.fromkeys(hero_sources+footer_sources))
        with ThreadPoolExecutor(max_workers=3) as pool:
            rendered=dict(zip(unique_sources,pool.map(lambda s:rasterize(s,cache_dir),unique_sources)))
        hero_frames=[rendered[s] for s in hero_sources]
        footer_frames=[rendered[s] for s in footer_sources]
    save_gif(hero_frames,OUT/'header.gif');save_gif(footer_frames,OUT/'footer.gif')
    # A proof image, not an embedded README decoration.
    board=Image.new('RGB',(960,360*4+28*4),P['sky'])
    draw=ImageDraw.Draw(board)
    for i,idx in enumerate([0,50,100,150]):
        y=i*388; draw.text((20,y+7),f'{idx*FRAME_MS/1000:.1f} s | V2.1 living loop proof',fill=P['cream'])
        board.paste(hero_frames[idx],(0,y+28))
    board.save(PREVIEW/'motion-contact-sheet.png')
    event_board=Image.new('RGB',(960,360*4+28*4),P['sky'])
    event_draw=ImageDraw.Draw(event_board)
    for i,(idx,label) in enumerate([(27,'Dragon wing flap'),(82,'Rabbit hop + owl reaction'),(120,'Wizard spell'),(170,'Letter highlight')]):
        y=i*388;event_draw.text((20,y+7),f'{idx*FRAME_MS/1000:.2f} s | {label}',fill=P['cream'])
        event_board.paste(hero_frames[idx],(0,y+28))
    event_board.save(PREVIEW/'scene-events-contact-sheet.png')
    report={"version":"2.1","source":"code-native SVG geometry; original screenshot unmodified", "loop_ms":LOOP_MS,"frame_ms":FRAME_MS,"sample_fps":FPS,
      "seam_equal_svg":hero_svg(0)==hero_svg(LOOP_S),"footer_seam_equal_svg":footer_svg(0)==footer_svg(LOOP_S),"font":"DejaVu Sans",
      "title_strings":["JAEHYEONG KO","AI × CODE × PLAY"],"title_positions_fixed":True,"title_color_highlight":True,
      "loop_strategy":"periodic functions; no forced reset or duplicate final frame",
      "available_exports":["header.gif","footer.gif","header.png","footer.png"],"default_readme_images":["header.gif","footer.gif"],"files":{}}
    for f in sorted(OUT.iterdir()):
        if f.suffix not in ['.gif','.png','.svg']:continue
        item={"bytes":f.stat().st_size,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()}
        if f.suffix in ['.png','.gif']:
            im=Image.open(f);item.update(width=im.width,height=im.height,frames=getattr(im,'n_frames',1))
            if f.suffix=='.gif':
                item.update(gif_metrics(f))
                assert item['duration_ms']==LOOP_MS
                assert item['boundary_within_adjacent_max']
        report['files'][f.name]=item
    assert report['seam_equal_svg'] and report['footer_seam_equal_svg']
    assert (OUT/'header.gif').stat().st_size<1.5*1024*1024
    assert (OUT/'footer.gif').stat().st_size<350*1024
    (PREVIEW/'render-report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--poster-only',action='store_true')
    main(parser.parse_args().poster_only)
