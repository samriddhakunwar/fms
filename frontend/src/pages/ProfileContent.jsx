import PageHeader from '../components/PageHeader';

export default function ProfileContent() {
  return (
    <>
      <PageHeader title="My Profile" description="Your employee information." />
      <section className="simple-card profile"><h2>Sita Sharma</h2><p><b>Employee ID:</b> EMP-1054</p><p><b>Role:</b> Inventory Assistant</p><p><b>Department:</b> Warehouse</p><p><b>Email:</b> sita@factory.com</p></section>
    </>
  );
}
