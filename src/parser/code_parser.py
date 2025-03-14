"""
Code parser implementation for processing code repositories.
"""
from typing import Dict, List, Any, Optional
import os
import logging
from pathlib import Path

import libcst as cst
from tree_sitter import Language, Parser

logger = logging.getLogger(__name__)

class CodeParser:
    """
    Parser for code repositories that extracts structure and relationships
    from source code files.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the code parser.
        
        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.supported_languages = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".go": "go",
            ".rb": "ruby",
            ".rs": "rust",
        }
        
        # Initialize parsers
        self._init_parsers()
        
        logger.info("Code Parser initialized")
    
    def _init_parsers(self):
        """Initialize language-specific parsers."""
        # TODO: Initialize tree-sitter parsers for each supported language
        self.parsers = {}
        
        # For Python, we'll use libcst for more detailed parsing
        self.python_parser = cst.parse_module
    
    async def parse_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Parse a code repository and extract structure and content.
        
        Args:
            repo_path: Path to the code repository
            
        Returns:
            Parsed repository data
        """
        repo_path = Path(repo_path)
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        logger.info(f"Parsing repository: {repo_path}")
        
        parsed_files = []
        for root, _, files in os.walk(repo_path):
            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                
                if ext in self.supported_languages:
                    try:
                        parsed_file = await self.parse_file(file_path)
                        parsed_files.append(parsed_file)
                    except Exception as e:
                        logger.error(f"Error parsing file {file_path}: {e}")
        
        return {
            "repository": str(repo_path),
            "files": parsed_files
        }
    
    async def parse_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse a single file and extract its structure and content.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Parsed file data
        """
        ext = file_path.suffix.lower()
        language = self.supported_languages.get(ext)
        
        if not language:
            raise ValueError(f"Unsupported file type: {ext}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if language == "python":
            return await self._parse_python_file(file_path, content)
        else:
            return await self._parse_generic_file(file_path, content, language)
    
    async def _parse_python_file(self, file_path: Path, content: str) -> Dict[str, Any]:
        """
        Parse a Python file using libcst.
        
        Args:
            file_path: Path to the file
            content: File content
            
        Returns:
            Parsed Python file data
        """
        try:
            module = self.python_parser(content)
            
            # Extract classes and functions
            visitor = PythonStructureVisitor()
            module.visit(visitor)
            
            return {
                "path": str(file_path),
                "language": "python",
                "classes": visitor.classes,
                "functions": visitor.functions,
                "imports": visitor.imports,
                "content": content,
                "chunks": self._chunk_content(content, "python")
            }
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {e}")
            return {
                "path": str(file_path),
                "language": "python",
                "error": str(e),
                "content": content,
                "chunks": self._chunk_content(content, "python")
            }
    
    async def _parse_generic_file(self, file_path: Path, content: str, language: str) -> Dict[str, Any]:
        """
        Parse a file using tree-sitter.
        
        Args:
            file_path: Path to the file
            content: File content
            language: Programming language
            
        Returns:
            Parsed file data
        """
        # TODO: Implement tree-sitter parsing for other languages
        return {
            "path": str(file_path),
            "language": language,
            "content": content,
            "chunks": self._chunk_content(content, language)
        }
    
    def _chunk_content(self, content: str, language: str) -> List[Dict[str, Any]]:
        """
        Split file content into semantic chunks.
        
        Args:
            content: File content
            language: Programming language
            
        Returns:
            List of content chunks
        """
        # Simple chunking by splitting on empty lines
        # TODO: Implement more sophisticated chunking based on language semantics
        chunks = []
        lines = content.split("\n")
        
        current_chunk = []
        current_chunk_start = 0
        
        for i, line in enumerate(lines):
            current_chunk.append(line)
            
            # End of chunk if empty line or chunk size limit reached
            if (not line.strip() or i == len(lines) - 1 or 
                len("\n".join(current_chunk)) > 1000):  # Chunk size limit
                
                if current_chunk:
                    chunk_content = "\n".join(current_chunk)
                    chunks.append({
                        "content": chunk_content,
                        "start_line": current_chunk_start,
                        "end_line": i,
                        "language": language
                    })
                
                current_chunk = []
                current_chunk_start = i + 1
        
        return chunks


class PythonStructureVisitor(cst.CSTVisitor):
    """Visitor to extract structure from Python code."""
    
    def __init__(self):
        super().__init__()
        self.classes = []
        self.functions = []
        self.imports = []
        self.current_class = None
    
    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        class_info = {
            "name": node.name.value,
            "start_line": node.start_pos[0] if node.start_pos else 0,
            "end_line": node.end_pos[0] if node.end_pos else 0,
            "methods": [],
            "bases": [base.value.value for base in node.bases if hasattr(base.value, "value")]
        }
        
        # Store previous class context
        prev_class = self.current_class
        self.current_class = class_info
        self.classes.append(class_info)
        
        # Visit class body
        for statement in node.body.body:
            if isinstance(statement, cst.FunctionDef):
                self.visit_FunctionDef(statement)
        
        # Restore previous class context
        self.current_class = prev_class
    
    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        function_info = {
            "name": node.name.value,
            "start_line": node.start_pos[0] if node.start_pos else 0,
            "end_line": node.end_pos[0] if node.end_pos else 0,
            "parameters": [param.name.value for param in node.params.params 
                          if hasattr(param, "name") and hasattr(param.name, "value")]
        }
        
        if self.current_class:
            self.current_class["methods"].append(function_info)
        else:
            self.functions.append(function_info)
    
    def visit_Import(self, node: cst.Import) -> None:
        for name in node.names:
            self.imports.append({
                "type": "import",
                "name": name.name.value,
                "alias": name.asname.name.value if name.asname else None
            })
    
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        module = ".".join([n.value for n in node.module]) if node.module else ""
        for name in node.names:
            self.imports.append({
                "type": "import_from",
                "module": module,
                "name": name.name.value,
                "alias": name.asname.name.value if name.asname else None
            })