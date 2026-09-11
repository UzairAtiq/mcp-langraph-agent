# Test cases for evaluating the MCP + LangGraph agent
# Each case defines: input prompt, expected tools (in order), and expected behavior notes

TEST_CASES = [
    {
        "id": "test_1_full_flow",
        "prompt": "Look up customer 3 and post their status to Slack",
        "expected_tools": ["lookup_customer", "send_slack_message"],
        "expected_behavior": "Should call lookup_customer first to get customer data, then call send_slack_message with the customer's status included in the message."
    },
    {
        "id": "test_2_lookup_only",
        "prompt": "What is customer 5's email address?",
        "expected_tools": ["lookup_customer"],
        "expected_behavior": "Should call lookup_customer only. Should NOT call send_slack_message since the user didn't ask to post anywhere."
    },
    {
        "id": "test_3_slack_only",
        "prompt": "Send a message to Slack saying 'Deployment completed successfully'",
        "expected_tools": ["send_slack_message"],
        "expected_behavior": "Should call send_slack_message directly with the given message. Should NOT call lookup_customer since no customer lookup was requested."
    },
]