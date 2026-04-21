# -*- coding: utf-8 -*-
"""Captura screenshots de cada cena da cutscene de abertura."""
import os, sys, math, random
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.mixer.init()

_fake = type('S', (), {'play': lambda *a,**k: None, 'stop': lambda *a: None,
                       'set_volume': lambda *a: None})
pygame.mixer.Sound = lambda **k: _fake()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jogo

# Tempo no meio de cada cena para captura
CENAS = [
    (3.0,  "intro0_l1_portal.png"),
    (9.0,  "intro1_nova_dimensao.png"),
    (15.0, "intro2_l1_destruida.png"),
    (20.5, "intro3_ejecao.png"),
    (27.0, "intro4_sobreviventes.png"),
    (33.0, "intro5_ld7_revelada.png"),
    (39.5, "intro6_ld7_decola.png"),
]

SCENE_STARTS = [0, 6, 12, 18, 23, 30, 37]
BREAKS = [6.0, 12.0, 18.0, 23.0, 30.0, 37.0]

for tempo_alvo, nome_arquivo in CENAS:
    random.seed(42)
    g = jogo.Game.__new__(jogo.Game)
    g.highscore = jogo.load_hs()
    g.sfx = {}; g.music = None
    g.state = jogo.Game.MENU
    g._init_game()
    g._start_intro_cs()

    # Simula frames até o tempo alvo
    frames = int(tempo_alvo * jogo.FPS)
    random.seed(42)
    for _ in range(frames):
        g._update_intro_cs()

    # Força tempo exato
    g.cs_t = tempo_alvo
    g.cs_scene = len([b for b in BREAKS if tempo_alvo >= b])

    g._draw_intro_cs()
    pygame.image.save(jogo.screen, nome_arquivo)
    print(f"Salvo: {nome_arquivo}")

pygame.quit()
print("Concluído!")
