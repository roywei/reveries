"""
list of tool functions
"""

import re

TOOL_EXPLAINATION = """
- calculator: A simple calculator that performs basic arithmetic operations.
"""

TOOLS = [
    {
        "name": "calculator",
        "description": "A simple calculator that performs basic arithmetic operations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '2 + 3 * 4').",
                }
            },
            "required": ["expression"],
        },
    }
]


def calculate(expression):
    """
    Simple calculator
    """
    # Remove any non-digit or non-operator characters from the expression
    expression = re.sub(r"[^0-9+\-*/().]", "", expression)

    try:
        # Evaluate the expression using the built-in eval() function
        result = eval(expression)
        return str(result)
    except (SyntaxError, ZeroDivisionError, NameError, TypeError, OverflowError):
        return "Error: Invalid expression"
