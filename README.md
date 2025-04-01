# Project Name

Azure Speech Avatar integration with Copilot 

## Features

This project framework provides the following features:

* Avatar demo
* Copilot integration with no OpenAI

## Getting Started
To run the project locally, create a .vscode folder, and put the following contents into the launch.json 
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
          "SPEECH_REGION": "<your-speech-region>",
          "SPEECH_KEY": "<your-speech-key>",

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

### Prerequisites

(ideally very short, if any)

- OS
- Library version
- ...

### Installation

(ideally very short)

- npm install [package name]
- mvn install
- ...

### Quickstart
(Add steps to get up and running quickly)

1. git clone [repository clone url]
2. cd [repository name]
3. ...


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
