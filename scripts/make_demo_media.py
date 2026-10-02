"""Gera screenshots e GIF do front a partir do caso de demonstração (offline).

Uso: pip install playwright pillow gradio && python scripts/make_demo_media.py
Saída: docs/assets/*.png e docs/assets/demo.gif
"""
import sys, threading, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'docs'/'assets'; sys.path.insert(0,str(ROOT))
PORT=7871; W,H=1440,1000
STEPS=[  # (arquivo, aba a abrir, legenda)
    ('01-home','', 'Cole um alvo ou o texto da isca — tudo passivo por padrão'),
    ('02-graph','Grafo','Grafo de relações: evidência (contínua) vs. ligação proposta pela IA (tracejada)'),
    ('03-entities','Isca e IA','Regras BR + GLiNER: entidades derivadas, com método e confiança'),
    ('04-iocs','IOCs','Cada IOC com decisão: BLOCK, HUNT, MONITOR ou TAKEDOWN PREP'),
    ('05-timeline','Linha do tempo','Primeira e última observação por entidade, com fontes'),
    ('06-export','Exportar','STIX 2.1, MISP e Sigma prontos para o TIP/SIEM'),
]

def font(size,bold=False):
    for f in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if Path(f).exists(): return ImageFont.truetype(f,size)
    return ImageFont.load_default()

def caption(png,text,step,total):
    im=Image.open(png).convert('RGB'); bar=64
    canvas=Image.new('RGB',(im.width,im.height+bar),(11,13,16)); canvas.paste(im,(0,0))
    d=ImageDraw.Draw(canvas)
    d.rectangle([0,im.height,im.width,im.height+1],fill=(37,42,50))
    d.text((28,im.height+20),text,font=font(22,True),fill=(242,244,247))
    tag=f'{step}/{total}  ·  TROPEIRO INTEL'; w=d.textlength(tag,font=font(15))
    d.text((im.width-w-28,im.height+24),tag,font=font(15),fill=(232,163,61))
    return canvas

def _chrome():
    """Usa o Chromium já instalado se o Playwright não achar o dele (override: CHROME_PATH)."""
    import os, glob
    return os.environ.get('CHROME_PATH') or next(iter(sorted(glob.glob('/opt/pw-browsers/chromium-*/chrome-linux/chrome'))),None)

def main():
    from playwright.sync_api import sync_playwright
    from tropeiro.frontend.app import build_app
    app=build_app()
    app.queue(); app.launch(server_name='127.0.0.1',server_port=PORT,prevent_thread_lock=True,quiet=True)
    time.sleep(2); shots=[]
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=_chrome()); pg=b.new_page(viewport={'width':W,'height':H})
        pg.goto(f'http://127.0.0.1:{PORT}'); pg.wait_for_selector('text=Nova investigação',timeout=30000); time.sleep(1)
        for i,(name,tab,cap) in enumerate(STEPS):
            if i==1:
                pg.get_by_role('button',name='Carregar caso de demonstração').click()
                pg.wait_for_selector('.ti-kpis',timeout=30000); time.sleep(1.2)
            if tab:
                pg.get_by_role('tab',name=tab).click(); time.sleep(.9)
            path=OUT/f'{name}.png'; pg.evaluate('window.scrollTo(0,0)'); time.sleep(.3); pg.screenshot(path=str(path)); shots.append((path,cap))
        b.close()
    app.close()
    frames=[caption(pth,cap,i+1,len(shots)).resize((1100,int(1100*(H+64)/W))) for i,(pth,cap) in enumerate(shots)]
    pal=[f.quantize(colors=128,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE) for f in frames]
    pal[0].save(OUT/'demo.gif',save_all=True,append_images=pal[1:],duration=[2200]+[2800]*(len(pal)-1),loop=0,optimize=True)
    print('ok',[f.name for f in OUT.iterdir()])

if __name__=='__main__': main()
