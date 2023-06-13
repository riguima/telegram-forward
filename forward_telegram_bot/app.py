import os

from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message


def create_app() -> Client:
    load_dotenv()
    app = Client(
        os.environ['BOT_NAME'],
        api_id=os.environ['API_ID'],
        api_hash=os.environ['API_HASH'],
        bot_token=os.environ['BOT_TOKEN'],
    )

    @app.on_message(filters.command('start'))
    async def start(client: Client, message: Message) -> None:
        await message.reply(
            (
                '/logar [número de telefone] - Para realizar o login, '
                'necessário para adicionar redirecionamentos\n'
                '/adicionar [id ou titulo] [id ou titulo] - '
                'Para adicionar um redirecionamento\n/listar - Lista os '
                'redirecionamentos adicionados\n/remover '
                '[id do redirecionamento] - Para remover um redirecionamento'
            )
        )
    return app
