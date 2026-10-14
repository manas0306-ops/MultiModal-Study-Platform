import re
from typing import List, Dict, Any

class SemanticChunker:
    """
    Chunks extracted multimodal units into retrieval-ready knowledge units
    without ever losing their underlying source coordinates.
    """

    @classmethod
    def chunk_pdf_pages(cls, pages: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        chunks = []
        for p in pages:
            text = p["text"]
            if not text:
                continue
            
            # Paragraph-based chunking within page
            paragraphs = [para.strip() for para in text.split("\n\n") if len(para.strip()) > 30]
            if not paragraphs:
                paragraphs = [text]
                
            for p_idx, para in enumerate(paragraphs):
                # Detect likely topic/concept keywords
                topic, concept = cls._detect_topic_and_concept(para)
                chunks.append({
                    "content_type": "text",
                    "topic": topic,
                    "concept": concept,
                    "content": para,
                    "source": {
                        "type": "pdf",
                        "file": filename,
                        "page": p["page_number"],
                        "total_pages": p.get("total_pages", 1),
                        "citation_label": f"📄 {filename} — Page {p['page_number']}"
                    }
                })
        return chunks

    @classmethod
    def chunk_pptx_slides(cls, slides: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        chunks = []
        for s in slides:
            text = s["text"]
            if not text and not s.get("diagram_description"):
                continue
                
            content = text
            if s.get("speaker_notes"):
                content += f"\n[Presenter Notes]: {s['speaker_notes']}"
            if s.get("diagram_description"):
                content += f"\n[Visual Description]: {s['diagram_description']}"
                
            topic, concept = cls._detect_topic_and_concept(content, fallback_title=s.get("title"))
            
            chunks.append({
                "content_type": "slide",
                "topic": topic,
                "concept": concept,
                "content": content.strip(),
                "source": {
                    "type": "pptx",
                    "file": filename,
                    "slide": s["slide_number"],
                    "title": s.get("title", f"Slide {s['slide_number']}"),
                    "citation_label": f"📊 {filename} — Slide {s['slide_number']}"
                }
            })
        return chunks

    @classmethod
    def chunk_video_segments(cls, segments: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        chunks = []
        for seg in segments:
            text = seg["text"]
            if not text:
                continue
            topic, concept = cls._detect_topic_and_concept(text)
            chunks.append({
                "content_type": "video_transcript",
                "topic": topic,
                "concept": concept,
                "content": text,
                "source": {
                    "type": "video",
                    "file": filename,
                    "start_seconds": seg["start_seconds"],
                    "end_seconds": seg["end_seconds"],
                    "timestamp_formatted": seg["timestamp_formatted"],
                    "citation_label": f"🎥 {filename} — {seg['timestamp_formatted'].split(' - ')[0]}"
                }
            })
        return chunks

    @classmethod
    def chunk_docx_sections(cls, sections: List[Dict[str, Any]], filename: str) -> List[Dict[str, Any]]:
        chunks = []
        for sec in sections:
            text = sec["text"]
            if not text:
                continue
            topic, concept = cls._detect_topic_and_concept(text, fallback_title=sec.get("heading"))
            chunks.append({
                "content_type": "text",
                "topic": topic,
                "concept": concept,
                "content": text,
                "source": {
                    "type": "docx",
                    "file": filename,
                    "section": sec.get("section_index", 1),
                    "heading": sec.get("heading", "General"),
                    "citation_label": f"📝 {filename} — Section {sec.get('section_index', 1)}"
                }
            })
        return chunks

    @classmethod
    def _detect_topic_and_concept(cls, text: str, fallback_title: str = None) -> (str, str):
        t_lower = text.lower()
        
        # 1. Biological Sciences & Biochemistry
        if any(w in t_lower for w in ["mitochondria", "cellular respiration", "atp", "glycolysis", "krebs", "electron transport", "chloroplast", "photosynthesis", "ribosome"]):
            topic = "Cellular Biology & Bioenergetics"
            if "mitochondria" in t_lower or "atp" in t_lower:
                concept = "Mitochondrial ATP Synthesis"
            elif "glycolysis" in t_lower:
                concept = "Glycolysis Pathway"
            elif "photosynthesis" in t_lower or "chloroplast" in t_lower:
                concept = "Photosynthesis & Light Reactions"
            elif "krebs" in t_lower or "citric acid" in t_lower:
                concept = "Citric Acid (Krebs) Cycle"
            else:
                concept = "Cellular Respiration"
            return topic, concept

        if any(w in t_lower for w in ["dna", "rna", "transcription", "translation", "chromosome", "allele", "genetics", "mutation"]):
            topic = "Molecular Genetics"
            if "transcription" in t_lower:
                concept = "Gene Transcription"
            elif "translation" in t_lower or "protein synthesis" in t_lower:
                concept = "Ribosomal Translation"
            elif "mutation" in t_lower:
                concept = "Genetic Mutations"
            elif "crispr" in t_lower:
                concept = "Gene Editing & CRISPR"
            else:
                concept = "DNA Replication & Structure"
            return topic, concept

        # 2. World History & Social Sciences
        if any(w in t_lower for w in ["bastille", "french revolution", "estates-general", "robespierre", "guillotine", "louis xvi", "jacobin"]):
            topic = "The French Revolution"
            if "bastille" in t_lower:
                concept = "Storming of the Bastille (1789)"
            elif "estates-general" in t_lower or "third estate" in t_lower:
                concept = "The Estates-General & Third Estate"
            elif "robespierre" in t_lower or "terror" in t_lower:
                concept = "The Reign of Terror"
            elif "declaration of the rights" in t_lower:
                concept = "Declaration of Rights of Man"
            else:
                concept = "Origins of the French Revolution"
            return topic, concept

        if any(w in t_lower for w in ["world war", "treaty of versailles", "cold war", "soviet", "civil war", "renaissance"]):
            topic = "Modern World History"
            if "cold war" in t_lower or "soviet" in t_lower:
                concept = "The Cold War Era"
            elif "versailles" in t_lower:
                concept = "Treaty of Versailles & Interwar Period"
            elif "renaissance" in t_lower:
                concept = "The European Renaissance"
            else:
                concept = "Global Conflicts & Diplomacy"
            return topic, concept

        # 3. Computer Networks & Distributed Systems
        if any(w in t_lower for w in ["tcp", "udp", "three-way handshake", "handshake", "packet", "socket", "sliding window", "ip address", "subnet"]):
            topic = "Computer Networks"
            if "handshake" in t_lower or "three-way" in t_lower or "syn-ack" in t_lower:
                concept = "TCP Three-Way Handshake"
            elif "udp" in t_lower:
                concept = "UDP Transport Protocol"
            elif "sliding window" in t_lower or "flow control" in t_lower:
                concept = "TCP Flow & Congestion Control"
            elif "ip" in t_lower or "subnet" in t_lower or "routing" in t_lower:
                concept = "IP Addressing & Packet Routing"
            else:
                concept = "Transport Layer Protocols"
            return topic, concept

        # 4. Machine Learning & Artificial Intelligence
        if any(w in t_lower for w in ["gradient descent", "neural network", "backpropagation", "loss function", "transformer", "attention mechanism", "overfitting"]):
            topic = "Machine Learning & Deep Learning"
            if "gradient descent" in t_lower:
                concept = "Gradient Descent Optimization"
            elif "transformer" in t_lower or "attention" in t_lower:
                concept = "Transformer Self-Attention Mechanism"
            elif "backpropagation" in t_lower:
                concept = "Neural Backpropagation"
            elif "overfitting" in t_lower or "regularization" in t_lower:
                concept = "Model Overfitting & Regularization"
            else:
                concept = "Deep Neural Architectures"
            return topic, concept

        # 5. Physics & Chemistry
        if any(w in t_lower for w in ["thermodynamics", "entropy", "enthalpy", "covalent", "ionic bond", "electromagnetism", "quantum"]):
            topic = "Physical & Chemical Principles"
            if "entropy" in t_lower or "second law" in t_lower:
                concept = "Entropy & Second Law of Thermodynamics"
            elif "quantum" in t_lower:
                concept = "Quantum States & Wave-Particle Duality"
            elif "covalent" in t_lower or "ionic" in t_lower or "bond" in t_lower:
                concept = "Chemical Bonding & Molecular Orbitals"
            else:
                concept = "Thermodynamic Laws"
            return topic, concept

        # 6. Operating Systems & Concurrency (Standard CS)
        if "deadlock" in t_lower:
            topic = "Deadlocks"
            if "banker" in t_lower or "safety algorithm" in t_lower:
                concept = "Banker's Algorithm"
            elif "safe state" in t_lower:
                concept = "Safe State"
            elif "prevention" in t_lower or "mutual exclusion" in t_lower or "hold and wait" in t_lower:
                concept = "Deadlock Prevention"
            elif "avoidance" in t_lower:
                concept = "Deadlock Avoidance"
            elif "resource allocation graph" in t_lower or "rag" in t_lower:
                concept = "Resource Allocation Graph"
            else:
                concept = "Deadlock Conditions"
            return topic, concept
            
        elif "process" in t_lower or "thread" in t_lower or "pcb" in t_lower:
            topic = "Processes & Threads"
            if "thread" in t_lower:
                concept = "Multithreading & Concurrency"
            elif "context switch" in t_lower:
                concept = "Context Switching"
            elif "pcb" in t_lower or "process control block" in t_lower:
                concept = "Process Control Block"
            else:
                concept = "Process Lifecycle"
            return topic, concept
            
        elif "schedul" in t_lower or "fcfs" in t_lower or "sjf" in t_lower or "round robin" in t_lower:
            topic = "CPU Scheduling"
            if "round robin" in t_lower:
                concept = "Round Robin Scheduling"
            elif "sjf" in t_lower or "shortest job" in t_lower:
                concept = "Shortest Job First"
            elif "fcfs" in t_lower:
                concept = "First-Come First-Served"
            else:
                concept = "Scheduling Criteria"
            return topic, concept

        elif "memory" in t_lower or "paging" in t_lower or "segmentation" in t_lower or "virtual" in t_lower:
            topic = "Memory Management"
            if "paging" in t_lower or "page table" in t_lower:
                concept = "Paging & Address Translation"
            elif "virtual memory" in t_lower or "page fault" in t_lower:
                concept = "Virtual Memory & Page Faults"
            elif "segmentation" in t_lower:
                concept = "Segmentation"
            else:
                concept = "Memory Allocation"
            return topic, concept

        # 7. Dynamic Subject Detection & Intelligent Topic Extraction
        # If a fallback title / heading was provided (e.g. from PPTX slide, DOCX heading, or PDF header)
        if fallback_title and len(fallback_title.strip()) > 3:
            clean_title = fallback_title.strip()
            return clean_title, f"{clean_title} Core Concept"

        # Heuristic noun-phrase extractor from the first sentence
        first_line = text.strip().split("\n")[0].split(".")[0].strip()
        words = re.findall(r"[A-Z][a-zA-Z0-9_-]+", first_line)
        if len(words) >= 2:
            extracted_concept = " ".join(words[:3])
            return extracted_concept, f"{extracted_concept} Principles"
        elif len(words) == 1:
            return words[0], f"{words[0]} Overview"

        # Fallback to general academic concept based on first sentence snippet
        snippet = " ".join(re.findall(r"\b[A-Za-z0-9_-]+\b", text)[:4]).title()
        topic_name = snippet if snippet else "General Study"
        return topic_name, f"{topic_name} Fundamentals"
