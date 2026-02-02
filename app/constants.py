"""应用枚举常量"""
from enum import Enum


class UserType(str, Enum):
    """用户类型"""

    CANDIDATE = "candidate"
    ADMIN = "admin"


class ApplicationStatus(str, Enum):
    """投递状态"""

    PARSING = "PARSING"
    PARSED = "PARSED"
    SCORING = "SCORING"
    SCORED = "SCORED"
    QUESTIONS_READY = "QUESTIONS_READY"
    HUMAN_REVIEW = "HUMAN_REVIEW"
    REJECTED = "REJECTED"
    NEXT_ROUND = "NEXT_ROUND"
    CANCELLED = "CANCELLED"  # 候选人取消投递


class TaskStatus(str, Enum):
    """任务状态"""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


class FileType(str, Enum):
    """文件类型"""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


# 状态转移规则
VALID_STATUS_TRANSITIONS = {
    ApplicationStatus.PARSING: [ApplicationStatus.PARSED, ApplicationStatus.HUMAN_REVIEW, ApplicationStatus.CANCELLED],
    ApplicationStatus.PARSED: [
        ApplicationStatus.SCORING,
        ApplicationStatus.HUMAN_REVIEW,
        ApplicationStatus.CANCELLED,
    ],
    ApplicationStatus.SCORING: [
        ApplicationStatus.SCORED,
        ApplicationStatus.HUMAN_REVIEW,
        ApplicationStatus.CANCELLED,
    ],
    ApplicationStatus.SCORED: [
        ApplicationStatus.QUESTIONS_READY,
        ApplicationStatus.HUMAN_REVIEW,
        ApplicationStatus.CANCELLED,
    ],
    ApplicationStatus.QUESTIONS_READY: [
        ApplicationStatus.QUESTIONS_READY,
        ApplicationStatus.HUMAN_REVIEW,
        ApplicationStatus.CANCELLED,
    ],
    ApplicationStatus.HUMAN_REVIEW: [
        ApplicationStatus.PARSING,
        ApplicationStatus.SCORING,
        ApplicationStatus.QUESTIONS_READY,
        ApplicationStatus.CANCELLED,
    ],
    ApplicationStatus.REJECTED: [],
    ApplicationStatus.NEXT_ROUND: [],
    ApplicationStatus.CANCELLED: [],  # 已取消状态不允许再转移
}
