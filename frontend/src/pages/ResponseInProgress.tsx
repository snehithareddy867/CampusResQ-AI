import { useParams } from 'react-router-dom';
import { ShieldAlert, Info, Map, CheckCircle2, Loader2 } from 'lucide-react';

import { useIncidentSocket } from '../hooks/useIncidentSocket';

export default function ResponseInProgress() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const { incident, connectionError } = useIncidentSocket(incidentId);

  if (!incident) {
    return (
      <div className="page-content items-center justify-center">
        <Loader2 size={32} className="text-primary mb-4" style={{ animation: 'spin 1s linear infinite' }} />
        <p className="text-muted">Loading incident details...</p>
        <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  const isReplanning = incident.status === 'REPLANNING';
  const isResolved = incident.status === 'RESOLVED';

  return (
    <div className="page-content">
      {connectionError && (
        <div className="badge badge-warning text-center justify-center p-2 mb-4" style={{ whiteSpace: 'normal', borderRadius: '8px' }}>
          Live connection interrupted. Reconnecting...
        </div>
      )}

      {isReplanning && (
        <div className="card mb-6" style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', borderColor: 'rgba(245, 158, 11, 0.3)', padding: '16px' }}>
          <div className="flex items-center gap-2 text-warning mb-2">
            <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
            <span style={{ fontWeight: 600 }}>AI is replanning the response</span>
          </div>
          <p className="text-small text-muted">Adapting to changing conditions...</p>
        </div>
      )}

      <div className="text-center mb-8">
        <h1 className="text-h1 mb-2">
          {isResolved ? 'Incident Resolved' : isReplanning ? 'Updating Plan...' : 'Help is on the way.'}
        </h1>
        <p className="text-body">
          {isResolved ? 'The situation has been handled.' : 'The right teams are being coordinated.'}
        </p>
      </div>

      {!isResolved && (
        <div className="card text-center mb-6" style={{ 
          borderColor: isReplanning ? 'var(--warning)' : 'var(--accent-primary)', 
          borderStyle: 'solid', 
          borderWidth: 2, 
          padding: '24px',
          transition: 'border-color 0.3s'
        }}>
          <h2 className={`text-h2 ${isReplanning ? 'text-warning' : 'text-danger'} mb-2`}>
            {incident.estimated_response_time_minutes ? `${incident.estimated_response_time_minutes} min` : 'Calculating...'}
          </h2>
          <p className={`text-small ${isReplanning ? 'text-warning' : 'text-danger'} font-bold mb-4`}>ETA</p>
          
          <div className="flex items-center justify-center gap-3">
            <div className={`badge ${isReplanning ? 'badge-warning' : 'badge-danger'}`}>
              {incident.incident_type || 'Emergency Team'}
            </div>
            <span className="text-small" style={{ fontWeight: 600 }}>
              {incident.status.replace('_', ' ')}
            </span>
          </div>
        </div>
      )}

      <div className="card glass mb-6">
        <h3 className="text-h3 flex items-center gap-2 mb-4">
          <span className="badge badge-ai">CampusResQ AI</span>
        </h3>
        <p className="text-small mb-4 text-muted">
          CampusResQ AI has assessed this as a <strong>{incident.severity || 'HIGH'}</strong> priority incident.
        </p>
        
        <div className="flex-col gap-3">
          {/* Display live timeline from backend */}
          {incident.timeline && [...incident.timeline].reverse().slice(0, 5).map((event, idx) => {
            const isLatest = idx === 0;
            return (
              <div key={event.id || idx} className="flex gap-3 text-small" style={{ opacity: isLatest ? 1 : 0.7, fontWeight: isLatest ? 600 : 400 }}>
                {isLatest && !isResolved ? (
                   <div style={{ width: 16, height: 16, borderRadius: '50%', border: '2px solid var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: 2 }}>
                     <div style={{ width: 6, height: 6, backgroundColor: 'var(--accent-primary)', borderRadius: '50%' }} />
                   </div>
                ) : (
                  <CheckCircle2 size={16} color="var(--success)" style={{ marginTop: 2, flexShrink: 0 }} />
                )}
                <div>
                  <span>{event.description}</span>
                  <div className="text-muted" style={{ fontSize: '0.7rem', fontWeight: 400 }}>
                    {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {incident.immediate_guidance && !isResolved && (
        <div className="card mb-6" style={{ backgroundColor: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.3)' }}>
          <h3 className="text-h3 flex items-center gap-2 mb-4 text-info">
            <ShieldAlert size={20} />
            While you wait
          </h3>
          <div className="text-small mb-2" style={{ whiteSpace: 'pre-wrap' }}>
            {incident.immediate_guidance}
          </div>
        </div>
      )}
      
      {!isResolved && (
        <div className="flex gap-4">
          <button className="btn btn-secondary flex-1">
            <Info size={16} />
            <span>Update Incident</span>
          </button>
          <button className="btn btn-secondary flex-1">
            <Map size={16} />
            <span>Live Map</span>
          </button>
        </div>
      )}

      {/* Responder Actions */}
      {incident.status !== 'RESOLVED' && incident.status !== 'CANCELLED' && (
        <div className="card mt-6 border-focus" style={{ borderColor: 'var(--accent-primary)' }}>
          <h3 className="text-h3 mb-4">Responder Actions</h3>
          <div className="flex-col gap-3">
            {(incident.status === 'REPORTED' || incident.status === 'ANALYZING' || incident.status === 'WAITING_FOR_APPROVAL' || incident.status === 'DISPATCHING') && (
              <button 
                className="btn btn-primary btn-block"
                onClick={async () => {
                  try {
                    await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/incidents/${incident.id}/accept`, {
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                    });
                  } catch (e) { console.error(e); }
                }}
              >
                Accept Incident
              </button>
            )}
            
            {(incident.status === 'ACKNOWLEDGED' || incident.status === 'DISPATCHING') && (
              <button 
                className="btn btn-primary btn-block"
                onClick={async () => {
                  try {
                    await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/incidents/${incident.id}/start`, {
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                    });
                  } catch (e) { console.error(e); }
                }}
              >
                Start Response
              </button>
            )}

            {(incident.status === 'IN_PROGRESS' || incident.status === 'REPLANNING') && (
              <button 
                className="btn btn-success btn-block"
                onClick={async () => {
                  try {
                    await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000/api'}/incidents/${incident.id}/resolve`, {
                      method: 'POST',
                      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
                    });
                  } catch (e) { console.error(e); }
                }}
              >
                Resolve Incident
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
