
# Art Style Fusion Prompt Engineering

Art Style Fusion Prompt Engineering is a Gradio-based web application that allows users to generate prompts that blend art styles, 
image descriptions, and artist inspirations for creative projects like image generation using advanced LLMs and Stable Diffusion.

Art Style Fusion Prompt Engineering is a Gradio app that blends art styles, descriptions, and artist recommendations into prompts for T5 text encoders (Tested Heavily with Flux)

## Features
1. **Art Style Selection**: Choose from a wide range of art styles like Anime, Surrealism, Renaissance, and more.
2. **Image or Loose Prompt Input**: Upload an image for description or input a loose text prompt directly.
3. **Artist Recommendations**: Receive artist recommendations based on the selected style and image description.
4. **Artistic Prompt Generation**: Generate a detailed artistic prompt that combines style, scene description, and artist influence.
5. **Stable Diffusion Prompt Conversion**: Compact and convert the artistic prompt into a 300-character prompt suitable for Stable Diffusion models.

## Installation
To run this project locally, follow these steps:

### Prerequisites
- Python 3.8+
- Pip (Python package installer)

### Clone the Repository
```
clone me
```

### Install Required Packages
Install the dependencies using:
#### Pip Install
```
pip install -r requirements.txt
```
#### Conda Install
```
conda install -c conda-forge gradio pillow requests
```

### Run the Application
Run the Gradio app with the following command:
```
python gradio-app-art-style-fusion.py
```
By default, the app will be available at `http://localhost:7633`.

## Credits
This project makes use of the following third-party technologies:
- **[Gradio](https://gradio.app/)**: For building the interactive UI.
- **[Pillow (PIL)](https://python-pillow.org/)**: For image processing and manipulation.
- **[Requests](https://docs.python-requests.org/en/master/)**: For handling API requests and communication with LLMs.

## How to Use
1. **Configuration**: Input your API keys for OpenAI and OpenRouter in the Configuration section.
2. **Step 1: Select Art Style**: Choose an art style from the dropdown menu and generate its description.
3. **Step 2: Input Description**: Upload an image or provide a loose prompt to describe the scene or concept.
4. **Step 3: Get Artist Recommendation**: Click the button to receive an artist recommendation that matches the selected style.
5. **Step 4: Generate Artistic Prompt**: Generate a fusion prompt that combines all the details. Compatible with Flux and other T5 models.
6. **Step 5: Convert to Stable Diffusion Prompt**: Use the LLM to compact the generated prompt for Stable Diffusion models. (this does not always work in one shot!)

## License
This project is licensed under the MIT License. See the LICENSE file for more details.
