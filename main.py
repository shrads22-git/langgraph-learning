from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

load_dotenv()


@tool
def calculator(operation: str, a: float, b: float) -> float:
    """Perform a basic arithmetic operation.

    Args:
        operation: One of add, subtract, multiply, or divide.
        a: First number.
        b: Second number.
    """
    if operation == "add":
        return a + b

    if operation == "subtract":
        return a - b

    if operation == "multiply":
        return a * b

    if operation == "divide":
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b

    raise ValueError(
        "Unsupported operation. Use add, subtract, multiply, or divide."
    )


agent = create_agent(
    model="openai:gpt-4.1-mini",
    tools=[calculator],
    system_prompt=(
        "You are a careful math assistant. "
        "For arithmetic questions, always use the calculator tool. "
        "Do not calculate the answer mentally."
    ),
)


def main() -> None:
    question = "What is 17 + 9 × 6?"

    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": question,
                }
            ]
        },
        config={
            "run_name": "calculator-agent-test",
            "tags": ["trajectory-evaluation", "calculator", "v1"],
            "metadata": {
                "exercise": "Product School trajectory scoring",
            },
        },
    )

    final_message = result["messages"][-1]
    for i, msg in enumerate(result["messages"]):
        print(f"\nMessage {i}: {type(msg).__name__}")
        print(msg)

    print(final_message.content)


if __name__ == "__main__":
    main()
