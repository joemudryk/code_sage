import openai
import traceback
import logging
from utils import get_setting, hash_string

logger = logging.getLogger(__name__)

OPEN_AI_API_KEY = get_setting(name="OPEN_AI_API_KEY")
CODE_SAGE_ENABLED = get_setting(name="OPEN_AI_API_KEY") or False
RESPONSE_WORD_LIMIT = get_setting(name="RESPONSE_WORD_LIMIT") or 120


if OPEN_AI_API_KEY:
    openai.api_key = OPEN_AI_API_KEY
else:
    logger.error(
        "CHAT_GPT_API_KEY has not been set in django settings or as an environment variable"
    )


# Questions sent to OpenAI and the answers given will be stored in this dictionary for caching
# They will be in the format:  {"{hashed_question}": "{answer_from_open_ai}", ..., ...}
CACHED_ERROR_SOLUTIONS = {}


def get_gpt_error_solution_suggestion(error: Exception) -> str:
    error_text = repr(error)
    prompt = (
        f"In {RESPONSE_WORD_LIMIT} words or less, tell me how I can fix the following python exception error: "
        f"\n {error_text}"
        f"\n"
        f"The traceback for the error is the following:"
        f"{traceback.format_exc()}"
    )
    hashed_prompt = hash_string(prompt)

    if hashed_prompt in CACHED_ERROR_SOLUTIONS:
        return CACHED_ERROR_SOLUTIONS[hashed_prompt]

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        temperature=0,
        max_tokens=182,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    solution_suggestion = str(response["choices"][0]["text"]).replace("\n", "")

    CACHED_ERROR_SOLUTIONS[hashed_prompt] = solution_suggestion
    return solution_suggestion


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        # If the chat gpt api key is set, inject a solution suggestion into the logs
        if OPEN_AI_API_KEY and CODE_SAGE_ENABLED:
            logger.exception(
                f"An unexpected error occurred. {exception}",
                extra={
                    "error": repr(exception),
                    "suggestion": get_gpt_error_solution_suggestion(error=exception),
                    "traceback": traceback.format_exc(),
                },
            )
