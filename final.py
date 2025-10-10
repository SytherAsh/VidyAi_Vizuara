import streamlit as st
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from wikipedia_extractor import WikipediaExtractor
from story_generator import StoryGenerator
from comic_image_generator import ComicImageGenerator

# Load environment variables from .env if present
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv()

# Default API keys (loaded from environment if available)
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
HF_API_TOKEN: Optional[str] = os.getenv("HF_API_TOKEN")

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
        hf_token = st.text_input("Hugging Face API Token", type="password", value=HF_API_TOKEN, help="Enter your Hugging Face API token")
        
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
        
        # Display generated scene prompts
    if st.session_state.scene_prompts:
        st.markdown("---")
        st.markdown('<div class="sub-header">Generated Scene Prompts</div>', unsafe_allow_html=True)
        
        # Display scene prompts in an expandable section
        with st.expander("Show Scene Prompts", expanded=False):
            for i, prompt in enumerate(st.session_state.scene_prompts):
                st.markdown(f"### Scene {i+1}")
                st.text_area(f"Prompt for Scene {i+1}", value=prompt, height=150, key=f"scene_prompt_{i}")
        
        # Generate comic images button
        if st.button("Generate Comic Images", type="primary"):
            if not hf_token:
                st.error("Please enter your Hugging Face API token in the sidebar to continue.")
            else:
                with st.spinner(f"Generating {len(st.session_state.scene_prompts)} comic images... This may take several minutes."):
                    image_generator = ComicImageGenerator(hf_token=hf_token)
                    image_paths = image_generator.generate_comic_strip(
                        st.session_state.scene_prompts,
                        "data/images",
                        st.session_state.page_info["title"]
                    )
                    st.session_state.comic_images = image_paths
                    
                    if image_paths:
                        st.success(f"Successfully generated {len(image_paths)} comic panels!")
                    else:
                        st.error("Failed to generate comic images. Please check the logs for details.")
    
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
                        st.image(st.session_state.comic_images[idx], caption=f"Scene {idx+1}", use_column_width=True)
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
            st.experimental_rerun()

# Call main function if script is run directly
if __name__ == "__main__":
    main()