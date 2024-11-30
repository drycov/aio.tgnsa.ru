import asyncio
from datetime import datetime, timedelta
from tabulate import tabulate
import inspect

from proxy.core import generate_token, add_user, list_users


class AsyncProxyAdminShell:
    intro = "Добро пожаловать в Proxy Admin Shell. Введите 'help' для списка команд.\n"
    prompt = "(proxy-admin) "

    async def do_add_user(self, username):
        """Добавить пользователя."""
        token = generate_token()
        expiry_date = datetime.now() + timedelta(days=7)
        try:
            await add_user(username, token, expiry_date)
            print(f"Пользователь '{username}' добавлен с токеном {token}")
        except ValueError as e:
            print(f"Ошибка: {e}")

    async def do_list_users(self, _):
        """Вывести список пользователей."""
        users = await list_users()
        print(tabulate(users, headers=["Имя", "Токен", "Срок действия"], tablefmt="grid"))

    async def do_help(self, _):
        """Показать список доступных команд."""
        commands = [
            (name[3:], method.__doc__.strip() if method.__doc__ else "Описание отсутствует")
            for name, method in inspect.getmembers(self, predicate=inspect.iscoroutinefunction)
            if name.startswith("do_")
        ]
        print("Доступные команды:")
        print(tabulate(commands, headers=["Команда", "Описание"], tablefmt="grid"))

    async def cmdloop(self):
        """Асинхронный цикл команд."""
        print(self.intro)
        while True:
            line = input(self.prompt).strip()
            if line.lower() == "exit":
                break
            elif line.startswith("add_user"):
                parts = line.split(" ", 1)
                if len(parts) < 2 or not parts[1].strip():
                    print("Ошибка: Укажите имя пользователя. Пример: add_user test_user")
                    continue
                await self.do_add_user(parts[1].strip())
            elif line.lower() == "list_users":
                await self.do_list_users(None)
            elif line.lower() == "help":
                await self.do_help(None)
            else:
                print(f"Неизвестная команда: {line}")

async def main():
    shell = AsyncProxyAdminShell()
    await shell.cmdloop()


if __name__ == "__main__":
    asyncio.run(main())