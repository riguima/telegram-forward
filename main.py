from pyrogram import filters, idle
from pyrogram.client import Client
from pyrogram.types import Message
from sqlalchemy import select

from forward_telegram_bot.app import add_forward_to_app, create_apps
from forward_telegram_bot.database import session
from forward_telegram_bot.models import Forward, User


if __name__ == '__main__':
    apps = create_apps()
    for e, app in enumerate(apps):
        app.start()
        if e != 0:
            for user in session.scalars(select(User)).all():
                query = select(Forward).where(Forward.user == user)
                for forward in session.scalars(query).all():
                    add_forward_to_app(forward, app)
    idle()
    for app in apps:
        app.stop()
