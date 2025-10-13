import os
from datetime import datetime, timezone
from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import select, func, or_
from models import db, User, Resource, Booking, Maintenance, ResourceType, BookingStatus

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secure-default-kaina-key')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'instance', 'kaina.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def check_conflict(resource_id, start_time, end_time, booking_id_to_exclude=None):
    booking_query = select(Booking).where(
        Booking.resource_id == resource_id,
        Booking.status == BookingStatus.APPROVED,
        Booking.start_time < end_time,
        Booking.end_time > start_time
    )
    if booking_id_to_exclude:
        booking_query = booking_query.where(Booking.id != booking_id_to_exclude)
    if db.session.execute(booking_query).scalars().first():
        return True, "Time slot conflicts with an approved booking."
    maintenance_query = select(Maintenance).where(
        Maintenance.resource_id == resource_id,
        Maintenance.start_time < end_time,
        Maintenance.end_time > start_time
    )
    if db.session.execute(maintenance_query).scalars().first():
        return True, "Resource is scheduled for maintenance during this time."
    return False, ""

def get_resource_status(resource):
    now = datetime.now(timezone.utc)
    if db.session.execute(select(Maintenance).where(Maintenance.resource_id == resource.id, Maintenance.start_time <= now, Maintenance.end_time >= now)).scalars().first():
        return "Maintenance", "danger"
    if db.session.execute(select(Booking).where(Booking.resource_id == resource.id, Booking.status == BookingStatus.APPROVED, Booking.start_time <= now, Booking.end_time >= now)).scalars().first():
        return "In Use", "warning"
    return "Available", "success"

@app.route('/')
def dashboard():
    """Shows the main dashboard with search, sort, and filter."""
    # Get parameters from URL query string
    search_query = request.args.get('q', '')
    type_filter = request.args.get('type', '')
    sort_param = request.args.get('sort', 'name_asc')

    # Start with a base query
    query = select(Resource)

    # Apply search filter if a query is provided
    if search_query:
        search_term = f"%{search_query}%"
        query = query.where(
            or_(
                Resource.name.ilike(search_term),
                Resource.description.ilike(search_term),
                Resource.location.ilike(search_term)
            )
        )

    # Apply type filter
    if type_filter and type_filter in [e.name for e in ResourceType]:
        query = query.where(Resource.resource_type == ResourceType[type_filter])

    # Apply sorting
    if sort_param == 'name_desc':
        query = query.order_by(Resource.name.desc())
    elif sort_param == 'date_asc':
        query = query.order_by(Resource.created_at.asc())
    elif sort_param == 'date_desc':
        query = query.order_by(Resource.created_at.desc())
    else: # Default sort
        query = query.order_by(Resource.name.asc())

    resources = db.session.execute(query).scalars().all()
    resource_data = [(res, *get_resource_status(res)) for res in resources]

    return render_template('dashboard.html',
                           resource_data=resource_data,
                           ResourceType=ResourceType,
                           current_filter=type_filter,
                           search_query=search_query,
                           sort_param=sort_param,
                           title="Resource Dashboard")

@app.route('/resource/<int:resource_id>')
def resource_detail(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    now = datetime.now(timezone.utc)
    upcoming_bookings = db.session.execute(select(Booking).where(Booking.resource_id == resource_id, Booking.status == BookingStatus.APPROVED, Booking.end_time >= now).order_by(Booking.start_time)).scalars().all()
    upcoming_maintenances = db.session.execute(select(Maintenance).where(Maintenance.resource_id == resource_id, Maintenance.end_time >= now).order_by(Maintenance.start_time)).scalars().all()
    current_user = db.session.get(User, 2) or db.session.execute(select(User).limit(1)).scalar_one()
    return render_template('resource_detail.html', resource=resource, bookings=upcoming_bookings, maintenances=upcoming_maintenances, current_user=current_user, title=resource.name)

@app.route('/book/<int:resource_id>', methods=['POST'])
def create_booking(resource_id):
    resource = db.get_or_404(Resource, resource_id)
    try:
        start_time = datetime.fromisoformat(request.form.get('start_time')).astimezone(timezone.utc)
        end_time = datetime.fromisoformat(request.form.get('end_time')).astimezone(timezone.utc)
        purpose = request.form.get('purpose')
        user_id = request.form.get('user_id')
    except (ValueError, TypeError):
        flash("Invalid date format provided.", 'danger')
        return redirect(url_for('resource_detail', resource_id=resource_id))

    if not all([start_time, end_time, purpose, user_id]):
        flash("All fields are required.", 'danger')
        return redirect(url_for('resource_detail', resource_id=resource_id))

    if end_time <= start_time:
        flash("End time must be after start time.", 'danger')
        return redirect(url_for('resource_detail', resource_id=resource_id))

    if resource.max_booking_duration_hours and (end_time - start_time).total_seconds() / 3600 > resource.max_booking_duration_hours:
        flash(f"Booking exceeds max duration of {resource.max_booking_duration_hours} hours.", 'danger')
        return redirect(url_for('resource_detail', resource_id=resource_id))

    is_conflict, reason = check_conflict(resource_id, start_time, end_time)
    if is_conflict:
        flash(f"Booking failed. {reason}", 'danger')
        return redirect(url_for('resource_detail', resource_id=resource_id))

    new_booking = Booking(resource_id=resource_id, user_id=user_id, purpose=purpose, start_time=start_time, end_time=end_time, status=BookingStatus.PENDING)
    db.session.add(new_booking)
    db.session.commit()
    flash('Booking request submitted and is pending approval.', 'success')
    return redirect(url_for('resource_detail', resource_id=resource_id))

@app.route('/admin')
def admin_dashboard(): return redirect(url_for('admin_manage_bookings'))

@app.route('/admin/bookings')
def admin_manage_bookings():
    pending_bookings = db.session.execute(select(Booking).where(Booking.status == BookingStatus.PENDING).order_by(Booking.start_time)).scalars().all()
    other_bookings = db.session.execute(select(Booking).where(Booking.status != BookingStatus.PENDING).order_by(Booking.created_at.desc()).limit(10)).scalars().all()
    return render_template('admin/manage_bookings.html', pending_bookings=pending_bookings, other_bookings=other_bookings, title="Manage Bookings")

@app.route('/admin/booking/<int:booking_id>/approve', methods=['POST'])
def admin_approve_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    is_conflict, reason = check_conflict(booking.resource_id, booking.start_time, booking.end_time, booking_id_to_exclude=booking.id)
    if is_conflict:
        booking.status = BookingStatus.REJECTED
        flash(f'Booking auto-rejected due to a conflict: {reason}', 'danger')
    else:
        booking.status = BookingStatus.APPROVED
        flash('Booking approved successfully.', 'success')
    db.session.commit()
    return redirect(url_for('admin_manage_bookings'))

@app.route('/admin/booking/<int:booking_id>/reject', methods=['POST'])
def admin_reject_booking(booking_id):
    booking = db.get_or_404(Booking, booking_id)
    booking.status = BookingStatus.REJECTED
    db.session.commit()
    flash('Booking rejected.', 'info')
    return redirect(url_for('admin_manage_bookings'))

@app.route('/admin/resources')
def admin_manage_resources():
    resources = db.session.execute(select(Resource).order_by(Resource.name)).scalars().all()
    return render_template('admin/manage_resources.html', resources=resources, title="Manage Resources")

@app.route('/reports')
def reports():
    try:
        usage_report_data = db.session.execute(
            select(Resource.name, Resource.resource_type, func.sum((func.julianday(Booking.end_time) - func.julianday(Booking.start_time)) * 24).label('total_hours'))
            .join(Booking, Resource.id == Booking.resource_id).where(Booking.status == BookingStatus.APPROVED)
            .group_by(Resource.id).order_by(func.collate(func.sum((func.julianday(Booking.end_time) - func.julianday(Booking.start_time)) * 24), 'NOCASE').desc())
        ).all()
    except Exception:
        usage_report_data = []
        flash("Could not generate report. Database may not support required date functions.", "warning")
    return render_template('reports.html', report_data=usage_report_data, title="Usage Reports")

@app.context_processor
def inject_utility(): return dict(datetime=datetime, timezone=timezone, BookingStatus=BookingStatus, request=request)

@app.template_filter('datetimeformat')
def format_datetime(value, format='%Y-%m-%d %H:%M'): return value.astimezone().strftime(format) if value else ""

if __name__ == '__main__': app.run(debug=True, port=5001)
