_ERROR_ = ("ПОТЕРЯ СОЕДИНЕНИЯ", ...)
_STATUS_ = ("СОЗДАТЬ ЛОББИ С ИГРОЙ 1", ...)


class Menager():
    """Класс связывающий фронт- и бэк-енд части локальной программы.

    Подразумевается, что у всех объектов этого класса будет 2 единных очереди,
    через которые будут передаваться сообщения"""

    from collections import deque

    queue_status = deque()
    queue_messange = deque()

    def push_status(self, status: object, error: int = None):
        """Функция для отправки бэкенд частью изменений игры

        Args:
            status (object): отправка статуса игры, как правило в виде игрового поля.
            error (int, optional): Номер ошибки из _ERROR_ => переход к \
                          стандартному набору действий. Defaults to None:int.
        """
        self.queue_status.append((status, error))

    def pop_status(self,):
        """Получение фронтендом статуса игры

        Returns:
            tuple: Сообщение вида (status: object, error: int = None)\
                    В status если запущена игра - игровое поле (не str),\
                    если нет запущенной игры - None,\
                    если игра завершилась - str с ником победителя.\
                    В error код глобальной ошибки.
        """
        return self.queue_status.pop() if len(self.queue_status) else (None, None)

    # Для меню и игр нужно согласовать необходимые сообщения.
    # Например для крестиков-ноликов это может быть в виде:
    #  {1 : "ход на верхнюю левую клетку", 2 : ход на верхнюю центральную клетку}
    # для всякого рода ввода "введите ник" возвращать нужно tuple (int, str),
    # где int из _STATUS_

    def push_messange(self, messange: object):
        """Функция для отправки фронтенд частью команд управления

        Args:
            messange (object): сообщение управления.\
                (зависит от состояния приложения,\
                например в меню может быть int из _STATUS_)
        """
        self.queue_messange.append(messange)

    def pop_messange(self, ):
        """Функция для получения бэкенд частью команд управления игрой/меню

        Returns:
            object: сообщение управления.\
                (зависит от состояния приложения,\
                например в меню может быть int из _STATUS_)\
                При пустой очереди возращает None

        """
        return self.queue_messange.pop() if len(self.queue_messange) else None
