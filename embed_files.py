
from embedder.ollama import OllamaEmbedder
from document.reader.pdf import PDFReader
from document import Document
import glob
from tqdm import tqdm
embedder = OllamaEmbedder(model='nomic-embed-text', dimensions='768')

def embed_files(files_list):
    reader = PDFReader()
    embedder = OllamaEmbedder(model='nomic-embed-text', dimensions='768')
    documents =[]
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
        embedded_object = {
            'file_name': document['file_name'],
            'content': []
        }
        for content in document['sections']:
            embedded_object['content'].append({
                'content': content.content,
                'embedding': embedder.get_embedding(content.content)
            })
        embedded_list.append(embedded_object)
    return  embedded_list

def embed_text(text):
    return embedder.get_embedding(text)
