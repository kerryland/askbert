from sentence_transformers import SentenceTransformer, util
from sklearn.preprocessing import normalize

import json
import logging
import numpy as np
import torch


_LOGGER = logging.getLogger(__name__)

# Load the model
#model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

entityNames = {}
entityByDomain = {} # dictionary
sentenceByDomain = {} # dictionary

servicesByDomain = {}
service_sentence_by_domain = {}
service_id_by_dmain = {}

entity_sentence_embeddings = None
entity_sentence_key_list = None
entity_id_list = None

class ServiceEmbeddings:
    sentence = None
    embedding = None
    service_id = None


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


    print("Encoding entity sentences (e.g. light kitchen lights)")
    entity_sentence_embeddings = model.encode(entity_sentence_key_list)
    print()

    print("Encoding service sentences (e.g. turn on)")
    # Iterate through the services
    # Result is dictionary of domains, containing a list of
    # service description embeddings and names.
    for service_desc, inner_dict in sentenceByDomain.items():
        print(service_desc)

        # Encode the service description
        service_sentence_embedding = model.encode([service_desc])

        # Iterate through the service ids
        # e.g. "light", and "media_player", both which have "turn_on" verb
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


def findLikelyEntities(input_text):
    user_input_embedding = model.encode([input_text])

    # Find most likley entities
    similarities = util.pytorch_cos_sim(user_input_embedding, entity_sentence_embeddings)[0]

    # Find the index of the most similar sentence
    most_similar_entity_idx = similarities.argmax()

    top_k = 10
    top_k_values, top_k_indices = torch.topk(similarities, k=top_k)

    fine_tune_embeddings = model.encode([""])

    ft_ptr = 0
    ptr = 0
    for i in top_k_indices:

        entity_id = entity_id_list[i]
        domain_id = entity_id.split(".")[0]

        print(f"matching entity: {entity_id}")

        #if (top_k_values[ptr] > 0.7):
        if True:
            print(f"similar_idx: {i}. {top_k_values[ptr]}")

            # Find services for domain
            services = servicesByDomain.get(domain_id)
            if services == None:
                print(f"No services for domain {domain_id}")
            else:
                for se in services:
                    print(f"Found service {se.service_id} for {domain_id}")

                    sl = np.concatenate([entity_sentence_embeddings[i], se.embedding])

                    #se.embedding = service_sentence_embedding
                    #se.service_id = service_id
        else:
            print(f"Not good enough entity: {entity_id}. {top_k_values[ptr]}")

        ptr += 1

    similarities = util.pytorch_cos_sim(user_input_embedding, fine_tune_embeddings)[0]
    print(similarities)
    most_similar_service_idx = similarities.argmax()

    if most_similar_entity_idx == None:
       most_similar_sentence = "No match"
       print("Nothing similar")
    else:

        # Retrieve the most similar sentence
        most_similar_sentence = entity_sentence_key_list[most_similar_entity_idx]

        print("Most similar entity:", most_similar_sentence)
        print("                    ", entity_sentence_key_list[most_similar_entity_idx])

        print(f"Matching service idx: {most_similar_service_idx}")

        try:
            print(f"Matching service: {servicesByDomain.get(domain_id)[most_similar_service_idx].service_id}")
        except:
            print("Match went bang")
           

loadJson("/mnt/dietpi_userdata/homeassistant/custom_components/askbert/server")

while True:
    query = input("Enter a query (or type 'quit' to exit): ")
    print(f"Got >{query}<")
    if query.lower() == "quit":
        break

    findLikelyEntities(query)




"""
# Define common and variable parts
common_part = "tell me about the"
variable_parts = ["blue car", "red car", "yellow car"]

# Encode the common part
common_embedding = model.encode(common_part)

# Encode the variable parts
variable_embeddings = model.encode(variable_parts)

# Combine embeddings (simple addition in this case)
combined_embeddings = np.array([common_embedding + var_emb for var_emb in variable_embeddings])

# Normalize combined embeddings (optional but often useful for cosine similarity)
#combined_embeddings = normalize(combined_embeddings)

# Function to find the closest match for a new query
def find_closest_match(query, combined_embeddings, variable_parts):
    query_embedding = model.encode(query).reshape(1, -1)
    query_embedding = normalize(query_embedding)
    # Compute cosine similarities
    similarities = util.cos_sim(query_embedding, combined_embeddings)
    # Find the index of the closest match
    closest_idx = np.argmax(similarities)
    return variable_parts[closest_idx]

# Test with a new query
query = "tell me about the red car"
closest_match = find_closest_match(query, combined_embeddings, variable_parts)
print(f"The closest match for the query '{query}' is '{closest_match}'")

"""
