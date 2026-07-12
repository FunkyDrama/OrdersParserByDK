"""Runtime message catalog (gettext-style)."""

LANGUAGES = ("en", "ru", "uk")

_current_language = "en"


def set_language(code: str) -> None:
    """Selects the language for all subsequent runtime messages."""
    global _current_language
    if code in LANGUAGES:
        _current_language = code


def get_language() -> str:
    """The currently selected runtime-message language."""
    return _current_language


def tr(key: str, **kwargs: object) -> str:
    """Translates a message template and interpolates the data values.

    ``key`` is the English source text. Unknown keys fall back to the key
    itself, so a missing translation can never crash processing.
    """
    catalog = _CATALOG.get(_current_language)
    template = catalog.get(key, key) if catalog else key
    return template.format(**kwargs) if kwargs else template


_RU = {
    # --- banners ---
    "New order": "Новый заказ",
    # --- field labels ---
    "Processing date": "Дата обработки заказа",
    "Order ID": "Номер заказа",
    "Shop name": "Название магазина",
    "Product title": "Название товара",
    "Item SKU": "SKU товара",
    "Quantity": "Количество",
    "Customization": "Кастомизация",
    "Customer address": "Адрес клиента",
    "Shipping address": "Адрес доставки",
    "Ship by": "Заказ отправить до",
    "Items total": "Общая сумма за товары",
    "Order total": "Сумма заказа",
    "Total": "Тотал",
    "Shipping paid by us": "Сумма, уплаченная нами за доставку",
    "Shipping price charged": "Установленная цена за доставку",
    "Shipping method": "Тип доставки",
    "Carrier": "Почтовая служба",
    "Carrier (label bought outside Etsy)": "Почтовая служба (если доставка куплена не на Etsy)",
    "Tracking number": "Трек-номер",
    "Tracking number (label bought outside Amazon)": "Трек-номер, если шиплейбл куплен не на Амазон",
    "Tracking link": "Ссылка на отслеживание",
    "Listing link": "Ссылка на листинг",
    "Product size": "Размер товара",
    "Shipping label uploaded": "Шиплейбл загружен",
    # --- problems ---
    "||| The address is too long/short, could not process it |||": "||| Адрес слишком длинный/короткий, не удалось обработать |||",
    "||| Order {number}: marketplace not recognized, skipping |||": "||| Заказ {number}: маркетплейс не распознан, пропускаю |||",
    "||| Order not added: the parser found no items in the HTML |||": "||| Заказ не добавлен: парсер не нашел товары в HTML |||",
    "||| Order skipped, moving on to the next one |||": "||| Заказ пропущен, перехожу к следующему |||",
    "||| No listing links found |||": "||| Не найдено ни одной ссылки на листинг |||",
    "||| Could not find the listing link |||": "||| Не смог найти ссылку на листинг |||",
    "||| Could not get the SKU |||": "||| Не смог получить SKU |||",
    "||| Could not get the shipping address |||": "||| Не смог получить адрес доставки |||",
    "||| Could not get the customer address |||": "||| Не смог получить адрес клиента |||",
    "||| Could not get the customization, it may not be specified |||": "||| Не смог получить кастомизацию, возможно, она не указана |||",
    "||| Could not get the quantity |||": "||| Не смог получить количество |||",
    "||| Could not get the smaller size for sheet routing |||": "||| Не смог получить меньший размер для сортировки |||",
    "||| Could not get the listing title |||": "||| Не смог получить название листинга |||",
    "||| Could not get the shop name |||": "||| Не смог получить название магазина |||",
    "||| Could not get the carrier name |||": "||| Не смог получить название почтовой службы |||",
    "||| Could not get the order ID |||": "||| Не смог получить ID заказа |||",
    "||| Could not get the items total |||": "||| Не смог получить общую сумму за товары |||",
    "||| Could not get the product size |||": "||| Не смог получить размер товара |||",
    "||| Could not get the carrier |||": "||| Не смог получить службу доставки |||",
    "||| Could not get the tracking link |||": "||| Не смог получить ссылку на отслеживание |||",
    "||| Could not get the order total |||": "||| Не смог получить сумму заказа |||",
    "||| Could not get the shipping amount we paid |||": "||| Не смог получить сумму, уплаченную нами за доставку |||",
    "||| Could not get the shipping method |||": "||| Не смог получить тип доставки |||",
    "||| Could not get the tracking number |||": "||| Не смог получить трек-номер |||",
    "||| Could not compute the Total: some amounts failed to parse, the cell will hold !ERROR! — check the order manually |||": "||| Не смог посчитать Total: часть сумм не распарсилась, в ячейке будет !ERROR! — проверьте заказ вручную |||",
    "||| Could not recognize the size from the text: {text} |||": "||| Не удалось распознать размер из текста: {text} |||",
    "||| Error writing the {marketplace} order: {error} |||": "||| Ошибка записи заказа {marketplace}: {error} |||",
    "||| Error processing the {name} order: {error} |||": "||| Ошибка обработки заказа {name}: {error} |||",
    "||| Error while searching for the listing link: {error} |||": "||| Ошибка при поиске ссылки на листинг: {error} |||",
    "||| Error while getting the customization: {error} |||": "||| Ошибка при получении кастомизации: {error} |||",
    "||| Error while getting the listing links: {error} |||": "||| Ошибка при получении ссылок на листинги: {error} |||",
    "||| Error: {error} |||": "||| Ошибка: {error} |||",
    "||| Check that the shipping label exists, most likely it is not in the app folder |||": "||| Проверьте наличие шиплейбла, скорее всего его нет в папке с программой |||",
    "||| Shipping method not found |||": "||| Тип доставки не найден |||",
    "||| Total not found |||": "||| Тотал не найден |||",
    "||| Shipping price charged not found |||": "||| Установленная цена за доставку не найдена |||",
    "!!!An error occurred: {error}!!!": "!!!Произошла ошибка: {error}!!!",
    # --- notes / done ---
    "---Routing to sheet: {sheet}---": "---Распределяем по листу: {sheet}---",
    "---Order file not found on the Drive, so the file extension could not be determined for sheet routing.\nThe order was added to the ERROR sheet---": "---Файл заказа не найден на диске, поэтому не смог определить расширение файла и отсортировать по листу.\nЗаказ был добавлен на лист ERROR---",
    "<<<Order added to the spreadsheet>>>": "<<<Заказ добавлен в таблицу>>>",
    # --- misc ---
    "The SKU was taken from the title, verify it after it lands in the spreadsheet!": "SKU был взят из названия, проверьте после добавления в таблицу!",
    "The SKU is not specified on the listing, trying to get it from the product title": "SKU не указан на листинге, пытаюсь получить его из названия товара",
    "<-- All data added successfully. Please double-check the data in the spreadsheet! -->": "<-- Все данные успешно добавлены. Проверьте внимательно данные в таблице! -->",
    "Warning: {failed} order(s) skipped due to errors, written: {ok}.": "Внимание: заказов пропущено из-за ошибок: {failed}, записано: {ok}.",
    "File {path} not found.": "Файл {path} не найден.",
    "Press Enter to exit...": "Нажмите Enter, чтобы выйти из программы...",
    "The program was interrupted by the user.": "Работа программы была прервана пользователем.",
    "Fatal error: {message}": "Критическая ошибка: {message}",
    "marketplace not recognized": "маркетплейс не распознан",
}

_UK = {
    # --- banners ---
    "New order": "Нове замовлення",
    # --- field labels ---
    "Processing date": "Дата обробки замовлення",
    "Order ID": "Номер замовлення",
    "Shop name": "Назва магазину",
    "Product title": "Назва товару",
    "Item SKU": "SKU товару",
    "Quantity": "Кількість",
    "Customization": "Кастомізація",
    "Customer address": "Адреса клієнта",
    "Shipping address": "Адреса доставки",
    "Ship by": "Відправити до",
    "Items total": "Загальна сума за товари",
    "Order total": "Сума замовлення",
    "Total": "Разом",
    "Shipping paid by us": "Сума, сплачена нами за доставку",
    "Shipping price charged": "Встановлена ціна за доставку",
    "Shipping method": "Тип доставки",
    "Carrier": "Поштова служба",
    "Carrier (label bought outside Etsy)": "Поштова служба (якщо доставку куплено не на Etsy)",
    "Tracking number": "Трек-номер",
    "Tracking number (label bought outside Amazon)": "Трек-номер, якщо шиплейбл куплено не на Amazon",
    "Tracking link": "Посилання на відстеження",
    "Listing link": "Посилання на лістинг",
    "Product size": "Розмір товару",
    "Shipping label uploaded": "Шиплейбл завантажено",
    # --- problems ---
    "||| The address is too long/short, could not process it |||": "||| Адреса задовга/закоротка, не вдалося обробити |||",
    "||| Order {number}: marketplace not recognized, skipping |||": "||| Замовлення {number}: маркетплейс не розпізнано, пропускаю |||",
    "||| Order not added: the parser found no items in the HTML |||": "||| Замовлення не додано: парсер не знайшов товари в HTML |||",
    "||| Order skipped, moving on to the next one |||": "||| Замовлення пропущено, переходжу до наступного |||",
    "||| No listing links found |||": "||| Не знайдено жодного посилання на лістинг |||",
    "||| Could not find the listing link |||": "||| Не зміг знайти посилання на лістинг |||",
    "||| Could not get the SKU |||": "||| Не зміг отримати SKU |||",
    "||| Could not get the shipping address |||": "||| Не зміг отримати адресу доставки |||",
    "||| Could not get the customer address |||": "||| Не зміг отримати адресу клієнта |||",
    "||| Could not get the customization, it may not be specified |||": "||| Не зміг отримати кастомізацію, можливо, її не вказано |||",
    "||| Could not get the quantity |||": "||| Не зміг отримати кількість |||",
    "||| Could not get the smaller size for sheet routing |||": "||| Не зміг отримати менший розмір для сортування |||",
    "||| Could not get the listing title |||": "||| Не зміг отримати назву лістинга |||",
    "||| Could not get the shop name |||": "||| Не зміг отримати назву магазину |||",
    "||| Could not get the carrier name |||": "||| Не зміг отримати назву поштової служби |||",
    "||| Could not get the order ID |||": "||| Не зміг отримати номер замовлення |||",
    "||| Could not get the items total |||": "||| Не зміг отримати загальну суму за товари |||",
    "||| Could not get the product size |||": "||| Не зміг отримати розмір товару |||",
    "||| Could not get the carrier |||": "||| Не зміг отримати службу доставки |||",
    "||| Could not get the tracking link |||": "||| Не зміг отримати посилання на відстеження |||",
    "||| Could not get the order total |||": "||| Не зміг отримати суму замовлення |||",
    "||| Could not get the shipping amount we paid |||": "||| Не зміг отримати суму, сплачену нами за доставку |||",
    "||| Could not get the shipping method |||": "||| Не зміг отримати тип доставки |||",
    "||| Could not get the tracking number |||": "||| Не зміг отримати трек-номер |||",
    "||| Could not compute the Total: some amounts failed to parse, the cell will hold !ERROR! — check the order manually |||": "||| Не зміг порахувати Total: частина сум не розпарсилась, у комірці буде !ERROR! — перевірте замовлення вручну |||",
    "||| Could not recognize the size from the text: {text} |||": "||| Не вдалося розпізнати розмір із тексту: {text} |||",
    "||| Error writing the {marketplace} order: {error} |||": "||| Помилка запису замовлення {marketplace}: {error} |||",
    "||| Error processing the {name} order: {error} |||": "||| Помилка обробки замовлення {name}: {error} |||",
    "||| Error while searching for the listing link: {error} |||": "||| Помилка під час пошуку посилання на лістинг: {error} |||",
    "||| Error while getting the customization: {error} |||": "||| Помилка під час отримання кастомізації: {error} |||",
    "||| Error while getting the listing links: {error} |||": "||| Помилка під час отримання посилань на лістинги: {error} |||",
    "||| Error: {error} |||": "||| Помилка: {error} |||",
    "||| Check that the shipping label exists, most likely it is not in the app folder |||": "||| Перевірте наявність шиплейбла, найімовірніше його немає в папці з програмою |||",
    "||| Shipping method not found |||": "||| Тип доставки не знайдено |||",
    "||| Total not found |||": "||| Total не знайдено |||",
    "||| Shipping price charged not found |||": "||| Встановлену ціну за доставку не знайдено |||",
    "!!!An error occurred: {error}!!!": "!!!Сталася помилка: {error}!!!",
    # --- notes / done ---
    "---Routing to sheet: {sheet}---": "---Розподіляю на лист: {sheet}---",
    "---Order file not found on the Drive, so the file extension could not be determined for sheet routing.\nThe order was added to the ERROR sheet---": "---Файл замовлення не знайдено на Диску, тому не зміг визначити розширення файлу та відсортувати за аркушем.\nЗамовлення додано на аркуш ERROR---",
    "<<<Order added to the spreadsheet>>>": "<<<Замовлення додано до таблиці>>>",
    # --- misc ---
    "The SKU was taken from the title, verify it after it lands in the spreadsheet!": "SKU взято з назви, перевірте після додавання до таблиці!",
    "The SKU is not specified on the listing, trying to get it from the product title": "SKU не вказано на лістингу, намагаюся отримати його з назви товару",
    "<-- All data added successfully. Please double-check the data in the spreadsheet! -->": "<-- Усі дані успішно додано. Уважно перевірте дані в таблиці! -->",
    "Warning: {failed} order(s) skipped due to errors, written: {ok}.": "Увага: замовлень пропущено через помилки: {failed}, записано: {ok}.",
    "File {path} not found.": "Файл {path} не знайдено.",
    "Press Enter to exit...": "Натисніть Enter, щоб вийти з програми...",
    "The program was interrupted by the user.": "Роботу програми було перервано користувачем.",
    "Fatal error: {message}": "Критична помилка: {message}",
    "marketplace not recognized": "маркетплейс не розпізнано",
}

_CATALOG: dict[str, dict[str, str]] = {"ru": _RU, "uk": _UK}


def banner_words() -> list[str]:
    """All translations of the "New order" banner word, for log parsing."""
    words = ["New order"]
    for catalog in _CATALOG.values():
        words.append(catalog["New order"])
    return words
