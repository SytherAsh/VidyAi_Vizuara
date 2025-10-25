import streamlit as st
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from wikipedia_extractor import WikipediaExtractor
from story_generator import StoryGenerator
from comic_image_generator import ComicImageGenerator
from narration_generator import NarrationGenerator
from tts_generator import generate_scene_audios, synthesize_to_mp3, estimate_tts_duration_seconds
from video_creator import create_video, list_available_topics, list_available_audio_topics

# Load environment variables from .env if present
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

# Default API keys (loaded from environment if available)
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wiki_comic_generator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("WikiComicGenerator")



# Streamlit UI
def main():
    st.set_page_config(
        page_title="Wiki Comic Generator",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state variables
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'selected_topic' not in st.session_state:
        st.session_state.selected_topic = None
    if 'page_info' not in st.session_state:
        st.session_state.page_info = None
    if 'storyline' not in st.session_state:
        st.session_state.storyline = None
    if 'scene_prompts' not in st.session_state:
        st.session_state.scene_prompts = None
    if 'comic_images' not in st.session_state:
        st.session_state.comic_images = None
    if 'story_saved' not in st.session_state:
        st.session_state.story_saved = False
    if 'narrations' not in st.session_state:
        st.session_state.narrations = None
    if 'narration_style' not in st.session_state:
        st.session_state.narration_style = "dramatic"
    if 'voice_tone' not in st.session_state:
        st.session_state.voice_tone = "engaging"
    if 'final_video' not in st.session_state:
        st.session_state.final_video = None
    if 'audio_paths' not in st.session_state:
        st.session_state.audio_paths = None
    
    # Add custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E3A8A;
            text-align: center;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.5rem;
            color: #1E88E5;
            margin-bottom: 1rem;
        }
        .info-text {
            background-color: #E3F2FD;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .success-text {
            background-color: #E8F5E9;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .error-text {
            background-color: #FFEBEE;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
        }
        .comic-panel {
            margin: 10px;
            padding: 10px;
            border: 2px solid #1E88E5;
            border-radius: 10px;
        }
        .comic-caption {
            font-size: 0.9rem;
            font-style: italic;
            margin-top: 0.5rem;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # App header
    st.markdown('<div class="main-header">Wikipedia Comic Strip Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="info-text">Transform Wikipedia articles into engaging comic strips with AI-generated images!</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/200px-Wikipedia-logo-v2.svg.png", width=100)
        st.markdown("## API Keys")
        
        # API keys
        groq_api_key = st.text_input("Groq API Key", type="password", value=GROQ_API_KEY)
        gemini_api_key = st.text_input("Gemini API Key", type="password", value=GEMINI_API_KEY, help="Enter your Google Gemini API key")
        
        st.markdown("## Settings")
        
        # Wikipedia language selection
        wiki_lang = st.selectbox(
            "Wikipedia Language",
            options=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh"],
            index=0,
            format_func=lambda x: {
                "en": "English", "es": "Spanish", "fr": "French", 
                "de": "German", "it": "Italian", "pt": "Portuguese",
                "ru": "Russian", "ja": "Japanese", "zh": "Chinese"
            }.get(x, x),
            help="Select Wikipedia language"
        )
        
        # Story length
        story_length = st.select_slider(
            "Story Length",
            options=["short", "medium", "long"],
            value="medium",
            help="Select the desired length of the generated story"
        )
        
        # Comic style
        comic_style = st.selectbox(
            "Comic Art Style",
            options=[
                "manga", "western comic", "comic book", "noir comic", 
                "superhero comic", "indie comic", "cartoon", "graphic novel",
                "golden age comic", "modern comic", "mahua"
            ],
            index=1,
            help="Select the art style for the comic images"
        )
        
        # Number of scenes
        num_scenes = st.slider(
            "Number of Scenes",
            min_value=3,
            max_value=15,
            value=10,
            help="Select the number of scenes to generate"
        )
        
        st.markdown("---")
        st.markdown("## Narration Settings")
        
        # Narration style
        narration_style = st.selectbox(
            "Narration Style",
            options=["dramatic", "educational", "storytelling", "documentary"],
            index=0,
            help="Select the style of narration for your comic"
        )
        
        # Voice tone
        voice_tone = st.selectbox(
            "Voice Tone",
            options=["engaging", "serious", "playful", "informative"],
            index=0,
            help="Select the tone of voice for narration"
        )
        
        # Update session state
        st.session_state.narration_style = narration_style
        st.session_state.voice_tone = voice_tone

        st.markdown("---")
        st.markdown("## Video Settings")
        target_total_seconds = st.number_input("Target Total Video Duration (seconds)", min_value=0, max_value=600, value=0, help="0 = auto from audio")
        min_scene_seconds = st.number_input("Minimum Scene Duration (seconds)", min_value=1, max_value=10, value=2)
        fps = st.selectbox("Frame Rate", options=[24, 25, 30], index=2)
        resolution = st.selectbox("Resolution", options=["1280x720", "1920x1080"], index=1)
        bgm_enabled = st.checkbox("Enable background music (optional)", value=False)
        negative_concepts = st.text_input("Negative concepts to avoid (comma-separated)", value="text, letters, captions, subtitles, watermark, logo")
        style_sheet = st.text_area("Style sheet (optional)", value="", help="Global art directives")
        character_sheet = st.text_area("Character sheet (optional)", value="", help="Names, outfits, colors to keep consistent")
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This app extracts content from Wikipedia, uses Groq to generate
        comic book storylines, and creates comic images using Hugging Face models.
        
        Created by Airavat.
        """)
    
    # Main content
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="sub-header">Search Wikipedia</div>', unsafe_allow_html=True)
        
        # Search interface
        query = st.text_input("Enter your search query:", placeholder="Example: Albert Einstein, Moon Landing, etc.")
        search_button = st.button("Search", type="primary")
        
        if search_button and query:
            if not groq_api_key:
                st.error("Please enter your Groq API key in the sidebar to continue.")
            else:
                with st.spinner("Searching Wikipedia..."):
                    wiki_extractor = WikipediaExtractor(language=wiki_lang)
                    search_results = wiki_extractor.search_wikipedia(query)
                    
                    if isinstance(search_results, str):
                        st.warning(search_results)
                    else:
                        st.session_state.search_results = search_results
                        st.session_state.selected_topic = None
                        st.session_state.page_info = None
                        st.session_state.storyline = None
                        st.session_state.scene_prompts = None
                        st.session_state.comic_images = None
                        st.success(f"Found {len(search_results)} results for '{query}'")
        
        # Display search results
        if st.session_state.search_results:
            st.markdown("### Search Results")
            
            for i, result in enumerate(st.session_state.search_results):
                if st.button(f"{i+1}. {result}", key=f"result_{i}"):
                    st.session_state.selected_topic = result
                    st.session_state.page_info = None
                    st.session_state.storyline = None
                    st.session_state.scene_prompts = None
                    st.session_state.comic_images = None
    
    with col2:
        # Display selected topic and retrieve page info
        if st.session_state.selected_topic:
            st.markdown(f'<div class="sub-header">Selected Topic: {st.session_state.selected_topic}</div>', unsafe_allow_html=True)
            
            if st.session_state.page_info is None:
                with st.spinner(f"Getting information about '{st.session_state.selected_topic}'..."):
                    wiki_extractor = WikipediaExtractor(language=wiki_lang)
                    page_info = wiki_extractor.get_page_info(st.session_state.selected_topic)
                    st.session_state.page_info = page_info
            
            # Handle errors in page retrieval
            if "error" in st.session_state.page_info:
                st.error(st.session_state.page_info["message"])
                
                # Show disambiguation options if available
                if "options" in st.session_state.page_info:
                    st.markdown("### Possible options:")
                    for i, option in enumerate(st.session_state.page_info["options"]):
                        if st.button(f"{i+1}. {option}", key=f"option_{i}"):
                            st.session_state.selected_topic = option
                            st.session_state.page_info = None
                            st.session_state.storyline = None
                            st.session_state.scene_prompts = None
                            st.session_state.comic_images = None
            else:
                # Show page summary
                st.markdown("### Summary")
                st.markdown(st.session_state.page_info["summary"])
                
                # Generate storyline button
                if st.button("Generate Comic Storyline", type="primary"):
                    if not groq_api_key:
                        st.error("Please enter your Groq API key in the sidebar to continue.")
                    else:
                        with st.spinner("Generating comic storyline... This may take a minute."):
                            story_generator = StoryGenerator(api_key=groq_api_key)
                            storyline = story_generator.generate_comic_storyline(
                                st.session_state.page_info["title"],
                                st.session_state.page_info["content"],
                                target_length=story_length
                            )
                            st.session_state.storyline = storyline
                            st.session_state.scene_prompts = None
                            st.session_state.comic_images = None
                            st.session_state.story_saved = False
                            st.session_state.narrations = None
    
    # Display generated storyline
    if st.session_state.storyline:
        st.markdown("---")
        st.markdown('<div class="sub-header">Generated Comic Storyline</div>', unsafe_allow_html=True)
        
        # Add a download button for the storyline
        st.download_button(
            label="Download Storyline",
            data=st.session_state.storyline,
            file_name=f"{st.session_state.page_info['title']}_comic_storyline.md",
            mime="text/markdown"
        )
        
        # Display the storyline in an expandable section
        with st.expander("Show Full Storyline", expanded=False):
            st.markdown(st.session_state.storyline)
        
        # Generate scene prompts button
        if st.button("Generate Scene Prompts for Comic Panels", type="primary"):
            if not groq_api_key:
                st.error("Please enter your Groq API key in the sidebar to continue.")
            else:
                with st.spinner(f"Generating {num_scenes} scene prompts for comic panels..."):
                    story_generator = StoryGenerator(api_key=groq_api_key)
                    scene_prompts = story_generator.generate_scene_prompts(
                        st.session_state.page_info["title"],
                        st.session_state.storyline,
                        comic_style,
                        num_scenes=num_scenes
                    )
                    st.session_state.scene_prompts = scene_prompts
                    st.session_state.comic_images = None
                    
                    # Save story content to text files
                    with st.spinner("Saving story content to text files..."):
                        file_paths = story_generator.save_story_content(
                            st.session_state.page_info["title"],
                            st.session_state.storyline,
                            scene_prompts,
                            st.session_state.page_info
                        )
                        st.session_state.story_saved = True
                        st.success("Story content saved to text files!")
        
        # Display generated scene prompts
    if st.session_state.scene_prompts:
        st.markdown("---")
        st.markdown('<div class="sub-header">Generated Scene Prompts</div>', unsafe_allow_html=True)
        
        # Display scene prompts in an expandable section
        with st.expander("Show Scene Prompts", expanded=False):
            for i, prompt in enumerate(st.session_state.scene_prompts):
                st.markdown(f"### Scene {i+1}")
                st.text_area(f"Prompt for Scene {i+1}", value=prompt, height=150, key=f"scene_prompt_{i}")
        
        # Narration generation section
        if st.session_state.story_saved:
            st.markdown("---")
            st.markdown('<div class="sub-header">Generate Narration</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Generate All Scene Narrations", type="secondary"):
                    if not groq_api_key:
                        st.error("Please enter your Groq API key in the sidebar to continue.")
                    else:
                        with st.spinner(f"Generating narrations for all {len(st.session_state.scene_prompts)} scenes..."):
                            narration_generator = NarrationGenerator(api_key=groq_api_key)
                            narrations = narration_generator.generate_all_scene_narrations(
                                st.session_state.page_info["title"],
                                st.session_state.narration_style,
                                st.session_state.voice_tone
                            )
                            st.session_state.narrations = narrations
                            st.success(f"Generated narrations for {len(st.session_state.scene_prompts)} scenes!")
            
            with col2:
                if st.button("Generate Single Scene Narration", type="secondary"):
                    if not groq_api_key:
                        st.error("Please enter your Groq API key in the sidebar to continue.")
                    else:
                        scene_number = st.number_input("Scene Number", min_value=1, max_value=len(st.session_state.scene_prompts), value=1)
                        if st.button("Generate", key="generate_single_narration"):
                            with st.spinner(f"Generating narration for scene {scene_number}..."):
                                narration_generator = NarrationGenerator(api_key=groq_api_key)
                                narration = narration_generator.generate_scene_narration(
                                    st.session_state.page_info["title"],
                                    st.session_state.scene_prompts[scene_number - 1],
                                    scene_number,
                                    st.session_state.narration_style,
                                    st.session_state.voice_tone
                                )
                                st.text_area(f"Narration for Scene {scene_number}", value=narration, height=100)
        
        # Generate comic images button
        if st.button("Generate Comic Images", type="primary"):
            if not gemini_api_key:
                st.error("Please enter your Gemini API key in the sidebar to continue.")
            else:
                with st.spinner(f"Generating {len(st.session_state.scene_prompts)} comic images... This may take several minutes."):
                    image_generator = ComicImageGenerator(api_key=gemini_api_key)
                    image_paths = image_generator.generate_comic_strip(
                        st.session_state.scene_prompts,
                        "data/images",
                        st.session_state.page_info["title"],
                        style_sheet=style_sheet,
                        character_sheet=character_sheet,
                        negative_concepts=[s.strip() for s in negative_concepts.split(',') if s.strip()],
                        aspect_ratio="16:9"
                    )
                    st.session_state.comic_images = image_paths
                    
                    if image_paths:
                        st.success(f"Successfully generated {len(image_paths)} comic panels!")
                    else:
                        st.error("Failed to generate comic images. Please check the logs for details.")
    
    # Display generated narrations
    if st.session_state.narrations:
        st.markdown("---")
        st.markdown('<div class="sub-header">Generated Narrations</div>', unsafe_allow_html=True)
        
        # Display narrations in an expandable section
        with st.expander("Show All Narrations", expanded=False):
            for scene_key, scene_data in st.session_state.narrations['narrations'].items():
                scene_num = scene_data['scene_number']
                narration = scene_data['narration']
                st.markdown(f"### Scene {scene_num}")
                st.text_area(f"Narration for Scene {scene_num}", value=narration, height=100, key=f"narration_{scene_num}")
        
        # Download button for narrations
        if 'file_paths' in st.session_state.narrations and 'complete' in st.session_state.narrations['file_paths']:
            with open(st.session_state.narrations['file_paths']['complete'], 'r', encoding='utf-8') as f:
                narration_content = f.read()
            
            st.download_button(
                label="Download Complete Narration",
                data=narration_content,
                file_name=f"{st.session_state.page_info['title']}_complete_narration.txt",
                mime="text/plain"
            )

        # TTS generation controls
        st.markdown("---")
        st.markdown('<div class="sub-header">Text-to-Speech (MP3)</div>', unsafe_allow_html=True)

        # Voice selection and params
        voice = st.selectbox(
            "Voice",
            options=[
                "en-IN-NeerjaNeural",
                "en-US-AriaNeural",
                "en-GB-LibbyNeural",
                "en-US-GuyNeural",
                "en-AU-NatashaNeural"
            ],
            index=0,
            help="Select the voice for narration audio"
        )
        rate = st.slider("Speech Rate", min_value=-50, max_value=50, value=0, format="%d%%")
        volume = st.slider("Volume", min_value=-50, max_value=50, value=0, format="%d%%")

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Generate MP3s for All Scenes", type="primary"):
                with st.spinner("Generating MP3 files for all scenes..."):
                    audio_paths = generate_scene_audios(
                        st.session_state.narrations,
                        st.session_state.page_info["title"],
                        base_dir="data/narration",
                        voice=voice,
                        rate=f"{rate:+d}%",
                        volume=f"{volume:+d}%"
                    )
                    st.session_state.audio_paths = audio_paths
                    st.success(f"Generated {len(audio_paths)} MP3 files")
        with col_b:
            scene_num_single = st.number_input(
                "Generate Single Scene MP3",
                min_value=1,
                max_value=st.session_state.narrations.get("total_scenes", len(st.session_state.narrations.get("narrations", {}))),
                value=1,
            )
            if st.button("Generate MP3 for Scene", key="gen_single_mp3"):
                scene_key = f"scene_{int(scene_num_single)}"
                scene_data = st.session_state.narrations["narrations"].get(scene_key)
                if scene_data:
                    text = scene_data.get("narration", "").strip()
                    safe_title = st.session_state.page_info["title"].replace('/', '_')
                    out_dir = os.path.join("data/narration", safe_title, "audio")
                    os.makedirs(out_dir, exist_ok=True)
                    mp3_path = os.path.join(out_dir, f"scene_{int(scene_num_single)}.mp3")
                    synthesize_to_mp3(text, mp3_path, voice=voice, rate=f"{rate:+d}%", volume=f"{volume:+d}%")
                    if "audio_paths" not in st.session_state:
                        st.session_state.audio_paths = {}
                    st.session_state.audio_paths[scene_key] = mp3_path
                    st.success(f"Generated MP3 for scene {int(scene_num_single)}")

        # Preview audio players if available
        if st.session_state.audio_paths:
            st.markdown("### Scene Audio Previews")
            for scene_key, scene_data in st.session_state.narrations["narrations"].items():
                scene_num = scene_data["scene_number"]
                mp3_path = st.session_state.audio_paths.get(scene_key)
                if mp3_path and os.path.exists(mp3_path):
                    st.markdown(f"Scene {scene_num}")
                    with open(mp3_path, "rb") as f:
                        st.audio(f.read(), format="audio/mp3")

        # Generate Final Video
        if st.session_state.comic_images:
            st.markdown("---")
            st.markdown('<div class="sub-header">Generate Final Video</div>', unsafe_allow_html=True)
            
            # Video settings
            col1, col2, col3 = st.columns(3)
            with col1:
                video_resolution = st.selectbox(
                    "Video Resolution",
                    options=["1920x1080", "1280x720", "1080p", "720p"],
                    index=0,
                    help="Select the output video resolution"
                )
            with col2:
                video_fps = st.selectbox(
                    "Frames Per Second",
                    options=[24, 30, 60],
                    index=1,
                    help="Select the video frame rate"
                )
            with col3:
                video_quality = st.selectbox(
                    "Video Quality",
                    options=["High", "Medium", "Low"],
                    index=0,
                    help="Select the video quality setting"
                )
            
            # Background music option
            bgm_enabled = st.checkbox("Add Background Music", value=False)
            bgm_path = None
            bgm_volume = 0.08
            
            if bgm_enabled:
                bgm_path = st.file_uploader(
                    "Upload Background Music",
                    type=['mp3', 'wav', 'm4a'],
                    help="Upload a background music file (optional)"
                )
                if bgm_path:
                    # Save uploaded file temporarily
                    temp_bgm_path = os.path.join("temp", f"bgm_{st.session_state.page_info['title']}.{bgm_path.name.split('.')[-1]}")
                    os.makedirs("temp", exist_ok=True)
                    with open(temp_bgm_path, "wb") as f:
                        f.write(bgm_path.getbuffer())
                    bgm_path = temp_bgm_path
                
                bgm_volume = st.slider(
                    "Background Music Volume",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.08,
                    step=0.01,
                    help="Adjust the background music volume (0.0 = silent, 1.0 = full volume)"
                )
            
            # Video generation buttons
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Generate Video with Audio", type="primary", disabled=not st.session_state.audio_paths):
                    if not st.session_state.audio_paths:
                        st.warning("Please generate audio files first!")
                    else:
                        with st.spinner("Creating video with audio..."):
                            try:
                                result = create_video(
                                    title=st.session_state.page_info["title"],
                                    resolution=video_resolution,
                                    fps=video_fps,
                                    crossfade=0.3,
                                    min_scene_seconds=float(min_scene_seconds),
                                    head_pad=0.15,
                                    tail_pad=0.15,
                                    bgm_path=bgm_path,
                                    bgm_volume=bgm_volume,
                                    use_audio=True,
                                    verbose=False
                                )
                                
                                if result:
                                    st.session_state.final_video = result["video_path"]
                                    st.success("🎉 Video with audio generated successfully!")
                                else:
                                    st.error("❌ Failed to generate video. Check logs for details.")
                            except Exception as e:
                                st.error(f"❌ Error generating video: {str(e)}")
            
            with col_b:
                if st.button("Generate Video (Images Only)", type="secondary"):
                    with st.spinner("Creating video with images only..."):
                        try:
                            result = create_video(
                                title=st.session_state.page_info["title"],
                                resolution=video_resolution,
                                fps=video_fps,
                                crossfade=0.3,
                                min_scene_seconds=float(min_scene_seconds),
                                head_pad=0.15,
                                tail_pad=0.15,
                                bgm_path=bgm_path,
                                bgm_volume=bgm_volume,
                                use_audio=False,
                                verbose=False
                            )
                            
                            if result:
                                st.session_state.final_video = result["video_path"]
                                st.success("🎉 Video generated successfully!")
                            else:
                                st.error("❌ Failed to generate video. Check logs for details.")
                        except Exception as e:
                            st.error(f"❌ Error generating video: {str(e)}")
            
            # Display generated video
            if st.session_state.final_video and os.path.exists(st.session_state.final_video):
                st.markdown("### 🎬 Your Generated Video")
                
                # Video info
                file_size = os.path.getsize(st.session_state.final_video) / (1024 * 1024)  # MB
                st.info(f"📁 File: {os.path.basename(st.session_state.final_video)} | 📏 Size: {file_size:.1f} MB")
                
                # Video player
                with open(st.session_state.final_video, "rb") as f:
                    st.video(f.read())
                
                # Download button
                with open(st.session_state.final_video, "rb") as f:
                    st.download_button(
                        label="📥 Download Video",
                        data=f.read(),
                        file_name=os.path.basename(st.session_state.final_video),
                        mime="video/mp4",
                        type="primary"
                    )
                
                # Clean up temporary background music file
                if bgm_path and os.path.exists(bgm_path):
                    try:
                        os.remove(bgm_path)
                    except:
                        pass
    
    # Display generated comic images
    if st.session_state.comic_images:
        st.markdown("---")
        st.markdown('<div class="sub-header">Your Generated Comic Strip</div>', unsafe_allow_html=True)
        
        # Create columns for comic panels
        cols_per_row = 3
        panels = []
        for i in range(0, len(st.session_state.comic_images), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(st.session_state.comic_images):
                    with cols[j]:
                        st.image(st.session_state.comic_images[idx], caption=f"Scene {idx+1}", use_container_width=True)
                        # Add scene prompt as a caption
                        if idx < len(st.session_state.scene_prompts):
                            scene_prompt = st.session_state.scene_prompts[idx]
                            # Extract just the first line as a short caption
                            short_caption = scene_prompt.split('\n')[0] if '\n' in scene_prompt else scene_prompt
                            st.markdown(f'<div class="comic-caption">{short_caption}</div>', unsafe_allow_html=True)
        
        # Add download button for a zip file of all images
        # Note: This would require implementing a function to create a zip file
        st.markdown("### Download Options")
        st.warning("Download functionality for the complete comic strip will be implemented in a future update.")
        
        # Reset button
        if st.button("Start Over", type="secondary"):
            st.session_state.search_results = None
            st.session_state.selected_topic = None
            st.session_state.page_info = None
            st.session_state.storyline = None
            st.session_state.scene_prompts = None
            st.session_state.comic_images = None
            st.session_state.story_saved = False
            st.session_state.narrations = None
            st.rerun()

    # Additional section for creating videos from existing content
    st.markdown("---")
    st.markdown('<div class="sub-header">Create Video from Existing Content</div>', unsafe_allow_html=True)
    st.markdown("Create videos from previously generated comic strips and audio files.")
    
    # List available topics
    available_topics = list_available_topics()
    available_audio_topics = list_available_audio_topics()
    
    if available_topics:
        st.markdown("### Available Comic Strips")
        
        # Create a selectbox for topic selection
        selected_existing_topic = st.selectbox(
            "Select a comic strip to create video from:",
            options=[""] + available_topics,
            help="Choose from previously generated comic strips"
        )
        
        if selected_existing_topic:
            st.info(f"Selected: {selected_existing_topic}")
            
            # Check if audio is available
            has_audio = selected_existing_topic in available_audio_topics
            st.write(f"Audio available: {'✅ Yes' if has_audio else '❌ No'}")
            
            # Video settings for existing content
            col1, col2, col3 = st.columns(3)
            with col1:
                existing_resolution = st.selectbox(
                    "Resolution",
                    options=["1920x1080", "1280x720", "1080p", "720p"],
                    index=0,
                    key="existing_resolution"
                )
            with col2:
                existing_fps = st.selectbox(
                    "FPS",
                    options=[24, 30, 60],
                    index=1,
                    key="existing_fps"
                )
            with col3:
                existing_quality = st.selectbox(
                    "Quality",
                    options=["High", "Medium", "Low"],
                    index=0,
                    key="existing_quality"
                )
            
            # Background music for existing content
            existing_bgm_enabled = st.checkbox("Add Background Music", value=False, key="existing_bgm")
            existing_bgm_path = None
            existing_bgm_volume = 0.08
            
            if existing_bgm_enabled:
                existing_bgm_path = st.file_uploader(
                    "Upload Background Music",
                    type=['mp3', 'wav', 'm4a'],
                    help="Upload a background music file (optional)",
                    key="existing_bgm_upload"
                )
                if existing_bgm_path:
                    # Save uploaded file temporarily
                    temp_bgm_path = os.path.join("temp", f"existing_bgm_{selected_existing_topic}.{existing_bgm_path.name.split('.')[-1]}")
                    os.makedirs("temp", exist_ok=True)
                    with open(temp_bgm_path, "wb") as f:
                        f.write(existing_bgm_path.getbuffer())
                    existing_bgm_path = temp_bgm_path
                
                existing_bgm_volume = st.slider(
                    "Background Music Volume",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.08,
                    step=0.01,
                    help="Adjust the background music volume",
                    key="existing_bgm_volume"
                )
            
            # Video generation buttons for existing content
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("Create Video with Audio", disabled=not has_audio, key="existing_with_audio"):
                    if not has_audio:
                        st.warning("No audio files found for this topic!")
                    else:
                        with st.spinner("Creating video with audio..."):
                            try:
                                result = create_video(
                                    title=selected_existing_topic,
                                    resolution=existing_resolution,
                                    fps=existing_fps,
                                    crossfade=0.3,
                                    min_scene_seconds=2.0,
                                    head_pad=0.15,
                                    tail_pad=0.15,
                                    bgm_path=existing_bgm_path,
                                    bgm_volume=existing_bgm_volume,
                                    use_audio=True,
                                    verbose=False
                                )
                                
                                if result:
                                    st.success("🎉 Video with audio created successfully!")
                                    st.session_state.existing_video = result["video_path"]
                                else:
                                    st.error("❌ Failed to create video. Check logs for details.")
                            except Exception as e:
                                st.error(f"❌ Error creating video: {str(e)}")
            
            with col_b:
                if st.button("Create Video (Images Only)", key="existing_images_only"):
                    with st.spinner("Creating video with images only..."):
                        try:
                            result = create_video(
                                title=selected_existing_topic,
                                resolution=existing_resolution,
                                fps=existing_fps,
                                crossfade=0.3,
                                min_scene_seconds=2.0,
                                head_pad=0.15,
                                tail_pad=0.15,
                                bgm_path=existing_bgm_path,
                                bgm_volume=existing_bgm_volume,
                                use_audio=False,
                                verbose=False
                            )
                            
                            if result:
                                st.success("🎉 Video created successfully!")
                                st.session_state.existing_video = result["video_path"]
                            else:
                                st.error("❌ Failed to create video. Check logs for details.")
                        except Exception as e:
                            st.error(f"❌ Error creating video: {str(e)}")
            
            # Display existing video if created
            if hasattr(st.session_state, 'existing_video') and st.session_state.existing_video and os.path.exists(st.session_state.existing_video):
                st.markdown("### 🎬 Generated Video from Existing Content")
                
                # Video info
                file_size = os.path.getsize(st.session_state.existing_video) / (1024 * 1024)  # MB
                st.info(f"📁 File: {os.path.basename(st.session_state.existing_video)} | 📏 Size: {file_size:.1f} MB")
                
                # Video player
                with open(st.session_state.existing_video, "rb") as f:
                    st.video(f.read())
                
                # Download button
                with open(st.session_state.existing_video, "rb") as f:
                    st.download_button(
                        label="📥 Download Video",
                        data=f.read(),
                        file_name=os.path.basename(st.session_state.existing_video),
                        mime="video/mp4",
                        type="primary",
                        key="download_existing_video"
                    )
                
                # Clean up temporary background music file
                if existing_bgm_path and os.path.exists(existing_bgm_path):
                    try:
                        os.remove(existing_bgm_path)
                    except:
                        pass
    else:
        st.info("No existing comic strips found. Generate some comic strips first!")

# Call main function if script is run directly
if __name__ == "__main__":
    main()