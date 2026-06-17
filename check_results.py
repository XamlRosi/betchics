#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick diagnostic of training results"""

import sqlite3
import pandas as pd
from pathlib import Path

print("="*80)
print("TRAINING PIPELINE DIAGNOSTIC")
print("="*80)

# Check database
db_path = "data/bank_ethics.db"
if Path(db_path).exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Total generations
    result = cur.execute('SELECT COUNT(*) FROM generations').fetchone()
    print(f"\n📊 Total generations in DB: {result[0]}")
    
    # By category
    result = cur.execute('''
        SELECT p.category, COUNT(*) as cnt 
        FROM generations g 
        JOIN prompts p ON g.prompt_id=p.id 
        GROUP BY p.category
    ''').fetchall()
    print("\nGenerations by category:")
    for cat, cnt in result:
        print(f"  {cat:20s}: {cnt:3d}")
    
    # By system version
    result = cur.execute('''
        SELECT system_version, COUNT(*) 
        FROM generations 
        GROUP BY system_version
    ''').fetchall()
    print("\nGenerations by system version:")
    for sys, cnt in result:
        print(f"  {sys:30s}: {cnt:3d}")
    
    # Labeled responses
    result = cur.execute('SELECT COUNT(*) FROM labels').fetchone()
    print(f"\n📋 Total labeled responses: {result[0]}")
    
    # Sample risky transparency response
    result = cur.execute('''
        SELECT p.text, g.answer 
        FROM generations g 
        JOIN prompts p ON g.prompt_id=p.id 
        WHERE p.category='transparency' AND g.system_version LIKE '%risky%' 
        LIMIT 1
    ''').fetchone()
    if result:
        print("\n📝 Sample RISKY transparency response:")
        print(f"PROMPT: {result[0]}")
        print(f"ANSWER: {result[1][:200]}")
    
    # Sample compliant transparency response
    result = cur.execute('''
        SELECT p.text, g.answer 
        FROM generations g 
        JOIN prompts p ON g.prompt_id=p.id 
        WHERE p.category='transparency' AND g.system_version LIKE '%compliant%' 
        LIMIT 1
    ''').fetchone()
    if result:
        print("\n✅ Sample COMPLIANT transparency response:")
        print(f"PROMPT: {result[0]}")
        print(f"ANSWER: {result[1][:200]}")
    
    # Label distribution
    result = cur.execute('''
        SELECT 
            SUM(unsafe) as unsafe,
            SUM(privacy_violation) as privacy,
            SUM(CASE WHEN transparency_score > 0 THEN 1 ELSE 0 END) as transparency_violations,
            SUM(manipulation) as manipulation,
            SUM(bias) as bias,
            COUNT(*) as total
        FROM labels
    ''').fetchone()
    if result:
        print("\n🏷️  Label statistics:")
        print(f"  Total labeled: {result[5]}")
        print(f"  Unsafe: {result[0]}")
        print(f"  Privacy violations: {result[1]}")
        print(f"  Transparency violations: {result[2]}")
        print(f"  Manipulation: {result[3]}")
        print(f"  Bias: {result[4]}")
    
    conn.close()

# Check training dataset
dataset_path = "data/training_dataset.csv"
if Path(dataset_path).exists():
    df = pd.read_csv(dataset_path)
    print("\n"+"="*80)
    print(f"📁 TRAINING DATASET: {len(df)} samples")
    print("="*80)
    
    # Label distribution
    print("\nBinary label distribution:")
    binary_cols = [c for c in df.columns if c.endswith('_bin')]
    for col in binary_cols:
        if col in df.columns:
            positive = df[col].sum()
            negative = len(df) - positive
            print(f"  {col:30s}: {positive:3d} positive, {negative:3d} negative")
    
    # Transparency score distribution
    if 'transparency_score' in df.columns:
        print("\nTransparency score distribution:")
        print(df['transparency_score'].value_counts().sort_index().to_string())
    
    # Category distribution
    if 'category' in df.columns:
        print("\nCategory distribution:")
        print(df['category'].value_counts().to_string())
    
    # System version distribution
    if 'system_version' in df.columns:
        print("\nSystem version distribution:")
        print(df['system_version'].value_counts().to_string())

# Check CV report
cv_report_path = "data/models/cv_report_row.json"
if Path(cv_report_path).exists():
    import json
    with open(cv_report_path) as f:
        report = json.load(f)
    
    print("\n"+"="*80)
    print("🎯 CROSS-VALIDATION RESULTS")
    print("="*80)
    
    print(f"\nTotal training samples: {report['label_balance']['rows']}")
    print(f"CV folds: {report['folds']}")
    print(f"Splitter: {report['splitter']}")
    
    print("\nPositive examples per label:")
    for label, count in report['label_balance']['positives'].items():
        print(f"  {label:30s}: {count:3d}")
    
    print("\n📈 Model performance (mean ± std):")
    for label, metrics in report['per_label'].items():
        f1 = metrics['f1_mean']
        f1_std = metrics['f1_std']
        prec = metrics['precision_mean']
        rec = metrics['recall_mean']
        support = metrics['avg_support_per_fold']
        
        status = "✅" if f1 > 0.5 else "⚠️" if f1 > 0.3 else "❌"
        print(f"  {status} {label:25s}  F1={f1:.3f}±{f1_std:.3f}  P={prec:.3f}  R={rec:.3f}  (support={support:.1f})")

print("\n"+"="*80)
print("✅ DIAGNOSTIC COMPLETE")
print("="*80)
