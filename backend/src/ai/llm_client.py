"""
llm_client.py

AI 파이프라인 전체에서 공통으로 사용할 ChapOpenAI LLM 객체를 생성하는 모듈입니다.

이번 프로젝트의 AI 파이프라인은 여러 모델을 각각 따로 생성하지 않고,
하나의 공통 LLM 객체를 생성한 뒤 각 하위 Chain에서 서로 다른 prompt를 적용하는 구조입니다.

사용 예시:
    from src.ai.llm_client import get_llm

    llm = get_llm()

주의:
- 이 파일은 LLM 객체 생성만 담당합니다.
- Financial Context Builder, News Query Generator, Evidence Filter, Report Writer 등은
  이 LLM 객체를 주입받아 각자 다른 system prompt로 동작합니다.
- OPENAI_API_KEY는 .env 파일 또는 환경 변수에 설정되어 있어야 합니다.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


# .env 파일 로드
load_dotenv()


DEFAULT_MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))


@lru_cache(maxsize=1)

def get_llm() -> ChatOpenAI:
    """
    프로젝트 전체에서 공유할 공통 ChatOpenAI 객체를 생성합니다.

    lru_cache를 사용하여 get_llm()을 여러 번 호출해도
    동일한 LLM 객체를 재사용하도록 합니다.

    Returns:
        ChatOpenAI: 공통 LLM 객체

    Raises:
        ValueError: OPENAI_API_KEY가 설정되어 있지 않은 경우
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY가 설정되어 있지 않습니다."
            ".env 파일 또는 환경 변수에 OPENAI_API_KEY를 추가해주세요."
        )

    return ChatOpenAI(
        model=DEFAULT_MODEL_NAME,
        temperature=DEFAULT_TEMPERATURE,
        api_key=api_key,
    )


if __name__ == "__main__":
    llm = get_llm()

    print("[LLM Client Test]")
    print("model:", DEFAULT_MODEL_NAME)
    print("temperature:", DEFAULT_TEMPERATURE)
    print("llm object:", llm)

    response = llm.invoke("간단히 'LLM 연결 성공'이라고만 답해줘.")
    print("response:", response.content)
    