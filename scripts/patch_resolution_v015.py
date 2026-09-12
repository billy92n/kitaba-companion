from pathlib import Path

anchor = '                "The player controls only the protagonist\'s attempted actions, speech, intentions and voluntary thoughts. NPC reactions, action outcomes and external events remain GM-controlled even if the player writes a desired reaction.",\n'
addition = anchor + (
    '                "Treat any player wording that states a success or world outcome as an attempted action, not as an automatic fact. Resolve uncertainty from established abilities, knowledge, tools, injuries, opposition, environment and stakes; when a meaningful uncertain outcome exists, perform the resolution privately and allow failure, partial success, complications or success as warranted. Trivial uncontested actions need no roll.",\n'
    '                "When the player gives a terse action, enrich its presentation with concise physical detail, sensory context and character-consistent emotional shading so the scene feels alive, but do not invent a materially different intention, irreversible choice or successful outcome. If added detail would change risk or intent, keep the expansion minimal or ask for clarification.",\n'
)

for rel in ['src-tauri/src/db.rs', 'reference/engine.py']:
    p = Path(rel)
    text = p.read_text(encoding='utf-8')
    if 'Treat any player wording that states a success or world outcome as an attempted action' not in text:
        if anchor not in text:
            raise SystemExit(f'anchor not found in {rel}')
        p.write_text(text.replace(anchor, addition, 1), encoding='utf-8')

test = Path('reference/tests/test_immersive_patch.py')
text = test.read_text(encoding='utf-8')
marker = 'def test_release_version_is_015():\n'
block = '''def test_companion_contract_requires_real_resolution_and_enriched_terse_actions():
    rust = _read("src-tauri/src/db.rs")
    ref = _read("reference/engine.py")
    for text in (rust, ref):
        assert "states a success or world outcome as an attempted action" in text
        assert "perform the resolution privately" in text
        assert "allow failure, partial success, complications or success" in text
        assert "When the player gives a terse action" in text
        assert "do not invent a materially different intention" in text


'''
if 'test_companion_contract_requires_real_resolution_and_enriched_terse_actions' not in text:
    if marker not in text:
        raise SystemExit('test insertion marker not found')
    test.write_text(text.replace(marker, block + marker, 1), encoding='utf-8')

changelog = Path('CHANGELOG.md')
text = changelog.read_text(encoding='utf-8')
needle = '- préparation du contrat MJ 0.1.5 : narration plus courte et interactive, coordonnées cartographiques persistées, identité visuelle persistante et musique adaptative de scène.\n'
extra = needle + '- arbitrage renforcé : une réussite déclarée par le joueur reste une tentative ; le MJ résout en privé selon compétences, contexte, opposition et enjeux, avec échec et réussite partielle possibles ;\n- les actions joueur très brèves sont reformulées de façon vivante et concise (gestes, sensations, nuance émotionnelle) sans inventer une intention différente ni garantir le résultat.\n'
if 'une réussite déclarée par le joueur reste une tentative' not in text:
    if needle not in text:
        raise SystemExit('changelog anchor not found')
    changelog.write_text(text.replace(needle, extra, 1), encoding='utf-8')
