use thiserror::Error;

#[derive(Debug, Error)]
pub enum KitabaError {
    #[error("Database error: {0}")]
    Database(#[from] rusqlite::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("Invalid KITABA_UPDATE: {0}")]
    Validation(String),
    #[error("Campaign not found")]
    CampaignNotFound,
    #[error("Update already applied")]
    DuplicateUpdate,
    #[error("Revision conflict: local={local}, update={incoming}")]
    RevisionConflict { local: i64, incoming: i64 },
    #[error("Timeline conflict")]
    TimelineConflict,
    #[error("Entity conflict: {0}")]
    EntityConflict(String),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
}

impl serde::Serialize for KitabaError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        serializer.serialize_str(&self.to_string())
    }
}
