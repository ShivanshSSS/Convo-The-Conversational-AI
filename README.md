
## **Convo: Human-Centric Voice AI**

Convo is a next-generation conversational AI that speaks _with_ you, not _at_ you. Built for seamless, voice-first interaction, it enables natural back-and-forth conversations without wake words or friction. It listens intelligently, responds dynamically, and adapts its personality to fit your context—all in real time.

----------

### **Why Convo?**

Most voice assistants feel robotic, rigid, and reactive. Convo changes that with:

-   **Wake-word-free conversations** that flow naturally once started
-   **Real-time interruption handling** that feels intuitive, not clunky
-   **Adaptive voice personas** that match your mood or task
-   **Deep context tracking** that remembers what you’re talking about—across turns, topics, or even documents
    

Convo doesn’t just talk—it understands.

----------

### **Key Features**

----------

#### 1. **True Voice-to-Voice Interaction**

-   Conversational turn-taking with no need to press buttons or say “Hey” every time
-   Bidirectional audio makes conversations feel organic and human
    

----------

#### 2. **Smart Interruption Management**

-   Real-time detection using RMS audio analysis
-   Adapts on the fly:
    -   Stops instantly when it senses urgence
    -   Pauses if it’s not sure
    -   Finishes its thought if you weren’t really interrupting

Ambient noise? Ignored. You? Prioritized.

----------

#### 3. **Contextual Intelligence**

-   Remembers conversation history
-   Tracks themes and topics
-   Resolves references (“she,” “that report,” etc.)
-   Knows who and what you’re talking about—even across sessions

It’s like talking to someone who’s actually paying attention.

----------

#### 4. **Voice Personalities**

-   Choose from a library of distinct voice personas—calm, bold, curious, warm
-   Dynamically switches voices based on context or user preference
-   Customize pitch, speed, and tonality
-   Create your own voice identity

Make your assistant truly _yours_.

----------

#### 5. **Retrieval-Augmented Intelligence (RAG)**

-   Ask questions based on real documents—PDFs, Word files, CSVs, you name it
-   Convo fetches and cites relevant content on the fly
-   Understands and answers in context across multiple sources
    
From knowledge bases to contracts, Convo brings your content into the conversation.
## Installation


```bash
bash 

# Clone the repository
git clone https://github.com/lifelesscycle/Convo.git

# Navigate to project directory
cd Convo

# Install dependencies
pip install -r requirements.txt

# Initialize chat boy 
python chat.py
```
## API Keys Configuration

Convo requires API keys for various services. Create a `.env` file in the root directory with the following:

```
# Google Gemini AI for large language model
GEMINI_API_KEY=your_gemini_api_key_here

# Deepgram for real-time text to speech generation
DEEPGRAM_API_KEY=your_deepgram_api_key_here

```
Also in the `Logic.py` and `Generate_audio.py` you need to update the Deepgram API key in the following section :
` DEEPGRAM_API_KEY="YOUR KEY GOES HERE " `

## Reference

### Core Classes

-   `Chatbot`: Main interface for the system
-   `Logic`: Handles audio output , RMS analysis and interruption detection and response behavior 
-   `History and Logs`: Maintains conversation context and history
-   `Rag`: Handles document retrieval and knowledge integration
-   `Generate Voice`: Controls voice synthesis
-   `Extra Function`: For intializing and selecting voice models and profiles 


## RAG Document Support

Convo supports the following document formats for its RAG capabilities:

-   PDF (.pdf)
-   Plain text (.txt)
-   Microsoft Word (.docx, .doc)
-   CSV (.csv)
-   JSON (.json)
-   Markdown (.md)
-   HTML (.html)
-   Excel (.xlsx, .xls)

## Voice Profiles

The system includes several pre-configured voice profiles:
|Profile Name|Description|Expressed Gender|
|--|--|--|
|Aura-2-Thalia-en | Clear, Confident, Energetic, Enthusiastic |Feminine
|Aura-2-Odysseus-en| Calm, Smooth, Comfortable, Professional| Masculine
|Aura-2-Arcas-en| Natural, Smooth, Clear, Comfortable | Masculine
|Aura-2-cora-en|Smooth, Melodic, Caring|Feminine

## Requirements

-   Python 3.8+
-   PyTorch 1.9+
-   CUDA-compatible GPU recommended for optimal performance
-   Minimum 8GB RAM (16GB+ recommended)
-   Microphone and speakers/headphones

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Built With

-   [OpenAI Whisper](https://github.com/openai/whisper) for ASR
-   [Google Gemini API](https://gemini.google.com) for large language model capabilities
-   [Deepgram](https://deepgram.com) for real-time speech recognition
-   [PyTorch](https://pytorch.org) for the underlying machine learning framework
-   [Hugging Face](https://huggingface.co) for NLP and embeddings
