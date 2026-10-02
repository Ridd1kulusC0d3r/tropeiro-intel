from __future__ import annotations
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

DEFAULT_GLINER_MODEL = "urchade/gliner_multi-v2.1"
QWEN_LIGHT_MODEL = "Qwen/Qwen3-0.6B"
QWEN_BALANCED_MODEL = "Qwen/Qwen3-1.7B"

DEFAULT_ENTITY_LABELS = [
    "organization","brand","domain","url","ip address","email address",
    "phone number","asn","registrar","hosting provider","certificate name",
    "tracking id","malware family","campaign name","threat actor alias",
    "country","financial institution","payment method"
]

@dataclass
class AIModelMetadata:
    component: str
    model: str
    status: str
    note: str = ""
    derived_only: bool = True

def runtime_profile() -> Dict[str, Any]:
    result={"gpu":False,"device":"cpu","recommended_qwen_model":QWEN_LIGHT_MODEL}
    try:
        import torch
        result["gpu"]=bool(torch.cuda.is_available())
        result["device"]="cuda" if result["gpu"] else "cpu"
        if result["gpu"]:
            result["gpu_name"]=torch.cuda.get_device_name(0)
            result["recommended_qwen_model"]=QWEN_BALANCED_MODEL
    except Exception as exc:
        result["torch_error"]=str(exc)
    return result

def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value,ensure_ascii=False,default=str))

def _stable_hash(value: Any) -> str:
    raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def build_ai_text_corpus(report_data: Mapping[str,Any], lure_text: str="", campaign_note: str="", max_chars: int=18000) -> List[Dict[str,str]]:
    corpus=[]
    def add(source,text):
        text=str(text or "").strip()
        if text:
            corpus.append({"source":source,"text":text[:max_chars]})
    add("lure_text",lure_text)
    add("campaign_note",campaign_note)
    for row in report_data.get("ioc_decisions",[])[:100]:
        add("ioc_decision",json.dumps(row,ensure_ascii=False,default=str))
    for row in report_data.get("ownership",{}).values():
        add("ownership",json.dumps(row,ensure_ascii=False,default=str))
    for row in report_data.get("domain_similarity",[])[:100]:
        add("domain_similarity",json.dumps(row,ensure_ascii=False,default=str))
    return corpus

def extract_gliner_entities(texts: Iterable[Mapping[str,str]], model: Any, labels: Optional[List[str]]=None, threshold: float=.45) -> List[Dict[str,Any]]:
    labels=labels or DEFAULT_ENTITY_LABELS
    out=[];seen=set()
    for item in texts:
        source=str(item.get("source","text"));text=str(item.get("text",""))
        if not text.strip():
            continue
        try:
            entities=model.predict_entities(text,labels,threshold=threshold)
        except TypeError:
            entities=model.predict_entities(text,labels)
        for e in entities or []:
            value=str(e.get("text","")).strip()
            if not value:
                continue
            label=str(e.get("label","entity"))
            key=(source,value.casefold(),label.casefold())
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "candidate_id":"ai-ent-"+hashlib.sha256(("|".join(key)).encode()).hexdigest()[:12],
                "value":value,"label":label,"score":round(float(e.get("score",0) or 0),4),
                "start":e.get("start"),"end":e.get("end"),"source_context":source,
                "model":"GLiNER","derived":True,"analyst_confirmed":False
            })
    return sorted(out,key=lambda x:x["score"],reverse=True)

class GLiNERLocal:
    def __init__(self,model_name: str=DEFAULT_GLINER_MODEL,threshold: float=.45):
        self.model_name=model_name
        self.threshold=threshold
        self._model=None
    def load(self):
        if self._model is None:
            from gliner import GLiNER
            self._model=GLiNER.from_pretrained(self.model_name)
        return self._model
    def extract(self,texts,labels=None):
        return extract_gliner_entities(texts,self.load(),labels=labels,threshold=self.threshold)

class QwenLocalChat:
    def __init__(self,model_name: Optional[str]=None,thinking: bool=False):
        profile=runtime_profile()
        self.model_name=model_name or profile["recommended_qwen_model"]
        self.thinking=thinking
        self._tokenizer=None
        self._model=None
    def load(self):
        if self._model is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self._tokenizer=AutoTokenizer.from_pretrained(self.model_name)
            self._model=AutoModelForCausalLM.from_pretrained(self.model_name,torch_dtype="auto",device_map="auto")
        return self._tokenizer,self._model
    def chat(self,system: str,user: str,max_new_tokens: int=900) -> str:
        tok,model=self.load()
        messages=[{"role":"system","content":system},{"role":"user","content":user}]
        kwargs={"tokenize":False,"add_generation_prompt":True}
        try:
            text=tok.apply_chat_template(messages,enable_thinking=self.thinking,**kwargs)
        except TypeError:
            text=tok.apply_chat_template(messages,**kwargs)
        inputs=tok([text],return_tensors="pt").to(model.device)
        gen={"max_new_tokens":max_new_tokens,"do_sample":True,"temperature":.6 if self.thinking else .7,"top_p":.95 if self.thinking else .8,"top_k":20}
        ids=model.generate(**inputs,**gen)
        out=ids[0][len(inputs.input_ids[0]):]
        return tok.decode(out,skip_special_tokens=True).strip()

def build_evidence_packet(report_data: Mapping[str,Any],max_evidence: int=220) -> Dict[str,Any]:
    packet={
        "schema":"tropeiro-evidence-packet-v1",
        "case":_clone(report_data.get("meta",{})),
        "executive_assessment":_clone(report_data.get("executive_assessment",{})),
        "ioc_decisions":_clone(report_data.get("ioc_decisions",[])[:120]),
        "attribution_assessments":_clone(report_data.get("attribution_assessments",[])[:80]),
        "collection_gaps":_clone(report_data.get("collection_gaps",[])[:80]),
        "next_best_pivots":_clone(report_data.get("next_best_pivots",[])[:80]),
        "lifecycle":_clone(report_data.get("lifecycle",{})),
        "victimology":_clone(report_data.get("victimology",{})),
        "objectives":_clone(report_data.get("objectives",{})),
        "source_status":_clone(report_data.get("source_status",[])[:120]),
        "feature_matrix":_clone(report_data.get("feature_matrix",[])[:120]),
        "evidence_ledger":_clone(report_data.get("evidence_ledger",[])[:max_evidence]),
    }
    packet["packet_sha256"]=_stable_hash(packet)
    return packet

def allowed_evidence_refs(packet: Mapping[str,Any]) -> set:
    refs=set()
    for row in packet.get("evidence_ledger",[]) or []:
        if isinstance(row,dict):
            for key in ("evidence_id","id","event_id"):
                if row.get(key):
                    refs.add(str(row[key]))
    return refs

def ai_system_prompt(language: str="pt-BR") -> str:
    return (
        "Voce e o copiloto analitico do Tropeiro Intel. Responda em "+language+". "
        "Use somente o EVIDENCE_PACKET. Nao altere nem invente evidencia. "
        "Separe observado, inferencia e hipotese. Cite somente evidence_refs existentes. "
        "Se faltar suporte, use insufficient_evidence. Nao transforme correlacao em identidade. "
        "Nao forneca instrucoes ofensivas. Retorne JSON valido sem markdown."
    )

def analysis_request(packet: Mapping[str,Any]) -> str:
    schema={
        "executive_summary":"string",
        "key_findings":[{"statement":"string","analytic_type":"observed|inference|hypothesis","confidence":"HIGH|MODERATE|LOW|INSUFFICIENT","evidence_refs":["EV-ID"],"basis":"short string"}],
        "hypotheses":[{"hypothesis":"string","support_refs":["EV-ID"],"contradiction_refs":["EV-ID"],"confidence":"HIGH|MODERATE|LOW|INSUFFICIENT"}],
        "collection_priorities":[{"priority":"P1|P2|P3","action":"string","why":"string"}],
        "detection_opportunities":[{"surface":"dns|proxy|email|identity|other","idea":"string","evidence_refs":["EV-ID"]}],
        "caveats":["string"]
    }
    return "Schema de saida: "+json.dumps(schema,ensure_ascii=False)+" EVIDENCE_PACKET: "+json.dumps(packet,ensure_ascii=False,default=str)

def parse_json_response(text: str) -> Dict[str,Any]:
    raw=str(text or "").strip()
    try:
        return {"status":"OK","data":json.loads(raw),"raw":raw}
    except Exception:
        first=raw.find("{");last=raw.rfind("}")
        if first>=0 and last>first:
            try:
                return {"status":"OK_RECOVERED","data":json.loads(raw[first:last+1]),"raw":raw}
            except Exception:
                pass
        return {"status":"RAW_TEXT","data":{"executive_summary":raw,"key_findings":[],"hypotheses":[],"collection_priorities":[],"detection_opportunities":[],"caveats":["LLM response was not valid JSON."]},"raw":raw}

def validate_ai_analysis(value: Mapping[str,Any],packet: Mapping[str,Any]) -> Dict[str,Any]:
    result=_clone(dict(value or {}));allowed=allowed_evidence_refs(packet);warnings=[]
    for section,keys in (("key_findings",["evidence_refs"]),("hypotheses",["support_refs","contradiction_refs"]),("detection_opportunities",["evidence_refs"])):
        for row in result.get(section,[]) or []:
            if not isinstance(row,dict):
                continue
            for key in keys:
                refs=[str(x) for x in row.get(key,[]) or []]
                invalid=[x for x in refs if x not in allowed]
                if invalid:
                    warnings.append({"section":section,"invalid_refs":invalid})
                row[key]=[x for x in refs if x in allowed]
    result["_validation"]={"allowed_evidence_refs":len(allowed),"warnings":warnings,"evidence_packet_sha256":packet.get("packet_sha256")}
    return result

def enforce_evidence_support(analysis: Dict[str,Any]) -> Dict[str,Any]:
    """Achado sem nenhuma referência válida não pode ser 'observed' nem ter confiança alta."""
    downgraded=0
    for row in analysis.get("key_findings",[]) or []:
        if isinstance(row,dict) and not row.get("evidence_refs"):
            if row.get("analytic_type")=="observed" or row.get("confidence") in ("HIGH","MODERATE"):
                row["analytic_type"]="hypothesis"; row["confidence"]="INSUFFICIENT"; downgraded+=1
    analysis.setdefault("_validation",{})["downgraded_findings"]=downgraded
    return analysis

def run_qwen_analysis(chat: QwenLocalChat,packet: Mapping[str,Any],language: str="pt-BR",max_new_tokens: int=1200,retry: bool=True) -> Dict[str,Any]:
    raw=chat.chat(ai_system_prompt(language),analysis_request(packet),max_new_tokens=max_new_tokens)
    parsed=parse_json_response(raw)
    if retry and parsed["status"]=="RAW_TEXT":
        fix="Sua resposta anterior nao era JSON valido. Reenvie SOMENTE o JSON do schema, sem texto extra. Resposta anterior: "+raw[:3000]
        parsed=parse_json_response(chat.chat(ai_system_prompt(language),fix,max_new_tokens=max_new_tokens))
        if parsed["status"]!="RAW_TEXT": parsed["status"]="OK_RETRY"
    data=enforce_evidence_support(validate_ai_analysis(parsed["data"],packet))
    data["_generation_status"]=parsed["status"]
    return data

def ask_qwen_about_case(chat: QwenLocalChat,packet: Mapping[str,Any],question: str,language: str="pt-BR",max_new_tokens: int=700) -> str:
    prompt="EVIDENCE_PACKET: "+json.dumps(packet,ensure_ascii=False,default=str)+" PERGUNTA: "+str(question)+" Responda curto, separando fatos de inferencias e citando evidence_id quando existir."
    return chat.chat(ai_system_prompt(language),prompt,max_new_tokens=max_new_tokens)

def attach_ai_overlay(report_data: Mapping[str,Any],entities=None,analysis=None,metadata=None,packet=None) -> Dict[str,Any]:
    out=_clone(report_data)
    before=_stable_hash(out.get("evidence_ledger",[]))
    out["ai_entities"]=_clone(entities or [])
    out["ai_analysis"]=_clone(analysis or {})
    out["ai_metadata"]=_clone(metadata or {})
    if packet:
        out["ai_evidence_packet"]={"schema":packet.get("schema"),"packet_sha256":packet.get("packet_sha256")}
    if before!=_stable_hash(out.get("evidence_ledger",[])):
        raise RuntimeError("AI overlay attempted to mutate Evidence Ledger")
    return out
