
from embedder.ollama import OllamaEmbedder
from document.reader.pdf import PDFReader
from document import Document
import glob
from tqdm import tqdm
import ollama
embedder = OllamaEmbedder(model='nomic-embed-text', dimensions='768')


def embed_files(files_list):
    reader = PDFReader()
    documents = []
    for document in files_list:
        read_document = reader.read(document)
        documents.append({
            'file_name': document.filename,
            'sections': [],
        })

        for doc in read_document:
            documents[-1]['sections'].append(doc)

    embedded_list = []
    for document in tqdm(documents):
        raw_string = " ".join(
            list(map(lambda doc: doc.content, document['sections'])))
        abstract = ollama.generate(
            model='llama3', prompt=f'without outputting stuff like to my knowledge or Abstract Give me abstract for this file {raw_string}')['response']
        owner = ollama.generate(
            model='llama3', prompt=f'Tell me which departmant or role in the organization is most responsible for maintaining of this document {raw_string} format output like this ** department reponsible for maintaining this document is {{name of the department or role}} ** ')['response']
        print(owner)
        embedded_object = {
            'file_name': document['file_name'],
            "abstract": abstract,
            "owner": owner.rsplit("**")[1],
            'content': []
        }

        for content in document['sections']:

            embedded_object['content'].append({
                'content': content.content,
                'embedding': embedder.get_embedding(content.content)
            })
        embedded_list.append(embedded_object)
    return embedded_list


def embed_text(text):
    return embedder.get_embedding(text)
