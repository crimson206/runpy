"""Flexible parser system for handling various data formats in CLI input"""

import json
import ast
import re
from typing import Any, Dict, Callable, Optional, List
from abc import ABC, abstractmethod


class ParserError(Exception):
    """Base exception for parser errors"""
    pass


class Parser(ABC):
    """Abstract base class for parsers"""
    
    @abstractmethod
    def can_parse(self, input_string: str) -> bool:
        """Check if this parser can handle the input string"""
        pass
    
    @abstractmethod
    def parse(self, input_string: str) -> Any:
        """Parse the input string and return Python object"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the parser"""
        pass
    
    @property
    def description(self) -> str:
        """Description of the parser"""
        return ""


class JSONParser(Parser):
    """Standard JSON parser - the default"""
    
    @property
    def name(self) -> str:
        return "json"
    
    @property
    def description(self) -> str:
        return "Standard JSON format"
    
    def can_parse(self, input_string: str) -> bool:
        """Check if string is valid JSON"""
        try:
            json.loads(input_string)
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    def parse(self, input_string: str) -> Any:
        """Parse JSON string"""
        try:
            return json.loads(input_string)
        except json.JSONDecodeError as e:
            raise ParserError(f"Invalid JSON: {str(e)}")


class PythonParser(Parser):
    """Python dict/list literal parser using ast.literal_eval"""
    
    @property
    def name(self) -> str:
        return "python"
    
    @property
    def description(self) -> str:
        return "Python dict/list literals (e.g., {'key': 'value'})"
    
    def can_parse(self, input_string: str) -> bool:
        """Check if string is a valid Python literal"""
        try:
            # Try to parse as Python literal
            result = ast.literal_eval(input_string)
            # Ensure it's a dict or list, not just a string/number
            return isinstance(result, (dict, list))
        except (ValueError, SyntaxError):
            return False
    
    def parse(self, input_string: str) -> Any:
        """Parse Python literal"""
        try:
            result = ast.literal_eval(input_string)
            if not isinstance(result, (dict, list)):
                raise ParserError("Input must be a dict or list")
            return result
        except (ValueError, SyntaxError) as e:
            raise ParserError(f"Invalid Python literal: {str(e)}")


class TypeScriptParser(Parser):
    """TypeScript/JavaScript object notation parser"""
    
    @property
    def name(self) -> str:
        return "typescript"
    
    @property
    def description(self) -> str:
        return "TypeScript/JavaScript object notation (e.g., {key: 'value'})"
    
    def can_parse(self, input_string: str) -> bool:
        """Check if string looks like TypeScript object notation"""
        # Basic check for TypeScript-style objects
        trimmed = input_string.strip()
        if not (trimmed.startswith('{') and trimmed.endswith('}')):
            return False
        
        # Check for unquoted keys (TypeScript style)
        # Look for patterns like "key:" without quotes
        unquoted_key_pattern = r'[{,]\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:'
        return bool(re.search(unquoted_key_pattern, trimmed))
    
    def parse(self, input_string: str) -> Any:
        """Convert TypeScript notation to Python dict"""
        try:
            # Replace unquoted keys with quoted keys
            # First, handle keys after opening brace
            json_string = re.sub(r'{\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r'{"\1":', input_string)
            # Then, handle keys after commas
            json_string = re.sub(r',\s*([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:', r',"\1":', json_string)
            
            # Replace single quotes with double quotes for values
            # But be careful not to replace escaped single quotes
            json_string = re.sub(r"(?<!\\)'", '"', json_string)
            
            # Handle boolean values (TypeScript uses lowercase)
            json_string = re.sub(r'\btrue\b', 'true', json_string, flags=re.IGNORECASE)
            json_string = re.sub(r'\bfalse\b', 'false', json_string, flags=re.IGNORECASE)
            json_string = re.sub(r'\bnull\b', 'null', json_string, flags=re.IGNORECASE)
            
            # Try to parse as JSON
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ParserError(f"Failed to parse TypeScript notation: {str(e)}")


class ParserRegistry:
    """Registry for managing multiple parsers"""
    
    def __init__(self):
        self._parsers: List[Parser] = []
        self._default_parser: Optional[Parser] = None
        
        # Register built-in parsers
        self.register(JSONParser(), default=True)
        self.register(PythonParser())
        self.register(TypeScriptParser())
    
    def register(self, parser: Parser, default: bool = False) -> None:
        """Register a new parser"""
        self._parsers.append(parser)
        if default or self._default_parser is None:
            self._default_parser = parser
    
    def unregister(self, parser_name: str) -> None:
        """Remove a parser by name"""
        self._parsers = [p for p in self._parsers if p.name != parser_name]
    
    def get_parser(self, name: str) -> Optional[Parser]:
        """Get a specific parser by name"""
        for parser in self._parsers:
            if parser.name == name:
                return parser
        return None
    
    def parse(self, input_string: str, parser_name: Optional[str] = None) -> Any:
        """
        Parse input string using specified parser or auto-detect
        
        Args:
            input_string: The string to parse
            parser_name: Optional specific parser to use
            
        Returns:
            Parsed Python object
            
        Raises:
            ParserError: If parsing fails
        """
        # If specific parser requested, use it
        if parser_name:
            parser = self.get_parser(parser_name)
            if not parser:
                raise ParserError(f"Parser '{parser_name}' not found")
            return parser.parse(input_string)
        
        # Try each parser in order
        errors = []
        for parser in self._parsers:
            if parser.can_parse(input_string):
                try:
                    return parser.parse(input_string)
                except ParserError as e:
                    errors.append(f"{parser.name}: {str(e)}")
        
        # If no parser could handle it, try default
        if self._default_parser:
            try:
                return self._default_parser.parse(input_string)
            except ParserError as e:
                errors.append(f"{self._default_parser.name} (default): {str(e)}")
        
        # Nothing worked, report all errors
        error_msg = "Failed to parse input with any available parser:\n"
        error_msg += "\n".join(f"  - {error}" for error in errors)
        raise ParserError(error_msg)
    
    def list_parsers(self) -> List[Dict[str, str]]:
        """List all registered parsers"""
        return [
            {
                "name": parser.name,
                "description": parser.description,
                "default": parser == self._default_parser
            }
            for parser in self._parsers
        ]


# Global registry instance
_registry = ParserRegistry()


# Convenience functions
def parse(input_string: str, parser: Optional[str] = None) -> Any:
    """Parse input string using the global parser registry"""
    return _registry.parse(input_string, parser)


def register_parser(parser: Parser, default: bool = False) -> None:
    """Register a custom parser"""
    _registry.register(parser, default)


def list_parsers() -> List[Dict[str, str]]:
    """List all available parsers"""
    return _registry.list_parsers()