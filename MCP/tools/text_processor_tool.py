from typing import Any, List
import re
import string
from collections import Counter


class TextProcessorTool:
    """A text processing tool for various text manipulation and analysis tasks."""

    def __init__(self) -> None:
        self.name: str = "text_processor"
        self.title: str = "Text Processor"
        self.description: str = "Performs text processing operations including formatting, analysis, search, and transformation"
        self.input_schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": [
                        "word_count", "char_count", "line_count", "sentence_count",
                        "find_replace", "extract_emails", "extract_urls", "clean_text",
                        "to_uppercase", "to_lowercase", "to_title_case", "reverse_text",
                        "remove_punctuation", "extract_numbers", "word_frequency",
                        "split_text", "join_text", "trim_whitespace"
                    ],
                    "description": "Text processing operation to perform"
                },
                "text": {
                    "type": "string",
                    "description": "Input text to process"
                },
                "find_pattern": {
                    "type": "string",
                    "description": "Pattern to find (for find_replace operation)"
                },
                "replace_with": {
                    "type": "string",
                    "description": "Text to replace with (for find_replace operation)"
                },
                "separator": {
                    "type": "string",
                    "default": " ",
                    "description": "Separator for split/join operations"
                },
                "text_list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of text strings (for join_text operation)"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether operations should be case sensitive"
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
                if "default" in param_info:
                    arg_desc += f" (default: {param_info['default']})"
                args_desc.append(arg_desc)

        output = f"Tool: {self.name}\n"
        if self.title:
            output += f"User-readable title: {self.title}\n"
        
        output += f"""Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""
        return output

    def execute(self, operation: str, text: str = None, find_pattern: str = None,
                replace_with: str = None, separator: str = " ", text_list: List[str] = None,
                case_sensitive: bool = True) -> dict[str, Any]:
        """Execute the text processing operation."""
        try:
            if operation in ["word_count", "char_count", "line_count", "sentence_count"] and text is None:
                return {"error": "Text is required for this operation"}
            
            if operation == "word_count":
                words = text.split()
                return {"word_count": len(words), "text_length": len(text)}
            
            elif operation == "char_count":
                return {
                    "char_count": len(text),
                    "char_count_no_spaces": len(text.replace(" ", "")),
                    "char_count_no_whitespace": len(re.sub(r'\s', '', text))
                }
            
            elif operation == "line_count":
                lines = text.split('\n')
                return {"line_count": len(lines), "non_empty_lines": len([l for l in lines if l.strip()])}
            
            elif operation == "sentence_count":
                # Simple sentence detection
                sentences = re.split(r'[.!?]+', text)
                sentences = [s.strip() for s in sentences if s.strip()]
                return {"sentence_count": len(sentences)}
            
            elif operation == "find_replace":
                if text is None or find_pattern is None or replace_with is None:
                    return {"error": "Text, find_pattern, and replace_with are required"}
                
                flags = 0 if case_sensitive else re.IGNORECASE
                result = re.sub(find_pattern, replace_with, text, flags=flags)
                matches = len(re.findall(find_pattern, text, flags=flags))
                
                return {
                    "result": result,
                    "replacements_made": matches,
                    "original_length": len(text),
                    "new_length": len(result)
                }
            
            elif operation == "extract_emails":
                if text is None:
                    return {"error": "Text is required"}
                
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, text)
                return {"emails": emails, "count": len(emails)}
            
            elif operation == "extract_urls":
                if text is None:
                    return {"error": "Text is required"}
                
                url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
                urls = re.findall(url_pattern, text)
                return {"urls": urls, "count": len(urls)}
            
            elif operation == "clean_text":
                if text is None:
                    return {"error": "Text is required"}
                
                # Remove extra whitespace, normalize line breaks
                cleaned = re.sub(r'\s+', ' ', text)
                cleaned = cleaned.strip()
                return {"result": cleaned, "original_length": len(text), "cleaned_length": len(cleaned)}
            
            elif operation == "to_uppercase":
                if text is None:
                    return {"error": "Text is required"}
                return {"result": text.upper()}
            
            elif operation == "to_lowercase":
                if text is None:
                    return {"error": "Text is required"}
                return {"result": text.lower()}
            
            elif operation == "to_title_case":
                if text is None:
                    return {"error": "Text is required"}
                return {"result": text.title()}
            
            elif operation == "reverse_text":
                if text is None:
                    return {"error": "Text is required"}
                return {"result": text[::-1]}
            
            elif operation == "remove_punctuation":
                if text is None:
                    return {"error": "Text is required"}
                
                translator = str.maketrans('', '', string.punctuation)
                result = text.translate(translator)
                return {"result": result}
            
            elif operation == "extract_numbers":
                if text is None:
                    return {"error": "Text is required"}
                
                numbers = re.findall(r'-?\d+\.?\d*', text)
                return {"numbers": numbers, "count": len(numbers)}
            
            elif operation == "word_frequency":
                if text is None:
                    return {"error": "Text is required"}
                
                words = text.lower().split() if not case_sensitive else text.split()
                # Remove punctuation from words
                words = [word.strip(string.punctuation) for word in words if word.strip(string.punctuation)]
                frequency = Counter(words)
                
                return {
                    "word_frequency": dict(frequency.most_common()),
                    "unique_words": len(frequency),
                    "total_words": sum(frequency.values())
                }
            
            elif operation == "split_text":
                if text is None:
                    return {"error": "Text is required"}
                
                parts = text.split(separator)
                return {"result": parts, "count": len(parts)}
            
            elif operation == "join_text":
                if text_list is None:
                    return {"error": "text_list is required for join operation"}
                
                result = separator.join(text_list)
                return {"result": result, "parts_joined": len(text_list)}
            
            elif operation == "trim_whitespace":
                if text is None:
                    return {"error": "Text is required"}
                
                result = text.strip()
                return {
                    "result": result,
                    "original_length": len(text),
                    "trimmed_length": len(result)
                }
            
            else:
                return {"error": f"Unknown operation: {operation}"}
        
        except Exception as e:
            return {"error": f"Text processing failed: {str(e)}"}