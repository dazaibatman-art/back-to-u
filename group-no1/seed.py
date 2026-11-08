"""
Database seed script for Group No1 Global Lost & Found Management System.
Inserts clearly labelled, realistic demonstration users, sample items across all categories,
verified claims, in-app messages, and notifications idempotently (no duplicate creation on re-runs).
"""

from datetime import date, timedelta
from app import create_app
from app.extensions import db
from app.models import User, Item, Claim, Message, Notification, utc_now


def seed_database():
    app = create_app("development")

    with app.app_context():
        print("-> Ensuring database tables exist...")
        db.create_all()

        print("-> Seeding demonstration users...")
        users_data = [
            {
                "full_name": "Demo Member",
                "email": "demo@example.com",
                "phone": "+1 (555) 234-5678",
                "password": "Password123!",
                "role": "user"
            },
            {
                "full_name": "Jane Smith (Finder)",
                "email": "jane@example.com",
                "phone": "+1 (555) 345-6789",
                "password": "Password123!",
                "role": "user"
            },
            {
                "full_name": "Alex Johnson (Claimant)",
                "email": "alex@example.com",
                "phone": "+1 (555) 456-7890",
                "password": "Password123!",
                "role": "user"
            },
            {
                "full_name": "Platform Administrator",
                "email": "admin@example.com",
                "phone": "+1 (555) 000-1111",
                "password": "AdminPassword123!",
                "role": "admin"
            }
        ]

        user_objects = {}
        for u in users_data:
            existing = User.query.filter_by(email=u["email"]).first()
            if not existing:
                user = User(
                    full_name=u["full_name"],
                    email=u["email"],
                    phone=u["phone"],
                    role=u["role"]
                )
                user.set_password(u["password"])
                db.session.add(user)
                db.session.flush()
                user_objects[u["email"]] = user
                print(f"   Created user: {u['email']}")
            else:
                user_objects[u["email"]] = existing

        db.session.commit()

        print("-> Seeding sample lost & found items across categories...")
        today = date.today()

        # Seed items preserving the original 3 from Index.html plus other realistic categories
        items_data = [
            {
                "name": "Black Leather Wallet",
                "category": "accessories",
                "public_description": "Black bi-fold leather wallet found near Central Park fountain bench. Good condition.",
                "private_verification_details": "Contains a library card ending in 4492, $35 cash, and a silver transit token.",
                "location_found": "Central Park, New York, NY",
                "date_found": today - timedelta(days=2),
                "status": "active",
                "finder_email": "jane@example.com"
            },
            {
                "name": "iPhone 13 Pro",
                "category": "electronics",
                "public_description": "Sierra Blue iPhone 13 Pro with clear bumper case and small crack on screen protector.",
                "private_verification_details": "Lockscreen photo is a Golden Retriever dog; serial number starts with F2LZ9.",
                "location_found": "Grand Central Terminal, New York, NY",
                "date_found": today - timedelta(days=3),
                "status": "pending_claim",
                "finder_email": "jane@example.com"
            },
            {
                "name": "House Keys with Red Carabiner",
                "category": "accessories",
                "public_description": "Set of four silver keys with a red aluminum carabiner and miniature brass bicycle keychain.",
                "private_verification_details": "One key has a blue rubber cap labeled 'FRONT'; stamped with number 204.",
                "location_found": "Chicago Public Library, Chicago, IL",
                "date_found": today - timedelta(days=4),
                "status": "active",
                "finder_email": "demo@example.com"
            },
            {
                "name": "Blue Passport and Travel Wallet",
                "category": "documents",
                "public_description": "Navy passport holder containing international travel paperwork, found near security line.",
                "private_verification_details": "Passport issued in 2021; contains boarding pass stub for flight DL442.",
                "location_found": "O'Hare Airport Terminal 2, Chicago, IL",
                "date_found": today - timedelta(days=5),
                "status": "active",
                "finder_email": "demo@example.com"
            },
            {
                "name": "Black North Face Backpack",
                "category": "bags",
                "public_description": "Black Borealis backpack left in the quiet study room of University Hall.",
                "private_verification_details": "Contains spiral notebook with chemistry formulas and a purple stainless steel water bottle.",
                "location_found": "University Campus Hall B, Boston, MA",
                "date_found": today - timedelta(days=1),
                "status": "active",
                "finder_email": "jane@example.com"
            },
            {
                "name": "Silver Chain Necklace with Pendant",
                "category": "jewelry",
                "public_description": "Fine silver chain necklace with a circular tree-of-life engraved pendant.",
                "private_verification_details": "Engraved with initials 'M.K. 2018' on the back of the circular pendant.",
                "location_found": "Riverwalk Cafe, Austin, TX",
                "date_found": today - timedelta(days=6),
                "status": "claimed",
                "finder_email": "demo@example.com"
            },
            {
                "name": "Ray-Ban Aviator Sunglasses in Case",
                "category": "other",
                "public_description": "Classic gold frame aviator sunglasses in a brown leather snap case.",
                "private_verification_details": "Microfiber cleaning cloth inside is green; left arm has tiny scratch near hinge.",
                "location_found": "Santa Monica Pier, Los Angeles, CA",
                "date_found": today - timedelta(days=7),
                "status": "returned",
                "finder_email": "demo@example.com"
            }
        ]

        item_objects = {}
        for it in items_data:
            existing = Item.query.filter_by(name=it["name"]).first()
            if not existing:
                finder = user_objects.get(it["finder_email"])
                item = Item(
                    name=it["name"],
                    category=it["category"],
                    public_description=it["public_description"],
                    private_verification_details=it["private_verification_details"],
                    location_found=it["location_found"],
                    date_found=it["date_found"],
                    status=it["status"],
                    moderation_status="approved",
                    finder_id=finder.id if finder else None,
                    finder_display_name=finder.full_name if finder else "Anonymous"
                )
                db.session.add(item)
                db.session.flush()
                item_objects[it["name"]] = item
                print(f"   Created item: {it['name']} [{it['category']}]")
            else:
                item_objects[it["name"]] = existing

        db.session.commit()

        print("-> Seeding sample claims, messages, and notifications...")
        phone_item = item_objects.get("iPhone 13 Pro")
        claimant = user_objects.get("alex@example.com")
        finder = user_objects.get("jane@example.com")

        if phone_item and claimant and finder:
            existing_claim = Claim.query.filter_by(item_id=phone_item.id, claimant_id=claimant.id).first()
            if not existing_claim:
                claim = Claim(
                    item_id=phone_item.id,
                    claimant_id=claimant.id,
                    claim_message="I dropped my phone while boarding the 5:45 PM express train at Grand Central. I can unlock it in person.",
                    evidence_details="Lockscreen is my Golden Retriever 'Barnaby'. The phone's IMEI ends in 9102. Phone number is linked to my SIM card.",
                    status="Under Review"
                )
                db.session.add(claim)
                db.session.flush()

                # Add sample in-app messages
                msg1 = Message(
                    claim_id=claim.id,
                    sender_id=claimant.id,
                    recipient_id=finder.id,
                    content="Hello! Thank you so much for reporting my iPhone. I can meet you at Grand Central Station security booth."
                )
                msg2 = Message(
                    claim_id=claim.id,
                    sender_id=finder.id,
                    recipient_id=claimant.id,
                    content="Hi Alex! Yes, the lockscreen picture matches your description perfectly. Let's coordinate a safe handoff tomorrow afternoon."
                )
                db.session.add_all([msg1, msg2])

                # Add sample notification
                notif = Notification(
                    recipient_id=finder.id,
                    related_item_id=phone_item.id,
                    related_claim_id=claim.id,
                    notification_type="claim_received",
                    title="New Claim on iPhone 13 Pro",
                    message="Alex Johnson submitted an ownership claim for review."
                )
                db.session.add(notif)
                print("   Created sample claim & safe chat on iPhone 13 Pro")

        # Add a completed claim for Ray-Ban Sunglasses to demonstrate completed status & trust score
        glasses_item = item_objects.get("Ray-Ban Aviator Sunglasses in Case")
        demo_user = user_objects.get("demo@example.com")
        if glasses_item and claimant and demo_user:
            existing_sunglasses_claim = Claim.query.filter_by(item_id=glasses_item.id, claimant_id=claimant.id).first()
            if not existing_sunglasses_claim:
                comp_claim = Claim(
                    item_id=glasses_item.id,
                    claimant_id=claimant.id,
                    claim_message="Left my Ray-Ban sunglasses on the picnic table at Santa Monica Pier.",
                    evidence_details="Brown leather snap case with green microfiber cloth inside.",
                    status="Completed",
                    reviewer_id=demo_user.id,
                    review_notes="Verified in person at Visitor Center. Item successfully returned.",
                    reviewed_at=utc_now(),
                    completed_at=utc_now()
                )
                db.session.add(comp_claim)
                print("   Created completed return sample record")

        db.session.commit()
        print("\n=== Database Seeding Complete! ===")
        print("Demo Credentials for Testing:")
        print("  - Standard User: demo@example.com / Password123!")
        print("  - Finder User:   jane@example.com / Password123!")
        print("  - Claimant User: alex@example.com / Password123!")
        print("  - Admin User:    admin@example.com / AdminPassword123!\n")


if __name__ == "__main__":
    seed_database()
