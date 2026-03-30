import base64
from pathlib import Path

from AIwardrobe.model.factory import classify_model
from AIwardrobe.utils.prompt_loader import load_classify_prompts


class ClassificationModel:
    def __init__(self):
        self.agent = classify_model
        self.prompt = load_classify_prompts()

    def execute(self, path: str):
        # Temporary: inline base64 data URL; could switch to signed URLs / SSO later
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        suffix = Path(path).suffix  # ".webp"
        ext = suffix.lower().lstrip(".")  # "webp"
        url = f"data:image/{ext};base64,{b64}"

        completion = self.agent.chat.completions.create(
            model="qwen3-vl-plus-2025-12-19",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": url
                            },
                        },
                        {"type": "text", "text": self.prompt},
                    ],
                },
            ],
        )

        answer_content = completion.choices[0].message.content or ""
        return answer_content

if __name__ == '__main__':
    classify = ClassificationModel()
    print(classify.execute(path="../data/Acne.webp"))
