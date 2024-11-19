import asyncio
import traceback
from pathlib import Path

from aiohttp import web

from app.models import Task
from app.utils.logger_instance import app_logger
from healthy import Healthy
from .admin_service import AdminService
from .templates import AdminTemplates

static_path = Path(__file__).parent / "static"


@web.middleware
async def error_middleware(request: web.Request, handler) -> web.Response:
    try:
        response = await handler(request)

        # Если response — это dict, преобразуем его в JSON-ответ
        if isinstance(response, dict):
            return web.json_response(response)

        # Если это web.Response с кодом 404, обрабатываем как 404 ошибку
        if isinstance(response, web.Response) and response.status == 404:
            return await handle_404(request)

        return response

    except web.HTTPException as ex:
        app_logger.error(f"HTTP Exception: {ex.status} {request.method} {request.path}")

        # Обработка специфических HTTP ошибок
        if ex.status == 404:
            return await handle_404(request)
        elif ex.status == 500:
            return web.Response(
                text="500: Internal server error",
                content_type="text/html",
                status=500,
            )
        raise  # Если ошибка другая, пробрасываем дальше

    except asyncio.CancelledError:
        app_logger.warning(f"Request cancelled: {request.method} {request.path}")
        raise  # Позволяем отменённым задачам завершиться корректно

    except Exception as e:
        # Логирование необработанных исключений
        app_logger.error(f"Unhandled exception: {traceback.format_exc()}")
        return web.Response(
            text="500: Internal server error",
            content_type="text/html",
            status=500,
        )


# Обработчик для 404 ошибки
async def handle_404(request):
    return web.Response(text="404: Page not found", content_type="text/html", status=404)


@web.middleware
async def logging_middleware(request, handler):
    app_logger.info(f"Incoming request: {request.method} {request.path}")
    try:
        response = await handler(request)
        return response
    except Exception as e:
        app_logger.error(f"Error processing request {request.method} {request.path}: {e}")
        raise


class BaseAPI:
    @staticmethod
    def json_response(data, status=200):
        return web.json_response(data, status=status)

    @staticmethod
    def html_response(html, status=200):
        return web.Response(text=html, content_type="text/html", status=status)


# Создаём класс для работы с Health
class HealthAPI(BaseAPI):
    health_checker = Healthy()

    @staticmethod
    async def get_status(request):
        """
        Возвращает HTML с текущим статусом компонентов системы.
        """
        html = await AdminTemplates.render_status_page(HealthAPI.health_checker)
        return HealthAPI.html_response(html)

    @staticmethod
    async def get_health(request):
        """
        Возвращает JSON с текущими статусами всех компонентов.
        """
        data = await HealthAPI.health_checker.get_all_statuses()
        return HealthAPI.json_response(data)

    @staticmethod
    async def get_health_report(request):
        """
        Возвращает отчёт в формате HTML или JSON.
        """
        report_format = request.query.get("format", "html")
        if report_format == "json":
            data = await HealthAPI.health_checker.generate_report()
            return HealthAPI.json_response(data)
        else:
            html = await AdminTemplates.generate_html_report(HealthAPI.health_checker)
            return HealthAPI.html_response(html)

    @staticmethod
    async def health_action(request):
        data = await request.post()
        action = data.get("action", "")
        if action == "restart":
            await HealthAPI.health_checker.perform_health_checks()
            return web.json_response({"message": "Health checks restarted"})
        elif action == "reload":
            await HealthAPI.health_checker.perform_health_checks()
            return web.json_response({"message": "Health checks reloaded"})
        else:
            return web.json_response({"error": "Invalid action"}, status=400)


# Создаём класс для работы с Admin
class AdminAPI(BaseAPI):
    @staticmethod
    async def render_menu(request):
        """
        Возвращает главное меню админки.
        """
        html = AdminTemplates.render_admin_menu()
        return AdminAPI.html_response(html)

    @staticmethod
    async def render_user_list(request):
        """
        Возвращает список пользователей в HTML.
        """
        users = AdminService.get_all_users()
        html = AdminTemplates.render_user_page(users)
        return AdminAPI.html_response(html)

        # html = await AdminTemplates.render_user_page(users)
        # return AdminAPI.html_response(html)

    @staticmethod
    async def update_user(request):
        """
        Обновляет пользователя (назначает/снимает роль администратора).
        """
        try:
            data = await request.post()
            print(data)  # Выводим данные для дебага
            tg_id = int(data.get("tg_id", 0))
            action = data.get("action", "")
            is_admin = action == "grant_admin"
            user = AdminService.update_user_role(tg_id, is_admin)
            if user:
                return web.json_response({"message": f"User {tg_id} updated"})
            else:
                return web.json_response({"error": "User not found"}, status=404)
        except Exception as e:
            app_logger.error(f"Error updating user: {e}")
            return web.json_response({"error": "Internal server error", "details": str(e)}, status=500)


class TaskApi(BaseAPI):
    @staticmethod
    async def get_tasks(request):
        tasks = Task.get_all()
        html = AdminTemplates.render_task_list(tasks)
        return TaskApi.html_response(html)

    @staticmethod
    async def delete_task(request):
        """
        Удаляет задачу по идентификатору.
        """
        task_id = request.match_info.get("task_id")
        if not task_id:
            return web.json_response({"error": "Task ID is required"}, status=400)

        try:
            Task.delete(task_id)
            return web.json_response({"message": f"Task {task_id} deleted successfully"})
        except Exception as e:
            app_logger.error(f"Error deleting task {task_id}: {e}")
            return web.json_response({"error": "Internal server error", "details": str(e)}, status=500)


# Настройка маршрутов
class SchedulerApi(BaseAPI):
    @staticmethod
    async def get_schedule(request):
        from main import housekeeper
        schedule = housekeeper.get_all_jobs()
        html = AdminTemplates.render_schedule_tasks(schedule)
        return SchedulerApi.html_response(html)

    @staticmethod
    async def get_schedule_by_id(request: web.Request) -> web.Response:
        job_id = request.match_info.get("job_id")

        if not job_id:
            # Возвращаем ошибку, если идентификатор задачи отсутствует
            return web.json_response({"error": "Job ID is required"}, status=400)
        from main import housekeeper
        job = housekeeper.get_job_by_id(job_id)
        if not job:
            # Возвращаем 404, если задача не найдена
            return web.json_response({"error": f"Job with ID {job_id} not found"}, status=404)

        return SchedulerApi.json_response(job)


def setup_routes(app):
    app.router.add_static('/static', path=static_path.resolve(), name='static')
    app.router.add_get("/admin", AdminAPI.render_menu)
    app.router.add_get("/admin/", AdminAPI.render_menu)  # С завершающим слэшем
    app.router.add_get("/admin/users", AdminAPI.render_user_list)
    app.router.add_post("/admin/users", AdminAPI.update_user)
    app.router.add_post("/admin/action", AdminAPI.update_user)
    app.router.add_get("/health", HealthAPI.get_health)
    app.router.add_get("/health/status", HealthAPI.get_status)
    app.router.add_get("/health/report", HealthAPI.get_health_report)
    app.router.add_post("/health/action", HealthAPI.health_action)
    app.router.add_get("/tasks", TaskApi.get_tasks)
    app.router.add_delete("/tasks/delete/{task_id}", TaskApi.delete_task)
    app.router.add_get("/schedule", SchedulerApi.get_schedule)
    app.router.add_get("/schedule/{job_id}", SchedulerApi.get_schedule_by_id)
    app.router.add_get("/{tail:.*}", handle_404)  # Обработчик всех неизвестных маршрутов


def create_app():
    """
    Создаёт экземпляр приложения aiohttp.
    """
    app = web.Application(middlewares=[logging_middleware, error_middleware])
    setup_routes(app)  # Добавление маршрутов
    return app


# Запуск сервера
def run(host="127.0.0.1", port=8000):
    app = create_app()  # Получаем приложение из create_app
    app_logger.info(f"Health API server running on port {port}")
    web.run_app(app, host=host, port=port, print=None)


def stop_server():
    app = create_app()  # Получаем приложение из create_app
    if app is None:
        app_logger.error("Health API server is not running.")
        return

    app_logger.warning("Stopping Health API server...")
    loop = asyncio.get_event_loop()

    # Остановка планировщика задач, если он используется
    from main import housekeeper  # Подключите ваш планировщик
    housekeeper.scheduler.shutdown(wait=False)

    # Остановка задач
    tasks = asyncio.all_tasks(loop)
    for task in tasks:
        task.cancel()

    try:
        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
    except asyncio.CancelledError:
        pass

    loop.stop()
    loop.close()
    app_logger.info("Health API server stopped.")
