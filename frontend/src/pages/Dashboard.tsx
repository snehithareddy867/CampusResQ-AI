import { AlertTriangle, Clock, MapPin, Activity, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { incidentService } from '../services/incidentService';
import { useAuth } from '../context/AuthContext';
import type { Incident } from '../types';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [departmentIncidents, setDepartmentIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const data = await incidentService.getMyIncidents();
        setIncidents(data);
        
        if (user && user.department !== 'NONE') {
          const deptData = await incidentService.getDepartmentIncidents();
          setDepartmentIncidents(deptData);
        }
      } catch (err) {
        console.error("Failed to load incidents", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchIncidents();
  }, [user]);

  const activeIncidents = incidents.filter(i => i.status !== 'RESOLVED' && i.status !== 'CANCELLED');
  const activeDeptIncidents = departmentIncidents.filter(i => i.status !== 'RESOLVED' && i.status !== 'CANCELLED');

  return (
    <div className="page-content">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-h2">Hello, {user?.name || 'User'}</h1>
          <p className="text-muted">CampusResQ AI is ready.</p>
          {user?.department !== 'NONE' && (
            <span className="badge badge-ai mt-2">{user?.department} Department</span>
          )}
        </div>
        <button onClick={() => { logout(); navigate('/login'); }} className="btn btn-secondary" style={{ padding: '8px' }}>
          <LogOut size={16} />
        </button>
      </div>

      <div 
        className="card card-interactive"
        style={{
          backgroundColor: 'var(--accent-primary)',
          color: '#fff',
          border: 'none',
          padding: '32px 24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          boxShadow: '0 8px 32px var(--accent-primary-glow)'
        }}
        onClick={() => navigate('/report')}
      >
        <AlertTriangle size={48} className="mb-4" />
        <h2 className="text-h2 mb-2">Report an Emergency</h2>
        <p style={{ opacity: 0.9 }}>Tell us what happened. We'll find the right team.</p>
      </div>

      <h3 className="text-h3 mt-6 mb-2">Active Incidents</h3>
      {isLoading ? (
        <div className="card glass text-center text-muted">Loading incidents...</div>
      ) : activeIncidents.length > 0 ? (
        <div className="flex-col gap-4">
          {activeIncidents.map(incident => (
            <div 
              key={incident.id} 
              className="card glass card-interactive" 
              onClick={() => navigate(`/response/${incident.id}`)}
            >
              <div className="flex justify-between items-center mb-4">
                <span className="badge badge-danger">{incident.id.split('-')[0]}</span>
                {incident.estimated_response_time_minutes ? (
                  <span className="text-small text-danger" style={{ fontWeight: 600 }}>
                    ETA {incident.estimated_response_time_minutes} min
                  </span>
                ) : (
                  <span className="text-small text-warning" style={{ fontWeight: 600 }}>Analyzing</span>
                )}
              </div>
              <h4 className="text-h3 mb-2">{incident.incident_type || 'Emergency Request'}</h4>
              <div className="flex items-center gap-2 mb-2 text-small">
                <MapPin size={16} color="var(--text-secondary)" />
                <span>{incident.location_name || 'Unknown Location'}</span>
              </div>
              <div className="flex items-center gap-2 text-small">
                <Activity size={16} color="var(--success)" />
                <span className="text-success">{incident.status.replace('_', ' ')}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card glass text-center text-muted">
          No active incidents reported by you.
        </div>
      )}

      <h3 className="text-h3 mt-6 mb-2">Recent Activity</h3>
      <div className="card text-small flex-col gap-4">
        <div className="flex gap-3">
          <Clock size={16} className="text-muted" />
          <div>
            <p style={{ fontWeight: 500 }}>System Sync Completed</p>
            <p className="text-muted">Just now</p>
          </div>
        </div>
      </div>

      {user?.department !== 'NONE' && (
        <>
          <h3 className="text-h3 mt-6 mb-2">{user?.department} Department Incidents</h3>
          {isLoading ? (
            <div className="card glass text-center text-muted">Loading department incidents...</div>
          ) : activeDeptIncidents.length > 0 ? (
            <div className="flex-col gap-4">
              {activeDeptIncidents.map(incident => (
                <div 
                  key={incident.id} 
                  className="card glass card-interactive" 
                  onClick={() => navigate(`/response/${incident.id}`)}
                >
                  <div className="flex justify-between items-center mb-4">
                    <span className="badge badge-danger">{incident.id.split('-')[0]}</span>
                    {incident.estimated_response_time_minutes ? (
                      <span className="text-small text-danger" style={{ fontWeight: 600 }}>
                        ETA {incident.estimated_response_time_minutes} min
                      </span>
                    ) : (
                      <span className="text-small text-warning" style={{ fontWeight: 600 }}>Analyzing</span>
                    )}
                  </div>
                  <h4 className="text-h3 mb-2">{incident.incident_type || 'Emergency Request'}</h4>
                  <div className="flex items-center gap-2 mb-2 text-small">
                    <MapPin size={16} color="var(--text-secondary)" />
                    <span>{incident.location_name || 'Unknown Location'}</span>
                  </div>
                  <div className="flex items-center gap-2 text-small">
                    <Activity size={16} color="var(--success)" />
                    <span className="text-success">{incident.status.replace('_', ' ')}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card glass text-center text-muted">
              No active incidents assigned to your department.
            </div>
          )}
        </>
      )}
      <div className="card text-small flex-col gap-4">
        <div className="flex gap-3">
          <Clock size={16} className="text-muted" />
          <div>
            <p style={{ fontWeight: 500 }}>System Sync Completed</p>
            <p className="text-muted">Just now</p>
          </div>
        </div>
      </div>
    </div>
  );
}
