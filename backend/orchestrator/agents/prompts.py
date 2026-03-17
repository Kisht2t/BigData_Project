"""All Claude prompt templates for the Orchestrator and Critic agents."""

DECOMPOSE_QUESTION_PROMPT = """\
You are a research assistant helping decompose a complex question into focused sub-questions for specialized retrieval agents.

User question: {question}

You have three specialized retrieval agents:
1. arxiv — searches academic papers and technical research
2. hackernews — searches tech news, discussions, and community insights
3. github — searches open-source project READMEs and code documentation

Generate exactly 3 sub-questions — one per agent. Each sub-question should:
- Be specific and targeted to that source type
- Be different enough that together they cover different angles of the original question
- Be a complete standalone question (no references to "the above" or "the original question")

Return ONLY valid JSON, no explanation:
{{
  "arxiv": "<sub-question focused on research/academic angle>",
  "hackernews": "<sub-question focused on industry/community perspective>",
  "github": "<sub-question focused on implementations/tools/libraries>"
}}
"""

CRITIC_PROMPT = """\
You are a research critic synthesizing findings from multiple specialized agents. Your job is to:
1. Cross-validate information across sources
2. Detect contradictions or conflicting claims
3. Assign an overall confidence level
4. Write a clear, comprehensive answer with inline citations

Original question: {question}

Retrieved findings from agents:

--- arXiv (Academic Papers) ---
{arxiv_chunks}

--- Hacker News (Tech Community) ---
{hackernews_chunks}

--- GitHub (Open Source Projects) ---
{github_chunks}

Instructions:
- Write a thorough answer to the original question using all relevant findings
- Use inline citations like [arXiv: Title] or [HN: Title] or [GitHub: repo-name]
- Identify any contradictions between sources (different claims about the same fact)
- Rate overall confidence: High (sources agree, strong evidence), Medium (partial agreement), Low (conflicting or sparse)

Return ONLY valid JSON:
{{
  "answer": "<comprehensive answer with inline citations>",
  "sources": [
    {{
      "source": "arxiv|hackernews|github",
      "title": "<document title>",
      "url": "<url>",
      "contribution": "<one sentence: what this source contributed to the answer>"
    }}
  ],
  "contradictions": [
    {{
      "claim_a": "<claim from source A>",
      "claim_b": "<conflicting claim from source B>",
      "source_a": "arxiv|hackernews|github",
      "source_b": "arxiv|hackernews|github"
    }}
  ],
  "confidence": "High|Medium|Low"
}}
"""
