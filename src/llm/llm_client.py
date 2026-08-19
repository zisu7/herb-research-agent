import os
from pathlib import Path
from dotenv import load_dotenv
import requests

# 固定加载项目根目录下的 .env
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path)

API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()
BASE_URL = "https://api.deepseek.com/v1"
MODEL = "deepseek-chat"

_token_stats = {
    "total_prompt_tokens": 0,
    "total_completion_tokens": 0,
    "total_calls": 0,
}


def is_llm_available():
    if not API_KEY:
        return False
    return True


def get_token_stats():
    return dict(_token_stats)


def reset_token_stats():
    _token_stats["total_prompt_tokens"] = 0
    _token_stats["total_completion_tokens"] = 0
    _token_stats["total_calls"] = 0


def chat_completion(system_prompt, user_content, max_retries=2):
    if not is_llm_available():
        raise RuntimeError(
            "DEEPSEEK_API_KEY 未配置，LLM不可用。请在 .env 文件中设置有效的 API Key。"
        )

    if not system_prompt or not isinstance(system_prompt, str):
        raise ValueError("system_prompt 不能为空且必须是字符串")
    if not user_content or not isinstance(user_content, str):
        raise ValueError("user_content 不能为空且必须是字符串")

    url = f"{BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)

            _token_stats["total_prompt_tokens"] += prompt_tokens
            _token_stats["total_completion_tokens"] += completion_tokens
            _token_stats["total_calls"] += 1

            choices = data.get("choices", [])
            if not choices:
                raise RuntimeError("API返回为空，未获取到模型输出")

            return choices[0]["message"]["content"].strip()

        except requests.exceptions.Timeout as e:
            last_error = f"请求超时(第{attempt + 1}次): {e}"
        except requests.exceptions.ConnectionError as e:
            last_error = f"网络连接失败(第{attempt + 1}次): {e}"
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else "unknown"
            error_detail = ""
            try:
                error_body = e.response.json() if e.response is not None else {}
                error_detail = error_body.get("error", {}).get("message", "")
            except Exception:
                pass

            if status_code == 401:
                raise RuntimeError(f"API Key 无效或已过期(HTTP 401): {error_detail}")
            elif status_code == 429:
                last_error = f"请求频率超限(HTTP 429，第{attempt + 1}次): {error_detail}"
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(last_error)
            elif status_code == 400 and "max_tokens" in str(error_detail).lower():
                raise RuntimeError(f"Token 超限(HTTP 400): {error_detail}")
            elif status_code == 400:
                raise RuntimeError(f"请求参数错误(HTTP 400): {error_detail}")
            elif status_code >= 500:
                last_error = f"服务端错误(HTTP {status_code}，第{attempt + 1}次): {error_detail}"
                if attempt < max_retries:
                    import time
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(last_error)
            else:
                raise RuntimeError(f"HTTP请求失败(HTTP {status_code}): {error_detail}")

        except requests.exceptions.RequestException as e:
            last_error = f"网络请求异常(第{attempt + 1}次): {e}"
        except RuntimeError:
            raise
        except Exception as e:
            last_error = f"未知错误(第{attempt + 1}次): {e}"

        if attempt < max_retries and "429" not in str(last_error) and "500" not in str(last_error):
            break

    raise RuntimeError(f"LLM调用失败，已重试{max_retries}次。最后错误: {last_error}")


def health_check():
    if not is_llm_available():
        return {"status": "unavailable", "reason": "DEEPSEEK_API_KEY 未配置"}

    try:
        result = chat_completion(
            system_prompt="你是一个健康检查助手。",
            user_content="请回复：OK",
        )
        return {"status": "ok", "response": result}
    except Exception as e:
        return {"status": "error", "reason": str(e)}