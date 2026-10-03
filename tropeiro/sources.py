"""Executor de fontes: coleta concorrente, com prazo, circuit breaker e estados explícitos.

Cada fonte é uma `Task` (uma consulta a um assunto: domínio, IP ou hash). O executor roda as tarefas em paralelo,
respeita um **prazo total** (uma fonte lenta não trava a busca) e devolve uma linha de status por tarefa:
OK, UNAVAILABLE (falhou), TIMEOUT (estourou o prazo) ou SKIPPED_* (nem tentada, com o motivo).
"""
from __future__ import annotations
import time, urllib.error
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple
from .models import Observation

BUDGET_DEADLINE={"free":45.0,"balanced":90.0,"extended":180.0}      # segundos para a coleta inteira

@dataclass
class Task:
    source: str                                    # nome mostrado ao usuário (ex.: "dns:A", "urlscan")
    subject: str                                   # domínio, IP ou hash consultado
    fn: Callable[[], Any]                          # devolve observações ou (observações, linhas_extras)

def status_row(source,subject,status,items=0,seconds=0.0,error=""):
    return {"source":source,"subject":subject,"status":status,"items":items,"seconds":round(seconds,2),"error":error}

def skipped_row(source,subject,reason,detail=""):
    return status_row(source,subject,reason,error=detail)

def describe_error(exc: BaseException) -> str:
    """Mensagem curta e acionável (o usuário precisa entender sem ler traceback)."""
    if isinstance(exc,urllib.error.HTTPError):
        hint={401:"autenticação necessária",403:"acesso negado (a fonte pode exigir chave de API)",404:"não encontrado",429:"limite de requisições da fonte"}.get(exc.code,"")
        return f"HTTP {exc.code}"+(f" — {hint}" if hint else "")
    if isinstance(exc,(TimeoutError,)) or "timed out" in str(exc).lower(): return "tempo esgotado ao falar com a fonte"
    if isinstance(exc,urllib.error.URLError): return f"falha de rede ({getattr(exc,'reason',exc)})"
    if isinstance(exc,ConnectionError): return f"conexão interrompida ({exc})"
    return f"{type(exc).__name__}: {str(exc)[:160]}"

def _run(task: Task) -> Tuple[List[Observation],List[dict],float]:
    t=time.time(); res=task.fn()
    obs,extra=(res if isinstance(res,tuple) else (res,[]))
    return list(obs or []),list(extra or []),time.time()-t

def run_tasks(tasks: List[Task], deadline: float=90.0, max_workers: int=8,
              on_progress: Optional[Callable[[int,int,dict],None]]=None) -> Tuple[List[Observation],List[dict]]:
    """Executa as tarefas em paralelo. Devolve (observações, linhas de status)."""
    observations: List[Observation]=[]; rows: List[dict]=[]
    if not tasks: return observations,rows
    start=time.time()
    pool=ThreadPoolExecutor(max_workers=max(1,min(max_workers,len(tasks))),thread_name_prefix="tropeiro-src")
    pending={pool.submit(_run,t):t for t in tasks}
    total=len(tasks); done=0
    try:
        while pending:
            left=deadline-(time.time()-start)
            if left<=0: break
            finished,_=wait(list(pending),timeout=left,return_when=FIRST_COMPLETED)
            if not finished: break
            for fut in finished:
                task=pending.pop(fut); done+=1
                try:
                    obs,extra,secs=fut.result()
                    row=status_row(task.source,task.subject,"OK",len(obs),secs)
                    observations+=obs; rows.append(row); rows+=extra
                except Exception as exc:
                    row=status_row(task.source,task.subject,"UNAVAILABLE",0,time.time()-start,describe_error(exc)); rows.append(row)
                if on_progress: on_progress(done,total,row)
        for fut,task in pending.items():                      # estourou o prazo: não espera mais
            fut.cancel(); done+=1
            row=status_row(task.source,task.subject,"TIMEOUT",0,deadline,f"prazo da busca esgotado ({deadline:.0f}s); resultado parcial")
            rows.append(row)
            if on_progress: on_progress(done,total,row)
    finally:
        pool.shutdown(wait=False,cancel_futures=True)
    return observations,rows
