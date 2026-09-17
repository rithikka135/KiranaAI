from app.documents.analysis_deck_generator import (
    generate_analysis_deck,
)


def generate_weekly_analysis_deck_tool() -> dict:

    try:

        file_path = generate_analysis_deck()

        return {
            "success": True,
            "message": "Weekly sales analysis deck generated successfully.",
            "file_path": file_path,
        }

    except Exception as e:

        return {
            "success": False,
            "message": f"Unable to generate analysis deck: {str(e)}",
        }