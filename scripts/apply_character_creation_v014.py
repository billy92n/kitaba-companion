from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrence(s), found {count}: {old[:100]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


def regex_replace(path: str, pattern: str, repl: str, expected: int = 1, flags: int = 0) -> None:
    p = ROOT / path
    text = p.read_text(encoding="utf-8")
    new, count = re.subn(pattern, repl, text, flags=flags)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} regex replacement(s), found {count}: {pattern!r}")
    p.write_text(new, encoding="utf-8")


# --- Version bump ---------------------------------------------------------
replace("package.json", '"version": "0.1.3"', '"version": "0.1.4"')
replace("package-lock.json", '"version": "0.1.3"', '"version": "0.1.4"', expected=2)
replace("src-tauri/Cargo.toml", 'version = "0.1.3"', 'version = "0.1.4"')
replace("src-tauri/tauri.conf.json", '"version": "0.1.3"', '"version": "0.1.4"')
regex_replace(
    "src-tauri/Cargo.lock",
    r'(\[\[package\]\]\nname = "kitaba-companion"\nversion = ")0\.1\.3(")',
    r'\g<1>0.1.4\2',
)
replace(
    ".github/workflows/build-windows.yml",
    "name: kitaba-companion-windows-0.1.3",
    "name: kitaba-companion-windows-0.1.4",
)

# --- Generic fresh-campaign onboarding UI --------------------------------
app = "src/App.tsx"
replace(
    app,
    '  const [selectedId, setSelectedId] = useState("");\n',
    '  const [selectedId, setSelectedId] = useState("");\n  const [newCampaignName, setNewCampaignName] = useState("Kitaba Solo — Nouvelle campagne");\n',
)
replace(
    app,
    '  const currentLocation = entities.find((e) => e.entity_type === "current_location")?.data;\n',
    '  const currentLocation = entities.find((e) => e.entity_type === "current_location")?.data;\n  const characterInitialized = entities.some((e) => e.entity_type === "player_character");\n',
)
replace(
    app,
    '''  async function createSullyCampaign() {
    setBusy(true);
    try {
      const created = await backend.createCampaign("Sully — Kitaba Solo");
      await refreshCampaigns();
      setSelectedId(created.id);
      setActive("sync");
      setStatus("Campagne créée. Exporte maintenant le contexte complet MJ vers ChatGPT pour initialiser la campagne sans perdre les données cachées futures.");
    } catch (e) { setStatus(`Erreur : ${String(e)}`); }
    finally { setBusy(false); }
  }
''',
    '''  async function createCampaign() {
    const name = newCampaignName.trim();
    if (!name) { setStatus("Indique un nom de campagne avant de la créer."); return; }
    setBusy(true);
    try {
      const created = await backend.createCampaign(name);
      await refreshCampaigns();
      setSelectedId(created.id);
      setActive("sync");
      setStatus("Campagne vierge créée. Exporte le contexte complet MJ puis effectue la création du personnage avec le MJ avant toute narration.");
    } catch (e) { setStatus(`Erreur : ${String(e)}`); }
    finally { setBusy(false); }
  }
''',
)
replace(
    app,
    '        defaultPath: isGm ? "Sully_Kitaba_Context_MJ.json" : "Sully_Kitaba_Context_Joueur.json",',
    '        defaultPath: `${campaign.name.replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "") || "Kitaba"}_${isGm ? "Context_MJ" : "Context_Joueur"}.json`,',
)
replace(app, "aucune mort de Sully n'a été confirmée", "aucune mort du personnage n'a été confirmée")
replace(app, 'player_portrait: "Importer le portrait de Sully",', 'player_portrait: "Importer le portrait du personnage",')
replace(app, '"Portrait de Sully importé et intégré aux sauvegardes de campagne."', '"Portrait du personnage importé et intégré aux sauvegardes de campagne."')
replace(app, 'pc.name ?? "Sully"', 'pc.name ?? "Personnage non créé"')
replace(app, '>Portrait de Sully<', '>Portrait du personnage<')
replace(app, "Seuls les lieux connus de Sully peuvent apparaître.", "Seuls les lieux légitimement connus du personnage peuvent apparaître.")
replace(app, "que Sully peut légitimement connaître", "que le personnage peut légitimement connaître")
replace(app, 'placeholder="Rechercher dans ce que Sully connaît…"', 'placeholder="Rechercher dans les connaissances du personnage…"')
replace(app, '<strong>Sully est mort dans la timeline active.</strong>', '<strong>Le personnage est mort dans la timeline active.</strong>')
replace(
    app,
    '''  function renderOverview() {
    const recentJournal = entities.filter((e) => e.entity_type === "journal_entry").slice(-5).reverse();''',
    '''  function renderOverview() {
    if (!characterInitialized) return <section className="panel empty-state"><div className="eyebrow">Phase de création</div><h2>Personnage non initialisé</h2><p>Cette campagne est volontairement vierge. Exporte le contexte complet MJ, termine la création du personnage avec le MJ, puis importe le premier KITABA_UPDATE avant de commencer la narration.</p><p className="muted">Le Companion ne doit jamais inventer le nom, l'âge, l'espèce, l'apparence, les proches ou les connaissances de départ.</p><button onClick={() => setActive("sync")}>Ouvrir la synchronisation</button></section>;
    const recentJournal = entities.filter((e) => e.entity_type === "journal_entry").slice(-5).reverse();''',
)
replace(
    app,
    '''  function renderSync() {
    return <>
      <section className="grid two">''',
    '''  function renderSync() {
    return <>
      {!characterInitialized && <section className="panel onboarding-panel"><div className="eyebrow">Démarrage d'une campagne neuve</div><h2>Création du personnage avant la scène 1</h2><p>1. Exporte le contexte complet MJ de cette campagne vierge. 2. Dans le chat de jeu, crée le personnage et fixe son apparence ainsi que son ancrage immédiat. 3. Importe le premier KITABA_UPDATE d'initialisation. 4. Commence seulement ensuite la narration.</p><div className="warning">Aucun concept du monde ne doit être supposé connu du joueur. Le MJ doit introduire naturellement le vocabulaire, les lieux, les proches et les règles découvertes.</div></section>}
      <section className="grid two">''',
)
replace(
    app,
    '''        {!campaign ? <><section className="panel empty-state"><h2>Créer la campagne de Sully</h2><p>Le Companion crée uniquement le conteneur de campagne. Il n'invente aucune statistique, relation, aptitude ou élément de lore.</p><div className="action-row"><button onClick={createSullyCampaign} disabled={busy}>Créer la campagne</button><button className="secondary" onClick={restoreBackup}>Restaurer un fichier .kitaba</button></div></section>{renderArchivedCampaigns()}</> : renderSection()}''',
    '''        {!campaign ? <><section className="panel empty-state"><h2>Nouvelle campagne Kitaba Solo</h2><p>Crée uniquement un conteneur canonique vierge. La création du personnage se fera ensuite avec le MJ avant toute narration.</p><label style={{display:"grid",gap:".45rem",maxWidth:"34rem",margin:"1rem auto"}}>Nom de campagne<input value={newCampaignName} onChange={(e) => setNewCampaignName(e.target.value)} placeholder="Ex. Kitaba Solo — Playtest" /></label><div className="action-row"><button onClick={createCampaign} disabled={busy || !newCampaignName.trim()}>Créer la campagne vierge</button><button className="secondary" onClick={restoreBackup}>Restaurer un fichier .kitaba</button></div></section>{renderArchivedCampaigns()}</> : renderSection()}''',
)

# --- Continuity contract: onboarding + knowledge discipline ---------------
rules_tail_rust = '                "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed."\n'
replace(
    "src-tauri/src/db.rs",
    rules_tail_rust,
    '                "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed.",\n'
    '                "For a fresh campaign with no player_character, complete character creation and starting-world anchoring before the first narrated gameplay scene.",\n'
    '                "Never assume the human player knows developer or world terminology. Introduce unfamiliar concepts diegetically and contextually when first encountered, even if the character would regard them as ordinary.",\n'
    '                "The initial campaign update must persist the player_character, immediate known setting, relevant close relations and baseline knowledge actually possessed by the character before gameplay begins.",\n'
    '                "Do not generate or import a character/PNJ portrait until the represented person\'s appearance has been canonically fixed; an illustration never creates canon by itself."\n'
)
rules_tail_py = '                    "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed."\n'
replace(
    "reference/engine.py",
    rules_tail_py,
    '                    "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed.",\n'
    '                    "For a fresh campaign with no player_character, complete character creation and starting-world anchoring before the first narrated gameplay scene.",\n'
    '                    "Never assume the human player knows developer or world terminology. Introduce unfamiliar concepts diegetically and contextually when first encountered, even if the character would regard them as ordinary.",\n'
    '                    "The initial campaign update must persist the player_character, immediate known setting, relevant close relations and baseline knowledge actually possessed by the character before gameplay begins.",\n'
    '                    "Do not generate or import a character/PNJ portrait until the represented person\'s appearance has been canonically fixed; an illustration never creates canon by itself."\n'
)

# --- Regression tests ------------------------------------------------------
test_file = ROOT / "reference/tests/test_project_parity.py"
tests = test_file.read_text(encoding="utf-8")
addition = r'''


def test_fresh_campaign_ui_is_generic_and_requires_character_creation_before_play():
    app = _read("src/App.tsx")
    assert "Nouvelle campagne Kitaba Solo" in app
    assert "Créer la campagne vierge" in app
    assert "Création du personnage avant la scène 1" in app
    assert "createSullyCampaign" not in app
    assert 'backend.createCampaign("Sully — Kitaba Solo")' not in app
    assert '"Personnage non créé"' in app


def test_companion_contract_teaches_onboarding_and_player_knowledge_discipline():
    rust = _read("src-tauri/src/db.rs")
    py = _read("reference/engine.py")
    phrases = [
        "complete character creation and starting-world anchoring before the first narrated gameplay scene",
        "Never assume the human player knows developer or world terminology",
        "initial campaign update must persist the player_character",
        "appearance has been canonically fixed",
    ]
    for phrase in phrases:
        assert phrase in rust
        assert phrase in py


def test_frontend_has_no_sully_specific_runtime_copy():
    app = _read("src/App.tsx")
    forbidden = [
        "Créer la campagne de Sully",
        "Portrait de Sully",
        "Sully est mort",
        "ce que Sully connaît",
        "lieux connus de Sully",
    ]
    for text in forbidden:
        assert text not in app
'''
if "test_fresh_campaign_ui_is_generic_and_requires_character_creation_before_play" in tests:
    raise SystemExit("reference/tests/test_project_parity.py: onboarding tests already present")
test_file.write_text(tests.rstrip() + addition + "\n", encoding="utf-8")

# --- Documentation ---------------------------------------------------------
readme = ROOT / "README.md"
text = readme.read_text(encoding="utf-8")
text = text.replace("Version **0.1.3**", "Version **0.1.4**", 1)
needle = "- audit metadata and integrity diagnostics\n"
if needle not in text:
    raise SystemExit("README.md: expected implemented-list anchor missing")
text = text.replace(needle, needle + "- generic fresh-campaign creation with an explicit pre-narration character-creation gate\n- self-describing onboarding rules requiring diegetic introduction of world terminology and canon-before-image discipline\n", 1)
text = text.replace("A complete 0.1.3 Windows build has passed these gates on GitHub Actions.", "The 0.1.4 Windows build must pass the same gates before release.", 1)
readme.write_text(text, encoding="utf-8")

status = ROOT / "docs/STATUS.md"
text = status.read_text(encoding="utf-8")
text = text.replace("real Sully workflow", "real fresh-campaign workflow")
text = text.replace("Installed-app end-to-end Sully smoke test", "Installed-app end-to-end fresh-campaign smoke test")
text = text.replace("A complete 0.1.3 direct-source Windows build has passed all of these gates. The generated artifact contains both `kitaba-companion.exe` and `Kitaba Companion_0.1.2_x64-setup.exe`.", "The 0.1.4 candidate must pass all of these gates before release. The release artifact must contain both `kitaba-companion.exe` and the 0.1.4 NSIS installer.")
text = text.replace("using the real Sully campaign workflow", "using a brand-new generic campaign workflow")
if "Fresh-campaign character creation gate" not in text:
    text = text.replace("| React shell + sync/import/export UI | IMPLEMENTED+STATIC-TESTED |", "| React shell + sync/import/export UI | IMPLEMENTED+STATIC-TESTED |\n| Fresh-campaign character creation gate | IMPLEMENTED+STATIC-TESTED |\n| Generic campaign naming / no hard-coded protagonist | IMPLEMENTED+STATIC-TESTED |\n| Diegetic terminology + canon-before-image contract rules | IMPLEMENTED+TESTED |")
status.write_text(text, encoding="utf-8")

changelog = ROOT / "CHANGELOG.md"
text = changelog.read_text(encoding="utf-8")
entry = '''# Changelog

## 0.1.4 — fresh-character onboarding

- Removed Sully-specific assumptions from runtime campaign creation, export filenames, search, death, map, world and portrait UI copy.
- Added generic named campaign creation and an explicit pre-narration character-creation gate for fresh campaigns.
- Added onboarding guidance: export the empty GM context, create/anchor the character with the GM, import the initialization update, then begin scene 1.
- Extended the Companion continuity contract so future game chats must introduce unfamiliar world terminology contextually instead of assuming developer knowledge.
- Required the initialization update to persist the protagonist, immediate setting, relevant close relations and legitimate baseline knowledge before gameplay begins.
- Added canon-before-image rules so portraits/scenes cannot invent undecided appearances.
- Added regression tests preventing a return to a hard-coded Sully launch path.

'''
if not text.startswith("# Changelog\n"):
    raise SystemExit("CHANGELOG.md: unexpected header")
text = entry + text[len("# Changelog\n\n"):]
changelog.write_text(text, encoding="utf-8")

print("0.1.4 fresh-character onboarding patch applied")
