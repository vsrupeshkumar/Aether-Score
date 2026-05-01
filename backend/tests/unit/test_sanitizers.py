"""
Unit tests for sanitizers
"""
import pytest
from utils.sanitizers import (
    sanitize_html,
    sanitize_chat_message,
    sanitize_address
)


@pytest.mark.unit
class TestSanitizers:
    """Test input sanitizers"""
    
    def test_sanitize_html_safe_text(self):
        """Test sanitizing safe text"""
        text = "Hello, world!"
        result = sanitize_html(text)
        assert result == "Hello, world!"
    
    def test_sanitize_html_script_tag(self):
        """Test sanitizing script tag"""
        text = "<script>alert('XSS')</script>Hello"
        result = sanitize_html(text)
        # HTML is escaped, so script tags become &lt;script&gt;
        assert "<script>" not in result  # Should be escaped
        assert "&lt;script&gt;" in result or "<script>" not in result.lower()
    
    def test_sanitize_html_iframe(self):
        """Test sanitizing iframe"""
        text = "<iframe src='evil.com'></iframe>Content"
        result = sanitize_html(text)
        assert "<iframe" not in result.lower()
    
    def test_sanitize_html_javascript_protocol(self):
        """Test sanitizing javascript: protocol"""
        text = "<a href='javascript:alert(1)'>Click</a>"
        result = sanitize_html(text)
        assert "javascript:" not in result.lower()
    
    def test_sanitize_html_event_handlers(self):
        """Test sanitizing event handlers"""
        text = "<div onclick='alert(1)'>Content</div>"
        result = sanitize_html(text)
        assert "onclick" not in result.lower()
    
    def test_sanitize_html_not_string(self):
        """Test sanitizing non-string"""
        result = sanitize_html(12345)
        assert result == ""
    
    def test_sanitize_chat_message_normal(self):
        """Test sanitizing normal chat message"""
        message = "Hello, I want a loan!"
        result = sanitize_chat_message(message)
        assert result == "Hello, I want a loan!"
    
    def test_sanitize_chat_message_whitespace(self):
        """Test sanitizing message with whitespace"""
        message = "  Hello, world!  "
        result = sanitize_chat_message(message)
        assert result == "Hello, world!"
    
    def test_sanitize_chat_message_html(self):
        """Test sanitizing message with HTML"""
        message = "<script>alert('XSS')</script>Hello"
        result = sanitize_chat_message(message)
        assert "<script>" not in result.lower()
    
    def test_sanitize_chat_message_control_chars(self):
        """Test sanitizing control characters"""
        message = "Hello\x00\x01\x02World"
        result = sanitize_chat_message(message)
        assert "\x00" not in result
        assert "\x01" not in result
    
    def test_sanitize_chat_message_too_long(self):
        """Test sanitizing message that's too long"""
        message = "a" * 2000
        result = sanitize_chat_message(message)
        assert len(result) == 1000
    
    def test_sanitize_chat_message_not_string(self):
        """Test sanitizing non-string message"""
        result = sanitize_chat_message(12345)
        assert result == ""
    
    def test_sanitize_address_valid(self):
        """Test sanitizing valid address"""
        address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = sanitize_address(address)
        assert result == address.lower()
    
    def test_sanitize_address_whitespace(self):
        """Test sanitizing address with whitespace"""
        address = "  0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0  "
        result = sanitize_address(address)
        assert result == "0x742d35cc6634c0532925a3b844bc9e7595f0beb0"
    
    def test_sanitize_address_no_prefix(self):
        """Test sanitizing address without 0x"""
        address = "742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        result = sanitize_address(address)
        assert result.startswith("0x")
        assert len(result) == 42
    
    def test_sanitize_address_invalid(self):
        """Test sanitizing invalid address"""
        address = "not-an-address"
        result = sanitize_address(address)
        assert result is None
    
    def test_sanitize_address_not_string(self):
        """Test sanitizing non-string address"""
        result = sanitize_address(12345)
        assert result is None
    
    def test_sanitize_address_invalid_length(self):
        """Test sanitizing address with invalid length"""
        address = "0x123"
        result = sanitize_address(address)
        assert result is None

