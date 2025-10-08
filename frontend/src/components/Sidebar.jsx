// Panel lateral que agrupa filtros, métricas y playlists del usuario.
import { motion } from "framer-motion";

const typeFilters = [
  { id: "all", label: "Todo" },
  { id: "image/", label: "Imágenes" },
  { id: "video/", label: "Vídeos" },
  { id: "audio/", label: "Audio" },
  { id: "application/pdf", label: "PDF" },
  { id: "text/", label: "Documentos" },
];

export function Sidebar({
  stats,
  tags,
  selectedTag,
  onSelectTag,
  selectedType,
  onSelectType,
  playlists,
  onSelectPlaylist,
  selectedPlaylist,
  onCreatePlaylist,
  onDeletePlaylist,
}) {
  // Renderiza una tarjeta resumida con animación suave.
  const renderStatCard = (label, value, accent) => (
    <motion.div
      key={label}
      className="glass-panel"
      style={{
        padding: "1.1rem",
        display: "flex",
        flexDirection: "column",
        gap: "0.35rem",
      }}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <span style={{ fontSize: "0.85rem", color: "var(--color-text-secondary)" }}>{label}</span>
      <strong style={{ fontSize: "1.6rem", color: accent }}>{value}</strong>
    </motion.div>
  );

  return (
    <aside
      style={{
        width: "310px",
        padding: "2rem 1.6rem 2rem 2rem",
        display: "flex",
        flexDirection: "column",
        gap: "2rem",
        position: "relative",
        zIndex: 2,
      }}
    >
      <section style={{ display: "grid", gap: "1rem" }}>
        {renderStatCard("Total", stats.total ?? 0, "var(--color-text-primary)")}
        {renderStatCard("Favoritos", stats.favorites ?? 0, "var(--color-accent-soft)")}
        {renderStatCard("Privados", stats.private ?? 0, "var(--color-warning)")}
      </section>

      <div className="gradient-divider" />

      <section>
        <h3 style={{ marginBottom: "0.8rem", fontSize: "1rem", letterSpacing: "0.06em" }}>
          Tipo de archivo
        </h3>
        <div style={{ display: "grid", gap: "0.6rem" }}>
          {typeFilters.map((filter) => {
            const active = selectedType === filter.id || (filter.id === "all" && selectedType === null);
            return (
              <button
                key={filter.id}
                className="ghost-button"
                onClick={() => onSelectType(filter.id === "all" ? null : filter.id)}
                style={{
                  justifyContent: "flex-start",
                  borderColor: active ? "rgba(123, 77, 255, 0.6)" : undefined,
                  background: active ? "rgba(123, 77, 255, 0.18)" : "transparent",
                  color: active ? "var(--color-text-primary)" : undefined,
                }}
              >
                {filter.label}
              </button>
            );
          })}
        </div>
      </section>

      <div className="gradient-divider" />

      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: "1rem", letterSpacing: "0.06em" }}>Etiquetas</h3>
          <span style={{ fontSize: "0.8rem", color: "var(--color-text-secondary)" }}>
            {tags.length} disponibles
          </span>
        </div>
        <div
          className="scroll-y"
          style={{
            maxHeight: "160px",
            marginTop: "0.8rem",
            display: "grid",
            gap: "0.5rem",
          }}
        >
          {[{ id: "all", name: "Todas" }, ...tags].map((tag) => {
            const active = selectedTag === tag.id || (tag.id === "all" && selectedTag === null);
            return (
              <button
                key={tag.id}
                className="ghost-button"
                onClick={() => onSelectTag(tag.id === "all" ? null : tag.id)}
                style={{
                  justifyContent: "space-between",
                  borderColor: active ? "rgba(123, 77, 255, 0.6)" : undefined,
                  background: active ? "rgba(123, 77, 255, 0.18)" : "transparent",
                  color: active ? "var(--color-text-primary)" : undefined,
                }}
              >
                <span>{tag.name}</span>
                {tag.isPrivate && <span style={{ fontSize: "0.75rem" }}>🔒</span>}
              </button>
            );
          })}
        </div>
      </section>

      <div className="gradient-divider" />

      <section style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: "1rem", letterSpacing: "0.06em" }}>Playlists</h3>
          <button className="ghost-button" onClick={onCreatePlaylist} style={{ paddingInline: "0.9rem" }}>
            + Nueva
          </button>
        </div>
        <div className="scroll-y" style={{ maxHeight: "200px", display: "grid", gap: "0.5rem" }}>
          {playlists.length === 0 ? (
            <p style={{ color: "var(--color-text-secondary)", fontSize: "0.9rem" }}>
              Crea tu primera playlist para agrupar contenido clave.
            </p>
          ) : (
            playlists.map((playlist) => {
              const active = selectedPlaylist === playlist.id;
              return (
                <div
                  key={playlist.id}
                  className="glass-panel"
                  style={{
                    padding: "0.85rem 1rem",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    border: active ? "1px solid rgba(123, 77, 255, 0.6)" : "1px solid transparent",
                    cursor: "pointer",
                  }}
                >
                  <button
                    onClick={() => onSelectPlaylist(active ? null : playlist.id)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: active ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    {playlist.name}
                  </button>
                  <button
                    className="ghost-button"
                    style={{ paddingInline: "0.6rem" }}
                    onClick={() => onDeletePlaylist(playlist.id)}
                  >
                    ✕
                  </button>
                </div>
              );
            })
          )}
        </div>
      </section>
    </aside>
  );
}
