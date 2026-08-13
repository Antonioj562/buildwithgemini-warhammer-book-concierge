# Copyright 2026 Google LLC
# Seed script for Warhammer 40k & 30k Book Concierge Firestore collection

from google.cloud import firestore

PROJECT_ID = "qwiklabs-gcp-04-4af6105616e2"

COLLECTION_NAME = "warhammer_books"

INITIAL_BOOKS = [
    {
        "id": "horus-rising",
        "title": "Horus Rising",
        "series": "The Horus Heresy",
        "series_index": 1,
        "author": "Dan Abnett",
        "faction": "Sons of Horus / Luna Wolves",
        "synopsis": "The seeds of heresy are sown at the height of the Great Crusade as Warmaster Horus leads the Space Marine Legions.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "5/5",
    },
    {
        "id": "false-gods",
        "title": "False Gods",
        "series": "The Horus Heresy",
        "series_index": 2,
        "author": "Graham McNeill",
        "faction": "Sons of Horus / Chaos",
        "synopsis": "Warmaster Horus is wounded on Davin, and dark forces scheme to corrupt the Master of Mankind's favored son.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "4.5/5",
    },
    {
        "id": "galaxy-in-flames",
        "title": "Galaxy in Flames",
        "series": "The Horus Heresy",
        "series_index": 3,
        "author": "Ben Counter",
        "faction": "Sons of Horus / World Eaters / Emperor's Children",
        "synopsis": "The tragic betrayal at Isstvan III unfolds as loyalist Space Marines fight for survival against their Primarchs.",
        "format": "physical",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "5/5",
    },
    {
        "id": "the-flight-of-the-eisenstein",
        "title": "The Flight of the Eisenstein",
        "series": "The Horus Heresy",
        "series_index": 4,
        "author": "James Swallow",
        "faction": "Death Guard / Imperial",
        "synopsis": "Captain Nathaniel Garro steals the frigate Eisenstein to warn Terra of Warmaster Horus's treason.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "4.8/5",
    },
    {
        "id": "fulgrim",
        "title": "Fulgrim",
        "series": "The Horus Heresy",
        "series_index": 5,
        "author": "Graham McNeill",
        "faction": "Emperor's Children",
        "synopsis": "The descent of Primarch Fulgrim and his Emperor's Children Legion into decadence and Chaos obsession.",
        "format": "ebook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "4.7/5",
    },
    {
        "id": "thousand-sons",
        "title": "Thousand Sons",
        "series": "The Horus Heresy",
        "series_index": 12,
        "author": "Graham McNeill",
        "faction": "Thousand Sons",
        "synopsis": "Magnus the Red attempts to warn the Emperor of Horus's betrayal through forbidden sorcery, triggering the Burning of Prospero.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "5/5",
    },
    {
        "id": "prospero-burns",
        "title": "Prospero Burns",
        "series": "The Horus Heresy",
        "series_index": 15,
        "author": "Dan Abnett",
        "faction": "Space Wolves",
        "synopsis": "Leman Russ and his Space Wolves are unleashed upon Prospero to bring Magnus the Red to justice.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "4.6/5",
    },
    {
        "id": "eisenhorn-xenos",
        "title": "Eisenhorn: Xenos",
        "series": "Warhammer 40,000",
        "series_index": 1,
        "author": "Dan Abnett",
        "faction": "Inquisition / Imperium",
        "synopsis": "Inquisitor Gregor Eisenhorn investigates a sinister alien mystery and Heretic cabal in the 41st Millennium.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "5/5",
    },
    {
        "id": "helsreach",
        "title": "Helsreach",
        "series": "Warhammer 40,000",
        "series_index": 1,
        "author": "Aaron Dembski-Bowden",
        "faction": "Black Templars / Orks",
        "synopsis": "Chaplain Grimaldus and the Black Templars defend the hive city of Helsreach against a massive Ork Waaagh!.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "4.9/5",
    },
    {
        "id": "the-infinite-and-the-divine",
        "title": "The Infinite and the Divine",
        "series": "Warhammer 40,000",
        "series_index": 1,
        "author": "Robert Rath",
        "faction": "Necrons",
        "synopsis": "Trazyn the Infinite and Orikan the Diviner engage in a millenia-long feud across time and space over an ancient artifact.",
        "format": "audiobook",
        "available_formats": ["audiobook", "physical", "ebook"],
        "rating": "5/5",
    },
]


def seed_database():
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)

    print(f"Seeding Firestore collection '{COLLECTION_NAME}' in project '{PROJECT_ID}'...")
    for book in INITIAL_BOOKS:
        doc_id = book["id"]
        data = {k: v for k, v in book.items() if k != "id"}
        collection_ref.document(doc_id).set(data)
        print(f"  Added document: {doc_id} -> '{book['title']}'")

    print("Firestore seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
