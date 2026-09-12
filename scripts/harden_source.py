from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"Expected source pattern not found in {path}: {old!r}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")


# Keep the ATTACH path owned for the full SQLite call instead of borrowing a
# temporary Cow<str>. This removes a fragile lifetime pattern in restore code.
replace_exact(
    "src-tauri/src/db.rs",
    '            conn.execute("ATTACH DATABASE ?1 AS incoming", [temp_db.to_string_lossy().as_ref()])?;',
    '            let temp_db_owned = temp_db.to_string_lossy().into_owned();\n            conn.execute("ATTACH DATABASE ?1 AS incoming", [&temp_db_owned])?;',
)

# This connection is only passed immutably in the delete command.
replace_exact(
    "src-tauri/src/lib.rs",
    'fn delete_campaign_permanently(campaign_id: String, expected_name: String, state: State<\'_ , DbState>) -> Result<(), KitabaError> {',
    'fn delete_campaign_permanently(campaign_id: String, expected_name: String, state: State<\'_ , DbState>) -> Result<(), KitabaError> {',
) if False else None

p = Path("src-tauri/src/lib.rs")
text = p.read_text(encoding="utf-8")
old = '''fn delete_campaign_permanently(campaign_id: String, expected_name: String, state: State<'_, DbState>) -> Result<(), KitabaError> {\n    let mut conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;'''
new = '''fn delete_campaign_permanently(campaign_id: String, expected_name: String, state: State<'_, DbState>) -> Result<(), KitabaError> {\n    let conn = state.conn.lock().map_err(|_| KitabaError::Validation("database lock poisoned".into()))?;'''
if old not in text:
    raise SystemExit("Expected delete_campaign_permanently mutability pattern not found")
p.write_text(text.replace(old, new, 1), encoding="utf-8")
