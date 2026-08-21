import { ShieldAlert, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="page-content items-center justify-center" style={{ padding: '40px 24px', textAlign: 'center' }}>
      <div 
        className="animate-pulse-glow"
        style={{
          width: 80,
          height: 80,
          borderRadius: '50%',
          backgroundColor: 'rgba(255, 59, 59, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '24px'
        }}
      >
        <ShieldAlert size={48} color="var(--accent-primary)" />
      </div>
      
      <h1 className="text-h1 mb-4">
        CampusResQ <span className="text-primary">AI</span>
      </h1>
      
      <p className="text-body mb-8" style={{ maxWidth: '80%', margin: '0 auto 32px' }}>
        The intelligent emergency response network. You report it, AI handles the rest.
      </p>

      <div className="flex-col w-full gap-4 mt-8">
        <button 
          className="btn btn-primary btn-block justify-between"
          onClick={() => navigate('/dashboard')}
        >
          <span>Get Started</span>
          <ArrowRight size={20} />
        </button>
        <button className="btn btn-secondary btn-block">
          Login to your account
        </button>
      </div>

      <div className="mt-auto pt-8 flex-col gap-4">
        <div className="card glass text-left w-full animate-slide-up" style={{ animationDelay: '0.2s' }}>
          <h3 className="text-h3 mb-2 flex items-center gap-2">
            <span className="badge badge-ai">AI Orchestrated</span>
          </h3>
          <p className="text-small">
            CampusResQ AI routes the emergency to the correct departments and coordinates the response instantly.
          </p>
        </div>
      </div>
    </div>
  );
}
