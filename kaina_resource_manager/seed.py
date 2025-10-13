from datetime import datetime, timedelta, timezone
from app import app
from models import db, User, Resource, Booking, Maintenance, UserRole, ResourceType, BookingStatus

def seed_database():
    with app.app_context():
        print("--- Starting database seeding for Kaina ---")
        db.drop_all()
        db.create_all()

        u1 = User(name="Kaina Admin", email="admin@kaina.io", role=UserRole.ADMIN)
        u2 = User(name="Dr. Aris Thorne", email="aris.t@kaina.io", role=UserRole.FACULTY)
        u3 = User(name="Lena Soto", email="lena.s@kaina.io", role=UserRole.STUDENT)
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        r1 = Resource(name="Photon Lab Alpha", description="Advanced optics and laser research lab.", resource_type=ResourceType.ROOM, location="Helios Tower, Floor 3", capacity=8, usage_notes="Laser safety certification required.")
        r2 = Resource(name="Meeting Room 'Orion'", description="Conference room with video conferencing.", resource_type=ResourceType.ROOM, location="Starlight Building, Floor 2", capacity=12)
        r3 = Resource(name="Quantum Annealer 'Leap'", description="D-Wave quantum computing system for optimization problems.", resource_type=ResourceType.EQUIPMENT, location="Cryo-Lab 1", model_number="Advantage 5.1", max_booking_duration_hours=4)
        r4 = Resource(name="Electron Microscope 'Zeus'", description="High-resolution SEM for material analysis.", resource_type=ResourceType.EQUIPMENT, location="Materials Science Wing", model_number="FEI Quanta 3D")
        db.session.add_all([r1, r2, r3, r4])
        db.session.commit()

        now = datetime.now(timezone.utc)
        b1 = Booking(user_id=u2.id, resource_id=r1.id, status=BookingStatus.APPROVED, purpose="Holographic data storage experiment", start_time=now - timedelta(days=2, hours=4), end_time=now - timedelta(days=2))
        b2 = Booking(user_id=u3.id, resource_id=r4.id, status=BookingStatus.APPROVED, purpose="Analyze nano-composite samples", start_time=now - timedelta(hours=2), end_time=now + timedelta(hours=1))
        b3 = Booking(user_id=u2.id, resource_id=r3.id, status=BookingStatus.PENDING, purpose="Protein folding simulation", start_time=now + timedelta(days=1, hours=9), end_time=now + timedelta(days=1, hours=13))
        b4 = Booking(user_id=u3.id, resource_id=r2.id, status=BookingStatus.PENDING, purpose="Thesis defense practice session", start_time=now + timedelta(days=4, hours=14), end_time=now + timedelta(days=4, hours=16))
        m1 = Maintenance(resource_id=r4.id, reason="Scheduled vacuum pump replacement.", start_time=now - timedelta(days=1), end_time=now + timedelta(days=1))
        m2 = Maintenance(resource_id=r3.id, reason="Cryogenic system calibration.", start_time=now + timedelta(days=8), end_time=now + timedelta(days=9))
        db.session.add_all([b1, b2, b3, b4, m1, m2])
        db.session.commit()

        print("✅ Kaina database seeded successfully!")

if __name__ == '__main__':
    seed_database()
