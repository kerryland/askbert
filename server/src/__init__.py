
import nltk
from flask import Flask, request, jsonify
from itertools import islice
import torch
import numpy as np

import logging
# json and jsonify seems silly
import json
from sentence_transformers import SentenceTransformer, util

_LOGGER = logging.getLogger(__name__)

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
#model = SentenceTransformer('all-MiniLM-L6-v2')

nltk.download('punkt')

entityNames = {}
entityByDomain = {} # dictionary
sentenceByDomain = {} # dictionary

servicesByDomain = {}

entity_sentence_embeddings = None
entity_sentence_key_list = None
entity_id_list = None

class ServiceEmbeddings:
    embedding = None
    service_id = None

def create_app(test_config=None):
    app = Flask(__name__)


    @app.route("/")
    def hello_world():
        return "Hello, World!"


    @app.route('/ask')
    def ask():
        input_text  = request.args.get('q', '')
        print(f"input text: {input_text}")

        # TODO: add 'convert_to_tensor=True'???
        user_input_embedding = model.encode([input_text])

        global entity_sentence_embeddings
        global entity_sentence_key_list
        global entity_id_list
        global servicesByDomain

        # TODO: Why [0]
        similarities = util.pytorch_cos_sim(user_input_embedding, entity_sentence_embeddings)[0]

        print(similarities)

        # Find the index of the most similar sentence
        most_similar_idx = similarities.argmax()

        top_k = 3
        top_k_values, top_k_indices = torch.topk(similarities, k=top_k)

        fine_tune_embeddings = []

        ft_ptr = 0
        ptr = 0
        for i in top_k_indices:
            if (top_k_values[ptr] > 0.7):
                entity_id = entity_id_list[i]
                domain_id = entity_id.split(".")[0]
                print(f"similar_idx: {i}. {top_k_values[ptr]}")
                print(f"matching entity: {entity_id}")

                # Find services for domain
                services = servicesByDomain.get(domain_id)
                if services == None:
                    print(f"No services for domain {domain_id}")
                else:
                    for se in services:
                        print(f"Found service {se.service_id}")

                        fine_tune_embeddings.append(entity_sentence_embeddings[i] + se.embedding)
                        #se.embedding = service_sentence_embedding
                        #se.service_id = service_id
            ptr += 1

        similarities = util.pytorch_cos_sim(user_input_embedding, np.array(fine_tune_embeddings))[0]
        print(similarities)
        #most_similar_idx = similarities.argmax()

        if most_similar_idx == None:
           most_similar_sentence = "No match"
           print("Nothing similar")
        else:

            # Retrieve the most similar sentence
            most_similar_sentence = entity_sentence_key_list[most_similar_idx]

            print("Most similar sentence:", most_similar_sentence)
            print("                      ", entity_sentence_key_list[most_similar_idx])

            

        # Refine 
        """
        # Combine sentences with their similarity scores and original indices
        sentence_similarity_pairs = [(sentence_key_list[i], similarities[i], i) for i in range(len(sentence_key_list))]

        sorted_sentence_similarity_pairs = sorted(sentence_similarity_pairs, key=lambda x: x[1], reverse=True)

        # Print sorted sentences
        print("Sorted sentences based on similarity to the input sentence:")
        for sentence, similarity, index in islice(sorted_sentence_similarity_pairs, 3):

            print(f"> {sentence}")

            # This is a significant performance hit
            # Remove matched words from the input
            filtered_input, filtered_target = remove_similar_words(input_text, sentence)

            print("  Filtered Input :", filtered_input)
            print("  Filtered Target:", filtered_target)

            # Find the location (TODO) and the domain of the candidate sentence
            #for entity_id in sentence_value_list[index]:
            #    print("     ", entity_id) 
        """


        response = jsonify(
                {
                    "message": most_similar_sentence
                }
        )
        return response

    def tokenize_sentence(sentence):
        return nltk.word_tokenize(sentence)

    def remove_similar_words(sent1, sent2):
        # Tokenize the sentences
        tokens1 = tokenize_sentence(sent1)
        tokens2 = tokenize_sentence(sent2)

        # Compute embeddings for all words
        embeddings1 = model.encode(tokens1)
        embeddings2 = model.encode(tokens2)

        # Find similar words
        similar_words = set()
        for i, token1 in enumerate(tokens1):
            for j, token2 in enumerate(tokens2):
                similarity = util.pytorch_cos_sim(embeddings1[i], embeddings2[j]).item()
                if similarity > 0.7:  # adjust the threshold as needed
                    similar_words.add(token1)
                    similar_words.add(token2)

        # Remove similar words from the original sentences
        filtered_tokens1 = [word for word in tokens1 if word not in similar_words]
        filtered_tokens2 = [word for word in tokens2 if word not in similar_words]

        filtered_sent1 = ' '.join(filtered_tokens1)
        filtered_sent2 = ' '.join(filtered_tokens2)

        return filtered_sent1, filtered_sent2


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
        global entity_sentence_embeddings
        global entity_sentence_key_list
        global entity_id_list
        global servicesByDomain

        entity_sentence_key_list = []
        entity_id_list = list(entityNames.keys())


        # Iterate through the entities
        for entity_id, inner_dict in entityNames.items():
            entity_desc = inner_dict[0]
            print(entity_desc)
                
            #TODO: Proper i18n and map to 'better' english for some domains
            entity_domain_name = entity_id.split(".")[0].replace("_", " ")

            entity_sentence_key_list.append(entity_desc + " " + entity_domain_name)

        for s in entity_sentence_key_list:
            print(">" + s + "<")


        print("Encoding entity sentences")
        entity_sentence_embeddings = model.encode(entity_sentence_key_list)
        print("Encoded entity sentences")

        # Iterate through the services
        # Result is dictionary of domains, containing a list of
        # service description embeddings and names.
        for service_desc, inner_dict in sentenceByDomain.items():
            print(service_desc)

            # Encode the service description
            service_sentence_embedding = model.encode([service_desc])

            # Iterate through the service ids
            for service_id, values in inner_dict.items():

                se = ServiceEmbeddings()
                se.embedding = service_sentence_embedding
                se.service_id = service_id

                # Get the existing mappings for this domain
                service_domain_id = service_id.split(".")[0]
                services = servicesByDomain.get(service_domain_id)

                if (services == None):
                    servicesByDomain[service_domain_id] = []

                # Add reference to this new mapping
                servicesByDomain[service_domain_id].append(se)
               


    loadJson("/mnt/dietpi_userdata/homeassistant/custom_components/askbert/server")

    return app
