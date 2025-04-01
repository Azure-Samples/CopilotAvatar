import re
import requests

class DirectLineClient:
    def __init__(self):
        self._watermark = None
        self._app_settings = {
            "BotId": None,
            "BotTokenEndpoint": "https://3da91219fae9e6bf878a89078d0db4.1c.environment.api.powerplatform.com/powervirtualagents/botsbyschema/cra66_dianne/directline/token?api-version=2022-03-01-preview",
            "BotName": "Dianne"
        }
        # self._end_conversation_message = self._bot_env_prefix + os.getenv("END_CONVERSATION_MESSAGE", "quit")
        self._user_display_name = "You"
        self._base_url = "https://directline.botframework.com/v3/directline"
        self._token = self.__get_token()

    def __get_token(self):
        try:
            response = requests.get(self._app_settings["BotTokenEndpoint"])
            response.raise_for_status()
            return response.json()["token"]
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            raise
        except Exception as err:
            print(f"Other error occurred: {err}")
            raise

    def start_conversation(self):
        response = requests.post(
            f"{self._base_url}/conversations",
            headers={"Authorization": f"Bearer {self._token}"}
        )
        response.raise_for_status()
        return response.json()["conversationId"]

    def send_message(self, conversation_id, message):   
        response = requests.post(
            f"{self._base_url}/conversations/{conversation_id}/activities",
            headers={
                "Authorization": f"Bearer {self._token}",
                "Accept": "application/json;charset=UTF-8",
            },
            json={
                "type": "message",
                "from": {"id": "userId", "name": "userName"},
                "text": message,
                "textFormat": "plain",
                "locale": "en-US"
            }
        )
        response.raise_for_status()
        return response.json()

    def get_bot_responses(self, conversation_id):
        response = requests.get(
            f"{self._base_url}/conversations/{conversation_id}/activities",
            headers={"Authorization": f"Bearer {self._token}"},
            params={"watermark": self._watermark}
        )
        response.raise_for_status()
        activities = response.json()
        self._watermark = activities.get("watermark")
        return activities.get("activities", [])


    def get_bot_message(self, responses):
        response_str = ""
        for activity in responses:
            if not self._app_settings["BotId"] and activity["from"].get("role") == "bot":
                self._app_settings["BotId"] = activity["from"]["id"]
            
            if activity["type"] == "message" and activity["from"]["id"] == self._app_settings["BotId"]:
                response_str += f"{activity['text']}" + "\n"

        cleaned_text = re.sub(r'\[\d+\]?', '', response_str)
        cleaned_text = re.sub(r'\[\d+\]: cite:\d+ "Citation-\d+"', '', cleaned_text)
        cleaned_text = re.sub(r': cite:\d+ "Citation-\d+"', '', cleaned_text)
        cleaned_text = re.sub(r'\u200b', '', cleaned_text)
        cleaned_text = cleaned_text.strip()
        return cleaned_text