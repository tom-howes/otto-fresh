"""
Enhanced chunker optimized for documentation and code completion
Extracts: type hints, docstrings, decorators, exceptions, interfaces, exports, globals
"""
from .chunker import CodeChunker
import re
from typing import List, Dict


class EnhancedCodeChunker(CodeChunker):
    """
    Extended chunker with rich context extraction for:
    - Professional documentation generation
    - Intelligent code completion
    - Deep code understanding
    """
    
    def _extract_file_context(self, content: str, language: str) -> Dict:
        """Enhanced context extraction with all metadata"""
        # Get base context
        context = super()._extract_file_context(content, language)
        
        # Add language-specific enhancements
        if language == 'python':
            context['imports'] = self._extract_python_imports_improved(content)
            context.update({
                'decorators': self._extract_python_decorators(content),
                'type_hints': self._extract_python_type_hints(content),
                'docstrings': self._extract_python_docstrings(content),
                'global_vars': self._extract_python_globals(content),
                'exception_handling': self._extract_python_exceptions(content),
                'class_methods': self._extract_python_class_methods(content),
                'async_functions': self._extract_python_async(content),
            })

        elif language in ['javascript', 'typescript']:
            context['imports'] = self._extract_js_imports_improved(content)
            context.update({
                'exports': self._extract_js_exports(content),
                'async_functions': self._extract_js_async(content),
            })
            
            if language == 'typescript':
                context.update({
                    'interfaces': self._extract_ts_interfaces(content),
                    'types': self._extract_ts_types(content),
                    'enums': self._extract_ts_enums(content),
                    'generics': self._extract_ts_generics(content),
                })
        
        elif language == 'java':
            context.update({
                'annotations': self._extract_java_annotations(content),
                'interfaces': self._extract_java_interfaces(content),
                'access_modifiers': self._extract_java_access_modifiers(content),
            })
        
        return context
    
    def _extract_python_imports_improved(self, content: str) -> List[str]:
        """Improved Python import extraction - catches more patterns"""
        imports = []
        seen = set()
        
        for line in content.split('\n')[:200]:  # Check first 200 lines
            stripped = line.strip()
            
            # Skip comments
            if stripped.startswith('#'):
                continue
            
            # Pattern 1: import module
            if stripped.startswith('import '):
                # Handle: import os, sys, json
                modules = stripped[7:].split(',')
                for module in modules:
                    module = module.strip().split()[0].split('.')[0]  # Get root module
                    if module and module not in seen:
                        imports.append(module)
                        seen.add(module)
            
            # Pattern 2: from module import ...
            elif stripped.startswith('from '):
                match = re.search(r'from\s+([\w.]+)', stripped)
                if match:
                    module = match.group(1).split('.')[0]  # Get root module
                    if module and module not in seen:
                        imports.append(module)
                        seen.add(module)
            
            if len(imports) >= 20:
                break
            
        return imports
    
    def _extract_js_imports_improved(self, content: str) -> List[str]:
        """Improved JavaScript/TypeScript import extraction"""
        imports = []
        seen = set()
        
        for line in content.split('\n')[:200]:
            # Pattern 1: import ... from 'module'
            if 'import' in line and 'from' in line:
                match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', line)
                if match:
                    module = match.group(1)
                    # Get package name (before first /)
                    pkg = module.split('/')[0]
                    if pkg and pkg not in seen and pkg not in ['.', '..']:
                        imports.append(pkg)
                        seen.add(pkg)
            
            # Pattern 2: require('module')
            elif 'require(' in line:
                match = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', line)
                if match:
                    module = match.group(1)
                    pkg = module.split('/')[0]
                    if pkg and pkg not in seen and pkg not in ['.', '..']:
                        imports.append(pkg)
                        seen.add(pkg)
            
            if len(imports) >= 20:
                break
            
        return imports
        
    # ==================== PYTHON EXTRACTORS ====================
    
    def _extract_python_decorators(self, content: str) -> List[str]:
        """Extract Python decorators (e.g., @property, @staticmethod)"""
        decorators = set()
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('@'):
                # Extract decorator name (handle @decorator and @decorator(...))
                match = re.search(r'@([\w.]+)', line)
                if match:
                    decorators.add(match.group(1))
                    if len(decorators) >= 15:
                        break
        return sorted(list(decorators))
    
    def _extract_python_type_hints(self, content: str) -> Dict:
        """Extract type hints from function signatures"""
        type_hints = {}
        
        # Pattern for function with type hints: def func(x: int, y: str) -> bool:
        pattern = r'def\s+(\w+)\s*\((.*?)\)\s*(?:->\s*([^:]+))?:'
        
        for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
            func_name = match.group(1)
            params_str = match.group(2)
            return_type = match.group(3).strip() if match.group(3) else None
            
            # Parse parameters
            params = {}
            if params_str:
                for param in params_str.split(','):
                    param = param.strip()
                    if ':' in param:
                        param_match = re.search(r'(\w+)\s*:\s*([^=]+)', param)
                        if param_match:
                            param_name = param_match.group(1)
                            param_type = param_match.group(2).strip()
                            params[param_name] = param_type
            
            type_hints[func_name] = {
                'params': params,
                'return_type': return_type,
                'signature': f"def {func_name}({params_str})"
            }
            
            if len(type_hints) >= 25:
                break
        
        return type_hints
    
    def _extract_python_docstrings(self, content: str) -> Dict:
        """Extract docstrings from functions and classes"""
        docstrings = {}
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for function/class definition
            match = re.search(r'(def|class)\s+(\w+)', line)
            if match:
                def_type = match.group(1)
                name = match.group(2)
                
                # Look for docstring in next few lines
                j = i + 1
                while j < min(i + 10, len(lines)):
                    next_line = lines[j].strip()
                    
                    # Found docstring start
                    if next_line.startswith('"""') or next_line.startswith("'''"):
                        quote = '"""' if '"""' in next_line else "'''"
                        docstring_lines = [next_line.strip(quote)]
                        
                        # Multi-line docstring
                        if quote not in next_line[3:]:
                            k = j + 1
                            while k < min(j + 20, len(lines)):
                                doc_line = lines[k]
                                if quote in doc_line:
                                    docstring_lines.append(doc_line.split(quote)[0])
                                    break
                                docstring_lines.append(doc_line.strip())
                                k += 1
                        
                        docstring = ' '.join(docstring_lines).strip()
                        docstrings[name] = {
                            'type': def_type,
                            'text': docstring[:300],  # First 300 chars
                            'line': i
                        }
                        break
                    
                    # Skip empty lines and comments
                    if next_line and not next_line.startswith('#'):
                        break
                    
                    j += 1
            
            i += 1
            if len(docstrings) >= 20:
                break
        
        return docstrings
    
    def _extract_python_globals(self, content: str) -> List[str]:
        """Extract global constants and variables"""
        globals_vars = []
        
        for line in content.split('\n')[:150]:
            line_stripped = line.strip()
            
            # Skip comments, imports, and definitions
            if line_stripped.startswith(('#', 'import', 'from', 'def', 'class', '@')):
                continue
            
            # Look for module-level assignments
            if '=' in line and not any(x in line for x in ['==', '!=', '<=', '>=']):
                # Match: CONSTANT = value or variable = value
                match = re.search(r'^([A-Z_][A-Z0-9_]*|[a-z_][a-z0-9_]*)\s*=', line)
                if match:
                    var_name = match.group(1)
                    # Prioritize constants (all caps)
                    if var_name.isupper():
                        globals_vars.insert(0, var_name)
                    else:
                        globals_vars.append(var_name)
                    
            if len(globals_vars) >= 20:
                break
        
        return globals_vars[:20]
    
    def _extract_python_exceptions(self, content: str) -> Dict:
        """Extract exception handling information"""
        exceptions = {
            'raised': set(),
            'caught': set(),
            'custom': []
        }
        
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            # Find raise statements
            if 'raise ' in line:
                match = re.search(r'raise\s+(\w+)', line)
                if match:
                    exceptions['raised'].add(match.group(1))
            
            # Find except clauses
            if 'except ' in line:
                # Handle: except Exception, except (Error1, Error2), except Exception as e
                matches = re.findall(r'except\s+(\w+)', line)
                exceptions['caught'].update(matches)
            
            # Find custom exception definitions
            if 'class ' in line and any(x in line for x in ['Exception', 'Error']):
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    exceptions['custom'].append(match.group(1))
        
        return {
            'raised': sorted(list(exceptions['raised']))[:10],
            'caught': sorted(list(exceptions['caught']))[:10],
            'custom': exceptions['custom'][:5]
        }
    
    def _extract_python_class_methods(self, content: str) -> Dict:
        """Extract class methods and their relationships"""
        class_methods = {}
        current_class = None
        
        for line in content.split('\n'):
            stripped = line.strip()
            
            # New class definition
            if stripped.startswith('class '):
                match = re.search(r'class\s+(\w+)', line)
                if match:
                    current_class = match.group(1)
                    class_methods[current_class] = {
                        'methods': [],
                        'static': [],
                        'class_methods': [],
                        'properties': []
                    }
            
            # Method in a class
            elif current_class and stripped.startswith('def '):
                match = re.search(r'def\s+(\w+)', line)
                if match:
                    method_name = match.group(1)
                    
                    # Check previous lines for decorators
                    if '@staticmethod' in content[max(0, content.find(line)-100):content.find(line)]:
                        class_methods[current_class]['static'].append(method_name)
                    elif '@classmethod' in content[max(0, content.find(line)-100):content.find(line)]:
                        class_methods[current_class]['class_methods'].append(method_name)
                    elif '@property' in content[max(0, content.find(line)-100):content.find(line)]:
                        class_methods[current_class]['properties'].append(method_name)
                    else:
                        class_methods[current_class]['methods'].append(method_name)
            
            # Reset if we're back to module level (no indentation)
            elif not line.startswith((' ', '\t')) and stripped and current_class:
                current_class = None
        
        return class_methods
    
    def _extract_python_async(self, content: str) -> List[str]:
        """Extract async function names"""
        async_funcs = []
        
        for line in content.split('\n'):
            if 'async def ' in line:
                match = re.search(r'async\s+def\s+(\w+)', line)
                if match:
                    async_funcs.append(match.group(1))
                    
            if len(async_funcs) >= 15:
                break
        
        return async_funcs
    
    # ==================== JAVASCRIPT/TYPESCRIPT EXTRACTORS ====================
    
    def _extract_js_exports(self, content: str) -> Dict:
        """Extract JavaScript/TypeScript exports"""
        exports = {
            'named': [],
            'default': None,
            'all': []
        }
        
        for line in content.split('\n')[:200]:
            # Named exports: export const/function/class
            if 'export ' in line and 'default' not in line:
                match = re.search(r'export\s+(?:const|let|var|function|class|interface|type)\s+(\w+)', line)
                if match:
                    name = match.group(1)
                    exports['named'].append(name)
                    exports['all'].append(name)
            
            # Default export
            if 'export default' in line:
                match = re.search(r'export\s+default\s+(\w+)', line)
                if match:
                    exports['default'] = match.group(1)
                    exports['all'].append(f'default:{match.group(1)}')
                elif 'export default class' in line or 'export default function' in line:
                    exports['default'] = 'anonymous'
            
            if len(exports['all']) >= 20:
                break
        
        return exports
    
    def _extract_js_async(self, content: str) -> List[str]:
        """Extract async functions in JavaScript/TypeScript"""
        async_funcs = []
        
        patterns = [
            r'async\s+function\s+(\w+)',
            r'async\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*async',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                async_funcs.append(match.group(1))
        
        return list(set(async_funcs))[:15]
    
    def _extract_ts_interfaces(self, content: str) -> Dict:
        """Extract TypeScript interfaces with their properties"""
        interfaces = {}
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Found interface definition
            if 'interface ' in line:
                match = re.search(r'interface\s+(\w+)', line)
                if match:
                    interface_name = match.group(1)
                    properties = []
                    
                    # Extract properties (next few lines)
                    j = i + 1
                    while j < min(i + 30, len(lines)):
                        prop_line = lines[j].strip()
                        
                        # End of interface
                        if prop_line.startswith('}'):
                            break
                        
                        # Extract property: name: type
                        prop_match = re.search(r'(\w+)[?]?\s*:\s*([^;,]+)', prop_line)
                        if prop_match:
                            properties.append(f"{prop_match.group(1)}: {prop_match.group(2).strip()}")
                        
                        j += 1
                    
                    interfaces[interface_name] = properties[:10]  # First 10 properties
            
            i += 1
            if len(interfaces) >= 15:
                break
        
        return interfaces
    
    def _extract_ts_types(self, content: str) -> Dict:
        """Extract TypeScript type definitions"""
        types = {}
        
        for line in content.split('\n')[:200]:
            if 'type ' in line and '=' in line:
                match = re.search(r'type\s+(\w+)\s*=\s*([^;]+)', line)
                if match:
                    type_name = match.group(1)
                    type_def = match.group(2).strip()
                    types[type_name] = type_def[:100]  # Truncate long definitions
                    
            if len(types) >= 15:
                break
        
        return types
    
    def _extract_ts_enums(self, content: str) -> Dict:
        """Extract TypeScript enums"""
        enums = {}
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            if 'enum ' in line:
                match = re.search(r'enum\s+(\w+)', line)
                if match:
                    enum_name = match.group(1)
                    values = []
                    
                    # Extract enum values
                    j = i + 1
                    while j < min(i + 20, len(lines)):
                        val_line = lines[j].strip()
                        
                        if val_line.startswith('}'):
                            break
                        
                        val_match = re.search(r'(\w+)', val_line)
                        if val_match:
                            values.append(val_match.group(1))
                        
                        j += 1
                    
                    enums[enum_name] = values[:8]
            
            i += 1
            if len(enums) >= 10:
                break
        
        return enums
    
    def _extract_ts_generics(self, content: str) -> List[str]:
        """Extract generic type usage"""
        generics = set()
        
        # Find generic patterns: <T>, <K, V>, etc.
        for match in re.finditer(r'<([A-Z][A-Za-z0-9,\s]+)>', content):
            generic = match.group(1)
            generics.add(generic.strip())
        
        return sorted(list(generics))[:15]
    
    # ==================== JAVA EXTRACTORS ====================
    
    def _extract_java_annotations(self, content: str) -> List[str]:
        """Extract Java annotations"""
        annotations = set()
        
        for line in content.split('\n'):
            if line.strip().startswith('@'):
                match = re.search(r'@(\w+)', line)
                if match:
                    annotations.add(match.group(1))
                    
            if len(annotations) >= 15:
                break
        
        return sorted(list(annotations))
    
    def _extract_java_interfaces(self, content: str) -> List[str]:
        """Extract Java interface names"""
        interfaces = []
        
        for line in content.split('\n')[:200]:
            if 'interface ' in line:
                match = re.search(r'interface\s+(\w+)', line)
                if match:
                    interfaces.append(match.group(1))
                    
            if len(interfaces) >= 15:
                break
        
        return interfaces
    
    def _extract_java_access_modifiers(self, content: str) -> Dict:
        """Extract Java access modifiers usage"""
        modifiers = {
            'public': 0,
            'private': 0,
            'protected': 0,
            'static': 0,
            'final': 0
        }
        
        for line in content.split('\n')[:300]:
            for modifier in modifiers.keys():
                if modifier in line:
                    modifiers[modifier] += 1
        
        return modifiers
    
    # ==================== ENHANCED CONTENT BUILDER ====================
    
    def _build_enriched_content(self, chunk: Dict, file_path: str,
                               file_context: Dict, repo_context: Dict, language: str) -> str:
        """Build super-enriched content with all extracted metadata"""
        
        parts = []
        
        # ===== REPOSITORY CONTEXT =====
        parts.append(f"# Repository: {repo_context['repo_name']}")
        if repo_context['description']:
            parts.append(f"# Description: {repo_context['description']}")
        parts.append(f"# Primary Language: {repo_context['primary_language']}")
        parts.append("")
        
        # ===== FILE CONTEXT =====
        parts.append(f"# File: {file_path}")
        parts.append(f"# Language: {language}")
        
        # Dependencies/Imports
        if file_context.get('imports'):
            imports_str = ', '.join(file_context['imports'][:8])
            parts.append(f"# Imports: {imports_str}")
        
        # Classes and Functions
        if file_context.get('classes'):
            parts.append(f"# Classes: {', '.join(file_context['classes'])}")
        
        if file_context.get('functions'):
            parts.append(f"# Functions: {', '.join(file_context['functions'][:12])}")
        
        # ===== PYTHON-SPECIFIC CONTEXT =====
        if language == 'python':
            if file_context.get('decorators'):
                parts.append(f"# Decorators: {', '.join(file_context['decorators'][:8])}")
            
            if file_context.get('global_vars'):
                parts.append(f"# Globals: {', '.join(file_context['global_vars'][:8])}")
            
            if file_context.get('async_functions'):
                parts.append(f"# Async Functions: {', '.join(file_context['async_functions'][:6])}")
            
            # Exception handling
            exceptions = file_context.get('exception_handling', {})
            if exceptions.get('raised'):
                parts.append(f"# Raises: {', '.join(exceptions['raised'][:5])}")
            if exceptions.get('caught'):
                parts.append(f"# Catches: {', '.join(exceptions['caught'][:5])}")
            if exceptions.get('custom'):
                parts.append(f"# Custom Exceptions: {', '.join(exceptions['custom'])}")
            
            # Type hints for this specific chunk
            type_hints = file_context.get('type_hints', {})
            chunk_name = chunk.get('name', '')
            if chunk_name in type_hints:
                hint = type_hints[chunk_name]
                if hint.get('params'):
                    params_str = ', '.join([f"{k}: {v}" for k, v in list(hint['params'].items())[:5]])
                    parts.append(f"# Parameters: {params_str}")
                if hint.get('return_type'):
                    parts.append(f"# Returns: {hint['return_type']}")
            
            # Docstring for this chunk
            docstrings = file_context.get('docstrings', {})
            if chunk_name in docstrings:
                doc = docstrings[chunk_name]
                parts.append(f"# Docstring: {doc['text'][:150]}")
            
            # Class methods context
            class_methods = file_context.get('class_methods', {})
            for class_name, methods in class_methods.items():
                if class_name in chunk.get('content', ''):
                    if methods.get('methods'):
                        parts.append(f"# Class {class_name} Methods: {', '.join(methods['methods'][:6])}")
                    if methods.get('static'):
                        parts.append(f"# Static Methods: {', '.join(methods['static'])}")
                    if methods.get('properties'):
                        parts.append(f"# Properties: {', '.join(methods['properties'])}")
        
        # ===== TYPESCRIPT-SPECIFIC CONTEXT =====
        if language == 'typescript':
            if file_context.get('interfaces'):
                interfaces = file_context['interfaces']
                parts.append(f"# Interfaces: {', '.join(list(interfaces.keys())[:6])}")
                
                # Show properties for relevant interfaces
                for iface_name, props in list(interfaces.items())[:2]:
                    if props:
                        parts.append(f"# {iface_name} Properties: {', '.join(props[:4])}")
            
            if file_context.get('types'):
                types = file_context['types']
                parts.append(f"# Type Definitions: {', '.join(list(types.keys())[:6])}")
            
            if file_context.get('enums'):
                enums = file_context['enums']
                parts.append(f"# Enums: {', '.join(list(enums.keys())[:4])}")
            
            if file_context.get('generics'):
                parts.append(f"# Generics Used: {', '.join(file_context['generics'][:5])}")
        
        # ===== JAVASCRIPT/TYPESCRIPT EXPORTS =====
        if language in ['javascript', 'typescript']:
            exports = file_context.get('exports', {})
            if exports.get('named'):
                parts.append(f"# Named Exports: {', '.join(exports['named'][:8])}")
            if exports.get('default'):
                parts.append(f"# Default Export: {exports['default']}")
            
            if file_context.get('async_functions'):
                parts.append(f"# Async Functions: {', '.join(file_context['async_functions'][:6])}")
        
        # ===== JAVA-SPECIFIC CONTEXT =====
        if language == 'java':
            if file_context.get('annotations'):
                parts.append(f"# Annotations: {', '.join(file_context['annotations'][:8])}")
            
            if file_context.get('interfaces'):
                parts.append(f"# Interfaces: {', '.join(file_context['interfaces'][:6])}")
            
            modifiers = file_context.get('access_modifiers', {})
            if any(modifiers.values()):
                parts.append(f"# Access: public={modifiers.get('public', 0)}, "
                           f"private={modifiers.get('private', 0)}, "
                           f"protected={modifiers.get('protected', 0)}")
        
        parts.append("")
        
        # ===== CHUNK-SPECIFIC CONTEXT =====
        parts.append(f"# Code Section: {chunk.get('name', 'code_block')}")
        parts.append(f"# Type: {chunk['type']}")
        parts.append(f"# Lines: {chunk['start_line']}-{chunk['end_line']} ({chunk.get('num_lines', 0)} lines)")
        
        if chunk.get('summary'):
            parts.append(f"# Summary: {chunk['summary']}")
        
        parts.append("")
        parts.append("# ===== CODE =====")
        parts.append(chunk['content'])
        
        return '\n'.join(parts)