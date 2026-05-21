import { FileText, Loader2, Sparkles } from "lucide-react";

function AnswerPanel({ answer, isLoading }) {
  return (
    <section className="answer-panel">
      <div className="section-title">
        <Sparkles size={20} aria-hidden="true" />
        <h2>Answer</h2>
      </div>

      {isLoading ? (
        <div className="loading-block">
          <Loader2 className="spin" size={26} aria-hidden="true" />
          <span>Generating answer</span>
        </div>
      ) : answer ? (
        <div className="answer-text">{answer}</div>
      ) : (
        <div className="empty-panel">
          <FileText size={22} aria-hidden="true" />
          <span>Run a search to generate an answer.</span>
        </div>
      )}
    </section>
  );
}

export default AnswerPanel;

