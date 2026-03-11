from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User, Role, RecyclingCenter, Resource, ResourceType, Announcement

app = create_app()

with app.app_context():
    print("🌱 Seeding WasteWise database...")

    if not User.query.filter_by(email="admin@wastewise.ng").first():
        admin = User(
            name="Super Admin", email="admin@wastewise.ng",
            password=generate_password_hash("Admin1234!"),
            role=Role.SUPER_ADMIN, lga="Ikeja", state="Lagos",
        )
        db.session.add(admin)
        db.session.flush()

        db.session.add(User(
            name="Ikeja LGA Admin", email="community@wastewise.ng",
            password=generate_password_hash("Admin1234!"),
            role=Role.COMMUNITY_ADMIN, admin_lga="Ikeja", lga="Ikeja", state="Lagos",
        ))
        db.session.add(User(
            name="Green Collector", email="collector@wastewise.ng",
            password=generate_password_hash("Collect1234!"),
            role=Role.COLLECTOR, phone="08012345678",
            lga="Ikeja", state="Lagos", service_radius=5.0,
            service_area="Ikeja, Maryland, Alausa",
            accepted_waste_types="PLASTIC,PAPER,GLASS,METAL", is_available=True,
        ))
        db.session.add(User(
            name="Jane Household", email="household@wastewise.ng",
            password=generate_password_hash("House1234!"),
            role=Role.HOUSEHOLD, phone="08087654321",
            address="12 Allen Avenue, Ikeja",
            latitude=6.6018, longitude=3.3515,
            lga="Ikeja", state="Lagos",
        ))
        db.session.add(RecyclingCenter(
            name="EcoGreen Recycling Hub",
            address="45 Obafemi Awolowo Way, Ikeja",
            latitude=6.5958, longitude=3.3422,
            lga="Ikeja", state="Lagos", phone="08011111111",
            opening_hours="Mon-Sat: 8am - 5pm",
            accepted_materials="PLASTIC,PAPER,GLASS,METAL",
            is_verified=True, is_active=True,
        ))
        db.session.add(RecyclingCenter(
            name="Lagos E-Waste Center",
            address="3 Broad Street, Lagos Island",
            latitude=6.4541, longitude=3.3947,
            lga="Lagos Island", state="Lagos", phone="08022222222",
            opening_hours="Mon-Fri: 9am - 4pm",
            accepted_materials="E_WASTE,METAL",
            is_verified=True, is_active=True,
        ))
        db.session.add(Resource(
            title="How to Segregate Your Waste at Home",
            summary="Learn the basics of separating recyclables from general waste.",
            content="Waste segregation is the process of separating different types of waste at the source...",
            type=ResourceType.ARTICLE, tags="beginner,household,recycling", is_published=True,
        ))
        db.session.add(Resource(
            title="Understanding E-Waste and Its Dangers",
            summary="Why electronic waste needs special handling.",
            content="Electronic waste contains hazardous materials like lead and mercury...",
            type=ResourceType.ARTICLE, tags="e-waste,health,environment", is_published=True,
        ))
        db.session.add(Announcement(
            title="Welcome to WasteWise Nigeria!",
            body="Together we can build cleaner, healthier communities.",
            lga=None, author_id=admin.id,
        ))

        db.session.commit()
        print("✅ Done!")
        print("  admin@wastewise.ng      / Admin1234!")
        print("  community@wastewise.ng  / Admin1234!")
        print("  collector@wastewise.ng  / Collect1234!")
        print("  household@wastewise.ng  / House1234!")
    else:
        print("ℹ️  Already seeded.")