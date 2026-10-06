import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, AlertCircle, Lock, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Login: React.FC = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || '/';

  // If already logged in, redirect
  if (isAuthenticated) {
    navigate(from, { replace: true });
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsSubmitting(true);

    try {
      await login({ username: username.trim(), password: password.trim() });
      navigate(from, { replace: true });
    } catch (err: any) {
      if (err.response?.status === 401) {
        setError('Invalid username or password');
      } else {
        setError('An error occurred during login. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-icon-wrapper">
            <Shield className="auth-icon" />
          </div>
          <h2 className="auth-title">
            Sentinel<span className="auth-title-accent">X</span>
          </h2>
          <p className="auth-subtitle">
            Intelligent Data Loss Prevention
          </p>
        </div>

        {error && (
          <div className="auth-error">
            <AlertCircle className="auth-error-icon" />
            <span>{error}</span>
          </div>
        )}

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="auth-form-group">
            <label htmlFor="username" className="auth-label">
              <User className="auth-label-icon" />
              Username
            </label>
            <input
              id="username"
              name="username"
              type="text"
              required
              className="auth-input"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
            />
          </div>

          <div className="auth-form-group">
            <label htmlFor="password" className="auth-label">
              <Lock className="auth-label-icon" />
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              className="auth-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="auth-btn"
          >
            {isSubmitting ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
