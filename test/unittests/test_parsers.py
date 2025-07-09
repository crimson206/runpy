"""Unit tests for the flexible parser system"""

import pytest
from runpycli.parsers import (
    JSONParser, PythonParser, TypeScriptParser,
    ParserRegistry, ParserError, parse
)


class TestJSONParser:
    """Test standard JSON parser"""
    
    def test_valid_json_dict(self):
        parser = JSONParser()
        result = parser.parse('{"name": "test", "value": 123}')
        assert result == {"name": "test", "value": 123}
    
    def test_valid_json_list(self):
        parser = JSONParser()
        result = parser.parse('[1, 2, 3]')
        assert result == [1, 2, 3]
    
    def test_json_with_bool_and_null(self):
        parser = JSONParser()
        result = parser.parse('{"active": true, "disabled": false, "empty": null}')
        assert result == {"active": True, "disabled": False, "empty": None}
    
    def test_invalid_json(self):
        parser = JSONParser()
        with pytest.raises(ParserError) as exc_info:
            parser.parse('{invalid json}')
        assert "Invalid JSON" in str(exc_info.value)
    
    def test_can_parse_valid_json(self):
        parser = JSONParser()
        assert parser.can_parse('{"key": "value"}')
        assert parser.can_parse('[]')
        assert not parser.can_parse('not json')


class TestPythonParser:
    """Test Python dict/list literal parser"""
    
    def test_python_dict_single_quotes(self):
        parser = PythonParser()
        result = parser.parse("{'name': 'test', 'value': 123}")
        assert result == {"name": "test", "value": 123}
    
    def test_python_dict_double_quotes(self):
        parser = PythonParser()
        result = parser.parse('{"name": "test", "value": 123}')
        assert result == {"name": "test", "value": 123}
    
    def test_python_list(self):
        parser = PythonParser()
        result = parser.parse("[1, 2, 3, 'string']")
        assert result == [1, 2, 3, "string"]
    
    def test_python_with_bool_and_none(self):
        parser = PythonParser()
        result = parser.parse("{'active': True, 'disabled': False, 'empty': None}")
        assert result == {"active": True, "disabled": False, "empty": None}
    
    def test_invalid_python_literal(self):
        parser = PythonParser()
        with pytest.raises(ParserError) as exc_info:
            parser.parse("{'key': some_variable}")  # undefined variable
        assert "Invalid Python literal" in str(exc_info.value)
    
    def test_can_parse_python_literals(self):
        parser = PythonParser()
        assert parser.can_parse("{'key': 'value'}")
        assert parser.can_parse('["list", "items"]')
        assert not parser.can_parse('"just a string"')  # strings are not dicts/lists


class TestTypeScriptParser:
    """Test TypeScript/JavaScript object notation parser"""
    
    def test_unquoted_keys(self):
        parser = TypeScriptParser()
        result = parser.parse('{name: "test", value: 123}')
        assert result == {"name": "test", "value": 123}
    
    def test_single_quoted_values(self):
        parser = TypeScriptParser()
        result = parser.parse("{name: 'test', value: 123}")
        assert result == {"name": "test", "value": 123}
    
    def test_mixed_quotes(self):
        parser = TypeScriptParser()
        result = parser.parse('{first: "double", second: \'single\'}')
        assert result == {"first": "double", "second": "single"}
    
    def test_typescript_booleans(self):
        parser = TypeScriptParser()
        result = parser.parse('{active: true, disabled: false, empty: null}')
        assert result == {"active": True, "disabled": False, "empty": None}
    
    def test_nested_objects(self):
        parser = TypeScriptParser()
        result = parser.parse('{user: {name: "John", age: 30}, active: true}')
        assert result == {"user": {"name": "John", "age": 30}, "active": True}
    
    def test_arrays_in_typescript(self):
        parser = TypeScriptParser()
        result = parser.parse('{items: [1, 2, 3], names: ["a", "b"]}')
        assert result == {"items": [1, 2, 3], "names": ["a", "b"]}
    
    def test_can_parse_typescript_notation(self):
        parser = TypeScriptParser()
        assert parser.can_parse('{key: "value"}')
        assert parser.can_parse('{key: "value", another: 123}')
        assert not parser.can_parse('{"key": "value"}')  # This is valid JSON, not TS style


class TestParserRegistry:
    """Test the parser registry and auto-detection"""
    
    def test_registry_initialization(self):
        registry = ParserRegistry()
        parsers = registry.list_parsers()
        assert len(parsers) == 3
        assert any(p["name"] == "json" for p in parsers)
        assert any(p["name"] == "python" for p in parsers)
        assert any(p["name"] == "typescript" for p in parsers)
    
    def test_auto_detect_json(self):
        registry = ParserRegistry()
        result = registry.parse('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_auto_detect_python(self):
        registry = ParserRegistry()
        result = registry.parse("{'key': 'value', 'number': 42}")
        assert result == {"key": "value", "number": 42}
    
    def test_auto_detect_typescript(self):
        registry = ParserRegistry()
        result = registry.parse('{key: "value", number: 42}')
        assert result == {"key": "value", "number": 42}
    
    def test_specify_parser(self):
        registry = ParserRegistry()
        # Force using JSON parser for Python-style input
        with pytest.raises(ParserError):
            registry.parse("{'key': 'value'}", parser_name="json")
    
    def test_unknown_parser(self):
        registry = ParserRegistry()
        with pytest.raises(ParserError) as exc_info:
            registry.parse('{"key": "value"}', parser_name="unknown")
        assert "Parser 'unknown' not found" in str(exc_info.value)
    
    def test_unparseable_input(self):
        registry = ParserRegistry()
        with pytest.raises(ParserError) as exc_info:
            registry.parse("this is not valid input")
        assert "Failed to parse input with any available parser" in str(exc_info.value)


class TestGlobalParseFunctions:
    """Test the global convenience functions"""
    
    def test_global_parse_json(self):
        result = parse('{"test": true}')
        assert result == {"test": True}
    
    def test_global_parse_python(self):
        result = parse("{'test': True}")
        assert result == {"test": True}
    
    def test_global_parse_typescript(self):
        result = parse('{test: true}')
        assert result == {"test": True}
    
    def test_global_parse_with_parser_name(self):
        result = parse('{"test": 123}', parser="json")
        assert result == {"test": 123}


class TestEdgeCases:
    """Test edge cases and special scenarios"""
    
    def test_empty_objects(self):
        assert parse('{}') == {}
        assert parse('[]') == []
    
    def test_whitespace_handling(self):
        result = parse('  {  "key"  :  "value"  }  ')
        assert result == {"key": "value"}
        
        result = parse('  {  key  :  "value"  }  ')
        assert result == {"key": "value"}
    
    def test_special_characters_in_keys(self):
        # TypeScript parser should handle underscore and dollar signs
        parser = TypeScriptParser()
        result = parser.parse('{_key: "value", $var: 123, key_name: true}')
        assert result == {"_key": "value", "$var": 123, "key_name": True}
    
    def test_unicode_values(self):
        result = parse('{"emoji": "🎉", "text": "Hello, 世界"}')
        assert result == {"emoji": "🎉", "text": "Hello, 世界"}
    
    def test_escaped_quotes(self):
        # JSON with escaped quotes
        result = parse('{"text": "He said \\"Hello\\""}')
        assert result == {"text": 'He said "Hello"'}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])