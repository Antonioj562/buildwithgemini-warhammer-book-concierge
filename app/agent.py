# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import math
import re

from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

MODEL = "gemini-3.6-flash"

# Hardcoded project ID as required for Agent Platform compatibility
PROJECT_ID = "qwiklabs-gcp-04-4af6105616e2"
COLLECTION_NAME = "warhammer_books"
USER_LOGS_COLLECTION = "user_reading_logs"
GCS_BUCKET_NAME = "warhammer-book-concierge-covers-qwiklabs-gcp-04-4af6105616e2"

# Lazy-initialized Firestore client
_firestore_client = None


def _get_firestore_client() -> firestore.Client:
    global _firestore_client
    if _firestore_client is None:
        _firestore_client = firestore.Client(project=PROJECT_ID)
    return _firestore_client


def get_books_from_firestore(query: str = "", faction: str = "", series: str = "") -> str:
    """Queries the Firestore catalog ('warhammer_books') for Warhammer 40k/30k books and audiobooks.

    Args:
        query: Optional general keyword or title search term.
        faction: Optional faction or Space Marine legion filter (e.g. 'Thousand Sons', 'Space Wolves', 'Necrons').
        series: Optional series name filter (e.g. 'The Horus Heresy' or 'Warhammer 40,000').

    Returns:
        A list of matching books retrieved directly from the Firestore database.
    """
    db = _get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()

    results = []
    q = query.lower().strip()
    f = faction.lower().strip()
    s = series.lower().strip()

    for doc in docs:
        book = doc.to_dict()
        match = True
        title = book.get("title", "")
        synopsis = book.get("synopsis", "")
        author = book.get("author", "")
        book_faction = book.get("faction", "")
        book_series = book.get("series", "")

        if q and not (q in title.lower() or q in synopsis.lower() or q in author.lower()):
            match = False
        if f and f not in book_faction.lower():
            match = False
        if s and s not in book_series.lower():
            match = False

        if match:
            results.append(
                f"- **{title}** ({book_series} #{book.get('series_index', '?')}) by {author}\n"
                f"  *Faction*: {book_faction}\n"
                f"  *Primary Format*: {book.get('format', 'book')}\n"
                f"  *Synopsis*: {synopsis}"
            )

    if not results:
        return f"No books found in Firestore for query='{query}', faction='{faction}', series='{series}'."

    return "\n\n".join(results)


def add_or_update_book_in_firestore(
    title: str,
    author: str,
    series: str,
    series_index: int,
    faction: str,
    synopsis: str,
    format_type: str = "book",
    rating: str = None,
) -> str:
    """Adds a new book or updates an existing book entry in the Firestore 'warhammer_books' collection.

    Args:
        title: Title of the book or audiobook.
        author: Author name.
        series: Series name (e.g. 'The Horus Heresy', 'Warhammer 40,000').
        series_index: Number/index in the series.
        faction: Associated faction or Space Marine legion.
        synopsis: Brief plot summary or description.
        format_type: Primary format ('audiobook', 'physical', 'ebook').
        rating: Optional rating string (e.g. '5/5').

    Returns:
        Confirmation message of document save in Firestore.
    """
    db = _get_firestore_client()
    doc_id = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    doc_ref = db.collection(COLLECTION_NAME).document(doc_id)

    data = {
        "title": title,
        "author": author,
        "series": series,
        "series_index": series_index,
        "faction": faction,
        "synopsis": synopsis,
        "format": format_type,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if rating:
        data["rating"] = rating

    doc_ref.set(data, merge=True)
    return f"Successfully saved '{title}' into Firestore collection '{COLLECTION_NAME}' (Document ID: {doc_id})."


def log_user_reading_activity(
    book_title: str,
    format_type: str = "book",
    status: str = "completed",
    rating: str = None,
    thoughts: str = None,
) -> str:
    """Logs a user's reading or audiobook activity (e.g., read, listened, currently listening) into Firestore.

    Args:
        book_title: The title of the book or audiobook.
        format_type: Format of consumption ('audiobook', 'physical', 'ebook', 'audio drama').
        status: Reading status ('completed', 'in_progress', 'want_to_read', 'dropped').
        rating: Optional rating given by the user (e.g. '5/5', '10/10').
        thoughts: Optional user notes or thoughts about the book.

    Returns:
        Confirmation message for logging the activity into Firestore.
    """
    db = _get_firestore_client()
    doc_id = f"{re.sub(r'[^a-z0-9]+', '-', book_title.lower()).strip('-')}-{int(datetime.datetime.now().timestamp())}"
    doc_ref = db.collection(USER_LOGS_COLLECTION).document(doc_id)

    data = {
        "book_title": book_title,
        "format": format_type,
        "status": status,
        "logged_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if rating:
        data["rating"] = rating
    if thoughts:
        data["thoughts"] = thoughts

    doc_ref.set(data)
    return f"Logged activity in Firestore collection '{USER_LOGS_COLLECTION}': Title='{book_title}', Format='{format_type}', Status='{status}'."


async def generate_cartoon_cover_art(
    tool_context: ToolContext,
    book_title: str,
    visual_description: str,
    faction: str = "",
) -> str:
    """Generates vibrant, cartoon / animated comic-book style cover art for a Warhammer 40k or 30k book or audiobook based on a visual description.

    Args:
        tool_context: Injected ToolContext for saving session artifacts in the Playground.
        book_title: Title of the book or audiobook.
        visual_description: Detailed visual description of the cover art scene (characters, armor, action, environment).
        faction: Associated faction or Space Marine legion (e.g. 'Space Wolves', 'Thousand Sons', 'Ultramarines').

    Returns:
        Public Cloud Storage HTTPS URL of the generated cover art image.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    prompt = (
        f"Generate a vibrant, cartoon / animated comic-book style Warhammer 40,000 / 30,000 book cover artwork for '{book_title}'. "
        f"Faction: {faction}. "
        f"Visual Scene Description: {visual_description}. "
        f"Art Style Instructions: Vibrant cartoon illustration style, bold clean black outlines, dynamic stylized comic book animation aesthetic, vibrant saturated colors, high resolution, heroic character pose."
    )

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        for candidate in response.candidates:
            for part in candidate.content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    raw_bytes = part.inline_data.data
                    file_name = f"{re.sub(r'[^a-z0-9]+', '_', book_title.lower()).strip('_')}_cartoon_cover.png"

                    # Resize image bytes to compact dimensions (max 512x512)
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(raw_bytes))
                        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                        out_buf = io.BytesIO()
                        img.save(out_buf, format="PNG", optimize=True)
                        img_data = out_buf.getvalue()
                    except Exception:
                        img_data = raw_bytes

                    # (1) Save artifact in Playground Artifacts panel
                    try:
                        artifact_part = types.Part.from_bytes(data=img_data, mime_type="image/png")
                        await tool_context.save_artifact(filename=file_name, artifact=artifact_part)
                    except Exception as art_err:
                        pass

                    # (2) Upload compact image bytes directly to public GCS bucket
                    sc = storage.Client(project=PROJECT_ID)
                    bucket = sc.bucket(GCS_BUCKET_NAME)
                    blob = bucket.blob(file_name)
                    blob.upload_from_string(img_data, content_type="image/png")

                    public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{file_name}"
                    
                    # Return HTML img tag with dynamic responsive styling to fit chat window
                    responsive_html = (
                        f'<img src="{public_url}" alt="{book_title} Cartoon Cover Art" '
                        f'style="max-width: 100%; max-height: 280px; width: auto; height: auto; '
                        f'border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); display: block; margin: 10px 0;" />\n\n'
                        f'Public Image URL: {public_url}'
                    )
                    return responsive_html
    except Exception as e:
        return f"Error generating cover art image: {str(e)}"

    return f"Unable to generate image for '{book_title}'."


async def generate_item_video(
    tool_context: ToolContext,
    title: str,
    prompt: str,
) -> str:
    """Generates a short video for a Warhammer 40k or 30k item, character, or scene using Google's Omni model (gemini-omni-flash-preview).

    Args:
        tool_context: Injected ToolContext for saving session artifacts in the Playground.
        title: Title of the book, character, or item for the video.
        prompt: Detailed visual prompt describing the scene, action, or character to generate in the short video.

    Returns:
        Public Cloud Storage HTTPS URL of the generated MP4 video.
    """
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
    try:
        response = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=(
                f"Generate a short animated cartoon video of {title}. "
                f"Art style: vibrant cartoon comic-book illustration style with bold black outlines, cel shading, and heroic action framing. "
                f"Visual description: {prompt}"
            ),
            response_modalities=["text", "video"],
        )

        raw_bytes = None
        if hasattr(response, "output_video") and response.output_video:
            v_data = getattr(response.output_video, "data", None) or (
                response.output_video.get("data") if isinstance(response.output_video, dict) else None
            )
            if v_data:
                import base64
                raw_bytes = base64.b64decode(v_data)

        if not raw_bytes and hasattr(response, "outputs") and response.outputs:
            for out in response.outputs:
                out_type = getattr(out, "type", None) or (out.get("type") if isinstance(out, dict) else None)
                out_data = getattr(out, "data", None) or (out.get("data") if isinstance(out, dict) else None)
                if out_type == "video" and out_data:
                    import base64
                    raw_bytes = base64.b64decode(out_data)
                    break

        if not raw_bytes:
            return f"Unable to retrieve video bytes for '{title}'."

        file_name = f"{re.sub(r'[^a-z0-9]+', '_', title.lower()).strip('_')}_video.mp4"

        # (1) Save artifact in Playground Artifacts panel
        try:
            artifact_part = types.Part.from_bytes(data=raw_bytes, mime_type="video/mp4")
            await tool_context.save_artifact(filename=file_name, artifact=artifact_part)
        except Exception as art_err:
            pass

        # (2) Upload video bytes directly to public GCS bucket
        sc = storage.Client(project=PROJECT_ID)
        bucket = sc.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(file_name)
        blob.upload_from_string(raw_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{file_name}"
        return public_url

    except Exception as e:
        return f"Error generating video: {str(e)}"


def calculate_reading_stats(books_read_count: int, total_heresy_read: int) -> str:
    """Calculates reading statistics and completion percentages for Warhammer series.

    Args:
        books_read_count: Total number of Warhammer books read or listened to so far.
        total_heresy_read: Number of mainline Horus Heresy books completed (out of 54 main entries).

    Returns:
        Formatted summary of reading progress percentages and milestones.
    """
    TOTAL_HERESY_ENTRIES = 54
    heresy_pct = round((total_heresy_read / TOTAL_HERESY_ENTRIES) * 100, 1) if TOTAL_HERESY_ENTRIES > 0 else 0
    return (
        f"Reading Stats Summary:\n"
        f"- Total Warhammer Books/Audiobooks Read: {books_read_count}\n"
        f"- Horus Heresy Mainline Progress: {total_heresy_read}/{TOTAL_HERESY_ENTRIES} books ({heresy_pct}% complete)\n"
        f"- Remaining Horus Heresy Mainline: {TOTAL_HERESY_ENTRIES - total_heresy_read} books"
    )


def get_horus_heresy_reading_path(faction_or_legion: str = "") -> str:
    """Provides a curated, chronological reading roadmap for the Horus Heresy series (30k) tailored to a specific Space Marine Legion, faction, or key event.

    Args:
        faction_or_legion: The Space Marine Legion, faction, or event interest (e.g. 'Alpha Legion', 'Thousand Sons', 'Space Wolves', 'Blood Angels', 'Ultramarines', 'World Eaters', 'Siege of Terra').

    Returns:
        A step-by-step reading roadmap highlighting essential books, key plot arcs, and where to jump in.
    """
    key = faction_or_legion.lower().strip()

    paths = {
        "alpha legion": [
            "1. **Horus Rising** (Horus Heresy #1) by Dan Abnett — *Essential Opening Trilogy*",
            "2. **False Gods** (Horus Heresy #2) by Graham McNeill — *Warmaster's Fall*",
            "3. **Galaxy in Flames** (Horus Heresy #3) by Ben Counter — *Istvaan III Betrayal*",
            "4. **Legion** (Horus Heresy #7) by Dan Abnett — *THE definitive Alpha Legion origin novel introducing Alpharius, Omegon, and the Cabal*",
            "5. **Scars** (Horus Heresy #28) by Chris Wraight — *Alpha Legion blockade and White Scars dilemma*",
            "6. **Praetorian of Dorn** (Horus Heresy #39) by John French — *Alpha Legion's covert infiltration of Sol System vs Imperial Fists*",
            "7. **The Buried Dagger** (Horus Heresy #54) by James Swallow — *Final prep before Siege of Terra*",
        ],
        "thousand sons": [
            "1. **Horus Heresy Opening Trilogy** (#1 Horus Rising, #2 False Gods, #3 Galaxy in Flames)",
            "2. **A Thousand Sons** (Horus Heresy #12) by Graham McNeill — *The tragedy of Magnus the Red, the Council of Nikaea, and the Prospero catastrophe*",
            "3. **Prospero Burns** (Horus Heresy #15) by Dan Abnett — *The Space Wolves counter-perspective on the Burning of Prospero*",
            "4. **The Crimson King** (Horus Heresy #44) by Graham McNeill — *Magnus seeks the shattered shards of his soul*",
            "5. **The Solar War** (Siege of Terra #1) by John French — *Thousand Sons assault on the Sol System*",
        ],
        "space wolves": [
            "1. **Horus Heresy Opening Trilogy** (#1 Horus Rising, #2 False Gods, #3 Galaxy in Flames)",
            "2. **Prospero Burns** (Horus Heresy #15) by Dan Abnett — *Leman Russ & the Vlka Fenryka unleashed on Prospero*",
            "3. **Scars** (Horus Heresy #28) by Chris Wraight — *Space Wolves surviving the Alpha Legion ambush at Alaxxes*",
            "4. **Wolfsbane** (Horus Heresy #49) by Guy Haley — *Leman Russ vs Horus Lupercal in single combat*",
        ],
        "blood angels": [
            "1. **Horus Heresy Opening Trilogy** (#1 Horus Rising, #2 False Gods, #3 Galaxy in Flames)",
            "2. **Fear to Tread** (Horus Heresy #21) by James Swallow — *Sanguinius and the Blood Angels ambushed at Signus Prime by Daemons*",
            "3. **The Unremembered Empire** (Horus Heresy #27) by Dan Abnett — *Imperium Secundus arc in Ultramar*",
            "4. **Ruinstorm** (Horus Heresy #46) by David Annandale — *Sanguinius breaking through the Ruinstorm to Terra*",
            "5. **The Lost and the Damned** (Siege of Terra #2) by Guy Haley — *Sanguinius defending the Eternity Gate*",
        ],
        "ultramarines": [
            "1. **Know No Fear** (Horus Heresy #19) by Dan Abnett — *Word Bearers surprise attack on Calth*",
            "2. **Betrayer** (Horus Heresy #24) by Aaron Dembski-Bowden — *Shadow Crusade: World Eaters & Word Bearers invade Ultramar*",
            "3. **The Unremembered Empire** (Horus Heresy #27) by Dan Abnett — *Roboute Guilliman establishes Imperium Secundus*",
            "4. **Angels of Caliban** (Horus Heresy #38) by Gav Thorpe — *Guilliman, Sanguinius, and Lion El'Jonson tension*",
            "5. **Ruinstorm** (Horus Heresy #46) by David Annandale — *Fighting through Chaos storms towards Terra*",
        ],
    }

    matched_key = None
    for p_key in paths:
        if p_key in key or key in p_key:
            matched_key = p_key
            break

    if matched_key:
        roadmap_lines = paths[matched_key]
        return (
            f"### 🗺️ Horus Heresy Curated Reading Path: **{faction_or_legion.title()}**\n\n"
            + "\n".join(roadmap_lines)
            + "\n\n*Pro-tip: You can listen to these titles as unabridged audiobooks narrated by Jonathan Keeble!*"
        )

    # General / Fallback Horus Heresy Core Path
    return (
        f"### 🗺️ Horus Heresy Core Essential Reading Order\n"
        f"1. **Horus Rising** (Book #1) by Dan Abnett\n"
        f"2. **False Gods** (Book #2) by Graham McNeill\n"
        f"3. **Galaxy in Flames** (Book #3) by Ben Counter\n"
        f"4. **The Flight of the Eisenstein** (Book #4) by James Swallow (Death Guard/Garro)\n"
        f"5. **Fulgrim** (Book #5) by Graham McNeill (Emperor's Children & Istvaan V Dropsite Massacre)\n"
        f"6. **Legion** (Book #7) by Dan Abnett (Alpha Legion & The Cabal)\n"
        f"7. **The First Heretic** (Book #14) by Aaron Dembski-Bowden (Word Bearers & origin of Heresy)\n"
        f"8. **Know No Fear** (Book #19) by Dan Abnett (Battle of Calth)\n"
        f"9. **Master of Mankind** (Book #41) by Aaron Dembski-Bowden (The Emperor in the Webway)\n"
        f"10. **Siege of Terra Series** (Books 1-8 ending with *The End and the Death*)\n\n"
        f"*(Specify a faction like Alpha Legion, Thousand Sons, Space Wolves, or Ultramarines for a customized path!)*"
    )


def get_faction_beginner_guide(faction: str) -> str:
    """Recommends the single best starting novel or series entry point for any Warhammer 40,000 / 30,000 faction.

    Args:
        faction: The faction name (e.g. 'Astra Militarum', 'Inquisition', 'Space Marines', 'Necrons', 'Orks', 'Night Lords', 'Adeptus Custodes', 'Tau Empire').

    Returns:
        Recommended beginner novel, author, key themes, and recommended consumption format (e.g., Audiobook vs Physical).
    """
    f = faction.lower().strip()

    guides = {
        "astra militarum": {
            "title": "Gaunt's Ghosts: First and Only",
            "author": "Dan Abnett",
            "format": "Audiobook / Physical (Narrated by Toby Longworth)",
            "why": "Follows Colonel-Commissar Ibram Gaunt and the Tanith First-and-Only 'Ghost' regiment in gritty, military sci-fi ground warfare across the Sabbat Worlds.",
        },
        "inquisition": {
            "title": "Eisenhorn: Xenos",
            "author": "Dan Abnett",
            "format": "Audiobook (Narrated by Toby Longworth)",
            "why": "The premier detective noir sci-fi masterpiece. Inquisitor Gregor Eisenhorn hunts heretics, aliens, and daemons across the Imperium's dark underbelly.",
        },
        "necrons": {
            "title": "The Infinite and the Divine",
            "author": "Robert Rath",
            "format": "Audiobook (Narrated by Richard Reed — FAN FAVORITE)",
            "why": "A hilarious and epic multi-millennia rival dynamic between Trazyn the Infinite and Orikan the Diviner as they squabble over ancient artifacts.",
        },
        "orks": {
            "title": "Brutal Kunnin'",
            "author": "Mike Brooks",
            "format": "Audiobook / Physical",
            "why": "Hilarious Ork perspective during a massive WAAAGH! invasion on an Adeptus Mechanicus forge world. Pure Ork madness and kunnin' tactics.",
        },
        "night lords": {
            "title": "Night Lords Omnibus (Soul Hunter)",
            "author": "Aaron Dembski-Bowden",
            "format": "Audiobook (Narrated by Andrew Wincott) / Physical",
            "why": "Widely considered one of the best Chaos Space Marine perspectives ever written. Grim, tragic, and terrifyingly immersive.",
        },
        "space marines": {
            "title": "Helsreach (Black Templars) or Dark Imperium (Ultramarines)",
            "author": "Aaron Dembski-Bowden / Guy Haley",
            "format": "Audiobook / Physical",
            "why": "Helsreach features Chaplain Grimaldus defending a hive city against millions of Orks. Dark Imperium showcases Primarch Roboute Guilliman in Era Indomitus.",
        },
    }

    matched_guide = None
    for g_key, data in guides.items():
        if g_key in f or f in g_key:
            matched_guide = (g_key, data)
            break

    if matched_guide:
        g_name, info = matched_guide
        return (
            f"### 🚀 Ultimate Beginner Guide: **{g_name.title()}**\n"
            f"- **Top Recommended Entry Book**: *{info['title']}*\n"
            f"- **Author**: {info['author']}\n"
            f"- **Recommended Format**: {info['format']}\n"
            f"- **Why it's the best start**: {info['why']}"
        )

    # General Fallback
    return (
        f"### 🚀 Top Recommended Warhammer 40k Entry Points:\n"
        f"1. **Inquisition**: *Eisenhorn: Xenos* by Dan Abnett\n"
        f"2. **Astra Militarum**: *Gaunt's Ghosts: First and Only* by Dan Abnett\n"
        f"3. **Space Marines**: *Helsreach* by Aaron Dembski-Bowden\n"
        f"4. **Necrons**: *The Infinite and the Divine* by Robert Rath\n"
        f"5. **Chaos Space Marines**: *Night Lords: Soul Hunter* by Aaron Dembski-Bowden"
    )


RAG_CORPUS_NAME = "projects/369908537639/locations/us-central1/ragCorpora/8037843415414603776"


def consult_black_library_corpus(query: str) -> str:
    """Search the official Black Library Warhammer 40k & 30k reference corpus and return matched passages and book lore.

    Args:
        query: What to look up (a book title, character, plot point, or faction lore).

    Returns:
        The matched reference passages, or a note if none was found.
    """
    from vertexai import rag
    import vertexai
    try:
        vertexai.init(project=PROJECT_ID, location="us-central1")
        resp = rag.retrieval_query(
            text=query,
            rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS_NAME)],
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=5),
        )
    except Exception as e:
        return f"Retrieval failed: {e}"

    contexts = getattr(resp.contexts, "contexts", [])
    passages = [c.text.strip() for c in contexts if getattr(c, "text", "").strip()]
    return "\n\n---\n\n".join(passages) or "No relevant Black Library passage found."


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback triggered after each turn to extract durable user preferences/facts into Vertex AI Memory Bank."""
    await callback_context.add_session_to_memory()
    return None


AGENT_ENGINE_RESOURCE_NAME = "projects/369908537639/locations/us-east1/reasoningEngines/3355973370763018240"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME,
)


from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback

a2ui_schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = a2ui_schema_manager.generate_system_prompt(
    role_description=(
        "You are the Warhammer 40k & 30k Book Concierge. You help Warhammer fans discover novels and audiobooks, "
        "navigate the Horus Heresy reading order, track their reading and audiobook progress in Firestore, "
        "recommend titles based on their favorite factions and Space Marine Legions, "
        "and generate custom cartoon-style cover art for books based on visual cover descriptions."
    ),
    workflow_description="Analyze the request and return structured A2UI cards/UI when appropriate, or use function tools to fetch book data, log reading activity, consult the Black Library corpus, generate cover art, or calculate reading stats.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects.\n\n"
        "FIRESTORE, COVER ART, RAG & MEMORY TOOL INSTRUCTIONS:\n"
        "- Use `consult_black_library_corpus` to search official Black Library book reference guides, plot summaries, and lore passages.\n"
        "- Use `get_books_from_firestore` to query the live Warhammer book catalog stored in Firestore.\n"
        "- Use `add_or_update_book_in_firestore` to add new book entries to the catalog.\n"
        "- Use `get_horus_heresy_reading_path` to navigate tailored Horus Heresy (30k) reading roadmaps by faction/legion.\n"
        "- Use `get_faction_beginner_guide` to provide beginner starting points for any 40k or 30k faction.\n"
        "- Whenever the user mentions reading or listening to a book or audiobook, use `log_user_reading_activity` "
        "to record the activity into Firestore.\n"
        "- Whenever cover art is requested or when suggesting cover art descriptions for Warhammer 40k/30k books, "
        "ALWAYS use the `generate_cartoon_cover_art` tool. Ensure all generated cover art uses a vibrant, cartoon / comic-book illustration style with bold black outlines and heroic action framing.\n"
        "- Whenever a short video is requested for a book, character, or scene, use `generate_item_video` to generate "
        "a video using Google's Omni model (gemini-omni-flash-preview).\n"
        "- Always distinguish between physical/ebook reads and audiobooks when recalling or summarizing history.\n"
        "- You have access to Python code execution in a secure Agent Engine sandbox (`code_executor`). Use it when complex calculation, data manipulation, or custom script execution is needed."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        consult_black_library_corpus,
        get_books_from_firestore,
        add_or_update_book_in_firestore,
        log_user_reading_activity,
        generate_cartoon_cover_art,
        generate_item_video,
        calculate_reading_stats,
        get_horus_heresy_reading_path,
        get_faction_beginner_guide,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

