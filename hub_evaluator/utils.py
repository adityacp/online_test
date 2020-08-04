# Python Imports
import importlib

# Local Imports
from .hub_settings import HUB_VERSION, CODE_EVALUATORS


def getIn(r, pth):
    for p in pth:
        r = r.get(p, {})
    return r


def parse_response(response):
    error = []
    output = []
    timeout = []
    parsed_data = {}
    if response:
        for data in response:
            name = getIn(data, ['content', 'name'])
            content = getIn(data, ['content'])
            if "traceback" in content:
                error.append("\n".join(content["traceback"]))
            elif name == "stderr":
                error.append(getIn(data, ['content', 'text']))
            elif name == "timeout":
                timeout.append(getIn(data, ['content', 'timeout']))
            elif name == "stdout":
                output.append(getIn(data, ['content', 'text']))
        if error:
            parsed_data = {"status": "error", "traceback": "\n".join(error)}
        if output:
            parsed_data = {"status": "output", "output": "".join(output)}
        if timeout:
            parsed_data = {"status": "timeout", "traceback": "".join(timeout)}
    else:
        parsed_data = {'status': "output", 'output': ""}
    return parsed_data


def create_evaluator_instance(metadata, test_case):

    def get_class(tc_type):
        _cls = CODE_EVALUATORS.get(tc_type)
        module_name, class_name = _cls.rsplit(".", 1)
        # load the module, will raise ImportError if module cannot be loaded
        get_module = importlib.import_module(module_name)
        # get the class, will raise AttributeError if class cannot be found
        get_class = getattr(get_module, class_name)
        return get_class

    cls = get_class(test_case.get('test_case_type'))
    instance = cls(metadata, test_case)
    return instance




