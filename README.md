
\documentclass{article}
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{hyperref}
\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{fancyvrb}

\titleformat{\section}{\large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\normalsize\bfseries}{\thesubsection}{1em}{}

\definecolor{lightgray}{gray}{0.95}
\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{lightgray},
  frame=single,
  breaklines=true
}

\title{\textbf{\Huge💵 Global Finance Assistant – Technical Documentation}}
\author{}
\date{}

\begin{document}
\maketitle

\section*{Overview}
A voice-enabled multi-agent assistant that delivers spoken market briefings based on user queries. \\
\textbf{Built with:} CrewAI, LangChain, OpenAI, ChromaDB, Streamlit

\noindent \href{https://finance-research-crew.streamlit.app/}{\textbf{🔗 Live Demo}}

\section*{🔊 Input Flow}
Users can provide input in two ways:
\begin{itemize}
  \item \textbf{Voice} – Recorded via \texttt{audiorecorder}, transcribed using \textbf{AssemblyAI API}
  \item \textbf{Text} – Entered manually into the Streamlit text input field
\end{itemize}
Both types are unified into a single query string before moving to the next stage.

\section*{🔍 Gemini-Based Query Validation}
All inputs go through a Gemini-powered validation step to ensure:
\begin{itemize}
  \item The query is financially relevant
  \item It is ethically appropriate
  \item It has sufficient clarity and specificity
\end{itemize}

\subsection*{Prompt Used}
\begin{lstlisting}[language=json]
You are a compliance officer for a financial assistant.
Evaluate the following query and respond ONLY with JSON like:
{
  "is_finance": true,
  "is_ethical": true,
  "confidence": 42,
  "reason": "Explain the confidence level briefly.",
  "suggestions": [
    "Improved version of the query suggestion 1",
    "Improved version of the query suggestion 2"
  ]
}
Query: {user_query}
\end{lstlisting}

\textbf{If Not Valid:} If either \texttt{is\_finance == false} or \texttt{is\_ethical == false}, the assistant halts and:
\begin{itemize}
  \item Explains why the query was rejected
  \item Offers up to 3 suggestions for improvement
\end{itemize}

\section*{🧠 Multi-Agent Workflow Kickoff}
Once validated, the query triggers the multi-agent finance crew, orchestrated by \textbf{CrewAI}.

\subsection*{Agents Involved}
\begin{itemize}
  \item Confidence Checker – Validates prompt quality
  \item Market Data Researcher – Gathers live market data
  \item Filing Scraper – Extracts recent earnings reports
  \item Retriever – Retrieves past insights from vector DB
  \item Quantitative Analyst – Analyzes risk and EPS surprises
  \item Language Narrator – Crafts Bloomberg-style narrative
  \item Voice Financier – Converts briefing to audio
\end{itemize}

\section*{🔄 Agent Prompts \& Tasks}
\subsection*{1. Confidence Checker}
\textbf{Purpose:} Ensure the query is clear, specific, and similar to indexed prompts.

\textbf{Prompt:}
\begin{lstlisting}
Rate this query on clarity and specificity (1-10):
"{query}"
Respond only with the number.
\end{lstlisting}

\textbf{Output:}
\begin{lstlisting}[language=json]
{
  "confidence_score": 0.92,
  "similarity_score": 0.78,
  "route_to_data_agents": true,
  "suggestions": []
}
\end{lstlisting}

\subsection*{2. Market Data Researcher}
\textbf{Prompt:}
\begin{lstlisting}
Extract company names or tickers related to this query:
"{query}"
\end{lstlisting}

\textbf{Output Example:}
\begin{lstlisting}[language=json]
[
  {
    "ticker": "AAPL",
    "name": "Apple Inc.",
    "price": 194.25,
    "change_percent": 1.25,
    "volume": 98765432,
    "eps_trailing_12m": 5.82
  }
]
\end{lstlisting}

\subsection*{3. Filing Scraper}
\textbf{Prompt:}
\begin{lstlisting}
Extract company names or tickers related to this query:
"{query}"
\end{lstlisting}

\textbf{Output Example:}
\begin{lstlisting}[language=json]
[
  {
    "company": "AAPL",
    "source": "https://investor.apple.com/releases/",
    "summary": "EPS came in at $5.82, outperforming analyst estimates by 8%. Volume was above average..."
  }
]
\end{lstlisting}

\subsection*{4. Retriever}
\textbf{Prompt:} Uses semantic search directly.

\textbf{Output Example:}
\begin{lstlisting}[language=json]
[
  {
    "content": "Apple shares rose after Q2 earnings beat...",
    "similarity": 0.85
  },
  {
    "content": "iPhone sales drove revenue growth in Asia...",
    "similarity": 0.78
  }
]
\end{lstlisting}

\subsection*{5. Quantitative Analyst}
\textbf{Prompt:}
\begin{lstlisting}
Given the following query:
"{query}"

Analyze and summarize:
- Allocation delta
- Earnings surprises
- Risk exposure
- Regional sentiment

Return structured JSON output.
\end{lstlisting}

\textbf{Output Example:}
\begin{lstlisting}[language=json]
{
  "allocation_change": "+5%",
  "earnings_surprise": "+8%",
  "risk_exposure": "Moderate",
  "regional_sentiment": "Positive in APAC"
}
\end{lstlisting}

\subsection*{6. Language Narrator}
\textbf{Prompt:}
\begin{lstlisting}
Write a concise 3-paragraph spoken market briefing:
Query: {query}

Include:
- Exposure change
- Key earnings surprises
- Sentiment summary

Style: Confident, professional, Bloomberg-style tone.
\end{lstlisting}

\textbf{Output Example:}
\begin{quote}
“Apple’s shares rose 1.25\% today, closing at \$194.25, following a strong Q2 earnings beat. EPS came in at \$5.82, outperforming analyst estimates by 8\%. Volume was above average at 98 million shares traded…”
\end{quote}

\subsection*{7. Voice Broadcaster}
Acts as a wrapper around the TTS engine (gTTS / Piper).

\textbf{Output:}
\begin{verbatim}
[AUDIO FILE GENERATED FROM TEXT]
\end{verbatim}

\section*{🎙️ Final Output}
After all agents complete their tasks:
\begin{itemize}
  \item The final briefing is displayed in the UI
  \item An audio file is generated using gTTS or Piper
  \item Users can listen to the briefing instantly
\end{itemize}

\section*{🛠️ Tech Stack}
\begin{itemize}
  \item \textbf{Agents:} CrewAI
  \item \textbf{LLMs:} Gemini, OpenAI
  \item \textbf{Tools:} yfinance, BeautifulSoup, ChromaDB
  \item \textbf{UI:} Streamlit
  \item \textbf{TTS:} gTTS / Piper
  \item \textbf{Hosting:} Streamlit Community Cloud
\end{itemize}

\section*{📈 Performance Benchmarks}
\begin{tabular}{ll}
\textbf{Task} & \textbf{Duration} \\
Confidence Check & 1.2s \\
Market Data Fetch & 3.5s \\
Filing Scraping & 4.8s \\
Quantitative Analysis & 2.1s \\
Narrative Synthesis & 1.8s \\
\textbf{Total Flow} & \textbf{~13.4s} (Sequential execution)
\end{tabular}

\section*{📬 Contact \& Contributions}
For questions, feature requests, or collaboration:

\begin{itemize}
  \item Email: \texttt{you@example.com}
  \item Twitter: \href{https://twitter.com/yourhandle}{@yourhandle}
  \item LinkedIn: \href{https://linkedin.com/in/yourprofile}{linkedin.com/in/yourprofile}
\end{itemize}

\end{document}
