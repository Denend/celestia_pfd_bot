# git remote add origin https://github.com/monsterlessons/learning_git.git

import os
import json
import socket
import asyncio
import sqlite3
import requests
import paramiko

from typing import Union, List
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, \
    CallbackQuery, ParseMode
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher
from aiogram.utils import executor

BOT_TOKEN = '6048975626:AAH7iEVWOBQO4o48lXcF7-G8jyzuOcORK9M'
loop = asyncio.get_event_loop()
bot = Bot(BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, loop=loop, storage=MemoryStorage())

admin_ids = ["prostosozhgitemena", ]

hello_message = """Enter remote server IP"""

post_req = '''NODE_TYPE=light
AUTH_TOKEN=$(celestia $NODE_TYPE auth admin --p2p.network blockspacerace)


curl -X POST \
     -H "Authorization: Bearer $AUTH_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"jsonrpc":"2.0","id":0,"method":"p2p.Info","params":[]}' \
     http://localhost:26658'''

user = 'root'
port = 22


class States(StatesGroup):
    get_ip = State()
    get_pass = State()
    get_call = State()


@dp.message_handler(commands=['start'])
async def start(message: Message):
    await bot.send_message(message.chat.id, hello_message)
    await States.get_ip.set()


@dp.message_handler(state=States.get_ip)
async def get_ip(message: Message, state: FSMContext):
    ip = message.text
    await States.get_pass.set()
    await state.update_data({'ip': ip})
    await message.answer(f'Enter root@{ip} password')


@dp.message_handler(state=States.get_pass)
async def get_pass(message: Message, state: FSMContext):
    secret = message.text
    await state.update_data({'secret': secret})
    data = await state.get_data()
    host = data['ip']
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=user, password=secret, port=port)
    except paramiko.ssh_exception.AuthenticationException:
        await message.answer('Authentication failed.')
        return await state.finish()
    except TimeoutError:
        await message.answer('Connection error. Check ip address.')
        return await state.finish()
    except socket.gaierror:
        await message.answer('Wrong IPv4 format.')
        return await state.finish()

    channel = client.get_transport().open_session()
    channel.get_pty()
    channel.exec_command(post_req)

    resp: dict = json.loads(channel.recv(1024).decode("utf-8"))
    node_id = ''
    if 'result' in resp.keys():
        result: dict = resp['result']
        if 'ID' in result.keys():
            node_id = result['ID']
            await state.update_data({'node_id': node_id})

            resp_text = requests.get(f'https://leaderboard.celestia.tools/api/v1/nodes/{node_id}',
                                 headers={
                                     "accept": "application/json, text/plain, */*",
                                     "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                                     "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
                                     "sec-ch-ua-mobile": "?0",
                                     "sec-ch-ua-platform": "\"macOS\"",
                                     "sec-fetch-dest": "empty",
                                     "sec-fetch-mode": "cors",
                                     "sec-fetch-site": "cross-site"
                                 },
                                 params={"referrer": "https://tiascan.com/",
                                         "referrerPolicy": "strict-origin-when-cross-origin",
                                         "body": None,
                                         "method": "GET",
                                         "mode": "cors",
                                         "credentials": "omit"}).text
            try:
                resp: dict = json.loads(resp_text)
                if 'uptime' in resp.keys():
                    uptime_score = resp['uptime']
                else:
                    uptime_score = 'Error'
                if 'pfb_count' in resp.keys():
                    pfb_count = resp['pfb_count']
                else:
                    pfb_count = 'Error'
            except Exception as e:
                uptime_score = 'Error'
                pfb_count = 'Error'
            await message.answer(f'''Connected to server.

<b>Your node id is:</b>
<code>{node_id}</code>

<b>uptime score:</b> <code>{uptime_score}</code>
<b>number of pay for blob txs:</b> <code>{pfb_count}</code>''', reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton('Update node data', callback_data='data'),
                    InlineKeyboardButton('Submit pay for blob tx', callback_data='txhash')).add(
                    InlineKeyboardButton('Close session', callback_data='close_session')).add(
                    InlineKeyboardButton('Check node in tiascan', url=f'https://tiascan.com/light-node/{node_id}')
                ))
        else:
            await message.answer('Ошибка. Попробуйте снова.')
    else:
        await message.answer('Ошибка. Попробуйте снова.')
    client.close()
    await States.get_call.set()


@dp.callback_query_handler(state=States.get_call)
async def callback(call: CallbackQuery, state: FSMContext):
    message = call.message
    msg_text = message.text
    node_id = (msg_text[msg_text.index("Your node id is:\n") + len("Your node id is:\n"):msg_text.index("\n\nuptime score:")])
    data = await state.get_data()

    if node_id != data['node_id']:
        await message.answer('Session expired.')
        return await state.finish()

    if call.data == 'data':
        await bot.delete_message(call.from_user.id, message.message_id)

        resp_text = requests.get(f'https://leaderboard.celestia.tools/api/v1/nodes/{node_id}',
                                 headers={
                                     "accept": "application/json, text/plain, */*",
                                     "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                                     "sec-ch-ua": "\"Google Chrome\";v=\"111\", \"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"111\"",
                                     "sec-ch-ua-mobile": "?0",
                                     "sec-ch-ua-platform": "\"macOS\"",
                                     "sec-fetch-dest": "empty",
                                     "sec-fetch-mode": "cors",
                                     "sec-fetch-site": "cross-site"
                                 },
                                 params={"referrer": "https://tiascan.com/",
                                         "referrerPolicy": "strict-origin-when-cross-origin",
                                         "body": None,
                                         "method": "GET",
                                         "mode": "cors",
                                         "credentials": "omit"}).text
        try:
            resp: dict = json.loads(resp_text)
            if 'uptime' in resp.keys():
                uptime_score = resp['uptime']
            else:
                uptime_score = 'Error'
            if 'pfb_count' in resp.keys():
                pfb_count = resp['pfb_count']
            else:
                pfb_count = 'Error'
        except Exception as e:
            uptime_score = 'Error'
            pfb_count = 'Error'
        await message.answer(f'''<b>Your node id is:</b>
<code>{node_id}</code>

<b>uptime score:</b> <code>{uptime_score}</code>
<b>number of pay for blob txs:</b> <code>{pfb_count}</code>''', reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton('Update node data', callback_data='data'),
                    InlineKeyboardButton('Submit pay for blob tx', callback_data=f'txhash')).add(
                    InlineKeyboardButton('Close session', callback_data='close_session')).add(
                    InlineKeyboardButton('Check node in tiascan', url=f'https://tiascan.com/light-node/{node_id}')
                ))

    elif call.data == 'txhash':
        data = await state.get_data()

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(hostname=data['ip'], username=user, password=data['secret'], port=port)
        except paramiko.ssh_exception.AuthenticationException:
            await message.answer('Failed to connect to the server, try again.')
            await bot.answer_callback_query(call.id)
            return
        except TimeoutError:
            await message.answer('Failed to connect to the server, try again.')
            await bot.answer_callback_query(call.id)
            return
        except socket.gaierror:
            await message.answer('Failed to connect to the server, try again.')
            await bot.answer_callback_query(call.id)
            return

        channel = client.get_transport().open_session()
        channel.get_pty()
        channel.exec_command('''(curl -X POST -d '{"namespace_id": "0c204d39600fddd3",
                      "data": "f1f20ca8007e910a3bf8b2e61da0f26bca07ef78717a6ea54165f5",
                      "gas_limit": 80000, "fee": 2000}' http://localhost:26659/submit_pfb)''')
        xxx = channel.recv(3000).decode("utf-8")
        client.close()
        try:
            resp: dict = json.loads(xxx)
        except Exception as e:
            await bot.answer_callback_query(
                call.id,
                'An error occurred on the network when connecting, try again!',
                show_alert=True
                )
            return

        txhash = ''
        try:
            if 'txhash' in resp.keys():
                txhash = resp['txhash']
            else:
                txhash = 'Failed to download <b>txhash</b> try logging in again'
        except Exception as e:
            txhash = 'Failed to download <b>txhash</b> try logging in again'

        await message.answer(f'Success, your txhash: <code>{txhash}</code>')
        await bot.answer_callback_query(call.id)

    elif call.data == 'close_session':
        await bot.delete_message(call.from_user.id, message.message_id)
        await message.answer('The session is over!')
        await state.finish()


@dp.callback_query_handler()
async def callback(call: CallbackQuery):
    await bot.delete_message(call.from_user.id, call.message.message_id)
    await call.message.answer('Session expired.')

if __name__ == "__main__":
    executor.start_polling(dp, loop=loop)