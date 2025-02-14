# Platonic Dialogue
A small CLI to help you write a Platonic dialogue with LangChain and OpenAI API.

## Installation
```sh
git clone 
cd dialogue
pip install -r requirements.txt
```

## Running
Create `.env` file and insert your OpenAI API key there.
```
OPENAI_API_KEY=your-key-here
```
Then run
```sh
python app.py
```

## Roadmap
- [ ] Refactor and mask code smell
- [ ] Stream text outputs
- [ ] Handle LLM memory buffering properly
- [ ] Add configurable generation config, templates, and roles
- [ ] Add more API providers and self-hosted LLMs
- [ ] Option to have 3+ interlocutors