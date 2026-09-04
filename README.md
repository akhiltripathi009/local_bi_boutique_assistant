# Local Business Intelligence Assistant for Apparel Boutiques

An AI-powered local business intelligence platform built for small independent storefronts using **Streamlit**, **Plotly**, and **Ollama** (Llama 3.2/3.1) for offline data computation and complete consumer privacy.

## 🚀 Key Modules Included
1.  **📊 Strategy Analytics Dashboard:** Deep-dive historical aggregations including Merchandise Sell-Through Velocity, Competitor Pricing Index, and Operations Sentiment Matrix.
2.  **⚡ Real-Time Operational Stream:** Interactive data stream tracing simulated customer checkout loops and live B2B supplier restocks directly into the SQLite database.
3.  **⚙️ Master Control Switchboard:** Operations circuit master switch to manually enable/disable transactions or adjust maximum stock bounds across the product catalog.
4.  **💬 Local Copilot Conversational Engine:** Privacy-first AI assistant for querying inventory insights and pricing positions using locally hosted LLMs.
5.  **⚠️ Size Curve Integrity Tracking:** Identifies fragmented stock layouts containing broken size curve metrics and provides automated remedies.

## 📦 Project Structure
- `app.py`: Main Streamlit application dashboard.
- `app1.py`: Enhanced dashboard version featuring luxury branding and Lottie animations.
- `init_db.py`: Database initialization script to setup SQLite schemas and seed initial data.
- `database_manager.py`: Core logic for SQLite database interactions and metric calculations.
- `simulation_engine.py`: Background engine for simulating sales and procurement restocks.
- `catalog_config.py`: Centralized product catalog containing 20 unique apparel styles.
- `insight_generator_ollama.py`: Integration layer for local Ollama LLM interactions.

## 🛠️ Setup & Installation

### Step 1: Install Python dependencies
Ensure you have Python 3.9+ installed, then run:
```bash
pip install -r requirements.txt
```

### Step 2: Download and start Ollama
1. Download Ollama from [ollama.com](https://ollama.com).
2. Start the Ollama server.
3. Pull the required analytical model (the app defaults to `llama3.2:3b` but `llama3.1` is also supported):
```bash
ollama pull llama3.2:3b
```

### Step 3: Initialize the Database
Before running the app for the first time, you must initialize the local SQLite database:
```bash
python init_db.py
```

### Step 4: Run the Application
You can run either the standard or the enhanced dashboard:
**Standard Dashboard:**
```bash
streamlit run app.py
```
**Enhanced Dashboard (with Animations):**
```bash
streamlit run app1.py
```

## 🔄 Workflow & Usage

1.  **Initialization:** Run `init_db.py` to create `boutique_bi.db`. This sets up the sales ledger, purchase ledger, and size matrix tables.
2.  **Analytics:** Open the dashboard and navigate to **Strategy Analytics** to see the current state of the business based on historical data.
3.  **Simulation:** Switch to the **Real-Time Operational Stream**. Check the "Activate Real-Time Ingestion Loop" box to start generating live data. You can adjust the simulation speed and active flash sale markdowns on the sidebar.
4.  **Operational Control:** Use the **Master Control Switchboard** to manage stock levels or stop sales/restocks for specific products if you detect anomalies or reach capacity limits.
5.  **AI Insights:** Use the **Local Copilot** at the bottom of the Analytics page to ask questions like "Which products have the highest sell-through?" or "Summarize pricing positions."

## 🔒 Privacy & Tech Stack
-   **Database:** SQLite (Local file-based)
-   **Frontend:** Streamlit & Plotly
-   **AI Engine:** Ollama (Local LLM Inference)
-   **Simulations:** Custom Python discrete-event logic
