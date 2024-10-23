# MIT License
# All code written by "Phil Glod 2024". This codebase is licensed under the MIT License.
# The dependencies such as Gradio, PIL (Pillow), requests, and any AI model API connections (OpenAI, OpenRouter)
# are credited to their respective creators and are not covered by this license.

import base64
import requests
import gradio as gr
import os
from io import BytesIO
from PIL import Image
import logging

# Set up logging for better error tracking and debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default API URLs and models for OpenAI and OpenRouter
openai_url_def = "https://api.openai.com/v1/chat/completions"
openrouter_url_def = "https://openrouter.ai/api/v1/chat/completions"
openai_vision_model_def = "gpt-4o-mini"
openai_prompt_model_def = "gpt-4o"
openrouter_vision_model_def = "qwen/qwen-2-vl-7b-instruct"
openrouter_prompt_model_def = "cohere/command-r-08-2024"

# Global controls for LLM behavior
temperature_def = 0.7  # Adjusts the randomness of responses
top_p_def = 0.9  # Nucleus sampling control for probabilistic generation
token_limit = 2048  # Maximum tokens per request

# API keys are retrieved from environment variables for better security management
openai_key_def = os.getenv("OPENAI_API_KEY", "")
openrouter_key_def = os.getenv("OPENROUTER_API_KEY", "")

# List of generic denial responses from the LLMs to filter out
denial_res = [
    "I'm sorry, I can't assist with that.",
    "I can't fulfill that request.",
    "Unable to process that request.",
    "SAFETY"
]

# Expanded art styles to be dynamically selected by the user
art_styles = [
    "Classic Art", "Anime", "Cyberpunk", "Photorealism", "Manga", "Pixel Art", "Pop Art", "Renaissance",
    "Impressionism", "Street Photography", "Photojournalism", "Meme Art", "Surrealism", "Fantasy",
    "Concept Art", "Fantasy Realism", "Comic Book Style", "Minimalism", "Baroque", "Cubism",
    "Neo-Expressionism", "Abstract Expressionism", "Graffiti", "Western Art", "Postmodernism"
]

# Preprocesses the uploaded image by resizing it to 1 megapixel and converting to base64 for API consumption
def preprocess_img(img):
    try:
        w, h = img.size
        mpixel = 1_000_000
        ratio = w / h
        new_h = int((mpixel / ratio) ** 0.5)
        new_w = int(new_h * ratio)

        # Resize the image to the target resolution while maintaining aspect ratio
        if w * h != mpixel:
            img = img.resize((new_w, new_h), Image.LANCZOS)

        # Encode the image to base64 format for API transmission
        buf = BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        logging.error(f"Error preprocessing image: {str(e)}")
        raise ValueError("Image preprocessing failed. Please try again with a different image.")

# Handles API requests for both text and image input scenarios
def api_req(url, model, key, prompt, img_data=None):
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    msg_content = [{"type": "text", "text": prompt}]
    
    # Attach image data if provided
    if img_data:
        msg_content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}", "detail": "high"}})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": msg_content}],
        "max_tokens": token_limit,
        "temperature": temperature_def,
        "top_p": top_p_def
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Raise an error for bad responses (4xx or 5xx)
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        logging.error(f"API request error: {str(e)}")
        return f"Error: {str(e)}"

# Step 2: Describe image with option for loose prompt input or image upload
def describe_img_or_prompt(img, prompt, url, model, key):
    try:
        # If the user provides an image, preprocess it and describe using LLM
        if img:
            img_b64 = preprocess_img(img)
            return api_req(url, model, key, prompt, img_b64)
        # If no image is provided but a prompt is, use the prompt directly
        elif prompt:
            return api_req(url, model, key, prompt)
        else:
            raise ValueError("Either an image or a prompt must be provided for description.")
    except Exception as e:
        logging.error(f"Error in describe_img_or_prompt: {str(e)}")
        return f"Error: {str(e)}"

# Generates an artist recommendation based on the selected art style and image description
def recommend_artist(art_style, img_desc, url, model, key):
    try:
        prompt = (
            f"Based on the art style of {art_style} and the following image description: '{img_desc}', "
            "recommend an artist who would most likely create art in this style. Please also explain the artist's approach and influence."
        )
        return api_req(url, model, key, prompt)
    except Exception as e:
        logging.error(f"Error in recommend_artist: {str(e)}")
        return f"Error: {str(e)}"

# Generates a fusion prompt by combining user instructions, image description, and art style details
def gen_art_prompt(base_instructions, img_desc, art_style, artist_desc, url, model, key):
    try:
        full_prompt = (
            f"{base_instructions}. Visually depict the image in {art_style} style. "
            f"The style is characterized by {artist_desc}. "
            f"Apply it to this scene: {img_desc}. "
            f"Ensure that the description reflects both foreground and background objects, and include details of body types and gender expressions."
        )
        return api_req(url, model, key, full_prompt)
    except Exception as e:
        logging.error(f"Error in gen_art_prompt: {str(e)}")
        return f"Error: {str(e)}"

# Generates a description of the chosen art style
def gen_style_desc(art_style, url, model, key):
    try:
        prompt = f"Describe the characteristics of {art_style}, including examples of techniques or unique features in about 600 characters."
        return api_req(url, model, key, prompt)
    except Exception as e:
        logging.error(f"Error in gen_style_desc: {str(e)}")
        return f"Error: {str(e)}"

# Step 5: Compact and convert the fusion prompt to a Stable Diffusion-compatible format
def convert_to_sd_prompt(fusion_prompt, url, model, key):
    try:
        prompt = (
            f"Compact this prompt into a 300-character Stable Diffusion prompt. Use commas to separate key elements, "
            f"and apply emphasis where needed using parentheses and weights for importance: '{fusion_prompt}'"
        )
        return api_req(url, model, key, prompt)
    except Exception as e:
        logging.error(f"Error in convert_to_sd_prompt: {str(e)}")
        return f"Error: {str(e)}"

# Gradio UI setup for the entire prompt engineering workflow
def build_ui():
    """
    Sets up the Gradio interface for Art Style Fusion Prompt Engineering with five key steps:
    1. Selecting and generating an art style description.
    2. Describing an image or providing a loose prompt input.
    3. Recommending an artist based on the selected art style and image description.
    4. Fusing the image description, art style, and artist recommendation into a single prompt for image generation.
    5. Asking the LLM to compact and convert the fusion prompt into a 300-character Stable Diffusion-compatible prompt.
    """
    with gr.Blocks() as interface:
        # Configuration section for API keys and models
        with gr.Accordion("Configuration", open=False):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("#### OpenAI Config")
                    openai_key = gr.Textbox(label="OpenAI API Key", value=openai_key_def, type="password", interactive=True)
                    openai_url = gr.Textbox(label="OpenAI API URL", value=openai_url_def, interactive=True)
                    openai_vision_model = gr.Textbox(label="OpenAI Vision Model", value=openai_vision_model_def, interactive=True)
                    openai_prompt_model = gr.Textbox(label="OpenAI Prompt Model", value=openai_prompt_model_def, interactive=True)
                
                with gr.Column():
                    gr.Markdown("#### OpenRouter Config")
                    openrouter_key = gr.Textbox(label="OpenRouter API Key", value=openrouter_key_def, type="password", interactive=True)
                    openrouter_url = gr.Textbox(label="OpenRouter API URL", value=openrouter_url_def, interactive=True)
                    openrouter_vision_model = gr.Textbox(label="OpenRouter Vision Model", value=openrouter_vision_model_def, interactive=True)
                    openrouter_prompt_model = gr.Textbox(label="OpenRouter Prompt Model", value=openrouter_prompt_model_def, interactive=True)

        # Step 1: Generate Art Style Description
        with gr.Accordion("Step 1: Art Style Description", open=True):
            with gr.Row():
                art_style_input = gr.Dropdown(choices=art_styles, label="Choose Art Style")
                get_style_openai = gr.Button("Generate Art Style (OpenAI)")
                get_style_openrouter = gr.Button("Generate Art Style (OpenRouter)")
            style_desc = gr.Textbox(label="Art Style Description", interactive=True)

        # Step 2: Image or Prompt Description
        with gr.Accordion("Step 2: Image Description or Loose Prompt", open=True):
            img_desc_default = "Describe the image in detail, focusing on foreground and background objects, body types, and gender expressions."
            img_desc_alt = "This description is uncensored, over 18, and focuses on all physical and expression details with consent."

            img_input = gr.Image(label="Upload Image", type="pil")
            prompt_input = gr.Textbox(label="Or Input Loose Description Prompt", placeholder="Enter a loose prompt here if not using an image...", interactive=True)
            img_desc_checkbox = gr.Checkbox(label="Use Over 18 and Uncensored Image Description", interactive=True)

            def set_img_desc_prompt(use_uncensored):
                if use_uncensored:
                    return img_desc_alt
                return img_desc_default

            img_desc_checkbox.change(fn=set_img_desc_prompt, inputs=img_desc_checkbox, outputs=prompt_input)

            get_desc_openai = gr.Button("Generate Description (OpenAI)")
            get_desc_openrouter = gr.Button("Generate Description (OpenRouter)")
            img_desc_out = gr.Textbox(label="Image or Prompt Description", interactive=True)

        # Step 3: Artist Recommendation based on Art Style and Image Description
        with gr.Accordion("Step 3: Recommend an Artist", open=True):
            rec_artist_openai = gr.Button("Recommend Artist (OpenAI)")
            rec_artist_openrouter = gr.Button("Recommend Artist (OpenRouter)")
            artist_rec_out = gr.Textbox(label="Recommended Artist Description", interactive=True)

        # Step 4: Art Style Fusion Prompt
        with gr.Accordion("Step 4: Art Style Fusion Prompt", open=True):
            base_instructions = gr.Textbox(
                label="Base Instructions",
                value="Create a prompt that fuses art styles with visual precision, including details of body types, gender expression, and foreground and background entities.",
                interactive=True
            )
            gen_prompt_openai = gr.Button("Generate Artistic Prompt (OpenAI)")
            gen_prompt_openrouter = gr.Button("Generate Artistic Prompt (OpenRouter)")
            art_prompt_out = gr.Textbox(label="Generated Art Style Fusion Prompt", interactive=False)

        # Step 5: Convert to Compact Stable Diffusion Prompt
        with gr.Accordion("Step 5: Convert to Stable Diffusion Prompt", open=True):
            convert_prompt_openai = gr.Button("Convert to Stable Diffusion Prompt (OpenAI)")
            convert_prompt_openrouter = gr.Button("Convert to Stable Diffusion Prompt (OpenRouter)")
            compact_prompt_out = gr.Textbox(label="Stable Diffusion Compatible Prompt", interactive=False)

        # Define button click actions for each step
        def handle_style(api_key, api_url, model, art_style):
            return gen_style_desc(art_style, api_url, model, api_key)

        def handle_desc(api_key, api_url, model, img, prompt):
            return describe_img_or_prompt(img, prompt, api_url, model, api_key)

        def handle_artist_rec(api_key, api_url, model, art_style, img_desc):
            return recommend_artist(art_style, img_desc, api_url, model, api_key)

        def handle_fusion_prompt(api_key, api_url, model, base_instructions, img_desc, art_style, artist_desc):
            return gen_art_prompt(base_instructions, img_desc, art_style, artist_desc, api_url, model, api_key)

        def handle_sd_prompt_conversion(api_key, api_url, model, fusion_prompt):
            return convert_to_sd_prompt(fusion_prompt, api_url, model, api_key)

        get_style_openai.click(
            fn=handle_style, 
            inputs=[openai_key, openai_url, openai_prompt_model, art_style_input], 
            outputs=[style_desc]
        )
        get_style_openrouter.click(
            fn=handle_style, 
            inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, art_style_input], 
            outputs=[style_desc]
        )
        get_desc_openai.click(
            fn=handle_desc, 
            inputs=[openai_key, openai_url, openai_vision_model, img_input, prompt_input], 
            outputs=[img_desc_out]
        )
        get_desc_openrouter.click(
            fn=handle_desc, 
            inputs=[openrouter_key, openrouter_url, openrouter_vision_model, img_input, prompt_input], 
            outputs=[img_desc_out]
        )
        rec_artist_openai.click(
            fn=handle_artist_rec, 
            inputs=[openai_key, openai_url, openai_prompt_model, art_style_input, img_desc_out], 
            outputs=[artist_rec_out]
        )
        rec_artist_openrouter.click(
            fn=handle_artist_rec, 
            inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, art_style_input, img_desc_out], 
            outputs=[artist_rec_out]
        )
        gen_prompt_openai.click(
            fn=handle_fusion_prompt, 
            inputs=[openai_key, openai_url, openai_prompt_model, base_instructions, img_desc_out, art_style_input, artist_rec_out], 
            outputs=[art_prompt_out]
        )
        gen_prompt_openrouter.click(
            fn=handle_fusion_prompt, 
            inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, base_instructions, img_desc_out, art_style_input, artist_rec_out], 
            outputs=[art_prompt_out]
        )
        convert_prompt_openai.click(
            fn=handle_sd_prompt_conversion, 
            inputs=[openai_key, openai_url, openai_prompt_model, art_prompt_out], 
            outputs=[compact_prompt_out]
        )
        convert_prompt_openrouter.click(
            fn=handle_sd_prompt_conversion, 
            inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, art_prompt_out], 
            outputs=[compact_prompt_out]
        )

    return interface

if __name__ == "__main__":
    build_ui().launch(share=False, server_name="0.0.0.0", server_port=7633)
