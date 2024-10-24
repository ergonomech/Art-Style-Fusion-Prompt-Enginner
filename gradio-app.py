# MIT License
# Code by ergonomech 2024. Licensed under MIT License.
# Credits to Gradio, PIL (Pillow), requests, and AI APIs.

import gradio as gr
import os
import base64
from utils.api import API
from utils.image import Img
from utils.logger import setup_log
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = setup_log()

# Utility function to safely load environment variables with fallback
def get_env_variable(var_name, default_value):
    return os.getenv(var_name) or default_value

# Function to load the logo as a base64 string
def get_logo_base64():
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
    with open(logo_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to read markdown content from a file
def read_markdown_file(filename):
    file_path = os.path.join(os.path.dirname(__file__), filename)
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

# Load base prompts and art styles from .env
base_prompts = {
    "style": get_env_variable("BASE_STYLE_PROMPT", ""),
    "image": get_env_variable("BASE_IMAGE_PROMPT", ""),
    "artist": get_env_variable("BASE_ARTIST_PROMPT", ""),
    "generate": get_env_variable("BASE_GENERATE_PROMPT", ""),
    "sd_convert": get_env_variable("SD_CONVERT_PROMPT", ""),
}

# Load additional settings for prompt adjustments
nsfw_append = get_env_variable("NSFW_APPEND", "")
no_semantic_explanation = get_env_variable("NO_SEMANTIC_EXPLANATION", "")

# Load art styles as a list
art_styles = get_env_variable("ART_STYLES", "").split(",")

# Gradio UI setup
def build_ui():
    with gr.Blocks(theme='gradio/monochrome', analytics_enabled=False, css=".gradio-container { max-width: 100%; }") as app:
        logo_base64 = get_logo_base64()
        gr.HTML(f"""
        <div style="text-align: center;">
            <img src="data:image/png;base64,{logo_base64}" alt="Logo" style="width: 100%; margin: 20px 0;">
        </div>
        """)

        introduction_text = read_markdown_file("introduction.md")
        gr.Markdown(introduction_text)

        with gr.Accordion("Config", open=False):
            openai_key = gr.Textbox(label="OpenAI Key", value=get_env_variable('OPENAI_API_KEY', ''), type="password")
            openrouter_key = gr.Textbox(label="OpenRouter Key", value=get_env_variable('OPENROUTER_API_KEY', ''), type="password")
            openai_url = gr.Textbox(label="OpenAI URL", value=get_env_variable('OPENAI_URL', 'https://api.openai.com/v1/chat/completions'))
            openrouter_url = gr.Textbox(label="OpenRouter URL", value=get_env_variable('OPENROUTER_URL', 'https://openrouter.ai/api/v1/chat/completions'))
            temp = gr.Slider(label="Temperature", value=float(get_env_variable('TEMPERATURE', '0.7')), minimum=0.1, maximum=1.0)
            top_p = gr.Slider(label="Top P", value=float(get_env_variable('TOP_P', '0.9')), minimum=0.1, maximum=1.0)
            token_limit = gr.Slider(label="Token Limit", value=int(get_env_variable('TOKEN_LIMIT', '2048')), minimum=1000, maximum=4096)
            openai_model = gr.Textbox(label="OpenAI Prompt Model", value=get_env_variable('OPENAI_PROMPT_MODEL', 'gpt-4o'), interactive=True)
            openai_vision = gr.Textbox(label="OpenAI Vision Model", value=get_env_variable('OPENAI_VISION_MODEL', 'gpt-4o-mini'), interactive=True)
            openrouter_model = gr.Textbox(label="OpenRouter Prompt Model", value=get_env_variable('OPENROUTER_PROMPT_MODEL', 'cohere/command-r-08-2024'), interactive=True)
            openrouter_vision = gr.Textbox(label="OpenRouter Vision Model", value=get_env_variable('OPENROUTER_VISION_MODEL', 'qwen/qwen-2-vl-7b-instruct'), interactive=True)

        with gr.Accordion("Art Style Selection", open=False):
            art_style = gr.Dropdown(choices=art_styles, label="Select Art Style")
            style_desc = gr.Code(label="Art Style Description", interactive=True, language="markdown")
            nsfw_checkbox_style = gr.Checkbox(label="Include NSFW Context for Art Style", interactive=True)
            get_style_openai = gr.Button("Generate Style Description (OpenAI)")
            get_style_openrouter = gr.Button("Generate Style Description (OpenRouter)")
        
        with gr.Accordion("Input Description", open=False):
            img_input = gr.Image(label="Upload Image", type="pil")
            prompt_input = gr.Code(label="Or Enter a Description", interactive=True, language="markdown")
            nsfw_checkbox_image = gr.Checkbox(label="Include NSFW Context for Image Description", interactive=True)
            img_desc_output = gr.Code(label="Generated Description", interactive=True, language="markdown")
            get_desc_openai = gr.Button("Generate Image Description (OpenAI)")
            get_desc_openrouter = gr.Button("Generate Image Description (OpenRouter)")

        with gr.Accordion("Artist Recommendation", open=False):
            artist_output = gr.Code(label="Recommended Artist", interactive=True, language="markdown")
            nsfw_checkbox_artist = gr.Checkbox(label="Include NSFW Context for Artist Recommendation", interactive=True)
            get_artist_openai = gr.Button("Recommend Artist (OpenAI)")
            get_artist_openrouter = gr.Button("Recommend Artist (OpenRouter)")
        
        with gr.Accordion("Generate Artistic Prompt", open=False):
            prompt_base = gr.Code(label="Base Instructions", value=base_prompts['generate'], interactive=True)
            gen_prompt = gr.Code(label="Generated Prompt", interactive=True, language="markdown")
            nsfw_checkbox_generate = gr.Checkbox(label="Include NSFW Context for Artistic Prompt", interactive=True)
            generate_prompt_openai = gr.Button("Generate Artistic Prompt (OpenAI)")
            generate_prompt_openrouter = gr.Button("Generate Artistic Prompt (OpenRouter)")

        with gr.Accordion("Stable Diffusion Prompt", open=False):
            sd_prompt_output = gr.Code(label="SD-Compatible Prompt", interactive=True, language="markdown")
            nsfw_checkbox_sd = gr.Checkbox(label="Include NSFW Context for SD Prompt", interactive=True)
            convert_sd_openai = gr.Button("Convert to SD Prompt (OpenAI)")
            convert_sd_openrouter = gr.Button("Convert to SD Prompt (OpenRouter)")

        readme_text = read_markdown_file("README.md")
        with gr.Accordion("Readme", open=False):
            gr.Markdown(readme_text)

        # Define functions for each step (no changes to these)
        def add_nsfw_context(prompt, nsfw):
            if nsfw:
                prompt += f" {nsfw_append}"
            return prompt + f" {no_semantic_explanation} Fit answer appropriately between 150 to 2000 characters."

        def handle_style_desc(api_key, api_url, model, temp, top_p, token_limit, style, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['style'] + f" for the art style: {style}", nsfw)
            return api.req(prompt)

        def handle_image_desc(api_key, api_url, model, temp, top_p, token_limit, img, prompt, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['image'], nsfw)
            img_data = Img.preprocess(img) if img else None
            return api.req(prompt, img_data)

        def handle_artist_rec(api_key, api_url, model, temp, top_p, token_limit, style, img_desc, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['artist'] + f" for style {style} with: '{img_desc}'", nsfw)
            return api.req(prompt)

        def handle_prompt_gen(api_key, api_url, model, temp, top_p, token_limit, base_inst, style, img_desc, artist_desc, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(f"{base_inst} Style: {style}. Inspired by: {artist_desc}. Scene: {img_desc}.", nsfw)
            return api.req(prompt)[:1000]

        def handle_sd_prompt(api_key, api_url, model, temp, top_p, token_limit, fusion_prompt, nsfw):
            api = API(api_key, api_url, model, token_limit, temp, top_p)
            prompt = add_nsfw_context(base_prompts['sd_convert'], nsfw)
            return api.req(f"{prompt} '{fusion_prompt}'")

        # Assign button click actions
        get_style_openai.click(
            fn=handle_style_desc,
            inputs=[openai_key, openai_url, openai_model, temp, top_p, token_limit, art_style, nsfw_checkbox_style],
            outputs=[style_desc]
        )
        get_style_openrouter.click(
            fn=handle_style_desc,
            inputs=[openrouter_key, openrouter_url, openrouter_model, temp, top_p, token_limit, art_style, nsfw_checkbox_style],
            outputs=[style_desc]
        )

        get_desc_openai.click(
            fn=handle_image_desc,
            inputs=[openai_key, openai_url, openai_vision, temp, top_p, token_limit, img_input, prompt_input, nsfw_checkbox_image],
            outputs=[img_desc_output]
        )
        get_desc_openrouter.click(
            fn=handle_image_desc,
            inputs=[openrouter_key, openrouter_url, openrouter_vision, temp, top_p, token_limit, img_input, prompt_input, nsfw_checkbox_image],
            outputs=[img_desc_output]
        )

        get_artist_openai.click(
            fn=handle_artist_rec,
            inputs=[openai_key, openai_url, openai_model, temp, top_p, token_limit, art_style, img_desc_output, nsfw_checkbox_artist],
            outputs=[artist_output]
        )
        get_artist_openrouter.click(
            fn=handle_artist_rec,
            inputs=[openrouter_key, openrouter_url, openrouter_model, temp, top_p, token_limit, art_style, img_desc_output, nsfw_checkbox_artist],
            outputs=[artist_output]
        )

        generate_prompt_openai.click(
            fn=handle_prompt_gen,
            inputs=[openai_key, openai_url, openai_model, temp, top_p, token_limit, prompt_base, art_style, img_desc_output, artist_output, nsfw_checkbox_generate],
            outputs=[gen_prompt]
        )
        generate_prompt_openrouter.click(
            fn=handle_prompt_gen,
            inputs=[openrouter_key, openrouter_url, openrouter_model, temp, top_p, token_limit, prompt_base, art_style, img_desc_output, artist_output, nsfw_checkbox_generate],
            outputs=[gen_prompt]
        )

        convert_sd_openai.click(
            fn=handle_sd_prompt,
            inputs=[openai_key, openai_url, openai_model, temp, top_p, token_limit, gen_prompt, nsfw_checkbox_sd],
            outputs=[sd_prompt_output]
        )
        convert_sd_openrouter.click(
            fn=handle_sd_prompt,
            inputs=[openrouter_key, openrouter_url, openrouter_model, temp, top_p, token_limit, gen_prompt, nsfw_checkbox_sd],
            outputs=[sd_prompt_output]
        )

    return app

if __name__ == "__main__":
    build_ui().launch(server_port=7633)
