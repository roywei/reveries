import openai
from .load_env import load_dotenv

load_dotenv()


def get_client(provider):
    if provider == "OpenAI":
        return openai.Client()
