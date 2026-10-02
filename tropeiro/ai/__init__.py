from .core import (
    DEFAULT_GLINER_MODEL,QWEN_LIGHT_MODEL,QWEN_BALANCED_MODEL,DEFAULT_ENTITY_LABELS,
    AIModelMetadata,runtime_profile,build_ai_text_corpus,extract_gliner_entities,GLiNERLocal,
    QwenLocalChat,build_evidence_packet,allowed_evidence_refs,ai_system_prompt,
    analysis_request,parse_json_response,validate_ai_analysis,run_qwen_analysis,
    ask_qwen_about_case,attach_ai_overlay
)
from .core import enforce_evidence_support
from .hybrid import extract_hybrid, correlate_entities, lure_similarity
