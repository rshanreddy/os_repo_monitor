import pandas as pd
import os
import anthropic

ANTHROPIC_TOKEN = os.getenv("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=ANTHROPIC_TOKEN)

def generate_trend_analysis(trending_df):
    """Analyzes trends in top repos using Claude"""
    
    prompt = f"""You are a technical VC analyst specializing in open source AI projects. 
    Analyze these top 10 trending AI repositories from the past week:
    
    {trending_df.to_string()}
    
    Write a concise (3-4 sentences) analysis of:
    1. Key trends or patterns in what's gaining traction
    2. Notable technical innovations or approaches
    3. Potential commercial implications
    
    Focus on concrete technical details and growth metrics. Avoid subjective language."""
    
    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content
    except Exception as e:
        print(f"Error generating analysis: {e}")
        return None

def test_trend_analysis():
    # More realistic test data
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
    
    print("Input Data for Analysis:")
    print(test_data)
    print("\nGenerating Analysis...")
    
    analysis = generate_trend_analysis(test_data)
    print("\nAI Analysis:")
    print(analysis)

if __name__ == "__main__":
    test_trend_analysis()