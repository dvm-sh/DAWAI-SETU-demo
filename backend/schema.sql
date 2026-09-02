-- DAWAI-SETU Enterprise Database Schema
-- Compatible with PostgreSQL 14+

CREATE TYPE user_role AS ENUM ('donor', 'recipient', 'disposal_partner', 'admin');
CREATE TYPE verification_status AS ENUM ('pending', 'verified', 'rejected', 'suspended');
CREATE TYPE medicine_status AS ENUM (
    'available', 'near_expiry', 'high_surplus_risk', 
    'reserved', 'in_transfer', 'redistributed', 
    'expired', 'disposal_pending', 'disposed'
);
CREATE TYPE transfer_status AS ENUM ('pending', 'accepted', 'scheduled', 'collected', 'verified', 'completed');
CREATE TYPE emergency_urgency AS ENUM ('low', 'medium', 'high', 'critical');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    org_name VARCHAR(255) NOT NULL,
    org_type VARCHAR(100) NOT NULL,
    license_number VARCHAR(100) UNIQUE NOT NULL,
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    status verification_status DEFAULT 'pending',
    verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medicines (
    id SERIAL PRIMARY KEY,
    donor_id INT REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    quantity INT NOT NULL CHECK (quantity >= 0),
    expiry_date DATE NOT NULL,
    storage_condition VARCHAR(100) NOT NULL,
    status medicine_status DEFAULT 'available',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE medicine_requirements (
    id SERIAL PRIMARY KEY,
    recipient_id INT REFERENCES organizations(id) ON DELETE CASCADE,
    medicine_name VARCHAR(255) NOT NULL,
    quantity_required INT NOT NULL,
    urgency emergency_urgency DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    medicine_id INT REFERENCES medicines(id) ON DELETE CASCADE,
    requirement_id INT REFERENCES medicine_requirements(id) ON DELETE CASCADE,
    match_score DECIMAL(5, 2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE transfers (
    id SERIAL PRIMARY KEY,
    transfer_code VARCHAR(50) UNIQUE NOT NULL,
    medicine_id INT REFERENCES medicines(id) ON DELETE CASCADE,
    donor_id INT REFERENCES organizations(id),
    recipient_id INT REFERENCES organizations(id),
    quantity INT NOT NULL,
    status transfer_status DEFAULT 'pending',
    initiated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE transfer_events (
    id SERIAL PRIMARY KEY,
    transfer_id INT REFERENCES transfers(id) ON DELETE CASCADE,
    status transfer_status NOT NULL,
    location VARCHAR(255),
    notes TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE disposal_requests (
    id SERIAL PRIMARY KEY,
    medicine_id INT REFERENCES medicines(id) ON DELETE CASCADE,
    donor_id INT REFERENCES organizations(id),
    disposal_partner_id INT REFERENCES organizations(id),
    quantity INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    proof_document_url VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE emergency_requests (
    id SERIAL PRIMARY KEY,
    recipient_id INT REFERENCES organizations(id) ON DELETE CASCADE,
    medicine_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    urgency emergency_urgency NOT NULL,
    reason TEXT NOT NULL,
    required_by TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    action VARCHAR(255) NOT NULL,
    entity_affected VARCHAR(100) NOT NULL,
    entity_id INT NOT NULL,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ml_predictions (
    id SERIAL PRIMARY KEY,
    medicine_id INT REFERENCES medicines(id) ON DELETE CASCADE,
    predicted_demand INT NOT NULL,
    predicted_surplus INT NOT NULL,
    expiry_risk_score DECIMAL(5, 2) NOT NULL,
    recommendation VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for optimized querying
CREATE INDEX idx_medicines_donor ON medicines(donor_id);
CREATE INDEX idx_medicines_expiry ON medicines(expiry_date);
CREATE INDEX idx_transfers_status ON transfers(status);
CREATE INDEX idx_audit_user ON audit_logs(user_id);