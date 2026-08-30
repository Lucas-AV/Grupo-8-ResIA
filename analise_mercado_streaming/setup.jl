# setup.jl
# Roda uma única vez para criar o ambiente Julia deste projeto (isolado, reprodutível).
# Uso: julia setup.jl

using Pkg

println("Ativando o ambiente do projeto em: ", @__DIR__)
Pkg.activate(@__DIR__)

println("Instalando dependências (CSV, DataFrames, Plots)...")
Pkg.add(["CSV", "DataFrames", "Plots"])

println("Pré-compilando pacotes...")
Pkg.precompile()

println()
println("Ambiente configurado com sucesso.")
println("Este projeto agora tem seu próprio Project.toml e Manifest.toml,")
println("isolados do resto do sistema (como um venv do Python).")
println()
println("A partir de agora, rode a análise com: julia analise_mercado.jl")
