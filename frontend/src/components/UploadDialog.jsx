// Modal para subir nuevos archivos con opciones avanzadas.
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

export function UploadDialog({ open, onClose, onUpload, loading }) {
  // Almacenamos los archivos seleccionados en el input.
  const [files, setFiles] = useState([]);
  // Permite activar la conversión a PDF para documentos ofimáticos.
  const [convertToPdf, setConvertToPdf] = useState(false);
  // Permite extraer el audio en MP3 desde vídeos.
  const [convertToAudio, setConvertToAudio] = useState(false);
  // Permite enviar el material directamente a la zona privada.
  const [markPrivate, setMarkPrivate] = useState(false);

  // Empaquetamos la información y delegamos en el controlador superior.
  const handleSubmit = (event) => {
    event.preventDefault();
    if (files.length === 0) return;

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));
    formData.append("convertToPdf", convertToPdf ? "1" : "0");
    formData.append("convertToAudio", convertToAudio ? "1" : "0");
    formData.append("private", markPrivate ? "1" : "0");
    onUpload(formData);
  };

  // Limpiamos la selección cuando el modal se oculta.
  useEffect(() => {
    if (!open) {
      setFiles([]);
      setConvertToPdf(false);
      setConvertToAudio(false);
      setMarkPrivate(false);
    }
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(5, 2, 10, 0.65)",
            backdropFilter: "blur(6px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 40,
          }}
          onClick={onClose}
        >
          <motion.form
            className="glass-panel"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            onSubmit={handleSubmit}
            onClick={(event) => event.stopPropagation()}
            style={{
              width: "min(640px, 92vw)",
              padding: "2rem",
              display: "flex",
              flexDirection: "column",
              gap: "1.4rem",
            }}
          >
            <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h3 style={{ fontSize: "1.4rem", fontWeight: 700 }}>Subir nuevo contenido</h3>
                <p style={{ color: "var(--color-text-secondary)", marginTop: "0.4rem" }}>
                  Selecciona uno o varios archivos multimedia y configura las opciones adicionales.
                </p>
              </div>
              <button className="ghost-button" onClick={onClose} type="button">
                Cerrar
              </button>
            </header>

            <label
              className="glass-panel"
              style={{
                border: "1px dashed rgba(163, 123, 255, 0.4)",
                padding: "1.6rem",
                textAlign: "center",
                cursor: "pointer",
              }}
            >
              <input
                type="file"
                multiple
                style={{ display: "none" }}
                onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
              />
              <p style={{ fontSize: "1.1rem", fontWeight: 600 }}>Arrastra o haz clic para seleccionar archivos</p>
              <p style={{ color: "var(--color-text-secondary)", marginTop: "0.4rem" }}>
                Soportamos imágenes, vídeos, audio y documentos.
              </p>
            </label>

            {files.length > 0 && (
              <div className="glass-panel" style={{ padding: "1rem" }}>
                <strong style={{ display: "block", marginBottom: "0.6rem" }}>Archivos elegidos</strong>
                <ul style={{ listStyle: "none", display: "grid", gap: "0.4rem" }}>
                  {files.map((file) => (
                    <li key={file.name} style={{ color: "var(--color-text-secondary)" }}>
                      {file.name}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <section style={{ display: "grid", gap: "0.8rem" }}>
              <label style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
                <input
                  type="checkbox"
                  checked={convertToPdf}
                  onChange={(event) => setConvertToPdf(event.target.checked)}
                />
                Convertir documentos compatibles a PDF automáticamente.
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
                <input
                  type="checkbox"
                  checked={convertToAudio}
                  onChange={(event) => setConvertToAudio(event.target.checked)}
                />
                Extraer audio de los vídeos en formato MP3.
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
                <input
                  type="checkbox"
                  checked={markPrivate}
                  onChange={(event) => setMarkPrivate(event.target.checked)}
                />
                Guardar los archivos en el área privada.
              </label>
            </section>

            <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.8rem" }}>
              <button type="button" className="ghost-button" onClick={onClose}>
                Cancelar
              </button>
              <button type="submit" className="primary-button" disabled={loading || files.length === 0}>
                {loading ? "Subiendo..." : "Confirmar subida"}
              </button>
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
