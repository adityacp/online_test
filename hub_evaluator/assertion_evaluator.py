# Python Imports
import re
from textwrap import dedent
from functools import partial

# Local Imports
from .hub_client import HubClient
from .utils import parse_response
from yaksh.error_messages import compare_outputs, prettify_exceptions


class AssertionEvaluator:
    def __init__(self, metadata, test_case_data):
        self.language = metadata.get("language")
        self.user_answer = metadata.get('user_answer')
        self.partial_grading = metadata.get('partial_grading')
        self.test_case = test_case_data.get('test_case')
        self.weight = test_case_data.get('weight')
        codes = {
            "python": self.python_code,
            "r": self.r_code,
            "cpp": self.cpp_code,
            "c": self.c_code,
            "java": self.java_code,
            "bash": self.bash_code,
        }
        self.execution_code = codes[self.language]

    def get_result(self, kernel_out, execute_reply):
        success = None
        err = {}
        code_err = True
        if execute_reply.get("status") == "error":
            ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
            success = False
            err = (kernel_out.get("traceback") or
                    "\n".join(execute_reply.get("traceback")))
            err = err.replace("\n", "") if self.language == "cpp" else err
            err = prettify_exceptions(
                "Error", ansi_escape.sub('', err)
            )
        elif execute_reply.get("status") == "timeout":
            success, err = False, kernel_out["traceback"]
            err = prettify_exceptions(
                "TimeoutError", err
            )
        elif execute_reply.get("status") == "ok":
            ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
            success, err = False, kernel_out.get("traceback")
            err = prettify_exceptions(
                "AssertionError", ansi_escape.sub('', err),
                testcase=self.test_case
            ) if err else {}
            if not err:
                success = True
            code_err = False
        return success, err, code_err

    def check_code(self, kernel_id, hub_client, username):
        kernel_out, reply = hub_client.send_code(
            kernel_id, username, self.execution_code
        )
        success, err, code_err = self.get_result(kernel_out, reply)
        return code_err, success, err, self.weight

    @property
    def c_code(self):
        assert_def = dedent("""\
            #define ASSERT(C) if ( !(C) )\
            { fprintf(stderr, "AssertionError: "#C);exit(EXIT_FAILURE); }
            """
            )
        return f"{assert_def}\n{self.user_answer}\n{self.test_case}"

    @property
    def cpp_code(self):
        assert_def = dedent("""\
            #include<iostream>
            #define ASSERT(C) if ( !(C) ){ std::cerr << "AssertionError: "#C; }
            """
            )
        return f".undo\n{assert_def}\n{self.user_answer}\n{self.test_case}"

    @property
    def python_code(self):
        return f"{self.user_answer}\n{self.test_case}"

    @property
    def java_code(self):
        return f"{self.user_answer}\n{self.test_case}"

    @property
    def bash_code(self):
        return f"{self.user_answer}\n{self.test_case}"

    @property
    def r_code(self):
        assert_def = dedent("""\
            ASSERT <- function(result) {
                if(!result) {warning("AssertionError")}
            }
            """)
        return f"{assert_def}\n{self.user_answer}\n{self.test_case}"