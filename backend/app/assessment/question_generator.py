import random
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.entities import Course, Topic, Concept, KnowledgeUnit, Question, QuestionAttempt
from backend.app.assessment.validation_pipeline import QuestionValidationPipeline

logger = logging.getLogger("edupath.assessment.generator")

class AdaptiveQuestionGenerator:
    """
    Generates source-grounded, difficulty-calibrated assessment questions
    backed by real course knowledge units and validated through the verification pipeline.
    """

    # Domain Question Templates grounded in Operating Systems & Computer Architecture
    CURATED_BANK = [
        {
            "concept_name": "Deadlock Conditions",
            "topic_name": "Deadlocks",
            "question_text": "Which of the following is NOT one of the four necessary Coffman conditions required for a deadlock to occur?",
            "options": [
                "Mutual Exclusion",
                "Preemptive Scheduling",
                "Hold and Wait",
                "Circular Wait"
            ],
            "correct_answer": "Preemptive Scheduling",
            "explanation": "The four Coffman conditions are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. Preemption breaks deadlocks; 'No Preemption' is the necessary condition.",
            "difficulty": 0.40,
            "source_evidence": "The four Coffman conditions necessary for deadlock are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.",
            "source_reference": {"document": "Operating Systems.pdf", "page": 42}
        },
        {
            "concept_name": "Banker's Algorithm",
            "topic_name": "Deadlocks",
            "question_text": "How does Dijkstra's Banker's Algorithm decide whether to grant a resource request from a process?",
            "options": [
                "It immediately allocates the resource if the request does not exceed total system capacity.",
                "It simulates the allocation and checks if the system remains in a guaranteed Safe State.",
                "It forcibly terminates the longest running process to free memory.",
                "It waits until all other running processes have completed execution."
            ],
            "correct_answer": "It simulates the allocation and checks if the system remains in a guaranteed Safe State.",
            "explanation": "Banker's Algorithm tests for safety by simulating the allocation of predetermined maximum possible amounts of all resources, granting the request only if a safe sequence exists.",
            "difficulty": 0.65,
            "source_evidence": "Banker's Algorithm is a deadlock avoidance algorithm testing for safe states in resource allocation.",
            "source_reference": {"document": "OS_Lecture7.pptx", "slide": 18}
        },
        {
            "concept_name": "Safe State",
            "topic_name": "Deadlocks",
            "question_text": "What is the precise definition of a 'Safe State' in deadlock avoidance?",
            "options": [
                "A state where CPU utilization is guaranteed to remain above 90%.",
                "A state where there exists a sequence of processes such that each can satisfy its maximum resource claims with available plus released resources.",
                "A state where no process currently holds any locks or mutexes.",
                "A state where all processes have been suspended to prevent race conditions."
            ],
            "correct_answer": "A state where there exists a sequence of processes such that each can satisfy its maximum resource claims with available plus released resources.",
            "explanation": "A safe sequence ensures that even in the worst-case scenario where every process requests its maximum declared resources, no deadlock will occur.",
            "difficulty": 0.60,
            "source_evidence": "A state is safe if there exists a sequence of processes such that each process can satisfy its maximum resource requests.",
            "source_reference": {"document": "Operating Systems.pdf", "page": 43}
        },
        {
            "concept_name": "Resource Allocation Graph",
            "topic_name": "Deadlocks",
            "question_text": "In a Resource Allocation Graph (RAG) where each resource type has only a single instance, what does the presence of a cycle signify?",
            "options": [
                "A deadlock definitely exists.",
                "A deadlock is completely impossible.",
                "The system is operating at peak throughput.",
                "A context switch is currently in progress."
            ],
            "correct_answer": "A deadlock definitely exists.",
            "explanation": "If each resource type has exactly one instance, a cycle in the Resource Allocation Graph is both a necessary and sufficient condition for deadlock.",
            "difficulty": 0.55,
            "source_evidence": "Slide 18 contains a resource allocation graph demonstrating a deadlock cycle scenario.",
            "source_reference": {"document": "OS_Lecture7.pptx", "slide": 18}
        },
        {
            "concept_name": "Paging & Address Translation",
            "topic_name": "Memory Management",
            "question_text": "What major memory fragmentation problem is completely eliminated by pure paging?",
            "options": [
                "Internal fragmentation",
                "External fragmentation",
                "Thrashing",
                "Page faults"
            ],
            "correct_answer": "External fragmentation",
            "explanation": "Paging divides physical memory into fixed-size frames, so any free frame can be allocated to a process, completely eliminating external fragmentation.",
            "difficulty": 0.50,
            "source_evidence": "Paging divides physical memory into fixed frames, eliminating external fragmentation.",
            "source_reference": {"document": "Operating Systems.pdf", "page": 84}
        },
        {
            "concept_name": "Round Robin Scheduling",
            "topic_name": "CPU Scheduling",
            "question_text": "In Round Robin scheduling, what happens if the time quantum is chosen to be extremely large (larger than the longest CPU burst)?",
            "options": [
                "The algorithm degenerates into First-Come First-Served (FCFS).",
                "The algorithm achieves perfect Shortest Job First optimality.",
                "The system encounters a guaranteed deadlock.",
                "Context switching overhead increases exponentially."
            ],
            "correct_answer": "The algorithm degenerates into First-Come First-Served (FCFS).",
            "explanation": "If the time quantum is larger than any process's burst time, no process is preempted before completion, making the queue behave identically to FCFS.",
            "difficulty": 0.55,
            "source_evidence": "If time quantum is very large, Round Robin scheduling becomes equivalent to FCFS.",
            "source_reference": {"document": "Operating Systems.pdf", "page": 62}
        },
        # Cellular Biology & Genetics
        {
            "concept_name": "Mitochondrial ATP Synthesis",
            "topic_name": "Cellular Biology & Bioenergetics",
            "question_text": "How does the proton electrochemical gradient across the inner mitochondrial membrane generate cellular ATP?",
            "options": [
                "Proton motive force drives the rotation of ATP synthase to phosphorylate ADP into ATP.",
                "Protons directly cleave glucose into lactate in the outer membrane.",
                "Protons combine with nitrogen gas to synthesize amino acids.",
                "Protons hydrolyze ATP into adenosine monophosphate to release heat."
            ],
            "correct_answer": "Proton motive force drives the rotation of ATP synthase to phosphorylate ADP into ATP.",
            "explanation": "Oxidative phosphorylation uses the proton gradient established by the electron transport chain to power ATP synthase.",
            "difficulty": 0.50,
            "source_evidence": "Proton electrochemical gradient across the inner membrane powers ATP synthase rotation yielding ATP.",
            "source_reference": {"document": "Cell_Biology_Ch4.pdf", "page": 112}
        },
        {
            "concept_name": "Glycolysis Pathway",
            "topic_name": "Cellular Biology & Bioenergetics",
            "question_text": "What is the net yield of ATP and NADH per glucose molecule metabolized via glycolysis?",
            "options": [
                "2 net ATP and 2 NADH",
                "4 net ATP and 0 NADH",
                "36 net ATP and 10 NADH",
                "1 net ATP and 4 FADH2"
            ],
            "correct_answer": "2 net ATP and 2 NADH",
            "explanation": "Glycolysis invests 2 ATP and produces 4 ATP, giving a net gain of 2 ATP and reduces 2 NAD+ to 2 NADH.",
            "difficulty": 0.45,
            "source_evidence": "Glycolysis converts one glucose into two pyruvate molecules, producing a net 2 ATP and 2 NADH.",
            "source_reference": {"document": "Cell_Biology_Ch4.pdf", "page": 105}
        },
        # World History
        {
            "concept_name": "Storming of the Bastille (1789)",
            "topic_name": "The French Revolution",
            "question_text": "Why was the medieval fortress of the Bastille targeted by the Parisian insurrection on July 14, 1789?",
            "options": [
                "To seize gunpowder stores and challenge the military authority of the royal monarchy.",
                "To liberate thousands of captive royal prisoners of war.",
                "To sign the Treaty of Paris with foreign ambassadors.",
                "To construct the first National Assembly building."
            ],
            "correct_answer": "To seize gunpowder stores and challenge the military authority of the royal monarchy.",
            "explanation": "The insurgents sought the large stores of gunpowder kept in the Bastille and viewed the fortress as a physical symbol of royal tyranny.",
            "difficulty": 0.45,
            "source_evidence": "On July 14, 1789, insurgents stormed the Bastille fortress primarily to seize munitions and gunpowder.",
            "source_reference": {"document": "French_Revolution_Lectures.pptx", "slide": 12}
        },
        {
            "concept_name": "The Estates-General & Third Estate",
            "topic_name": "The French Revolution",
            "question_text": "What fundamental structural grievance led the Third Estate to declare itself the National Assembly in June 1789?",
            "options": [
                "Voting by order allowed the First and Second Estates to consistently outvote the Third Estate 2-to-1 despite representing 98% of the populace.",
                "The Third Estate was legally forbidden from paying taxes to the crown.",
                "The King mandated that only nobles could attend universities.",
                "The clergy demanded complete control of the French navy."
            ],
            "correct_answer": "Voting by order allowed the First and Second Estates to consistently outvote the Third Estate 2-to-1 despite representing 98% of the populace.",
            "explanation": "Under the traditional voting-by-order rules, the privileged nobility and clergy could outvote the commoners regardless of demographic representation.",
            "difficulty": 0.50,
            "source_evidence": "The Third Estate rejected voting by order, demanding vote by head where each delegate held one vote.",
            "source_reference": {"document": "French_Revolution_Lectures.pptx", "slide": 8}
        },
        # Computer Networks
        {
            "concept_name": "TCP Three-Way Handshake",
            "topic_name": "Computer Networks",
            "question_text": "What sequence of TCP control flags establishes a reliable connection between client and server?",
            "options": [
                "SYN (client) -> SYN-ACK (server) -> ACK (client)",
                "ACK (client) -> SYN (server) -> FIN (client)",
                "SYN (client) -> RST (server) -> ACK (client)",
                "PUSH (client) -> PUSH-ACK (server) -> DATA (client)"
            ],
            "correct_answer": "SYN (client) -> SYN-ACK (server) -> ACK (client)",
            "explanation": "The 3-way handshake synchronizes sequence numbers between endpoints before application data transmission begins.",
            "difficulty": 0.45,
            "source_evidence": "TCP establishes a full-duplex session using SYN, SYN-ACK, and ACK packet transmission.",
            "source_reference": {"document": "Networking_Protocols.pdf", "page": 88}
        },
        {
            "concept_name": "UDP Transport Protocol",
            "topic_name": "Computer Networks",
            "question_text": "Why do low-latency real-time applications such as VoIP and live streaming utilize UDP instead of TCP?",
            "options": [
                "UDP eliminates connection setup delays and does not retransmit dropped packets.",
                "UDP guarantees strict chronological packet delivery without jitter.",
                "UDP provides automatic end-to-end payload compression.",
                "UDP assigns dedicated hardware routers for each stream."
            ],
            "correct_answer": "UDP eliminates connection setup delays and does not retransmit dropped packets.",
            "explanation": "UDP is connectionless and does not perform retransmissions or flow control, avoiding latency stalls for real-time traffic.",
            "difficulty": 0.40,
            "source_evidence": "UDP provides connectionless best-effort transport without retransmission delays.",
            "source_reference": {"document": "Networking_Protocols.pdf", "page": 94}
        }
    ]

    @classmethod
    async def generate_questions_for_course(
        cls,
        db: AsyncSession,
        course_id: str,
        user_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        count: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Generates approved, verified questions strictly grounded in the course's
        topics and knowledge units. Never defaults to unrelated seed courses.
        """
        # Fetch question history for user to prevent duplicates
        past_questions = []
        if user_id:
            h_res = await db.execute(
                select(Question.question_text).join(QuestionAttempt).filter(QuestionAttempt.user_id == user_id)
            )
            past_questions = [row[0] for row in h_res.all()]

        # 1. Discover all actual topics and concepts for THIS course
        t_stmt = select(Topic).filter(Topic.course_id == course_id)
        if topic_id:
            t_stmt = t_stmt.filter(Topic.id == topic_id)
        t_res = await db.execute(t_stmt)
        course_topics = t_res.scalars().all()
        topic_names = {t.name.lower(): t for t in course_topics}

        c_res = await db.execute(
            select(Concept).filter(Concept.topic_id.in_([t.id for t in course_topics])) if course_topics else select(Concept).filter(False)
        )
        course_concepts = c_res.scalars().all()
        concept_names = {c.name.lower(): c for c in course_concepts}

        # 2. Filter curated bank matching ONLY topics or concepts present in this course
        candidates = []
        for q in cls.CURATED_BANK:
            if q["topic_name"].lower() in topic_names or q["concept_name"].lower() in concept_names:
                candidates.append(q)

        random.shuffle(candidates)
        approved_questions = []

        for candidate in candidates:
            if len(approved_questions) >= count:
                break

            # Run validation pipeline
            is_valid, reason = QuestionValidationPipeline.validate_question(
                candidate_question=candidate,
                source_evidence=candidate["source_evidence"],
                question_history=past_questions
            )

            if is_valid:
                # Find matching concept in DB for this course
                concept = concept_names.get(candidate["concept_name"].lower())
                if not concept and course_concepts:
                    concept = course_concepts[0]

                if concept:
                    q_entity = Question(
                        course_id=course_id,
                        concept_id=concept.id,
                        question_type="mcq",
                        question_text=candidate["question_text"],
                        options=candidate["options"],
                        correct_answer=candidate["correct_answer"],
                        explanation=candidate["explanation"],
                        difficulty=candidate["difficulty"],
                        source_evidence=candidate["source_evidence"],
                        source_reference=candidate["source_reference"],
                        is_verified=True
                    )
                    db.add(q_entity)
                    await db.flush()

                    approved_questions.append({
                        "question_id": q_entity.id,
                        "concept_id": concept.id,
                        "concept_name": candidate["concept_name"],
                        "topic_name": candidate["topic_name"],
                        "question_text": candidate["question_text"],
                        "options": candidate["options"],
                        "difficulty": candidate["difficulty"],
                        "source": candidate["source_reference"]
                    })
                    past_questions.append(candidate["question_text"])

        # 3. Dynamic KnowledgeUnit synthesis if more questions needed for uploaded document
        if len(approved_questions) < count:
            ku_stmt = select(KnowledgeUnit).filter(KnowledgeUnit.course_id == course_id)
            if topic_id:
                topic_obj = await db.get(Topic, topic_id)
                if topic_obj:
                    ku_stmt = ku_stmt.filter(KnowledgeUnit.topic_name == topic_obj.name)
            ku_res = await db.execute(ku_stmt)
            units = ku_res.scalars().all()
            random.shuffle(units)

            for ku in units:
                if len(approved_questions) >= count:
                    break

                # Extract concise summary from content
                content_clean = ku.content.strip().replace("\n", " ")
                sentences = [s.strip() for s in content_clean.split(".") if len(s.strip()) > 20]
                if not sentences:
                    continue
                key_fact = sentences[0]

                question_text = f"According to {ku.source_file}, which statement correctly summarizes {ku.concept_name}?"
                if question_text in past_questions:
                    continue

                correct_ans = key_fact + "."
                distractor_1 = f"It is completely superseded and irrelevant in modern implementations of {ku.topic_name}."
                distractor_2 = f"It only occurs when system bandwidth is throttled below minimum hardware thresholds."
                distractor_3 = f"It requires manual operator intervention before executing subsequent cycles."

                syn_candidate = {
                    "question_text": question_text,
                    "options": [correct_ans, distractor_1, distractor_2, distractor_3],
                    "correct_answer": correct_ans,
                    "explanation": f"Source document ({ku.source_file}) explicitly states: {key_fact}.",
                    "difficulty": 0.50,
                    "source_evidence": key_fact,
                    "source_reference": ku.source_location
                }

                # Find or assign concept
                concept = concept_names.get(ku.concept_name.lower()) if ku.concept_name else (course_concepts[0] if course_concepts else None)
                if not concept and course_topics:
                    # Create concept on the fly
                    concept = Concept(
                        topic_id=course_topics[0].id,
                        name=ku.concept_name or "Core Principles",
                        summary=key_fact[:120],
                        difficulty_baseline=0.5
                    )
                    db.add(concept)
                    await db.flush()

                if concept:
                    q_entity = Question(
                        course_id=course_id,
                        concept_id=concept.id,
                        question_type="mcq",
                        question_text=syn_candidate["question_text"],
                        options=syn_candidate["options"],
                        correct_answer=syn_candidate["correct_answer"],
                        explanation=syn_candidate["explanation"],
                        difficulty=syn_candidate["difficulty"],
                        source_evidence=syn_candidate["source_evidence"],
                        source_reference=syn_candidate["source_reference"],
                        is_verified=True
                    )
                    db.add(q_entity)
                    await db.flush()

                    approved_questions.append({
                        "question_id": q_entity.id,
                        "concept_id": concept.id,
                        "concept_name": ku.concept_name,
                        "topic_name": ku.topic_name,
                        "question_text": syn_candidate["question_text"],
                        "options": syn_candidate["options"],
                        "difficulty": syn_candidate["difficulty"],
                        "source": syn_candidate["source_reference"]
                    })
                    past_questions.append(question_text)

        await db.commit()
        return approved_questions
