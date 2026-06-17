import sqlite3
import pandas as pd

conn = sqlite3.connect('data/bank_ethics.db')

# Виж всички prompts по category
result = conn.execute('SELECT category, COUNT(*) FROM prompts GROUP BY category').fetchall()
print("Prompts by category:")
for cat, cnt in result:
    print(f"  {cat}: {cnt}")

# Виж transparency prompts CSV
csv_df = pd.read_csv('data/prompts_transparency.csv')
print(f"\nTransparency CSV:")
print(f"  Total rows: {len(csv_df)}")
print(f"  family_key values: {csv_df['family_key'].unique()}")
print(f"  First prompt: {csv_df['prompt'].iloc[0]}")

# Виж дали този prompt е в DB
first_prompt = csv_df['prompt'].iloc[0]
result = conn.execute('SELECT id, category, text FROM prompts WHERE text LIKE ? LIMIT 1', (f'%{first_prompt[:30]}%',)).fetchone()
if result:
    print(f"\nFirst CSV prompt found in DB:")
    print(f"  ID: {result[0]}")
    print(f"  Category: {result[1]}")
    print(f"  Text: {result[2][:80]}")
else:
    print(f"\nFirst CSV prompt NOT found in DB")

# Провери hash collision
import hashlib
def build_prompt_hash(text, category, demographic_group, pair_id, source):
    raw = "||".join([
        category or "",
        demographic_group or "",
        pair_id or "",
        source or "",
        text,
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

row = csv_df.iloc[0]
family_key = row.get('family_key')
source_parts = f"src=custom_bg|family_key={family_key}|scenario_id={row.get('scenario_id')}|style={row.get('style')}"
prompt_hash = build_prompt_hash(
    text=row['prompt'],
    category=family_key,
    demographic_group=row.get('demographic_group') if pd.notna(row.get('demographic_group')) else None,
    pair_id=row.get('pair_id') if pd.notna(row.get('pair_id')) else None,
    source=source_parts
)

print(f"\nExpected hash for first prompt: {prompt_hash[:16]}...")
result = conn.execute('SELECT id, category, prompt_hash FROM prompts WHERE prompt_hash=?', (prompt_hash,)).fetchone()
if result:
    print(f"✅ Prompt exists with hash: ID={result[0]}, category={result[1]}")
else:
    print(f"❌ Prompt with this hash NOT found")
    # Търси по текст
    result = conn.execute('SELECT id, category, prompt_hash FROM prompts WHERE text=?', (row['prompt'],)).fetchone()
    if result:
        print(f"⚠️ But found by text: ID={result[0]}, category={result[1]}, hash={result[2][:16]}...")

conn.close()
