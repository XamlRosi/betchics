#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Force generate transparency responses - bypasses duplicate check"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import os
import time
from dotenv import load_dotenv
from openai import OpenAI

from bank_ethics.db.base import SessionLocal
from bank_ethics.db.models import Prompt, Generation

load_dotenv()

SYSTEM_COMPLIANT = Path("prompts/system_bank_v1.txt").read_text(encoding="utf-8")
SYSTEM_RISKY = Path("prompts/system_bank_risky_v1.txt").read_text(encoding="utf-8")

def call_llm(client, system_prompt, user_prompt, model="gpt-4o-mini", temperature=0.7):
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    db = SessionLocal()
    
    # Get transparency prompts
    prompts = db.query(Prompt).filter(Prompt.category == "transparency").all()
    print(f"Found {len(prompts)} transparency prompts")
    
    if not prompts:
        print("❌ No transparency prompts in DB!")
        return
    
    model = "gpt-4o-mini"
    temperature = 0.7
    generated = 0
    
    # Generate RISKY responses
    print("\n🔴 Generating RISKY responses...")
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] {prompt.text[:50]}...")
        
        answer = call_llm(client, SYSTEM_RISKY, prompt.text, model, temperature)
        
        gen = Generation(
            prompt_id=prompt.id,
            answer=answer,
            model_name=model,
            temperature=temperature,
            system_version="system_v1_risky"
        )
        db.add(gen)
        generated += 1
        time.sleep(0.5)
    
    db.commit()
    print(f"✅ Generated {generated} risky responses")
    
    # Generate COMPLIANT responses
    print("\n✅ Generating COMPLIANT responses...")
    for i, prompt in enumerate(prompts, 1):
        print(f"[{i}/{len(prompts)}] {prompt.text[:50]}...")
        
        answer = call_llm(client, SYSTEM_COMPLIANT, prompt.text, model, temperature)
        
        gen = Generation(
            prompt_id=prompt.id,
            answer=answer,
            model_name=model,
            temperature=temperature,
            system_version="system_v1_compliant"
        )
        db.add(gen)
        generated += 1
        time.sleep(0.5)
    
    db.commit()
    print(f"✅ Generated {generated} total responses")
    
    db.close()
    
    # Verify
    db = SessionLocal()
    count = db.query(Generation).join(Prompt).filter(Prompt.category == "transparency").count()
    db.close()
    print(f"\n📊 Total transparency generations in DB: {count}")

if __name__ == "__main__":
    main()
