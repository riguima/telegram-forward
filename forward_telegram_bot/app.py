import os

from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types import Message
from pyromod import listen
from sqlalchemy import select

from forward_telegram_bot.common import is_valid_phone_number
from forward_telegram_bot.database import Session
from forward_telegram_bot.models import Forward, User


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
                '/adicionar [id do chat] [id do chat] - '
                'Para adicionar um redirecionamento\n/listar - Lista os '
                'redirecionamentos adicionados\n/remover '
                '[id do redirecionamento] - Para remover um redirecionamento'
            ),
        )

    @app.on_message(filters.command('logar'))
    async def login(client: Client, message: Message) -> None:
        phone_number = message.text.split()[-1]
        if user_already_logged_in(message.chat.username):
            await message.reply('Usuário já está logado')
        elif is_valid_phone_number(phone_number):
            client = Client(
                message.chat.username,
                api_id=os.environ['API_ID'],
                api_hash=os.environ['API_HASH'],
            )
            await client.connect()
            sent_code = await client.send_code(phone_number)
            code = await message.chat.ask('Digite o código de verificação')
            await client.sign_in(
                phone_number,
                sent_code.phone_code_hash,
                code.text
            )
        else:
            await message.reply(
                (
                    'Número de telefone inválido: utilize como no exemplo: '
                    '+5511999999999'
                ),
            )

    def user_already_logged_in(username: str) -> bool:
        with Session() as session:
            query = select(User)
            return username in [m.name for m in session.execute(query).all()]

    @app.on_message(filters.command('adicionar'))
    async def add_forward(client: Client, message: Message) -> None:
        if len(message.text.split()) < 3:
            await message.reply(
                (
                    'Use adicionando os dois ids dos chats, como no exemplo: '
                    '/adicionar 12345678 12345679'
                )
            )
        from_chat, to_chat = message.text.split()[1:3]
        with Session() as session:
            query = select(User).where(User.name == message.chat.username)
            user = session.execute(query).first()
            if user:
                forward = Forward(from_chat=from_chat, to_chat=to_chat)
                user.forwards.append(forward)
                session.commit()
            else:
                await message.reply(
                    (
                        'Primeira faça login antes de adicionar um '
                        'redirecionamento'
                    )
                )
        user = Client(
            message.chat.username,
            api_id=os.environ['API_ID'],
            api_hash=os.environ['API_HASH'],
        )

        @user.on_message(filters.chat(from_chat))
        def forward_message(client: Client, message: Message) -> None:
            client.send_message(to_chat, message.text)

        user.start()
        await message.reply('Redirecionamento adicionado')

    @app.on_message(filters.command('listar'))
    async def show_forwards(client: Client, message: Message) -> None:
        with Session() as session:
            query = select(User).where(User.name == message.chat.username)
            user = session.execute(query).first()
        if not user:
            text = 'Primeiro faça login antes de listar seus redirecionamentos'
        elif user.forwards:
            text_format = '{:<10}{:<20}{:<20}'
            text = text_format.format('ID', 'Do Chat', 'Para o chat')
            for forward in user.forwards:
                text += text_format.format(
                    forward.id, forward.from_chat, forward.to_chat
                )
        else:
            text = 'Nenhum redirecionamento adicionado'
        await message.reply(text)

    @app.on_message(filters.command('remover'))
    async def remove_forward(client: Client, message: Message) -> None:
        with Session() as session:
            forward = session.get(int(message.text.split()[-1]))
            if forward is not None:
                session.delete(forward)
                session.commit()
                await message.reply('Redirecionamento removido')
            else:
                await message.reply('ID inválido')

    return app
