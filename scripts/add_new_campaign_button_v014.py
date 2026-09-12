from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrence(s), found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


app = "src/App.tsx"
replace(
    app,
    '''  async function analyzeUpdate() {
''',
    '''  async function createAnotherCampaign() {
    const suggested = "Kitaba Solo — Nouvelle campagne";
    const value = window.prompt("Nom de la nouvelle campagne", suggested);
    if (value === null) return;
    const name = value.trim();
    if (!name) { setStatus("Création annulée : le nom de campagne ne peut pas être vide."); return; }
    setBusy(true);
    try {
      const created = await backend.createCampaign(name);
      await refreshCampaigns();
      setSelectedId(created.id);
      setSearchQuery("");
      setActive("sync");
      setStatus("Nouvelle campagne vierge créée. Exporte son contexte complet MJ puis termine la création du personnage avant toute narration.");
    } catch (e) { setStatus(`Création impossible : ${String(e)}`); }
    finally { setBusy(false); }
  }

  async function analyzeUpdate() {
''',
)
replace(
    app,
    '''<article className="panel"><h2>Gestion de la campagne</h2><p className="muted">Archiver masque la campagne sans supprimer ses données. La suppression définitive n'est disponible que depuis les archives et crée d'abord une sauvegarde technique automatique.</p><button className="ghost" onClick={archiveCurrentCampaign} disabled={busy}>Archiver cette campagne</button></article>''',
    '''<article className="panel"><h2>Gestion de la campagne</h2><p className="muted">Tu peux créer une nouvelle campagne indépendante sans modifier la campagne active. Archiver masque une campagne sans supprimer ses données.</p><div className="action-row"><button className="secondary" onClick={createAnotherCampaign} disabled={busy}>Nouvelle campagne</button><button className="ghost" onClick={archiveCurrentCampaign} disabled={busy}>Archiver cette campagne</button></div></article>''',
)

tests_path = ROOT / "reference/tests/test_project_parity.py"
tests = tests_path.read_text(encoding="utf-8")
if "test_existing_campaign_can_create_an_independent_new_campaign" in tests:
    raise SystemExit("new-campaign management regression test already present")
tests += '''\n\ndef test_existing_campaign_can_create_an_independent_new_campaign():\n    app = _read("src/App.tsx")\n    assert "async function createAnotherCampaign()" in app\n    assert ">Nouvelle campagne</button>" in app\n    assert "Nouvelle campagne vierge créée" in app\n'''
tests_path.write_text(tests, encoding="utf-8")

changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text(encoding="utf-8")
anchor = "- Added regression tests preventing a return to a hard-coded Sully launch path.\n"
if anchor not in changelog:
    raise SystemExit("CHANGELOG.md 0.1.4 anchor missing")
changelog = changelog.replace(anchor, anchor + "- Added a New campaign action even when another active campaign exists, so independent playthroughs no longer require archiving the current one first.\n", 1)
changelog_path.write_text(changelog, encoding="utf-8")

print("Added independent new-campaign action to 0.1.4")
