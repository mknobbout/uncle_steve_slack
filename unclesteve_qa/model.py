import os
import pickle
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import pytesseract
from sklearn.neighbors import NearestNeighbors
from PIL import Image

class USEQAModel:

    USE_MULTI_QA_URL = 'https://tfhub.dev/google/universal-sentence-encoder-multilingual-qa/2'

    def __init__(self):
        self.answers = None
        self.use_multi_qa_model = hub.load(self.USE_MULTI_QA_URL)
        self.nn_model = NearestNeighbors(n_neighbors=1, metric='cosine')
        self.text_processing_func = None

    def train(self, context_answers: list, text_processing_func = None, batch_size: int = 500):
        # Unzip list
        contexts, self.answers = zip(*context_answers)
        self.text_processing_func = self.default_text_processing_func if text_processing_func is None \
            else text_processing_func

        result = ()
        print('Attempting to embed %s sentences!' % len(self.answers))
        for i in range(0, len(self.answers), batch_size):
            print('Embedding batch [%d,%d]...' % (i, min(len(self.answers), i+batch_size)))
            batch_contexts, batch_answers = contexts[i:i + batch_size], self.answers[i:i + batch_size]

            # Calculate embeddings
            answer_embeddings = self.use_multi_qa_model.signatures['response_encoder'](
                input=tf.constant(list(map(self.text_processing_func, batch_answers))),
                context=tf.constant(list(map(self.text_processing_func, batch_contexts))))["outputs"]
            # Append to result
            result += (answer_embeddings,)

        # Train a 1-nn cosine model
        print('Training 1-cosine nn model...')
        self.nn_model.fit(np.vstack(result))
        print('Done!')

    @staticmethod
    def default_text_processing_func(text: str):
        return text

    def get_answer(self, question):
        # Get question
        question_embedding = self.use_multi_qa_model.signatures['question_encoder'](
            tf.constant([self.text_processing_func(question)]))["outputs"]
        # Find answer
        dists, indices = self.nn_model.kneighbors(question_embedding)
        return self.answers[indices[0][0]], dists[0][0]

    def get_image_answer(self, image: Image):
        return self.get_answer(
            pytesseract.image_to_string(image)
        )

    def save(self, out_path):
        with open(out_path, 'wb') as f:
            # Pickle self
            pickle.dump(self, f)

    @classmethod
    def load(cls, in_path):
        with open(in_path, 'rb') as f:
            obj: cls = pickle.load(f)
        return obj

    def __getstate__(self):
        odict = self.__dict__.copy()  # copy the dict since we change it
        del odict['use_multi_qa_model']  # remove entry
        return odict

    def __setstate__(self, odict):
        self.__dict__.update(odict)
        self.use_multi_qa_model = hub.load(self.USE_MULTI_QA_URL)
