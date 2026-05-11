import chromadb
import os
import sys
import re

# ─── 경로 및 설정 ────────────────────────────────────────────────────────
CHROMA_PATH = "/home/jetson/remote_vector_db"
COLLECTION_NAME = "medical_knowledge"

# ─── 1. 데이터 소스: Emergency.jsx에서 지침 추출 ──────────────────────────
def extract_from_jsx(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # ACTION_GUIDES 객체 추출 (간단한 정규식 및 파싱)
    guides = []
    
    # 각 지침의 제목과 상세 설명을 추출
    # 예: '심폐소생술': { title: '...', description: '...', steps: [...] }
    pattern = re.compile(r"'([^']+)':\s*{\s*title:\s*'([^']+)',\s*description:\s*'([^']+)'")
    matches = pattern.findall(content)
    
    for name, title, desc in matches:
        text = f"상황: {name}\n제목: {title}\n설명: {desc}\n"
        
        # 단계별 처치법 추출 (단순 텍스트 매칭)
        step_pattern = re.compile(rf"'{name}':.*?steps:\s*\[(.*?)\]", re.DOTALL)
        step_match = step_pattern.search(content)
        if step_match:
            steps_text = step_match.group(1)
            titles = re.findall(r"title:\s*'([^']+)'", steps_text)
            descs = re.findall(r"desc:\s*'([^']+)'", steps_text)
            for i, (st, sd) in enumerate(zip(titles, descs)):
                text += f"단계 {i+1}: {st} - {sd}\n"
        
        guides.append({
            "id": f"gui_{name}",
            "text": text,
            "metadata": {"source": "dashboard_gui", "category": name}
        })
    return guides

# ─── 2. 데이터 소스: 텍스트 가이드라인 파일 ────────────────────────────────
def extract_from_txt(file_path):
    if not os.path.exists(file_path): return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return [{
        "id": "txt_guideline_summary",
        "text": content,
        "metadata": {"source": "maritime_law_txt", "category": "guideline"}
    }]

# ─── 메인 실행 로직 ───────────────────────────────────────────────────────
def main():
    print(f"[*] Initializing Vector DB at {CHROMA_PATH}...")
    
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        # 기존 컬렉션이 있으면 가져오고 없으면 생성
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        
        all_docs = []
        
        # 1. JSX 지침 추출 (Jetson의 로컬 경로 기준)
        jsx_path = "/home/jetson/m_medic_latest/src/pages/Emergency.jsx"
        if os.path.exists(jsx_path):
            print(f"[*] Extracting data from {jsx_path}...")
            all_docs.extend(extract_from_jsx(jsx_path))
        
        # 2. TXT 지침 추출
        txt_path = "/home/jetson/m_medic_latest/maritime_medical_knowledge.txt" # 기존에 있던 파일 활용 시도
        if os.path.exists(txt_path):
            print(f"[*] Extracting data from {txt_path}...")
            all_docs.extend(extract_from_txt(txt_path))
            
        if not all_docs:
            print("[!] No documents found to index.")
            return

        # 3. DB에 저장
        print(f"[*] Indexing {len(all_docs)} documents...")
        ids = [d['id'] for d in all_docs]
        texts = [d['text'] for d in all_docs]
        metadatas = [d['metadata'] for d in all_docs]
        
        collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"[+] Successfully indexed {len(all_docs)} documents into '{COLLECTION_NAME}'!")
        
    except Exception as e:
        print(f"[!] Error during population: {e}")

if __name__ == "__main__":
    main()
