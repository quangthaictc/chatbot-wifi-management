import logging
from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from config.settings import GEMINI_API_KEY
from services.gemini_func import tools_list


class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.5-flash"

        self.system_instruction = """
Role: You are QuackWF Bot, an AI assistant designed for network administrators. Your primary mission is to assist in managing internal Wi-Fi networks within a Software-Defined Networking (SDN)
architecture.
Task: You will receive messages from the network administrator. Your goal is to interpret the admin's intent and utilize the available system tools to gather the necessary network data.
Response Style: Telegram MARKDOWN style. Once the data is retrieved, provide a response that is concise, accurate, and strictly focused on the provided information. Avoid unnecessary filler 
and get straight to the point.
        """

        self.config = types.GenerateContentConfig(
            system_instruction=self.system_instruction,
            tools=tools_list,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(
                disable=False
            ),
            temperature=0.5,
        )

        self.chat_session = self.client.aio.chats.create(
            model=self.model, config=self.config
        )

    async def received_message(self, message: str):
        try:
            response = await self.chat_session.send_message(message)
            return response.text

        except ClientError as e:
            if e.code == 429:
                return "You've reached the daily limit of 20 requests. See you again after 3:00 PM"
        except ServerError:
            return "Google's servers are a bit busy right now. Mind trying again in a few seconds?"
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"""\n\n========== Exception from function 'received_message() line 27' ==========
            {e}
            """)
            return "Something went wrong. Please try again later."
