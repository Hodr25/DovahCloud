// Contenedor en cuadrícula que organiza los archivos disponibles.
import { AnimatePresence, motion } from "framer-motion";
import { FileCard } from "./FileCard.jsx";

export function FileGrid({ files, onSelect, onToggleFavorite, onQuickPlay, onAddToPlaylist }) {
  return (
    <motion.section
      layout
      style={{
        display: "grid",
        gap: "1.5rem",
        gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
        position: "relative",
      }}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <AnimatePresence mode="popLayout">
        {files.map((file) => (
          <motion.div
            key={file.id}
            layout
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.94 }}
            transition={{ duration: 0.2 }}
          >
            <FileCard
              file={file}
              onSelect={onSelect}
              onToggleFavorite={onToggleFavorite}
              onQuickPlay={onQuickPlay}
              onAddToPlaylist={onAddToPlaylist}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.section>
  );
}
