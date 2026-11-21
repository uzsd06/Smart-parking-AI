-- ==========================================
-- SMARTPARK AI DATABASE SCHEMA
-- Member B: Parking Management & Database
-- ==========================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    phone TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. VEHICLES TABLE
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    registration_number TEXT UNIQUE NOT NULL,
    vehicle_type TEXT NOT NULL
        CHECK (vehicle_type IN ('regular', 'EV', 'accessible')),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- 3. PARKING SLOTS TABLE
CREATE TABLE IF NOT EXISTS parking_slots (
    slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    slot_number TEXT UNIQUE NOT NULL,
    slot_type TEXT NOT NULL
        CHECK (slot_type IN ('regular', 'EV', 'accessible')),
    gate TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'available'
        CHECK (status IN ('available', 'blocked', 'maintenance'))
);

-- 4. BOOKINGS TABLE
CREATE TABLE IF NOT EXISTS bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    slot_id INTEGER,

    arrival_time TEXT NOT NULL,
    duration INTEGER NOT NULL CHECK (duration > 0),
    destination_gate TEXT NOT NULL,

    requires_charging INTEGER NOT NULL DEFAULT 0
        CHECK (requires_charging IN (0, 1)),

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN (
            'pending',
            'allocated',
            'checked-in',
            'completed',
            'cancelled'
        )),

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
    FOREIGN KEY (slot_id) REFERENCES parking_slots(slot_id)
);

-- Indexes for faster database queries
CREATE INDEX IF NOT EXISTS idx_bookings_user
ON bookings(user_id);

CREATE INDEX IF NOT EXISTS idx_bookings_slot
ON bookings(slot_id);

CREATE INDEX IF NOT EXISTS idx_bookings_arrival
ON bookings(arrival_time);
