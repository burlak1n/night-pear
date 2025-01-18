import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from dao.base import BaseDAO
from dao.session_maker import session_manager
import logging
import sys
from config import TOKEN, ALLOWED_USER_IDS

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile

import datetime

from pydantic import BaseModel, Field

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from dao.database import Base

class User(Base):
    """
    Модель таблицы пользователей, регистрирующихся при первом использовании бота.
    """
    username: Mapped[str]
    fullname: Mapped[str]

    win_count: Mapped[int] = mapped_column(default=0)
    def __repr__(self):
        return f"ID: {self.id}\nUsername: {self.username}\nFullname: {self.fullname}\nВремя регистрации: {self.created_at}\nВремя последнего использования:\n{self.updated_at}\nЧисло побед: {self.win_count}"

t = {
    datetime.date(2025, 1, 19): [0, "сигма бой бобр"],
    datetime.date(2025, 1, 20): [1, ""],
    datetime.date(2025, 1, 21): [2, ""],
    datetime.date(2025, 1, 22): [3, ""],
    datetime.date(2025, 1, 23): [4, ""],
    datetime.date(2025, 1, 24): [5, ""]
}

for key, value in t.items():
  if value[1]: # Проверка на пустую строку
    t[key] = sorted(value[1].lower().split())
    print(f"Дата: {key}, Отсортированные слова: {t[key]}")
  else:
    print(f"Дата: {key}, Строка пустая.")
    
class UserDAO(BaseDAO):
    model=User

class UserAdd(BaseModel):
    id: int = Field(description="Телеграм айди пользователя")
    username: str = Field(description="Username пользователя")
    fullname: str = Field(description="Полное имя пользователя")


logging.basicConfig(level=logging.INFO, stream=sys.stdout)
# Initialize Bot instance with default bot properties which will be passed to all API calls
bot = Bot(token=TOKEN)

dp = Dispatcher()


@dp.message(CommandStart())
@session_manager.connection(commit=True)
async def command_start_handler(message: Message, session:AsyncSession) -> None:
    """
    This handler receives messages with `/start` command
    """
    today = datetime.datetime.now().date()
    data = t.get(today)[0]
    user: User = await UserDAO.find_by_ids(session, [message.from_user.id])
    if not user:
        m = message.from_user
        _ = await UserDAO.add(session, UserAdd(id=m.id, username=m.username, fullname=m.full_name))
    else:
        user = user[0]
    if data is not None:
        await message.answer(f'''
        По закону Архимеда после плотного обеда полагается... решить головоломку и получить мерч Вышки на НОЧИ Студента 2025!

До самой НОЧИ Студента осталось совсем чуть-чуть, и «Груша» поможет сделать ее самой незабываемой. Соверши покупку с 20 по 24 число, реши все ежедневные задания и забери памятный мерч.

А вот и сегодняшнее задание!
        ''')
        
        await message.answer_photo(FSInputFile(f"./data/{data}.jpg"), caption="Твоя задача – найти 10 слов, связанных с НОЧЬю Студента этого года. Записывай их через пробел без знаков препинания. Как только соберешь все, отправь в чат бота одним сообщением. Помни, что попытка всего одна – удачи!")

@dp.message(F.from_user.id.in_(ALLOWED_USER_IDS), Command("stats"))
@session_manager.connection(commit=True)
async def answer_handler(message: Message, session: AsyncSession) -> None:
    users = sorted(await UserDAO.find_all(session, None), key=lambda user: user.win_count, reverse=True)
    await message.answer(f"Всего пользователей {len(users)}:")
    for user in users:
        u = str(user)
        await message.answer(u) 

@dp.message()
@session_manager.connection(commit=True)
async def answer_handler(message: Message, session: AsyncSession) -> None:
    user: User = await UserDAO.find_by_ids(session, [message.from_user.id])
    if user:
        user = user[0]
        
        now = datetime.datetime.now()

        today = now.date()
        data:str = t.get(today)[1]
        
        msg = sorted(message.text.lower().split())

        if len(msg) > 1 and user.updated_at.date() == today:
            user.updated_at = now
            if msg == sorted(data.lower().split()):
                user.win_count += 1
                await message.answer("Ура, ты верно выполнил задание! Мы зачли твой ответ. Не забудь зайти в следующие дни до НОЧИ, чтобы решить оставшиеся головоломки")
            else:
                await message.answer("Ой, к сожалению, ты сделал что-то не так (\nСегодняшняя попытка, увы, не засчитывается")
            await session.commit()

    else:
        await message.answer("Сначала введи /start")

async def main() -> None:
    await dp.start_polling(bot)


if __name__ == "__main__":
    
    asyncio.run(main())