
from flask import Flask, request, jsonify
import logging
# json and jsonify seems silly
import json
from sentence_transformers import SentenceTransformer, util

_LOGGER = logging.getLogger(__name__)

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
#model = SentenceTransformer('all-MiniLM-L6-v2')


entityNames = {}
entityByDomain = {} # dictionary
sentenceByDomain = {} # dictionary

sentence_embeddings = None
sentence_key_list = None
sentence_value_list = None


def create_app(test_config=None):
    app = Flask(__name__)


    @app.route("/")
    def hello_world():
        return "Hello, World!"


    @app.route('/ask')
    def ask():
        input_text  = request.args.get('q', '')
        print(f"input text: {input_text}")

        user_input_embedding = model.encode([input_text])

        global sentence_embeddings
        global sentence_key_list
        global sentence_value_list

        # TODO: Why [0]
        similarities = util.pytorch_cos_sim(user_input_embedding, sentence_embeddings)

        print(similarities)

        # Find the index of the most similar sentence
        most_similar_idx = similarities.argmax()

        print(f"most_similar_idx: {most_similar_idx}")

        if most_similar_idx == None:
           most_similar_sentence = "No match"
           print("Nothing similar")
        else:

            # Retrieve the most similar sentence
            most_similar_sentence = sentence_key_list[most_similar_idx]

            print("Most similar sentence:", most_similar_sentence)
            print("                      ", sentence_key_list[most_similar_idx])
            print("                      ", sentence_value_list[most_similar_idx])


        response = jsonify(
                {
                    "message": most_similar_sentence
                }
        )
        return response



    # Initialise data
    def loadJson(outputpath):
        print("Loading json")

        with open(outputpath + '/entity-by-domain.json', 'r', encoding='utf-8') as file:
           entityByDomain = json.load(file)

        with open(outputpath + '/sentences.json', 'r', encoding='utf-8') as file:
           sentenceByDomain = json.load(file)

        with open(outputpath + '/entity-names.json', 'r', encoding='utf-8') as file:
           entityNames = json.load(file)

        _LOGGER.debug("Loaded json - done")
        print("Loaded json")

        # Store the sentences in the model
        global sentence_embeddings
        global sentence_key_list
        global sentence_value_list

        sentence_key_list = list(sentenceByDomain.keys())
        sentence_value_list = list(sentenceByDomain.values())

        print("Encoding sentences")
        sentence_embeddings = model.encode(sentence_key_list)
        print("Encoded sentences")


    loadJson("/mnt/dietpi_userdata/homeassistant/custom_components/askbert/server")

    return app
