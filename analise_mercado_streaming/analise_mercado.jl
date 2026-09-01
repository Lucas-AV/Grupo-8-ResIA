# analise_mercado.jl
# Análise do mercado de streaming de música: visão global, Brasil e Spotify
# Nano-Challenge CBL — Residência em IA (UnB / LabLivre / Instituto Eldorado)
#
# Como rodar: veja o GUIA_AMBIENTE_FEDORA.md desta pasta para instruções de instalação.
# Pré-requisito: já ter rodado `julia setup.jl` uma vez nesta pasta.

using Pkg
Pkg.activate(@__DIR__)  # usa o ambiente isolado deste projeto, não o ambiente global

using CSV
using DataFrames
using Statistics
using Plots
using Printf

const DATA_DIR = joinpath(@__DIR__, "data")

# ---------------------------------------------------------------------------
# 1. Carregar os dados
# ---------------------------------------------------------------------------

spotify_q    = CSV.read(joinpath(DATA_DIR, "spotify_quarterly.csv"), DataFrame)
global_rev   = CSV.read(joinpath(DATA_DIR, "global_market_revenue.csv"), DataFrame)
global_subs  = CSV.read(joinpath(DATA_DIR, "global_paid_subscribers.csv"), DataFrame)
brasil       = CSV.read(joinpath(DATA_DIR, "brazil_market.csv"), DataFrame)
market_share = CSV.read(joinpath(DATA_DIR, "platform_market_share.csv"), DataFrame)

println("Dados carregados:")
println(" - Spotify trimestral:       ", nrow(spotify_q), " linhas")
println(" - Receita global (IFPI):    ", nrow(global_rev), " linhas")
println(" - Assinantes pagos globais: ", nrow(global_subs), " linhas")
println(" - Mercado brasileiro:       ", nrow(brasil), " linhas")
println(" - Participação de mercado:  ", nrow(market_share), " linhas")

# ---------------------------------------------------------------------------
# 2. Spotify: evolução trimestral de usuários e receita
# ---------------------------------------------------------------------------

println("\n=== Spotify: crescimento trimestral ===")

p1 = plot(spotify_q.quarter, spotify_q.mau_millions,
    label = "MAU (milhões)", marker = :circle, linewidth = 2,
    xlabel = "Trimestre", ylabel = "Milhões de usuários",
    title = "Spotify: MAU e Assinantes Premium por trimestre",
    xrotation = 45, legend = :topleft, size = (800, 500))
plot!(p1, spotify_q.quarter, spotify_q.premium_subs_millions,
    label = "Assinantes Premium (milhões)", marker = :square, linewidth = 2)
savefig(p1, joinpath(@__DIR__, "output_spotify_usuarios.png"))

p2 = plot(spotify_q.quarter, spotify_q.total_revenue_eur_m,
    label = "Receita total (€M)", marker = :circle, linewidth = 2, color = :seagreen,
    xlabel = "Trimestre", ylabel = "€ milhões",
    title = "Spotify: Receita Total por Trimestre",
    xrotation = 45, legend = :topleft, size = (800, 500))
savefig(p2, joinpath(@__DIR__, "output_spotify_receita.png"))

p2b = plot(spotify_q.quarter, spotify_q.operating_margin_pct,
    label = "Margem operacional (%)", marker = :diamond, linewidth = 2, color = :firebrick,
    xlabel = "Trimestre", ylabel = "Margem operacional (%)",
    title = "Spotify: Margem Operacional por Trimestre",
    xrotation = 45, legend = :topleft, size = (800, 500))
savefig(p2b, joinpath(@__DIR__, "output_spotify_margem.png"))

mau_growth  = (last(spotify_q.mau_millions) / first(spotify_q.mau_millions) - 1) * 100
subs_growth = (last(spotify_q.premium_subs_millions) / first(spotify_q.premium_subs_millions) - 1) * 100
@printf("MAU cresceu %.1f%% entre %s e %s\n", mau_growth, first(spotify_q.quarter), last(spotify_q.quarter))
@printf("Assinantes Premium cresceram %.1f%% no mesmo período\n", subs_growth)

# ---------------------------------------------------------------------------
# 3. Mercado global: receita por formato (IFPI)
# ---------------------------------------------------------------------------

println("\n=== Mercado Global de Música Gravada (IFPI) ===")

latest_year = maximum(skipmissing(global_rev.year))
row_latest  = global_rev[global_rev.year .== latest_year, :][1, :]

@printf("Em %d, o mercado global somou US\$ %.1f bi, dos quais streaming representou %.1f%%\n",
    latest_year, row_latest.total_revenue_usd_bn,
    row_latest.streaming_revenue_usd_bn / row_latest.total_revenue_usd_bn * 100)

dados_recentes = filter(row -> !ismissing(row.streaming_revenue_usd_bn), global_rev)

p3 = plot(dados_recentes.year, dados_recentes.total_revenue_usd_bn,
    label = "Receita total", marker = :circle, linewidth = 2,
    xlabel = "Ano", ylabel = "US\$ bilhões",
    title = "Mercado Global de Música Gravada (IFPI)",
    legend = :topleft, size = (800, 500))
plot!(p3, dados_recentes.year, dados_recentes.streaming_revenue_usd_bn,
    label = "Receita de streaming", marker = :square, linewidth = 2)
savefig(p3, joinpath(@__DIR__, "output_mercado_global.png"))

# ---------------------------------------------------------------------------
# 4. Assinantes pagos globais ao longo do tempo
# ---------------------------------------------------------------------------

p4 = bar(string.(global_subs.year), global_subs.subscribers_millions,
    label = "Assinantes pagos (milhões)",
    xlabel = "Ano", ylabel = "Milhões de assinantes",
    title = "Crescimento de Assinantes Pagos de Streaming no Mundo",
    legend = false, size = (800, 500))
savefig(p4, joinpath(@__DIR__, "output_assinantes_globais.png"))

# ---------------------------------------------------------------------------
# 5. Brasil vs Mundo: comparação de crescimento
# ---------------------------------------------------------------------------

println("\n=== Brasil vs Mundo ===")

brasil_completo = filter(row -> !ismissing(row.growth_pct_yoy), brasil)
brasil_latest   = brasil_completo[argmax(brasil_completo.year), :]
global_growth_latest = row_latest.growth_pct_yoy

razao = brasil_latest.growth_pct_yoy / global_growth_latest
@printf("Em %d, o Brasil cresceu %.1f%% contra %.1f%% do mercado global — %.1fx mais rápido\n",
    brasil_latest.year, brasil_latest.growth_pct_yoy, global_growth_latest, razao)

p5 = bar(["Brasil", "Global"], [brasil_latest.growth_pct_yoy, global_growth_latest],
    label = "", xlabel = "Mercado", ylabel = "Crescimento (% a.a.)",
    title = "Crescimento do Mercado Fonográfico — Brasil vs Global ($(brasil_latest.year))",
    size = (800, 500))
savefig(p5, joinpath(@__DIR__, "output_brasil_vs_global.png"))

println("\nEvolução do Brasil no ranking global da IFPI:")
for row in eachrow(brasil)
    println("  $(row.year): posição #$(row.global_ranking)")
end

# ---------------------------------------------------------------------------
# 6. Participação de mercado entre plataformas + concentração (HHI)
# ---------------------------------------------------------------------------

println("\n=== Participação de Mercado entre Plataformas ===")

p6 = bar(market_share.platform, market_share.share_pct,
    label = "Participação (%)", xlabel = "Plataforma",
    ylabel = "% dos assinantes pagos globais",
    title = "Participação de Mercado — Streaming de Música (fim de 2025, MIDiA Research)",
    xrotation = 20, legend = false, size = (800, 500))
savefig(p6, joinpath(@__DIR__, "output_market_share.png"))

# Índice de Herfindahl-Hirschman (HHI) aproximado, para medir concentração de mercado.
# Escala usual: HHI < 1500 = competitivo | 1500-2500 = moderadamente concentrado | > 2500 = altamente concentrado
hhi = sum(market_share.share_pct .^ 2)
@printf("\nÍndice de concentração (HHI aproximado): %.0f\n", hhi)

if hhi < 1500
    println("Interpretação: mercado competitivo")
elseif hhi < 2500
    println("Interpretação: mercado moderadamente concentrado")
else
    println("Interpretação: mercado altamente concentrado")
end
println("Atenção: a categoria \"Outros\" agrega várias plataformas menores num único bloco, " *
        "então o HHI real (com cada uma separada) tende a ser um pouco mais baixo do que este valor aproximado.")

println("\nAnálise concluída. Gráficos salvos como .png na pasta deste script.")
