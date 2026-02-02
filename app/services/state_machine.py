"""状态机服务"""
from app.constants import ApplicationStatus, VALID_STATUS_TRANSITIONS


class StateMachineService:
    """应用状态转移服务"""

    @staticmethod
    def can_transition(
        current_status: ApplicationStatus, next_status: ApplicationStatus
    ) -> bool:
        """检查状态转移是否合法"""
        if current_status == next_status:
            return True
        valid_nexts = VALID_STATUS_TRANSITIONS.get(current_status, [])
        return next_status in valid_nexts

    @staticmethod
    def transition(
        current_status: ApplicationStatus, next_status: ApplicationStatus
    ) -> bool:
        """执行状态转移（仅校验，不做副作用）"""
        return StateMachineService.can_transition(current_status, next_status)


def transition_status(current_status: str, new_status: str) -> str:
    """
    状态转移辅助函数
    
    Args:
        current_status: 当前状态（字符串）
        new_status: 目标状态（字符串）
        
    Returns:
        str: 新状态
        
    Raises:
        ValueError: 状态转移不合法时抛出
    """
    try:
        current = ApplicationStatus(current_status)
        new = ApplicationStatus(new_status)
    except ValueError as e:
        raise ValueError(f"无效的状态: {e}")
    
    if not StateMachineService.can_transition(current, new):
        valid_next = VALID_STATUS_TRANSITIONS.get(current, [])
        raise ValueError(
            f"状态转移不合法: {current_status} -> {new_status}. "
            f"允许的转移: {[s.value for s in valid_next]}"
        )
    
    return new.value
