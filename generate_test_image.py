import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from comic_image_generator import ComicImageGenerator


def main():
    # Load .env and read Gemini API key
    load_dotenv()
    gemini_api_key = os.getenv("GEMINI_API_KEY")

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    if not gemini_api_key:
        raise SystemExit("Gemini API key is missing. Set GEMINI_API_KEY in your .env file.")

    # Fixed prompt for quick testing - Krishna and Arjun
    prompt = (
        """
        Visual: Lord Krishna in his divine form as the charioteer, adorned in brilliant peacock feather crown and golden crown, wearing ornate yellow silk dhoti with intricate gold borders, multiple necklaces of pearls and gems, armlets and bracelets, holding the reins of the divine chariot with one hand while gesturing with the other, his dark blue complexion glowing with divine radiance, serene yet powerful expression, lotus eyes filled with wisdom and compassion. Prince Arjuna in full warrior regalia, wearing golden armor with intricate engravings, ornate helmet with peacock feathers, holding his divine bow Gandiva, arrows in his quiver, muscular build, determined yet conflicted expression, royal blue and gold attire, standing beside Krishna on the magnificent golden chariot drawn by white horses. The battlefield of Kurukshetra in the background with vast armies arrayed, dust clouds rising, war banners fluttering, distant mountains and sacred ground, divine light emanating from the chariot, cosmic energy swirling around them, sacred symbols and divine auras, dramatic sky with clouds and divine illumination, epic scale composition showing the divine conversation between Krishna and Arjuna before the great war, cinematic lighting with golden hour glow, detailed ancient Indian architecture and weaponry, rich textures of silk, metal, and divine energy, sharp focus on the two central figures, depth-of-field background, no on-image text, no modern elements, 16:9 landscape format, high detail, photorealistic style with divine mystical elements.
        
        Style: Epic historical fantasy art, photorealistic rendering with divine mystical elements, rich Indian classical art influences, cinematic composition, dramatic lighting, detailed textures, vibrant colors with golden and blue tones, no text overlays, professional comic book quality, ancient Indian aesthetic with modern digital art techniques.
        """
        )

    # Default output location
    out_dir = "/home/yashsawant/Desktop/genai/wiki_streamlit/data/images/test"
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(out_dir, f"new_prompt_{timestamp}.jpg")

    generator = ComicImageGenerator(api_key=gemini_api_key)

    success = generator.generate_comic_image(scene_prompt=prompt, output_path=out_path, scene_num=1)
    if success and os.path.exists(out_path):
        print(f"SUCCESS: Image written to {out_path}")
        return 0
    else:
        print("FAILED: Could not generate image. Check logs for details.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


