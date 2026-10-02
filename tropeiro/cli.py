"""CLI offline: `tropeiro lure arquivo.txt --case C1 --out saida/` (sem rede, sem Colab)."""
import argparse, json, sys
from pathlib import Path
from .intelligence.br_lures import detect_br_lures, extract_lure_infra
from .intelligence.sigma import sigma_rules
from .reporting.stix import bundle_from_iocs
from .reporting.misp import misp_event
from .utils import defang
from .intelligence.legit_domains import partition_iocs

def main(argv=None):
    ap=argparse.ArgumentParser(prog='tropeiro',description='Tropeiro Intel (modo offline)')
    sub=ap.add_subparsers(dest='cmd',required=True)
    p=sub.add_parser('lure',help='analisa texto de isca: marca/tema, IOCs, PIX/WhatsApp, e exporta STIX/MISP/Sigma')
    p.add_argument('file',help="arquivo de texto ('-' = stdin)")
    p.add_argument('--case',default='CASE'); p.add_argument('--tlp',default='AMBER')
    p.add_argument('--out',help='diretório para stix.json, misp.json e sigma_*.yml')
    w=sub.add_parser('workbench',help='abre o Workbench (Gradio) no navegador local')
    w.add_argument('--port',type=int,default=7860); w.add_argument('--share',action='store_true',help='link público temporário do Gradio (cuidado com dados do caso)')
    a=ap.parse_args(argv)
    if a.cmd=='workbench':
        from .frontend.app import launch_local
        launch_local(a.port,a.share); return 0
    text=sys.stdin.read() if a.file=='-' else Path(a.file).read_text(encoding='utf-8')
    iocs=extract_lure_infra(text)
    act,ctx=partition_iocs(iocs)
    result={'lures':detect_br_lures(text),'iocs':iocs,'somente_contexto':ctx}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('defanged:',', '.join(defang(d) for d in act.get('domain',[])) or '-')
    if a.out:
        out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
        (out/'stix.json').write_text(bundle_from_iocs(act,case_id=a.case,tlp=a.tlp,context_only=ctx).serialize(pretty=True),encoding='utf-8')
        (out/'misp.json').write_text(json.dumps(misp_event(a.case,act,tlp=a.tlp,context_only=ctx),ensure_ascii=False,indent=2),encoding='utf-8')
        for k,v in sigma_rules(act,a.case).items(): (out/f'sigma_{k}.yml').write_text(v+'\n',encoding='utf-8')
        print('exportado em',out)
    return 0

if __name__=='__main__': sys.exit(main())
