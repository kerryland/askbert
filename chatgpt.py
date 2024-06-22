# XY
from sentence_transformers import SentenceTransformer, util
import re
import spacy

# Load pre-trained SentenceTransformer model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Load spaCy model for NER
nlp = spacy.load('en_core_web_sm')

# Define multiple template sentences with placeholders
templates = [
    "set the heat pump to [temperature] degrees",
    "turn the heat pump to [temperature] degrees",
    "adjust the heat pump to [temperature] degrees",
    "set the bedroom light to [color]",
    "turn the bedroom light to [color]",
    "change the bedroom light to [color]"
]

# Function to extract variable part using regex
def extract_variable(sentence, template):
    # Create a regex pattern from the template
    pattern = re.sub(r'\[.*?\]', '(.+)', template)
    match = re.match(pattern, sentence)
    if match:
        return match.group(1).strip()  # Return the captured variable
    return None

# Function to identify the type of variable
def identify_variable_type(variable):
    # Check if variable is a number (temperature)
    if re.match(r'^\d+$', variable):
        return "temperature"
    # Check if variable is a color
    if variable.lower() in ["red", "green", "blue", "yellow", "purple", "orange", "white", "black"]:
        return "color"
    return "unknown"

# Example input sentences
input_sentences = [
    "turn the heat pump to 25 degrees",
    "set the bedroom light to blue"
]

for input_sentence in input_sentences:
    # Encode the input sentence
    input_embedding = model.encode(input_sentence)
    
    # Find the best matching template
    best_match = None
    best_similarity = -1

    for template in templates:
        template_embedding = model.encode(template.replace("[temperature]", "").replace("[color]", ""))
        similarity = util.pytorch_cos_sim(template_embedding, input_embedding).item()
        
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = template

    # Print the best matching template and similarity score
    print(f"Input sentence: {input_sentence}")
    print(f"Best matching template: {best_match}")
    print(f"Similarity: {best_similarity}")

    # Extract the variable part using the best matching template
    if best_match:
        variable_part = extract_variable(input_sentence, best_match)
        if variable_part:
            variable_type = identify_variable_type(variable_part)
            print(f"Extracted variable: {variable_part}")
            print(f"Variable type: {variable_type}")
        else:
            print("No variable part found")
    print()  # Newline for better readability

