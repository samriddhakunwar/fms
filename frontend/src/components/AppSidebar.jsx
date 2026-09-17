import { menuByRole, roleNames } from '../data/factoryData';

export default function AppSidebar({ role, page, onSelect, onLogout }) {
  return (
    <aside className="simple-sidebar">
      <h2>Factory MS</h2>
      <p>{roleNames[role]} Panel</p>

      <nav>
        {menuByRole[role].map((item) => (
          <button
            className={page === item ? 'selected' : ''}
            key={item}
            onClick={() => onSelect(item)}
          >
            {item}
          </button>
        ))}
      </nav>

      <button className="logout-button" onClick={onLogout}>Logout</button>
    </aside>
  );
}
