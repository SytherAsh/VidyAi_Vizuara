# Wikipedia Comic Strip Generator

A powerful AI-driven application that transforms Wikipedia articles into engaging comic strips using advanced language models and image generation technology. This project combines Wikipedia content extraction, AI-powered story generation, and automated comic panel creation to produce educational and entertaining visual narratives.

## 🎯 Project Overview

The Wikipedia Comic Strip Generator is an innovative tool that:
- Extracts content from Wikipedia articles in multiple languages
- Uses AI to generate compelling comic book storylines
- Creates detailed scene prompts for visual storytelling
- Generates high-quality comic panel images using state-of-the-art AI models
- Provides both web UI (Streamlit) and API (Flask) interfaces

## 🚀 Features

### Core Functionality
- **Multi-language Wikipedia Support**: Extract content from Wikipedia in 9 different languages
- **AI-Powered Story Generation**: Transform factual content into engaging comic narratives
- **Intelligent Scene Creation**: Generate detailed visual prompts for comic panels
- **Multiple Art Styles**: Support for various comic art styles (manga, superhero, noir, etc.)
- **Age-Appropriate Content**: Customize content complexity for different audiences
- **Educational Focus**: Balance entertainment with educational value

### User Interface
- **Streamlit Web App**: Interactive web interface for easy use
- **Flask API**: RESTful API for programmatic access
- **Real-time Progress**: Live updates during generation process
- **Download Options**: Export storylines and generated images

## 🏗️ Architecture

### Project Structure
```
genai/
├── README.md
├── vidai.ipynb
└── wiki_streamlit/
    ├── final.py                 # Main Streamlit application
    ├── app.py                   # Flask API server
    ├── requirements.txt         # Python dependencies
    ├── wiki_comic_generator.log # Application logs
    ├── data/                    # Generated content storage
    │   ├── images/             # Generated comic panels
    │   │   ├── Ramayana/
    │   │   ├── Shivaji/
    │   │   ├── World War II/
    │   │   └── FIFA World Cup/
    │   └── *_data.json         # Extracted Wikipedia data
    └── test/                    # Test files and documentation
        ├── info.txt
        ├── proposal.txt
        └── test1.txt
```

### System Components

#### 1. Wikipedia Content Extraction (`WikipediaExtractor`)
- **Purpose**: Fetches and processes Wikipedia articles
- **Features**:
  - Multi-language support (EN, ES, FR, DE, IT, PT, RU, JA, ZH)
  - Disambiguation handling
  - Content sanitization and formatting
  - Automatic retry with exponential backoff
  - Data persistence to JSON files

#### 2. AI Story Generation (`StoryGenerator`)
- **Purpose**: Converts Wikipedia content into comic storylines
- **AI Model**: Groq's LLaMA 3.1 8B Instant
- **Features**:
  - Configurable story length (short/medium/long)
  - Character development and dialogue generation
  - Scene-by-scene narrative structure
  - Educational content integration

#### 3. Scene Prompt Generation
- **Purpose**: Creates detailed visual descriptions for image generation
- **Features**:
  - Style-specific guidance (manga, superhero, noir, etc.)
  - Age-appropriate content filtering
  - Education level customization
  - Character consistency maintenance

#### 4. Image Generation (`ComicImageGenerator`)
- **Purpose**: Generates comic panel images from text prompts
- **Primary Model**: Black Forest Labs FLUX.1-dev
- **Fallback Model**: RunwayML Stable Diffusion v1.5
- **Features**:
  - Automatic fallback on API failures
  - Payment error handling
  - Placeholder image generation
  - Batch processing capabilities

## 🤖 AI Models Used

### 1. Groq LLaMA 3.1 8B Instant
- **Provider**: Groq
- **Purpose**: Text generation for storylines and scene prompts
- **Capabilities**:
  - Fast inference (up to 500+ tokens/second)
  - High-quality text generation
  - Context understanding up to 8K tokens
  - Optimized for creative writing tasks

**Usage in Project**:
- Generates comic storylines from Wikipedia content
- Creates detailed scene descriptions for image generation
- Handles character dialogue and narrative structure

### 2. Black Forest Labs FLUX.1-dev
- **Provider**: Hugging Face Inference API
- **Purpose**: Primary image generation model
- **Capabilities**:
  - State-of-the-art text-to-image generation
  - High-resolution output (1024x1024)
  - Excellent prompt following
  - Photorealistic and artistic styles

**Usage in Project**:
- Generates comic panel images from scene prompts
- Supports various art styles and visual themes
- Produces high-quality visual content

### 3. RunwayML Stable Diffusion v1.5
- **Provider**: Hugging Face Inference API
- **Purpose**: Fallback image generation model
- **Capabilities**:
  - Reliable text-to-image generation
  - Good prompt understanding
  - Free tier availability
  - Consistent output quality

**Usage in Project**:
- Serves as backup when primary model fails
- Handles payment/quota issues gracefully
- Ensures project reliability

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Internet connection for API access

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd genai/wiki_streamlit
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Set Up API Keys
Create a `.env` file in the `wiki_streamlit` directory:
```env
GROQ_API_KEY=your_groq_api_key_here
HF_API_TOKEN=your_huggingface_token_here
```

**API Key Setup**:
1. **Groq API Key**: 
   - Visit [console.groq.com](https://console.groq.com)
   - Sign up/login and generate an API key
   - Free tier includes generous usage limits

2. **Hugging Face Token**:
   - Visit [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
   - Create a new token with read permissions
   - Free tier available for most models

### Step 4: Run the Application

#### Option A: Streamlit Web App (Recommended)
```bash
streamlit run final.py
```
Access the app at `http://localhost:8501`

#### Option B: Flask API Server
```bash
python app.py
```
API available at `http://localhost:5000`

## 📖 Usage Guide

### Web Interface (Streamlit)

1. **Search Wikipedia**:
   - Enter your search query (e.g., "Albert Einstein", "Moon Landing")
   - Select Wikipedia language
   - Click "Search" to find articles

2. **Select Article**:
   - Choose from search results
   - Review article summary
   - Handle disambiguation if needed

3. **Generate Storyline**:
   - Click "Generate Comic Storyline"
   - Wait for AI processing (1-2 minutes)
   - Review generated narrative

4. **Create Scene Prompts**:
   - Select comic art style
   - Choose number of scenes (3-15)
   - Click "Generate Scene Prompts"

5. **Generate Images**:
   - Click "Generate Comic Images"
   - Wait for image generation (5-15 minutes)
   - View your comic strip!

### API Usage (Flask)

#### Search Wikipedia
```bash
curl "http://localhost:5000/search?query=Albert%20Einstein&lang=en"
```

#### Generate Complete Comic
```bash
curl -X GET "http://localhost:5000/page_info?title=Albert%20Einstein&lang=en" \
  -H "Groq-Api-Key: your_groq_key" \
  -H "Hf-Api-Key: your_hf_token"
```

## ⚙️ Configuration Options

### Story Generation
- **Length**: Short (500 words), Medium (1000 words), Long (2000 words)
- **Style**: Manga, Superhero, Noir, Cartoon, European, Indie, Retro
- **Audience**: Kids, Teens, General, Adult
- **Education Level**: Basic, Standard, Advanced

### Image Generation
- **Scenes**: 3-15 panels per comic
- **Resolution**: High-quality output (1024x1024)
- **Style Consistency**: Maintained across all panels
- **Fallback Handling**: Automatic model switching on failures

### Language Support
- English (en)
- Spanish (es)
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Russian (ru)
- Japanese (ja)
- Chinese (zh)

## 🔧 Technical Details

### Error Handling
- **Network Issues**: Automatic retry with exponential backoff
- **API Failures**: Graceful fallback to alternative models
- **Content Issues**: Disambiguation and suggestion handling
- **Rate Limiting**: Built-in delay and retry mechanisms

### Performance Optimization
- **Caching**: Wikipedia content saved locally
- **Batch Processing**: Efficient image generation pipeline
- **Memory Management**: Optimized for large content processing
- **Logging**: Comprehensive error tracking and debugging

### Data Management
- **Storage**: Organized file structure for generated content
- **Persistence**: JSON files for Wikipedia data
- **Cleanup**: Automatic directory creation and management
- **Backup**: Generated content preserved for reuse

## 📊 Example Outputs

The application has generated successful comic strips for various topics:

- **Historical Events**: World War II, Ancient Civilizations
- **Cultural Topics**: Ramayana, Diwali celebrations
- **Sports**: FIFA World Cup
- **Historical Figures**: Shivaji Maharaj
- **Scientific Topics**: Space exploration, Physics

Each comic includes:
- 10 high-quality panels
- Consistent character design
- Educational narrative
- Appropriate visual style
- Downloadable content

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**:
   - Verify keys in `.env` file
   - Check API key validity
   - Ensure sufficient quota

2. **Image Generation Failures**:
   - Check Hugging Face token
   - Verify model availability
   - Try fallback model

3. **Wikipedia Access Issues**:
   - Check internet connection
   - Verify language settings
   - Try different search terms

4. **Memory Issues**:
   - Reduce number of scenes
   - Process shorter articles
   - Restart application

### Debug Mode
Enable detailed logging by modifying the logging level in `final.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Future Enhancements

### Planned Features
- **Voice Narration**: Audio generation for comic strips
- **Video Export**: Animated comic sequences
- **Custom Characters**: User-defined character designs
- **Collaborative Editing**: Multi-user comic creation
- **Advanced Styling**: More art style options
- **Mobile App**: Native mobile application

### Technical Improvements
- **Caching System**: Redis-based content caching
- **Database Integration**: PostgreSQL for data management
- **Microservices**: Containerized service architecture
- **CDN Integration**: Fast content delivery
- **Analytics**: Usage tracking and optimization

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
git clone <repository-url>
cd genai/wiki_streamlit
pip install -r requirements.txt
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Wikipedia**: For providing comprehensive content
- **Groq**: For fast and reliable AI text generation
- **Hugging Face**: For image generation models and infrastructure
- **Streamlit**: For the excellent web framework
- **Open Source Community**: For various supporting libraries

## 📞 Support

For support, questions, or feature requests:
- Create an issue in the repository
- Contact the development team
- Check the documentation wiki

## 📈 Project Status

- **Version**: 1.0.0
- **Status**: Active Development
- **Last Updated**: December 2024
- **Maintainer**: Airavat

---

**Made with ❤️ by the Wikipedia Comic Generator Team**
