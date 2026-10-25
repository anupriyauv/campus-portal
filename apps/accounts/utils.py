from .models import AuditLog

def log_audit_event(user, action, model_name=None, object_id=None, object_repr=None, change_message=None, ip_address=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=object_id,
        object_repr=object_repr,
        change_message=change_message,
        ip_address=ip_address,
    )