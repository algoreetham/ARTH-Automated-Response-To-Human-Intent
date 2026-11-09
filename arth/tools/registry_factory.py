"""Central Tool Registry Factory for ARTH.
Pre-registers all built tools across phases.
"""

from arth.tools.base import ToolRegistry
from arth.tools.test_tool import TestActionTool
from arth.tools.risky_tool import RiskyTestActionTool
from arth.tools.reminders_tool import RemindersTool
from arth.tools.todos_tool import TodosTool
from arth.tools.notes_tool import NotesTool
from arth.tools.clipboard_tool import ClipboardTool
from arth.tools.weather_tool import WeatherTool
from arth.tools.news_tool import NewsTool
from arth.tools.web_search_tool import WebSearchTool
from arth.tools.study_helper_tool import StudyHelperTool
from arth.tools.files_tool import FileManagerTool
from arth.tools.apps_tool import AppControlTool
from arth.tools.status_tool import StatusReportTool
from arth.tools.project_tool import ProjectHelperTool
from arth.tools.gmail_tool import GmailTool
from arth.tools.calendar_tool import CalendarTool


def get_default_registry() -> ToolRegistry:
    """Instantiate and register all available ARTH tools."""
    registry = ToolRegistry()
    registry.register(TestActionTool())
    registry.register(RiskyTestActionTool())
    registry.register(RemindersTool())
    registry.register(TodosTool())
    registry.register(NotesTool())
    registry.register(ClipboardTool())
    registry.register(WeatherTool())
    registry.register(NewsTool())
    registry.register(WebSearchTool())
    registry.register(StudyHelperTool())
    registry.register(FileManagerTool())
    registry.register(AppControlTool())
    registry.register(StatusReportTool())
    registry.register(ProjectHelperTool())
    registry.register(GmailTool())
    registry.register(CalendarTool())
    return registry
