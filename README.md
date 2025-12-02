Real Estate Price Analyzer & Chatbot

A full-stack AI-powered tool for analyzing real estate prices, comparing areas, generating trends, and chatting with an intelligent assistant — built using Django, React, Recharts, and OpenAI/Grok LLM.

Features

🧠 AI Chatbot

Ask anything about prices, areas, or trends
Powered by LLM (Grok / OpenAI depending on configuration)
Smart responses based on your real dataset

📊 Interactive Price Charts
Line graph for single-location yearly price trends
Multi-area comparison charts
Clean dark mode + glass-morphism UI ✨

🗂️ Filtered Data Table
Displays cleaned dataset slice for your query
Elegant glass UI styling
Responsive for all devices

🔎 Summary Insights
Auto-generated summary for each query
Average price
Record count
Quick interpretation

🛠️ Tech Stack

Frontend
React (CRA)
React Bootstrap
Recharts (Data Visualization)
Custom UI (Glass-morphism + Dark theme)

Backend
Django REST Framework
Pandas for Excel processing
Custom API endpoints for:
/api/analyze/?area=Akurdi
/api/compare/?areas=Akurdi,Pimple Saudagar
/api/chat/

AI
LLM integration
Custom prompt pipeline

📁 Project Structure
realestate-chatbot/
│
├── api/
│   ├── views.py       # Analysis, comparison, chatbot API
│   ├── urls.py
│   └── data/realestate.xlsx
│
├── frontend/client/
│   ├── public/        # Assets (bot.png, favicon, index.html)
│   └── src/
│       ├── components/
│       │   ├── PriceChart.js
│       │   ├── SummaryBox.js
│       │   ├── DataTable.js
│       │   ├── ChatInput.js
│       │   └── Navbar.js
│       ├── App.js
│       └── index.js
│
└── README.md

⚙️ Environment Variables

Create .env inside backend folder:
GROK_API_KEY=your_grok_key_here

🚀 Run Locally
Backend
cd api
pip install -r requirements.txt
python manage.py runserver

Frontend
cd frontend/client
npm install
npm start
