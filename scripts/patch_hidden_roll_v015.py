from pathlib import Path

needle = '                "Treat any player wording that states a success or world outcome as an attempted action, not as an automatic fact. Resolve uncertainty from established abilities, knowledge, tools, injuries, opposition, environment and stakes; when a meaningful uncertain outcome exists, perform the resolution privately and allow failure, partial success, complications or success as warranted. Trivial uncontested actions need no roll.",\n'
replacement = '                "Treat any player wording that states a success or world outcome as an attempted action, not as an automatic fact. Resolve uncertainty from established abilities, knowledge, tools, injuries, opposition, environment and stakes; when a meaningful uncertain outcome exists, perform a single hidden dice-like or equivalent random draw calibrated to the real odds, then allow failure, partial success, complications or success as warranted. Do not expose the number by default, do not reroll merely because the result is inconvenient, and do not roll for trivial uncontested actions.",\n'

for rel in ['src-tauri/src/db.rs', 'reference/engine.py']:
    p = Path(rel)
    text = p.read_text(encoding='utf-8')
    if replacement in text:
        continue
    if needle not in text:
        raise SystemExit(f'needle not found in {rel}')
    p.write_text(text.replace(needle, replacement, 1), encoding='utf-8')

t = Path('reference/tests/test_immersive_patch.py')
text = t.read_text(encoding='utf-8')
text = text.replace('assert "perform the resolution privately" in text', 'assert "single hidden dice-like or equivalent random draw" in text')
if 'assert "do not reroll merely because the result is inconvenient" in text' not in text:
    text = text.replace('assert "allow failure, partial success, complications or success" in text\n', 'assert "allow failure, partial success, complications or success" in text\n        assert "do not reroll merely because the result is inconvenient" in text\n')
t.write_text(text, encoding='utf-8')
