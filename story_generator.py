import re
import os
import json
import logging
from typing import List, Dict, Any
from groq import Groq

# Configure logging
logger = logging.getLogger("WikiComicGenerator")


class StoryGenerator:
    def __init__(self, api_key: str, text_dir: str = "data/text"):
        """
        Initialize the Groq story generator
        
        Args:
            api_key: Groq API key
            text_dir: Directory to store generated text content
        """
        self.client = Groq(api_key=api_key)
        self.text_dir = text_dir
        self.create_text_directory()
        logger.info("StoryGenerator initialized with Groq client")

    def create_text_directory(self) -> None:
        """Create text directory for storing story content"""
        try:
            if not os.path.exists(self.text_dir):
                os.makedirs(self.text_dir)
                logger.info(f"Created text directory: {self.text_dir}")
        except Exception as e:
            logger.error(f"Failed to create text directory: {str(e)}")
            raise RuntimeError(f"Failed to create text directory: {str(e)}")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename
        
        Args:
            filename: Original filename string
            
        Returns:
            Sanitized filename safe for all operating systems
        """
        # Replace invalid characters with underscores
        sanitized = re.sub(r'[\\/*?:"<>|]', '_', filename)
        # Limit filename length
        return sanitized[:200]

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
        
        # Create prompt for the LLM (strict, production-ready, no extra text)
        prompt = f"""
        You are creating a professional comic book storyline for "{title}" strictly from the provided Wikipedia content. Follow the format EXACTLY and do not include any additional commentary.
        
        HARD REQUIREMENTS:
        - Target length: ~{word_count} words (±50 words)
        - 3 acts with clear transitions
        - Historically accurate; no invented facts
        - Use only details present in the provided content
        - If any important detail is uncertain or missing in the source, omit it rather than inventing
        
        FORMAT (FOLLOW EXACTLY):
        # {title}: Comic Storyline
        
        ## Overview
        [Exactly 2 sentences summarizing the core arc]
        
        ## Main Characters
        [3-5 character entries; each a single sentence with role and trait]
        
        ## Act 1: [Specific Title]
        [~{word_count // 3} words covering setup, stakes, and inciting event]
        
        ## Act 2: [Specific Title]
        [~{word_count // 3} words covering conflict, turning points, and developments]
        
        ## Act 3: [Specific Title]
        [~{word_count // 3} words covering resolution and lasting impact]
        
        ## Key Visuals
        [Exactly 5 bullet points describing scene-worthy visuals]
        
        SOURCE MATERIAL (use only this):
        {content}
        """
        
        try:
            # Generate storyline using Groq
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert comic book writer and historian who creates engaging, accurate, and visually compelling storylines based on real information."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.4,
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
        
        # Create prompt for the LLM (no dialog lines; concise visual-only prompts)
        prompt = f"""
        Based on the following comic storyline about "{title}", create EXACTLY {num_scenes} sequential scene prompts for image generation.

        REQUIREMENTS FOR EVERY SCENE:
        1. Strict narrative order from start to finish
        2. Visual description ONLY (no text, no captions, no speech, no voiceover)
        3. 50–80 words describing setting, characters, actions, framing, lighting
        4. Maintain character and setting consistency across scenes
        5. Adhere to the {comic_style} style characteristics
        6. Do NOT introduce new facts, characters, places, or events not present in the storyline

        STYLE PARAMETERS:
        - Comic Style: {comic_style} — {style_guidance}
        - Age Group: {age_group} — {age_guidance}
        - Education Level: {education_level} — {education_guidance}

        STORYLINE TO CONVERT (the only source of truth; no external inventions):
        {storyline}

        OUTPUT FORMAT (FOLLOW EXACTLY, NO EXTRA LINES):
        Scene [number]: [Specific scene title]
        Visual: [50–80 word, visual-only description; no text elements]
        Style: {comic_style} with [specific stylistic elements to emphasize]

        Produce EXACTLY {num_scenes} scenes.
        """
        
        try:
            # Generate scene prompts using Groq
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert comic artist who outputs concise, visual-only, production-ready scene prompts with zero on-image text."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.4,
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

    def save_story_content(self, title: str, storyline: str, scene_prompts: List[str], page_info: Dict[str, Any] = None) -> Dict[str, str]:
        """
        Save story content to text files for further processing
        
        Args:
            title: Title of the story
            storyline: Generated storyline
            scene_prompts: List of scene prompts
            page_info: Wikipedia page information (optional)
            
        Returns:
            Dictionary with file paths of saved content
        """
        try:
            # Sanitize title for filename
            safe_title = self.sanitize_filename(title)
            
            # Create story directory
            story_dir = os.path.join(self.text_dir, safe_title)
            if not os.path.exists(story_dir):
                os.makedirs(story_dir)
                logger.info(f"Created story directory: {story_dir}")
            
            file_paths = {}
            
            # Save storyline
            storyline_path = os.path.join(story_dir, f"{safe_title}_storyline.txt")
            with open(storyline_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title} - Comic Storyline\n\n")
                f.write(storyline)
            file_paths['storyline'] = storyline_path
            logger.info(f"Saved storyline to: {storyline_path}")
            
            # Save scene prompts
            scenes_path = os.path.join(story_dir, f"{safe_title}_scene_prompts.txt")
            with open(scenes_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title} - Scene Prompts\n\n")
                for i, prompt in enumerate(scene_prompts, 1):
                    f.write(f"## Scene {i}\n")
                    f.write(prompt)
                    f.write("\n\n" + "="*50 + "\n\n")
            file_paths['scenes'] = scenes_path
            logger.info(f"Saved scene prompts to: {scenes_path}")
            
            # Save page info as JSON for reference
            if page_info:
                page_info_path = os.path.join(story_dir, f"{safe_title}_page_info.json")
                with open(page_info_path, 'w', encoding='utf-8') as f:
                    json.dump(page_info, f, ensure_ascii=False, indent=2)
                file_paths['page_info'] = page_info_path
                logger.info(f"Saved page info to: {page_info_path}")
            
            # Create combined content file
            combined_path = os.path.join(story_dir, f"{safe_title}_combined.txt")
            with open(combined_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title} - Complete Story Content\n\n")
                f.write("## Storyline\n")
                f.write(storyline)
                f.write("\n\n" + "="*80 + "\n\n")
                f.write("## Scene Prompts\n\n")
                for i, prompt in enumerate(scene_prompts, 1):
                    f.write(f"### Scene {i}\n")
                    f.write(prompt)
                    f.write("\n\n" + "-"*50 + "\n\n")
            file_paths['combined'] = combined_path
            logger.info(f"Saved combined content to: {combined_path}")
            
            return file_paths
            
        except Exception as e:
            logger.error(f"Failed to save story content: {str(e)}")
            return {}

    def generate_and_save_story(self, title: str, content: str, target_length: str = "medium",
                               comic_style: str = "western comic", num_scenes: int = 10,
                               age_group: str = "general", education_level: str = "standard",
                               page_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate complete story and save all content to text files
        
        Args:
            title: Title of the story
            content: Wikipedia content
            target_length: Desired length of the story
            comic_style: Selected comic art style
            num_scenes: Number of scenes to generate
            age_group: Target age group
            education_level: Education level for content complexity
            page_info: Wikipedia page information (optional)
            
        Returns:
            Dictionary containing generated content and file paths
        """
        logger.info(f"Generating complete story for '{title}'")
        
        # Generate storyline
        storyline = self.generate_comic_storyline(title, content, target_length)
        
        # Generate scene prompts
        scene_prompts = self.generate_scene_prompts(
            title, storyline, comic_style, num_scenes, age_group, education_level
        )
        
        # Save all content to text files
        file_paths = self.save_story_content(title, storyline, scene_prompts, page_info)
        
        return {
            "title": title,
            "storyline": storyline,
            "scene_prompts": scene_prompts,
            "file_paths": file_paths
        }
