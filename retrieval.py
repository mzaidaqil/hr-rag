import os

from dotenv import load_dotenv

from hr_assistant.config import load_settings
from hr_assistant.rag import RagService


def main():
    load_dotenv()
    settings = load_settings()
    rag = RagService(settings)

    question = "What is the PTO carryover policy?"
    ans = rag.answer_policy_question(question=question, user_context={"region": "US"})

    print("ANSWER:")
    print(ans.answer)
    print("\nCITATIONS:")
    for c in ans.citations:
        print(f"- {c.title} ({c.effective_date}) [{c.source_path}]")


if __name__ == "__main__":
    main()