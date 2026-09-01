from app.models.audit import AuditLog

def log_action(db, action, actor_id=None, target_type=None, target_id=None, details=None):
    entry = AuditLog(actor_id=actor_id, action=action, target_type=target_type, target_id=target_id, details=details)
    db.add(entry)
    return entry
