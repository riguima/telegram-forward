import os

from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import Message
from pyromod import listen
from sqlalchemy import select

from forward_telegram_bot.common import is_valid_phone_number
from forward_telegram_bot.database import session
from forward_telegram_bot.models import Forward, User


users = session.scalars(select(User)).all()
apps = {}
load_dotenv()
for user in users:
    apps[user.name] = Client(
        user.name,
        api_id=os.environ['API_ID'],
        api_hash=os.environ['API_HASH'],
    )


def create_apps() -> list[Client]:
    load_dotenv()
    global apps
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
        if message.chat.username in apps:
            await message.reply('Usuário já está logado')
        elif is_valid_phone_number(phone_number):
            user = Client(
                message.chat.username,
                api_id=os.environ['API_ID'],
                api_hash=os.environ['API_HASH'],
            )
            await user.connect()
            sent_code = await user.send_code(phone_number)
            code = await message.chat.ask(
                (
                    'Digite o código de verificação, digite nesse padrão '
                    '(aacodigo): '
                )
            )
            try:
                await user.sign_in(
                    phone_number,
                    sent_code.phone_code_hash,
                    str(code.text)[2:],
                )
            except SessionPasswordNeeded:
                password = await message.chat.ask(
                    (
                        'Digite sua senha de verificação de duas etapas, '
                        'digite nesse formato (aasenha)'
                    )
                )
                user.password = str(password.text)[2:]
                await user.sign_in(
                    phone_number,
                    sent_code.phone_code_hash,
                    str(code.text)[2:],
                )
            session.add(User(name=message.chat.username))
            session.commit()
            await message.reply('Login realizado com sucesso')
        else:
            await message.reply(
                (
                    'Número de telefone inválido: utilize como no exemplo: '
                    '+5511999999999'
                ),
            )

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
        query = select(User).where(User.name == message.chat.username)
        user = session.scalars(query).first()
        if user:
            forward = Forward(
                from_chat=from_chat, to_chat=to_chat, user=user
            )
            session.add(forward)
            session.commit()
        else:
            await message.reply(
                (
                    'Primeira faça login antes de adicionar um '
                    'redirecionamento'
                )
            )

        user_app = apps[message.chat.username]

        @user_app.on_message(filters.chat(forward.from_chat))
        async def forward_message(client: Client, message: Message) -> None:
            await client.send_message(forward.to_chat, message.text)

        await message.reply('Redirecionamento adicionado')

    @app.on_message(filters.command('listar'))
    async def show_forwards(client: Client, message: Message) -> None:
        query = select(User).where(User.name == message.chat.username)
        user = session.scalars(query).first()
        if not user:
            text = 'Primeiro faça login antes de listar seus redirecionamentos'
        else:
            query = select(Forward).where(Forward.user == user)
            forwards = session.scalars(query).all()
            if forwards:
                text_format = '{:<10}{:<20}{:<20}\n'
                text = text_format.format('ID', 'Do Chat', 'Para o chat')
                for forward in forwards:
                    text += text_format.format(
                        forward.id, forward.from_chat, forward.to_chat
                    )
            else:
                text = 'Nenhum redirecionamento adicionado'
        await message.reply(text)

    @app.on_message(filters.command('remover'))
    async def remove_forward(client: Client, message: Message) -> None:
        forward = session.get(Forward, int(message.text.split()[-1]))
        if forward is not None:
            session.delete(forward)
            session.commit()
            await message.reply('Redirecionamento removido')
        else:
            await message.reply('ID inválido')
        user_app = apps[message.chat.username]
        await user_app.restart()
        query = select(Forward).where(Forward.user == user)
        forwards = session.scalars(query).all()
        for forward in forwards:
            @user_app.on_message(filters.chat(forward.from_chat))
            async def forward_message(client: Client, message: Message) -> None:
                await client.send_message(forward.to_chat, message.text)

    return [app, *list(apps.values())]
