/**
 * Placeholder page for routes that are not yet implemented.
 * Clearly indicates the feature is planned for a future phase.
 */
export default function PlaceholderPage({
  title,
  phase,
  icon,
}: {
  title: string;
  phase: number;
  icon: string;
}) {
  return (
    <div className="placeholder-page">
      <div className="placeholder-card">
        <span className="placeholder-icon">{icon}</span>
        <h2>{title}</h2>
        <p className="placeholder-phase">Coming in Phase {phase}</p>
        <p className="placeholder-description">
          This feature is planned for a future development phase.
          <br />
          The foundation is in place and ready for implementation.
        </p>
        <div className="placeholder-badge">
          <span className="badge-dot" />
          Under Development
        </div>
      </div>
    </div>
  );
}
