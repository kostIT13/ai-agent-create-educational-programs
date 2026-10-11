"""Детерминированные проверки графа курса (переиспользуются Critic'ом позже)."""

from validators.course import (
    check_hours_total,
    check_outcomes_referenced,
    check_prereq_cycles,
    validate_course,
)

__all__ = [
    "check_hours_total",
    "check_outcomes_referenced",
    "check_prereq_cycles",
    "validate_course",
]