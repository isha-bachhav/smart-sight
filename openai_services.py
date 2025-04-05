import os
import base64
import io
import numpy as np
from PIL import Image, ImageFilter

print("Initializing with advanced image processing for object recognition")

# Load common object labels
def load_or_create_labels():
    labels_file_path = 'static/resources/imagenet_labels.txt'
    
    # Check if directory exists, if not create it
    os.makedirs(os.path.dirname(labels_file_path), exist_ok=True)
    
    # Common object categories (simplified)
    common_labels = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
        "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog",
        "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
        "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball", "kite", 
        "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket", "bottle",
        "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", 
        "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", 
        "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
        "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush", "house", "building",
        "grass", "tree", "sidewalk", "road", "river", "mountain", "ocean", "sky", "cloud", "desk",
        "door", "stairs", "shelf", "closet", "lamp", "pillow", "blanket", "curtain", "window",
        "street light", "fence", "wall", "floor", "ceiling", "roof", "trash can", "cabinet"
    ]
    
    # Only create file if it doesn't exist
    if not os.path.exists(labels_file_path):
        print("Creating common object labels file...")
        # Write the labels to the file
        with open(labels_file_path, 'w') as f:
            for label in common_labels:
                f.write(f"{label}\n")
        print(f"Created label file with {len(common_labels)} categories")
    
    # Return the labels
    try:
        with open(labels_file_path, 'r') as f:
            return [line.strip() for line in f.readlines()]
    except:
        return common_labels

# Load labels
COMMON_OBJECTS = load_or_create_labels()
print(f"Loaded {len(COMMON_OBJECTS)} object categories")

def preprocess_image(base64_image):
    """
    Preprocesses a base64 image for analysis.
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        
        # Resize and normalize image for consistent processing
        image = image.resize((224, 224))
        image_array = np.array(image) / 255.0
        
        return image_array, image
    except Exception as e:
        raise Exception(f"Error preprocessing image: {str(e)}")

def analyze_image(base64_image, timestamp=None):
    """
    Analyze an image and return a detailed description suitable for blind users.
    Now with specific object detection including people recognition.
    
    Args:
        base64_image (str): Base64 encoded image
        timestamp (str, optional): Timestamp to prevent caching
        
    Returns:
        str: Description of the image with detected objects
    """
    try:
        # Preprocess image
        image_array, original_image = preprocess_image(base64_image)
        
        # Basic image analysis for brightness and blur
        gray_image = original_image.convert('L')
        gray_array = np.array(gray_image)
        brightness = np.mean(gray_array) / 255
        brightness_desc = "dark" if brightness < 0.4 else "well-lit" if brightness > 0.6 else "moderately lit"
        
        # Detect edges to estimate complexity/busyness
        edge_image = original_image.filter(ImageFilter.FIND_EDGES)
        edge_array = np.array(edge_image.convert('L'))
        edge_strength = np.mean(edge_array)
        complexity = "simple" if edge_strength < 10 else "complex" if edge_strength > 30 else "moderately detailed"
        
        # Initialize detected objects list
        detected_objects = []
        
        # Convert to RGB for analysis
        rgb_image = np.array(original_image.convert('RGB'))
        
        # PERSON DETECTION
        # Only run if image is large enough
        if rgb_image.shape[0] > 10 and rgb_image.shape[1] > 10:
            # Extract RGB channels
            r = rgb_image[:,:,0]
            g = rgb_image[:,:,1]
            b = rgb_image[:,:,2]
            
            # Create skin masks for different skin tones
            skin_mask1 = ((r > 95) & (g > 40) & (b > 20) & (r > g) & (r > b))
            skin_mask2 = ((r > 190) & (g > 110) & (b > 70) & (r > g) & (r > b))
            skin_mask3 = ((r > 80) & (r < 200) & (g > 30) & (g < 170) & (b > 15) & (b < 140))
            
            # Combine masks
            skin_mask = skin_mask1 | skin_mask2 | skin_mask3
            
            # Calculate percentage
            total_pixels = skin_mask.shape[0] * skin_mask.shape[1]
            if total_pixels > 0:  # Avoid division by zero
                skin_pixels = np.sum(skin_mask)
                skin_percentage = float(skin_pixels) / float(total_pixels)
                
                # Check for person
                if skin_percentage > 0.05:
                    detected_objects.append("person")
                    
                    # Basic face detection
                    if rgb_image.shape[0] >= 3:  # Make sure image has enough rows
                        top_third = rgb_image[:rgb_image.shape[0]//3, :, :]
                        top_gray = np.mean(top_third, axis=2)
                        
                        if top_gray.size > 0:  # Make sure we have data
                            top_edges = np.array(Image.fromarray(top_gray.astype(np.uint8))
                                              .filter(ImageFilter.FIND_EDGES))
                            face_edge_strength = np.mean(top_edges)
                            
                            if face_edge_strength > 20:
                                detected_objects.append("face")
        
        # OBJECT DETECTION
        # Safe division
        grid_size = 3
        height, width = rgb_image.shape[0], rgb_image.shape[1]
        
        # Only process if image is large enough for grid
        if height > grid_size and width > grid_size:
            cell_height = height // grid_size
            cell_width = width // grid_size
            
            # Analyze grid cells
            for i in range(grid_size):
                for j in range(grid_size):
                    # Define cell boundaries
                    y_start = i * cell_height
                    y_end = min((i + 1) * cell_height, height)
                    x_start = j * cell_width
                    x_end = min((j + 1) * cell_width, width)
                    
                    # Safe extraction (ensure indices are valid)
                    if y_start < y_end and x_start < x_end:
                        # Extract cell
                        cell = rgb_image[y_start:y_end, x_start:x_end, :]
                        
                        if cell.size > 0:  # Only process non-empty cells
                            # Compute cell features
                            cell_mean = np.mean(cell, axis=(0, 1))
                            cell_std = np.std(cell, axis=(0, 1))
                            
                            # Process grayscale for edge detection
                            cell_gray = np.mean(cell, axis=2).astype(np.uint8)
                            cell_edge_img = Image.fromarray(cell_gray).filter(ImageFilter.FIND_EDGES)
                            cell_edge_array = np.array(cell_edge_img)
                            cell_edge_strength = np.mean(cell_edge_array)
                            
                            # Extract color information
                            if len(cell_mean) >= 3:  # Ensure we have RGB
                                r_mean, g_mean, b_mean = cell_mean[0], cell_mean[1], cell_mean[2]
                                
                                # Blue (sky, water)
                                if b_mean > r_mean + 20 and b_mean > g_mean + 20 and b_mean > 150:
                                    if i == 0 and "sky" not in detected_objects:
                                        detected_objects.append("sky")
                                    elif cell_std.mean() < 30 and "water" not in detected_objects:
                                        detected_objects.append("water")
                                
                                # Green (plants, grass, trees)
                                if g_mean > r_mean + 10 and g_mean > b_mean + 10 and g_mean > 100:
                                    if i >= grid_size//2:
                                        if "grass" not in detected_objects and "plants" not in detected_objects:
                                            detected_objects.append("plants")
                                    else:
                                        if "tree" not in detected_objects and "plants" not in detected_objects:
                                            detected_objects.append("tree")
                                
                                # Furniture detection
                                if cell_edge_strength > 30 and cell_std.mean() < 40 and i == 1:
                                    if "furniture" not in detected_objects:
                                        detected_objects.append("furniture")
                                
                                # Wall detection
                                if cell_edge_strength < 20 and cell_std.mean() < 30:
                                    if "wall" not in detected_objects and i < grid_size-1:
                                        detected_objects.append("wall")
                                
                                # Path/Road detection
                                if abs(r_mean - g_mean) < 20 and abs(g_mean - b_mean) < 20 and r_mean < 150:
                                    if i >= grid_size-1 and "path" not in detected_objects:
                                        detected_objects.append("path")
        
        # Remove duplicates
        detected_objects = list(set(detected_objects))
        
        # Dominant color detection
        try:
            colors = original_image.convert('RGB').getcolors(maxcolors=1024)
            color_desc = "mixed colors"
            
            if colors:
                colors.sort(reverse=True)
                dominant_color_rgb = colors[0][1]
                r, g, b = dominant_color_rgb
                
                # Define color ranges
                color_map = {
                    "red": r > 200 and g < 100 and b < 100,
                    "green": r < 100 and g > 200 and b < 100,
                    "blue": r < 100 and g < 100 and b > 200,
                    "yellow": r > 200 and g > 200 and b < 100,
                    "purple": r > 100 and g < 100 and b > 200,
                    "orange": r > 200 and g > 100 and b < 100,
                    "white": r > 200 and g > 200 and b > 200,
                    "black": r < 50 and g < 50 and b < 50,
                    "gray": abs(r - g) < 30 and abs(g - b) < 30 and r > 50 and r < 200
                }
                
                # Find matching color
                for name, condition in color_map.items():
                    if condition:
                        color_desc = name
                        break
        except:
            # Fallback if color analysis fails
            color_desc = "mixed colors"
        
        # Scene environment analysis
        # Safely crop image for analysis
        img_width, img_height = original_image.size
        top = original_image.crop((0, 0, img_width, img_height//3))
        bottom = original_image.crop((0, 2*img_height//3, img_width, img_height))
        
        # Analyze regions
        top_array = np.array(top.convert('L'))
        top_brightness = np.mean(top_array) / 255 if top_array.size > 0 else 0
        
        # Check for sky
        top_rgb = np.array(top.convert('RGB'))
        has_sky = False
        if top_rgb.size > 0:
            top_blue = np.mean(top_rgb[:,:,2]) / 255
            has_sky = top_brightness > 0.6 and top_blue > 0.5
        
        # Check for ground
        bottom_array = np.array(bottom.convert('L'))
        has_ground = False
        if bottom_array.size > 0:
            bottom_variance = np.var(bottom_array)
            has_ground = bottom_variance < 2000
        
        # Determine scene type
        scene_type = "outdoor" if has_sky else "indoor" if brightness < 0.5 else "unknown"
        
        # Generate appropriate description
        if detected_objects:
            # Define priority for natural description
            priority_objects = ["person", "face", "furniture", "wall", "path", "sky", "water", "tree", "plants"]
            
            # Sort objects by priority (use list index or high number if not in priority list)
            def get_priority(obj):
                try:
                    return priority_objects.index(obj)
                except ValueError:
                    return 999
            
            sorted_objects = sorted(detected_objects, key=get_priority)
            
            # Person-centered description
            if "person" in sorted_objects:
                description = "I detect a person "
                
                # Filter other objects
                other_objects = [obj for obj in sorted_objects if obj != "person" and obj != "face"]
                
                if "face" in sorted_objects:
                    description += "with a visible face "
                
                # Add other object info
                if other_objects:
                    if len(other_objects) == 1:
                        description += f"with {other_objects[0]} in the background. "
                    else:
                        objects_text = ", ".join(other_objects[:-1]) + f" and {other_objects[-1]}"
                        description += f"with {objects_text} in the background. "
                else:
                    description += f"in a {brightness_desc} {scene_type} environment. "
            else:
                # Object-centered description
                if len(sorted_objects) == 1:
                    description = f"I detect {sorted_objects[0]} "
                elif len(sorted_objects) == 2:
                    description = f"I detect {sorted_objects[0]} and {sorted_objects[1]} "
                else:
                    objects_text = ", ".join(sorted_objects[:-1]) + f" and {sorted_objects[-1]}"
                    description = f"I detect {objects_text} "
                
                description += f"in this {brightness_desc} {scene_type} scene. "
        else:
            # General scene description
            description = f"This appears to be a {brightness_desc}, {complexity} {scene_type} scene with primarily {color_desc} tones. "
            
            # Add scene details
            if scene_type == "outdoor":
                if has_sky:
                    description += "There appears to be sky above. "
                if has_ground:
                    description += "There appears to be a path or ground surface below. "
            elif scene_type == "indoor":
                if edge_strength > 30:
                    description += "The space appears to contain various objects or furniture. "
                else:
                    description += "The space appears to be relatively open. "
        
        return description
    except Exception as e:
        return f"I'm having trouble analyzing this image: {str(e)}. If you're trying to navigate, please proceed with caution and consider asking for assistance."

def describe_surroundings(base64_image, context="", timestamp=None):
    """
    Provide navigation assistance based on an image and context.
    
    Args:
        base64_image (str): Base64 encoded image
        context (str): Additional context like user's goal or question
        timestamp (str, optional): Timestamp to prevent caching
        
    Returns:
        str: Navigation guidance
    """
    try:
        # Preprocess image
        _, original_image = preprocess_image(base64_image)
        
        # Basic image analysis
        width, height = original_image.size
        
        # Divide image into regions for spatial analysis
        regions = []
        region_names = ["top-left", "top-right", "center", "bottom-left", "bottom-right"]
        
        # Split image into 5 regions
        left = original_image.crop((0, 0, width//2, height//2))
        right = original_image.crop((width//2, 0, width, height//2))
        center = original_image.crop((width//4, height//4, 3*width//4, 3*height//4))
        bottom_left = original_image.crop((0, height//2, width//2, height))
        bottom_right = original_image.crop((width//2, height//2, width, height))
        
        regions = [left, right, center, bottom_left, bottom_right]
        
        # Analyze each region for contrast (potential obstacles)
        region_descriptions = []
        for i, region in enumerate(regions):
            region_array = np.array(region.convert('L'))
            std_dev = np.std(region_array)
            mean_brightness = np.mean(region_array) / 255
            
            # Higher contrast might indicate objects or obstacles
            if std_dev > 50:
                region_descriptions.append(f"potential objects in the {region_names[i]}")
            elif mean_brightness < 0.3:
                region_descriptions.append(f"dark area in the {region_names[i]}")
            elif mean_brightness > 0.8:
                region_descriptions.append(f"bright area in the {region_names[i]}")
        
        # Check for potential path (higher brightness in bottom center usually indicates path)
        bottom_center = original_image.crop((width//3, 2*height//3, 2*width//3, height))
        bottom_brightness = np.mean(np.array(bottom_center.convert('L'))) / 255
        
        if bottom_brightness > 0.6:
            path_desc = "There may be a clear path directly ahead."
        elif bottom_brightness < 0.3:
            path_desc = "The path ahead appears dark or may have obstacles."
        else:
            path_desc = "The path ahead has moderate visibility."
        
        # Edge detection for obstacles
        edges = original_image.filter(ImageFilter.FIND_EDGES)
        edge_strength = np.mean(np.array(edges.convert('L')))
        obstacle_desc = ""
        if edge_strength > 40:
            obstacle_desc = "I detect many potential objects or obstacles in your surroundings. "
        elif edge_strength > 20:
            obstacle_desc = "I detect some potential objects or obstacles. "
        
        # Analyze horizontal lines that might indicate pathways, corridors or sidewalks
        horizontal_edges = original_image.filter(ImageFilter.FIND_EDGES)
        horizontal_array = np.array(horizontal_edges.convert('L'))
        # Only analyze bottom half for pathways
        lower_half = horizontal_array[height//2:, :]
        horizontal_strength = np.mean(lower_half)
        
        path_guidance = ""
        if horizontal_strength > 30:
            path_guidance = "There appears to be a path or corridor ahead. "
        
        # Compose navigation guidance
        navigation = f"Based on my analysis: "
        
        if obstacle_desc:
            navigation += obstacle_desc
        
        if region_descriptions:
            navigation += f"I notice {', '.join(region_descriptions[:3])}. "
        
        navigation += path_desc + " "
        
        if path_guidance:
            navigation += path_guidance
        
        # Add context-specific guidance
        if context:
            context_lower = context.lower()
            if "find" in context_lower or "looking for" in context_lower:
                target = context_lower.split("find")[-1].strip() if "find" in context_lower else context_lower.split("looking for")[-1].strip()
                navigation += f"Without advanced object recognition, I can't specifically identify a {target}. "
        
        # Safety recommendation
        navigation += "Please proceed with caution and use your cane or other assistive device if available."
        
        return navigation
    except Exception as e:
        return f"I'm having trouble analyzing this scene for navigation. Please proceed with extreme caution or seek assistance. Error: {str(e)}"

def recognize_text(base64_image):
    """
    Extract and read text visible in an image.
    Uses basic image processing as a placeholder for proper OCR.
    
    Args:
        base64_image (str): Base64 encoded image
        
    Returns:
        str: Extracted text
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to grayscale
        gray_image = image.convert('L')
        
        # Apply Gaussian blur to reduce noise
        blurred = gray_image.filter(ImageFilter.GaussianBlur(radius=1))
        
        # Manual thresholding to detect potential text areas
        threshold = 128
        binary_image = blurred.point(lambda x: 0 if x < threshold else 255)
        
        # Calculate features that might indicate text presence
        contrast = np.std(np.array(gray_image))
        edges = gray_image.filter(ImageFilter.FIND_EDGES)
        edge_density = np.mean(np.array(edges))
        
        # Check for text-like patterns
        has_text_patterns = contrast > 50 and edge_density > 10
        
        if has_text_patterns:
            # Simulate text detection regions for feedback
            regions_count = int(edge_density / 5)  # Approximate number of text regions
            regions_count = min(max(1, regions_count), 10)  # Between 1 and 10
            
            # Create a helpful response for the user
            response = "I detect what appears to be text in this image. "
            
            if contrast > 70:
                response += "The text seems to have good contrast and should be readable with proper OCR. "
            else:
                response += "The text has low contrast which might make it difficult to read. "
                
            if regions_count > 5:
                response += "I detect multiple text regions or paragraphs. "
            else:
                response += "I detect what might be a few words or a short text passage. "
                
            response += "Without full OCR capabilities, I can't read the specific text content. "
            response += "For accurate text reading, you may need a dedicated OCR application or assistance."
            
            return response
        else:
            return "I don't detect clear text patterns in this image. The image may not contain readable text or the text may be too small, blurry, or low-contrast to detect. Please try again with a clearer image of the text."
    except Exception as e:
        return f"Error in text recognition: {str(e)}"

# Initialize labels file
load_or_create_labels()