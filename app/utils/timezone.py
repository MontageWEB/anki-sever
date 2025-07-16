"""
时区工具
"""
from datetime import timezone

def fix_timezone_fields(obj):
    """修正对象时间字段的时区信息"""
    time_fields = ['created_at', 'updated_at', 'first_review_at', 'next_review_at']
    for field in time_fields:
        if hasattr(obj, field):
            value = getattr(obj, field)
            if value and value.tzinfo is None:
                setattr(obj, field, value.replace(tzinfo=timezone.utc))

UTC = timezone.utc 