# Python Imports
from aiohttp import ClientSession
import json
import asyncio
from asyncio import TimeoutError
import sys
import traceback
import websockets
import uuid
import time
from datetime import datetime
from ws4py.client.threadedclient import WebSocketClient
# Local Imports
from .hub_settings import (
    HUB_HOST, HUB_URL, API_URL, ADMIN_TOKEN, WEBSOCKET_PROTOCOL, WS_TIMEOUT,
    HUB_VERSION
)
from .utils import parse_response


class HubClient:

    def __init__(self, token=None):
        self.admin_header = {'Authorization': f'token {ADMIN_TOKEN}'}
        self.user_header = {'Authorization': f'token {token}'} if token else {}

    async def get_response(self, session, url, headers):
        async with session.get(url, headers=headers) as response:
            return await response.text()

    async def post_response(self, session, url, headers, data=None):
        async with session.post(url, headers=headers, data=data) as response:
            return await response.text()

    async def delete_response(self, session, url, headers):
        async with session.delete(url, headers=headers) as response:
            return await response.text()

    async def create_user(self, username):
        """ POST /users/[:username]
            Create a new user on the hub with the given username
        """
        request_url = f'{HUB_URL}/users/{username}'
        async with ClientSession() as session:
            return json.loads(
                await self.post_response(
                    session, request_url, self.admin_header
                )
            )

    async def create_token(self, username):
        """ POST /users/[:username]/tokens
            Create a new token for the username
        """
        request_url = f'{HUB_URL}/users/{username}/tokens'
        async with ClientSession() as session:
            return json.loads(
                await self.post_response(
                    session, request_url, self.admin_header
                )
            )

    async def start_user_server(self, username):
        # POST /users/[:username]/server
        # Start a user server
        request_url = f'{HUB_URL}/users/{username}/server'
        async with ClientSession() as session:
            return await self.post_response(
                session, request_url, self.user_header
            )

    async def stop_user_server(self, username):
        # DELETE /users/[:username]/server
        # Stop a user server
        request_url = f'{HUB_URL}/users/{username}/server'
        async with ClientSession() as session:
            return await self.delete_response(
                session, request_url, self.user_header
            )

    async def start_user_kernel(self, username, kernel_name):
        # POST /user/[:username]/api/kernels
        # Start a new kernel
        request_url = f'{API_URL}/user/{username}/api/kernels'
        data = json.dumps({"name": kernel_name})
        async with ClientSession() as session:
            return json.loads(
                await self.post_response(
                    session, request_url, self.user_header, data
                )
            )

    async def get_user_kernels(self, username):
        # GET /user/[:username]/api/kernels
        # Get the list of running kernels.
        request_url = f'{API_URL}/user/{username}/api/kernels'
        async with ClientSession() as session:
            return json.loads(
                await self.get_response(session, request_url, self.user_header)
            )

    async def remove_user_kernel(self, username, kernel_id):
        # DELETE /user/[:username]/api/kernels/[:kernel_id]
        # Shutdown the kernel.
        request_url = f'{API_URL}/user/{username}/api/kernels/{kernel_id}'
        async with ClientSession() as session:
            return await self.delete_response(
                session, request_url, self.user_header
            )

    async def interrupt_user_kernel(self, username, kernel_id):
        # POST /user/[:username]/api/kernels/[:kernel_id]/interrupt
        # Interrupt the kernel.
        request_url = f'{API_URL}/user/{username}/api/kernels/{kernel_id}'+\
                        '/interrupt'
        async with ClientSession() as session:
            return await self.post_response(
                    session, request_url, self.user_header
                )

    async def restart_user_kernel(self, username, kernel_id):
        # POST /user/[:username]/api/kernels/[:kernel_id]/restart
        # Restart the kernel.
        request_url = f'{API_URL}/user/{username}/api/kernels/{kernel_id}'+\
                        '/restart'
        async with ClientSession() as session:
            return json.loads(
                await self.post_response(
                    session, request_url, self.user_header
                )
            )

    def send_code(self, kernel_id, username, code, ips=None,
                  timeout=WS_TIMEOUT):
        uri = f"{WEBSOCKET_PROTOCOL}://{HUB_HOST}/user/{username}" +\
                f"/api/kernels/{kernel_id}/channels"
        headers = list(zip(self.user_header.keys(), self.user_header.values()))
        ws = WSClient(uri, headers, username, ips, code)
        ws.connect()
        ws.run_forever()
        return ws.result, ws.execute_reply


class WSClient(WebSocketClient):
    def __init__(self, uri, headers, username, ips, code):
        # WebSocketClient.__init__(self, uri, headers=headers)
        self.i = 0
        self.appended_data = []
        self.result = {}
        self.execute_reply = {}
        self.username = username
        self.inputs = ips
        self.code = code
        super(WSClient, self).__init__(uri, headers=headers)

    def get_execute_header(self, username, code):
        hdr = {
            'msg_id': uuid.uuid4().hex,
            'username': username,
            'session': uuid.uuid4().hex,
            'data': datetime.now().isoformat(),
            'msg_type': 'execute_request',
            'version': HUB_VERSION
            }
        content = {'code': code, 'silent': False, 'allow_stdin': True}
        msg = {'header': hdr, 'parent_header': hdr, 'metadata': {},
               'content': content, "channel": "shell"}
        return msg

    def get_input_header(self, username, input_val):
        hdr = {
            'msg_id': uuid.uuid4().hex,
            'username': username,
            'session': uuid.uuid4().hex,
            'data': datetime.now().isoformat(),
            'msg_type': 'input_reply',
            'version': HUB_VERSION
            }
        content = {'value': input_val}
        msg = {'header': hdr, 'parent_header': hdr, 'metadata': {},
               'content': content, "channel": "stdin"}
        return msg

    def opened(self):
        self.send(json.dumps(self.get_execute_header(self.username, self.code)))

    def closed(self, code, reason):
        print("\n\n", self.appended_data)
        self.result = parse_response(self.appended_data)
        self.appended_data.clear()

    def received_message(self, m):
        rsp = json.loads(m.data.decode('utf8'))
        msg_type = rsp["msg_type"]
        if msg_type == "input_request":
            msg = json.dumps(
                self.get_input_header(self.username, self.inputs[self.i])
            )
            self.send(msg.encode("utf-8"))
            self.i += 1
        content = rsp["content"]
        if msg_type == "stream" or msg_type == "error":
            self.appended_data.append(rsp)
        if msg_type == "execute_reply":
            self.execute_reply = content
        if (content.get("status") == "ok" or
                content.get("status") == "error"):
            self.close()

