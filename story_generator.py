import re
import logging
from typing import List
from groq import Groq

# Configure logging
logger = logging.getLogger("WikiComicGenerator")


class StoryGenerator:
    def __init__(self, api_key: str):
        """
        Initialize the Groq story generator
        
        Args:
            api_key: Groq API key
        """
        self.client = Groq(api_key=api_key)
        logger.info("StoryGenerator initialized with Groq client")

    def generate_comic_storyline(self, title: str, content: str, target_length: str = "medium") -> str:
        """
        Generate a comic storyline from Wikipedia content
        
        Args:
            title: Title of the Wikipedia article
            content: Content of the Wikipedia article
            target_length: Desired length of the story (short, medium, long)
            
        Returns:
            Generated comic storyline
        """
        logger.info(f"Generating comic storyline for: {title} with target length: {target_length}")
        
        # Map target length to approximate word count
        length_map = {
            "short": 500,
            "medium": 1000,
            "long": 2000
        }
        
        word_count = length_map.get(target_length, 1000)
        
        # Check content length and truncate if necessary to avoid token limits
        max_chars = 15000
        if len(content) > max_chars:
            logger.info(f"Content too long ({len(content)} chars), truncating to {max_chars} chars")
            content = content[:max_chars] + "..."
        
        # Create prompt for the LLM
        prompt = f"""
        Create an engaging and detailed comic book storyline based on the following Wikipedia article about "{title}".
        
        The storyline should:
        1. Be approximately {word_count} words
        2. Capture the most important facts and details from the article
        3. Have a clear beginning, middle, and end
        4. Include vivid descriptions of key scenes suitable for comic panels
        5. Feature compelling characters based on real figures from the topic
        6. Include dialogue suggestions for major moments
        7. Be organized into distinct scenes or chapters
        8. Balance educational content with entertainment value
        
        Here is the Wikipedia content to base your storyline on:
        
        {content}
        
        FORMAT YOUR RESPONSE AS:
        # {title}: Comic Storyline
        
        ## Overview
        [Brief overview of the storyline]
        
        ## Main Characters
        [List of main characters with short descriptions]
        
        ## Act 1: [Title]
        [Detailed storyline for Act 1 with scene descriptions and key dialogue]
        
        ## Act 2: [Title]
        [Detailed storyline for Act 2 with scene descriptions and key dialogue]
        
        ## Act 3: [Title]
        [Detailed storyline for Act 3 with scene descriptions and key dialogue]
        
        ## Key Visuals
        [Suggestions for important visual elements to include in the comic]
        """
        
        try:
            # Generate storyline using Groq
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert comic book writer and historian who creates engaging, accurate, and visually compelling storylines based on real information."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9
            )
            
            storyline = response.choices[0].message.content
            logger.info(f"Successfully generated comic storyline for: {title}")
            
            return storyline
            
        except Exception as e:
            logger.error(f"Failed to generate storyline: {str(e)}")
            return f"Error generating storyline: {str(e)}"

    def generate_scene_prompts(self, title: str, storyline: str, comic_style: str, num_scenes: int = 10, 
                              age_group: str = "general", education_level: str = "standard") -> List[str]:
        """
        Generate detailed scene prompts for comic panels based on the storyline
        
        Args:
            title: Title of the article
            storyline: Generated comic storyline
            comic_style: Selected comic art style
            num_scenes: Number of scene prompts to generate (default 10)
            age_group: Target age group (kids, teens, general, adult)
            education_level: Education level for content complexity (basic, standard, advanced)
            
        Returns:
            List of scene prompts for image generation
        """
        logger.info(f"Generating {num_scenes} scene prompts for comic in {comic_style} style, targeting {age_group} with {education_level} education level")
        
        # Prepare style-specific guidance based on comic style
        style_guidance = {
            "manga": "Use manga-specific visual elements like speed lines, expressive emotions, and distinctive panel layouts. Character eyes should be larger, with detailed hair and simplified facial features. Use black and white with screen tones for shading.",
            "superhero": "Use bold colors, dynamic poses with exaggerated anatomy, dramatic lighting, and action-oriented compositions. Include detailed musculature and costumes with strong outlines and saturated colors.",
            "cartoon": "Use simplified, exaggerated character features with bold outlines. Employ bright colors, expressive faces, and playful physics. Include visual effects like motion lines and impact stars.",
            "noir": "Use high-contrast black and white or muted colors with dramatic shadows. Feature low-key lighting, rain effects, and urban settings. Characters should have realistic proportions with hardboiled expressions.",
            "european": "Use detailed backgrounds with architectural precision and clear line work. Character designs should be semi-realistic with consistent proportions. Panel layouts should be regular and methodical.",
            "indie": "Use unconventional art styles with personal flair. Panel layouts can be experimental and fluid. Line work may be sketchy or deliberately unpolished. Colors can be watercolor-like or limited palette.",
            "retro": "Use halftone dots for shading, slightly faded colors, and classic panel compositions. Character designs should reflect the comics of the 50s-70s with simplified but distinctive features.",
        }.get(comic_style.lower(), f"Incorporate distinctive visual elements of {comic_style} style consistently in all panels.")
        
        # Prepare age-appropriate guidance
        age_guidance = {
            "kids": "Use simple, clear vocabulary and straightforward concepts. Avoid complex themes, frightening imagery, or adult situations. Characters should be expressive and appealing. Educational content should be presented in an engaging, accessible way.",
            "teens": "Use relatable language and themes important to adolescents. Include more nuanced emotional content and moderate complexity. Educational aspects can challenge readers while remaining accessible.",
            "general": "Balance accessibility with depth. Include some complexity in both themes and visuals while remaining broadly appropriate. Educational content should be informative without being overly technical.",
            "adult": "Include sophisticated themes, complex characterizations, and nuanced storytelling. Educational content can be presented with full complexity and technical detail where appropriate."
        }.get(age_group.lower(), "Create content appropriate for a general audience with balanced accessibility and depth.")
        
        # Prepare education level guidance
        education_guidance = {
            "basic": "Use simple vocabulary, clear explanations, and focus on foundational concepts. Break down complex ideas into easily digestible components with examples.",
            "standard": "Use moderate vocabulary and present concepts with appropriate depth for general understanding. Balance educational content with narrative engagement.",
            "advanced": "Use field-specific terminology where appropriate and explore concepts in depth. Present nuanced details and sophisticated analysis of the subject matter."
        }.get(education_level.lower(), "Present educational content with balanced complexity suitable for interested general readers.")
        
        # Create prompt for the LLM
        prompt = f"""
        Based on the following comic storyline about "{title}", create exactly {num_scenes} sequential scene prompts for generating comic panels.

        Each scene prompt MUST:
        1. Follow a logical narrative sequence from beginning to end
        2. Include DETAILED visual descriptions of the scene, setting, characters, and actions
        3. Include ZERO text elements in the image (no dialogue, no captions, no narrator/voiceover). The generator should leave clean composition space but must not render any text.
        4. Maintain character consistency throughout all scenes
        5. Be self-contained but connect logically to the previous and next scenes
        6. Incorporate specific visual elements from the {comic_style} comic art style

        IMPORTANT PARAMETERS TO FOLLOW:
        - Comic Style: {comic_style} — {style_guidance}
        - Age Group: {age_group} — {age_guidance}
        - Education Level: {education_level} — {education_guidance}

        Here is the comic storyline to convert into scene prompts:
        
        {storyline}
        
        FORMAT EACH SCENE PROMPT AS:
        Scene [number]: [Brief scene title]
        Visual: [Extremely detailed visual description of the scene including setting, characters, positions, expressions, actions, and any specific visual elements. Do NOT include any text, speech, captions, or on-screen words. Leave clean space where speech bubbles could go, but render no text.]
        Style: {comic_style} style with [specific stylistic elements to emphasize].
        
        PROVIDE EXACTLY {num_scenes} SCENES IN SEQUENTIAL ORDER.
        MAKE SURE EACH SCENE HAS AT LEAST ONE DIALOG LINE, as these will be directly included in speech bubbles.
        ENSURE ALL DIALOG TEXT IS GRAMMATICALLY CORRECT and appropriate for the target audience.
        SCENE DESCRIPTIONS MUST BE EXTREMELY DETAILED to ensure the image generator can create accurate images.
        """
        
        try:
            # Generate scene prompts using Groq
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert comic book artist and writer who creates detailed, engaging scene descriptions for comic panels with consistent characters and storylines. You always ensure dialog is grammatically correct and include specific dialog text for each scene."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=4000,
                top_p=0.9
            )
            
            scenes_text = response.choices[0].message.content
            
            # Process the text to extract individual scene prompts
            scene_prompts = []
            scene_pattern = re.compile(r'Scene \d+:.*?(?=Scene \d+:|$)', re.DOTALL)
            matches = scene_pattern.findall(scenes_text)
            
            for match in matches:
                # Remove any dialog lines to ensure no text renders
                cleaned = re.sub(r'^\s*Dialog\s*:\s*.*$', '', match, flags=re.IGNORECASE | re.MULTILINE)
                # Also remove narrator/caption/voiceover style lines
                cleaned = re.sub(r'^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$', '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
                scene_prompts.append(cleaned.strip())
            
            # If we didn't get enough scenes, pad with generic ones WITHOUT any text
            while len(scene_prompts) < num_scenes:
                scene_num = len(scene_prompts) + 1
                scene_prompts.append(f"""Scene {scene_num}: Additional scene from {title}
                Visual: A character from the story stands in a relevant setting from {title}, looking thoughtful. No on-screen text, no captions, no speech.
                Style: {comic_style} style with appropriate elements for {age_group} audience.""")
            
            # If we got too many scenes, truncate
            scene_prompts = scene_prompts[:num_scenes]
            
            # Validate each scene prompt to ensure it contains NO dialog/text
            validated_prompts = []
            for i, prompt in enumerate(scene_prompts):
                scene_num = i + 1
                
                # Strip any remaining dialog-like lines if present (ensure no text artifacts)
                prompt = re.sub(r'^\s*Dialog\s*:\s*.*$', '', prompt, flags=re.IGNORECASE | re.MULTILINE)
                prompt = re.sub(r'^\s*(Narrator|Caption|Voiceover|Voice-over|Announcer)\s*:\s*.*$', '', prompt, flags=re.IGNORECASE | re.MULTILINE)
                # Also remove any quoted lines that might be interpreted as dialog
                prompt = re.sub(r'^\s*"[^"]+"\s*$', '', prompt, flags=re.MULTILINE)
                
                validated_prompts.append(prompt)
            
            logger.info(f"Successfully generated {len(validated_prompts)} scene prompts")
            return validated_prompts
            
        except Exception as e:
            logger.error(f"Failed to generate scene prompts: {str(e)}")
            return [f"Error generating scene prompt: {str(e)}"]
