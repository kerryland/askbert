
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

#nltk.download('punkt')

input_text = "Hi World"

# TODO: add 'convert_to_tensor=True'???
user_input_embedding = model.encode([input_text])

src1 = ["Hello World", "Something else"]
src2 = ["Goodbye World", "Another thing"]
src3 = ["Hi World", "Something else", "Goodbye World", "Another thing"]
emb1 = model.encode(src1)
emb2 = model.encode(src2)
emb3 = model.encode(src3)
emb4 = emb1 + emb2
emb5 = np.concatenate([emb1, emb3])

print(f"emb1. {emb1.shape}")
print(f"emb2. {emb2.shape}")
print(f"emb3. {emb3.shape}")
print(f"emb4. {emb4.shape}")
print(f"emb5. {emb5.shape}")

similarities = util.pytorch_cos_sim(user_input_embedding, emb1)[0]
similarities = util.pytorch_cos_sim(user_input_embedding, emb2)[0]
similarities = util.pytorch_cos_sim(user_input_embedding, emb3)[0]
similarities = util.pytorch_cos_sim(user_input_embedding, emb4)[0]
similarities = util.pytorch_cos_sim(user_input_embedding, emb5)[0]
#print(similarities)

idx = 0
top_k_values, top_k_indices = torch.topk(similarities, k=3)
for i in top_k_indices:
    print(f"top {i}. {top_k_values[idx]}")
    idx+=1


#most_similar_idx = similarities.argmax()
#print(most_similar_idx)
#print(src1[most_similar_idx])
#
#
#similarities = util.pytorch_cos_sim(user_input_embedding, emb2)[0]
#print(similarities)
#most_similar_idx = similarities.argmax()
#print(src2[most_similar_idx])
#
#similarities = util.pytorch_cos_sim(user_input_embedding, emb1)[0]
#print(similarities)
#most_similar_idx = similarities.argmax()
#print(src1[most_similar_idx])
#
#a = np.array(emb1)
#b = np.array(emb2)
#c = a + b
#
#similarities = util.pytorch_cos_sim(user_input_embedding, c)[0]
#print(similarities)
#most_similar_idx = similarities.argmax()
#print((src1 + src2)[most_similar_idx])
#
