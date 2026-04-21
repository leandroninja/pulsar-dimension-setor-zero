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
    # Plasma bolt: sweep 1400→300 Hz, sine+saw mix com harmônico
    n = int(SR*0.13)
    s = []
    for i in range(n):
        t = i/SR
        f = 1400*math.exp(-9*t)
        env = math.exp(-16*t)*(1-math.exp(-60*t))
        v = (0.48*math.sin(2*math.pi*f*t)
           + 0.30*_saw(f*1.5, t)
           + 0.22*math.sin(2*math.pi*f*2.01*t))
        s.append(int(32767*0.30*env*v))
    return _mk(s)

def _snd_hit():
    # Impacto metálico: ruído + tom descendente + anel breve
    n = int(SR*0.10)
    s = []
    for i in range(n):
        t = i/SR
        noise = random.uniform(-1,1)
        ring  = math.sin(2*math.pi*380*math.exp(-20*t)*t)*math.exp(-18*t)
        thump = _saw(90*math.exp(-25*t), t)*math.exp(-22*t)
        env   = math.exp(-22*t)*(1-math.exp(-80*t))
        s.append(int(32767*0.34*env*(noise*0.5+ring*0.3+thump*0.2)))
    return _mk(s)

def _snd_explosion():
    # Explosão inimiga: sub-bass + crunch + estilhaços
    n = int(SR*0.60)
    s = []
    for i in range(n):
        t = i/SR
        sub   = _saw(65*math.exp(-3*t), t)*math.exp(-3.5*t)*(1-math.exp(-40*t))
        noise = random.uniform(-1,1)*math.exp(-5.5*t)
        crack = _sq(700*math.exp(-22*t), t)*math.exp(-28*t)
        debris= random.uniform(-1,1)*math.exp(-9*t)*0.4
        v = 0.42*sub + 0.32*noise + 0.16*crack + 0.10*debris
        s.append(int(32767*0.52*v))
    return _mk(s)

def _snd_powerup():
    # Cristal de energia: arpejo ascendente com harmônicos e shimmer
    freqs = [330, 415, 523, 659, 784, 1047, 1319]
    s = []
    for k, freq in enumerate(freqs):
        dur = 0.072
        seg = int(SR*dur)
        for j in range(seg):
            t = j/SR
            env = math.exp(-4*t/dur)*(1-math.exp(-50*t))
            v = (0.45*math.sin(2*math.pi*freq*t)
               + 0.25*math.sin(2*math.pi*freq*2*t)
               + 0.18*math.sin(2*math.pi*freq*3.01*t)
               + 0.12*_saw(freq*0.5, t))
            s.append(int(32767*0.38*env*v))
    return _mk(s)

def _snd_bomb():
    # Bomba épica: sub-bass colossal + cascata de ruído + reverb tail
    n = int(SR*2.2)
    s = []
    for i in range(n):
        t = i/SR
        sub    = _saw(38*math.exp(-0.4*t), t)*math.exp(-1.2*t)*(1-math.exp(-35*t))
        mid    = random.uniform(-1,1)*math.exp(-2.2*t)
        crack  = _sq(280*math.exp(-18*t), t)*math.exp(-22*t)
        reverb = (random.uniform(-1,1)*math.exp(-4*(t-0.12))
                  if t>0.12 else 0.0)*0.55
        shk    = math.sin(2*math.pi*28*t)*math.exp(-2*t)*0.3
        v = 0.34*sub + 0.28*mid + 0.14*crack + 0.16*reverb + 0.08*shk
        s.append(int(32767*0.68*v))
    return _mk(s)

def _snd_player_dmg():
    # Dano ao jogador: impacto metálico + alarme pulsante + distorção
    n = int(SR*0.30)
    s = []
    for i in range(n):
        t = i/SR
        impact = _sq(160*math.exp(-7*t), t)*math.exp(-14*t)
        alarm  = (math.sin(2*math.pi*460*t)*math.exp(-5*t)
                  *abs(math.sin(2*math.pi*16*t)))
        noise  = random.uniform(-1,1)*math.exp(-9*t)
        v = 0.38*impact + 0.38*alarm + 0.24*noise
        s.append(int(32767*0.46*v))
    return _mk(s)

def _snd_boss_alert():
    # Alerta de chefe: 3 acordes dramáticos com modulação de urgência
    chords = [(988,740,494), (880,660,440), (988,740,494)]
    s = []
    for chord in chords:
        dur = 0.28; seg = int(SR*dur)
        for j in range(seg):
            t = j/SR
            env   = math.exp(-2*t/dur)*(1-math.exp(-25*t))
            v     = sum(math.sin(2*math.pi*f*t)/3 for f in chord)
            pulse = 0.65 + 0.35*abs(math.sin(2*math.pi*10*t))
            s.append(int(32767*0.38*env*v*pulse))
    return _mk(s)

def _snd_boss_death():
    # Morte do chefe: explosão em 3 estágios com echo final
    n = int(SR*1.6)
    s = []
    for i in range(n):
        t = i/SR
        if t < 0.18:
            sub = _saw(90*math.exp(-6*t), t)
            nz  = random.uniform(-1,1)
            v   = (sub*0.5+nz*0.5)*math.exp(-7*t)*(1-math.exp(-60*t))
        elif t < 0.85:
            lt  = t-0.18
            deb = random.uniform(-1,1)*math.exp(-3.5*lt)
            ton = _saw(110*math.exp(-2.5*lt), lt)*math.exp(-4*lt)
            v   = deb*0.55+ton*0.45
        else:
            lt  = t-0.85
            v   = random.uniform(-1,1)*math.exp(-4.5*lt)*0.38
        s.append(int(32767*0.62*v))
    return _mk(s)

def _snd_music():
    # ── 8 compassos, BPM 160, Lá menor ──────────────────────────────────────
    bpm = 160; b = 60.0/bpm; e = b/2; h = b*2
    PI2 = 2*math.pi

    mel = [                                    # melodia principal (lead)
        (440,b),(0,e),(523,e),(659,h),         # compasso 1
        (587,b),(523,b),(494,h),               # compasso 2
        (523,b),(0,e),(659,e),(784,h),         # compasso 3
        (698,b),(659,b),(587,h),               # compasso 4
        (659,b),(0,e),(880,e),(784,h),         # compasso 5
        (698,b),(659,b),(587,h),               # compasso 6
        (523,b),(659,b),(587,b),(523,b),       # compasso 7
        (440,h),(0,e),(440,e),(523,b),         # compasso 8
    ]
    harm = [                                   # harmonia (pad, 1 terça abaixo)
        (330,b),(0,e),(392,e),(523,h),  (440,b),(392,b),(370,h),
        (392,b),(0,e),(523,e),(587,h),  (523,b),(494,b),(440,h),
        (523,b),(0,e),(659,e),(587,h),  (523,b),(494,b),(440,h),
        (392,b),(523,b),(440,b),(392,b),(330,h),(0,e),(330,e),(392,b),
    ]

    total = sum(d for _, d in mel)
    n = int(total*SR) + SR//4
    buf = array.array('h', [0]*(n*2))

    def wb(idx, v):
        if 0 <= idx < n:
            buf[2*idx]   = max(-32767, min(32767, buf[2*idx]   + v))
            buf[2*idx+1] = max(-32767, min(32767, buf[2*idx+1] + v))

    # ── Lead synth: saw + sine, ataque rápido, decay natural ─────────────────
    pos = 0
    for freq, dur in mel:
        samp = int(dur*SR)
        if freq > 0:
            for i in range(samp):
                t = i/SR
                env = (1-math.exp(-28*t))*math.exp(-1.6*t/dur)
                v = int(32767*0.17*env*(_saw(freq,t)*0.58+math.sin(PI2*freq*t)*0.42))
                wb(pos+i, v)
        pos += samp

    # ── Pad: sine duplo com chorus leve (levemente desafinado) ───────────────
    pos = 0
    for freq, dur in harm:
        samp = int(dur*SR)
        if freq > 0:
            for i in range(samp):
                t = i/SR
                env = (1-math.exp(-12*t))*math.exp(-1.4*t/dur)
                v = int(32767*0.08*env*(
                    math.sin(PI2*freq*t)
                    +math.sin(PI2*freq*1.008*t))*0.5)
                wb(pos+i, v)
        pos += samp

    # ── Arpejo: square, 8th notes, percorre acorde de Lá menor ──────────────
    arp = [220, 330, 440, 523, 659, 784, 659, 523]
    samp_e = int(e*SR); pos = 0; ai = 0
    while pos < n - samp_e:
        f = arp[ai % 8]
        for i in range(samp_e):
            env = math.exp(-9*i/SR)*(1-math.exp(-70*i/SR))
            wb(pos+i, int(32767*0.09*env*_sq(f, i/SR)))
        pos += samp_e; ai += 1

    # ── Sub-bass: saw + sine, quarter notes, linha andante ───────────────────
    bass = [110,110,131,98, 110,165,98,110]*4
    samp_b = int(b*SR); pos = 0
    for fb in bass:
        if pos >= n: break
        for i in range(samp_b):
            t = i/SR
            env = (1-math.exp(-18*t))*math.exp(-2.8*t/b)
            v = int(32767*0.19*env*(_saw(fb,t)*0.66+math.sin(PI2*fb*t)*0.34))
            wb(pos+i, v)
        pos += samp_b

    # ── Kick: sweep 145→20Hz + ruído de ataque ───────────────────────────────
    sk = int(0.22*SR); ki = 0; pos = 0
    while pos < n - samp_b:
        if ki % 2 == 0:                        # beats 1 e 3 do compasso
            for i in range(sk):
                if pos+i >= n: break
                t = i/SR
                f2 = 145*math.exp(-16*t)
                env = math.exp(-5.5*t)*(1-math.exp(-80*t))
                nz  = random.uniform(-1,1)*math.exp(-18*t)
                v = int(32767*0.28*env*(math.sin(PI2*f2*t)*0.70+nz*0.30))
                wb(pos+i, v)
        pos += samp_b; ki += 1

    # ── Snare: ruído + tom descendente 220Hz ─────────────────────────────────
    ss = int(0.14*SR); si = 0; pos = 0
    while pos < n - samp_b:
        if si % 4 in (1, 3):                   # beats 2 e 4
            for i in range(ss):
                if pos+i >= n: break
                t = i/SR
                env  = math.exp(-10*t)*(1-math.exp(-100*t))
                tone = math.sin(PI2*220*math.exp(-30*t)*t)
                v = int(32767*0.16*env*(random.uniform(-1,1)*0.62+tone*0.38))
                wb(pos+i, v)
        pos += samp_b; si += 1

    # ── Hi-hat fechado: ruído de alta frequência, tempo e contratempo ────────
    sh = int(0.042*SR); pos = 0
    while pos < n - samp_b:
        for i in range(sh):
            if pos+i >= n: break
            wb(pos+i, int(32767*0.065*math.exp(-48*i/SR)*random.uniform(-1,1)))
        pos2 = pos + samp_e
        for i in range(sh):
            if pos2+i >= n: break
            wb(pos2+i, int(32767*0.055*math.exp(-52*i/SR)*random.uniform(-1,1)))
        pos += samp_b

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
pygame.display.set_caption("PULSAR: DIMENSÃO SETOR ZERO")
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


# ── Helper de brilho ───────────────────────────────────────────────────────────
def _bright(col, v):
    return tuple(min(255, c + v) for c in col)


# ── Desenho do jogador ─────────────────────────────────────────────────────────
def draw_player(surf, cx, cy, col, inv=0):
    if inv > 0 and (inv // 6) % 2 == 0: return
    cx, cy = int(cx), int(cy)
    t = pygame.time.get_ticks()
    c0=dim(col,0.12); c1=dim(col,0.28); c2=dim(col,0.50); c3=dim(col,0.72); c4=col
    c5=_bright(col,60)
    GLASS=(50,90,200); FLAME=(255,150,20)
    glow = _bright(FLAME,70) if (t//65)%2 else FLAME

    # Sombra das asas
    pygame.draw.polygon(surf,c0,[(cx,cy-4),(cx-24,cy+8),(cx-28,cy+18),(cx-20,cy+20),(cx-8,cy+10)])
    pygame.draw.polygon(surf,c0,[(cx,cy-4),(cx+24,cy+8),(cx+28,cy+18),(cx+20,cy+20),(cx+8,cy+10)])
    # Asas principais
    pygame.draw.polygon(surf,c1,[(cx,cy-2),(cx-20,cy+7),(cx-24,cy+16),(cx-16,cy+18),(cx-6,cy+9)])
    pygame.draw.polygon(surf,c1,[(cx,cy-2),(cx+20,cy+7),(cx+24,cy+16),(cx+16,cy+18),(cx+6,cy+9)])
    # Painel iluminado das asas
    pygame.draw.polygon(surf,c2,[(cx-2,cy),(cx-14,cy+7),(cx-18,cy+14),(cx-12,cy+16),(cx-4,cy+8)])
    pygame.draw.polygon(surf,c2,[(cx+2,cy),(cx+14,cy+7),(cx+18,cy+14),(cx+12,cy+16),(cx+4,cy+8)])
    # Borda das asas
    pygame.draw.polygon(surf,c3,[(cx,cy-2),(cx-20,cy+7),(cx-24,cy+16),(cx-16,cy+18),(cx-6,cy+9)],1)
    pygame.draw.polygon(surf,c3,[(cx,cy-2),(cx+20,cy+7),(cx+24,cy+16),(cx+16,cy+18),(cx+6,cy+9)],1)
    # Canhões das asas
    for dx in [-21, 21]:
        pygame.draw.rect(surf,c2,(cx+dx-1,cy+8,2,9))
        pygame.draw.rect(surf,c5,(cx+dx-1,cy+15,2,4))
    # Linha de painel das asas
    pygame.draw.line(surf,c3,(cx-6,cy+2),(cx-18,cy+13),1)
    pygame.draw.line(surf,c3,(cx+6,cy+2),(cx+18,cy+13),1)
    # Fuselagem central
    pygame.draw.polygon(surf,c2,[(cx,cy-20),(cx-5,cy-8),(cx-6,cy+8),(cx-4,cy+18),(cx+4,cy+18),(cx+6,cy+8),(cx+5,cy-8)])
    pygame.draw.polygon(surf,c4,[(cx,cy-20),(cx-5,cy-8),(cx-6,cy+8),(cx-4,cy+18),(cx+4,cy+18),(cx+6,cy+8),(cx+5,cy-8)],1)
    # Destaque central da fuselagem
    pygame.draw.line(surf,c5,(cx,cy-18),(cx,cy+10),1)
    # Painéis laterais da fuselagem
    pygame.draw.line(surf,c1,(cx-4,cy-4),(cx-4,cy+12),1)
    pygame.draw.line(surf,c1,(cx+4,cy-4),(cx+4,cy+12),1)
    # Plataforma traseira (entre motores)
    pygame.draw.rect(surf,c0,(cx-9,cy+16,18,6))
    pygame.draw.rect(surf,c1,(cx-9,cy+16,18,6),1)
    # Cockpit
    pygame.draw.ellipse(surf,dim(GLASS,0.5),(cx-6,cy-23,12,11))
    pygame.draw.ellipse(surf,GLASS,(cx-4,cy-22,8,8))
    pygame.draw.ellipse(surf,_bright(GLASS,90),(cx-3,cy-21,4,4))
    # Pods de motor duplos
    for dx in [-5, 5]:
        ex, ey = cx+dx, cy+22
        pygame.draw.ellipse(surf,c0,(ex-4,ey-6,8,10))
        pygame.draw.ellipse(surf,c1,(ex-3,ey-5,6,8))
        pygame.draw.ellipse(surf,c3,(ex-3,ey-5,6,8),1)
        pygame.draw.circle(surf,glow,(ex,ey+4),3)
        pygame.draw.circle(surf,dim(FLAME,0.25),(ex,ey+4),5,1)


# ── Desenho de 10 tipos de inimigos ───────────────────────────────────────────
def draw_enemy(surf, cx, cy, col, etype, flash=0):
    c = (220,220,220) if flash>0 else col
    c0=dim(c,0.12); c1=dim(c,0.28); c2=dim(c,0.50); c3=dim(c,0.72); c4=c
    c5=_bright(c,55)
    GLASS=(50,90,200); ENG=(180,70,20)
    t = pygame.time.get_ticks()
    glow = _bright(ENG,60) if (t//80)%2 else ENG
    cx, cy = int(cx), int(cy)

    if etype == 0:   # Padrão — caça interceptador (faces down)
        # Asas traseiras (motores no topo)
        pygame.draw.polygon(surf,c0,[(cx-4,cy-13),(cx-22,cy-2),(cx-18,cy+6),(cx-6,cy+1)])
        pygame.draw.polygon(surf,c0,[(cx+4,cy-13),(cx+22,cy-2),(cx+18,cy+6),(cx+6,cy+1)])
        pygame.draw.polygon(surf,c1,[(cx-3,cy-11),(cx-18,cy-1),(cx-14,cy+5),(cx-5,cy+1)])
        pygame.draw.polygon(surf,c1,[(cx+3,cy-11),(cx+18,cy-1),(cx+14,cy+5),(cx+5,cy+1)])
        pygame.draw.polygon(surf,c2,[(cx-3,cy-9),(cx-12,cy-1),(cx-9,cy+4),(cx-4,cy+1)])
        pygame.draw.polygon(surf,c2,[(cx+3,cy-9),(cx+12,cy-1),(cx+9,cy+4),(cx+4,cy+1)])
        # Borda das asas
        pygame.draw.polygon(surf,c3,[(cx-3,cy-11),(cx-18,cy-1),(cx-14,cy+5),(cx-5,cy+1)],1)
        pygame.draw.polygon(surf,c3,[(cx+3,cy-11),(cx+18,cy-1),(cx+14,cy+5),(cx+5,cy+1)],1)
        # Fuselagem
        body=[(cx,cy+14),(cx-6,cy+2),(cx-5,cy-12),(cx,cy-14),(cx+5,cy-12),(cx+6,cy+2)]
        pygame.draw.polygon(surf,c2,body); pygame.draw.polygon(surf,c4,body,1)
        pygame.draw.line(surf,c5,(cx,cy-12),(cx,cy+10),1)
        # Nariz (ponta inferior)
        pygame.draw.polygon(surf,c3,[(cx,cy+14),(cx-4,cy+6),(cx+4,cy+6)])
        pygame.draw.polygon(surf,c5,[(cx,cy+15),(cx-2,cy+10),(cx+2,cy+10)])
        # Cockpit
        pygame.draw.ellipse(surf,GLASS,(cx-4,cy-10,8,8))
        pygame.draw.ellipse(surf,_bright(GLASS,70),(cx-2,cy-9,4,4))
        # Glow do motor
        pygame.draw.circle(surf,glow,(cx,cy-14),3)
        pygame.draw.circle(surf,dim(ENG,0.25),(cx,cy-14),5,1)

    elif etype == 1: # Rápido — interceptador esbelto
        # Asas finas
        pygame.draw.polygon(surf,c1,[(cx-2,cy-12),(cx-18,cy-4),(cx-14,cy+4),(cx-2,cy+2)])
        pygame.draw.polygon(surf,c1,[(cx+2,cy-12),(cx+18,cy-4),(cx+14,cy+4),(cx+2,cy+2)])
        pygame.draw.polygon(surf,c2,[(cx-2,cy-10),(cx-13,cy-3),(cx-9,cy+3),(cx-2,cy+1)])
        pygame.draw.polygon(surf,c2,[(cx+2,cy-10),(cx+13,cy-3),(cx+9,cy+3),(cx+2,cy+1)])
        pygame.draw.polygon(surf,c3,[(cx-2,cy-12),(cx-18,cy-4),(cx-14,cy+4),(cx-2,cy+2)],1)
        pygame.draw.polygon(surf,c3,[(cx+2,cy-12),(cx+18,cy-4),(cx+14,cy+4),(cx+2,cy+2)],1)
        # Fuselagem longa e estreita
        body=[(cx,cy+15),(cx-3,cy),(cx-3,cy-13),(cx,cy-15),(cx+3,cy-13),(cx+3,cy)]
        pygame.draw.polygon(surf,c2,body); pygame.draw.polygon(surf,c4,body,1)
        pygame.draw.line(surf,c5,(cx,cy-13),(cx,cy+12),1)
        # Nariz pontiagudo
        pygame.draw.polygon(surf,c5,[(cx,cy+16),(cx-2,cy+10),(cx+2,cy+10)])
        # Cockpit
        pygame.draw.ellipse(surf,GLASS,(cx-3,cy-12,6,6))
        pygame.draw.ellipse(surf,_bright(GLASS,60),(cx-2,cy-11,4,4))
        # Motores gêmeos
        for dx in [-3, 3]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-15),2)
            pygame.draw.circle(surf,dim(ENG,0.2),(cx+dx,cy-15),4,1)

    elif etype == 2: # Pesado — bombardeiro encouraçado
        # Casco blindado externo
        pygame.draw.polygon(surf,c0,[(cx,cy+18),(cx-24,cy+8),(cx-26,cy-6),(cx-14,cy-16),(cx+14,cy-16),(cx+26,cy-6),(cx+24,cy+8)])
        pygame.draw.polygon(surf,c1,[(cx,cy+16),(cx-20,cy+8),(cx-22,cy-4),(cx-12,cy-14),(cx+12,cy-14),(cx+22,cy-4),(cx+20,cy+8)])
        pygame.draw.polygon(surf,c2,[(cx-8,cy+14),(cx-16,cy+6),(cx-18,cy-2),(cx-8,cy-10),(cx+8,cy-10),(cx+18,cy-2),(cx+16,cy+6),(cx+8,cy+14)])
        pygame.draw.polygon(surf,c4,[(cx,cy+16),(cx-20,cy+8),(cx-22,cy-4),(cx-12,cy-14),(cx+12,cy-14),(cx+22,cy-4),(cx+20,cy+8)],1)
        # Painéis de armadura
        pygame.draw.line(surf,c3,(cx-18,cy+4),(cx-10,cy+12),1)
        pygame.draw.line(surf,c3,(cx+18,cy+4),(cx+10,cy+12),1)
        pygame.draw.line(surf,c3,(cx-20,cy-2),(cx-12,cy-10),1)
        pygame.draw.line(surf,c3,(cx+20,cy-2),(cx+12,cy-10),1)
        # Canhões laterais
        for dx in [-20, 20]:
            pygame.draw.rect(surf,c3,(cx+dx-2,cy+10,4,8))
            pygame.draw.rect(surf,c5,(cx+dx-1,cy+16,2,4))
        # Cockpit
        pygame.draw.ellipse(surf,GLASS,(cx-5,cy-6,10,10))
        pygame.draw.ellipse(surf,_bright(GLASS,60),(cx-3,cy-5,6,6))
        # Motores triplos
        for dx in [-10, 0, 10]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-16),3)
            pygame.draw.circle(surf,dim(ENG,0.2),(cx+dx,cy-16),5,1)

    elif etype == 3: # Zigue-zague — caça com aletas
        # Fuselagem central
        body=[(cx,cy+13),(cx-5,cy+2),(cx-5,cy-10),(cx,cy-13),(cx+5,cy-10),(cx+5,cy+2)]
        pygame.draw.polygon(surf,c2,body); pygame.draw.polygon(surf,c4,body,1)
        pygame.draw.line(surf,c5,(cx,cy-11),(cx,cy+11),1)
        # Asas assimétricas
        pygame.draw.polygon(surf,c1,[(cx-5,cy-2),(cx-24,cy-10),(cx-20,cy+2),(cx-5,cy+6)])
        pygame.draw.polygon(surf,c1,[(cx+5,cy-2),(cx+24,cy-10),(cx+20,cy+2),(cx+5,cy+6)])
        pygame.draw.polygon(surf,c2,[(cx-5,cy-1),(cx-17,cy-7),(cx-14,cy+2),(cx-5,cy+5)])
        pygame.draw.polygon(surf,c2,[(cx+5,cy-1),(cx+17,cy-7),(cx+14,cy+2),(cx+5,cy+5)])
        # Aletas traseiras
        pygame.draw.polygon(surf,c2,[(cx-5,cy-8),(cx-14,cy-14),(cx-10,cy-10)])
        pygame.draw.polygon(surf,c2,[(cx+5,cy-8),(cx+14,cy-14),(cx+10,cy-10)])
        pygame.draw.line(surf,c3,(cx-5,cy-8),(cx-14,cy-14),1)
        pygame.draw.line(surf,c3,(cx+5,cy-8),(cx+14,cy-14),1)
        # Nariz
        pygame.draw.polygon(surf,c5,[(cx,cy+13),(cx-3,cy+6),(cx+3,cy+6)])
        # Cockpit
        pygame.draw.ellipse(surf,GLASS,(cx-3,cy-9,6,7))
        # Motor
        pygame.draw.circle(surf,glow,(cx,cy-13),3)
        pygame.draw.circle(surf,dim(ENG,0.2),(cx,cy-13),5,1)

    elif etype == 4: # Bombardeiro — asa voadora larga
        # Asa principal
        pygame.draw.polygon(surf,c0,[(cx,cy+10),(cx-32,cy),(cx-38,cy-10),(cx-26,cy-18),(cx+26,cy-18),(cx+38,cy-10),(cx+32,cy)])
        pygame.draw.polygon(surf,c1,[(cx,cy+8),(cx-28,cy+1),(cx-34,cy-8),(cx-22,cy-16),(cx+22,cy-16),(cx+34,cy-8),(cx+28,cy+1)])
        pygame.draw.polygon(surf,c2,[(cx,cy+6),(cx-18,cy+1),(cx-22,cy-6),(cx-14,cy-12),(cx+14,cy-12),(cx+22,cy-6),(cx+18,cy+1)])
        pygame.draw.polygon(surf,c4,[(cx,cy+8),(cx-28,cy+1),(cx-34,cy-8),(cx-22,cy-16),(cx+22,cy-16),(cx+34,cy-8),(cx+28,cy+1)],1)
        # Nervuras das asas
        for dx in [-22,-11,11,22]:
            pygame.draw.line(surf,c3,(cx+dx,cy+4),(cx+dx,cy-10),1)
        # Baias de bombas centrais
        pygame.draw.rect(surf,c0,(cx-8,cy-4,16,12))
        pygame.draw.rect(surf,c3,(cx-8,cy-4,16,12),1)
        for dx in [-4,4]:
            pygame.draw.rect(surf,c5,(cx+dx-1,cy+7,2,4))
        # Cockpit
        pygame.draw.ellipse(surf,GLASS,(cx-4,cy-8,8,6))
        pygame.draw.ellipse(surf,_bright(GLASS,50),(cx-2,cy-7,4,4))
        # Motores nos pods das asas
        for dx in [-20, 20]:
            pygame.draw.ellipse(surf,c1,(cx+dx-5,cy-20,10,6))
            pygame.draw.ellipse(surf,c3,(cx+dx-5,cy-20,10,6),1)
            pygame.draw.circle(surf,glow,(cx+dx,cy-20),3)

    elif etype == 5: # Varredor — crescente/meia-lua
        # Corpo em crescente
        pygame.draw.polygon(surf,c0,[(cx-22,cy-8),(cx-14,cy-16),(cx,cy-18),(cx+14,cy-16),(cx+22,cy-8),(cx+16,cy+8),(cx,cy+4),(cx-16,cy+8)])
        pygame.draw.polygon(surf,c1,[(cx-18,cy-6),(cx-10,cy-14),(cx,cy-16),(cx+10,cy-14),(cx+18,cy-6),(cx+12,cy+6),(cx,cy+2),(cx-12,cy+6)])
        pygame.draw.polygon(surf,c2,[(cx-12,cy-4),(cx-6,cy-12),(cx,cy-13),(cx+6,cy-12),(cx+12,cy-4),(cx+8,cy+3),(cx,cy+1),(cx-8,cy+3)])
        pygame.draw.polygon(surf,c4,[(cx-18,cy-6),(cx-10,cy-14),(cx,cy-16),(cx+10,cy-14),(cx+18,cy-6),(cx+12,cy+6),(cx,cy+2),(cx-12,cy+6)],1)
        # Nariz central (arma principal)
        pygame.draw.polygon(surf,c3,[(cx,cy+6),(cx-4,cy+2),(cx+4,cy+2)])
        pygame.draw.polygon(surf,c5,[(cx,cy+9),(cx-2,cy+4),(cx+2,cy+4)])
        # Canhões nas pontas
        for dx in [-18, 18]:
            pygame.draw.rect(surf,c3,(cx+dx-1,cy+4,2,8))
            pygame.draw.rect(surf,c5,(cx+dx-1,cy+10,2,3))
        # Cockpit
        pygame.draw.ellipse(surf,GLASS,(cx-4,cy-10,8,7))
        pygame.draw.ellipse(surf,_bright(GLASS,50),(cx-2,cy-9,4,4))
        # Motores nas pontas do crescente
        for dx in [-12, 12]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-16),3)
            pygame.draw.circle(surf,dim(ENG,0.2),(cx+dx,cy-16),5,1)

    elif etype == 6: # Kamikaze — faca espacial
        # Corpo estreito e longo
        body=[(cx,cy+16),(cx-4,cy+4),(cx-3,cy-12),(cx,cy-14),(cx+3,cy-12),(cx+4,cy+4)]
        pygame.draw.polygon(surf,c2,body); pygame.draw.polygon(surf,c4,body,1)
        pygame.draw.line(surf,c5,(cx,cy-12),(cx,cy+14),1)
        # Aletas agressivas inclinadas para frente
        pygame.draw.polygon(surf,c1,[(cx-4,cy),(cx-22,cy-12),(cx-18,cy+6),(cx-4,cy+8)])
        pygame.draw.polygon(surf,c1,[(cx+4,cy),(cx+22,cy-12),(cx+18,cy+6),(cx+4,cy+8)])
        pygame.draw.polygon(surf,c2,[(cx-4,cy+2),(cx-16,cy-8),(cx-13,cy+5),(cx-4,cy+7)])
        pygame.draw.polygon(surf,c2,[(cx+4,cy+2),(cx+16,cy-8),(cx+13,cy+5),(cx+4,cy+7)])
        # Espinhos nas pontas
        pygame.draw.line(surf,c5,(cx-22,cy-12),(cx-26,cy-16),1)
        pygame.draw.line(surf,c5,(cx+22,cy-12),(cx+26,cy-16),1)
        # Nariz afiado
        pygame.draw.polygon(surf,c5,[(cx,cy+16),(cx-2,cy+10),(cx+2,cy+10)])
        # Sensor (sem cockpit visível)
        pygame.draw.rect(surf,dim(GLASS,0.7),(cx-2,cy-8,4,4))
        pygame.draw.rect(surf,GLASS,(cx-2,cy-8,4,4),1)
        # Motor
        pygame.draw.circle(surf,glow,(cx,cy-14),3)
        pygame.draw.circle(surf,dim(ENG,0.2),(cx,cy-14),6,1)

    elif etype == 7: # Torre — plataforma de artilharia
        # Corpo retangular blindado
        pygame.draw.rect(surf,c0,(cx-18,cy-14,36,26))
        pygame.draw.rect(surf,c1,(cx-16,cy-12,32,22))
        pygame.draw.rect(surf,c2,(cx-10,cy-8,20,14))
        pygame.draw.rect(surf,c4,(cx-16,cy-12,32,22),1)
        # Cantos blindados
        for dx, dy in [(-16,-12),(14,-12),(-16,8),(14,8)]:
            pygame.draw.rect(surf,c3,(cx+dx,cy+dy,4,4))
        # Canhões laterais
        for dx in [-22, 22]:
            pygame.draw.rect(surf,c0,(cx+dx-3,cy-4,6,10))
            pygame.draw.rect(surf,c3,(cx+dx-2,cy-3,4,8))
            pygame.draw.rect(surf,c5,(cx+dx-1,cy+5,2,5))
        # Torre central com canhão ventral
        pygame.draw.ellipse(surf,c2,(cx-6,cy-6,12,10))
        pygame.draw.rect(surf,c3,(cx-1,cy+4,2,10))
        pygame.draw.rect(surf,c5,(cx-1,cy+12,2,4))
        # Sensor
        pygame.draw.circle(surf,GLASS,(cx,cy-2),3)
        pygame.draw.circle(surf,_bright(GLASS,60),(cx,cy-2),1)
        # Propulsor traseiro
        pygame.draw.rect(surf,c1,(cx-6,cy+12,12,4))
        pygame.draw.circle(surf,glow,(cx,cy+16),3)

    elif etype == 8: # Elite — caça de fuselagem dupla
        # Fuselagem esquerda
        bl=[(cx-16,cy+12),(cx-20,cy+2),(cx-18,cy-12),(cx-12,cy-14),(cx-8,cy-2),(cx-10,cy+10)]
        pygame.draw.polygon(surf,c1,bl); pygame.draw.polygon(surf,c3,bl,1)
        pygame.draw.line(surf,c4,(cx-14,cy-12),(cx-14,cy+8),1)
        # Fuselagem direita
        br=[(cx+16,cy+12),(cx+20,cy+2),(cx+18,cy-12),(cx+12,cy-14),(cx+8,cy-2),(cx+10,cy+10)]
        pygame.draw.polygon(surf,c1,br); pygame.draw.polygon(surf,c3,br,1)
        pygame.draw.line(surf,c4,(cx+14,cy-12),(cx+14,cy+8),1)
        # Conexão central
        pygame.draw.rect(surf,c2,(cx-8,cy-4,16,10))
        pygame.draw.rect(surf,c4,(cx-8,cy-4,16,10),1)
        pygame.draw.line(surf,c5,(cx,cy-2),(cx,cy+4),1)
        # Cockpits duplos
        for dx in [-14, 14]:
            pygame.draw.ellipse(surf,GLASS,(cx+dx-3,cy-10,6,6))
            pygame.draw.ellipse(surf,_bright(GLASS,60),(cx+dx-2,cy-9,4,4))
        # Canhões cruzados
        for dx in [-8, 8]:
            pygame.draw.rect(surf,c3,(cx+dx-1,cy+10,2,8))
            pygame.draw.rect(surf,c5,(cx+dx-1,cy+16,2,4))
        # Motores quádruplos
        for dx in [-18,-6,6,18]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-14),2)
            pygame.draw.circle(surf,dim(ENG,0.2),(cx+dx,cy-14),4,1)

    else:            # Destruidor — mini-cruzador pesado
        # Casco principal
        pygame.draw.polygon(surf,c0,[(cx,cy+22),(cx-24,cy+12),(cx-28,cy-2),(cx-16,cy-18),(cx+16,cy-18),(cx+28,cy-2),(cx+24,cy+12)])
        pygame.draw.polygon(surf,c1,[(cx,cy+20),(cx-20,cy+10),(cx-24,cy-2),(cx-14,cy-16),(cx+14,cy-16),(cx+24,cy-2),(cx+20,cy+10)])
        pygame.draw.polygon(surf,c2,[(cx,cy+14),(cx-12,cy+7),(cx-14,cy-1),(cx-8,cy-10),(cx+8,cy-10),(cx+14,cy-1),(cx+12,cy+7)])
        pygame.draw.polygon(surf,c4,[(cx,cy+20),(cx-20,cy+10),(cx-24,cy-2),(cx-14,cy-16),(cx+14,cy-16),(cx+24,cy-2),(cx+20,cy+10)],1)
        # Superestrutura central
        pygame.draw.rect(surf,c2,(cx-6,cy-6,12,16))
        pygame.draw.rect(surf,c4,(cx-6,cy-6,12,16),1)
        pygame.draw.line(surf,c5,(cx,cy-4),(cx,cy+10),1)
        # Canhões anti-aéreos laterais
        for dx in [-20, 20]:
            pygame.draw.rect(surf,c3,(cx+dx-2,cy+8,4,10))
            pygame.draw.rect(surf,c5,(cx+dx-1,cy+16,2,5))
        # Nariz
        pygame.draw.polygon(surf,c3,[(cx,cy+22),(cx-4,cy+14),(cx+4,cy+14)])
        # Cockpit blindado
        pygame.draw.ellipse(surf,GLASS,(cx-4,cy-2,8,7))
        pygame.draw.ellipse(surf,_bright(GLASS,50),(cx-2,cy-1,4,4))
        # Motores triplos
        for dx in [-10, 0, 10]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-18),3)
            pygame.draw.circle(surf,dim(ENG,0.2),(cx+dx,cy-18),5,1)


# ── Desenho de 10 bosses únicos ────────────────────────────────────────────────
def draw_boss(surf, cx, cy, col, hp, btype, flash=0):
    c  = (220,220,220) if flash>0 else col
    c0=dim(c,0.12); c1=dim(c,0.20); c2=dim(c,0.38); c3=dim(c,0.62); c4=c
    c5=_bright(c,50)
    GLASS=(50,90,200); FLAME=(200,100,20); RED=(220,60,40)
    t = pygame.time.get_ticks()
    glow = _bright(FLAME,60) if (t//80)%2 else FLAME
    pulse = 0.5+0.5*math.sin(t*0.004)
    cx, cy = int(cx), int(cy)
    maxhp = 300 + btype * 50

    if btype == 0:   # Asa-delta — porta-aviões alado
        pygame.draw.polygon(surf,c0,[(cx,cy+42),(cx-46,cy+20),(cx-92,cy),(cx-64,cy-32),(cx-30,cy-40),(cx,cy-28),(cx+30,cy-40),(cx+64,cy-32),(cx+92,cy),(cx+46,cy+20)])
        pygame.draw.polygon(surf,c1,[(cx,cy+38),(cx-42,cy+18),(cx-86,cy),(cx-60,cy-28),(cx-28,cy-36),(cx,cy-25),(cx+28,cy-36),(cx+60,cy-28),(cx+86,cy),(cx+42,cy+18)])
        pygame.draw.polygon(surf,c2,[(cx,cy+28),(cx-28,cy+10),(cx-62,cy-4),(cx-44,cy-22),(cx-20,cy-30),(cx,cy-20),(cx+20,cy-30),(cx+44,cy-22),(cx+62,cy-4),(cx+28,cy+10)])
        pygame.draw.polygon(surf,c4,[(cx,cy+38),(cx-42,cy+18),(cx-86,cy),(cx-60,cy-28),(cx-28,cy-36),(cx,cy-25),(cx+28,cy-36),(cx+60,cy-28),(cx+86,cy),(cx+42,cy+18)],1)
        pygame.draw.rect(surf,c2,(cx-14,cy-22,28,48)); pygame.draw.rect(surf,c4,(cx-14,cy-22,28,48),1)
        pygame.draw.line(surf,c5,(cx,cy-20),(cx,cy+24),1)
        for dx in [-86, 86]:
            pygame.draw.rect(surf,c3,(cx+dx-3,cy+2,6,14)); pygame.draw.rect(surf,c5,(cx+dx-1,cy+14,2,6))
            pygame.draw.circle(surf,glow,(cx+dx,cy+2),4)
        for dx in [-60,-38,-18,18,38,60]:
            pygame.draw.line(surf,c3,(cx+dx,cy+10),(cx+dx//2,cy-12),1)
        for dx in [-36,-12,12,36]:
            pygame.draw.rect(surf,c0,(cx+dx-7,cy+4,14,10)); pygame.draw.rect(surf,c3,(cx+dx-7,cy+4,14,10),1)
        pygame.draw.rect(surf,c2,(cx-8,cy-26,16,10)); pygame.draw.rect(surf,GLASS,(cx-6,cy-25,12,8))
        pygame.draw.rect(surf,_bright(GLASS,60),(cx-3,cy-24,7,5))
        pygame.draw.line(surf,c4,(cx,cy-26),(cx-16,cy-36),1); pygame.draw.line(surf,c4,(cx,cy-26),(cx+12,cy-34),1)
        pygame.draw.circle(surf,c5,(cx-16,cy-36),2)
        for dx in [-22,-8,8,22]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-36),5); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+dx,cy-36),8,1)
        for dx in [-44,44]: pygame.draw.circle(surf,glow,(cx+dx,cy-20),4)
        pygame.draw.polygon(surf,c3,[(cx,cy+42),(cx-8,cy+28),(cx+8,cy+28)])
        pygame.draw.rect(surf,c3,(cx-5,cy+26,10,16)); pygame.draw.rect(surf,c5,(cx-2,cy+40,4,6))

    elif btype == 1: # Caranguejo — cruzador orgânico
        pygame.draw.ellipse(surf,c0,(cx-62,cy-30,124,60))
        pygame.draw.ellipse(surf,c1,(cx-58,cy-28,116,56))
        pygame.draw.ellipse(surf,c2,(cx-42,cy-18,84,36))
        pygame.draw.ellipse(surf,c4,(cx-58,cy-28,116,56),1)
        pygame.draw.line(surf,c5,(cx-38,cy),(cx+38,cy),1)
        for sx,ex1,ey1,ex2,ey2,ex3,ey3 in [
                (-58,-84,cy-22,-96,cy+5,-106,cy+28),
                (58,84,cy-22,96,cy+5,106,cy+28)]:
            pygame.draw.line(surf,c2,(cx+sx,cy),(cx+ex1,ey1),4)
            pygame.draw.line(surf,c4,(cx+sx,cy),(cx+ex1,ey1),1)
            pygame.draw.line(surf,c2,(cx+ex1,ey1),(cx+ex2,ey2),4)
            pygame.draw.line(surf,c4,(cx+ex1,ey1),(cx+ex2,ey2),1)
            pygame.draw.line(surf,c2,(cx+ex2,ey2),(cx+ex3,ey3),3)
            pygame.draw.line(surf,c4,(cx+ex2,ey2),(cx+ex3,ey3),1)
            pygame.draw.circle(surf,c3,(cx+ex3,ey3),9); pygame.draw.circle(surf,c5,(cx+ex3,ey3),4)
            pygame.draw.circle(surf,c4,(cx+ex3,ey3),9,1)
        for sx,ey in [(-50,cy+22),(-34,cy+28),(34,cy+28),(50,cy+22)]:
            nx=cx+sx+(8 if sx>0 else -8)
            pygame.draw.line(surf,c2,(cx+sx,cy+16),(nx,ey),2); pygame.draw.circle(surf,c3,(nx,ey),4)
        for ox in [-18, 0, 18]:
            r2=11 if ox==0 else 8; r3=7 if ox==0 else 5; r4=4 if ox==0 else 2
            pygame.draw.circle(surf,c1,(cx+ox,cy-4),r2); pygame.draw.circle(surf,RED,(cx+ox,cy-4),r3)
            pygame.draw.circle(surf,_bright(RED,60),(cx+ox,cy-4),r4); pygame.draw.circle(surf,c4,(cx+ox,cy-4),r2,1)
        for dx in [-28,-14,0,14,28]:
            pygame.draw.rect(surf,c3,(cx+dx-3,cy+24,6,10)); pygame.draw.rect(surf,c5,(cx+dx-1,cy+32,2,5))
        for dx in [-24,-8,8,24]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-28),4); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+dx,cy-28),6,1)
        for ox in [-24,0,24]:
            pygame.draw.line(surf,c4,(cx+ox,cy-28),(cx+ox+int(ox*0.3),cy-42),1)
            pygame.draw.circle(surf,glow,(cx+ox+int(ox*0.3),cy-42),3)

    elif btype == 2: # Canhoneira — fragata pesada
        pygame.draw.polygon(surf,c0,[(cx,cy+34),(cx-54,cy+16),(cx-62,cy-10),(cx-38,cy-30),(cx+38,cy-30),(cx+62,cy-10),(cx+54,cy+16)])
        pygame.draw.polygon(surf,c1,[(cx,cy+28),(cx-48,cy+14),(cx-56,cy-8),(cx-34,cy-26),(cx+34,cy-26),(cx+56,cy-8),(cx+48,cy+14)])
        pygame.draw.polygon(surf,c2,[(cx,cy+18),(cx-28,cy+8),(cx-32,cy-4),(cx-20,cy-16),(cx+20,cy-16),(cx+32,cy-4),(cx+28,cy+8)])
        pygame.draw.polygon(surf,c4,[(cx,cy+28),(cx-48,cy+14),(cx-56,cy-8),(cx-34,cy-26),(cx+34,cy-26),(cx+56,cy-8),(cx+48,cy+14)],1)
        for dx in [-56, 56]:
            pygame.draw.ellipse(surf,c1,(cx+dx-18,cy-13,36,28))
            pygame.draw.ellipse(surf,c2,(cx+dx-12,cy-9,24,18))
            pygame.draw.ellipse(surf,c4,(cx+dx-18,cy-13,36,28),1)
            for dy in [-5, 5]:
                pygame.draw.rect(surf,c3,(cx+dx-3,cy+dy+12,6,14)); pygame.draw.rect(surf,c5,(cx+dx-1,cy+dy+24,2,6))
        pygame.draw.rect(surf,c2,(cx-20,cy-22,40,16)); pygame.draw.rect(surf,c4,(cx-20,cy-22,40,16),1)
        pygame.draw.rect(surf,c3,(cx-10,cy-32,20,12)); pygame.draw.rect(surf,GLASS,(cx-8,cy-31,16,10))
        pygame.draw.rect(surf,_bright(GLASS,60),(cx-5,cy-30,10,7))
        pygame.draw.rect(surf,c3,(cx-4,cy+26,8,16)); pygame.draw.rect(surf,c5,(cx-2,cy+40,4,6))
        for dx in [-28,28]:
            pygame.draw.rect(surf,c3,(cx+dx-2,cy+22,5,12)); pygame.draw.rect(surf,c5,(cx+dx-1,cy+32,3,5))
        for dx in [-28,-10,10,28]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-28),5); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+dx,cy-28),7,1)
        for dy in [-6,6]:
            pygame.draw.line(surf,c3,(cx-42,cy+dy),(cx-28,cy+dy+8),1)
            pygame.draw.line(surf,c3,(cx+42,cy+dy),(cx+28,cy+dy+8),1)
        for dx in [-14, 14]:
            pygame.draw.circle(surf,RED,(cx+dx,cy),5); pygame.draw.circle(surf,_bright(RED,40),(cx+dx,cy),2)

    elif btype == 3: # Dreadnought — fortaleza espacial
        pygame.draw.rect(surf,c0,(cx-78,cy-38,156,76))
        pygame.draw.rect(surf,c1,(cx-74,cy-36,148,68))
        pygame.draw.rect(surf,c2,(cx-56,cy-22,112,42))
        pygame.draw.rect(surf,c4,(cx-74,cy-36,148,68),1)
        for dy in [-18,0,18]: pygame.draw.line(surf,c3,(cx-74,cy+dy),(cx+74,cy+dy),1)
        for dx in [-38,0,38]: pygame.draw.line(surf,c3,(cx+dx,cy-36),(cx+dx,cy+36),1)
        for dx in [-55,-33,-11,11,33,55]:
            pygame.draw.rect(surf,c2,(cx+dx-6,cy-50,12,16)); pygame.draw.rect(surf,c4,(cx+dx-6,cy-50,12,16),1)
            pygame.draw.rect(surf,c3,(cx+dx-3,cy-54,6,8)); pygame.draw.rect(surf,c5,(cx+dx-1,cy-57,2,6))
        for dx in [-55,-33,-11,11,33,55]:
            pygame.draw.rect(surf,c3,(cx+dx-3,cy+36,6,14)); pygame.draw.rect(surf,c5,(cx+dx-1,cy+48,2,6))
        for bx2 in [cx-82, cx+74]:
            pygame.draw.rect(surf,c2,(bx2,cy-14,12,26)); pygame.draw.rect(surf,c4,(bx2,cy-14,12,26),1)
        pygame.draw.rect(surf,c2,(cx-36,cy-36,72,10)); pygame.draw.rect(surf,c4,(cx-36,cy-36,72,10),1)
        pygame.draw.rect(surf,c3,(cx-22,cy-36,44,18)); pygame.draw.rect(surf,GLASS,(cx-18,cy-35,36,14))
        pygame.draw.rect(surf,_bright(GLASS,50),(cx-12,cy-34,24,9))
        for dx in [-46,-24,-4,4,24,46]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-36),5); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+dx,cy-36),8,1)
        pygame.draw.circle(surf,RED,(cx,cy),11); pygame.draw.circle(surf,_bright(RED,60),(cx,cy),6)
        pygame.draw.circle(surf,c4,(cx,cy),11,1)
        for dy in [-24,0,24]:
            for bx3 in [cx-74, cx+66]:
                pygame.draw.rect(surf,c2,(bx3,cy+dy-5,10,10)); pygame.draw.rect(surf,c4,(bx3,cy+dy-5,10,10),1)
        pygame.draw.line(surf,c4,(cx,cy-36),(cx,cy-54),1)
        pygame.draw.line(surf,c4,(cx-12,cy-48),(cx+12,cy-48),1)

    elif btype == 4: # Fantasma — caçador esguio
        body4=[(cx,cy+66),(cx-10,cy+28),(cx-16,cy),(cx-13,cy-38),(cx,cy-60),(cx+13,cy-38),(cx+16,cy),(cx+10,cy+28)]
        pygame.draw.polygon(surf,c0,body4)
        pygame.draw.polygon(surf,c1,[(cx,cy+62),(cx-8,cy+26),(cx-13,cy-2),(cx-11,cy-36),(cx,cy-56),(cx+11,cy-36),(cx+13,cy-2),(cx+8,cy+26)])
        pygame.draw.polygon(surf,c2,[(cx,cy+50),(cx-5,cy+18),(cx-8,cy-2),(cx-6,cy-28),(cx,cy-44),(cx+6,cy-28),(cx+8,cy-2),(cx+5,cy+18)])
        pygame.draw.polygon(surf,c4,body4,1)
        pygame.draw.polygon(surf,c1,[(cx-16,cy-6),(cx-56,cy-24),(cx-48,cy+2),(cx-16,cy+12)])
        pygame.draw.polygon(surf,c1,[(cx+16,cy-6),(cx+56,cy-24),(cx+48,cy+2),(cx+16,cy+12)])
        pygame.draw.polygon(surf,c2,[(cx-13,cy-4),(cx-40,cy-18),(cx-34,cy),(cx-13,cy+9)])
        pygame.draw.polygon(surf,c2,[(cx+13,cy-4),(cx+40,cy-18),(cx+34,cy),(cx+13,cy+9)])
        pygame.draw.polygon(surf,dim(c1,0.7),[(cx-13,cy-30),(cx-42,cy-44),(cx-36,cy-24),(cx-13,cy-22)])
        pygame.draw.polygon(surf,dim(c1,0.7),[(cx+13,cy-30),(cx+42,cy-44),(cx+36,cy-24),(cx+13,cy-22)])
        for dx in [-10, 10]:
            pygame.draw.ellipse(surf,c1,(cx+dx-5,cy-62,10,10))
            pygame.draw.circle(surf,glow,(cx+dx,cy-62),4)
        for dx in [-16,16]: pygame.draw.circle(surf,dim(glow,0.5),(cx+dx,cy-46),3)
        pygame.draw.ellipse(surf,dim(GLASS,0.6),(cx-8,cy-22,16,13))
        pygame.draw.ellipse(surf,GLASS,(cx-6,cy-20,12,10))
        pygame.draw.circle(surf,RED,(cx,cy-15),4); pygame.draw.circle(surf,_bright(RED,80),(cx,cy-15),2)
        pygame.draw.line(surf,c3,(cx,cy-56),(cx,cy+62),1)
        pygame.draw.line(surf,c5,(cx,cy-30),(cx,cy+20),1)
        pygame.draw.polygon(surf,c5,[(cx,cy+66),(cx-4,cy+52),(cx+4,cy+52)])
        for dx in [-30,30]:
            pygame.draw.line(surf,c3,(cx+dx,cy-16),(cx+dx,cy+4),1)
            pygame.draw.circle(surf,glow,(cx+dx,cy-16),3)

    elif btype == 5: # Cristal — entidade hexagonal
        r=60
        pts_outer=[(cx+int(r*math.cos(math.pi/3*i-math.pi/2)),cy+int(r*math.sin(math.pi/3*i-math.pi/2))) for i in range(6)]
        pts_inner=[(cx+int(r*0.54*math.cos(math.pi/3*i-math.pi/2)),cy+int(r*0.54*math.sin(math.pi/3*i-math.pi/2))) for i in range(6)]
        rot_off=(t%4000)/4000.0*2*math.pi
        for i in range(12):
            a=2*math.pi*i/12+rot_off
            rx2=cx+int((r+16)*math.cos(a)); ry2=cy+int((r+16)*math.sin(a))
            pygame.draw.circle(surf,c3,(rx2,ry2),4); pygame.draw.circle(surf,c5,(rx2,ry2),2)
        pygame.draw.polygon(surf,c0,[(x+3,y+3) for x,y in pts_outer])
        pygame.draw.polygon(surf,c1,pts_outer)
        pygame.draw.polygon(surf,c2,pts_inner)
        for i in range(6):
            a1=math.pi/3*i-math.pi/2; a2=math.pi/3*(i+1)-math.pi/2
            ax=cx+int(r*0.54*math.cos(a1)); ay=cy+int(r*0.54*math.sin(a1))
            bx2=cx+int(r*0.54*math.cos(a2)); by2=cy+int(r*0.54*math.sin(a2))
            ox=cx+int((r+24)*math.cos((a1+a2)/2)); oy=cy+int((r+24)*math.sin((a1+a2)/2))
            pygame.draw.polygon(surf,c2,[(ax,ay),(ox,oy),(bx2,by2)])
            pygame.draw.polygon(surf,c4,[(ax,ay),(ox,oy),(bx2,by2)],1)
        pygame.draw.polygon(surf,c4,pts_outer,2)
        for i in range(6):
            a=math.pi/3*i-math.pi/2
            x1=cx+int(r*0.54*math.cos(a)); y1=cy+int(r*0.54*math.sin(a))
            x2=cx+int(r*math.cos(a)); y2=cy+int(r*math.sin(a))
            pygame.draw.line(surf,c4,(x1,y1),(x2,y2),1)
        for i in range(6):
            a=math.pi/3*i-math.pi/2+math.pi/6
            mx2=cx+int(r*0.76*math.cos(a)); my2=cy+int(r*0.76*math.sin(a))
            pygame.draw.polygon(surf,c3,
                [(mx2+int(5*math.cos(a-math.pi/2)),my2+int(5*math.sin(a-math.pi/2))),
                 (mx2+int(12*math.cos(a)),my2+int(12*math.sin(a))),
                 (mx2+int(5*math.cos(a+math.pi/2)),my2+int(5*math.sin(a+math.pi/2)))])
        nr=18+int(pulse*5)
        pygame.draw.circle(surf,c1,(cx,cy),nr+4); pygame.draw.circle(surf,c2,(cx,cy),nr)
        pygame.draw.circle(surf,c4,(cx,cy),nr-4); pygame.draw.circle(surf,c5,(cx,cy),nr-8)
        pygame.draw.circle(surf,_bright(c4,90),(cx,cy),5)
        for i in range(6):
            a=math.pi/3*i-math.pi/2+math.pi/6
            vx=cx+int((r+2)*math.cos(a)); vy=cy+int((r+2)*math.sin(a))
            pygame.draw.circle(surf,glow,(vx,vy),4)

    elif btype == 6: # Nave-mãe — disco colossal
        pygame.draw.ellipse(surf,c0,(cx-92,cy-28,184,58))
        pygame.draw.ellipse(surf,c1,(cx-88,cy-26,176,52))
        pygame.draw.ellipse(surf,c2,(cx-64,cy-18,128,36))
        pygame.draw.ellipse(surf,c4,(cx-88,cy-26,176,52),2)
        pygame.draw.ellipse(surf,c2,(cx-40,cy-44,80,36))
        pygame.draw.ellipse(surf,GLASS,(cx-30,cy-42,60,30))
        pygame.draw.ellipse(surf,_bright(GLASS,50),(cx-18,cy-40,36,18))
        pygame.draw.ellipse(surf,c4,(cx-40,cy-44,80,36),1)
        for i in range(12):
            a=2*math.pi*i/12
            wx=cx+int(74*math.cos(a)); wy=cy+int(18*math.sin(a))
            pygame.draw.circle(surf,c3,(wx,wy),5); pygame.draw.circle(surf,c5,(wx,wy),2)
            if i%3==0:
                nx=cx+int(82*math.cos(a)); ny=cy+int(20*math.sin(a))
                pygame.draw.line(surf,c4,(wx,wy),(nx,ny),2)
        for i in range(8):
            a=math.pi/4*i
            pygame.draw.line(surf,c3,(cx,cy),(cx+int(64*math.cos(a)),cy+int(16*math.sin(a))),1)
        for dx in [-50,-28,-8,8,28,50]:
            pygame.draw.circle(surf,glow,(cx+dx,cy+26),5); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+dx,cy+26),7,1)
        for dx in [-30,-10,10,30]:
            pygame.draw.rect(surf,c3,(cx+dx-3,cy+24,6,12)); pygame.draw.rect(surf,c5,(cx+dx-1,cy+34,2,5))
        pygame.draw.circle(surf,RED,(cx,cy),10); pygame.draw.circle(surf,_bright(RED,60),(cx,cy),5)
        pygame.draw.circle(surf,c4,(cx,cy),10,1)
        for i in range(8):
            a=2*math.pi*i/8
            ex2=cx+int(44*math.cos(a)); ey2=cy+int(10*math.sin(a))
            pygame.draw.circle(surf,dim(c3,0.6),(ex2,ey2),3)

    elif btype == 7: # Tempestade — caçador angular agressivo
        pygame.draw.polygon(surf,c0,[(cx,cy-64),(cx+36,cy-18),(cx+74,cy+8),(cx+44,cy+36),(cx,cy+24),(cx-44,cy+36),(cx-74,cy+8),(cx-36,cy-18)])
        pygame.draw.polygon(surf,c1,[(cx,cy-60),(cx+32,cy-14),(cx+70,cy+6),(cx+40,cy+32),(cx,cy+20),(cx-40,cy+32),(cx-70,cy+6),(cx-32,cy-14)])
        pygame.draw.polygon(surf,c2,[(cx,cy-46),(cx+20,cy-10),(cx+46,cy+2),(cx+24,cy+20),(cx,cy+14),(cx-24,cy+20),(cx-46,cy+2),(cx-20,cy-10)])
        pygame.draw.polygon(surf,c4,[(cx,cy-60),(cx+32,cy-14),(cx+70,cy+6),(cx+40,cy+32),(cx,cy+20),(cx-40,cy+32),(cx-70,cy+6),(cx-32,cy-14)],1)
        pygame.draw.rect(surf,c2,(cx-14,cy-54,28,72)); pygame.draw.rect(surf,c4,(cx-14,cy-54,28,72),1)
        pygame.draw.line(surf,c5,(cx,cy-52),(cx,cy+16),1)
        pygame.draw.line(surf,c4,(cx,cy-60),(cx+70,cy+6),1); pygame.draw.line(surf,c4,(cx,cy-60),(cx-70,cy+6),1)
        for dx,gy in [(-70,cy+6),(70,cy+6),(-48,cy+32),(48,cy+32)]:
            pygame.draw.rect(surf,c3,(cx+dx-3,gy,7,14)); pygame.draw.rect(surf,c5,(cx+dx-1,gy+12,3,6))
            pygame.draw.circle(surf,glow,(cx+dx,gy),4)
        pygame.draw.polygon(surf,c3,[(cx,cy+38),(cx-8,cy+22),(cx+8,cy+22)])
        pygame.draw.polygon(surf,c5,[(cx,cy+40),(cx-3,cy+28),(cx+3,cy+28)])
        pygame.draw.ellipse(surf,GLASS,(cx-9,cy-44,18,16))
        pygame.draw.ellipse(surf,_bright(GLASS,70),(cx-6,cy-42,12,11))
        for mx,gy in [(-28,cy-22),(28,cy-22),(-46,cy-10),(46,cy-10),(-62,cy+2),(62,cy+2)]:
            pygame.draw.circle(surf,glow,(cx+mx,gy),4); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+mx,gy),6,1)
        pygame.draw.circle(surf,RED,(cx,cy-12),8); pygame.draw.circle(surf,_bright(RED,60),(cx,cy-12),4)

    elif btype == 8: # Titã — encouraçado colossal
        pygame.draw.rect(surf,c0,(cx-90,cy-46,180,92))
        pygame.draw.rect(surf,c1,(cx-86,cy-44,172,84))
        pygame.draw.rect(surf,c2,(cx-62,cy-28,124,54))
        pygame.draw.rect(surf,c4,(cx-86,cy-44,172,84),1)
        pygame.draw.rect(surf,c1,(cx-58,cy-64,116,22)); pygame.draw.rect(surf,c2,(cx-48,cy-64,96,18))
        pygame.draw.rect(surf,c4,(cx-58,cy-64,116,22),1)
        for dx in [-56,-38,-20,-5,5,20,38,56]:
            pygame.draw.rect(surf,c2,(cx+dx-5,cy-78,10,16)); pygame.draw.rect(surf,c4,(cx+dx-5,cy-78,10,16),1)
            pygame.draw.rect(surf,c3,(cx+dx-2,cy-80,5,8)); pygame.draw.rect(surf,c5,(cx+dx-1,cy-82,3,6))
        for dy in [-28,0,28]:
            for bx3 in [cx-90, cx+82]:
                pygame.draw.rect(surf,c2,(bx3,cy+dy-5,10,10)); pygame.draw.rect(surf,c4,(bx3,cy+dy-5,10,10),1)
                pygame.draw.circle(surf,glow,(bx3+5,cy+dy),3)
        for dx in [-54,-28,-6,6,28,54]:
            pygame.draw.rect(surf,c3,(cx+dx-4,cy+44,8,18)); pygame.draw.rect(surf,c5,(cx+dx-2,cy+60,4,6))
        for dy in [-28,0,28]: pygame.draw.line(surf,c3,(cx-86,cy+dy),(cx+86,cy+dy),1)
        for dx in [-42,0,42]: pygame.draw.line(surf,c3,(cx+dx,cy-44),(cx+dx,cy+44),1)
        pygame.draw.rect(surf,c3,(cx-26,cy-44,52,20)); pygame.draw.rect(surf,GLASS,(cx-22,cy-43,44,16))
        pygame.draw.rect(surf,_bright(GLASS,50),(cx-16,cy-42,32,11))
        pygame.draw.circle(surf,RED,(cx,cy),14); pygame.draw.circle(surf,_bright(RED,70),(cx,cy),8)
        pygame.draw.circle(surf,_bright(RED,120),(cx,cy),3); pygame.draw.circle(surf,c4,(cx,cy),14,1)
        for dx in [-50,-26,-4,4,26,50]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-44),6); pygame.draw.circle(surf,dim(FLAME,0.15),(cx+dx,cy-44),9,1)
        for dx in [-70, 70]:
            pygame.draw.circle(surf,glow,(cx+dx,cy-30),5); pygame.draw.circle(surf,dim(FLAME,0.2),(cx+dx,cy-30),7,1)
        for dx,dy in [(-86,-44),(86,-44),(-86,44),(86,44)]:
            pygame.draw.rect(surf,c3,(cx+dx-4,cy+dy-4,8,8)); pygame.draw.circle(surf,c5,(cx+dx,cy+dy),3)
        pygame.draw.line(surf,c4,(cx,cy-64),(cx,cy-84),1)
        pygame.draw.line(surf,c4,(cx-18,cy-78),(cx+18,cy-78),1)
        pygame.draw.circle(surf,c5,(cx,cy-84),2)

    else:            # Soberano Zero — entidade dimensional final
        pulse2 = 5 if (t//180)%2 else 0
        outer_r=90; inner_r=54
        rot_a=(t%8000)/8000.0*2*math.pi
        # Aura de glow
        for gr in range(110,60,-10):
            ga=int(10*(1-gr/110.0)*(0.5+0.5*math.sin(t*0.003+gr*0.05)))
            gs=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
            pygame.draw.circle(gs,(*col,ga),(gr,gr),gr)
            surf.blit(gs,(cx-gr,cy-gr))
        # Tentáculos de energia
        for i in range(0,20,2):
            a=math.pi/10*i-math.pi/2
            tx=cx+int(outer_r*math.cos(a)); ty=cy+int(outer_r*math.sin(a))
            tlen=28+pulse2
            tend_x=cx+int((outer_r+tlen)*math.cos(a)); tend_y=cy+int((outer_r+tlen)*math.sin(a))
            tc=RED if (t//100)%2 else _bright(RED,40)
            pygame.draw.line(surf,tc,(tx,ty),(tend_x,tend_y),2)
            pygame.draw.circle(surf,tc,(tend_x,tend_y),5)
        # Estrela de 10 pontas
        star_pts=[]
        for i in range(20):
            a=math.pi/10*i-math.pi/2
            r=outer_r if i%2==0 else inner_r
            star_pts.append((cx+int(r*math.cos(a)),cy+int(r*math.sin(a))))
        pygame.draw.polygon(surf,c0,[(x+3,y+3) for x,y in star_pts])
        pygame.draw.polygon(surf,c1,star_pts)
        inner_fill=[]
        for i in range(20):
            a=math.pi/10*i-math.pi/2
            r2=inner_r-12 if i%2==0 else int(inner_r*0.52)
            inner_fill.append((cx+int(r2*math.cos(a)),cy+int(r2*math.sin(a))))
        pygame.draw.polygon(surf,c2,inner_fill)
        pygame.draw.polygon(surf,c4,star_pts,2)
        # Anel externo rotativo (8 módulos)
        ring_r=outer_r+22
        for i in range(8):
            a=2*math.pi*i/8+rot_a
            rx2=cx+int(ring_r*math.cos(a)); ry2=cy+int(ring_r*math.sin(a))
            pygame.draw.circle(surf,c2,(rx2,ry2),7); pygame.draw.circle(surf,c5,(rx2,ry2),3)
            pygame.draw.circle(surf,c4,(rx2,ry2),7,1)
            bx2=cx+int(outer_r*0.88*math.cos(a)); by2=cy+int(outer_r*0.88*math.sin(a))
            pygame.draw.line(surf,c3,(bx2,by2),(rx2,ry2),1)
        # Anéis concêntricos de armas
        for r in [30,46,62,78]: pygame.draw.circle(surf,c3,(cx,cy),r,1)
        # Turrets externas
        for i in range(0,20,2):
            a=math.pi/10*i-math.pi/2
            tx=cx+int(outer_r*math.cos(a)); ty=cy+int(outer_r*math.sin(a))
            pygame.draw.circle(surf,c3,(tx,ty),7); pygame.draw.circle(surf,c5,(tx,ty),3)
        # Canhões internos
        for i in range(1,20,2):
            a=math.pi/10*i-math.pi/2
            tx=cx+int(inner_r*math.cos(a)); ty=cy+int(inner_r*math.sin(a))
            pygame.draw.circle(surf,c2,(tx,ty),5); pygame.draw.circle(surf,c3,(tx,ty),2)
        # Raios de energia
        for i in range(0,20,2):
            a=math.pi/10*i-math.pi/2
            ex=cx+int(outer_r*math.cos(a)); ey=cy+int(outer_r*math.sin(a))
            pygame.draw.line(surf,c3,(cx,cy),(ex,ey),1)
        for i in range(1,20,2):
            a=math.pi/10*i-math.pi/2
            ex=cx+int(inner_r*math.cos(a)); ey=cy+int(inner_r*math.sin(a))
            pygame.draw.line(surf,dim(c3,0.5),(cx,cy),(ex,ey),1)
        # Núcleo multi-camadas
        pr=20+pulse2; cr=int(24+pulse*5)
        pygame.draw.circle(surf,c0,(cx,cy),cr+6)
        pygame.draw.circle(surf,dim(RED,0.4),(cx,cy),cr+2)
        pygame.draw.circle(surf,RED,(cx,cy),pr)
        pygame.draw.circle(surf,_bright(RED,80),(cx,cy),pr-7)
        pygame.draw.circle(surf,_bright(RED,140),(cx,cy),pr-13)
        pygame.draw.circle(surf,(255,210,210),(cx,cy),pr-17)
        pygame.draw.circle(surf,c4,(cx,cy),pr,1)
        # Olho central
        pygame.draw.ellipse(surf,(0,0,0),(cx-10,cy-5,20,10))
        pygame.draw.ellipse(surf,_bright(RED,70),(cx-10,cy-5,20,10),1)
        pygame.draw.circle(surf,_bright(RED,100),(cx,cy),3)
        # Motores espectrais
        for i in range(5):
            a=2*math.pi*i/5-math.pi/2
            mx=cx+int(66*math.cos(a)); my=cy+int(66*math.sin(a))
            pygame.draw.circle(surf,glow,(mx,my),6); pygame.draw.circle(surf,dim(FLAME,0.2),(mx,my),9,1)

    # Barra de HP universal
    tops = [70, 65, 65, 110, 100, 95, 80, 100, 120, 115]
    bar_w=220; bar_x=cx-110; bar_y=cy-tops[min(btype,9)]
    pygame.draw.rect(surf,dim(c,0.22),(bar_x,bar_y,bar_w,8))
    fill=max(0,int(bar_w*hp/maxhp))
    bar_col=(220,50,50) if flash==0 and hp<maxhp*0.3 else c
    pygame.draw.rect(surf,bar_col,(bar_x,bar_y,fill,8))
    pygame.draw.rect(surf,c4,(bar_x,bar_y,bar_w,8),1)


# ── Asteroides e projéteis ────────────────────────────────────────────────────
def draw_asteroid(surf, cx, cy, radius, col, seed):
    rng = random.Random(seed)
    npts = 12
    pts = []
    for i in range(npts):
        a = 2*math.pi*i/npts + rng.uniform(-0.20, 0.20)
        r = radius * rng.uniform(0.60, 1.0)
        pts.append((int(cx + r*math.cos(a)), int(cy + r*math.sin(a))))
    # Sombra
    pygame.draw.polygon(surf,dim(col,0.08),[(x+2,y+2) for x,y in pts])
    # Corpo
    pygame.draw.polygon(surf,dim(col,0.18),pts)
    # Face iluminada
    lit = pts[:npts//2+1]
    if len(lit) >= 3:
        pygame.draw.polygon(surf,dim(col,0.30),lit)
    pygame.draw.polygon(surf,dim(col,0.55),pts,1)
    # Crateras
    r1 = max(2, int(radius*0.28))
    cr1x = cx + rng.randint(-int(radius*0.3), int(radius*0.3))
    cr1y = cy + rng.randint(-int(radius*0.3), int(radius*0.3))
    pygame.draw.circle(surf,dim(col,0.08),(cr1x,cr1y),r1)
    pygame.draw.circle(surf,dim(col,0.40),(cr1x,cr1y),r1,1)
    if radius > 8:
        r2 = max(2, int(radius*0.18))
        cr2x = cx + rng.randint(-int(radius*0.4), int(radius*0.4))
        cr2y = cy + rng.randint(-int(radius*0.4), int(radius*0.4))
        pygame.draw.circle(surf,dim(col,0.08),(cr2x,cr2y),r2)
        pygame.draw.circle(surf,dim(col,0.35),(cr2x,cr2y),r2,1)

def draw_bullet_player(surf, bx, by, col):
    bx, by = int(bx), int(by)
    pygame.draw.rect(surf,dim(col,0.3),(bx-3,by-8,6,16))
    pygame.draw.rect(surf,col,(bx-2,by-7,4,14))
    pygame.draw.rect(surf,_bright(col,80),(bx-1,by-6,2,12))
    pygame.draw.circle(surf,_bright(col,120),(bx,by-7),2)

def draw_bullet_enemy(surf, bx, by, col):
    bx, by = int(bx), int(by)
    pygame.draw.circle(surf,dim(col,0.3),(bx,by),6)
    pygame.draw.circle(surf,col,(bx,by),4)
    pygame.draw.circle(surf,_bright(col,80),(bx,by),2)

def draw_powerup(surf, cx, cy, ptype, col, bp_col):
    cx, cy = int(cx), int(cy)
    t = pygame.time.get_ticks()
    pulse = 2 if (t//200)%2 else 0
    if ptype == 0:
        c=col; r=10+pulse
        pts=[(cx,cy-r),(cx+r,cy),(cx,cy+r),(cx-r,cy)]
        pygame.draw.polygon(surf,dim(c,0.25),pts)
        pygame.draw.polygon(surf,c,pts,1)
        pygame.draw.polygon(surf,_bright(c,60),[(cx,cy-r//2),(cx+r//2,cy),(cx,cy+r//2),(cx-r//2,cy)])
        pygame.draw.circle(surf,_bright(c,100),(cx,cy),3)
    else:
        c=bp_col; r=10+pulse
        pygame.draw.circle(surf,dim(c,0.20),(cx,cy),r+2)
        pygame.draw.circle(surf,dim(c,0.40),(cx,cy),r)
        pygame.draw.circle(surf,c,(cx,cy),r,1)
        pygame.draw.circle(surf,_bright(c,80),(cx,cy),r-3,1)
        pygame.draw.circle(surf,_bright(c,120),(cx,cy),4)
        pygame.draw.line(surf,_bright(c,80),(cx,cy-r+3),(cx,cy+r-3),1)
        pygame.draw.line(surf,_bright(c,80),(cx-r+3,cy),(cx+r-3,cy),1)


# ── Classe principal ───────────────────────────────────────────────────────────
class Game:
    MENU            = 0
    PLAYING         = 1
    BOSS_WARN       = 2
    PHASE_CLEAR     = 3
    CONTINUE_PROMPT = 4
    GAME_OVER       = 5
    VICTORY         = 6
    INTRO_CS        = 7

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
                    self._start_intro_cs()
                elif self.state == self.INTRO_CS and k in (pygame.K_RETURN, pygame.K_SPACE):
                    self._init_game(); self.state = self.PLAYING
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

        if self.state == self.INTRO_CS:
            self._update_intro_cs()
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
                hw=[92,62,62,78,18,62,90,74,90,95][min(self.boss['btype'],9)]
                hh=[42,32,36,46,66,62,30,66,48,95][min(self.boss['btype'],9)]
                bossrect=pygame.Rect(int(self.boss['x'])-hw,int(self.boss['y'])-hh,hw*2,hh*2)
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
        elif self.state==self.INTRO_CS:         self._draw_intro_cs()
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
        if self.bomb_flash > 0:
            bf = self.bomb_flash                    # 50 → 0
            p  = 1.0 - bf / 50.0                   # 0.0 → 1.0
            c2 = pal['ui']
            WHITE = (255, 255, 220)
            vfx = pygame.Surface((W, H), pygame.SRCALPHA)

            # Flash branco inicial (primeiros 25% da animação)
            if p < 0.25:
                fa = int(240 * (1.0 - p/0.25))
                pygame.draw.rect(vfx, (*WHITE, fa), (0, 0, W, H))

            # Overlay colorido que dissolve
            oa = int(155 * max(0.0, 1.0 - p*1.6))
            if oa > 0:
                pygame.draw.rect(vfx, (*c2, oa), (0, 0, W, H))

            # Onda de choque principal (expande até cobrir a tela)
            max_r = int(math.sqrt(W*W + H*H)//2) + 50
            rr = int(p * max_r)
            rw = max(2, int(16*(1.0-p)))
            ra = int(255 * max(0.0, 1.0 - p*1.1))
            if rr > 2 and ra > 0:
                pygame.draw.circle(vfx, (*c2, ra), (W//2, H//2), rr, rw)
                # Anel interno (segunda onda, levemente atrasada)
                r2 = max(0, rr - 65)
                if r2 > 2:
                    pygame.draw.circle(vfx, (*WHITE, ra*2//3),
                        (W//2, H//2), r2, max(1, rw//2))
                # Terceiro anel tênue
                r3 = max(0, rr - 130)
                if r3 > 2:
                    pygame.draw.circle(vfx, (*c2, ra//3),
                        (W//2, H//2), r3, max(1, rw//3))

            # Explosões secundárias espalhadas (posições fixas por seed)
            rng_b = random.Random(1337)
            for _ in range(16):
                bex = rng_b.randint(55, W-55)
                bey = rng_b.randint(55, H-55)
                df  = math.hypot(bex-W//2, bey-H//2) / max_r
                lp  = max(0.0, min(1.0, (p - df*0.22) / 0.78))
                if lp > 0.0:
                    br = max(1, int(lp * 42))
                    ba = int(210 * (1.0 - lp))
                    if ba > 0:
                        pygame.draw.circle(vfx, (*c2, ba), (bex, bey), br)
                        if br > 7:
                            pygame.draw.circle(vfx, (*WHITE, min(255, ba+60)),
                                (bex, bey), br//3)

            # Linhas de energia radiando do centro (primeiros 55%)
            if p < 0.55:
                lp2 = p / 0.55
                lr  = int(lp2 * int(W * 0.82))
                la  = int(170 * (1.0 - lp2))
                if la > 0 and lr > 10:
                    for deg in range(0, 360, 20):
                        ang = math.radians(deg + p*80)
                        lx  = W//2 + int(lr * math.cos(ang))
                        ly  = H//2 + int(lr * math.sin(ang))
                        sr2 = max(0, lr - int(lr*0.72))
                        sx2 = W//2 + int(sr2 * math.cos(ang))
                        sy2 = H//2 + int(sr2 * math.sin(ang))
                        pygame.draw.line(vfx, (*c2, la//2), (sx2,sy2), (lx,ly), 1)

            # Brilho nas bordas (sobe e desce com seno)
            ev = int(95 * math.sin(math.pi * p))
            if ev > 0:
                for er in range(55, 0, -12):
                    ea = max(0, ev * er // 55)
                    pygame.draw.rect(vfx, (*c2, ea), (0,    0,    er,  H))
                    pygame.draw.rect(vfx, (*c2, ea), (W-er, 0,    er,  H))
                    pygame.draw.rect(vfx, (*c2, ea), (0,    0,    W,   er))
                    pygame.draw.rect(vfx, (*c2, ea), (0,    H-er, W,   er))

            screen.blit(vfx, (0, 0))

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
        pal = self.pal; c = pal['ui']; t = pygame.time.get_ticks()
        tf = t / 1000.0

        # ── Boss decorativo no fundo (muito escuro) ───────────────────────────
        draw_boss(screen, 662, H//2+20, dim(c, 0.07), 500, 9, 0)

        # ── Nave do jogador em destaque (esquerda) ────────────────────────────
        shx = 188; shy = H//2 + 15 + int(10*math.sin(tf*1.5))
        for gr in range(28, 2, -5):
            ga = max(0, int(44*(28-gr)//26))
            gs2 = pygame.Surface((gr*2, gr*2), pygame.SRCALPHA)
            pygame.draw.circle(gs2, (*c, ga), (gr, gr), gr)
            screen.blit(gs2, (shx-gr, shy-gr))
        fh = 14 + int(8*math.sin(tf*10))
        fc2 = (255,160,30) if int(tf*14)%2 else (255,220,60)
        pygame.draw.polygon(screen, fc2,
            [(shx-4,shy+22),(shx+4,shy+22),(shx,shy+22+fh)])
        for i in range(4):
            ly = shy - 55 - i*55
            if ly > 5:
                pygame.draw.rect(screen, dim(c, max(0.2, 0.58-i*0.12)),
                    (shx-1, ly, 2, 38))
        draw_player(screen, shx, shy, c)

        # ── Inimigos em formação (direita → esquerda) ─────────────────────────
        for row, etype in enumerate([1, 0, 3]):
            ry = 104 + row * 46
            for col in range(5):
                ex = W+80 - ((t//4 + row*170 + col*155) % (W+350))
                ey = ry + int(4*math.sin(tf*1.1 + col*0.85 + row*1.3))
                draw_enemy(screen, ex, ey, dim(pal['ec'], 0.24), etype)

        # ── Painel do título ──────────────────────────────────────────────────
        pw = 494; ph2 = 122; px2 = W//2+52; py2 = 14
        ps = pygame.Surface((pw, ph2), pygame.SRCALPHA)
        ps.fill((0, 0, 0, 158))
        screen.blit(ps, (px2-pw//2, py2))
        pygame.draw.line(screen, c, (px2-pw//2, py2), (px2+pw//2, py2), 1)
        pygame.draw.line(screen, c, (px2-pw//2, py2+ph2), (px2+pw//2, py2+ph2), 1)
        pygame.draw.line(screen, dim(c,0.38), (px2-pw//2, py2), (px2-pw//2, py2+ph2), 1)
        pygame.draw.line(screen, dim(c,0.38), (px2+pw//2, py2), (px2+pw//2, py2+ph2), 1)
        for bx3, dx3 in [(px2-pw//2, 1),(px2+pw//2, -1)]:
            for by3, dy3 in [(py2, 1),(py2+ph2, -1)]:
                pygame.draw.line(screen, c,
                    (bx3+dx3*2, by3+dy3*2),(bx3+dx3*18, by3+dy3*2), 1)
                pygame.draw.line(screen, c,
                    (bx3+dx3*2, by3+dy3*2),(bx3+dx3*2, by3+dy3*14), 1)
        glow_text(screen, "PULSAR", _font_lg, c, px2, py2+8, center=True)
        pygame.draw.line(screen, dim(c,0.28),
            (px2-205, py2+50),(px2+205, py2+50), 1)
        glow_text(screen, "DIMENSÃO  SETOR  ZERO", _font_md,
            dim(c,0.88), px2, py2+54, center=True)
        glow_text(screen, "A ÚLTIMA FREQUÊNCIA DE RESISTÊNCIA", _font_sm,
            dim(c,0.42), px2, py2+82, center=True)
        glow_text(screen, "UMA NOVA DIMENSÃO.", _font_sm,
            dim(c,0.62), px2, py2+100, center=True)

        # ── Features do jogo ──────────────────────────────────────────────────
        feats = [("10","SETORES"),("10","CHEFES"),("10","TIPOS"),("5","ARMAS")]
        for i,(num,lbl) in enumerate(feats):
            fx2 = W//2-103+i*82; fy2 = 150
            pygame.draw.rect(screen, dim(c,0.10), (fx2-25, fy2, 50, 38))
            pygame.draw.rect(screen, dim(c,0.30), (fx2-25, fy2, 50, 38), 1)
            glow_text(screen, num,  _font_md, c,          fx2, fy2+2,  center=True)
            glow_text(screen, lbl,  _font_sm, dim(c,0.5), fx2, fy2+24, center=True)

        # ── Painel de controles (direita) ─────────────────────────────────────
        cpx = W//2+102; cpy = H//2-52
        pygame.draw.rect(screen, dim(c,0.08), (cpx, cpy, 192, 110))
        pygame.draw.rect(screen, dim(c,0.28), (cpx, cpy, 192, 110), 1)
        glow_text(screen, "CONTROLES", _font_sm, dim(c,0.62),
            cpx+96, cpy+6, center=True)
        pygame.draw.line(screen, dim(c,0.2),
            (cpx+6, cpy+22),(cpx+186, cpy+22), 1)
        ctrls = [("SETAS/WASD","MOVER"),("ESPAÇO/Z","ATIRAR"),
                 ("B / X","BOMBA"),("ESC","SAIR")]
        for i,(k,v) in enumerate(ctrls):
            glow_text(screen, f"{k} — {v}", _font_sm, dim(c,0.47),
                cpx+96, cpy+28+i*18, center=True)

        # ── ENTER pulsante ────────────────────────────────────────────────────
        ent_c = c if int(tf*1.7)%2==0 else dim(c,0.28)
        glow_text(screen,
            "►  PRESSIONE  ENTER  PARA  INICIAR  ◄",
            _font_md, ent_c, W//2, H-124, center=True)

        # ── Separador + highscore ─────────────────────────────────────────────
        pygame.draw.line(screen, dim(c,0.24), (30, H-102), (W-30, H-102), 1)
        for mx in [30, W//2, W-30]:
            pygame.draw.circle(screen, dim(c,0.58), (mx, H-102), 3)
        glow_text(screen, f"RECORDE: {self.highscore:07d}",
            _font_sm, dim(c,0.62), W//2, H-94, center=True)

        # ── Barra de setores colorida ─────────────────────────────────────────
        ph_y = H - 64
        glow_text(screen, "SETORES:", _font_sm, dim(c,0.35), 52, ph_y+4, center=True)
        for i, ph in enumerate(PHASES):
            fx3 = 102 + i*62; ph_c = ph['ui']
            filled = i < self.phase_idx
            pygame.draw.rect(screen, dim(ph_c,0.16), (fx3-19, ph_y, 38, 20))
            pygame.draw.rect(screen,
                dim(ph_c, 0.55 if filled else 0.18), (fx3-19, ph_y, 38, 20), 1)
            glow_text(screen, f"{i+1:02d}", _font_sm,
                ph_c if filled else dim(ph_c,0.28), fx3, ph_y+2, center=True)

        # ── Decorações de canto ────────────────────────────────────────────────
        cs = 18
        for bx4, dx4 in [(8,1),(W-8,-1)]:
            for by4, dy4 in [(8,1),(H-8,-1)]:
                pygame.draw.line(screen, dim(c,0.38),
                    (bx4,by4),(bx4+dx4*cs,by4), 1)
                pygame.draw.line(screen, dim(c,0.38),
                    (bx4,by4),(bx4,by4+dy4*cs), 1)

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

    # ── Cutscene de abertura ──────────────────────────────────────────────────
    def _start_intro_cs(self):
        self.state       = self.INTRO_CS
        self.cs_t        = 0.0
        self.cs_scene    = 0
        self.cs_particles= []
        self.cs_exploded = False

    def _update_intro_cs(self):
        dt = 1.0 / FPS
        self.cs_t += dt
        t = self.cs_t
        BREAKS = [6.0, 12.0, 18.0, 26.0, 35.0, 44.0, 52.0, 58.0]
        self.cs_scene = len([b for b in BREAKS if t >= b])

        for p in self.cs_particles:
            p[0]+=p[2]; p[1]+=p[3]; p[4]-=dt
        self.cs_particles=[p for p in self.cs_particles if p[4]>0]

        update_stars(self.stars)

        if self.cs_scene == 2:
            local_t = t - 12.0
            if random.random()<0.18 and local_t<4.8:
                spawn_particles(self.cs_particles, 280, H//2,
                                PHASES[0]['ui'], n=6, spd=3)
            if local_t>4.6 and not self.cs_exploded:
                self.cs_exploded=True
                spawn_particles(self.cs_particles, 280, H//2,
                                (255,200,50), n=45, spd=8)
        elif self.cs_scene==3 and not self.cs_exploded:
            self.cs_exploded=True
            spawn_particles(self.cs_particles, 280, H//2,
                            (255,180,30), n=55, spd=7)

        if t >= 63.0:
            self._init_game()
            self.state = self.PLAYING

    def _draw_intro_cs(self):
        t     = self.cs_t
        scene = self.cs_scene
        c_cyan  = PHASES[9]['ui']
        c_green = PHASES[0]['ui']

        screen.fill((0, 0, 6))
        draw_stars(screen, self.stars, PHASES[9]['star'])

        def draw_L1(cx, cy, col, inv=0):
            if inv and (inv//6)%2==0: return
            cx,cy=int(cx),int(cy)
            pts=[(cx,cy-16),(cx-14,cy+9),(cx-7,cy+3),
                 (cx,cy+11),(cx+7,cy+3),(cx+14,cy+9)]
            pygame.draw.polygon(screen,dim(col,0.35),pts)
            pygame.draw.polygon(screen,col,pts,1)
            pygame.draw.circle(screen,col,(cx,cy-4),4)
            pygame.draw.circle(screen,dim(col,0.25),(cx,cy-4),3)

        def draw_pts():
            for p in self.cs_particles:
                a=p[4]/p[5]; col2=dim(p[6],a)
                sx,sy=int(p[0]),int(p[1])
                if 0<=sx<W and 0<=sy<H: screen.set_at((sx,sy),col2)

        def fade_in(text, font, col, x, y, start_abs, dur=1.2, center=True):
            dt2=t-start_abs
            if dt2<=0: return
            alpha=min(255,int(dt2/dur*255))
            s=pygame.Surface((W,H),pygame.SRCALPHA)
            img=font.render(text,True,col)
            rx=x-img.get_width()//2 if center else x
            s.blit(img,(rx,y)); s.set_alpha(alpha)
            screen.blit(s,(0,0))

        def draw_lom(cx, cy, col, scale=1.0, arm_raise=0.0):
            cx,cy=int(cx),int(cy)
            s=scale
            # legs
            pygame.draw.rect(screen,dim(col,0.5),(cx-int(7*s),cy+int(14*s),int(6*s),int(14*s)))
            pygame.draw.rect(screen,dim(col,0.5),(cx+int(2*s),cy+int(14*s),int(6*s),int(14*s)))
            pygame.draw.rect(screen,col,(cx-int(7*s),cy+int(14*s),int(6*s),int(14*s)),1)
            pygame.draw.rect(screen,col,(cx+int(2*s),cy+int(14*s),int(6*s),int(14*s)),1)
            # boots
            pygame.draw.rect(screen,dim(col,0.3),(cx-int(9*s),cy+int(26*s),int(8*s),int(5*s)))
            pygame.draw.rect(screen,dim(col,0.3),(cx+int(1*s),cy+int(26*s),int(8*s),int(5*s)))
            # torso
            pygame.draw.rect(screen,dim(col,0.4),(cx-int(10*s),cy,int(20*s),int(16*s)))
            pygame.draw.rect(screen,col,(cx-int(10*s),cy,int(20*s),int(16*s)),1)
            # chest insignia
            pygame.draw.line(screen,_bright(col,40),(cx-int(5*s),cy+int(4*s)),(cx+int(5*s),cy+int(4*s)),1)
            pygame.draw.line(screen,_bright(col,40),(cx,cy+int(2*s)),(cx,cy+int(10*s)),1)
            # shoulder pads
            pygame.draw.ellipse(screen,_bright(col,20),(cx-int(14*s),cy-int(2*s),int(8*s),int(6*s)))
            pygame.draw.ellipse(screen,col,(cx+int(6*s),cy-int(2*s),int(8*s),int(6*s)))
            # arms
            arm_off=int(arm_raise*12*s)
            pygame.draw.line(screen,col,(cx-int(10*s),cy+int(2*s)),(cx-int(16*s),cy+int(12*s)-arm_off),2)
            pygame.draw.line(screen,col,(cx+int(10*s),cy+int(2*s)),(cx+int(16*s),cy+int(12*s)),2)
            # helmet
            pygame.draw.circle(screen,dim(col,0.45),(cx,cy-int(8*s)),int(10*s))
            pygame.draw.circle(screen,col,(cx,cy-int(8*s)),int(10*s),1)
            # visor
            pygame.draw.ellipse(screen,dim(col,0.12),(cx-int(6*s),cy-int(13*s),int(12*s),int(7*s)))
            pygame.draw.ellipse(screen,_bright(col,30),(cx-int(6*s),cy-int(13*s),int(12*s),int(7*s)),1)
            # glare on visor
            pygame.draw.line(screen,_bright(col,80),(cx-int(4*s),cy-int(12*s)),(cx-int(2*s),cy-int(10*s)),1)
            # antenna
            pygame.draw.line(screen,col,(cx+int(6*s),cy-int(17*s)),(cx+int(6*s),cy-int(23*s)),1)
            pygame.draw.circle(screen,_bright(col,60),(cx+int(6*s),cy-int(23*s)),2)

        def draw_survivor(cx, cy, col, stype=0):
            cx,cy=int(cx),int(cy)
            # base body — smaller than lom
            pygame.draw.rect(screen,dim(col,0.4),(cx-5,cy,10,13))
            pygame.draw.rect(screen,col,(cx-5,cy,10,13),1)
            pygame.draw.rect(screen,dim(col,0.4),(cx-4,cy+13,3,10))
            pygame.draw.rect(screen,dim(col,0.4),(cx+1,cy+13,3,10))
            pygame.draw.circle(screen,dim(col,0.5),(cx,cy-6),6)
            pygame.draw.circle(screen,col,(cx,cy-6),6,1)
            if stype==0:
                # leader: cape + chest emblem
                cape=[(cx-5,cy),(cx-12,cy+18),(cx+5,cy+18),(cx+5,cy)]
                pygame.draw.polygon(screen,dim(col,0.25),cape)
                pygame.draw.polygon(screen,dim(col,0.5),cape,1)
                pygame.draw.circle(screen,_bright(col,50),(cx,cy+4),3)
                # pointing right arm
                pygame.draw.line(screen,col,(cx+5,cy+2),(cx+18,cy-4),2)
                pygame.draw.line(screen,col,(cx-5,cy+2),(cx-8,cy+10),2)
            elif stype==1:
                # soldier: shoulder armor + rifle
                pygame.draw.rect(screen,_bright(col,20),(cx-9,cy-2,6,5))
                pygame.draw.rect(screen,_bright(col,20),(cx+3,cy-2,6,5))
                # rifle
                pygame.draw.line(screen,_bright(col,30),(cx+5,cy+2),(cx+22,cy+1),3)
                pygame.draw.rect(screen,col,(cx+14,cy-1,4,6),1)
                pygame.draw.line(screen,col,(cx-5,cy+2),(cx-9,cy+10),2)
            elif stype==2:
                # engineer: device + hologram
                pygame.draw.rect(screen,_bright(col,20),(cx+5,cy+2,10,8))
                pygame.draw.rect(screen,col,(cx+5,cy+2,10,8),1)
                # hologram beam above device
                hcol=_bright(col,60)
                hs=pygame.Surface((20,20),pygame.SRCALPHA)
                pygame.draw.polygon(hs,(*hcol,80),[(10,0),(2,18),(18,18)])
                screen.blit(hs,(cx+0,cy-18))
                pygame.draw.line(screen,col,(cx-5,cy+2),(cx-9,cy+10),2)

        def draw_ruins_bg():
            # far sky gradient — dark green
            for ry in range(0,H//2,2):
                a=int(8*(ry/(H//2)))
                pygame.draw.line(screen,(0,a,0),(0,ry),(W,ry))
            # distant broken arch
            pygame.draw.arc(screen,(0,40,20),
                (80,H//2-80,120,100),0,math.pi,3)
            pygame.draw.line(screen,(0,40,20),(80,H//2+20),(80,H//2+60),3)
            pygame.draw.line(screen,(0,40,20),(200,H//2+20),(200,H//2+60),3)
            # mid collapsed walls
            wall_segs=[
                (0,H-160,50,H-120),(50,H-120,110,H-145),
                (110,H-145,180,H-100),(180,H-100,260,H-140),
                (260,H-140,340,H-90),(340,H-90,420,H-130),
                (420,H-130,500,H-95),(500,H-95,580,H-120),
                (580,H-120,640,H-100),(640,H-100,W,H-130),
            ]
            for x1,y1,x2,y2 in wall_segs:
                pygame.draw.line(screen,(0,55,15),(x1,y1),(x2,y2),4)
                pygame.draw.line(screen,(0,30,8),(x1,y1),(x2,y2),2)
            # broken beam
            pygame.draw.line(screen,(0,40,10),(160,H-160),(340,H-100),3)
            # floor rubble
            for rx,rw,rh2 in [(50,30,8),(120,18,5),(200,40,10),
                              (350,22,6),(450,35,9),(560,20,7),(680,28,8)]:
                pygame.draw.ellipse(screen,(0,35,10),(rx,H-rh2*2,rw,rh2))
                pygame.draw.ellipse(screen,(0,50,15),(rx,H-rh2*2,rw,rh2),1)
            # damaged terminal
            pygame.draw.rect(screen,(0,30,10),(580,H-160,40,60))
            pygame.draw.rect(screen,(0,55,20),(580,H-160,40,60),1)
            pygame.draw.rect(screen,(0,15,5),(583,H-155,34,30))
            pygame.draw.line(screen,(0,80,30),(583,H-147),(590,H-130),1)
            # ground lines
            for gy in range(H-55,H,12):
                pygame.draw.line(screen,(0,40,12),(0,gy),(W,gy),1)

        SCENE_STARTS = [0,6,12,18,26,35,44,52,58]
        local_t = t - SCENE_STARTS[min(scene,8)]

        if scene == 0:
            pr = int(50+math.sin(local_t*4)*5)
            for pw in range(22,2,-3):
                pa=max(0,int(58*(1-pw/24.0)*(0.6+0.4*math.sin(local_t*5))))
                ps2=pygame.Surface((W,H),pygame.SRCALPHA)
                pygame.draw.circle(ps2,(*c_cyan,pa),(120,H//2),pr+pw,pw)
                screen.blit(ps2,(0,0))
            pygame.draw.circle(screen,(0,0,0),(120,H//2),pr)
            pygame.draw.circle(screen,c_cyan,(120,H//2),pr,2)
            emerge_x=int(120+min(1.0,local_t/5.5)*145)
            if emerge_x>125: draw_L1(emerge_x,H//2,c_green)
            fade_in("ANO 2247 — COORDENADAS: DESCONHECIDAS",
                    _font_sm,c_cyan,W//2,H//2+80,1.0)
            fade_in("DIMENSÃO: DESCONHECIDA",
                    _font_md,c_cyan,W//2,H//2+108,2.5)

        elif scene == 1:
            lx=int(280+math.sin(local_t*0.6)*12)
            ly=int(H//2+math.sin(local_t*0.9)*8)
            draw_L1(lx,ly,c_green)
            for i,etype in enumerate([0,1,3]):
                prog=max(0.0,min(1.0,(local_t-i*1.0)/2.5))
                ex=int(W-80-i*80-(1.0-prog)*200)
                ey=int(H//2-65+i*55)
                if prog>0.05:
                    draw_enemy(screen,ex,ey,PHASES[5]['ec'],etype)
            fade_in("ESTA DIMENSÃO É DIFERENTE",
                    _font_md,c_cyan,W//2,H//2+70,6.5)
            fade_in("ARMAS QUE A HUMANIDADE JAMAIS VISLUMBROU",
                    _font_sm,dim(c_cyan,0.6),W//2,H//2+100,8.5)

        elif scene == 2:
            for i,etype in enumerate([0,1,3]):
                ex=int(W-80-i*80); ey=int(H//2-65+i*55)
                draw_enemy(screen,ex,ey,PHASES[5]['ec'],etype)
                bprog=(local_t*1.8+i*0.6)%1.0
                bx=int(ex+(280-ex)*bprog); by=int(ey+(H//2-ey)*bprog)
                if 0<=bx<W and 0<=by<H:
                    pygame.draw.circle(screen,PHASES[5]['be'],(bx,by),4)
                    pygame.draw.circle(screen,
                        _bright(PHASES[5]['be'],60),(bx,by),2)
            if local_t<5.0:
                draw_L1(280,H//2,c_green,
                        1 if int(local_t*12)%3==0 else 0)
            draw_pts()
            fade_in("A L1 FOI DESTRUÍDA EM QUESTÃO DE SEGUNDOS",
                    _font_sm,(255,80,80),W//2,H//2+90,13.5)

        elif scene == 3:
            # L.O.M ejeta em cápsula elaborada com entrada atmosférica
            draw_pts()
            if local_t<0.4:
                fa=int((1-local_t/0.4)*220)
                fs=pygame.Surface((W,H),pygame.SRCALPHA)
                fs.fill((255,200,60,fa)); screen.blit(fs,(0,0))
            cap_prog=min(1.0,local_t/6.5)
            cap_x=int(W//2+math.sin(local_t*2.2)*30)
            cap_y=int(50+cap_prog*(H-180))
            # heat shield glow at bottom of pod
            if cap_prog>0.3:
                heat=min(1.0,(cap_prog-0.3)/0.4)
                for gr in range(28,4,-4):
                    ga=int(60*heat*(1-gr/30.0))
                    hs2=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
                    hcol=(255,int(100+80*heat),0)
                    pygame.draw.ellipse(hs2,(*hcol,ga),(0,gr//2,gr*2,gr))
                    screen.blit(hs2,(cap_x-gr,cap_y+18))
            # plasma trail
            for ti in range(1,6):
                ty=cap_y-ti*14
                ta=max(0,int(130-ti*25))
                tc=(int(200-ti*20),int(60+ti*10),0)
                trail=pygame.Surface((12,8),pygame.SRCALPHA)
                pygame.draw.ellipse(trail,(*tc,ta),(0,0,12,8))
                screen.blit(trail,(cap_x-6,ty))
            # escape pod hull
            pod_col=_bright(c_cyan,10)
            pygame.draw.polygon(screen,dim(pod_col,0.5),
                [(cap_x,cap_y-22),(cap_x-12,cap_y-8),
                 (cap_x-12,cap_y+10),(cap_x+12,cap_y+10),(cap_x+12,cap_y-8)])
            pygame.draw.polygon(screen,pod_col,
                [(cap_x,cap_y-22),(cap_x-12,cap_y-8),
                 (cap_x-12,cap_y+10),(cap_x+12,cap_y+10),(cap_x+12,cap_y-8)],1)
            # nose cone
            pygame.draw.polygon(screen,_bright(pod_col,30),
                [(cap_x,cap_y-28),(cap_x-5,cap_y-22),(cap_x+5,cap_y-22)])
            # side fins
            pygame.draw.polygon(screen,dim(pod_col,0.4),
                [(cap_x-12,cap_y+4),(cap_x-20,cap_y+14),(cap_x-12,cap_y+10)])
            pygame.draw.polygon(screen,dim(pod_col,0.4),
                [(cap_x+12,cap_y+4),(cap_x+20,cap_y+14),(cap_x+12,cap_y+10)])
            pygame.draw.polygon(screen,pod_col,
                [(cap_x-12,cap_y+4),(cap_x-20,cap_y+14),(cap_x-12,cap_y+10)],1)
            pygame.draw.polygon(screen,pod_col,
                [(cap_x+12,cap_y+4),(cap_x+20,cap_y+14),(cap_x+12,cap_y+10)],1)
            # window with L.O.M face silhouette
            pygame.draw.ellipse(screen,dim(c_cyan,0.15),
                                (cap_x-7,cap_y-8,14,14))
            pygame.draw.ellipse(screen,c_cyan,
                                (cap_x-7,cap_y-8,14,14),1)
            pygame.draw.circle(screen,dim(c_cyan,0.35),(cap_x,cap_y-2),4)
            pygame.draw.line(screen,dim(c_cyan,0.3),(cap_x,cap_y+2),(cap_x,cap_y+4),1)
            # glare on window
            pygame.draw.line(screen,_bright(c_cyan,60),
                             (cap_x-4,cap_y-7),(cap_x-2,cap_y-5),1)
            # thruster exhaust at bottom
            fh=10+int(math.sin(local_t*18)*5)
            fc_ex=(255,140,20) if int(local_t*14)%2 else (255,220,40)
            pygame.draw.polygon(screen,fc_ex,
                [(cap_x-4,cap_y+10),(cap_x+4,cap_y+10),(cap_x,cap_y+10+fh)])
            # atmospheric entry orange haze bottom
            atm=pygame.Surface((W,80),pygame.SRCALPHA)
            for ah in range(80,0,-4):
                aa=int(40*cap_prog*(1-ah/80.0))
                pygame.draw.line(atm,(255,80,0,aa),(0,80-ah),(W,80-ah))
            screen.blit(atm,(0,H-80))
            # L.O.M lands (local_t > 6)
            if cap_prog>=1.0:
                lom_land_y=H-180-31
                draw_lom(cap_x,lom_land_y,c_cyan,scale=1.0)
            fade_in("L.O.M EJETOU NO ÚLTIMO INSTANTE",
                    _font_md,c_cyan,W//2,80,1.2)
            fade_in("Cápsula de emergência — entrada atmosférica crítica",
                    _font_sm,dim(c_cyan,0.55),W//2,118,2.8)
            fade_in("Destino: superfície desconhecida...",
                    _font_sm,dim(c_cyan,0.4),W//2,148,4.5)

        elif scene == 4:
            # Ruínas elaboradas + L.O.M encontra sobreviventes
            draw_ruins_bg()
            lom_x=min(240,int(80+local_t*26))
            lom_y=H-170
            draw_lom(lom_x,lom_y,c_cyan,scale=1.1)
            # survivors emerge from rubble right side
            surv_positions=[(520,H-170),(570,H-170),(620,H-170)]
            surv_colors=[c_cyan,dim(c_cyan,0.8),dim(c_cyan,0.65)]
            surv_types=[0,1,2]
            for i,(sx,sy) in enumerate(surv_positions):
                prog2=min(1.0,max(0.0,(local_t-i*0.8)/1.5))
                if prog2>0:
                    sy2=int(sy+(1-prog2)*40)
                    draw_survivor(sx,sy2,surv_colors[i],surv_types[i])
                    # torch/light from each survivor
                    torch_col=_bright(surv_colors[i],40)
                    for gr in range(20,4,-4):
                        ga=int(25*(1-gr/22.0)*prog2)
                        ts=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
                        pygame.draw.circle(ts,(*torch_col,ga),(gr,gr),gr)
                        screen.blit(ts,(sx-gr,sy2-gr-10))
            # dust particles on ground
            for dx2 in range(0,W,80):
                dp=int(math.sin(t*2+dx2*0.05)*3)
                pygame.draw.circle(screen,dim(c_cyan,0.15),(dx2,H-8+dp),2)
            fade_in("OS ÚLTIMOS SOBREVIVENTES DA RESISTÊNCIA",
                    _font_md,c_cyan,W//2,40,26.5)
            fade_in("Eles encontraram L.O.M entre os escombros.",
                    _font_sm,dim(c_cyan,0.6),W//2,78,28.0)
            fade_in("Setor por setor, a dimensão havia caído.",
                    _font_sm,dim(c_cyan,0.5),W//2,106,30.0)
            fade_in("'Não sobrou mais ninguém além de nós.'",
                    _font_sm,_bright(c_cyan,20),W//2,134,32.0)

        elif scene == 5:
            # Sobreviventes apresentam a LD7 ao L.O.M — hangar
            c_ld7=PHASES[0]['ui']
            # hangar ceiling beams
            for bx2 in range(0,W,100):
                pygame.draw.line(screen,dim(c_cyan,0.2),(bx2,0),(bx2,H//3),3)
                pygame.draw.line(screen,(0,30,15),(bx2,0),(bx2,H//3),1)
            pygame.draw.line(screen,dim(c_cyan,0.25),(0,H//3),(W,H//3),2)
            # floor grid
            for fx2 in range(0,W,60):
                pygame.draw.line(screen,dim(c_ld7,0.12),(fx2,H//3),(fx2,H),1)
            for fy2 in range(H//3,H,40):
                pygame.draw.line(screen,dim(c_ld7,0.12),(0,fy2),(W,fy2),1)
            # platform/pedestal for LD7
            pygame.draw.rect(screen,(0,50,20),(W//2-60,H//2+30,120,20))
            pygame.draw.rect(screen,dim(c_ld7,0.4),(W//2-60,H//2+30,120,20),1)
            pygame.draw.rect(screen,(0,40,15),(W//2-80,H//2+48,160,12))
            pygame.draw.rect(screen,dim(c_ld7,0.3),(W//2-80,H//2+48,160,12),1)
            # spotlight beams from ceiling onto LD7
            pulse_s=0.75+0.25*math.sin(local_t*2.5)
            for sbx,sbw in [(W//2-30,60),(W//2-50,100)]:
                sp_s=pygame.Surface((sbw,H//2+20),pygame.SRCALPHA)
                sa=int(22*pulse_s)
                pygame.draw.polygon(sp_s,(*c_ld7,sa),
                    [(sbw//2-4,0),(sbw//2+4,0),(sbw,H//2+20),(0,H//2+20)])
                screen.blit(sp_s,(sbx,0))
            # LD7 on pedestal with glow rings
            ld7_cx=W//2; ld7_cy=H//2+10
            for gr in range(55,8,-7):
                ga=max(0,int(40*(1-gr/55.0)*pulse_s))
                gs2=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
                pygame.draw.circle(gs2,(*c_ld7,ga),(gr,gr),gr)
                screen.blit(gs2,(ld7_cx-gr,ld7_cy-gr))
            draw_player(screen,ld7_cx,ld7_cy,c_ld7)
            # L.O.M on the left
            lom_prog=min(1.0,local_t/1.5)
            lom_px=int(160+lom_prog*40)
            draw_lom(lom_px,H//2+10,c_cyan,scale=1.1,arm_raise=min(1.0,max(0.0,local_t-3.0)/2.0))
            # 3 survivors on the right
            for i,(sx,stype) in enumerate([(580,0),(625,1),(665,2)]):
                sp=min(1.0,max(0.0,(local_t-i*0.5)/1.2))
                if sp>0:
                    sy2=int(H//2+10+(1-sp)*30)
                    draw_survivor(sx,sy2,dim(c_cyan,0.75+i*0.08),stype)
            # speech bubble from leader (right side)
            if local_t>4.0:
                bub_a=min(255,int((local_t-4.0)/1.2*255))
                bub_s=pygame.Surface((W,H),pygame.SRCALPHA)
                bub_x=460; bub_y=H//2-80; bub_w=220; bub_h=52
                pygame.draw.rect(bub_s,(0,0,0,180),(bub_x,bub_y,bub_w,bub_h),0,6)
                pygame.draw.rect(bub_s,(*c_ld7,200),(bub_x,bub_y,bub_w,bub_h),1,6)
                # tail pointing to leader
                pygame.draw.polygon(bub_s,(*c_ld7,160),
                    [(580,bub_y+bub_h),(572,bub_y+bub_h+12),(592,bub_y+bub_h)])
                bub_s.set_alpha(bub_a)
                screen.blit(bub_s,(0,0))
                fade_in("'Agora você tem uma chance.'",
                        _font_sm,c_ld7,bub_x+bub_w//2,bub_y+8,4.0,1.0)
                fade_in("'Uma. Não desperdice.'",
                        _font_sm,_bright(c_ld7,30),bub_x+bub_w//2,bub_y+28,5.2,1.0)
            fade_in("A LD7 — ÚNICA ARMA DESTA DIMENSÃO",
                    _font_md,c_ld7,W//2,22,35.5,1.0)
            fade_in("Construída em segredo. Nunca pilotada.",
                    _font_sm,dim(c_ld7,0.6),W//2,56,37.2,1.0)

        elif scene == 6:
            # Interior da cockpit da LD7
            GOLD=(220,150,0); CYAN_HUD=(0,210,230); RED_L=(180,20,20)
            prog=min(1.0,local_t/2.5)
            VP=(W//2,H//2-30)
            # perspective grid — blue lines to vanishing point
            grid_col=(0,30,int(90*prog))
            for gx2 in range(0,W+1,50):
                pygame.draw.line(screen,grid_col,(gx2,H),VP,1)
            for gy2 in range(VP[1],H,35):
                blend=int(80*prog*(gy2-VP[1])/(H-VP[1]))
                pygame.draw.line(screen,(0,0,blend),(0,gy2),(W,gy2),1)
            # red vertical center lines
            for rx2 in [W//2-3,W//2,W//2+3]:
                rc=max(0,int(RED_L[0]*prog))
                pygame.draw.line(screen,(rc,int(RED_L[1]*prog),int(RED_L[2]*prog)),
                                 (rx2,VP[1]),(rx2,H),1)
            # LEFT PANEL
            lp_x=0; lp_w=185; lp_a=int(220*prog)
            lp_s=pygame.Surface((lp_w,H),pygame.SRCALPHA)
            pygame.draw.rect(lp_s,(0,0,0,180),(0,0,lp_w,H))
            pygame.draw.rect(lp_s,(*GOLD,lp_a),(0,0,lp_w,H),1)
            pygame.draw.rect(lp_s,(*GOLD,lp_a),(4,4,lp_w-8,H-8),1)
            # FUEL label
            fuel_img=_font_sm.render("FUEL",True,GOLD)
            lp_s.blit(fuel_img,(8,10))
            for fi in range(4):
                fb=max(0.0,(prog-(fi*0.08)))
                fb=min(1.0,fb/0.6)
                fc_bar=(int(200*fb),int(40+60*(1-fb)),0)
                fw2=int((lp_w-20)*fb)
                pygame.draw.rect(lp_s,(20,20,20),(8,32+fi*14,lp_w-20,10))
                pygame.draw.rect(lp_s,fc_bar,(8,32+fi*14,fw2,10))
                pygame.draw.rect(lp_s,(*GOLD,100),(8,32+fi*14,lp_w-20,10),1)
            # circular gauge
            gcx=lp_w//2; gcy=120; gr2=28
            pygame.draw.circle(lp_s,(20,15,0),( gcx,gcy),gr2)
            pygame.draw.circle(lp_s,GOLD,(gcx,gcy),gr2,1)
            for gt in range(0,360,30):
                r=math.radians(gt)
                pygame.draw.line(lp_s,(*GOLD,120),
                    (int(gcx+gr2*0.85*math.cos(r)),int(gcy+gr2*0.85*math.sin(r))),
                    (int(gcx+gr2*math.cos(r)),int(gcy+gr2*math.sin(r))),1)
            needle_a=math.radians(-90+prog*200)
            pygame.draw.line(lp_s,(255,80,0),
                (gcx,gcy),
                (int(gcx+gr2*0.75*math.cos(needle_a)),
                 int(gcy+gr2*0.75*math.sin(needle_a))),2)
            num_img=_font_sm.render("60  84",True,GOLD)
            lp_s.blit(num_img,(8,152))
            # DAMAGE STATUS
            dmg_img=_font_sm.render("DAMAGE STATUS",True,(*GOLD,int(200*prog)))
            lp_s.blit(dmg_img,(4,175))
            # LD7 silhouette damage panel
            ld7_dmg_s=pygame.Surface((lp_w-16,60),pygame.SRCALPHA)
            ld7_dmg_s.fill((0,0,0,0))
            draw_player(ld7_dmg_s,(lp_w-16)//2,30,GOLD)
            ld7_dmg_s.set_alpha(int(200*prog))
            lp_s.blit(ld7_dmg_s,(8,192))
            lp_s.set_alpha(int(255*prog))
            screen.blit(lp_s,(lp_x,0))
            # RIGHT PANEL
            rp_x=W-185; rp_w=185
            rp_s=pygame.Surface((rp_w,H),pygame.SRCALPHA)
            pygame.draw.rect(rp_s,(0,0,0,180),(0,0,rp_w,H))
            pygame.draw.rect(rp_s,(*GOLD,lp_a),(0,0,rp_w,H),1)
            pygame.draw.rect(rp_s,(*GOLD,lp_a),(4,4,rp_w-8,H-8),1)
            nav_img=_font_sm.render("NAVIGATION",True,GOLD)
            rp_s.blit(nav_img,(8,10))
            # cyan circle + chevron
            ncx=rp_w//2; ncy=70; nr=36
            pygame.draw.circle(rp_s,(0,15,20),(ncx,ncy),nr)
            pygame.draw.circle(rp_s,CYAN_HUD,(ncx,ncy),nr,2)
            chevron=[(ncx,ncy-14),(ncx-10,ncy+2),(ncx-5,ncy+2),
                     (ncx-5,ncy+14),(ncx+5,ncy+14),(ncx+5,ncy+2),(ncx+10,ncy+2)]
            pygame.draw.polygon(rp_s,(*CYAN_HUD,int(220*prog)),chevron)
            # rotation ring
            ra=local_t*0.8
            pygame.draw.arc(rp_s,(*CYAN_HUD,int(180*prog)),
                (ncx-nr,ncy-nr,nr*2,nr*2),ra,ra+math.pi*1.4,2)
            # smaller circular display
            scx=rp_w//2; scy=148; sr=20
            pygame.draw.circle(rp_s,(0,10,15),(scx,scy),sr)
            pygame.draw.circle(rp_s,CYAN_HUD,(scx,scy),sr,1)
            pygame.draw.line(rp_s,CYAN_HUD,(scx,scy-sr+4),(scx,scy+sr-4),1)
            pygame.draw.line(rp_s,CYAN_HUD,(scx-sr+4,scy),(scx+sr-4,scy),1)
            # AMMO bars
            ammo_img=_font_sm.render("AMMO",True,GOLD)
            rp_s.blit(ammo_img,(8,178))
            for ai in range(6):
                ab=min(1.0,prog)
                abh=int(30*ab*(1.0-ai*0.06))
                ac=(int(50+170*ab),int(200*ab),0)
                pygame.draw.rect(rp_s,ac,(10+ai*22,210-abh,14,abh))
                pygame.draw.rect(rp_s,(*GOLD,100),(10+ai*22,178+2,14,32),1)
            rp_s.set_alpha(int(255*prog))
            screen.blit(rp_s,(rp_x,0))
            # BOTTOM CENTER bar
            bc_s=pygame.Surface((W,50),pygame.SRCALPHA)
            pygame.draw.rect(bc_s,(0,0,0,160),(0,0,W,50))
            pygame.draw.line(bc_s,(*GOLD,int(200*prog)),(0,0),(W,0),1)
            coords_img=_font_md.render("09 : 00 : 60",True,
                tuple(int(c*prog) for c in GOLD))
            bc_s.blit(coords_img,(W//2-coords_img.get_width()//2,10))
            bc_s.set_alpha(int(255*prog))
            screen.blit(bc_s,(0,H-50))
            # L.O.M silhouette in cockpit seat
            if prog>0.4:
                seat_a=min(1.0,(prog-0.4)/0.4)
                draw_lom(W//2,H-130,dim(GOLD,0.35*seat_a),scale=1.3)
            fade_in("SISTEMAS OPERACIONAIS",_font_md,GOLD,W//2,22,44.5,1.0)
            fade_in("LD7 — PRONTO PARA COMBATE",
                    _font_sm,CYAN_HUD,W//2,58,46.5,1.0)

        elif scene == 7:
            # LD7 revelada com glow
            c_ld7=PHASES[0]['ui']
            pulse=0.7+0.3*math.sin(local_t*3)
            for gr in range(80,8,-8):
                ga=max(0,int(50*(1-gr/80.0)*pulse))
                gs2=pygame.Surface((gr*2,gr*2),pygame.SRCALPHA)
                pygame.draw.circle(gs2,(*c_ld7,ga),(gr,gr),gr)
                screen.blit(gs2,(W//2-gr,H//2-gr))
            draw_player(screen,W//2,H//2,c_ld7)
            fade_in("A  LD7",_font_lg,c_ld7,W//2,H//2-100,52.5,1.0)
            fade_in("A ÚNICA ARMA DESSA DIMENSÃO",
                    _font_md,dim(c_ld7,0.75),W//2,H//2+60,54.0)
            fade_in("NUNCA TESTADA. NUNCA PILOTADA.",
                    _font_sm,dim(c_ld7,0.5),W//2,H//2+90,55.5)

        elif scene == 8:
            # LD7 decolando
            c_ld7=PHASES[0]['ui']
            ld7_y=int(H//2-local_t*34)
            ld7_x=W//2
            fh=18+int(math.sin(local_t*14)*8)
            fc3=(255,160,30) if int(local_t*14)%2 else (255,220,60)
            pygame.draw.polygon(screen,fc3,
                [(ld7_x-4,ld7_y+22),(ld7_x+4,ld7_y+22),(ld7_x,ld7_y+22+fh)])
            if ld7_y > -30: draw_player(screen,ld7_x,ld7_y,c_ld7)
            fade_in("NÃO HÁ REFORÇOS. NÃO HÁ PLANO B.",
                    _font_md,c_ld7,W//2,H//2+60,58.5)
            fade_in("SÓ EXISTE A LD7",
                    _font_lg,c_ld7,W//2,H//2+108,60.0)
            if local_t>2.5 and int(t*1.5)%2:
                glow_text(screen,"ENTER / SPACE — INICIAR",_font_sm,
                          dim(c_ld7,0.4),W//2,H-22,center=True)
            screen.blit(_scanline,(0,0))
            return

        if int(t*1.5)%2:
            glow_text(screen,"ENTER / SPACE — SALTAR",_font_sm,
                      dim(c_cyan,0.25),W//2,H-22,center=True)
        screen.blit(_scanline,(0,0))


# ── Entrada ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
