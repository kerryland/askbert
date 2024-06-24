import nltk
from sentence_transformers import SentenceTransformer, util

nltk.download('punkt')

# Initialize the sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def tokenize_sentence(sentence):
    return nltk.word_tokenize(sentence)

def remove_similar_words(sent1, sent2):
    # Tokenize the sentences
    tokens1 = tokenize_sentence(sent1)
    tokens2 = tokenize_sentence(sent2)

    # Compute embeddings for all words
    embeddings1 = model.encode(tokens1, convert_to_tensor=True)
    embeddings2 = model.encode(tokens2, convert_to_tensor=True)

    # Find similar words
    similar_words = set()
    for i, token1 in enumerate(tokens1):
        for j, token2 in enumerate(tokens2):
            similarity = util.pytorch_cos_sim(embeddings1[i], embeddings2[j]).item()
            if similarity > 0.7:  # You can adjust the threshold as needed
                similar_words.add(token1)
                similar_words.add(token2)

    # Remove similar words from the original sentences
    filtered_tokens1 = [word for word in tokens1 if word not in similar_words]
    filtered_tokens2 = [word for word in tokens2 if word not in similar_words]

    filtered_sent1 = ' '.join(filtered_tokens1)
    filtered_sent2 = ' '.join(filtered_tokens2)

    return filtered_sent1, filtered_sent2

# Example sentences
sentence1 = "The quick brown fox jumps over the lazy dog."
sentence2 = "A fast brown fox leaps over a sleepy dog."

# Remove similar words
filtered_sentence1, filtered_sentence2 = remove_similar_words(sentence1, sentence2)

print("Original Sentence 1:", sentence1)
print("Original Sentence 2:", sentence2)
print("Filtered Sentence 1:", filtered_sentence1)
print("Filtered Sentence 2:", filtered_sentence2)

