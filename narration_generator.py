import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

# Configure logging
logger = logging.getLogger("WikiComicGenerator")


class NarrationGenerator:
    def __init__(self, api_key: str, text_dir: str = "data/text", narration_dir: str = "data/narration"):
        """
        Initialize the Narration Generator
        
        Args:
            api_key: Groq API key
            text_dir: Directory containing story text files
            narration_dir: Directory to store generated narration files
        """
        self.client = Groq(api_key=api_key)
        self.text_dir = text_dir
        self.narration_dir = narration_dir
        self.create_narration_directory()
        logger.info("NarrationGenerator initialized with Groq client")

    def create_narration_directory(self) -> None:
        """Create narration directory for storing generated narration files"""
        try:
            if not os.path.exists(self.narration_dir):
                os.makedirs(self.narration_dir)
                logger.info(f"Created narration directory: {self.narration_dir}")
        except Exception as e:
            logger.error(f"Failed to create narration directory: {str(e)}")
            raise RuntimeError(f"Failed to create narration directory: {str(e)}")

    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a string to be used as a filename
        
        Args:
            filename: Original filename string
            
        Returns:
            Sanitized filename safe for all operating systems
        """
        # Replace invalid characters with underscores
        sanitized = filename.replace('\\', '_').replace('/', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_').replace(':', '_')
        # Limit filename length
        return sanitized[:200]

    def load_story_content(self, title: str) -> Dict[str, Any]:
        """
        Load story content from text files
        
        Args:
            title: Title of the story
            
        Returns:
            Dictionary containing loaded story content
        """
        try:
            safe_title = self.sanitize_filename(title)
            story_dir = os.path.join(self.text_dir, safe_title)
            
            if not os.path.exists(story_dir):
                logger.error(f"Story directory not found: {story_dir}")
                return {}
            
            content = {}
            
            # Load storyline
            storyline_path = os.path.join(story_dir, f"{safe_title}_storyline.txt")
            if os.path.exists(storyline_path):
                with open(storyline_path, 'r', encoding='utf-8') as f:
                    content['storyline'] = f.read()
            
            # Load scene prompts
            scenes_path = os.path.join(story_dir, f"{safe_title}_scene_prompts.txt")
            if os.path.exists(scenes_path):
                with open(scenes_path, 'r', encoding='utf-8') as f:
                    content['scene_prompts'] = f.read()
            
            # Load page info
            page_info_path = os.path.join(story_dir, f"{safe_title}_page_info.json")
            if os.path.exists(page_info_path):
                with open(page_info_path, 'r', encoding='utf-8') as f:
                    content['page_info'] = json.load(f)
            
            # Load combined content
            combined_path = os.path.join(story_dir, f"{safe_title}_combined.txt")
            if os.path.exists(combined_path):
                with open(combined_path, 'r', encoding='utf-8') as f:
                    content['combined'] = f.read()
            
            logger.info(f"Successfully loaded story content for: {title}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load story content: {str(e)}")
            return {}

    def generate_scene_narration(self, title: str, scene_prompt: str, scene_number: int, 
                                narration_style: str = "dramatic", voice_tone: str = "engaging",
                                target_seconds: int = 0, min_words: int = 18, max_words: int = 28) -> str:
        """
        Generate narration for a specific scene
        
        Args:
            title: Title of the story
            scene_prompt: Scene prompt text
            scene_number: Number of the scene
            narration_style: Style of narration (dramatic, educational, storytelling, documentary)
            voice_tone: Tone of voice (engaging, serious, playful, informative)
            
        Returns:
            Generated narration text for the scene
        """
        logger.info(f"Generating narration for scene {scene_number} of '{title}'")
        
        # Style-specific guidance
        style_guidance = {
            "dramatic": "Use dramatic language with vivid descriptions, emotional depth, and cinematic pacing. Build tension and excitement.",
            "educational": "Use clear, informative language that explains concepts and provides context. Focus on learning and understanding.",
            "storytelling": "Use traditional storytelling techniques with engaging narrative flow, character development, and plot progression.",
            "documentary": "Use factual, objective language with historical context and detailed explanations. Present information professionally."
        }.get(narration_style.lower(), "Use engaging and clear language to describe the scene.")
        
        # Voice tone guidance
        tone_guidance = {
            "engaging": "Use an enthusiastic, captivating voice that draws the audience in and maintains their interest.",
            "serious": "Use a respectful, solemn tone appropriate for important historical or serious topics.",
            "playful": "Use a light, fun tone that makes the content enjoyable and accessible, especially for younger audiences.",
            "informative": "Use a clear, professional tone that focuses on delivering information effectively."
        }.get(voice_tone.lower(), "Use a clear and engaging tone.")
        
        # Determine word range based on target seconds if provided (heuristic ~2.5 wps)
        if target_seconds and target_seconds > 0:
            approx_words = int(target_seconds * 2.5)
            lo = max(min_words, approx_words - 4)
            hi = max(max_words, approx_words + 4)
        else:
            lo = min_words
            hi = max_words

        # Create prompt for narration generation (short, reel-style)
        prompt = f"""
        Create a concise, captivating voice-over for scene {scene_number} of "{title}". Keep it short like a social media reel narration.
        
        STRICT REQUIREMENTS:
        - EXACTLY 2 sentences
        - TOTAL {lo}–{hi} words
        - Punchy, cinematic, and engaging
        - Complement the visuals without repeating them verbatim
        - Ground strictly in the provided STORYLINE and SCENE PROMPT
        - Do NOT introduce facts, characters, or events not present in the sources
        - If a detail is uncertain, omit it rather than inventing
        
        STYLE:
        - Style: {narration_style} - {style_guidance}
        - Tone: {voice_tone} - {tone_guidance}
        
        STORYLINE (source of truth):
        {self.load_story_content(title).get('storyline', '')}
        
        SCENE PROMPT (visual context):
        {scene_prompt}
        
        Output exactly 2 sentences totaling {lo}–{hi} words. No extra text.
        """
        
        try:
            # Generate narration using Groq
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an expert narrator and storyteller who creates compelling, engaging narration for visual media. You excel at creating voice-over scripts that enhance storytelling and provide meaningful context."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.3,
                max_tokens=500,
                top_p=0.9
            )
            
            narration = response.choices[0].message.content.strip()
            logger.info(f"Successfully generated narration for scene {scene_number}")
            
            return narration
            
        except Exception as e:
            logger.error(f"Failed to generate narration for scene {scene_number}: {str(e)}")
            return f"Error generating narration: {str(e)}"

    def generate_all_scene_narrations(self, title: str, narration_style: str = "dramatic", 
                                    voice_tone: str = "engaging") -> Dict[str, Any]:
        """
        Generate narration for all scenes of a story
        
        Args:
            title: Title of the story
            narration_style: Style of narration
            voice_tone: Tone of voice
            
        Returns:
            Dictionary containing all generated narrations and metadata
        """
        logger.info(f"Generating narrations for all scenes of '{title}'")
        
        # Load story content
        story_content = self.load_story_content(title)
        if not story_content:
            logger.error(f"Could not load story content for: {title}")
            return {}
        
        # Parse scene prompts from the loaded content
        scene_prompts = self._parse_scene_prompts(story_content.get('scene_prompts', ''))
        
        if not scene_prompts:
            logger.error(f"No scene prompts found for: {title}")
            return {}
        
        # Generate narration for each scene
        narrations = {}
        for i, scene_prompt in enumerate(scene_prompts, 1):
            narration = self.generate_scene_narration(
                title, scene_prompt, i, narration_style, voice_tone
            )
            narrations[f"scene_{i}"] = {
                "scene_number": i,
                "narration": narration,
                "scene_prompt": scene_prompt
            }
        
        # Save narrations to files
        file_paths = self._save_narrations(title, narrations, narration_style, voice_tone)
        
        result = {
            "title": title,
            "narration_style": narration_style,
            "voice_tone": voice_tone,
            "total_scenes": len(scene_prompts),
            "narrations": narrations,
            "file_paths": file_paths
        }
        
        logger.info(f"Successfully generated {len(scene_prompts)} narrations for '{title}'")
        return result

    def _parse_scene_prompts(self, scene_prompts_text: str) -> List[str]:
        """
        Parse individual scene prompts from the loaded text
        
        Args:
            scene_prompts_text: Raw text containing scene prompts
            
        Returns:
            List of individual scene prompts
        """
        try:
            # Split by scene markers
            scenes = []
            lines = scene_prompts_text.split('\n')
            current_scene = []
            
            for line in lines:
                if line.strip().startswith('## Scene'):
                    if current_scene:
                        scenes.append('\n'.join(current_scene).strip())
                    current_scene = [line]
                elif line.strip().startswith('==='):
                    if current_scene:
                        scenes.append('\n'.join(current_scene).strip())
                        current_scene = []
                elif current_scene:
                    current_scene.append(line)
            
            # Add the last scene if exists
            if current_scene:
                scenes.append('\n'.join(current_scene).strip())
            
            # Filter out empty scenes
            scenes = [scene for scene in scenes if scene.strip()]
            
            logger.info(f"Parsed {len(scenes)} scene prompts")
            return scenes
            
        except Exception as e:
            logger.error(f"Failed to parse scene prompts: {str(e)}")
            return []

    def _save_narrations(self, title: str, narrations: Dict[str, Any], 
                        narration_style: str, voice_tone: str) -> Dict[str, str]:
        """
        Save generated narrations to files
        
        Args:
            title: Title of the story
            narrations: Dictionary containing all narrations
            narration_style: Style of narration used
            voice_tone: Tone of voice used
            
        Returns:
            Dictionary with file paths of saved narrations
        """
        try:
            safe_title = self.sanitize_filename(title)
            narration_story_dir = os.path.join(self.narration_dir, safe_title)
            
            if not os.path.exists(narration_story_dir):
                os.makedirs(narration_story_dir)
                logger.info(f"Created narration directory: {narration_story_dir}")
            
            file_paths = {}
            
            # Save individual scene narrations
            for scene_key, scene_data in narrations.items():
                scene_num = scene_data['scene_number']
                narration_text = scene_data['narration']
                scene_prompt = scene_data['scene_prompt']
                
                scene_file = os.path.join(narration_story_dir, f"scene_{scene_num}_narration.txt")
                with open(scene_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Scene {scene_num} Narration - {title}\n\n")
                    f.write(f"**Style:** {narration_style}\n")
                    f.write(f"**Tone:** {voice_tone}\n\n")
                    f.write("## Narration Text\n")
                    f.write(narration_text)
                    f.write("\n\n" + "="*50 + "\n\n")
                    f.write("## Original Scene Prompt\n")
                    f.write(scene_prompt)
                
                file_paths[scene_key] = scene_file
            
            # Save complete narration file
            complete_file = os.path.join(narration_story_dir, f"{safe_title}_complete_narration.txt")
            with open(complete_file, 'w', encoding='utf-8') as f:
                f.write(f"# Complete Narration - {title}\n\n")
                f.write(f"**Style:** {narration_style}\n")
                f.write(f"**Tone:** {voice_tone}\n")
                f.write(f"**Total Scenes:** {len(narrations)}\n\n")
                f.write("="*80 + "\n\n")
                
                for scene_key, scene_data in narrations.items():
                    scene_num = scene_data['scene_number']
                    narration_text = scene_data['narration']
                    f.write(f"## Scene {scene_num}\n\n")
                    f.write(narration_text)
                    f.write("\n\n" + "-"*50 + "\n\n")
            
            file_paths['complete'] = complete_file
            
            # Save narrations as JSON for programmatic access
            json_file = os.path.join(narration_story_dir, f"{safe_title}_narrations.json")
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(narrations, f, ensure_ascii=False, indent=2)
            file_paths['json'] = json_file
            
            logger.info(f"Saved narrations to: {narration_story_dir}")
            return file_paths
            
        except Exception as e:
            logger.error(f"Failed to save narrations: {str(e)}")
            return {}

    def generate_enhanced_narration(self, title: str, scene_number: int, 
                                  additional_context: str = "", 
                                  narration_style: str = "dramatic",
                                  voice_tone: str = "engaging") -> str:
        """
        Generate enhanced narration with additional context
        
        Args:
            title: Title of the story
            scene_number: Number of the scene
            additional_context: Additional context to include
            narration_style: Style of narration
            voice_tone: Tone of voice
            
        Returns:
            Enhanced narration text
        """
        logger.info(f"Generating enhanced narration for scene {scene_number} of '{title}'")
        
        # Load story content
        story_content = self.load_story_content(title)
        if not story_content:
            return "Error: Could not load story content"
        
        # Parse scene prompts
        scene_prompts = self._parse_scene_prompts(story_content.get('scene_prompts', ''))
        
        if scene_number > len(scene_prompts) or scene_number < 1:
            return f"Error: Scene {scene_number} not found"
        
        scene_prompt = scene_prompts[scene_number - 1]
        
        # Add additional context to the prompt
        enhanced_prompt = f"{scene_prompt}\n\nAdditional Context: {additional_context}"
        
        # Generate enhanced narration
        narration = self.generate_scene_narration(
            title, enhanced_prompt, scene_number, narration_style, voice_tone
        )
        
        return narration

