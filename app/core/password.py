import secrets
import string


def generate_password(
    length: int = 16,
    use_uppercase: bool = True,
    use_lowercase: bool = True,
    use_digits: bool = True,
    use_special: bool = True,
    special_chars: str = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
) -> str:
    """
    Генерация криптографически стойкого пароля с возможностью настройки символов.

    Args:
        length: Длина пароля.
        use_uppercase: Включать заглавные буквы.
        use_lowercase: Включать строчные буквы.
        use_digits: Включать цифры.
        use_special: Включать специальные символы.
        special_chars: Набор спецсимволов.

    Returns:
        Сгенерированный пароль.
    """
    if length < 4:
        raise ValueError(
            "Длина пароля должна быть не менее 4 символов для безопасности")

    charset = ""
    if use_uppercase:
        charset += string.ascii_uppercase
    if use_lowercase:
        charset += string.ascii_lowercase
    if use_digits:
        charset += string.digits
    if use_special:
        charset += special_chars

    if not charset:
        raise ValueError(
            "Должен быть хотя бы один тип символов для генерации пароля")

    # Гарантируем, что пароль содержит хотя бы один символ каждого выбранного типа
    password_chars = []

    if use_uppercase:
        password_chars.append(secrets.choice(string.ascii_uppercase))
    if use_lowercase:
        password_chars.append(secrets.choice(string.ascii_lowercase))
    if use_digits:
        password_chars.append(secrets.choice(string.digits))
    if use_special:
        password_chars.append(secrets.choice(special_chars))

    # Остальную часть пароля добираем случайными символами из всего набора
    remaining_length = length - len(password_chars)
    password_chars.extend(secrets.choice(charset)
                          for _ in range(remaining_length))

    # Перемешиваем символы, чтобы не было шаблонов
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)
