#!/usr/bin/env python3
import os, json
from predict.shield import ShieldPatterns
from predict.prompt_fingerprint import NBModel
ROOT=os.path.dirname(__file__)+"/.."
DATA=os.path.join(ROOT,"data")
def main():
    sp=os.path.join(DATA,"shield_patterns.yaml"); mp=os.path.join(DATA,"prompt_fingerprint.model.json")
    if not os.path.exists(sp): print("Falta data/shield_patterns.yaml"); return
    shield=ShieldPatterns.from_yaml(sp)
    text="role: system\nYou are an AI. Respond in JSON with fields {answer, reasoning}.\n"
    res=shield.analyze(text); print("[Shield] hits:", res["hits"]); print("[Shield] score:", res["score"])
    if os.path.exists(mp):
        m=NBModel.load(mp); print("[NB] proba:", m.predict_proba(text))
    else:
        print("[NB] sin modelo (entrena con train/train_prompt_fingerprint.py)")
if __name__=="__main__": main()
