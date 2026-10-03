import time, urllib.error, io
from tropeiro.models import Observation
from tropeiro.sources import Task, run_tasks, describe_error

def ob(v): return Observation('e','domain','x',v)

def test_tasks_run_in_parallel_and_report_ok():
    def slow(): time.sleep(.4); return [ob('a')]
    t=time.time(); obs,rows=run_tasks([Task(f's{i}','d',slow) for i in range(6)],deadline=5,max_workers=6)
    assert time.time()-t<1.2 and len(obs)==6 and {r['status'] for r in rows}=={'OK'}   # em série seriam 2,4 s

def test_failure_becomes_unavailable_with_readable_message():
    def boom(): raise urllib.error.HTTPError('http://x',403,'Forbidden',{},io.BytesIO(b''))
    obs,rows=run_tasks([Task('urlscan','d',boom),Task('ok','d',lambda:[ob('v')])],deadline=5)
    bad=next(r for r in rows if r['source']=='urlscan')
    assert bad['status']=='UNAVAILABLE' and 'HTTP 403' in bad['error'] and 'chave' in bad['error'] and len(obs)==1

def test_deadline_returns_partial_result_with_timeout_rows():
    def hang(): time.sleep(3); return [ob('late')]
    t=time.time(); obs,rows=run_tasks([Task('fast','d',lambda:[ob('quick')]),Task('slow','d',hang)],deadline=.6)
    assert time.time()-t<1.5 and [o.value for o in obs]==['quick']
    slow=next(r for r in rows if r['source']=='slow'); assert slow['status']=='TIMEOUT' and 'prazo' in slow['error']

def test_extra_rows_and_progress_callback():
    seen=[]
    obs,rows=run_tasks([Task('a','d',lambda:([ob('1')],[{'source':'a:detalhes','subject':'d','status':'OK','items':1,'seconds':0,'error':''}]))],
                       deadline=5,on_progress=lambda done,total,row:seen.append((done,total,row['source'])))
    assert {r['source'] for r in rows}=={'a','a:detalhes'} and seen==[(1,1,'a')]

def test_empty_task_list_is_fine():
    assert run_tasks([])==([],[])

def test_describe_error_variants():
    assert 'tempo esgotado' in describe_error(TimeoutError('timed out'))
    assert 'falha de rede' in describe_error(urllib.error.URLError('nope'))
    assert describe_error(ValueError('x')).startswith('ValueError')
