import uuid
import pytest
from sqlalchemy.future import select

from backend.app.database.connection import AsyncSessionLocal, init_db
from backend.app.models.entities import Course, Document, KnowledgeUnit, Topic, Concept, Question
from backend.app.ingestion.multimodal_service import MultimodalIngestionService
from backend.app.ingestion.chunking import SemanticChunker
from backend.app.retrieval.hybrid_retriever import HybridRetriever
from backend.app.ai.grounding_gate import GroundingGate
from backend.app.ai.tutor import GroundedTutorService
from backend.app.assessment.question_generator import AdaptiveQuestionGenerator
from backend.app.services.revision_generator import RevisionGeneratorService
from backend.app.services.exam_simulator import ExamSimulatorService
from backend.app.services.flashcards import FlashcardService


@pytest.mark.asyncio
async def test_multi_subject_scoping_and_zero_deadlock_bias():
    """
    Comprehensive deterministic verification suite demonstrating:
    1. Dynamic topic/concept derivation across distinct subjects (Biology, History, Networking, Transcripts, Slides).
    2. Strict course and document-level retrieval scoping with zero cross-contamination.
    3. Complete elimination of deadlock bias when querying non-deadlock material.
    4. Adaptive assessment, flashcard, and revision dynamic generation from active course knowledge units.
    """
    await init_db()

    async with AsyncSessionLocal() as db:
        run_id = uuid.uuid4().hex[:6]
        # =====================================================================
        # SUBJECT A: Cellular Biology (PDF/Text)
        # =====================================================================
        bio_course = Course(
            code=f"BIO_101_{run_id}",
            title="Cellular Biology & Bioenergetics",
            domain="Life Sciences",
            status="READY"
        )
        db.add(bio_course)
        await db.flush()

        bio_content = (
            "Mitochondria are the primary powerhouses of the eukaryotic cell. "
            "The proton electrochemical gradient across the inner mitochondrial membrane powers ATP synthase rotation. "
            "Oxidative phosphorylation synthesizes ATP from adenosine diphosphate and inorganic phosphate.\n\n"
            "Glycolysis occurs in the cytoplasm and breaks down one glucose molecule into two pyruvate molecules. "
            "The net energetic yield of glycolysis is two ATP and two NADH molecules under anaerobic conditions."
        ).encode("utf-8")

        bio_ingest = await MultimodalIngestionService.process_document(
            db=db,
            course_id=bio_course.id,
            filename="Cell_Biology_Ch4.txt",
            file_bytes=bio_content
        )
        assert bio_ingest["status"] == "ready"
        assert bio_ingest["knowledge_units"] >= 2
        assert "Cellular Biology" in bio_ingest["filename"] or bio_ingest["topics"] >= 1

        # Retrieval Assertion for Biology
        bio_retrieval = await HybridRetriever.retrieve(
            db=db,
            course_id=bio_course.id,
            query="How does ATP synthase work in mitochondria to make ATP?",
            top_k=3
        )
        assert len(bio_retrieval["results"]) > 0
        top_bio = bio_retrieval["results"][0]
        assert "mitochondria" in top_bio["content"].lower() or "atp" in top_bio["content"].lower()
        # ABSOLUTE ZERO DEADLOCK EVIDENCE CHECK:
        for hit in bio_retrieval["results"]:
            assert "deadlock" not in hit["content"].lower()
            assert "coffman" not in hit["content"].lower()
            assert "banker" not in hit["content"].lower()

        # AI Tutor Grounding Assertion for Biology
        bio_tutor = await GroundedTutorService.ask(
            db=db,
            course_id=bio_course.id,
            query="What is the net yield of glycolysis?",
            mode="beginner",
            scope="course"
        )
        assert bio_tutor["grounded"] is True
        assert len(bio_tutor["citations"]) > 0
        assert "Cell_Biology_Ch4.txt" in bio_tutor["citations"][0]["document"]
        assert "deadlock" not in bio_tutor["answer"].lower()

        # Assessment Question Generation for Biology
        bio_questions = await AdaptiveQuestionGenerator.generate_questions_for_course(
            db=db,
            course_id=bio_course.id,
            count=2
        )
        assert len(bio_questions) >= 1
        for q in bio_questions:
            assert "deadlock" not in q["question_text"].lower()
            assert "coffman" not in q["question_text"].lower()
            assert any(term in q["question_text"].lower() or term in q["concept_name"].lower() for term in ["atp", "mitochondria", "glycolysis", "cell"])

        # Quick Revision for Biology
        bio_revision = await RevisionGeneratorService.generate_quick_revision(
            db=db,
            course_id=bio_course.id
        )
        assert "deadlock" not in bio_revision["title"].lower()
        assert not any("deadlock" in take.lower() for take in bio_revision["core_takeaways"])

        # Exam Simulator for Biology
        bio_exam = await ExamSimulatorService.create_exam(
            db=db,
            course_id=bio_course.id,
            question_count=2
        )
        assert "Cellular Biology" in bio_exam["title"]
        assert len(bio_exam["questions"]) >= 1

        # =====================================================================
        # SUBJECT B: World History (The French Revolution)
        # =====================================================================
        hist_course = Course(
            code=f"HIST_201_{run_id}",
            title="The French Revolution & Modern History",
            domain="History",
            status="READY"
        )
        db.add(hist_course)
        await db.flush()

        hist_content = (
            "On July 14, 1789, insurgents stormed the medieval fortress and prison known as the Bastille. "
            "The Parisian revolutionaries sought to seize large stores of gunpowder and ammunition to resist royal military forces. "
            "The fall of the Bastille became the paramount symbol of the collapse of royal despotism.\n\n"
            "In June 1789, delegates of the Third Estate broke away from the traditional Estates-General assembly. "
            "They constituted themselves as the National Assembly and swore the Tennis Court Oath, demanding constitutional equality."
        ).encode("utf-8")

        hist_ingest = await MultimodalIngestionService.process_document(
            db=db,
            course_id=hist_course.id,
            filename="French_Revolution_Lectures.txt",
            file_bytes=hist_content
        )
        assert hist_ingest["status"] == "ready"

        hist_retrieval = await HybridRetriever.retrieve(
            db=db,
            course_id=hist_course.id,
            query="Why did revolutionaries storm the Bastille in July 1789?",
            top_k=3
        )
        assert len(hist_retrieval["results"]) > 0
        top_hist = hist_retrieval["results"][0]
        assert "bastille" in top_hist["content"].lower() or "1789" in top_hist["content"].lower()
        for hit in hist_retrieval["results"]:
            assert "deadlock" not in hit["content"].lower()
            assert "banker" not in hit["content"].lower()

        # Questions for History
        hist_questions = await AdaptiveQuestionGenerator.generate_questions_for_course(
            db=db,
            course_id=hist_course.id,
            count=2
        )
        assert len(hist_questions) >= 1
        for q in hist_questions:
            assert "deadlock" not in q["question_text"].lower()
            assert any(term in q["question_text"].lower() or term in q["concept_name"].lower() for term in ["bastille", "estate", "revolution", "french"])

        # =====================================================================
        # SUBJECT C: Computer Networks (Transport Layer)
        # =====================================================================
        net_course = Course(
            code=f"NET_301_{run_id}",
            title="Computer Networking Protocols",
            domain="Computer Science",
            status="READY"
        )
        db.add(net_course)
        await db.flush()

        net_content = (
            "The Transmission Control Protocol establishes a reliable connection using the TCP three-way handshake. "
            "The initiating client transmits a SYN packet with an initial sequence number. "
            "The server responds with a SYN-ACK packet, and the client replies with an ACK packet.\n\n"
            "The User Datagram Protocol is a connectionless transport protocol that transmits datagrams without handshakes. "
            "UDP avoids retransmission overhead and latency delays, making it optimal for live audio and interactive video streams."
        ).encode("utf-8")

        net_ingest = await MultimodalIngestionService.process_document(
            db=db,
            course_id=net_course.id,
            filename="Networking_Protocols.txt",
            file_bytes=net_content
        )
        assert net_ingest["status"] == "ready"

        net_retrieval = await HybridRetriever.retrieve(
            db=db,
            course_id=net_course.id,
            query="What packets are exchanged during a TCP three-way handshake?",
            top_k=2
        )
        assert len(net_retrieval["results"]) > 0
        assert any("syn" in r["content"].lower() for r in net_retrieval["results"])
        for hit in net_retrieval["results"]:
            assert "deadlock" not in hit["content"].lower()

        # =====================================================================
        # SUBJECT D: Operating Systems Deadlocks (Preserved in dedicated course)
        # =====================================================================
        # Querying OS_101 or deadlock content correctly returns deadlocks without breaking
        os_res = await db.execute(select(Course).filter(Course.code == "OS_101"))
        os_course = os_res.scalars().first()
        if os_course:
            os_retrieval = await HybridRetriever.retrieve(
                db=db,
                course_id=os_course.id,
                query="What are the four Coffman conditions for deadlock?",
                top_k=2
            )
            assert len(os_retrieval["results"]) > 0
            # Here deadlock content SHOULD be found because user asked the OS course about deadlocks
            assert "deadlock" in os_retrieval["results"][0]["content"].lower() or "coffman" in os_retrieval["results"][0]["content"].lower()

        # =====================================================================
        # SUBJECT E: Multimodal Video/Audio Transcript with Timestamps
        # =====================================================================
        audio_transcript = (
            "[01:15] Welcome everyone. Today we are examining cellular bioenergetics in the mitochondria.\n"
            "[03:45] Notice how ATP synthase uses proton motive force across the cristae membrane.\n"
            "[06:20] In our next segment, we contrast aerobic respiration with anaerobic fermentation."
        ).encode("utf-8")

        audio_ingest = await MultimodalIngestionService.process_document(
            db=db,
            course_id=bio_course.id,
            filename="Bio_Lecture_Podcast.mp4",
            file_bytes=audio_transcript
        )
        assert audio_ingest["status"] == "ready"
        assert audio_ingest["video_segments"] == 3

        # Retrieve specific timestamped segment
        seg_retrieval = await HybridRetriever.retrieve(
            db=db,
            course_id=bio_course.id,
            query="proton motive force cristae membrane",
            top_k=1
        )
        assert len(seg_retrieval["results"]) > 0
        top_seg = seg_retrieval["results"][0]
        assert top_seg["source"].get("type") in ["video", "pdf", "docx"]

        # =====================================================================
        # SUBJECT F: Slide-Heavy Document with Notes
        # =====================================================================
        slides_data = [
            {
                "slide_number": 1,
                "title": "Introduction to Cellular Metabolism",
                "text": "Cellular respiration converts biochemical energy from nutrients into ATP.",
                "speaker_notes": "Emphasize to students that ATP is the universal molecular energy currency.",
                "diagram_description": "Schematic diagram comparing glycolysis, Krebs cycle, and electron transport chain.",
                "source": {"type": "pptx", "slide": 1}
            },
            {
                "slide_number": 2,
                "title": "Mitochondrial Electron Transport",
                "text": "Complexes I through IV transfer electrons and pump protons across the inner membrane.",
                "speaker_notes": "Check for student misconceptions between passive diffusion and active proton pumping.",
                "diagram_description": "Membrane protein complexes pumping H+ into intermembrane space.",
                "source": {"type": "pptx", "slide": 2}
            }
        ]
        slide_chunks = SemanticChunker.chunk_pptx_slides(slides_data, "Metabolism_Slides.pptx")
        assert len(slide_chunks) == 2
        assert slide_chunks[0]["source"]["slide"] == 1
        assert "Presenter Notes" in slide_chunks[0]["content"]
        assert "Visual Description" in slide_chunks[0]["content"]

        # =====================================================================
        # PROOF OF STRICT ISOLATION & ZERO CROSS-POLLINATION
        # =====================================================================
        # Querying BIO_101 for a history question returns ZERO history hits from the database
        isolated_check = await HybridRetriever.retrieve(
            db=db,
            course_id=bio_course.id,
            query="Who was Robespierre during the Reign of Terror?",
            top_k=3
        )
        for hit in isolated_check["results"]:
            assert "robespierre" not in hit["content"].lower()
            assert "guillotine" not in hit["content"].lower()

        # Querying HIST_201 for a networking question returns ZERO networking hits
        hist_isolated_check = await HybridRetriever.retrieve(
            db=db,
            course_id=hist_course.id,
            query="What is a TCP SYN packet?",
            top_k=3
        )
        for hit in hist_isolated_check["results"]:
            assert "syn" not in hit["content"].lower()
            assert "tcp" not in hit["content"].lower()

        # Flashcard SM-2 Spaced Repetition for Biology Course
        bio_cards = await FlashcardService.get_due_flashcards(
            db=db,
            user_id="demo-learner-uuid-1",
            course_id=bio_course.id,
            limit=5
        )
        assert len(bio_cards) >= 1
        assert any("atp" in c["front"].lower() or "mitochondria" in c["front"].lower() or "glycolysis" in c["front"].lower() or "cellular" in c["topic"].lower() for c in bio_cards)
        for c in bio_cards:
            assert "deadlock" not in c["front"].lower()
            assert "coffman" not in c["front"].lower()
