import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

# Download the necessary NLTK data files
def setup_nltk():
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk.data.find('corpora/wordnet')
        nltk.data.find('corpora/omw-1.4')
    except LookupError:
        print("Downloading NLTK data files...")
        nltk.download('punkt')          # Tokenizer
        nltk.download('stopwords')      # Stopwords
        nltk.download('wordnet')        # WordNet for stemming
        nltk.download('omw-1.4')        # Open Multilingual Wordnet for stemming
    print("NLTK data files downloaded successfully.")

def processing(text):
    # Converting to lowercase
    text = text.lower()
    # Tokenization
    tokens = word_tokenize(text)
    # Elimination of punctuation 
    tokens = [word for word in tokens if word.isalnum()]
    # Stopword removal
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in stop_words]
    # Lemmatization
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    # Rejoining tokens into a single string
    text = ' '.join(tokens)
    return text