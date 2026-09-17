import { employees } from '../data/factoryData';

export default function EmployeeTable() {
  return (
    <section className="simple-card">
      <table>
        <thead><tr><th>Name</th><th>Role</th><th>Email</th></tr></thead>
        <tbody>{employees.map((employee) => <tr key={employee.email}><td>{employee.name}</td><td>{employee.role}</td><td>{employee.email}</td></tr>)}</tbody>
      </table>
    </section>
  );
}
