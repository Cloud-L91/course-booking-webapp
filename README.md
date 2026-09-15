# The Cake Is a Lie

Academic project developed for the Web Applications course at Polytechnic University of Turin.

I built **The Cake Is a Lie** as a web application for managing kitchen sessions of a cooking school.
The platform provides an environment where visitors and students can browse culinary offerings, reserve kitchen workstations, rate past experiences, and manage their weekly schedule. Cooking school managers can create new classes, schedule sessions, oversee enrolled students and waiting lists, and monitor administrative analytics.

The user interface is in English and designed primarily for desktop use, while retaining some responsive layouts for mobile devices.

---

## Simulated Time Context

The application operates within a fictional single week from Monday to Sunday, with a fixed reference time set to **Wednesday, 13:00**.  
This temporal reference determines:
- The distinction between upcoming, in-progress, and past sessions.
- The cancellation window: bookings can only be cancelled up to 12 hours prior to the session start time.
- Access to the post-class rating form, unlocked exclusively for attended past sessions.

---

## Demo accounts

The database comes pre-populated with accounts across both roles to allow testing of standard flows, edge cases, schedule overlap detection, and waiting list promotions.

| Role | Email | Password |
|---|---|---|---|
| Manager | `jill.valentine@example.com` | `jill123` |
| Manager | `cave.johnson@aperture.com` | `cave123` |
| Student | `paolo.scavalcacinghie@example.com ` | `paolo123` |
| Student | `tifa.lockhart@example.com` | `tifa123` |
| Student | `barry.burton@example.com` | `barry123` |
| Student | `eric.cartman@example.com` | `cartman123` |
| Student | `ellen.ripley@example.com` | `ripley123` |

---

## Design and implementation choices

For the homepage, I used photo-based cards to immediately display key details (difficulty, duration, and available spots), while reserving the detailed page for ingredients and extended descriptions. For the profiles, I tailored the components: a tabbed interface for students to separate active sessions, waitlists, and past sessions; summary cards for manager statistics; and collapsible accordions to manage course sessions and participants in a compact layout.

The visual palette uses primarily soft cream, warm peach, turquoise, and dark charcoal, styled through customized CSS rules overriding Bootstrap 5 components.

On the backend, Flask handles application routing while database operations are divided across domain-focused DAO modules (`user_dao.py`, `cooking_class_dao.py`, `booking_dao.py`, `utilities_dao.py`).

To prevent race conditions during concurrent requests, seat availability checks and student enrollments are managed within single transactional routines, ensuring a session cannot exceed its configured capacity.

---

## Optional Requirements (Prova Finale)

In accordance with the optional requirements for the Prova Finale, I implemented:

- **FIFO waiting list:** When a class session reaches its maximum seating capacity, students can join its dedicated waiting list. Students can view their numeric position in each list from their profile or leave the queue at any time. Waiting list entries do not count against the 4 active enrollment limit.
- **Automatic promotion on cancellation:** When an enrolled student cancels their reservation, the first student in the waiting queue is automatically promoted to `ENROLLED` status, provided they have not reached their active weekly enrollment limit.
- **Manager analytics dashboard:** Cooking school managers have access to real-time statistics covering total classes, total sessions, total enrollments, total waiting students, the most popular cuisine by enrollments, and the highest-rated class.

---

## Main features

- Public catalog of cooking sessions with seat availability counters and booking badges.
- Session detail views showing chef names, classroom/kitchen, dietary category, full description, and at least 4 ingredients.
- Promotional galleries featuring 3 photos per cooking class.
- Separate registration and role access control for students and managers.
- Overlapping schedule conflict checks preventing simultaneous bookings.
- Cap of at most 4 active class session enrollments per student during the week.
- 12-hour cancellation deadline enforcement relative to the reference time.
- 1 to 5 star rating system for completed sessions with average score aggregation per class.
- Manager portal for creating classes with image uploads, adding sessions, and managing empty sessions.
- Dual-layer validation (HTML5 form attributes and Python server-side string/length verification).
- Password hashing using Werkzeug security utilities (`generate_password_hash` and `check_password_hash`).

---

## Technology

- **Backend:** Python 3, Flask, SQLite3
- **Authentication:** Flask-Login
- **Templating:** Jinja2, semantic HTML5
- **Styling:** Bootstrap 5, Bootstrap Icons, custom modular CSS
- **Scripting:** Vanilla JavaScript for password visibility toggles

Dependencies are listed in [`requirements.txt`](requirements.txt).

---

## Local execution

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
