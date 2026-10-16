# 6. Define the tool schema

import inspect

def tool_to_schema(tool_func):
    signature = inspect.signature(tool_func)

    properties = {}
    required = []

    type_mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
    }

    for name, parameter in signature.parameters.items():
        python_type = parameter.annotation

        # print("annotation:", repr(python_type))
        
        if python_type not in type_mapping:
            raise TypeError(
                f"Unsupported type for parameter: {name}"
            )

        properties[name] = {
            "type": type_mapping[python_type]
        }

        if parameter.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": tool_func.__name__,
            "description": inspect.getdoc(tool_func) or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }