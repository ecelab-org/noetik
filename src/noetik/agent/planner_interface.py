# A facade around the LLM: plan(state) -> PlannerResponse that returns a list of tool calls or a final answer.
# Abstracts away whether you’re using OpenAI, Anthropic, or HF/TGI.
