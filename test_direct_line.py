import asyncio
from DirectLineClient import DirectLineClient


dl_client = DirectLineClient()
conversation_id = dl_client.start_conversation()
dl_client.send_message(conversation_id, "what are the 4 thing to do reach full potential ?")
got_response_from_bot = False
while not got_response_from_bot:
    responses = dl_client.get_bot_responses(conversation_id)
    if responses:
        bot_response_message = dl_client.get_bot_message(responses)
        if bot_response_message:
            print(bot_response_message)
            got_response_from_bot = True