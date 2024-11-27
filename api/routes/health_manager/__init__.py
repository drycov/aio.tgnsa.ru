from fastapi import APIRouter, HTTPException, Response

from healthy import Healthy

HealthManager = APIRouter()
health_checker = Healthy()  # Создаем экземпляр класса Healthy


@HealthManager.get("/health/status")
async def get_health_status():
    """
    Возвращает текущий статус всех компонентов.
    """
    try:
        return await health_checker.get_all_statuses()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статусов: {str(e)}")


@HealthManager.get("/health/report")
async def get_health_report():
    """
    Возвращает подробный отчет о состоянии системы в формате JSON.
    """
    try:
        return await health_checker.generate_report()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации отчета: {str(e)}")


@HealthManager.get("/health/report/html")
async def get_health_report_html():
    """
    Возвращает подробный отчет о состоянии системы в формате HTML.
    """
    try:
        html_report = await health_checker.generate_html_report()
        return Response(content=html_report, media_type="text/html")
    except Exception as e:
        return Response(content=f"<h1>Ошибка генерации отчета</h1><p>{str(e)}</p>", media_type="text/html")


@HealthManager.get("/health/component/{component_name}")
async def get_component_status(component_name: str):
    """
    Возвращает статус конкретного компонента по его имени.
    """
    try:
        if component_name not in health_checker.components:
            raise HTTPException(status_code=404, detail=f"Компонент {component_name} не зарегистрирован.")
        return await health_checker.get_component_status(component_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка проверки компонента {component_name}: {str(e)}")


@HealthManager.post("/health/check")
async def run_health_checks():
    """
    Запускает полную проверку состояния всех компонентов.
    """
    try:
        return await health_checker.perform_health_checks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения проверки состояния: {str(e)}")
