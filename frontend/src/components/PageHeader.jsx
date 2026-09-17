export default function PageHeader({ title, description }) {
  return (
    <>
      <h1>{title}</h1>
      <p className="page-text">{description}</p>
    </>
  );
}
