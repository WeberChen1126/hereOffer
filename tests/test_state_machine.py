"""状态机测试"""
import pytest
from app.constants import ApplicationStatus
from app.services.state_machine import StateMachineService


def test_valid_transition():
    """测试合法转移"""
    assert StateMachineService.can_transition(
        ApplicationStatus.PARSING, ApplicationStatus.PARSED
    )
    assert StateMachineService.can_transition(
        ApplicationStatus.PARSED, ApplicationStatus.SCORING
    )
    assert StateMachineService.can_transition(
        ApplicationStatus.SCORING, ApplicationStatus.SCORED
    )
    assert StateMachineService.can_transition(
        ApplicationStatus.SCORED, ApplicationStatus.QUESTIONS_READY
    )


def test_invalid_transition():
    """测试非法转移"""
    assert not StateMachineService.can_transition(
        ApplicationStatus.PARSING, ApplicationStatus.QUESTIONS_READY
    )
    assert not StateMachineService.can_transition(
        ApplicationStatus.PARSED, ApplicationStatus.PARSING
    )


def test_same_state_transition():
    """测试相同状态转移"""
    assert StateMachineService.can_transition(
        ApplicationStatus.QUESTIONS_READY, ApplicationStatus.QUESTIONS_READY
    )


def test_human_review_transition():
    """测试进入人工审核"""
    assert StateMachineService.can_transition(
        ApplicationStatus.PARSING, ApplicationStatus.HUMAN_REVIEW
    )
    assert StateMachineService.can_transition(
        ApplicationStatus.SCORED, ApplicationStatus.HUMAN_REVIEW
    )
    # 从 HUMAN_REVIEW 可以回到 PARSING
    assert StateMachineService.can_transition(
        ApplicationStatus.HUMAN_REVIEW, ApplicationStatus.PARSING
    )
