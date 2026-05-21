import { Hammer, Layers, Package, PaintBucket, Tag } from "lucide-react";

function compactText(value, fallback = "Unknown") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}

function scorePercent(score) {
  return `${Math.round(Number(score || 0) * 100)}%`;
}

function ProductCard({ product, rank }) {
  return (
    <article className="product-card">
      <div className="product-header">
        <div className="rank-badge">{rank}</div>
        <div className="product-heading">
          <h3>{compactText(product.product_title, "Untitled product")}</h3>
          <div className="product-subline">
            <Package size={15} aria-hidden="true" />
            <span>UID {compactText(product.product_uid)}</span>
            <span className="dot" />
            <span>{compactText(product.source)}</span>
          </div>
        </div>
        <div className="score-badge">{scorePercent(product.score)}</div>
      </div>

      <div className="meta-strip">
        <span title="Brand">
          <Tag size={14} aria-hidden="true" />
          {compactText(product.brand)}
        </span>
        <span title="Color">
          <PaintBucket size={14} aria-hidden="true" />
          {compactText(product.color)}
        </span>
        <span title="Material">
          <Hammer size={14} aria-hidden="true" />
          {compactText(product.material)}
        </span>
        <span title="Category">
          <Layers size={14} aria-hidden="true" />
          {compactText(product.category)}
        </span>
      </div>

      <p className="description-snippet">{compactText(product.description_text, "No description available.")}</p>
    </article>
  );
}

export default ProductCard;

