import requests

from dsp import LM


class DeepSeek(LM):
    def __init__(self, model, api_key, **kwargs,):
        self.model = model
        self.api_key = api_key
        self.provider = "default"
        self.history = []
        self.kwargs = {
            "temperature": kwargs.get("temperature", 0.0),
            "max_tokens": min(kwargs.get("max_tokens", 4096), 4096),
            "top_p": kwargs.get("top_p", 0.95),
            "top_k": kwargs.get("top_k", 1),
            "n": kwargs.pop("n", kwargs.pop("num_generations", 1)),
            **kwargs,
        }
        self.kwargs["model"] = model
        self.base_url = "https://api.deepseek.com/chat/completions"

    def basic_request(self, prompt: str, **kwargs):
        headers = {
            "Authorization": "Bearer " + self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        data = {
            **kwargs,
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "steam": False
        }

        response = requests.post(self.base_url, headers=headers, json=data)
        response = response.json()

        self.history.append({
            "prompt": prompt,
            "response": response,
            "kwargs": kwargs,
        })
        return response

    def __call__(self, prompt, **kwargs):
        response = self.request(prompt, **kwargs)
        completions = [result['message']['content'] for result in response["choices"]]
        return completions