import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/authService';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, LogIn } from 'lucide-react';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const data = await authService.login(email, password);
      login(data.token, data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'We couldn\'t sign you in. Check your email and password and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="page-content justify-center" style={{ minHeight: '100vh', padding: '24px' }}>
      <div className="text-center mb-8">
        <ShieldAlert size={48} color="var(--accent-primary)" style={{ margin: '0 auto 16px' }} />
        <h1 className="text-h2">Welcome Back</h1>
        <p className="text-muted">Sign in to CampusResQ AI</p>
      </div>

      <form onSubmit={handleSubmit} className="card glass flex-col gap-4">
        {error && (
          <div className="badge badge-danger text-center justify-center p-2" style={{ whiteSpace: 'normal', borderRadius: '8px' }}>
            {error}
          </div>
        )}
        
        <div className="input-group">
          <label className="input-label">Email</label>
          <input 
            type="email" 
            className="input-field" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="input-group">
          <label className="input-label">Password</label>
          <input 
            type="password" 
            className="input-field" 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button 
          type="submit" 
          className="btn btn-primary btn-block mt-4"
          disabled={isLoading}
        >
          {isLoading ? 'Signing in...' : (
            <>
              <LogIn size={20} />
              <span>Login</span>
            </>
          )}
        </button>

        <div className="text-center mt-4">
          <p className="text-small">
            Don't have an account? <Link to="/signup" className="text-primary">Sign up</Link>
          </p>
        </div>
      </form>
    </div>
  );
}
