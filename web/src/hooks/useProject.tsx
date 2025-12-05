import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../api/client';

interface Project {
  project_id: string;
  name: string;
  description?: string;
  owner_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  member_count: number;
  created_at: string;
}

interface ProjectContextType {
  currentProject: Project | null;
  projects: Project[];
  loading: boolean;
  switchProject: (projectId: string) => void;
  refreshProjects: () => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project>;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const [currentProject, setCurrentProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const response = await api.get('/projects');
      const projectsList = response.data;
      setProjects(projectsList);

      // Load saved project from localStorage or use first project
      const savedProjectId = localStorage.getItem('currentProjectId');
      const savedProject = projectsList.find((p: Project) => p.project_id === savedProjectId);
      
      if (savedProject) {
        setCurrentProject(savedProject);
      } else if (projectsList.length > 0) {
        setCurrentProject(projectsList[0]);
        localStorage.setItem('currentProjectId', projectsList[0].project_id);
      }
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const switchProject = (projectId: string) => {
    const project = projects.find(p => p.project_id === projectId);
    if (project) {
      setCurrentProject(project);
      localStorage.setItem('currentProjectId', projectId);
      // Trigger reload of data for new project
      window.dispatchEvent(new CustomEvent('projectChanged', { detail: projectId }));
    }
  };

  const refreshProjects = async () => {
    await loadProjects();
  };

  const createProject = async (name: string, description?: string): Promise<Project> => {
    const response = await api.post('/projects', { name, description });
    const newProject = response.data;
    await refreshProjects();
    switchProject(newProject.project_id);
    return newProject;
  };

  return (
    <ProjectContext.Provider
      value={{
        currentProject,
        projects,
        loading,
        switchProject,
        refreshProjects,
        createProject,
      }}
    >
      {children}
    </ProjectContext.Provider>
  );
}

export function useProject() {
  const context = useContext(ProjectContext);
  if (context === undefined) {
    throw new Error('useProject must be used within a ProjectProvider');
  }
  return context;
}
