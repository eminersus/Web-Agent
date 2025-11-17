"""
Basic Tools API - Time, calculations, and text analysis
"""

from fastmcp import FastMCP
from datetime import datetime
from typing import Annotated


class ToolsAPI:
    """Basic utility tools for the Web Agent"""
    
    def __init__(self, mcp: FastMCP):
        """
        Initialize ToolsAPI and register tools with the MCP instance.
        
        Args:
            mcp: FastMCP instance to register tools with
        """
        self.mcp = mcp
        self._register_tools()
    
    def _register_tools(self):
        """Register all tools with the MCP instance."""
        self.mcp.tool()(self.get_current_time)
        self.mcp.tool()(self.calculate)
        self.mcp.tool()(self.analyze_text)
    
    def get_current_time(self) -> str:
        """
        Get the current date and time in a human-readable format.
        
        Returns:
            Current date and time as a formatted string
        
        Example:
            >>> get_current_time()
            "Current time: 2024-01-15 14:30:45"
        """
        now = datetime.now()
        return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def calculate(
        self,
        expression: Annotated[str, "Mathematical expression to evaluate (e.g., '2 + 2 * 3', '(10 + 5) / 3')"]
    ) -> str:
        """
        Calculate a mathematical expression safely.
        
        Supports basic arithmetic operations: +, -, *, /, %, ()
        
        Args:
            expression: Mathematical expression as a string
        
        Returns:
            Result of the calculation or error message
        
        Example:
            >>> calculate("2 + 2 * 3")
            "Result: 8"
            >>> calculate("(10 + 5) / 3")
            "Result: 5.0"
        """
        try:
            # Only allow safe characters for evaluation
            allowed_chars = set('0123456789+-*/()%. ')
            if not all(c in allowed_chars for c in expression):
                return "Error: Expression contains invalid characters. Only numbers and operators (+, -, *, /, %, ()) are allowed."
            
            # Evaluate safely with no access to builtins
            result = eval(expression, {"__builtins__": {}}, {})
            return f"Result: {result}"
        except ZeroDivisionError:
            return "Error: Division by zero"
        except SyntaxError:
            return "Error: Invalid mathematical expression syntax"
        except Exception as e:
            return f"Error calculating expression: {str(e)}"
    
    def analyze_text(
        self,
        text: Annotated[str, "Text to analyze"],
        analysis_type: Annotated[str, "Type of analysis: 'sentiment', 'keywords', or 'summary'"] = "sentiment"
    ) -> dict:
        """
        Analyze text for sentiment, keywords, or generate a summary.
        
        This is a placeholder implementation. In production, you would integrate
        with NLP libraries or APIs.
        
        Args:
            text: The text to analyze
            analysis_type: Type of analysis - "sentiment", "keywords", or "summary"
        
        Returns:
            Dictionary containing analysis results
        
        Example:
            >>> analyze_text("This is a great product!", "sentiment")
            {"text_length": 24, "word_count": 5, "analysis_type": "sentiment", 
             "sentiment": "positive", "confidence": 0.75}
        """
        result = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "analysis_type": analysis_type,
        }
        
        if analysis_type == "sentiment":
            # Simple placeholder sentiment analysis
            positive_words = {"great", "excellent", "good", "wonderful", "amazing", "fantastic"}
            negative_words = {"bad", "terrible", "awful", "horrible", "poor", "worst"}
            
            words = set(text.lower().split())
            pos_count = len(words & positive_words)
            neg_count = len(words & negative_words)
            
            if pos_count > neg_count:
                result["sentiment"] = "positive"
                result["confidence"] = 0.75
            elif neg_count > pos_count:
                result["sentiment"] = "negative"
                result["confidence"] = 0.75
            else:
                result["sentiment"] = "neutral"
                result["confidence"] = 0.60
        
        elif analysis_type == "keywords":
            # Extract first 5 words as keywords (placeholder)
            words = text.split()
            result["keywords"] = words[:5] if len(words) > 5 else words
        
        elif analysis_type == "summary":
            # Simple truncation summary
            result["summary"] = text[:100] + "..." if len(text) > 100 else text
        
        else:
            result["error"] = f"Unknown analysis type: {analysis_type}"
        
        return result

