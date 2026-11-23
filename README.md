# 🚗 SmartPark AI – Intelligent Parking Management System

### Smart Parking. Smarter City.

SmartPark AI is an intelligent parking management system that optimises parking slot allocation using the **Hill Climbing Search Algorithm**. It considers vehicle compatibility, parking availability, booking time conflicts and distance from the destination gate to provide efficient parking allocation.

The application provides a user-friendly interface for booking and managing parking slots, along with an admin dashboard for monitoring parking utilisation and analysing booking trends.

## 🎯 1. Problem Statement

Traditional parking systems often rely on manual allocation or first-come-first-served approaches, resulting in inefficient space utilisation, unnecessary searching time, booking conflicts and inconvenience for users.

SmartPark AI addresses these challenges through intelligent parking allocation, automated booking management, real-time availability checking and parking visualisation.

## 💡 2. Key Features

- **User Registration & Login:** Users can create accounts and access the application.
- **Vehicle Management:** Register and manage Regular, EV and Accessible vehicles.
- **Smart Parking Booking:** Book slots based on arrival time, parking duration and destination gate.
- **AI-Based Slot Allocation:** Uses Hill Climbing to identify suitable parking slots.
- **EV Charging Support:** Considers EV charging requirements during allocation.
- **Booking Management:** View upcoming bookings and cancel reservations.
- **Automatic Re-allocation:** Reallocates parking slots when bookings are cancelled or allocation conditions change.
- **Notifications:** Generates notifications when parking slot assignments change.
- **Admin Dashboard:** Monitor parking slots, users and bookings.
- **Parking Visualisation:** View parking occupancy and slot availability.
- **Analytics:** Analyse parking utilisation, booking trends and peak hours.
- **Algorithm Comparison:** Compare Hill Climbing with Random and First-Available allocation approaches.

## 🧠 3. AI Algorithm – Hill Climbing Search

SmartPark AI uses the **Hill Climbing Search Algorithm**, a heuristic local search technique, to optimise parking slot allocation.

The algorithm evaluates possible parking assignments using a fitness function that considers:

1. Vehicle-slot compatibility.
2. Parking slot availability.
3. Arrival time and parking duration.
4. Booking conflicts with existing reservations.
5. Distance from the selected destination gate.
6. EV charging and accessibility requirements.

The algorithm searches for an allocation with a higher fitness score and selects a suitable parking slot while maintaining valid booking constraints.

### Algorithm Comparison

The system also compares Hill Climbing allocation against:

- Random Allocation
- First-Available Allocation

This helps evaluate the effectiveness of intelligent parking allocation.

## 📂 4. Project Structure

```text
SmartPark-AI/
│
├── backend/               # Backend operations
├── database/              # Database management
├── pages/                 # Streamlit application pages
├── services/              # Supporting services
├── assets/                # Images and visual assets
├── .streamlit/            # Streamlit configuration
│
├── Home.py                # Main application entry point
├── main.py                # Application module
├── ui.py                  # UI components
├── hill_climbing.py       # Hill Climbing algorithm
├── availability.py        # Parking availability
├── integration.py         # Backend and algorithm integration
├── reallocation.py        # Parking slot reallocation
├── parking_data.py        # Parking data handling
├── seed_demo.py           # Demo data setup
├── requirements.txt       # Project dependencies
└── README.md
```

## 🔄 5. Application Workflow

The application follows a six-step workflow:

1. **User Registration & Login:** Users create accounts and register their vehicles.
2. **Parking Booking:** Users enter arrival time, parking duration, destination gate and EV charging preferences.
3. **AI-Based Parking Allocation:** Hill Climbing evaluates available slots and selects a suitable allocation.
4. **Booking Confirmation & Management:** Booking details are saved, and users can view or cancel reservations.
5. **Notifications & Re-allocation:** The system handles slot reallocation and generates notifications when assignments change.
6. **Admin Dashboard & Analytics:** Administrators monitor parking occupancy, bookings, users and allocation performance.

## 🖥️ 6. Development Environment

- **Operating System:** Windows
- **Programming Environment:** Python 3
- **Virtual Environment:** Python `.venv`
- **IDE:** Visual Studio Code
- **Version Control:** Git and GitHub
- **Deployment Platform:** Streamlit Community Cloud

## 👥 7. Team Contributions

| **Tushita (Member 1)** | Hill Climbing Search Algorithm, fitness function design, parking slot allocation, vehicle-slot compatibility, gate-distance optimisation, availability checking, booking cancellation and waiting-list management with automatic reallocation. |
| **Vidhi (Member 2)** | Backend development, SQLite database design and initialization, user registration and login, vehicle management, parking booking and cancellation, booking conflict detection, availability checking and integration of backend modules with the AI allocation algorithm. |
| **Uzma (Member 3)** | Streamlit frontend development, application pages, user interface, admin dashboard, parking map visualisation, data analytics, charts, notifications interface and application deployment. |
