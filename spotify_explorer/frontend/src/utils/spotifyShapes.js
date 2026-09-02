export function trackSummary(track) {
  if (!track || !track.name) return null;
  return {
    image: track.album?.images?.[0]?.url ?? null,
    title: track.name,
    subtitle: (track.artists ?? []).map((a) => a.name).join(", "),
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
        : (artist.genres ?? []).join(", "),
  };
}

export function albumSummary(album) {
  if (!album || !album.name) return null;
  return {
    image: album.images?.[0]?.url ?? null,
    title: album.name,
    subtitle: (album.artists ?? []).map((a) => a.name).join(", "),
  };
}
