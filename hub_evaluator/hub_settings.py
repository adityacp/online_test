# Jupyterhub settings

HUB_VERSION = "5.3"

HUB_HOST = "127.0.0.1:9000"

# Change to https if jupyterhub runs with https
HUB_PROTOCOL = "http"

# Change to wss if jupyterhub runs with https
WEBSOCKET_PROTOCOL = "ws"

HUB_URL = f"{HUB_PROTOCOL}://{HUB_HOST}/hub/api"

API_URL = f"{HUB_PROTOCOL}://{HUB_HOST}"

# Generate the admin token from the JupyterHub and add it here
ADMIN_TOKEN = "09ad55d6f585406bbee0c17e34242ccb"

WS_TIMEOUT = 10

KERNEL_MAPPER = {
    "python": "python3", "c": "c", "cpp": "xcpp14", "java": "java",
    "r": "ir", "bash": "bash"
}

CODE_EVALUATORS = {
    "stdiobasedtestcase":
        "hub_evaluator.stdio_evaluator.StdioEvaluator",
    "standardtestcase":
        "hub_evaluator.assertion_evaluator.AssertionEvaluator",
}
