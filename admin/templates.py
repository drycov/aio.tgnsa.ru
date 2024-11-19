from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from app.models import User

template_path = Path(__file__).parent / "templates"
env = Environment(loader=FileSystemLoader(template_path))


class AdminTemplates:
    @staticmethod
    def render_base_template(title: str, body: str) -> str:
        template = env.get_template("base.html")
        return template.render(title=title, body=body)

    # Иконки для статусов
    @staticmethod
    def render_admin_menu() -> str:
        return AdminTemplates.render_base_template("Admin Menu", "<h2>Welcome to the Admin Panel</h2>")

    @staticmethod
    def render_user_page(users: List[User]) -> str:
        template = env.get_template("users.html")
        body = template.render(users=users)
        return AdminTemplates.render_base_template("Manage Users", body)

    @staticmethod
    async def render_status_page(self) -> str:
        health_statuses = await self.perform_health_checks()
        status_icons = self.status_icons
        template = env.get_template("status.html")
        body = template.render(health_statuses=health_statuses, status_icons=status_icons)
        return AdminTemplates.render_base_template("System Status", body)

    @staticmethod
    async def generate_html_report(self) -> str:
        health_statuses = await self.perform_health_checks()
        status_icons = self.status_icons
        template = env.get_template("report.html")
        body = template.render(statuses=health_statuses, status_icons=status_icons)
        return AdminTemplates.render_base_template("Health Report", body)

    @staticmethod
    def render_task_list(self) -> str:
        template = env.get_template("task_list.html")
        body = template.render(tasks=self)
        return AdminTemplates.render_base_template("Task List", body)

    @staticmethod
    def render_task(self) -> str:
        template = env.get_template("task_item.html")
        body = template.render(task=self)
        return AdminTemplates.render_base_template("Task List", body)

    @staticmethod
    def render_schedule_tasks(self) -> str:
        template = env.get_template("schedule_tasks.html")
        body = template.render(tasks=self)
        return AdminTemplates.render_base_template("Job List", body)