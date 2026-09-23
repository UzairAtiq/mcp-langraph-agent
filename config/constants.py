from enum import Enum

# centralized post status enumeration
class PostStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DISCARDED = "discarded"
    PUBLISHED = "published"
    REJECTED = "rejected"
    PUBLISH_FAILED = "publish_failed"
