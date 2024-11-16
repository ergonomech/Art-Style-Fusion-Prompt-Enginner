# MIT License
# Code by ergonomech 2024. Licensed under MIT License.
# Credits to Gradio, PIL (Pillow), requests, and AI APIs.

import gradio as gr
import os
import base64
import platform
from utils.api import API
from utils.image import Img
from utils.logger import setup_log
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)
logger = setup_log()

# Detect operating system and hostname
def get_hostname_and_os():
    os_type = platform.system()
    if os_type == 'Windows':
        hostname = os.getenv('COMPUTERNAME')
    else:
        hostname = os.uname().nodename
    return os_type, hostname

os_type, hostname = get_hostname_and_os()

# Utility function to retrieve environment variables with a default fallback
def get_env_variable(var_name, default_value):
    env_value = os.getenv(var_name)
    if env_value:
        return env_value
    return default_value

# Load logo for the UI
def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
    with open(logo_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Read markdown content for the UI
def read_markdown_file(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# NSFW handling function to append context when necessary
def add_nsfw_context(prompt, nsfw):
    if nsfw:
        prompt += f" {nsfw_append}"
    prompt += f" {no_semantic_explanation}"
    return prompt

# Load base prompts and other settings from environment
base_prompts = {
    "style": get_env_variable("BASE_STYLE_PROMPT", ""),
    "image": get_env_variable("BASE_IMAGE_PROMPT", ""),
    "image_nsfw": get_env_variable("BASE_IMAGE_NSFW_PROMPT", ""),
    "artist": get_env_variable("BASE_ARTIST_PROMPT", ""),
    "generate": get_env_variable("BASE_GENERATE_PROMPT", ""),
    "sd_convert": get_env_variable("SD_CONVERT_PROMPT", ""),
}

# Load additional configurations for NSFW and semantic explanations
nsfw_append = get_env_variable("NSFW_APPEND", "")
no_semantic_explanation = get_env_variable("NO_SEMANTIC_EXPLANATION", "")

# Define available art styles from environment variables
art_styles = get_env_variable("ART_STYLES", "").split(",")

# Default configuration for Ollama server and model
DEFAULT_OLLAMA_URL = get_env_variable("OLLAMA_SERVER_URL", "http://data-tamer-01.local:11434")
DEFAULT_MODEL_NAME = get_env_variable("OLLAMA_MODEL_NAME", "hf.co/leafspark/Llama-3.2-11B-Vision-Instruct-GGUF:Q8_0")

# Gradio UI setup function
def build_ui():
    with gr.Blocks(theme='gradio/monochrome', analytics_enabled=False, css=".gradio-container { max-width: 100%; }") as app:
        # Displaying Logo and Introduction Text
        logo_base64 = get_logo_base64()
        gr.HTML(f"<div style='text-align: center;'><img src='data:image/png;base64,{logo_base64}' alt='Logo' style='width: 100%; margin: 20px 0;'></div>")

        introduction_text = read_markdown_file("introduction.md")
        gr.Markdown(introduction_text)

        # Configuration Section: Independent model and setting fields for each platform
        with gr.Accordion("Config", open=False):
            # Ollama-specific server URL and model
            ollama_url = gr.Textbox(label="Ollama Server URL", value=DEFAULT_OLLAMA_URL)
            ollama_prompt_model = gr.Textbox(label="Ollama Prompt Model", value=DEFAULT_MODEL_NAME, interactive=True)
            ollama_vision_model = gr.Textbox(label="Ollama Vision Model", value=DEFAULT_MODEL_NAME, interactive=True)

            # OpenAI and OpenRouter settings for prompt and vision models
            openai_key = gr.Textbox(label="OpenAI Key", value=get_env_variable('OPENAI_API_KEY', ''), type="password")
            openrouter_key = gr.Textbox(label="OpenRouter Key", value=get_env_variable('OPENROUTER_API_KEY', ''), type="password")
            openai_url = gr.Textbox(label="OpenAI URL", value=get_env_variable('OPENAI_URL', 'https://api.openai.com/v1/chat/completions'))
            openrouter_url = gr.Textbox(label="OpenRouter URL", value=get_env_variable('OPENROUTER_URL', 'https://openrouter.ai/api/v1/chat/completions'))
            openai_prompt_model = gr.Textbox(label="OpenAI Prompt Model", value=get_env_variable('OPENAI_PROMPT_MODEL', 'gpt-4o'), interactive=True)
            openai_vision_model = gr.Textbox(label="OpenAI Vision Model", value=get_env_variable('OPENAI_VISION_MODEL', 'gpt-4o-mini'), interactive=True)
            openrouter_prompt_model = gr.Textbox(label="OpenRouter Prompt Model", value=get_env_variable('OPENROUTER_PROMPT_MODEL', 'cohere/command-r-08-2024'), interactive=True)
            openrouter_vision_model = gr.Textbox(label="OpenRouter Vision Model", value=get_env_variable('OPENROUTER_VISION_MODEL', 'qwen/qwen-2-vl-7b-instruct'), interactive=True)

            # Advanced settings for all models
            temp = gr.Slider(label="Temperature", value=float(get_env_variable('TEMPERATURE', '0.7')), minimum=0.1, maximum=1.0)
            top_p = gr.Slider(label="Top P", value=float(get_env_variable('TOP_P', '0.9')), minimum=0.1, maximum=1.0)
            token_limit = gr.Slider(label="Token Limit", value=int(get_env_variable('TOKEN_LIMIT', '8192')), minimum=1000, maximum=8192)

        # Art Style Selection and Generation Section
        with gr.Accordion("Art Style Selection", open=False):
            art_style = gr.Dropdown(choices=art_styles, label="Select Art Style")
            style_desc = gr.Code(label="Art Style Description", interactive=True, language="markdown")
            nsfw_checkbox_style = gr.Checkbox(label="Include NSFW Context for Art Style", interactive=True)
            get_style_openai = gr.Button("Generate Style Description (OpenAI)")
            get_style_openrouter = gr.Button("Generate Style Description (OpenRouter)")
            get_style_ollama = gr.Button("Generate Style Description (Ollama)")

        # Image Analysis Section with Vision Model Selection
        with gr.Accordion("Input Description", open=False):
            img_input = gr.Image(label="Upload Image", type="pil")
            img_desc_output = gr.Code(label="Generated Description", interactive=True, language="markdown")
            nsfw_checkbox_image = gr.Checkbox(label="Include NSFW Context for Image Description", interactive=True)
            get_desc_openai = gr.Button("Generate Image Description (OpenAI)")
            get_desc_openrouter = gr.Button("Generate Image Description (OpenRouter)")
            get_desc_ollama = gr.Button("Generate Image Description (Ollama)")

        # Artist Recommendation Section with Enhanced Visual Style Information
        with gr.Accordion("Artist Recommendation", open=False):
            artist_output = gr.Code(label="Recommended Artist and Unique Style", interactive=True, language="markdown")
            nsfw_checkbox_artist = gr.Checkbox(label="Include NSFW Context for Artist Recommendation", interactive=True)
            get_artist_openai = gr.Button("Recommend Artist (OpenAI)")
            get_artist_openrouter = gr.Button("Recommend Artist (OpenRouter)")
            get_artist_ollama = gr.Button("Recommend Artist (Ollama)")

        # Artistic Prompt Generation Section combining Artist, Style, and Image Descriptions
        with gr.Accordion("Generate Artistic Prompt", open=False):
            prompt_base = gr.Code(label="Base Instructions", value=base_prompts['generate'], interactive=True)
            gen_prompt = gr.Code(label="Generated Prompt", interactive=True, language="markdown")
            nsfw_checkbox_generate = gr.Checkbox(label="Include NSFW Context for Artistic Prompt", interactive=True)
            generate_prompt_openai = gr.Button("Generate Artistic Prompt (OpenAI)")
            generate_prompt_openrouter = gr.Button("Generate Artistic Prompt (OpenRouter)")
            generate_prompt_ollama = gr.Button("Generate Artistic Prompt (Ollama)")

        # Stable Diffusion Prompt Conversion Section
        with gr.Accordion("Stable Diffusion Prompt", open=False):
            sd_prompt_output = gr.Code(label="SD-Compatible Prompt", interactive=True, language="markdown")
            nsfw_checkbox_sd = gr.Checkbox(label="Include NSFW Context for SD Prompt", interactive=True)
            convert_sd_openai = gr.Button("Convert to SD Prompt (OpenAI)")
            convert_sd_openrouter = gr.Button("Convert to SD Prompt (OpenRouter)")
            convert_sd_ollama = gr.Button("Convert to SD Prompt (Ollama)")

        # Define functions to handle detailed and combined outputs

        def handle_style_desc(api_key, api_url, model, temp, top_p, token_limit, style, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['style'] + f" for the art style: {style}", nsfw)
            return api.req(prompt)

        def handle_image_desc(api_key, api_url, model, temp, top_p, token_limit, img, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = base_prompts['image_nsfw'] if nsfw else base_prompts['image']
            prompt = add_nsfw_context(prompt, nsfw)
            img_data = Img.preprocess(img) if img else None
            return api.req(prompt, img_data)

        def handle_artist_rec(api_key, api_url, model, temp, top_p, token_limit, style, img_desc, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['artist'] + f" for style {style} and characteristics: '{img_desc}'", nsfw)
            return api.req(prompt)

        def handle_prompt_gen(api_key, api_url, model, temp, top_p, token_limit, base_inst, style, img_desc, artist_desc, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            
            prompt = f"""
            Scene Description: {img_desc}

            Your task is to enhance this scene so that it embodies the art style of {style} and the unique characteristics of the artist {artist_desc}. Ensure the description incorporates the following details:

            - Quality: Describe the scene as if it were rendered in the highest quality possible, with attention to minute details and textures.
            - Aesthetic Harmony: Apply the visual themes and distinct artistic methods of {artist_desc}.
            - Artistic Style: The overall aesthetic should clearly reflect the {style} style.

            Produce a detailed, cohesive prompt that integrates these aspects.
            """
            
            prompt = add_nsfw_context(prompt, nsfw)
            generated_prompt = api.req(prompt)[:token_limit]
            return generated_prompt

        def handle_sd_prompt(api_key, api_url, model, temp, top_p, token_limit, fusion_prompt, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['sd_convert'] + f" '{fusion_prompt}'", nsfw)
            return api.req(prompt)

        # Assign button click actions with appropriate inputs and functions for each model option
        get_style_openai.click(fn=handle_style_desc, inputs=[openai_key, openai_url, openai_prompt_model, temp, top_p, token_limit, art_style, nsfw_checkbox_style], outputs=[style_desc])
        get_style_openrouter.click(fn=handle_style_desc, inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, temp, top_p, token_limit, art_style, nsfw_checkbox_style], outputs=[style_desc])
        get_style_ollama.click(fn=lambda style, nsfw, ollama_url_val, ollama_model_val: API(url=ollama_url_val, model=ollama_model_val).ollama_generate_completion(add_nsfw_context(f"{base_prompts['style']} {style}", nsfw)), inputs=[art_style, nsfw_checkbox_style, ollama_url, ollama_prompt_model], outputs=[style_desc])

        get_desc_openai.click(fn=handle_image_desc, inputs=[openai_key, openai_url, openai_vision_model, temp, top_p, token_limit, img_input, nsfw_checkbox_image], outputs=[img_desc_output])
        get_desc_openrouter.click(fn=handle_image_desc, inputs=[openrouter_key, openrouter_url, openrouter_vision_model, temp, top_p, token_limit, img_input, nsfw_checkbox_image], outputs=[img_desc_output])
        get_desc_ollama.click(fn=lambda img, nsfw, ollama_url_val, ollama_model_val: API(url=ollama_url_val, model=ollama_model_val).ollama_analyze_image(img), inputs=[img_input, nsfw_checkbox_image, ollama_url, ollama_vision_model], outputs=[img_desc_output])

        get_artist_openai.click(fn=handle_artist_rec, inputs=[openai_key, openai_url, openai_prompt_model, temp, top_p, token_limit, art_style, img_desc_output, nsfw_checkbox_artist], outputs=[artist_output])
        get_artist_openrouter.click(fn=handle_artist_rec, inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, temp, top_p, token_limit, art_style, img_desc_output, nsfw_checkbox_artist], outputs=[artist_output])
        get_artist_ollama.click(fn=lambda style, img_desc, nsfw, ollama_url_val, ollama_model_val: API(url=ollama_url_val, model=ollama_model_val).ollama_generate_completion(add_nsfw_context(f"{base_prompts['artist']} {style} with {img_desc}", nsfw)), inputs=[art_style, img_desc_output, nsfw_checkbox_artist, ollama_url, ollama_prompt_model], outputs=[artist_output])

        generate_prompt_openai.click(fn=handle_prompt_gen, inputs=[openai_key, openai_url, openai_prompt_model, temp, top_p, token_limit, prompt_base, art_style, img_desc_output, artist_output, nsfw_checkbox_generate], outputs=[gen_prompt])
        generate_prompt_openrouter.click(fn=handle_prompt_gen, inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, temp, top_p, token_limit, prompt_base, art_style, img_desc_output, artist_output, nsfw_checkbox_generate], outputs=[gen_prompt])
        generate_prompt_ollama.click(fn=lambda base_inst, style, img_desc, artist_desc, nsfw, ollama_url_val, ollama_model_val: API(url=ollama_url_val, model=ollama_model_val).ollama_generate_completion(add_nsfw_context(f"{base_inst} Style: {style}. Inspired by: {artist_desc}. Scene: {img_desc}.", nsfw)), inputs=[prompt_base, art_style, img_desc_output, artist_output, nsfw_checkbox_generate, ollama_url, ollama_prompt_model], outputs=[gen_prompt])

        convert_sd_openai.click(fn=handle_sd_prompt, inputs=[openai_key, openai_url, openai_prompt_model, temp, top_p, token_limit, gen_prompt, nsfw_checkbox_sd], outputs=[sd_prompt_output])
        convert_sd_openrouter.click(fn=handle_sd_prompt, inputs=[openrouter_key, openrouter_url, openrouter_prompt_model, temp, top_p, token_limit, gen_prompt, nsfw_checkbox_sd], outputs=[sd_prompt_output])
        convert_sd_ollama.click(fn=lambda sd_prompt, nsfw, ollama_url_val, ollama_model_val: API(url=ollama_url_val, model=ollama_model_val).ollama_generate_completion(add_nsfw_context(f"{base_prompts['sd_convert']} '{sd_prompt}'", nsfw)), inputs=[gen_prompt, nsfw_checkbox_sd, ollama_url, ollama_prompt_model], outputs=[sd_prompt_output])

    return app

# Launch Gradio app
if __name__ == "__main__":
    build_ui().launch(server_port=7633, server_name=hostname, debug=False, show_api=False, width="100%", inbrowser=True)
