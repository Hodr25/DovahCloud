// Panel deslizable que muestra los metadatos completos de un archivo.
import { AnimatePresence, motion } from "framer-motion";
import { API_BASE_URL } from "../api/client.js";

function formatDate(isoString) {
  // Traducimos la fecha ISO a un mensaje legible.
  if (!isoString) return "Fecha no disponible";
  const date = new Date(isoString);
  return date.toLocaleString();
}

export function FileDetailDrawer({ file, onClose }) {
  const open = Boolean(file);

  return (
    <AnimatePresence>
      {open && (
        <motion.aside
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(7, 2, 16, 0.65)",
            backdropFilter: "blur(6px)",
            display: "flex",
            justifyContent: "flex-end",
            zIndex: 30,
          }}
          onClick={onClose}
        >
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 140, damping: 18 }}
            className="glass-panel"
            style={{
              width: "min(520px, 90vw)",
              padding: "2.2rem",
              height: "100%",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "1.4rem",
            }}
            onClick={(event) => event.stopPropagation()}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ fontSize: "1.5rem", fontWeight: 700 }}>{file.name}</h3>
                <p style={{ color: "var(--color-text-secondary)", marginTop: "0.2rem" }}>
                  {file.mimeType} · {file.size ? `${(file.size / (1024 * 1024)).toFixed(2)} MB` : "Tamaño desconocido"}
                </p>
              </div>
              <button className="ghost-button" onClick={onClose}>
                Cerrar
              </button>
            </div>

            {file.thumbnailUrl && (
              <img
                src={file.thumbnailUrl}
                alt={`Miniatura de ${file.name}`}
                style={{
                  width: "100%",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid rgba(163, 123, 255, 0.18)",
                  boxShadow: "var(--shadow-soft)",
                }}
              />
            )}

            <section>
              <h4 style={{ marginBottom: "0.6rem", fontSize: "1rem", letterSpacing: "0.04em" }}>Descripción</h4>
              <p style={{ color: "var(--color-text-secondary)", lineHeight: 1.6 }}>
                {file.description || "Aún no se ha documentado este recurso."}
              </p>
            </section>

            <section>
              <h4 style={{ marginBottom: "0.6rem", fontSize: "1rem", letterSpacing: "0.04em" }}>Detalles</h4>
              <ul style={{ display: "grid", gap: "0.4rem", listStyle: "none" }}>
                <li style={{ color: "var(--color-text-secondary)" }}>Subido: {formatDate(file.uploadedAt)}</li>
                <li style={{ color: "var(--color-text-secondary)" }}>
                  Acceso: {file.isPrivate ? "Privado" : "Público"}
                </li>
                <li style={{ color: "var(--color-text-secondary)" }}>
                  Favorito: {file.isFavorite ? "Sí" : "No"}
                </li>
                <li style={{ color: "var(--color-text-secondary)" }}>
                  Etiquetas: {file.tags.length ? file.tags.join(", ") : "Sin etiquetas"}
                </li>
              </ul>
            </section>

            <div style={{ display: "flex", gap: "1rem" }}>
              {file.mediaUrl && (
                <a
                  className="primary-button"
                  href={file.mediaUrl.startsWith("http") ? file.mediaUrl : `${API_BASE_URL.replace("/api", "")}${file.mediaUrl}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Abrir archivo
                </a>
              )}
              <a
                className="ghost-button"
                href={`/descargar/${file.id}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Descargar original
              </a>
            </div>
          </motion.div>
        </motion.aside>
      )}
    </AnimatePresence>
  );
}
