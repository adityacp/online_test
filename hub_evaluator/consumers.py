# Python, Django and Channels Imports
import json
import time
import os
import asyncio
from django.shortcuts import get_object_or_404
from django.template import Context, Template
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async

# Local Imports
from hub_evaluator.hub_client import HubClient
from hub_evaluator.hub_settings import WEBSOCKET_PROTOCOL, HUB_HOST
from hub_evaluator.utils import parse_response, create_evaluator_instance
from yaksh.models import AnswerPaper
from .models import Authentication


class HubConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
        self.username = self.user.username
        self.room_group_name = f'quiz_{self.username}'
        self.token = await self.get_token()
        self.hc = HubClient(token=self.token)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        code = text_data_json.get('code')
        kernel_id = text_data_json.get('kernel_id')
        answer_data = text_data_json.get("result")
        start = time.perf_counter()
        tc_data = json.loads(await self.get_data(
            code, answer_data.get("uid"), answer_data.get("ap_id")
        ))
        test_case_instances = await self.get_evaluator_objects(tc_data)
        success = False
        test_case_success_status = [False]
        if len(test_case_instances) != 0:
            test_case_success_status = [False] * len(test_case_instances)
        error = []
        weight = 0.0
        result = {}
        template_path = os.path.join(os.path.dirname(__file__),
                                     'templates', 'error_template.html'
                                    )
        for idx, test_case_instance in enumerate(test_case_instances):
            eval_result = await asyncio.wait_for(
                sync_to_async(test_case_instance.check_code)(
                    kernel_id, self.hc, self.username
                ), timeout=10
            )
            code_err, test_case_success, err, mark_fraction = eval_result
            if test_case_success:
                weight += mark_fraction * test_case_instance.weight
            else:
                error.append(err)
            test_case_success_status[idx] = test_case_success
            if err.get("exception") == "TimeoutError":
                await self.hc.interrupt_user_kernel(
                    self.username, kernel_id
                )
                break
        print(f"\n\n Elapsed {time.perf_counter() - start} secs")
        success = all(test_case_success_status)
        result["success"] = success
        if not success:
            with open(template_path) as f:
                template_data = f.read()
                template = Template(template_data)
                context = Context({"error_message": error})
                render_error = template.render(context)
                result["error"] = render_error
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'send_message',
                'code': code,
                'response': result.get("error"),
                'success': result.get("success")
            }
        )

    # Receive message from room group
    async def send_message(self, event):
        code = event['code']
        result = event['response']
        success = event['success']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'code': code,
            'response': result,
            'success': success
        }))

    @database_sync_to_async
    def get_data(self, code, uid, ap_id):
        self.paper = get_object_or_404(AnswerPaper, id=ap_id, user=self.user)
        self.answer = self.paper.answers.select_related('question').get(id=uid)
        question = self.answer.question
        return question.consolidate_answer_data(code, self.user)

    @database_sync_to_async
    def update_paper(self):
        print("update_paper", self.paper, self.answer)

    @database_sync_to_async
    def get_token(self):
        return Authentication.objects.filter(user=self.user).last().token

    async def get_evaluator_objects(self, kwargs):
        metadata = kwargs.get('metadata')
        test_case_data = kwargs.get('test_case_data')
        test_case_instances = []

        for test_case in test_case_data:
            test_case_instance = create_evaluator_instance(metadata, test_case)
            test_case_instances.append(test_case_instance)
        return test_case_instances
