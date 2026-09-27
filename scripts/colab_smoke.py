"""Offline smoke validation for the public Colab backend."""
import json
from pathlib import Path

import tropeiro
from tropeiro.similarity import compare_domains, extract_durable_identifiers
from tropeiro.correlation.advanced import source_independence
from tropeiro.intelligence import build_ioc_decisions, WarningListEngine
from tropeiro.reporting.rich_html import build_report

def main():
    assert tropeiro.__version__ == "4.0.1"
    assert compare_domains(["example.com","exampl3.com"], min_score=0.1)
    assert isinstance(source_independence([{"source":"rdap"}]), dict)
    rows=build_ioc_decisions([{
        "value":"example.test","type":"domain","confidence":.2,"active":False,
        "source_families":1,"evidence_count":1,"context":{}
    }], WarningListEngine())
    assert rows
    nb=json.loads(Path("notebooks/Tropeiro_Intel_Official_Colab.ipynb").read_text())
    assert len(nb["cells"]) >= 60
    print(json.dumps({"version":tropeiro.__version__,"cells":len(nb["cells"]),"status":"ok"}))

if __name__ == "__main__":
    main()
