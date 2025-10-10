import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from comic_image_generator import ComicImageGenerator


def main():
    # Load .env and read HF token
    load_dotenv()
    hf_token = os.getenv("HF_API_TOKEN")

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if not hf_token:
        raise SystemExit("HF token is missing. Set HF_API_TOKEN in your .env file.")

    # Fixed prompt for quick testing
    prompt = (
        """
        Maharana Pratap in full Rajput armor leading cavalry on the battlefield at Haldighati, mounted on his loyal horse Chetak, raised spear in hand, vibrant saffron and green banners whipping in the wind, Mughal infantry in the distant haze, dust clouds and flying embers, glinting steel, ornate chainmail and helmet with plume, angular jaw and fierce determined gaze, sunbeams cutting through smoke, dynamic cinematic composition, detailed historical attire and Rajput motifs, realistic textures, sharp focus on foreground, depth-of-field background, dramatic rim lighting, 16:9 landscape, high detail, epic scale, no on-image text, no modern elements"""
        )

    # Default output location
    out_dir = "/home/yashsawant/Desktop/genai/wiki_streamlit/data/images/test"
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"new_prompt_{timestamp}.jpg")

    # Model endpoints (primary + free fallback)
    model_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    fallback_model_url = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"

    generator = ComicImageGenerator(
        hf_token=hf_token,
        model_url=model_url,
        fallback_model_url=fallback_model_url,
    )

    success = generator.generate_comic_image(scene_prompt=prompt, output_path=out_path, scene_num=1)
    if success and os.path.exists(out_path):
        print(f"SUCCESS: Image written to {out_path}")
        return 0
    else:
        print("FAILED: Could not generate image. Check logs for details.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


