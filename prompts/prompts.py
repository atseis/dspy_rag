
INTENT_RECOG="""
    The following conversation has taken place:
    {conversation_history}
    
    The user has just input: "{user_input}"
    
    Based on the above conversation, determine if the input is a:
    1. New query
    2. Feedback on the previous conversation
    
    Please respond with either "new query" or "feedback".
    """