import os
import random
import datetime
from voice_service import text_to_speech
from models import db, ChatbotResponse, UserQuery, KnowledgeBase
from web_search import search_web
from query_classifier import is_web_search_query

# Chatbot name and configuration
CHATBOT_NAME = "Smart Sight Assistant"
USE_WEB_SEARCH = True  # Enable or disable web search functionality
USE_PERPLEXITY = False  # Perplexity API has been disabled

# Cache for storing previous conversations to maintain context
conversation_cache = {}

def get_chatbot_response(user_query, session_id="default", use_memory=True):
    """
    Get a response from the AI chatbot based on the user's query.
    
    Args:
        user_query (str): The user's question or request
        session_id (str): Unique identifier for the conversation session
        use_memory (bool): Whether to use previous conversation history
        
    Returns:
        str: The chatbot's response
    """
    try:
        # Initialize conversation history if this is a new session
        if session_id not in conversation_cache:
            conversation_cache[session_id] = []
        
        # Initial welcome message that's triggered by a special key
        if user_query == "__welcome_message__":
            return f"Hello, I'm {CHATBOT_NAME}, your Smart Sight assistant. How can I help you today?"
        
        # Get response from our enhanced local response generator
        response = generate_simple_response(user_query)
        
        # Store the conversation for context if using memory
        if use_memory:
            # Store user message
            conversation_cache[session_id].append({
                "role": "user",
                "content": user_query
            })
            
            # Store assistant response
            conversation_cache[session_id].append({
                "role": "assistant",
                "content": response
            })
            
            # Limit conversation history to last 20 messages to prevent memory issues
            if len(conversation_cache[session_id]) > 20:
                conversation_cache[session_id] = conversation_cache[session_id][-20:]
        
        return response
        
    except Exception as e:
        print(f"Error in chatbot response generation: {str(e)}")
        return f"I'm sorry, I encountered an error processing your request. Please try asking in a different way."

def generate_simple_response(query):
    """
    Generate a simple response when no API key is available.
    This is an enhanced local chatbot that provides responses to common queries.
    
    Args:
        query (str): The user's question
        
    Returns:
        str: A contextually appropriate response based on pattern matching
    """
    import datetime
    
    query = query.lower().strip()
    
    # First, check if we have a matching response in the knowledge base or db
    try:
        # 1. First, check the knowledge base with exact word match
        knowledge_item_exact = KnowledgeBase.query.filter(
            KnowledgeBase.question.ilike(f"%{query}%"),
            KnowledgeBase.active == True
        ).first()
        
        if knowledge_item_exact:
            print(f"Found exact matching knowledge base item for query: {query}")
            return knowledge_item_exact.answer
        
        # 2. Then look for partial word matches in the knowledge base
        query_words = query.split()
        if len(query_words) > 1:
            for word in query_words:
                if len(word) > 3:  # Only use significant words (longer than 3 chars)
                    knowledge_item_partial = KnowledgeBase.query.filter(
                        KnowledgeBase.question.ilike(f"%{word}%"),
                        KnowledgeBase.active == True
                    ).first()
                    
                    if knowledge_item_partial:
                        print(f"Found partial matching knowledge base item for word '{word}' in query: {query}")
                        return knowledge_item_partial.answer
        
        # 3. Fall back to predefined chatbot responses
        db_response = ChatbotResponse.query.filter(
            ChatbotResponse.pattern.ilike(f"%{query}%"), 
            ChatbotResponse.active == True
        ).first()
        
        if db_response:
            return db_response.response
            
    except Exception as e:
        print(f"Error querying database for response: {str(e)}")
        # Continue with fallback responses if database query fails
    
    # Initial welcome message that's triggered by a special key
    if query == "__welcome_message__":
        return f"Hello, I'm {CHATBOT_NAME}, your Smart Sight assistant. How can I help you today?"
    
    # Time-related questions
    if any(word in query for word in ["time", "what time", "hour", "clock"]):
        now = datetime.datetime.now()
        return f"The current time is {now.strftime('%I:%M %p')}."
    
    # Date-related questions
    elif any(word in query for word in ["date", "day", "today", "month", "year"]):
        now = datetime.datetime.now()
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    
    # Weather-related questions
    elif any(word in query for word in ["weather", "temperature", "forecast", "rain", "snow"]):
        return f"I don't have access to real-time weather data, but I can help you access a weather service through your device's browser if needed."
    
    # Greeting patterns
    elif any(word in query for word in ["hello", "hi ", "hey", "greetings", "good morning", "good afternoon", "good evening"]):
        now = datetime.datetime.now()
        hour = now.hour
        
        if hour < 12:
            greeting = "Good morning"
        elif hour < 18:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
            
        greetings = [
            f"{greeting}! This is {CHATBOT_NAME}. How can I assist you today?",
            f"Hi there! {CHATBOT_NAME} here. What can I help you with?",
            f"Greetings! This is {CHATBOT_NAME}. How may I assist you with Smart Sight today?"
        ]
        return random.choice(greetings)
    
    # Camera and vision-related commands
    elif any(word in query for word in ["identify", "recognize", "what is this", "what do you see", "what's in front of me"]):
        return f"To identify objects around you, I'll need to use your camera. Would you like me to take a picture now and describe what I see?"
    
    # Navigation-related commands
    elif any(word in query for word in ["navigate", "direction", "guide me", "where am i", "help me walk"]):
        return f"I can help guide you based on what I see through your camera. Would you like me to analyze your surroundings and provide navigation guidance?"
    
    # Text reading commands
    elif any(phrase in query for phrase in ["read text", "read this", "what does it say", "scan text"]):
        return f"I can read text from images. Would you like me to take a picture now and read any text I can find?"
    
    # About the chatbot name
    elif any(phrase in query for phrase in ["your name", "who are you", "what's your name", "what are you called"]):
        return f"I'm the {CHATBOT_NAME}. I'm designed to help you navigate and understand your surroundings using voice commands and image recognition."
    
    # Help with app commands
    elif any(phrase in query for phrase in ["how to use", "help me", "instructions", "tutorial", "what can you do", "how does this work"]):
        return f"I'm {CHATBOT_NAME}, your Smart Sight assistant. I can help you in several ways:\n1. Say 'identify objects' to recognize what's around you\n2. Say 'navigate' for guidance in your surroundings\n3. Say 'read text' to extract and read text from images\n4. You can also just ask me questions naturally. How can I help you today?"
    
    # Questions about the app
    elif "what is smart sight" in query or "about this app" in query or "tell me about this app" in query:
        return f"Smart Sight is a voice-controlled navigation app with the tagline 'Eyes that Listen. Hands that Guide.' I'm {CHATBOT_NAME}, your assistant in this app. Smart Sight is designed specifically for blind and visually impaired users, using advanced technology to identify objects, navigate surroundings, and read text, all through a voice-first interface."
    
    # Emergency help
    elif any(word in query for word in ["emergency", "help me", "danger", "unsafe", "911", "police", "ambulance"]):
        return f"If you're in an emergency situation, please say 'Call emergency services' or try to reach out to someone nearby for immediate assistance. Your safety is the priority."
    
    # Location-specific help
    elif any(phrase in query for phrase in ["where am i", "my location", "lost", "find my way"]):
        return f"To help you determine your location, I can describe what I see around you through the camera. Would you like me to do that now?"
    
    # Specific location guidance
    elif "take me to" in query or "how do i get to" in query or "directions to" in query:
        destination = query.split("to")[-1].strip()
        return f"To help guide you to {destination}, I'll need to analyze your surroundings using the camera. Would you like me to start navigation guidance?"
    
    # Mental health support
    elif any(word in query for word in ["lonely", "sad", "depressed", "anxious", "scared", "worried"]):
        return f"I understand that navigating the world can sometimes be challenging and overwhelming. Remember that you're not alone. Would you like me to connect you with support resources or would you prefer some encouraging words?"
    
    # Thank you responses
    elif any(phrase in query for phrase in ["thank", "thanks", "appreciate", "grateful"]):
        gratitude_responses = [
            f"You're welcome! I'm here to help make your day a little easier.",
            f"It's my pleasure to assist you. What else can I help with?",
            f"I'm glad I could help! Is there anything else you need assistance with?"
        ]
        return random.choice(gratitude_responses)
    
    # Goodbye responses
    elif any(phrase in query for phrase in ["bye", "goodbye", "see you", "that's all", "exit", "quit", "stop"]):
        farewell_responses = [
            f"Goodbye! I'm here whenever you need assistance. Just open the app and speak.",
            f"Take care! Remember that {CHATBOT_NAME} is always ready to help when you need me.",
            f"Until next time! Feel free to call on me whenever you need help navigating your world."
        ]
        return random.choice(farewell_responses)
    
    # Jokes or entertainment
    elif "tell me a joke" in query or "make me laugh" in query or "say something funny" in query:
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "What do you call a fake noodle? An impasta!",
            "How do you organize a space party? You planet!",
            "Why did the blind man fall into the well? Because he couldn't see that well.",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus."
        ]
        return random.choice(jokes)
    
    # Feedback about the app
    elif any(phrase in query for phrase in ["feedback", "suggestion", "improve", "problem with app"]):
        return f"Thank you for wanting to provide feedback. Your input helps make Smart Sight better for all users. What specific suggestion or feedback do you have about the app?"
    
    # Personal questions
    elif any(phrase in query for phrase in ["how are you", "how do you feel", "are you real", "are you human"]):
        personal_responses = [
            f"I'm {CHATBOT_NAME}, an AI assistant designed to help you navigate your surroundings. I'm functioning well and ready to assist you!",
            f"I'm not human, but I am here specifically to help you interact with your world more easily. How can I help you today?",
            f"I'm doing well, thank you for asking! My purpose is to be your helpful companion in navigating the world around you."
        ]
        return random.choice(personal_responses)
    
    # Battery or device status
    elif any(phrase in query for phrase in ["battery", "charge", "power", "device status"]):
        return f"I don't have direct access to your device's battery information. If you're concerned about battery life, I recommend keeping your device charged regularly since using the camera can use significant power."
    
    # Volume adjustment
    elif any(phrase in query for phrase in ["volume up", "louder", "volume down", "quieter", "mute"]):
        if "up" in query or "louder" in query:
            return f"I've noted your request to increase the volume. Please use your device's volume buttons to adjust to a comfortable level."
        elif "down" in query or "quieter" in query or "mute" in query:
            return f"I've noted your request to decrease the volume. Please use your device's volume buttons to adjust to a comfortable level."
        else:
            return f"To adjust the volume, please use your device's volume buttons."
    
    # Perplexity API has been completely removed
    # Moving directly to web search functionality
    
    # Check if we should handle this with web search
    if USE_WEB_SEARCH and is_web_search_query(query):
        print(f"Performing web search for: {query}")
        web_response = search_web(query)
        if web_response:
            return web_response
        else:
            return f"I tried searching the web for information about '{query}', but couldn't find a good answer. Is there something else you'd like to know, or would you like me to help with navigation, object identification, or text reading?"
    
    # General knowledge fallback
    elif any(word in query for word in ["what is", "who is", "where is", "when", "why", "how does"]):
        if USE_WEB_SEARCH:
            print(f"Performing web search for knowledge question: {query}")
            web_response = search_web(query)
            if web_response:
                return web_response
        
        return f"That's an interesting question about '{query}'. While I don't have access to a knowledge database right now, I can focus on helping you navigate your surroundings, identify objects, or read text. Would you like help with any of those?"
    
    # Default helpful response for queries we can't specifically handle
    else:
        # Extract the first few words to acknowledge the query
        query_preview = ' '.join(query.split()[:3]) + "..."
        
        # Try web search for unhandled queries if enabled
        if USE_WEB_SEARCH:
            print(f"Trying web search for unhandled query: {query}")
            web_response = search_web(query)
            if web_response:
                return web_response
        
        responses = [
            f"I heard you asking about '{query_preview}'. I can help you navigate your surroundings, identify objects, or read text. What would you like me to do?",
            f"I understand you're interested in '{query_preview}'. As your navigation assistant, I can best help with identifying objects, providing directions, or reading text. Would you like me to do any of those?",
            f"Thanks for your question about '{query_preview}'. I'm here to assist with navigating your environment. Would you like me to take a picture and describe what I see?"
        ]
        
        return random.choice(responses)