from pyrogram import filters, idle
from pyrogram.client import Client
from pyrogram.types import Message
from sqlalchemy import select

from forward_telegram_bot.app import create_apps
from forward_telegram_bot.database import session
from forward_telegram_bot.models import Forward, User


if __name__ == '__main__':
    apps = create_apps()
    for app in apps:
        app.start()
    for user in session.scalars(select(User)).all():
        query = select(Forward).where(Forward.user == user)
        forwards = session.scalars(query).all()
        for forward in forwards:
            @app.on_message(filters.chat(forward.from_chat))
            async def forward_message(client: Client, message: Message) -> None:
                await client.send_message(forward.to_chat, message.text)
    idle()
    for app in apps:
        app.stop()
