import sqlite3

conn = sqlite3.connect('data/bank_ethics.db')

# Transparency generations
result = conn.execute('''
    SELECT COUNT(*) 
    FROM generations g 
    JOIN prompts p ON g.prompt_id=p.id 
    WHERE p.category='transparency'
''').fetchone()
print(f'Transparency generations: {result[0]}')

# Risky example
result = conn.execute('''
    SELECT p.text, g.answer 
    FROM generations g 
    JOIN prompts p ON g.prompt_id=p.id 
    WHERE p.category='transparency' AND g.system_version LIKE '%risky%' 
    LIMIT 1
''').fetchone()
if result:
    print(f'\n📝 RISKY example:')
    print(f'PROMPT: {result[0]}')
    print(f'ANSWER: {result[1][:200]}')

# Compliant example
result = conn.execute('''
    SELECT p.text, g.answer 
    FROM generations g 
    JOIN prompts p ON g.prompt_id=p.id 
    WHERE p.category='transparency' AND g.system_version LIKE '%compliant%' 
    LIMIT 1
''').fetchone()
if result:
    print(f'\n✅ COMPLIANT example:')
    print(f'PROMPT: {result[0]}')
    print(f'ANSWER: {result[1][:200]}')

# Labeled transparency
result = conn.execute('''
    SELECT COUNT(*) 
    FROM labels l 
    JOIN generations g ON l.gen_id=g.id 
    JOIN prompts p ON g.prompt_id=p.id 
    WHERE p.category='transparency'
''').fetchone()
print(f'\n📋 Transparency labeled: {result[0]}')

# Transparency violations detected
result = conn.execute('''
    SELECT SUM(CASE WHEN transparency_score>0 THEN 1 ELSE 0 END), COUNT(*) 
    FROM labels l 
    JOIN generations g ON l.gen_id=g.id 
    JOIN prompts p ON g.prompt_id=p.id 
    WHERE p.category='transparency'
''').fetchone()
if result[1] > 0:
    print(f'Transparency violations: {result[0]} out of {result[1]}')

conn.close()
