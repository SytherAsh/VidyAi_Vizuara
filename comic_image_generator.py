import os
import re
import time
import logging
import requests
from typing import List

# Configure logging
logger = logging.getLogger("WikiComicGenerator")


class ComicImageGenerator:
    def __init__(self, hf_token: str, model_url: str = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev", 
                 fallback_model_url: str = None):
        """
        Initialize the Comic Image Generator
        
        Args:
            hf_token: Hugging Face API token
            model_url: URL for the primary image generation model
            fallback_model_url: URL for a fallback model (if primary fails)
        """
        self.hf_token = hf_token
        self.model_url = model_url
        self.fallback_model_url = fallback_model_url
        self.headers = {"Authorization": f"Bearer {hf_token}"}
        logger.info("ComicImageGenerator initialized with Hugging Face token")
        
        # Test API token validity at initialization
        self._test_api_token()
        
    def _test_api_token(self):
        """Test if the API token is valid and has available quota"""
        try:
            # Make a small request to check token validity
            test_response = requests.get("https://api-inference.huggingface.co/status", 
                                        headers=self.headers, timeout=10)
            
            if test_response.status_code != 200:
                logger.warning(f"API token validation failed with status code: {test_response.status_code}")
                logger.warning("You may encounter issues with image generation due to token limitations")
            else:
                logger.info("API token validated successfully")
                
        except Exception as e:
            logger.warning(f"Could not validate API token: {str(e)}")

    def _handle_payment_required_error(self, scene_num: int):
        """Handle 402 Payment Required errors specifically"""
        logger.error(f"Payment required error for scene {scene_num}. This indicates:")
        logger.error("1. Your API token has run out of free quota")
        logger.error("2. The model you're using requires payment")
        logger.error("3. There may be billing issues with your Hugging Face account")
        logger.error("Please check your Hugging Face account settings or consider using a free model")

    def _extract_dialog_from_prompt(self, scene_prompt: str) -> list:
        """Extract dialog lines from the scene prompt for adding to the image"""
        dialog_lines = []
        
        # Match lines starting with "Dialog:" followed by character name and dialog
        dialog_pattern = re.compile(r'Dialog:\s*([^:]+?):\s*"([^"]+)"', re.IGNORECASE)
        matches = dialog_pattern.findall(scene_prompt)
        
        narrator_like_names = {"narrator", "caption", "voiceover", "voice-over", "announcer"}
        for character, line in matches:
            if character.strip().lower() in narrator_like_names:
                continue
            dialog_lines.append((character.strip(), line.strip()))
        
        # If no dialog found with the structured format, try to extract any quoted text
        if not dialog_lines:
            # Look for quoted text with character attribution
            alt_pattern = re.compile(r'([^:]+?):\s*"([^"]+)"')
            matches = alt_pattern.findall(scene_prompt)
            for character, line in matches:
                character_lower = character.lower()
                if (
                    "style" not in character_lower
                    and "visual" not in character_lower
                    and character_lower.strip() not in narrator_like_names
                ):
                    dialog_lines.append((character.strip(), line.strip()))
        
        # If still no dialog, add a generic one
        if not dialog_lines:
            dialog_lines.append(("Character", "This is an important moment in our story."))
            logger.warning("No dialog found in scene prompt, using generic dialog")
        
        return dialog_lines

    def _enhance_scene_prompt(self, scene_prompt: str) -> str:
        """Enhance the scene prompt to improve image generation accuracy"""
        # Remove narrator/caption/voiceover lines from the prompt entirely
        cleaned_prompt = re.sub(
            r"^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$",
            "",
            scene_prompt,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        # Extract the main visual description
        visual_match = re.search(r'Visual:\s*(.+?)(?=\nDialog:|Style:|$)', cleaned_prompt, re.DOTALL)
        
        if visual_match:
            visual_description = visual_match.group(1).strip()
            
            # Extract style information
            style_match = re.search(r'Style:\s*(.+?)$', cleaned_prompt, re.DOTALL)
            style_info = style_match.group(1).strip() if style_match else ""
            
            # Create an enhanced prompt focused on the visual elements with technical specs
            enhanced_prompt = f"""
            Create a high-quality comic panel with these exact specifications:
            
            Visual content:
            {visual_description}
            
            Technical requirements:
            - Aspect ratio: 16:9 landscape
            - Resolution: high definition, crisp details
            - Style: {style_info}
            - Composition: clear, balanced framing; no on-image text
            - Lighting: cinematic with clear highlights and shadows
            - Colors: vibrant but not oversaturated
            - Character consistency: match designs across panels
            
            Grounding:
            - Depict ONLY the elements present in the "Visual content" above
            - Do NOT introduce new characters, symbols, or text
            
            Quality standards:
            - Professional comic art quality
            - Clear expressions and readable poses
            - Detailed but clean backgrounds
            - Consistent art style with prior panels
            - Absolutely no text, captions, or speech bubbles in the image
            """
            
            return enhanced_prompt
        
        return scene_prompt  # Return original if we couldn't extract visual description

    def _add_dialog_bubbles(self, image_path: str, dialog_lines: list) -> str:
        """Add dialog bubbles to the generated image"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Open the image
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # Try to use a system font, fall back to default if not available
            try:
                font = ImageFont.truetype("Arial", 20)
                name_font = ImageFont.truetype("Arial", 16)
            except IOError:
                font = ImageFont.load_default()
                name_font = ImageFont.load_default()
            
            # Calculate positions for dialog bubbles
            max_bubbles = min(3, len(dialog_lines))  # Limit to 3 bubbles maximum
            img_width, img_height = img.size
            
            # Spacing parameters
            bubble_padding = 10
            text_max_width = int(img_width * 0.8)
            line_spacing = 25
            
            for i in range(max_bubbles):
                character, line = dialog_lines[i]
                
                # Calculate bubble position - stagger them vertically
                vertical_position = int(img_height * 0.1) + (i * int(img_height * 0.25))
                
                # Word wrap the dialog text to fit in the bubble
                words = line.split()
                lines_of_text = []
                current_line = ""
                
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    text_width = font.getbbox(test_line)[2] if hasattr(font, 'getbbox') else font.getsize(test_line)[0]
                    
                    if text_width <= text_max_width:
                        current_line = test_line
                    else:
                        lines_of_text.append(current_line)
                        current_line = word
                
                if current_line:
                    lines_of_text.append(current_line)
                
                # Calculate bubble dimensions
                bubble_height = len(lines_of_text) * line_spacing + bubble_padding * 2
                bubble_width = text_max_width + bubble_padding * 2
                
                # Draw bubble background
                bubble_x = (img_width - bubble_width) // 2
                bubble_y = vertical_position
                
                # Draw semi-transparent white bubble background
                draw.rectangle(
                    [(bubble_x, bubble_y), (bubble_x + bubble_width, bubble_y + bubble_height)],
                    fill=(255, 255, 255, 200),
                    outline=(0, 0, 0)
                )
                
                # Draw character name above bubble
                name_width = name_font.getbbox(character)[2] if hasattr(name_font, 'getbbox') else name_font.getsize(character)[0]
                name_x = bubble_x + (bubble_width - name_width) // 2
                name_y = bubble_y - 20
                
                # Draw semi-transparent background for name
                draw.rectangle(
                    [(name_x - 5, name_y), (name_x + name_width + 5, name_y + 20)],
                    fill=(200, 200, 255, 200),
                    outline=(0, 0, 0)
                )
                
                draw.text((name_x, name_y), character, fill=(0, 0, 0), font=name_font)
                
                # Draw dialog text
                for j, text_line in enumerate(lines_of_text):
                    line_width = font.getbbox(text_line)[2] if hasattr(font, 'getbbox') else font.getsize(text_line)[0]
                    text_x = bubble_x + (bubble_width - line_width) // 2
                    text_y = bubble_y + bubble_padding + j * line_spacing
                    draw.text((text_x, text_y), text_line, fill=(0, 0, 0), font=font)
            
            # Save the modified image
            img.save(image_path)
            logger.info(f"Added {max_bubbles} dialog bubbles to image")
            return image_path
            
        except Exception as e:
            logger.error(f"Failed to add dialog bubbles: {str(e)}")
            return image_path

    def generate_comic_image(self, scene_prompt: str, output_path: str, scene_num: int, 
                           attempt: int = 1, max_retries: int = 3, timeout: int = 120,
                           use_fallback: bool = False) -> bool:
        """
        Generate a comic image based on a scene prompt
        
        Args:
            scene_prompt: Textual description of the scene
            output_path: Path to save the generated image
            scene_num: Scene number for logging
            attempt: Current attempt number
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
            use_fallback: Whether to use the fallback model
            
        Returns:
            Boolean indicating success
        """
        current_model_url = self.fallback_model_url if use_fallback else self.model_url
        
        if use_fallback and not self.fallback_model_url:
            logger.warning("Fallback requested but no fallback model URL configured")
            return False
        
        # Remove all dialog/narrator/caption lines to prevent any text rendering
        scene_prompt = re.sub(r'^\s*Dialog\s*:\s*.*$', '', scene_prompt, flags=re.IGNORECASE | re.MULTILINE)
        scene_prompt = re.sub(r'^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$', '', scene_prompt, flags=re.IGNORECASE | re.MULTILINE)
        
        # Enhance the scene prompt for better image generation
        enhanced_prompt = self._enhance_scene_prompt(scene_prompt)
            
        payload = {"inputs": enhanced_prompt, "options": {"wait_for_model": True}}
        logger.info(f"Generating image for scene {scene_num}, attempt {attempt}" + 
                   (f" using fallback model" if use_fallback else ""))
        
        try:
            response = requests.post(current_model_url, headers=self.headers, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                logger.info(f"Successfully generated image for scene {scene_num}, saved to {output_path}")
                
                # Intentionally do not add any bubbles or text overlays
                return True
                
            elif response.status_code == 402:
                logger.warning(f"Payment required error for scene {scene_num}, attempt {attempt}")
                self._handle_payment_required_error(scene_num)
                
                # Try fallback model if available and not already using it
                if self.fallback_model_url and not use_fallback:
                    logger.info(f"Attempting to use fallback model for scene {scene_num}")
                    return self.generate_comic_image(scene_prompt, output_path, scene_num, 
                                                  attempt=1, max_retries=max_retries, 
                                                  use_fallback=True)
                elif attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1})")
                    time.sleep(wait_time)
                    return self.generate_comic_image(scene_prompt, output_path, scene_num, 
                                                  attempt + 1, max_retries, use_fallback=use_fallback)
                else:
                    logger.error(f"Max retries reached for scene {scene_num} with payment errors")
                    return self._try_placeholder_image(output_path, scene_num)
            else:
                logger.warning(f"Error generating image for scene {scene_num}, attempt {attempt}: {response.status_code}")
                
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1})")
                    time.sleep(wait_time)
                    return self.generate_comic_image(scene_prompt, output_path, scene_num, 
                                                  attempt + 1, max_retries, use_fallback=use_fallback)
                else:
                    logger.error(f"Max retries reached for scene {scene_num}")
                    return self._try_placeholder_image(output_path, scene_num)
                    
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for scene {scene_num}, attempt {attempt}: {str(e)}")
            
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds... (Attempt {attempt + 1})")
                time.sleep(wait_time)
                return self.generate_comic_image(scene_prompt, output_path, scene_num, 
                                              attempt + 1, max_retries, use_fallback=use_fallback)
            else:
                logger.error(f"Max retries reached for scene {scene_num}")
                return self._try_placeholder_image(output_path, scene_num)
    
    def _try_placeholder_image(self, output_path: str, scene_num: int) -> bool:
        """Generate a placeholder image with scene description when all else fails"""
        try:
            # Use PIL to create a simple placeholder image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image with a light background
            img = Image.new('RGB', (800, 600), color=(245, 245, 245))
            draw = ImageDraw.Draw(img)
            
            # Add text explaining this is a placeholder
            main_text = f"Scene {scene_num}\nImage generation failed\nPlease check your Hugging Face token"
            
            # Try to use a system font, fall back to default if not available
            try:
                font = ImageFont.truetype("Arial", 32)
                dialog_font = ImageFont.truetype("Arial", 24)
            except IOError:
                font = ImageFont.load_default()
                dialog_font = ImageFont.load_default()
                
            # Calculate text position to center it
            text_width, text_height = draw.textsize(main_text, font=font) if hasattr(draw, 'textsize') else (300, 100)
            position = ((800 - text_width) // 2, (600 - text_height) // 2 - 100)
            
            # Draw text on image
            draw.text(position, main_text, fill=(0, 0, 0), font=font)
            
            # Do not add any dialog onto the placeholder image
            
            # Save the image
            img.save(output_path)
            logger.info(f"Created placeholder image for scene {scene_num} with dialog")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create placeholder image: {str(e)}")
            return False

    def generate_comic_strip(self, scene_prompts: List[str], output_dir: str, comic_title: str,
                           fallback_free_model: str = None) -> List[str]:
        """
        Generate a full comic strip from scene prompts
        
        Args:
            scene_prompts: List of scene prompts
            output_dir: Directory to save generated images
            comic_title: Title of the comic for filenames
            fallback_free_model: URL for a free model to use as fallback
            
        Returns:
            List of paths to generated images
        """
        logger.info(f"Generating comic strip with {len(scene_prompts)} scenes")
        
        # Set fallback model if provided
        if fallback_free_model:
            self.fallback_model_url = fallback_free_model
            logger.info(f"Set fallback model to: {fallback_free_model}")
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        
        # Create a specific directory for this comic
        safe_title = re.sub(r'[\\/*?:"<>|]', '_', comic_title)
        comic_dir = os.path.join(output_dir, safe_title)
        if not os.path.exists(comic_dir):
            os.makedirs(comic_dir)
            logger.info(f"Created comic directory: {comic_dir}")
        
        # Generate images for each scene
        image_paths = []
        payment_errors_count = 0
        
        for i, scene_prompt in enumerate(scene_prompts):
            scene_num = i + 1
            output_path = os.path.join(comic_dir, f"scene_{scene_num}.jpg")
            
            success = self.generate_comic_image(scene_prompt, output_path, scene_num)
            
            if success:
                image_paths.append(output_path)
            else:
                logger.warning(f"Failed to generate image for scene {scene_num}")
                payment_errors_count += 1
                
            # If we've had multiple payment errors in a row, it's likely a persistent issue
            if payment_errors_count >= 3 and self.fallback_model_url is None:
                logger.warning("Multiple payment errors detected. Suggesting free model alternatives.")
                logger.warning("Consider using one of these free models:")
                logger.warning("- https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1")
                logger.warning("- https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5")
                
                # Prompt if user wants to retry with a free model
                self.fallback_model_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
                logger.info(f"Automatically setting fallback model to: {self.fallback_model_url}")
        
        logger.info(f"Generated {len(image_paths)} out of {len(scene_prompts)} scenes")
        return image_paths
