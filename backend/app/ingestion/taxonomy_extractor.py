import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger("edupath.ingestion.taxonomy")

class TaxonomyExtractor:
    """
    Extracts structured topics, concepts, summaries, and prerequisite dependency graphs
    from ingested knowledge units.
    """

    # Multi-domain Knowledge Graph Blueprints
    DOMAIN_PREREQUISITES = {
        # Operating Systems & Concurrency
        "Banker's Algorithm": ["Safe State", "Deadlock Avoidance"],
        "Deadlock Avoidance": ["Resource Allocation Graph", "Deadlock Conditions"],
        "Safe State": ["Resource Allocation Graph", "Deadlock Conditions"],
        "Resource Allocation Graph": ["Deadlock Conditions", "Process Lifecycle"],
        "Deadlock Prevention": ["Deadlock Conditions"],
        "Deadlock Conditions": ["Process Lifecycle", "Multithreading & Concurrency"],
        "Multithreading & Concurrency": ["Process Lifecycle"],
        "Context Switching": ["Process Control Block", "Process Lifecycle"],
        "Process Control Block": ["Process Lifecycle"],
        "Round Robin Scheduling": ["Scheduling Criteria", "Context Switching"],
        "Shortest Job First": ["Scheduling Criteria"],
        "First-Come First-Served": ["Scheduling Criteria"],
        "Scheduling Criteria": ["Process Lifecycle"],
        "Virtual Memory & Page Faults": ["Paging & Address Translation"],
        "Paging & Address Translation": ["Memory Allocation"],
        "Segmentation": ["Memory Allocation"],

        # Cellular Biology & Genetics
        "Mitochondrial ATP Synthesis": ["Cellular Respiration", "Citric Acid (Krebs) Cycle"],
        "Citric Acid (Krebs) Cycle": ["Glycolysis Pathway"],
        "Cellular Respiration": ["Glycolysis Pathway"],
        "Ribosomal Translation": ["Gene Transcription"],
        "Gene Transcription": ["DNA Replication & Structure"],
        "Genetic Mutations": ["DNA Replication & Structure"],
        "Gene Editing & CRISPR": ["Molecular Genetics"],

        # World History
        "Storming of the Bastille (1789)": ["The Estates-General & Third Estate", "Origins of the French Revolution"],
        "The Reign of Terror": ["Storming of the Bastille (1789)", "Declaration of Rights of Man"],
        "Declaration of Rights of Man": ["The Estates-General & Third Estate"],
        "The Cold War Era": ["Treaty of Versailles & Interwar Period"],

        # Computer Networking
        "TCP Flow & Congestion Control": ["TCP Three-Way Handshake"],
        "TCP Three-Way Handshake": ["Transport Layer Protocols", "IP Addressing & Packet Routing"],
        "UDP Transport Protocol": ["Transport Layer Protocols"],

        # Machine Learning
        "Transformer Self-Attention Mechanism": ["Deep Neural Architectures"],
        "Deep Neural Architectures": ["Neural Backpropagation"],
        "Neural Backpropagation": ["Gradient Descent Optimization"],
        "Model Overfitting & Regularization": ["Gradient Descent Optimization"],
    }

    CONCEPT_SUMMARIES = {
        # Operating Systems
        "Deadlock Conditions": "Four Coffman conditions necessary for deadlock: Mutual Exclusion, Hold and Wait, No Preemption, Circular Wait.",
        "Resource Allocation Graph": "Directed graph where vertices represent processes and resources, with request and assignment edges determining circular wait cycles.",
        "Deadlock Prevention": "Eliminates deadlocks by invalidating at least one of the four necessary Coffman conditions at system design time.",
        "Deadlock Avoidance": "Dynamic run-time decision making ensuring the system never enters an unsafe state that could lead to deadlocks.",
        "Safe State": "A state is safe if there exists a sequence of processes such that each process can satisfy its maximum resource requests using currently available and released resources.",
        "Banker's Algorithm": "Dijkstra's deadlock avoidance algorithm testing for safety by simulating the allocation of predetermined maximum possible amounts of all resources.",
        "Process Lifecycle": "The stages a program undergoes during execution: New, Ready, Running, Waiting, Terminated.",
        "Process Control Block": "Data structure containing OS information for process management (PID, registers, program counter, open files).",
        "Context Switching": "Storing the state of a CPU process so that it can be restored and execution resumed from the same point later.",
        "Multithreading & Concurrency": "Simultaneous execution of multiple lightweight subprocesses sharing common memory space and code segments.",
        "Scheduling Criteria": "Metrics used to compare CPU scheduling algorithms: CPU utilization, throughput, turnaround time, waiting time, and response time.",
        "First-Come First-Served": "Non-preemptive scheduling executing processes in the strict order of arrival in the ready queue.",
        "Shortest Job First": "Scheduling algorithm that selects the process with the smallest execution burst time.",
        "Round Robin Scheduling": "Preemptive algorithm designed for time-sharing systems where each process receives a fixed time slice (quantum).",
        "Memory Allocation": "Methods used by the operating system to distribute main memory among concurrent processes.",
        "Paging & Address Translation": "Memory management scheme dividing physical memory into fixed-size frames and virtual memory into pages mapped via a Page Table.",
        "Virtual Memory & Page Faults": "Technique allowing execution of processes not completely in physical memory, triggering a page fault interrupt on invalid page access.",
        "Segmentation": "Memory management scheme supporting user view of memory using variable-length segments (code, stack, data).",

        # Biology
        "Mitochondrial ATP Synthesis": "Generation of adenosine triphosphate (ATP) across the inner mitochondrial membrane via oxidative phosphorylation and ATP synthase.",
        "Glycolysis Pathway": "Anaerobic cytoplasmic breakdown of glucose into pyruvate yielding a net gain of 2 ATP and 2 NADH molecules.",
        "Citric Acid (Krebs) Cycle": "Cyclic series of chemical reactions in mitochondrial matrix oxidizing acetyl-CoA into carbon dioxide, NADH, and FADH2.",
        "Photosynthesis & Light Reactions": "Solar energy conversion into chemical energy (ATP, NADPH) inside thylakoid membranes releasing oxygen.",
        "Cellular Respiration": "Complete metabolic breakdown of glucose into water and carbon dioxide producing cellular energy.",
        "DNA Replication & Structure": "Double-helix antiparallel structure replicating semi-conservatively using DNA polymerases and helicases.",
        "Gene Transcription": "Synthesis of single-stranded messenger RNA from DNA template strand by RNA polymerase.",
        "Ribosomal Translation": "Assembly of polypeptide amino acid chains by ribosomes decoding mRNA codons with transfer RNAs.",

        # History
        "Origins of the French Revolution": "Severe financial crisis, fiscal inequality among the Three Estates, and Enlightenment ideals challenging absolute monarchy.",
        "The Estates-General & Third Estate": "1789 assembly breakdown where commoners formed the National Assembly demanding constitutional governance.",
        "Storming of the Bastille (1789)": "July 14, 1789 popular uprising seizing royal fortress and weapons, marking irreversible revolutionary rupture.",
        "The Reign of Terror": "Radical Jacobin emergency regime headed by Maximilien Robespierre executing political opponents via guillotine.",
        "Declaration of Rights of Man": "Foundational civil human rights document proclaiming liberty, equality, and popular sovereignty.",

        # Computer Networking
        "TCP Three-Way Handshake": "Connection establishment protocol exchanging SYN, SYN-ACK, and ACK packets ensuring reliable bi-directional communication.",
        "UDP Transport Protocol": "Connectionless, low-overhead transport protocol transmitting datagrams without handshakes or delivery guarantees.",
        "TCP Flow & Congestion Control": "Sliding window and AIMD mechanisms adjusting transmission rates to prevent receiver buffer and network bottleneck overflow.",
        "IP Addressing & Packet Routing": "Hierarchical network layer addressing (IPv4/IPv6) and hop-by-hop packet forwarding across intermediate routers.",

        # Machine Learning
        "Gradient Descent Optimization": "Iterative first-order optimization method computing parameter updates opposite the cost function gradient.",
        "Neural Backpropagation": "Efficient application of calculus chain rule calculating partial derivatives of loss with respect to all layer weights.",
        "Transformer Self-Attention Mechanism": "Scaled dot-product attention weighing pairwise relationships between all tokens in a sequence concurrently."
    }

    @classmethod
    def extract_taxonomy(cls, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Derives topics, concepts, summaries, and directed prerequisite links
        from the ingested chunks across any multimodal learning domain.
        """
        topics_map: Dict[str, Dict[str, Any]] = {}
        concepts_map: Dict[str, Dict[str, Any]] = {}
        ordered_concepts: List[str] = []

        for ch in chunks:
            t_name = ch.get("topic", "General Study")
            c_name = ch.get("concept", "Core Concept")
            content = ch.get("content", "")
            
            if t_name not in topics_map:
                topics_map[t_name] = {
                    "name": t_name,
                    "concepts": set(),
                    "chunk_count": 0
                }
            topics_map[t_name]["concepts"].add(c_name)
            topics_map[t_name]["chunk_count"] += 1

            if c_name not in concepts_map:
                ordered_concepts.append(c_name)
                # Synthesize informative summary from chunk excerpt if not in catalog
                summary = cls.CONCEPT_SUMMARIES.get(c_name)
                if not summary:
                    cleaned_excerpt = " ".join(content.strip().split()[:25])
                    summary = f"Key principles: {cleaned_excerpt}..." if cleaned_excerpt else f"Core study principles and mechanisms of {c_name}."
                
                # Prerequisite resolution: static blueprint or sequential ordering in document
                prereqs = cls.DOMAIN_PREREQUISITES.get(c_name, [])
                if not prereqs and len(ordered_concepts) > 1:
                    # Link to immediate preceding concept in same topic
                    prev_c = ordered_concepts[-2]
                    if prev_c != c_name and concepts_map[prev_c]["topic_name"] == t_name:
                        prereqs = [prev_c]

                concepts_map[c_name] = {
                    "name": c_name,
                    "topic_name": t_name,
                    "summary": summary,
                    "difficulty_baseline": 0.5,
                    "prerequisites": prereqs
                }

        # Convert sets to lists for JSON serialization
        topics_list = []
        for idx, (t_name, data) in enumerate(topics_map.items()):
            topics_list.append({
                "name": t_name,
                "order_index": idx + 1,
                "concepts": list(data["concepts"]),
                "chunk_count": data["chunk_count"]
            })

        return {
            "topics": topics_list,
            "concepts": list(concepts_map.values()),
            "prerequisites": [
                {"concept": c_name, "prerequisite": pr}
                for c_name, data in concepts_map.items()
                for pr in data["prerequisites"]
            ]
        }
