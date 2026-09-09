/**
 * Colored status indicator dot with optional label.
 */
export default function StatusIndicator({
  status,
  label,
}: {
  status: 'ok' | 'degraded' | 'offline' | 'unknown';
  label?: string;
}) {
  const colorMap: Record<string, string> = {
    ok: 'var(--color-success)',
    degraded: 'var(--color-warning)',
    offline: 'var(--color-danger)',
    unknown: 'var(--color-muted)',
  };

  return (
    <span className="status-indicator">
      <span
        className="status-dot"
        style={{ backgroundColor: colorMap[status] || colorMap.unknown }}
      />
      {label && <span className="status-label">{label}</span>}
    </span>
  );
}
