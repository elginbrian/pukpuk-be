import asyncio
from app.application.use_cases import GenerateAIInsightUseCase

async def test_ai_response():
    use_case = GenerateAIInsightUseCase(None, None, None, None)

    try:
        # Test with a simple query
        result, suggestions = await use_case._generate_ai_response(
            'What about inventory?', [], None, 'corn', 'midwest', 'summer', []
        )
        print(f'Success! Response starts with: \"{result[:100]}...\"')
        print(f'Suggestions: {suggestions}')
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(test_ai_response())