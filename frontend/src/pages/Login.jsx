import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const accounts = {
  'admin@gmail.com': { password: 'admin123', role: 'admin' },
  'manager@gmail.com': { password: 'manager123', role: 'manager' },
  'staff@gmail.com': { password: 'staff123', role: 'staff' },
};

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');

  const submit = (event) => {
    event.preventDefault();
    const account = accounts[form.email];

    if (!account || account.password !== form.password) {
      setError('Please check your email and password.');
      return;
    }
    navigate(`/${account.role}`);
  };

  return (
    <main className="login-page">
      <section className="login-intro">
        <div className="brand"><span className="brand-mark">F</span> Factory Management System</div>

        <div className="intro-copy">
          <span className="eyebrow">Factory management system</span>
          <h1>Run the factory floor with clarity.</h1>
          <p>One simple workspace for inventory, customer orders, sales activity, and your team.</p>
        </div>
      </section>

      <section className="login-panel">
        <form className="login-card" onSubmit={submit}>
          <span className="eyebrow">Welcome back</span>
          <h2>Sign in to Factory Management System</h2>

          <label>Email address<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>

          <label>Password<input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></label>

          {error && <p className="form-error">{error}</p>}
          <button className="primary-button" type="submit">Sign in <span>→</span></button>
        </form>
      </section>
    </main>
  )
}
