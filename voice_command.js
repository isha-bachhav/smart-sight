// Voice commands functionality
let recognizer;
let isRecognizing = false;
let lastCommand = "";
let lastRecognitionTime = 0;

// Initialize the speech recognition
function initVoiceCommands() {
    // Create Speech Recognition elements
    createVisualFeedbackElements();
    
    // Initialize Speech Recognition
    try {
        // Use the WebSpeech API for voice recognition
        window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        // Initialize continuous listening mode flag
        window.isListeningMode = false;
        window.expectingChatbotQuery = false;
        
        // Create speech recognition object
        recognizer = new SpeechRecognition();
        recognizer.lang = 'en-US'; // Default to English
        recognizer.interimResults = false;
        recognizer.maxAlternatives = 1;
        
        // Add event listeners
        recognizer.onresult = handleVoiceResult;
        recognizer.onerror = handleVoiceError;
        recognizer.onend = handleVoiceEnd;
        
        console.log("Voice commands initialized");
    }
    catch (e) {
        console.error("Voice recognition not supported:", e);
        announce("Voice commands are not available on this device.");
    }
}

// Create visual feedback elements for voice commands
function createVisualFeedbackElements() {
    // Create a listening indicator if it doesn't exist
    if (!document.getElementById('listening-indicator')) {
        const indicator = document.createElement('div');
        indicator.id = 'listening-indicator';
        indicator.classList.add('listening-indicator');
        indicator.innerHTML = `
            <div class="eye-listening">
                <div class="eye-iris"></div>
                <div class="eye-pupil"></div>
            </div>
            <div class="listening-text">Listening...</div>
        `;
        indicator.style.display = 'none';
        document.body.appendChild(indicator);
        
        // Add styles for listening indicator
        const style = document.createElement('style');
        style.textContent = `
            .listening-indicator {
                position: fixed;
                top: 70px;
                left: 50%;
                transform: translateX(-50%);
                background-color: rgba(0, 0, 0, 0.7);
                color: white;
                padding: 15px 25px;
                border-radius: 30px;
                display: flex;
                flex-direction: column;
                align-items: center;
                z-index: 1000;
                box-shadow: 0 0 20px rgba(142, 68, 173, 0.6);
                border: 1px solid rgba(142, 68, 173, 0.4);
            }
            
            .eye-listening {
                position: relative;
                width: 60px;
                height: 30px;
                border-radius: 50%;
                background: #21005d;
                overflow: hidden;
                margin-bottom: 8px;
            }
            
            .eye-iris {
                position: absolute;
                width: 40px;
                height: 40px;
                background: radial-gradient(circle, #7954a1 20%, #3a1a5e 60%);
                border-radius: 50%;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                animation: look 3s infinite;
            }
            
            .eye-pupil {
                position: absolute;
                width: 20px;
                height: 20px;
                background: #000;
                border-radius: 50%;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                animation: pupil-pulse 1.5s infinite;
            }
            
            .listening-text {
                font-size: 16px;
                margin-top: 5px;
                opacity: 0.9;
            }
            
            @keyframes look {
                0%, 100% { transform: translate(-50%, -50%); }
                25% { transform: translate(-70%, -50%); }
                75% { transform: translate(-30%, -50%); }
            }
            
            @keyframes pupil-pulse {
                0%, 100% { transform: translate(-50%, -50%) scale(1); }
                50% { transform: translate(-50%, -50%) scale(0.8); }
            }
        `;
        document.head.appendChild(style);
    }
}

// Show/hide the listening indicator
function toggleListeningIndicator(show) {
    const indicator = document.getElementById('listening-indicator');
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
    }
    
    // Also update the pulse animation on the main screen
    const mainScreen = document.getElementById('main-screen');
    if (mainScreen) {
        if (show) {
            mainScreen.classList.add('listening');
        } else {
            mainScreen.classList.remove('listening');
        }
    }
}

// Toggle continuous listening mode
function toggleContinuousListening() {
    window.isListeningMode = !window.isListeningMode;
    
    if (window.isListeningMode) {
        announce("Continuous listening mode activated. I'll listen for commands until you say 'stop listening'.");
        
        // Start listening
        if (!isRecognizing) {
            startVoiceRecognition();
        }
    } else {
        announce("Continuous listening mode deactivated.");
        
        // Visual feedback
        toggleListeningIndicator(false);
    }
}

// Start the voice recognition service
function startVoiceRecognition() {
    // Don't restart if already recognizing
    if (isRecognizing) return;
    
    try {
        isRecognizing = true;
        recognizer.start();
        console.log("Voice recognition started");
        
        // Show listening indicator
        toggleListeningIndicator(true);
        
        // Provide haptic feedback
        vibrate([50, 25, 50]);
        
        // Record start time
        lastRecognitionTime = Date.now();
    } catch (e) {
        console.error("Error starting voice recognition:", e);
        isRecognizing = false;
        toggleListeningIndicator(false);
    }
}

// Handle voice recognition results
function handleVoiceResult(event) {
    isRecognizing = false;
    toggleListeningIndicator(false);
    
    // Get the transcript of the recognized speech
    const transcript = event.results[0][0].transcript.trim();
    console.log("Voice recognized:", transcript);
    
    // Update feedback area
    const feedbackArea = document.getElementById('feedback-area');
    if (feedbackArea) {
        feedbackArea.textContent = `You said: ${transcript}`;
    }
    
    // Debounce to prevent duplicate commands
    const now = Date.now();
    const timeSinceLastCommand = now - lastRecognitionTime;
    
    if (timeSinceLastCommand < 1000 && transcript === lastCommand) {
        console.log("Ignoring duplicate command");
        return;
    }
    
    // Process the command
    lastCommand = transcript;
    processVoiceCommand(transcript);
    
    // Restart listening if in continuous mode
    if (window.isListeningMode) {
        setTimeout(() => {
            if (window.isListeningMode) {
                startVoiceRecognition();
            }
        }, 1000);
    }
}

// Handle voice recognition errors
function handleVoiceError(event) {
    isRecognizing = false;
    toggleListeningIndicator(false);
    
    console.error("Voice recognition error:", event.error);
    
    // Handle different error types
    let errorMessage = "";
    switch (event.error) {
        case 'no-speech':
            errorMessage = "I didn't hear anything. Please try again.";
            break;
        case 'audio-capture':
            errorMessage = "No microphone was found. Ensure microphone is connected and permissions are granted.";
            break;
        case 'not-allowed':
            errorMessage = "Microphone permission is denied. Please enable microphone access.";
            break;
        case 'network':
            errorMessage = "Network error occurred. Please check your connection.";
            break;
        case 'aborted':
            // Silent error - user likely cancelled
            return;
        default:
            errorMessage = "Error recognizing voice. Please try again.";
    }
    
    // Only announce errors if not in continuous listening mode
    if (!window.isListeningMode) {
        announce(errorMessage);
    } else {
        console.log("Error in continuous mode, restarting:", errorMessage);
        setTimeout(() => {
            if (window.isListeningMode) {
                startVoiceRecognition();
            }
        }, 2000);
    }
}

// Handle voice recognition end event
function handleVoiceEnd() {
    console.log("Voice recognition ended");
    isRecognizing = false;
    toggleListeningIndicator(false);
    
    // Restart listening if in continuous mode
    if (window.isListeningMode) {
        setTimeout(() => {
            if (window.isListeningMode) {
                startVoiceRecognition();
            }
        }, 1000);
    }
}

// Process voice commands
function processVoiceCommand(command) {
    if (!command) return;
    
    const lowerCommand = command.toLowerCase();
    
    // Check for "remember" commands to add to knowledge base
    if (processKnowledgeCommand(command)) {
        return;
    }
    
    // Handle continuous listening mode
    if (lowerCommand.includes('start listening') || lowerCommand.includes('begin listening')) {
        toggleContinuousListening();
        return;
    }
    
    if (lowerCommand.includes('stop listening') || lowerCommand.includes('end listening')) {
        window.isListeningMode = false;
        announce("Continuous listening mode deactivated.");
        return;
    }
    
    // Handle specific commands
    if (lowerCommand.includes('what is this') || lowerCommand.includes('identify') || 
        lowerCommand.includes('what do you see') || lowerCommand.includes('describe this')) {
        captureImageAndProcess('identify');
        return;
    }
    
    if (lowerCommand.includes('guide me') || lowerCommand.includes('navigate') || 
        lowerCommand.includes('help me find') || lowerCommand.includes('which way')) {
        captureImageAndProcess('navigate');
        return;
    }
    
    if (lowerCommand.includes('read this') || lowerCommand.includes('read text') || 
        lowerCommand.includes('what does it say') || lowerCommand.includes('read aloud')) {
        captureImageAndProcess('read');
        return;
    }
    
    if (lowerCommand.includes('night mode') || lowerCommand.includes('dark mode')) {
        toggleNightMode();
        return;
    }
    
    if (lowerCommand.includes('normal mode') || lowerCommand.includes('day mode') || lowerCommand.includes('light mode')) {
        // If in night mode, switch to normal mode
        if (document.body.classList.contains('night-mode')) {
            document.body.classList.remove('night-mode');
            announce("Normal mode activated.");
        } else {
            announce("Already in normal mode.");
        }
        return;
    }
    
    // Emergency mode
    if (lowerCommand.includes('emergency mode') || lowerCommand.includes('emergency') && !lowerCommand.includes('cancel')) {
        toggleEmergencyMode();
        return;
    }
    
    // Cancel emergency mode
    if (lowerCommand.includes('cancel emergency')) {
        if (document.body.classList.contains('emergency-mode')) {
            document.body.classList.remove('emergency-mode');
            const emergencyOverlay = document.getElementById('emergency-overlay');
            if (emergencyOverlay) emergencyOverlay.remove();
            
            const emergencyStyle = document.getElementById('emergency-style');
            if (emergencyStyle) emergencyStyle.remove();
            
            announce("Emergency mode deactivated.");
        } else {
            announce("Emergency mode is not active.");
        }
        return;
    }
    
    // For other queries, route to chatbot
    window.expectingChatbotQuery = true;
    processChatbotQuery(command);
}

// Toggle emergency mode
function toggleEmergencyMode() {
    if (document.body.classList.contains('emergency-mode')) {
        // Already in emergency mode
        announce("Emergency mode is already active.");
        return;
    }
    
    // Create emergency overlay if it doesn't exist
    if (!document.getElementById('emergency-overlay')) {
        const overlay = document.createElement('div');
        overlay.id = 'emergency-overlay';
        overlay.innerHTML = `
            <div class="emergency-message">EMERGENCY MODE ACTIVE</div>
            <div class="emergency-instructions">
                Show this screen to others for assistance.<br>
                Say "cancel emergency" to exit this mode.
            </div>
        `;
        document.body.appendChild(overlay);
        
        // Add emergency mode styles if they don't exist
        if (!document.getElementById('emergency-style')) {
            const style = document.createElement('style');
            style.id = 'emergency-style';
            style.textContent = `
                #emergency-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: red;
                    color: white;
                    z-index: 10000;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    animation: flash 1s infinite;
                }
                
                .emergency-message {
                    font-size: 32px;
                    font-weight: bold;
                    margin-bottom: 20px;
                    text-align: center;
                }
                
                .emergency-instructions {
                    font-size: 18px;
                    text-align: center;
                    margin: 0 20px;
                }
                
                @keyframes flash {
                    0%, 100% { background-color: red; }
                    50% { background-color: #ff5555; }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    // Add emergency class to body
    document.body.classList.add('emergency-mode');
    
    // Provide feedback
    vibrate([200, 100, 200, 100, 200]);
    announce("Emergency mode activated. This screen will flash red to attract attention. Say 'cancel emergency' to exit this mode.");
    
    // Play alert sound if available
    const alertSound = new Audio('/static/resources/alert.mp3');
    alertSound.onerror = function() {
        console.log('Alert sound not available, using beep instead');
        const beep = createBeepSound();
        beep.play();
    };
    alertSound.play().catch(e => {
        console.log('Error playing alert sound:', e);
        // Fallback to beep if audio fails to play
        const beep = createBeepSound();
        beep.play();
    });
}
