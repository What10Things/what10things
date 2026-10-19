#!/usr/bin/env python3
"""Apply only inspected W10 subject-quality code; abort on live code drift."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASELINE_SHA256 = {'Prepare evidence search': 'bea082a956cee5a5fbae9c4c3994669e9b21c9abae79c24a8a7b2fb6ed74dd78', 'Parse Bing evidence': '5a716edf87d9bf6f032cc08839291dbccf02f9ae7b5a1f4d7f79cc04ac418d24', 'Assemble evidence pack': 'e5bceb0266c5060f77fcb55fc4d0fb87bae214671e7c2ea08073de8554a0fe1c', 'Build evidence-grounded research prompt': '77558a042c3b767b7e678c71b15dee02ed83447a111f401dd0b65670d012b539', 'Validate ten sourced facts': '348e478cb3e088df584d2a078431f2d199743b1f9f1fd7a99eff96150af948a8'}


def patch(workflow):
    source = json.loads((ROOT / "automation/n8n/W10-R01-evidence-research.json").read_text())[0]
    proposed = {node["name"]: node for node in source["nodes"]}
    out = copy.deepcopy(workflow)
    live = {node["name"]: node for node in out["nodes"]}
    for name, baseline in BASELINE_SHA256.items():
        if name not in live:
            raise ValueError(f"Missing expected node: {name}")
        code = live[name]["parameters"]["jsCode"]
        replacement = proposed[name]["parameters"]["jsCode"]
        if code == replacement:
            continue
        if hashlib.sha256(code.encode()).hexdigest() != baseline:
            raise ValueError(f"Live code differs from inspected baseline: {name}; inspect drift before deployment")
        live[name]["parameters"]["jsCode"] = replacement
    return out


def main():
    source = json.loads(Path(sys.argv[1]).read_text())
    is_list = isinstance(source, list)
    before = source[0] if is_list else source
    result = patch(before)
    # Keep byte-identical files when already installed so the existing deploy
    # helper can avoid an unnecessary n8n restart.
    if result == before:
        Path(sys.argv[2]).write_bytes(Path(sys.argv[1]).read_bytes())
    else:
        Path(sys.argv[2]).write_text(json.dumps([result] if is_list else result,ensure_ascii=False,indent=2)+"\n")


if __name__ == "__main__":
    main()
