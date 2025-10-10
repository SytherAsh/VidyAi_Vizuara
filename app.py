from flask import Flask, request, jsonify
import os
from .text_service import WikipediaExtractor, StoryGenerator
from .image_service import ComicImageGenerator

app = Flask(__name__)

DATA_DIR = "data"
IMAGE_DIR = os.path.join(DATA_DIR, "images")

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    lang = request.args.get("lang", "en")
    
    if not query:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    extractor = WikipediaExtractor(language=lang)
    result = extractor.search_wikipedia(query)
    return jsonify({"results": result})

@app.route("/page_info", methods=["GET"])
def page_info():
    title = request.args.get("title")
    lang = request.args.get("lang", "en")
    groq_api_key = request.headers.get("Groq-Api-Key")
    hf_token = request.headers.get("Hf-Api-Key")

    if not all([title, groq_api_key, hf_token]):
        return jsonify({"error": "Missing required title or API keys"}), 400

    try:
        # Step 1: Get page content
        extractor = WikipediaExtractor(language=lang)
        info = extractor.get_page_info(title)
        content = info.get("content", "")

        if not content:
            return jsonify({"error": "No content found for the title"}), 404

        # Step 2: Generate storyline
        story_generator = StoryGenerator(api_key=groq_api_key)
        storyline = story_generator.generate_comic_storyline(title, content, target_length="medium")

        # Step 3: Generate scenes
        scenes = story_generator.generate_scene_prompts(title, storyline, comic_style="Western", num_scenes=5)

        # Step 4: Generate images
        image_generator = ComicImageGenerator(hf_token=hf_token)
        image_paths = image_generator.generate_comic_strip(scenes, IMAGE_DIR, title)

        return jsonify({
            "title": title,
            "storyline": storyline,
            "scenes": scenes,
            "image_paths": image_paths
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
