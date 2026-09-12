from pathlib import Path

p = Path("src-tauri/src/db.rs")
text = p.read_text(encoding="utf-8")

old = '''        } else {
            conn.restore(DatabaseName::Main, &temp_db, None::<fn(rusqlite::backup::Progress)>)?;
            migrate(conn)?;
            conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")?;
            if asset_root.exists() { std::fs::remove_dir_all(asset_root)?; }
            copy_dir_recursive(&temp_root.join("assets"), asset_root)?;
        }'''

new = '''        } else {
            // Full-application restore: prepare both rollback material and the incoming
            // filesystem state before replacing anything live.
            let restore_token = Uuid::new_v4().to_string();
            let asset_parent = asset_root.parent().unwrap_or_else(|| std::path::Path::new("."));
            std::fs::create_dir_all(asset_parent)?;
            let staged_assets = asset_parent.join(format!(".full-restore-stage-{restore_token}"));
            let previous_assets = asset_parent.join(format!(".full-restore-previous-{restore_token}"));
            std::fs::create_dir_all(&staged_assets)?;
            copy_dir_recursive(&temp_root.join("assets"), &staged_assets)?;

            let previous_db = std::env::temp_dir().join(format!("kitaba-full-restore-previous-{restore_token}.sqlite"));
            conn.backup(DatabaseName::Main, &previous_db, None)?;

            let had_previous_assets = asset_root.exists();
            if had_previous_assets {
                std::fs::rename(asset_root, &previous_assets)?;
            }
            if let Err(err) = std::fs::rename(&staged_assets, asset_root) {
                if had_previous_assets {
                    let _ = std::fs::rename(&previous_assets, asset_root);
                }
                let _ = std::fs::remove_file(&previous_db);
                return Err(err.into());
            }

            let database_result = (|| -> Result<(), KitabaError> {
                conn.restore(DatabaseName::Main, &temp_db, None::<fn(rusqlite::backup::Progress)>)?;
                migrate(conn)?;
                conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")?;
                Ok(())
            })();

            if let Err(restore_error) = database_result {
                let recovery_result = (|| -> Result<(), KitabaError> {
                    conn.restore(DatabaseName::Main, &previous_db, None::<fn(rusqlite::backup::Progress)>)?;
                    migrate(conn)?;
                    conn.execute_batch("PRAGMA foreign_keys=ON; PRAGMA journal_mode=WAL;")?;
                    Ok(())
                })();
                let _ = std::fs::remove_dir_all(asset_root);
                if had_previous_assets {
                    let _ = std::fs::rename(&previous_assets, asset_root);
                }
                let _ = std::fs::remove_file(&previous_db);
                if let Err(recovery_error) = recovery_result {
                    return Err(KitabaError::Validation(format!(
                        "full restore failed ({restore_error}); automatic rollback also failed ({recovery_error})"
                    )));
                }
                return Err(restore_error);
            }

            if previous_assets.exists() { let _ = std::fs::remove_dir_all(&previous_assets); }
            let _ = std::fs::remove_file(&previous_db);
        }'''

if old not in text:
    raise SystemExit("full restore block not found")
text = text.replace(old, new, 1)

if "rust_core_full_backup_restore_roundtrip_with_assets" in text:
    raise SystemExit("full restore regression test already present")

new_test = r'''

    #[test]
    fn rust_core_full_backup_restore_roundtrip_with_assets() {
        let mut conn = setup();
        let sully = create_campaign(&conn, "Sully").unwrap();
        let other = create_campaign(&conn, "Other").unwrap();
        let sully_entity = Uuid::new_v4().to_string();
        let other_entity = Uuid::new_v4().to_string();
        apply_update(&mut conn, &update_json(
            &sully.id, &sully.current_timeline_id, 0,
            json!([{"op":"create","entity_type":"player_character","entity_id":sully_entity,"data":{"first_name":"Sully","age":8}}]),
            json!([]),
        )).unwrap();
        apply_update(&mut conn, &update_json(
            &other.id, &other.current_timeline_id, 0,
            json!([{"op":"create","entity_type":"player_character","entity_id":other_entity,"data":{"first_name":"Other"}}]),
            json!([]),
        )).unwrap();

        let root = std::env::temp_dir().join(format!("kitaba-rust-full-restore-test-{}", Uuid::new_v4()));
        let asset_root = root.join("assets");
        std::fs::create_dir_all(&root).unwrap();
        let sully_image = root.join("sully.png");
        let other_image = root.join("other.png");
        let sully_bytes = b"\x89PNG\r\n\x1a\nfull-sully-original";
        let other_bytes = b"\x89PNG\r\n\x1a\nfull-other-original";
        std::fs::write(&sully_image, sully_bytes).unwrap();
        std::fs::write(&other_image, other_bytes).unwrap();
        import_asset(&conn, &sully.id, "world_map", &sully_image, &asset_root).unwrap();
        import_asset(&conn, &other.id, "player_portrait", &other_image, &asset_root).unwrap();

        let backup = root.join("full.kitaba");
        create_technical_backup(&conn, None, &backup, "full-test", &asset_root).unwrap();

        apply_update(&mut conn, &update_json(
            &sully.id, &sully.current_timeline_id, 1,
            json!([{"op":"patch","entity_type":"player_character","entity_id":sully_entity,"data":{"first_name":"Changed Sully"}}]),
            json!([]),
        )).unwrap();
        apply_update(&mut conn, &update_json(
            &other.id, &other.current_timeline_id, 1,
            json!([{"op":"patch","entity_type":"player_character","entity_id":other_entity,"data":{"first_name":"Changed Other"}}]),
            json!([]),
        )).unwrap();
        std::fs::remove_dir_all(&asset_root).unwrap();
        std::fs::create_dir_all(&asset_root).unwrap();

        restore_technical_backup(&mut conn, &backup, &asset_root).unwrap();

        let sully_name: String = conn.query_row(
            "SELECT json_extract(data_json,'$.first_name') FROM entity_documents WHERE campaign_id=?1 AND id=?2",
            params![sully.id, sully_entity], |r| r.get(0),
        ).unwrap();
        let other_name: String = conn.query_row(
            "SELECT json_extract(data_json,'$.first_name') FROM entity_documents WHERE campaign_id=?1 AND id=?2",
            params![other.id, other_entity], |r| r.get(0),
        ).unwrap();
        assert_eq!(sully_name, "Sully");
        assert_eq!(other_name, "Other");

        for (cid, expected) in [(&sully.id, sully_bytes.as_slice()), (&other.id, other_bytes.as_slice())] {
            let assets = list_assets(&conn, cid).unwrap();
            assert_eq!(assets.len(), 1);
            let path = managed_asset_path(&asset_root, cid, &assets[0].relative_path).unwrap();
            assert_eq!(std::fs::read(path).unwrap(), expected);
        }
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
