function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function spotifyUrl(obj) {
  return obj?.external_urls?.spotify ?? null;
}

export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: asArray(track.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(track),
    previewUrl: track.preview_url ?? null,
    durationMs: track.duration_ms ?? null,
  };
}

export function artistSummary(artist) {
  if (!artist || !artist.name) return null;
  return {
    image: artist.images?.[0]?.url ?? null,
    title: artist.name,
    subtitle:
      artist.followers?.total != null
        ? `${artist.followers.total.toLocaleString("pt-BR")} seguidores`
        : asArray(artist.genres).join(", "),
    url: spotifyUrl(artist),
  };
}

export function albumSummary(album) {
  if (!album || !album.name) return null;
  return {
    image: album.images?.[0]?.url ?? null,
    title: album.name,
    subtitle: asArray(album.artists).map((a) => a.name).join(", "),
    url: spotifyUrl(album),
  };
}

export function playlistSummary(playlist) {
  if (!playlist || !playlist.name) return null;
  return {
    image: playlist.images?.[0]?.url ?? null,
    title: playlist.name,
    subtitle: playlist.owner?.display_name ? `por ${playlist.owner.display_name}` : "",
    url: spotifyUrl(playlist),
  };
}
