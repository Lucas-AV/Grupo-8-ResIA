/** OAuth é controlado pelo backend; o navegador nunca recebe client secret ou token. */
export function urlInicioSpotify(apiUrl: string) {
  return `${apiUrl.replace(/\/$/, '')}/auth/spotify/iniciar`;
}
