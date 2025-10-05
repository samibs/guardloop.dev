"""Unit tests for ResponseParser"""

import pytest
from guardloop.core.parser import ResponseParser, CodeBlock, ParsedResponse


class TestResponseParser:
    """Test ResponseParser functionality"""

    @pytest.fixture
    def parser(self):
        """Create parser instance"""
        return ResponseParser()

    def test_extract_code_blocks(self, parser):
        """Test code block extraction"""
        text = """
Here's a Python function:

```python
def hello():
    print("Hello World")
```

And a JavaScript example:

```javascript
console.log("Hello");
```
        """

        blocks = parser.extract_code_blocks(text)

        assert len(blocks) == 2
        assert blocks[0].language == "python"
        assert 'print("Hello World")' in blocks[0].content
        assert blocks[1].language == "javascript"
        assert 'console.log' in blocks[1].content

    def test_extract_file_paths(self, parser):
        """Test file path extraction"""
        text = """
Update the file /path/to/file.py
Also modify ./src/app.js
Check C:/Windows/System32/config.xml
        """

        paths = parser.extract_file_paths(text)

        assert len(paths) >= 2
        assert any("file.py" in p for p in paths)
        assert any("app.js" in p for p in paths)

    def test_extract_commands(self, parser):
        """Test command extraction"""
        text = """
Run the following:
$ npm install
$ pip install requests
Execute: python script.py
        """

        commands = parser.extract_commands(text)

        assert len(commands) >= 2
        assert any("npm install" in c for c in commands)
        assert any("pip install" in c for c in commands)

    def test_extract_test_coverage(self, parser):
        """Test coverage extraction"""
        text1 = "Test coverage: 95.5%"
        text2 = "Coverage is 100%"
        text3 = "No coverage mentioned"

        assert parser.extract_test_coverage(text1) == 95.5
        assert parser.extract_test_coverage(text2) == 100.0
        assert parser.extract_test_coverage(text3) is None

    def test_extract_explanations(self, parser):
        """Test explanation extraction"""
        text = """
This is an explanation paragraph that is long enough to be included.

```python
code here
```

This is another explanation with sufficient length to be extracted.

$ command
        """

        explanations = parser.extract_explanations(text)

        assert len(explanations) >= 1
        assert any("explanation" in e.lower() for e in explanations)

    def test_parse_full_response(self, parser):
        """Test full response parsing"""
        text = """
Here's the implementation:

```python
# File: src/app.py
def authenticate(user):
    try:
        return validate_token(user.token)
    except Exception as e:
        logger.error(f"Auth failed: {e}")
```

Test coverage: 98%

Run this command:
$ pytest tests/

The code includes proper error handling and security checks.
        """

        parsed = parser.parse(text)

        assert len(parsed.code_blocks) >= 1
        assert parsed.test_coverage == 98.0
        assert len(parsed.commands) >= 1
        assert len(parsed.explanations) >= 1
        assert parsed.metadata["has_error_handling"] is True

    def test_metadata_extraction(self, parser):
        """Test metadata extraction"""
        text = """
Security: We need to add authentication
Testing: Unit tests are required
Error handling: try/catch blocks added
        """

        parsed = parser.parse(text)

        assert parsed.metadata["has_security_mentions"] is True
        assert parsed.metadata["has_test_mentions"] is True
        assert parsed.metadata["has_error_handling"] is True

    def test_get_language_from_path(self, parser):
        """Test language detection from file path"""
        assert parser.get_language_from_path("file.py") == "python"
        assert parser.get_language_from_path("app.js") == "javascript"
        assert parser.get_language_from_path("component.tsx") == "typescript"
        assert parser.get_language_from_path("Main.cs") == "csharp"
        assert parser.get_language_from_path("unknown.xyz") is None


class TestCodeBlock:
    """Test CodeBlock dataclass"""

    def test_code_block_creation(self):
        """Test creating code blocks"""
        block = CodeBlock(
            language="python",
            content="print('hello')",
            file_path="test.py",
            line_range=(1, 10),
        )

        assert block.language == "python"
        assert block.content == "print('hello')"
        assert block.file_path == "test.py"
        assert block.line_range == (1, 10)


class TestParsedResponse:
    """Test ParsedResponse dataclass"""

    def test_parsed_response_creation(self):
        """Test creating parsed response"""
        response = ParsedResponse(
            code_blocks=[CodeBlock("python", "code")],
            file_paths=["file.py"],
            commands=["npm install"],
            test_coverage=95.0,
        )

        assert len(response.code_blocks) == 1
        assert len(response.file_paths) == 1
        assert len(response.commands) == 1
        assert response.test_coverage == 95.0
