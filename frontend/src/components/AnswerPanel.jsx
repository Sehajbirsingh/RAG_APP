import { Brain, FileText, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";

function splitThinking(answer, thinking) {
  if (!answer) {
    return {
      cleanAnswer: "",
      thinkingText: thinking || "",
    };
  }

  const endTag = "</think>";
  const endIndex = answer.lastIndexOf(endTag);
  if (endIndex === -1) {
    return {
      cleanAnswer: answer,
      thinkingText: thinking || "",
    };
  }

  const startTag = "<think>";
  const startIndex = answer.indexOf(startTag);
  const embeddedThinking =
    startIndex === -1
      ? answer.slice(0, endIndex)
      : answer.slice(startIndex + startTag.length, endIndex);

  return {
    cleanAnswer: answer.slice(endIndex + endTag.length).trim(),
    thinkingText: (thinking || embeddedThinking).trim(),
  };
}

function formatElapsedTime(milliseconds) {
  if (!milliseconds && milliseconds !== 0) return "";

  const totalSeconds = Math.max(1, Math.round(milliseconds / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes > 0) {
    return `${minutes}m ${seconds}s`;
  }

  return `${seconds}s`;
}

function renderInlineMarkdown(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    return part;
  });
}

function renderAnswerMarkdown(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !/^[-_]{3,}$/.test(line))
    .map((line, index) => {
      if (line.startsWith("## ")) {
        return <h3 key={index}>{renderInlineMarkdown(line.slice(3))}</h3>;
      }

      if (line.startsWith("### ")) {
        return <h4 key={index}>{renderInlineMarkdown(line.slice(4))}</h4>;
      }

      if (line.startsWith("- ")) {
        return (
          <div className="markdown-bullet" key={index}>
            <span aria-hidden="true" />
            <p>{renderInlineMarkdown(line.slice(2))}</p>
          </div>
        );
      }

      return <p key={index}>{renderInlineMarkdown(line)}</p>;
    });
}

function AnswerPanel({ answer, thinking, isLoading, elapsedMs }) {
  const [showThinking, setShowThinking] = useState(false);
  const { cleanAnswer, thinkingText } = splitThinking(answer, thinking);
  const elapsedTime = formatElapsedTime(elapsedMs);

  return (
    <section className="answer-panel">
      <div className="panel-heading">
        <div className="section-title">
          <Sparkles size={20} aria-hidden="true" />
          <h2>Answer</h2>
        </div>

        {cleanAnswer && !isLoading && (
          <button
            className="ghost-button"
            type="button"
            onClick={() => setShowThinking((value) => !value)}
          >
            <Brain size={16} aria-hidden="true" />
            {showThinking ? "Hide thinking" : "View thinking"}
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="loading-block">
          <Loader2 className="spin" size={26} aria-hidden="true" />
          <span>Generating answer</span>
        </div>
      ) : cleanAnswer ? (
        <>
          {showThinking ? (
            <div className="thinking-panel">
              {thinkingText || "No thinking trace was returned for this response. Restart the backend and run a new search if this result was generated before thinking capture was enabled."}
            </div>
          ) : (
            <div className="answer-text answer-markdown">{renderAnswerMarkdown(cleanAnswer)}</div>
          )}
          {elapsedTime && <div className="answer-time">{elapsedTime}</div>}
        </>
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
