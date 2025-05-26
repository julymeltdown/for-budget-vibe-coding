import os
import json
import logging
import requests
import time
import re

class NotificationManager:
    def __init__(self, config_path=None):
        """알림 관리자 클래스 초기화"""
        # 기본 설정
        self.default_config = {
            "enabled": True,
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "",
                "username": "Automation Bot"
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "notification_cooldown": 300,  # 5분
            "last_notification_time": {}
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
        
        logging.info("알림 관리자 초기화 완료")
    
    def send_slack_notification(self, message, attachments=None):
        """Slack으로 알림을 전송합니다."""
        if not self.config["enabled"] or not self.config["slack"]["enabled"]:
            logging.info("Slack 알림 비활성화됨")
            return False
        
        if not self.config["slack"]["webhook_url"]:
            logging.error("Slack webhook URL이 설정되지 않음")
            return False
        
        # 쿨다운 확인
        notification_key = f"slack_{hash(message)}"
        last_time = self.config["last_notification_time"].get(notification_key, 0)
        current_time = time.time()
        
        if current_time - last_time < self.config["notification_cooldown"]:
            logging.info(f"Slack 알림 쿨다운 중 (남은 시간: {int(self.config['notification_cooldown'] - (current_time - last_time))}초)")
            return False
        
        try:
            # 알림 데이터 구성
            payload = {
                "text": message,
                "username": self.config["slack"]["username"]
            }
            
            if self.config["slack"]["channel"]:
                payload["channel"] = self.config["slack"]["channel"]
            
            if attachments:
                payload["attachments"] = attachments
            
            # 알림 전송
            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=payload
            )
            
            if response.status_code == 200:
                logging.info("Slack 알림 전송 성공")
                
                # 마지막 알림 시간 업데이트
                self.config["last_notification_time"][notification_key] = current_time
                
                return True
            else:
                logging.error(f"Slack 알림 전송 실패: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logging.error(f"Slack 알림 전송 중 오류 발생: {e}")
            return False
    
    def send_telegram_notification(self, message):
        """Telegram으로 알림을 전송합니다."""
        if not self.config["enabled"] or not self.config["telegram"]["enabled"]:
            logging.info("Telegram 알림 비활성화됨")
            return False
        
        if not self.config["telegram"]["bot_token"] or not self.config["telegram"]["chat_id"]:
            logging.error("Telegram 봇 토큰 또는 채팅 ID가 설정되지 않음")
            return False
        
        # 쿨다운 확인
        notification_key = f"telegram_{hash(message)}"
        last_time = self.config["last_notification_time"].get(notification_key, 0)
        current_time = time.time()
        
        if current_time - last_time < self.config["notification_cooldown"]:
            logging.info(f"Telegram 알림 쿨다운 중 (남은 시간: {int(self.config['notification_cooldown'] - (current_time - last_time))}초)")
            return False
        
        try:
            # 알림 전송
            url = f"https://api.telegram.org/bot{self.config['telegram']['bot_token']}/sendMessage"
            payload = {
                "chat_id": self.config["telegram"]["chat_id"],
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                logging.info("Telegram 알림 전송 성공")
                
                # 마지막 알림 시간 업데이트
                self.config["last_notification_time"][notification_key] = current_time
                
                return True
            else:
                logging.error(f"Telegram 알림 전송 실패: {response.status_code} {response.text}")
                return False
        
        except Exception as e:
            logging.error(f"Telegram 알림 전송 중 오류 발생: {e}")
            return False
    
    def send_notification(self, message, title=None, severity="info", attachments=None):
        """모든 활성화된 채널로 알림을 전송합니다."""
        if not self.config["enabled"]:
            logging.info("알림 시스템 비활성화됨")
            return False
        
        # 제목 추가
        if title:
            formatted_message = f"*{title}*\n{message}"
        else:
            formatted_message = message
        
        # 심각도에 따른 아이콘 추가
        if severity == "error":
            icon = "🚨"
        elif severity == "warning":
            icon = "⚠️"
        else:
            icon = "ℹ️"
        
        formatted_message = f"{icon} {formatted_message}"
        
        # 각 채널로 알림 전송
        results = []
        
        # Slack 알림
        if self.config["slack"]["enabled"]:
            slack_result = self.send_slack_notification(formatted_message, attachments)
            results.append(slack_result)
        
        # Telegram 알림
        if self.config["telegram"]["enabled"]:
            telegram_result = self.send_telegram_notification(formatted_message)
            results.append(telegram_result)
        
        # 하나 이상의 채널에서 성공했으면 성공으로 간주
        return any(results) if results else False
    
    def notify_subtask_failure(self, task_id, task_name, subtask_id, subtask_name, failure_count, error_message=None):
        """서브태스크 실패 알림을 전송합니다."""
        title = f"서브태스크 실패 알림 ({failure_count}회)"
        message = f"태스크: {task_name} ({task_id})\n"
        message += f"서브태스크: {subtask_name} ({subtask_id})\n"
        message += f"실패 횟수: {failure_count}\n"
        
        if error_message:
            message += f"오류 메시지: ```{error_message}```"
        
        return self.send_notification(message, title, "error")
    
    def notify_test_failure(self, task_id, subtask_id, test_result):
        """테스트 실패 알림을 전송합니다."""
        title = "테스트 실패 알림"
        message = f"태스크: {task_id}\n"
        message += f"서브태스크: {subtask_id}\n"
        
        # 안전한 딕셔너리 접근
        if isinstance(test_result, dict):
            message += f"실패한 테스트: {test_result.get('failed_count', 0)}\n"
            message += f"오류 테스트: {test_result.get('error_count', 0)}\n"
            
            # 실패한 테스트 목록 추출 (최대 5개)
            output = test_result.get("output", "")
            if output:
                failure_pattern = r"FAILED\s+([\w\.]+)::\w+\s+"
                failures = re.findall(failure_pattern, output)
                
                if failures:
                    message += "\n실패한 테스트 목록:\n"
                    for i, failure in enumerate(failures[:5]):
                        message += f"{i+1}. {failure}\n"
                    
                    if len(failures) > 5:
                        message += f"외 {len(failures) - 5}개 더..."
        else:
            message += "테스트 결과 정보를 파싱할 수 없습니다."
        
        return self.send_notification(message, title, "error")
    
    def notify_mock_detection(self, analysis_result):
        """모의 처리 감지 알림을 전송합니다."""
        if analysis_result["total_mocks"] == 0 and analysis_result["total_commented_code"] == 0:
            return False
        
        title = "코드 품질 경고"
        message = ""
        
        if analysis_result["total_mocks"] > 0:
            message += f"모의(mock) 처리 발견: {analysis_result['total_mocks']} 개 ({analysis_result['files_with_mocks']} 파일)\n\n"
            
            # 상위 3개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["mocks"]],
                key=lambda x: len(x["mocks"]),
                reverse=True
            )[:3]
            
            for file_result in top_files:
                message += f"- {file_result['file']}: {len(file_result['mocks'])} 개\n"
        
        if analysis_result["total_commented_code"] > 0:
            if message:
                message += "\n"
            
            message += f"주석 처리된 코드 발견: {analysis_result['total_commented_code']} 개 ({analysis_result['files_with_commented_code']} 파일)\n\n"
            
            # 상위 3개 파일 목록
            top_files = sorted(
                [f for f in analysis_result["details"] if f["commented_code"]],
                key=lambda x: len(x["commented_code"]),
                reverse=True
            )[:3]
            
            for file_result in top_files:
                message += f"- {file_result['file']}: {len(file_result['commented_code'])} 개\n"
        
        return self.send_notification(message, title, "warning")
    
    def notify_task_completion(self, task_id, task_name):
        """태스크 완료 알림을 전송합니다."""
        title = "태스크 완료 알림"
        message = f"태스크 '{task_name}' ({task_id})가 성공적으로 완료되었습니다."
        
        return self.send_notification(message, title, "info")


# 테스트 코드
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 알림 관리자 생성
    notification_manager = NotificationManager()
    
    # 테스트 알림 전송
    notification_manager.send_notification(
        "이것은 테스트 알림입니다.",
        "테스트 알림",
        "info"
    )
