// Panel contextual que muestra el contenido de la playlist seleccionada.
import { motion } from "framer-motion";

export function PlaylistPanel({ playlist, onPlayItem, onRemoveItem }) {
  if (!playlist) {
    return (
      <div
        className="glass-panel"
        style={{
          padding: "1.4rem",
          borderRadius: "var(--radius-lg)",
          color: "var(--color-text-secondary)",
        }}
      >
        Selecciona una playlist para revisar sus archivos y lanzar la reproducción rápida.
      </div>
    );
  }

  return (
    <motion.div
      className="glass-panel"
      style={{
        padding: "1.6rem",
        display: "flex",
        flexDirection: "column",
        gap: "1rem",
      }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h3 style={{ fontSize: "1.3rem", fontWeight: 600 }}>{playlist.name}</h3>
          <p style={{ color: "var(--color-text-secondary)", marginTop: "0.3rem" }}>
            {playlist.items.length} elemento(s) · Perfecta para sesiones temáticas.
          </p>
        </div>
      </header>

      <div className="scroll-y" style={{ maxHeight: "240px", display: "grid", gap: "0.6rem" }}>
        {playlist.items.length === 0 ? (
          <p style={{ color: "var(--color-text-secondary)" }}>
            Añade archivos desde la cuadrícula superior para completar esta playlist.
          </p>
        ) : (
          playlist.items.map((item) => (
            <motion.div
              key={item.id}
              className="glass-panel"
              style={{
                padding: "0.9rem 1rem",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <div>
                <strong>{item.name}</strong>
                <p style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)" }}>{item.mimeType}</p>
              </div>
              <div style={{ display: "flex", gap: "0.6rem" }}>
                <button className="ghost-button" onClick={() => onPlayItem?.(item)}>
                  ▶
                </button>
                <button className="ghost-button" onClick={() => onRemoveItem?.(item)}>
                  ✕
                </button>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
}
