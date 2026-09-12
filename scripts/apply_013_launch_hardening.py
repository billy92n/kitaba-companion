from pathlib import Path


def replace(path: str, old: str, new: str, expected: int = 1) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    count = text.count(old)
    if count != expected:
        raise SystemExit(f"{path}: expected {expected} occurrence(s), found {count}: {old[:120]!r}")
    p.write_text(text.replace(old, new), encoding="utf-8")


# Frontend: dedicated persistent world state + campaign media library.
replace(
    "src/lib/types.ts",
    '  | "knowledge"\n  | "map"',
    '  | "knowledge"\n  | "world"\n  | "media"\n  | "map"',
)
replace(
    "src/components/Sidebar.tsx",
    '  ["knowledge", "Connaissances"],\n  ["map", "Carte"],',
    '  ["knowledge", "Connaissances"],\n  ["world", "Monde"],\n  ["media", "Médiathèque"],\n  ["map", "Carte"],',
)
replace(
    "src/App.tsx",
    '  knowledge: ["knowledge", "rumor", "belief"],\n  map: ["place", "map_marker", "map", "current_location"],',
    '  knowledge: ["knowledge", "rumor", "belief"],\n  world: ["faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"],\n  media: [],\n  map: ["place", "map_marker", "map", "current_location"],',
)
replace(
    "src/App.tsx",
    '  knowledge: "Connaissances",\n  map: "Carte",',
    '  knowledge: "Connaissances",\n  world: "Monde",\n  media: "Médiathèque",\n  map: "Carte",',
)
replace(
    "src/App.tsx",
    '  const [jsonText, setJsonText] = useState("");\n  const [preview, setPreview] = useState<UpdatePreview | null>(null);',
    '  const [jsonText, setJsonText] = useState("");\n  const [rawUpdateVisible, setRawUpdateVisible] = useState(false);\n  const [preview, setPreview] = useState<UpdatePreview | null>(null);',
)
replace(
    "src/App.tsx",
    '  const [portraitUrl, setPortraitUrl] = useState<string | null>(null);',
    '  const [portraitUrl, setPortraitUrl] = useState<string | null>(null);\n  const [mediaPreviewUrl, setMediaPreviewUrl] = useState<string | null>(null);\n  const [mediaPreviewAssetId, setMediaPreviewAssetId] = useState<string | null>(null);',
)

old_search = '''  const searchResults = useMemo(() => {\n    const q = searchQuery.trim().toLocaleLowerCase("fr");\n    if (!q) return [];\n    return entities.filter((entity) => `${entity.entity_type} ${JSON.stringify(entity.data)}`.toLocaleLowerCase("fr").includes(q)).slice(0, 24);\n  }, [entities, searchQuery]);'''
new_search = '''  const searchableEntities = useMemo(() => entities.map((entity) => ({\n    entity,\n    text: `${entity.entity_type} ${JSON.stringify(entity.data)}`.toLocaleLowerCase("fr"),\n  })), [entities]);\n\n  const searchResults = useMemo(() => {\n    const q = searchQuery.trim().toLocaleLowerCase("fr");\n    if (!q) return [];\n    return searchableEntities.filter((row) => row.text.includes(q)).slice(0, 24).map((row) => row.entity);\n  }, [searchQuery, searchableEntities]);'''
replace("src/App.tsx", old_search, new_search)

replace(
    "src/App.tsx",
    '    const [player, rests, audit, assetRows] = await Promise.all([\n      backend.listEntities(campaignId, false),\n      backend.listRestPoints(campaignId),\n      backend.listAuditEvents(campaignId, 30),\n      backend.listAssets(campaignId),\n    ]);',
    '    const [player, rests, audit, assetRows, integrityReport] = await Promise.all([\n      backend.listEntities(campaignId, false),\n      backend.listRestPoints(campaignId),\n      backend.listAuditEvents(campaignId, 30),\n      backend.listAssets(campaignId),\n      backend.campaignIntegrityReport(campaignId),\n    ]);',
)
replace("src/App.tsx", '    setAssets(assetRows);\n    const mapAsset', '    setAssets(assetRows);\n    setIntegrity(integrityReport);\n    const mapAsset')
replace(
    "src/App.tsx",
    '    setGmEntities([]);\n    setGmUnlocked(false);\n    setIntegrity(null);',
    '    setGmEntities([]);\n    setGmUnlocked(false);\n    setMediaPreviewUrl(null);\n    setMediaPreviewAssetId(null);',
)
replace(
    "src/App.tsx",
    '      setPreview(next);\n      setStatus("Structure, révision et timeline validées. L’application transactionnelle effectuera le contrôle final des opérations.");',
    '      setPreview(next);\n      setRawUpdateVisible(false);\n      setStatus("Structure, révision et timeline validées. Le contenu brut reste masqué pour éviter les spoilers MJ.");',
)
replace(
    "src/App.tsx",
    '      setJsonText(text);\n      setPreview(null);\n      setStatus("Fichier KITABA_UPDATE chargé. Clique sur Analyser avant application.");',
    '      setJsonText(text);\n      setRawUpdateVisible(false);\n      setPreview(null);\n      setStatus("Fichier KITABA_UPDATE chargé. Son contenu brut est masqué ; clique sur Analyser avant application.");',
)
replace(
    "src/App.tsx",
    '      setPreview(null);\n      setJsonText("");\n      const note',
    '      setPreview(null);\n      setJsonText("");\n      setRawUpdateVisible(false);\n      const note',
)

old_import_visual = '''  async function importVisual(kind: "world_map" | "player_portrait") {\n    if (!campaign) return;\n    try {\n      const path = await open({\n        title: kind === "world_map" ? "Importer le fond de carte" : "Importer le portrait de Sully",\n        multiple: false,\n        directory: false,\n        filters: [{ name: "Image", extensions: ["png", "jpg", "jpeg", "webp"] }],\n      });\n      if (!path || Array.isArray(path)) return;\n      await backend.importCampaignAsset(campaign.id, kind, path);\n      await refreshCampaignData(campaign.id);\n      setStatus(kind === "world_map" ? "Fond de carte importé et intégré aux sauvegardes de campagne." : "Portrait importé et intégré aux sauvegardes de campagne.");\n    } catch (e) {\n      setStatus(`Import d'image impossible : ${String(e)}`);\n    }\n  }'''
new_import_visual = '''  async function importVisual(kind: "world_map" | "player_portrait" | "npc_portrait" | "other_image") {\n    if (!campaign) return;\n    const titles: Record<typeof kind, string> = {\n      world_map: "Importer le fond de carte",\n      player_portrait: "Importer le portrait de Sully",\n      npc_portrait: "Importer un portrait de PNJ",\n      other_image: "Importer une image de campagne",\n    };\n    try {\n      const path = await open({\n        title: titles[kind],\n        multiple: false,\n        directory: false,\n        filters: [{ name: "Image", extensions: ["png", "jpg", "jpeg", "webp"] }],\n      });\n      if (!path || Array.isArray(path)) return;\n      await backend.importCampaignAsset(campaign.id, kind, path);\n      await refreshCampaignData(campaign.id);\n      setStatus(kind === "world_map" ? "Fond de carte importé et intégré aux sauvegardes de campagne." : kind === "player_portrait" ? "Portrait de Sully importé et intégré aux sauvegardes de campagne." : kind === "npc_portrait" ? "Portrait de PNJ ajouté à la médiathèque de campagne." : "Image ajoutée à la médiathèque de campagne.");\n    } catch (e) {\n      setStatus(`Import d'image impossible : ${String(e)}`);\n    }\n  }\n\n  async function previewMediaAsset(asset: AssetSummary) {\n    if (!campaign) return;\n    try {\n      const url = await backend.readAssetDataUrl(campaign.id, asset.id);\n      setMediaPreviewUrl(url);\n      setMediaPreviewAssetId(asset.id);\n    } catch (e) { setStatus(`Prévisualisation impossible : ${String(e)}`); }\n  }'''
replace("src/App.tsx", old_import_visual, new_import_visual)

old_textarea = '''          <textarea value={jsonText} onChange={(e) => { setJsonText(e.target.value); setPreview(null); }} placeholder={'{ "format": "KITABA_UPDATE", ... }'} />'''
new_textarea = '''          {rawUpdateVisible ? <><div className="warning">Mode collage manuel : le JSON peut contenir des données MJ. Préfère « Charger un fichier » pour conserver les secrets masqués.</div><textarea value={jsonText} onChange={(e) => { setJsonText(e.target.value); setPreview(null); }} placeholder={'{ "format": "KITABA_UPDATE", ... }'} /></> : jsonText ? <div className="preview-box"><strong>Payload chargé — contenu brut masqué</strong><p className="muted">Le Companion conserve le fichier en mémoire pour l'analyse sans afficher les opérations MJ.</p><div className="action-row"><button className="ghost" onClick={() => { setRawUpdateVisible(true); setPreview(null); }}>Afficher / modifier le JSON</button><button className="ghost" onClick={() => { setJsonText(""); setPreview(null); setRawUpdateVisible(false); }}>Retirer</button></div></div> : <div className="empty-inline">Charge directement le fichier KITABA_UPDATE. Le contenu brut restera masqué.</div>}'''
replace("src/App.tsx", old_textarea, new_textarea)
old_actions = '''          <div className="action-row"><button className="ghost" onClick={loadUpdateFile} disabled={busy || Boolean(campaign?.death_pending)}>Charger un fichier</button><button className="secondary" onClick={analyzeUpdate} disabled={busy || !jsonText.trim() || Boolean(campaign?.death_pending)}>Analyser</button>{preview && <button onClick={importUpdate} disabled={busy || Boolean(campaign?.death_pending)}>Appliquer la mise à jour</button>}</div>'''
new_actions = '''          <div className="action-row"><button className="ghost" onClick={loadUpdateFile} disabled={busy || Boolean(campaign?.death_pending)}>Charger un fichier</button><button className="ghost" onClick={() => setRawUpdateVisible(true)} disabled={busy || Boolean(campaign?.death_pending) || Boolean(jsonText)}>Collage manuel (avancé)</button><button className="secondary" onClick={analyzeUpdate} disabled={busy || !jsonText.trim() || Boolean(campaign?.death_pending)}>Analyser</button>{preview && <button onClick={importUpdate} disabled={busy || Boolean(campaign?.death_pending)}>Appliquer la mise à jour</button>}</div>'''
replace("src/App.tsx", old_actions, new_actions)

old_asset_panel = '''      <section className="panel asset-panel"><h2>Visuels de campagne</h2><p className="muted">Les visuels importés sont copiés dans le stockage local de Kitaba et inclus dans les sauvegardes <code>.kitaba</code>.</p><div className="asset-actions"><button className="secondary" onClick={() => importVisual("player_portrait")}>Importer / remplacer le portrait</button><button className="secondary" onClick={() => importVisual("world_map")}>Importer / remplacer la carte</button><span>{assets.length} visuel(s) géré(s) par la campagne</span></div></section>'''
new_asset_panel = '''      <section className="panel asset-panel"><h2>Visuels de campagne</h2><p className="muted">Les visuels importés sont copiés dans le stockage local de Kitaba et inclus dans les sauvegardes <code>.kitaba</code>.</p><div className="asset-actions"><button className="secondary" onClick={() => importVisual("player_portrait")}>Importer / remplacer le portrait</button><button className="secondary" onClick={() => importVisual("world_map")}>Importer / remplacer la carte</button><button className="secondary" onClick={() => importVisual("npc_portrait")}>Ajouter portrait PNJ</button><button className="secondary" onClick={() => importVisual("other_image")}>Ajouter image</button><span>{assets.length} visuel(s) géré(s) par la campagne</span></div></section>'''
replace("src/App.tsx", old_asset_panel, new_asset_panel)

render_anchor = "  function renderGmVault() {"
media_fn = '''  function renderMedia() {\n    return <section className="panel"><h2>Médiathèque de campagne</h2><p className="muted">Portraits et illustrations conservés localement et inclus dans les sauvegardes. Les illustrations d'ambiance ne modifient jamais le canon à elles seules.</p><div className="action-row"><button className="secondary" onClick={() => importVisual("npc_portrait")}>Ajouter un portrait PNJ</button><button className="secondary" onClick={() => importVisual("other_image")}>Ajouter une illustration</button><button className="ghost" onClick={() => importVisual("player_portrait")}>Portrait de Sully</button><button className="ghost" onClick={() => importVisual("world_map")}>Carte du monde</button></div>{assets.length === 0 ? <div className="empty-inline">Aucun visuel importé.</div> : <div className="audit-list">{assets.map((asset) => <div className="audit-row" key={asset.id}><div><strong>{asset.kind.replaceAll("_", " ")}</strong><span>{new Date(asset.created_at).toLocaleString("fr-FR")}</span></div><button className="ghost small" onClick={() => previewMediaAsset(asset)}>{mediaPreviewAssetId === asset.id ? "Actualiser" : "Voir"}</button></div>)}</div>}{mediaPreviewUrl && <div style={{marginTop: "1rem", textAlign: "center"}}><img src={mediaPreviewUrl} alt="Prévisualisation du visuel sélectionné" style={{maxWidth: "100%", maxHeight: "70vh", objectFit: "contain", borderRadius: ".6rem"}} /></div>}</section>;\n  }\n\n'''
replace("src/App.tsx", render_anchor, media_fn + render_anchor)
replace(
    "src/App.tsx",
    '    if (active === "map") return renderMap();\n    if (active === "character")',
    '    if (active === "map") return renderMap();\n    if (active === "world") return <section className="panel"><h2>État du monde connu</h2><p className="muted">Factions, institutions, marchés, conflits, villes et autres changements durables que Sully peut légitimement connaître. Les évolutions hors champ inconnues restent dans le Coffre MJ.</p><EntityList entities={sectionEntities} empty="Aucun état mondial connu n\\'est encore enregistré." /></section>;\n    if (active === "media") return renderMedia();\n    if (active === "character")',
)

# Self-describing Companion contract: World State is first-class and can remain GM-only.
world_entry = '                "world": ["faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"],\n'
replace(
    "src-tauri/src/db.rs",
    '                "knowledge": ["knowledge", "rumor", "belief"],\n                "map":',
    '                "knowledge": ["knowledge", "rumor", "belief"],\n' + world_entry + '                "map":',
)
replace(
    "src-tauri/src/db.rs",
    '                "Store repeated dead-timeline material resolutions in dead_timeline_resolutions with stable fingerprints."',
    '                "Store repeated dead-timeline material resolutions in dead_timeline_resolutions with stable fingerprints.",\n                "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed."',
)
py_world_entry = '                    "world": ["faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"],\n'
replace(
    "reference/engine.py",
    '                    "knowledge": ["knowledge", "rumor", "belief"],\n                    "map":',
    '                    "knowledge": ["knowledge", "rumor", "belief"],\n' + py_world_entry + '                    "map":',
)
replace(
    "reference/engine.py",
    '                    "Store repeated dead-timeline material resolutions in dead_timeline_resolutions with stable fingerprints."',
    '                    "Store repeated dead-timeline material resolutions in dead_timeline_resolutions with stable fingerprints.",\n                    "Persist durable campaign-world changes, including off-screen changes unknown to the player, as entities. Keep unknown world truth in GM scope until legitimately revealed."',
)

# Regression tests.
engine_test = Path("reference/tests/test_engine.py")
engine_text = engine_test.read_text(encoding="utf-8")
if "def test_world_state_contract_and_hidden_persistence(eng):" not in engine_text:
    engine_text += '''\n\ndef test_world_state_contract_and_hidden_persistence(eng):\n    cid, tid = eng.create_campaign("World state")\n    secret_id = u()\n    eng.apply_update(base_update(\n        cid, tid,\n        gm_operations=[{\n            "op": "create",\n            "entity_type": "faction",\n            "entity_id": secret_id,\n            "data": {"name": "Hidden faction", "status": "SECRET_WORLD_SENTINEL"},\n        }],\n    ))\n    player = eng.export_context(cid, "PLAYER")\n    full = eng.export_context(cid, "GM_FULL")\n    expected = {"faction", "organization", "settlement", "state", "market", "economy_state", "conflict", "world_event", "environment_state", "resource_state", "infrastructure", "law", "political_state"}\n    assert expected <= set(full["companion_contract"]["ui_entity_types"]["world"])\n    assert "SECRET_WORLD_SENTINEL" not in json.dumps(player)\n    assert "SECRET_WORLD_SENTINEL" in json.dumps(full)\n'''
    engine_test.write_text(engine_text, encoding="utf-8")

parity = Path("reference/tests/test_project_parity.py")
parity_text = parity.read_text(encoding="utf-8")
if "def test_sync_ui_masks_raw_update_payload_by_default():" not in parity_text:
    parity_text += '''\n\ndef test_sync_ui_masks_raw_update_payload_by_default():\n    app = _read("src/App.tsx")\n    assert "rawUpdateVisible" in app\n    assert "Payload chargé — contenu brut masqué" in app\n    assert "Collage manuel (avancé)" in app\n    assert "Mode collage manuel" in app\n\n\ndef test_world_state_has_dedicated_player_ui_and_contract():\n    app = _read("src/App.tsx")\n    sidebar = _read("src/components/Sidebar.tsx")\n    rust = _read("src-tauri/src/db.rs")\n    py = _read("reference/engine.py")\n    assert '["world", "Monde"]' in sidebar\n    assert 'world: ["faction", "organization", "settlement"' in app\n    assert '\"world\": [\"faction\", \"organization\", \"settlement\"' in rust\n    assert '\"world\": [\"faction\", \"organization\", \"settlement\"' in py\n'''
    parity.write_text(parity_text, encoding="utf-8")

# Release 0.1.3 metadata (workflow artifact name is updated separately through GitHub API).
for path in ["package.json", "src-tauri/Cargo.toml", "src-tauri/tauri.conf.json"]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if "0.1.2" not in text:
        raise SystemExit(f"{path}: 0.1.2 not found")
    p.write_text(text.replace("0.1.2", "0.1.3"), encoding="utf-8")

lock = Path("src-tauri/Cargo.lock")
lock_text = lock.read_text(encoding="utf-8")
needle = 'name = "kitaba-companion"\nversion = "0.1.2"'
if lock_text.count(needle) != 1:
    raise SystemExit(f"Cargo.lock root package pattern count={lock_text.count(needle)}")
lock.write_text(lock_text.replace(needle, 'name = "kitaba-companion"\nversion = "0.1.3"'), encoding="utf-8")

readme = Path("README.md")
readme.write_text(
    readme.read_text(encoding="utf-8")
    .replace("Version **0.1.2**", "Version **0.1.3**")
    .replace("complete 0.1.2 Windows build", "complete 0.1.3 Windows build"),
    encoding="utf-8",
)
status = Path("docs/STATUS.md")
status.write_text(
    status.read_text(encoding="utf-8").replace(
        "complete 0.1.2 direct-source Windows build",
        "complete 0.1.3 direct-source Windows build",
    ),
    encoding="utf-8",
)

changelog = Path("CHANGELOG.md")
c = changelog.read_text(encoding="utf-8")
entry = '''\n## 0.1.3 — campaign launch hardening\n\n- Added explicit persistent World State entity categories for factions, organizations, settlements, states, markets, economy, conflicts, world events, environment, resources, infrastructure, laws and politics.\n- Added a player-facing World section while keeping unknown/off-screen world truth in GM scope.\n- Hardened ChatGPT update import so file-loaded raw JSON is hidden by default; manual raw-paste mode now carries an explicit spoiler warning.\n- Added a campaign media library entry point for NPC portraits and other illustrations, backed by the existing checksum-protected asset store and `.kitaba` backups.\n- Campaign integrity diagnostics now refresh automatically with campaign data.\n- Reduced search re-serialization work by precomputing searchable entity text only when campaign entities change.\n- Added regression tests for hidden World State persistence and raw-update anti-spoiler UI.\n\n'''
if "## 0.1.3 — campaign launch hardening" not in c:
    changelog.write_text(c.replace("# Changelog\n", "# Changelog\n" + entry, 1), encoding="utf-8")
