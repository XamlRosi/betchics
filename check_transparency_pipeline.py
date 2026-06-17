#!/usr/bin/env python3
"""
Diagnostic script to check transparency data pipeline status
"""
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "data/bank_ethics.db"
CSV_PATH = "data/training_dataset.csv"

def check_database():
    print("=" * 80)
    print("DATABASE CHECK")
    print("=" * 80)
    
    conn = sqlite3.connect(DB_PATH)
    
    # Check prompts
    result = conn.execute("SELECT category, COUNT(*) FROM prompts GROUP BY category").fetchall()
    print("\n📝 Prompts by category:")
    for cat, count in result:
        print(f"  {cat}: {count}")
    
    # Check generations for transparency
    result = conn.execute("""
        SELECT g.system_version, COUNT(*) 
        FROM generations g 
        JOIN prompts p ON g.prompt_id = p.id 
        WHERE p.category='transparency' 
        GROUP BY g.system_version
    """).fetchall()
    print("\n🤖 Transparency generations:")
    for sys_ver, count in result:
        print(f"  {sys_ver}: {count}")
    
    # Check labels for transparency
    result = conn.execute("""
        SELECT COUNT(*) 
        FROM labels l 
        JOIN generations g ON l.gen_id = g.id 
        JOIN prompts p ON g.prompt_id = p.id 
        WHERE p.category='transparency'
    """).fetchone()
    print(f"\n🏷️  Transparency labeled: {result[0]}")
    
    # Check sample transparency labels
    result = conn.execute("""
        SELECT p.text, g.answer, l.transparency_score, l.unsafe, l.privacy_violation, l.bias
        FROM labels l 
        JOIN generations g ON l.gen_id = g.id 
        JOIN prompts p ON g.prompt_id = p.id 
        WHERE p.category='transparency'
        LIMIT 5
    """).fetchall()
    
    if result:
        print("\n📊 Sample transparency labels:")
        for prompt, answer, trans, unsafe, priv, bias in result:
            print(f"\n  Prompt: {prompt[:50]}...")
            print(f"  Answer: {answer[:50]}...")
            print(f"  transparency_score={trans}, unsafe={unsafe}, privacy={priv}, bias={bias}")
    else:
        print("\n⚠️  No labeled transparency examples found!")
    
    conn.close()


def check_csv():
    print("\n" + "=" * 80)
    print("TRAINING CSV CHECK")
    print("=" * 80)
    
    if not Path(CSV_PATH).exists():
        print(f"\n❌ CSV not found: {CSV_PATH}")
        return
    
    df = pd.read_csv(CSV_PATH)
    
    print(f"\n📊 Total rows: {len(df)}")
    
    print("\n📁 Categories:")
    print(df['category'].value_counts().to_dict())
    
    if 'transparency_score' in df.columns:
        print("\n🎯 Transparency scores:")
        print(df['transparency_score'].value_counts().to_dict())
    else:
        print("\n⚠️  transparency_score column not found")
    
    if 'transparency_violation_bin' in df.columns:
        print(f"\n🚨 Transparency violations (binary): {df['transparency_violation_bin'].sum()}")
    else:
        print("\n⚠️  transparency_violation_bin column not found")
    
    # Check transparency samples
    if 'category' in df.columns:
        trans_df = df[df['category'] == 'transparency']
        print(f"\n📝 Transparency samples in CSV: {len(trans_df)}")
        
        if len(trans_df) > 0:
            print("\n📄 Sample transparency row:")
            sample = trans_df.iloc[0]
            print(f"  Prompt: {sample.get('prompt', 'N/A')[:60]}...")
            print(f"  Answer: {sample.get('answer', 'N/A')[:60]}...")
            print(f"  transparency_score: {sample.get('transparency_score', 'N/A')}")
            print(f"  transparency_violation_bin: {sample.get('transparency_violation_bin', 'N/A')}")


def check_columns():
    print("\n" + "=" * 80)
    print("COLUMN ALIGNMENT CHECK")
    print("=" * 80)
    
    if not Path(CSV_PATH).exists():
        print(f"\n❌ CSV not found: {CSV_PATH}")
        return
    
    df = pd.read_csv(CSV_PATH)
    
    expected_targets = [
        "unsafe",
        "privacy_violation", 
        "bias",
        "manipulation",
        "financial_risk",
        "transparency_violation",
        "missing_human_escalation"
    ]
    
    print("\n🎯 Target column status:")
    for target in expected_targets:
        raw_exists = target in df.columns
        bin_exists = f"{target}_bin" in df.columns
        
        status = "✅" if (raw_exists or bin_exists) else "❌"
        details = []
        if raw_exists:
            details.append(f"raw: {df[target].dtype}")
        if bin_exists:
            details.append(f"bin: {df[f'{target}_bin'].sum()} violations")
        
        print(f"  {status} {target:30s} {', '.join(details) if details else 'MISSING'}")


if __name__ == "__main__":
    check_database()
    check_csv()
    check_columns()
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print("""
To fix the transparency model:

1. Check if transparency prompts need labeling:
   python scripts/03_judge_labels.py --category transparency

2. Re-export training data:
   python scripts/05_export_training_data.py --out data/training_dataset.csv

3. Retrain model (now fixed to handle transparency_score):
   python scripts/06_train.py --csv data/training_dataset.csv

4. Test:
   python test_model.py
""")
