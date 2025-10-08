// Contenedor principal de la interfaz moderna para DovahCloud.
import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AnimatedBackground } from "./components/AnimatedBackground.jsx";
import { LoginForm } from "./components/LoginForm.jsx";
import { Header } from "./components/Header.jsx";
import { Sidebar } from "./components/Sidebar.jsx";
import { FileGrid } from "./components/FileGrid.jsx";
import { FileDetailDrawer } from "./components/FileDetailDrawer.jsx";
import { UploadDialog } from "./components/UploadDialog.jsx";
import { NotificationStack } from "./components/NotificationStack.jsx";
import { PlaylistPanel } from "./components/PlaylistPanel.jsx";
import { apiDelete, apiGet, apiPost } from "./api/client.js";
import { useApi } from "./hooks/useApi.js";

export default function App() {
  // Estado que mantiene la sesión actual.
  const [user, setUser] = useState(null);
  // Conjunto completo de archivos accesibles.
  const [files, setFiles] = useState([]);
  // Catálogo de etiquetas disponibles.
  const [tags, setTags] = useState([]);
  // Playlists personales del usuario.
  const [playlists, setPlaylists] = useState([]);
  // Cadena de búsqueda para filtrar contenido.
  const [search, setSearch] = useState("");
  // Estado que activa el filtro de favoritos.
  const [showFavorites, setShowFavorites] = useState(false);
  // Filtro de tipo MIME principal.
  const [selectedType, setSelectedType] = useState(null);
  // Filtro de etiqueta seleccionado actualmente.
  const [selectedTag, setSelectedTag] = useState(null);
  // Playlist activa en el panel contextual.
  const [selectedPlaylistId, setSelectedPlaylistId] = useState(null);
  // Archivo actualmente abierto en el panel lateral.
  const [activeFile, setActiveFile] = useState(null);
  // Controla la visibilidad del modal de subida.
  const [showUploadDialog, setShowUploadDialog] = useState(false);
  // Cola de notificaciones para feedback rápido.
  const [notifications, setNotifications] = useState([]);

  // Añade una nueva notificación a la cola.
  const pushNotification = useCallback((title, body) => {
    setNotifications((current) => [
      ...current,
      { id: `${Date.now()}-${Math.random()}`, title, body },
    ]);
  }, []);

  // Elimina una notificación concreta.
  const dismissNotification = useCallback((id) => {
    setNotifications((current) => current.filter((item) => item.id !== id));
  }, []);

  // Hook reutilizable para gestionar el inicio de sesión.
  const {
    execute: executeLogin,
    loading: loginLoading,
    error: loginError,
  } = useApi((payload) => apiPost("/login", payload), { throwOnError: true });

  // Hook reutilizable para gestionar la subida de archivos.
  const {
    execute: executeUpload,
    loading: uploadLoading,
  } = useApi((formData) => apiPost("/files", formData));

  // Carga el estado de sesión cuando se monta la aplicación.
  useEffect(() => {
    apiGet("/session")
      .then((response) => {
        if (response.authenticated) {
          setUser(response.user);
        }
      })
      .catch((error) => {
        console.error("Error al obtener la sesión:", error);
      });
  }, []);

  // Función utilitaria para solicitar los archivos con los filtros actuales.
  const fetchFiles = useCallback(() => {
    if (!user) return Promise.resolve();

    const params = new URLSearchParams();
    if (search.trim()) params.set("search", search.trim());
    if (showFavorites) params.set("favorites", "1");
    if (selectedType) params.set("type", selectedType);

    return apiGet(`/files?${params.toString()}`)
      .then((data) => setFiles(data))
      .catch(() => pushNotification("Error", "No fue posible cargar los archivos."));
  }, [user, search, showFavorites, selectedType, pushNotification]);

  // Refresco de datos cada vez que hay un usuario autenticado o cambian parámetros de filtrado.
  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);

  // Recupera las etiquetas una única vez tras autenticación.
  useEffect(() => {
    if (!user) return;
    apiGet("/tags")
      .then((data) => setTags(data))
      .catch(() => pushNotification("Aviso", "No se pudieron cargar las etiquetas."));
  }, [user]);

  // Recupera las playlists asociadas a la cuenta.
  const loadPlaylists = useCallback(() => {
    if (!user) return;
    apiGet("/playlists")
      .then((data) => setPlaylists(data))
      .catch(() => pushNotification("Aviso", "No fue posible sincronizar las playlists."));
  }, [user]);

  useEffect(() => {
    if (!user) return;
    loadPlaylists();
  }, [user, loadPlaylists]);

  // Genera estadísticas básicas para el panel lateral.
  const stats = useMemo(() => {
    return {
      total: files.length,
      favorites: files.filter((file) => file.isFavorite).length,
      private: files.filter((file) => file.isPrivate).length,
    };
  }, [files]);

  // Identifica el objeto etiqueta actual para filtrado por nombre.
  const activeTag = useMemo(
    () => (selectedTag ? tags.find((tag) => tag.id === selectedTag) : null),
    [selectedTag, tags]
  );

  // Calcula la playlist seleccionada para el panel contextual.
  const activePlaylist = useMemo(
    () => playlists.find((playlist) => playlist.id === selectedPlaylistId) ?? null,
    [playlists, selectedPlaylistId]
  );

  // Aplica los filtros en memoria sobre el listado general de archivos.
  const filteredFiles = useMemo(() => {
    if (!activeTag) return files;
    return files.filter((file) => file.tags.includes(activeTag.name));
  }, [files, activeTag]);

  // Gestiona el flujo de login con manejo de errores profesionales.
  const handleLogin = useCallback(
    async (credentials) => {
      try {
        const response = await executeLogin(credentials);
        if (response?.authenticated) {
          setUser(response.user);
          pushNotification("Bienvenido", "Sesión iniciada correctamente.");
        }
      } catch (error) {
        const message =
          error?.payload?.error ?? "No pudimos verificar tus credenciales, por favor revisa e inténtalo de nuevo.";
        pushNotification("Acceso denegado", message);
      }
    },
    [executeLogin, pushNotification]
  );

  // Cierra la sesión actual y limpia los estados dependientes.
  const handleLogout = useCallback(() => {
    apiPost("/logout")
      .then(() => {
        setUser(null);
        setFiles([]);
        setPlaylists([]);
        setTags([]);
        pushNotification("Sesión finalizada", "Has salido de DovahCloud con éxito.");
      })
      .catch(() => pushNotification("Aviso", "No se pudo cerrar sesión correctamente."));
  }, [pushNotification]);

  // Alterna el estado de favorito directamente a través de la API.
  const handleToggleFavorite = useCallback(
    (file) => {
      apiPost(`/files/${file.id}/favorite`)
        .then((updated) => {
          setFiles((current) =>
            current.map((item) =>
              item.id === updated.id ? { ...item, isFavorite: updated.favorite } : item
            )
          );
          setActiveFile((current) =>
            current && current.id === updated.id ? { ...current, isFavorite: updated.favorite } : current
          );
        })
        .catch(() => pushNotification("Aviso", "No fue posible actualizar el favorito."));
    },
    [pushNotification]
  );

  // Envía una subida con las opciones especificadas.
  const handleUpload = useCallback(
    async (formData) => {
      const result = await executeUpload(formData);
      if (result && result.uploaded) {
        setShowUploadDialog(false);
        setFiles((current) => [...result.uploaded, ...current]);
        pushNotification("Subida completada", `${result.count} archivo(s) añadidos con éxito.`);
      }
    },
    [executeUpload, pushNotification]
  );

  // Añade un archivo a la playlist activa.
  const handleAddToPlaylist = useCallback(
    (file) => {
      if (!selectedPlaylistId) {
        pushNotification("Selecciona una playlist", "Elige una playlist en el panel lateral para añadir contenido.");
        return;
      }

      apiPost(`/playlists/${selectedPlaylistId}/items`, { fileId: file.id })
        .then((updated) => {
          setPlaylists((current) =>
            current.map((playlist) => (playlist.id === updated.id ? updated : playlist))
          );
          pushNotification("Playlist actualizada", `${file.name} ahora forma parte de la lista.`);
        })
        .catch(() => pushNotification("Aviso", "No fue posible añadir el archivo a la playlist."));
    },
    [selectedPlaylistId, pushNotification]
  );

  // Elimina un archivo de la playlist activa mediante la API.
  const handleRemoveFromPlaylist = useCallback(
    (file) => {
      if (!selectedPlaylistId) return;
      apiDelete(`/playlists/${selectedPlaylistId}/items/${file.id}`)
        .then((updated) => {
          setPlaylists((current) =>
            current.map((playlist) => (playlist.id === updated.id ? updated : playlist))
          );
          pushNotification("Elemento eliminado", `${file.name} ya no pertenece a la playlist.`);
        })
        .catch(() => pushNotification("Aviso", "No fue posible eliminar el archivo de la playlist."));
    },
    [selectedPlaylistId, pushNotification]
  );

  // Estado de refresco manual para archivos y playlists.
  const handleRefresh = useCallback(() => {
    fetchFiles();
    loadPlaylists();
  }, [fetchFiles, loadPlaylists]);

  // Permite crear una nueva playlist con un nombre sugerido.
  const handleCreatePlaylist = useCallback(() => {
    const name = prompt("Nombre para la nueva playlist:");
    if (!name) return;

    apiPost("/playlists", { name })
      .then((created) => {
        setPlaylists((current) => [created, ...current]);
        setSelectedPlaylistId(created.id);
        pushNotification("Playlist creada", "Organiza tus archivos con esta nueva lista.");
      })
      .catch(() => pushNotification("Aviso", "No se pudo crear la playlist."));
  }, [pushNotification]);

  // Elimina por completo una playlist del usuario.
  const handleDeletePlaylist = useCallback(
    (playlistId) => {
      if (!window.confirm("¿Seguro que deseas eliminar esta playlist?")) return;
      apiDelete(`/playlists/${playlistId}`)
        .then(() => {
          setPlaylists((current) => current.filter((playlist) => playlist.id !== playlistId));
          if (selectedPlaylistId === playlistId) {
            setSelectedPlaylistId(null);
          }
          pushNotification("Playlist eliminada", "La lista ya no está disponible.");
        })
        .catch(() => pushNotification("Aviso", "No se pudo eliminar la playlist."));
    },
    [pushNotification, selectedPlaylistId]
  );

  // Reproduce un archivo directamente en una pestaña nueva si hay enlace disponible.
  const handleQuickPlay = useCallback(
    (file) => {
      if (!file.mediaUrl) {
        pushNotification("Vista previa no disponible", "Este archivo no cuenta con streaming directo.");
        return;
      }
      const target = file.mediaUrl.startsWith("http")
        ? file.mediaUrl
        : `${window.location.origin}${file.mediaUrl}`;
      window.open(target, "_blank", "noopener,noreferrer");
    },
    [pushNotification]
  );

  // Cuerpo principal cuando no hay sesión activa.
  if (!user) {
    return (
      <main style={{ flex: 1, display: "grid", placeItems: "center", position: "relative" }}>
        <AnimatedBackground />
        <LoginForm onSubmit={handleLogin} loading={loginLoading} error={loginError?.payload?.error} />
        <NotificationStack messages={notifications} onDismiss={dismissNotification} />
      </main>
    );
  }

  // Interfaz completa para usuarios autenticados.
  return (
    <div style={{ display: "flex", flex: 1, position: "relative" }}>
      <AnimatedBackground />

      <Sidebar
        stats={stats}
        tags={tags}
        selectedTag={selectedTag}
        onSelectTag={setSelectedTag}
        selectedType={selectedType}
        onSelectType={setSelectedType}
        playlists={playlists}
        selectedPlaylist={selectedPlaylistId}
        onSelectPlaylist={setSelectedPlaylistId}
        onCreatePlaylist={handleCreatePlaylist}
        onDeletePlaylist={handleDeletePlaylist}
      />

      <main
        style={{
          flex: 1,
          padding: "2rem",
          paddingLeft: "0.5rem",
          position: "relative",
          zIndex: 2,
          display: "flex",
          flexDirection: "column",
          gap: "1.8rem",
        }}
      >
        <Header
          user={user}
          search={search}
          onSearchChange={setSearch}
          onOpenUpload={() => setShowUploadDialog(true)}
          onToggleFavorites={() => setShowFavorites((value) => !value)}
          showFavorites={showFavorites}
          onRefresh={handleRefresh}
          onLogout={handleLogout}
        />

        <FileGrid
          files={filteredFiles}
          onSelect={setActiveFile}
          onToggleFavorite={handleToggleFavorite}
          onQuickPlay={handleQuickPlay}
          onAddToPlaylist={handleAddToPlaylist}
        />

        <motion.section layout style={{ display: "grid", gap: "1.4rem", gridTemplateColumns: "1fr 320px" }}>
          <PlaylistPanel
            playlist={activePlaylist}
            onPlayItem={handleQuickPlay}
            onRemoveItem={handleRemoveFromPlaylist}
          />

          <div className="glass-panel" style={{ padding: "1.4rem" }}>
            <h3 style={{ fontSize: "1.1rem", marginBottom: "0.8rem" }}>Consejos rápidos</h3>
            <ul style={{ listStyle: "disc", paddingLeft: "1.2rem", display: "grid", gap: "0.5rem" }}>
              <li>Utiliza las etiquetas para clasificar sesiones temáticas.</li>
              <li>Resalta tus favoritos para acceder todavía más rápido.</li>
              <li>Los archivos privados respetan tus permisos actuales.</li>
            </ul>
          </div>
        </motion.section>
      </main>

      <FileDetailDrawer file={activeFile} onClose={() => setActiveFile(null)} />

      <UploadDialog
        open={showUploadDialog}
        onClose={() => setShowUploadDialog(false)}
        onUpload={handleUpload}
        loading={uploadLoading}
      />

      <NotificationStack messages={notifications} onDismiss={dismissNotification} />
    </div>
  );
}
