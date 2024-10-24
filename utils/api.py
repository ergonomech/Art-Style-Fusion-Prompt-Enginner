import requests
import logging

class API:
    def __init__(self, key=None, url=None, model=None, token_limit=2048, temp=0.7, top_p=0.9):
        self.key = key
        self.url = url
        self.model = model
        self.token_limit = token_limit
        self.temp = temp
        self.top_p = top_p

    def req(self, prompt, img_data=None):
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"}
        content = [{"type": "text", "text": prompt}]
        if img_data:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}", "detail": "high"}})
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "max_tokens": self.token_limit,
            "temperature": self.temp,
            "top_p": self.top_p
        }
        try:
            res = requests.post(self.url, headers=headers, json=payload)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"].strip()
        except requests.RequestException as e:
            logging.error(f"API error: {str(e)}")
            return f"Error: {str(e)}"
