import { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Cpu, CheckCircle2, Loader2, AlertCircle } from 'lucide-react';

import { useIncidentSocket } from '../hooks/useIncidentSocket';

export default function AIAnalyzing() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const navigate = useNavigate();
  const { incident, connectionError } = useIncidentSocket(incidentId);

  // We map backend statuses or events to our UI stages
  const getStageLevel = () => {
    if (!incident) return 0;
    
    // Check timeline for specific AI events
    const events = incident.timeline.map(t => t.event);
    
    if (incident.status === 'DISPATCHING' || incident.status === 'IN_PROGRESS' || incident.status === 'REPLANNING' || incident.status === 'RESOLVED') {
      return 4; // Complete
    }
    
    if (events.includes('RESPONDER_ASSIGNED') || events.includes('DEPARTMENT_ASSIGNED')) {
      return 3;
    }
    
    if (events.includes('AI_ANALYSIS_COMPLETED') || incident.severity) {
      return 2;
    }
    
    if (events.includes('AI_ANALYSIS_STARTED') || incident.status === 'ANALYZING') {
      return 1;
    }
    
    return 0; // REPORTED / Understanding incident
  };

  const stage = getStageLevel();

  const stages = [
    "Understanding incident...",
    "Assessing severity...",
    "Identifying response teams...",
    "Checking available resources..."
  ];

  useEffect(() => {
    // If analysis is completely finished and response teams are being coordinated/dispatched
    if (stage >= 4) {
      const timer = setTimeout(() => navigate(`/response/${incidentId}`), 1000);
      return () => clearTimeout(timer);
    }
  }, [stage, navigate, incidentId]);

  return (
    <div className="page-content items-center justify-center" style={{ minHeight: '80vh' }}>
      <div className="flex-col items-center mb-8">
        <div 
          className="animate-pulse-glow"
          style={{
            width: 100,
            height: 100,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(236, 72, 153, 0.2))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '32px'
          }}
        >
          <Cpu size={48} color="#d8b4fe" />
        </div>
        
        <h2 className="text-h2 text-center mb-2">Analyzing Report</h2>
        <p className="text-muted">Incident ID: {incidentId?.split('-')[0]}</p>
        
        {connectionError && (
          <div className="badge badge-warning mt-4 flex items-center gap-1">
            <AlertCircle size={14} /> Connection interrupted. Retrying...
          </div>
        )}
      </div>

      <div className="card w-full glass">
        <div className="flex-col gap-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 size={20} color="var(--success)" />
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Report received</span>
          </div>
          <div className="flex items-center gap-3">
            <CheckCircle2 size={20} color="var(--success)" />
            <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Location identified</span>
          </div>
          
          {stages.map((text, idx) => (
            <div key={idx} className="flex items-center gap-3" style={{ opacity: stage >= idx ? 1 : 0.3, transition: 'opacity 0.3s' }}>
              {stage > idx ? (
                <CheckCircle2 size={20} color="var(--success)" />
              ) : stage === idx ? (
                <Loader2 size={20} className="text-primary" style={{ animation: 'spin 1s linear infinite' }} />
              ) : (
                <div style={{ width: 20, height: 20, borderRadius: '50%', border: '2px solid var(--text-tertiary)' }} />
              )}
              <span style={{ fontWeight: stage === idx ? 600 : 500, color: stage >= idx ? 'var(--text-primary)' : 'var(--text-secondary)' }}>
                {text}
              </span>
            </div>
          ))}
        </div>
      </div>
      
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
