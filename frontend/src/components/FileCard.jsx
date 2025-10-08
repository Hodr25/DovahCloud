// Tarjeta representativa para cada archivo dentro de la cuadrícula.
import { motion } from "framer-motion";

function getIconByMime(mimeType) {
  // Asociamos un emoji según el tipo para un reconocimiento rápido.
  if (!mimeType) return "📁";
  if (mimeType.startsWith("image/")) return "🖼️";
  if (mimeType.startsWith("video/")) return "🎬";
  if (mimeType.startsWith("audio/")) return "🎧";
  if (mimeType === "application/pdf") return "📄";
  if (mimeType.includes("zip") || mimeType.includes("rar")) return "🗜️";
  return "📦";
}

function formatSize(bytes) {
  // Creamos una representación legible del tamaño de archivo.
  if (!bytes) return "—";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / Math.pow(1024, exponent);
  return `${value.toFixed(1)} ${units[exponent]}`;
}

export function FileCard({ file, onSelect, onToggleFavorite, onQuickPlay, onAddToPlaylist }) {
  const icon = getIconByMime(file.mimeType);

  return (
    <motion.article
      className="glass-panel"
      style={{
        padding: "1.1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.8rem",
        cursor: "pointer",
        position: "relative",
        overflow: "hidden",
      }}
      whileHover={{ y: -4, scale: 1.01 }}
      transition={{ duration: 0.2 }}
      onClick={() => onSelect(file)}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ display: "flex", gap: "0.8rem", alignItems: "center" }}>
          <span
            style={{
              fontSize: "1.8rem",
              filter: "drop-shadow(0 6px 12px rgba(89, 33, 212, 0.4))",
            }}
          >
            {icon}
          </span>
          <div>
            <h4
              style={{
                fontSize: "1.05rem",
                fontWeight: 600,
                marginBottom: "0.35rem",
                lineHeight: 1.3,
              }}
              className="text-balance"
            >
              {file.name}
            </h4>
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.88rem" }}>
              {file.mimeType ?? "Tipo desconocido"}
            </p>
          </div>
        </div>
        <button
          className="ghost-button"
          onClick={(event) => {
            event.stopPropagation();
            onToggleFavorite(file);
          }}
        >
          {file.isFavorite ? "★" : "☆"}
        </button>
      </div>

      <p
        style={{
          fontSize: "0.9rem",
          color: "var(--color-text-secondary)",
          lineHeight: 1.5,
          flexGrow: 1,
        }}
        className="text-balance"
      >
        {file.description || "Sin descripción registrada para este elemento."}
      </p>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)" }}>
          {formatSize(file.size)}
        </span>
        <div style={{ display: "flex", gap: "0.6rem" }}>
          <button
            className="ghost-button"
            onClick={(event) => {
              event.stopPropagation();
              onQuickPlay(file);
            }}
          >
            ▶ Vista previa
          </button>
          {onAddToPlaylist && (
            <button
              className="ghost-button"
              onClick={(event) => {
                event.stopPropagation();
                onAddToPlaylist(file);
              }}
            >
              ➕ Playlist
            </button>
          )}
        </div>
      </div>

      {file.thumbnailUrl && (
        <img
          src={file.thumbnailUrl}
          alt={`Miniatura de ${file.name}`}
          style={{
            position: "absolute",
            inset: "auto -20% -30% auto",
            width: "220px",
            opacity: 0.2,
            transform: "rotate(-12deg)",
            pointerEvents: "none",
          }}
        />
      )}
    </motion.article>
  );
}
