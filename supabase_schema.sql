-- =============================================================================
-- Lynex - Supabase Database Schema (Fixed Order)
-- =============================================================================
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/_/sql
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Users Table (extends Supabase auth.users)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Projects Table (without RLS policies yet)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Project Members Table (create this BEFORE adding policies)
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.project_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(project_id, user_id)
);

-- =============================================================================
-- API Keys Table
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES public.projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL CHECK (environment IN ('test', 'live')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);

-- =============================================================================
-- NOW Enable Row Level Security and Add Policies
-- =============================================================================

-- Users Table RLS
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own data" ON public.users;
CREATE POLICY "Users can read own data" ON public.users
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own data" ON public.users;
CREATE POLICY "Users can update own data" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Projects Table RLS
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own projects" ON public.projects;
CREATE POLICY "Users can read own projects" ON public.projects
    FOR SELECT USING (
        owner_id = auth.uid() OR
        EXISTS (
            SELECT 1 FROM public.project_members
            WHERE project_id = id AND user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS "Users can create projects" ON public.projects;
CREATE POLICY "Users can create projects" ON public.projects
    FOR INSERT WITH CHECK (owner_id = auth.uid());

DROP POLICY IF EXISTS "Owners can update projects" ON public.projects;
CREATE POLICY "Owners can update projects" ON public.projects
    FOR UPDATE USING (owner_id = auth.uid());

DROP POLICY IF EXISTS "Owners can delete projects" ON public.projects;
CREATE POLICY "Owners can delete projects" ON public.projects
    FOR DELETE USING (owner_id = auth.uid());

-- Project Members Table RLS
ALTER TABLE public.project_members ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read project members" ON public.project_members;
CREATE POLICY "Users can read project members" ON public.project_members
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.projects
            WHERE id = project_id AND (
                owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = id AND pm.user_id = auth.uid()
                )
            )
        )
    );

DROP POLICY IF EXISTS "Owners and admins can add members" ON public.project_members;
CREATE POLICY "Owners and admins can add members" ON public.project_members
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = p.id 
                    AND pm.user_id = auth.uid() 
                    AND pm.role IN ('owner', 'admin')
                )
            )
        )
    );

DROP POLICY IF EXISTS "Owners and admins can update members" ON public.project_members;
CREATE POLICY "Owners and admins can update members" ON public.project_members
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = p.id 
                    AND pm.user_id = auth.uid() 
                    AND pm.role IN ('owner', 'admin')
                )
            )
        )
    );

DROP POLICY IF EXISTS "Owners and admins can remove members" ON public.project_members;
CREATE POLICY "Owners and admins can remove members" ON public.project_members
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = p.id 
                    AND pm.user_id = auth.uid() 
                    AND pm.role IN ('owner', 'admin')
                )
            )
        )
    );

-- API Keys Table RLS
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read project API keys" ON public.api_keys;
CREATE POLICY "Users can read project API keys" ON public.api_keys
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = p.id AND pm.user_id = auth.uid()
                )
            )
        )
    );

DROP POLICY IF EXISTS "Owners and admins can create API keys" ON public.api_keys;
CREATE POLICY "Owners and admins can create API keys" ON public.api_keys
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = p.id 
                    AND pm.user_id = auth.uid() 
                    AND pm.role IN ('owner', 'admin')
                )
            )
        )
    );

DROP POLICY IF EXISTS "Owners and admins can delete API keys" ON public.api_keys;
CREATE POLICY "Owners and admins can delete API keys" ON public.api_keys
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.projects p
            WHERE p.id = project_id AND (
                p.owner_id = auth.uid() OR
                EXISTS (
                    SELECT 1 FROM public.project_members pm
                    WHERE pm.project_id = p.id 
                    AND pm.user_id = auth.uid() 
                    AND pm.role IN ('owner', 'admin')
                )
            )
        )
    );

-- =============================================================================
-- Functions and Triggers
-- =============================================================================

-- Function to automatically create user profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create user profile on signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for projects updated_at
DROP TRIGGER IF EXISTS update_projects_updated_at ON public.projects;
CREATE TRIGGER update_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Trigger for users updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- =============================================================================
-- Indexes for Performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_projects_owner_id ON public.projects(owner_id);
CREATE INDEX IF NOT EXISTS idx_project_members_project_id ON public.project_members(project_id);
CREATE INDEX IF NOT EXISTS idx_project_members_user_id ON public.project_members(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_project_id ON public.api_keys(project_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON public.api_keys(key_hash);

-- =============================================================================
-- Grant Permissions
-- =============================================================================
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- =============================================================================
-- Success!
-- =============================================================================
-- ✅ Your Supabase database is now ready for Lynex!
-- 
-- Next steps:
-- 1. ✅ This SQL should run without errors now
-- 2. ⏭️ Copy your Supabase keys to .env.local
-- 3. ⏭️ Start the backend services
-- 4. ⏭️ Start the frontend
-- =============================================================================
