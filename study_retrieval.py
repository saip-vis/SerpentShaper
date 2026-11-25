"""Local, in-memory study retrieval and cautious percentage suggestions.

Uploaded material is untrusted: retrieval never executes its contents, and
suggestions are only literal family/percentage pairs requiring user review.
"""
from collections import Counter
from io import BytesIO
import hashlib
import math
import re
import threading

MAX_FILE_BYTES = 12 * 1024 * 1024
MAX_PAGES = 200
MAX_TEXT_CHARS = 1_000_000
MAX_STUDIES = 5
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 160
TOKEN = re.compile(r'[a-z0-9]+', re.I)
# Only exact, unambiguous abbreviations from the interface. Broad or ambiguous
# full-text prose and table layouts must not become numeric values implicitly.
FAMILIES = {'3ftx': '3ftx', 'pla2': 'pla2', 'svmp': 'svmp', 'svsp': 'svsp',
            'kspi': 'kunitz', 'crisp': 'crisp', 'laao': 'laao',
            'bpp': 'bradykinin_potentiating_peptide'}
PAIR = re.compile(r'(?<![a-z0-9])(3ftx|pla2|svmp|svsp|kspi|crisp|laao|bpp)\b\s*(?:[:=]\s*|\(\s*)?(\d{1,3}(?:\.\d+)?)\s*%', re.I)


def chunks_for_pages(pages):
    chunks=[]
    for page_no, text in enumerate(pages, 1):
        text=' '.join((text or '').split())
        if not text:
            continue
        for start in range(0, len(text), CHUNK_SIZE-CHUNK_OVERLAP):
            excerpt=text[start:start+CHUNK_SIZE]
            # Avoid presenting a truncated abbreviation or number as a candidate.
            safe=excerpt if start == 0 else excerpt.split(' ', 1)[-1]
            if start+CHUNK_SIZE < len(text):
                safe=safe.rsplit(' ', 1)[0]
            chunks.append({'page':page_no,'text':safe,'tokens':Counter(TOKEN.findall(safe.lower()))})
            if start+CHUNK_SIZE >= len(text): break
    return chunks


def suggestions(text):
    found=[]
    for match in PAIR.finditer(text):
        value=float(match.group(2))
        if value<=100:
            found.append({'component':FAMILIES[match.group(1).lower()],
                          'label':match.group(1), 'value':value,
                          'quoted_text':match.group(0)})
    return found


class StudyIndex:
    def __init__(self):
        self.studies=[]
        self.lock=threading.RLock()

    def add(self, filename, content):
        if not isinstance(filename,str) or not filename or len(filename)>200:
            raise ValueError('Provide a file name of at most 200 characters.')
        if not isinstance(content,bytes) or not content or len(content)>MAX_FILE_BYTES:
            raise ValueError('Upload a nonempty file no larger than 12 MB.')
        suffix=filename.rsplit('.',1)[-1].lower() if '.' in filename else ''
        if suffix == 'pdf':
            if not content.startswith(b'%PDF-'):
                raise ValueError('The file is not a PDF.')
            try:
                from pypdf import PdfReader
                reader=PdfReader(BytesIO(content), strict=False)
                if reader.is_encrypted: raise ValueError('Encrypted PDFs are not supported.')
                if len(reader.pages)>MAX_PAGES: raise ValueError('PDFs must have 200 pages or fewer.')
                pages=[];total=0
                for page in reader.pages:
                    text=page.extract_text() or ''
                    total+=len(text)
                    if total>MAX_TEXT_CHARS: raise ValueError('The extracted text is too large.')
                    pages.append(text)
            except ValueError:
                raise
            except Exception as exc:
                raise ValueError('Could not read this PDF. Try a text-based PDF.') from exc
        elif suffix == 'txt':
            try: text=content.decode('utf-8-sig')
            except UnicodeDecodeError as exc: raise ValueError('Text files must be UTF-8 encoded.') from exc
            if len(text)>MAX_TEXT_CHARS: raise ValueError('The extracted text is too large.')
            pages=[text]
        else:
            raise ValueError('Upload a PDF or UTF-8 text file.')
        chunks=chunks_for_pages(pages)
        if not chunks: raise ValueError('No extractable text was found. Scanned PDFs need OCR first.')
        digest=hashlib.sha256(content).hexdigest()
        with self.lock:
            previous=next((s for s in self.studies if s['sha256']==digest),None)
            if previous: return {'name':previous['name'],'pages':previous['pages'],'duplicate':True}
            if len(self.studies)>=MAX_STUDIES: raise ValueError('Remove a study before adding more than five.')
            name=filename.replace('\\','/').split('/')[-1]
            self.studies.append({'name':name,'sha256':digest,'pages':len(pages),'chunks':chunks})
        return {'name':name,'pages':len(pages),'duplicate':False}

    def clear(self):
        with self.lock: self.studies.clear()

    def search(self, query, limit=6):
        if not isinstance(query,str) or len(query)>500: raise ValueError('Search text must be 500 characters or fewer.')
        terms=set(TOKEN.findall(query.lower()))
        if not terms: return []
        with self.lock:
            all_chunks=[(s,c) for s in self.studies for c in s['chunks']]
            if not all_chunks:return []
            df=Counter(term for _,c in all_chunks for term in terms if term in c['tokens'])
            scored=[]
            for study,chunk in all_chunks:
                score=sum((1+math.log(chunk['tokens'][term]))*math.log(1+(len(all_chunks)+1)/(df[term]+1))
                          for term in terms if chunk['tokens'][term])
                if score:
                    scored.append((score,study,chunk))
            scored.sort(key=lambda row: (-row[0],row[1]['name'],row[2]['page']))
            return [{'study':s['name'],'sha256':s['sha256'],'page':c['page'],
                     'excerpt':c['text'],'suggestions':suggestions(c['text'])}
                    for _,s,c in scored[:max(0,min(limit,10))]]
