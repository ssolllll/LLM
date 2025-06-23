import re
import requests
import logging
import time
from typing import Dict, Union
import urllib.parse

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
from youtube_transcript_api.errors import NoTranscriptFound, TranscriptsDisabled, VideoUnavailable

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

def extract_video_id(youtube_url:str) -> str:
    """
    YouTube URL에서 video_id 추출
    """
    patterns = [
        r"(?:v=|\/)([0-9A-Za-z_-]{11}).*",
        r"youtu\.be/([0-9A-Za-z_-]{11})",
        r"embed/([0-9A-Za-z_-]{11})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError("올바르지 않은 YouTube URL입니다.")

def get_transcript(video_id: str) -> Union[str, Dict[str, str]]:
    """
    YouTube 영상의 자막을 가져옵니다 (한국어 우선, 영어 fallback)
    """
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:
            transcript = transcript_list.find_transcript(['ko', 'ko-KR'])
            logger.info("한국어 자막을 찾았습니다.")
        except NoTranscriptFound:
            try:
                transcript = transcript_list.find_transcript(['en', 'en-US','en-GB'])
                logger.info("영어 자막을 사용합니다.")
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(['ko','ko-KR'])
                    logger.info("자동 생성된 한국어 자막을 사용합니다.")
                except NoTranscriptFound:
                    transcript = transcript_list.find_generated_transcript(['en','en-US'])
                    logger.info("자동 생성된 영어 자막을 사용합니다.")
        
        transcript_data = transcript.fetch()

        try:
            if isinstance(transcript_data, list) and len(transcript_data) > 0:
                if isinstance(transcript_data[0], dict):
                    full_text = " ".join([entry.get('text', '') for entry in transcript_data])
                else:
                    formatter = TextFormatter()
                    full_text = formatter.format_transcript(transcript_data)
            else:
                full_text = str(transcript_data)
        except Exception as format_error:
            logger.error(f"자막 포맷팅 오류 : {str(format_error)}")
            full_text = str(transcript_data)

        return full_text.strip()

    except TranscriptsDisabled:
        return {"error" : "이 영상은 자막이 비활성화되어 있습니다."}
    except NoTranscriptFound:
        return {"error" : "이 영상에는 사용 가능한 자막이 없습니다."}
    except Exception as e:
        logger.error(f"자막 추출 중 오류 : {str(e)}")
        return {"error" : f"자막을 가져오는 중 오류 발생 : {str(e)}"}
    
def summarize_text(text: str) -> Union[str, Dict[str, str]]:
    """
    LLM 모델로 텍스트 요약
    """
    try:
        prompt = (
            "다음은 YouTube 영상의 자막입니다. 핵심 내용을 3~5개의 주요 포인트로 요약해주세요. "
            "응답은 무조건 한글로 응답하세요. "
            "각 포인트는 명확하고 구체적으로 작성해주세요.\n\n"
            f"자막 내용 : \n{text}\n\n"
            "요약:"
        )

        payload = {
            "model" : OLLAMA_MODEL,
            "prompt" : prompt,
            "stream" : False,
            "options" : {
                "temperature" : 0.7,
                "top_p" : 0.9,
                "max_tokens" : 1000
            }
        }

        response = requests.post(
            OLLAMA_ENDPOINT,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            logger.error(f"Ollama API 오류 : {response.status_code} - {response.text}")
            return {"error" : f"요약 생성 중 오류 발생 : HTTP {response.status_code}"}
        
        result = response.json()
        summary = result.get("response", "").strip()

        if not summary:
            return {"error" : "요약을 생성할 수 없습니다."}
        
        return summary
    
    except requests.exceptions.Timeout:
        logger.error("Ollama API 타임아웃")
        return {"error" : "요약 생성 시간이 초과되었습니다."}
    except requests.exceptions.ConnectionError:
        logger.error("Ollama API 연결 오류")
        return {"error" : "LLM 서비스에 연결할 수 없습니다. Ollama가 실행 중인지 확인해주세요."}
    except Exception as e:
        logger.error(f"요약 생성 중 오류 : {str(e)}")
        return {"error" : f"요약 생성 중 오류 발생 : {str(e)}"}
    
def process_youtube_summary(youtube_url : str) -> Dict[str, Union[str, Dict]]:
    """
    YouTube URL을 받아서 자막을 추출하고 요약을 생성함.
    """
    try:
        if not youtube_url or not isinstance(youtube_url, str):
            return {"error" : "올바른 YouTube URL을 입력해주세요."}
        
        youtube_url = youtube_url.strip()

        video_id = extract_video_id(youtube_url)
        transcript = get_transcript(video_id)
        if isinstance(transcript, dict) and "error" in transcript:
            return transcript
        
        if len(transcript.strip()) < 50:
            return {"error" : "자막이 너무 짧거나 비어있습니다."}
        
        summary = summarize_text(transcript)
        if isinstance(summary, dict) and "error" in summary:
            return summary
        
        return {
            "video_id" : video_id,
            "transcript_length" : len(transcript),
            "summary" : summary,
            "status" : "success"
        }
    
    except ValueError as e:
        return {"error" : str(e)}
    except Exception as e:
        return {"error" : f"처리 중 오류 발생 : {str(e)}"}
    
def validate_youtube_url(url: str) -> bool:
    try:
        extract_video_id(url)
        return True
    except Exception as e:
        return False
    
def get_video_info(video_id: str) -> Dict[str, str]:

    return {
        "video_id" : video_id,
        "video_url" : f"https://www.youtube.com/watch?v={video_id}",
        "thumbnail_url" : f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    }