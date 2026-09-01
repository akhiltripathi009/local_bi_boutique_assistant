# Local Business Intelligence Assistant for Apparel Boutiques

An AI-powered local business intelligence platform built for small independent storefronts using **Streamlit**, **Plotly**, and **Ollama** (Llama 3.1) for offline data computation and complete consumer privacy.

## 🚀 Key Modules Included
1. **Real-time Event Ingestion & Animation:** Interactive data stream tracing simulated customer checkout loops and live B2B supplier restocks without resetting component parameters.
2. **Size Curve Integrity Tracking:** Identifies fragmented stock layouts containing broken size curve metrics.
3. **Sentiment Parsing Matrices:** Classifies customer logs focusing on structural product design vectors like apparel fit or fabric failures.
4. **Offline Privacy Engine:** Outlines how to query data fields using locally hosted instances over local host architectures via Ollama.

## 📦 Running the Application Locally

### Step 1: Install Python dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Download and start Ollama
1. Download Ollama for your OS from [ollama.com](https://ollama.com)
2. Run the application or terminal server environment.
3. Pull the required analytical model:
```bash
ollama pull llama3.1
```

### Step 3: Run the Dashboard
```bash
streamlit run app.py
```
