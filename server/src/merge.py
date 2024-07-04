from sentence_transformers import SentenceTransformer, util
from sklearn.preprocessing import normalize

import json
import logging
import numpy as np
import torch
import time
import os
import pickle

_LOGGER = logging.getLogger(__name__)

# Load the model
#model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

entityNames = {}
entityByDomain = {} # dictionary
sentenceByDomain = {} # dictionary

service_sentence_by_domain = {}
service_id_by_dmain = {}

entity_sentence_embeddings = None
entity_sentence_key_list = None
entity_id_list = None

all_sentences = None
entity_data_list = None

class ServiceEmbeddings:
    service_id = None
    entity_id = None


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

    # KJS
    #print(sentenceByDomain['Start'])
    #sentenceByDomain['Start'] = {'timer.start': [["timer.first", "First Timer"], ["timer.second", "Second timer"]]}
    #print(sentenceByDomain['Start'])
    #quit()

    # Store the sentences in the model
    global entity_sentence_embeddings
    global entity_sentence_key_list
    global entity_id_list
    global all_sentences
    global entity_data_list

    entity_sentence_key_list = []
    entity_id_list = list(entityNames.keys())

    all_sentences = []
    entity_data_list = []

    # Iterate through the services
    # Result is dictionary of domains, containing a list of
    # service description embeddings and names. (e.g. "turn_on")
    i = 0
    for service_desc, inner_dict in sentenceByDomain.items():
        print("Service desc: " + service_desc)

        # Encode the service description
        # service_sentence_embedding = model.encode([service_desc])

        # Iterate through the service ids
        for service_id, entity_infos in inner_dict.items():

            # Get the existing mappings for this domain
            service_domain_id = service_id.split(".")[0]

            #TODO: Add proper domain name
            domain_name = service_domain_id

            for entity_info in entity_infos:
                entity_id   = entity_info[0]
                entity_desc = entity_info[1]
                print(" ", entity_desc)

                se = ServiceEmbeddings()
                se.service_id = service_id
                se.entity_id = entity_id

                entity_data_list.append(se)

                #print(f"Service: {service_id} ({service_desc}) Entity: {entity_id} ({entity_desc})") 

                sentence = f"{domain_name} {service_desc} {entity_desc}"
                all_sentences.append(sentence)


def findLikelyEntities(input_text):
    global all_sentences
    global entity_data_list
    global entity_sentence_embeddings

    user_input_embedding = model.encode([input_text])

    # Find most likley entities
    similarities = util.pytorch_cos_sim(user_input_embedding, entity_sentence_embeddings)[0]

    # similarities = model.similarity(user_input_embedding, entity_sentence_embeddings)[0]

    top_k = 3
    top_k_values, top_k_indices = torch.topk(similarities, k=top_k)

    ptr = 0
    for i in top_k_indices:
        print(f"{i} {ptr}, {top_k_values[ptr]}")

        most_similar_sentence = all_sentences[i]
        entity_data = entity_data_list[i]

        print(f"Similar sentence: {most_similar_sentence}, {top_k_values[ptr]}")
        print(f"   service:  {entity_data.service_id} entity: {entity_data.entity_id}")
        print()
        for s in range(i-1, i+2):
            if s == i:
                print(f"-->{s}: {all_sentences[s]}")
            else:
                print(f"   {s}: {all_sentences[s]}")

        ptr += 1



def loadData():
    global entity_id_list
    global all_sentences
    global entity_data_list
    global entity_sentence_embeddings

    start = time.time_ns()


    pickle_file = 'embeddings.pkl'

    rebuild_data = True

    if os.path.exists(pickle_file):
        try:
            with open(pickle_file, 'rb') as file:
                work_data = pickle.load(file)

            entity_sentence_embeddings = work_data[0]
            all_sentences = work_data[1]
            entity_data_list = work_data[2]

            print("Data loaded from pickle file:")

            rebuild_data = False
        except:
            print("Failed to load from pickle file")

    if rebuild_data:
        # Create new data
        loadJson("/mnt/dietpi_userdata/homeassistant/custom_components/askbert/server")

        with open(pickle_file, 'wb') as file:
            print("Encoding *everything*")
            entity_sentence_embeddings = model.encode(all_sentences)
            print(f"Encoding took {(time.time_ns() - start) // 1000000}")

            work_data = [ entity_sentence_embeddings,
                          all_sentences,
                          entity_data_list ]


            pickle.dump(work_data, file)
            print("Data created and saved to pickle file:")


loadData()

print()
print("Loaded Sentences:")
print()
#i = 0
#for s in all_sentences:
#    if (i > 6037 and i < 6041):
#        print(f"{i}a: {s}")
#    i += 1
#
#print(f"Total sentences {i}")
#
#print(f"  6039b: {all_sentences[6039]}")

while True:
    # print(f"  6039c: {all_sentences[6039]}")
    print("--------------------------------------------------------")
    query = input("Enter a query (or type 'quit' to exit): ")
    if query.lower() == "quit":
        break

    if query != "":
        print("--------------------------------------------------------")
        findLikelyEntities(query)

