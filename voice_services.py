import os
import tempfile
import base64
from gtts import gTTS
import speech_recognition as sr

def text_to_speech(text, lang='en'):
    """
    Convert text to speech and return the audio content.
    
    Args:
        text (str): The text to convert to speech
        lang (str): Language code (default: 'en')
        
    Returns:
        bytes: Audio content
    """
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio:
            temp_path = temp_audio.name
        
        # Generate speech using gTTS
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_path)
        
        # Read the audio file
        with open(temp_path, 'rb') as audio_file:
            audio_content = audio_file.read()
        
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass
        
        return audio_content
    
    except Exception as e:
        raise Exception(f"Failed to convert text to speech: {str(e)}")

def recognize_speech(audio_data):
    """
    Convert speech to text using SpeechRecognition.
    
    Args:
        audio_data (bytes): Audio data in bytes
        
    Returns:
        str: Recognized text
    """
    recognizer = sr.Recognizer()
    
    try:
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
            temp_path = temp_audio.name
            temp_audio.write(audio_data)
        
        # Use the recognizer to convert speech to text
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)
        
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass
        
        return text
    
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Could not request results from speech recognition service"
    except Exception as e:
        return f"Error recognizing speech: {str(e)}"

def get_command_intent(text):
    """
    Process a voice command and determine the intent.
    
    Args:
        text (str): The recognized text from speech
        
    Returns:
        dict: Intent information with command type and parameters
    """
    if not text:
        return {"type": "unknown", "original": ""}
        
    text = text.lower().strip()
    
    # Define common command patterns with expanded vocabulary
    navigation_phrases = [
        "navigate", "guide", "take me", "find", "where is", "how do i get to", 
        "directions to", "way to", "path to", "route to", "lead me to",
        "help me find", "locate", "show me the way", "get me to"
    ]
    
    recognition_phrases = [
        "what is", "describe", "identify", "recognize", "what's in front", 
        "what do you see", "tell me what you see", "what's that", "what are these",
        "analyze", "examine", "check", "detect", "scan", "what's around me",
        "what objects", "what things", "show me"
    ]
    
    chatbot_phrases = [
        "ask", "question", "tell me about", "explain", "how does", "why is", "when was",
        "what's the meaning of", "can you explain", "I want to know", "do you know",
        "what do you think", "give me information"
    ]
    
    reading_phrases = [
        "read", "text", "what does it say", "read aloud", "read this", 
        "what's written", "scan text", "read document", "read sign",
        "interpret text", "translate", "read label", "what is written"
    ]
    
    help_phrases = [
        "help", "assist", "instructions", "commands", "what can you do",
        "how to use", "tutorial", "guide me", "options", "features",
        "functions", "capabilities", "how do you work", "instructions"
    ]
    
    emergency_phrases = [
        "emergency", "help me", "danger", "unsafe", "call for help",
        "sos", "medical", "accident", "fell", "hurt", "injured", "stuck"
    ]
    
    # Check for emergency situations first (highest priority)
    if any(phrase in text for phrase in emergency_phrases):
        return {
            "type": "emergency",
            "priority": "high",
            "situation": text,
            "original": text
        }
    
    # Check for navigation commands
    elif any(phrase in text for phrase in navigation_phrases):
        # Try to extract destination with different patterns
        destination = ""
        for phrase in navigation_phrases:
            if phrase in text and phrase + " to " in text:
                destination = text.split(phrase + " to ")[-1].strip()
                break
            elif " to " in text:
                destination = text.split(" to ")[-1].strip()
                break
        
        # If we still don't have a destination, look for other patterns
        if not destination and "find" in text:
            destination = text.split("find")[-1].strip()
        elif not destination and "where is" in text:
            destination = text.split("where is")[-1].strip()
        
        return {
            "type": "navigation",
            "destination": destination,
            "original": text
        }
    
    # Check for object recognition commands
    elif any(phrase in text for phrase in recognition_phrases):
        # Try to extract specific object interest
        object_of_interest = ""
        for phrase in recognition_phrases:
            if phrase in text and text.startswith(phrase):
                object_of_interest = text[len(phrase):].strip()
                break
        
        return {
            "type": "recognition",
            "object": object_of_interest,
            "original": text
        }
    
    # Check for text reading commands
    elif any(phrase in text for phrase in reading_phrases):
        return {
            "type": "read_text",
            "original": text
        }
    
    # Check for chatbot queries
    elif any(phrase in text for phrase in chatbot_phrases):
        # Extract the query content
        query_content = text
        for phrase in chatbot_phrases:
            if phrase in text and text.startswith(phrase):
                query_content = text[len(phrase):].strip()
                break
            
        return {
            "type": "chatbot",
            "query": query_content,
            "original": text
        }
        
    # Check for help commands
    elif any(phrase in text for phrase in help_phrases):
        # Check for specific help topics
        help_topic = "general"
        if "navigation" in text:
            help_topic = "navigation"
        elif "recognition" in text or "identify" in text:
            help_topic = "recognition"
        elif "read" in text or "text" in text:
            help_topic = "reading"
        elif "chatbot" in text or "ask" in text or "question" in text:
            help_topic = "chatbot"
        
        return {
            "type": "help",
            "topic": help_topic,
            "original": text
        }
    
    # Simple commands
    elif "stop" in text or "cancel" in text:
        return {
            "type": "control",
            "action": "stop",
            "original": text
        }
    elif "pause" in text:
        return {
            "type": "control",
            "action": "pause",
            "original": text
        }
    elif "resume" in text or "continue" in text:
        return {
            "type": "control",
            "action": "resume",
            "original": text
        }
    elif "repeat" in text or "say again" in text:
        return {
            "type": "control",
            "action": "repeat",
            "original": text
        }
    
    # Default response for unrecognized commands
    else:
        # Try to detect if this might be a partial command
        possible_intents = []
        
        # Check partial matches for common actions
        navigation_indicators = ["go", "move", "walk", "turn", "right", "left", "straight", "forward", "backward", "back"]
        recognition_indicators = ["what", "see", "look", "object", "thing", "front", "around"]
        reading_indicators = ["text", "sign", "label", "screen", "document", "paper"]
        
        if any(word in text for word in navigation_indicators):
            possible_intents.append("navigation")
        if any(word in text for word in recognition_indicators):
            possible_intents.append("recognition")
        if any(word in text for word in reading_indicators):
            possible_intents.append("reading")
            
        if possible_intents:
            return {
                "type": "ambiguous",
                "possible_intents": possible_intents,
                "original": text
            }
        
        return {
            "type": "unknown",
            "original": text
        }
