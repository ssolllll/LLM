from typing import Any, Union
import math
import operator


class CalculatorTool:
    """A calculator tool for performing mathematical operations."""

    def __init__(self) -> None:
        self.name: str = "calculator"
        self.title: str = "Mathematical Calculator"
        self.description: str = "Performs basic and advanced mathematical calculations including arithmetic, trigonometry, and logarithms"
        self.input_schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4', 'sin(pi/2)', 'log(100)')"
                },
                "operation": {
                    "type": "string",
                    "enum": ["evaluate", "add", "subtract", "multiply", "divide", "power", "sqrt", "sin", "cos", "tan", "log"],
                    "description": "Type of mathematical operation to perform"
                },
                "operands": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Numbers to operate on (for specific operations)"
                }
            },
            "required": ["operation"]
        }

    def format_for_llm(self) -> str:
        """Format tool information for LLM."""
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = f"- {param_name}: {param_info.get('description', 'No description')}"
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                if "enum" in param_info:
                    arg_desc += f" (options: {', '.join(param_info['enum'])})"
                args_desc.append(arg_desc)

        output = f"Tool: {self.name}\n"
        if self.title:
            output += f"User-readable title: {self.title}\n"
        
        output += f"""Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""
        return output

    def execute(self, operation: str, expression: str = None, operands: list = None) -> dict[str, Any]:
        """Execute the calculator operation."""
        try:
            if operation == "evaluate" and expression:
                # Safe evaluation of mathematical expressions
                allowed_names = {
                    k: v for k, v in math.__dict__.items() if not k.startswith("__")
                }
                allowed_names.update({"abs": abs, "round": round})
                result = eval(expression, {"__builtins__": {}}, allowed_names)
                return {"result": result, "expression": expression}
            
            elif operation in ["add", "subtract", "multiply", "divide", "power"] and operands:
                if len(operands) < 2:
                    return {"error": "At least 2 operands required for this operation"}
                
                ops = {
                    "add": operator.add,
                    "subtract": operator.sub,
                    "multiply": operator.mul,
                    "divide": operator.truediv,
                    "power": operator.pow
                }
                
                result = operands[0]
                for operand in operands[1:]:
                    result = ops[operation](result, operand)
                
                return {"result": result, "operation": operation, "operands": operands}
            
            elif operation == "sqrt" and operands:
                if len(operands) != 1:
                    return {"error": "Square root requires exactly 1 operand"}
                return {"result": math.sqrt(operands[0]), "operation": operation}
            
            elif operation in ["sin", "cos", "tan"] and operands:
                if len(operands) != 1:
                    return {"error": f"{operation} requires exactly 1 operand"}
                trig_funcs = {"sin": math.sin, "cos": math.cos, "tan": math.tan}
                return {"result": trig_funcs[operation](operands[0]), "operation": operation}
            
            elif operation == "log" and operands:
                if len(operands) not in [1, 2]:
                    return {"error": "Log requires 1 or 2 operands"}
                if len(operands) == 1:
                    result = math.log10(operands[0])
                else:
                    result = math.log(operands[0], operands[1])
                return {"result": result, "operation": operation}
            
            else:
                return {"error": "Invalid operation or missing required parameters"}
                
        except Exception as e:
            return {"error": f"Calculation error: {str(e)}"}