"""Main LLM client class for abstracting different LLM providers."""

import json
from typing import List, Dict, Any, Optional, Union, Type
from abc import ABC, abstractmethod

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from .llm_config import LLMConfig, GeminiConfig, OllamaConfig


class LLMClient:
    """Main LLM client that abstracts different LLM providers."""
    
    def __init__(self, config: LLMConfig):
        """Initialize the LLM client with a configuration.
        
        Args:
            config: Configuration object for the LLM provider
        """
        self.config = config
        self._llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the appropriate LLM based on the configuration."""
        if isinstance(self.config, GeminiConfig):
            return ChatGoogleGenerativeAI(
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                google_api_key=self.config.api_key,
            )
        elif isinstance(self.config, OllamaConfig):
            kwargs = {
                "model": self.config.model,
                "temperature": self.config.temperature,
                "base_url": self.config.base_url,
                "timeout": self.config.timeout,
            }
            
            # Add optional parameters if they are set
            if self.config.num_ctx is not None:
                kwargs["num_ctx"] = self.config.num_ctx
            if self.config.num_predict is not None:
                kwargs["num_predict"] = self.config.num_predict
            if self.config.repeat_penalty is not None:
                kwargs["repeat_penalty"] = self.config.repeat_penalty
            if self.config.top_k is not None:
                kwargs["top_k"] = self.config.top_k
            if self.config.top_p is not None:
                kwargs["top_p"] = self.config.top_p
                
            return ChatOllama(**kwargs)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    def chat(
        self,
        messages: Union[str, List[Dict[str, str]]],
        tools: Optional[List[Dict[str, Any]]] = None,
        structured_output: Optional[Type[BaseModel]] = None,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a chat message to the LLM.
        
        Args:
            messages: Either a string message or a list of message dictionaries
                     with 'role' and 'content' keys
            tools: Optional list of tools in OpenAI JSON format
            structured_output: Optional Pydantic model for structured JSON output
            system_message: Optional system message to prepend
            
        Returns:
            Dictionary containing the response, usage info, and any tool calls
        """
        # Convert messages to LangChain format
        formatted_messages = self._format_messages(messages, system_message)
        
        # Configure the LLM chain
        llm_chain = self._llm
        
        # Handle tools if provided
        if tools:
            # Convert OpenAI tool format to LangChain tools
            langchain_tools = self._convert_tools(tools)
            llm_chain = llm_chain.bind_tools(langchain_tools)
        
        # Handle structured output if requested
        if structured_output:
            parser = JsonOutputParser(pydantic_object=structured_output)
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You must respond with valid JSON that matches the required schema. {format_instructions}"),
                *[(msg.type, msg.content) for msg in formatted_messages]
            ])
            
            chain = prompt | llm_chain | parser
            
            try:
                result = chain.invoke({
                    "format_instructions": parser.get_format_instructions()
                })
                return {
                    "content": result,
                    "structured": True,
                    "tool_calls": [],
                    "usage": {}  # Usage info varies by provider
                }
            except Exception as e:
                return {
                    "error": f"Failed to parse structured output: {str(e)}",
                    "content": None,
                    "structured": True,
                    "tool_calls": [],
                    "usage": {}
                }
        
        # Regular chat without structured output
        try:
            if self.config.thinking_enabled:
                # Add thinking prompt for models that support it
                thinking_message = SystemMessage(content="Think step by step before answering. Show your reasoning process.")
                formatted_messages.insert(0, thinking_message)
            
            result = llm_chain.invoke(formatted_messages)
            
            # Extract tool calls if any
            tool_calls = []
            if hasattr(result, 'tool_calls') and result.tool_calls:
                tool_calls = [
                    {
                        "id": tc.get("id", ""),
                        "function": {
                            "name": tc.get("name", ""),
                            "arguments": json.dumps(tc.get("args", {}))
                        },
                        "type": "function"
                    }
                    for tc in result.tool_calls
                ]
            
            return {
                "content": result.content,
                "structured": False,
                "tool_calls": tool_calls,
                "usage": getattr(result, 'usage_metadata', {})
            }
            
        except Exception as e:
            return {
                "error": f"Chat request failed: {str(e)}",
                "content": None,
                "structured": False,
                "tool_calls": [],
                "usage": {}
            }
    
    def _format_messages(
        self, 
        messages: Union[str, List[Dict[str, str]]], 
        system_message: Optional[str] = None
    ) -> List[Union[SystemMessage, HumanMessage, AIMessage]]:
        """Convert messages to LangChain message format."""
        formatted = []
        
        if system_message:
            formatted.append(SystemMessage(content=system_message))
        
        if isinstance(messages, str):
            formatted.append(HumanMessage(content=messages))
        else:
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "system":
                    formatted.append(SystemMessage(content=content))
                elif role == "assistant" or role == "ai":
                    formatted.append(AIMessage(content=content))
                else:  # user or human
                    formatted.append(HumanMessage(content=content))
        
        return formatted
    
    def _convert_tools(self, tools: List[Dict[str, Any]]) -> List:
        """Convert OpenAI tool format to LangChain tools."""
        langchain_tools = []
        
        for tool_def in tools:
            if tool_def.get("type") == "function":
                func_def = tool_def.get("function", {})
                name = func_def.get("name", "")
                description = func_def.get("description", "")
                parameters = func_def.get("parameters", {})
                
                # Create a dynamic tool using LangChain's tool decorator
                @tool(name=name, description=description)
                def dynamic_tool(**kwargs):
                    """Dynamically created tool."""
                    return f"Tool {name} called with arguments: {kwargs}"
                
                # Set the parameters schema
                if parameters:
                    dynamic_tool.args_schema = self._create_args_schema(name, parameters)
                
                langchain_tools.append(dynamic_tool)
        
        return langchain_tools
    
    def _create_args_schema(self, tool_name: str, parameters: Dict[str, Any]) -> Type[BaseModel]:
        """Create a Pydantic model from OpenAI tool parameters."""
        from pydantic import create_model
        
        fields = {}
        properties = parameters.get("properties", {})
        required = parameters.get("required", [])
        
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            prop_description = prop_def.get("description", "")
            
            # Map JSON Schema types to Python types
            if prop_type == "string":
                python_type = str
            elif prop_type == "integer":
                python_type = int
            elif prop_type == "number":
                python_type = float
            elif prop_type == "boolean":
                python_type = bool
            elif prop_type == "array":
                python_type = List[Any]
            elif prop_type == "object":
                python_type = Dict[str, Any]
            else:
                python_type = Any
            
            # Make field optional if not in required list
            if prop_name not in required:
                python_type = Optional[python_type]
            
            fields[prop_name] = (python_type, prop_description)
        
        return create_model(f"{tool_name}Args", **fields)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "thinking_enabled": self.config.thinking_enabled,
        }
