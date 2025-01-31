import pandas as pd
import os
import anthropic

def test_data_creation():
    # Create test data
    test_data = pd.DataFrame({
        'repo_full_name': [
            'deepseek-ai/DeepSeek-Coder',
            'microsoft/phi-2',
            'mistralai/mistral-7b',
            'anthropic/claude-3',
            'ollama/ollama'
        ],
        'current_stars': [11500, 8300, 15200, 7800, 11000],
        'description': [
            "Open-source code generation model trained on 2T tokens",
            "Small language model optimized for code and reasoning",
            "Open source 7B parameter LLM with strong performance",
            "Research on constitutional AI and model alignment",
            "Run Llama 2, Mistral, and other LLMs locally"
        ],
        'daily_gain': [500, 300, 200, 400, 250],
        'daily_pct': [4.5, 3.8, 1.3, 5.4, 2.3],
        'weekly_gain': [2500, 1800, 1200, 2200, 1500],
        'weekly_pct': [27.8, 27.7, 8.6, 39.3, 15.8]
    })
    
    print("Created test DataFrame:")
    print(test_data)
    return test_data

def generate_trend_analysis(df):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    prompt = f"""You're a technical VC partner analyzing trending AI repos. For this weekly report, analyze:

{df.to_string()}

Provide 3 bullet points:
- GROWTH: Top 2 repos by weekly % gain and their focus
- SIGNAL: What specific market demand this reveals
- ACTION: One concrete vertical to investigate

Be extremely specific with numbers and technical details."""

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        analysis = response.content[0].text.strip()
        
        return f"""📊 WEEKLY AI REPO TRENDS ANALYSIS
{'-' * 40}

{analysis}"""
    except Exception as e:
        print(f"Error in analysis: {e}")
        return None

if __name__ == "__main__":
    print("Starting test...")
    df = test_data_creation()
    print("\nGenerating analysis...")
    analysis = generate_trend_analysis(df)
    print("\nAI Analysis:")
    print(analysis)