from pathlib import Path

path = Path("scripts/apply_013_launch_hardening.py")
lines = path.read_text(encoding="utf-8").splitlines()
desired = '    if (active === "map") return renderMap();\n    if (active === "world") return <section className="panel"><h2>État du monde connu</h2><p className="muted">Factions, institutions, marchés, conflits, villes et autres changements durables que Sully peut légitimement connaître. Les évolutions hors champ inconnues restent dans le Coffre MJ.</p><EntityList entities={sectionEntities} empty="Aucun état mondial connu n\'est encore enregistré." /></section>;\n    if (active === "media") return renderMedia();\n    if (active === "character")'
found = False
for i, line in enumerate(lines):
    if 'Aucun état mondial connu' in line and 'if (active ===' in line:
        lines[i] = "    " + repr(desired) + ","
        found = True
        break
if not found:
    raise SystemExit("Malformed world-section replacement line not found")
source = "\n".join(lines) + "\n"
code = compile(source, str(path), "exec")
exec(code, {"__name__": "__main__"})
