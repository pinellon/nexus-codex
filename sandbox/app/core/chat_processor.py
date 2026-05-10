import openai

class ChatProcessor:
    def __init__(self, api_key, logger):
        self.api_key = api_key
        self.logger = logger
        openai.api_key = self.api_key

    def process_input(self, text):
        try:
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=text,
                max_tokens=150
            )
            return response.choices[0].text.strip()
        except Exception as e:
            self.logger.error(f"ChatProcessor error: {str(e)}")
            return None
