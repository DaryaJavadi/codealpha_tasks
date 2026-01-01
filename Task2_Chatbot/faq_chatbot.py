"""
FAQ Chatbot with Web UI using Flask, NLTK and SpaCy
Install required libraries:
pip install nltk spacy scikit-learn flask
python -m spacy download en_core_web_sm
"""

import nltk
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from flask import Flask, render_template_string, request, jsonify

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

try:
    nltk.data.find('corpora/omw-1.4')
except LookupError:
    nltk.download('omw-1.4')

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Load SpaCy model
nlp = spacy.load('en_core_web_sm')

# FAQ Database
FAQ_DATABASE = [
    {
        "question": "What are your business hours?",
        "answer": "We are open Monday to Friday from 9 AM to 6 PM EST. Weekend support is available via email."
    },
    {
        "question": "How do I reset my password?",
        "answer": "Click on 'Forgot Password' on the login page, enter your email, and follow the instructions sent to your inbox."
    },
    {
        "question": "What payment methods do you accept?",
        "answer": "We accept all major credit cards (Visa, MasterCard, AmEx), PayPal, and bank transfers for enterprise accounts."
    },
    {
        "question": "How can I track my order?",
        "answer": "Log into your account and go to 'My Orders'. Click on the order number to see real-time tracking information."
    },
    {
        "question": "What is your return policy?",
        "answer": "We offer 30-day returns for unused items in original packaging. Refunds are processed within 5-7 business days."
    },
    {
        "question": "Do you offer technical support?",
        "answer": "Yes! Technical support is available 24/7 via live chat, email at support@company.com, or call 1-800-SUPPORT."
    },
    {
        "question": "How do I upgrade my account?",
        "answer": "Go to Account Settings > Subscription > Upgrade Plan. Choose your desired plan and complete the payment process."
    },
    {
        "question": "Is my data secure?",
        "answer": "Yes, we use 256-bit SSL encryption and are SOC 2 Type II certified. Your data is stored in secure, encrypted servers."
    },
    {
        "question": "Can I cancel my subscription anytime?",
        "answer": "Yes, you can cancel anytime from your account settings. You'll have access until the end of your billing period."
    },
    {
        "question": "Do you offer student discounts?",
        "answer": "Yes! Students get 50% off with a valid .edu email address. Apply the discount code at checkout."
    }
]

# Example questions for the UI
EXAMPLE_QUESTIONS = [
    "What are your hours?",
    "How do I reset my password?",
    "What payment methods do you accept?",
    "How can I track my order?",
    "What is your return policy?",
    "Do you offer technical support?"
]


class FAQChatbot:
    def __init__(self, faq_data):
        self.faq_data = faq_data
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Preprocess all FAQ questions
        self.faq_questions = [faq['question'] for faq in faq_data]
        self.processed_questions = [self.preprocess_nltk(q) for q in self.faq_questions]
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.processed_questions)
    
    def preprocess_nltk(self, text):
        """Preprocess text using NLTK"""
        # Tokenization
        tokens = word_tokenize(text.lower())
        
        # Remove stopwords and punctuation
        tokens = [token for token in tokens if token.isalnum() and token not in self.stop_words]
        
        # Lemmatization
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        return ' '.join(tokens)
    
    def preprocess_spacy(self, text):
        """Preprocess text using SpaCy"""
        doc = nlp(text.lower())
        
        # Tokenization, stopword removal, and lemmatization
        tokens = [token.lemma_ for token in doc 
                 if not token.is_stop and not token.is_punct and token.is_alpha]
        
        return ' '.join(tokens)
    
    def find_best_match_tfidf(self, user_query):
        """Find best match using TF-IDF and cosine similarity"""
        # Preprocess user query
        processed_query = self.preprocess_nltk(user_query)
        
        # Transform query to TF-IDF vector
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Get best match
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        return best_idx, best_score
    
    def find_best_match_spacy(self, user_query):
        """Find best match using SpaCy's semantic similarity"""
        user_doc = nlp(user_query.lower())
        
        best_idx = 0
        best_similarity = 0
        
        for idx, question in enumerate(self.faq_questions):
            faq_doc = nlp(question.lower())
            similarity = user_doc.similarity(faq_doc)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_idx = idx
        
        return best_idx, best_similarity
    
    def get_answer(self, user_query, method='tfidf', threshold=0.3):
        """Get answer for user query"""
        if method == 'tfidf':
            best_idx, score = self.find_best_match_tfidf(user_query)
        elif method == 'spacy':
            best_idx, score = self.find_best_match_spacy(user_query)
        else:
            raise ValueError("Method must be 'tfidf' or 'spacy'")
        
        # Check if confidence is above threshold
        if score < threshold:
            return {
                'answer': "I couldn't find a relevant answer. Please rephrase or contact support.",
                'confidence': float(score),
                'matched_question': None
            }
        
        return {
            'answer': self.faq_data[best_idx]['answer'],
            'confidence': float(score),
            'matched_question': self.faq_data[best_idx]['question']
        }


# Initialize Flask app
app = Flask(__name__)

# Initialize chatbot
print("Initializing FAQ Chatbot...")
chatbot = FAQChatbot(FAQ_DATABASE)
print("✓ Chatbot ready!")

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FAQ Chatbot - NLP Powered</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 900px;
            width: 100%;
            display: flex;
            flex-direction: column;
            height: 90vh;
            max-height: 700px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 20px 20px 0 0;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .header-icon {
            width: 50px;
            height: 50px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
        }
        
        .header-text h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header-text p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .method-selector {
            background: #f8f9fa;
            padding: 15px 25px;
            display: flex;
            align-items: center;
            gap: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .method-selector label {
            font-weight: 600;
            color: #333;
        }
        
        .method-selector select {
            padding: 8px 15px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 14px;
            cursor: pointer;
            background: white;
        }
        
        .examples-section {
            background: #f8f9fa;
            padding: 15px 25px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .examples-title {
            font-size: 13px;
            color: #666;
            margin-bottom: 10px;
            font-weight: 600;
        }
        
        .example-chips {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }
        
        .example-chip {
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .example-chip:hover {
            background: #667eea;
            color: white;
            transform: translateY(-2px);
        }
        
        .chat-area {
            flex: 1;
            overflow-y: auto;
            padding: 25px;
            background: #fafafa;
        }
        
        .message {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            flex-shrink: 0;
        }
        
        .message.bot .message-avatar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message.user .message-avatar {
            background: #34495e;
            color: white;
        }
        
        .message-content {
            max-width: 70%;
        }
        
        .message-bubble {
            padding: 12px 18px;
            border-radius: 18px;
            line-height: 1.5;
        }
        
        .message.bot .message-bubble {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .message-meta {
            font-size: 11px;
            color: #999;
            margin-top: 5px;
            padding: 0 8px;
        }
        
        .confidence-badge {
            display: inline-block;
            background: #e8f5e9;
            color: #2e7d32;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 10px;
            font-weight: 600;
            margin-left: 5px;
        }
        
        .confidence-badge.medium {
            background: #fff3e0;
            color: #e65100;
        }
        
        .confidence-badge.low {
            background: #ffebee;
            color: #c62828;
        }
        
        .matched-question {
            font-size: 11px;
            color: #666;
            margin-top: 8px;
            padding: 8px;
            background: #f5f5f5;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }
        
        .typing-indicator {
            display: none;
            padding: 12px 18px;
            background: white;
            border-radius: 18px;
            width: fit-content;
        }
        
        .typing-indicator.active {
            display: block;
        }
        
        .typing-dots {
            display: flex;
            gap: 4px;
        }
        
        .typing-dots span {
            width: 8px;
            height: 8px;
            background: #667eea;
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out;
        }
        
        .typing-dots span:nth-child(1) { animation-delay: -0.32s; }
        .typing-dots span:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        .input-area {
            padding: 20px 25px;
            background: white;
            border-radius: 0 0 20px 20px;
            border-top: 1px solid #e0e0e0;
        }
        
        .input-form {
            display: flex;
            gap: 10px;
        }
        
        .input-form input {
            flex: 1;
            padding: 14px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 15px;
            transition: all 0.3s;
        }
        
        .input-form input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .input-form button {
            padding: 14px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .input-form button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        .input-form button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .welcome-message {
            text-align: center;
            color: #999;
            padding: 40px 20px;
        }
        
        .welcome-message h2 {
            color: #667eea;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-icon">🤖</div>
            <div class="header-text">
                <h1>FAQ Chatbot</h1>
                <p>Powered by NLTK & SpaCy NLP</p>
            </div>
        </div>
        
        <div class="method-selector">
            <label for="method">Matching Method:</label>
            <select id="method">
                <option value="tfidf">TF-IDF with NLTK</option>
                <option value="spacy">Semantic Similarity with SpaCy</option>
            </select>
        </div>
        
        <div class="examples-section">
            <div class="examples-title">💡 Try asking:</div>
            <div class="example-chips">
                {% for example in examples %}
                <div class="example-chip" onclick="askExample('{{ example }}')">{{ example }}</div>
                {% endfor %}
            </div>
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="welcome-message">
                <h2>👋 Welcome!</h2>
                <p>Ask me anything about our services, policies, or support.</p>
                <p style="margin-top: 10px; font-size: 13px;">Click on the example questions above to get started!</p>
            </div>
        </div>
        
        <div class="input-area">
            <form class="input-form" id="chatForm">
                <input 
                    type="text" 
                    id="userInput" 
                    placeholder="Type your question here..." 
                    autocomplete="off"
                    required
                />
                <button type="submit" id="sendBtn">Send</button>
            </form>
        </div>
    </div>
    
    <script>
        const chatArea = document.getElementById('chatArea');
        const chatForm = document.getElementById('chatForm');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');
        const methodSelect = document.getElementById('method');
        let firstMessage = true;
        
        function addMessage(text, isUser, confidence = null, matchedQuestion = null) {
            if (firstMessage) {
                chatArea.innerHTML = '';
                firstMessage = false;
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
            
            let confidenceBadge = '';
            if (confidence !== null) {
                const confidencePercent = (confidence * 100).toFixed(0);
                let badgeClass = 'low';
                if (confidence > 0.6) badgeClass = '';
                else if (confidence > 0.4) badgeClass = 'medium';
                
                confidenceBadge = `<span class="confidence-badge ${badgeClass}">${confidencePercent}% match</span>`;
            }
            
            let matchedQuestionHTML = '';
            if (matchedQuestion) {
                matchedQuestionHTML = `<div class="matched-question">📌 Matched FAQ: "${matchedQuestion}"</div>`;
            }
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${isUser ? '👤' : '🤖'}</div>
                <div class="message-content">
                    <div class="message-bubble">${text}</div>
                    <div class="message-meta">
                        ${new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        ${confidenceBadge}
                    </div>
                    ${matchedQuestionHTML}
                </div>
            `;
            
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function showTyping() {
            const typingDiv = document.createElement('div');
            typingDiv.className = 'message bot';
            typingDiv.id = 'typingIndicator';
            typingDiv.innerHTML = `
                <div class="message-avatar">🤖</div>
                <div class="message-content">
                    <div class="typing-indicator active">
                        <div class="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                    </div>
                </div>
            `;
            chatArea.appendChild(typingDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function hideTyping() {
            const typingIndicator = document.getElementById('typingIndicator');
            if (typingIndicator) {
                typingIndicator.remove();
            }
        }
        
        async function sendMessage(message) {
            addMessage(message, true);
            userInput.value = '';
            sendBtn.disabled = true;
            
            showTyping();
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        method: methodSelect.value
                    })
                });
                
                const data = await response.json();
                hideTyping();
                
                addMessage(
                    data.answer,
                    false,
                    data.confidence,
                    data.matched_question
                );
            } catch (error) {
                hideTyping();
                addMessage('Sorry, something went wrong. Please try again.', false);
            }
            
            sendBtn.disabled = false;
            userInput.focus();
        }
        
        function askExample(question) {
            userInput.value = question;
            sendMessage(question);
        }
        
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const message = userInput.value.trim();
            if (message) {
                sendMessage(message);
            }
        });
        
        userInput.focus();
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, examples=EXAMPLE_QUESTIONS)


@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    method = data.get('method', 'tfidf')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    result = chatbot.get_answer(user_message, method=method)
    
    return jsonify(result)


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Starting FAQ Chatbot Web Server...")
    print("="*60)
    print("\n📱 Open your browser and go to: http://127.0.0.1:5000")
    print("\n💡 Press CTRL+C to stop the server\n")
    app.run(debug=True, host='0.0.0.0', port=5000)