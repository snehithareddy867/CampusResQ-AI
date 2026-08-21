import { Bell, User, ShieldAlert } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';

export default function Header() {
  const location = useLocation();
  const navigate = useNavigate();
  
  if (location.pathname === '/') return null;

  return (
    <header className="glass" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 24px',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      borderBottom: '1px solid var(--glass-border)'
    }}>
      <div 
        className="flex items-center gap-2" 
        style={{ cursor: 'pointer' }}
        onClick={() => navigate('/dashboard')}
      >
        <ShieldAlert color="var(--accent-primary)" size={24} />
        <h2 className="text-h3" style={{ margin: 0 }}>CampusResQ AI</h2>
      </div>
      
      <div className="flex items-center gap-4">
        <div style={{ position: 'relative', cursor: 'pointer' }}>
          <Bell size={20} color="var(--text-secondary)" />
          <span style={{
            position: 'absolute',
            top: -2,
            right: -2,
            width: 8,
            height: 8,
            backgroundColor: 'var(--accent-primary)',
            borderRadius: '50%',
            boxShadow: '0 0 8px var(--accent-primary-glow)'
          }} />
        </div>
        <div style={{
          width: 32,
          height: 32,
          borderRadius: '50%',
          backgroundColor: 'var(--bg-tertiary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer'
        }}>
          <User size={16} color="var(--text-secondary)" />
        </div>
      </div>
    </header>
  );
}
