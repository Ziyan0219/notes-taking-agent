# Notes Taking Agent 📚

An AI-powered system that converts PDF courseware into structured, easy-to-understand notes with practice exercises. Built with LangGraph and FastAPI.

## Features ✨

- **Intelligent Topic Analysis**: Automatically identifies main topics and themes in PDF courseware
- **Formula Extraction**: Extracts and organizes mathematical formulas with derivations
- **Structured Note Generation**: Creates well-organized study notes with clear relationships
- **Practice Questions**: Generates exercises for each formula and concept
- **Comprehensive Exercises**: Creates integrated problems combining multiple concepts
- **Cost-Optimized**: Minimizes LLM API calls through intelligent caching and processing

## Architecture 🏗️

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Web Interface                    │
├─────────────────────────────────────────────────────────────┤
│                    LangGraph Agent Flow                     │
├─────────────────────────────────────────────────────────────┤
│  PDF Parser  │  Content    │  Note       │  Exercise       │
│  Module      │  Analyzer   │  Generator  │  Generator      │
├─────────────────────────────────────────────────────────────┤
│                    Data Storage Layer                       │
└─────────────────────────────────────────────────────────────┘
```

## Installation 🚀

### Prerequisites

- Python 3.11+
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Ziyan0219/notes-taking-agent.git
   cd notes-taking-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.template .env
   # Edit .env file and add your OpenAI API key
   ```

5. **Run the application**
   ```bash
   python app/main.py
   ```

6. **Access the web interface**
   Open your browser and go to `http://localhost:8000`

## Usage 📖

1. **Upload PDF**: Use the web interface to upload your PDF courseware
2. **Processing**: The AI agent will automatically:
   - Analyze the document structure
   - Identify main topics and subtopics
   - Extract formulas and derivations
   - Generate structured notes
   - Create practice exercises
3. **Download**: Get your generated notes and exercises

## Project Structure 📁

```
notes-taking-agent/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── models/              # Data models and schemas
│   ├── agents/              # LangGraph agent implementations
│   ├── services/            # Business logic services
│   ├── utils/               # Utility functions
│   └── templates/           # HTML templates
├── tests/                   # Test files
├── docs/                    # Documentation
├── static/                  # Static files (CSS, JS, images)
├── uploads/                 # Uploaded PDF files
├── requirements.txt         # Python dependencies
├── .env.template           # Environment variables template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## Configuration ⚙️

### Environment Variables

Copy `.env.template` to `.env` and configure:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# File Upload Configuration
MAX_FILE_SIZE=50MB
UPLOAD_DIR=./uploads
```

## Development 🛠️

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black app/
flake8 app/
```

### Development Mode

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints 🔌

- `GET /` - Web interface
- `POST /upload` - Upload PDF file
- `POST /process` - Start PDF processing
- `GET /status/{filename}` - Get processing status
- `GET /download/{filename}` - Download generated notes
- `GET /health` - Health check

## Cost Optimization 💰

The system implements several strategies to minimize LLM API costs:

1. **Single PDF Parse**: Content is extracted once and cached
2. **Intelligent Chunking**: Large documents are processed in logical chunks
3. **Context Reuse**: Previous analysis results are passed between processing steps
4. **Batch Processing**: Multiple related tasks are combined in single API calls

## Contributing 🤝

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support 💬

If you encounter any issues or have questions, please:

1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/Ziyan0219/notes-taking-agent/issues)
3. Create a new issue if needed

## Roadmap 🗺️

- [ ] Support for multiple PDF formats
- [ ] Integration with more AI models
- [ ] Advanced formula recognition
- [ ] Export to multiple formats (Word, LaTeX, etc.)
- [ ] Collaborative note editing
- [ ] Mobile app support

---

Made with ❤️ by [Ziyan](https://github.com/Ziyan0219)

