type Propriedades = {
  nome: string;
  artista: string;
  explicacao: string;
  confianca: number;
};

export function CartaoFaixa({ nome, artista, explicacao, confianca }: Propriedades) {
  return (
    <article className="cartao-faixa">
      <div className="capa-faixa" aria-hidden="true">♪</div>
      <div className="dados-faixa">
        <span className="rotulo">Exemplo visual</span>
        <h3>{nome}</h3>
        <p className="artista">{artista}</p>
        <p className="explicacao"><span>✦</span>{explicacao}</p>
        <div className="confianca">
          <span>Confiança demonstrativa</span>
          <strong>{Math.round(confianca * 100)}%</strong>
        </div>
      </div>
    </article>
  );
}

