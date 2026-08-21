import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authService } from '../services/authService';
import { useAuth } from '../context/AuthContext';
import { ShieldAlert, UserPlus } from 'lucide-react';
import type { DepartmentName } from '../types';

export default function Signup() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    campus_id: '',
    department: 'NONE' as DepartmentName,
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const data = await authService.register(formData);
      login(data.token, data.user);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const departments: DepartmentName[] = ['NONE', 'MEDICAL', 'SECURITY', 'TRANSPORT', 'FACILITIES', 'COMMUNICATION'];

  return (
    <div className="page-content" style={{ minHeight: '100vh', padding: '24px' }}>
      <div className="text-center mb-6 mt-4">
        <ShieldAlert size={40} color="var(--accent-primary)" style={{ margin: '0 auto 16px' }} />
        <h1 className="text-h2">Create Account</h1>
      </div>

      <form onSubmit={handleSubmit} className="card glass flex-col gap-4">
        {error && (
          <div className="badge badge-danger text-center justify-center p-2" style={{ whiteSpace: 'normal', borderRadius: '8px' }}>
            {error}
          </div>
        )}
        
        <div className="input-group">
          <label className="input-label">Full Name</label>
          <input 
            type="text" 
            className="input-field" 
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            required
          />
        </div>
        
        <div className="input-group">
          <label className="input-label">Campus ID</label>
          <input 
            type="text" 
            className="input-field" 
            value={formData.campus_id}
            onChange={(e) => setFormData({...formData, campus_id: e.target.value})}
            required
          />
        </div>
        
        <div className="input-group">
          <label className="input-label">Email</label>
          <input 
            type="email" 
            className="input-field" 
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            required
          />
        </div>
        
        <div className="input-group">
          <label className="input-label">Password</label>
          <input 
            type="password" 
            className="input-field" 
            value={formData.password}
            onChange={(e) => setFormData({...formData, password: e.target.value})}
            required
          />
        </div>
        
        <div className="input-group">
          <label className="input-label">Department Association</label>
          <p className="text-small text-muted mb-2">Everyone can report an emergency. Department membership only determines which response alerts you receive.</p>
          <select 
            className="input-field"
            value={formData.department}
            onChange={(e) => setFormData({...formData, department: e.target.value as DepartmentName})}
            style={{ backgroundColor: 'var(--bg-tertiary)', padding: '14px 16px', appearance: 'none' }}
          >
            {departments.map(d => (
              <option key={d} value={d}>{d === 'NONE' ? 'No Department (Standard User)' : d}</option>
            ))}
          </select>
        </div>

        <button 
          type="submit" 
          className="btn btn-primary btn-block mt-4"
          disabled={isLoading}
        >
          {isLoading ? 'Creating account...' : (
            <>
              <UserPlus size={20} />
              <span>Create Account</span>
            </>
          )}
        </button>

        <div className="text-center mt-2">
          <p className="text-small">
            Already have an account? <Link to="/login" className="text-primary">Log in</Link>
          </p>
        </div>
      </form>
    </div>
  );
}
