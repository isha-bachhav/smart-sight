// Main application functionality

// Initialize the application
function initApp() {
    // Initialize camera functionality
    initCamera();
    
    // Initialize voice commands
    initVoiceCommands();
    
    // Check required permissions
    checkPermissions();
    
    // Set up touch interface
    setupTouchInterface();
    
    // Set up feather icons and other UI elements
    document.addEventListener('DOMContentLoaded', () => {
        if (window.feather) {
            feather.replace();
        }
        
        // Play welcome message
        playWelcomeMessage();
    });
}

// Play welcome message for first-time users or refreshed sessions
function playWelcomeMessage() {
    fetch('/api/welcome')
        .then(response => response.json())
        .then(data => {
            if (data && data.message) {
                // Add slight delay for better UX
                setTimeout(() => {
                    speakText(data.message);
                    // Play a welcome beep sound for audio feedback
                    signalUser();
                }, 1000);
            }
        })
        .catch(error => console.error('Error fetching welcome message:', error));
}

// Check for required permissions
function checkPermissions() {
    // Check for microphone and camera permissions
    navigator.permissions.query({name: 'microphone'})
        .then(result => {
            if (result.state === 'granted') {
                console.log('Microphone permission granted');
            } else {
                console.warn('Microphone permission not granted');
                document.getElementById('feedback-area').textContent = 
                    'Please allow microphone access for voice commands.';
            }
        })
        .catch(err => console.error('Error checking microphone permission:', err));
    
    navigator.permissions.query({name: 'camera'})
        .then(result => {
            if (result.state === 'granted') {
                console.log('Camera permission granted');
            } else {
                console.warn('Camera permission not granted');
                document.getElementById('feedback-area').textContent = 
                    'Please allow camera access for object identification.';
            }
        })
        .catch(err => console.error('Error checking camera permission:', err));
}

// Setup touchable interface
function setupTouchInterface() {
    const mainScreen = document.getElementById('main-screen');
    const feedbackArea = document.getElementById('feedback-area');
    
    // Main screen touch
    if (mainScreen) {
        mainScreen.addEventListener('click', () => {
            signalUser();
            feedbackArea.textContent = 'Listening...';
            startVoiceRecognition();
            
            // Visual feedback
            function handleSwipeGesture() {
                mainScreen.classList.add('pulse');
                setTimeout(() => {
                    mainScreen.classList.remove('pulse');
                }, 300);
            }
            
            handleSwipeGesture();
        });
    }
    
    // Button event listeners
    document.getElementById('help-button').addEventListener('click', () => {
        signalUser();
        feedbackArea.textContent = "Providing help...";
        processVoiceCommand('help');
    });
    
    document.getElementById('identify-button').addEventListener('click', () => {
        signalUser();
        feedbackArea.textContent = "Identifying objects...";
        captureImageAndProcess('identify');
    });
    
    document.getElementById('navigate-button').addEventListener('click', () => {
        signalUser();
        feedbackArea.textContent = "Navigation assistant activated...";
        captureImageAndProcess('navigate');
    });
    
    document.getElementById('read-text-button').addEventListener('click', () => {
        signalUser();
        feedbackArea.textContent = "Reading text...";
        captureImageAndProcess('read');
    });
    
    document.getElementById('chatbot-button').addEventListener('click', () => {
        signalUser();
        feedbackArea.textContent = "Ask a question...";
        startVoiceRecognition();
        window.expectingChatbotQuery = true;
    });
}

// Capture image and process based on mode
function captureImageAndProcess(mode) {
    // Show loading indicator immediately
    document.querySelector('.eye-loading').classList.add('visible');
    
    // Take picture using camera (which returns a Promise)
    takePicture()
        .then(imageData => {
            if (!imageData) {
                document.querySelector('.eye-loading').classList.remove('visible');
                announce("No image captured. Please try again.");
                return;
            }
            
            // Process based on mode
            switch(mode) {
                case 'identify':
                    identifyObjects(imageData);
                    break;
                case 'navigate':
                    provideNavigation(imageData);
                    break;
                case 'read':
                    readText(imageData);
                    break;
                default:
                    document.querySelector('.eye-loading').classList.remove('visible');
                    announce("Invalid mode selected");
            }
        })
        .catch(error => {
            document.querySelector('.eye-loading').classList.remove('visible');
            console.error("Camera error:", error);
            announce("Camera not available. Please check camera permissions.");
        });
}

// Identify objects in image
function identifyObjects(imageData) {
    const feedbackArea = document.getElementById('feedback-area');
    feedbackArea.textContent = "Analyzing image...";
    
    // Convert base64 image to blob for multipart/form-data
    const blob = dataURItoBlob(imageData);
    const formData = new FormData();
    formData.append('image', blob, 'image.jpg');
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    
    fetch(`/api/analyze-image?t=${timestamp}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector('.eye-loading').classList.remove('visible');
        
        if (data && data.description) {
            feedbackArea.textContent = data.description;
            speakText(data.description);
        } else {
            feedbackArea.textContent = "Could not identify objects. Please try again.";
            speakText("Could not identify objects. Please try again.");
        }
    })
    .catch(error => {
        document.querySelector('.eye-loading').classList.remove('visible');
        console.error('Error identifying objects:', error);
        feedbackArea.textContent = "Error analyzing image. Please try again.";
        speakText("Error analyzing image. Please try again.");
    });
}

// Provide navigation assistance based on image
function provideNavigation(imageData) {
    const feedbackArea = document.getElementById('feedback-area');
    feedbackArea.textContent = "Analyzing surroundings for navigation...";
    
    // Convert base64 image to blob for multipart/form-data
    const blob = dataURItoBlob(imageData);
    const formData = new FormData();
    formData.append('image', blob, 'image.jpg');
    
    // Get any additional context from user (can be empty for basic navigation)
    const context = ''; // This could be set by a previous voice command
    formData.append('context', context);
    
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    
    fetch(`/api/describe-surroundings?t=${timestamp}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector('.eye-loading').classList.remove('visible');
        
        if (data && data.description) {
            feedbackArea.textContent = data.description;
            speakText(data.description);
            vibrate([100, 50, 100]); // Distinctive vibration pattern
        } else {
            feedbackArea.textContent = "Could not analyze surroundings. Please try again.";
            speakText("Could not analyze surroundings. Please try again.");
        }
    })
    .catch(error => {
        document.querySelector('.eye-loading').classList.remove('visible');
        console.error('Error providing navigation:', error);
        feedbackArea.textContent = "Error analyzing surroundings. Please try again.";
        speakText("Error analyzing surroundings. Please try again.");
    });
}

// Extract and read text from an image
function readText(imageData) {
    const feedbackArea = document.getElementById('feedback-area');
    feedbackArea.textContent = "Reading text from image...";
    
    // Convert base64 image to blob for multipart/form-data
    const blob = dataURItoBlob(imageData);
    const formData = new FormData();
    formData.append('image', blob, 'image.jpg');
    
    fetch('/api/read-text', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector('.eye-loading').classList.remove('visible');
        
        if (data && data.text && data.text.trim() !== '') {
            feedbackArea.textContent = data.text;
            speakText(data.text);
        } else {
            feedbackArea.textContent = "No text detected in image. Please try again.";
            speakText("No text detected in image. Please try again.");
        }
    })
    .catch(error => {
        document.querySelector('.eye-loading').classList.remove('visible');
        console.error('Error reading text:', error);
        feedbackArea.textContent = "Error reading text. Please try again.";
        speakText("Error reading text. Please try again.");
    });
}

// Process query with chatbot
function processChatbotQuery(query) {
    const feedbackArea = document.getElementById('feedback-area');
    feedbackArea.textContent = "Processing: " + query;
    
    // First check if the query is a knowledge request
    if (processKnowledgeCommand(query)) {
        // If it was a knowledge request, it's already been handled
        document.querySelector('.eye-loading').classList.remove('visible');
        return;
    }
    
    fetch('/api/chatbot', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query
        })
    })
    .then(response => response.json())
    .then(data => {
        document.querySelector('.eye-loading').classList.remove('visible');
        
        if (data && data.response) {
            feedbackArea.textContent = data.response;
            speakText(data.response);
        } else {
            feedbackArea.textContent = "I couldn't find an answer. Please try again.";
            speakText("I couldn't find an answer. Please try again.");
        }
    })
    .catch(error => {
        document.querySelector('.eye-loading').classList.remove('visible');
        console.error('Error processing query:', error);
        feedbackArea.textContent = "Error processing query. Please try again.";
        speakText("Error processing query. Please try again.");
    });
}

// Convert data URI to Blob for server uploads
function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    
    return new Blob([ab], {type: mimeString});
}

// Speak text using Web Speech API or server fallback
function speakText(text) {
    if (!text) return;
    
    // Try using server-side TTS
    fetch('/api/tts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            text: text
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data && data.audio) {
            // Convert base64 audio to blob and play
            const audioBlob = base64ToBlob(data.audio, 'audio/mp3');
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();
        } else {
            throw new Error('Invalid audio data');
        }
    })
    .catch(error => {
        console.error('Error with server TTS:', error);
        
        // Fallback to browser TTS
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.0;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        window.speechSynthesis.speak(utterance);
    });
}

// Provide haptic feedback when available
function vibrate(pattern) {
    if (navigator.vibrate) {
        navigator.vibrate(pattern);
    }
}

// Announce message for screen readers
function announce(message) {
    const announcer = document.getElementById('a11y-announcer');
    announcer.textContent = message;
    
    // Also update the visible feedback area
    const feedbackArea = document.getElementById('feedback-area');
    feedbackArea.textContent = message;
    
    // Speak the message
    speakText(message);
}

// Convert base64 to blob for audio processing
function base64ToBlob(base64, mimeType) {
    const byteString = atob(base64);
    const arrayBuffer = new ArrayBuffer(byteString.length);
    const intArray = new Uint8Array(arrayBuffer);
    
    for (let i = 0; i < byteString.length; i++) {
        intArray[i] = byteString.charCodeAt(i);
    }
    
    return new Blob([intArray], {type: mimeType});
}

// Toggle dark/night mode for low-light environments
function toggleNightMode() {
    const body = document.body;
    const isCurrentlyNightMode = body.classList.contains('night-mode');
    
    if (isCurrentlyNightMode) {
        body.classList.remove('night-mode');
        localStorage.setItem('nightMode', 'false');
        announce("Normal mode activated");
    } else {
        body.classList.add('night-mode');
        localStorage.setItem('nightMode', 'true');
        announce("Night mode activated for low light conditions");
    }
}

// Load preferences on init
window.addEventListener('DOMContentLoaded', () => {
    // Check if night mode was previously enabled
    if (localStorage.getItem('nightMode') === 'true') {
        document.body.classList.add('night-mode');
    }
    
    // Start the app
    initApp();
});

// Add a function to regularly check API connectivity
function checkApiConnectivity() {
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            // Server is healthy, update status
            document.body.classList.add('api-connected');
            document.body.classList.remove('api-disconnected');
            
            // Remove any existing error messages
            const existingErrors = document.querySelectorAll('.error-message');
            existingErrors.forEach(error => error.remove());
        })
        .catch(error => {
            console.error('Health check failed:', error);
            document.body.classList.remove('api-connected');
            document.body.classList.add('api-disconnected');
            
            // Only add error message if one doesn't already exist
            if (!document.querySelector('.error-message')) {
                const errorMessage = document.createElement('div');
                errorMessage.classList.add('error-message');
                errorMessage.textContent = 'Connection to server lost. Please refresh the page.';
                document.body.appendChild(errorMessage);
            }
        });
}

// Check connectivity when page loads and then every 30 seconds
window.addEventListener('DOMContentLoaded', () => {
    // Initial check
    checkApiConnectivity();
    
    // Set interval for periodic checks
    setInterval(checkApiConnectivity, 30000);
});

// Function to add knowledge to the database
async function addKnowledgeToDatabase(question, answer, category = 'user-provided') {
    try {
        const response = await fetch('/api/add-knowledge', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                answer: answer,
                category: category
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            announce("Information added to my knowledge. I'll remember that.");
            return true;
        } else {
            announce("Sorry, I couldn't save that information. Please try again.");
            console.error('Error adding knowledge:', data.error);
            return false;
        }
    } catch (error) {
        console.error('Error adding knowledge to database:', error);
        announce("There was a technical issue. Please try again later.");
        return false;
    }
}
