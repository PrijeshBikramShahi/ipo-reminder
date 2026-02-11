-- IPO Reminder System Database Schema for PostgreSQL
-- This schema is optimized for Render.com deployment

-- Enable UUID extension if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create IPOs table
CREATE TABLE IF NOT EXISTS ipos (
    id SERIAL PRIMARY KEY,
    company VARCHAR(255) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create FCM tokens table
CREATE TABLE IF NOT EXISTS fcm_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(500) UNIQUE NOT NULL,
    device_id VARCHAR(255),
    platform VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Create user preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    fcm_token_id INTEGER NOT NULL REFERENCES fcm_tokens(id) ON DELETE CASCADE,
    notification_days_before INTEGER DEFAULT 1,
    notification_time VARCHAR(10) DEFAULT '08:00',
    notify_on_opening BOOLEAN DEFAULT true,
    notify_day_before BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create notification log table
CREATE TABLE IF NOT EXISTS notification_log (
    id SERIAL PRIMARY KEY,
    ipo_id INTEGER NOT NULL REFERENCES ipos(id) ON DELETE CASCADE,
    fcm_token_id INTEGER NOT NULL REFERENCES fcm_tokens(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_ipos_start_date ON ipos(start_date);
CREATE INDEX IF NOT EXISTS idx_ipos_end_date ON ipos(end_date);
CREATE INDEX IF NOT EXISTS idx_ipos_company ON ipos(company);

CREATE INDEX IF NOT EXISTS idx_fcm_tokens_token ON fcm_tokens(token);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_active ON fcm_tokens(active);
CREATE INDEX IF NOT EXISTS idx_fcm_tokens_platform ON fcm_tokens(platform);

CREATE INDEX IF NOT EXISTS idx_user_preferences_fcm_token_id ON user_preferences(fcm_token_id);
CREATE INDEX IF NOT EXISTS idx_user_preferences_notification_time ON user_preferences(notification_time);

CREATE INDEX IF NOT EXISTS idx_notification_log_sent_at ON notification_log(sent_at);
CREATE INDEX IF NOT EXISTS idx_notification_log_success ON notification_log(success);
CREATE INDEX IF NOT EXISTS idx_notification_log_ipo_id ON notification_log(ipo_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic updated_at updates
DROP TRIGGER IF EXISTS update_ipos_updated_at ON ipos;
CREATE TRIGGER update_ipos_updated_at 
    BEFORE UPDATE ON ipos 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_fcm_tokens_updated_at ON fcm_tokens;
CREATE TRIGGER update_fcm_tokens_updated_at 
    BEFORE UPDATE ON fcm_tokens 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create view for upcoming IPOs
CREATE OR REPLACE VIEW upcoming_ipos_view AS
SELECT 
    id,
    company,
    start_date,
    end_date,
    created_at,
    updated_at,
    EXTRACT(DAY FROM start_date - CURRENT_TIMESTAMP) as days_until_opening,
    CASE 
        WHEN start_date > CURRENT_TIMESTAMP THEN 'upcoming'
        WHEN end_date >= CURRENT_TIMESTAMP THEN 'open'
        ELSE 'closed'
    END as status
FROM ipos
WHERE start_date >= CURRENT_TIMESTAMP OR end_date >= CURRENT_TIMESTAMP
ORDER BY start_date ASC;

-- Create function to get database statistics
CREATE OR REPLACE FUNCTION get_database_stats()
RETURNS TABLE(
    total_ipos INTEGER,
    active_tokens INTEGER,
    total_tokens INTEGER,
    notifications_today INTEGER,
    upcoming_ipos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM ipos)::INTEGER as total_ipos,
        (SELECT COUNT(*) FROM fcm_tokens WHERE active = true)::INTEGER as active_tokens,
        (SELECT COUNT(*) FROM fcm_tokens)::INTEGER as total_tokens,
        (SELECT COUNT(*) FROM notification_log WHERE DATE(sent_at) = CURRENT_DATE AND success = true)::INTEGER as notifications_today,
        (SELECT COUNT(*) FROM ipos WHERE start_date >= CURRENT_TIMESTAMP)::INTEGER as upcoming_ipos;
END;
$$ LANGUAGE plpgsql;

-- Insert sample data for testing (optional)
-- INSERT INTO ipos (company, start_date, end_date) VALUES 
-- ('Test Company 1', CURRENT_TIMESTAMP + INTERVAL '7 days', CURRENT_TIMESTAMP + INTERVAL '14 days'),
-- ('Test Company 2', CURRENT_TIMESTAMP + INTERVAL '14 days', CURRENT_TIMESTAMP + INTERVAL '21 days');

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;