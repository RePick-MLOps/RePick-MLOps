import json
from pathlib import Path


def check_processed_states():
    processed_states_path = Path("./data/vectordb/processed_states.json")

    if not processed_states_path.exists():
        print("Error: processed_states.json not found!")
        return False

    with open(processed_states_path, "r", encoding="utf-8") as f:
        states = json.load(f)

    has_errors = False
    for pdf_file, state in states.items():
        print(f"\nChecking {pdf_file}:")
        print(f"- Text summaries: {len(state['text_summary'])}")
        print(f"- Image summaries: {len(state['image_summary'])}")
        print(f"- Table summaries: {len(state['table_summary'])}")

        if not any(
            [state["text_summary"], state["image_summary"], state["table_summary"]]
        ):
            print(f"Warning: No summaries found for {pdf_file}")
            has_errors = True

    return not has_errors


if __name__ == "__main__":
    success = check_processed_states()
    if not success:
        print(
            "\nError: Some files have no summaries. Please check the PDF processing pipeline."
        )
