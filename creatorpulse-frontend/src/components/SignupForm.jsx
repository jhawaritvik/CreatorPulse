import { useState } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';

export default function SignupForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { 
        data: { 
          full_name: fullName 
        } 
      }
    });
    
    if (error) {
      setError(error.message);
    } else {
      // Check if email confirmation is required
      if (data.user && !data.user.email_confirmed_at) {
        setError('Please check your email for a confirmation link before signing in.');
      } else {
        navigate('/dashboard');
      }
    }
    
    setLoading(false);
  };

  return (
    <form onSubmit={handleSignup} className="space-y-6">
      <div>
        <label htmlFor="fullName" className="sr-only">
          Full Name
        </label>
        <input
          id="fullName"
          name="fullName"
          type="text"
          autoComplete="name"
          required
          className="input"
          placeholder="Full Name"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </div>
      
      <div>
        <label htmlFor="email" className="sr-only">
          Email address
        </label>
        <input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          className="input"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>
      
      <div>
        <label htmlFor="password" className="sr-only">
          Password
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="new-password"
          required
          className="input"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </div>

      {error && (
        <div className="text-red-600 text-sm text-center">
          {error}
        </div>
      )}

      <div>
        <button
          type="submit"
          disabled={loading}
          className="btn"
        >
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </div>
    </form>
  );
}
