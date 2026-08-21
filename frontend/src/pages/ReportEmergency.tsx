import { Mic, Camera, MapPin, Send, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { incidentService } from '../services/incidentService';

export default function ReportEmergency() {
  const navigate = useNavigate();
  const [description, setDescription] = useState('');
  const [danger, setDanger] = useState<'yes' | 'unsure' | null>(null);
  const [locationName, setLocationName] = useState('Library Block');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (!description && danger === null) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const incidentData = {
        description,
        location_name: locationName || "Library Block",
        severity: danger === 'yes' ? 'HIGH' : undefined
      };
      
      const newIncident = await incidentService.createIncident(incidentData);
      navigate(`/analyzing/${newIncident.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to submit report. Please try again.');
      setIsLoading(false);
    }
  };

  return (
    <div className="page-content">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-h2">Report Emergency</h1>
        <span className="badge badge-ai">AI Assisted</span>
      </div>

      <div className="card glass mb-6" style={{ borderColor: 'rgba(216, 180, 254, 0.3)' }}>
        <p className="text-small">
          🤖 <strong>You don't need to know who to call.</strong><br/>
          Describe what happened and CampusResQ AI will coordinate the right response teams.
        </p>
      </div>
      
      {error && (
        <div className="badge badge-danger text-center justify-center p-2 mb-4" style={{ whiteSpace: 'normal', borderRadius: '8px' }}>
          {error}
        </div>
      )}

      <div className="input-group mb-6">
        <label className="input-label text-h3 mb-2" style={{ color: 'var(--text-primary)' }}>What happened?</label>
        <textarea 
          className="input-field" 
          rows={4}
          placeholder="e.g. Someone collapsed near the library..."
          value={description}
          onChange={e => setDescription(e.target.value)}
          disabled={isLoading}
        />
        
        <div className="flex gap-4 mt-2">
          <button className="btn btn-secondary flex-1" style={{ padding: '12px' }} disabled={isLoading}>
            <Mic size={20} color="var(--accent-primary)" />
            <span>Voice Report</span>
          </button>
          <button className="btn btn-secondary flex-1" style={{ padding: '12px' }} disabled={isLoading}>
            <Camera size={20} />
            <span>Add Photo</span>
          </button>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-h3 mb-4">Location</h3>
        <div className="card flex justify-between items-center card-interactive border-focus mb-3">
          <div className="flex items-center gap-3">
            <MapPin size={24} color="var(--accent-blue)" />
            <div>
              <p style={{ fontWeight: 600 }}>{locationName || "Library Block"}</p>
              <p className="text-small">Ground Floor, Near Entrance</p>
            </div>
          </div>
          <span className="text-small text-info">GPS Active</span>
        </div>
        <input 
          type="text" 
          className="input-field" 
          placeholder="e.g. Main Building, North Gate"
          value={locationName}
          onChange={e => setLocationName(e.target.value)}
          disabled={isLoading}
        />
      </div>

      <div className="mb-8">
        <h3 className="text-h3 mb-4">Is anyone in immediate danger?</h3>
        <div className="flex gap-4">
          <div 
            className={`card flex-1 flex-col items-center justify-center card-interactive ${danger === 'yes' ? 'card-selected' : ''}`}
            onClick={() => !isLoading && setDanger('yes')}
            style={{ padding: '16px', opacity: isLoading ? 0.5 : 1 }}
          >
            <AlertTriangle size={24} color={danger === 'yes' ? 'var(--accent-primary)' : 'var(--text-secondary)'} className="mb-2" />
            <span style={{ fontWeight: 500, color: danger === 'yes' ? 'var(--accent-primary)' : 'inherit' }}>Yes</span>
          </div>
          <div 
            className={`card flex-1 flex-col items-center justify-center card-interactive ${danger === 'unsure' ? 'border-focus' : ''}`}
            onClick={() => !isLoading && setDanger('unsure')}
            style={{ padding: '16px', backgroundColor: danger === 'unsure' ? 'var(--bg-tertiary)' : 'var(--bg-secondary)', opacity: isLoading ? 0.5 : 1 }}
          >
            <span style={{ fontWeight: 500 }}>Not Sure</span>
          </div>
        </div>
      </div>

      <button 
        className="btn btn-danger btn-block mt-auto"
        onClick={handleSubmit}
        disabled={isLoading || (!description && danger === null)}
      >
        <Send size={20} />
        <span>{isLoading ? 'Sending Report...' : 'Submit Emergency'}</span>
      </button>
    </div>
  );
}
