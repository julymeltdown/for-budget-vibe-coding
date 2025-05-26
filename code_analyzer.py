import os
import re
import ast
import logging
import json
import sys
from pathlib import Path

class CodeAnalyzer:
    def __init__(self, config_path=None):
        """Initialize code analysis class"""
        # Default configuration
        self.default_config = {
            "src_dir": "src",
            "test_dir": "tests",
            "ignore_dirs": ["venv", "__pycache__", ".git"],
            "ignore_files": ["__init__.py"],
            "mock_patterns": [
                r"# TODO:",
                r"# FIXME:",
                r"mock\.",
                r"@mock",
                r"unittest\.mock",
                r"pytest\.monkeypatch"
            ],
            "commented_code_patterns": [
                r"# [a-zA-Z_][a-zA-Z0-9_]*\s*\(",
                r"# def ",
                r"# class ",
                r"# if ",
                r"# for ",
                r"# while "
            ]
        }
        
        # Load configuration file
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"Configuration file loaded: {config_path}")
            except Exception as e:
                logging.error(f"Failed to load configuration file: {e}")
        
        logging.info("Code analyzer initialization complete")
    
    def find_files(self, directory, extensions=None):
        """Find files in the specified directory."""
        if extensions is None:
            extensions = ['.py']
        
        files = []
        for root, dirs, filenames in os.walk(directory):
            # Exclude directories to ignore
            dirs[:] = [d for d in dirs if d not in self.config["ignore_dirs"]]
            
            for filename in filenames:
                # Check extensions
                if any(filename.endswith(ext) for ext in extensions):
                    # Exclude files to ignore
                    if filename not in self.config["ignore_files"]:
                        files.append(os.path.join(root, filename))
        
        return files
    
    def detect_mocks(self, file_path):
        """Detect mock usage in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Search for mock patterns
            mock_instances = []
            for pattern in self.config["mock_patterns"]:
                for match in re.finditer(pattern, content):
                    line_number = content[:match.start()].count('\n') + 1
                    line_content = content.splitlines()[line_number - 1]
                    mock_instances.append({
                        "line": line_number,
                        "content": line_content,
                        "pattern": pattern
                    })
            
            return mock_instances
        
        except Exception as e:
            logging.error(f"Error detecting mocks: {e}")
            return []
    
    def detect_commented_code(self, file_path):
        """Detect commented out code in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Search for commented code patterns
            commented_code = []
            for pattern in self.config["commented_code_patterns"]:
                for match in re.finditer(pattern, content):
                    line_number = content[:match.start()].count('\n') + 1
                    line_content = content.splitlines()[line_number - 1]
                    commented_code.append({
                        "line": line_number,
                        "content": line_content,
                        "pattern": pattern
                    })
            
            return commented_code
        
        except Exception as e:
            logging.error(f"Error detecting commented code: {e}")
            return []
    
    def analyze_project(self, directory=None):
        """Analyze the entire project."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # Get file list
        files = self.find_files(directory)
        
        # Analysis results
        analysis_result = {
            "total_files": len(files),
            "files_with_mocks": 0,
            "files_with_commented_code": 0,
            "total_mocks": 0,
            "total_commented_code": 0,
            "details": []
        }
        
        # Analyze each file
        for file_path in files:
            file_result = {
                "file": file_path,
                "mocks": self.detect_mocks(file_path),
                "commented_code": self.detect_commented_code(file_path)
            }
            
            # Update statistics
            if file_result["mocks"]:
                analysis_result["files_with_mocks"] += 1
                analysis_result["total_mocks"] += len(file_result["mocks"])
            
            if file_result["commented_code"]:
                analysis_result["files_with_commented_code"] += 1
                analysis_result["total_commented_code"] += len(file_result["commented_code"])
            
            # Add detailed information (only if mocks or commented code found)
            if file_result["mocks"] or file_result["commented_code"]:
                analysis_result["details"].append(file_result)
        
        logging.info(f"Project analysis complete: {analysis_result['total_files']} files, {analysis_result['total_mocks']} mocks, {analysis_result['total_commented_code']} commented code blocks")
        return analysis_result
    
    def get_analysis_summary(self, analysis_result):
        """Return analysis result summary."""
        summary = []
        
        # Mock usage summary
        if analysis_result["total_mocks"] > 0:
            summary.append(f"Mock usage found: {analysis_result['total_mocks']} instances ({analysis_result['files_with_mocks']} files)")
            
            # Top 5 files
            top_files = sorted(
                [f for f in analysis_result["details"] if f["mocks"]],
                key=lambda x: len(x["mocks"]),
                reverse=True
            )[:5]
            
            for file_result in top_files:
                summary.append(f"  - {file_result['file']}: {len(file_result['mocks'])} instances")
        
        # Commented code summary
        if analysis_result["total_commented_code"] > 0:
            summary.append(f"Commented code found: {analysis_result['total_commented_code']} blocks ({analysis_result['files_with_commented_code']} files)")
            
            # Top 5 files
            top_files = sorted(
                [f for f in analysis_result["details"] if f["commented_code"]],
                key=lambda x: len(x["commented_code"]),
                reverse=True
            )[:5]
            
            for file_result in top_files:
                summary.append(f"  - {file_result['file']}: {len(file_result['commented_code'])} blocks")
        
        return "\n".join(summary) if summary else "No temporary code found"
    
    def check_hexagonal_architecture(self, directory=None):
        """Check hexagonal architecture compliance."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # Hexagonal architecture layers
        hexagonal_layers = {
            "domain": False,
            "application": False,
            "infrastructure": False,
            "ports": False,
            "adapters": False
        }
        
        # Check directory structure
        for root, dirs, files in os.walk(directory):
            for layer in hexagonal_layers:
                if layer in os.path.basename(root).lower():
                    hexagonal_layers[layer] = True
        
        # Results
        result = {
            "is_hexagonal": all(hexagonal_layers.values()),
            "layers": hexagonal_layers,
            "missing_layers": [layer for layer, exists in hexagonal_layers.items() if not exists]
        }
        
        if result["is_hexagonal"]:
            logging.info("Hexagonal architecture compliance confirmed")
        else:
            logging.warning(f"Hexagonal architecture non-compliance: missing layers {result['missing_layers']}")
        
        return result
    
    def check_jwt_implementation(self, directory=None):
        """Check JWT implementation."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # JWT-related patterns
        jwt_patterns = [
            r"import\s+jwt",
            r"from\s+jwt\s+import",
            r"\.jwt\.",
            r"JwtService",
            r"JWTService",
            r"TokenService",
            r"accessToken",
            r"refreshToken",
            r"access_token",
            r"refresh_token"
        ]
        
        # Get file list
        files = self.find_files(directory)
        
        # Check JWT implementation
        jwt_files = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for pattern in jwt_patterns:
                    if re.search(pattern, content):
                        jwt_files.append(file_path)
                        break
            
            except Exception as e:
                logging.error(f"Error checking JWT implementation: {e}")
        
        # Results
        result = {
            "has_jwt": len(jwt_files) > 0,
            "jwt_files": jwt_files,
            "jwt_file_count": len(jwt_files)
        }
        
        if result["has_jwt"]:
            logging.info(f"JWT implementation confirmed: {result['jwt_file_count']} files")
        else:
            logging.warning("JWT implementation not found")
        
        return result
    
    def analyze_code_quality(self, directory=None):
        """Analyze code quality comprehensively."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # Analyze mocks and commented code
        mock_analysis = self.analyze_project(directory)
        
        # Check hexagonal architecture
        hexagonal_check = self.check_hexagonal_architecture(directory)
        
        # Check JWT implementation
        jwt_check = self.check_jwt_implementation(directory)
        
        # Comprehensive results
        result = {
            "mock_analysis": mock_analysis,
            "hexagonal_check": hexagonal_check,
            "jwt_check": jwt_check,
            "overall_quality": {
                "has_mocks": mock_analysis["total_mocks"] > 0,
                "has_commented_code": mock_analysis["total_commented_code"] > 0,
                "is_hexagonal": hexagonal_check["is_hexagonal"],
                "has_jwt": jwt_check["has_jwt"]
            }
        }
        
        # Overall quality score (out of 100)
        quality_score = 100
        
        # Deduct points for mocks
        if result["overall_quality"]["has_mocks"]:
            quality_score -= min(30, mock_analysis["total_mocks"] * 2)
        
        # Deduct points for commented code
        if result["overall_quality"]["has_commented_code"]:
            quality_score -= min(20, mock_analysis["total_commented_code"])
        
        # Deduct points for non-hexagonal architecture
        if not result["overall_quality"]["is_hexagonal"]:
            quality_score -= 25
        
        # Deduct points for missing JWT
        if not result["overall_quality"]["has_jwt"]:
            quality_score -= 15
        
        result["overall_quality"]["score"] = max(0, quality_score)
        
        logging.info(f"Code quality analysis complete: score {result['overall_quality']['score']}/100")
        return result


# Test code
if __name__ == "__main__":
    # Logging setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create code analyzer
    analyzer = CodeAnalyzer()
    
    # Test directory analysis
    test_dir = "."
    if len(sys.argv) > 1:
        test_dir = sys.argv[1]
    
    # Analyze project
    analysis_result = analyzer.analyze_project(test_dir)
    
    # Print analysis summary
    summary = analyzer.get_analysis_summary(analysis_result)
    print("\n=== Code Analysis Summary ===")
    print(summary)
    
    # Analyze code quality
    quality_result = analyzer.analyze_code_quality(test_dir)
    print("\n=== Code Quality Analysis Results ===")
    print(f"Quality Score: {quality_result['overall_quality']['score']}/100")
    print(f"Hexagonal Architecture Compliance: {'Yes' if quality_result['hexagonal_check']['is_hexagonal'] else 'No'}")
    print(f"JWT Implementation: {'Yes' if quality_result['jwt_check']['has_jwt'] else 'No'}")
    
    if quality_result['hexagonal_check']['missing_layers']:
        print(f"Missing Hexagonal Layers: {', '.join(quality_result['hexagonal_check']['missing_layers'])}")
