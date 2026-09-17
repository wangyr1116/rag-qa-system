import app.chunker as chunker
import app.document_loader as loader

text = loader.load_text_file("data/sample.txt")
chunks = chunker.chunk_text(text, chunk_size=150, overlap=30)
print(f"Total chunks: {len(chunks)}")
count = 0
for index, chunk in enumerate(chunks, start=1):
    print(f"--- Chunk {index} (length: {len(chunk)}) ---")
    print(chunk)