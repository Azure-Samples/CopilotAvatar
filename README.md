# Copilot Avatar

The text-to-speech avatar transforms written content into a digital video featuring a photorealistic human, whether using a prebuilt avatar or a customized version, all while delivering a natural-sounding voice. These avatar videos can be generated either asynchronously or in real-time. Developers have the option to create applications that incorporate the text-to-speech avatar through an API or utilize a content creation tool within Speech Studio to produce video content without any coding experience. Powered by advanced neural network models, this feature allows users to create lifelike, high-quality synthetic avatar videos for a variety of applications, all while upholding responsible AI practices.

The objective of this project is to facilitate seamless integration with Microsoft Copilot.

Microsoft 365 Copilot is a sophisticated artificial intelligence tool aimed at boosting productivity and simplifying everyday tasks. Integrated within Microsoft 365 applications, Copilot serves as an intelligent assistant, offering real-time support and insights. Whether you’re composing emails, drafting documents, or organizing your calendar, Copilot enables you to work more efficiently and effectively.

A standout feature of Copilot is its ability to comprehend and respond to natural language inquiries. You can request Copilot to execute tasks, locate information, or generate recommendations simply by typing or speaking your needs. For instance, you might ask Copilot to summarize a lengthy document, retrieve pertinent emails, or draft a reply on your behalf. This intuitive interaction allows you to concentrate on what truly matters while Copilot manages the repetitive and time-consuming aspects of your work.

Moreover, Copilot harnesses the power of artificial intelligence to deliver personalized assistance tailored to your unique requirements. It learns from your interactions and adapts to your preferences, ensuring that the support you receive is consistently relevant and beneficial. With Copilot, you can enhance collaboration with your team, maintain organization, and make informed decisions with ease.

## Features

* Simple avatar demonstration
* Integration of avatars with Copilot, eliminating the need for GPT models
* Container app integration.

## Built With
* [![Azure][Azure-logo]][Azure-url]
* [![Python][Python-logo]][Python-url]
* [![Fastapi][Fastapi-logo]][Fastapi-url]
* [![Docker][Docker-logo]][Docker-url]

## Getting Started

Follow these steps to run the project locally.

### Prerequisites

- Python 3.12+  
- Docker  
- VS Code  

### Installation

1. Clone the repository:
    ```git
    git clone ..
    cd ..
    ```

2. Now open the cloned repo in a command line or VSCode, and set up the Python environment and install project dependencies:
    ```sh
    python -m venv venv
    venv\Scripts\activate  # On Linux use `source venv/bin/activate`
    pip install -r requirements.txt
    ```
3. To run the project locally, create a .vscode folder, and put the following contents into the launch.json 
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run Flask (app.py)",
            "type": "debugpy",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "app.py",
                "FLASK_RUN_HOST": "0.0.0.0",
                "FLASK_RUN_PORT": "5000",
                "SPEECH_REGION": "<your-region>",
                "SPEECH_KEY": "<your-key>",
                "COPILOT_ENDPOINT": "<your-copilot-endpoint>"
            },
            "args": [
                "run"
            ],
            "jinja": true,
            "console": "integratedTerminal"
        }
    ]
}
```



## Demo

A demo app is included to show how to use the project.

To run the demo, follow these steps:

(Add steps to start up the demo)

1.
2.
3.

## Resources

(Any additional resources or related projects)

- Link to supporting information
- Link to similar sample
- ...


<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/ajakupov/NewsExplorer.svg?style=for-the-badge
[contributors-url]: https://github.com/ajakupov/NewsExplorer/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/ajakupov/NewsExplorer.svg?style=for-the-badge
[forks-url]: https://github.com/ajakupov/NewsExplorer/network/members
[stars-shield]: https://img.shields.io/github/stars/ajakupov/NewsExplorer.svg?style=for-the-badge
[stars-url]: https://github.com/ajakupov/NewsExplorer/stargazers
[issues-shield]: https://img.shields.io/github/issues/ajakupov/NewsExplorer.svg?style=for-the-badge
[issues-url]: https://github.com/ajakupov/NewsExplorer/issues
[license-shield]: https://img.shields.io/github/license/ajakupov/NewsExplorer.svg?style=for-the-badge
[license-url]: https://github.com/ajakupov/NewsExplorer/blob/main/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/company/microsoft/
[product-screenshot]: https://learn.microsoft.com/en-us/azure/ai-services/containers/media/container-security.svg
[Python-logo]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54
[Python-url]: https://www.python.org
[Django-logo]: https://img.shields.io/badge/django-35495E?style=for-the-badge&logo=django&logoColor=4FC08D
[Django-url]: https://www.djangoproject.com
[Fastapi-logo]: https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi
[Fastapi-url]: https://fastapi.tiangolo.com
[Nodejs-logo]: https://img.shields.io/badge/node.js-339933?style=for-the-badge&logo=Node.js&logoColor=white
[Nodejs-url]: https://nodejs.org/en
[Docker-logo]: https://img.shields.io/badge/docker-257bd6?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com
[Streamlit-logo]: https://img.shields.io/badge/-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white
[Streamlit-url]: https://streamlit.io
[Ollama-logo]: https://img.shields.io/badge/-Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white
[Ollama-url]: https://ollama.com
[Azure-logo]: https://img.shields.io/badge/azure-0089D6?style=for-the-badge&logo=azure&logoColor=white
[Azure-url]: https://azure.microsoft.com/en-us/

