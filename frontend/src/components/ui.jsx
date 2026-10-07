// Markup shared by the list pages. Each renders exactly the Bootstrap HTML
// the pages used to write out by hand.

export function Modal({ title, onClose, onSubmit, large, saving, submitLabel, footer, children }) {
  const inner = (
    <>
      <div className="modal-header">
        <h5 className="modal-title">{title}</h5>
        <button type="button" className="btn-close" onClick={onClose} aria-label="Close" />
      </div>
      <div className="modal-body">{children}</div>
      <div className="modal-footer">
        {footer ?? (
          <>
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {submitLabel}
            </button>
          </>
        )}
      </div>
    </>
  );

  return (
    <>
      <div className="modal d-block" tabIndex={-1} role="dialog">
        <div className={large ? "modal-dialog modal-lg" : "modal-dialog"} role="document">
          <div className="modal-content">
            {onSubmit ? <form onSubmit={onSubmit}>{inner}</form> : inner}
          </div>
        </div>
      </div>
      <div className="modal-backdrop show" />
    </>
  );
}

export function ConfirmModal({
  title,
  onClose,
  onConfirm,
  busy,
  confirmLabel = "Delete",
  busyLabel = "Deleting…",
  variant = "danger",
  children,
}) {
  return (
    <Modal
      title={title}
      onClose={onClose}
      footer={
        <>
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className={`btn btn-${variant}`} onClick={onConfirm} disabled={busy}>
            {busy ? busyLabel : confirmLabel}
          </button>
        </>
      }
    >
      {children}
    </Modal>
  );
}

/** The "Loading…" / empty row of a table body; renders nothing once there are rows. */
export function StatusRow({ loading, empty, colSpan, children }) {
  if (loading) {
    return (
      <tr>
        <td colSpan={colSpan} className="text-center py-4">
          Loading…
        </td>
      </tr>
    );
  }
  if (empty) {
    return (
      <tr>
        <td colSpan={colSpan} className="text-center py-4 text-muted">
          {children}
        </td>
      </tr>
    );
  }
  return null;
}

export function FieldError({ errors }) {
  return errors ? <div className="text-danger small">{errors[0]}</div> : null;
}
