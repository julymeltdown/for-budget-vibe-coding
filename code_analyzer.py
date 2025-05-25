import os
import re
import ast
import logging
import json
from pathlib import Path

class CodeAnalyzer:
    def __init__(self, config_path=None):
        """코드 분석 클래스 초기화"""
        # 기본 설정
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
        
        # 설정 파일 로드
        self.config = self.default_config.copy()
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    self.config.update(user_config)
                logging.info(f"설정 파일 로드 완료: {config_path}")
            except Exception as e:
                logging.error(f"설정 파일 로드 실패: {e}")
        
        logging.info("코드 분석기 초기화 완료")
    
    def find_files(self, directory, extensions=None):
        """지정된 디렉토리에서 파일을 찾습니다."""
        if extensions is None:
            extensions = ['.py']
        
        files = []
        for root, dirs, filenames in os.walk(directory):
            # 무시할 디렉토리 제외
            dirs[:] = [d for d in dirs if d not in self.config["ignore_dirs"]]
            
            for filename in filenames:
                # 확장자 확인
                if any(filename.endswith(ext) for ext in extensions):
                    # 무시할 파일 제외
                    if filename not in self.config["ignore_files"]:
                        files.append(os.path.join(root, filename))
        
        return files
    
    def detect_mocks(self, file_path):
        """파일에서 모의(mock) 처리를 감지합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 모의 처리 패턴 검색
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
            logging.error(f"모의 처리 감지 중 오류 발생: {e}")
            return []
    
    def detect_commented_code(self, file_path):
        """파일에서 주석 처리된 코드를 감지합니다."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 주석 처리된 코드 패턴 검색
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
            logging.error(f"주석 처리된 코드 감지 중 오류 발생: {e}")
            return []
    
    def analyze_project(self, directory=None):
        """프로젝트 전체를 분석합니다."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # 파일 목록 가져오기
        files = self.find_files(directory)
        
        # 분석 결과
        analysis_result = {
            "total_files": len(files),
            "files_with_mocks": 0,
            "files_with_commented_code": 0,
            "total_mocks": 0,
            "total_commented_code": 0,
            "details": []
        }
        
        # 각 파일 분석
        for file_path in files:
            file_result = {
                "file": file_path,
                "mocks": self.detect_mocks(file_path),
                "commented_code": self.detect_commented_code(file_path)
            }
            
            # 통계 업데이트
            if file_result["mocks"]:
                analysis_result["files_with_mocks"] += 1
                analysis_result["total_mocks"] += len(file_result["mocks"])
            
            if file_result["commented_code"]:
                analysis_result["files_with_commented_code"] += 1
                analysis_result["total_commented_code"] += len(file_result["commented_code"])
            
            # 상세 정보 추가 (모의 처리 또는 주석 처리된 코드가 있는 경우에만)
            if file_result["mocks"] or file_result["commented_code"]:
                analysis_result["details"].append(file_result)
        
        logging.info(f"프로젝트 분석 완료: {analysis_result['total_files']} 파일, {analysis_result['total_mocks']} 모의 처리, {analysis_result['total_commented_code']} 주석 처리된 코드")
        return analysis_result
    
    def get_analysis_summary(self, analysis_result):
        """분석 결과 요약을 반환합니다."""
        summary = []
        
        # 모의 처리 요약
        if analysis_result["total_mocks"] > 0:
            summary.append(f"모의(mock) 처리 발견: {analysis_result['total_mocks']} 개 ({analysis_result['files_with_mocks']} 파일)")
            
            # 상위 5개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["mocks"]],
                key=lambda x: len(x["mocks"]),
                reverse=True
            )[:5]
            
            for file_result in top_files:
                summary.append(f"  - {file_result['file']}: {len(file_result['mocks'])} 개")
        
        # 주석 처리된 코드 요약
        if analysis_result["total_commented_code"] > 0:
            summary.append(f"주석 처리된 코드 발견: {analysis_result['total_commented_code']} 개 ({analysis_result['files_with_commented_code']} 파일)")
            
            # 상위 5개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["commented_code"]],
                key=lambda x: len(x["commented_code"]),
                reverse=True
            )[:5]
            
            for file_result in top_files:
                summary.append(f"  - {file_result['file']}: {len(file_result['commented_code'])} 개")
        
        return "\n".join(summary) if summary else "임시 처리 없음"
    
    def check_hexagonal_architecture(self, directory=None):
        """헥사고날 아키텍처 준수 여부를 검사합니다."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # 헥사고날 아키텍처 레이어
        hexagonal_layers = {
            "domain": False,
            "application": False,
            "infrastructure": False,
            "ports": False,
            "adapters": False
        }
        
        # 디렉토리 구조 확인
        for root, dirs, files in os.walk(directory):
            for layer in hexagonal_layers:
                if layer in os.path.basename(root).lower():
                    hexagonal_layers[layer] = True
        
        # 결과
        result = {
            "is_hexagonal": all(hexagonal_layers.values()),
            "layers": hexagonal_layers,
            "missing_layers": [layer for layer, exists in hexagonal_layers.items() if not exists]
        }
        
        if result["is_hexagonal"]:
            logging.info("헥사고날 아키텍처 준수 확인")
        else:
            logging.warning(f"헥사고날 아키텍처 미준수: 누락된 레이어 {result['missing_layers']}")
        
        return result
    
    def check_jwt_implementation(self, directory=None):
        """JWT 구현 여부를 검사합니다."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # JWT 관련 패턴
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
        
        # 파일 목록 가져오기
        files = self.find_files(directory)
        
        # JWT 구현 검사
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
                logging.error(f"JWT 구현 검사 중 오류 발생: {e}")
        
        # 결과
        result = {
            "has_jwt": len(jwt_files) > 0,
            "jwt_files": jwt_files,
            "jwt_file_count": len(jwt_files)
        }
        
        if result["has_jwt"]:
            logging.info(f"JWT 구현 확인: {result['jwt_file_count']} 파일")
        else:
            logging.warning("JWT 구현 미확인")
        
        return result
    
    def analyze_code_quality(self, directory=None):
        """코드 품질을 종합적으로 분석합니다."""
        if directory is None:
            directory = self.config["src_dir"]
        
        # 모의 처리 및 주석 처리된 코드 분석
        mock_analysis = self.analyze_project(directory)
        
        # 헥사고날 아키텍처 검사
        hexagonal_check = self.check_hexagonal_architecture(directory)
        
        # JWT 구현 검사
        jwt_check = self.check_jwt_implementation(directory)
        
        # 종합 결과
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
        
        # 종합 품질 점수 (100점 만점)
        quality_score = 100
        
        # 모의 처리 감점
        if result["overall_quality"]["has_mocks"]:
            quality_score -= min(30, mock_analysis["total_mocks"] * 2)
        
        # 주석 처리된 코드 감점
        if result["overall_quality"]["has_commented_code"]:
            quality_score -= min(20, mock_analysis["total_commented_code"])
        
        # 헥사고날 아키텍처 미준수 감점
        if not result["overall_quality"]["is_hexagonal"]:
            quality_score -= 25
        
        # JWT 미구현 감점
        if not result["overall_quality"]["has_jwt"]:
            quality_score -= 15
        
        result["overall_quality"]["score"] = max(0, quality_score)
        
        logging.info(f"코드 품질 분석 완료: 점수 {result['overall_quality']['score']}/100")
        return result


# 테스트 코드
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 코드 분석기 생성
    analyzer = CodeAnalyzer()
    
    # 테스트 디렉토리 분석
    test_dir = "."
    if len(sys.argv) > 1:
        test_dir = sys.argv[1]
    
    # 프로젝트 분석
    analysis_result = analyzer.analyze_project(test_dir)
    
    # 분석 결과 요약 출력
    summary = analyzer.get_analysis_summary(analysis_result)
    print("\n=== 코드 분석 결과 요약 ===")
    print(summary)
    
    # 코드 품질 분석
    quality_result = analyzer.analyze_code_quality(test_dir)
    print("\n=== 코드 품질 분석 결과 ===")
    print(f"품질 점수: {quality_result['overall_quality']['score']}/100")
    print(f"헥사고날 아키텍처 준수: {'예' if quality_result['hexagonal_check']['is_hexagonal'] else '아니오'}")
    print(f"JWT 구현: {'예' if quality_result['jwt_check']['has_jwt'] else '아니오'}")
    
    if quality_result['hexagonal_check']['missing_layers']:
        print(f"누락된 헥사고날 레이어: {', '.join(quality_result['hexagonal_check']['missing_layers'])}")
