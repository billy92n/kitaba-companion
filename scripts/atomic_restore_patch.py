from pathlib import Path

p = Path("src-tauri/src/db.rs")
text = p.read_text(encoding="utf-8")

old_commit = '''    tx.commit()?;\n    for old in old_paths {'''
new_commit = '''    if let Err(err) = tx.commit() {\n        let _ = std::fs::remove_file(&target);\n        return Err(err.into());\n    }\n    for old in old_paths {'''
if old_commit not in text:
    raise SystemExit("import_asset commit pattern not found")
text = text.replace(old_commit, new_commit, 1)

old_restore = '''            let temp_db_owned = temp_db.to_string_lossy().into_owned();
            conn.execute("ATTACH DATABASE ?1 AS incoming", [&temp_db_owned])?;
            let merge_result = (|| -> Result<(), KitabaError> {
                let tx = conn.transaction()?;
                tx.execute_batch("PRAGMA defer_foreign_keys=ON;")?;
                tx.execute("DELETE FROM technical_backups WHERE campaign_id=?1", [cid])?;
                tx.execute("DELETE FROM campaigns WHERE id=?1", [cid])?;
                tx.execute("INSERT INTO campaigns SELECT * FROM incoming.campaigns WHERE id=?1", [cid])?;
                for table in [
                    "timelines", "entity_documents", "entity_links", "applied_updates",
                    "rest_points", "dead_timelines", "dead_timeline_resolutions",
                    "technical_backups", "audit_log", "assets",
                ] {
                    tx.execute(&format!("INSERT INTO {table} SELECT * FROM incoming.{table} WHERE campaign_id=?1"), [cid])?;
                }
                tx.commit()?;
                Ok(())
            })();
            let detach = conn.execute_batch("DETACH DATABASE incoming;");
            merge_result?;
            detach?;

            let destination = asset_root.join(cid);
            if destination.exists() { std::fs::remove_dir_all(&destination)?; }
            copy_dir_recursive(&incoming_asset_dir, &destination)?;'''

new_restore = '''            // Stage the incoming campaign assets on the same filesystem before touching
            // either the canonical database or the currently active asset directory. This
            // makes ordinary I/O failures happen while the old state is still untouched.
            std::fs::create_dir_all(asset_root)?;
            let destination = asset_root.join(cid);
            let swap_token = Uuid::new_v4().to_string();
            let staged_destination = asset_root.join(format!(".restore-stage-{cid}-{swap_token}"));
            let previous_destination = asset_root.join(format!(".restore-previous-{cid}-{swap_token}"));
            std::fs::create_dir_all(&staged_destination)?;
            copy_dir_recursive(&incoming_asset_dir, &staged_destination)?;

            let temp_db_owned = temp_db.to_string_lossy().into_owned();
            conn.execute("ATTACH DATABASE ?1 AS incoming", [&temp_db_owned])?;
            let merge_result = (|| -> Result<(), KitabaError> {
                let tx = conn.transaction()?;
                tx.execute_batch("PRAGMA defer_foreign_keys=ON;")?;
                tx.execute("DELETE FROM technical_backups WHERE campaign_id=?1", [cid])?;
                tx.execute("DELETE FROM campaigns WHERE id=?1", [cid])?;
                tx.execute("INSERT INTO campaigns SELECT * FROM incoming.campaigns WHERE id=?1", [cid])?;
                for table in [
                    "timelines", "entity_documents", "entity_links", "applied_updates",
                    "rest_points", "dead_timelines", "dead_timeline_resolutions",
                    "technical_backups", "audit_log", "assets",
                ] {
                    tx.execute(&format!("INSERT INTO {table} SELECT * FROM incoming.{table} WHERE campaign_id=?1"), [cid])?;
                }

                // Keep the SQLite transaction open while swapping the filesystem state.
                // If activation fails, dropping tx rolls the DB back. If SQLite commit
                // fails after activation, restore the previous asset directory immediately.
                let had_previous_assets = destination.exists();
                if had_previous_assets {
                    std::fs::rename(&destination, &previous_destination)?;
                }
                if let Err(err) = std::fs::rename(&staged_destination, &destination) {
                    if had_previous_assets {
                        let _ = std::fs::rename(&previous_destination, &destination);
                    }
                    return Err(err.into());
                }

                if let Err(err) = tx.commit() {
                    let _ = std::fs::remove_dir_all(&destination);
                    if had_previous_assets {
                        let _ = std::fs::rename(&previous_destination, &destination);
                    }
                    return Err(err.into());
                }

                if previous_destination.exists() {
                    let _ = std::fs::remove_dir_all(&previous_destination);
                }
                Ok(())
            })();
            let detach = conn.execute_batch("DETACH DATABASE incoming;");
            if staged_destination.exists() { let _ = std::fs::remove_dir_all(&staged_destination); }
            if merge_result.is_err() && previous_destination.exists() && !destination.exists() {
                let _ = std::fs::rename(&previous_destination, &destination);
            }
            merge_result?;
            detach?;'''

if old_restore not in text:
    raise SystemExit("campaign restore block not found")
text = text.replace(old_restore, new_restore, 1)

if "rust_core_campaign_backup_restore_preserves_other_campaign_and_assets" in text:
    raise SystemExit("restore regression test already present")

new_test = r'''

    #[test]
    fn rust_core_campaign_backup_restore_preserves_other_campaign_and_assets() {
        let mut conn = setup();
        let sully = create_campaign(&conn, "Sully").unwrap();
        let other = create_campaign(&conn, "Other campaign").unwrap();
        let entity_id = Uuid::new_v4().to_string();
        let initial = update_json(
            &sully.id,
            &sully.current_timeline_id,
            0,
            json!([{"op":"create","entity_type":"player_character","entity_id":entity_id,"data":{"first_name":"Sully","age":8}}]),
            json!([]),
        );
        apply_update(&mut conn, &initial).unwrap();

        let root = std::env::temp_dir().join(format!("kitaba-rust-restore-test-{}", Uuid::new_v4()));
        let asset_root = root.join("assets");
        std::fs::create_dir_all(&root).unwrap();
        let original_image = root.join("original.png");
        let original_bytes = b"\x89PNG\r\n\x1a\nkitaba-original";
        std::fs::write(&original_image, original_bytes).unwrap();
        let original_asset = import_asset(&conn, &sully.id, "world_map", &original_image, &asset_root).unwrap();

        let backup = root.join("sully.kitaba");
        create_technical_backup(&conn, Some(&sully.id), &backup, "test", &asset_root).unwrap();

        let changed = update_json(
            &sully.id,
            &sully.current_timeline_id,
            1,
            json!([{"op":"patch","entity_type":"player_character","entity_id":entity_id,"data":{"first_name":"Changed"}}]),
            json!([]),
        );
        apply_update(&mut conn, &changed).unwrap();
        let replacement_image = root.join("replacement.png");
        std::fs::write(&replacement_image, b"\x89PNG\r\n\x1a\nreplacement").unwrap();
        import_asset(&conn, &sully.id, "world_map", &replacement_image, &asset_root).unwrap();

        restore_technical_backup(&mut conn, &backup, &asset_root).unwrap();

        let restored: (i64, String) = conn.query_row(
            "SELECT current_revision,current_timeline_id FROM campaigns WHERE id=?1",
            [&sully.id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        ).unwrap();
        assert_eq!(restored.0, 1);
        assert_eq!(restored.1, sully.current_timeline_id);
        let restored_name: String = conn.query_row(
            "SELECT json_extract(data_json,'$.first_name') FROM entity_documents WHERE campaign_id=?1 AND id=?2",
            params![sully.id, entity_id],
            |r| r.get(0),
        ).unwrap();
        assert_eq!(restored_name, "Sully");

        let other_still_exists: i64 = conn.query_row(
            "SELECT COUNT(*) FROM campaigns WHERE id=?1",
            [&other.id],
            |r| r.get(0),
        ).unwrap();
        assert_eq!(other_still_exists, 1);

        let restored_assets = list_assets(&conn, &sully.id).unwrap();
        assert_eq!(restored_assets.len(), 1);
        assert_eq!(restored_assets[0].id, original_asset.id);
        let restored_path = managed_asset_path(&asset_root, &sully.id, &restored_assets[0].relative_path).unwrap();
        assert_eq!(std::fs::read(restored_path).unwrap(), original_bytes);

        assert_eq!(conn.query_row("PRAGMA integrity_check", [], |r| r.get::<_, String>(0)).unwrap(), "ok");
        let mut fk = conn.prepare("PRAGMA foreign_key_check").unwrap();
        assert!(fk.query([]).unwrap().next().unwrap().is_none());
        let _ = std::fs::remove_dir_all(root);
    }
'''

idx = text.rfind("\n}")
if idx < 0:
    raise SystemExit("test module closing brace not found")
text = text[:idx] + new_test + text[idx:]
p.write_text(text, encoding="utf-8")
