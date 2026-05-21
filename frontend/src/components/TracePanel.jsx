import { CheckCircle2, Filter, Gauge, Loader2, RotateCcw, SlidersHorizontal, XCircle } from "lucide-react";

function TraceValue({ label, value }) {
  return (
    <div className="trace-value">
      <span>{label}</span>
      <strong>{value || "None"}</strong>
    </div>
  );
}

function TracePanel({ trace, isLoading }) {
  if (isLoading) {
    return (
      <section className="trace-panel">
        <div className="section-title">
          <SlidersHorizontal size={20} aria-hidden="true" />
          <h2>Metadata Trace</h2>
        </div>
        <div className="loading-block">
          <Loader2 className="spin" size={26} aria-hidden="true" />
          <span>Extracting metadata filters</span>
        </div>
      </section>
    );
  }

  if (!trace) {
    return (
      <section className="trace-panel">
        <div className="section-title">
          <SlidersHorizontal size={20} aria-hidden="true" />
          <h2>Metadata Trace</h2>
        </div>
        <div className="empty-panel">
          <Gauge size={22} aria-hidden="true" />
          <span>No trace yet.</span>
        </div>
      </section>
    );
  }

  const used = Boolean(trace.metadata_step_used);

  return (
    <section className="trace-panel">
      <div className="section-title">
        <SlidersHorizontal size={20} aria-hidden="true" />
        <h2>Metadata Trace</h2>
      </div>

      <div className={`decision-banner ${used ? "used" : "skipped"}`}>
        {used ? <CheckCircle2 size={19} aria-hidden="true" /> : <XCircle size={19} aria-hidden="true" />}
        <span>{trace.decision}</span>
      </div>

      <div className="trace-grid">
        <TraceValue label="Brand" value={trace.brand} />
        <TraceValue label="Color" value={trace.color} />
        <TraceValue label="Material" value={trace.material} />
        <TraceValue label="Confidence" value={trace.confidence} />
      </div>

      <div className="count-row">
        <span>
          <Filter size={15} aria-hidden="true" />
          {trace.filtered_count ?? "Skipped"}
        </span>
        <span>
          <Gauge size={15} aria-hidden="true" />
          {trace.candidate_count ?? trace.original_count ?? "NA"}
        </span>
        {trace.fallback_used && (
          <span>
            <RotateCcw size={15} aria-hidden="true" />
            Fallback
          </span>
        )}
      </div>
    </section>
  );
}

export default TracePanel;
