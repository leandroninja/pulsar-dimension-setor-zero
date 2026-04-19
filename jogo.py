# -*- coding: utf-8 -*-
import pygame, math, random, array, sys, json, os

# ── Áudio ──────────────────────────────────────────────────────────────────────
SR = 44100

def _sq(f, t):  return 1.0 if (f * t) % 1 < 0.5 else -1.0
def _saw(f, t): return 2.0 * ((f * t) % 1) - 1.0

def _mk(samples):
    buf = array.array('h', [0] * (len(samples) * 2))
    for i, v in enumerate(samples):
        buf[2*i] = buf[2*i+1] = max(-32767, min(32767, int(v)))
    return pygame.mixer.Sound(buffer=buf)

def _snd_shoot():
    n = int(SR*0.07)
    return _mk([32767*0.2*(1-i/n)**2*_sq(900*math.exp(-12*i/SR),i/SR) for i in range(n)])

def _snd_hit():
    n = int(SR*0.05)
    return _mk([32767*0.25*(1-i/n)**1.5*random.uniform(-1,1) for i in range(n)])

def _snd_explosion():
    n = int(SR*0.4)
    return _mk([32767*0.42*math.exp(-4*i/SR)*(random.uniform(-1,1)*0.6+_saw(80*math.exp(-2*i/SR),i/SR)*0.4) for i in range(n)])

def _snd_powerup():
    s=[]
    for freq in [523,659,784,1047]:
        seg=int(SR*0.1)
        for j in range(seg):
            t=j/SR; s.append(32767*0.35*math.exp(-5*t/0.1)*math.sin(2*math.pi*freq*t))
    return _mk(s)

def _snd_bomb():
    n=int(SR*1.3)
    return _mk([32767*0.55*math.exp(-1.8*i/SR)*(1-math.exp(-20*i/SR))*(random.uniform(-1,1)*0.5+_saw(50*math.exp(-i/SR),i/SR)*0.5) for i in range(n)])

def _snd_player_dmg():
    n=int(SR*0.18)
    return _mk([32767*0.38*math.exp(-8*i/SR)*(_sq(180*math.exp(-4*i/SR),i/SR)*0.6+random.uniform(-0.4,0.4)) for i in range(n)])

def _snd_boss_alert():
    s=[]
    for freq in [880,660,440]:
        for j in range(int(SR*0.22)):
            t=j/SR; s.append(32767*0.3*math.exp(-3*t/0.22)*_sq(freq,t))
    return _mk(s)

def _snd_boss_death():
    n=int(SR*0.9)
    return _mk([32767*0.55*math.exp(-2*i/SR)*(random.uniform(-1,1)*0.6+_saw(60*math.exp(-1.5*i/SR),i/SR)*0.4) for i in range(n)])

def _snd_music():
    vol=0.14; bpm=145; beat=60/bpm; h=beat/2; q=beat/4
    mel=[
        (440,q),(0,q),(494,q),(523,h),(494,q),(440,q),(0,h),
        (392,q),(440,q),(494,h),(392,q),(330,beat),(0,beat),
        (523,q),(0,q),(587,q),(659,h),(587,q),(523,q),(0,h),
        (494,q),(523,q),(587,h),(494,q),(440,beat),(0,beat),
    ]
    bass=[110,110,131,131,110,110,98,98]*4
    total=max(sum(d for _,d in mel),h*len(bass))
    n=int(total*SR)
    buf=array.array('h',[0]*(n*2))
    pos=0
    for freq,dur in mel:
        samp=int(dur*SR)
        for i in range(samp):
            if freq>0 and pos+i<n:
                t=i/SR; env=math.exp(-2*t/dur)
                v=int(32767*vol*0.65*env*_sq(freq,t))
                buf[2*(pos+i)]  =max(-32767,min(32767,buf[2*(pos+i)]  +v))
                buf[2*(pos+i)+1]=max(-32767,min(32767,buf[2*(pos+i)+1]+v))
        pos+=samp
    pos=0
    for freq in bass:
        samp=int(h*SR)
        for i in range(samp):
            if pos+i<n:
                t=i/SR; env=0.5+0.5*math.exp(-6*t/h)
                v=int(32767*vol*0.5*env*_sq(freq//2,t))
                buf[2*(pos+i)]  =max(-32767,min(32767,buf[2*(pos+i)]  +v))
                buf[2*(pos+i)+1]=max(-32767,min(32767,buf[2*(pos+i)+1]+v))
        pos+=samp
    return pygame.mixer.Sound(buffer=buf)


# ── Init ───────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=512)

W, H  = 800, 600
FPS   = 60
SCORE_FILE = "highscore.json"
MAX_CONTINUES = 5

PHASES = [
    {"name":"SETOR VERDE",    "star":(0,160,0),    "ec":(0,255,65),   "bc":(0,200,80),   "ui":(0,255,65),   "bg":(0,8,0),    "be":(0,255,80),   "bp":(150,255,80)},
    {"name":"SETOR CIANO",    "star":(0,130,200),  "ec":(0,200,255),  "bc":(0,160,220),  "ui":(0,200,255),  "bg":(0,4,12),   "be":(0,200,255),  "bp":(80,220,255)},
    {"name":"SETOR ÂMBAR",    "star":(190,130,0),  "ec":(255,175,0),  "bc":(220,110,0),  "ui":(255,175,0),  "bg":(8,5,0),    "be":(255,155,0),  "bp":(255,220,60)},
    {"name":"SETOR VIOLETA",  "star":(120,0,180),  "ec":(200,0,255),  "bc":(160,0,220),  "ui":(200,0,255),  "bg":(6,0,12),   "be":(200,0,255),  "bp":(230,100,255)},
    {"name":"SETOR VERMELHO", "star":(200,30,30),  "ec":(255,80,80),  "bc":(220,20,20),  "ui":(255,80,80),  "bg":(10,0,0),   "be":(255,60,60),  "bp":(255,180,60)},
    {"name":"SETOR BRANCO",   "star":(160,160,200),"ec":(210,210,255),"bc":(170,170,230),"ui":(220,220,255),"bg":(4,4,10),   "be":(200,200,255),"bp":(255,255,180)},
    {"name":"SETOR ROSA",     "star":(190,0,130),  "ec":(255,70,190), "bc":(200,0,150),  "ui":(255,80,200), "bg":(8,0,6),    "be":(255,60,180), "bp":(255,180,255)},
    {"name":"SETOR LARANJA",  "star":(200,100,0),  "ec":(255,145,0),  "bc":(220,90,0),   "ui":(255,145,0),  "bg":(8,4,0),    "be":(255,120,0),  "bp":(255,230,0)},
    {"name":"SETOR DOURADO",  "star":(200,180,0),  "ec":(255,225,0),  "bc":(220,180,0),  "ui":(255,225,0),  "bg":(6,6,0),    "be":(255,205,0),  "bp":(255,255,130)},
    {"name":"SETOR FINAL",    "star":(0,200,255),  "ec":(0,255,220),  "bc":(0,210,210),  "ui":(0,255,255),  "bg":(0,4,8),    "be":(0,220,255),  "bp":(180,255,255)},
]

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("NAVE RETRÔ")
clock  = pygame.time.Clock()

_font_lg = pygame.font.SysFont("Courier New", 36, bold=True)
_font_md = pygame.font.SysFont("Courier New", 22, bold=True)
_font_sm = pygame.font.SysFont("Courier New", 16, bold=True)

_scanline = pygame.Surface((W, H), pygame.SRCALPHA)
for _y in range(0, H, 2):
    pygame.draw.line(_scanline, (0,0,0,55), (0,_y), (W,_y))


# ── Utilitários ────────────────────────────────────────────────────────────────
def load_hs():
    try:
        with open(SCORE_FILE) as f: return json.load(f).get("hs", 0)
    except: return 0

def save_hs(score):
    if score > load_hs():
        with open(SCORE_FILE,"w") as f: json.dump({"hs":score},f)

def dim(col, f):
    return tuple(max(0,min(255,int(c*f))) for c in col)

def glow_text(surf, text, font, col, x, y, center=False):
    gc = dim(col, 0.25)
    for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:
        img = font.render(text, True, gc)
        rx = x-img.get_width()//2+dx if center else x+dx
        surf.blit(img, (rx, y+dy))
    img = font.render(text, True, col)
    rx = x-img.get_width()//2 if center else x
    surf.blit(img, (rx, y))

def spawn_particles(particles, x, y, col, n=16, spd=3.5):
    for _ in range(n):
        a = random.uniform(0,2*math.pi); s = random.uniform(0.5,spd)
        life = random.uniform(0.35,0.85)
        particles.append([float(x),float(y),math.cos(a)*s,math.sin(a)*s,life,life,col])


# ── Estrelas ───────────────────────────────────────────────────────────────────
def make_stars():
    stars=[]
    for _ in range(80): stars.append([random.uniform(0,W),random.uniform(0,H),0.55,1,0])
    for _ in range(50): stars.append([random.uniform(0,W),random.uniform(0,H),1.5, 1,1])
    for _ in range(25): stars.append([random.uniform(0,W),random.uniform(0,H),3.2, 2,2])
    return stars

def update_stars(stars):
    for s in stars:
        s[1]+=s[2]
        if s[1]>H: s[1]=random.uniform(-8,0); s[0]=random.uniform(0,W)

def draw_stars(surf, stars, col):
    for s in stars:
        af=[0.22,0.5,1.0][int(s[4])]; c=dim(col,af)
        sx,sy=int(s[0]),int(s[1])
        if s[3]<=1:
            if 0<=sx<W and 0<=sy<H: surf.set_at((sx,sy),c)
        else:
            pygame.draw.circle(surf,c,(sx,sy),int(s[3]))
        if s[2]>=3.0 and 0<=sx<W and sy-4>=0:
            surf.set_at((sx,sy-4),dim(c,0.3))


# ── Desenho do jogador ─────────────────────────────────────────────────────────
def draw_player(surf, cx, cy, col, inv=0):
    if inv>0 and (inv//6)%2==0: return
    pts=[(cx,cy-16),(cx-14,cy+9),(cx-7,cy+3),(cx,cy+11),(cx+7,cy+3),(cx+14,cy+9)]
    pygame.draw.polygon(surf,dim(col,0.35),pts)
    pygame.draw.polygon(surf,col,pts,1)
    pygame.draw.circle(surf,col,(cx,cy-4),4)
    pygame.draw.circle(surf,dim(col,0.25),(cx,cy-4),3)
    gc=col if (pygame.time.get_ticks()//80)%2 else dim(col,0.5)
    pygame.draw.circle(surf,gc,(cx,cy+11),3)
    pygame.draw.circle(surf,dim(col,0.2),(cx,cy+11),5)


# ── Desenho de 10 tipos de inimigos ───────────────────────────────────────────
def draw_enemy(surf, cx, cy, col, etype, flash=0):
    c  = (220,220,220) if flash>0 else col
    cf = dim(c,0.35)
    cx, cy = int(cx), int(cy)

    if etype == 0:   # Padrão — triângulo com asas
        pts=[(cx,cy+13),(cx-12,cy-7),(cx-6,cy+1),(cx,cy-9),(cx+6,cy+1),(cx+12,cy-7)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.circle(surf,c,(cx,cy+3),3)
    elif etype == 1: # Rápido — diamante
        pts=[(cx,cy-11),(cx+8,cy),(cx,cy+11),(cx-8,cy)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
    elif etype == 2: # Pesado — hexágono
        pts=[(cx,cy+17),(cx-17,cy+8),(cx-22,cy-5),(cx-10,cy-16),(cx+10,cy-16),(cx+22,cy-5),(cx+17,cy+8)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.circle(surf,c,(cx,cy),5)
    elif etype == 3: # Zigue-zague — seta com barbatanas
        pts=[(cx,cy-12),(cx+14,cy+6),(cx+6,cy+2),(cx,cy+12),(cx-6,cy+2),(cx-14,cy+6)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.line(surf,c,(cx-14,cy+6),(cx-18,cy-2),1)
        pygame.draw.line(surf,c,(cx+14,cy+6),(cx+18,cy-2),1)
    elif etype == 4: # Bombardeiro — retângulo largo
        pygame.draw.rect(surf,cf,(cx-18,cy-8,36,18))
        pygame.draw.rect(surf,c,(cx-18,cy-8,36,18),1)
        pygame.draw.rect(surf,c,(cx-6,cy+9,12,6),1)
        pygame.draw.circle(surf,c,(cx-12,cy),4,1)
        pygame.draw.circle(surf,c,(cx+12,cy),4,1)
    elif etype == 5: # Varredor — crescente (meia-lua)
        pts=[(cx-20,cy-4),(cx-12,cy-12),(cx,cy-14),(cx+12,cy-12),(cx+20,cy-4),
             (cx+14,cy+8),(cx,cy+4),(cx-14,cy+8)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
    elif etype == 6: # Kamikaze — triângulo agressivo
        pts=[(cx,cy+15),(cx-16,cy-12),(cx,cy-6),(cx+16,cy-12)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.line(surf,c,(cx-16,cy-12),(cx-22,cy-4),1)
        pygame.draw.line(surf,c,(cx+16,cy-12),(cx+22,cy-4),1)
    elif etype == 7: # Torre — retângulo com canhões
        pygame.draw.rect(surf,cf,(cx-14,cy-10,28,22))
        pygame.draw.rect(surf,c,(cx-14,cy-10,28,22),1)
        pygame.draw.rect(surf,c,(cx-2,cy+12,4,8))
        pygame.draw.rect(surf,c,(cx-10,cy+10,6,6),1)
        pygame.draw.rect(surf,c,(cx+4,cy+10,6,6),1)
    elif etype == 8: # Elite — duplo diamante / gravata
        pts=[(cx-20,cy),(cx-6,cy-10),(cx,cy),(cx-6,cy+10)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pts=[(cx+20,cy),(cx+6,cy-10),(cx,cy),(cx+6,cy+10)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.circle(surf,c,(cx,cy),4)
    else:            # Destruidor — mini-cruzador
        pts=[(cx,cy+20),(cx-22,cy+10),(cx-26,cy-2),(cx-14,cy-18),(cx+14,cy-18),(cx+26,cy-2),(cx+22,cy+10)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.circle(surf,c,(cx,cy-4),6)
        for dx in [-14,14]:
            pygame.draw.circle(surf,c,(cx+dx,cy+4),3,1)


# ── Desenho de 10 bosses únicos ────────────────────────────────────────────────
def draw_boss(surf, cx, cy, col, hp, btype, flash=0):
    c  = (220,220,220) if flash>0 else col
    cf = dim(c,0.28)
    cx, cy = int(cx), int(cy)
    maxhp = 300 + btype * 50

    if btype == 0:   # Asa-delta — cruzador largo
        pts=[(cx,cy+26),(cx-30,cy+14),(cx-60,cy+2),(cx-42,cy-18),(cx-20,cy-24),(cx,cy-16),(cx+20,cy-24),(cx+42,cy-18),(cx+60,cy+2),(cx+30,cy+14)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,2)
        pygame.draw.circle(surf,c,(cx,cy-2),10); pygame.draw.circle(surf,cf,(cx,cy-2),8)
        for dx in [-30,30]: pygame.draw.circle(surf,c,(cx+dx,cy+8),5,1)

    elif btype == 1: # Caranguejo — corpo + garras
        pygame.draw.ellipse(surf,cf,(cx-44,cy-22,88,44))
        pygame.draw.ellipse(surf,c,(cx-44,cy-22,88,44),2)
        for sx,ex1,ey1,ex2,ey2 in [(-44,-68,cy-8,-72,cy+10),( 44, 68,cy-8, 72,cy+10)]:
            pygame.draw.line(surf,c,(cx+sx,cy),(cx+ex1,ey1),2)
            pygame.draw.line(surf,c,(cx+ex1,ey1),(cx+ex2,ey2),2)
            pygame.draw.circle(surf,c,(cx+ex2,ey2),5)
        pygame.draw.circle(surf,c,(cx,cy),8); pygame.draw.circle(surf,cf,(cx,cy),6)

    elif btype == 2: # Canhoneira — oval + pods
        pygame.draw.ellipse(surf,cf,(cx-38,cy-20,76,40))
        pygame.draw.ellipse(surf,c,(cx-38,cy-20,76,40),2)
        for dx in [-40,40]:
            pygame.draw.ellipse(surf,cf,(cx+dx-12,cy-8,24,20))
            pygame.draw.ellipse(surf,c,(cx+dx-12,cy-8,24,20),1)
            pygame.draw.rect(surf,c,(cx+dx-3,cy+12,6,10))
        pygame.draw.circle(surf,c,(cx,cy),7); pygame.draw.circle(surf,cf,(cx,cy),5)

    elif btype == 3: # Dreadnought — fortaleza retangular
        pygame.draw.rect(surf,cf,(cx-56,cy-26,112,52))
        pygame.draw.rect(surf,c,(cx-56,cy-26,112,52),2)
        for dx in [-40,-20,0,20,40]:
            pygame.draw.rect(surf,c,(cx+dx-4,cy+26,8,10))
        for dx in [-32,0,32]:
            pygame.draw.rect(surf,c,(cx+dx-6,cy-36,12,12))
        pygame.draw.circle(surf,c,(cx,cy),10); pygame.draw.circle(surf,cf,(cx,cy),8)

    elif btype == 4: # Fantasma — diamante rotacionado
        pts=[(cx,cy-46),(cx+28,cy),(cx,cy+46),(cx-28,cy)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,2)
        for dx,dy in [(-14,-12),(14,-12),(0,16)]:
            pygame.draw.circle(surf,c,(cx+dx,cy+dy),5,1)
        pygame.draw.circle(surf,c,(cx,cy),8); pygame.draw.circle(surf,cf,(cx,cy),6)

    elif btype == 5: # Cristal — hexágono espinhoso
        r=38
        for i in range(6):
            a=math.pi/3*i-math.pi/2
            x1,y1=cx+int(r*math.cos(a)),cy+int(r*math.sin(a))
            x2,y2=cx+int((r+14)*math.cos(a+math.pi/6)),cy+int((r+14)*math.sin(a+math.pi/6))
            pygame.draw.line(surf,c,(cx,cy),(x2,y2),1)
            pygame.draw.circle(surf,c,(x1,y1),4,1)
        pts=[( cx+int(r*math.cos(math.pi/3*i-math.pi/2)), cy+int(r*math.sin(math.pi/3*i-math.pi/2)) ) for i in range(6)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,2)
        pygame.draw.circle(surf,c,(cx,cy),9); pygame.draw.circle(surf,cf,(cx,cy),7)

    elif btype == 6: # Nave-mãe — disco enorme
        pygame.draw.ellipse(surf,cf,(cx-64,cy-18,128,36))
        pygame.draw.ellipse(surf,c,(cx-64,cy-18,128,36),2)
        pygame.draw.ellipse(surf,cf,(cx-28,cy-30,56,28))
        pygame.draw.ellipse(surf,c,(cx-28,cy-30,56,28),1)
        for dx in range(-56,64,20):
            pygame.draw.circle(surf,c,(cx+dx,cy+10),4,1)
        pygame.draw.circle(surf,c,(cx,cy-16),7)

    elif btype == 7: # Tempestade de Fogo — nave angular agressiva
        pts=[(cx,cy-44),(cx+22,cy-8),(cx+50,cy+8),(cx+28,cy+28),(cx,cy+16),(cx-28,cy+28),(cx-50,cy+8),(cx-22,cy-8)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,2)
        pygame.draw.line(surf,c,(cx,cy-44),(cx,cy+16),1)
        for dx in [-20,20]: pygame.draw.circle(surf,c,(cx+dx,cy+10),4,1)
        pygame.draw.circle(surf,c,(cx,cy-14),8); pygame.draw.circle(surf,cf,(cx,cy-14),6)

    elif btype == 8: # Titã — encouraçado massivo
        pygame.draw.rect(surf,cf,(cx-62,cy-32,124,64))
        pygame.draw.rect(surf,c,(cx-62,cy-32,124,64),2)
        pygame.draw.rect(surf,cf,(cx-42,cy-46,84,18))
        pygame.draw.rect(surf,c,(cx-42,cy-46,84,18),1)
        for dx in [-46,-22,0,22,46]:
            pygame.draw.rect(surf,c,(cx+dx-4,cy+30,8,14))
        for dx in [-34,0,34]:
            pygame.draw.circle(surf,c,(cx+dx,cy),6,1)
        pygame.draw.circle(surf,c,(cx,cy),11); pygame.draw.circle(surf,cf,(cx,cy),9)

    else:            # Soberano Final — complexo, múltiplas partes
        pts=[(cx,cy-48),(cx+24,cy-20),(cx+56,cy),(cx+32,cy+24),(cx+16,cy+40),(cx,cy+28),(cx-16,cy+40),(cx-32,cy+24),(cx-56,cy),(cx-24,cy-20)]
        pygame.draw.polygon(surf,cf,pts); pygame.draw.polygon(surf,c,pts,2)
        for dx in [-28,28]: pygame.draw.circle(surf,c,(cx+dx,cy-8),8,1)
        for dx in [-44,44]: pygame.draw.circle(surf,c,(cx+dx,cy+8),5,1)
        pygame.draw.circle(surf,c,(cx,cy),13); pygame.draw.circle(surf,cf,(cx,cy),10)
        pygame.draw.circle(surf,dim(c,0.8),(cx,cy),5)

    # Barra de HP universal
    bar_w=200; bar_x=cx-100; bar_y=cy-(52 if btype in(8,9) else 42)
    pygame.draw.rect(surf,dim(c,0.22),(bar_x,bar_y,bar_w,7))
    fill=max(0,int(bar_w*hp/maxhp))
    bar_col=(220,50,50) if flash==0 and hp<maxhp*0.3 else c
    pygame.draw.rect(surf,bar_col,(bar_x,bar_y,fill,7))
    pygame.draw.rect(surf,c,(bar_x,bar_y,bar_w,7),1)


# ── Asteroides e projéteis ────────────────────────────────────────────────────
def draw_asteroid(surf, cx, cy, radius, col, seed):
    rng = random.Random(seed)
    pts = []
    for i in range(9):
        a = 2*math.pi*i/9 + rng.uniform(-0.25, 0.25)
        r = radius * rng.uniform(0.65, 1.0)
        pts.append((int(cx + r*math.cos(a)), int(cy + r*math.sin(a))))
    pygame.draw.polygon(surf, dim(col, 0.22), pts)
    pygame.draw.polygon(surf, dim(col, 0.65), pts, 1)

def draw_bullet_player(surf, bx, by, col):
    pygame.draw.rect(surf,col,(int(bx)-2,int(by)-6,4,12))
    pygame.draw.rect(surf,dim(col,0.4),(int(bx)-1,int(by)-9,2,4))

def draw_bullet_enemy(surf, bx, by, col):
    pygame.draw.circle(surf,col,(int(bx),int(by)),4)
    pygame.draw.circle(surf,dim(col,0.4),(int(bx),int(by)),6,1)

def draw_powerup(surf, cx, cy, ptype, col, bp_col):
    cx,cy=int(cx),int(cy)
    if ptype==0:
        c=col; pts=[(cx,cy-10),(cx+10,cy),(cx,cy+10),(cx-10,cy)]
        pygame.draw.polygon(surf,dim(c,0.28),pts); pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.line(surf,c,(cx,cy-5),(cx,cy+5),1)
        pygame.draw.line(surf,c,(cx-5,cy),(cx+5,cy),1)
    else:
        c=bp_col
        pygame.draw.circle(surf,dim(c,0.28),(cx,cy),10)
        pygame.draw.circle(surf,c,(cx,cy),10,1)
        pygame.draw.circle(surf,c,(cx,cy),4)


# ── Classe principal ───────────────────────────────────────────────────────────
class Game:
    MENU            = 0
    PLAYING         = 1
    BOSS_WARN       = 2
    PHASE_CLEAR     = 3
    CONTINUE_PROMPT = 4
    GAME_OVER       = 5
    VICTORY         = 6

    def __init__(self):
        self.highscore = load_hs()
        self.sfx = {}; self.music = None
        self._load_audio()
        self.state = self.MENU
        self._init_game()

    def _load_audio(self):
        try:
            self.sfx = {
                'shoot':      _snd_shoot(),
                'hit':        _snd_hit(),
                'explosion':  _snd_explosion(),
                'powerup':    _snd_powerup(),
                'bomb':       _snd_bomb(),
                'player_dmg': _snd_player_dmg(),
                'boss_alert': _snd_boss_alert(),
                'boss_death': _snd_boss_death(),
            }
            self.music = _snd_music(); self.music.play(-1)
        except Exception as e: print(f"Audio: {e}")

    def _play(self, name):
        s = self.sfx.get(name)
        if s: s.play()

    def _init_game(self):
        self.phase_idx     = 0
        self.score         = 0
        self.lives         = 10
        self.continues_left = MAX_CONTINUES
        self.weapon_lvl    = 1
        self.bombs         = 3
        self._start_phase()

    def _start_phase(self, keep_player=False):
        pal = PHASES[min(self.phase_idx, len(PHASES)-1)]
        self.pal        = pal
        self.stars      = make_stars()
        if not keep_player:
            self.px = float(W//2); self.py = float(H-100)
            self.weapon_lvl = 1; self.bombs = 3
        else:
            self.px = float(W//2); self.py = float(H-100)
        self.inv        = 0
        self.shoot_cd   = 0
        self.p_bullets  = []; self.e_bullets = []
        self.enemies    = []; self.asteroids = []
        self.powerups   = []; self.particles = []
        self.boss       = None
        self.boss_vx    = 1.6 + self.phase_idx * 0.12
        self.bomb_flash = 0
        self.kills      = 0
        self.target_kills = 40 + self.phase_idx * 8
        self.spawn_cd   = 80
        self.spawned    = 0
        self.state_timer = 0
        self.pspd       = 1.0 + self.phase_idx * 0.15

    # ── Loop principal ────────────────────────────────────────────────────────
    def run(self):
        while True:
            clock.tick(FPS)
            self._events()
            self._update()
            self._draw()

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                save_hs(self.score); pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:
                    save_hs(self.score); pygame.quit(); sys.exit()
                if self.state == self.MENU and k == pygame.K_RETURN:
                    self.state = self.PLAYING
                if self.state == self.GAME_OVER and k == pygame.K_RETURN:
                    self._init_game(); self.state = self.PLAYING
                if self.state == self.VICTORY and k == pygame.K_RETURN:
                    self._init_game(); self.state = self.MENU
                if self.state == self.CONTINUE_PROMPT:
                    if k in (pygame.K_s, pygame.K_RETURN, pygame.K_y):
                        self.lives = 10
                        self._start_phase(keep_player=True)
                        self.state = self.PLAYING
                    elif k in (pygame.K_n, pygame.K_r):
                        self._init_game(); self.state = self.PLAYING
                if self.state == self.PLAYING and k in (pygame.K_b, pygame.K_x):
                    self._use_bomb()

    def _update(self):
        if self.state == self.BOSS_WARN:
            self.state_timer -= 1
            update_stars(self.stars)
            if self.state_timer <= 0:
                self._spawn_boss(); self.state = self.PLAYING
            return

        if self.state == self.PHASE_CLEAR:
            self.state_timer -= 1
            update_stars(self.stars)
            if self.state_timer <= 0:
                self.phase_idx += 1
                if self.phase_idx >= 10:
                    save_hs(self.score); self.state = self.VICTORY
                else:
                    self._start_phase(keep_player=True); self.state = self.PLAYING
            return

        if self.state == self.CONTINUE_PROMPT:
            update_stars(self.stars)
            self.continue_countdown -= 1
            if self.continue_countdown <= 0:
                self.state = self.MENU
            return

        if self.state != self.PLAYING:
            return

        keys = pygame.key.get_pressed()
        spd = 5.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: self.px -= spd
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: self.px += spd
        if keys[pygame.K_UP]    or keys[pygame.K_w]: self.py -= spd
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: self.py += spd
        self.px = max(16,min(W-16,self.px))
        self.py = max(20,min(H-20,self.py))

        if self.shoot_cd > 0: self.shoot_cd -= 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_z]) and self.shoot_cd <= 0:
            self._player_shoot()
            self.shoot_cd = max(5, 12 - self.weapon_lvl*2)

        if self.inv > 0: self.inv -= 1
        update_stars(self.stars)

        new_pb=[]
        for b in self.p_bullets:
            b[0]+=b[2]; b[1]+=b[3]
            if -10<b[1]<H+10 and -10<b[0]<W+10: new_pb.append(b)
        self.p_bullets=new_pb

        new_eb=[]
        for b in self.e_bullets:
            b[0]+=b[2]; b[1]+=b[3]
            if -20<b[0]<W+20 and -20<b[1]<H+20: new_eb.append(b)
        self.e_bullets=new_eb

        if self.boss is None:
            self._do_spawn()
            for e in self.enemies: self._update_enemy(e)
            self.enemies   = [e for e in self.enemies   if e['alive']]
            for a in self.asteroids: self._update_asteroid(a)
            self.asteroids = [a for a in self.asteroids if a['alive']]
            if (self.spawned >= self.target_kills
                    and not self.enemies and not self.asteroids
                    and self.state == self.PLAYING):
                self._play('boss_alert')
                self.state = self.BOSS_WARN
                self.state_timer = FPS*3
        else:
            self._update_boss()

        new_pu=[]
        for p in self.powerups:
            p[1]+=1.6
            if p[1]<H+20: new_pu.append(p)
        self.powerups=new_pu

        for p in self.particles:
            p[0]+=p[2]; p[1]+=p[3]; p[4]-=1/FPS
        self.particles=[p for p in self.particles if p[4]>0]

        if self.bomb_flash>0: self.bomb_flash-=1
        self._collisions()

        if self.boss and self.boss['hp']<=0:
            spawn_particles(self.particles,self.boss['x'],self.boss['y'],self.pal['bc'],n=50,spd=7)
            self._play('boss_death')
            self.score += 500 + self.phase_idx*150
            self.boss = None
            self.state = self.PHASE_CLEAR
            self.state_timer = FPS*3

    # ── Lógica ────────────────────────────────────────────────────────────────
    def _player_shoot(self):
        col=self.pal['bp']; bspd=10.0
        angles={1:[0],2:[-8,8],3:[-18,0,18],4:[-22,-7,7,22],5:[-28,-14,0,14,28]}
        for deg in angles.get(self.weapon_lvl,[0]):
            ang=math.radians(deg)
            self.p_bullets.append([self.px,self.py-16,bspd*math.sin(ang),-bspd*math.cos(ang),col,1])
        self._play('shoot')

    def _use_bomb(self):
        if self.bombs<=0: return
        self.bombs-=1; self.bomb_flash=50; self._play('bomb')
        for e in self.enemies:   e['hp']=0
        for a in self.asteroids: a['hp']=0
        if self.boss: self.boss['hp']-=100
        self.e_bullets.clear()
        spawn_particles(self.particles,W//2,H//2,self.pal['ui'],n=60,spd=9)

    def _do_spawn(self):
        if self.spawned>=self.target_kills: return
        self.spawn_cd-=1
        if self.spawn_cd>0: return
        r=random.random()
        if r<0.18:
            rad=random.choice([18,28])
            spd=random.uniform(1.0,2.0)*self.pspd
            self.asteroids.append({'x':random.uniform(rad,W-rad),'y':float(-rad),
                'r':rad,'vy':spd,'seed':random.randint(0,99999),'hp':3 if rad>20 else 1,'alive':True})
        else:
            weights=[8,5,4,4,3,3,3,3,3,2]
            etype=random.choices(range(10),weights=weights)[0]
            si=max(45,int(100/self.pspd))
            hp=[1,1,3,1,2,1,1,1,2,4][etype]
            ex=random.uniform(18,W-18)
            ey=-18.0 if etype!=5 else (float(random.choice([-20,H+20])))
            vx0=random.uniform(-1.0,1.0)*self.pspd
            vy0=random.uniform(1.0,2.0)*self.pspd
            if etype==5: vy0=(1.0 if ey<0 else -1.0)*self.pspd; vx0=2.5*self.pspd*(1 if ex<W//2 else -1); ex=(-20.0 if vx0>0 else W+20.0)
            if etype==7: vy0=0.2*self.pspd
            self.enemies.append({
                'x':ex,'y':ey,'vx':vx0,'vy':vy0,
                'etype':etype,'hp':hp,'max_hp':hp,
                'shoot_cd':random.randint(20,si),'shoot_int':si,
                'strafe_t':random.randint(30,80),'alive':True,'flash':0,
                'drop':random.random(),'phase':0,'timer':0,
            })
        self.spawned+=1
        self.spawn_cd=max(16,int(50/self.pspd))

    def _update_enemy(self, e):
        et=e['etype']; e['timer']+=1
        if et==3: # Zigue-zague
            e['x']+=math.sin(e['timer']*0.12)*3.0*self.pspd
            e['y']+=e['vy']
        elif et==6: # Kamikaze — acelera em direção ao jogador
            if e['y']>80:
                dx=self.px-e['x']; dy=self.py-e['y']
                d=math.hypot(dx,dy) or 1
                spd=min(0.05*self.pspd+e['timer']*0.003,6.0)
                e['vx']+=(dx/d)*spd*0.15; e['vy']+=(dy/d)*spd*0.15
                mx=4*self.pspd; e['vx']=max(-mx,min(mx,e['vx']))
                my=5*self.pspd; e['vy']=max(-my,min(my,e['vy']))
            e['x']+=e['vx']; e['y']+=e['vy']
        elif et==7: # Torre — quase estacionária
            e['x']+=math.sin(e['timer']*0.02)*0.8
            e['y']+=e['vy']
        elif et==5: # Varredor — horizontal
            e['x']+=e['vx']; e['y']+=0.5*self.pspd
        else:
            e['x']+=e['vx']; e['y']+=e['vy']
            e['strafe_t']-=1
            if e['strafe_t']<=0:
                e['vx']=random.uniform(-1.8,1.8)*self.pspd
                e['strafe_t']=random.randint(30,80)
        if e['x']<14 or e['x']>W-14: e['vx']*=-1
        if e['y']>H+40 or e['x']<-60 or e['x']>W+60 or e['hp']<=0: e['alive']=False
        if e['flash']>0: e['flash']-=1
        # Disparo
        if et==6: return  # kamikaze não atira
        e['shoot_cd']-=1
        if e['shoot_cd']<=0 and 10<e['y']<H-10:
            dx=self.px-e['x']; dy=self.py-e['y']
            d=math.hypot(dx,dy) or 1
            sp=4.0*self.pspd
            if et==4:   # Bombardeiro — bombas verticais
                self.e_bullets.append([e['x'],e['y'],0,sp*1.1,self.pal['be']])
            elif et==2: # Pesado — triplo
                for ang in [-0.25,0,0.25]:
                    self.e_bullets.append([e['x'],e['y'],(dx/d+ang)*sp,(dy/d)*sp,self.pal['be']])
            elif et==7: # Torre — rápido
                self.e_bullets.append([e['x'],e['y'],dx/d*sp*1.3,dy/d*sp*1.3,self.pal['be']])
                e['shoot_int']=max(20,e['shoot_int']-1)
            elif et==8: # Elite — triplo + mira
                for ang in [-0.2,0,0.2]:
                    self.e_bullets.append([e['x'],e['y'],(dx/d+ang)*sp,(dy/d)*sp,self.pal['be']])
            elif et==9: # Destruidor — spread 4 vias
                for ang in [-0.35,-0.12,0.12,0.35]:
                    self.e_bullets.append([e['x'],e['y'],(dx/d+ang)*sp,(dy/d)*sp,self.pal['be']])
            else:
                self.e_bullets.append([e['x'],e['y'],dx/d*sp,dy/d*sp,self.pal['be']])
            e['shoot_cd']=e['shoot_int']

    def _update_asteroid(self, a):
        a['y']+=a['vy']
        if a['y']>H+a['r']+10 or a['hp']<=0: a['alive']=False

    def _spawn_boss(self):
        btype = min(self.phase_idx, 9)
        maxhp = 300 + btype*50
        self.boss={'x':float(W/2),'y':-90.0,'hp':maxhp,'maxhp':maxhp,
                   'entering':True,'atk_cd':140,'flash':0,'btype':btype,
                   'angle':0.0,'sub_phase':0}

    def _update_boss(self):
        b=self.boss
        if b['entering']:
            b['y']+=1.4
            if b['y']>=115: b['y']=115.0; b['entering']=False
            return
        b['angle']+=0.02
        if b['flash']>0: b['flash']-=1
        hp_f=b['hp']/b['maxhp']
        bt=b['btype']

        # Movimento por tipo
        if bt==0:   # Asa-delta — oscilação simples
            b['x']+=self.boss_vx
        elif bt==1: # Caranguejo — oscilação + avanço lento
            b['x']+=self.boss_vx; b['y']=115+math.sin(b['angle'])*15
        elif bt==2: # Canhoneira — figura-8
            b['x']=W/2+math.sin(b['angle'])*240
            b['y']=115+math.sin(b['angle']*2)*30
        elif bt==3: # Dreadnought — lento, avança
            b['x']+=self.boss_vx*0.6
            b['y']=115+math.sin(b['angle']*0.5)*20
        elif bt==4: # Fantasma — teleporta a cada N frames
            b['x']+=self.boss_vx
            if b['atk_cd']==5:
                b['x']=float(random.uniform(80,W-80))
        elif bt==5: # Cristal — rotaciona em círculo
            b['x']=W/2+math.cos(b['angle']*0.7)*220
            b['y']=120+math.sin(b['angle']*0.7)*40
        elif bt==6: # Nave-mãe — muito lento
            b['x']+=self.boss_vx*0.4
            b['y']=120+math.sin(b['angle']*0.3)*10
        elif bt==7: # Tempestade — agressivo, rápido
            b['x']+=self.boss_vx*1.4
            b['y']=110+math.sin(b['angle']*1.5)*28
        elif bt==8: # Titã — lento mas imponente
            b['x']+=self.boss_vx*0.5
            b['y']=120+math.sin(b['angle']*0.4)*15
        else:       # Soberano — combina padrões
            b['x']=W/2+math.sin(b['angle']*0.8)*230
            b['y']=118+math.sin(b['angle']*1.6)*35

        if b['x']>W-70 or b['x']<70: self.boss_vx*=-1

        b['atk_cd']-=1
        if b['atk_cd']>0: return
        b['atk_cd']=max(35,int(85/self.pspd))
        sp=5.0*self.pspd
        bx,by=b['x'],b['y']
        dx=self.px-bx; dy=self.py-by; d=math.hypot(dx,dy) or 1
        spread=5 if hp_f<0.5 else 3

        if bt==0:   # Fan
            for i in range(spread):
                ang=math.radians((i-(spread-1)/2)*(25 if hp_f<0.5 else 16))
                self.e_bullets.append([bx,by+28,math.sin(ang)*sp,math.cos(ang)*sp,self.pal['be']])
        elif bt==1: # Garras — atira dos lados
            for ox in [-44,44]:
                self.e_bullets.append([bx+ox,by+10,dx/d*sp,dy/d*sp,self.pal['be']])
            if hp_f<0.5:
                self.e_bullets.append([bx,by+28,dx/d*sp,dy/d*sp,self.pal['be']])
        elif bt==2: # Triplo rápido
            for ang in [-0.2,0,0.2]:
                self.e_bullets.append([bx,by+22,(dx/d+ang)*sp,dy/d*sp,self.pal['be']])
            if hp_f<0.5:
                for ang in [-0.35,0.35]:
                    self.e_bullets.append([bx,by+22,(dx/d+ang)*sp*0.9,dy/d*sp*0.9,self.pal['be']])
        elif bt==3: # 4 cantos + rain
            for ox in [-50,-20,20,50]:
                self.e_bullets.append([bx+ox,by+28,0,sp,self.pal['be']])
            if hp_f<0.5:
                self.e_bullets.append([bx,by+28,dx/d*sp,dy/d*sp,self.pal['be']])
        elif bt==4: # Burst após teleporte
            for i in range(6 if hp_f<0.5 else 4):
                ang=2*math.pi*i/(6 if hp_f<0.5 else 4)
                self.e_bullets.append([bx,by,math.cos(ang)*sp,math.sin(ang)*sp,self.pal['be']])
            self.e_bullets.append([bx,by+28,dx/d*sp,dy/d*sp,self.pal['be']])
        elif bt==5: # Fan giratório
            base=b['angle']*30
            for i in range(6):
                ang=math.radians(base+i*60)
                self.e_bullets.append([bx,by,math.cos(ang)*sp,math.sin(ang)*sp,self.pal['be']])
        elif bt==6: # Spawn inimigos + tiro
            if len(self.enemies)<12:
                si=max(45,int(100/self.pspd))
                self.enemies.append({'x':bx-50,'y':by+30,'vx':-1.0,'vy':1.5,
                    'etype':0,'hp':1,'max_hp':1,'shoot_cd':si//2,'shoot_int':si,
                    'strafe_t':60,'alive':True,'flash':0,'drop':0.0,'phase':0,'timer':0})
                self.enemies.append({'x':bx+50,'y':by+30,'vx':1.0,'vy':1.5,
                    'etype':0,'hp':1,'max_hp':1,'shoot_cd':si//2,'shoot_int':si,
                    'strafe_t':60,'alive':True,'flash':0,'drop':0.0,'phase':0,'timer':0})
            for ang in [-0.3,0,0.3]:
                self.e_bullets.append([bx,by+18,(dx/d+ang)*sp,dy/d*sp,self.pal['be']])
        elif bt==7: # Dupla rajada + mira
            for ox in [-18,18]:
                self.e_bullets.append([bx+ox,by+12,ox*0.06*sp,sp,self.pal['be']])
            self.e_bullets.append([bx,by+28,dx/d*sp*1.1,dy/d*sp*1.1,self.pal['be']])
            if hp_f<0.5:
                self.e_bullets.append([bx,by+28,dx/d*sp*1.2,dy/d*sp*1.2,self.pal['be']])
        elif bt==8: # Anel + parede
            for i in range(8):
                ang=2*math.pi*i/8
                self.e_bullets.append([bx,by,math.cos(ang)*sp*0.8,math.sin(ang)*sp*0.8,self.pal['be']])
            for ox in range(-60,70,24):
                self.e_bullets.append([bx+ox,by+32,0,sp,self.pal['be']])
        else:       # Soberano — tudo
            for i in range(spread+2):
                ang=math.radians((i-(spread+1)/2)*20)
                self.e_bullets.append([bx,by+28,math.sin(ang)*sp,math.cos(ang)*sp,self.pal['be']])
            for i in range(5):
                ang=2*math.pi*i/5+b['angle']
                self.e_bullets.append([bx,by,math.cos(ang)*sp*0.9,math.sin(ang)*sp*0.9,self.pal['be']])
            self.e_bullets.append([bx,by+28,dx/d*sp*1.2,dy/d*sp*1.2,self.pal['be']])

    def _collisions(self):
        bullets_keep=[]
        for b in self.p_bullets:
            bx,by=b[0],b[1]
            brect=pygame.Rect(int(bx)-2,int(by)-6,4,12)
            removed=False
            for e in self.enemies:
                if not e['alive']: continue
                ew=[14,10,24,14,20,22,16,16,20,28][e['etype']]
                eh=[28,22,36,28,22,28,28,24,20,40][e['etype']]
                if brect.colliderect(pygame.Rect(int(e['x'])-ew//2,int(e['y'])-eh//2,ew,eh)):
                    removed=True; e['hp']-=b[5]; e['flash']=8; self._play('hit')
                    if e['hp']<=0:
                        spawn_particles(self.particles,e['x'],e['y'],self.pal['ec'])
                        self._play('explosion'); self.score+=[10,15,30,12,20,14,8,12,25,50][e['etype']]
                        self.kills+=1
                        drop_ch=[0.12,0.06,0.40,0.12,0.25,0.12,0.10,0.15,0.30,0.70][e['etype']]
                        if e['drop']<drop_ch:
                            pt=0 if random.random()<0.65 else 1
                            self.powerups.append([e['x'],e['y'],pt,0])
                    break
            if not removed:
                for a in self.asteroids:
                    if not a['alive']: continue
                    if math.hypot(bx-a['x'],by-a['y'])<a['r']:
                        removed=True; a['hp']-=b[5]; self._play('hit')
                        if a['hp']<=0:
                            spawn_particles(self.particles,a['x'],a['y'],self.pal['star'])
                            self._play('explosion'); self.score+=5
                        break
            if not removed and self.boss and not self.boss['entering']:
                bossrect=pygame.Rect(int(self.boss['x'])-56,int(self.boss['y'])-32,112,64)
                if brect.colliderect(bossrect):
                    removed=True; self.boss['hp']-=b[5]; self.boss['flash']=5; self._play('hit')
                    spawn_particles(self.particles,bx,by,self.pal['bc'],n=6,spd=2)
            if not removed: bullets_keep.append(b)
        self.p_bullets=bullets_keep

        if self.inv<=0:
            eb_keep=[]
            for b in self.e_bullets:
                if math.hypot(b[0]-self.px,b[1]-self.py)<11:
                    self._hit_player()
                else: eb_keep.append(b)
            self.e_bullets=eb_keep
            prect=pygame.Rect(int(self.px)-10,int(self.py)-13,20,26)
            for e in self.enemies:
                if not e['alive']: continue
                ew=[14,10,24,14,20,22,16,16,20,28][e['etype']]
                if prect.colliderect(pygame.Rect(int(e['x'])-ew//2,int(e['y'])-14,ew,28)):
                    self._hit_player(); e['hp']=0; break
            for a in self.asteroids:
                if not a['alive']: continue
                if math.hypot(self.px-a['x'],self.py-a['y'])<a['r']+10:
                    self._hit_player(); break

        pu_keep=[]
        for p in self.powerups:
            if math.hypot(self.px-p[0],self.py-p[1])<22:
                self._play('powerup')
                if p[2]==0: self.weapon_lvl=min(5,self.weapon_lvl+1)
                else:        self.bombs=min(5,self.bombs+1)
            else: pu_keep.append(p)
        self.powerups=pu_keep

    def _hit_player(self):
        if self.inv>0: return
        self.lives-=1; self.weapon_lvl=max(1,self.weapon_lvl-1)
        self.inv=120; self._play('player_dmg')
        spawn_particles(self.particles,self.px,self.py,self.pal['ui'],n=20,spd=4)
        if self.lives<=0:
            if self.continues_left>0:
                self.continues_left-=1
                self.continue_countdown=FPS*10   # 10 segundos
                self.state=self.CONTINUE_PROMPT
            else:
                save_hs(self.score)
                self.highscore=max(self.highscore,self.score)
                self.state=self.GAME_OVER

    # ── Desenho ───────────────────────────────────────────────────────────────
    def _draw(self):
        pal=self.pal
        screen.fill(pal['bg'])
        draw_stars(screen,self.stars,pal['star'])
        if   self.state==self.MENU:             self._draw_menu()
        elif self.state==self.BOSS_WARN:        self._draw_hud(); self._draw_scene(); self._draw_boss_warn()
        elif self.state==self.PHASE_CLEAR:      self._draw_hud(); self._draw_scene(); self._draw_phase_clear()
        elif self.state==self.PLAYING:          self._draw_hud(); self._draw_scene()
        elif self.state==self.CONTINUE_PROMPT:  self._draw_continue()
        elif self.state==self.GAME_OVER:        self._draw_game_over()
        elif self.state==self.VICTORY:          self._draw_victory()
        screen.blit(_scanline,(0,0))
        pygame.display.flip()

    def _draw_scene(self):
        pal=self.pal
        for p in self.particles:
            a=p[4]/p[5]; c=dim(p[6],a); sx,sy=int(p[0]),int(p[1])
            if 0<=sx<W and 0<=sy<H: screen.set_at((sx,sy),c)
        for b in self.e_bullets: draw_bullet_enemy(screen,b[0],b[1],b[4])
        for a in self.asteroids: draw_asteroid(screen,a['x'],a['y'],a['r'],pal['star'],a['seed'])
        for e in self.enemies:   draw_enemy(screen,e['x'],e['y'],pal['ec'],e['etype'],e['flash'])
        if self.boss:            draw_boss(screen,self.boss['x'],self.boss['y'],pal['bc'],self.boss['hp'],self.boss['btype'],self.boss['flash'])
        for p in self.powerups:  draw_powerup(screen,p[0],p[1],p[2],pal['ui'],pal['bp'])
        for b in self.p_bullets: draw_bullet_player(screen,b[0],b[1],b[4])
        draw_player(screen,int(self.px),int(self.py),pal['ui'],self.inv)
        if self.bomb_flash>0:
            alpha=int(180*self.bomb_flash/50)
            fs=pygame.Surface((W,H),pygame.SRCALPHA); fs.fill((*pal['ui'],alpha)); screen.blit(fs,(0,0))

    def _draw_hud(self):
        pal=self.pal; c=pal['ui']
        glow_text(screen,f"SCORE  {self.score:07d}",_font_sm,c,10,10)
        glow_text(screen,f"MELHOR {self.highscore:07d}",_font_sm,c,10,30)
        ph_idx=min(self.phase_idx,9)
        glow_text(screen,f"FASE {ph_idx+1:02d}/10  {PHASES[ph_idx]['name']}",_font_sm,c,W//2,10,center=True)
        # Vidas (max 10)
        glow_text(screen,"VIDAS",_font_sm,c,W-160,10)
        for i in range(min(self.lives,10)):
            lx=W-150+i*14; pts=[(lx,6),(lx-5,17),(lx,13),(lx+5,17)]
            pygame.draw.polygon(screen,c,pts,1)
        glow_text(screen,f"CONT x{self.continues_left}",_font_sm,dim(c,0.65),W-95,28)
        glow_text(screen,f"PWR {'█'*self.weapon_lvl}{'░'*(5-self.weapon_lvl)}",_font_sm,c,10,H-28)
        glow_text(screen,f"BOMB x{self.bombs}",_font_sm,c,W-100,H-28)
        # Barra de progresso inimigos
        if self.boss is None:
            filled=min(self.spawned,self.target_kills)
            bar_w=200; bx=W//2-bar_w//2; by=H-16
            pygame.draw.rect(screen,dim(c,0.2),(bx,by,bar_w,6))
            pygame.draw.rect(screen,dim(c,0.6),(bx,by,int(bar_w*filled/self.target_kills),6))
            pygame.draw.rect(screen,dim(c,0.4),(bx,by,bar_w,6),1)

    def _draw_menu(self):
        pal=self.pal; c=pal['ui']; t=pygame.time.get_ticks()/1000
        glow_text(screen,"NAVE RETRÔ",_font_lg,c,W//2,H//2-100,center=True)
        glow_text(screen,"10 FASES · 10 CHEFES · SURVIVAL MODE",_font_sm,dim(c,0.65),W//2,H//2-52,center=True)
        if int(t*1.5)%2==0:
            glow_text(screen,"PRESSIONE ENTER PARA INICIAR",_font_sm,c,W//2,H//2-12,center=True)
        lines=[("SETAS / WASD","MOVER"),("ESPAÇO / Z","ATIRAR"),("B / X","BOMBA")]
        for i,(k,v) in enumerate(lines):
            glow_text(screen,f"{k:<14} {v}",_font_sm,dim(c,0.55),W//2,H//2+32+i*22,center=True)
        glow_text(screen,f"MELHOR: {self.highscore:07d}",_font_sm,dim(c,0.75),W//2,H//2+120,center=True)
        for i,ph in enumerate(PHASES):
            col=ph['ui']; r=6 if i==0 else 4
            pygame.draw.circle(screen,col,(W//2-90+i*20,H//2+155),r,0 if i<self.phase_idx else 1)

    def _draw_boss_warn(self):
        c=self.pal['ui']
        if pygame.time.get_ticks()//250%2:
            bt=min(self.phase_idx,9)
            nomes=["CRUZADOR","CARANGUEJO","CANHONEIRA","DREADNOUGHT","FANTASMA",
                   "CRISTALINO","NAVE-MÃE","TEMPESTADE","TITÃ","SOBERANO FINAL"]
            glow_text(screen,f"⚠  CHEFE: {nomes[bt]}  ⚠",_font_md,c,W//2,H//2-12,center=True)

    def _draw_phase_clear(self):
        c=self.pal['ui']
        ph=min(self.phase_idx,9)
        glow_text(screen,f"FASE {ph+1} CONCLUÍDA",_font_lg,c,W//2,H//2-32,center=True)
        glow_text(screen,f"PONTOS: {self.score:07d}",_font_md,c,W//2,H//2+22,center=True)
        if ph<9:
            glow_text(screen,f"PRÓXIMO: {PHASES[ph+1]['name']}",_font_sm,dim(c,0.65),W//2,H//2+56,center=True)

    def _draw_continue(self):
        ph=min(self.phase_idx,len(PHASES)-1)
        c=PHASES[ph]['ui']; bg=PHASES[ph]['bg']
        screen.fill(bg)
        draw_stars(screen,self.stars,PHASES[ph]['star'])
        glow_text(screen,"VIDAS ESGOTADAS",_font_lg,c,W//2,H//2-110,center=True)
        secs=math.ceil(self.continue_countdown/FPS)
        glow_text(screen,f"CONTINUES RESTANTES: {self.continues_left}",_font_md,c,W//2,H//2-60,center=True)
        pygame.draw.rect(screen,dim(c,0.15),(W//2-200,H//2-30,400,140))
        pygame.draw.rect(screen,dim(c,0.5),(W//2-200,H//2-30,400,140),1)
        glow_text(screen,"CONTINUAR?",_font_md,c,W//2,H//2-15,center=True)
        glow_text(screen,f"S / ENTER  —  Continuar da Fase {ph+1}",_font_sm,c,W//2,H//2+18,center=True)
        glow_text(screen,"N / R       —  Recomeçar do Início",_font_sm,dim(c,0.65),W//2,H//2+42,center=True)
        # Countdown
        bar_w=360; filled=int(bar_w*self.continue_countdown/(FPS*10))
        pygame.draw.rect(screen,dim(c,0.2),(W//2-180,H//2+74,bar_w,8))
        col_cd=(220,60,60) if secs<=3 else c
        pygame.draw.rect(screen,col_cd,(W//2-180,H//2+74,filled,8))
        pygame.draw.rect(screen,dim(c,0.5),(W//2-180,H//2+74,bar_w,8),1)
        glow_text(screen,f"{secs:02d}s",_font_md,col_cd,W//2,H//2+88,center=True)
        screen.blit(_scanline,(0,0))

    def _draw_game_over(self):
        ph=min(self.phase_idx,len(PHASES)-1)
        c=PHASES[ph]['ui']; bg=PHASES[ph]['bg']
        screen.fill(bg); draw_stars(screen,self.stars,PHASES[ph]['star'])
        glow_text(screen,"GAME OVER",_font_lg,c,W//2,H//2-70,center=True)
        glow_text(screen,f"PONTUAÇÃO FINAL: {self.score:07d}",_font_md,c,W//2,H//2-10,center=True)
        glow_text(screen,f"FASE ALCANÇADA: {ph+1}/10",_font_sm,dim(c,0.7),W//2,H//2+28,center=True)
        if self.score>=self.highscore and self.score>0:
            glow_text(screen,"★  NOVO RECORDE!  ★",_font_sm,c,W//2,H//2+55,center=True)
        glow_text(screen,"ENTER — JOGAR NOVAMENTE",_font_sm,dim(c,0.55),W//2,H//2+86,center=True)

    def _draw_victory(self):
        t=pygame.time.get_ticks()/1000; cyc=int(t*2)%len(PHASES)
        c=PHASES[cyc]['ui']; bg=PHASES[0]['bg']
        screen.fill(bg); draw_stars(screen,self.stars,PHASES[cyc]['star'])
        glow_text(screen,"★  VITÓRIA TOTAL  ★",_font_lg,c,W//2,H//2-80,center=True)
        glow_text(screen,"TODOS OS 10 SETORES LIBERTADOS",_font_md,c,W//2,H//2-28,center=True)
        glow_text(screen,f"PONTUAÇÃO FINAL: {self.score:07d}",_font_md,c,W//2,H//2+18,center=True)
        glow_text(screen,"ENTER — MENU PRINCIPAL",_font_sm,dim(c,0.55),W//2,H//2+68,center=True)


# ── Entrada ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
