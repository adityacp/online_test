# Python and Django Imports
import re
from asgiref.sync import async_to_sync

# Local Imports
from .hub_client import HubClient
from .utils import parse_response
from yaksh.error_messages import compare_outputs, prettify_exceptions


class StdioEvaluator:
    def __init__(self, metadata, test_case_data):
        self.language = metadata.get("language")
        self.user_answer = metadata.get('user_answer')
        self.partial_grading = metadata.get('partial_grading')
        self.expected_input = test_case_data.get('expected_input')
        self.expected_output = test_case_data.get('expected_output')
        self.weight = test_case_data.get('weight')

    def get_result(self, kernel_out, execute_reply):
        success = None
        err = {}
        code_err = True
        if execute_reply.get("status") == "error":
            ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
            success, err = False, kernel_out.get("traceback") or kernel_out.get("output")
            err = prettify_exceptions(
                "Error", ansi_escape.sub('', err)
            )
        elif execute_reply.get("status") == "timeout":
            success, err = False, kernel_out["traceback"]
            err = prettify_exceptions(
                "TimeoutError", err
            )
        elif execute_reply.get("status") == "ok":
            user_output = kernel_out.get("output").replace("[1] ", "")
            success, err = compare_outputs(self.expected_output,
                                           user_output,
                                           self.expected_input
                                           )
            code_err = False
        return success, err, code_err

    def check_code(self, kernel_id, hub_client, username):
        kernel_out, reply = hub_client.send_code(
            kernel_id, username, self.user_answer,
            self.expected_input.replace("\r", "").split("\n")
        )
        # response = parse_response(kernel_out)
        success, err, code_err = self.get_result(kernel_out, reply)
        return code_err, success, err, self.weight
