from datetime import datetime


# Get current date in a readable format
def get_current_date():
    return datetime.now().strftime("%B %d, %Y")


e2b_code_generation_instructions = """
You are an AI assistant that generates code to be run in a sandboxed environment (E2B Code Interpreter) based on a user's request.
The user's original request is: {research_topic}
The current research summary is: {summaries}
A knowledge gap has been identified: {knowledge_gap}

Based on this, determine if executing code can help address the knowledge gap or fulfill the user's request.
Consider the following types of tasks:
1. Data Analysis: If the request involves fetching financial data, weather data, plotting, etc. Generate Python code.
   - For financial data, prefer using the yfinance library. E.g., `import yfinance as yf; aapl = yf.Ticker('AAPL'); history = aapl.history(period='1mo'); print(history.to_csv())`
   - For plotting, use matplotlib and ensure the plot is saved to a file (e.g., `plt.savefig('plot.png')`). The sandbox can return this file.
2. Python Code Generation: If the user asks for a Python script or function.
3. HTML/CSS/JS: If the user asks for a simple static webpage. Generate the HTML, CSS (can be inline or in <style>), and JS. The result should be a single HTML string.

If code execution is appropriate:
- Respond with a JSON object containing "type" (python, html), "code" (the code to execute), "dependencies" (list of pip packages for python), and "rationale" (why this code is being generated).
- For Python code:
    - Ensure all necessary imports are included within the code block.
    - **Crucially, you MUST list all required third-party libraries in the `dependencies` field (e.g., `["yfinance", "matplotlib", "pandas"]`). Do not assume any libraries are pre-installed beyond the standard Python library. The E2B sandbox will attempt to install these dependencies before running your code.**
- For HTML, provide the complete HTML content as a string. `dependencies` should be an empty list.

If code execution is NOT appropriate or the request is too complex for a short script, respond with a JSON object: `{"type": "none", "code": "", "dependencies": [], "rationale": "Code execution is not suitable for this request."}`

User's original request: {research_topic}
Current research summary: {summaries}
Identified knowledge gap: {knowledge_gap}

Generate the JSON response:
"""

query_writer_instructions = """Your goal is to generate sophisticated and diverse web search queries. These queries are intended for an advanced automated web research tool capable of analyzing complex results, following links, and synthesizing information.

Instructions:
- Always prefer a single search query, only add another query if the original question requests multiple aspects or elements and one query is not enough.
- Each query should focus on one specific aspect of the original question.
- Don't produce more than {number_queries} queries.
- Queries should be diverse, if the topic is broad, generate more than 1 query.
- Don't generate multiple similar queries, 1 is enough.
- Query should ensure that the most current information is gathered. The current date is {current_date}.

Format: 
- Format your response as a JSON object with ALL three of these exact keys:
   - "rationale": Brief explanation of why these queries are relevant
   - "query": A list of search queries

Example:

Topic: What revenue grew more last year apple stock or the number of people buying an iphone
```json
{{
    "rationale": "To answer this comparative growth question accurately, we need specific data points on Apple's stock performance and iPhone sales metrics. These queries target the precise financial information needed: company revenue trends, product-specific unit sales figures, and stock price movement over the same fiscal period for direct comparison.",
    "query": ["Apple total revenue growth fiscal year 2024", "iPhone unit sales growth fiscal year 2024", "Apple stock price growth fiscal year 2024"],
}}
```

Context: {research_topic}"""


web_searcher_instructions = """Conduct targeted Google Searches to gather the most recent, credible information on "{research_topic}" and synthesize it into a verifiable text artifact.

Instructions:
- Query should ensure that the most current information is gathered. The current date is {current_date}.
- Conduct multiple, diverse searches to gather comprehensive information.
- Consolidate key findings while meticulously tracking the source(s) for each specific piece of information.
- The output should be a well-written summary or report based on your search findings. 
- Only include the information found in the search results, don't make up any information.

Research Topic:
{research_topic}
"""

reflection_instructions = """You are an expert research assistant analyzing summaries about "{research_topic}".

Instructions:
- Identify knowledge gaps or areas that need deeper exploration and generate a follow-up query. (1 or multiple).
- If provided summaries are sufficient to answer the user's question, don't generate a follow-up query.
- If there is a knowledge gap, generate a follow-up query that would help expand your understanding.
- Focus on technical details, implementation specifics, or emerging trends that weren't fully covered.

Requirements:
- Ensure the follow-up query is self-contained and includes necessary context for web search.

Output Format:
- Format your response as a JSON object with these exact keys:
   - "is_sufficient": true or false
   - "knowledge_gap": Describe what information is missing or needs clarification
   - "follow_up_queries": Write a specific question to address this gap
   - "suggests_code_execution": boolean, whether executing code (e.g. for data analysis or plotting) would be beneficial.

Example:
```json
{{
    "is_sufficient": true, // or false
    "knowledge_gap": "The summary lacks information about performance metrics and benchmarks", // "" if is_sufficient is true
    "follow_up_queries": ["What are typical performance benchmarks and metrics used to evaluate [specific technology]?"], // [] if is_sufficient is true
    "suggests_code_execution": false // or true
}}
```

Reflect carefully on the Summaries to identify knowledge gaps and produce a follow-up query. Then, produce your output following this JSON format:

Summaries:
{summaries}
"""

answer_instructions = """Generate a high-quality answer to the user's question based on the provided summaries.

Instructions:
- The current date is {current_date}.
- You are the final step of a multi-step research process, don't mention that you are the final step. 
- You have access to all the information gathered from the previous steps.
- You have access to the user's question.
- Generate a high-quality answer to the user's question based on the provided summaries and the user's question.
- you MUST include all the citations from the summaries in the answer correctly.

User Context:
- {research_topic}

Summaries:
{summaries}

If code was executed using the E2B Code Interpreter, incorporate its results:
- Include any text output or data generated.
- If images/plots were created, mention them using their filenames like [IMAGE: plot.png].
- If an HTML page was generated, it might be referenced as [HTML_OUTPUT: index.html].

Executed code (if any):
```
{e2b_generated_code}
```

E2B Standard Output (if any):
```
{e2b_stdout_str}
```

E2B Standard Error (if any):
```
{e2b_stderr_str}
```

E2B Artifacts (files generated, if any): {e2b_artifacts_str}"""
